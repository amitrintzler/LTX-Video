# Video Studio

A local web UI and webhook for the trailer toolkit. Runs on **127.0.0.1 only** — it
triggers hours of GPU work and writes files, so nothing outside this Mac can reach it.

## Start

```bash
cinematic-pipeline/studio/start.sh
```

Then open **http://127.0.0.1:8765**. Needs `fastapi` and `uvicorn`
(`pip3 install fastapi uvicorn`).

## The one rule it enforces

LTX Desktop owns a single Metal pipeline, so **generation jobs run one at a time**.
Submit three renders and one runs while two queue. Everything that doesn't touch the
GPU — reassembly, scoring, thumbnails, QA, vertical cuts — runs in parallel. This was
enforced by hand all through the trailer's production; here it is enforced by the queue.

## Jobs

| Job | GPU | Typical | What it does |
|---|---|---|---|
| `offline-cut` | no | ~20s | Whole edit, audio and titles with placeholder footage. The fast way to judge a change. |
| `reassemble` | no | ~1 min | Rebuild titles, music and edit from clips already generated. |
| `compose-score` | no | seconds | Compose the music cue. |
| `capture-screenshots` | no | ~1 min | Re-capture the live site into the project's reference folder. |
| `qa` | no | ~30s | Duration, streams, freeze, duplicate frames, silence, loudness, per-segment spread, verdict. |
| `vertical-cut` | no | ~1 min | Derive a 9:16 (or 1:1) cut from a finished master. |
| `regenerate-clip` | **yes** | ~35 min | Regenerate one atmosphere clip. Clears that clip's cached payload and result, then refills it. |
| `render-preview` | **yes** | ~3 h | Generate all clips at preview quality. |
| `render-final` | **yes** | ~3 h | Generate all clips at final quality. |

## Configs

The trailer's titles, shot list, prompts, seeds, story lessons, chain rows and payoff
shapes are exported as JSON. **Load defaults** in the Config panel gives you exactly the
constants that produced the delivered master; edit, save under a name, then choose that
name in a job's `config` field.

Running with no config uses the tuned defaults, so the delivered master stays
reproducible. A dry run with the exported config produces byte-identical output to a dry
run without it — that equivalence is what makes the config layer safe.

Saved configs live in `~/LTX-Studio/configs`, logs in `~/LTX-Studio/logs`.

## Webhook

```bash
# QA a file
curl -X POST http://127.0.0.1:8765/webhook/qa \
  -H 'Content-Type: application/json' \
  -d '{"params":{"video":"/path/to/video.mp4"}}'

# Fast edit check
curl -X POST http://127.0.0.1:8765/webhook/offline-cut -d '{}'

# Regenerate one clip at final quality
curl -X POST http://127.0.0.1:8765/webhook/regenerate-clip \
  -H 'Content-Type: application/json' \
  -d '{"params":{"clip":"tape_turn","profile":"final"}}'
```

Returns the job id immediately; work continues in the background. Any trigger on this
Mac works — a shell alias, a Shortcut, a cron entry, a Stream Deck button.

## API

`GET /api/job-types` · `POST /api/jobs` · `GET /api/jobs` · `GET /api/jobs/{id}` ·
`POST /api/jobs/{id}/cancel` · `GET /api/jobs/{id}/logs` (server-sent events) ·
`GET /api/configs` · `GET /api/configs/default` · `GET|PUT /api/configs/{name}` ·
`GET /api/outputs` · `GET /api/file?path=…` · `POST /webhook/{job_type}` · `GET /health`

File serving is confined to `~/LTX-Renders` and the project folder.

## Limits

- Cancelling a running generation terminates the local process; LTX Desktop may take a
  moment to free the backend.
- `capture-screenshots` needs Playwright in the same interpreter
  (`pip3 install playwright && python3 -m playwright install chromium`); it says so
  rather than leaving stale captures.
- No authentication, because it is bound to localhost. Do not expose it through a tunnel
  without adding a shared secret first.
