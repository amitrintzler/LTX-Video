import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import torch
import torchaudio
import soundfile as sf
from TTS.api import TTS
from torch.serialization import add_safe_globals

try:
    from TTS.config.shared_configs import (
        BaseAudioConfig,
        BaseDatasetConfig,
        BaseTrainingConfig,
        TrainerConfig,
    )
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig

    add_safe_globals(
        [
            XttsConfig,
            XttsAudioConfig,
            XttsArgs,
            BaseAudioConfig,
            BaseDatasetConfig,
            BaseTrainingConfig,
            TrainerConfig,
        ]
    )
except Exception:
    # XTTS config may not be available until the package is installed.
    pass


def _resolve_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    bundled = (
        Path(__file__).resolve().parent
        / "outputs"
        / "ffmpeg-macos-aarch64-v7.1"
    )
    if bundled.exists():
        return str(bundled)
    fallback = (
        Path("/opt/homebrew/lib/python3.11/site-packages/imageio_ffmpeg/binaries")
        / "ffmpeg-macos-aarch64-v7.1"
    )
    if fallback.exists():
        return str(fallback)
    raise FileNotFoundError("ffmpeg not found; install ffmpeg or imageio-ffmpeg.")


def _device(preferred: str | None) -> str:
    if preferred:
        return preferred
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _mix_with_ambient(ffmpeg: str, voice: Path, ambient: Path, out_path: Path) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(ambient),
        "-i",
        str(voice),
        "-filter_complex",
        "[0:a]volume=0.6[a0];[1:a]volume=1.2[a1];"
        "[a0][a1]amix=inputs=2:normalize=0,"
        "loudnorm=I=-16:LRA=11:TP=-1.0,aresample=48000",
        "-t",
        "10.1",
        "-c:a",
        "pcm_s16le",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS with Coqui XTTS v2.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument(
        "--speaker-wav",
        required=True,
        help="Reference speaker WAV (10-30s clean voice works best).",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code (default: en).",
    )
    parser.add_argument(
        "--model",
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        help="XTTS model name.",
    )
    parser.add_argument(
        "--out",
        default="outputs/xtts_voice.wav",
        help="Output WAV path.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Override device (cuda/mps/cpu).",
    )
    parser.add_argument(
        "--ambient",
        default=None,
        help="Optional ambient WAV to mix with voice.",
    )
    parser.add_argument(
        "--mix-out",
        default="outputs/xtts_voice_mix.wav",
        help="Output path for mixed audio when --ambient is provided.",
    )
    args = parser.parse_args()

    speaker_wav = Path(args.speaker_wav)
    if not speaker_wav.exists():
        raise FileNotFoundError(f"Speaker WAV not found: {speaker_wav}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    device = _device(args.device)
    def _load_audio_sf(audiopath: str, sampling_rate: int) -> torch.Tensor:
        audio, lsr = sf.read(audiopath)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
        if lsr != sampling_rate:
            audio_tensor = torchaudio.functional.resample(
                audio_tensor, lsr, sampling_rate
            )
        audio_tensor = audio_tensor.clamp(-1, 1)
        return audio_tensor

    try:
        from TTS.tts.models import xtts as xtts_module

        xtts_module.load_audio = _load_audio_sf
    except Exception:
        pass

    tts = TTS(model_name=args.model, progress_bar=True).to(device)
    tts.tts_to_file(
        text=args.text,
        file_path=str(out_path),
        speaker_wav=str(speaker_wav),
        language=args.language,
    )

    if args.ambient:
        ffmpeg = _resolve_ffmpeg()
        ambient = Path(args.ambient)
        if not ambient.exists():
            raise FileNotFoundError(f"Ambient WAV not found: {ambient}")
        mix_out = Path(args.mix_out)
        mix_out.parent.mkdir(parents=True, exist_ok=True)
        _mix_with_ambient(ffmpeg, out_path, ambient, mix_out)
        print(f"Mixed audio written to {mix_out}")
    else:
        print(f"Voice audio written to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"XTTS error: {exc}", file=sys.stderr)
        raise
