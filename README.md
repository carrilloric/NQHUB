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
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Neo4j Browser: http://localhost:7474
- RedisInsight: http://localhost:8001
- Mailpit (emails): http://localhost:8025
- Grafana: http://localhost:3001

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

## 📚 Documentation

- **[PROJECT_PLANv0.md](PROJECT_PLANv0.md)** - Complete project plan and architecture
- **[CLAUDE.md](CLAUDE.md)** - Claude Code guidance
- **[MIGRATION_PLAN.md](MIGRATION_PLAN.md)** - VM migration plan (coming soon)
- **[frontend/README.md](frontend/README.md)** - Frontend documentation
- **[backend/README.md](backend/README.md)** - Backend documentation

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
