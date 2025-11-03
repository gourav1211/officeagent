# Rebuild Plan: Office AI Agent (Backend + Desktop)

This plan defines the step-by-step sequence to rebuild the Office AI Agent from scratch on Windows, strictly following the docs under `docs/`. We will execute one step at a time, validating each milestone before moving on. The Electron/Vite frontend is intentionally excluded.

- Scope: Python package `office_ai_agent` (orchestrator, agents, tools, utils), FastAPI server, Tkinter desktop app, and office file workspace.
- Exclusions: Electron/Vite/TypeScript UI. CLI is optional and not planned unless requested.
- Runtime target: Windows 10/11, Python 3.10–3.11.

## Execution protocol

- We will proceed in numbered steps. After each step, we will validate acceptance criteria ("green before next").
- PowerShell commands are provided for Windows (`pwsh.exe`).
- We’ll preserve public contracts and tool names as described in the docs.

## Milestones overview

1) Scaffold project structure and dependencies
2) Utils foundation: file manager, logger, metrics
3) Tools: simple file-producing tools + registry and orchestrator helpers
4) Config system (env + dataclasses)
5) Orchestrator core (heuristic planner + Gemini integration path) + execute/streaming contract
6) Specialized agents (document, presentation, spreadsheet, communication, workflow)
7) FastAPI server (endpoints + SSE)
8) Desktop app (Tkinter GUI) + launcher
9) Dependency pinning and requirements finalization
10) Quality gates (black/isort/flake8, optional mypy) + smoke tests (pytest)
11) Optional packaging (setup.py) and console entry points
12) Optional deployment notes (container/server)
13) Docs polish and handoff

---

## Step 1 — Scaffold project structure and dependencies

Objectives
- Create directory layout, placeholder modules, and minimal `__init__.py` so the package imports.
- Add `requirements.txt`, `requirements_office.txt`, `requirements_server.txt` with initial dependencies (to be refined in Step 9).
- Add `launcher.py` placeholder.

Tasks
- Create folders/files per docs:
  - `office_ai_agent/` with subfolders: `core/`, `agents/`, `tools/`, `utils/` and files: `desktop_app.py`, `server.py`, `__init__.py`.
  - Placeholders in each module with TODO markers.
  - `office_ai_files/` will be auto-created by FileManager later—do not commit empty.
- Add initial dependency files:
  - `requirements.txt`: full stack (LangChain, FastAPI, Uvicorn, Office libs, dotenv, httpx, typing extras, tooling).
  - `requirements_server.txt`: server-only minimal set.
  - `requirements_office.txt`: `python-docx`, `python-pptx`, `openpyxl`.

Acceptance criteria
- `python -c "import office_ai_agent; print('ok')"` runs without ImportError (placeholders allowed).

