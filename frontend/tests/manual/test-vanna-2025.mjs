/**
 * Test script for Vanna with 2025 query
 * Tests if Vanna now generates SQL for future years
 */

const BASE_URL = 'http://localhost:8002';

async function login() {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'admin@nqhub.com',
      password: 'admin_inicial_2024'
    })
  });

  if (!response.ok) {
    console.error('❌ Login failed:', await response.text());
    process.exit(1);
  }

  const data = await response.json();
  return data.access_token;
}

async function testVannaQuery(token, question) {
  console.log(`\n=== Testing Query: "${question}" ===\n`);

  const response = await fetch(`${BASE_URL}/api/v1/assistant/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: question,
      conversation_id: null
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ Query failed:', errorText);
    return;
  }

  const result = await response.json();

  // Extract the assistant message content
  const content = result.assistant_message?.content || '';
  const metadata = result.metadata || {};

  console.log('📊 Response:\n');
  console.log(content);

  if (metadata.sql) {
    console.log('\n🔍 Generated SQL:');
    console.log(metadata.sql);
  }

  // Check if query was rejected
  if (content.includes('no puedo generar') || content.includes('NO 2025') || content.includes('cannot generate')) {
    console.log('\n❌ FAIL: Query was rejected (should generate SQL)');
    return false;
  } else if (metadata.sql) {
    console.log('\n✅ SUCCESS: SQL was generated for 2025 query');
    return true;
  }

  return false;
}

async function main() {
  try {
    const token = await login();
    console.log('✅ Login successful');

    // Test 1: 2025 query (should now generate SQL)
    const test1 = await testVannaQuery(token, 'dame el minimo y maximo de NQ de noviembre de 2025');

    // Test 2: Query without year (should generate SQL or ask for year)
    const test2 = await testVannaQuery(token, 'dame el minimo y maximo de NQ de noviembre');

    console.log('\n\n📋 Summary:');
    console.log(`Test 1 (2025 query): ${test1 ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Test 2 (no year): ${test2 !== false ? '✅ PASS' : '❌ FAIL'}`);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

main();
