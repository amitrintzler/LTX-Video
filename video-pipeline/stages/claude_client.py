"""
stages/claude_client.py — Shared LLM helpers for Claude Code CLI and LM Studio.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from typing import Any, Optional


class ClaudeCLIError(RuntimeError):
    pass


def run_claude_research(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    schema: dict[str, Any],
    timeout: int = 300,
) -> dict[str, Any]:
    """Call Claude CLI with WebSearch enabled for live research synthesis."""
    cmd = [
        "claude",
        "--print",
        "--output-format", "text",
        "--model", model,
        "--system-prompt", system_prompt,
        "--allowedTools", "WebSearch",
        "--dangerously-skip-permissions",
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise ClaudeCLIError(
            "Claude Code CLI not found on PATH."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ClaudeCLIError("Claude Code CLI timed out during research") from e

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise ClaudeCLIError(stderr[-2000:] or "Claude Code CLI failed without output")

    output = (result.stdout or "").strip()
    if not output:
        raise ClaudeCLIError("Claude Code CLI returned empty output")

    payload = _extract_json_payload(output)
    if isinstance(payload, dict):
        return payload
    raise ClaudeCLIError("Claude Code CLI did not return valid JSON for research")


def run_claude_text(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    provider: str = "claude",
    base_url: str = "http://localhost:1234/v1",
    api_key: str = "lm-studio",
    timeout: int = 600,
) -> str:
    """Run the configured LLM backend and return raw text output."""
    result = _run_llm(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
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
    provider: str = "claude",
    base_url: str = "http://localhost:1234/v1",
    api_key: str = "lm-studio",
    timeout: int = 600,
    max_tokens: int = 32768,
) -> dict[str, Any]:
    """Run the configured LLM backend and parse a structured JSON response."""
    result = _run_llm(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        output_format="json",
        json_schema=schema,
        timeout=timeout,
        max_tokens=max_tokens,
    )
    try:
        payload = _extract_json_payload(result)
    except Exception:
        payload = None
    if isinstance(payload, dict):
        return payload

    repaired = _repair_json_response(
        prompt=prompt,
        raw_output=result,
        model=model,
        system_prompt=system_prompt,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        schema=schema,
        timeout=timeout,
        max_tokens=max_tokens,
    )
    payload = _extract_json_payload(repaired)
    if not isinstance(payload, dict):
        raise ClaudeCLIError("LLM backend did not return valid JSON")
    return payload


def _run_llm(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    provider: str,
    base_url: str,
    api_key: str,
    output_format: str,
    json_schema: Optional[dict[str, Any]] = None,
    timeout: int = 600,
    max_tokens: int = 32768,
) -> str:
    if provider == "lmstudio":
        return _run_lmstudio(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            base_url=base_url,
            api_key=api_key,
            output_format=output_format,
            json_schema=json_schema,
            timeout=timeout,
            max_tokens=max_tokens,
        )

    return _run_claude(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        output_format=output_format,
        json_schema=json_schema,
        timeout=timeout,
    )


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


def _run_lmstudio(
    *,
    prompt: str,
    model: str,
    system_prompt: str,
    base_url: str,
    api_key: str,
    output_format: str,
    json_schema: Optional[dict[str, Any]] = None,
    timeout: int = 600,
    max_tokens: int = 32768,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    messages = _build_lmstudio_messages(system_prompt=system_prompt, prompt=prompt, model=model)
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.0 if json_schema is not None else 0.2,
    }
    if json_schema is not None:
        body["max_tokens"] = max_tokens
    if json_schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": json_schema,
                "strict": True,
            },
        }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        raise ClaudeCLIError(
            f"LM Studio API returned HTTP {e.code} at {url}: {details[-2000:] or e.reason}"
        ) from e
    except urllib.error.URLError as e:
        raise ClaudeCLIError(
            f"Cannot reach LM Studio API at {url}. Start LM Studio's local server on port 1234."
        ) from e

    try:
        choice = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ClaudeCLIError("LM Studio returned an unexpected response shape") from e

    if isinstance(choice, list):
        choice = "".join(
            part.get("text", "")
            for part in choice
            if isinstance(part, dict)
        )

    if not isinstance(choice, str):
        choice = str(choice)

    if output_format == "json" and json_schema is not None:
        return choice.strip()
    return choice.strip()


def _build_lmstudio_messages(*, system_prompt: str, prompt: str, model: str) -> list[dict[str, str]]:
    """Build chat messages for LM Studio.

    Gemma instruction-tuned models are documented as user/model-only, so we fold
    the system instructions into the first user turn for those models. Other
    chat-tuned models keep the standard system+user split.
    """
    if "gemma" in model.lower():
        combined = (
            "System instructions:\n"
            f"{system_prompt.strip()}\n\n"
            "Task:\n"
            f"{prompt.strip()}\n"
        )
        return [{"role": "user", "content": combined}]

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]


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
            raise ClaudeCLIError("LLM backend did not return valid JSON")
        data = json.loads(text[start : end + 1])

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


def _repair_json_response(
    *,
    prompt: str,
    raw_output: str,
    model: str,
    system_prompt: str,
    provider: str,
    base_url: str,
    api_key: str,
    schema: dict[str, Any],
    timeout: int,
    max_tokens: int = 32768,
) -> str:
    repair_prompt = (
        "The previous response was not valid JSON.\n"
        "Return exactly one JSON object that matches the schema below.\n"
        "Do not add markdown, explanation, or code fences.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n\n"
        f"Original task:\n{prompt}\n\n"
        f"Invalid response:\n{raw_output}\n"
    )
    return _run_llm(
        prompt=repair_prompt,
        model=model,
        system_prompt=system_prompt,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        output_format="json",
        json_schema=schema,
        timeout=timeout,
        max_tokens=max_tokens,
    )
