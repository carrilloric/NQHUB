#!/bin/bash
# Start all 4 ETL workers

echo "🚀 Starting 4 ETL workers..."

docker start nqhub_worker_1 nqhub_worker_2 nqhub_worker_3 nqhub_worker_4 2>/dev/null || {
    echo "Workers not created yet, creating them..."
    cd "$(dirname "$0")/.."
    docker run -d --name nqhub_worker_1 --network nqhub_v0_nqhub_network \
      -v "$(pwd)/backend:/app" \
      -v nqhub_v0_etl_temp:/tmp/etl_jobs \
      -e DATABASE_URL=postgresql://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e REDIS_URL=redis://nqhub_redis:6379 \
      -e ENVIRONMENT=development \
      --restart unless-stopped \
      nqhub_v0_worker-1:latest

    docker run -d --name nqhub_worker_2 --network nqhub_v0_nqhub_network \
      -v "$(pwd)/backend:/app" \
      -v nqhub_v0_etl_temp:/tmp/etl_jobs \
      -e DATABASE_URL=postgresql://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e REDIS_URL=redis://nqhub_redis:6379 \
      -e ENVIRONMENT=development \
      --restart unless-stopped \
      nqhub_v0_worker-2:latest

    docker run -d --name nqhub_worker_3 --network nqhub_v0_nqhub_network \
      -v "$(pwd)/backend:/app" \
      -v nqhub_v0_etl_temp:/tmp/etl_jobs \
      -e DATABASE_URL=postgresql://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e REDIS_URL=redis://nqhub_redis:6379 \
      -e ENVIRONMENT=development \
      --restart unless-stopped \
      nqhub_v0_worker-3:latest

    docker run -d --name nqhub_worker_4 --network nqhub_v0_nqhub_network \
      -v "$(pwd)/backend:/app" \
      -v nqhub_v0_etl_temp:/tmp/etl_jobs \
      -e DATABASE_URL=postgresql://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@nqhub_postgres:5432/nqhub \
      -e REDIS_URL=redis://nqhub_redis:6379 \
      -e ENVIRONMENT=development \
      --restart unless-stopped \
      nqhub_v0_worker-4:latest
}

sleep 2
echo ""
echo "📊 Worker Status:"
docker ps --filter "name=nqhub_worker" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Workers started. Check status at: http://localhost:8002/api/v1/etl/worker/status"
