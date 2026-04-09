"""
stages/claude_client.py — Shared LLM helpers for Claude Code CLI and LM Studio.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional


class ClaudeCLIError(RuntimeError):
    pass


class StructuredLLMResponseError(ClaudeCLIError):
    def __init__(
        self,
        message: str,
        *,
        prompt: str,
        raw_output: str,
        repaired_output: str | None = None,
        provider: str = "claude",
        model: str = "",
    ) -> None:
        super().__init__(message)
        self.prompt = prompt
        self.raw_output = raw_output
        self.repaired_output = repaired_output
        self.provider = provider
        self.model = model


class CodexCLIError(ClaudeCLIError):
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
        "--output-format", "json",
        "--model", model,
        "--system-prompt", system_prompt,
        "--allowedTools", "WebSearch",
        "--dangerously-skip-permissions",
        "--json-schema", json.dumps(schema),
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

    # Claude CLI --output-format json wraps output in an envelope:
    # {"type":"result","subtype":"success","result":"...","is_error":false,...}
    # Try to unwrap it, then extract the actual research JSON.
    try:
        envelope = json.loads(output)
    except json.JSONDecodeError:
        envelope = None

    if isinstance(envelope, dict):
        # Unwrap the CLI envelope to get the actual text Claude returned
        inner = envelope.get("result") or envelope.get("content") or ""
        if isinstance(inner, list):
            inner = "".join(
                c.get("text", "") for c in inner
                if isinstance(c, dict) and c.get("type") == "text"
            )
        if isinstance(inner, str) and inner.strip():
            payload = _extract_json_payload(inner.strip())
            if isinstance(payload, dict):
                return payload
        # Maybe the envelope itself is the payload (--json-schema forced it)
        if all(k in envelope for k in ("research_markdown", "outline_markdown")):
            return envelope

    payload = _extract_json_payload(output)
    if isinstance(payload, dict):
        return payload
    raise ClaudeCLIError("Claude Code CLI did not return valid JSON for research")


def run_codex_research(
    *,
    prompt: str,
    schema: dict[str, Any],
    model: Optional[str] = None,
    timeout: int = 300,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Call Codex CLI with web search enabled for live research synthesis."""
    cmd = ["codex", "--search", "exec", "--full-auto"]
    if model:
        cmd.extend(["--model", model])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output.json"
        schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
        cmd.extend(
            [
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
            ]
        )
        if work_dir is not None:
            cmd.extend(["--cd", str(work_dir)])
        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as e:
            raise CodexCLIError("Codex CLI not found on PATH.") from e
        except subprocess.TimeoutExpired as e:
            raise CodexCLIError("Codex CLI timed out during research") from e

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise CodexCLIError(stderr[-2000:] or "Codex CLI failed without output")

        if not output_path.exists():
            output = (result.stdout or "").strip()
            if output:
                payload = _extract_json_payload(output)
                if isinstance(payload, dict):
                    return payload
            raise CodexCLIError("Codex CLI did not produce an output file")

        output = output_path.read_text().strip()
        if not output:
            raise CodexCLIError("Codex CLI returned empty output")

        payload = _extract_json_payload(output)
        if isinstance(payload, dict):
            return payload
        raise CodexCLIError("Codex CLI did not return valid JSON for research")


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

    repaired = None
    try:
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
    except ClaudeCLIError as exc:
        raise StructuredLLMResponseError(
            str(exc),
            prompt=prompt,
            raw_output=result,
            repaired_output=repaired,
            provider=provider,
            model=model,
        ) from exc
    if not isinstance(payload, dict):
        raise StructuredLLMResponseError(
            "LLM backend did not return valid JSON",
            prompt=prompt,
            raw_output=result,
            repaired_output=repaired,
            provider=provider,
            model=model,
        )
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
    if provider == "codex":
        return _run_codex(
            prompt=prompt,
            model=model,
            output_format=output_format,
            json_schema=json_schema,
            timeout=timeout,
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

    payload = _post_lmstudio_request(
        url=url,
        body=body,
        api_key=api_key,
        timeout=timeout,
    )
    choice = _extract_lmstudio_choice(payload)

    if output_format == "json" and json_schema is not None and not choice.strip():
        fallback_prompt = (
            "Return exactly one JSON object that matches the schema below.\n"
            "Do not use markdown, prose, or code fences.\n\n"
            f"Schema:\n{json.dumps(json_schema, indent=2, ensure_ascii=False)}\n\n"
            f"Task:\n{prompt}"
        )
        fallback_body: dict[str, Any] = {
            "model": model,
            "messages": _build_lmstudio_messages(
                system_prompt=system_prompt,
                prompt=fallback_prompt,
                model=model,
            ),
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }
        payload = _post_lmstudio_request(
            url=url,
            body=fallback_body,
            api_key=api_key,
            timeout=timeout,
        )
        choice = _extract_lmstudio_choice(payload)

    if not choice.strip():
        raise ClaudeCLIError("LM Studio returned empty output")

    return choice.strip()


def _run_codex(
    *,
    prompt: str,
    model: str,
    output_format: str,
    json_schema: Optional[dict[str, Any]] = None,
    timeout: int = 600,
) -> str:
    cmd = ["codex", "exec", "--full-auto"]
    if model:
        cmd.extend(["--model", model])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_path = tmp_path / "output.txt"
        cmd.extend(["--output-last-message", str(output_path)])
        if output_format == "json" and json_schema is not None:
            schema_path = tmp_path / "schema.json"
            schema_path.write_text(json.dumps(json_schema, indent=2, ensure_ascii=False) + "\n")
            cmd.extend(["--output-schema", str(schema_path)])
        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as e:
            raise CodexCLIError("Codex CLI not found on PATH.") from e
        except subprocess.TimeoutExpired as e:
            raise CodexCLIError("Codex CLI timed out") from e

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise CodexCLIError(stderr[-2000:] or "Codex CLI failed without output")

        if output_path.exists():
            output = output_path.read_text().strip()
            if output:
                return output

        output = (result.stdout or "").strip()
        if output:
            return output
        raise CodexCLIError("Codex CLI returned empty output")


def _post_lmstudio_request(*, url: str, body: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
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
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        raise ClaudeCLIError(
            f"LM Studio API returned HTTP {e.code} at {url}: {details[-2000:] or e.reason}"
        ) from e
    except urllib.error.URLError as e:
        raise ClaudeCLIError(
            f"Cannot reach LM Studio API at {url}. Start LM Studio's local server on port 1234."
        ) from e


def _extract_lmstudio_choice(payload: dict[str, Any]) -> str:
    try:
        message = payload["choices"][0].get("message", {})
    except (KeyError, IndexError, TypeError) as e:
        raise ClaudeCLIError("LM Studio returned an unexpected response shape") from e

    choice: Any = message.get("content")
    if not choice:
        choice = payload.get("choices", [{}])[0].get("text", "")

    if isinstance(choice, list):
        choice = "".join(
            part.get("text", "")
            for part in choice
            if isinstance(part, dict)
        )

    if not isinstance(choice, str):
        choice = str(choice)
    return choice


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
