#!/bin/bash
set -e

echo "🚀 Starting FocusLens..."

# Start infrastructure
docker compose up -d
echo "✅ Infrastructure ready"

# Wait for postgres to be healthy
until docker exec focuslens-ai-postgres-1 pg_isready -U fl_user -d focuslens 2>/dev/null; do
  sleep 1
done

# Init DB (idempotent)
cd services/ingestion && python init_db.py && cd ../..

# Start all backend services in background
uvicorn services.ingestion.main:app --host 0.0.0.0 --port 8001 &
python services/event/main.py &
uvicorn services.analytics.main:app --host 0.0.0.0 --port 8004 &
uvicorn services.backend.main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd frontend && npm run dev &

echo ""
echo "✅ FocusLens is running!"
echo "👉 Open http://localhost:3000 and click START"
wait