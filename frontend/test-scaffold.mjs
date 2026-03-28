/**
 * Test script to verify frontend scaffold setup
 */

import { chromium } from 'playwright';

async function testScaffold() {
  console.log('🚀 Testing NQHUB 2.0 Frontend Scaffold...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Test landing page
    console.log('1. Testing landing page...');
    await page.goto('http://localhost:3001/');
    await page.waitForSelector('h1');
    console.log('✅ Landing page loaded\n');

    // Test login with mock credentials
    console.log('2. Testing login with MSW mock...');
    await page.fill('input[type="email"]', 'test@nqhub.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    console.log('✅ Login successful, redirected to dashboard\n');

    // Test all new routes
    const routes = [
      { path: '/features', title: 'Feature Engineering' },
      { path: '/backtesting/rule-based', title: 'Rule-Based Backtesting' },
      { path: '/backtesting/ai', title: 'AI-Powered Backtesting' },
      { path: '/ml', title: 'Machine Learning' },
      { path: '/approval', title: 'Approval Workflow' },
      { path: '/bot', title: 'Trading Bots' },
      { path: '/orders', title: 'Orders' },
      { path: '/risk', title: 'Risk Management' },
      { path: '/trades', title: 'Trade History' },
      { path: '/strategies', title: 'Trading Strategies' },
      { path: '/assistant', title: 'AI Assistant' },
      { path: '/settings', title: 'Settings' },
    ];

    console.log('3. Testing new pages...');
    for (const route of routes) {
      await page.goto(`http://localhost:3001${route.path}`);
      await page.waitForSelector('h2');
      const heading = await page.textContent('h2');
      if (heading.includes(route.title)) {
        console.log(`✅ ${route.path} - "${route.title}" loaded successfully`);
      } else {
        console.log(`❌ ${route.path} - Expected "${route.title}", got "${heading}"`);
      }
    }

    // Test MSW API mocking
    console.log('\n4. Testing MSW API handlers...');
    await page.goto('http://localhost:3001/features');

    // Verify the page loads without errors
    const errors = [];
    page.on('pageerror', error => errors.push(error));
    await page.waitForTimeout(2000);

    if (errors.length === 0) {
      console.log('✅ No console errors detected');
    } else {
      console.log('❌ Console errors found:', errors);
    }

    console.log('\n🎉 Frontend scaffold test completed successfully!');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testScaffold().catch(console.error);