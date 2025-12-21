# E2E Tests - Playwright

## Credenciales de Prueba

Las credenciales están centralizadas en `e2e/test-helpers.ts`:

```typescript
import { TEST_USERS } from './test-helpers';

// Usuario admin
TEST_USERS.admin.email     // 'admin@nqhub.com'
TEST_USERS.admin.password  // 'admin_inicial_2024'
```

**IMPORTANTE:** El password proviene de `backend/.env`:
```bash
SUPERUSER_EMAIL=admin@nqhub.com
SUPERUSER_PASSWORD=admin_inicial_2024
```

## Helpers Disponibles

### Login Automático

```typescript
import { loginUser } from './test-helpers';

test('my test', async ({ page }) => {
  await loginUser(page);  // Login como admin por defecto
  // Usuario ya está logueado y en el dashboard
});
```

### Navegación al Data Module

```typescript
import { navigateToDataModule, navigateToMarketState } from './test-helpers';

test('data module test', async ({ page }) => {
  await loginUser(page);
  await navigateToDataModule(page, 'Market State');
  // Ya estás en el tab de Market State
});

// O usar el helper específico:
test('market state test', async ({ page }) => {
  await loginUser(page);
  await navigateToMarketState(page);
});
```

### Setup Completo

```typescript
import { setupTestSession } from './test-helpers';

test('full flow', async ({ page }) => {
  await setupTestSession(page);  // Login + navegación al Data Module
  // Listo para comenzar el test
});
```

## Ejecutar Tests

```bash
# Todos los tests
pnpm test:e2e

# Test específico
pnpm playwright test e2e/market-state-complete.spec.ts

# Con UI mode (recomendado para debugging)
pnpm playwright test --ui

# Con browser visible
pnpm playwright test --headed
```

## Debugging

### Ver Console Logs del Browser

```typescript
page.on('console', msg => console.log('BROWSER:', msg.text()));
```

### Screenshots Automáticos

Los screenshots se guardan automáticamente en `test-results/` cuando un test falla.

### Video Grabación

Videos se graban automáticamente y se guardan en `test-results/`.

## Notas Importantes

1. **Button Text:** El botón de login dice `"Login"`, NO `"Sign In"`
2. **Password:** Es `admin_inicial_2024`, NO `admin123`
3. **baseURL:** Los tests usan `http://localhost:3001` (configurado en `playwright.config.ts`)
4. **Web Server:** Playwright inicia automáticamente el frontend con `pnpm dev`

## Tests Existentes

- `market-state-complete.spec.ts` - Test completo del flujo de Market State
- `footprint-*.spec.ts` - Tests de Footprint charts
- `etl-*.spec.ts` - Tests del pipeline ETL

## Agregar Nuevos Tests

1. Crear archivo `e2e/my-test.spec.ts`
2. Importar helpers:
   ```typescript
   import { test, expect } from '@playwright/test';
   import { loginUser, navigateToDataModule } from './test-helpers';
   ```
3. Usar los helpers para setup rápido:
   ```typescript
   test.beforeEach(async ({ page }) => {
     await loginUser(page);
     await navigateToDataModule(page);
   });
   ```

## Troubleshooting

### "Timeout waiting for Login button"
- Verificar que el texto sea `"Login"` y no `"Sign In"`
- Verificar que el frontend esté corriendo en puerto 3001

### "Incorrect email or password"
- Verificar password en `backend/.env`
- Debe ser `admin_inicial_2024`

### Tests lentos
- Usar `test.beforeEach` para compartir setup entre tests
- Considerar usar `storageState` para reutilizar sesión autenticada
