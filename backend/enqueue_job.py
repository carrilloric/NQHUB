#!/usr/bin/env python3
"""
Script to manually enqueue an ETL job for processing
"""
import redis
from rq import Queue

# Connect to Redis
redis_conn = redis.Redis(host='localhost', port=6379, db=0)
queue = Queue('etl_queue', connection=redis_conn)

# ETL job ID from the database
job_id = 'edf3b71a-287b-405e-9c04-58c9bb9a19a4'

# Enqueue the job
job = queue.enqueue(
    'app.etl.tasks.process_etl_job',
    job_id,
    job_timeout='2h',  # 2 hour timeout for large files
    result_ttl=86400,   # Keep result for 24 hours
    failure_ttl=86400   # Keep failure info for 24 hours
)

print(f"✅ Job enqueued successfully!")
print(f"   Job ID: {job.id}")
print(f"   ETL Job ID: {job_id}")
print(f"   Queue: etl_queue")
print(f"   Status: {job.get_status()}")