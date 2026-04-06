"""
stages/claude_client.py — Shared Claude Code CLI helpers.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Optional


class ClaudeCLIError(RuntimeError):
    pass


def run_claude_text(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    timeout: int = 600,
) -> str:
    """Run Claude Code CLI and return the raw text output."""
    result = _run_claude(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        output_format="text",
        timeout=timeout,
    )
    return result.strip()


def run_claude_json(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    schema: dict[str, Any],
    timeout: int = 600,
) -> dict[str, Any]:
    """Run Claude Code CLI and parse a structured JSON response."""
    result = _run_claude(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        output_format="json",
        json_schema=schema,
        timeout=timeout,
    )
    payload = _extract_json_payload(result)
    if not isinstance(payload, dict):
        raise ClaudeCLIError("Claude CLI did not return a JSON object")
    return payload


def _run_claude(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    output_format: str,
    json_schema: Optional[dict[str, Any]] = None,
    timeout: int = 600,
) -> str:
    cmd = [
        "claude",
        "--print",
        "--output-format",
        output_format,
        "--model",
        model,
        "--system-prompt",
        system_prompt,
        "--tools",
        "",
        "--dangerously-skip-permissions",
    ]
    if json_schema is not None:
        cmd.extend(["--json-schema", json.dumps(json_schema)])
    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise ClaudeCLIError(
            "Claude Code CLI not found on PATH. Install Claude Code or add 'claude' to PATH."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ClaudeCLIError("Claude Code CLI timed out") from e

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise ClaudeCLIError(stderr[-2000:] or "Claude Code CLI failed without output")

    output = (result.stdout or "").strip()
    if not output:
        raise ClaudeCLIError("Claude Code CLI returned empty output")
    return output


def _extract_json_payload(output: str) -> Any:
    text = output.strip()

    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ClaudeCLIError("Claude CLI did not return valid JSON")
        data = json.loads(text[start : end + 1])

    # Claude Code JSON output may wrap the text result in a content array.
    if isinstance(data, dict) and "content" in data and isinstance(data["content"], list):
        chunks = []
        for chunk in data["content"]:
            if isinstance(chunk, dict) and chunk.get("type") == "text":
                chunks.append(chunk.get("text", ""))
        joined = "".join(chunks).strip()
        if joined:
            return _extract_json_payload(joined)

    if isinstance(data, str):
        return _extract_json_payload(data)

    return data