Try it
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
# We will fill requirements in Step 9; for now just verify importability without installs
python -c "import sys; print(sys.version)"
python -c "import importlib; importlib.import_module('office_ai_agent'); print('ok')"
```

Notes
- No behavior yet. This is structural scaffolding only.

---

## Step 2 — Utils foundation (file manager, logger, metrics)

Objectives
- Implement `utils/file_manager.py` to create and manage `office_ai_files/` structure; support DOCX/PPTX/XLSX when libs present, else `.txt` fallbacks.
- Implement `utils/logger.py` for structured logging respecting `LOG_LEVEL`.
- Implement `utils/metrics.py` for in-process metrics and JSON snapshot.

Tasks
- FileManager: ensure directories `documents/`, `presentations/`, `spreadsheets/`, `templates/`, `exports/` are created on init; implement save methods with fallbacks.
- Logger: basic logger factory; optional file handler via config; sensible format.
- Metrics: simple counters/timers; export method used by server `/metrics`.

Acceptance criteria
- Running small local script that uses FileManager to create a document/presentation/spreadsheet yields files in `office_ai_files/*` with `.txt` fallback if office libs absent.

Try it
```powershell
python - <<'PY'
from office_ai_agent.utils.file_manager import FileManager
fm = FileManager()
print(fm.save_text_document('demo_doc', 'Hello'))
print(fm.save_text_presentation('demo_pres', ["Slide 1", "Slide 2"]))
print(fm.save_text_spreadsheet('demo_sheet', [["A","B"],[1,2]]))
PY
```

Notes
- This step enables observable outputs without LLMs.

---

## Step 3 — Tools: simple file-producing tools + registry + orchestrator helpers

Objectives
- Implement `tools/simple_tools.py` with create/save document/presentation/spreadsheet tools and FS helpers (list_files, get_file_info, create_folder).
- Implement `tools/office_tools.py` registry that registers those tools.
- Implement `tools/orchestrator_tools.py` with `delegate_to_agent` and basic status helpers (stubs OK for now).

Tasks
- Use LangChain tool decorators where appropriate; ensure return values are JSON-serializable dicts with `status`.
- Ensure tool names match docs: `create_document`, `add_heading`, `add_paragraph`, `save_document`, `create_presentation`, `add_slide`, `add_text_to_slide`, `save_presentation`, `create_workbook`, `write_cell`, `save_workbook`, `list_files`, `get_file_info`, `create_folder`.

Acceptance criteria
- Importing registry returns expected tool list.
- Direct invocation of at least one tool yields a file in `office_ai_files/`.

Try it
```powershell
python - <<'PY'
from office_ai_agent.tools.office_tools import OfficeToolRegistry
reg = OfficeToolRegistry()
print([t.name for t in reg.get_all_tools()][:5])
PY
```

Notes
- Keep operations quick and deterministic; avoid blocking IO.

---

## Step 4 — Config system (env + dataclasses)

Objectives
- Implement `core/config.py` with dataclasses for LLM, office toggles, UI/server, monitoring, misc.
- Env var loading, defaults, validation, optional JSON persistence.

Tasks
- Respect variables in docs: `GEMINI_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`, `ENABLE_POWERPOINT`, `ENABLE_WORD`, `ENABLE_EXCEL`, `ENABLE_OUTLOOK`, `ENABLE_TEAMS`, `API_PORT`, `WEB_PORT`(ignored by server), `LOG_LEVEL`, `SENTRY_DSN`, `DEBUG`, `DEVELOPMENT`.
- Implement `Config.load()` and `Config.save_config(path)`.

Acceptance criteria
- `Config.load()` reflects env values and sensible defaults; invalid values raise clear errors.

Try it
```powershell
$env:LLM_PROVIDER = 'gemini'
python - <<'PY'
from office_ai_agent.core.config import Config
cfg = Config.load()
print(cfg)
PY
```

Notes
- LLM key validation can be deferred to orchestrator init.

---

## Step 5 — Orchestrator core (heuristic planner + Gemini path)

Objectives
- Implement `core/agent_orchestrator.py` with `OfficeAIAgent` using LangChain tools agent pattern.
- Expose `execute(task, context=None, user_id=None, task_id=None) -> dict` and `execute_streaming(...)`.

Tasks
- Prepare LLM (Gemini) per env; use deterministic plan until LLM is available.
- Assemble tools from `OfficeToolRegistry` and agents (step 6 fleshes out specialized agents; before that, orchestrator can still run basic tools).
- Track status, metrics, execution history.

Acceptance criteria
- With `GEMINI_API_KEY` set (optional for deterministic mode), calling `execute` on a simple task succeeds and produces a file via tools.
- Streaming returns incremental chunks (minimally implemented is fine).

Try it
```powershell
python - <<'PY'
from office_ai_agent.core.agent_orchestrator import OfficeAIAgent
from office_ai_agent.core.config import Config
agent = OfficeAIAgent(Config.load())
print(agent.execute('Create a short test document'))
PY
```

Notes
- For offline dev, we may add a `DRY_RUN` env to bypass LLM and invoke a default plan; optional.

---

## Step 6 — Specialized agents

Objectives
- Implement `agents/base_agent.py` and the five agents: `document_agent.py`, `presentation_agent.py`, `spreadsheet_agent.py`, `communication_agent.py`, `workflow_agent.py`.
- Each defines `_initialize_tools()` and `_get_system_prompt()`; expose `execute` and `execute_streaming`.

Tasks
- Register agents in orchestrator `_initialize_agents()` and optional enum `AgentType` in config.
- Keep prompts scoped and practical per app (Word/PowerPoint/Excel responsibilities).

Acceptance criteria
- Orchestrator can delegate tasks to a specific agent and produce corresponding files.

Try it
```powershell
python - <<'PY'
from office_ai_agent.core.agent_orchestrator import OfficeAIAgent
from office_ai_agent.core.config import Config
agent = OfficeAIAgent(Config.load())
print(agent.execute('Create a 2-slide presentation about ROI'))
PY
```

Notes
- Ensure tool names referenced in prompts match registered names.

---

## Step 7 — FastAPI server (REST + SSE)

Objectives
- Implement `office_ai_agent/server.py` with endpoints:
  - POST `/execute`
  - GET `/execute_stream` (SSE)
  - GET `/agents`
  - GET `/metrics`
  - GET `/status/{task_id}`
- Provide `run(host, port)` function and module entry (`python -m office_ai_agent.server`).

Tasks
- Pydantic models: `ExecuteRequest{task, context?, user_id?, task_id?}`.
- Wire CORS for localhost dev; wire metrics export.

Acceptance criteria
- Server starts and endpoints function.

Try it
```powershell
python -m office_ai_agent.server
# In another shell
$body = @{ task = 'Create a 3-slide presentation about Q4 sales' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/execute -Body $body -ContentType 'application/json'
```

Notes
- SSE test snippet available in docs via `httpx.stream`.

---

## Step 8 — Desktop app (Tkinter) + launcher

Objectives
- Implement `desktop_app.py` with a simple, responsive UI for task input, status, and metrics.
- Add `launcher.py` at repo root to start the desktop app.

Tasks
- Ensure long operations don’t block UI thread (threads/async where needed).

Acceptance criteria
- `python .\launcher.py` opens the UI and can run a basic task, producing an output file.

---

## Step 9 — Finalize dependencies and pin versions

Objectives
- Populate `requirements*.txt` with tested pins for Python 3.10–3.11.

Tasks
- requirements.txt (full): langchain, google-generativeai, langchain-google-genai, fastapi, uvicorn[standard], python-docx, python-pptx, openpyxl, httpx, pydantic, python-dotenv, typing-extensions, black, isort, flake8, pytest.
- requirements_server.txt: fastapi, uvicorn[standard], langchain, google-generativeai, langchain-google-genai, httpx, pydantic, python-dotenv.
- requirements_office.txt: python-docx, python-pptx, openpyxl.

Acceptance criteria
- Fresh venv can install dependencies and run server + desktop successfully.

Try it
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m office_ai_agent.server
```

Notes
- We’ll adapt pins if any incompatibilities arise on the target machine.

---

## Step 10 — Quality gates and smoke tests

Objectives
- Add basic lint/type/test configuration and a few smoke tests.

Tasks
- Run: `black .`, `isort .`, `flake8 .`; optional `mypy office_ai_agent`.
- Add `tests/` with 2–3 smoke tests (FileManager saves, a tool call works, server /agents responds).

Acceptance criteria
- Lint passes; tests pass on fresh venv.

---

## Step 11 — Optional packaging

Objectives
- Provide `setup.py` (or pyproject) with console entry points if desired.

Tasks
- Entry points (optional):
  - `office-ai-agent` → `office_ai_agent.desktop_app:main`

Acceptance criteria
- `py -m build` produces a wheel; `pip install -e .` works locally.

---

## Step 12 — Optional deployment notes

- Containerize server: `python:3.11-slim`, copy code and `requirements_server.txt`, expose 8765, entry `python -m office_ai_agent.server`.
- Secrets via environment; persist `office_ai_files/`.
- If exposing publicly, put a proxy/gateway and add auth.

---

## Step 13 — Docs polish and handoff

- Ensure root `README.md` and `docs/` references align with rebuilt code.
- Include troubleshooting and examples.

---

## Tracking checklist

- [x] Step 1 — Scaffold project structure and dependencies
- [x] Step 2 — Utils foundation (file manager, logger, metrics)
- [x] Step 3 — Tools (simple + registry + orchestrator helpers)
- [x] Step 4 — Config system
- [x] Step 5 — Orchestrator core
- [x] Step 6 — Specialized agents
- [x] Step 7 — FastAPI server
- [ ] Step 8 — Desktop app + launcher
- [ ] Step 9 — Finalize dependencies and pins
- [ ] Step 10 — Quality gates + smoke tests
- [ ] Step 11 — Optional packaging
- [ ] Step 12 — Optional deployment notes
- [ ] Step 13 — Docs polish and handoff

## Assumptions
- LLM provider: Gemini only; set GEMINI_API_KEY for LLM-generated content (deterministic fallbacks still produce files without it).
- Tkinter available on Windows Python distribution.
- We will keep tool names stable as documented to maintain prompt compatibility.

## Risks and mitigations
- Package version conflicts: mitigate by pinning and adjusting based on install errors.
- LLM key availability: provide clear error on startup if missing; allow offline testing for utils/tools where feasible.
- UI thread blocking: use threads/async for long operations.
