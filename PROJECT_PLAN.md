# NQHUB v0 - Plan de Inicio del Proyecto

## Visión General

NQHUB es una plataforma profesional de análisis de trading para futuros de NQ (Nasdaq 100 E-mini). Este documento describe la arquitectura completa del sistema, incluyendo frontend (React), backend (Python), bases de datos, y el sistema de autenticación por invitación.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        NQHUB v0                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐      ┌──────────────┐     ┌─────────────┐ │
│  │   Frontend  │◄────►│   Backend    │◄───►│  Databases  │ │
│  │  (React)    │      │   (Python)   │     │             │ │
│  │             │      │              │     │ PostgreSQL  │ │
│  │  Port 3000  │      │  Port 8000   │     │ TimescaleDB │ │
│  └─────────────┘      └──────────────┘     │ Redis       │ │
│        ▲                                    └─────────────┘ │
│        │                                                     │
│        └──────── ngrok (exposición inicial) ────────────    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Stack Tecnológico

### Frontend
- **Framework**: React 18 + TypeScript
- **Routing**: React Router 6
- **State Management**:
  - React Context (auth, UI, servicios)
  - Zustand (datos de negocio, charts)
- **UI**: Radix UI + TailwindCSS 3
- **Build**: Vite
- **Testing**: Vitest

### Backend
- **Lenguaje**: Python 3.11+
- **Framework Web**: FastAPI (recomendado) o Flask
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Auth**: JWT + bcrypt
- **WebSockets**: FastAPI WebSockets / Socket.io
- **Task Queue**: Celery + Redis (para ETL jobs)
- **Testing**: pytest

### Bases de Datos
- **PostgreSQL 15+**: Base de datos principal (usuarios, configuraciones, metadata)
- **TimescaleDB**: Extensión de PostgreSQL para datos históricos de trading (OHLCV, orderflow)
- **Redis 7+**:
  - Cache de datos de charts
  - Session storage
  - WebSocket pub/sub
  - Celery broker

### Infraestructura
- **Ambiente de Desarrollo**: WSL 2 (Ubuntu)
- **Containerización**: Docker + Docker Compose
- **Exposición Externa**: ngrok (inicial)
- **Variables de Entorno**: python-dotenv

## Estructura de Proyecto Propuesta

```
nqhub/
├── frontend/                      # Todo el código React existente
│   ├── src/
│   │   ├── client/               # (actual client/)
│   │   ├── shared/               # (actual shared/)
│   │   └── ...
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── backend/                       # Nuevo backend en Python
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Configuración (DB, Redis, etc.)
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   │
│   │   ├── api/                  # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py       # Login, register, invitations
│   │   │   │   ├── users.py      # User management
│   │   │   │   ├── charts.py     # Chart data endpoints
│   │   │   │   ├── etl.py        # ETL pipeline endpoints
│   │   │   │   └── admin.py      # Admin-only endpoints
│   │   │   └── deps.py           # Route dependencies
│   │   │
│   │   ├── core/                 # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── security.py       # JWT, password hashing
│   │   │   ├── permissions.py    # Role-based access control
│   │   │   └── invitations.py    # Invitation logic
│   │   │
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User, Role
│   │   │   ├── invitation.py     # Invitation tokens
│   │   │   ├── trading.py        # OHLCV, Indicators
│   │   │   └── etl.py            # DataSource, ETLJob
│   │   │
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Login, Register, Token
│   │   │   ├── user.py           # User response schemas
│   │   │   ├── invitation.py     # Invitation schemas
│   │   │   └── chart.py          # Chart data schemas
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py   # Auth operations
│   │   │   ├── user_service.py   # User CRUD
│   │   │   ├── chart_service.py  # Chart data retrieval
│   │   │   ├── etl_service.py    # ETL operations
│   │   │   └── cache_service.py  # Redis operations
│   │   │
│   │   ├── db/                   # Database utilities
│   │   │   ├── __init__.py
│   │   │   ├── session.py        # SQLAlchemy session
│   │   │   ├── base.py           # Base model
│   │   │   └── init_db.py        # DB initialization
│   │   │
│   │   └── utils/                # Utilities
│   │       ├── __init__.py
│   │       ├── email.py          # Email sending (invitations)
│   │       └── validators.py     # Custom validators
│   │
│   ├── alembic/                  # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/                    # pytest tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   └── test_users.py
│   │
│   ├── requirements.txt          # Python dependencies
│   ├── requirements-dev.txt      # Dev dependencies
│   ├── pyproject.toml           # Python project config
│   ├── .env.example             # Environment variables template
│   └── README.md
│
├── docker/                       # Docker configurations
│   ├── docker-compose.yml       # All services
│   ├── docker-compose.dev.yml   # Development overrides
│   ├── Dockerfile.backend       # Backend image
│   ├── Dockerfile.frontend      # Frontend image (production)
│   ├── postgres/
│   │   └── init.sql             # Initial DB setup
│   └── nginx/
│       └── nginx.conf           # Production proxy config
│
├── scripts/                      # Utility scripts
│   ├── init_superuser.py        # Create first superuser
│   ├── generate_invitation.py   # Generate invitation token
│   └── dev_setup.sh             # Development environment setup
│
├── docs/                         # Additional documentation
│   ├── API.md                   # API documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── DEVELOPMENT.md           # Development guide
│
├── .gitignore
├── README.md                     # Main project README
└── CLAUDE.md                     # Claude Code guidance (actualizado)
```

