"""
Progress Tracker for Market State Snapshot Generation

Simple in-memory progress tracking using a dict (can be upgraded to Redis later)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
import uuid

@dataclass
class ProgressInfo:
    job_id: str
    symbol: str
    total_snapshots: int
    completed_snapshots: int
    status: str  # "running", "completed", "error"
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def percentage(self) -> float:
        if self.total_snapshots == 0:
            return 0.0
        return round((self.completed_snapshots / self.total_snapshots) * 100, 1)

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()

    @property
    def estimated_seconds_remaining(self) -> float:
        if self.completed_snapshots == 0:
            return 0.0
        avg_time_per_snapshot = self.elapsed_seconds / self.completed_snapshots
        remaining_snapshots = self.total_snapshots - self.completed_snapshots
        return round(avg_time_per_snapshot * remaining_snapshots, 1)


class ProgressTracker:
    """Thread-safe in-memory progress tracker"""

    def __init__(self):
        self._jobs: Dict[str, ProgressInfo] = {}

    def create_job(self, symbol: str, total_snapshots: int) -> str:
        """Create a new progress tracking job"""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = ProgressInfo(
            job_id=job_id,
            symbol=symbol,
            total_snapshots=total_snapshots,
            completed_snapshots=0,
            status="running",
            start_time=datetime.utcnow()
        )
        return job_id

    def update_progress(self, job_id: str, completed: int):
        """Update job progress"""
        if job_id in self._jobs:
            self._jobs[job_id].completed_snapshots = completed

    def complete_job(self, job_id: str):
        """Mark job as completed"""
        if job_id in self._jobs:
            self._jobs[job_id].status = "completed"
            self._jobs[job_id].end_time = datetime.utcnow()

    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed"""
        if job_id in self._jobs:
            self._jobs[job_id].status = "error"
            self._jobs[job_id].error_message = error_message
            self._jobs[job_id].end_time = datetime.utcnow()

    def get_progress(self, job_id: str) -> Optional[ProgressInfo]:
        """Get job progress info"""
        return self._jobs.get(job_id)

    def delete_job(self, job_id: str):
        """Delete job from tracker"""
        if job_id in self._jobs:
            del self._jobs[job_id]


# Global singleton instance
progress_tracker = ProgressTracker()
