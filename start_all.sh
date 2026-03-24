#!/bin/bash

# Start minikube
minikube start

# Port forward services
kubectl port-forward svc/backend -n focuslens 8000:8000 &
kubectl port-forward svc/ingestion -n focuslens 8001:8001 &

# Start frontend
(cd frontend && npm run dev) &

# Start edge/main.py
python edge/main.py