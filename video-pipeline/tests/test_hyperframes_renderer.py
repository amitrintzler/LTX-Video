"""Tests for the hyperframes renderer. Unit tests mock the model and every
subprocess; the one integration test drives the real pinned CLI and is skipped
unless `npm ci` has been run in video-pipeline/hyperframes."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PipelineConfig  # noqa: E402
from stages.renderers import get_renderer  # noqa: E402
from stages.renderers import hyperframes as hf  # noqa: E402

REAL_CLI = Path(__file__).parent.parent / "hyperframes/node_modules/.bin/hyperframes"

GOOD_FRAGMENT = """<style>#scene .t { position:absolute; left:96px; top:96px; font-size:64px; }</style>
<div id="t-title" class="t">Long call payoff</div>
<script>tl.fromTo("#t-title", {opacity:0}, {opacity:1, duration:1}, 0.5);</script>"""


def _cfg(**kw):
    base = dict(
        render_llm_provider="lmstudio",
        render_llm_model="local-model",
        render_backup_providers=["claude"],
        claude_model="claude-sonnet-4-6",
        renderer_max_retries=3,
    )
    base.update(kw)
    return PipelineConfig(**base)


def _scene(duration=6):
    return {
        "title": "Payoff",
        "description": "Draw a long call payoff.",
        "narration": "A long call profits when price rises.",
        "duration_sec": duration,
        "style": "dark background #0d1117, green #00C896",
    }


def _finding(code, severity="error", section="layout", selector="#a", **kw):
    return {
        "code": code,
        "severity": severity,
        "selector": selector,
        "message": f"{code} happened",
        "fixHint": f"fix {code}",
        **kw,
    }


def _report(findings=(), browser_skipped=False):
    report = {"ok": not findings, "browserSkipped": browser_skipped}
    for section in ("lint", "runtime", "layout", "motion", "contrast"):
        report[section] = {"ok": True, "findings": []}
    for section, finding in findings:
        report[section]["findings"].append(finding)
    return report


class FakeTools:
    """Stands in for subprocess.run: answers `check` from a queue of reports
    and `render` by writing a file, remembering what it was asked to render."""

    def __init__(self, reports):
        self.reports = list(reports)
        self.commands = []
        self.rendered_html = []

    def __call__(self, cmd, **kwargs):
        self.commands.append(cmd)
        sub = cmd[1]
        if sub == "check":
            report = self.reports.pop(0)
            return subprocess.CompletedProcess(cmd, 1, json.dumps(report), "")
        assert sub == "render", cmd
        out = Path(cmd[cmd.index("-o") + 1])
        out.write_bytes(b"fake-mp4")
        self.rendered_html.append((Path(kwargs["cwd"]) / "index.html").read_text())
        return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def toolchain(tmp_path, monkeypatch):
    cli = tmp_path / "bin" / "hyperframes"
    cli.parent.mkdir()
    cli.write_text("#!/bin/sh\n")
    gsap = tmp_path / "gsap.min.js"
    gsap.write_text("/* gsap */")
    monkeypatch.setattr(hf, "CLI_PATH", cli)
    monkeypatch.setattr(hf, "GSAP_PATH", gsap)
    monkeypatch.setattr(hf, "verify_video", lambda *a, **k: None)
    return cli


def _run(tools, scene, cfg, out_path, *, lm=None, claude=None):
    lm = lm or MagicMock(return_value=GOOD_FRAGMENT)
    claude = claude or MagicMock(return_value=GOOD_FRAGMENT)
    with (
        patch("stages.renderers.hyperframes._call_lmstudio_api", lm),
        patch("stages.renderers.hyperframes._call_claude_cli", claude),
        patch("stages.renderers.hyperframes.subprocess.run", tools),
    ):
        return hf.render(scene, cfg, out_path)


# ── Registry ─────────────────────────────────────────────────────


def test_registry_has_hyperframes_and_script_stage_does_not_offer_it():
    assert get_renderer("hyperframes").render is hf.render
    script_src = (Path(__file__).parent.parent / "stages/script.py").read_text()
    assert "hyperframes" not in script_src


# ── Fragment extraction and sanitising ───────────────────────────


def test_extract_html_takes_fenced_block_or_starts_at_first_tag():
    assert hf.extract_html("Here:\n```html\n<div>x</div>\n```\nDone") == "<div>x</div>"
    assert hf.extract_html("Sure!\n<div>y</div>") == "<div>y</div>"
    assert hf.extract_html("```html\n<div>z</div>") == "<div>z</div>"


def test_sanitize_strips_cdn_scripts_links_and_external_urls():
    raw = """<!DOCTYPE html><html><head><title>t</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto">
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<style>@import url("https://x.example/a.css");
#scene .a { background: url(https://evil.example/a.png); color: #fff }</style></head>
<body><div id="a">hi <img src="https://example.com/logo.png"></div>
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><image href="//cdn.example/x.png"/></svg>
<script>tl.to("#a", {x:10, duration:1}, 0);</script></body></html>"""
    parts = hf.sanitize_fragment(raw)
    full = parts.as_fragment()
    assert "http://www.w3.org/2000/svg" in full  # namespace is not a fetch
    for banned in (
        "cdn.jsdelivr",
        "googleapis",
        "evil.example",
        "example.com",
        "cdn.example",
        "@import",
        "<link",
        "<html",
        "<body",
        "<head",
        "<title",
        "DOCTYPE",
    ):
        assert banned not in full, banned
    assert 'tl.to("#a"' in parts.script
    assert "src=" not in parts.markup.replace("<svg", "")


def test_sanitize_removes_timeline_creation_and_registration():
    raw = """<div id="a">x</div><script>
