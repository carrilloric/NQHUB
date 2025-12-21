/**
 * Test sending a message to the Assistant
 */
import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:3001';

async function testSendMessage() {
  console.log('🧪 Testing Assistant Message Send...\n');

  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Login
    console.log('🔐 Logging in...');
    await page.goto(BASE_URL);
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('   ✅ Login successful\n');

    // Wait for page to load
    await page.waitForTimeout(2000);

    // Find and click the Globe/Assistant button to open panel
    console.log('🌐 Opening Assistant Panel...');
    const globeButton = await page.locator('button[aria-label*="LLM"], button[aria-label*="assistant"], svg.lucide-globe').locator('..').first();
    await globeButton.click();
    console.log('   ✅ Panel opened\n');

    await page.waitForTimeout(2000);

    // Take screenshot after opening panel
    await page.screenshot({ path: '/tmp/assistant-after-open.png', fullPage: true });
    console.log('   📸 Screenshot saved: /tmp/assistant-after-open.png\n');

    // Find and fill the input with exact placeholder
    console.log('💬 Sending message...');
    const input = await page.locator('textarea[placeholder="Ask me anything..."]');
    await input.waitFor({ state: 'visible', timeout: 10000 });
    await input.fill('What is the ETL status?');

    // Click send button
    const sendButton = await page.locator('button:has-text("Send")').first();
    await sendButton.click();
    console.log('   ✅ Message sent\n');

    // Wait for response
    console.log('⏳ Waiting for Claude response...');
    await page.waitForTimeout(5000);

    // Take screenshot of response
    await page.screenshot({ path: '/tmp/assistant-chat-response.png', fullPage: true });
    console.log('   📸 Screenshot saved: /tmp/assistant-chat-response.png\n');

    // Check if messages appeared
    const messageElements = await page.locator('[class*="message"], [class*="Message"]').count();
    console.log(`   ${messageElements > 0 ? '✅' : '❌'} Messages in chat: ${messageElements}\n`);

    console.log('✅ TEST COMPLETED!');

  } catch (error) {
    console.log(`\n❌ ERROR: ${error.message}`);
    await page.screenshot({ path: '/tmp/assistant-chat-error.png', fullPage: true });
  }

  await browser.close();
}

testSendMessage().catch(console.error);
