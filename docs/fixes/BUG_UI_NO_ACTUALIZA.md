# BUG: Cambios de UI no se reflejan en navegadores

## Fecha
2025-11-02

## Descripción del Problema

Se realizaron cambios en el componente `DataIngestETLSection.tsx` para:
1. Eliminar el mensaje "Mock data for staging environment insight"
2. Expandir la ventana de Pipeline Monitoring de 520px a 800px
3. Eliminar sección "INGESTION WORKFLOW"

**Síntoma:** Los cambios NO se ven en navegadores (Edge, Chrome) pero **SÍ se ven en Playwright**.

## Archivos Modificados

### `/frontend/src/client/components/data-module/DataIngestETLSection.tsx`

**Cambios aplicados:**

```typescript
// LÍNEAS 34-43: Header sin mensaje "Mock data"
<header className="flex flex-col gap-2 pb-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
  <div className="flex-1">
    <p className="text-[0.65rem] font-semibold uppercase tracking-[0.26em] text-muted-foreground/70">
      Pipeline Monitoring
    </p>
    <h3 className="text-xl font-semibold text-foreground/90">
      ETL orchestration health and job telemetry
    </h3>
  </div>
</header>

// LÍNEA 45: Ventana expandida
<div className="max-h-[800px] overflow-y-auto pr-1">
  <ETLDashboard />
</div>
```

**Antes era:**
```typescript
<span className="text-xs uppercase tracking-[0.24em] text-muted-foreground/60">
  Mock data for staging environment insight
</span>

<div className="max-h-[520px] overflow-y-auto pr-1">
```

## Pruebas Realizadas

### ✅ Playwright Test - PASA
```bash
pnpm test:e2e etl-upload.spec.ts
# Resultado: 14/14 tests passed
```

### ✅ Verificación Manual con Playwright
```javascript
// Script: test-ui-changes.mjs
// Resultado:
❌ "INGESTION WORKFLOW" presente: false  ✅ CORRECTO
❌ "Mock data for staging environment insight" presente: false  ✅ CORRECTO
✅ "Pipeline Monitoring" presente: true  ✅ CORRECTO
✅ Container con max-h-[800px] encontrado: true  ✅ CORRECTO
```

Screenshot: `/tmp/data-module-current.png` - Muestra los cambios correctamente aplicados.

### ❌ Navegadores Reales - FALLAN

**Edge:**
- Sigue mostrando "INGESTION WORKFLOW"
- Sigue mostrando "Mock data for staging environment insight"
- NO ve los cambios

**Chrome:**
- Mismo comportamiento que Edge
- NO ve los cambios

**Chrome Incognito:**
- Mismo comportamiento
- NO ve los cambios

## Intentos de Solución

1. ✅ Hard refresh: `Ctrl + Shift + R` - NO funcionó
2. ✅ Borrar caché del navegador - NO funcionó
3. ✅ Modo incógnito - NO funcionó
4. ✅ Reiniciar servidor Vite - NO funcionó
5. ✅ Cerrar navegador completamente - NO funcionó
6. ✅ Probar en navegador diferente (Chrome) - NO funcionó

## Estado del Servidor

```
Frontend (Vite): http://localhost:3001 - RUNNING
Backend (FastAPI): http://localhost:8002 - RUNNING
Redis: port 6379 - RUNNING
RQ Worker: PID 847646 - RUNNING
```

## Logs de Vite

Vite reporta HMR updates correctamente:
```
2:13:14 PM [vite] (client) hmr update /src/client/components/data-module/DataIngestETLSection.tsx
2:13:17 PM [vite] (client) hmr update /src/client/components/data-module/DataIngestETLSection.tsx
2:34:16 PM [vite] (client) hmr update /src/client/components/data-module/DataIngestETLSection.tsx
```

## Hipótesis

1. **Posible duplicación de componente**: Puede haber otro archivo con contenido similar que se esté renderizando
2. **Problema de routing**: El componente modificado no es el que se renderiza en la ruta `/data`
3. **Problema de build**: Vite puede estar sirviendo una versión en caché del build
4. **LocalStorage/SessionStorage**: Puede haber estado guardado en el navegador que sobrescribe el renderizado

## Siguiente Paso Recomendado

1. Verificar dónde se importa `DataIngestETLSection` y si hay múltiples instancias
2. Buscar si hay otro componente similar que contenga el texto "INGESTION WORKFLOW"
3. Verificar si hay algún sistema de feature flags o configuración que sobrescriba el componente
4. Hacer un build de producción (`pnpm build`) y verificar si el problema persiste

## Código de Verificación

Para verificar que Playwright ve los cambios:
```bash
node test-ui-changes.mjs
```

Para ver screenshot de lo que Playwright renderiza:
```bash
# Ver screenshot en:
/tmp/data-module-current.png
```

## Contacto
Si necesitas ayuda adicional, este bug requiere investigación más profunda del sistema de routing y componentes de React.