const tl = gsap.timeline({
  paused: true,
  defaults: { ease: "power2.out" }
});
tl.to("#a", {opacity: 1, duration: 1}, 0);
window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
tl.play();
tl.seek(0);
</script>"""
    parts = hf.sanitize_fragment(raw)
    assert "gsap.timeline" not in parts.script
    assert "__timelines" not in parts.script
    assert "tl.play" not in parts.script
    assert 'tl.to("#a"' in parts.script
    assert "const tl" not in parts.script  # would shadow the host timeline


def test_sanitize_aliases_a_renamed_timeline_to_the_host_timeline():
    raw = """<div id="a">x</div><script>
const master = gsap.timeline({ paused: true });
master.to("#a", {opacity: 1, duration: 1}, 0);
</script>"""
    parts = hf.sanitize_fragment(raw)
    assert "const master = tl;" in parts.script
    assert "gsap.timeline" not in parts.script
    assert hf.fragment_findings(parts) == []

    chained = hf.sanitize_fragment(
        '<div id="a">x</div><script>gsap.timeline({paused:true}).to("#a",{x:1},0);</script>'
    )
    assert chained.script.startswith("tl")
    assert "gsap.timeline" not in chained.script


def test_fragment_findings_flag_collisions_and_nondeterminism():
    parts = hf.sanitize_fragment(
        """<div id="scene"><div id="a">x</div><div id="a">y</div></div>
<script>const r = Math.random(); setTimeout(() => {}, 5); // Math.random in a comment
tl.to("#a", {x: 1, repeat: -1}, 0);</script>"""
    )
    codes = [f["code"] for f in hf.fragment_findings(parts)]
    assert codes.count("nondeterministic_script") == 3  # random, timer, repeat -1
    assert "reserved_id" in codes
    assert "duplicate_id" in codes
    assert all(f["severity"] == "error" for f in hf.fragment_findings(parts))

    no_tween = hf.sanitize_fragment('<div id="a">x</div><script>var q = 1;</script>')
    assert [f["code"] for f in hf.fragment_findings(no_tween)] == ["no_tweens"]
    assert hf.fragment_findings(hf.sanitize_fragment(GOOD_FRAGMENT)) == []


# ── Wrapper and sidecar ──────────────────────────────────────────


def test_document_attributes_come_from_config_not_the_model():
    parts = hf.sanitize_fragment(GOOD_FRAGMENT)
    doc = hf.build_document(
        parts,
        width=1280,
        height=720,
        fps=24,
        duration_sec=7.5,
        bg_color="#112233",
    )
    root = (
        'id="root" data-composition-id="main" data-start="0" data-duration="7.5" '
        'data-width="1280" data-height="720" data-fps="24"'
    )
    assert root in doc
    assert (
        '<div id="scene" class="clip" data-start="0" data-duration="7.5" '
        'data-track-index="0">' in doc
    )
    assert 'content="width=1280, height=720"' in doc
    assert '<script src="gsap.min.js"></script>' in doc  # local file, no CDN
    assert "http" not in doc.split("<body>")[0].replace("http-equiv", "")
    assert doc.count("gsap.timeline(") == 1
    assert doc.count('window.__timelines["main"] = tl;') == 1
    assert "background:#112233" in doc
    assert 'data-resolution="landscape"' not in doc  # only for preset sizes

    landscape = hf.build_document(
        parts, width=1920, height=1080, fps=30, duration_sec=6, bg_color="#000"
    )
    assert 'data-resolution="landscape"' in landscape
    assert 'data-duration="6"' in landscape


def test_motion_sidecar_has_keeps_moving_and_one_assertion_per_unique_text_id():
    markup = """
