"""
stages/renderers/hyperframes.py - Renderer: HyperFrames HTML/GSAP composition

Opt-in sibling of the Manim renderer (select it with ``"renderer": "hyperframes"``
on a scene, or ``primary_renderer``). The mechanics are the same: a model writes
the scene, a checker gates it with structured feedback, failed attempts retry on
the same provider ladder, and when none pass the least-defective attempt ships.

What differs is the artifact and the gate.

* The model writes a FRAGMENT: one ``<style>`` block, the elements that live
  inside ``#scene``, and one ``<script>`` of tween statements on a timeline
  called ``tl``. This module owns the structure (root, clip, timeline creation
  and registration, local GSAP) so a model cannot break the contract.
* The gate is ``hyperframes check`` (lint, runtime errors, layout, motion,
  contrast, sampled across the timeline) plus a generated ``index.motion.json``
  sidecar: ``keepsMoving`` over the whole scene and one ``staysInFrame`` per
  element id that carries text. Any finding with severity "error", or
  ``sweep_static``, fails the attempt. Warnings are recorded, never gating.
* The shipped clip is rendered by ``hyperframes render`` and verified with
  ffprobe (size, frame rate, duration).

Setup (once):  cd video-pipeline/hyperframes && npm ci

Beside ``scene_NNN.mp4`` this writes ``scene_NNN.html`` (the full composition;
it loads ``gsap.min.js`` from its own folder, so copy that file next to it to
re-render by hand) and ``scene_NNN.motion.json``. A clip that shipped with
check findings also gets ``scene_NNN.defects.json``. Rejected attempts are kept
under ``_rejected/``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from config import PipelineConfig
from stages.renderers.manim import (
    ManimRenderError,
    _call_claude_cli,
    _call_lmstudio_api,
    _defects_path,
    _extract_bg_color,
    _pick_best_attempt,
    _write_defects,
)

HYPERFRAMES_DIR = Path(__file__).resolve().parents[2] / "hyperframes"
CLI_PATH = HYPERFRAMES_DIR / "node_modules" / ".bin" / "hyperframes"
GSAP_PATH = HYPERFRAMES_DIR / "node_modules" / "gsap" / "dist" / "gsap.min.js"

# The retry prompt carries `error[-2000:]`, so the feedback must fit in that
# window or the first (worst) findings are the ones cut off.
MAX_FEEDBACK_FINDINGS = 8
MAX_FEEDBACK_CHARS = 1900
MAX_FINDING_CHARS = 230
MAX_PREVIOUS_FRAGMENT_CHARS = 9000


class HyperframesError(ManimRenderError):
    """A scene attempt failed in a way the next attempt can fix."""


class HyperframesCheckError(HyperframesError):
    """The composition loaded but `hyperframes check` gated it."""

    def __init__(self, message: str, findings: list[dict]):
        super().__init__(message)
        self.findings = findings


class HyperframesToolError(HyperframesError):
    """The toolchain itself failed (CLI missing, check could not run, render
    timed out, output does not match the config). Retrying the model cannot
    help, so this is never retried."""


# ── Paths / environment ──────────────────────────────────────────


def _cli_path() -> Path:
    if not CLI_PATH.exists():
        raise HyperframesToolError(
            f"HyperFrames CLI not found at {CLI_PATH}. "
            f"Run `npm ci` in {HYPERFRAMES_DIR} first."
        )
    if not GSAP_PATH.exists():
        raise HyperframesToolError(
            f"GSAP not found at {GSAP_PATH}. Run `npm ci` in {HYPERFRAMES_DIR}."
        )
    return CLI_PATH


def _tool_env() -> dict:
    return {
        **os.environ,
        "HYPERFRAMES_SKIP_SKILLS": "1",
        "HYPERFRAMES_NO_UPDATE_CHECK": "1",
        "NO_COLOR": "1",
    }


def _rejected_stem(out_path: Path, attempt: int) -> str:
    return f"{out_path.stem}_attempt{attempt}"


def _html_path(out_path: Path) -> Path:
    return out_path.with_suffix(".html")


def _motion_path(out_path: Path) -> Path:
    return out_path.with_name(out_path.stem + ".motion.json")


def check_timeout(duration_sec: float) -> int:
    return int(120 + 6 * max(float(duration_sec or 0), 1.0))


def render_timeout(duration_sec: float) -> int:
    return int(180 + 8 * max(float(duration_sec or 0), 1.0))


def _fmt_seconds(value: float) -> str:
    value = float(value)
    return str(int(value)) if value == int(value) else f"{value:g}"


# ── Entry point ──────────────────────────────────────────────────


def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    """Render a hyperframes scene to out_path. Returns out_path on success."""
    log = logging.getLogger("hyperframes")
    cli = _cli_path()

    duration_sec = scene.get("duration_sec", 8)
    bg_color = _extract_bg_color(scene.get("style", ""))
    system = _build_system_prompt(
        width=config.render_width,
        height=config.render_height,
        fps=config.render_fps,
        duration_sec=duration_sec,
        bg_color=bg_color,
    )
    base_message = _build_user_message(scene, duration_sec)

    if config.renderer_max_retries < 1:
        raise HyperframesError("renderer_max_retries must be >= 1")

    last_error: Optional[str] = None
    last_fragment = ""
    # Attempts that were checked and gated. If none passes, the least-defective
    # one that is still a real animation is rendered and shipped.
    candidates: list[dict] = []
    for attempt in range(config.renderer_max_retries):
        log.info(
            f"Render attempt {attempt + 1}/{config.renderer_max_retries} for {out_path.name}"
        )
        sys.stderr.flush()
        sys.stdout.flush()

        # Same ladder as Manim: cheapest rung first, the last attempt escalates.
        ladder = config.render_provider_sequence()
        rung = 0 if attempt < config.renderer_max_retries - 1 else len(ladder) - 1
        provider = ladder[rung]
        model = config.render_llm_model_name_for(provider)
        log.info(f"Codegen backend for attempt {attempt + 1}: {provider}:{model}")

        message = base_message
        if last_error and last_fragment:
            message += (
                "\n\nYour previous fragment (fix it, keep what already works):\n"
                + last_fragment[:MAX_PREVIOUS_FRAGMENT_CHARS]
            )

        try:
            if provider == "lmstudio":
                raw = _call_lmstudio_api(
                    model=model,
                    system=system,
                    description=message,
                    error=last_error,
                    base_url=config.lmstudio_base_url,
                    api_key=config.lmstudio_api_key,
                    extract=extract_html,
                )
            else:
                raw = _call_claude_cli(
                    model, system, message, last_error, extract=extract_html
                )
            log.info(f"Generated fragment ({len(raw)} chars) for {out_path.name}")

            parts = sanitize_fragment(raw)
            last_fragment = parts.as_fragment()
            document = build_document(
                parts,
                width=config.render_width,
                height=config.render_height,
                fps=config.render_fps,
                duration_sec=duration_sec,
                bg_color=bg_color,
            )
            sidecar = build_motion_sidecar(parts.markup, duration_sec)
            local = fragment_findings(parts)
            # Nothing to look at or nothing moving: no point booting Chrome.
            fatal = [f for f in local if f["code"] in {"empty_scene", "no_tweens"}]
            if fatal:
                raise HyperframesCheckError(build_feedback(fatal), fatal)

            with tempfile.TemporaryDirectory(prefix="hyperframes_render_") as tmp:
                project = Path(tmp)
                _write_project(project, document, sidecar)
                report = run_check(cli, project, duration_sec)
                findings = local + collect_findings(report)
                gating = sorted(
                    (f for f in findings if is_gating(f)),
                    key=lambda f: -finding_weight(f),
                )
                warnings = [f for f in findings if not is_gating(f)]
                log.info(
                    f"hyperframes check for {out_path.name}: {len(gating)} gating, "
                    f"{len(warnings)} non-gating findings"
                )
                if gating:
                    problems = [describe_finding(f) for f in gating]
                    candidates.append(
                        _keep_rejected(
                            out_path,
                            attempt + 1,
                            document,
                            sidecar,
                            report,
                            gating,
                            problems,
                            shippable=_is_shippable(report, gating),
                        )
                    )
                    raise HyperframesCheckError(build_feedback(gating), gating)
                _render_and_verify(cli, project, out_path, config, duration_sec)
            _publish_sources(out_path, document, sidecar)
            _defects_path(out_path).unlink(missing_ok=True)
            return out_path
        except HyperframesToolError:
            raise
        except ManimRenderError as e:
            last_error = str(e)
            log.error(f"Render failed attempt {attempt + 1}: {last_error[:300]}")
            if attempt == config.renderer_max_retries - 1:
                log.error(
                    f"Final render failure after {config.renderer_max_retries} attempts:\n"
                    f"{last_error[:1000]}"
                )
                shippable = [c for c in candidates if c["shippable"]]
                if shippable:
                    return _ship_best_attempt(
                        cli, shippable, len(candidates), out_path, config, duration_sec
                    )
                raise

    raise HyperframesError(  # unreachable, but satisfies type checkers
        f"HyperFrames failed after {config.renderer_max_retries} attempts"
    )


# ── Fragment extraction and sanitising ───────────────────────────


def extract_html(output: str) -> str:
    """Pull the fragment out of a model reply: the fenced block if there is
    one, otherwise everything from the first tag."""
    text = output.strip()
    fence = re.search(r"```[a-zA-Z]*[ \t]*\n?(.*?)```", text, flags=re.S)
    if fence:
        return fence.group(1).strip()
    text = re.sub(r"^```[a-zA-Z]*[ \t]*\n?", "", text)  # truncated, unclosed fence
    first_tag = text.find("<")
    return text[first_tag:].strip() if first_tag > 0 else text


class FragmentParts:
    """The three pieces of a sanitised fragment."""

    def __init__(
        self,
        css: str,
        markup: str,
        script: str,
        notes: list[str],
        aliases: Optional[list[str]] = None,
    ):
        self.css = css
        self.markup = markup
        self.script = script
        self.notes = notes
        # Names the model gave its own timeline; each is rebound to `tl`.
        self.aliases = aliases or []

    def as_fragment(self) -> str:
        blocks = []
        if self.css.strip():
            blocks.append(f"<style>\n{self.css.strip()}\n</style>")
        blocks.append(self.markup.strip())
        if self.script.strip():
            blocks.append(f"<script>\n{self.script.strip()}\n</script>")
        return "\n".join(blocks)


_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)(?:</style\s*>|\Z)", re.S | re.I)
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)(?:</script\s*>|\Z)", re.S | re.I)
_DROP_TAG_RE = re.compile(
    r"<(?:link|meta|base)\b[^>]*>|<title\b[^>]*>.*?</title\s*>"
    r"|<(iframe|object|embed)\b[^>]*>.*?</\1\s*>|<(?:iframe|object|embed)\b[^>]*/?>",
    re.S | re.I,
)
_WRAPPER_RE = re.compile(r"<!doctype[^>]*>|</?(?:html|head|body)\b[^>]*>", re.S | re.I)
_EXTERNAL_ATTR_RE = re.compile(
    r"""\s+(?:src|href|xlink:href|poster|data)\s*=\s*(?:"\s*(?:https?:)?//[^"]*"|'\s*(?:https?:)?//[^']*')""",
    re.I,
)
_CSS_IMPORT_RE = re.compile(r"@import\b[^;]*;?", re.I)
_EXTERNAL_URL_RE = re.compile(r"""url\(\s*['"]?\s*(?:https?:)?//[^)]*\)""", re.I)
_JS_TYPES = {"", "text/javascript", "application/javascript", "module"}