## Sistema de Autenticación por Invitación

### Roles del Sistema

1. **superuser** (Superusuario)
   - Acceso completo al sistema
   - Puede generar invitaciones
   - Puede gestionar todos los usuarios
   - Acceso a configuraciones avanzadas
   - Panel de administración completo

2. **trader** (Trader)
   - Acceso a charts y análisis
   - Acceso a módulo de datos
   - No puede invitar usuarios
   - No accede a configuraciones de sistema

### Flujo de Registro por Invitación

```
┌──────────────┐
│ Superusuario │
└──────┬───────┘
       │
       │ 1. Genera invitación desde Admin Panel
       ▼
┌─────────────────────────────────────┐
│ Backend: POST /api/v1/admin/invitations  │
│ - Crea token único (UUID)           │
│ - Define rol (trader)               │
│ - Establece expiración (7 días)    │
│ - Guarda en DB                      │
└──────┬──────────────────────────────┘
       │
       │ 2. Retorna URL de invitación
       ▼
┌─────────────────────────────────────┐
│ https://nqhub.ngrok.io/register?token=xxx │
└──────┬──────────────────────────────┘
       │
       │ 3. Superusuario envía URL al nuevo trader
       ▼
┌──────────────┐
│ Nuevo Trader │
└──────┬───────┘
       │
       │ 4. Accede a la URL
       ▼
┌─────────────────────────────────────┐
│ Frontend: /register?token=xxx       │
│ - Valida token con backend          │
│ - Muestra formulario de registro    │
└──────┬──────────────────────────────┘
       │
       │ 5. Completa registro
       ▼
┌─────────────────────────────────────┐
│ Backend: POST /api/v1/auth/register │
│ - Valida token                      │
│ - Verifica que no esté usado        │
│ - Crea usuario con rol especificado│
│ - Marca invitación como usada       │
│ - Retorna JWT token                 │
└──────┬──────────────────────────────┘
       │
       │ 6. Auto-login con JWT
       ▼
┌──────────────┐
│  Dashboard   │
└──────────────┘
```

### Modelo de Base de Datos

#### Tabla: users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL, -- 'superuser' o 'trader'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### Tabla: invitations
```sql
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255), -- Opcional: pre-asignar invitación a email
    role VARCHAR(50) NOT NULL DEFAULT 'trader',
    invited_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    used_by UUID REFERENCES users(id)
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);
```

#### Tabla: sessions (opcional, para revocación de tokens)
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL, -- JWT ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT false
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_jti ON sessions(token_jti);
```

## Modificaciones en Frontend para Superusuario

### 1. Actualizar Tipos de Roles

**Archivo**: `frontend/src/client/state/app.tsx`

```typescript
// Cambiar de:
export type Role = "admin" | "trader" | "analystSenior" | "analystJunior";

// A:
export type Role = "superuser" | "trader";
```

### 2. Crear Componente de Admin Panel

**Nuevo archivo**: `frontend/src/client/pages/AdminPanel.tsx`

Funcionalidades:
- Lista de usuarios registrados
- Generar invitaciones
- Gestionar invitaciones pendientes/usadas
- Revocar acceso de usuarios
- Ver estadísticas del sistema

### 3. Crear Componente de Invitaciones

**Nuevo archivo**: `frontend/src/client/components/admin/InvitationManager.tsx`

Features:
- Botón "Generar Nueva Invitación"
- Modal para configurar invitación (email opcional, rol, expiración)
- Lista de invitaciones con estados (pendiente, usada, expirada)
- Copiar URL de invitación
- Revocar invitación

### 4. Crear Página de Registro

**Nuevo archivo**: `frontend/src/client/pages/Register.tsx`

Funcionalidades:
- Validar token en URL
- Formulario de registro (email, password, first_name, last_name)
- Mensajes de error (token inválido/expirado)
- Auto-redirect a dashboard después de registro

### 5. Actualizar Sidebar

**Archivo**: `frontend/src/client/components/layout/Sidebar.tsx`

Agregar items condicionales para superuser:
```typescript
{user.role === 'superuser' && (
  <>
    <SidebarItem icon={Users} to="/admin/users">
      User Management
    </SidebarItem>
    <SidebarItem icon={Settings} to="/admin/settings">
      System Settings
    </SidebarItem>
  </>
)}
```

### 6. Actualizar Rutas

**Archivo**: `frontend/src/client/App.tsx`

```typescript
<Route path="/register" element={<Register />} />
<Route
  path="/admin"
  element={
    <ProtectedRoute requiredRole="superuser">
      <AdminPanel />
    </ProtectedRoute>
  }
