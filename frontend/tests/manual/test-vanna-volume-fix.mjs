/**
 * Test script for the exact user query about average volume
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
    return false;
  }

  const result = await response.json();

  const content = result.assistant_message?.content || '';
  const metadata = result.metadata || {};

  console.log('📊 Response:\n');
  console.log(content);

  if (metadata.sql) {
    console.log('\n🔍 Generated SQL:');
    console.log(metadata.sql);

    // Check if it uses active_contracts JOIN
    if (metadata.sql.includes('active_contracts') && metadata.sql.includes('is_current')) {
      console.log('\n✅ SUCCESS: SQL uses active_contracts JOIN pattern');
      return true;
    } else {
      console.log('\n❌ FAIL: SQL does NOT use active_contracts JOIN pattern');
      return false;
    }
  }

  return false;
}

async function main() {
  try {
    const token = await login();
    console.log('✅ Login successful');

    // Test the EXACT query the user asked
    const success = await testVannaQuery(
      token,
      'cual fue el promedio de volumen de las velas de las 9:30 AM EST en el mes de noviembre de 2025'
    );

    console.log('\n\n📋 Final Result:');
    console.log(success ? '✅ PASS: active_contracts pattern is working!' : '❌ FAIL: active_contracts pattern NOT used');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

main();
