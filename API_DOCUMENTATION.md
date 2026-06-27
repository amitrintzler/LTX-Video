# LTX Video Pipeline - REST API Documentation

## Server Setup

**Start the API server:**
```bash
cd /Users/amitri/Projects/LTX-Video
python video-pipeline/api_server.py
```

**Server Details:**
- Base URL: `http://localhost:8080`
- Port: 8080
- Protocol: HTTP/REST
- Worker: 1 (single-process, thread-safe)
- No authentication required (local use)

---

## API Endpoints

### 1. Health Check
**Check if the API server is running and ready.**

```
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "active_jobs": 0,
  "queued_jobs": 0
}
```

**Use Case:** Verify server is running before submitting jobs

---

### 2. Create Job (Topic-Based)
**Submit a video generation job using a topic string.**

```
POST /jobs
Content-Type: application/json
```

**Request Body:**
```json
{
  "topic": "call option payoff diagram",
  "stage": "all",
  "mode": "narrated",
  "skip_validation": false,
  "max_scenes": null,
  "config_overrides": {}
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `topic` | string | YES | - | Video topic (e.g., "call option payoff", "bull call spread") |
| `stage` | string | NO | "all" | Pipeline stage: `all`, `research`, `script`, `render`, `tts`, `stitch` |
| `mode` | string | NO | "both" | Output mode: `narrated`, `companion-long`, `both` |
| `skip_validation` | boolean | NO | false | Skip scene validator (faster, less strict) |
| `max_scenes` | integer | NO | null | Maximum number of scenes to generate |
| `config_overrides` | object | NO | {} | Config parameter overrides (see Config Overrides section) |

**Response (201 Created):**
```json
{
  "job_id": "be80736e-b4f9-4e03-8542-a7e1608d1ed3",
  "status": "pending",
  "created_at": "2026-04-24T11:32:59.021648",
  "stage": "all",
  "topic_or_title": "call option payoff diagram"
}
```

**Status Codes:**
- `201` - Job created successfully
- `400` - Invalid request (missing required fields)
- `500` - Server error

**Example:**
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "bull call spread strategy",
    "stage": "all",
    "skip_validation": true
  }'
```

---

### 3. Create Job (Script JSON)
**Submit a job with explicit scene definitions (Hyperframes-compatible).**

```
POST /jobs
Content-Type: application/json
```

**Request Body:**
```json
{
  "script_json": {
    "title": "Call Option Payoff",
    "scenes": [
      {
        "id": "s01",
        "start": 0,
        "duration": 3,
        "content": "<div class='flex-center'><div class='text-title'>Title</div></div>"
      },
      {
        "id": "s02",
        "start": 3,
        "duration": 5,
        "content": "<svg>...</svg>"
      }
    ]
  },
  "stage": "render",
  "mode": "companion-long"
}
```

**Scene Structure:**
```json
{
  "id": "unique_scene_id",
  "start": 0.0,
  "duration": 3.0,
  "content": "<html-or-svg-here>"
}
```

**Parameters:**
- `title` (string): Video title
- `scenes` (array): Array of scene objects
  - `id` (string): Unique scene identifier
  - `start` (float): Start time in seconds
  - `duration` (float): Scene duration in seconds
  - `content` (string): HTML/SVG markup

**Response (201 Created):**
```json
{
  "job_id": "1cfcbc2a-c052-4d68-8a15-241966f6cc5e",
  "status": "pending",
  "created_at": "2026-04-24T13:18:46.686434",
  "stage": "render",
  "topic_or_title": "Call Option Payoff"
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_json": {
      "title": "Options Example",
      "scenes": [
        {
          "id": "s01",
          "start": 0,
          "duration": 3,
          "content": "<div style=\"text-align:center; font-size:80px; color:#FFD700;\">Options 101</div>"
        }
      ]
    },
    "stage": "render"
  }'
```

---

### 4. List All Jobs
**Get a list of all submitted jobs.**

