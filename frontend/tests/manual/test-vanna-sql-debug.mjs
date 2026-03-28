/**
 * Debug script for Vanna SQL generation
 * Shows the exact SQL being generated
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
  console.log('✅ Response:', JSON.stringify(result, null, 2));
}

async function main() {
  try {
    const token = await login();
    console.log('✅ Login successful');

    // Test the original query that had SQL validation issues
    await testVannaQuery(token, 'dame el maximo valor de NQ en noviembre');

    console.log('\n✅ Test complete!\n');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

main();
