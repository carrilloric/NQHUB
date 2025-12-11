# NQHUB Database Connections Reference

**Updated**: 2025-11-02
**Purpose**: Centralized documentation for all database connections

---

## 📊 Active Databases

### 1. NQHUB PostgreSQL + TimescaleDB (PRIMARY)

**Purpose**: Production database for NQHUB application

**Connection Details**:
```
Host:         localhost
Port:         5433
Database:     nqhub
User:         nqhub
Password:     nqhub_password
Docker:       nqhub_postgres
Image:        timescale/timescaledb:latest-pg15
```

**Connection Strings**:
```bash
# Standard PostgreSQL
postgresql://nqhub:nqhub_password@localhost:5433/nqhub

# Async (SQLAlchemy with asyncpg)
postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub

# psql CLI
psql -h localhost -p 5433 -U nqhub -d nqhub

# Docker exec
docker exec -it nqhub_postgres psql -U nqhub -d nqhub

# With password env var
PGPASSWORD=nqhub_password psql -h localhost -p 5433 -U nqhub -d nqhub
```

**Configuration Files**:
- Backend: `backend/.env`
  ```bash
  DATABASE_URL=postgresql://nqhub:nqhub_password@localhost:5433/nqhub
  DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub
  ```
- Docker: `docker/docker-compose.yml`
  ```yaml
  services:
    postgres:
      container_name: nqhub_postgres
      image: timescale/timescaledb:latest-pg15
      ports:
        - "5433:5432"
  ```

**Database Schema**:
- **Authentication Tables**: `users`, `invitations`, `password_reset_tokens`
- **ETL Tables**: `market_data_ticks` (hypertable), `candlestick_*` (8 timeframes), `rollover_periods`, `processed_files`, `etl_jobs`
- **Migrations**: Managed by Alembic
- **Documentation**: `backend/DATABASE_SCHEMA.md`

**TimescaleDB Features**:
- Hypertable: `market_data_ticks` (partitioned by `ts_event`, 1-day chunks)
- Continuous aggregates: (planned for candlestick tables)
- Compression: (planned after initial data load)

**Common Commands**:
```bash
# List all tables
docker exec nqhub_postgres psql -U nqhub -d nqhub -c "\dt"

# Check table schema
docker exec nqhub_postgres psql -U nqhub -d nqhub -c "\d market_data_ticks"

# View hypertables
docker exec nqhub_postgres psql -U nqhub -d nqhub -c "SELECT * FROM timescaledb_information.hypertables;"

# Database size
docker exec nqhub_postgres psql -U nqhub -d nqhub -c "SELECT pg_size_pretty(pg_database_size('nqhub'));"

# Run migrations
cd backend && source .venv/bin/activate && alembic upgrade head
```

---

### 2. Legacy PostgreSQL (REFERENCE ONLY)

**Purpose**: Read-only reference database from previous NQ orderflow system

**Connection Details**:
```
Host:         localhost
Port:         5432
Database:     nq_orderflow
User:         victor
Password:     victor2108
Location:     Different WSL instance
Status:       READ-ONLY (for reference/migration only)
```

**Connection Strings**:
```bash
# psql CLI
PGPASSWORD=victor2108 psql -h localhost -p 5432 -U victor -d nq_orderflow

# Python (if needed for migration scripts)
postgresql://victor:victor2108@localhost:5432/nq_orderflow
```

**Database Content**:
- Size: 20 GB
- Rows: 99.6M ticks
- Tables: `market_data`, `ohlc_5min`, `futures_contract_ranges`, `processed_files_5min`, `rollover_ticks`
- Documentation: `_reference/docs/LEGACY_DATABASE_SCHEMA.md`
- Metadata: `_reference/docs/database_metadata.json`

**Usage**:
- **DO NOT WRITE** to this database
- Use only for reference and data migration validation
- Schema analysis already completed and documented

---

## 🔴 Redis Stack

**Purpose**: Real-time data, job queue, caching, session storage

**Connection Details**:
```
Host:         localhost
Port:         6379
Docker:       nqhub_redis
Image:        redis/redis-stack:latest
```

**Connection Strings**:
```bash
# Standard Redis
redis://localhost:6379/0

# Redis CLI
redis-cli -h localhost -p 6379

# Docker exec
docker exec -it nqhub_redis redis-cli
```

**Configuration**:
- Backend: `backend/.env`
  ```bash
  REDIS_URL=redis://localhost:6379/0
  ```

**Use Cases**:
- **Database 0**: Session storage, cache
- **Database 1**: Job queue (RQ/Celery for ETL)
- **Database 2**: Real-time market data (RedisTimeSeries)
- **Database 3**: LLM conversation history

**Common Commands**:
```bash
# Check connection
redis-cli ping

# List all keys
redis-cli keys '*'

# Monitor real-time commands
redis-cli monitor

# Check memory usage
redis-cli info memory
```

---

## 🟢 Neo4j Graph Database

**Purpose**: Knowledge graph for AI assistant, relationship mapping

**Connection Details**:
```
HTTP:         http://localhost:7474
Bolt:         bolt://localhost:7687
Docker:       nqhub_neo4j
Image:        neo4j:latest
User:         neo4j
Password:     (check docker/.env)
```

**Connection Strings**:
```bash
# Bolt protocol (Python driver)
bolt://neo4j:password@localhost:7687

# HTTP API
http://localhost:7474
```

**Configuration**:
- Backend: `backend/.env`
  ```bash
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
  ```

