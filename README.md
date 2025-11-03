# Office AI Agent (Backend + Desktop)

A Windows-friendly Office AI Agent that generates Word, PowerPoint, and Excel files. It offers:
- A desktop app (Tkinter) for quick local use
- A FastAPI server for REST access and streaming updates (SSE)
- Multi-agent orchestration with Gemini (Google) and deterministic fallbacks

This README is the practical getting-started guide for running the software on your machine.

## Prerequisites

- Windows 10/11
- Python 3.10 or 3.11
- PowerShell
- Gemini API key (recommended for LLM-generated content)

Note: The system will still create files even without an API key, using deterministic content.

## Quick start

1) Clone and enter the project

```powershell
# Replace with your repository URL
git clone <your-repo-url>.git
cd officeagent
```

2) Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Install dependencies

```powershell
pip install -r requirements.txt
```

4) Set environment variables (or create a .env)

Create a `.env` file in the project root with at least:

```
GEMINI_API_KEY=your-gemini-api-key
LLM_PROVIDER=gemini
# Default model (recommended):
LLM_MODEL=gemini-2.5-flash
# or another supported model:
# LLM_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.7

# Feature toggles
ENABLE_POWERPOINT=true
ENABLE_WORD=true
ENABLE_EXCEL=true
```

Alternatively, you can set these in the shell:

```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
$env:LLM_PROVIDER = 'gemini'
$env:LLM_MODEL = 'gemini-2.5-flash'
$env:LLM_TEMPERATURE = '0.7'
```

## Run the desktop app

```powershell
python .\launcher.py
```

- Enter a task like: "Create a 3-slide presentation about Q4 sales" and pick "presentation" agent (or leave Auto).
- Files are saved under `office_ai_files/`.

## Run the API server

```powershell
python -m office_ai_agent.server
```

Endpoints (default port 8765):
- POST `/execute` — start a task
- GET `/execute_stream` — Server-Sent Events (SSE) updates
- GET `/agents` — list available agents
- GET `/metrics` — metrics snapshot
- GET `/status/{task_id}` — status of a previously started task

Example (PowerShell):

```powershell
$body = @{ task = "Create a 2-slide presentation about ROI"; context = @{ agent = "presentation" } } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/execute -Body $body -ContentType 'application/json'
```

### Streaming example (Python)

```python
import httpx

with httpx.stream("GET", "http://127.0.0.1:8765/execute_stream", params={"task": "Create a 2-slide presentation about ROI"}) as r:
    for line in r.iter_lines():
        if line and line.startswith(b"data: "):
            print(line[6:].decode())
```

## Sample tasks

- Presentation: "Create a 4-slide presentation about oranges with clear bullet points"
- Document: "Create a one-page document about oranges nutrition facts with clear sections and bullets"
- Spreadsheet: "Create a spreadsheet with 3 columns (Variety, Price, Region) and 5 rows about orange varieties"

## Project structure (key parts)

```
office_ai_agent/
  core/                # orchestrator (OfficeAIAgent) + config
  agents/              # document, presentation, spreadsheet, communication, workflow
  tools/               # office file tools and registry
  utils/               # file manager, logger, metrics
  server.py            # FastAPI app
  desktop_app.py       # Tkinter UI
launcher.py            # desktop app launcher
requirements*.txt      # pinned dependencies
office_ai_files/       # generated outputs (ignored by git)
```

## Troubleshooting

- No PPTX/DOCX/XLSX created?
  - Ensure python-pptx/python-docx/openpyxl are installed (in requirements.txt). The app falls back to .txt if these are missing.
- No LLM content in outputs?
  - Set `GEMINI_API_KEY` and choose a valid `LLM_MODEL`.
- Server exits immediately?
  - Make sure you’re not running another command in the same terminal after launching. Use a second terminal to call the API.

## Preparing to push to GitHub

This repo includes a `.gitignore` that excludes venvs, caches, local config (like `.env`), and generated files (`office_ai_files/`).

Typical first push:

```powershell
git init
git add .
git commit -m "Initial commit: Office AI Agent"
# Replace with your remote URL
git branch -M main
git remote add origin https://github.com/<your-org-or-user>/<your-repo>.git
git push -u origin main
```

## Notes

- See the `docs/` folder for detailed component READMEs.
- This README focuses on running the software locally and pushing to GitHub without leaking secrets.
