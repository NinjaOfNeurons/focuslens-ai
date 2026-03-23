import pandas as pd
import numpy as np
from scipy.signal import find_peaks

def compute_rhythm(df: pd.DataFrame) -> dict:
    """
    Analyses the focus signal over time to find
    natural attention cycles and distraction patterns.
    """
    if df.empty or len(df) < 10:
        return {
            "avg_focus_duration_seconds":       0,
            "avg_distraction_duration_seconds": 0,
            "focus_cycles":                     0,
            "longest_focus_seconds":            0,
            "longest_distraction_seconds":      0
        }

    signal = df["focused"].astype(int).values

    # --- smooth signal with exponential moving average ---
    alpha    = 0.15
    smoothed = np.zeros(len(signal))
    smoothed[0] = signal[0]
    for i in range(1, len(signal)):
        smoothed[i] = alpha * signal[i] + (1 - alpha) * smoothed[i - 1]

    # --- find focus peaks (sustained attention bursts) ---
    peaks, _ = find_peaks(smoothed, height=0.5, distance=10, prominence=0.1)

    # --- segment into focused / distracted runs ---
    focus_durations       = []
    distraction_durations = []

    current_state = signal[0]
    run_length    = 1

    # each frame is ~0.1 seconds (10fps)
    frame_duration = 0.1

    for i in range(1, len(signal)):
        if signal[i] == current_state:
            run_length += 1
        else:
            duration = run_length * frame_duration
            if current_state == 1:
                focus_durations.append(duration)
            else:
                distraction_durations.append(duration)
            current_state = signal[i]
            run_length    = 1

    # flush last run
    duration = run_length * frame_duration
    if current_state == 1:
        focus_durations.append(duration)
    else:
        distraction_durations.append(duration)

    return {
        "avg_focus_duration_seconds": round(
            float(np.mean(focus_durations)) if focus_durations else 0, 2),
        "avg_distraction_duration_seconds": round(
            float(np.mean(distraction_durations)) if distraction_durations else 0, 2),
        "focus_cycles":          len(peaks),
        "longest_focus_seconds": round(
            float(max(focus_durations)) if focus_durations else 0, 2),
        "longest_distraction_seconds": round(
            float(max(distraction_durations)) if distraction_durations else 0, 2),
    }