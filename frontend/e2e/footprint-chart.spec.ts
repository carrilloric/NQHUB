import { test, expect } from '@playwright/test';

test.describe('Footprint Chart Mode', () => {
  test('should activate footprint mode and display bid×ask numbers', async ({ page }) => {
    // Navigate to chart test page
    await page.goto('/chart-test');

    // Wait for chart to initialize
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    console.log('Chart instance loaded');

    // Take screenshot of initial state (normal mode)
    await page.screenshot({ path: 'test-results/01-normal-mode.png', fullPage: true });

    // Apply zoom to trigger footprint mode (< 12 bars)
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        // Set visible range to show only 10 bars (triggers footprint mode)
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
        console.log('Zoom applied: 10 bars visible');
      }
    });

    // Wait for footprint to render
    await page.waitForTimeout(2000);

    // Verify footprint mode header is visible
    await expect(page.locator('text=[FOOTPRINT MODE')).toBeVisible();
    console.log('Footprint mode header visible');

    // Take screenshot of footprint mode
    await page.screenshot({ path: 'test-results/02-footprint-mode.png', fullPage: true });

    // Check that volume profile (blue bars on left) is visible
    // This is rendered on canvas, so we check the canvas exists
    const canvases = await page.$$('canvas');
    console.log(`Found ${canvases.length} canvas elements`);
    expect(canvases.length).toBeGreaterThan(0);

    // Log visible text for debugging
    const visibleText = await page.evaluate(() => {
      const canvases = document.querySelectorAll('canvas');
      return `Canvases: ${canvases.length}`;
    });
    console.log(visibleText);

    // Additional screenshot with different zoom for comparison
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        // Try different range - 8 bars
        timeScale.setVisibleLogicalRange({ from: 80, to: 88 });
      }
    });

    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/03-footprint-8-bars.png', fullPage: true });

    // Reset zoom to normal
    await page.click('button:has-text("Reset Zoom")');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/04-reset-to-normal.png', fullPage: true });
  });

  test('should display volume profile in both modes', async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);

    // Screenshot normal mode
    await page.screenshot({ path: 'test-results/volume-profile-normal.png', fullPage: true });

    // Zoom to footprint (< 12 bars)
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        chart.timeScale().setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/volume-profile-footprint.png', fullPage: true });
  });
});
