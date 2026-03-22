from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json, datetime

app = FastAPI()

@app.websocket("/ws/landmarks")
async def landmarks(ws: WebSocket):
    await ws.accept()
    client = ws.client.host
    print(f"[+] Client connected: {client}")
    try:
        while True:
            raw  = await ws.receive_text()
            data = json.loads(raw)

            focused = data["focused"]
            ear     = data["ear"]
            yaw     = data["yaw"]
            pitch   = data["pitch"]
            ts      = datetime.datetime.fromtimestamp(data["ts"] / 1000)

            status = "FOCUSED    " if focused else "DISTRACTED "
            print(
                f"[{ts.strftime('%H:%M:%S')}] "
                f"{status} | "
                f"EAR={ear:.3f} | "
                f"Yaw={yaw:+.1f}° | "
                f"Pitch={pitch:+.1f}°"
            )

    except WebSocketDisconnect:
        print(f"[-] Client disconnected: {client}")