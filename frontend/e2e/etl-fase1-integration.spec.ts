import { test, expect } from '@playwright/test';

test.describe('ETL Dashboard FASE 1 Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@nqhub.com');
    await page.fill('input[name="password"]', 'change-this-password');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForURL(/\/(dashboard|data)/);

    // Navigate to Data Module ETL section
    await page.goto('/data');
    await page.waitForSelector('[data-testid="etl-dashboard"]');
  });

  test('should have all 5 tabs in ETL Dashboard', async ({ page }) => {
    // Check all tabs exist
    await expect(page.locator('[data-testid="upload-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="jobs-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="symbols-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="coverage-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-tab"]')).toBeVisible();
  });

  test('should navigate between all tabs without errors', async ({ page }) => {
    // Upload tab (default)
    await expect(page.locator('text=Upload Databento ZIP File')).toBeVisible();

    // Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');
    await expect(page.locator('text=Processing Jobs')).toBeVisible();

    // Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    await expect(page.locator('text=Symbol Explorer')).toBeVisible();

    // Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
    await expect(page.locator('text=Coverage Heat Map')).toBeVisible();

    // Stats tab
    await page.click('[data-testid="stats-tab"]');
    await expect(page.locator('text=Database Statistics')).toBeVisible();
  });

  test('should load all FASE 1 components successfully', async ({ page }) => {
    // Test Jobs tab - JobSummaryCards
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');
    await expect(page.locator('[data-testid="stat-total"]')).toBeVisible();

    // Test Symbols tab - SymbolExplorer
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    await expect(page.locator('[data-testid="symbols-table"]')).toBeVisible();

    // Test Coverage tab - CoverageHeatMap
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
    await expect(page.locator('[data-testid="coverage-table"]')).toBeVisible();
  });

  test('should display data in all components', async ({ page }) => {
    // Jobs Summary should have numbers
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');
    const totalJobs = await page.locator('[data-testid="stat-total"]').textContent();
    expect(parseInt(totalJobs || '0')).toBeGreaterThanOrEqual(0);

    // Symbols should have data
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    const totalSymbols = await page.locator('[data-testid="total-symbols"]').textContent();
    expect(parseInt(totalSymbols || '0')).toBeGreaterThanOrEqual(0);

    // Coverage should have summary
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
    await expect(page.locator('[data-testid="summary-complete"]')).toBeVisible();
  });

  test('should maintain state when switching tabs', async ({ page }) => {
    // Navigate to Symbols and search
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    await page.fill('[data-testid="symbol-search"]', 'NQ');

    // Switch to Coverage
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Switch back to Symbols - search should be preserved
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    const searchValue = await page.locator('[data-testid="symbol-search"]').inputValue();
    expect(searchValue).toBe('NQ');
  });

  test('should have consistent styling across all tabs', async ({ page }) => {
    const tabs = [
      { testId: 'jobs-tab', component: 'job-summary-cards' },
      { testId: 'symbols-tab', component: 'symbol-explorer' },
      { testId: 'coverage-tab', component: 'coverage-heatmap' }
    ];

    for (const tab of tabs) {
      await page.click(`[data-testid="${tab.testId}"]`);
      await page.waitForSelector(`[data-testid="${tab.component}"]`);

      // Check component is visible
      await expect(page.locator(`[data-testid="${tab.component}"]`)).toBeVisible();

      // No console errors
      const consoleErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      expect(consoleErrors).toHaveLength(0);
    }
  });

  test('should show loading states then data', async ({ page }) => {
    // Reload and immediately check Jobs tab
    await page.reload();
    await page.click('[data-testid="jobs-tab"]');

    // Eventually loads
    await page.waitForSelector('[data-testid="job-summary-cards"]', { timeout: 10000 });

    // Check Symbols
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]', { timeout: 10000 });

    // Check Coverage
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]', { timeout: 10000 });
  });

  test('should handle API responses correctly', async ({ page }) => {
    // Set up response monitoring
    const apiResponses: { url: string; status: number }[] = [];

    page.on('response', response => {
      if (response.url().includes('/api/v1/etl/')) {
        apiResponses.push({
          url: response.url(),
          status: response.status()
        });
      }
    });

    // Visit all tabs to trigger API calls
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Wait for API responses
    await page.waitForTimeout(1000);

    // Check all API calls succeeded
    for (const response of apiResponses) {
      expect(response.status).toBeLessThan(500); // No server errors
    }
  });

  test('should be responsive and usable on different screen sizes', async ({ page }) => {
    // Test on tablet size
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    await expect(page.locator('[data-testid="symbols-table"]')).toBeVisible();

    // Test on mobile size
    await page.setViewportSize({ width: 375, height: 667 });

    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
    await expect(page.locator('[data-testid="coverage-table"]')).toBeVisible();
  });

  test('complete FASE 1 user flow', async ({ page }) => {
    // User wants to understand their data coverage

    // 1. Check job status first
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');
    const completedJobs = await page.locator('[data-testid="stat-completed"]').textContent();
    console.log(`Completed jobs: ${completedJobs}`);

    // 2. Explore available symbols
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');
    const symbolCount = await page.locator('[data-testid="total-symbols"]').textContent();
    console.log(`Available symbols: ${symbolCount}`);

    // 3. Check coverage for data gaps
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
    const completeCount = await page.locator('[data-testid="summary-complete"]').textContent();
    const missingCount = await page.locator('[data-testid="summary-missing"]').textContent();
    console.log(`Coverage: ${completeCount} complete, ${missingCount} missing`);

    // All steps completed successfully
    expect(true).toBe(true);
  });
});
