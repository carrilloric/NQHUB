import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('🌐 Navegando a http://localhost:3001...');
  await page.goto('http://localhost:3001');
  await page.waitForLoadState('networkidle');
  
  console.log('📝 Logueando como admin...');
  await page.fill('input[name="email"], input[type="email"]', 'admin@nqhub.com');
  await page.fill('input[name="password"], input[type="password"]', 'admin_inicial_2024');
  await page.click('button[type="submit"]');
  await page.waitForURL('http://localhost:3001/dashboard', { timeout: 10000 });
  
  console.log('📂 Navegando a Data Module...');
  await page.goto('http://localhost:3001/data');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Tomar screenshot
  await page.screenshot({ path: '/tmp/data-module-current.png', fullPage: true });
  console.log('📸 Screenshot guardado en /tmp/data-module-current.png');
  
  // Buscar textos específicos
  const bodyText = await page.textContent('body');
  
  console.log('\n=== VERIFICACIÓN DE CAMBIOS ===');
  console.log('❌ "INGESTION WORKFLOW" presente:', bodyText.includes('INGESTION WORKFLOW'));
  console.log('❌ "Mock data for staging environment insight" presente:', bodyText.includes('Mock data for staging environment insight'));
  console.log('✅ "Pipeline Monitoring" presente:', bodyText.includes('Pipeline Monitoring'));
  console.log('✅ "ETL orchestration" presente:', bodyText.includes('ETL orchestration'));
  
  // Verificar el max-height del div
  const jobsContainer = await page.locator('div.max-h-\\[800px\\]').count();
  console.log('✅ Container con max-h-[800px] encontrado:', jobsContainer > 0);
  
  await browser.close();
  console.log('\n✅ Test completado');
})();