def _script_attr(attrs: str, name: str) -> Optional[str]:
    m = re.search(rf"""\b{name}\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+))""", attrs, re.I)
    if not m:
        return None
    return next(g for g in m.groups() if g is not None)


def _matching_paren(text: str, open_idx: int) -> int:
    """Index of the ')' that closes the '(' at open_idx, or -1."""
    depth = 0
    quote = ""
    i = open_idx
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = ""
        elif ch in "\"'`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


_TIMELINE_CALL_RE = re.compile(
    r"(?:\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*)?\bgsap\s*\.\s*timeline\s*\("
)
_REGISTRY_RE = re.compile(
    r"(?:window\s*\.\s*)?__timelines\b(?:\s*\[[^\]]*\]|\s*\.\s*\w+)?\s*=[^;\n]*;?"
)
_TL_CONTROL = (
    r"\s*\.\s*(?:play|resume|restart|reverse|pause|seek|progress|time)\s*\([^)]*\)\s*;?"
)


def _strip_timeline_setup(script: str, notes: list[str], aliases: list[str]) -> str:
    """The host creates `tl`, registers it and seeks it. Anything the model
    wrote for that is removed (or aliased to `tl`) so there is exactly one
    timeline and it stays paused."""
    out = []
    pos = 0
    while True:
        m = _TIMELINE_CALL_RE.search(script, pos)
        if not m:
            out.append(script[pos:])
            break
        close = _matching_paren(script, m.end() - 1)
        if close == -1:
            out.append(script[pos:])
            break
        out.append(script[pos : m.start()])
        end = close + 1
        rest = script[end:]
        name = m.group(1)
        if rest.lstrip().startswith("."):
            out.append("tl")  # gsap.timeline({...}).to(...) chain
        elif name and name != "tl":
            out.append(f"const {name} = tl;")
            aliases.append(name)
            if script[end : end + 1] == ";":
                end += 1
        elif script[end : end + 1] == ";":
            end += 1
        notes.append("replaced model-created timeline with the host timeline")
        pos = end
    script = "".join(out)
    script, n_reg = _REGISTRY_RE.subn("", script)
    names = "|".join(re.escape(n) for n in ["tl", *aliases])
    script, n_ctl = re.subn(rf"\b(?:{names}){_TL_CONTROL}", "", script)
    if n_reg:
        notes.append("removed __timelines registration")
    if n_ctl:
        notes.append("removed timeline playback control")
    return script


