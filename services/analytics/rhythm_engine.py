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

    signal = df["focused"].astype(int).values  #[1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1]

    # --- smooth signal with exponential moving average ---
    """
    Alpha = 0.15 means each new value is 15% the current frame and 85% the history. So a single frame of distraction barely moves the smoothed line. Only sustained distraction pulls it down.
    raw:      1 1 1 0 1 1 1 0 0 0 1 1 1
    smoothed: 1 1 1 .9 .9 .9 .9 .8 .7 .6 .7 .7 .8
    """    
    alpha    = 0.15  
    smoothed = np.zeros(len(signal))
    smoothed[0] = signal[0]
    for i in range(1, len(signal)):
        smoothed[i] = alpha * signal[i] + (1 - alpha) * smoothed[i - 1]



    # --- find focus peaks (sustained attention bursts) ---
    """scipy.signal.find_peaks finds local maxima in the smoothed signal. Each peak represents a sustained attention burst — a period where you were consistently focused.
    height=0.5 — only count peaks above 50% focus probability
    distance=10 — peaks must be at least 10 frames (1 second) apart
    prominence=0.1 — peak must stand out from surrounding signal by at least 0.1
  
    
    The number of peaks = focus_cycles in your analytics output.

    """
    peaks, _ = find_peaks(smoothed, height=0.5, distance=10, prominence=0.1)



    # --- segment into focused / distracted runs ---
    """
    signal:  1 1 1 1 0 0 1 1 1 1 1 0 1
    runs:    [focus:4] [distract:2] [focus:5] [distract:1] [focus:1]
    seconds: [0.4s]    [0.2s]       [0.5s]    [0.1s]       [0.1s]
    """
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