# FocusLens AI

An intelligent focus tracking system that uses computer vision and machine learning to analyse attention patterns during work or study sessions. FocusLens runs entirely on your local machine — no cloud, no video storage, no external dependencies.

---

## What it does

FocusLens watches your face through your webcam, extracts behavioural signals in real time, and builds a picture of your cognitive state over time. It detects when you are focused, when you are distracted, and learns the natural rhythm of your attention so it can predict focus drops before they happen.

No raw video is ever stored. The system processes frames locally, extracts only numerical features, and discards the video immediately.

---

## Architecture

FocusLens is built as an edge-to-server system. The machine running the webcam handles all visual processing locally. Only a small JSON feature vector is sent to the server pipeline — never raw video frames.

![alt text](asset/static/image.png)

---

## Features
 
### Real-time focus detection
Detects attention state from webcam feed at 10 frames per second using facial landmark analysis. Computes eye openness, head orientation, and gaze direction to classify each frame as focused or distracted.
 
### Rich feature extraction
Every frame produces a structured feature vector including eye aspect ratio (left and right independently), head pose in three axes (yaw, pitch, roll), iris position and gaze zone, blink detection, and a session identifier that ties all frames together.
 
### Cognitive Rhythm Engine
Analyses the focus signal over time to detect natural attention cycles. Uses signal smoothing, peak detection, and frequency analysis to identify your personal productivity rhythm. Predicts upcoming focus drops before they occur.
 
### Gaze zone tracking
Tracks iris position to determine where attention is directed — centre, left, right, up, or down. Feeds into distraction pattern analysis and future attention heatmap features.
 
### Session analytics
Every session produces a summary report including overall focus score (0–100), distraction frequency, peak productivity windows, dominant attention cycle duration, and gaze zone distribution.
 
### MLOps pipeline
Experiment tracking via MLflow, model versioning, and an automated retraining pipeline. The rule-based focus classifier is designed to be replaced by a trained ONNX model with zero changes to the data pipeline.
 
---
 
## Tech stack
 
| Layer | Technology |
|---|---|
| Edge capture | Python, OpenCV, MediaPipe FaceMesh |
| Transport | WebSocket, JSON feature vectors |
| Message bus | Apache Kafka (via apache/kafka:3.7.0) |
| Ingestion | Python, FastAPI |
| Event processing | Python, FastAPI, psycopg2 |
| Analytics | Python, FastAPI, Pandas, SciPy |
| Time-series DB | PostgreSQL + TimescaleDB extension |
| Cache | Redis |
| ML tracking | MLflow |
| Model serving | ONNX Runtime |
| Frontend | React, Vite |
| Container runtime | Docker, Docker Compose |
| Orchestration | Kubernetes (minikube) |
| CI/CD | GitHub Actions (self-hosted runner) |
| Observability | Prometheus, Grafana, Loki |
 
---
 
## Project structure
 
```
focuslens-ai/
├── edge/                        # edge agent — runs on webcam machine
│   ├── main.py                  # orchestrator, camera loop
│   ├── landmark_extractor.py    # MediaPipe feature extraction
│   ├── visualizer.py            # optional visual overlay (SHOW_WINDOW flag)
│   └── requirements.txt
│
├── services/
│   ├── ingestion/               # WebSocket receiver, Kafka producer
│   │   ├── main.py
│   │   ├── init_db.py           # creates database schema
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── event/                   # Kafka consumer, PostgreSQL writer
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── analytics/               # rhythm engine, session scoring, REST API
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── rhythm_engine.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── backend/                 # BFF — aggregates data for dashboard
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── frontend/                    # React dashboard
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── api.js               # API calls to backend
│       └── main.js              # dashboard UI
│
├── k8s/                         # Kubernetes manifests
│   ├── configmap/
│   │   └── config.yaml
│   ├── secrets/
│   │   └── secrets.yaml
│   ├── infra/
│   │   ├── redpanda.yaml        # Kafka (apache/kafka:3.7.0)
│   │   ├── postgres.yaml        # TimescaleDB
│   │   └── redis.yaml
│   ├── services/
│   │   ├── ingestion.yaml
│   │   ├── event.yaml
│   │   ├── analytics.yaml
│   │   └── backend.yaml
│   └── ingress.yaml
│
├── docker-compose.yml           # local development (no K8s)
└── .gitignore
```
 