def sanitize_fragment(raw: str) -> FragmentParts:
    """Split a model fragment into css / markup / script and strip everything
    the host owns or the sandbox must not load."""
    notes: list[str] = []
    text = _COMMENT_RE.sub("", raw)

    styles = []

    def take_style(m: re.Match) -> str:
        styles.append(m.group(1))
        return ""

    text = _STYLE_RE.sub(take_style, text)

    scripts = []

    def take_script(m: re.Match) -> str:
        attrs, body = m.group(1), m.group(2)
        if _script_attr(attrs, "src") is not None:
            notes.append("dropped <script src>")
        elif (_script_attr(attrs, "type") or "").strip().lower() not in _JS_TYPES:
            notes.append("dropped non-JavaScript <script>")
        else:
            scripts.append(body)
        return ""

    text = _SCRIPT_RE.sub(take_script, text)

    text, n = _DROP_TAG_RE.subn("", text)
    if n:
        notes.append("dropped link/meta/iframe tags")
    text = _WRAPPER_RE.sub("", text)
    text, n = _EXTERNAL_ATTR_RE.subn("", text)
    if n:
        notes.append("dropped external src/href attributes")
    text, n = _EXTERNAL_URL_RE.subn("none", text)
    if n:
        notes.append("dropped external url()")

    css = "\n".join(styles)
    css = _CSS_IMPORT_RE.sub("", css)
    css, n = _EXTERNAL_URL_RE.subn("none", css)
    if n:
        notes.append("dropped external url() in css")
    css = css.replace("</style", "<\\/style")

    script = "\n".join(scripts)
    aliases: list[str] = []
    script = _strip_timeline_setup(script, notes, aliases)
    script = script.replace("</script", "<\\/script")
    return FragmentParts(css.strip(), text.strip(), script.strip(), notes, aliases)