```
GET /jobs
```

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "job_id": "1cfcbc2a-c052-4d68-8a15-241966f6cc5e",
      "status": "failed",
      "created_at": "2026-04-24T13:18:46.686434",
      "stage": "render",
      "topic_or_title": "Call Option Payoff"
    },
    {
      "job_id": "f3135aca-690f-4271-aeb5-f6189545333a",
      "status": "running",
      "created_at": "2026-04-24T13:18:19.560639",
      "stage": "all",
      "topic_or_title": "call option payoff"
    }
  ]
}
```

**Response Fields:**
- `job_id`: Unique job identifier
- `status`: Current status (pending, running, complete, failed)
- `created_at`: ISO 8601 timestamp
- `stage`: Pipeline stage being executed
- `topic_or_title`: Topic string or video title

**Example:**
```bash
curl http://localhost:8080/jobs | python -m json.tool
```

---

### 5. Get Job Details
**Get detailed information about a specific job.**

```
GET /jobs/{job_id}
```

**Response (200 OK):**
```json
{
  "job_id": "be80736e-b4f9-4e03-8542-a7e1608d1ed3",
  "status": "failed",
  "created_at": "2026-04-24T11:32:59.021648",
  "stage": "all",
  "topic_or_title": "call option payoff diagram",
  "output_files": [],
  "error": "Scene content does not match the brief.\n  Coverage: 31% — expected at least 40%.",
  "elapsed_sec": 471.98
}
```

**Response Fields:**
- `job_id`: Job identifier
- `status`: One of: pending, running, complete, failed
- `created_at`: Job creation timestamp
- `stage`: Pipeline stage
- `topic_or_title`: Topic or title
- `output_files`: List of generated MP4 filenames
- `error`: Error message (null if no error)
- `elapsed_sec`: Seconds elapsed since job creation

**Status Meanings:**
- `pending` - Job created, waiting to start
- `running` - Job is currently executing
- `complete` - Job finished successfully, outputs ready
- `failed` - Job failed, check `error` field

**Example:**
```bash
curl http://localhost:8080/jobs/be80736e-b4f9-4e03-8542-a7e1608d1ed3 | python -m json.tool
```

---

### 6. Stream Job Logs (Server-Sent Events)
**Get real-time logs as the job executes.**

```
GET /jobs/{job_id}/logs
```

**Response (200 OK):**
- Content-Type: `text/event-stream`
- Connection: Keep-alive (streaming)

**Stream Format:**
```
data: "[STAGE] research: Starting research phase..."
data: "[STAGE] research: Searching for information..."
data: "[INFO] Generated 5 scenes"
data: "[STAGE] script: Building script..."
data: "[STAGE] render: Starting render..."
data: "[DONE]
```

**Each log line is a JSON string:**
```json
"[STAGE] research: Starting research phase..."
```

**Client Implementation (JavaScript):**
```javascript
const jobId = "be80736e-b4f9-4e03-8542-a7e1608d1ed3";
const eventSource = new EventSource(`/jobs/${jobId}/logs`);

eventSource.onmessage = (event) => {
  if (event.data === "[DONE]") {
    console.log("Job completed");
    eventSource.close();
  } else {
    console.log(event.data);
    // Update UI with log line
  }
};

eventSource.onerror = (error) => {
  console.error("Connection error:", error);
  eventSource.close();
};
```

**Client Implementation (Python):**
```python
import requests
import json

job_id = "be80736e-b4f9-4e03-8542-a7e1608d1ed3"
response = requests.get(f"http://localhost:8080/jobs/{job_id}/logs", stream=True)

for line in response.iter_lines():
    if line:
        data = line.decode('utf-8')
        if data.startswith('data: '):
            log_text = data[6:]  # Remove "data: " prefix
            if log_text == "[DONE]":
                print("Job completed")
                break
            print(log_text)
```

---

### 7. List Output Files
**Get list of generated output files for a completed job.**

```
GET /jobs/{job_id}/files
```

**Response (200 OK):**
```json
{
  "job_id": "1cfcbc2a-c052-4d68-8a15-241966f6cc5e",
  "output_files": [
    "call-payoff-video.mp4",
    "call-payoff-companion.mp4"
  ],
  "download_base": "/jobs/1cfcbc2a-c052-4d68-8a15-241966f6cc5e/files"
}
```

**Example:**
```bash
curl http://localhost:8080/jobs/1cfcbc2a-c052-4d68-8a15-241966f6cc5e/files
```

---

### 8. Download Output File
**Download a generated MP4 video file.**

```
GET /jobs/{job_id}/files/{filename}
```

**Response (200 OK):**
- Content-Type: `video/mp4`
- Content-Disposition: `attachment; filename="{filename}"`
- Binary MP4 data

**Example:**
```bash
# Download to current directory
curl -O http://localhost:8080/jobs/1cfcbc2a-c052-4d68-8a15-241966f6cc5e/files/output.mp4

# Download with custom name
curl http://localhost:8080/jobs/1cfcbc2a-c052-4d68-8a15-241966f6cc5e/files/output.mp4 \
  -o my-video.mp4
```

---

## Config Overrides

**Whitelisted configuration parameters you can override:**

```json
{
  "config_overrides": {
    "critic_enabled": true,
    "critic_max_attempts": 3,
    "critic_score_threshold": 0.7,
    "render_workers": 4,
    "renderer_max_retries": 2,
    "llm_retry_delay_sec": 2,
    "critic_retry_delay_sec": 5,
    "tts_enabled": false,
    "tts_voice": "alloy",
    "tts_speed": 1.0,
    "output_mode": "narrated",
    "block_degraded_output": false,
    "max_fallback_scene_ratio": 0.3,
    "llm_provider": "openai",
    "render_llm_provider": "openai",
    "script_chunk_size": 3
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "options basics",
    "config_overrides": {
      "tts_enabled": false,
      "critic_enabled": false,
      "render_workers": 2
    }
  }'
```

---

## Complete Workflow Examples

### Example 1: Generate Video from Topic (Full Pipeline)

```bash
#!/bin/bash

# 1. Submit job
JOB=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "call option payoff",
    "stage": "all",
    "skip_validation": true
  }')

