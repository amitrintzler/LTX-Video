"""What the engine is asked to make, and what comes back.

A shot used to mean a video clip, because video was the only thing this pipeline
produced. Stills were side effects. Naming the kind up front lets one engine
serve video, images and audio, and lets a provider refuse work it cannot do
before a render starts rather than halfway through.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

VIDEO = "video"
IMAGE = "image"
AUDIO = "audio"
KINDS = (VIDEO, IMAGE, AUDIO)


@dataclass(frozen=True)
class MediaSpec:
    """One piece of media to generate.

    `extra` carries whatever a particular provider understands - camera motion,
    negative prompts, LoRAs - without the engine needing to know the vocabulary
    of every service it might talk to.
    """

    id: str
    kind: str
    prompt: str = ""
    seconds: float | None = None
    width: int | None = None
    height: int | None = None
    seed: int | None = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"{self.id}: unknown media kind {self.kind!r}")
        if self.kind == IMAGE and self.seconds:
            raise ValueError(f"{self.id}: a still cannot have a duration")
        if self.kind == VIDEO and not self.seconds:
            raise ValueError(f"{self.id}: video needs a duration")


@dataclass(frozen=True)
class MediaAsset:
    """Generated media on disk, and the request that produced it."""

    spec: MediaSpec
    path: Path
    provider: str
    payload: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