# ── Local findings (cheap, before the browser runs) ──────────────

_JS_COMMENT_RE = re.compile(r"/\*.*?\*/|(?<![:\"'])//[^\n]*", re.S)
_NONDETERMINISTIC = (
    (r"\bMath\s*\.\s*random\b", "Math.random"),
    (
        r"\bDate\s*\.\s*now\b|\bnew\s+Date\b|\bperformance\s*\.\s*now\b",
        "Date/performance clock",
    ),
    (r"\bsetTimeout\b|\bsetInterval\b", "setTimeout/setInterval"),
    (r"\brequestAnimationFrame\b", "requestAnimationFrame"),
    (r"\brepeat\s*:\s*-1\b", "repeat: -1 (infinite repeat)"),
)


class _IdCollector(HTMLParser):
    """Walks the fragment markup collecting each element id and whether the
    element holds visible text (own or descendant, SVG <text> included)."""

    VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr", "path", "circle", "rect", "line",
        "ellipse", "polygon", "polyline", "stop", "use",
    }  # fmt: skip

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.elements: list[dict] = []

    def handle_starttag(self, tag, attrs):
        el = {"tag": tag, "id": dict(attrs).get("id"), "text": False}
        self.elements.append(el)
        if tag not in self.VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        self.elements.append({"tag": tag, "id": dict(attrs).get("id"), "text": False})

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            for el in self.stack:
                el["text"] = True


def _collect_elements(markup: str) -> list[dict]:
    parser = _IdCollector()
    try:
        parser.feed(markup)
        parser.close()
    except Exception:  # noqa: BLE001 - malformed model HTML must not crash the stage
        pass
    return parser.elements


def fragment_findings(parts: FragmentParts) -> list[dict]:
    """Defects visible without a browser: ids that collide, a wrapper the host
    already owns, scene with nothing in it, nothing animated, and APIs that make
    a frame depend on wall-clock time."""
    findings: list[dict] = []

    def add(code: str, message: str, fix: str, selector: str = "") -> None:
        findings.append(
            {
                "code": code,
                "severity": "error",
                "section": "fragment",
                "selector": selector,
                "message": message,
                "fixHint": fix,
            }
        )

    elements = _collect_elements(parts.markup)
    if not elements:
        add(
            "empty_scene",
            "The fragment has no elements.",
            "Put the visible elements inside the fragment (the host supplies #scene).",
        )
    seen: dict[str, int] = {}
    for el in elements:
        if el["id"]:
            seen[el["id"]] = seen.get(el["id"], 0) + 1
    for ident, count in seen.items():
        if ident in {"scene", "root"}:
            add(
                "reserved_id",
                f"id '{ident}' belongs to the host wrapper.",
                "Remove your own #scene/#root element; write only its children.",
                f"#{ident}",
            )
        elif count > 1:
            add(
                "duplicate_id",
                f"id '{ident}' is used by {count} elements.",
                "Give every element a unique id.",
                f"#{ident}",
            )
    names = "|".join(re.escape(n) for n in ["tl", *parts.aliases])
    if not re.search(
        rf"\b(?:{names})\s*\.\s*(?:to|from|fromTo|set|call|add)\s*\(", parts.script
    ):
        add(
            "no_tweens",
            "The script has no tween statements on tl.",
            "Animate with tl.fromTo/tl.to/tl.set at explicit positions.",
        )
    code = _JS_COMMENT_RE.sub("", parts.script)
    for pattern, label in _NONDETERMINISTIC:
        if re.search(pattern, code):
            add(
                "nondeterministic_script",
                f"The script uses {label}; frames are rendered by seeking, so output must depend only on tl time.",
                "Remove it; drive everything with tweens on tl at explicit positions.",
            )
    return findings


# ── Document and sidecar construction ────────────────────────────


def _resolution_attr(width: int, height: int) -> str:
    preset = {
        (1920, 1080): "landscape",
        (1080, 1920): "portrait",
        (1080, 1080): "square",
    }
    name = preset.get((width, height))
    return f' data-resolution="{name}"' if name else ""


