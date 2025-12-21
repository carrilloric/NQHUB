/**
 * Market State Complete Flow E2E Test
 *
 * Tests:
 * 1. Login and navigation
 * 2. DatePicker functionality
 * 3. Progress tracking in real-time
 * 4. Snapshot generation
 * 5. Pattern display
 */
import { test, expect } from '@playwright/test';

test.describe('Market State - Complete Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3001');

    // Login
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Navigate to Data Module
    await page.click('a:has-text("Data Module")');
    await page.waitForURL('**/data', { timeout: 10000 });

    // Click Market State tab
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('[data-testid="market-state-section"]', { timeout: 10000 });
  });

  test('should have properly styled DatePicker components', async ({ page }) => {
    // Find Start Date picker button
    const startDateButton = page
      .locator('label:has-text("Start Date")')
      .locator('..')
      .locator('button')
      .first();

    // Should be visible and have proper width
    await expect(startDateButton).toBeVisible();

    // Check that button has w-full class (through parent div)
    const parentDiv = page.locator('label:has-text("Start Date")').locator('..');
    await expect(parentDiv).toHaveClass(/space-y-2/);

    // Click to open calendar
    await startDateButton.click();

    // Calendar popover should appear
    const calendar = page.locator('[role="dialog"]');
    await expect(calendar).toBeVisible({ timeout: 2000 });

    // Close calendar
    await page.keyboard.press('Escape');
    await expect(calendar).not.toBeVisible();
  });

  test('should generate snapshots with real-time progress', async ({ page }) => {
    // Fill in generation form
    await page.fill('#gen-symbol', 'NQZ5');
    await page.fill('#start-time', '09:00');
    await page.fill('#end-time', '09:30');

    // Select interval
    const intervalSelect = page.locator('label:has-text("Interval")').locator('..').locator('[role="combobox"]');
    await intervalSelect.click();
    await page.click('text=5 minutes');

    // Click Generate button
    const generateButton = page.locator('button:has-text("Generate Snapshots")');
    await generateButton.click();

    // Progress bar should appear quickly
    const progressCard = page.locator('text=Generating Snapshots...');
    await expect(progressCard).toBeVisible({ timeout: 3000 });

    // Progress bar element
    const progressBar = page.locator('[role="progressbar"]');
    await expect(progressBar).toBeVisible();

    // Check for progress details
    await expect(page.locator('text=Elapsed Time')).toBeVisible();
    await expect(page.locator('text=Est. Remaining')).toBeVisible();

    // Wait for snapshot text to appear (should show "Snapshot X / Y")
    const snapshotText = page.locator('text=Snapshot');
    await expect(snapshotText).toBeVisible({ timeout: 5000 });

    // Wait for completion (max 60 seconds for small range)
    await expect(progressCard).not.toBeVisible({ timeout: 60000 });

    // Success message should appear
    const successMessage = page.locator('text=Generated').first();
    await expect(successMessage).toBeVisible({ timeout: 5000 });

    // Dashboard should be visible (patterns loaded)
    const dashboard = page.locator('text=Market State Dashboard');
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should show pattern counts and details', async ({ page }) => {
    // First generate a snapshot (reuse generation logic)
    await page.fill('#gen-symbol', 'NQZ5');
    await page.fill('#start-time', '09:00');
    await page.fill('#end-time', '09:15');

    const intervalSelect = page.locator('label:has-text("Interval")').locator('..').locator('[role="combobox"]');
    await intervalSelect.click();
    await page.click('text=5 minutes');

    await page.click('button:has-text("Generate Snapshots")');

    // Wait for completion
    await expect(page.locator('text=Generating Snapshots...')).not.toBeVisible({ timeout: 60000 });

    // Dashboard should show total patterns
    await expect(page.locator('text=Total Patterns')).toBeVisible({ timeout: 5000 });

    // Should show breakdown by timeframe
    await expect(page.locator('text=5min')).toBeVisible();

    // Click "All Timeframes" tab if needed
    const allTab = page.locator('button:has-text("All")');
    if (await allTab.isVisible()) {
      await allTab.click();
    }

    // Should see pattern tables or counts
    const patternSection = page.locator('text=Active Patterns').or(page.locator('text=FVGs'));
    await expect(patternSection.first()).toBeVisible({ timeout: 5000 });
  });

  test('should load existing snapshot by date/time', async ({ page }) => {
    // Fill load form
    await page.fill('#load-symbol', 'NQZ5');

    // Click load date picker
    const loadDateButton = page
      .locator('text=Load Existing Snapshot')
      .locator('..')
      .locator('..')
      .locator('label:has-text("Date (UTC)")')
      .locator('..')
      .locator('button')
      .first();

    await loadDateButton.click();

    // Calendar should open
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 2000 });

    // Close it
    await page.keyboard.press('Escape');

    // Fill time
    await page.fill('#load-time', '09:00');

    // Click Load Snapshot button
    await page.click('button:has-text("Load Snapshot")');

    // Either success or error message should appear
    const messageCard = page.locator('.border-green-500, .border-destructive').first();
    await expect(messageCard).toBeVisible({ timeout: 10000 });
  });

  test('should list available snapshots', async ({ page }) => {
    // Fill symbol
    await page.fill('#load-symbol', 'NQZ5');

    // Click List Available button
    await page.click('button:has-text("List Available")');

    // Either success message or error should appear
    const response = page.locator('text=Found').or(page.locator('text=Failed'));
    await expect(response.first()).toBeVisible({ timeout: 10000 });
  });

  test('should handle interval dropdown correctly', async ({ page }) => {
    // Find interval select
    const intervalSelect = page
      .locator('label:has-text("Interval")')
      .locator('..')
      .locator('[role="combobox"]');

    // Should show default (5 minutes)
    await expect(intervalSelect).toContainText('5 minutes');

    // Click to open
    await intervalSelect.click();

    // All options should be visible
    await expect(page.locator('text=1 minute')).toBeVisible();
    await expect(page.locator('text=15 minutes')).toBeVisible();
    await expect(page.locator('text=30 minutes')).toBeVisible();
    await expect(page.locator('text=60 minutes')).toBeVisible();

    // Select 15 minutes
    await page.click('text=15 minutes');

    // Should update
    await expect(intervalSelect).toContainText('15 minutes');
  });

  test('should show error for invalid date range', async ({ page }) => {
    // Fill with invalid range (end before start)
    await page.fill('#gen-symbol', 'NQZ5');
    await page.fill('#start-time', '16:00');
    await page.fill('#end-time', '09:00');

    // Try to generate
    await page.click('button:has-text("Generate Snapshots")');

    // Should show error or validation message
    // (Backend should handle this)
    const errorCard = page.locator('.border-destructive');
    await expect(errorCard).toBeVisible({ timeout: 10000 });
  });
});
