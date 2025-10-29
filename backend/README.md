# NQHUB Backend

Python/FastAPI backend for NQHUB Trading Analytics Platform.

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL + TimescaleDB
- **Cache**: Redis
- **Knowledge Graph**: Neo4j
- **AI**: LangGraph + mem0 + ElevenLabs
- **Task Queue**: Celery
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with TimescaleDB
- Redis 7+
- Neo4j 5.15+
- (Optional) NVIDIA GPU with CUDA 12.1+ for AI worker

### Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-ai.txt
```

3. For GPU support (AI worker):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

4. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your values
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Create superuser:
```bash
python scripts/init_superuser.py
```

## Development

### Run the server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --port 8000

# Or using Python directly
python -m app.main
```

### Run tests

```bash
pytest
pytest -v  # Verbose
pytest tests/test_auth.py  # Specific test file
```

### Database migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

### Code formatting

```bash
# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/
```

## Project Structure

```
app/
├── ai_engine/          # AI Engine (LangGraph, mem0, ElevenLabs)
│   ├── core/          # Engine core
│   ├── langgraph/     # LangGraph graphs and nodes
│   ├── memory/        # Memory management (mem0 + Neo4j)
│   ├── voice/         # Voice integration
│   ├── prompts/       # System prompts
│   └── tools/         # Agent tools
├── api/               # API endpoints
│   └── v1/           # API v1
├── core/              # Core business logic
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
├── services/          # Business logic services
├── db/                # Database utilities
└── utils/             # Utilities
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `NEO4J_URI`: Neo4j Bolt connection string
- `SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`: LLM API keys
- `ELEVENLABS_API_KEY`: Voice API key

## Docker

See `../docker/` for Docker configurations.

```bash
# From project root
docker-compose up backend

# With AI worker (requires GPU)
docker-compose up backend ai_worker
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_login -v
```

## Deployment

See `PROJECT_PLANv0.md` and `MIGRATION_PLAN.md` for deployment instructions.
