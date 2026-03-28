/**
 * Pattern Detection Page E2E Test
 *
 * Tests:
 * 1. Login and navigation to Pattern Detection page
 * 2. Tab switching between FVG, Order Blocks, and Liquidity Pools
 * 3. Filters functionality (timeframe, date range, symbol)
 * 4. Data loading and display in tables
 * 5. Chart visualization
 * 6. Pattern detail display
 * 7. Pagination
 */
import { test, expect } from '@playwright/test';

test.describe('Pattern Detection - Complete Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3001');

    // Login
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Navigate directly to Pattern Detection page
    await page.goto('http://localhost:3001/pattern-detection');
    await page.waitForURL('**/pattern-detection', { timeout: 10000 });
  });

  test('should display Pattern Detection page with 3 tabs', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1:has-text("Pattern Detection")')).toBeVisible();

    // Check subtitle
    await expect(page.locator('p:has-text("ICT pattern analysis with candlestick chart overlays")')).toBeVisible();

    // Check tabs are visible
    await expect(page.locator('button:has-text("Fair Value Gaps")')).toBeVisible();
    await expect(page.locator('button:has-text("Order Blocks")')).toBeVisible();
    await expect(page.locator('button:has-text("Liquidity Pools")')).toBeVisible();

    // Check default tab is FVG
    const fvgTab = page.locator('[role="tabpanel"]:has-text("Fair Value Gaps (FVG)")');
    await expect(fvgTab).toBeVisible();
  });

  test('should switch between tabs correctly', async ({ page }) => {
    // Click Order Blocks tab
    await page.click('button:has-text("Order Blocks")');

    // Check Order Blocks content is visible
    const obPanel = page.locator('[role="tabpanel"]:has-text("Last candle before significant impulse move")');
    await expect(obPanel).toBeVisible();

    // Click Liquidity Pools tab
    await page.click('button:has-text("Liquidity Pools")');

    // Check Liquidity Pools content is visible
    const lpPanel = page.locator('[role="tabpanel"]:has-text("Areas where stop-loss orders accumulate")');
    await expect(lpPanel).toBeVisible();

    // Switch back to FVG
    await page.click('button:has-text("Fair Value Gaps")');
    const fvgPanel = page.locator('[role="tabpanel"]:has-text("Price gaps created by imbalance")');
    await expect(fvgPanel).toBeVisible();
  });

  test('should have working filters', async ({ page }) => {
    // Test timeframe selector
    const timeframeSelector = page.locator('select[id="timeframe"]').first();
    await expect(timeframeSelector).toBeVisible();

    // Change timeframe
    await timeframeSelector.selectOption('15min');
    await expect(timeframeSelector).toHaveValue('15min');

    // Test symbol input
    const symbolInput = page.locator('input[id="symbol"]');
    await expect(symbolInput).toBeVisible();
    await expect(symbolInput).toHaveValue('NQH25');

    // Change symbol
    await symbolInput.clear();
    await symbolInput.fill('ESH25');
    await expect(symbolInput).toHaveValue('ESH25');

    // Test refresh button
    const refreshButton = page.locator('button:has-text("Refresh")');
    await expect(refreshButton).toBeVisible();
    await refreshButton.click();
  });

  test('should load and display FVG data', async ({ page }) => {
    // Wait for FVG data to load (chart should be visible)
    await page.waitForSelector('[data-testid="fvg-chart"]', { timeout: 10000 });

    // Check chart is displayed
    const chart = page.locator('[data-testid="fvg-chart"]');
    await expect(chart).toBeVisible();

    // Check table is displayed with data
    const table = page.locator('table').first();
    await expect(table).toBeVisible();

    // Check table has rows (mock data should provide multiple patterns)
    const tableRows = page.locator('tbody tr');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThan(0);
    expect(rowCount).toBeLessThanOrEqual(10); // Default page size

    // Check first row has expected columns
    const firstRow = tableRows.first();
    await expect(firstRow.locator('td').nth(0)).toContainText('#'); // ID
    await expect(firstRow.locator('td').nth(1)).toContainText(':'); // Time
    await expect(firstRow.locator('td').nth(2)).toContainText('.'); // Gap High
    await expect(firstRow.locator('td').nth(3)).toContainText('.'); // Gap Low

    // Check badges exist
    const badges = firstRow.locator('[role="status"]');
    const badgeCount = await badges.count();
    expect(badgeCount).toBeGreaterThan(0);
  });

  test('should display pattern details when clicking a row', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Click first row
    const firstRow = page.locator('tbody tr').first();
    await firstRow.click();

    // Check detail card appears
    const detailCard = page.locator('[data-testid="pattern-detail"]');
    await expect(detailCard).toBeVisible();

    // Check detail card has content
    await expect(detailCard).toContainText('Selected Pattern');
    await expect(detailCard).toContainText('Premium Level');
    await expect(detailCard).toContainText('Consequent Encroachment');
    await expect(detailCard).toContainText('Discount Level');
  });

  test('should handle Order Blocks tab', async ({ page }) => {
    // Switch to Order Blocks tab
    await page.click('button:has-text("Order Blocks")');

    // Wait for OB data to load
    await page.waitForSelector('[data-testid="ob-chart"]', { timeout: 10000 });

    // Check chart is displayed
    const chart = page.locator('[data-testid="ob-chart"]');
    await expect(chart).toBeVisible();

    // Check table has Order Block specific columns
    const table = page.locator('table').first();
    await expect(table).toBeVisible();

    // Check filter dropdowns
    const statusFilter = page.locator('select').nth(1); // Second select after timeframe
    await expect(statusFilter).toBeVisible();

    // Change status filter
    await statusFilter.selectOption('TESTED');
    await expect(statusFilter).toHaveValue('TESTED');
  });

  test('should handle Liquidity Pools tab', async ({ page }) => {
    // Switch to Liquidity Pools tab
    await page.click('button:has-text("Liquidity Pools")');

    // Wait for LP data to load
    await page.waitForSelector('[data-testid="lp-chart"]', { timeout: 10000 });

    // Check chart is displayed
    const chart = page.locator('[data-testid="lp-chart"]');
    await expect(chart).toBeVisible();

    // Check table has Liquidity Pool specific columns
    const table = page.locator('table').first();
    await expect(table).toBeVisible();

    // Check pool type badges (EQH, EQL, NYH, etc.)
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const firstRow = page.locator('tbody tr').first();
    const poolTypeBadge = firstRow.locator('[role="status"]').first();
    await expect(poolTypeBadge).toBeVisible();
  });

  test('should handle pagination', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Check pagination info
    const paginationInfo = page.locator('text=/Page \\d+ of \\d+/');
    await expect(paginationInfo).toBeVisible();

    // Check Next button
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeVisible();

    // Click Next if not disabled
    const isDisabled = await nextButton.isDisabled();
    if (!isDisabled) {
      await nextButton.click();

      // Wait for new data
      await page.waitForTimeout(500);

      // Check page changed
      await expect(paginationInfo).toContainText('Page 2');

      // Check Previous button is now enabled
      const prevButton = page.locator('button:has-text("Previous")');
      await expect(prevButton).toBeEnabled();

      // Go back to page 1
      await prevButton.click();
      await page.waitForTimeout(500);
      await expect(paginationInfo).toContainText('Page 1');
    }
  });

  test('should apply date range filter', async ({ page }) => {
    // Open start date calendar
    const startDateButton = page.locator('button:has-text("Start date")');
    await expect(startDateButton).toBeVisible();
    await startDateButton.click();

    // Select a date (today)
    const todayButton = page.locator('[role="gridcell"] button[aria-selected="false"]').first();
    await todayButton.click();

    // Open end date calendar
    const endDateButton = page.locator('button:has-text("End date")');
    await expect(endDateButton).toBeVisible();
    await endDateButton.click();

    // Select end date (today)
    const endTodayButton = page.locator('[role="gridcell"] button[aria-selected="false"]').first();
    await endTodayButton.click();

    // Apply filters
    const applyButton = page.locator('button:has-text("Apply")');
    await expect(applyButton).toBeVisible();
    await applyButton.click();

    // Wait for data refresh
    await page.waitForTimeout(500);

    // Verify data is still displayed
    await expect(page.locator('tbody tr').first()).toBeVisible();
  });

  test('should maintain filter state across tabs', async ({ page }) => {
    // Change timeframe to 15min
    const timeframeSelector = page.locator('select[id="timeframe"]').first();
    await timeframeSelector.selectOption('15min');

    // Change symbol
    const symbolInput = page.locator('input[id="symbol"]');
    await symbolInput.clear();
    await symbolInput.fill('ESH25');

    // Switch to Order Blocks tab
    await page.click('button:has-text("Order Blocks")');

    // Check timeframe is still 15min
    await expect(timeframeSelector).toHaveValue('15min');

    // Check symbol is still ESH25
    await expect(symbolInput).toHaveValue('ESH25');

    // Switch to Liquidity Pools tab
    await page.click('button:has-text("Liquidity Pools")');

    // Check filters are maintained
    await expect(timeframeSelector).toHaveValue('15min');
    await expect(symbolInput).toHaveValue('ESH25');
  });
});

test.describe('Pattern Detection - Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate and login
    await page.goto('http://localhost:3001');
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.goto('http://localhost:3001/pattern-detection');
  });

  test('should handle empty data gracefully', async ({ page }) => {
    // Apply a filter that might return no results
    const symbolInput = page.locator('input[id="symbol"]');
    await symbolInput.clear();
    await symbolInput.fill('INVALID');

    // Trigger refresh
    await page.click('button:has-text("Refresh")');

    // Wait for response
    await page.waitForTimeout(1000);

    // Check for "No patterns found" message or empty table
    const noDataMessage = page.locator('text=/No .* found/i');
    const emptyTable = page.locator('tbody:has(td:has-text("No results"))');

    // Either no data message or empty table should be visible
    const hasNoDataIndication = await noDataMessage.isVisible() || await emptyTable.isVisible();
    expect(hasNoDataIndication).toBeTruthy();
  });
});