"""Request/response schemas for the video pipeline REST API."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, model_validator


class JobRequest(BaseModel):
    """Request body for POST /jobs."""

    topic: Optional[str] = None
    script_json: Optional[dict] = None
    stage: Literal[
        "all", "research", "script", "render", "tts", "stitch", "validate"
    ] = "all"
    mode: Literal["narrated", "companion-long", "both"] = "both"
    output_mode: Optional[Literal["narrated", "companion-short", "companion-long"]] = None
    skip_validation: bool = False
    max_scenes: Optional[int] = None
    config_overrides: dict[str, Any] = {}

    @model_validator(mode="after")
    def exactly_one_input(self):
        """Validate that exactly one of topic or script_json is provided."""
        topic_provided = self.topic is not None and str(self.topic).strip()
        script_provided = self.script_json is not None

        if not topic_provided and not script_provided:
            raise ValueError("Either topic or script_json must be provided")
        if topic_provided and script_provided:
            raise ValueError("Cannot provide both topic and script_json")
        return self


class JobResponse(BaseModel):
    """Response body for job creation and listing."""

    job_id: str
    status: Literal["pending", "running", "complete", "failed"]
    created_at: str
    stage: str
    topic_or_title: str


class JobDetail(JobResponse):
    """Extended job response with output files and elapsed time."""

    output_files: list[str] = []
    error: Optional[str] = None
    elapsed_sec: Optional[float] = None


class JobListResponse(BaseModel):
    """Response body for listing all jobs."""

    jobs: list[JobResponse]


class FilesResponse(BaseModel):
    """Response body for listing downloadable files."""

    files: list[str]


class HealthResponse(BaseModel):
    """Response body for health check."""

    status: str
    active_jobs: int
    queued_jobs: int
