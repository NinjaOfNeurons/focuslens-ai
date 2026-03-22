from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaProducer
import json
import datetime

app = FastAPI()

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

@app.websocket("/ws/landmarks")
async def landmarks(ws: WebSocket):
    await ws.accept()
    print(f"[+] Client connected: {ws.client.host}")
    try:
        while True:
            raw  = await ws.receive_text()
            data = json.loads(raw)

            ts      = datetime.datetime.fromtimestamp(data["ts"] / 1000)
            focused = data["focus"]["rule_based"]
            ear     = data["eye"]["ear_avg"]
            yaw     = data["head_pose"]["yaw"]
            pitch   = data["head_pose"]["pitch"]
            zone    = data["gaze"]["gaze_zone"]
            session = data["session_id"][:8]

            status = "FOCUSED    " if focused else "DISTRACTED "
            print(
                f"[{ts.strftime('%H:%M:%S')}] "
                f"{status} | "
                f"EAR={ear:.3f} | "
                f"Yaw={yaw:+.1f}° | "
                f"Gaze={zone:<8} | "
                f"Session={session}"
            )

            # publish to redpanda
            producer.send("focus-raw", value=data)

    except WebSocketDisconnect:
        print(f"[-] Client disconnected")