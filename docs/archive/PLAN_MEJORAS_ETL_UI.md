# PLAN: Mejorar Visibilidad y Control del ETL Pipeline

**Fecha:** 2025-11-02
**Contexto:** Jobs ETL se quedan en "Pending" sin mostrar progreso real. Necesitamos mejor visibilidad de lo que está pasando internamente.

---

## FASE 1: Diagnóstico y Limpieza (URGENTE)

### 1.1 Verificar Worker RQ
```bash
# Verificar si el worker está corriendo
ps aux | grep rq

# Ver logs del worker
tail -f /path/to/worker.log

# Si no está corriendo, iniciarlo
cd backend
source .venv/bin/activate
rq worker --with-scheduler
```

### 1.2 Limpiar Jobs Actuales
**Opción A - Via UI:**
- Cancelar manualmente cada job desde la interfaz

**Opción B - Via Backend API:**
```bash
# Cancelar todos los jobs pending/active
curl -X DELETE http://localhost:8002/api/v1/etl/jobs/cleanup/pending
```

**Opción C - Directamente en Redis:**
```bash
# Limpiar todas las colas de RQ
redis-cli FLUSHDB
```

### 1.3 Verificar Estado del Sistema
```bash
# Backend FastAPI
lsof -i :8002

# Redis
redis-cli ping

# RQ Worker
ps aux | grep "rq worker"
```

---

## FASE 2: Mejoras de UI - Visibilidad del Progreso

### 2.1 Agregar Log Viewer en Tiempo Real

**Archivo:** `/frontend/src/client/components/data-module/etl/JobLogViewer.tsx` (NUEVO)

**Características:**
```typescript
interface JobLogViewerProps {
  jobId: string;
  autoScroll?: boolean;
  maxLines?: number;
}

// Componente que:
// - Hace polling al endpoint GET /api/v1/etl/jobs/{job_id}/logs
// - Muestra logs en tiempo real con auto-scroll
// - Colores según nivel (INFO, WARNING, ERROR)
// - Timestamps formateados
// - Filtro por nivel de log
```

**Ejemplo de UI:**
```
┌─ Job Logs: GLBX-20240719-W4UAD9HEC5.zip ─────────┐
│ [14:23:01] INFO  Starting extraction...          │
│ [14:23:02] INFO  Found 15 CSV files              │
│ [14:23:03] INFO  Extracting file 1/15...         │
│ [14:23:05] INFO  Parsing OHLC data...            │
│ [14:23:07] WARN  Detected potential gap at...    │
│ [14:23:10] INFO  Inserted 1,234,567 ticks        │
│ [Auto-scroll ON] [Clear] [Download]              │
└───────────────────────────────────────────────────┘
```

### 2.2 Mejorar JobMonitor con Detalles por Step

**Archivo:** `/frontend/src/client/components/data-module/etl/JobMonitor.tsx`

**Cambios:**

1. **Mostrar sub-step actual:**
```tsx
// Antes:
<span>Step 3 of 8</span>

// Después:
<span>Step 3 of 8: Loading Ticks</span>
<span className="text-xs text-muted-foreground">
  Processing file 12/15: GLBX.20240719.csv
</span>
```

2. **Agregar botón "View Logs":**
```tsx
<Button
  size="sm"
  variant="outline"
  onClick={() => setSelectedJobForLogs(job.id)}
>
  <FileText className="size-4 mr-2" />
  View Logs
</Button>
```

3. **Modal de Logs:**
```tsx
<Dialog open={!!selectedJobForLogs}>
  <DialogContent className="max-w-4xl h-[600px]">
    <JobLogViewer jobId={selectedJobForLogs} />
  </DialogContent>
</Dialog>
```

### 2.3 Agregar Filtros Mejorados

**Archivo:** `/frontend/src/client/components/data-module/etl/JobMonitor.tsx`

```tsx
// Agregar botón "Running" (jobs activos)
<Button
  variant={filterStatus === 'running' ? 'default' : 'outline'}
  size="sm"
  onClick={() => handleFilterChange('running')}
  data-testid="filter-running"
>
  Running ({countActiveJobs})
  {countActiveJobs > 0 && <Loader className="ml-2 size-3 animate-spin" />}
</Button>

// Agregar botón "Stop All Active"
{countActiveJobs > 0 && (
  <Button
    variant="destructive"
    size="sm"
    onClick={handleStopAllActive}
  >
    <XCircle className="size-4 mr-2" />
    Stop All Active ({countActiveJobs})
  </Button>
)}
```

