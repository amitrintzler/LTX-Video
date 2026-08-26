"""The seam between the engine and whatever actually generates media.

Two shapes have to fit under one protocol. LTX Desktop blocks on a single POST
for the best part of an hour and hands back a path. Hosted services return a
long-running operation and expect polling. So generation is split into submit,
poll and fetch, and a synchronous provider simply collapses them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

PENDING = "pending"
DONE = "done"
FAILED = "failed"


@dataclass
class Job:
    """A submitted request, however the provider chooses to identify it."""

    handle: Any
    payload: dict
    status: str = PENDING
    detail: str = ""
    result: dict | None = None


class ProviderError(RuntimeError):
    """Raised for anything the caller could act on: auth, quota, bad spec."""


@runtime_checkable
class Provider(Protocol):
    name: str
    #: which media kinds this provider will accept, from media.KINDS
    media: tuple[str, ...]

    def supports(self, kind: str) -> bool: ...

    def submit(self, spec, out_dir: Path) -> Job: ...

    def poll(self, job: Job) -> Job: ...

    def fetch(self, job: Job, out_dir: Path) -> Path: ...


class BaseProvider:
    """Shared behaviour: capability checks and the submit-poll-fetch loop."""

    name = "base"
    media: tuple[str, ...] = ()

    def supports(self, kind: str) -> bool:
        return kind in self.media

    def check(self, spec) -> None:
        if not self.supports(spec.kind):
            raise ProviderError(
                f"{self.name} does not generate {spec.kind}; it handles "
                f"{', '.join(self.media) or 'nothing'}"
            )

    def generate(self, spec, out_dir: Path, wait) -> Path:
        """Submit, wait for completion, and return the finished file.

        `wait` is injected so the caller owns sleeping and can report progress
        or cancel; the provider never blocks on its own timer.
        """
        self.check(spec)
        job = self.submit(spec, out_dir)
        while job.status == PENDING:
            wait(job)
            job = self.poll(job)
        if job.status == FAILED:
            raise ProviderError(f"{self.name}: {spec.id} failed: {job.detail}")
        return self.fetch(job, out_dir)
