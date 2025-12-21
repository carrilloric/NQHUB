/**
 * Test script for verifying Vanna's timeframe selection based on query keywords
 * Tests that Vanna selects the correct candlestick table based on temporal context
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

async function testQuery(token, question, expectedTable) {
  console.log(`\n=== Testing: "${question}" ===`);
  console.log(`Expected table: ${expectedTable}\n`);

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
  const metadata = result.metadata || {};

  if (metadata.sql) {
    console.log('🔍 Generated SQL:');
    console.log(metadata.sql);

    // Check if it uses the expected table
    const usesExpectedTable = metadata.sql.includes(expectedTable);

    if (usesExpectedTable) {
      console.log(`✅ SUCCESS: SQL uses ${expectedTable}`);
      return true;
    } else {
      console.log(`❌ FAIL: SQL does NOT use ${expectedTable}`);

      // Try to detect which table it actually used
      const tables = ['candlestick_30s', 'candlestick_1min', 'candlestick_5min', 'candlestick_15min',
                      'candlestick_1hr', 'candlestick_4hr', 'candlestick_daily', 'candlestick_weekly'];
      const usedTable = tables.find(t => metadata.sql.includes(t));
      if (usedTable) {
        console.log(`   Actually used: ${usedTable}`);
      }

      return false;
    }
  } else {
    console.log('❌ FAIL: No SQL generated');
    return false;
  }
}

async function main() {
  try {
    const token = await login();
    console.log('✅ Login successful\n');
    console.log('='.repeat(80));

    const tests = [
      // Daily queries
      {
        query: 'cual fue el volumen diario promedio de noviembre 2025',
        expected: 'candlestick_daily'
      },
      {
        query: 'dame el máximo y mínimo por día de noviembre 2025',
        expected: 'candlestick_daily'
      },

      // Weekly queries
      {
        query: 'análisis semanal de noviembre 2025',
        expected: 'candlestick_weekly'
      },
      {
        query: 'cual fue el volumen de la semana del 4 al 8 de noviembre 2025',
        expected: 'candlestick_weekly'
      },

      // Hourly queries
      {
        query: 'cual fue el precio cada hora del 5 de noviembre 2025',
        expected: 'candlestick_1hr'
      },

      // Intraday queries (should use 5min by default)
      {
        query: 'cual fue el máximo de NQ en noviembre 2025',
        expected: 'candlestick_5min' // Most common table
      },

      // Specific minute queries
      {
        query: 'volumen cada 5 minutos del 5 de noviembre',
        expected: 'candlestick_5min'
      },

      // 15-minute session queries
      {
        query: 'análisis de la sesión de las 15:00 a 15:30 del 5 de noviembre',
        expected: 'candlestick_15min'
      }
    ];

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
      const result = await testQuery(token, test.query, test.expected);
      if (result) {
        passed++;
      } else {
        failed++;
      }
      console.log(''); // Blank line between tests
    }

    console.log('='.repeat(80));
    console.log('\n📋 Final Summary:');
    console.log(`✅ Passed: ${passed}/${tests.length}`);
    console.log(`❌ Failed: ${failed}/${tests.length}`);

    if (failed === 0) {
      console.log('\n🎉 All tests passed! Timeframe selection is working correctly!');
    } else {
      console.log('\n⚠️ Some tests failed. Review the output above for details.');
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Test suite failed:', error.message);
    process.exit(1);
  }
}

main();
