import { test, expect } from '@playwright/test';

test.describe('Footprint Chart Themes', () => {
  test('should render correctly in Dark theme', async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    // Apply zoom to trigger footprint mode (< 12 bars)
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Verify footprint mode is active
    await expect(page.locator('text=[FOOTPRINT MODE')).toBeVisible();

    // Take screenshot of Dark theme
    await page.screenshot({ path: 'test-results/footprint-dark-theme.png', fullPage: true });
  });

  test('should render correctly in Light theme', async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    // Apply zoom to trigger footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Click on LIGHT button to switch theme
    await page.click('button:has-text("Light")');
    await page.waitForTimeout(1000);

    // Verify footprint mode is still active
    await expect(page.locator('text=[FOOTPRINT MODE')).toBeVisible();

    // Take screenshot of Light theme
    await page.screenshot({ path: 'test-results/footprint-light-theme.png', fullPage: true });
  });

  test('should test PAN in both modes', async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    // Test PAN in normal mode (> 12 candles)
    const chartCanvas = page.locator('canvas').first();

    // Get initial position
    const initialBox = await chartCanvas.boundingBox();
    if (!initialBox) throw new Error('Canvas not found');

    // Simulate drag (PAN)
    await page.mouse.move(initialBox.x + 100, initialBox.y + 100);
    await page.mouse.down();
    await page.mouse.move(initialBox.x + 200, initialBox.y + 100);
    await page.mouse.up();

    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/pan-normal-mode.png', fullPage: true });

    // Now test PAN in footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Simulate drag in footprint mode
    await page.mouse.move(initialBox.x + 100, initialBox.y + 100);
    await page.mouse.down();
    await page.mouse.move(initialBox.x + 50, initialBox.y + 100);
    await page.mouse.up();

    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/pan-footprint-mode.png', fullPage: true });
  });
});