**Common Cypher Queries**:
```cypher
// Check connection
MATCH (n) RETURN count(n);

// View all node types
MATCH (n) RETURN DISTINCT labels(n);

// Clear database (DANGER!)
MATCH (n) DETACH DELETE n;
```

---

## 📝 Environment Variables Reference

### Backend (.env)

```bash
# Primary Database
DATABASE_URL=postgresql://nqhub:nqhub_password@localhost:5433/nqhub
DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub

# Redis
REDIS_URL=redis://localhost:6379/0

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Application
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
ELEVENLABS_API_KEY=...
```

### Docker (.env)

```bash
# PostgreSQL
POSTGRES_DB=nqhub
POSTGRES_USER=nqhub
POSTGRES_PASSWORD=nqhub_password
POSTGRES_PORT=5433

# Redis
REDIS_PORT=6379

# Neo4j
NEO4J_AUTH=neo4j/your_password
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474
```

---

## 🔧 Docker Compose Services

### Start All Services

```bash
cd docker
docker-compose up -d

# View logs
docker-compose logs -f postgres redis neo4j

# Stop all services
docker-compose down

# Remove volumes (DANGER: deletes all data)
docker-compose down -v
```

### Individual Service Management

```bash
# PostgreSQL only
docker-compose up -d postgres
docker-compose logs -f postgres
docker-compose stop postgres

# Redis only
docker-compose up -d redis
docker-compose logs -f redis

# Neo4j only
docker-compose up -d neo4j
docker-compose logs -f neo4j
```

---

## 🗄️ Database Migrations

### Alembic (PostgreSQL)

```bash
cd backend
source .venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

**Migration Files Location**: `backend/alembic/versions/`

**Current Migrations**:
1. `e5719b486310` - Users and invitations tables
2. `8d5b0d19c24e` - Password reset tokens
3. `b215073e64fd` - Market data ticks table (TimescaleDB)
4. `0cac37df50d1` - Candlestick tables (8 timeframes)
5. `c32f6b61196a` - Auxiliary tables (rollover_periods, processed_files)

---

## 🔍 Connection Testing

### Test PostgreSQL Connection

```python
# backend/test_db_connection.py
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.fetchone())
    print("✅ PostgreSQL connection successful!")
```

### Test Redis Connection

```python
# backend/test_redis_connection.py
import redis

r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()
print("✅ Redis connection successful!")
```

### Test Neo4j Connection

```python
# backend/test_neo4j_connection.py
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    result = session.run("RETURN 1 AS num")
    print(result.single())
    print("✅ Neo4j connection successful!")

driver.close()
```

---

## 🚨 Port Conflicts

**Important**: Port 5432 is intentionally NOT used by NQHUB to avoid conflicts with the legacy database.

**Port Allocation**:
- `5432` - Reserved for legacy `nq_orderflow` database (different WSL instance)
- `5433` - NQHUB PostgreSQL + TimescaleDB
- `6379` - Redis
- `7474` - Neo4j HTTP
- `7687` - Neo4j Bolt
- `3001` - Frontend dev server
- `8002` - Backend API

**If you see port conflicts**:
```bash
# Check what's using a port
lsof -i :5433
netstat -tulpn | grep 5433

# Stop conflicting service
docker stop nqhub_postgres

# Change port in docker-compose.yml if needed
```

---

## 📚 Related Documentation

- **Database Schema**: `backend/DATABASE_SCHEMA.md`
- **ETL Plan**: `backend/ETL_PLAN.md`
- **Legacy Schema**: `_reference/docs/LEGACY_DATABASE_SCHEMA.md`
- **Data Dictionary**: `_reference/docs/DATA_DICTIONARY.md`
- **CSV Format**: `_reference/docs/csv_format_metadata.json`
- **Main README**: `README.md`

---

## 🔐 Security Notes

### Production Recommendations

1. **Change Default Passwords**: Never use default passwords in production
2. **Use Secrets Management**: Store credentials in env vars or secrets manager
3. **Enable SSL**: Use SSL/TLS for database connections in production
4. **Restrict Network Access**: Bind databases to localhost or private network
5. **Regular Backups**: Implement automated backup strategy
6. **Audit Logging**: Enable PostgreSQL audit logs
7. **Connection Pooling**: Use pgBouncer for PostgreSQL connection pooling

### Development Setup

Current setup is optimized for local development:
- Simple passwords for convenience
- Direct database access without SSL
- Exposed ports on localhost
- No connection pooling

**Do not deploy this configuration to production!**

---

## 🆘 Troubleshooting

### PostgreSQL Connection Refused

```bash
# Check if container is running
docker ps | grep nqhub_postgres

# Restart container
docker restart nqhub_postgres

# Check logs
docker logs nqhub_postgres

# Verify port binding
docker port nqhub_postgres
```

### Redis Connection Timeout

```bash
# Check if Redis is running
docker ps | grep nqhub_redis

# Test connection
redis-cli ping

# Restart if needed
docker restart nqhub_redis
```

### Alembic Migration Errors

```bash
# Check current version
alembic current

# View pending migrations
alembic heads

# Force revision (DANGER: only if you know what you're doing)
alembic stamp head
```

### Permission Denied Errors

```bash
# Fix Docker permissions
sudo chown -R $USER:$USER docker/

# Fix backend permissions
sudo chown -R $USER:$USER backend/
```

---

**Last Updated**: 2025-11-02
**Maintained By**: Development Team
**Questions**: See main README.md or create an issue
