import sys, numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

dur = float(sys.argv[1]) if len(sys.argv) > 1 else 33.0
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/music.wav"
proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
print("loaded")
prompt = ("upbeat modern corporate finance promo, driving electronic beat, energetic, "
          "confident, motivational, clean synths, subtle arpeggio, business technology")
inp = proc(text=[prompt], padding=True, return_tensors="pt")
# musicgen ~50 tokens/sec of audio
max_tokens = int(dur * 50) + 10
with torch.no_grad():
    wav = model.generate(**inp, max_new_tokens=max_tokens, do_sample=True, guidance_scale=3.0)
sr = model.config.audio_encoder.sampling_rate
audio = wav[0, 0].cpu().numpy()
sf.write(out, audio, sr)
print("DONE", out, round(len(audio)/sr, 1), "s @", sr)
