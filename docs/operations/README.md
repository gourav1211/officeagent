# Operations: Running, Config, and Files

This document covers day-to-day operations: running the desktop app or server, environment configuration, and where files go.

## Running modes

- Desktop GUI (Tkinter): local, simple UI

```powershell
python .\launcher.py
```

- API Server (FastAPI + Uvicorn)

```powershell
python -m office_ai_agent.server
```

## Environment configuration

`core/config.py` loads settings from env vars and optional JSON config files. Important variables:

- LLM (Gemini)
  - `GEMINI_API_KEY` (required)
  - `LLM_PROVIDER` (default `gemini`)
  - `LLM_MODEL` (default `gemini-1.5-pro`)
  - `LLM_TEMPERATURE` (float, default 0.7)

- Office toggles
  - `ENABLE_POWERPOINT` (true/false)
  - `ENABLE_WORD` (true/false)
  - `ENABLE_EXCEL` (true/false)
  - `ENABLE_OUTLOOK` (false by default)
  - `ENABLE_TEAMS` (false by default)

- UI/Server
  - `API_PORT` (e.g., 8765)
  - `WEB_PORT` (not used by server.py; safe to ignore)

- Monitoring
  - `LOG_LEVEL` (DEBUG|INFO|WARNING|ERROR|CRITICAL)
  - `SENTRY_DSN` (optional)

- Misc
  - `DEBUG` (true/false)
  - `DEVELOPMENT` (true/false)

You can also save a JSON config via `Config.save_config(...)`. The loader searches:
- `config.json` in the CWD
- `office_ai_agent.json` in the CWD
- `%USERPROFILE%\.office_ai_agent\config.json`

## Files and directories

Generated outputs live under `office_ai_files/` in the project root. Subfolders:
- `documents/` — DOCX or TXT
- `presentations/` — PPTX or TXT
- `spreadsheets/` — XLSX or TXT
- `templates/` — reserved for future use
- `exports/` — reserved for exports

`utils/file_manager.py` creates this structure automatically and ensures reasonable fallbacks.

## Common tasks

- Create a document via desktop app: enter a task like "Create a project proposal document" and press "Execute Task".
- Create a presentation via API: POST `/execute` with task "Create a 5-slide presentation about OKRs".
- Inspect results: check `office_ai_files/...` folders.
- Rotate logs: set a log file in `Config.monitoring.log_file` and use `LogLevel` as needed.

## Troubleshooting

- "LLM API key is required": set `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) and restart.
- Can’t create DOCX/PPTX/XLSX: ensure `python-docx`, `python-pptx`, and `openpyxl` are installed; otherwise you’ll see `.txt` outputs (intended fallback).
- Port in use: choose a different port in `run(host, port)` when starting the server.
