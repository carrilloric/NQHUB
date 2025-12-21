/**
 * Test script for Vanna Stats Modal
 * Tests the /api/v1/vanna/stats endpoint
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

async function testVannaStats(token) {
  console.log('\n=== Testing Vanna Stats Endpoint ===\n');

  const response = await fetch(`${BASE_URL}/api/v1/vanna/stats`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    console.error('❌ Vanna stats request failed:', await response.text());
    process.exit(1);
  }

  const stats = await response.json();
  console.log('✅ Vanna Stats Response:');
  console.log(JSON.stringify(stats, null, 2));

  // Validate structure
  if (!stats.status) {
    console.error('❌ Missing status field');
    process.exit(1);
  }

  if (stats.status === 'active') {
    console.log('\n✅ Vanna is active!');
    console.log(`   Total documents: ${stats.total_documents}`);
    console.log(`   SQL examples: ${stats.total_sql_examples}`);
    console.log(`   DDL schemas: ${stats.total_ddl}`);

    if (stats.breakdown) {
      console.log('\n   Category Breakdown:');
      console.log(`   - FVG: ${stats.breakdown.fvg}`);
      console.log(`   - Liquidity Pools: ${stats.breakdown.liquidity_pools}`);
      console.log(`   - Order Blocks: ${stats.breakdown.order_blocks}`);
      console.log(`   - ETL: ${stats.breakdown.etl}`);
      console.log(`   - Candles: ${stats.breakdown.candles}`);
      console.log(`   - Other: ${stats.breakdown.other}`);
    }
  } else {
    console.log(`\n⚠️  Vanna status: ${stats.status}`);
    console.log(`   Message: ${stats.message || 'N/A'}`);
  }
}

async function testVannaQueries(token) {
  console.log('\n=== Testing Vanna Queries Endpoint ===\n');

  const response = await fetch(`${BASE_URL}/api/v1/vanna/queries?limit=5`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    console.error('❌ Vanna queries request failed:', await response.text());
    return;
  }

  const queries = await response.json();
  console.log(`✅ Found ${queries.length} queries`);
  queries.forEach((q, i) => {
    console.log(`\n   Query ${i + 1}:`);
    console.log(`   ${q.content.substring(0, 80)}...`);
  });
}

async function main() {
  try {
    const token = await login();
    console.log('✅ Login successful');

    await testVannaStats(token);
    await testVannaQueries(token);

    console.log('\n✅ All tests passed!\n');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

main();
