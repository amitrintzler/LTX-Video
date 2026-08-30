# Licensing

Everything shipped inside the trailer, and what each thing permits.

## Music — third-party, licensed

**"Cinematic Trailer" by NastelBom**, from Pixabay.
Source: https://pixabay.com/music/main-title-cinematic-trailer-365143/

Pixabay Content License:

- Free for commercial and non-commercial use.
- No attribution required (crediting the artist is welcome, not obligatory).
- May not be redistributed or sold as a standalone audio file, and may not be
  used on a platform that primarily distributes audio. Inside a video it is fine.

Chosen over three alternatives on measurement, not taste: it reaches full
energy in its first second and spends only 9 of its first 60 seconds more than
12dB below its peak. The epic-buildup candidates stayed quiet for 38 of their
first 60 seconds, which would have left most of a 60-second trailer near
silent.

Three unused candidates are kept under the same licence in
`~/LTX-Renders/ltx25-optionseducator-trailer60/music-candidates/`:

| File | Track | Artist |
| --- | --- | --- |
| `1_total_war_epic_action.mp3` | Total War (Epic Action Cinematic Trailer Main) | AudioAtlant |
| `3_epic_hollywood_choir.mp3` | Epic Hollywood Trailer | Good_B_Music |
| `4_energetic_orchestral.mp3` | Trailer Cinematic Energetic | echoes_of_lumen |

## Synthesised score — ours

`cinematic-pipeline/scripts/compose_trailer_score.py` writes an original cue
from scratch: no samples, no third-party audio, no rights attached. It remains
in the repo as a fallback and can be used anywhere without restriction.
`make_music()` prefers `music/composed_score.wav`, so dropping either the
licensed track or a fresh synth render at that path selects it.

## Story illustrations — ours

From the Options Educator product repo
(`~/Projects/optionseducator/public/assets/story-illustrations`). Own work.

## Sound effects — ours

From the product's own asset library
(`~/Projects/optionseducator/public/assets/videos/sfx`).

## Generated city footage — ours, with a caveat

Rendered by LTX Desktop 2.5 from prompts in this repo. Check LTX Desktop's own
terms for the model's output rights.

The city is generated **in the game's style**. It is not footage of the real
game and must not be presented as such.

## Fonts

The film's titles use system faces. The capabilities dashboard uses Archivo and
IBM Plex via Google Fonts, both under the SIL Open Font License.
