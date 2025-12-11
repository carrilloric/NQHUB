import { test, expect } from '@playwright/test';

test.describe('Theme Toggle Behavior', () => {
  test('should toggle from Dark → Light → Dark and verify appearance', async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    // Activate footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);
    await expect(page.locator('text=[FOOTPRINT MODE')).toBeVisible();

    // 1. DARK theme (initial state)
    console.log('=== DARK THEME (INITIAL) ===');
    await page.screenshot({ path: 'test-results/toggle-1-dark-initial.png', fullPage: true });

    // 2. Switch to LIGHT theme
    await page.click('button:has-text("Light")');
    await page.waitForTimeout(1500);
    console.log('=== LIGHT THEME ===');
    await page.screenshot({ path: 'test-results/toggle-2-light.png', fullPage: true });

    // 3. Switch back to DARK theme
    await page.click('button:has-text("Dark")');
    await page.waitForTimeout(1500);
    console.log('=== DARK THEME (AFTER TOGGLE) ===');
    await page.screenshot({ path: 'test-results/toggle-3-dark-after.png', fullPage: true });

    // Verify footprint is still visible
    await expect(page.locator('text=[FOOTPRINT MODE')).toBeVisible();
  });
});