### 2.4 Agregar Progress Details Card

**Expandir cada job card con detalles:**
```tsx
<Collapsible>
  <CollapsibleTrigger>
    <ChevronDown className="size-4" />
    Details
  </CollapsibleTrigger>
  <CollapsibleContent>
    <div className="mt-3 space-y-2 text-xs">
      {/* Current file being processed */}
      <div className="flex justify-between">
        <span className="text-muted-foreground">Current File:</span>
        <span className="font-mono">{job.current_csv_file}</span>
      </div>

      {/* Processing rate */}
      <div className="flex justify-between">
        <span className="text-muted-foreground">Rate:</span>
        <span>{job.ticks_per_second?.toLocaleString()} ticks/sec</span>
      </div>

      {/* ETA */}
      <div className="flex justify-between">
        <span className="text-muted-foreground">ETA:</span>
        <span>{calculateETA(job)}</span>
      </div>

      {/* Memory usage */}
      <div className="flex justify-between">
        <span className="text-muted-foreground">Memory:</span>
        <span>{job.memory_usage_mb?.toFixed(1)} MB</span>
      </div>
    </div>
  </CollapsibleContent>
</Collapsible>
```

---

## FASE 3: Mejoras de Backend - Logging y Métricas

### 3.1 Endpoint de Logs

**Archivo:** `/backend/app/etl/routes.py` (AGREGAR)

```python
@router.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,  # INFO, WARNING, ERROR
    db: Session = Depends(get_db)
):
    """
    Get real-time logs for a specific ETL job
    """
    # Query job_logs table
    query = db.query(ETLJobLog).filter(ETLJobLog.job_id == job_id)

    if level:
        query = query.filter(ETLJobLog.level == level)

    logs = query.order_by(ETLJobLog.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()

    return {
        "job_id": job_id,
        "logs": logs,
        "total": query.count()
    }
```

### 3.2 Tabla de Logs

**Archivo:** `/backend/alembic/versions/YYYYMMDD_HHMM_create_etl_job_logs.py` (NUEVO)

```python
def upgrade():
    op.create_table(
        'etl_job_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_id', sa.String(), sa.ForeignKey('etl_jobs.id')),
        sa.Column('level', sa.String(10), nullable=False),  # INFO, WARNING, ERROR
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB(), nullable=True),  # Additional context
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Index('idx_job_logs_job_id', 'job_id'),
        sa.Index('idx_job_logs_created', 'created_at')
    )
```

### 3.3 Logger Wrapper para ETL Tasks

**Archivo:** `/backend/app/etl/utils.py` (AGREGAR)

```python
class ETLJobLogger:
    """Logger that writes to both file and database"""

    def __init__(self, job_id: str, db: Session):
        self.job_id = job_id
        self.db = db
        self.logger = logging.getLogger(f"etl.job.{job_id}")

    def info(self, message: str, **metadata):
        self.logger.info(message)
        self._log_to_db("INFO", message, metadata)

    def warning(self, message: str, **metadata):
        self.logger.warning(message)
        self._log_to_db("WARNING", message, metadata)

    def error(self, message: str, **metadata):
        self.logger.error(message)
        self._log_to_db("ERROR", message, metadata)

    def _log_to_db(self, level: str, message: str, metadata: dict):
        log_entry = ETLJobLog(
            job_id=self.job_id,
            level=level,
            message=message,
            metadata=metadata or {}
        )
        self.db.add(log_entry)
        self.db.commit()
```

### 3.4 Usar Logger en ETL Tasks

**Archivo:** `/backend/app/etl/tasks.py` (MODIFICAR)

```python
def process_etl_job(job_id: str):
    db = get_db_session()
    job = db.query(ETLJob).filter(ETLJob.id == job_id).first()
    logger = ETLJobLogger(job_id, db)

    try:
        # Step 1: Extract
        logger.info("Starting ZIP extraction", file=job.zip_filename)
        zip_path = extract_zip(job.zip_path)
        logger.info(f"Extracted {len(zip_files)} files")

        # Step 2: Parse
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"Parsing file {i}/{len(csv_files)}",
                       file=csv_file.name,
                       size_mb=csv_file.size / 1024 / 1024)

            df = parse_csv(csv_file)
            logger.info(f"Parsed {len(df)} rows")

            # Update progress
            update_job_progress(job_id, i, len(csv_files))

        # Step 3: Load ticks
        logger.info(f"Loading {total_ticks} ticks to database")
        load_ticks(df)
        logger.info(f"Successfully inserted {inserted_count} ticks")

        # ... más steps con logging

    except Exception as e:
        logger.error(f"Job failed: {str(e)}",
                    error_type=type(e).__name__,
                    traceback=traceback.format_exc())
        raise
```

