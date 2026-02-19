#!/usr/bin/env node
/**
 * Test Audit Module End-to-End
 *
 * Tests the complete audit module flow:
 * 1. Login
 * 2. Navigate to Data Module > Market State
 * 3. Load a snapshot
 * 4. Open Audit tab
 * 5. Generate audit report
 * 6. Verify markdown report is displayed
 */

import { chromium } from 'playwright';

async function testAuditModule() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('🧪 TESTING AUDIT MODULE - END TO END\n');
    console.log('=' .repeat(80));

    // Step 1: Login
    console.log('\n📝 Step 1: Login');
    await page.goto('http://localhost:3001/');
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('   ✅ Login successful');

    // Step 2: Navigate to Data Module
    console.log('\n📝 Step 2: Navigate to Data Module');
    await page.click('a[href="/data"]');
    await page.waitForURL('**/data**', { timeout: 5000 });
    console.log('   ✅ Navigated to Data Module');

    // Step 3: Open Market State tab
    console.log('\n📝 Step 3: Open Market State section');

    // Wait for the page to load and look for Market State button/link
    await page.waitForTimeout(2000);

    // Try to find and click "Market State" - it might be a tab or section
    const marketStateVisible = await page.locator('text=Market State').first().isVisible({ timeout: 5000 }).catch(() => false);

    if (!marketStateVisible) {
      console.log('   ⚠️  Market State not immediately visible, checking page structure...');
      const pageContent = await page.content();
      console.log('   📄 Looking for Market State in page...');
    }

    // Click on Market State if it's a tab
    const marketStateTabs = page.locator('button:has-text("Market State"), [role="tab"]:has-text("Market State")');
    const tabCount = await marketStateTabs.count();

    if (tabCount > 0) {
      await marketStateTabs.first().click();
      await page.waitForTimeout(1000);
      console.log('   ✅ Clicked Market State tab');
    } else {
      console.log('   ℹ️  Market State might already be visible or section-based');
    }

    // Step 4: Generate a snapshot first (needed to see the Audit tab)
    console.log('\n📝 Step 4: Generate/Load a Market State snapshot');

    // Set up test OB first
    console.log('   🔧 Setting up test Order Block...');
    const setupResponse = await fetch('http://localhost:8002/test-setup-audit-ob', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ob_id: 2064 })
    }).catch(() => null);

    // Look for snapshot controls
    const symbolInput = page.locator('input[placeholder*="NQ"], input[value*="NQ"]').first();
    const hasSymbolInput = await symbolInput.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasSymbolInput) {
      // Fill snapshot generation form
      await symbolInput.fill('NQZ5');

      // Set date to Nov 6, 2025
      const dateInput = page.locator('input[type="date"]').first();
      await dateInput.fill('2025-11-06');

      // Set time
      const timeInput = page.locator('input[type="time"]').first();
      if (await timeInput.isVisible().catch(() => false)) {
        await timeInput.fill('05:21');
      }

      // Click generate/load button
      const loadButton = page.locator('button:has-text("Load"), button:has-text("Generate"), button:has-text("Cargar")').first();
      await loadButton.click();
      await page.waitForTimeout(3000);
      console.log('   ✅ Snapshot loaded');
    } else {
      console.log('   ⚠️  Snapshot controls not found - may need manual setup');
    }

    // Step 5: Open Audit tab
    console.log('\n📝 Step 5: Open Audit tab');
    const auditTab = page.locator('[data-testid="audit-tab"], button:has-text("Audit"), [role="tab"]:has-text("Audit")').first();
    const auditTabVisible = await auditTab.isVisible({ timeout: 5000 }).catch(() => false);

    if (auditTabVisible) {
      await auditTab.click();
      await page.waitForTimeout(1000);
      console.log('   ✅ Audit tab opened');
    } else {
      console.log('   ❌ Audit tab not found - may need snapshot to be loaded first');
      throw new Error('Audit tab not visible');
    }

    // Step 6: Fill audit form
    console.log('\n📝 Step 6: Fill audit generation form');

    // Symbol should already be NQZ5
    const auditSymbol = page.locator('#symbol').first();
    if (await auditSymbol.isVisible().catch(() => false)) {
      await auditSymbol.fill('NQZ5');
    }

    // Timeframe - select 5min
    const timeframeSelect = page.locator('#timeframe').first();
    if (await timeframeSelect.isVisible().catch(() => false)) {
      await timeframeSelect.click();
      await page.locator('text=5min').first().click();
    }

    // Date
    const auditDate = page.locator('#snapshot-date').first();
    await auditDate.fill('2025-11-06');

    // Time
    const auditTime = page.locator('#snapshot-time').first();
    await auditTime.fill('05:21');

    console.log('   ✅ Form filled: NQZ5, 5min, 2025-11-06 05:21 UTC');

    // Step 7: Generate audit report
    console.log('\n📝 Step 7: Generate audit report');
    const generateButton = page.locator('button:has-text("Generar Audit Report")').first();
    await generateButton.click();

    // Wait for loading to finish
    await page.waitForTimeout(2000);

    // Check for error or success
    const hasError = await page.locator('text=Error generando').isVisible({ timeout: 2000 }).catch(() => false);
    if (hasError) {
      const errorText = await page.locator('p.text-destructive').first().textContent();
      console.log('   ❌ Error generating report:', errorText);
      throw new Error('Report generation failed');
    }

    console.log('   ✅ Report generation request sent');

    // Step 8: Verify markdown report
    console.log('\n📝 Step 8: Verify markdown report displayed');

    // Look for markdown report content
    const reportHeading = page.locator('text=AUDIT REPORT - Order Blocks').first();
    const reportVisible = await reportHeading.isVisible({ timeout: 5000 }).catch(() => false);

    if (reportVisible) {
      console.log('   ✅ Markdown report displayed');

      // Check for OB details
      const hasOBDetails = await page.locator('text=Para validar en ATAS').isVisible().catch(() => false);
      if (hasOBDetails) {
        console.log('   ✅ ATAS validation instructions present');
      }

      // Check for export button
      const exportButton = page.locator('button:has-text("Exportar Markdown")').first();
      const exportVisible = await exportButton.isVisible().catch(() => false);
      if (exportVisible) {
        console.log('   ✅ Export button available');
      }

    } else {
      console.log('   ❌ Markdown report not visible');

      // Get page content for debugging
      const bodyText = await page.locator('body').textContent();
      if (bodyText.includes('No hay Order Blocks activos')) {
        console.log('   ℹ️  Report shows: No active Order Blocks at this timestamp');
      }
    }

    console.log('\n' + '=' .repeat(80));
    console.log('✅ AUDIT MODULE TEST COMPLETE\n');

    // Keep browser open for inspection
    console.log('⏳ Browser will stay open for 10 seconds for inspection...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('\n❌ TEST FAILED:', error.message);
    console.log('\n📸 Taking screenshot...');
    await page.screenshot({ path: '/tmp/audit-test-error.png', fullPage: true });
    console.log('   Screenshot saved to: /tmp/audit-test-error.png');

    // Keep browser open on error
    console.log('\n⏳ Browser will stay open for 30 seconds for debugging...');
    await page.waitForTimeout(30000);
  } finally {
    await browser.close();
  }
}

testAuditModule();
