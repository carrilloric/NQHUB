# NQHUB v0 - Plan Completo de Reestructuración e Implementación

**Fecha**: 2025-10-29
**Versión**: v0.1
**Estado**: En desarrollo (WSL)

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Estructura de Directorios](#estructura-de-directorios)
5. [Servicios Docker](#servicios-docker)
6. [Sistema de Autenticación](#sistema-de-autenticación)
7. [Motor de IA Centralizado](#motor-de-ia-centralizado)
8. [Observabilidad](#observabilidad)
9. [Plan de Migración a VM](#plan-de-migración-a-vm)
10. [Infraestructura como Código](#infraestructura-como-código)
11. [Plan de Implementación](#plan-de-implementación)
12. [Variables de Entorno](#variables-de-entorno)
13. [Comandos de Desarrollo](#comandos-de-desarrollo)

---

## Visión General

NQHUB es una plataforma profesional de análisis de trading para futuros de NQ (Nasdaq 100 E-mini). El sistema incluye:

- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: Python + FastAPI
- **Charting**: SciChart (trial mode)
- **AI Assistant**: LangGraph + mem0 + ElevenLabs (voice-to-voice)
- **Knowledge Base**: Neo4j para grafos de conocimiento
- **Databases**: PostgreSQL + TimescaleDB (time-series) + Redis (cache/sessions)
- **Observabilidad**: Grafana + Loki + Prometheus
- **IaC**: Terraform + Ansible para migración a VM

---

## Arquitectura del Sistema

```
┌───────────────────────────────────────────────────────────────────────┐
│                           NQHUB v0 ARCHITECTURE                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐       ┌───────────────┐        ┌─────────────────┐ │
│  │   Frontend   │◄─────►│    Backend    │◄──────►│    Databases    │ │
│  │   (React)    │       │   (FastAPI)   │        │                 │ │
│  │              │       │               │        │  • PostgreSQL   │ │
│  │  Port 3000   │       │   Port 8000   │        │  • TimescaleDB  │ │
│  │              │       │               │        │  • Redis        │ │
│  │  • Charts    │       │  • Auth       │        │  • Neo4j        │ │
│  │  • Data Viz  │       │  • AI Engine  │        │                 │ │
│  │  • AI Chat   │       │  • WebSocket  │        └─────────────────┘ │
│  └──────────────┘       │  • ETL        │                            │
│         ▲               └───────────────┘                            │
│         │                      ▲                                     │
│         │                      │                                     │
│         │               ┌──────┴──────┐                             │
│         │               │  AI Worker  │ ◄── GPU (CUDA + PyTorch)    │
│         │               │  (Separate) │                             │
│         │               └─────────────┘                             │
│         │                                                            │
│  ┌──────┴────────────────────────────────────────────────────────┐  │
│  │                    Monitoring Stack                            │  │
│  │  Prometheus → Grafana ← Loki ← Promtail                       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│         ▲                                                             │
│         └──────── ngrok (exposición inicial) ────────────            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| React | 18.3.1 | UI Framework |
| TypeScript | 5.9.2 | Type safety |
| Vite | 7.1.2 | Build tool |
| React Router | 6.30.1 | Routing |
| TailwindCSS | 3.4.17 | Styling |
| Radix UI | Latest | UI Components |
| Zustand | 5.0.8 | State management (business logic) |
| React Context | Built-in | State management (infrastructure) |
| TanStack Query | 5.84.2 | Server state |
| SciChart | Trial | Professional charting |
| Vitest | 3.2.4 | Testing |

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.11+ | Language |
| FastAPI | 0.109.0+ | Web framework |
| Uvicorn | 0.27.0+ | ASGI server |
| SQLAlchemy | 2.0.25+ | ORM |
| Alembic | 1.13.1+ | Migrations |
| Pydantic | 2.5.3+ | Data validation |
| python-jose | 3.3.0+ | JWT |
| bcrypt | 4.1.2+ | Password hashing |
| Celery | 5.3.6+ | Task queue |
| WebSockets | 12.0+ | Real-time communication |

### AI/ML Stack

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| LangGraph | 0.0.20+ | AI orchestration |
| LangChain | 0.1.0+ | LLM framework |
| mem0 | 0.0.7+ | AI memory |
| OpenAI | Latest | LLM provider (GPT-4) |
| Anthropic | Latest | LLM provider (Claude) |
| Llama | 3.1 | LLM provider (local/Groq) |
| ElevenLabs | 0.2.27+ | Voice-to-voice |
| PyTorch | 2.1.0+ | ML framework |
| CUDA | 12.1+ | GPU acceleration |

### Databases

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| PostgreSQL | 15+ | Main database |
| TimescaleDB | Latest | Time-series data |
| Redis | 7+ | Cache, sessions, pub/sub |
| Neo4j | 5.15+ | Knowledge graph |

### Observabilidad

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Prometheus | Latest | Metrics collection |
| Grafana | Latest | Visualization |
| Loki | Latest | Log aggregation |
| Promtail | Latest | Log collection |

### Infraestructura

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Docker | 24.0+ | Containerization |
| Docker Compose | 2.23+ | Multi-container orchestration |
| Terraform | 1.6+ | Infrastructure provisioning |
| Ansible | 2.16+ | Configuration management |
| nginx | Latest | Reverse proxy |
| ngrok | Latest | Development exposure |

---

## Estructura de Directorios

```
nqhub/
├── frontend/                          # React SPA Frontend
│   ├── src/
│   │   ├── client/                   # (código actual de client/)
│   │   │   ├── pages/               # Route components
│   │   │   │   ├── Index.tsx       # Landing page
│   │   │   │   ├── Dashboard.tsx   # Main dashboard
│   │   │   │   ├── DataModule.tsx  # Data analytics
│   │   │   │   ├── Register.tsx    # Registration with invite
│   │   │   │   ├── AdminPanel.tsx  # Superuser admin
│   │   │   │   └── ...
│   │   │   ├── components/
│   │   │   │   ├── ui/             # Radix-based components
│   │   │   │   ├── layout/         # TopNavbar, Sidebar
│   │   │   │   ├── data-module/    # Data module components
│   │   │   │   │   ├── charts/     # Chart components
│   │   │   │   │   ├── indicators/ # Indicator management
│   │   │   │   │   └── etl/        # ETL dashboard
│   │   │   │   ├── ai-assistant/   # AI Assistant components
│   │   │   │   │   ├── ChatPanel.tsx
│   │   │   │   │   ├── LLMSelector.tsx
│   │   │   │   │   ├── VoiceControls.tsx
│   │   │   │   │   └── AudioVisualizer.tsx
│   │   │   │   ├── admin/          # Admin components
│   │   │   │   │   ├── InvitationManager.tsx
│   │   │   │   │   └── UserManagement.tsx
│   │   │   │   ├── auth/           # Auth components
│   │   │   │   │   └── ProtectedRoute.tsx
│   │   │   │   └── common/         # Shared components
│   │   │   ├── state/
│   │   │   │   ├── app.tsx         # Global state (Context)
│   │   │   │   ├── data-module.store.ts  # Data module (Zustand)
│   │   │   │   └── websocket.store.ts    # WebSocket state
│   │   │   ├── services/
│   │   │   │   ├── api-client.ts   # API client with JWT
│   │   │   │   ├── websocket.ts    # Resilient WebSocket
│   │   │   │   └── ai-engine.service.ts  # AI service
│   │   │   ├── lib/                # Utilities
│   │   │   ├── locales/            # i18n (en.json, es.json)
│   │   │   ├── App.tsx             # App entry + routing
│   │   │   └── global.css          # TailwindCSS globals
│   │   └── shared/                 # (código actual de shared/)
│   │       ├── api.ts              # Shared API types
│   │       └── mock-data.ts        # Mock data (to replace)
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .prettierrc
│   └── README.md
│
├── backend/                          # Python/FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Configuration
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   │
│   │   ├── ai_engine/              # ⭐ MOTOR CENTRAL DE IA
│   │   │   ├── __init__.py
│   │   │   ├── core/               # Core del motor
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py      # AIEngine singleton
│   │   │   │   ├── context.py     # Context types
│   │   │   │   └── config.py      # Multi-LLM config
│   │   │   ├── langgraph/         # LangGraph orchestration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── graph_builder.py  # Graph factory
│   │   │   │   ├── nodes/         # Reusable nodes
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── analysis.py
│   │   │   │   │   ├── trading.py
│   │   │   │   │   ├── charts.py
│   │   │   │   │   └── general.py
│   │   │   │   └── graphs/        # Context-specific graphs
│   │   │   │       ├── __init__.py
│   │   │   │       ├── chat_graph.py
│   │   │   │       ├── chart_graph.py
│   │   │   │       └── data_graph.py
│   │   │   ├── memory/            # Memory management
│   │   │   │   ├── __init__.py
│   │   │   │   ├── memory_manager.py
│   │   │   │   └── adapters/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── mem0_adapter.py    # Conversational
│   │   │   │       └── neo4j_adapter.py   # Knowledge graph
│   │   │   ├── voice/             # ElevenLabs integration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── voice_engine.py
│   │   │   │   ├── audio_processor.py
│   │   │   │   └── stream_handler.py
│   │   │   ├── prompts/           # System prompts
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── chart_analysis.py
│   │   │   │   └── trading_advisor.py
│   │   │   └── tools/             # Agent tools
│   │   │       ├── __init__.py
│   │   │       ├── chart_tools.py
│   │   │       ├── data_tools.py
│   │   │       └── market_tools.py
│   │   │
│   │   ├── api/                   # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py        # Login, register, JWT
│   │   │   │   ├── users.py       # User management
│   │   │   │   ├── admin.py       # Admin endpoints
│   │   │   │   ├── invitations.py # Invitation system
│   │   │   │   ├── charts.py      # Chart data
│   │   │   │   ├── etl.py         # ETL pipeline
│   │   │   │   ├── ai.py          # AI general endpoints
│   │   │   │   ├── ai_chat.py     # AI chat
│   │   │   │   ├── ai_chart_analysis.py  # Chart analysis
│   │   │   │   ├── ai_voice.py    # Voice endpoints
│   │   │   │   └── websocket.py   # WebSocket endpoints
│   │   │   └── deps.py            # Route dependencies
│   │   │
│   │   ├── core/                  # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py        # JWT, password hashing
│   │   │   ├── permissions.py     # RBAC
│   │   │   └── invitations.py     # Invitation logic
│   │   │
│   │   ├── models/                # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # User, Role
│   │   │   ├── invitation.py      # Invitation tokens
│   │   │   ├── session.py         # User sessions
│   │   │   ├── trading.py         # OHLCV, Indicators
│   │   │   └── etl.py             # DataSource, ETLJob
│   │   │
│   │   ├── schemas/               # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Login, Register, Token
│   │   │   ├── user.py            # User schemas
│   │   │   ├── invitation.py      # Invitation schemas
│   │   │   ├── chart.py           # Chart data schemas
│   │   │   └── ai.py              # AI request/response schemas
│   │   │
│   │   ├── services/              # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py    # Auth operations
│   │   │   ├── user_service.py    # User CRUD
│   │   │   ├── chart_service.py   # Chart data
│   │   │   ├── etl_service.py     # ETL operations
│   │   │   ├── cache_service.py   # Redis operations
│   │   │   ├── websocket_manager.py  # WebSocket connections
│   │   │   └── ai_service.py      # AI service layer
│   │   │
│   │   ├── db/                    # Database utilities
│   │   │   ├── __init__.py
│   │   │   ├── session.py         # SQLAlchemy session
│   │   │   ├── base.py            # Base model
│   │   │   └── init_db.py         # DB initialization
│   │   │
│   │   └── utils/                 # Utilities
│   │       ├── __init__.py
│   │       ├── email.py           # Email sending
│   │       └── validators.py      # Custom validators
│   │
│   ├── alembic/                   # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── tests/                     # pytest tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_ai_engine.py
│   │   └── ...
│   │
│   ├── scripts/                   # Utility scripts
│   │   ├── init_superuser.py      # Create first superuser
│   │   ├── generate_invitation.py # Generate invitation
│   │   ├── check_gpu.sh           # Verify GPU/CUDA
│   │   └── export_data.sh         # Export data for migration
│   │
│   ├── requirements.txt           # Python dependencies
│   ├── requirements-dev.txt       # Dev dependencies
│   ├── requirements-ai.txt        # AI/GPU dependencies
│   ├── pyproject.toml             # Project config
│   ├── .env.example               # Environment variables
│   └── README.md
│
├── docker/                        # Docker configurations
│   ├── docker-compose.yml         # Main services
│   ├── docker-compose.dev.yml     # Dev overrides
│   ├── docker-compose.monitoring.yml  # Observability stack
│   ├── Dockerfile.backend         # Backend image
│   ├── Dockerfile.ai-gpu          # AI worker with CUDA
│   ├── Dockerfile.frontend        # Frontend image (prod)
│   ├── postgres/
│   │   └── init.sql               # PostgreSQL + TimescaleDB init
│   ├── neo4j/
│   │   └── neo4j.conf             # Neo4j config
│   ├── prometheus/
│   │   └── prometheus.yml         # Prometheus config
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── system.json
│   │   │   ├── api.json
│   │   │   ├── websocket.json
│   │   │   ├── ai_engine.json
│   │   │   └── database.json
│   │   └── provisioning/
│   ├── loki/
│   │   └── loki-config.yml
│   ├── promtail/
│   │   └── promtail-config.yml
│   └── nginx/
│       └── nginx.conf             # Reverse proxy config
│
├── infrastructure/                # Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── modules/
│   │   │   ├── compute/
│   │   │   │   ├── main.tf
│   │   │   │   └── variables.tf
│   │   │   ├── networking/
│   │   │   │   ├── main.tf
│   │   │   │   └── variables.tf
│   │   │   └── storage/
│   │   │       ├── main.tf
│   │   │       └── variables.tf
│   │   └── environments/
│   │       ├── dev/
│   │       │   ├── main.tf
│   │       │   └── terraform.tfvars
│   │       └── production/
│   │           ├── main.tf
│   │           └── terraform.tfvars
│   │
│   ├── ansible/
│   │   ├── playbooks/
│   │   │   ├── setup.yml          # Initial server setup
│   │   │   ├── deploy.yml         # Deploy application
│   │   │   ├── update.yml         # Update application
│   │   │   └── backup.yml         # Backup procedures
│   │   ├── roles/
│   │   │   ├── docker/
│   │   │   │   └── tasks/main.yml
│   │   │   ├── nvidia/
│   │   │   │   └── tasks/main.yml
│   │   │   ├── monitoring/
│   │   │   │   └── tasks/main.yml
│   │   │   └── nqhub/
│   │   │       └── tasks/main.yml
│   │   └── inventory/
│   │       ├── dev.ini
│   │       └── production.ini
│   │
│   └── README.md
│
├── docs/                          # Additional documentation
│   ├── API.md                     # API documentation
│   ├── DEPLOYMENT.md              # Deployment guide
│   ├── DEVELOPMENT.md             # Development guide
│   ├── OBSERVABILITY.md           # Monitoring guide
│   └── MIGRATION.md               # Migration procedures
│
├── scripts/                       # Project-level scripts
│   ├── dev_setup.sh               # Complete dev setup
│   ├── start_dev.sh               # Start development
│   └── deploy.sh                  # Deployment script
│
├── .gitignore
├── README.md                      # Main project README
├── CLAUDE.md                      # Claude Code guidance
├── PROJECT_PLAN.md                # Original plan (archived)
├── PROJECT_PLANv0.md              # This document (current plan)
├── MIGRATION_PLAN.md              # VM migration plan (living doc)
├── AGENTS.md                      # Agent descriptions
├── DATA_MODULE_STRUCTURE.md       # Data module architecture
└── SCICHART_SETUP.md              # SciChart integration guide
```

---

## Servicios Docker

### docker-compose.yml - Servicios Principales

```yaml
version: '3.8'

services:
  # ==================== DATABASES ====================

  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: nqhub_postgres
    environment:
      POSTGRES_USER: nqhub
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: nqhub
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - nqhub_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nqhub"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: nqhub_redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - nqhub_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5.15-community
    container_name: nqhub_neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_memory_heap_initial__size: 512m
      NEO4J_dbms_memory_heap_max__size: 2G
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_plugins:/plugins
    networks:
      - nqhub_network
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p ${NEO4J_PASSWORD} 'RETURN 1'"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ==================== BACKEND ====================

  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    container_name: nqhub_backend
    environment:
      DATABASE_URL: postgresql://nqhub:${POSTGRES_PASSWORD}@postgres:5432/nqhub
      REDIS_URL: redis://redis:6379
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: development
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      GROQ_API_KEY: ${GROQ_API_KEY}
      ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY}
      MEM0_API_KEY: ${MEM0_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - backend_logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      neo4j:
        condition: service_healthy
    networks:
      - nqhub_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  ai_worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.ai-gpu
    container_name: nqhub_ai_worker
    environment:
      DATABASE_URL: postgresql://nqhub:${POSTGRES_PASSWORD}@postgres:5432/nqhub
      REDIS_URL: redis://redis:6379
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      NVIDIA_VISIBLE_DEVICES: all
      CUDA_VISIBLE_DEVICES: 0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      GROQ_API_KEY: ${GROQ_API_KEY}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    runtime: nvidia
    depends_on:
      - redis
      - neo4j
    networks:
      - nqhub_network
    command: python -m app.ai_engine.worker

  celery_worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    container_name: nqhub_celery_worker
    environment:
      DATABASE_URL: postgresql://nqhub:${POSTGRES_PASSWORD}@postgres:5432/nqhub
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - nqhub_network
    command: celery -A app.celery worker --loglevel=info

  celery_beat:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    container_name: nqhub_celery_beat
    environment:
      DATABASE_URL: postgresql://nqhub:${POSTGRES_PASSWORD}@postgres:5432/nqhub
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - nqhub_network
    command: celery -A app.celery beat --loglevel=info

  # ==================== FRONTEND ====================

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    container_name: nqhub_frontend
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_WS_URL: ws://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    networks:
      - nqhub_network
    command: pnpm dev --host

  # ==================== UTILITIES ====================

  mailpit:
    image: axllent/mailpit:latest
    container_name: nqhub_mailpit
    ports:
      - "8025:8025"  # Web UI
      - "1025:1025"  # SMTP
    networks:
      - nqhub_network

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  neo4j_logs:
  neo4j_plugins:
  backend_logs:

networks:
  nqhub_network:
    driver: bridge
```

### docker-compose.monitoring.yml - Stack de Observabilidad

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: nqhub_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - nqhub_network

  grafana:
    image: grafana/grafana:latest
    container_name: nqhub_grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./docker/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
      - loki
    networks:
      - nqhub_network

  loki:
    image: grafana/loki:latest
    container_name: nqhub_loki
    ports:
      - "3100:3100"
    volumes:
      - ./docker/loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - nqhub_network

  promtail:
    image: grafana/promtail:latest
    container_name: nqhub_promtail
    volumes:
      - ./docker/promtail/promtail-config.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - ./backend/logs:/app/backend/logs:ro
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
    networks:
      - nqhub_network

volumes:
  prometheus_data:
  grafana_data:
  loki_data:

networks:
  nqhub_network:
    external: true
```

---

## Sistema de Autenticación

### Roles

1. **superuser**
   - Acceso completo al sistema
   - Genera invitaciones
   - Gestiona usuarios
   - Acceso a configuraciones avanzadas
   - Panel de administración

2. **trader**
   - Acceso a charts y análisis
   - Acceso a módulo de datos
   - Uso del AI Assistant
   - Sin permisos administrativos

### Flujo de Invitación

```
1. Superuser → Genera invitación desde Admin Panel
   ↓
2. Backend → POST /api/v1/admin/invitations
   - Crea token UUID único
   - Define rol (trader/superuser)
   - Expiración: 7 días
   - Guarda en DB
   ↓
3. URL generada → https://nqhub.ngrok.io/register?token=xxx
   ↓
4. Nuevo usuario → Accede a URL
   ↓
5. Frontend → Valida token con backend
   - GET /api/v1/invitations/validate/{token}
   ↓
6. Usuario completa registro
   - Email, password, first_name, last_name
   ↓
7. Backend → POST /api/v1/auth/register
   - Valida token no usado/expirado
   - Crea usuario con rol
   - Marca invitación como usada
   - Retorna JWT token
   ↓
8. Auto-login → Dashboard
```

### Modelos de Base de Datos

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL,  -- 'superuser' | 'trader'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);
```

#### invitations
```sql
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),  -- Optional pre-assign
    role VARCHAR(50) NOT NULL DEFAULT 'trader',
    invited_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    used_by UUID REFERENCES users(id)
);
```

#### sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT false
);
```

---

## Motor de IA Centralizado

### Arquitectura

El motor de IA es un **servicio centralizado** (singleton) utilizado en múltiples partes de la aplicación.

### Contextos de Uso

```python
ContextType = Literal[
    "chat",              # Chat general
    "chart_analysis",    # Análisis de charts
    "data_module",       # Módulo de datos
    "trading",           # Sugerencias de trading
    "general"            # Contexto genérico
]
```

### Proveedores de LLM

El sistema soporta **3 proveedores** seleccionables por el usuario:

1. **OpenAI**
   - GPT-4-turbo
   - GPT-4
   - GPT-3.5-turbo

2. **Anthropic**
   - Claude 3.5 Sonnet
   - Claude 3 Opus
   - Claude 3 Sonnet

3. **Llama**
   - Llama 3.1 70B (Groq API)
   - Llama 3.1 8B (Local/Ollama)

### Componentes del Motor

#### AIEngine (Singleton)

```python
class AIEngine:
    """Motor central de IA"""

    def __init__(self):
        self.langgraph_builder = GraphBuilder()
        self.memory_manager = MemoryManager()
        self.voice_engine = VoiceEngine()

    async def process_message(
        self,
        message: str,
        user_id: str,
        context: ContextType,
        context_data: dict = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4-turbo"
    ):
        # Seleccionar LLM
        llm = self._get_llm(llm_provider, llm_model)

        # Seleccionar graph según contexto
        graph = self.langgraph_builder.get_graph(context, llm)

        # Cargar memoria
        memory = await self.memory_manager.get_memory(user_id, context)

        # Ejecutar
        result = await graph.ainvoke({
            "message": message,
            "user_id": user_id,
            "context": context,
            "context_data": context_data,
            "memory": memory
        })

        # Guardar memoria
        await self.memory_manager.save_interaction(
            user_id, context, message, result["response"]
        )

        return result
```

#### Memory Manager

**Dual Memory System**:
- **mem0**: Memoria conversacional (short-term)
- **Neo4j**: Knowledge graph (long-term, structured)

```python
class MemoryManager:
    def __init__(self):
        self.mem0_adapter = Mem0Adapter()
        self.neo4j_adapter = Neo4jAdapter()

    async def get_memory(self, user_id: str, context: str):
        # Conversational memory
        recent = await self.mem0_adapter.get_recent(user_id, context)

        # Knowledge graph context
        knowledge = await self.neo4j_adapter.get_relevant_knowledge(
            user_id, context
        )

        return {
            "recent": recent,
            "knowledge": knowledge
        }
```

#### Voice Engine

```python
class VoiceEngine:
    def __init__(self):
        self.elevenlabs_client = ElevenLabsClient()

    async def transcribe(self, audio_data: bytes) -> str:
        """Speech-to-text"""
        return await self.elevenlabs_client.transcribe(audio_data)

    async def synthesize(self, text: str) -> bytes:
        """Text-to-speech"""
        return await self.elevenlabs_client.synthesize(text)
```

### Frontend Integration

#### LLM Selector Component

```typescript
interface LLMSelectorProps {
  value: string;  // "provider:model" e.g. "openai:gpt-4-turbo"
  onChange: (value: string) => void;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ value, onChange }) => {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger>
        <Brain className="w-4 h-4" />
        <span>{getModelDisplayName(value)}</span>
      </SelectTrigger>
      <SelectContent>
        <SelectGroup label="OpenAI">
          <SelectItem value="openai:gpt-4-turbo">
            GPT-4 Turbo
          </SelectItem>
          <SelectItem value="openai:gpt-4">
            GPT-4
          </SelectItem>
        </SelectGroup>
        <SelectGroup label="Anthropic">
          <SelectItem value="anthropic:claude-3-5-sonnet-20241022">
            Claude 3.5 Sonnet
          </SelectItem>
          <SelectItem value="anthropic:claude-3-opus-20240229">
            Claude 3 Opus
          </SelectItem>
        </SelectGroup>
        <SelectGroup label="Llama">
          <SelectItem value="llama:llama-3.1-70b">
            Llama 3.1 70B (Groq)
          </SelectItem>
          <SelectItem value="llama:llama-3.1-8b">
            Llama 3.1 8B (Local)
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
};
```

#### AI Service

```typescript
class AIEngineService {
  async sendMessage(
    message: string,
    context: AIContext,
    contextData?: any,
    llmProvider?: string,
    llmModel?: string
  ): Promise<AIResponse> {
    return this.apiClient.post('/api/v1/ai/message', {
      message,
      context,
      context_data: contextData,
      llm_provider: llmProvider,
      llm_model: llmModel
    });
  }
}
```

---

## Observabilidad

### Stack Completo

- **Prometheus**: Métricas del sistema
- **Grafana**: Visualización
- **Loki**: Agregación de logs
- **Promtail**: Recolección de logs

### Dashboards en Grafana

1. **System Resources**
   - CPU, RAM, Disk, Network
   - Por servicio Docker

2. **API Performance**
   - Request rate (req/sec)
   - Latency (p50, p95, p99)
   - Error rate
   - Status code distribution

3. **WebSocket Connections**
   - Active connections
   - Connection/disconnection rate
   - Reconnection attempts
   - Message throughput

4. **AI Engine**
   - LLM API calls (por provider)
   - Tokens consumed
   - Cost tracking
   - Inference time
   - GPU utilization

5. **Database**
   - Query time (slow queries)
   - Connection pool usage
   - Cache hit rate (Redis)
   - TimescaleDB chunk compression

6. **ETL Pipeline**
   - Job status (success/failed)
   - Job duration
   - Data processed (rows/bytes)
   - Queue length (Celery)

### Métricas Clave

```python
# Backend metrics (FastAPI)
from prometheus_client import Counter, Histogram, Gauge

# API metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# WebSocket metrics
ws_connections_active = Gauge('ws_connections_active', 'Active WebSocket connections')
ws_messages_sent = Counter('ws_messages_sent_total', 'WebSocket messages sent')

# AI Engine metrics
ai_llm_calls = Counter('ai_llm_calls_total', 'LLM API calls', ['provider', 'model'])
ai_tokens_used = Counter('ai_tokens_used_total', 'Tokens consumed', ['provider', 'type'])
ai_inference_duration = Histogram('ai_inference_duration_seconds', 'AI inference time')

# Database metrics
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
redis_cache_hits = Counter('redis_cache_hits_total', 'Redis cache hits')
redis_cache_misses = Counter('redis_cache_misses_total', 'Redis cache misses')
```

### Alertas Configuradas

- API latency > 2s (p95)
- Error rate > 5%
- WebSocket disconnection rate > 10%
- Disk usage > 85%
- Database connection pool exhausted
- AI API cost threshold exceeded

---

## Plan de Migración a VM

Ver archivo completo: **MIGRATION_PLAN.md** (documento vivo que se actualiza con cada fase)

### Resumen de Fases

1. **Preparación**: Documentar, exportar datos, verificar Docker
2. **Selección de Proveedor**: AWS/GCP/Azure/Paperspace/RunPod
3. **Provisioning con Terraform**: VM con GPU, networking, storage
4. **Configuración con Ansible**: Docker, NVIDIA drivers, SSL, monitoring
5. **Despliegue**: Copiar código, restaurar datos, iniciar servicios
6. **Post-Migración**: Monitoring activo, backups, CI/CD

### Proveedor Recomendado (por confirmar)

**Criterios de evaluación**:
- GPU disponible (CUDA)
- Costo por hora
- Latency para usuarios
- Facilidad de setup
- Support para Docker + NVIDIA

### Checklist de Migración

- [ ] Exportar datos de PostgreSQL
- [ ] Exportar datos de Neo4j
- [ ] Exportar datos de Redis (si es necesario)
- [ ] Documentar todas las env vars
- [ ] Backup de configuraciones
- [ ] Verificar que todo corre en Docker
- [ ] Crear configuración de Terraform
- [ ] Crear playbooks de Ansible
- [ ] Provisionar VM
- [ ] Configurar DNS
- [ ] Setup SSL (Let's Encrypt)
- [ ] Copiar código
- [ ] Restaurar datos
- [ ] Iniciar servicios
- [ ] Verificar funcionamiento
- [ ] Configurar backups automáticos
- [ ] Setup CI/CD

---

## Infraestructura como Código

### Terraform

**Propósito**: Provisionar infraestructura

**Recursos a crear**:
- VM instance con GPU
- VPC y subnets
- Security groups (firewall rules)
- Load balancer (si es necesario)
- Storage volumes (persistent disks)
- DNS records

**Estructura**:
```
infrastructure/terraform/
├── main.tf              # Main config
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── modules/
│   ├── compute/         # VM instances
│   ├── networking/      # VPC, subnets, firewall
│   └── storage/         # Disks, backups
└── environments/
    ├── dev/
    └── production/
```

### Ansible

**Propósito**: Configurar servidores

**Roles**:
1. **docker**: Instalar Docker y Docker Compose
2. **nvidia**: Instalar NVIDIA drivers y CUDA
3. **monitoring**: Setup Prometheus/Grafana
4. **nqhub**: Deploy aplicación

**Playbooks**:
- `setup.yml`: Setup inicial del servidor
- `deploy.yml`: Deploy de la aplicación
- `update.yml`: Actualizar aplicación
- `backup.yml`: Ejecutar backups

**Estructura**:
```
infrastructure/ansible/
├── playbooks/
│   ├── setup.yml
│   ├── deploy.yml
│   ├── update.yml
│   └── backup.yml
├── roles/
│   ├── docker/
│   ├── nvidia/
│   ├── monitoring/
│   └── nqhub/
└── inventory/
    ├── dev.ini
    └── production.ini
```

---

## Plan de Implementación

### PASO 1: Backup y Preparación (5 min)

**Objetivo**: Asegurar estado actual antes de cambios

**Acciones**:
1. Crear branch: `git checkout -b restructure-v0`
2. Commit actual: `git add . && git commit -m "Pre-restructure snapshot"`
3. Verificar git status limpio

**Verificación**:
```bash
git status
git log -1
```

---

### PASO 2: Crear Estructura de Directorios (15 min)

**Objetivo**: Crear toda la estructura vacía

**Directorios principales**:
- `frontend/`
- `backend/app/` (con todos los submódulos)
- `docker/` (con subdirectorios para configs)
- `infrastructure/terraform/`
- `infrastructure/ansible/`
- `docs/`
- `scripts/`

**Crear `__init__.py` en módulos Python**

**Verificación**:
```bash
tree -L 3 -d
```

---

### PASO 3: Mover Frontend (15 min)

**Objetivo**: Reorganizar código React en `/frontend`

**Mover**:
- `client/` → `frontend/src/client/`
- `shared/` → `frontend/src/shared/`
- `public/` → `frontend/public/`
- Archivos de config (package.json, vite.config.ts, etc.)

**Actualizar**:
- Paths en vite.config.ts
- Paths en tsconfig.json
- Scripts en package.json si es necesario

**Verificación**:
```bash
cd frontend
pnpm install
# No ejecutar aún, solo verificar que instala
```

---

### PASO 4: Inicializar Backend Python (25 min)

**Objetivo**: Crear estructura completa de FastAPI

**Crear archivos clave**:
1. `backend/requirements.txt` - Dependencias base
2. `backend/requirements-ai.txt` - PyTorch, LangGraph, etc.
3. `backend/requirements-dev.txt` - pytest, etc.
4. `backend/pyproject.toml` - Project config
5. `backend/.env.example` - Template de env vars
6. `backend/app/main.py` - FastAPI entry point (básico)
7. `backend/app/config.py` - Configuration class

**Crear estructura de `app/` con `__init__.py`**:
- `ai_engine/` (con todos los submódulos)
- `api/v1/` (endpoints)
- `core/`, `models/`, `schemas/`, `services/`, `db/`, `utils/`

**Verificación**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Verificar que instala sin errores
```

---

### PASO 5: Docker Compose Completo (25 min)

**Objetivo**: Configurar todos los servicios Docker

**Crear archivos**:
1. `docker/docker-compose.yml` - Servicios principales
2. `docker/docker-compose.dev.yml` - Dev overrides
3. `docker/docker-compose.monitoring.yml` - Grafana stack
4. `docker/Dockerfile.backend`
5. `docker/Dockerfile.ai-gpu` (con CUDA)
6. `docker/Dockerfile.frontend`
7. `docker/postgres/init.sql` (TimescaleDB setup)
8. `docker/.env.docker` (ejemplo)

**Crear configs**:
- `docker/prometheus/prometheus.yml`
- `docker/loki/loki-config.yml`
- `docker/promtail/promtail-config.yml`
- `docker/grafana/provisioning/` (datasources, dashboards)

**Verificación**:
```bash
docker-compose config  # Verificar sintaxis
```

---

### PASO 5.5: Setup Observabilidad (20 min)

**Objetivo**: Configurar dashboards de Grafana

**Crear dashboards JSON**:
1. `docker/grafana/dashboards/system.json` - System resources
2. `docker/grafana/dashboards/api.json` - API performance
3. `docker/grafana/dashboards/websocket.json` - WebSocket metrics
4. `docker/grafana/dashboards/ai_engine.json` - AI metrics
5. `docker/grafana/dashboards/database.json` - DB metrics

**Crear provisioning configs**:
- `docker/grafana/provisioning/datasources/datasources.yml`
- `docker/grafana/provisioning/dashboards/dashboards.yml`

---

### PASO 6: Setup Alembic (10 min)

**Objetivo**: Configurar migrations de base de datos

**Acciones**:
1. Crear `backend/alembic.ini`
2. Inicializar: `cd backend && alembic init alembic`
3. Configurar `backend/alembic/env.py` para async SQLAlchemy
4. Crear primera migración:
   ```bash
   alembic revision -m "Initial tables: users, invitations, sessions"
   ```

**Verificación**:
```bash
alembic check  # Verificar configuración
```

---

### PASO 7: Scripts de Setup (20 min)

**Objetivo**: Crear scripts de automatización

**Crear scripts**:

1. **scripts/dev_setup.sh** (complete setup)
```bash
#!/bin/bash
# Start Docker services
# Setup backend venv
# Install dependencies
# Run migrations
# Create superuser
```

2. **scripts/start_dev.sh** (start development)
```bash
#!/bin/bash
# Start backend
# Start frontend
# Show logs
```

3. **backend/scripts/init_superuser.py**
4. **backend/scripts/generate_invitation.py**
5. **backend/scripts/check_gpu.sh** (verify CUDA)
6. **backend/scripts/export_data.sh** (for migration)

**Hacer ejecutables**:
```bash
chmod +x scripts/*.sh
chmod +x backend/scripts/*.sh
```

---

### PASO 8: Actualizar Documentación (15 min)

**Objetivo**: Docs actualizadas con nueva estructura

**Actualizar/crear**:
1. `README.md` - Nueva estructura, quick start
2. `CLAUDE.md` - Actualizar paths y estructura
3. `frontend/README.md` - Frontend-specific docs
4. `backend/README.md` - Backend-specific docs
5. `docs/DEVELOPMENT.md` - Development guide
6. `docs/API.md` - API documentation
7. `docs/OBSERVABILITY.md` - Monitoring guide
8. `.gitignore` - Actualizar patterns

---

### PASO 9: Motor de IA Base (35 min)

**Objetivo**: Implementar estructura del AI Engine

**Crear módulos**:

1. **core/**
   - `engine.py` - AIEngine singleton
   - `config.py` - Multi-LLM config
   - `context.py` - Context types

2. **langgraph/**
   - `graph_builder.py` - Graph factory
   - `nodes/` - Reusable nodes
   - `graphs/` - Context-specific graphs

3. **memory/**
   - `memory_manager.py` - Dual memory (mem0 + Neo4j)
   - `adapters/mem0_adapter.py`
   - `adapters/neo4j_adapter.py`

4. **voice/**
   - `voice_engine.py` - ElevenLabs integration
   - `audio_processor.py`
   - `stream_handler.py`

5. **prompts/**
   - `base.py`, `chat.py`, `chart_analysis.py`, etc.

6. **tools/**
   - `chart_tools.py`, `data_tools.py`, etc.

**Implementar configuración multi-LLM**

---

### PASO 10: Frontend - Selector de LLM (15 min)

**Objetivo**: UI para seleccionar LLM

**Crear componentes**:
1. `frontend/src/client/components/ai-assistant/LLMSelector.tsx`
2. `frontend/src/client/components/ai-assistant/AIAssistantButton.tsx`
3. Actualizar Zustand store con LLM preference

**Integrar en páginas**:
- DataModule
- Chat
- Anywhere AI Assistant is used

---

### PASO 11: Variables de Entorno (15 min)

**Objetivo**: Templates completos de env vars

**Crear archivos**:
1. `backend/.env.example` - Completo
2. `frontend/.env.example`
3. `docker/.env.example`

**Incluir**:
- Database URLs (PostgreSQL, Redis, Neo4j)
- Secret keys
- LLM API keys (OpenAI, Anthropic, Groq)
- ElevenLabs API key (vacía por ahora)
- mem0 API key
- CORS origins
- Mailpit config
- Grafana password

---

### PASO 12: Estructura Terraform (20 min)

**Objetivo**: IaC básico (sin provisionar)

**Crear estructura**:
```
infrastructure/terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── compute/
│   ├── networking/
│   └── storage/
└── environments/
    ├── dev/
    └── production/
```

**Contenido básico**:
- Provider config (AWS/GCP/Azure - por definir)
- Module definitions
- Variable declarations

---

### PASO 13: Estructura Ansible (20 min)

**Objetivo**: Playbooks básicos (sin ejecutar)

**Crear estructura**:
```
infrastructure/ansible/
├── playbooks/
│   ├── setup.yml
│   ├── deploy.yml
│   ├── update.yml
│   └── backup.yml
├── roles/
│   ├── docker/
│   ├── nvidia/
│   ├── monitoring/
│   └── nqhub/
└── inventory/
    ├── dev.ini
    └── production.ini
```

**Contenido básico**:
- Playbook structure
- Role definitions
- Inventory examples

---

### PASO 14: Verificación Completa (20 min)

**Objetivo**: Smoke test de todo

**Iniciar servicios**:
```bash
# Start databases
docker-compose up -d postgres redis neo4j mailpit

# Wait for healthy
docker-compose ps

# Verificar logs
docker-compose logs -f postgres
```

**Verificar cada servicio**:
- PostgreSQL: `psql -h localhost -U nqhub -d nqhub`
- Redis: `redis-cli ping`
- Neo4j: http://localhost:7474
- Mailpit: http://localhost:8025

**Intentar arrancar backend** (sin ejecutar completamente):
```bash
cd backend
source venv/bin/activate
python -c "from app.main import app; print('Import OK')"
```

**Intentar arrancar frontend**:
```bash
cd frontend
pnpm dev --port 3000
# Ctrl+C después de verificar que arranca
```

---

### PASO 15: Commit Final (5 min)

**Objetivo**: Guardar todo el progreso

**Acciones**:
```bash
git add .
git status  # Revisar cambios
git commit -m "Complete project restructure

- Separate frontend/backend
- Add Docker Compose (PostgreSQL, TimescaleDB, Redis, Neo4j, Mailpit)
- Add monitoring stack (Grafana, Loki, Prometheus)
- Add AI Engine with multi-LLM support (OpenAI, Anthropic, Llama)
- Add Terraform/Ansible structure for VM migration
- Update all documentation
"

git push origin restructure-v0
```

**Crear PR** (si usas GitHub):
```bash
gh pr create --title "Project Restructure v0" --body "Complete restructure as per PROJECT_PLANv0.md"
```

---

## Variables de Entorno

### Backend (.env)

```bash
# ==================== DATABASE ====================
DATABASE_URL=postgresql://nqhub:your_password@localhost:5432/nqhub
DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:your_password@localhost:5432/nqhub

# ==================== REDIS ====================
REDIS_URL=redis://localhost:6379

# ==================== NEO4J ====================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ==================== SECURITY ====================
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==================== CORS ====================
ALLOWED_ORIGINS=http://localhost:3000,https://your-ngrok-domain.ngrok.io

# ==================== AI / LLM ====================
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Groq (for Llama)
GROQ_API_KEY=gsk_...

# Ollama (for local Llama) - optional
OLLAMA_BASE_URL=http://localhost:11434

# mem0
MEM0_API_KEY=...

# ElevenLabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# ==================== EMAIL ====================
# Mailpit (development)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@nqhub.com

# Production (Gmail/SendGrid) - commented out
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# ==================== ENVIRONMENT ====================
ENVIRONMENT=development

# ==================== SUPERUSER (for init script) ====================
SUPERUSER_EMAIL=admin@nqhub.com
SUPERUSER_PASSWORD=change-this-password
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=development
```

### Docker (.env)

```bash
# Postgres
POSTGRES_PASSWORD=your_postgres_password

# Neo4j
NEO4J_PASSWORD=your_neo4j_password

# Backend
SECRET_KEY=your-secret-key

# Grafana
GRAFANA_PASSWORD=your_grafana_password

# API Keys (same as backend)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
ELEVENLABS_API_KEY=...
MEM0_API_KEY=...
```

---

## Comandos de Desarrollo

### Setup Inicial

```bash
# Complete setup
./scripts/dev_setup.sh

# Manual setup
docker-compose up -d postgres redis neo4j mailpit
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt -r requirements-ai.txt
alembic upgrade head
python scripts/init_superuser.py
cd ../frontend
pnpm install
```

### Desarrollo Diario

```bash
# Option 1: All in Docker
docker-compose up

# Option 2: Manual (recommended for dev)
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
pnpm dev

# Terminal 3 - ngrok (optional)
ngrok http 3000 --domain=your-static-domain.ngrok.io

# Terminal 4 - Logs
docker-compose logs -f postgres redis neo4j
```

### Base de Datos

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
python scripts/init_superuser.py
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
pnpm test

# Run specific test
cd backend
pytest tests/test_auth.py -v
```

### Monitoring

```bash
# Start monitoring stack
docker-compose -f docker/docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: http://localhost:3001 (admin/password)
# Prometheus: http://localhost:9090
# Loki: http://localhost:3100/ready

# View logs
docker-compose logs -f loki promtail
```

### Neo4j

```bash
# Access Neo4j Browser
open http://localhost:7474

# Cypher shell
docker exec -it nqhub_neo4j cypher-shell -u neo4j -p your_password

# Example queries
MATCH (n) RETURN count(n);  # Count all nodes
MATCH (n) DETACH DELETE n;  # Clear all data
```

### AI Worker

```bash
# Check GPU
nvidia-smi

# Run GPU check script
./backend/scripts/check_gpu.sh

# Start AI worker manually
cd backend
source venv/bin/activate
python -m app.ai_engine.worker
```

### Production Build

```bash
# Build frontend
cd frontend
pnpm build

# Build backend Docker image
cd backend
docker build -f ../docker/Dockerfile.backend -t nqhub-backend:latest .

# Build AI worker Docker image
docker build -f ../docker/Dockerfile.ai-gpu -t nqhub-ai-worker:latest .
```

---

## Próximos Pasos Después de Reestructuración

### Fase 2: Sistema de Autenticación (Semana 2)
- Implementar JWT completo
- Endpoints de auth
- Sistema de invitaciones
- Tests de autenticación

### Fase 3: Admin Panel (Semana 3)
- UI de administración
- Gestión de usuarios
- Gestión de invitaciones

### Fase 4: Integración de Datos (Semana 4)
- Reemplazar mock data con API real
- Setup TimescaleDB hypertables
- Cache con Redis
- SciChart integration

### Fase 5: WebSocket Resiliente (Semana 5)
- Implementar reconexión automática
- Heartbeat/ping-pong
- Message queue
- UI de estado de conexión

### Fase 6: AI Assistant (Semana 6)
- Implementar LangGraph graphs
- Integración con mem0 y Neo4j
- Chat UI
- Context-aware responses

### Fase 7: Voice Integration (Semana 7)
- ElevenLabs integration
- Audio streaming
- Speech-to-text
- Text-to-speech
- Voice controls UI

### Fase 8: Migración a VM (Semana 8+)
- Seleccionar proveedor cloud
- Provisionar con Terraform
- Configurar con Ansible
- Deploy y testing

---

## Notas Importantes

### SciChart
- Modo trial durante desarrollo
- Licencia requerida para producción
- Configurar license key cuando esté disponible

### GPU / CUDA
- Requerido para AI worker
- NVIDIA drivers instalados
- CUDA 12.1+
- PyTorch con CUDA support

### Neo4j
- Plugins APOC y Graph Data Science incluidos
- Configurar heap memory según disponibilidad
- Backup periódico de datos

### Observabilidad
- Grafana dashboards incluidos desde inicio
- Loki para logs centralizados
- Prometheus para métricas
- Alertas configuradas

### Seguridad
- JWT tokens con expiración
- Password hashing con bcrypt
- CORS configurado
- Rate limiting (por implementar)
- SSL/TLS en producción (Let's Encrypt)

### Performance
- Redis cache para datos frecuentes
- Connection pooling en PostgreSQL
- Async SQLAlchemy
- WebSocket con reconexión
- Batch processing para ETL

---

## Contacto y Soporte

Para preguntas o issues durante la implementación, referirse a:
- `CLAUDE.md` - Guía para Claude Code
- `docs/DEVELOPMENT.md` - Guía de desarrollo detallada
- `docs/API.md` - Documentación de API
- `MIGRATION_PLAN.md` - Plan de migración actualizado

---

**Última actualización**: 2025-10-29
**Versión**: v0.1
**Estado**: Documento completo - Listo para implementación