JOB_ID=$(echo $JOB | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "Job created: $JOB_ID"

# 2. Poll for completion
while true; do
  STATUS=$(curl -s http://localhost:8080/jobs/$JOB_ID | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "Status: $STATUS"
  
  if [[ "$STATUS" == "complete" ]]; then
    echo "Job completed!"
    break
  elif [[ "$STATUS" == "failed" ]]; then
    echo "Job failed!"
    curl -s http://localhost:8080/jobs/$JOB_ID | grep -o '"error":"[^"]*"'
    exit 1
  fi
  
  sleep 10
done

# 3. Download output
curl -s http://localhost:8080/jobs/$JOB_ID/files | \
  grep -o '"output_files":\[[^]]*\]' | \
  grep -o '"[^"]*\.mp4"' | \
  sed 's/"//g' | \
  while read file; do
    curl -o "$file" "http://localhost:8080/jobs/$JOB_ID/files/$file"
    echo "Downloaded: $file"
  done
```

### Example 2: Stream Logs in Real-Time

```bash
#!/bin/bash

JOB_ID="be80736e-b4f9-4e03-8542-a7e1608d1ed3"

echo "Streaming logs for job $JOB_ID..."
curl -N http://localhost:8080/jobs/$JOB_ID/logs | while IFS= read -r line; do
  if [[ $line == data:* ]]; then
    # Extract and print log text
    echo "${line:6}"
  fi
done
```

### Example 3: Python Integration

```python
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def create_video_job(topic, skip_validation=False):
    """Submit a video generation job."""
    response = requests.post(
        f"{BASE_URL}/jobs",
        json={
            "topic": topic,
            "stage": "all",
            "skip_validation": skip_validation
        }
    )
    response.raise_for_status()
    return response.json()["job_id"]

def wait_for_job(job_id, timeout=3600):
    """Wait for job to complete."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        job = response.json()
        
        if job["status"] == "complete":
            return True, job
        elif job["status"] == "failed":
            return False, job
        
        print(f"Status: {job['status']} (elapsed: {job['elapsed_sec']:.1f}s)")
        time.sleep(5)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

def download_output(job_id, filename, output_path):
    """Download output video file."""
    url = f"{BASE_URL}/jobs/{job_id}/files/{filename}"
    response = requests.get(url, stream=True)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded: {output_path}")

# Usage
job_id = create_video_job("bull call spread options")
print(f"Job ID: {job_id}")

success, job_data = wait_for_job(job_id)

if success:
    print(f"Job completed in {job_data['elapsed_sec']:.1f} seconds")
    print(f"Output files: {job_data['output_files']}")
    
    for filename in job_data['output_files']:
        download_output(job_id, filename, f"./{filename}")
else:
    print(f"Job failed: {job_data['error']}")
```

---

## Error Handling

**Common Error Responses:**

### 400 Bad Request
```json
{
  "detail": "Missing required field: topic"
}
```

### 404 Not Found
```json
{
  "detail": "Job not found: invalid-job-id"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

**Job-Level Errors:**
When a job fails, check the `error` field in the job detail response:

```json
{
  "status": "failed",
  "error": "Scene content does not match the brief.\n  Coverage: 31% — expected at least 40%.\n  Regenerate the scene script..."
}
```

---

## Rate Limits & Timeouts

- **Concurrent Jobs:** 2 (thread pool limited)
- **Job Timeout:** 10 minutes max per stage
- **Request Timeout:** 30 seconds (increase if needed)
- **Log Stream Timeout:** 300 seconds of inactivity closes connection

---

## Web UI Usage

**Alternative to API:** Use the web UI at `http://localhost:8080`

Features:
- Submit jobs via form (topic or JSON paste)
- Stream logs in real-time
- View job history with status badges
- Download output files
- Auto-refresh every 5 seconds

---

## Deployment Notes

**For Production:**

1. Change to multi-worker deployment (modify `api_server.py`):
   ```python
   uvicorn.run("api.server:app", host="0.0.0.0", port=8080, workers=4)
   ```

2. Add authentication (implement in `server.py`):
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```

3. Add database for job persistence (replace in-memory store)

4. Configure reverse proxy (nginx) for TLS/SSL

5. Set up monitoring/logging:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       handlers=[
           logging.FileHandler("api.log"),
           logging.StreamHandler()
       ]
   )
   ```

---

## Support

**Check Server Status:**
```bash
curl http://localhost:8080/health
```

**View Recent Jobs:**
```bash
curl http://localhost:8080/jobs | python -m json.tool | head -50
```

**Stop Server:**
```bash
pkill -f "api_server.py"
```

**Restart Server:**
```bash
pkill -f "api_server.py"
python /Users/amitri/Projects/LTX-Video/video-pipeline/api_server.py
```