### 3.5 Agregar Métricas de Progreso Detalladas

**Archivo:** `/backend/app/etl/models.py` (MODIFICAR)

```python
class ETLJob(Base):
    # ... campos existentes ...

    # Nuevos campos para tracking detallado
    current_csv_file: str = Column(String, nullable=True)
    csv_files_found: int = Column(Integer, default=0)
    ticks_per_second: float = Column(Float, nullable=True)
    memory_usage_mb: float = Column(Float, nullable=True)
    estimated_completion: datetime = Column(DateTime, nullable=True)
```

---

## FASE 4: Mejoras de Worker - Heartbeat y Monitoring

### 4.1 Heartbeat del Worker

**Problema:** No sabemos si el worker está vivo o trabado.

**Solución:**
```python
# backend/app/etl/worker.py

class WorkerHeartbeat:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.worker_id = f"worker_{os.getpid()}"

    def ping(self):
        """Update heartbeat every 5 seconds"""
        self.redis.setex(
            f"worker:heartbeat:{self.worker_id}",
            10,  # TTL 10 seconds
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "pid": os.getpid(),
                "status": "alive"
            })
        )
```

### 4.2 Endpoint para Worker Status

**Archivo:** `/backend/app/etl/routes.py` (AGREGAR)

```python
@router.get("/worker/status")
async def get_worker_status(redis: Redis = Depends(get_redis)):
    """Check if RQ worker is alive"""
    workers = Worker.all(connection=redis)

    return {
        "workers": [
            {
                "name": w.name,
                "state": w.get_state(),
                "current_job": w.get_current_job_id(),
                "successful_jobs": w.successful_job_count,
                "failed_jobs": w.failed_job_count,
                "total_working_time": w.total_working_time
            }
            for w in workers
        ],
        "total_workers": len(workers),
        "healthy": len(workers) > 0
    }
```

### 4.3 UI para Worker Status

**Agregar badge en ETLDashboard:**

```tsx
// frontend/src/client/components/data-module/etl/ETLDashboard.tsx

const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null);

useEffect(() => {
  const fetchWorkerStatus = async () => {
    const status = await apiClient.getWorkerStatus();
    setWorkerStatus(status);
  };

  fetchWorkerStatus();
  const interval = setInterval(fetchWorkerStatus, 5000);
  return () => clearInterval(interval);
}, []);

// Render:
<div className="flex items-center gap-2 mb-4">
  <Badge variant={workerStatus?.healthy ? 'success' : 'destructive'}>
    {workerStatus?.healthy ? (
      <>
        <Check className="size-3 mr-1" />
        Worker Online ({workerStatus.total_workers})
      </>
    ) : (
      <>
        <AlertCircle className="size-3 mr-1" />
        Worker Offline
      </>
    )}
  </Badge>
</div>
```

---

## FASE 5: Testing y Validación

### 5.1 Script de Test

**Archivo:** `/backend/scripts/test_etl_pipeline.py` (NUEVO)

```python
"""
Script para probar el ETL pipeline completo con logging
"""

import sys
from pathlib import Path

# Upload test file
test_zip = Path("test_data/GLBX-small.zip")
response = upload_zip(test_zip, ["5min"])

print(f"Job ID: {response['job_id']}")

# Monitor progress
while True:
    status = get_job_status(response['job_id'])
    print(f"[{status['status']}] Step {status['current_step']}/{status['total_steps']} - {status['progress_pct']}%")

    # Get latest logs
    logs = get_job_logs(response['job_id'], limit=5)
    for log in logs:
        print(f"  [{log['level']}] {log['message']}")

    if status['status'] in ['completed', 'failed']:
        break

    time.sleep(2)
```

### 5.2 Checklist de Validación

**Antes de considerar completo:**

- [ ] Worker RQ corriendo y reportando heartbeat
- [ ] Jobs progresan de "pending" a siguiente step
- [ ] Logs se guardan en DB en tiempo real
- [ ] UI muestra logs con auto-refresh
- [ ] Progress bar se actualiza correctamente
- [ ] Botón "Stop" cancela job inmediatamente
- [ ] Filtro "Running" muestra solo jobs activos
- [ ] ETA se calcula correctamente
- [ ] Métricas (ticks/sec) se actualizan

---