def build_document(
    parts: FragmentParts,
    *,
    width: int,
    height: int,
    fps: int,
    duration_sec: float,
    bg_color: str,
) -> str:
    """The full index.html. The wrapper owns structure; the fragment fills
    #scene. Everything here is fixed by config, never by the model."""
    d = _fmt_seconds(duration_sec)
    return f"""<!doctype html>
<html lang="en"{_resolution_attr(width, height)}>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={width}, height={height}" />
<script src="gsap.min.js"></script>
<style>
html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{bg_color}}}
#root{{position:relative;width:{width}px;height:{height}px;overflow:hidden}}
#scene{{position:absolute;left:0;top:0;width:{width}px;height:{height}px;overflow:hidden;background:{bg_color};color:#FFFFFF;font-family:"Inter",system-ui,sans-serif}}
</style>
<style>
{parts.css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{d}" data-width="{width}" data-height="{height}" data-fps="{fps}">
<div id="scene" class="clip" data-start="0" data-duration="{d}" data-track-index="0">
{parts.markup}
</div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{{
{parts.script}
}}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""


_SAFE_ID_RE = re.compile(r"^[A-Za-z_][\w-]*$")


def text_element_ids(markup: str) -> list[str]:
    """Ids that are unique in the fragment, safe as a CSS selector, belong to
    the model (not #scene/#root) and hold visible text."""
    elements = _collect_elements(markup)
    counts: dict[str, int] = {}
    for el in elements:
        if el["id"]:
            counts[el["id"]] = counts.get(el["id"], 0) + 1
    ids: list[str] = []
    for el in elements:
        ident = el["id"]
        if (
            ident
            and counts[ident] == 1
            and ident not in {"scene", "root"}
            and el["text"]
            and _SAFE_ID_RE.match(ident)
        ):
            ids.append(ident)
    return ids


def build_motion_sidecar(markup: str, duration_sec: float) -> dict:
    """Assertions `hyperframes check` verifies against the seeked timeline.
    One staysInFrame per text id: a selector matching two elements is
    `motion_selector_ambiguous`, one matching none is `motion_selector_missing`,
    so only ids proven unique and present are asserted."""
    assertions: list[dict] = [
        {"kind": "keepsMoving", "withinSelector": "#scene", "maxStaticSec": 2}
    ]
    for ident in text_element_ids(markup):
        assertions.append({"kind": "staysInFrame", "selector": f"#{ident}"})
    return {"duration": float(duration_sec), "assertions": assertions}


def _write_project(project: Path, document: str, sidecar: dict) -> None:
    (project / "index.html").write_text(document, encoding="utf-8")
    shutil.copy2(GSAP_PATH, project / "gsap.min.js")
    (project / "index.motion.json").write_text(
        json.dumps(sidecar, indent=1), encoding="utf-8"
    )


# ── hyperframes check ────────────────────────────────────────────


def run_check(cli: Path, project: Path, duration_sec: float) -> dict:
    """Run `hyperframes check` and return its parsed JSON report.

    A non-zero exit is normal when the composition has issues; what is NOT
    normal is output that is not a report, or a browser that never ran for a
    reason other than lint errors. Those raise HyperframesToolError."""
    cmd = [
        str(cli),
        "check",
        "--json",
        "--strict",
        "--frame-check",
        "--at-transitions",
    ]
    timeout = check_timeout(duration_sec)
    try:
        result = subprocess.run(
            cmd,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_tool_env(),
        )
    except subprocess.TimeoutExpired as e:
        raise HyperframesToolError(
            f"hyperframes check timed out after {timeout}s"
        ) from e
    except OSError as e:
        raise HyperframesToolError(f"could not run hyperframes check: {e}") from e
    return parse_check_output(result.stdout, result.stderr, result.returncode)


def parse_check_output(stdout: str, stderr: str = "", returncode: int = 0) -> dict:
    report = None
    text = (stdout or "").strip()
    try:
        report = json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                report = json.loads(text[start : end + 1])
            except ValueError:
                report = None
    if not isinstance(report, dict) or "lint" not in report:
        tail = (stderr or stdout or "").strip()[-600:]
        raise HyperframesToolError(
            f"hyperframes check produced no report (exit {returncode}): "
            f"{tail or 'no output'}"
        )
    if report.get("browserSkipped") and not any(
        is_gating(f) for f in collect_findings(report)
    ):
        raise HyperframesToolError(
            "hyperframes check could not start its browser (no lint errors "
            "explain it). Run `hyperframes doctor` in video-pipeline/hyperframes."
        )
    return report


def collect_findings(report: dict) -> list[dict]:
    """Flatten every report section's findings, tagging each with its section.
    The same defect is reported once per sample time (a contrast failure came
    back four times), so identical findings are collapsed."""
    findings: list[dict] = []
    seen: set[tuple] = set()
    for section, body in report.items():
        if not isinstance(body, dict) or not isinstance(body.get("findings"), list):
            continue
        for f in body["findings"]:
            if not isinstance(f, dict):
                continue
            key = (section, f.get("code"), f.get("selector"), f.get("message"))
            if key in seen:
                continue
            seen.add(key)
            findings.append({**f, "section": section})
    return findings


def is_gating(finding: dict) -> bool:
    """Errors gate. Warnings are recorded. Info is a transient at one sample.
    `sweep_static` (a frozen timeline) gates at any severity, since it makes
    every other verdict unreliable."""
    return finding.get("severity") == "error" or finding.get("code") == "sweep_static"


def describe_finding(finding: dict) -> str:
    code = finding.get("code", "finding")
    selector = finding.get("selector") or ""
    head = f"{code} {selector}".strip()
    text = f"{head}: {finding.get('message', '')}".strip()
    hint = finding.get("fixHint")
    if hint:
        text += f" (fix: {hint})"
    return text


def build_feedback(gating: list[dict]) -> str:
    """The retry message: the first MAX_FEEDBACK_FINDINGS gating findings as
    `code selector: message (fix: ...)`, each clipped, the whole kept under the
    window the codegen helpers forward."""
    lines = []
    for f in gating[:MAX_FEEDBACK_FINDINGS]:
        line = describe_finding(f)
        if len(line) > MAX_FINDING_CHARS:
            line = line[: MAX_FINDING_CHARS - 3] + "..."
        lines.append(line)
    extra = len(gating) - len(lines)
    if extra > 0:
        lines.append(f"... and {extra} more finding(s)")
    text = "hyperframes check rejected the composition:\n" + "\n".join(
        f"- {line}" for line in lines
    )
    return text[:MAX_FEEDBACK_CHARS]


# How much each kind of defect hurts a viewer. A runtime exception can leave the
# scene blank; text off the frame or overlapping cannot be read; a frozen window
# or low contrast is poor but the scene still plays.
_FINDING_WEIGHTS = (
    ("overflow", 3),
    ("overlap", 3),
    ("occlu", 3),
    ("off_frame", 3),
    ("out_of_canvas", 3),
    ("clipped", 3),
    ("frozen", 3),
    ("contrast", 2),
)


def finding_weight(finding: dict) -> int:
    if finding.get("section") == "runtime":
        return 5
    code = str(finding.get("code", ""))
    return next((w for key, w in _FINDING_WEIGHTS if key in code), 2)


def defect_score(findings: list[dict]) -> int:
    return sum(finding_weight(f) for f in findings)


def _is_shippable(report: dict, gating: list[dict]) -> bool:
    """A gated attempt may ship only if it is verified, playable, and moving:
    the browser ran (so layout was actually measured), nothing threw at
    runtime, and the whole timeline is not frozen. Otherwise slides are the
    honest fallback and the stage records the scene as degraded."""
    if report.get("browserSkipped"):
        return False
    return not any(
        f.get("section") == "runtime" or f.get("code") == "sweep_static" for f in gating
    )


# ── Rejected attempts, rendering, shipping ───────────────────────


def _keep_rejected(
    out_path: Path,
    attempt: int,
    document: str,
    sidecar: dict,
    report: dict,
    gating: list[dict],
    problems: list[str],
    *,
    shippable: bool,
) -> dict:
    rejected = out_path.parent / "_rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    stem = _rejected_stem(out_path, attempt)
    html_file = rejected / f"{stem}.html"
    motion_file = rejected / f"{stem}.motion.json"
    html_file.write_text(document, encoding="utf-8")
    motion_file.write_text(json.dumps(sidecar, indent=1), encoding="utf-8")
    (rejected / f"{stem}.check.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8"
    )
    return {
        "attempt": attempt,
        "html": html_file,
        "motion": motion_file,
        "document": document,
        "sidecar": sidecar,
        "problems": problems,
        "score": defect_score(gating),
        "shippable": shippable,
    }


def _ship_best_attempt(
    cli: Path,
    candidates: list[dict],
    total_attempts: int,
    out_path: Path,
    config: PipelineConfig,
    duration_sec: float,
) -> Path:
    """No attempt passed the gate. The least-defective one that is still a
    verified animation is rendered from its saved html and shipped with its
    findings written beside the clip."""
    log = logging.getLogger("hyperframes")
    best = _pick_best_attempt(candidates)
    with tempfile.TemporaryDirectory(prefix="hyperframes_render_") as tmp:
        project = Path(tmp)
        _write_project(project, best["document"], best["sidecar"])
        _render_and_verify(cli, project, out_path, config, duration_sec)
    _publish_sources(out_path, best["document"], best["sidecar"])
    _write_defects(best, out_path)
    log.warning(
        f"SHIPPED WITH CHECK FINDINGS: {out_path.name} is attempt {best['attempt']} of "
        f"{total_attempts} (defect score {best['score']}): "
        + "; ".join(best["problems"][:3])
    )
    return out_path


def _publish_sources(out_path: Path, document: str, sidecar: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _html_path(out_path).write_text(document, encoding="utf-8")
    _motion_path(out_path).write_text(json.dumps(sidecar, indent=1), encoding="utf-8")


def _render_and_verify(
    cli: Path,
    project: Path,
    out_path: Path,
    config: PipelineConfig,
    duration_sec: float,
) -> None:
    rendered = project / "out.mp4"
    timeout = render_timeout(duration_sec)
    cmd = [
        str(cli),
        "render",
        "-o",
        str(rendered),
        "--fps",
        str(config.render_fps),
        "--quality",
        "delivery",
        "--quiet",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_tool_env(),
        )
    except subprocess.TimeoutExpired as e:
        raise HyperframesToolError(
            f"hyperframes render timed out after {timeout}s"
        ) from e
    except OSError as e:
        raise HyperframesToolError(f"could not run hyperframes render: {e}") from e
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip()[-1500:]
        raise HyperframesError(
            f"hyperframes render failed (exit {result.returncode}): {tail}"
        )
    if not rendered.exists():
        raise HyperframesError("hyperframes render exited 0 but wrote no video")
    verify_video(rendered, config, duration_sec)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rendered, out_path)


def probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate:format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, check=True
        )
        return json.loads(result.stdout)
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
    ) as e:
        raise HyperframesToolError(f"ffprobe could not read {path.name}: {e}") from e


