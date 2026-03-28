# LAPTOP2 - Complete Port Mapping Guide

**System:** Windows + WSL2 (PlantData) + WSL2 (NQHUB_v0)
**Last Updated:** 2025-11-17
**Purpose:** Centralized port allocation reference to avoid conflicts

---

## Port Allocation Summary

| Port Range | System/Project | Description |
|------------|----------------|-------------|
| 0-1023 | System Reserved | Standard system ports |
| 1025 | NQHUB | mailpit-smtp (wslrelay) - PRIORITY |
| 2222 | Windows→WSL | SSH port forwarding |
| **3001** | **NQHUB** | **Frontend Vite - PRIORITY** |
| 5433 | NQHUB | postgres/timescale (docker) - PRIORITY |
| 6379 | NQHUB | redis (wslrelay) - PRIORITY (shared) |
| 7474 | NQHUB | neo4j-http (wslrelay) - PRIORITY (shared) |
| 7687 | NQHUB | neo4j-bolt (wslrelay) - PRIORITY (shared) |
| 8001 | NQHUB | redis-insight (docker interno) |
| **8002** | **NQHUB** | **Backend FastAPI - PRIORITY** |
| 8025 | NQHUB | mailpit-ui (wslrelay) - PRIORITY (shared) |
| **8080** | **Windows** | **OCCUPIED by svchost.exe - NEVER USE** |
| **8100-8199** | **PlantData** | **All PlantData services** |
| 8888 | NQHUB | jupyter-timeseries (optional) |
| **9000-9099** | **YupkaQuant** | **Reserved for YupkaQuant (when active)** |

---

## Detailed Port Mapping

### Windows Native Services

| Port | Service | Process | Notes |
|------|---------|---------|-------|
| **8080** | Windows Service | svchost.exe | ⚠️ **DO NOT USE** - System occupied on 0.0.0.0 |
| 2222 | Port Forward | WSL→SSH | Windows:2222 → WSL:22 |

### WSL2: NQHUB_v0 Environment

**Base Path:** `~/projects/NQHUB_v0/` (main project - PRIORITY)
**Related Projects:**
- `~/projects/YupkaQuant/` - See "YupkaQuant Port Adjustments" section below
- `~/projects/pythonVarios/` - jupyter (8888)

| Port | Service | Type | Access | Status | Priority |
|------|---------|------|--------|--------|----------|
| **1025** | mailpit-smtp | SMTP | 127.0.0.1 (wslrelay) | Active | HIGH |
| **3001** | nqhub-frontend | HTTP | 127.0.0.1 (Vite) | Active | **PRIORITY** |
| **5433** | postgres/timescale | TCP | docker interno | Active | **PRIORITY** |
| **6379** | redis | TCP | 127.0.0.1 (wslrelay) | Active | **PRIORITY** |
| **7474** | neo4j-http | HTTP | 127.0.0.1 (wslrelay) | Active | **PRIORITY** |
| **7687** | neo4j-bolt | TCP | 127.0.0.1 (wslrelay) | Active | **PRIORITY** |
| **8001** | redis-insight | HTTP | docker interno | Active | Medium |
| **8002** | nqhub-backend | HTTP | 127.0.0.1 (FastAPI) | Active | **PRIORITY** |
| **8025** | mailpit-ui | HTTP | 127.0.0.1 (wslrelay) | Active | HIGH |
| **8888** | jupyter-timeseries | HTTP | 127.0.0.1 (wslrelay) | Optional | Low |

### WSL2: YupkaQuant Environment (When Active)

**Base Path:** `~/projects/YupkaQuant/`
**Status:** Currently inactive - Ports need adjustment before startup
**Required Port Range:** **9000-9099** (to avoid conflicts with NQHUB_v0)

⚠️ **IMPORTANT:** YupkaQuant must be reconfigured to use ports 9000-9099 when running alongside NQHUB_v0. See detailed adjustment instructions in the "YupkaQuant Port Adjustments" section below.

