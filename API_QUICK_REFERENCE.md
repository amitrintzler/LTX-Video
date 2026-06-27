# API Quick Reference Card

## Server Start
```bash
python /Users/amitri/Projects/LTX-Video/video-pipeline/api_server.py
```
Base URL: `http://localhost:8080`

---

## Essential Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### Submit Job (Topic)
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "call option payoff",
    "stage": "all",
    "skip_validation": true
  }'
```

### Submit Job (Script/Hyperframes)
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_json": {
      "title": "My Video",
      "scenes": [
        {
          "id": "s01",
          "start": 0,
          "duration": 3,
          "content": "<div>...</div>"
        }
      ]
    },
    "stage": "render"
  }'
```

### Check Job Status
```bash
curl http://localhost:8080/jobs/{job_id}
```
Returns: `status` (pending|running|complete|failed), `elapsed_sec`, `output_files`, `error`

### Stream Logs (Real-Time)
```bash
curl http://localhost:8080/jobs/{job_id}/logs
```
SSE stream - use `curl -N` flag to disable buffering

### Download Output
```bash
curl http://localhost:8080/jobs/{job_id}/files/{filename} -o output.mp4
```

### List All Jobs
```bash
curl http://localhost:8080/jobs
```

---

## Job Statuses
- `pending` - Waiting to start
- `running` - Currently executing
- `complete` - Finished successfully
- `failed` - Error occurred

---

## Common Parameters

**For Topic-Based:**
- `topic` (required) - Topic string
- `stage` - all|research|script|render|tts|stitch (default: all)
- `skip_validation` - true|false (default: false)
- `mode` - narrated|companion-long|both (default: both)

**For Script JSON:**
- `script_json.title` (required)
- `script_json.scenes` (required) - Array of scene objects
- `stage` - all|research|script|render|tts|stitch (default: all)

**Scene Structure:**
```json
{
  "id": "unique_id",
  "start": 0.0,
  "duration": 3.0,
  "content": "<html-or-svg>"
}
```

---

## Workflow

1. **Submit:** POST /jobs → Get `job_id`
2. **Monitor:** GET /jobs/{job_id} → Check `status`
3. **Stream:** GET /jobs/{job_id}/logs → Watch logs
4. **Download:** GET /jobs/{job_id}/files/{name} → Get MP4

---

## Python Template

```python
import requests
import time

BASE = "http://localhost:8080"

# Submit
r = requests.post(f"{BASE}/jobs", json={"topic": "your topic"})
job_id = r.json()["job_id"]

# Wait
while True:
    job = requests.get(f"{BASE}/jobs/{job_id}").json()
    if job["status"] in ["complete", "failed"]:
        break
    time.sleep(5)

# Download
if job["status"] == "complete":
    for f in job["output_files"]:
        r = requests.get(f"{BASE}/jobs/{job_id}/files/{f}")
        open(f, "wb").write(r.content)
```

---

## Bash Template

```bash
# Submit and capture job_id
JOB=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"topic":"your topic"}')
JOB_ID=$(echo $JOB | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

# Poll status
while true; do
  STATUS=$(curl -s http://localhost:8080/jobs/$JOB_ID | \
    grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "Status: $STATUS"
  [[ "$STATUS" != "running" ]] && break
  sleep 5
done

# Download
curl -O "http://localhost:8080/jobs/$JOB_ID/files/output.mp4"
```

---

## JavaScript Template (Browser)

```javascript
const BASE = "http://localhost:8080";

async function createVideo(topic) {
  // Submit job
  const r = await fetch(`${BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic })
  });
  const { job_id } = await r.json();
  
  // Stream logs
  const es = new EventSource(`${BASE}/jobs/${job_id}/logs`);
  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      es.close();
      downloadFiles(job_id);
    } else {
      console.log(e.data);
    }
  };
}

async function downloadFiles(jobId) {
  const r = await fetch(`${BASE}/jobs/${jobId}`);
  const job = await r.json();
  
  for (const file of job.output_files) {
    const url = `${BASE}/jobs/${jobId}/files/${file}`;
    window.location.href = url;
  }
}
```

---

## Response Examples

**201 Created (Job Submitted):**
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "created_at": "2026-04-24T...",
  "stage": "all",
  "topic_or_title": "your topic"
}
```

**200 OK (Job Detail):**
```json
{
  "job_id": "abc123...",
  "status": "running",
  "elapsed_sec": 45.2,
  "output_files": [],
  "error": null
}
```

**500 on Error:**
```json
{
  "detail": "error message"
}
```

---

## Troubleshooting

**Server not responding?**
```bash
curl http://localhost:8080/health
```

**Job taking too long?**
- Check logs: `GET /jobs/{id}/logs`
- Disable validation: `"skip_validation": true`
- Reduce scope: `"stage": "render"` instead of `"all"`

**Download 404?**
- Wait for job to complete: `"status": "complete"`
- Check output_files list in job detail

**Logs not streaming?**
- Use `curl -N` for unbuffered streaming
- Check job_id is correct
- Ensure job is running or completed

---

## File Locations

- API Code: `/Users/amitri/Projects/LTX-Video/video-pipeline/api/`
- Server: `/Users/amitri/Projects/LTX-Video/video-pipeline/api_server.py`
- Web UI: `/Users/amitri/Projects/LTX-Video/video-pipeline/static/index.html`
- Outputs: `/tmp/ltx-video-api/{job_id}/output/`
