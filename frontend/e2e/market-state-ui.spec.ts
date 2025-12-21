/**
 * Market State UI Tests
 * Tests date picker standardization and progress tracking
 */
import { test, expect } from '@playwright/test';

test.describe('Market State UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3001');

    // Login
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("Sign In")');

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard');

    // Navigate to Data Module
    await page.click('a:has-text("Data Module")');
    await page.waitForURL('**/data');
  });

  test('should have DatePicker components in Generate section', async ({ page }) => {
    // Click Market State tab
    await page.click('button:has-text("Market State")');

    // Wait for the section to load
    await page.waitForSelector('text=Generate New Snapshots');

    // Check for DatePicker components (they have a trigger button)
    const startDatePicker = page.locator('label:has-text("Start Date")').locator('..').locator('button');
    const endDatePicker = page.locator('label:has-text("End Date")').locator('..').locator('button');

    await expect(startDatePicker).toBeVisible();
    await expect(endDatePicker).toBeVisible();

    // Verify they are NOT standard HTML date inputs
    const htmlDateInputs = page.locator('input[type="date"]');
    const count = await htmlDateInputs.count();
    expect(count).toBe(0); // Should be 0 because we use DatePicker, not HTML5 date input
  });

  test('should have Select dropdown for interval', async ({ page }) => {
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('text=Generate New Snapshots');

    // Find the interval select
    const intervalLabel = page.locator('label:has-text("Interval")');
    await expect(intervalLabel).toBeVisible();

    // Should have a Select trigger (not a number input)
    const selectTrigger = intervalLabel.locator('..').locator('[role="combobox"]');
    await expect(selectTrigger).toBeVisible();

    // Click to open dropdown
    await selectTrigger.click();

    // Check for preset options
    await expect(page.locator('text=1 minute')).toBeVisible();
    await expect(page.locator('text=5 minutes')).toBeVisible();
    await expect(page.locator('text=15 minutes')).toBeVisible();
    await expect(page.locator('text=30 minutes')).toBeVisible();
    await expect(page.locator('text=60 minutes')).toBeVisible();

    // Close dropdown
    await page.keyboard.press('Escape');
  });

  test('should have DatePicker in Load section', async ({ page }) => {
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('text=Load Existing Snapshot');

    // Check for DatePicker in Load section
    const loadDatePicker = page
      .locator('text=Load Existing Snapshot')
      .locator('..')
      .locator('..')
      .locator('label:has-text("Date (UTC)")')
      .locator('..')
      .locator('button');

    await expect(loadDatePicker).toBeVisible();
  });

  test('should show progress bar during generation', async ({ page }) => {
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('text=Generate New Snapshots');

    // Set symbol
    await page.fill('#gen-symbol', 'NQZ5');

    // Set time inputs
    await page.fill('#start-time', '09:00');
    await page.fill('#end-time', '09:15');

    // Click Generate button
    await page.click('button:has-text("Generate Snapshots")');

    // Wait for progress indicator to appear
    const progressCard = page.locator('text=Generating Snapshots...');
    await expect(progressCard).toBeVisible({ timeout: 5000 });

    // Check for progress bar
    const progressBar = page.locator('[role="progressbar"]');
    await expect(progressBar).toBeVisible();

    // Check for progress text
    await expect(page.locator('text=Snapshot')).toBeVisible();
    await expect(page.locator('text=Elapsed Time')).toBeVisible();
    await expect(page.locator('text=Est. Remaining')).toBeVisible();

    // Wait for completion (should be fast for small range)
    await expect(progressCard).not.toBeVisible({ timeout: 30000 });

    // Check for success message
    await expect(page.locator('text=Generated').first()).toBeVisible({ timeout: 5000 });
  });

  test('can select dates using DatePicker', async ({ page }) => {
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('text=Generate New Snapshots');

    // Click Start Date picker
    const startDateButton = page
      .locator('label:has-text("Start Date")')
      .locator('..')
      .locator('button')
      .first();

    await startDateButton.click();

    // Calendar should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Close calendar
    await page.keyboard.press('Escape');

    // Click End Date picker
    const endDateButton = page
      .locator('label:has-text("End Date")')
      .locator('..')
      .locator('button')
      .first();

    await endDateButton.click();

    // Calendar should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Close calendar
    await page.keyboard.press('Escape');
  });

  test('can change interval using Select dropdown', async ({ page }) => {
    await page.click('button:has-text("Market State")');
    await page.waitForSelector('text=Generate New Snapshots');

    // Find interval select
    const intervalSelect = page
      .locator('label:has-text("Interval")')
      .locator('..')
      .locator('[role="combobox"]');

    // Should show default (5 minutes)
    await expect(intervalSelect).toContainText('5 minutes');

    // Click to open
    await intervalSelect.click();

    // Select 15 minutes
    await page.click('text=15 minutes');

    // Verify selection
    await expect(intervalSelect).toContainText('15 minutes');
  });
});
