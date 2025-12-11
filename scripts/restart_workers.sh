#!/bin/bash
# Restart all 4 ETL workers

echo "🔄 Restarting 4 ETL workers..."

docker restart nqhub_worker_1 nqhub_worker_2 nqhub_worker_3 nqhub_worker_4

sleep 2
echo ""
echo "📊 Worker Status:"
docker ps --filter "name=nqhub_worker" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Workers restarted. Check status at: http://localhost:8002/api/v1/etl/worker/status"