---
 
## Data pipeline
 
Each webcam frame produces a feature vector:
 
```json
{
  "session_id": "746014e1-5464-4931-8dea-e446a2b43e7d",
  "frame_id": 1042,
  "ts": 1742600000000,
  "eye": {
    "ear_left": 0.32,
    "ear_right": 0.30,
    "ear_avg": 0.31,
    "blink_detected": false
  },
  "head_pose": {
    "yaw": -3.2,
    "pitch": 2.1,
    "roll": 0.5
  },
  "gaze": {
    "iris_left_x": 0.48,
    "iris_left_y": 0.51,
    "iris_right_x": 0.49,
    "iris_right_y": 0.50,
    "gaze_zone": "center"
  },
  "focus": {
    "rule_based": true,
    "score": null,
    "model_version": null
  },
  "face": {
    "detected": true,
    "confidence": 0.97
  }
}
```
 
---
 
## Prerequisites
 
Before starting, install the following on your machine:
 
- **Python 3.11** via miniconda
- **Docker Desktop** — must be running before any step
- **Node.js 22** via nvm
- **minikube** — local Kubernetes
- **kubectl** — Kubernetes CLI
- **helm** — Kubernetes package manager
 
```bash
# install minikube
brew install minikube
 
# install kubectl
brew install kubectl
 
# install helm
brew install helm
 
# install nvm then node 22
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# restart terminal then:
nvm install 22
nvm use 22
```
 
---
 
## Option A — Run with Docker Compose (development)
 
This is the fastest way to get running. No Kubernetes required.
 
### 1. Create conda environment
 
```bash
conda create -n focus python=3.11
conda activate focus
```
 
### 2. Start infrastructure
 
```bash
docker compose up -d
```
 
Starts Redpanda, PostgreSQL + TimescaleDB, and Redis.
 
Verify:
 
```bash
docker compose ps
# should show 3 containers running: redpanda, postgres, redis
```
 
### 3. Initialise database
 
```bash
cd services/ingestion
python -m pip install psycopg2-binary
python init_db.py
# output: [db] Tables created successfully
```
 
### 4. Install all dependencies
 
Run from the repo root:
 
```bash
# edge agent
cd edge && python -m pip install -r requirements.txt && cd ..
 
# services
cd services/ingestion && python -m pip install -r requirements.txt && cd ../..
cd services/event     && python -m pip install -r requirements.txt && cd ../..
cd services/analytics && python -m pip install -r requirements.txt && cd ../..
cd services/backend   && python -m pip install -r requirements.txt && cd ../..
 
# frontend
cd frontend && npm install && cd ..
```
 
### 5. Start all services
 
Open 7 terminals. Activate `conda activate focus` in each Python terminal.
 
```bash
# Terminal 1 — infrastructure (already running)
docker compose up -d
 
# Terminal 2 — ingestion service
cd services/ingestion
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
 
# Terminal 3 — event service
cd services/event
python main.py
 
# Terminal 4 — analytics service
cd services/analytics
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
 
# Terminal 5 — backend API
cd services/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
 
# Terminal 6 — frontend dashboard
cd frontend
npm run dev
 
# Terminal 7 — edge agent (starts webcam)
cd edge
python main.py
```
 
### 6. Open dashboard
 
```
http://localhost:3000
```
 
### 7. Verify data is flowing
 
```bash
docker exec -it focuslens-ai-postgres-1 psql -U fl_user -d focuslens \
  -c "SELECT session_id, ts, ear_avg, focused, gaze_zone FROM focus_events ORDER BY ts DESC LIMIT 5;"
```
 
---
 
## Option B — Run on Kubernetes (minikube)
 
### 1. Start minikube
 
Make sure Docker Desktop is running first.
 
```bash
minikube start --cpus=4 --memory=7000mb --disk-size=30g --driver=docker
```
 
Verify:
 
```bash
minikube status
kubectl get nodes
# should show: minikube   Ready   control-plane
```
 