| Port | Service | Current Config | Required Config | Action Needed |
|------|---------|----------------|-----------------|---------------|
| 80 → **9000** | frontend | Port 80 | Port 9000 | Update docker-compose.yml |
| 8000 → **9001** | backend | Port 8000 | Port 9001 | Update docker-compose.yml |
| (shared) | postgres | 5433 | Share NQHUB's 5433 | No change |
| (shared) | redis | 6379 | Share NQHUB's 6379 | No change |
| (shared) | neo4j | 7474/7687 | Share NQHUB's 7474/7687 | No change |

### WSL2: PlantData Environment

**Base Path:** `/home/ricardo-plant-data/projects/PlantData/`
**Port Range:** **8100-8199** (Reserved exclusively for PlantData)

#### Active Services

| Port | Service | Description | Protocol | Access URL |
|------|---------|-------------|----------|------------|
| **8100** | plantdata-frontend | Frontend web (Docker) | HTTP | http://localhost:8100 |
| **8101** | plantdata-backend | FastAPI REST API | HTTP | http://localhost:8101 |
| **8102** | plantdata-postgres | PostgreSQL database | TCP | localhost:8102 |
| **8103** | plantdata-redis | Redis cache/queue | TCP | localhost:8103 |
| **8109** | plantdata-frontend-dev | Frontend local dev | HTTP | http://localhost:8109 |
| **8110** | plantdata-neo4j-browser | Neo4j web UI | HTTP | http://localhost:8110 |
| **8111** | plantdata-neo4j-bolt | Neo4j database | TCP | neo4j://localhost:8111 |
| **8112** | plantdata-flower | Celery monitoring | HTTP | http://localhost:8112 |

#### Reserved/Future

| Port | Service | Description | Status |
|------|---------|-------------|--------|
| **8104** | plantdata-pgadmin | PostgreSQL admin | Reserved |
| **8105** | plantdata-api-docs | Standalone docs | Reserved |
| **8106-8108** | - | Available for use | Available |
| **8113-8149** | - | Additional services | Available |
| **8150-8199** | - | Future major features | Reserved |

---

## YupkaQuant Port Adjustments (When Activated)

⚠️ **IMPORTANT:** YupkaQuant must adjust its ports when running alongside NQHUB_v0

### Current vs Required Ports

| Service | Current Port | New Port (Required) | Reason |
|---------|--------------|---------------------|---------|
| **yukpaquan-frontend** | 80 | **9000** | NQHUB uses 3001, avoid web conflicts |
| **yukpaquan-backend** | 8000 | **9001** | NQHUB uses 8002, 8000 is common |
| PostgreSQL | 5433 | **Share 5433** | Use NQHUB's TimescaleDB instance |
| Redis | 6379 | **Share 6379** | Use NQHUB's Redis instance |
| Neo4j HTTP | 7474 | **Share 7474** | Use NQHUB's Neo4j instance |
| Neo4j Bolt | 7687 | **Share 7687** | Use NQHUB's Neo4j instance |
| Mailpit SMTP | 1025 | **Share 1025** | Use NQHUB's Mailpit instance |
| Mailpit UI | 8025 | **Share 8025** | Use NQHUB's Mailpit instance |

### Configuration Files to Update

**Before starting YupkaQuant, update these files:**

#### 1. Frontend (Vite/Docker)
```yaml
# docker-compose.yml or vite.config.ts
server:
  port: 9000  # Changed from 80
ports:
  - "9000:9000"  # Changed from 80:80
```

#### 2. Backend (FastAPI/Docker)
```yaml
# docker-compose.yml
ports:
  - "9001:8000"  # Host 9001 → Container 8000
```

#### 3. Environment Variables
```bash
# .env
FRONTEND_PORT=9000
FRONTEND_URL=http://localhost:9000
BACKEND_PORT=9001
BACKEND_URL=http://localhost:9001
CORS_ORIGINS=http://localhost:9000,http://localhost:9001

# API Base URL in frontend
VITE_API_BASE_URL=http://localhost:9001
```

