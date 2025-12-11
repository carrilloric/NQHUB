# NQHUB v0

Professional trading analytics platform for NQ Futures (Nasdaq 100 E-mini).

## 🏗️ Project Structure

```
nqhub/
├── frontend/          # React 18 + TypeScript + Vite
├── backend/           # Python + FastAPI + AI Engine
├── docker/            # Docker Compose configurations
├── infrastructure/    # Terraform + Ansible (IaC)
├── docs/              # Additional documentation
└── scripts/           # Development scripts
```

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **Python 3.11+**
- **Node.js 20+** & **pnpm**
- (Optional) **NVIDIA GPU** with CUDA 12.1+ for AI features

### Setup

1. **Clone and setup**:
```bash
git clone <repository>
cd NQHUB_v0
./scripts/dev_setup.sh
```

2. **Start development**:
```bash
./scripts/start_dev.sh
```

Or manually:
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
pnpm dev
```

3. **Access the application**:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8002
- API Docs: http://localhost:8002/api/docs
- PostgreSQL: localhost:5433 (Docker container `nqhub_postgres`)
- Neo4j Browser: http://localhost:7474
- RedisInsight: http://localhost:8001
- Mailpit (emails): http://localhost:8025

**Database Connections** (see [DATABASE_CONNECTIONS.md](DATABASE_CONNECTIONS.md) for details):
```bash
# NQHUB PostgreSQL + TimescaleDB
postgresql://nqhub:nqhub_password@localhost:5433/nqhub

# Connect via Docker
docker exec -it nqhub_postgres psql -U nqhub -d nqhub

# Redis
redis://localhost:6379/0

# Neo4j Bolt
bolt://neo4j:password@localhost:7687
```

**Note:** Port 5432 is reserved for legacy `nq_orderflow` database in another WSL instance.

## 📦 Tech Stack

### Frontend
- React 18, TypeScript, Vite
- TailwindCSS 3, Radix UI
- Zustand (state), TanStack Query
- SciChart (charting - trial mode)

### Backend
- Python 3.11, FastAPI
- **PostgreSQL + TimescaleDB** (historical time-series data)
- **Redis Stack** with TimeSeries, JSON, Search (real-time data & cache)
- **Neo4j** (knowledge graph)
- LangGraph, mem0, ElevenLabs (AI)

### Infrastructure
- Docker Compose
- Prometheus, Grafana, Loki (monitoring)
- Terraform, Ansible (deployment)

### Data Architecture

NQHUB uses a **dual-layer time-series architecture** optimized for both real-time performance and historical analysis:

**Real-time Layer (RedisTimeSeries)**
- Ultra-fast ingestion (~1M+ writes/sec)
- Live chart data (last 24-48 hours)
- In-memory aggregations
- Sub-millisecond query latency
- Auto-downsampling to TimescaleDB

**Historical Layer (TimescaleDB)**
- Long-term storage (years)
- Complex SQL queries
- Backtesting & analytics
- Automated compression
- Integration with PostgreSQL ecosystem

**Flow**: `Market Data → RedisTimeSeries (live) → Downsample → TimescaleDB (historical)`

### ETL Worker System

NQHUB uses **4 Docker-based RQ workers** for parallel ETL processing with automatic fault tolerance.

**Architecture**:
- 4 parallel workers processing Redis queue (`etl_queue`)
- Automatic restart on failure (`--restart unless-stopped`)
- Health checks every 30 seconds
- Graceful shutdown (SIGTERM/SIGINT handlers)
- Shared temp storage via bind mount (`/tmp/etl_jobs`)

**Quick Commands**:
```bash
# Start all 4 workers
./scripts/start_workers.sh

# Stop all workers
./scripts/stop_workers.sh

# Restart workers (e.g., after code changes)
./scripts/restart_workers.sh

# Monitor in real-time
./scripts/monitor_etl.sh --watch

# Check worker status via API
curl http://localhost:8002/api/v1/etl/worker/status
```

**Worker Status**:
- Each worker processes jobs independently from shared queue
- Supports parallel processing of multiple uploads
- Auto-reconnects to Redis if connection lost
- Detailed logging with job-specific context

See **[backend/ETL_PLAN.md](backend/ETL_PLAN.md)** for complete ETL system documentation.

## 📚 Documentation

### Project & Architecture
- **[PROJECT_PLANv0.md](PROJECT_PLANv0.md)** - Complete project plan and architecture
- **[CLAUDE.md](CLAUDE.md)** - Claude Code guidance
- **[MIGRATION_PLAN.md](MIGRATION_PLAN.md)** - VM migration plan (coming soon)

### Code Documentation
- **[frontend/README.md](frontend/README.md)** - Frontend documentation
- **[backend/README.md](backend/README.md)** - Backend documentation

### Database & ETL
- **[DATABASE_CONNECTIONS.md](DATABASE_CONNECTIONS.md)** - All database connection details and troubleshooting
- **[backend/DATABASE_SCHEMA.md](backend/DATABASE_SCHEMA.md)** - Complete PostgreSQL schema reference
- **[backend/ETL_PLAN.md](backend/ETL_PLAN.md)** - ETL system implementation plan

### Reference Data
- **[_reference/docs/README.md](_reference/docs/README.md)** - Legacy data and documentation index
- **[_reference/docs/DATA_DICTIONARY.md](_reference/docs/DATA_DICTIONARY.md)** - NQ Futures data structure guide
- **[_reference/docs/LEGACY_DATABASE_SCHEMA.md](_reference/docs/LEGACY_DATABASE_SCHEMA.md)** - Legacy system analysis

## 🔧 Development

### Docker Services

```bash
# Start main services
cd docker
docker-compose up -d

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# View logs
docker-compose logs -f postgres redis neo4j
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
pnpm test
```

## 🎯 Features

### Current (v0)
- ✅ Project structure with frontend/backend separation
- ✅ Docker Compose with all services
- ✅ FastAPI backend with multi-LLM configuration
- ✅ Monitoring stack (Grafana + Prometheus + Loki)
- ✅ Development scripts

### In Development
- 🚧 Authentication system (JWT + invitations)
- 🚧 AI Assistant with LangGraph
- 🚧 Data ingestion and charting
- 🚧 Real-time WebSocket
- 🚧 Voice integration (ElevenLabs)

### Planned
- 📋 Admin panel for superusers
- 📋 ETL pipeline monitoring
- 📋 SciChart integration (production)
- 📋 Deployment to cloud VM

## 🔐 Environment Variables

Copy `.env.example` files and configure:
```bash
cp backend/.env.example backend/.env
cp docker/.env.example docker/.env
```

Required variables:
- Database passwords
- JWT secret key
- LLM API keys (OpenAI, Anthropic, Groq)
- ElevenLabs API key (for voice features)

## 🚢 Deployment

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for deployment to cloud VM with Terraform and Ansible.

## 🤝 Contributing

This is currently a private development project.

## 📄 License

Proprietary - All rights reserved

## 📞 Support

For issues or questions, refer to the documentation in the `docs/` directory.