<div id="scene-bg"></div>
<div id="t-title">Title</div>
<div id="dup">a</div><div id="dup">b</div>
<div id="card"><span id="t-inner">Nested</span></div>
<svg id="chart"><rect id="bar"/><text id="svg-lbl">Strike</text></svg>
<div id="scene">x</div>
<div id="bad id">spaces</div>
<div id="shape"></div>
<div>no id with text</div>
"""
    sidecar = hf.build_motion_sidecar(markup, 8)
    assert sidecar["duration"] == 8.0
    first = sidecar["assertions"][0]
    assert first == {
        "kind": "keepsMoving",
        "withinSelector": "#scene",
        "maxStaticSec": 2,
    }
    stays = [
        a["selector"] for a in sidecar["assertions"] if a["kind"] == "staysInFrame"
    ]
    assert stays == ["#t-title", "#card", "#t-inner", "#chart", "#svg-lbl"]
    assert len(stays) == len(set(stays))  # never the same selector twice
    for banned in ("#dup", "#scene", "#bar", "#shape", "#scene-bg"):
        assert banned not in stays


# ── check output ─────────────────────────────────────────────────


def test_errors_gate_but_warnings_and_info_do_not():
    report = _report(
        [
            ("layout", _finding("text_box_overflow")),
            ("layout", _finding("canvas_overflow", severity="warning")),
            ("motion", _finding("transient", severity="info")),
        ]
    )
    gating = [f for f in hf.collect_findings(report) if hf.is_gating(f)]
    assert [f["code"] for f in gating] == ["text_box_overflow"]


def test_sweep_static_gates_even_as_a_warning():
    report = _report([("motion", _finding("sweep_static", severity="warning"))])
    assert [f["code"] for f in hf.collect_findings(report) if hf.is_gating(f)] == [
        "sweep_static"
    ]


def test_repeated_samples_of_one_finding_collapse():
    same = _finding("contrast_aa_failure", selector="#a")
    report = _report([("contrast", same)] * 4)
    assert len(hf.collect_findings(report)) == 1


def test_parse_check_output_tolerates_noise_and_rejects_non_reports():
    report = _report()
    noisy = "update available!\n" + json.dumps(report) + "\n"
    assert hf.parse_check_output(noisy)["ok"] is True
    with pytest.raises(hf.HyperframesToolError, match="no report"):
        hf.parse_check_output("Error: chrome crashed", "boom", 1)


def test_browser_skipped_is_a_tool_failure_unless_lint_explains_it():
    with pytest.raises(hf.HyperframesToolError, match="browser"):
        hf.parse_check_output(json.dumps(_report(browser_skipped=True)))
    explained = _report([("lint", _finding("css_parse_error"))], browser_skipped=True)
    assert hf.parse_check_output(json.dumps(explained))["browserSkipped"] is True


def test_feedback_is_capped_ordered_and_carries_fix_hints():
    gating = [
        {**_finding(f"layout_code_{i}", selector=f"#e{i}"), "section": "layout"}
        for i in range(12)
    ]
    gating[0]["message"] = "m" * 800
    text = hf.build_feedback(gating)
    assert text.count("\n- ") == 9  # 8 findings + the "and N more" line
    assert "layout_code_0 #e0:" in text
    assert "(fix: fix layout_code_1)" in text
    assert "layout_code_8" not in text
    assert "and 4 more" in text
    assert len(text) <= 1900
    assert "..." in text  # the 800 char message was clipped


# ── render(): ladder, retries, shipping ──────────────────────────


def test_clean_pass_writes_sources_and_clears_stale_defects(tmp_path, toolchain):
    out = tmp_path / "clips" / "scene_001.mp4"
    out.parent.mkdir()
    hf._defects_path(out).write_text("{}")
    tools = FakeTools([_report()])
    lm = MagicMock(return_value=GOOD_FRAGMENT)
    assert _run(tools, _scene(6), _cfg(), out, lm=lm) == out
    assert out.read_bytes() == b"fake-mp4"
    assert not hf._defects_path(out).exists()
    html = (out.parent / "scene_001.html").read_text()
    assert 'data-duration="6"' in html and "Long call payoff" in html
    motion = json.loads((out.parent / "scene_001.motion.json").read_text())
    assert motion["assertions"][0]["kind"] == "keepsMoving"
    assert {"kind": "staysInFrame", "selector": "#t-title"} in motion["assertions"]
    assert not (out.parent / "_rejected").exists()
    lm.assert_called_once()

    check_cmd = tools.commands[0]
    assert check_cmd[1:] == [
        "check",
        "--json",
        "--strict",
        "--frame-check",
        "--at-transitions",
    ]
    render_cmd = tools.commands[1]
    assert render_cmd[1] == "render"
    assert render_cmd[render_cmd.index("--fps") + 1] == "30"
    assert render_cmd[render_cmd.index("--quality") + 1] == "delivery"
    assert "--quiet" in render_cmd


def test_failed_check_retries_with_feedback_and_previous_fragment(tmp_path, toolchain):
    out = tmp_path / "scene_002.mp4"
    tools = FakeTools([_report([("layout", _finding("text_box_overflow"))]), _report()])
    lm = MagicMock(return_value=GOOD_FRAGMENT)
    _run(tools, _scene(), _cfg(), out, lm=lm)
    assert lm.call_count == 2
    first, second = lm.call_args_list
    assert first.kwargs["error"] is None
    assert (
        "text_box_overflow #a: text_box_overflow happened (fix: fix text_box_overflow)"
        in (second.kwargs["error"])
    )
    assert "Your previous fragment" in second.kwargs["description"]
    assert "Long call payoff" in second.kwargs["description"]
    assert first.kwargs["extract"] is hf.extract_html
    # the rejected attempt is kept for inspection
    rejected = out.parent / "_rejected"
    assert (rejected / "scene_002_attempt1.html").exists()
    assert (rejected / "scene_002_attempt1.motion.json").exists()
    assert json.loads((rejected / "scene_002_attempt1.check.json").read_text())
    assert not hf._defects_path(out).exists()


def test_last_attempt_escalates_to_the_paid_backend(tmp_path, toolchain):
    out = tmp_path / "scene_003.mp4"
    bad = _report([("layout", _finding("content_overlap"))])
    tools = FakeTools([bad, bad, _report()])
    lm = MagicMock(return_value=GOOD_FRAGMENT)
    claude = MagicMock(return_value=GOOD_FRAGMENT)
    _run(tools, _scene(), _cfg(), out, lm=lm, claude=claude)
    assert lm.call_count == 2
    assert claude.call_count == 1
    assert lm.call_args.kwargs["model"] == "local-model"
    assert claude.call_args.args[0] == "claude-sonnet-4-6"
    assert claude.call_args.kwargs["extract"] is hf.extract_html


def test_best_attempt_ships_rendered_from_its_saved_html_with_defects(
    tmp_path, toolchain
):
    out = tmp_path / "clips" / "scene_004.mp4"
    out.parent.mkdir()
    fragments = {
        1: '<div id="t-a1">attempt-one</div><script>tl.to("#t-a1",{x:1,duration:1},0);</script>',
        2: '<div id="t-a2">attempt-two</div><script>tl.to("#t-a2",{x:1,duration:1},0);</script>',
        3: '<div id="t-a3">attempt-three</div><script>tl.to("#t-a3",{x:1,duration:1},0);</script>',
    }
    calls = {"n": 0}

    def next_fragment(*args, **kwargs):
        calls["n"] += 1
        return fragments[calls["n"]]

    reports = [
        # score 2 + 3 = 5
        _report(
            [
                ("contrast", _finding("contrast_aa_failure", section="contrast")),
                ("layout", _finding("text_box_overflow")),
            ]
        ),
        # score 3: the winner
        _report([("layout", _finding("text_box_overflow"))]),
        # score 3 + 3 = 6
        _report(
            [
                ("layout", _finding("text_box_overflow", selector="#x")),
                ("layout", _finding("content_overlap", selector="#y")),
            ]
        ),
    ]
    tools = FakeTools(reports)
    result = _run(
        tools,
        _scene(),
        _cfg(),
        out,
        lm=MagicMock(side_effect=next_fragment),
        claude=MagicMock(side_effect=next_fragment),
    )
    assert result == out and out.read_bytes() == b"fake-mp4"
    # exactly one render, of attempt two
    assert len(tools.rendered_html) == 1
    assert "attempt-two" in tools.rendered_html[0]
    assert "attempt-one" not in tools.rendered_html[0]
    assert "attempt-two" in (out.parent / "scene_004.html").read_text()
    defects = json.loads(hf._defects_path(out).read_text())
    assert defects["attempt"] == 2
    assert defects["score"] == 3
    assert defects["problems"] == [
        "text_box_overflow #a: text_box_overflow happened (fix: fix text_box_overflow)"
    ]
    assert (out.parent / "scene_004.motion.json").exists()
    assert len(list((out.parent / "_rejected").glob("*.html"))) == 3


def test_tie_goes_to_the_later_attempt(tmp_path, toolchain):
    out = tmp_path / "scene_005.mp4"
    bad = _report([("layout", _finding("text_box_overflow"))])
    frags = iter(
        f'<div id="t{i}">pick-{i}</div><script>tl.to("#t{i}",{{x:1}},0);</script>'
        for i in (1, 2, 3)
    )
    tools = FakeTools([bad, bad, bad])
    _run(
        tools,
        _scene(),
        _cfg(),
        out,
        lm=MagicMock(side_effect=lambda *a, **k: next(frags)),
        claude=MagicMock(side_effect=lambda *a, **k: next(frags)),
    )
    assert "pick-3" in tools.rendered_html[0]


def test_unplayable_attempts_never_ship(tmp_path, toolchain):
    """Runtime exceptions and a frozen timeline are not 'least defective', they
    are broken: the stage must fall back to slides rather than ship them."""
    out = tmp_path / "scene_006.mp4"
    reports = [
        _report([("runtime", _finding("page_error", section="runtime"))]),
        _report([("motion", _finding("sweep_static", severity="warning"))]),
        _report([("lint", _finding("css_parse_error"))], browser_skipped=True),
    ]
    tools = FakeTools(reports)
    with pytest.raises(hf.HyperframesCheckError, match="css_parse_error"):
        _run(tools, _scene(), _cfg(), out)
    assert not out.exists()
    assert tools.rendered_html == []
    assert len(list((out.parent / "_rejected").glob("*.html"))) == 3


def test_tool_failures_are_not_retried(tmp_path, toolchain):
    out = tmp_path / "scene_007.mp4"
    lm = MagicMock(return_value=GOOD_FRAGMENT)

    def broken(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "chrome exploded")

    with pytest.raises(hf.HyperframesToolError, match="chrome exploded"):
        _run(broken, _scene(), _cfg(), out, lm=lm)
    lm.assert_called_once()


def test_model_failures_are_retried_and_empty_fragment_is_explained(
    tmp_path, toolchain
):
    out = tmp_path / "scene_008.mp4"
    outputs = iter(["", GOOD_FRAGMENT])
    lm = MagicMock(side_effect=lambda *a, **k: next(outputs))
    tools = FakeTools([_report()])
    _run(tools, _scene(), _cfg(), out, lm=lm)
    assert lm.call_count == 2
    assert "empty_scene" in lm.call_args.kwargs["error"]


def test_missing_cli_tells_the_user_to_run_npm_ci(tmp_path, monkeypatch):
    monkeypatch.setattr(hf, "CLI_PATH", tmp_path / "nope" / "hyperframes")
    lm = MagicMock()
    with pytest.raises(hf.HyperframesToolError, match="npm ci"):
        _run(FakeTools([]), _scene(), _cfg(), tmp_path / "scene_009.mp4", lm=lm)
    lm.assert_not_called()


# ── Output verification ──────────────────────────────────────────


def _probe(width=1920, height=1080, rate="30/1", duration="6.000000"):
    return {
        "streams": [{"width": width, "height": height, "r_frame_rate": rate}],
        "format": {"duration": duration},
    }


def test_verify_video_accepts_a_matching_render(monkeypatch):
    monkeypatch.setattr(hf, "probe_video", lambda p: _probe())
    hf.verify_video(Path("x.mp4"), PipelineConfig(), 6)
    monkeypatch.setattr(hf, "probe_video", lambda p: _probe(duration="6.4"))
    hf.verify_video(Path("x.mp4"), PipelineConfig(), 6)  # within 0.5 s


@pytest.mark.parametrize(
    "probe, expected",
    [
        (_probe(width=1280, height=720), "size 1280x720"),
        (_probe(rate="24/1"), "frame rate 24/1"),
        (_probe(duration="4.0"), "duration 4.00s"),
    ],
)
def test_verify_video_rejects_mismatches(monkeypatch, probe, expected):
    monkeypatch.setattr(hf, "probe_video", lambda p: probe)
    with pytest.raises(hf.HyperframesToolError, match=expected):
        hf.verify_video(Path("x.mp4"), PipelineConfig(), 6)


# ── Prompts ──────────────────────────────────────────────────────


def test_system_prompt_states_the_contract_with_real_numbers():
    prompt = hf._build_system_prompt(
        width=1920, height=1080, fps=30, duration_sec=12, bg_color="#0d1117"
    )
    for needle in (
        "1920x1080",
        "96px",
        "UNIQUE id",
        "28px",
        "EXACTLY 12 seconds",
        "#0d1117",
        "no Math.random",
        "gsap.timeline",
        "pathLength",
    ):
        assert needle in prompt, needle
    # the worked example must itself survive the sanitiser untouched
    example = prompt[prompt.index("<style>", prompt.index("EXAMPLE")) :]
    example = example[: example.index("Output ONLY")]
    parts = hf.sanitize_fragment(example)
    assert parts.notes == []
    assert hf.fragment_findings(parts) == []
    selectors = [
        a.get("selector")
        for a in hf.build_motion_sidecar(parts.markup, 12)["assertions"]
    ]
    assert "#val-profit" in selectors and "#t-title" in selectors


def test_user_message_carries_description_narration_and_duration():
    message = hf._build_user_message(_scene(9), 9)
    assert "exactly 9 seconds" in message
    assert "Draw a long call payoff." in message
    assert "A long call profits when price rises." in message
    assert "green #00C896" in message


# ── Integration (real pinned CLI) ────────────────────────────────

INTEGRATION_FRAGMENT = """<style>
#scene .title { position:absolute; left:96px; top:96px; width:1400px; height:80px;
  font-size:64px; font-weight:800; line-height:1.2; white-space:nowrap; }