### Access URLs (After Adjustment)

```bash
YupkaQuant Frontend:     http://localhost:9000
YupkaQuant Backend:      http://localhost:9001
YupkaQuant API Docs:     http://localhost:9001/docs
YupkaQuant API Redoc:    http://localhost:9001/redoc

# Shared Services (NQHUB instances)
PostgreSQL:              localhost:5433
Redis:                   localhost:6379
Neo4j Browser:           http://localhost:7474
Neo4j Bolt:              bolt://localhost:7687
Mailpit UI:              http://localhost:8025
```

### Startup Checklist

Before starting YupkaQuant:
- [ ] Verify NQHUB_v0 is running on its priority ports (3001, 8002, 5433, etc.)
- [ ] Update YupkaQuant docker-compose.yml frontend to port 9000
- [ ] Update YupkaQuant docker-compose.yml backend to port 9001:8000
- [ ] Update YupkaQuant frontend .env with `VITE_API_BASE_URL=http://localhost:9001`
- [ ] Update YupkaQuant backend .env with `CORS_ORIGINS=http://localhost:9000`
- [ ] Verify database connections point to NQHUB services (5433, 6379, etc.)
- [ ] Test access from Windows: http://localhost:9000
- [ ] Verify API communication: http://localhost:9001/docs

---

## Port Conflict Analysis

### Critical Conflicts to Avoid

| Port | Conflict | Resolution |
|------|----------|------------|
| **8080** | Windows svchost.exe (0.0.0.0) | ❌ Never use - Windows system service |
| **3001** | NQHUB frontend | ✅ YupkaQuant uses 9000 |
| **8002** | NQHUB backend | ✅ YupkaQuant uses 9001 |
| **5433** | NQHUB PostgreSQL | ✅ YupkaQuant shares this service |
| **6379** | NQHUB Redis | ✅ YupkaQuant shares this service |
| **7474/7687** | NQHUB Neo4j | ✅ YupkaQuant shares these services |
| **8100-8199** | PlantData range | ✅ No conflicts with any project |

### Port Isolation Strategy

1. **NQHUB_v0 (PRIORITY):** Uses 3001, 8002, 5433, 6379, 7474, 7687, 8025, 1025
2. **YupkaQuant:** Uses 9000-9099 range when active, shares databases with NQHUB
3. **PlantData:** Isolated to 8100-8199 range - no conflicts
4. **Windows:** Avoid 8080 completely

---

## Docker Compose Port Mappings

### PlantData Docker Compose

```yaml
# Host:Container port mapping
services:
  frontend:
    ports: ["8100:8100"]  # Container also uses 8100

  backend:
    ports: ["8101:8000"]  # Container 8000 → Host 8101

  postgres:
    ports: ["8102:5432"]  # Container 5432 → Host 8102

  redis:
    ports: ["8103:6379"]  # Container 6379 → Host 8103

  neo4j:
    ports:
      - "8110:7474"  # HTTP: Container 7474 → Host 8110
      - "8111:7687"  # Bolt: Container 7687 → Host 8111

  flower:
    ports: ["8112:5555"]  # Container 5555 → Host 8112
```

---

## Quick Reference

### Access All Services

```bash
# NQHUB_v0 Services (PRIORITY)
NQHUB Frontend:         http://localhost:3001
NQHUB Backend:          http://localhost:8002
NQHUB API Docs:         http://localhost:8002/api/docs
NQHUB API Redoc:        http://localhost:8002/api/redoc
Mailpit UI:             http://localhost:8025
Neo4j Browser:          http://localhost:7474
RedisInsight:           http://localhost:8001  (docker interno)
Jupyter Notebook:       http://localhost:8888  (optional)

# YupkaQuant Services (When Active - After Port Adjustment)
YupkaQuant Frontend:    http://localhost:9000
YupkaQuant Backend:     http://localhost:9001
YupkaQuant API Docs:    http://localhost:9001/docs

# PlantData Services
PlantData Frontend:     http://localhost:8100  (Docker)
PlantData Frontend Dev: http://localhost:8109  (Local dev)
PlantData API:          http://localhost:8101
PlantData API Docs:     http://localhost:8101/api/docs
Neo4j Browser:          http://localhost:8110
Flower (Celery):        http://localhost:8112
```

