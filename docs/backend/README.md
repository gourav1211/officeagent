# Backend: Package, Modules, and Build

This document explains how to recreate the Python backend package (`office_ai_agent`) from scratch, including modules, dependencies, and packaging.

## Package Layout

```
office_ai_agent/
  __init__.py            # exports OfficeAIAgent, Config, agent classes
  desktop_app.py         # Tkinter desktop GUI entry
  server.py              # FastAPI server app
  core/
    agent_orchestrator.py
    config.py
  agents/
    base_agent.py
    document_agent.py
    presentation_agent.py
    spreadsheet_agent.py
    communication_agent.py
    workflow_agent.py
  tools/
    office_tools.py
    orchestrator_tools.py
    simple_tools.py
  utils/
    file_manager.py
    logger.py
    metrics.py
```

## Responsibilities

- `core/agent_orchestrator.py` — wires LangChain LLM + agents + tools, exposes `OfficeAIAgent.execute()` and streaming.
- `core/config.py` — config dataclasses, env var loading, validation, and persistence.
- `agents/*` — 5 specialized agents inheriting from `BaseOfficeAgent`; each declares a system prompt and selects tools.
- `tools/office_tools.py` — central registry; currently registers a set of concrete simple tools for file generation.
- `tools/simple_tools.py` — file-creating tools that rely on `utils/file_manager.py`.
- `tools/orchestrator_tools.py` — delegation helpers and status utilities used by the orchestrator.
- `utils/logger.py`, `utils/metrics.py` — structured logging and lightweight metrics; `utils/file_manager.py` handles directory structure and file saving with docx/pptx/xlsx fallbacks.
- `server.py` — FastAPI app to expose `/execute`, `/execute_stream`, `/agents`, `/metrics`, `/status/{task_id}`.
- `desktop_app.py` — modern-styled Tkinter UI that calls the orchestrator directly.

## Dependencies

Use `requirements.txt` for the complete environment (LLM + Office libs + FastAPI + desktop extras). Minimal sets:
- `requirements_server.txt` — run just the API server.
- `requirements_office.txt` — Office file libraries (improve quality of outputs).

LLM provider: Gemini (Google). Recommended packages:
- `google-generativeai` (Gemini client)
- `langchain-google-genai` (LangChain integration for Gemini)

Python versions tested: 3.10–3.11 recommended. Some packages may not support latest nightly 3.12.

## Packaging (optional)

`setup.py` includes console entry points:
- `office-ai-agent` → `office_ai_agent.desktop_app:main`
- `office-ai-cli` → `office_ai_agent.cli:main` (CLI module isn’t included in code; omit or add a CLI before using.)

To build a wheel (optional):

```powershell
pip install build
py -m build
```

To install locally in editable mode during development:

```powershell
pip install -e .
```

## Recreating From Scratch

1) Create directories and files per the layout above.
2) Copy module contents or implement equivalents following the public interfaces shown in this doc.
3) Ensure the following runtime contract is preserved:
   - `OfficeAIAgent(config).execute(task, context?, user_id?, task_id?) -> dict`
   - FastAPI app exposes the same routes and pydantic model `ExecuteRequest{task, context?, user_id?, task_id?}`
   - Desktop app `main()` creates a window, runs tasks, and writes outputs to `office_ai_files/`
4) Keep tool names stable (e.g., `create_presentation`, `save_document`, `save_workbook`) so prompts/agents remain compatible.

## Notes on LLM Integration

- The orchestrator uses LangChain’s tools-agent pattern with Gemini via `langchain-google-genai`.
- Select the model via environment (`LLM_MODEL`, e.g., `gemini-1.5-pro`).

## Notes

- The orchestrator and agents use LangChain’s tools-agent pattern. Prompts are in each agent class.
- Tool implementations in `office_tools.py` are mostly placeholders that call into `file_manager.py`; they are enough to produce real files.
- If docx/pptx/xlsx libraries are missing, `file_manager.py` saves `.txt` files with structured content so behavior remains useful.