def verify_video(path: Path, config: PipelineConfig, duration_sec: float) -> None:
    """The rendered file must be what the config asked for."""
    info = probe_video(path)
    streams = info.get("streams") or []
    if not streams:
        raise HyperframesToolError(f"{path.name} has no video stream")
    stream = streams[0]
    problems = []
    if (stream.get("width"), stream.get("height")) != (
        config.render_width,
        config.render_height,
    ):
        problems.append(
            f"size {stream.get('width')}x{stream.get('height')}, "
            f"expected {config.render_width}x{config.render_height}"
        )
    try:
        fps = Fraction(str(stream.get("r_frame_rate", "0/1")))
    except (ValueError, ZeroDivisionError):
        fps = Fraction(0)
    if fps != config.render_fps:
        problems.append(
            f"frame rate {stream.get('r_frame_rate')}, expected {config.render_fps}"
        )
    try:
        duration = float((info.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        duration = 0.0
    if abs(duration - float(duration_sec)) > 0.5:
        problems.append(f"duration {duration:.2f}s, expected {float(duration_sec):g}s")
    if problems:
        raise HyperframesToolError(
            "rendered video does not match the config: " + "; ".join(problems)
        )


# ── Prompts ──────────────────────────────────────────────────────


def _build_user_message(scene: dict, duration_sec: float) -> str:
    parts = [f"Scene (exactly {_fmt_seconds(duration_sec)} seconds):"]
    title = str(scene.get("title") or "").strip()
    if title:
        parts.append(f"Title: {title}")
    parts.append(f"Description: {str(scene.get('description') or '').strip()}")
    style = str(scene.get("style") or "").strip()
    if style:
        parts.append(f"Visual style: {style}")
    hint = str(scene.get("layout_hint") or "").strip()
    if hint:
        parts.append(f"Layout hint: {hint}")
    narration = str(scene.get("narration") or "").strip()
    if narration:
        parts.append(
            "Narration (spoken over this scene; use it to time the reveals, "
            "do not print it on screen):\n" + narration
        )
    return "\n".join(parts)


def _build_system_prompt(
    *, width: int, height: int, fps: int, duration_sec: float, bg_color: str
) -> str:
    d = _fmt_seconds(duration_sec)
    margin = 96
    inner_w = width - 2 * margin
    inner_h = height - 2 * margin
    right = width - margin
    bottom = height - margin
    chart_w = inner_w - 560
    chart_h = inner_h - 320
    dur = float(duration_sec)
    draw_dur = max(round(dur - 3, 1), 1)
    count_at = round(dur * 0.4, 1)
    count_dur = max(round(dur * 0.6 - 0.5, 1), 1)
    cap_at = round(dur * 0.3, 1)
    return f"""You are a motion designer writing ONE scene of a finance explainer video as a HyperFrames composition: HTML + CSS + GSAP, rendered frame by frame in headless Chrome by seeking a paused GSAP timeline.

OUTPUT FORMAT (strict)
Return ONLY a fragment, no markdown fences, no commentary, made of exactly three parts in this order:
1. One <style> block. Start every selector with #scene (for example "#scene .card").
2. The elements that go INSIDE the scene. Do not write the scene container yourself.
3. One <script> block containing only tween statements on the existing timeline `tl`.
The host already provides <html>, <head>, <body>, #root, the #scene container (position:absolute, {width}x{height}, background {bg_color}, overflow hidden, color #FFFFFF, font Inter), GSAP, and `const tl = gsap.timeline({{ paused: true }})`, and it registers and seeks `tl` for you. NEVER write <html>/<head>/<body>, an element with id "scene" or "root", <link>, <script src>, @import, web fonts, images, or any http(s) URL. NEVER write gsap.timeline, window.__timelines, tl.seek, tl.play or tl.pause. Draw everything with HTML, CSS and inline SVG; there are no external assets.

CANVAS
- {width}x{height} px at {fps} fps, duration EXACTLY {d} seconds. Timeline positions run from 0 to {d}.
- Use position:absolute with pixel left/top/width/height for every element inside #scene. Do not rely on flex/grid for the page layout, and never put a CSS transform on an element that GSAP also animates (GSAP overwrites it); centre with left/top, or use xPercent/yPercent in the tween.
- Safe area: keep every element's box at least {margin}px from every edge, at every moment: x from {margin} to {right}, y from {margin} to {bottom} (a {inner_w}x{inner_h} area). Nothing may start off-canvas and slide in, or slide out; entrances are fades with a small move (up to 40px), starting from opacity 0.

TYPOGRAPHY AND IDS
- Minimum font-size 28px for ANY text, including chart labels and axis ticks. Titles 56-72px bold, key numbers 72-120px, labels 32-40px. Use only font-weights 400, 600, 700 or 800.
- EVERY element that contains text gets a UNIQUE id (id="t-title", "lbl-strike", "val-profit"). Never reuse an id, and never use the ids "scene" or "root". Tween by #id; a class selector is fine only for staggering a group of non-text shapes.
- Give each text box a generous explicit width and height, white-space:nowrap for one-line labels, and line-height 1.2 so the text never overflows its box. Budget about 0.6 x font-size px of width per character. Leave at least 24px between separate text blocks; two text blocks must never overlap each other at any time.
- Draw panels, bars and shapes BEFORE the text that sits on them in the markup so nothing covers text.
- Text colour must meet WCAG AA contrast (4.5:1) against what is behind it. On the dark background use #FFFFFF, #E6EDF3 or a bright accent (#FFD700 gold, #00C896 green, #FF6B6B red, #4DA3FF blue), never mid-grey. If the visual style names colours, use those.

MOTION (a checker enforces this)
- The picture must visibly change in EVERY 2-second window from 0 to {d} seconds, including the last seconds. Do not reveal everything in the first 3 seconds and then hold still. Spread the reveal over the whole duration, timed to the narration: stagger cards and labels, draw lines and curves on progressively, slide a marker along a curve, count numbers up, grow bars, fill a progress bar. Keep the end state on screen; do not fade everything out.
- Every tween goes on `tl` with an explicit absolute position in seconds as the last argument, and ends by {d}. Use tl.fromTo(target, {{from}}, {{to}}, position) for entrances (it applies the from-state immediately), and tl.set for instant changes. Never call gsap.to / gsap.from / gsap.set directly; only `tl` is seeked.
- Draw-on SVG paths: give the path pathLength="1" and stroke-dasharray="1", then tl.fromTo("#pay-line", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 3, ease: "power1.inOut"}}, 2).
- Counting numbers: const v = {{n: 0}}; tl.to(v, {{n: 125, duration: 3, ease: "none", onUpdate: () => {{ document.getElementById("val-profit").textContent = "$" + Math.round(v.n); }}}}, 4); The onUpdate may only derive text from the tween value.
- The scene must be deterministic: no Math.random, Date, performance.now, setTimeout, setInterval, requestAnimationFrame, event listeners, CSS transitions or @keyframes, and no repeat:-1 or infinite yoyo. Finite repeats are fine.

CONTENT
- Finance explainer style: clear, numerate and calm. Charts, payoff lines, axes, price ladders and callouts are inline SVG with the viewBox equal to its pixel size (no scaling, so font sizes stay real). Use realistic numbers that agree with the narration.
- Show short labels, numbers and a headline; never print the narration as sentences. No logos, photos, emoji or disclaimers.
- When a checker report is sent back to you, fix the geometry or timing it names. Do not add data-layout-* attributes to silence it. Return the whole corrected fragment.

EXAMPLE of the shape of a good answer (adapt it, do not copy it):
<style>
#scene .title {{ position:absolute; left:{margin}px; top:{margin}px; width:{inner_w}px; height:80px; font-size:64px; font-weight:800; line-height:1.2; white-space:nowrap; }}
#scene .panel {{ position:absolute; left:{margin}px; top:240px; width:{chart_w}px; height:{chart_h}px; background:#161B22; border-radius:24px; }}
#scene .stat {{ position:absolute; left:{margin + chart_w + 48}px; width:{inner_w - chart_w - 48}px; height:110px; font-size:96px; font-weight:800; line-height:1.2; white-space:nowrap; }}
#scene .cap {{ position:absolute; left:{margin + chart_w + 48}px; width:{inner_w - chart_w - 48}px; height:44px; font-size:32px; line-height:1.2; white-space:nowrap; color:#E6EDF3; }}
</style>
<div class="panel"></div>
<svg id="chart" width="{chart_w}" height="{chart_h}" viewBox="0 0 {chart_w} {chart_h}" style="position:absolute;left:{margin}px;top:240px">
  <line x1="40" y1="{chart_h - 40}" x2="{chart_w - 40}" y2="{chart_h - 40}" stroke="#E6EDF3" stroke-width="3"/>
  <path id="pay-line" d="M 40 {chart_h - 80} L {chart_w // 2} {chart_h - 80} L {chart_w - 40} 60" fill="none" stroke="#00C896" stroke-width="8" pathLength="1" stroke-dasharray="1"/>
  <circle id="marker" cx="40" cy="{chart_h - 80}" r="14" fill="#FFD700"/>
</svg>
<div id="t-title" class="title">Long call payoff at expiry</div>
<div id="val-profit" class="stat" style="top:300px;color:#00C896">$0</div>
<div id="lbl-profit" class="cap" style="top:420px">Profit if price rises</div>
<script>
tl.fromTo("#t-title", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.8, ease:"power2.out"}}, 0.2);
tl.fromTo(".panel", {{opacity:0}}, {{opacity:1, duration:0.8}}, 0.6);
tl.fromTo("#pay-line", {{strokeDashoffset:1}}, {{strokeDashoffset:0, duration:{draw_dur}, ease:"power1.inOut"}}, 1.5);
tl.to("#marker", {{attr:{{cx:{chart_w - 40}, cy:60}}, duration:{draw_dur}, ease:"power1.inOut"}}, 1.5);
tl.fromTo("#lbl-profit", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.6}}, {cap_at});
const v = {{n:0}};
tl.to(v, {{n:125, duration:{count_dur}, ease:"none", onUpdate:() => {{ document.getElementById("val-profit").textContent = "$" + Math.round(v.n); }}}}, {count_at});
</script>

Output ONLY the fragment."""