/>
<Route
  path="/admin/users"
  element={
    <ProtectedRoute requiredRole="superuser">
      <UserManagement />
    </ProtectedRoute>
  }
/>
```

### 7. Crear Higher-Order Component para Roles

**Nuevo archivo**: `frontend/src/client/components/auth/ProtectedRoute.tsx`

```typescript
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: Role | Role[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole
}) => {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requiredRole) {
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
    if (!roles.includes(user.role)) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return <>{children}</>;
};
```

## Plan de Implementación por Fases

### Fase 1: Reestructuración y Setup Inicial (Semana 1)

**Objetivos**:
- Reorganizar proyecto con carpetas frontend/backend separadas
- Configurar Docker Compose con PostgreSQL, TimescaleDB, Redis
- Setup básico de FastAPI
- Configurar ngrok

**Tareas**:
1. ✅ Crear nueva estructura de carpetas
2. ✅ Mover código de frontend a `/frontend`
3. ✅ Inicializar backend Python con FastAPI
4. ✅ Crear `docker-compose.yml` con servicios
5. ✅ Configurar variables de entorno
6. ✅ Setup Alembic para migrations
7. ✅ Documentar en README.md

**Entregables**:
- Estructura de carpetas completa
- Docker Compose funcional
- Backend responde en `http://localhost:8000`
- Frontend responde en `http://localhost:3000`
- Ambos expuestos vía ngrok

### Fase 2: Sistema de Autenticación (Semana 2)

**Objetivos**:
- Implementar autenticación completa con JWT
- Sistema de invitaciones
- Crear primer superusuario

**Tareas Backend**:
1. ✅ Modelos: User, Invitation, Session
2. ✅ Migrations de Alembic
3. ✅ Core security (JWT, bcrypt)
4. ✅ Endpoints:
   - `POST /api/v1/auth/login`
   - `POST /api/v1/auth/register` (con token)
   - `POST /api/v1/auth/refresh`
   - `POST /api/v1/auth/logout`
   - `GET /api/v1/invitations/validate/{token}`
   - `POST /api/v1/admin/invitations` (crear)
   - `GET /api/v1/admin/invitations` (listar)
5. ✅ Script: `init_superuser.py`
6. ✅ Tests de autenticación

**Tareas Frontend**:
1. ✅ Actualizar tipos de roles
2. ✅ Crear página Register
3. ✅ Actualizar componente Login
4. ✅ Implementar almacenamiento de JWT
5. ✅ Crear API client con interceptor de auth
6. ✅ Actualizar Context de Auth para usar backend real

**Entregables**:
- Sistema de autenticación funcionando end-to-end
- Primer superusuario creado vía script
- Flujo de invitación completo

### Fase 3: Panel de Administración (Semana 3)

**Objetivos**:
- UI completa para superusuario
- Gestión de usuarios e invitaciones

**Tareas Backend**:
1. ✅ Endpoints de administración:
   - `GET /api/v1/admin/users` (listar)
   - `PATCH /api/v1/admin/users/{id}` (actualizar)
   - `DELETE /api/v1/admin/users/{id}` (desactivar)
   - `DELETE /api/v1/admin/invitations/{id}` (revocar)
   - `GET /api/v1/admin/stats` (estadísticas)
2. ✅ Middleware de permisos

**Tareas Frontend**:
1. ✅ Página AdminPanel
2. ✅ Componente InvitationManager
3. ✅ Componente UserManagement
4. ✅ Actualizar Sidebar con items de admin
5. ✅ Implementar ProtectedRoute con roles
6. ✅ Agregar rutas de admin

**Entregables**:
- Panel de admin completamente funcional
- Superusuario puede gestionar usuarios e invitaciones

### Fase 4: Integración de Datos (Semana 4)

**Objetivos**:
- Reemplazar mock data con endpoints reales
- Configurar TimescaleDB para datos históricos
- Implementar cache con Redis

**Tareas Backend**:
1. ✅ Modelos para datos de trading (OHLCV, Footprint)
2. ✅ Setup de TimescaleDB hypertables
3. ✅ Endpoints de charts:
   - `GET /api/v1/charts/candles`
   - `GET /api/v1/charts/footprint`
   - `GET /api/v1/charts/volume-profile`
4. ✅ Servicio de cache con Redis
5. ✅ Seed data para testing

