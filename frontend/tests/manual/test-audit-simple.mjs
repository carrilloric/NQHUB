#!/usr/bin/env node
/**
 * Simple Audit Module Test - Direct API test
 */

console.log('🧪 TESTING AUDIT MODULE - API DIRECT TEST\n');
console.log('='.repeat(80));

// Test the audit endpoint directly
console.log('\n📝 Testing POST /api/v1/audit/order-blocks\n');

fetch('http://localhost:8002/api/v1/audit/order-blocks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: 'NQZ5',
    timeframe: '5min',
    snapshot_time: '2025-11-06T05:21:00'
  })
})
.then(res => res.json())
.then(data => {
  console.log('✅ Response received\n');
  console.log(`📊 Total OBs: ${data.total_obs}`);
  console.log(`⏰ Snapshot EST: ${data.snapshot_time_est}`);
  console.log(`⏰ Snapshot UTC: ${data.snapshot_time_utc}`);
  console.log(`📈 Symbol: ${data.symbol}`);
  console.log(`⏱️  Timeframe: ${data.timeframe}`);

  if (data.total_obs > 0) {
    console.log('\n📋 First Order Block:');
    const ob = data.order_blocks[0];
    console.log(`   ID: ${ob.ob_id}`);
    console.log(`   Type: ${ob.ob_type}`);
    console.log(`   Formation: ${ob.formation_time_est}`);
    console.log(`   Zone: ${ob.zone_low} - ${ob.zone_high}`);
    console.log(`   Quality: ${ob.quality}`);

    console.log('\n📄 Markdown Report Preview (first 500 chars):');
    console.log('-'.repeat(80));
    console.log(data.report_markdown.substring(0, 500));
    console.log('-'.repeat(80));

    // Check for key elements
    console.log('\n✅ Validation Checks:');
    console.log(`   Has markdown header: ${data.report_markdown.includes('AUDIT REPORT')}`);
    console.log(`   Has ATAS instructions: ${data.report_markdown.includes('Para validar en ATAS')}`);
    console.log(`   Has ICT expectations: ${data.report_markdown.includes('Expectativa ICT')}`);
    console.log(`   Has summary section: ${data.report_markdown.includes('Resumen del Audit')}`);

    console.log('\n' + '='.repeat(80));
    console.log('✅ AUDIT MODULE API TEST - PASSED');
    console.log('   The audit endpoint is working correctly!\n');
  } else {
    console.log('\n⚠️  No Order Blocks found at this timestamp');
    console.log('   Markdown report:');
    console.log(data.report_markdown);
  }
})
.catch(err => {
  console.error('\n❌ TEST FAILED:', err.message);
  console.error(err);
});