### 2. Enable addons
 
```bash
minikube addons enable ingress
minikube addons enable metrics-server
```
 
### 3. Create namespace
 
```bash
kubectl create namespace focuslens
```
 
### 4. Apply configmap and secrets
 
```bash
kubectl apply -f k8s/configmap/config.yaml
kubectl apply -f k8s/secrets/secrets.yaml
 
# verify
kubectl get configmap -n focuslens
kubectl get secret -n focuslens
```
 
### 5. Deploy infrastructure
 
```bash
kubectl apply -f k8s/infra/postgres.yaml
kubectl apply -f k8s/infra/redis.yaml
kubectl apply -f k8s/infra/redpanda.yaml
```
 
Wait for all three to be Running (takes 1-2 minutes for image pulls):
 
```bash
kubectl get pods -n focuslens -w
# wait until postgres-0, redis-0, redpanda-0 all show Running
```
 
### 6. Initialise database schema
 
```bash
kubectl exec -it postgres-0 -n focuslens -- psql -U fl_user -d focuslens -c "
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE TABLE IF NOT EXISTS focus_events (
    id          BIGSERIAL,
    session_id  TEXT        NOT NULL,
    frame_id    INTEGER     NOT NULL,
    ts          TIMESTAMPTZ NOT NULL,
    ear_left    FLOAT,
    ear_right   FLOAT,
    ear_avg     FLOAT,
    blink       BOOLEAN,
    yaw         FLOAT,
    pitch       FLOAT,
    roll        FLOAT,
    gaze_zone   TEXT,
    iris_left_x FLOAT,
    iris_left_y FLOAT,
    focused     BOOLEAN,
    focus_score FLOAT,
    PRIMARY KEY (id, ts)
);
SELECT create_hypertable('focus_events', 'ts', if_not_exists => TRUE);
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    started_at   TIMESTAMPTZ NOT NULL,
    ended_at     TIMESTAMPTZ,
    focus_score  FLOAT,
    total_frames INTEGER DEFAULT 0
);
"
```
 
### 7. Build Docker images inside minikube
 
This points your Docker CLI at minikube's internal Docker daemon so images are available to K8s without pushing to a registry:
 
```bash
eval $(minikube docker-env)
 
docker build -t focuslens/ingestion:latest services/ingestion/
docker build -t focuslens/event:latest     services/event/
docker build -t focuslens/analytics:latest services/analytics/
docker build -t focuslens/backend:latest   services/backend/
```
 
Verify images are available:
 
```bash
docker images | grep focuslens
```
 
### 8. Deploy services
 
```bash
kubectl apply -f k8s/services/ingestion.yaml
kubectl apply -f k8s/services/event.yaml
kubectl apply -f k8s/services/analytics.yaml
kubectl apply -f k8s/services/backend.yaml
```
 
Watch all pods come up:
 
```bash
kubectl get pods -n focuslens -w
```
 
All 7 pods should show Running:
 
```
analytics    Running
backend      Running
event        Running
ingestion    Running
postgres-0   Running
redis-0      Running
redpanda-0   Running
```
 
### 9. Expose services via port-forward
 
Since we are running minikube locally with the Docker driver, use port-forward to access services from your machine:
 
```bash
# expose backend API
kubectl port-forward svc/backend -n focuslens 8000:8000 &
 
# expose ingestion WebSocket
kubectl port-forward svc/ingestion -n focuslens 8001:8001 &
```
 
### 10. Verify the API is responding
 
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```
 
### 11. Start the edge agent
 
Open a new terminal with the focus conda environment:
 
```bash
conda activate focus
cd edge
python main.py
```
 
The edge agent opens your webcam and starts sending landmark data to the K8s ingestion service.
 
### 12. Verify data is flowing into K8s
 
```bash
kubectl logs -f deployment/event -n focuslens
# should show: [event] Saved frame 1 session xxxx focused=True
```
 
### 13. Query analytics
 
```bash
# get your session id
curl http://localhost:8000/api/latest-session
 
