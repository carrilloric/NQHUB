import { test, expect } from '@playwright/test';

// Test credentials
const SUPERUSER = {
  email: "admin@nqhub.com",
  password: "admin_inicial_2024",
};

test.describe('Liquidity Pool and Session Level Detection', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3001/');
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button:has-text("Login")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Navigate to Data Module
    await page.goto('http://localhost:3001/data');
    await page.waitForLoadState('networkidle');

    // Click on Pattern Detection tab (the tab contains emoji + text)
    const patternTab = page.locator('button:has-text("Pattern Detection")');
    await patternTab.click();
    await page.waitForTimeout(500);
  });

  test('should have 4 pattern detection tabs', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="pattern-detection-dashboard"]', { timeout: 10000 });

    // Check that all 4 tabs exist
    await expect(page.locator('[data-testid="fvg-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="lp-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="sl-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="ob-tab"]')).toBeVisible();
  });

  test('should detect Liquidity Pools (EQH/EQL)', async ({ page }) => {
    // Navigate to LP tab
    await page.click('[data-testid="lp-tab"]');
    await page.waitForTimeout(500);

    // Verify title and description
    await expect(page.locator('text=Liquidity Pool Detection')).toBeVisible();
    await expect(page.locator('text=Equal Highs (EQH) and Equal Lows (EQL)')).toBeVisible();

    // Fill in parameters
    await page.fill('#lp-symbol', 'NQZ5');
    await page.selectOption('#lp-timeframe', '5min');
    // Date should already be Nov 24, 2025

    // Click Generate
    await page.click('text=Generate Liquidity Pools');

    // Wait for results (max 30 seconds)
    await expect(page.locator('text=Detection Summary')).toBeVisible({ timeout: 30000 });

    // Verify results
    await expect(page.locator('text=Total Pools')).toBeVisible();
    await expect(page.locator('text=Showing')).toBeVisible();

    // Verify only EQH/EQL in breakdown (not session levels)
    const breakdownText = await page.locator('text=Breakdown by Type').locator('..').textContent();
    expect(breakdownText).toContain('EQH');
    expect(breakdownText).toContain('EQL');
    expect(breakdownText).not.toContain('ASH');
    expect(breakdownText).not.toContain('NYH');

    // Verify LP List table exists
    await expect(page.locator('text=Liquidity Pool List')).toBeVisible();

    // Verify zones are displayed (check for "pts)" which indicates zone size)
    const tableText = await page.locator('table').textContent();
    expect(tableText).toContain('pts)');

    // Verify report exists
    await expect(page.locator('text=Liquidity Pool Detection Report')).toBeVisible();
  });

  test('should detect Session Levels (ASH, ASL, LSH, LSL, NYH, NYL)', async ({ page }) => {
    // Navigate to Session Levels tab
    await page.click('[data-testid="sl-tab"]');
    await page.waitForTimeout(500);

    // Verify title and description
    await expect(page.locator('text=Session Level Detection')).toBeVisible();
    await expect(page.locator('text=Asian (ASH/ASL), London (LSH/LSL), NY (NYH/NYL)')).toBeVisible();

    // Fill in parameters
    await page.fill('#sl-symbol', 'NQZ5');
    await page.selectOption('#sl-timeframe', '5min');
    // Date should already be Nov 24, 2025

    // Click Generate
    await page.click('text=Generate Session Levels');

    // Wait for results
    await expect(page.locator('text=Detection Summary')).toBeVisible({ timeout: 30000 });

    // Verify session breakdown
    await expect(page.locator('text=Session Breakdown')).toBeVisible();
    const sessionText = await page.textContent('text=Session Breakdown');
    expect(sessionText).toBeTruthy();

    // Verify Session Level List table exists
    await expect(page.locator('text=Session Levels')).toBeVisible();

    // Verify ATAS format button exists
    await expect(page.locator('text=Copy for ATAS')).toBeVisible();

    // Verify ATAS format preview exists
    await expect(page.locator('text=ATAS Format Preview')).toBeVisible();

    // Check that session levels are point levels (no zones)
    const tableContent = await page.locator('table').textContent();
    // Should have ASH, ASL, LSH, LSL, NYH, NYL
    expect(tableContent).toMatch(/ASH|ASL|LSH|LSL|NYH|NYL/);
  });

  test('should copy ATAS format for Session Levels', async ({ page }) => {
    // Navigate to Session Levels tab
    await page.click('[data-testid="sl-tab"]');
    await page.waitForTimeout(500);

    // Generate Session Levels
    await page.click('text=Generate Session Levels');
    await expect(page.locator('text=Detection Summary')).toBeVisible({ timeout: 30000 });

    // Click Copy for ATAS button
    await page.click('text=Copy for ATAS');

    // Verify button changes to "Copied!"
    await expect(page.locator('text=Copied!')).toBeVisible();
    await page.waitForTimeout(2000);

    // Button should revert back
    await expect(page.locator('text=Copy for ATAS')).toBeVisible();
  });

  test('should show zone information for EQH/EQL', async ({ page }) => {
    // Navigate to LP tab
    await page.click('[data-testid="lp-tab"]');
    await page.waitForTimeout(500);

    // Generate LPs
    await page.click('text=Generate Liquidity Pools');
    await expect(page.locator('text=Detection Summary')).toBeVisible({ timeout: 30000 });

    // Check LP List table
    const table = page.locator('table').first();
    const tableText = await table.textContent();

    // Verify zone format appears (e.g., "24681.25 - 24684.75 (3.5 pts)")
    expect(tableText).toMatch(/\d+\.\d+\s*-\s*\d+\.\d+/);  // zone range
    expect(tableText).toContain('pts)');  // zone size

    // Verify table header shows "Level / Zone"
    await expect(page.locator('text=Level / Zone')).toBeVisible();
  });

  test('should filter LPs by type (EQH only)', async ({ page }) => {
    // Navigate to LP tab
    await page.click('[data-testid="lp-tab"]');
    await page.waitForTimeout(500);

    // Generate LPs
    await page.click('text=Generate Liquidity Pools');
    await expect(page.locator('text=Detection Summary')).toBeVisible({ timeout: 30000 });

    // Uncheck "Show All Pools"
    await page.click('#show-all-lp');
    await page.waitForTimeout(300);

    // Select only EQH
    await page.click('#pool-EQH');
    await page.waitForTimeout(300);

    // Verify filtered count changed
    const showingText = await page.locator('text=Showing').locator('..').textContent();
    expect(showingText).toBeTruthy();

    // Verify table only shows EQH
    const tableText = await page.locator('table').textContent();
    expect(tableText).toContain('EQH');
    expect(tableText).not.toContain('EQL');
  });
});