### Database Connections

```bash
# NQHUB_v0 Databases (PRIORITY - Shared with YupkaQuant)
PostgreSQL:  localhost:5433  (user: nqhub, db: nqhub, timescale enabled)
Redis:       localhost:6379  (database 0)
Neo4j HTTP:  localhost:7474
Neo4j Bolt:  bolt://localhost:7687

# YupkaQuant (Uses NQHUB databases when active)
PostgreSQL:  localhost:5433  (shared)
Redis:       localhost:6379  (shared, different db index if needed)
Neo4j:       localhost:7474/7687  (shared)

# PlantData Databases (Isolated)
PostgreSQL:  localhost:8102  (user: plantdata, db: plantdata)
Redis:       localhost:8103
Neo4j HTTP:  localhost:8110
Neo4j Bolt:  neo4j://localhost:8111  (user: neo4j)
```

---

## WSL Network Configuration

### WSLRelay Services (NQHUB)
Services exposed from WSL to Windows via wslrelay on 127.0.0.1:
- Ports: 1025, 3001, 6379, 7474, 7687, 8002, 8025, 8888

### Direct Docker Access (PlantData)
Services directly accessible from Windows (Docker Desktop integration):
- Ports 8100-8112 (entire PlantData range)

### Port Forwarding (Windows → WSL)
```powershell
# SSH access to WSL
Windows:2222 → WSL:22
```

---

## Troubleshooting

### Check Port Usage

```bash
# Windows (PowerShell as Admin)
netstat -ano | findstr :8080
Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess

# WSL (Linux)
sudo netstat -tulpn | grep :8100
sudo lsof -i :8100
```

### Common Issues

1. **CORS Errors in PlantData**
   - Ensure both ports in `.env`: `CORS_ORIGINS=http://localhost:8100,http://localhost:8109`

2. **Port Already in Use**
   - Check if another WSL instance is running
   - Verify Docker containers: `docker ps`
   - Kill process using port: `kill $(lsof -t -i:PORT)`

3. **Cannot Access from Windows**
   - Check Windows Firewall rules
   - Verify WSL2 networking: `ip addr show eth0`
   - Check Docker Desktop WSL2 integration

---

## Best Practices

1. **Port Allocation Rules**
   - NQHUB: Keep existing standard ports
   - PlantData: Stay within 8100-8199
   - New projects: Use 9000+ range

2. **Documentation**
   - Update this file when adding new services
   - Document in project-specific PORT_MAP.md
   - Add to docker-compose.yml comments

3. **Conflict Prevention**
   - Always check this file before allocating ports
   - Use `netstat` to verify availability
   - Test access from both WSL and Windows

---

## Maintenance Commands

```bash
# Start NQHUB_v0 services (PRIORITY)
cd ~/projects/NQHUB_v0
docker-compose up -d  # Start infrastructure
cd frontend && pnpm dev  # Start frontend on 3001
cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8002

# Start YupkaQuant (After port adjustment - see checklist above)
cd ~/projects/YupkaQuant
docker-compose up -d  # Ensure ports are 9000/9001

# Start PlantData services
cd /home/ricardo-plant-data/projects/PlantData
./start.sh  # or start.bat from Windows

# Stop all Docker containers
docker stop $(docker ps -q)

# View all listening ports
sudo netstat -tulpn | sort -k4 -n

# Check specific port availability
lsof -i :3001  # Check NQHUB frontend
lsof -i :8002  # Check NQHUB backend
lsof -i :9000  # Check YupkaQuant frontend
```

---

**Note:** This document should be the single source of truth for port allocation on LAPTOP2. Update immediately when changes are made to prevent conflicts.