import { test, expect } from '@playwright/test';

test.describe('ETL Job Summary Cards', () => {
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

  test('should display job summary cards when clicking Jobs tab', async ({ page }) => {
    // Click on Jobs tab
    await page.click('[data-testid="jobs-tab"]');

    // Wait for job summary cards to load
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Should show the component
    await expect(page.locator('[data-testid="job-summary-cards"]')).toBeVisible();
  });

  test('should display main stats: total, completed, active, failed', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Check main stat cards
    const totalStat = page.locator('[data-testid="stat-total"]');
    const completedStat = page.locator('[data-testid="stat-completed"]');
    const activeStat = page.locator('[data-testid="stat-active"]');
    const failedStat = page.locator('[data-testid="stat-failed"]');

    await expect(totalStat).toBeVisible();
    await expect(completedStat).toBeVisible();
    await expect(activeStat).toBeVisible();
    await expect(failedStat).toBeVisible();

    // Values should be numbers (not empty)
    const totalText = await totalStat.textContent();
    const completedText = await completedStat.textContent();
    const activeText = await activeStat.textContent();
    const failedText = await failedStat.textContent();

    expect(parseInt(totalText || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(completedText || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(activeText || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(failedText || '0')).toBeGreaterThanOrEqual(0);
  });

  test('should display secondary stats: pending, ticks, candles, duration', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Check secondary stat cards
    const pendingStat = page.locator('[data-testid="stat-pending"]');
    const ticksStat = page.locator('[data-testid="stat-ticks"]');
    const candlesStat = page.locator('[data-testid="stat-candles"]');
    const durationStat = page.locator('[data-testid="stat-duration"]');

    await expect(pendingStat).toBeVisible();
    await expect(ticksStat).toBeVisible();
    await expect(candlesStat).toBeVisible();
    await expect(durationStat).toBeVisible();
  });

  test('should have color-coded stat cards', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Check that completed card has green styling
    const completedCard = page.locator('[data-testid="stat-completed"]').locator('..');
    await expect(completedCard).toHaveClass(/bg-green/);

    // Check that active card has blue styling
    const activeCard = page.locator('[data-testid="stat-active"]').locator('..');
    await expect(activeCard).toHaveClass(/bg-blue/);

    // Check that failed card has red styling
    const failedCard = page.locator('[data-testid="stat-failed"]').locator('..');
    await expect(failedCard).toHaveClass(/bg-red/);
  });

  test('should show formatted numbers for large values', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Check ticks stat - if there are ticks, they should be formatted
    const ticksStat = page.locator('[data-testid="stat-ticks"]');
    const ticksText = await ticksStat.textContent();

    // Should be either a number, or formatted with K or M
    expect(ticksText).toMatch(/^\d+(\.\d+)?[KM]?$/);
  });

  test('should show duration in readable format', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Check duration stat format
    const durationStat = page.locator('[data-testid="stat-duration"]');
    const durationText = await durationStat.textContent();

    // Should be formatted like "< 1 min", "5 min", "1h 30m", etc.
    expect(durationText).toMatch(/^(< 1 min|\d+ min|\d+h \d+m)$/);
  });

  test('should show JobMonitor below summary cards', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // JobMonitor should also be visible
    await expect(page.locator('[data-testid="job-monitor"]')).toBeVisible();
  });

  test('should have correct sum of completed + active + failed + pending = total', async ({ page }) => {
    // Navigate to Jobs tab
    await page.click('[data-testid="jobs-tab"]');
    await page.waitForSelector('[data-testid="job-summary-cards"]');

    // Get all stat values
    const total = parseInt(await page.locator('[data-testid="stat-total"]').textContent() || '0');
    const completed = parseInt(await page.locator('[data-testid="stat-completed"]').textContent() || '0');
    const active = parseInt(await page.locator('[data-testid="stat-active"]').textContent() || '0');
    const failed = parseInt(await page.locator('[data-testid="stat-failed"]').textContent() || '0');
    const pending = parseInt(await page.locator('[data-testid="stat-pending"]').textContent() || '0');

    // The sum should equal total (or be less due to other states)
    const sum = completed + active + failed + pending;
    expect(sum).toBeLessThanOrEqual(total);
  });

  test('should handle loading state', async ({ page }) => {
    // Navigate directly to data page
    await page.goto('/data');

    // Click on Jobs tab immediately
    await page.click('[data-testid="jobs-tab"]');

    // Eventually should load the component
    await page.waitForSelector('[data-testid="job-summary-cards"]', { timeout: 10000 });
  });
});
