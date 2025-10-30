#!/bin/bash
set -e

echo "🚀 Setting up NQHUB development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "PROJECT_PLANv0.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Start Docker services
echo ""
echo "${YELLOW}📦 Starting Docker services...${NC}"
cd docker
docker-compose up -d postgres redis neo4j mailpit
cd ..

echo "${GREEN}✅ Docker services started${NC}"

# Wait for PostgreSQL to be ready
echo ""
echo "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 10
until docker exec nqhub_postgres pg_isready -U nqhub > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "${GREEN}✅ PostgreSQL is ready${NC}"

# Backend setup
echo ""
echo "${YELLOW}🐍 Setting up Python backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-ai.txt

echo "${GREEN}✅ Python dependencies installed${NC}"

# Run migrations
echo ""
echo "${YELLOW}🗄️  Running database migrations...${NC}"
alembic upgrade head
echo "${GREEN}✅ Migrations complete${NC}"

# Create superuser
echo ""
echo "${YELLOW}👤 Creating superuser...${NC}"
python scripts/init_superuser.py || echo "Superuser may already exist"
echo "${GREEN}✅ Superuser setup complete${NC}"

cd ..

# Frontend setup
echo ""
echo "${YELLOW}⚛️  Setting up React frontend...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    pnpm install
else
    echo "node_modules already exists, skipping install"
fi

echo "${GREEN}✅ Frontend dependencies ready${NC}"

cd ..

# Summary
echo ""
echo "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && pnpm dev"
echo ""
echo "Or use: ./scripts/start_dev.sh"
echo ""
echo "Services running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Mailpit UI: http://localhost:8025"
