# Engine

Shared parts of the video pipeline. A film supplies what it *is*; the engine
supplies everything about *making* it.

## Adding a generator

A generation service is configuration, not code. `providers/http_api.py` posts a
request, polls the operation, and downloads the result; all that differs between
services is where each value sits in the JSON, so those positions are described
as dotted paths:

```json
{
  "media": ["video"],
  "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-001:predictLongRunning",
  "auth":   {"type": "env_header", "var": "GEMINI_API_KEY", "header": "x-goog-api-key"},
  "submit": {"prompt": "instances[0].prompt", "seconds": "parameters.durationSeconds"},
  "poll":   {"operation": "name", "done": "done", "url": "https://.../v1/{operation}"},
  "fetch":  {"url": "response.generateVideoResponse.generatedSamples[0].video.uri"}
}
```

Credentials come from the environment and are never stored in the repo. A
missing one is reported before any request goes out.

**Verified:** `ltx_desktop` — it rendered the films in this repo.
**Not verified:** hosted providers. They are written against documented request
and response shapes but need credentials this machine does not have. The
submit/poll/fetch machinery is proven by `tests/test_http_provider.py`, which
runs a local server imitating the operation-and-poll shape. Confirm against the
real service before trusting a render to it.

Note that *Flow* is Google's consumer UI and has no documented public API; the
developer path to the same model is Veo through the Gemini API or Vertex AI.

## Media kinds

`media.MediaSpec` declares `video`, `image` or `audio` up front. A provider
lists what it accepts and refuses the rest before a render starts rather than
failing partway through.

## Brand

`brand.json` beside a film, with an image for the mark:

```json
{
  "name": "Options Educator",
  "wordmark": "OPTIONS EDUCATOR",
  "accent": "#38BDF8",
  "logo": "assets/logo.png",
  "watermark": {"corner": "bottom-right", "opacity": 0.5}
}
```

A project without a brand file still renders, unbranded. One without a logo gets
a neutral drawn mark rather than a hole.

## Text and language

`draw.py` handles the two failures that do not announce themselves: a face with
no glyphs for a script draws empty boxes rather than raising, and a Pillow built
without libraqm lays every string left-to-right, so Hebrew renders reversed and
Arabic letters never join. Paragraph direction is forced from the locale, not
detected from the first character — otherwise a Hebrew line opening with an
English term is laid out backwards.

Right-to-left locales need `python-bidi` and `arabic-reshaper`; a render refuses
rather than producing silently wrong text without them.
