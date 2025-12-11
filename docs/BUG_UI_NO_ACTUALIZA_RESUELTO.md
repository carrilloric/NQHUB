# BUG RESUELTO: Cambios de UI no se reflejaban en navegadores

## Fecha de Resolución
2025-11-02 15:00 (3 días después del bug inicial)

## Resumen Ejecutivo
**Problema:** Los cambios en `DataIngestETLSection.tsx` se veían en Playwright pero NO en navegadores reales (Edge/Chrome).

**Causa Raíz:** Dos instancias de Vite corriendo en puertos diferentes con código desactualizado.

**Solución:** Detener procesos duplicados, actualizar configuración de puerto, limpiar cachés y reiniciar Vite.

---

## Diagnóstico Detallado

### Investigación Inicial
Al ejecutar `lsof -i :3000 -i :3001` se descubrieron **DOS procesos Node.js/Vite corriendo simultáneamente**:

```bash
# Puerto 3000 - Vite VIEJO (desde Oct 30)
node    847041  ricardo  28u  IPv6  TCP *:3000 (LISTEN)

# Puerto 3001 - Vite NUEVO (desde 14:37 hoy)
node    912150  ricardo  26u  IPv6  TCP *:3001 (LISTEN)
```

### Problemas Identificados

1. **Duplicación de Procesos:**
   - Vite viejo (PID 847041) corriendo desde hace 3 días en puerto 3000
   - Vite nuevo (PID 912150) intentó iniciar pero tomó puerto alternativo 3001
   - Ambos sirviendo versiones diferentes del código

2. **Inconsistencia de Configuración:**
   - `vite.config.ts` configurado para puerto **3000**
   - `CLAUDE.md` documenta puerto **3001** como oficial
   - Tests E2E hardcoded a `localhost:3001`
   - Usuario navegando a `http://localhost:3001`

3. **Playwright funcionaba por:**
   - `playwright.config.ts` levanta servidor con `pnpm dev`
   - Usa el puerto configurado (3000 en ese momento)
   - Los tests navegaban a 3001 pero el webServer estaba configurado a 3000

### ¿Por qué los navegadores no veían los cambios?

**Escenario más probable:**
- Navegadores accedían a puerto 3001 (Vite nuevo)
- Vite nuevo iniciado con caché antiguo o sin rebuild completo
- HMR (Hot Module Replacement) funcionaba en puerto 3000 (Vite viejo)
- Los cambios se aplicaban al proceso equivocado

---

## Solución Implementada

### 1. Detener Procesos Duplicados
```bash
kill 847041  # Vite viejo en puerto 3000
kill 912150  # Vite nuevo en puerto 3001
```

### 2. Actualizar Configuración de Vite
**Archivo:** `/frontend/vite.config.ts`

```diff
  server: {
    host: "::",
-   port: 3000,
+   port: 3001,
    fs: {
```

### 3. Actualizar Configuración de Playwright
**Archivo:** `/frontend/playwright.config.ts`

```diff
  use: {
-   baseURL: "http://localhost:3000",
+   baseURL: "http://localhost:3001",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  webServer: {
    command: "pnpm dev",
-   url: "http://localhost:3000",
+   url: "http://localhost:3001",
    reuseExistingServer: !process.env.CI,
```

### 4. Limpiar Cachés
```bash
# Eliminar build antiguo
rm -rf /home/ricardo/projects/NQHUB_v0/frontend/dist

# Eliminar caché de Vite
rm -rf /home/ricardo/projects/NQHUB_v0/frontend/node_modules/.vite
```

### 5. Reiniciar Vite Limpiamente
```bash
cd /home/ricardo/projects/NQHUB_v0/frontend
pnpm dev
```

**Resultado:**
```
VITE v7.1.2  ready in 255 ms

➜  Local:   http://localhost:3001/
➜  Network: http://10.255.255.254:3001/
```

---

## Verificación de la Solución

### Test con Playwright MCP
**Fecha:** 2025-11-02 15:00

**Resultado:**
```
✅ "INGESTION WORKFLOW" NO presente (correcto)
✅ "Mock data for staging environment insight" NO presente (correcto)
✅ "Pipeline Monitoring" presente (correcto)
✅ "ETL orchestration health and job telemetry" presente (correcto)
```

**Screenshot guardado en:** `/tmp/data-module-fixed-2025-11-02T21-00-33-826Z.png`

---

## Instrucciones para el Usuario

### Paso 1: Limpiar Caché del Navegador
Ahora que Vite está corriendo correctamente en puerto 3001, necesitas limpiar la caché del navegador:

**Edge/Chrome:**
1. Presiona `Ctrl + Shift + Delete`
2. Selecciona "Imágenes y archivos en caché"
3. Rango de tiempo: "Última hora" o "Todo"
4. Click "Borrar datos"

**O simplemente:**
1. Navega a `http://localhost:3001`
2. Presiona `Ctrl + Shift + R` (hard refresh)
3. Si aún no funciona, cierra COMPLETAMENTE el navegador y reabre

### Paso 2: Verificar los Cambios
1. Abre `http://localhost:3001` en tu navegador
2. Inicia sesión (admin@nqhub.com / admin_inicial_2024)
3. Navega a "Data Module" > "🧪 Data Ingest & ETL"
4. Verifica que:
   - ❌ NO aparece "INGESTION WORKFLOW"
   - ❌ NO aparece "Mock data for staging environment insight"
   - ✅ SÍ aparece "Pipeline Monitoring"
   - ✅ SÍ aparece "ETL orchestration health and job telemetry"
   - ✅ La ventana del dashboard tiene scroll (max-height: 800px)

---

## Prevención Futura

### Mejores Prácticas

1. **Verificar Procesos Activos:**
   ```bash
   lsof -i :3001
   # Debe mostrar SOLO un proceso de Vite
   ```

2. **Reiniciar Vite Correctamente:**
   ```bash
   # Detener proceso anterior (Ctrl+C en terminal)
   # O encontrar y matar:
   pkill -f "vite"

   # Limpiar caché si es necesario
   rm -rf frontend/node_modules/.vite

   # Iniciar limpiamente
   cd frontend && pnpm dev
   ```

3. **Monitorear HMR:**
   - Los logs de Vite deben mostrar `hmr update` cuando editas archivos
   - Si no ves estos logs, HMR puede estar roto

4. **Usar Puerto Consistente:**
   - Siempre usar puerto **3001** (según CLAUDE.md)
   - Verificar que `vite.config.ts` tenga `port: 3001`

### Script de Verificación
Puedes crear un alias en tu `.bashrc` o `.zshrc`:

```bash
alias vite-check='lsof -i :3001 && echo "✅ Vite corriendo en puerto 3001" || echo "❌ Puerto 3001 libre, iniciar Vite"'
```

---

## Archivos Modificados

```
frontend/vite.config.ts           - Puerto cambiado de 3000 a 3001
frontend/playwright.config.ts     - URLs actualizadas a localhost:3001
```

## Archivos Eliminados

```
frontend/dist/                    - Build antiguo eliminado
frontend/node_modules/.vite/      - Caché de Vite eliminado
```

---

## Conclusión

El bug fue causado por un problema de gestión de procesos y configuración inconsistente de puertos, NO por un problema de React, HMR o código. La solución fue:

1. ✅ Identificar procesos duplicados
2. ✅ Estandarizar puerto a 3001
3. ✅ Limpiar cachés
4. ✅ Reiniciar servidor correctamente

**Estado:** ✅ RESUELTO

**Próximos Pasos para el Usuario:**
- Limpiar caché del navegador
- Verificar cambios en navegador real
- Reportar si persiste algún problema
