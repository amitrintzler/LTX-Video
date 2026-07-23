"""Custom logging handler that routes messages to a queue for SSE streaming."""

import logging
import queue
from typing import Callable, Optional


class QueueLogHandler(logging.Handler):
    """Log handler that puts formatted log records into a queue and optionally stores them."""

    def __init__(self, q: queue.Queue, on_log: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.q = q
        self.on_log = on_log  # Callback to store logs (e.g., append to job.log_history)
        self.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
        )

    def emit(self, record: logging.LogRecord):
        """Put formatted log record into queue and call on_log callback."""
        try:
            formatted = self.format(record)
            self.q.put(formatted)
            if self.on_log:
                self.on_log(formatted)
        except Exception:
            self.handleError(record)


def make_job_logger(
    job_id: str,
    log_queue: queue.Queue,
    on_log: Optional[Callable[[str], None]] = None,
) -> logging.Logger:
    """Create an isolated logger for one job.

    Does NOT propagate to root or parent loggers, ensuring logs from one job
    do not bleed into another job's log stream.

    Args:
        job_id: Unique job ID
        log_queue: Queue for SSE streaming
        on_log: Optional callback to store logs (e.g., job.log_history.append)
    """
    logger = logging.getLogger(f"pipeline.job.{job_id}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # CRITICAL: no bleed between jobs

    # Remove existing handlers if present (e.g., on job retry)
    logger.handlers.clear()

    handler = QueueLogHandler(log_queue, on_log)
    logger.addHandler(handler)

    return logger
