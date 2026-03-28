# Pendientes NQHUB - ETL System

**Fecha**: 2025-11-02
**Estado Actual**: FASES 1-3 COMPLETADAS ✅

---

## RESUMEN DEL PROGRESO

### ✅ COMPLETADO:

#### FASE 1: Background Jobs
- RQ Worker configurado y probado
- Redis conectado (puerto 6379)
- Task `process_etl_job()` implementada

#### FASE 2: Servicios ETL (5 archivos)
1. ✅ `app/etl/services/file_handler.py` - Subir y guardar ZIP
2. ✅ `app/etl/services/extractor.py` - Extraer ZIP y descomprimir .zst
3. ✅ `app/etl/services/csv_parser.py` - Parsear CSV de Databento
4. ✅ `app/etl/services/tick_loader.py` - Bulk insert de ticks
5. ✅ `app/etl/services/candle_builder.py` - Agregar candles por timeframe

#### FASE 3: Upload Endpoint
- ✅ `POST /api/v1/etl/upload-zip` actualizado
- ✅ Guarda archivo
- ✅ Encola job en RQ
- ✅ Maneja errores

---

## 🚧 FASE 4: FRONTEND DASHBOARD (PENDIENTE)

### Archivos a Crear:

#### 1. API Service Layer
**Archivo**: `frontend/src/client/services/etl.api.ts`

```typescript
import { apiRequest } from './api';

export interface ETLJob {
  id: string;
  status: string;
  zip_filename: string;
  progress_pct: number;
  current_step: number;
  selected_timeframes: string[] | null;
  csv_files_processed?: number;
  ticks_inserted?: number;
  candles_created?: number;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ETLJobList {
  jobs: ETLJob[];
  total: number;
  skip: number;
  limit: number;
}

export const etlApi = {
  // Subir archivo ZIP
  uploadZip: async (file: File, timeframes: string[]): Promise<ETLJob> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('selected_timeframes', JSON.stringify(timeframes));

    return apiRequest('/etl/upload-zip', {
      method: 'POST',
      body: formData
    });
  },

  // Obtener estado de un job
  getJobStatus: async (jobId: string): Promise<ETLJob> => {
    return apiRequest(`/etl/jobs/${jobId}`);
  },

  // Listar todos los jobs
  listJobs: async (skip = 0, limit = 20, status?: string): Promise<ETLJobList> => {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    });
    if (status) params.append('status', status);

    return apiRequest(`/etl/jobs?${params}`);
  },

  // Cancelar job
  cancelJob: async (jobId: string): Promise<void> => {
    return apiRequest(`/etl/jobs/${jobId}`, { method: 'DELETE' });
  }
};
```

#### 2. Componente de Subida de Archivos
**Archivo**: `frontend/src/client/components/etl/FileUploader.tsx`

**Features**:
- Drag & drop zone
- Validación de archivo (.zip, max 5GB)
- Checkboxes para seleccionar timeframes:
  - [ ] 30s
  - [ ] 1min
  - [ ] 5min
  - [ ] 15min
  - [ ] 1hr
  - [ ] 4hr
  - [ ] Daily
  - [ ] Weekly
  - [ ] Seleccionar todos / Ninguno
- Progress bar durante upload
- Mostrar respuesta del server (job creado)

**Ejemplo de UI**:
```tsx
<div className="border-2 border-dashed rounded-lg p-8">
  <input type="file" accept=".zip" />

  <div className="mt-4">
    <h3>Seleccionar Timeframes</h3>
    <div className="grid grid-cols-4 gap-2">
      {TIMEFRAMES.map(tf => (
        <label key={tf}>
          <input type="checkbox" checked={selected.includes(tf)} />
          {tf}
        </label>
      ))}
    </div>
  </div>

  <button onClick={handleUpload}>Subir y Procesar</button>
</div>
```

#### 3. Monitor de Jobs
**Archivo**: `frontend/src/client/components/etl/JobMonitor.tsx`

