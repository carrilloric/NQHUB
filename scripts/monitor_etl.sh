#!/bin/bash
# Real-time ETL monitoring dashboard

echo "📊 NQHUB ETL Monitoring Dashboard"
echo "================================="
echo ""

# Check worker status via API
echo "🔧 Worker Status (via API):"
curl -s http://localhost:8002/api/v1/etl/worker/status | python3 -m json.tool 2>/dev/null || echo "❌ Backend not running"
echo ""

# Check Docker containers
echo "🐳 Docker Containers:"
docker ps --filter "name=nqhub_worker" --format "table {{.Names}}\t{{.Status}}"
echo ""

# Check Redis queue
echo "📦 Redis Queue Status:"
echo "  Jobs in queue: $(redis-cli -h localhost -p 6379 LLEN rq:queue:etl_queue)"
echo ""

# Check recent jobs
echo "📋 Recent Jobs (Last 5):"
curl -s "http://localhost:8002/api/v1/etl/jobs?limit=5" 2>/dev/null | \
  python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for job in data.get('jobs', []):
        status_emoji = '✅' if job['status'] == 'completed' else '❌' if job['status'] == 'failed' else '⏳'
        print(f\"  {status_emoji} [{job['status']}] {job['zip_filename']} - Progress: {job['progress_pct']}%\")
        if job.get('status_detail'):
            print(f\"      Detail: {job['status_detail']}\")
except:
    print('  ❌ Could not fetch jobs')
"
echo ""

# Watch mode
if [ "$1" == "--watch" ] || [ "$1" == "-w" ]; then
    echo "Press Ctrl+C to stop watching..."
    while true; do
        sleep 2
        clear
        $0
    done
fi

echo "💡 Run with --watch to monitor in real-time"
