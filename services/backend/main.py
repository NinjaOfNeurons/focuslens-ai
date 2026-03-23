from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import psycopg2
import psycopg2.extras
import redis as redis_lib
import json
import os

ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://analytics:8004")
DATABASE_URL  = os.getenv("DATABASE_URL",  "postgresql://fl_user:fl_pass@postgres:5432/focuslens")
REDIS_URL     = os.getenv("REDIS_URL",     "redis://redis:6379")

cache = redis_lib.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="FocusLens Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.get("/api/sessions")
def list_sessions():
    import asyncio
    async def _():
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{ANALYTICS_URL}/sessions")
            return r.json()
    return asyncio.run(_())

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    cached = cache.get(f"session:{session_id}")
    if cached:
        return json.loads(cached)

    import asyncio
    async def _():
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{ANALYTICS_URL}/analytics/{session_id}")
            if r.status_code == 404:
                raise HTTPException(404, "Session not found")
            return r.json()

    result = asyncio.run(_())
    cache.setex(f"session:{session_id}", 60, json.dumps(result))
    return result

@app.get("/api/live/{session_id}")
def live_feed(session_id: str):
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT ts, ear_avg, focused, gaze_zone, yaw, pitch
        FROM focus_events
        WHERE session_id = %s
        ORDER BY ts DESC
        LIMIT 60
    """, (session_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "session_id": session_id,
        "frames": [dict(r) for r in reversed(rows)]
    }

@app.get("/api/latest-session")
def latest_session():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT session_id FROM focus_events
        ORDER BY ts DESC LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, "No sessions found")
    return {"session_id": row[0]}

@app.get("/health")
def health():
    return {"status": "ok"}