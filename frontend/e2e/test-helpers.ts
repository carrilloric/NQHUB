/**
 * E2E Test Helpers
 *
 * Credenciales y funciones helper para tests de Playwright
 */
import { Page } from '@playwright/test';

/**
 * Credenciales de usuarios de prueba
 *
 * IMPORTANTE: Estas credenciales son para el ambiente de desarrollo.
 * Password configurado en backend/.env como SUPERUSER_PASSWORD
 */
export const TEST_USERS = {
  admin: {
    email: 'admin@nqhub.com',
    password: 'admin_inicial_2024',
    role: 'SUPERUSER'
  },
  // Agregar más usuarios según sea necesario
  // trader: {
  //   email: 'trader@nqhub.com',
  //   password: 'trader_password',
  //   role: 'trader'
  // }
};

/**
 * URLs base para navegación
 */
export const URLS = {
  home: 'http://localhost:3001',
  login: 'http://localhost:3001',
  dashboard: 'http://localhost:3001/dashboard',
  dataModule: 'http://localhost:3001/data',
};

/**
 * Helper para login de usuario
 *
 * @param page - Playwright Page object
 * @param user - Usuario a utilizar (por defecto: admin)
 * @returns Promise que resuelve cuando el login está completo
 */
export async function loginUser(
  page: Page,
  user: keyof typeof TEST_USERS = 'admin'
): Promise<void> {
  const credentials = TEST_USERS[user];

  // Navegar a la página de login
  await page.goto(URLS.login);

  // Llenar formulario
  await page.fill('input[type="email"]', credentials.email);
  await page.fill('input[type="password"]', credentials.password);

  // Click en botón Login (NO "Sign In")
  await page.click('button:has-text("Login")');

  // Esperar navegación al dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Helper para navegar al Data Module
 *
 * @param page - Playwright Page object
 * @param tab - Tab específico a abrir (opcional)
 */
export async function navigateToDataModule(
  page: Page,
  tab?: 'ETL' | 'Charts' | 'Pattern Detection' | 'Market State'
): Promise<void> {
  // Click en Data Module en el nav
  await page.click('a:has-text("Data Module")');
  await page.waitForURL('**/data', { timeout: 10000 });

  // Si se especifica un tab, hacer click
  if (tab) {
    const tabEmoji = {
      'ETL': '🧪',
      'Charts': '📊',
      'Pattern Detection': '🔍',
      'Market State': '📸'
    }[tab];

    await page.click(`button:has-text("${tabEmoji} ${tab}")`);
  }
}

/**
 * Helper para navegar al Market State tab
 *
 * @param page - Playwright Page object
 */
export async function navigateToMarketState(page: Page): Promise<void> {
  await navigateToDataModule(page, 'Market State');
  await page.waitForTimeout(1000); // Esperar que el tab cargue
}

/**
 * Helper para login completo y navegación a Data Module
 *
 * @param page - Playwright Page object
 * @param user - Usuario a utilizar (por defecto: admin)
 */
export async function setupTestSession(
  page: Page,
  user: keyof typeof TEST_USERS = 'admin'
): Promise<void> {
  await loginUser(page, user);
  await navigateToDataModule(page);
}

/**
 * Helper para esperar console logs específicos
 *
 * @param page - Playwright Page object
 * @param searchText - Texto a buscar en console logs
 * @param timeout - Timeout en ms (por defecto: 5000)
 * @returns Promise con los logs encontrados
 */
export async function waitForConsoleLogs(
  page: Page,
  searchText: string,
  timeout: number = 5000
): Promise<string[]> {
  const logs: string[] = [];

  const handleConsole = (msg: any) => {
    const text = msg.text();
    if (text.includes(searchText)) {
      logs.push(text);
    }
  };

  page.on('console', handleConsole);

  await page.waitForTimeout(timeout);

  page.off('console', handleConsole);

  return logs;
}