# get full session report
curl http://localhost:8000/api/sessions/{session_id} | python -m json.tool
```
 
### 14. Start frontend dashboard
 
```bash
cd frontend
nvm use 22
npm run dev
```
 
Open `http://localhost:3000`
 
---
 
## Rebuilding after code changes
 
When you change any service code, rebuild and redeploy:
 
```bash
eval $(minikube docker-env)
docker build -t focuslens/{service}:latest services/{service}/
kubectl rollout restart deployment {service} -n focuslens
 
# example — rebuild backend
docker build -t focuslens/backend:latest services/backend/
kubectl rollout restart deployment backend -n focuslens
```
 
---
 
## Service ports
 
| Service | Port | Notes |
|---|---|---|
| Frontend dashboard | 3000 | npm run dev |
| Backend API | 8000 | port-forwarded from K8s |
| Ingestion service | 8001 | port-forwarded from K8s |
| Analytics service | 8004 | internal K8s only |
| PostgreSQL | 5432 | internal K8s only |
| Redpanda (Kafka) | 9092 | internal K8s only |
| Redis | 6379 | internal K8s only |
 
---
 
## API endpoints
 
```bash
# health check
GET http://localhost:8000/health
 
# latest session id
GET http://localhost:8000/api/latest-session
 
# full session analytics report
GET http://localhost:8000/api/sessions/{session_id}
 
# list all sessions
GET http://localhost:8000/api/sessions
 
# live feed — last 60 frames
GET http://localhost:8000/api/live/{session_id}
```
 
---
 
## Useful kubectl commands
 
```bash
# see all pods
kubectl get pods -n focuslens
 
# see all pods across all namespaces
kubectl get pods -A
 
# logs for a service
kubectl logs -f deployment/backend -n focuslens
 
# restart a deployment
kubectl rollout restart deployment backend -n focuslens
 
# describe a pod (for debugging)
kubectl describe pod {pod-name} -n focuslens
 
# exec into a pod
kubectl exec -it {pod-name} -n focuslens -- /bin/bash
 
# exec into postgres
kubectl exec -it postgres-0 -n focuslens -- psql -U fl_user -d focuslens
 
# check recent focus events
kubectl exec -it postgres-0 -n focuslens -- psql -U fl_user -d focuslens \
  -c "SELECT session_id, ts, ear_avg, focused, gaze_zone FROM focus_events ORDER BY ts DESC LIMIT 10;"
```


# Post-Kubernetes Setup Guide

After you have set up Kubernetes and deployed your services, follow these steps to get everything running locally.

---

## 1. Start Minikube
```bash
minikube start  # ~30 seconds
````

---

## 2. Port-forward your services

This allows you to access them locally on your machine:

```bash
kubectl port-forward svc/backend -n focuslens 8000:8000 &
kubectl port-forward svc/ingestion -n focuslens 8001:8001 &
```

---

## 3. Start the frontend

```bash
cd frontend
npm run dev
```

---

## 4. Run the edge service

```bash
python edge/main.py
```

---

## Optional: Run everything with one script

You can run a `start_all.sh` script to automate all steps:

```bash
#!/bin/bash

# Start Minikube
minikube start

# Port-forward services
kubectl port-forward svc/backend -n focuslens 8000:8000 &
kubectl port-forward svc/ingestion -n focuslens 8001:8001 &

# Start frontend
(cd frontend && npm run dev) &

# Start edge service
python edge/main.py
```

Make it executable and run:

```bash
chmod +x start_all.sh
./start_all.sh
```

This will start Minikube, port-forward services, launch the frontend, and run `edge/main.py` all at once.





---
 
## ML roadmap
 
| Phase | Approach | Status |
|---|---|---|
| 1 | Rule-based classifier (EAR + head pose thresholds) | Done |
| 2 | CNN on face crops — MobileNetV3 fine-tuned | Planned |
| 3 | LSTM over 30-frame windows for temporal smoothing | Planned |
| 4 | Multimodal — vision + time-series fusion | Planned |
 
---
 
## Privacy
 
- Raw video frames are never stored anywhere
- MediaPipe runs locally on the edge device
- Only numerical feature vectors leave the edge process
- All data stays on your local machine
- No external API calls, no cloud storage
 