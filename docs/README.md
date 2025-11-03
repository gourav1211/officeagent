# Rebuild Guide: Office AI Agent (Backend + Desktop)

This guide lets you rebuild the entire Office AI Agent backend and desktop app from scratch on Windows, preserving all functionality except the Electron frontend (intentionally excluded as requested).

- What you get: multi-agent orchestrator (LangChain), FastAPI server, Tkinter desktop UI, Office file generation (DOCX/PPTX/XLSX or text fallbacks), metrics/logging, and the office file workspace.
- What’s not included here: the Electron/Vite/TypeScript UI. Use the desktop app or REST API instead.

If you follow this folder’s READMEs top-to-bottom, you can recreate the project without referring to the original source.
For additional high-level context and feature descriptions, see the repository root `README.md`.

## Contents

- Architecture overview
- Prerequisites (Windows, Python, API keys)
- Project layout to recreate
- Environment setup (PowerShell)
- Build and run (desktop and server)
- Configuration reference (env vars)
- Verification checklist

## Architecture Overview

Components:
- Core orchestrator: `OfficeAIAgent` (LangChain) delegates to specialized agents and tools.
- Specialized agents: document, presentation, spreadsheet, communication, workflow.
- Tools: an Office tool registry exposing simple, concrete file operations (create/save docs, presentations, spreadsheets) plus orchestrator helpers.
- Desktop app (Tkinter): simple, full-featured GUI for task input, agent overview, metrics, and config display.
- FastAPI server: REST endpoints for execute, status, metrics, and SSE streaming.
- File workspace: `office_ai_files/` where generated DOCX/PPTX/XLSX (or .txt fallbacks) are saved.

Notes and constraints:
- LLM provider: Gemini (Google). A GEMINI_API_KEY is required; otherwise the app won’t start.
- Office integration is implemented via Python libraries (python-docx, python-pptx, openpyxl). If a library is missing, the system falls back to .txt generation so you still get useful files.

## Prerequisites

- Windows 10/11
- Python 3.10 – 3.11 recommended
- OpenAI API key (required) and optionally Anthropic API key
- PowerShell (this guide uses PowerShell commands)

Optional packages that improve output quality:
- python-docx (DOCX)
- python-pptx (PPTX)
- openpyxl (XLSX)

All are covered by the provided requirements files.

## Project Layout To Recreate

Create this structure (see each sub-README for details):

- `launcher.py` – desktop entry point
- `requirements.txt`, `requirements_office.txt`, `requirements_server.txt` – dependency sets
- `setup.py` – packaging entry points (optional for rebuild)
- `office_ai_agent/` – Python package
  - `core/` – orchestrator and config
  - `agents/` – specialized agents
  - `tools/` – tool registry and concrete tools
  - `utils/` – logger, metrics, file manager
  - `server.py` – FastAPI app
  - `desktop_app.py` – Tkinter UI
- `office_ai_files/` – output workspace for generated files (auto-created)

Frontend note: the original repo contains `electron_app/`; per your instruction, skip rebuilding it.

## Environment Setup (PowerShell)

1) Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

- Full desktop + server + office libs

```powershell
pip install -r requirements.txt
```

- Minimal server only (optional)

```powershell
pip install -r requirements_server.txt
```

3) Set required environment variables

```powershell
# REQUIRED
$env:GEMINI_API_KEY = "your-gemini-api-key"

# OPTIONAL
$env:LLM_PROVIDER = "gemini"
$env:LLM_MODEL = "gemini-1.5-pro"
$env:LLM_TEMPERATURE = "0.7"
$env:ENABLE_POWERPOINT = "true"
$env:ENABLE_WORD = "true"
$env:ENABLE_EXCEL = "true"
$env:LOG_LEVEL = "INFO"             # DEBUG, INFO, WARNING, ERROR
$env:WEB_PORT = "8000"              # not used by FastAPI here
$env:API_PORT = "8765"              # FastAPI will run on this if you use server.run
```

Tip: You can create a `.env` file and the app will load it automatically if `python-dotenv` is installed.

## Build and Run

- Desktop app (recommended for local use)

```powershell
python .\launcher.py
```

- API server (FastAPI + Uvicorn)

```powershell
python -m office_ai_agent.server
# or
python -c "from office_ai_agent.server import run; run(host='127.0.0.1', port=8765)"
```

Endpoints are described in `docs/api/README.md`.

## Configuration Reference (quick)

See `docs/operations/README.md` for a complete list. Key variables:
- GEMINI_API_KEY: required for LLM init.
- LLM_PROVIDER: gemini (default).
- LLM_MODEL, LLM_TEMPERATURE: model tuning.
- ENABLE_POWERPOINT/WORD/EXCEL: enable/disable agent toolsets.
- LOG_LEVEL: DEBUG|INFO|WARNING|ERROR|CRITICAL.
- API_PORT: server port; desktop app doesn’t use it directly.

## Verify Your Rebuild

- Launch desktop app; the UI should open and show "Ready". If you see an API key error panel, set OPENAI_API_KEY (or ANTHROPIC_API_KEY) and restart.
- Run a simple task, like: "Create a 3-slide presentation about Q4 sales." Check `office_ai_files/presentations/` for the saved file.
- Start the server and POST to `/execute`; confirm you get a JSON result and a file created in `office_ai_files/`.

If anything’s unclear, the sub-READMEs walk through every component in detail.
