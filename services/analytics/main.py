from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

from db            import fetch_session, fetch_all_sessions
from rhythm_engine import compute_rhythm

app = FastAPI(title="FocusLens Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def compute_focus_score(df: pd.DataFrame) -> float:
    """
    Simple focus score 0-100.
    Weighted by: focused ratio (60%) + stable gaze (20%) + low distraction frequency (20%)
    """
    if df.empty:
        return 0.0

    focused_ratio = df["focused"].mean()

    center_gaze_ratio = (df["gaze_zone"] == "center").mean()

    # distraction frequency — transitions from focused to distracted per minute
    transitions    = (df["focused"].astype(int).diff().abs() == 1).sum()
    duration_mins  = max(len(df) * 0.1 / 60, 0.01)
    distraction_freq = transitions / duration_mins
    # normalise — 0 transitions = 1.0, 10+ = 0.0
    distraction_score = max(0, 1 - (distraction_freq / 10))

    score = (
        focused_ratio      * 60 +
        center_gaze_ratio  * 20 +
        distraction_score  * 20
    )
    return round(float(score), 2)

def gaze_distribution(df: pd.DataFrame) -> dict:
    counts = df["gaze_zone"].value_counts(normalize=True) * 100
    zones  = ["center", "left", "right", "up", "down"]
    return {z: round(float(counts.get(z, 0)), 2) for z in zones}

def blink_rate(df: pd.DataFrame) -> float:
    duration_mins = max(len(df) * 0.1 / 60, 0.01)
    blinks        = df["blink"].sum()
    return round(float(blinks / duration_mins), 2)

@app.get("/analytics/{session_id}")
def get_session_analytics(session_id: str):
    df = fetch_session(session_id)

    if df.empty:
        raise HTTPException(status_code=404, detail="Session not found")

    duration_seconds = len(df) * 0.1
    focused_frames   = int(df["focused"].sum())
    distracted_frames = len(df) - focused_frames
    transitions      = int((df["focused"].astype(int).diff().abs() == 1).sum())
    distraction_count = transitions // 2  # each distraction = 1 in + 1 out

    return {
        "session_id":           session_id,
        "duration_minutes":     round(duration_seconds / 60, 2),
        "focus_score":          compute_focus_score(df),
        "total_frames":         len(df),
        "focused_frames":       focused_frames,
        "distracted_frames":    distracted_frames,
        "distraction_count":    distraction_count,
        "avg_ear":              round(float(df["ear_avg"].mean()), 4),
        "blink_rate_per_minute": blink_rate(df),
        "gaze_distribution":    gaze_distribution(df),
        "rhythm":               compute_rhythm(df),
    }

@app.get("/sessions")
def list_sessions():
    sessions = fetch_all_sessions()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")
    return sessions

@app.get("/health")
def health():
    return {"status": "ok"}