"""In-memory threadsafe job registry for the API."""

import queue
import threading
import uuid
from dataclasses import dataclass, field
from time import time
from typing import Optional


@dataclass
class Job:
    """Represents a single video generation job."""

    job_id: str
    status: str  # pending | running | complete | failed
    stage: str
    topic_or_title: str
    created_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error: Optional[str] = None
    output_files: list[str] = field(default_factory=list)
    log_queue: queue.Queue = field(default_factory=queue.Queue)
    log_history: list[str] = field(default_factory=list)  # Keep all logs for replay
    work_dir: Optional[str] = None

    @property
    def elapsed_sec(self) -> Optional[float]:
        """Seconds elapsed since job started."""
        if self.started_at is None:
            return None
        end = self.finished_at if self.finished_at else time()
        return end - self.started_at


class JobStore:
    """Thread-safe in-memory job registry."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()

    def create(
        self,
        stage: str,
        topic_or_title: str,
    ) -> Job:
        """Create a new pending job."""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            status="pending",
            stage=stage,
            topic_or_title=topic_or_title,
            created_at=time(),
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_all(self) -> list[Job]:
        """List all jobs, newest first."""
        with self._lock:
            return sorted(
                self._jobs.values(), key=lambda j: j.created_at, reverse=True
            )

    def update_status(
        self,
        job_id: str,
        status: str,
        **fields,
    ) -> None:
        """Update job status and optional other fields."""
        with self._lock:
            if job_id not in self._jobs:
                return
            job = self._jobs[job_id]
            job.status = status
            for key, value in fields.items():
                if hasattr(job, key):
                    setattr(job, key, value)


# Module-level singleton
store = JobStore()