#scene .bar { position:absolute; left:96px; top:520px; width:1728px; height:24px;
  background:#1f2937; border-radius:12px; }
</style>
<div class="bar"></div>
<div id="t-title" class="title">Break-even moves with premium</div>
<div id="val-count" class="title" style="top:240px;color:#FFD700">$0</div>
<svg id="chart" width="1728" height="300" viewBox="0 0 1728 300" style="position:absolute;left:96px;top:600px">
  <path id="line" d="M 0 250 L 700 250 L 1728 40" fill="none" stroke="#00C896" stroke-width="8" pathLength="1" stroke-dasharray="1"/>
</svg>
<script>
tl.fromTo("#t-title", {opacity:0, y:30}, {opacity:1, y:0, duration:0.6}, 0.1);
tl.fromTo("#line", {strokeDashoffset:1}, {strokeDashoffset:0, duration:2.6, ease:"none"}, 0.2);
const v = {n:0};
tl.to(v, {n:100, duration:2.6, ease:"none", onUpdate:() => { document.getElementById("val-count").textContent = "$" + Math.round(v.n); }}, 0.2);
</script>"""


@pytest.mark.skipif(
    not REAL_CLI.exists(),
    reason="needs `npm ci` in video-pipeline/hyperframes (pinned HyperFrames CLI)",
)
def test_real_cli_checks_and_renders_a_fixed_composition(tmp_path):
    out = tmp_path / "scene_001.mp4"
    cfg = PipelineConfig()
    parts = hf.sanitize_fragment(INTEGRATION_FRAGMENT)
    document = hf.build_document(
        parts,
        width=cfg.render_width,
        height=cfg.render_height,
        fps=cfg.render_fps,
        duration_sec=3,
        bg_color="#0d1117",
    )
    sidecar = hf.build_motion_sidecar(parts.markup, 3)
    project = tmp_path / "project"
    project.mkdir()
    hf._write_project(project, document, sidecar)
    report = hf.run_check(hf.CLI_PATH, project, 3)
    gating = [f for f in hf.collect_findings(report) if hf.is_gating(f)]
    assert gating == [], [hf.describe_finding(f) for f in gating]
    hf._render_and_verify(hf.CLI_PATH, project, out, cfg, 3)
    info = hf.probe_video(out)
    stream = info["streams"][0]
    assert (stream["width"], stream["height"]) == (1920, 1080)
    assert stream["r_frame_rate"] == "30/1"
    assert abs(float(info["format"]["duration"]) - 3) < 0.5
    assert shutil.which("ffprobe")
