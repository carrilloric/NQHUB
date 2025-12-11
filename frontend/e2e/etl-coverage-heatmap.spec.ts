import { test, expect } from '@playwright/test';

test.describe('ETL Coverage Heat Map', () => {
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

  test('should display Coverage tab in ETL Dashboard', async ({ page }) => {
    // Check that Coverage tab exists
    const coverageTab = page.locator('[data-testid="coverage-tab"]');
    await expect(coverageTab).toBeVisible();
    await expect(coverageTab).toHaveText('Coverage');
  });

  test('should load coverage heatmap when clicking Coverage tab', async ({ page }) => {
    // Click on Coverage tab
    await page.click('[data-testid="coverage-tab"]');

    // Wait for heatmap to load
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Should show the component
    await expect(page.locator('[data-testid="coverage-heatmap"]')).toBeVisible();
  });

  test('should display summary cards with status counts', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Check summary cards
    const completeCount = page.locator('[data-testid="summary-complete"]');
    const partialCount = page.locator('[data-testid="summary-partial"]');
    const missingCount = page.locator('[data-testid="summary-missing"]');

    await expect(completeCount).toBeVisible();
    await expect(partialCount).toBeVisible();
    await expect(missingCount).toBeVisible();

    // Values should be numbers
    const completeText = await completeCount.textContent();
    const partialText = await partialCount.textContent();
    const missingText = await missingCount.textContent();

    expect(parseInt(completeText || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(partialText || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(missingText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display coverage table with timeframe columns', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Check table exists
    const table = page.locator('[data-testid="coverage-table"]');
    await expect(table).toBeVisible();

    // Check headers include timeframes
    await expect(table.locator('th').filter({ hasText: 'Date' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: '30s' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: '1min' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: '5min' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: '15min' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: '1hr' })).toBeVisible();
  });

  test('should have status filter dropdown', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Check filter exists
    const statusFilter = page.locator('[data-testid="status-filter"]');
    await expect(statusFilter).toBeVisible();

    // Should have expected options
    await expect(statusFilter.locator('option[value="all"]')).toHaveText('All Status');
    await expect(statusFilter.locator('option[value="complete"]')).toHaveText('Complete Only');
    await expect(statusFilter.locator('option[value="partial"]')).toHaveText('Partial Only');
    await expect(statusFilter.locator('option[value="missing"]')).toHaveText('Missing Only');
  });

  test('should filter table by status', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Get initial row count
    const initialRows = page.locator('tr[data-testid^="coverage-row-"]');
    const initialCount = await initialRows.count();

    // If there are rows, test filtering
    if (initialCount > 0) {
      // Select 'complete' filter
      await page.selectOption('[data-testid="status-filter"]', 'complete');

      // Wait for filtering to apply
      await page.waitForTimeout(300);

      // Row count may change (or stay same if all are complete)
      const filteredRows = page.locator('tr[data-testid^="coverage-row-"]');
      const filteredCount = await filteredRows.count();

      // Either rows are filtered or message shows
      if (filteredCount === 0) {
        await expect(page.locator('text=No dates with complete status')).toBeVisible();
      }
    }
  });

  test('should have refresh button', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Find refresh button
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    await expect(refreshButton).toBeVisible();

    // Click refresh
    await refreshButton.click();

    // Should still show data after refresh
    await page.waitForSelector('[data-testid="coverage-heatmap"]');
  });

  test('should show legend with status colors', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Check legend items
    await expect(page.locator('text=Complete').first()).toBeVisible();
    await expect(page.locator('text=Partial').first()).toBeVisible();
    await expect(page.locator('text=Missing').first()).toBeVisible();
  });

  test('should display date range information', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // If there's data, date range should be shown
    const rows = page.locator('tr[data-testid^="coverage-row-"]');
    const count = await rows.count();

    if (count > 0) {
      // Should show "Coverage from X to Y" text
      await expect(page.locator('text=/Coverage from/')).toBeVisible();
    }
  });

  test('should handle loading state', async ({ page }) => {
    // Navigate to Data page
    await page.goto('/data');

    // Click on Coverage tab immediately
    await page.click('[data-testid="coverage-tab"]');

    // Eventually should load the component
    await page.waitForSelector('[data-testid="coverage-heatmap"]', { timeout: 10000 });
  });

  test('should show cells with candle counts', async ({ page }) => {
    // Navigate to Coverage tab
    await page.click('[data-testid="coverage-tab"]');
    await page.waitForSelector('[data-testid="coverage-heatmap"]');

    // Check for coverage cells
    const cells = page.locator('[data-testid^="cell-"]');
    const count = await cells.count();

    // If there are cells, check they have expected structure
    if (count > 0) {
      const firstCell = cells.first();
      await expect(firstCell).toBeVisible();

      // Cell should have a title attribute with candle info
      const title = await firstCell.getAttribute('title');
      expect(title).toBeTruthy();
      expect(title).toContain('candles');
    }
  });
});