**Tareas Frontend**:
1. ✅ Actualizar `shared/mock-data.ts` con llamadas reales
2. ✅ Actualizar Zustand store con async actions
3. ✅ Implementar loading states
4. ✅ Manejo de errores

**Entregables**:
- Datos de charts servidos desde backend
- Cache funcionando
- Frontend consumiendo API real

### Fase 5: WebSockets y Real-time (Semana 5)

**Objetivos**:
- Implementar actualizaciones en tiempo real
- WebSocket para datos de trading

**Tareas Backend**:
1. ✅ Setup FastAPI WebSockets
2. ✅ Implementar pub/sub con Redis
3. ✅ Endpoint WebSocket para real-time data
4. ✅ Simulador de datos en vivo (para testing)

**Tareas Frontend**:
1. ✅ Cliente WebSocket
2. ✅ Integrar con Zustand store
3. ✅ UI para indicar conexión/desconexión
4. ✅ Reconexión automática

**Entregables**:
- Datos de trading actualizados en tiempo real
- WebSocket estable con reconexión

## Configuración de Docker Compose

### docker-compose.yml (Base)

```yaml
version: '3.8'

services:
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

  redis:
    image: redis:7-alpine
    container_name: nqhub_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - nqhub_network

  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    container_name: nqhub_backend
    environment:
      DATABASE_URL: postgresql://nqhub:${POSTGRES_PASSWORD}@postgres:5432/nqhub
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    networks:
      - nqhub_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    container_name: nqhub_frontend
    environment:
      VITE_API_URL: http://localhost:8000
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

volumes:
  postgres_data:
  redis_data:

networks:
  nqhub_network:
    driver: bridge
```

## Variables de Entorno

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://nqhub:your_password@localhost:5432/nqhub
DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:your_password@localhost:5432/nqhub

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-ngrok-domain.ngrok.io

# Email (para invitaciones)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@nqhub.com

# Environment
ENVIRONMENT=development

# Superuser inicial (para script)
SUPERUSER_EMAIL=admin@nqhub.com
SUPERUSER_PASSWORD=change-this-password
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=development
```

## Scripts Útiles

### backend/scripts/init_superuser.py

```python
import asyncio
from app.db.session import get_session
from app.models.user import User
from app.core.security import get_password_hash
from app.config import settings

async def create_superuser():
    async with get_session() as session:
        # Check if superuser exists
        existing = await session.execute(
            select(User).where(User.email == settings.SUPERUSER_EMAIL)
        )
        if existing.scalar_one_or_none():
            print(f"Superuser {settings.SUPERUSER_EMAIL} already exists")
            return

        # Create superuser
        superuser = User(
            email=settings.SUPERUSER_EMAIL,
            hashed_password=get_password_hash(settings.SUPERUSER_PASSWORD),
            first_name="Admin",
            last_name="User",
            role="superuser",
            is_active=True
        )
        session.add(superuser)
        await session.commit()
        print(f"Superuser created: {settings.SUPERUSER_EMAIL}")

if __name__ == "__main__":
    asyncio.run(create_superuser())
```

### scripts/dev_setup.sh

```bash
#!/bin/bash

echo "🚀 Setting up NQHUB development environment..."

# Start Docker services
echo "📦 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
sleep 5

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Create superuser
echo "👤 Creating superuser..."
python scripts/init_superuser.py

# Frontend setup
echo "⚛️  Setting up React frontend..."
cd ../frontend
pnpm install

echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && pnpm dev"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up"
```

## Comandos de Desarrollo

### Iniciar todo con Docker
```bash
docker-compose up
```

### Desarrollo local (sin Docker)

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
pnpm dev
```

**Terminal 3 - ngrok**:
```bash
ngrok http 3000 --domain=your-static-domain.ngrok.io
```

### Crear migración de base de datos
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Generar invitación (después de Fase 2)
```bash
cd backend
python scripts/generate_invitation.py --role trader --email user@example.com
```

## Dependencias de Python (requirements.txt)

```
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Redis
redis==5.0.1
hiredis==2.3.2

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# Environment
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# CORS
python-cors==1.0.0

# WebSockets
websockets==12.0

# Background tasks
celery==5.3.6

# Utils
python-dateutil==2.8.2
pytz==2024.1
```

## Próximos Pasos Inmediatos

1. **Confirmar Stack**: ¿Estás de acuerdo con FastAPI para el backend?
2. **Reestructurar Proyecto**: Mover frontend a carpeta separada
3. **Inicializar Backend**: Crear estructura básica de FastAPI
4. **Setup Docker**: Crear docker-compose.yml
5. **Primera Migración**: Crear tablas de users e invitations

¿Quieres que empiece con alguna fase específica o prefieres que creemos la estructura completa primero?