## FASE 6: Quick Wins (Implementar Primero)

### Orden de Implementación:

**DÍA 1 - Diagnóstico:**
1. ✅ Verificar worker RQ está corriendo
2. ✅ Limpiar jobs viejos
3. ✅ Probar con 1 job pequeño y ver logs del worker

**DÍA 2 - Logging Básico:**
1. ✅ Crear tabla etl_job_logs
2. ✅ Agregar ETLJobLogger
3. ✅ Usar logger en tasks.py
4. ✅ Endpoint GET /jobs/{id}/logs

**DÍA 3 - UI Logs:**
1. ✅ Crear JobLogViewer component
2. ✅ Agregar botón "View Logs" en JobMonitor
3. ✅ Modal con logs en tiempo real

**DÍA 4 - Métricas:**
1. ✅ Agregar campos de progreso detallado (current_file, etc)
2. ✅ Calcular ETA y ticks/sec
3. ✅ Mostrar en UI

**DÍA 5 - Worker Monitoring:**
1. ✅ Heartbeat del worker
2. ✅ Endpoint /worker/status
3. ✅ Badge en UI

**DÍA 6 - Filtros y Bulk Actions:**
1. ✅ Filtro "Running"
2. ✅ Botón "Stop All Active"
3. ✅ Cleanup endpoint

---

## ARCHIVOS A CREAR/MODIFICAR

### Nuevos:
```
backend/app/etl/logger.py              # ETLJobLogger class
backend/app/etl/models.py              # ETLJobLog model
backend/alembic/versions/XXX_logs.py   # Migration para logs
backend/scripts/test_etl_pipeline.py   # Test script
frontend/src/client/components/data-module/etl/JobLogViewer.tsx
```

### Modificar:
```
backend/app/etl/routes.py              # Endpoints de logs y worker status
backend/app/etl/tasks.py               # Usar ETLJobLogger
backend/app/etl/models.py              # Campos adicionales en ETLJob
frontend/src/client/components/data-module/etl/JobMonitor.tsx
frontend/src/client/components/data-module/etl/ETLDashboard.tsx
frontend/src/client/services/api.ts    # Nuevos métodos API
frontend/src/client/types/etl.ts       # Tipos para logs
```

---

## COMANDOS ÚTILES

### Limpiar Todo y Empezar Fresco:
```bash
# 1. Detener todo
pkill -f "rq worker"
pkill -f "uvicorn"

# 2. Limpiar Redis
redis-cli FLUSHDB

# 3. Limpiar DB (opcional - solo si necesitas reset completo)
# psql -U nqhub -d nqhub -c "DELETE FROM etl_jobs;"

# 4. Reiniciar servicios
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002 &
rq worker --with-scheduler &

# 5. Verificar
ps aux | grep -E "(rq|uvicorn)"
redis-cli ping
curl http://localhost:8002/api/v1/etl/worker/status
```

### Monitoring en Tiempo Real:
```bash
# Terminal 1: Logs del backend
tail -f backend/logs/app.log

# Terminal 2: Logs del worker
rq worker --with-scheduler --logging_level DEBUG

# Terminal 3: Redis monitor
redis-cli MONITOR

# Terminal 4: Ver jobs en cola
watch -n 1 'rq info'
```

---

## NOTAS IMPORTANTES

1. **El problema de "Pending sin avanzar"** suele ser:
   - Worker RQ no está corriendo
   - Worker está trabado en un job anterior
   - Redis perdió la conexión
   - Error silencioso en el task que no se logea

2. **Siempre verificar primero:**
   ```bash
   # Worker vivo?
   ps aux | grep "rq worker"

   # Redis vivo?
   redis-cli ping

   # Hay jobs en cola?
   rq info
   ```

3. **Para debugging rápido:**
   - Iniciar worker en foreground: `rq worker --burst`
   - Ver errores inmediatamente en consola
   - Probar con archivo pequeño (1MB) primero

---

## PRÓXIMOS PASOS (Para la Sesión)

1. ✅ **PRIMERO:** Verificar worker está corriendo
2. ✅ **SEGUNDO:** Limpiar jobs actuales
3. ✅ **TERCERO:** Probar con 1 job pequeño y ver si progresa
4. ❌ Si no progresa → Ver logs del worker para encontrar error
5. ❌ Si progresa → Implementar mejoras de UI según prioridad

---

**Fecha de Creación:** 2025-11-02
**Estado:** Plan listo para implementación
**Prioridad:** Alta (jobs están trabados actualmente)
