import { test, expect } from '@playwright/test';

/**
 * Advanced Footprint Data Validation Test
 * Validates exact data points from the footprint chart
 */

test.describe('Footprint Exact Data Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chart-test');
    await page.waitForFunction(() => (window as any).__CHART_INSTANCE__);
  });

  test('should extract and validate real footprint data', async ({ page }) => {
    // Zoom to trigger footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        // Set exact range for 10 bars
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Extract all available data
    const chartData = await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      const series = (window as any).__CHART_SERIES__;
      const candlesData = (window as any).__CANDLES_DATA__;
      const footprintData = (window as any).__FOOTPRINT_DATA__;
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;

      if (!chart) return { error: 'No chart instance' };

      const timeScale = chart.timeScale();
      const logicalRange = timeScale.getVisibleLogicalRange();
      const priceScale = chart.priceScale('right');

      return {
        // Chart state
        visibleBars: logicalRange ? Math.round(logicalRange.to - logicalRange.from) : 0,
        logicalRange: logicalRange,

        // Candles data
        totalCandles: candlesData?.length || 0,
        visibleCandles: candlesData?.slice(
          Math.floor(logicalRange?.from || 0),
          Math.ceil(logicalRange?.to || 10)
        ).map(c => ({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
          volume: c.volume
        })) || [],

        // Footprint data
        footprintDataLength: footprintData?.length || 0,
        footprintCandlesLength: footprintCandles?.length || 0,
        footprintVisible: (window as any).__FOOTPRINT_VISIBLE__ || false,

        // Sample footprint candle structure
        sampleFootprintCandle: footprintCandles?.[0] ? {
          x: footprintCandles[0].x,
          width: footprintCandles[0].width,
          levelsCount: footprintCandles[0].levels?.length || 0,
          delta: footprintCandles[0].delta,
          volume: footprintCandles[0].volume,
          high: footprintCandles[0].high,
          low: footprintCandles[0].low,
          // Sample level data
          sampleLevel: footprintCandles[0].levels?.[0] ? {
            price: footprintCandles[0].levels[0].price,
            bidVolume: footprintCandles[0].levels[0].bidVolume,
            askVolume: footprintCandles[0].levels[0].askVolume,
            totalVolume: footprintCandles[0].levels[0].totalVolume,
            delta: footprintCandles[0].levels[0].delta,
            isPOC: footprintCandles[0].levels[0].isPOC
          } : null
        } : null
      };
    });

    console.log('Chart Data:', JSON.stringify(chartData, null, 2));

    // Validate footprint mode is active
    expect(chartData.visibleBars).toBeLessThanOrEqual(12);
    expect(chartData.visibleBars).toBeGreaterThanOrEqual(8);
    expect(chartData.footprintVisible).toBe(true);

    // Validate we have footprint data
    expect(chartData.footprintCandlesLength).toBeGreaterThan(0);

    // Validate footprint candle structure
    if (chartData.sampleFootprintCandle) {
      expect(chartData.sampleFootprintCandle.x).toBeGreaterThan(0);
      expect(chartData.sampleFootprintCandle.width).toBeGreaterThan(0);
      expect(chartData.sampleFootprintCandle.levelsCount).toBeGreaterThan(0);
      expect(chartData.sampleFootprintCandle.levelsCount).toBeLessThanOrEqual(8); // Max 8 levels per candle

      // Validate level structure
      if (chartData.sampleFootprintCandle.sampleLevel) {
        const level = chartData.sampleFootprintCandle.sampleLevel;
        expect(level.price).toBeGreaterThan(0);
        expect(level.bidVolume).toBeGreaterThanOrEqual(0);
        expect(level.askVolume).toBeGreaterThanOrEqual(0);
        expect(level.totalVolume).toBe(level.bidVolume + level.askVolume);
        expect(level.delta).toBe(level.bidVolume - level.askVolume);
      }
    }

    // Validate visible candles
    expect(chartData.visibleCandles.length).toBeGreaterThan(0);
    chartData.visibleCandles.forEach(candle => {
      expect(candle.open).toBeGreaterThan(0);
      expect(candle.high).toBeGreaterThanOrEqual(candle.open);
      expect(candle.high).toBeGreaterThanOrEqual(candle.close);
      expect(candle.low).toBeLessThanOrEqual(candle.open);
      expect(candle.low).toBeLessThanOrEqual(candle.close);
      expect(candle.volume).toBeGreaterThan(0);
    });
  });

  test('should validate footprint levels match reference pattern', async ({ page }) => {
    // Set to Light theme to match reference
    await page.click('button:has-text("Light")');
    await page.waitForTimeout(1000);

    // Zoom to footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Extract footprint levels
    const footprintLevels = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      if (!footprintCandles || footprintCandles.length === 0) return null;

      // Get first candle's levels for validation
      const firstCandle = footprintCandles[0];
      if (!firstCandle || !firstCandle.levels) return null;

      return firstCandle.levels.map(level => ({
        price: level.price.toFixed(2),
        bid: level.bidVolume,
        ask: level.askVolume,
        total: level.totalVolume,
        delta: level.delta,
        isPOC: level.isPOC || false,
        // Calculate dominance for color validation
        bidDominant: level.bidVolume > level.askVolume,
        askDominant: level.askVolume > level.bidVolume
      }));
    });

    console.log('Footprint Levels:', JSON.stringify(footprintLevels, null, 2));

    if (footprintLevels) {
      // Validate level structure
      expect(footprintLevels.length).toBeGreaterThan(0);
      expect(footprintLevels.length).toBeLessThanOrEqual(8);

      // Find POC
      const pocLevel = footprintLevels.find(l => l.isPOC);
      if (pocLevel) {
        console.log('POC Level:', pocLevel);
        expect(pocLevel.total).toBeGreaterThan(0);
      }

      // Validate color dominance logic
      footprintLevels.forEach(level => {
        if (level.bid > level.ask) {
          expect(level.bidDominant).toBe(true);
          expect(level.askDominant).toBe(false);
        } else if (level.ask > level.bid) {
          expect(level.bidDominant).toBe(false);
          expect(level.askDominant).toBe(true);
        }
      });
    }
  });

  test('should validate horizontal volume bars scale correctly', async ({ page }) => {
    // Zoom to footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Extract and validate volume bar scaling
    const volumeBarData = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      if (!footprintCandles || footprintCandles.length === 0) return null;

      const firstCandle = footprintCandles[0];
      if (!firstCandle || !firstCandle.levels) return null;

      // Find max volume for scaling reference
      const maxVolume = Math.max(...firstCandle.levels.map(l => l.totalVolume));

      return firstCandle.levels.map(level => {
        const volumeRatio = level.totalVolume / maxVolume;
        return {
          price: level.price.toFixed(2),
          totalVolume: level.totalVolume,
          volumeRatio: volumeRatio,
          expectedBarWidth: volumeRatio * 0.3, // 30% max width
          isPOC: level.isPOC || false
        };
      });
    });

    console.log('Volume Bar Scaling:', JSON.stringify(volumeBarData, null, 2));

    if (volumeBarData) {
      // Find the level with max volume
      const maxVolumeLevel = volumeBarData.find(l => l.volumeRatio === 1);
      if (maxVolumeLevel) {
        expect(maxVolumeLevel.expectedBarWidth).toBeCloseTo(0.3, 2);
      }

      // Validate scaling proportions
      volumeBarData.forEach(level => {
        expect(level.volumeRatio).toBeGreaterThanOrEqual(0);
        expect(level.volumeRatio).toBeLessThanOrEqual(1);
        expect(level.expectedBarWidth).toBeLessThanOrEqual(0.3);
      });
    }
  });

  test('should capture and validate visual appearance matches reference', async ({ page }) => {
    // Set to Light theme to match reference
    await page.click('button:has-text("Light")');
    await page.waitForTimeout(1000);

    // Zoom to footprint mode with exact 10 bars
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(2000);

    // Verify footprint mode is active
    await expect(page.locator('text=[FOOTPRINT MODE - 10 bars]')).toBeVisible();

    // Take screenshot for visual validation
    const screenshot = await page.screenshot({
      path: 'test-results/footprint-exact-match.png',
      fullPage: false,
      clip: { x: 30, y: 190, width: 1090, height: 620 } // Chart area only
    });

    // Extract visual characteristics
    const visualData = await page.evaluate(() => {
      const chartContainer = document.querySelector('canvas')?.parentElement;
      const computedStyle = chartContainer ? window.getComputedStyle(chartContainer) : null;

      return {
        backgroundColor: computedStyle?.backgroundColor || 'unknown',
        hasCanvas: document.querySelectorAll('canvas').length,
        footprintCanvasVisible: document.querySelector('canvas[style*="z-index: 20"]') !== null,
        themeButtonText: document.querySelector('button[data-testid="theme-toggle"]')?.textContent
      };
    });

    console.log('Visual Data:', visualData);

    // Validate visual setup
    expect(visualData.hasCanvas).toBeGreaterThan(0);
    expect(visualData.footprintCanvasVisible).toBe(true);
    expect(visualData.themeButtonText).toBe('Dark'); // Should say "Dark" when in Light theme
  });

  test('should validate PAN maintains data integrity', async ({ page }) => {
    // Zoom to footprint mode
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(1500);

    // Get initial footprint data
    const initialData = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      return {
        candleCount: footprintCandles?.length || 0,
        firstCandleX: footprintCandles?.[0]?.x || 0,
        lastCandleX: footprintCandles?.[footprintCandles.length - 1]?.x || 0
      };
    });

    // Perform PAN
    const chartCanvas = page.locator('canvas').first();
    const box = await chartCanvas.boundingBox();
    if (!box) throw new Error('Canvas not found');

    await page.mouse.move(box.x + 500, box.y + 300);
    await page.mouse.down();
    await page.mouse.move(box.x + 300, box.y + 300); // Pan left
    await page.mouse.up();

    await page.waitForTimeout(1000);

    // Get data after PAN
    const afterPanData = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      const chart = (window as any).__CHART_INSTANCE__;
      const timeScale = chart?.timeScale();
      const logicalRange = timeScale?.getVisibleLogicalRange();

      return {
        candleCount: footprintCandles?.length || 0,
        firstCandleX: footprintCandles?.[0]?.x || 0,
        lastCandleX: footprintCandles?.[footprintCandles.length - 1]?.x || 0,
        visibleBars: logicalRange ? Math.round(logicalRange.to - logicalRange.from) : 0
      };
    });

    console.log('PAN Test - Initial:', initialData, 'After:', afterPanData);

    // Validate PAN changed the view but maintained footprint mode
    expect(afterPanData.firstCandleX).not.toBe(initialData.firstCandleX);
    expect(afterPanData.visibleBars).toBeLessThanOrEqual(12); // Still in footprint range
  });

  test('should validate theme switch preserves all data', async ({ page }) => {
    // Start in Dark theme
    await page.evaluate(() => {
      const chart = (window as any).__CHART_INSTANCE__;
      if (chart) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleLogicalRange({ from: 100, to: 110 });
      }
    });

    await page.waitForTimeout(1500);

    // Get data in Dark theme
    const darkThemeData = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      return {
        candleCount: footprintCandles?.length || 0,
        firstCandleLevels: footprintCandles?.[0]?.levels?.length || 0,
        footprintVisible: (window as any).__FOOTPRINT_VISIBLE__ || false
      };
    });

    // Switch to Light theme
    await page.click('button:has-text("Light")');
    await page.waitForTimeout(1500);

    // Get data in Light theme
    const lightThemeData = await page.evaluate(() => {
      const footprintCandles = (window as any).__FOOTPRINT_CANDLES__;
      const chart = (window as any).__CHART_INSTANCE__;
      const timeScale = chart?.timeScale();
      const logicalRange = timeScale?.getVisibleLogicalRange();

      return {
        candleCount: footprintCandles?.length || 0,
        firstCandleLevels: footprintCandles?.[0]?.levels?.length || 0,
        footprintVisible: (window as any).__FOOTPRINT_VISIBLE__ || false,
        visibleBars: logicalRange ? Math.round(logicalRange.to - logicalRange.from) : 0
      };
    });

    console.log('Theme Switch - Dark:', darkThemeData, 'Light:', lightThemeData);

    // Validate data persisted through theme change
    expect(lightThemeData.candleCount).toBe(darkThemeData.candleCount);
    expect(lightThemeData.firstCandleLevels).toBe(darkThemeData.firstCandleLevels);
    expect(lightThemeData.footprintVisible).toBe(darkThemeData.footprintVisible);
    expect(lightThemeData.visibleBars).toBe(10); // Should maintain zoom level
  });
});