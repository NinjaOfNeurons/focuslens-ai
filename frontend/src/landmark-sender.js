// NO imports at top — MediaPipe loaded via CDN as globals

const WS_URL = "ws://localhost:8001/ws/landmarks";

const LEFT_EYE  = [159, 145, 33, 133];
const RIGHT_EYE = [386, 374, 263, 362];

function eyeAspectRatio(landmarks, indices) {
  const [top, bottom, left, right] = indices.map(i => landmarks[i]);
  const vertical   = Math.hypot(top.x - bottom.x, top.y - bottom.y);
  const horizontal = Math.hypot(left.x - right.x, left.y - right.y);
  return vertical / (horizontal + 1e-6);
}

function headPose(landmarks) {
  const nose     = landmarks[1];
  const chin     = landmarks[152];
  const leftEar  = landmarks[234];
  const rightEar = landmarks[454];
  const faceCenter = {
    x: (leftEar.x + rightEar.x) / 2,
    y: (leftEar.y + chin.y) / 2
  };
  const yaw   = (nose.x - faceCenter.x) * 180;
  const pitch = (nose.y - faceCenter.y) * 180;
  return { yaw, pitch };
}

export function startLandmarkSender(videoElement, onStatus) {
  let ws = null;

  function connect() {
    ws = new WebSocket(WS_URL);
    ws.onopen  = () => onStatus("Connected — session live");
    ws.onclose = () => {
      onStatus("Reconnecting...");
      setTimeout(connect, 2000);
    };
  }
  connect();

  const faceMesh = new FaceMesh({ locateFile: f =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
  });

  faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });

  faceMesh.onResults(results => {
    if (!results.multiFaceLandmarks?.length) {
      onStatus("No face detected");
      return;
    }

    const lm    = results.multiFaceLandmarks[0];
    const earL  = eyeAspectRatio(lm, LEFT_EYE);
    const earR  = eyeAspectRatio(lm, RIGHT_EYE);
    const ear   = (earL + earR) / 2;
    const { yaw, pitch } = headPose(lm);

    const focused = ear > 0.20 && Math.abs(yaw) < 30 && Math.abs(pitch) < 20;

    const payload = {
      ear:     parseFloat(ear.toFixed(4)),
      yaw:     parseFloat(yaw.toFixed(2)),
      pitch:   parseFloat(pitch.toFixed(2)),
      focused: focused,
      ts:      Date.now()
    };

    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    }

    onStatus(`EAR: ${payload.ear} | Yaw: ${payload.yaw}° | ${focused ? "FOCUSED" : "DISTRACTED"}`);
  });

  const camera = new Camera(videoElement, {
    onFrame: async () => { await faceMesh.send({ image: videoElement }); },
    width: 640,
    height: 480,
  });
  camera.start();
}