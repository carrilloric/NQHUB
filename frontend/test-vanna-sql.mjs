/**
 * Test Vanna.AI NL→SQL functionality through AI Assistant
 */
import { chromium } from 'playwright';

async function testVannaSQLQueries() {
  console.log('🧪 Testing Vanna.AI NL→SQL Integration\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Login
    console.log('1️⃣  Logging in...');
    await page.goto('http://localhost:3001');
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');
    await page.waitForURL('**/dashboard');
    console.log('✅ Logged in successfully\n');

    // 2. Go to Dashboard (where AssistantPanelCenter is)
    console.log('2️⃣  Navigating to Dashboard...');
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForTimeout(2000);
    console.log('✅ Dashboard loaded\n');

    // 3. Test SQL queries
    const sqlQueries = [
      "How many FVGs are in the database?",
      "Show me all unmitigated liquidity pools",
      "What's the average gap size for bullish FVGs?",
      "How many ETL jobs completed today?"
    ];

    for (let i = 0; i < sqlQueries.length; i++) {
      const query = sqlQueries[i];
      console.log(`\n${'='.repeat(60)}`);
      console.log(`📊 Query ${i+1}/${sqlQueries.length}: "${query}"`);
      console.log('='.repeat(60));

      // Find textarea and send query
      const textarea = page.locator('textarea[placeholder="Ask me anything..."]');
      await textarea.fill(query);

      // Click send button
      const sendButton = page.locator('button:has-text("Send")');
      await sendButton.click();
      console.log('⏳ Sending query to assistant...');

      // Wait for response (look for assistant message)
      await page.waitForTimeout(8000); // Give Vanna time to generate SQL and execute

      // Get the last assistant message
      const messages = await page.locator('.bg-muted.text-foreground').all();
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        const responseText = await lastMessage.textContent();
        console.log('\n🤖 Assistant Response:');
        console.log('-'.repeat(60));
        console.log(responseText.trim());
        console.log('-'.repeat(60));

        // Check if response contains SQL-related keywords
        if (responseText.includes('COUNT') || responseText.includes('result') || responseText.includes('Found')) {
          console.log('✅ Query appears to have executed successfully!');
        } else if (responseText.includes('error') || responseText.includes('Error') || responseText.includes('failed')) {
          console.log('❌ Query failed or returned error');
        } else {
          console.log('ℹ️  Response received (check manually)');
        }
      } else {
        console.log('⚠️  No response found');
      }

      // Wait before next query
      await page.waitForTimeout(2000);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✨ All Vanna.AI tests completed!');
    console.log('='.repeat(60));

    // Keep browser open for manual inspection
    console.log('\n👀 Browser will stay open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

testVannaSQLQueries().catch(console.error);
