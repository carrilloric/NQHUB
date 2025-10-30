#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}🚀 Starting NQHUB Development Environment${NC}"
echo ""

# Check if Docker services are running
if ! docker ps | grep -q nqhub_postgres; then
    echo "${YELLOW}Starting Docker services...${NC}"
    cd docker
    docker-compose up -d postgres redis neo4j mailpit
    cd ..
    sleep 5
fi

echo "${GREEN}✅ Docker services are running${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "${YELLOW}Shutting down...${NC}"
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo "${BLUE}Starting Backend (port 8000)...${NC}"
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "${BLUE}Starting Frontend (port 3000)...${NC}"
cd frontend
pnpm dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "${GREEN}✅ Development servers started!${NC}"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Backend Docs: http://localhost:8000/api/docs"
echo "  - Frontend: http://localhost:3000"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Neo4j: http://localhost:7474"
echo "  - Mailpit: http://localhost:8025"
echo ""
echo "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for background processes
wait
