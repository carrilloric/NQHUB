#!/usr/bin/env python3
"""
Re-enqueue pending ETL job
"""
import redis
from rq import Queue
import sys

# Job ID del archivo TUW.zip
JOB_ID = "15904bd1-bfb4-4b5d-9d76-5e642300bee7"

# Conectar a Redis
r = redis.from_url("redis://localhost:6379")
q = Queue('etl_queue', connection=r)

# Importar la función de procesamiento
from app.etl.tasks import process_etl_job

# Calculate dynamic timeout based on file size (214 MB)
# Formula: min(7200, 1800 + (file_size_gb * 900))
# For 214 MB = 0.214 GB: 1800 + (0.214 * 900) = 1992 seconds
timeout = 1992

# Enqueue el job
print(f"Enqueuing job {JOB_ID}...")
job = q.enqueue(
    process_etl_job,
    JOB_ID,
    job_id=f"rq:job:{JOB_ID}",
    job_timeout=timeout
)

print(f"✅ Job enqueued successfully!")
print(f"   Job ID: {job.id}")
print(f"   Queue position: {q.count}")
print(f"   Timeout: {timeout}s ({timeout/60:.1f} minutes)")
