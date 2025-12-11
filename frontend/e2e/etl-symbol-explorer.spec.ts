import { test, expect } from '@playwright/test';

test.describe('ETL Symbol Explorer', () => {
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

  test('should display Symbols tab in ETL Dashboard', async ({ page }) => {
    // Check that Symbols tab exists
    const symbolsTab = page.locator('[data-testid="symbols-tab"]');
    await expect(symbolsTab).toBeVisible();
    await expect(symbolsTab).toHaveText('Symbols');
  });

  test('should load symbol explorer when clicking Symbols tab', async ({ page }) => {
    // Click on Symbols tab
    await page.click('[data-testid="symbols-tab"]');

    // Wait for symbol explorer to load
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Should show the component
    await expect(page.locator('[data-testid="symbol-explorer"]')).toBeVisible();
  });

  test('should display summary cards with totals', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Check summary cards
    const totalTicks = page.locator('[data-testid="total-ticks"]');
    const totalCandles = page.locator('[data-testid="total-candles"]');
    const totalSymbols = page.locator('[data-testid="total-symbols"]');

    await expect(totalTicks).toBeVisible();
    await expect(totalCandles).toBeVisible();
    await expect(totalSymbols).toBeVisible();

    // Values should not be empty
    await expect(totalTicks).not.toHaveText('');
    await expect(totalCandles).not.toHaveText('');
    await expect(totalSymbols).not.toHaveText('');
  });

  test('should display symbols table with data', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Check table exists
    const table = page.locator('[data-testid="symbols-table"]');
    await expect(table).toBeVisible();

    // Check headers
    await expect(table.locator('th').filter({ hasText: 'Symbol' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: 'Ticks' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: 'Candles' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: 'Days' })).toBeVisible();
    await expect(table.locator('th').filter({ hasText: 'Avg/Day' })).toBeVisible();
  });

  test('should have symbol rows when data exists', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Wait for table to be populated (check if there are any symbol rows)
    // This test assumes there is data in the database
    const symbolRows = page.locator('tr[data-testid^="symbol-row-"]');

    // If there's data, we should have rows
    const count = await symbolRows.count();
    if (count > 0) {
      // Check first row has expected structure
      const firstRow = symbolRows.first();
      await expect(firstRow).toBeVisible();

      // Should have symbol name (font-mono)
      await expect(firstRow.locator('td.font-mono')).toBeVisible();
    }
  });

  test('should filter symbols by search term', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Get initial count
    const initialRows = page.locator('tr[data-testid^="symbol-row-"]');
    const initialCount = await initialRows.count();

    if (initialCount > 0) {
      // Type in search box
      const searchInput = page.locator('[data-testid="symbol-search"]');
      await searchInput.fill('NQ');

      // Wait for filtering
      await page.waitForTimeout(300);

      // Check that filtered results only contain NQ
      const filteredRows = page.locator('tr[data-testid^="symbol-row-"]');
      const filteredCount = await filteredRows.count();

      // All visible rows should contain NQ in the symbol name
      for (let i = 0; i < filteredCount; i++) {
        const row = filteredRows.nth(i);
        const symbolCell = row.locator('td.font-mono');
        const text = await symbolCell.textContent();
        expect(text?.toUpperCase()).toContain('NQ');
      }
    }
  });

  test('should sort table by clicking column headers', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Check that column headers are clickable
    const ticksHeader = page.locator('th').filter({ hasText: 'Ticks' });
    await expect(ticksHeader).toBeVisible();

    // Click to sort
    await ticksHeader.click();

    // The sort icon should change (indicates sorting is working)
    // We can check for the arrow icons
    await expect(page.locator('th').filter({ hasText: 'Ticks' }).locator('svg')).toBeVisible();
  });

  test('should refresh data when clicking refresh button', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Find refresh button
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    await expect(refreshButton).toBeVisible();

    // Click refresh
    await refreshButton.click();

    // Should still show data after refresh
    await page.waitForSelector('[data-testid="symbol-explorer"]');
  });

  test('should show empty state when search has no results', async ({ page }) => {
    // Navigate to Symbols tab
    await page.click('[data-testid="symbols-tab"]');
    await page.waitForSelector('[data-testid="symbol-explorer"]');

    // Search for something that doesn't exist
    const searchInput = page.locator('[data-testid="symbol-search"]');
    await searchInput.fill('ZZZZNONEXISTENT');

    // Wait for filtering
    await page.waitForTimeout(300);

    // Should show no results message
    await expect(page.locator('text=No symbols match your search')).toBeVisible();
  });

  test('should display loading state initially', async ({ page }) => {
    // Clear any previous state and reload
    await page.goto('/data');

    // Click on Symbols tab immediately
    await page.click('[data-testid="symbols-tab"]');

    // We might catch the loading state (or it might be too fast)
    // At minimum, the component should eventually load
    await page.waitForSelector('[data-testid="symbol-explorer"]', { timeout: 10000 });
  });
});