**Features**:
- Lista de jobs con paginación
- Para cada job mostrar:
  - Status badge (pending, extracting, parsing, loading_ticks, building_candles, completed, failed)
  - Progress bar (0-100%)
  - Nombre de archivo
  - Timeframes seleccionados
  - Estadísticas (ticks insertados, candles creados)
  - Tiempo transcurrido
  - Botón para cancelar (si está en progreso)
- Polling cada 2 segundos para jobs activos
- Auto-refresh de la lista
- Filtros por status

**Ejemplo de card de job**:
```tsx
<div className="border rounded p-4">
  <div className="flex justify-between">
    <span>{job.zip_filename}</span>
    <StatusBadge status={job.status} />
  </div>

  <ProgressBar value={job.progress_pct} />

  <div className="mt-2 text-sm">
    <span>Timeframes: {job.selected_timeframes?.join(', ')}</span>
    <span>Ticks: {job.ticks_inserted?.toLocaleString()}</span>
    <span>Candles: {job.candles_created?.toLocaleString()}</span>
  </div>

  {job.status === 'failed' && (
    <div className="text-red-500">{job.error_message}</div>
  )}
</div>
```

#### 4. Página Principal ETL
**Archivo**: `frontend/src/client/pages/ETLDashboard.tsx`

**Layout**:
```tsx
<div className="p-6">
  <h1>ETL Dashboard</h1>

  <Tabs>
    <TabList>
      <Tab>Upload</Tab>
      <Tab>Jobs</Tab>
      <Tab>Coverage</Tab>
    </TabList>

    <TabPanel>
      <FileUploader onUploadSuccess={(job) => {
        // Navegar a tab Jobs
        // Iniciar polling para ese job
      }} />
    </TabPanel>

    <TabPanel>
      <JobMonitor />
    </TabPanel>

    <TabPanel>
      <CoverageHeatmap />
    </TabPanel>
  </Tabs>
</div>
```

#### 5. Heatmap de Cobertura (Opcional - puede ser posterior)
**Archivo**: `frontend/src/client/components/etl/CoverageHeatmap.tsx`

**Features**:
- Grid con días (rows) y timeframes (cols)
- Colores:
  - Verde: completed
  - Amarillo: processing
  - Rojo: failed
  - Gris: pending/sin datos
- Tooltip al hover mostrando detalles
- Filtro por símbolo y rango de fechas

---

## ORDEN DE IMPLEMENTACIÓN RECOMENDADO:

### Paso 1: API Service (5 minutos)
- Crear `etl.api.ts` con las funciones de API

### Paso 2: FileUploader Component (30 minutos)
- Crear componente básico de upload
- Agregar drag & drop
- Agregar checkboxes de timeframes
- Integrar con API

### Paso 3: JobMonitor Component (45 minutos)
- Crear lista de jobs
- Agregar progress bars
- Implementar polling para jobs activos
- Agregar botones de acción (cancelar, refresh)

### Paso 4: ETLDashboard Page (15 minutos)
- Crear página con tabs
- Integrar FileUploader y JobMonitor
- Agregar navegación en App.tsx

### Paso 5: Styling & Polish (30 minutos)
- Mejorar UI/UX
- Agregar animaciones
- Responsive design

**Tiempo estimado total**: 2-3 horas

---

## TESTING DEL SISTEMA COMPLETO

### Prerequisitos:
1. PostgreSQL + TimescaleDB en puerto 5433
2. Redis en puerto 6379
3. Backend en puerto 8002
4. Frontend en puerto 3000/5173

### Pasos:

#### 1. Iniciar Worker (Terminal 1)
```bash
cd backend
source .venv/bin/activate
python3 -m app.etl.worker
```

#### 2. Iniciar Backend (Terminal 2)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

#### 3. Iniciar Frontend (Terminal 3)
```bash
cd frontend
pnpm dev
```

