#!/bin/bash

# Force Start Workers Script
# This script forcefully restarts all ETL workers to ensure job processing
# Addresses the frequent worker stopping issues

set -e

echo "==================================================="
echo "NQHUB ETL Workers - Force Start Script"
echo "==================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Step 1: Stopping all existing workers...${NC}"
# Kill any running worker processes
pkill -f "python.*worker.py" 2>/dev/null || true

# Stop and remove docker containers
docker ps -a | grep "nqhub_worker" | awk '{print $1}' | xargs -r docker stop 2>/dev/null || true
docker ps -a | grep "nqhub_worker" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

echo -e "${GREEN}✓ All workers stopped${NC}"
echo ""

echo -e "${YELLOW}Step 2: Verifying dependencies...${NC}"

# Check PostgreSQL
if docker ps | grep -q nqhub_postgres; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running. Starting...${NC}"
    docker start nqhub_postgres
    sleep 3
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running. Please start Redis first!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Clearing any stuck jobs from Redis...${NC}"
# Clear failed queue to prevent blocking
redis-cli -n 0 DEL rq:failed:default 2>/dev/null || true
echo -e "${GREEN}✓ Redis queues cleared${NC}"

echo ""
echo -e "${YELLOW}Step 4: Ensuring containers are on correct network...${NC}"

# Check if Redis is on docker_nqhub_network (legacy network)
REDIS_NETWORK=$(docker inspect nqhub_redis --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' | head -1)
if [ "$REDIS_NETWORK" == "docker_nqhub_network" ]; then
    echo -e "${GREEN}✓ Redis is on docker_nqhub_network${NC}"
    # Ensure PostgreSQL is also on this network
    docker network connect docker_nqhub_network nqhub_postgres 2>/dev/null || true
    NETWORK_TO_USE="docker_nqhub_network"
else
    echo -e "${YELLOW}Redis is on network: $REDIS_NETWORK${NC}"
    NETWORK_TO_USE="$REDIS_NETWORK"
fi

echo ""
echo -e "${YELLOW}Step 5: Starting workers on network $NETWORK_TO_USE...${NC}"

cd "$PROJECT_ROOT"

# Start workers directly with docker run on the correct network
for i in 1 2 3 4; do
  docker run -d \
    --name nqhub_worker_$i \
    --network "$NETWORK_TO_USE" \
    -e DATABASE_URL="postgresql://nqhub:nqhub_password@nqhub_postgres:5432/nqhub" \
    -e DATABASE_URL_ASYNC="postgresql+asyncpg://nqhub:nqhub_password@nqhub_postgres:5432/nqhub" \
    -e REDIS_URL="redis://nqhub_redis:6379" \
    -e ENVIRONMENT="development" \
    -v "$PROJECT_ROOT:/app" \
    -v /tmp/etl_jobs:/tmp/etl_jobs \
    nqhub_v0_worker-$i:latest \
  && echo -e "${GREEN}✓ Started worker $i${NC}" \
  || echo -e "${RED}✗ Failed to start worker $i${NC}"
done

echo ""
echo -e "${YELLOW}Step 6: Verifying worker status...${NC}"
sleep 5

# Check if workers are running
WORKERS_RUNNING=0
for i in 1 2 3 4; do
    if docker ps | grep -q "nqhub_worker_$i"; then
        echo -e "${GREEN}✓ Worker $i is running${NC}"
        WORKERS_RUNNING=$((WORKERS_RUNNING + 1))
    else
        echo -e "${RED}✗ Worker $i failed to start${NC}"
    fi
done

echo ""
if [ $WORKERS_RUNNING -eq 0 ]; then
    echo -e "${RED}ERROR: No workers are running!${NC}"
    echo "Checking docker logs..."
    docker-compose logs worker-1 2>&1 | tail -10
    exit 1
elif [ $WORKERS_RUNNING -lt 4 ]; then
    echo -e "${YELLOW}WARNING: Only $WORKERS_RUNNING of 4 workers are running${NC}"
else
    echo -e "${GREEN}SUCCESS: All $WORKERS_RUNNING workers are running${NC}"
fi

echo ""
echo -e "${YELLOW}Step 7: Checking for pending jobs...${NC}"

# Check Redis for pending jobs
PENDING_JOBS=$(redis-cli -n 0 LLEN rq:queue:default 2>/dev/null || echo 0)
if [ "$PENDING_JOBS" -gt 0 ]; then
    echo -e "${GREEN}Found $PENDING_JOBS pending jobs in queue${NC}"
    echo "Jobs should start processing now..."
else
    echo "No pending jobs found"
fi

echo ""
echo "==================================================="
echo -e "${GREEN}Worker restart complete!${NC}"
echo "==================================================="
echo ""
echo "Monitor workers with:"
echo "  docker-compose logs -f worker-1"
echo "  docker ps | grep nqhub_worker"
echo ""
echo "Check job status with:"
echo "  redis-cli -n 0 LLEN rq:queue:default  # Pending jobs"
echo "  redis-cli -n 0 LLEN rq:failed:default # Failed jobs"
echo ""