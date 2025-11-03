# Development: Workflow, Testing, and Quality

This repo ships without a formal test suite, but the dependencies include pytest should you add tests. Here’s how to work effectively on this codebase.

## Environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Code style

- Follow PEP8; optional tools included: black, isort, flake8, mypy

```powershell
black .
isort .
flake8 .
# Optional type check (may require additional stubs):
mypy office_ai_agent
```

## Adding features

- New tools → implement in `tools/*`, register in `OfficeToolRegistry`, reference by name in an agent.
- New agent → subclass `BaseOfficeAgent`, add to `AgentType` and orchestrator `_initialize_agents()`.
- Config → extend dataclasses in `core/config.py`; respect env loading/validation.

## Manual testing

- Desktop: run a task and verify new files in `office_ai_files/`.
- API: POST to `/execute` and confirm result JSON and file output.

## Packaging

Optional, for distribution:

```powershell
pip install build
py -m build
```

## Notes

- Avoid changing public tool names; prompts and orchestrator expect them.
- Keep long-running operations off the UI thread in `desktop_app.py`.
