from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import psycopg2
import psycopg2.extras
import redis
import json

app = FastAPI(title="FocusLens Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANALYTICS_URL = "http://localhost:8004"

DB = dict(
    host="localhost", port=5432,
    dbname="focuslens", user="fl_user", password="fl_pass"
)

cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

def get_conn():
    return psycopg2.connect(**DB)

# --- sessions ---

@app.get("/api/sessions")
def list_sessions():
    async def _():
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{ANALYTICS_URL}/sessions")
            return r.json()
    import asyncio
    return asyncio.run(_())

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    # check cache first
    cached = cache.get(f"session:{session_id}")
    if cached:
        return json.loads(cached)

    import asyncio
    async def _():
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{ANALYTICS_URL}/analytics/{session_id}"
            )
            if r.status_code == 404:
                raise HTTPException(404, "Session not found")
            return r.json()

    result = asyncio.run(_())
    # cache for 60 seconds
    cache.setex(f"session:{session_id}", 60, json.dumps(result))
    return result

# --- live feed for dashboard ---

@app.get("/api/live/{session_id}")
def live_feed(session_id: str):
    """Returns last 60 frames for live chart."""
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            ts,
            ear_avg,
            focused,
            gaze_zone,
            yaw,
            pitch
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
    """Returns the most recent session id."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT session_id
        FROM focus_events
        ORDER BY ts DESC
        LIMIT 1
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