#### 4. Test Flow:
1. Login como admin
2. Navegar a `/data/etl` o `/etl-dashboard`
3. Subir archivo ZIP de Databento
4. Seleccionar timeframes (ej: 5min, 1hr)
5. Click "Subir y Procesar"
6. Ver progreso en tiempo real
7. Verificar en PostgreSQL:
   ```sql
   SELECT * FROM etl_jobs ORDER BY created_at DESC LIMIT 1;
   SELECT COUNT(*) FROM market_data_ticks;
   SELECT COUNT(*) FROM candlestick_5min;
   SELECT COUNT(*) FROM candlestick_1hr;
   ```

---

## PENDIENTES ADICIONALES (Menor Prioridad)

### Backend:
1. **Rollover Detection** - Implementar algoritmo de detección
2. **Volume Profile Metrics** - POC, absorption, orderflow detail
3. **Cleanup Job Files** - Borrar archivos temporales después de procesar
4. **Error Recovery** - Retry logic para jobs fallidos
5. **Job Prioritization** - Queue con prioridades

### Frontend:
1. **Coverage Heatmap** - Visualización de cobertura por día/timeframe
2. **Statistics Panel** - Dashboard con métricas generales
3. **Real-time Updates** - WebSocket en lugar de polling
4. **Job History** - Historial completo con búsqueda y filtros
5. **Download Results** - Exportar logs de jobs

### DevOps:
1. **Docker Compose** - Setup completo con PostgreSQL, Redis, Backend, Worker
2. **Monitoring** - Métricas de jobs, performance
3. **Logging** - Centralizar logs de workers
4. **Tests** - Unit tests para servicios ETL
5. **CI/CD** - Pipeline para deploy automático

---

## ARCHIVOS DE DOCUMENTACIÓN

1. **ETL_STATUS.md** - Estado actual completo
2. **ETL_PLAN.md** - Plan original de 7 fases
3. **PENDIENTES.md** - Este archivo
4. **CLAUDE.md** - Context para Claude Code (proyecto general)

---

## COMANDOS ÚTILES PARA REANUDAR

### Ver estado de servicios:
```bash
# Redis
docker ps | grep redis

# PostgreSQL
docker ps | grep timescale

# Worker status
cd backend && source .venv/bin/activate && python3 -c "from app.etl.worker import get_redis_connection; from rq import Queue; conn = get_redis_connection(); queue = Queue('etl_queue', connection=conn); print(f'Jobs: {len(queue)}')"

# Backend logs
tail -f backend/logs/app.log
```

### Limpiar para testing:
```sql
-- Limpiar jobs de prueba
DELETE FROM etl_jobs WHERE status IN ('failed', 'pending');

-- Limpiar ticks de prueba
DELETE FROM market_data_ticks WHERE symbol = 'TEST';

-- Limpiar candles de prueba
DELETE FROM candlestick_5min WHERE symbol = 'TEST';
```

---

## PRÓXIMO PASO INMEDIATO

Cuando reanudes después de limpiar contexto:

1. Lee este archivo: `backend/PENDIENTES.md`
2. Lee: `backend/ETL_STATUS.md` para contexto completo
3. Comienza FASE 4 creando:
   - `frontend/src/client/services/etl.api.ts`
   - `frontend/src/client/components/etl/FileUploader.tsx`
   - `frontend/src/client/components/etl/JobMonitor.tsx`
   - `frontend/src/client/pages/ETLDashboard.tsx`
4. Agrega ruta en `App.tsx`: `/etl` → ETLDashboard

**Comando para empezar**:
```bash
# Terminal 1: Worker
cd backend && source .venv/bin/activate && python3 -m app.etl.worker

# Terminal 2: Backend (ya está corriendo)

# Terminal 3: Frontend (ya está corriendo)

# Terminal 4: Desarrollo
cd frontend/src/client
# Crear archivos de FASE 4
```
