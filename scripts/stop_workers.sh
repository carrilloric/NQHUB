#!/bin/bash
# Stop all 4 ETL workers

echo "🛑 Stopping 4 ETL workers..."

docker stop nqhub_worker_1 nqhub_worker_2 nqhub_worker_3 nqhub_worker_4

echo ""
echo "✅ Workers stopped"
