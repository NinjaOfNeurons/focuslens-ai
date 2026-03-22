import cv2
import mediapipe as mp
import websockets
import asyncio
import json
import time
import uuid

from visualizer import draw_overlay, draw_landmarks
from landmark_extractor import extract_all

WS_URL      = "ws://localhost:8001/ws/landmarks"
SHOW_WINDOW = False  # set True to see landmarks

SESSION_ID = str(uuid.uuid4())  # generated once per session
frame_id   = 0

async def run():
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 10)

    print(f"[edge] Camera opened — session: {SESSION_ID}")

    async for ws in websockets.connect(WS_URL):
        try:
            print("[edge] Connected to ingestion service")
            global frame_id

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                img_h, img_w = frame.shape[:2]
                rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)

                if not results.multi_face_landmarks:
                    if SHOW_WINDOW:
                        cv2.putText(frame, "No face detected", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                        cv2.imshow("FocusLens Edge", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    await asyncio.sleep(0.1)
                    continue

                frame_id += 1
                lm       = results.multi_face_landmarks[0].landmark
                features = extract_all(lm, img_w, img_h)

                # focus rule — uses extracted features
                ear     = features["eye"]["ear_avg"]
                yaw     = features["head_pose"]["yaw"]
                pitch   = features["head_pose"]["pitch"]
                focused = bool(
                    ear > 0.08 and
                    abs(yaw) < 30 and
                    abs(pitch) < 20
                )

                if SHOW_WINDOW:
                    frame = draw_landmarks(frame, results)
                    frame = draw_overlay(frame, ear, yaw, pitch, focused)
                    cv2.imshow("FocusLens Edge", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                payload = {
                    "session_id": SESSION_ID,
                    "frame_id":   frame_id,
                    "ts":         int(time.time() * 1000),
                    **features,              # eye, head_pose, gaze
                    "focus": {
                        "rule_based":    focused,
                        "score":         None,   # ML model fills later
                        "model_version": None
                    },
                    "face": {
                        "detected":   True,
                        "confidence": float(results.multi_face_landmarks[0]
                                           .landmark[0].visibility
                                           if hasattr(results.multi_face_landmarks[0]
                                           .landmark[0], 'visibility') else 0.99)
                    }
                }

                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.1)

        except websockets.ConnectionClosed:
            print("[edge] Reconnecting...")
            continue

    cap.release()
    if SHOW_WINDOW:
        cv2.destroyAllWindows()
    face_mesh.close()

if __name__ == "__main__":
    asyncio.run(run())