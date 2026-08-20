"""
Stage: audio bed (narration + music), 100% free / offline.

  - Narration: Piper TTS (offline, no API key) when a voice model is present.
  - Music:     any local file referenced by the project, or a procedural pad
               synthesised with ffmpeg when none is supplied.
  - Mix:       narration over a ducked music bed, normalised toward -16 LUFS.

LTX-2 can also emit *synchronised* audio per shot; when project.audio.use_shot_audio
is true the edit stage keeps the generated audio and this stage is skipped.
"""
from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

FF = cfg.ffmpeg_bin()


def _piper_cmd() -> list[str] | None:
    """piper on PATH, else the venv script, else `python -m piper`."""
    p = shutil.which("piper")
    if p:
        return [p]
    venv_piper = Path(sys.executable).parent / "piper"
    if venv_piper.exists():
        return [str(venv_piper)]
    try:
        import piper  # noqa: F401
        return [sys.executable, "-m", "piper"]
    except ImportError:
        return None


def narrate(text: str, voice_model: Path, out_wav: Path) -> Path | None:
    cmd = _piper_cmd()
    if not cmd or not voice_model.exists():
        print("    (skip narration: piper or voice model unavailable)")
        return None
    subprocess.run([*cmd, "-m", str(voice_model), "-f", str(out_wav)],
                   input=text, text=True, check=True)
    return out_wav


def procedural_music(duration: float, out_wav: Path) -> Path:
    """A soft two-note ambient pad — no external assets, royalty-free by construction."""
    fade_st = max(0.0, duration - 1.5)
    subprocess.run([
        FF, "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"sine=frequency=174.6:duration={duration:.2f}",
        "-f", "lavfi", "-i", f"sine=frequency=261.6:duration={duration:.2f}",
        "-filter_complex",
        f"[0][1]amix=inputs=2,volume=0.10,"
        f"afade=t=in:d=1.5,afade=t=out:st={fade_st:.2f}:d=1.5[a]",
        "-map", "[a]", str(out_wav)], check=True)
    return out_wav


def build_bed(project: dict, total_duration: float, work: Path,
              narration_wav: Path | None) -> Path:
    audio_cfg = project.get("audio", {})
    music_src = audio_cfg.get("music")
    music = work / "music.wav"
    if music_src and (work.parent / music_src).exists():
        subprocess.run([FF, "-y", "-loglevel", "error", "-i",
                        str(work.parent / music_src), "-t", f"{total_duration:.2f}",
                        str(music)], check=True)
    else:
        procedural_music(total_duration, music)

    out = work / "bed.wav"
    if narration_wav and narration_wav.exists():
        # Duck music under narration via sidechaincompress, then loudnorm.
        subprocess.run([
            FF, "-y", "-loglevel", "error",
            "-i", str(music), "-i", str(narration_wav),
            "-filter_complex",
            "[0:a]volume=0.5[m];"
            "[m][1:a]sidechaincompress=threshold=0.05:ratio=6:release=400[ducked];"
            "[ducked][1:a]amix=inputs=2:duration=longest,loudnorm=I=-16:TP=-1.5[a]",
            "-map", "[a]", str(out)], check=True)
    else:
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(music),
                        "-af", "loudnorm=I=-16:TP=-1.5", str(out)], check=True)
    return out
