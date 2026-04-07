"""
stages/topic_utils.py — Structured topic document helpers.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Union

from stages.scene_utils import safe_slug

TopicInput = Union[str, dict[str, Any]]


def is_topic_document(candidate: Any) -> bool:
    if not isinstance(candidate, dict):
        return False
    if "scenes" in candidate:
        return False
    return candidate.get("kind") == "topic" or any(
        key in candidate for key in ("lesson_id", "slug", "research_angles", "search_queries")
    )


def topic_title(topic: TopicInput) -> str:
    if isinstance(topic, dict):
        title = (
            topic.get("title")
            or topic.get("lesson_title")
            or topic.get("slug")
            or topic.get("lesson_id")
        )
        if isinstance(title, str) and title.strip():
            return title.strip()
        return "untitled"

    text = str(topic).strip()
    return text or "untitled"


def topic_slug(topic: TopicInput) -> str:
    if isinstance(topic, dict):
        slug = topic.get("slug") or topic.get("lesson_id") or topic.get("title")
        if isinstance(slug, str) and slug.strip():
            return safe_slug(slug)
        return "untitled"

    return safe_slug(topic_title(topic))


def topic_signature(topic: TopicInput) -> str:
    if isinstance(topic, dict):
        signature = topic.get("signature")
        if isinstance(signature, str) and signature.strip():
            return signature.strip()
        payload = json.dumps(topic, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    else:
        payload = topic_title(topic)

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def topic_context_json(topic: TopicInput) -> str:
    if isinstance(topic, dict):
        return json.dumps(topic, indent=2, ensure_ascii=False, sort_keys=True)
    return topic_title(topic)
