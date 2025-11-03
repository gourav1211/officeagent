# API: FastAPI Server

The server exposes endpoints to execute tasks via the orchestrator and read system status. Default port in examples is 8765.

## Start the server

```powershell
# From the project root with venv activated
python -m office_ai_agent.server
```

If you need a custom port or host, run:

```powershell
python -c "from office_ai_agent.server import run; run(host='127.0.0.1', port=8765)"
```

## Endpoints

- POST `/execute` — start a task
- GET `/execute_stream` — Server-Sent Events (SSE) streaming for live updates
- GET `/agents` — list available agents
- GET `/metrics` — metrics snapshot
- GET `/status/{task_id}` — status of a task started earlier

### Models

Request body for POST `/execute`:

```json
{
  "task": "Create a 3-slide presentation about Q4 sales",
  "context": {"title": "Q4 Sales"},
  "user_id": "user-123",
  "task_id": "optional-custom-id"
}
```

Response example:

```json
{
  "task_id": "task_20250101_120000_123456",
  "status": "completed",
  "result": {"...": "agent/tool output"},
  "execution_time": 1.23
}
```

### PowerShell examples

Because `curl` in PowerShell maps to `Invoke-WebRequest`, we’ll use `Invoke-RestMethod` for clarity.

- Execute a task:

```powershell
$body = @{ task = "Create a 3-slide presentation about Q4 sales" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/execute -Body $body -ContentType 'application/json'
```

- Check agents:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8765/agents
```

- Check metrics:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8765/metrics
```

- Check task status:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8765/status/task_2025...
```

### Streaming (SSE)

SSE returns text/event-stream. You can test it with a small Python client (recommended):

```python
import httpx

with httpx.stream("GET", "http://127.0.0.1:8765/execute_stream", params={"task": "Create a 2-slide presentation about ROI"}) as r:
    for line in r.iter_lines():
        if line and line.startswith(b"data: "):
            print(line[6:].decode())
```

Query parameters:
- `task` (required)
- `context` (optional JSON string)
- `user_id`, `task_id` (optional)

CORS: The app allows localhost:5173 origins for development, but we’re not using Electron here.

LLM provider
- The backend uses Gemini. Ensure `GEMINI_API_KEY` is set before starting the server.
