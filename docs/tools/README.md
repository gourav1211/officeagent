# Tools: Registry and Concrete Implementations

Tools are LangChain `BaseTool` functions registered in `OfficeToolRegistry`. They power document/presentation/spreadsheet creation and orchestrator helpers.

## Where tools live

- `tools/office_tools.py` — central registry; currently calls `_register_simple_tools()` which imports from `tools/simple_tools.py`.
- `tools/simple_tools.py` — concrete file-producing tools (create/save doc/pres/sheet, list files, etc.).
- `tools/orchestrator_tools.py` — meta-tools (delegate_to_agent, get_agent_status, etc.).

## Simple tools (file-producing)

Key tool names you can rely on:
- Document: `create_document`, `add_heading`, `add_paragraph`, `save_document`
- Presentation: `create_presentation`, `add_slide`, `add_text_to_slide`, `save_presentation`
- Spreadsheet: `create_workbook`, `write_cell`, `save_workbook`
- Filesystem helpers: `list_files`, `get_file_info`, `create_folder`

These call `utils/file_manager.py` to write files into `office_ai_files/` with proper formats when libraries are installed, or `.txt` fallbacks otherwise.

## Orchestrator tools

- `delegate_to_agent(agent_type, task, context?)` — a convenience function that synthesizes a minimal real workflow and returns saved file paths (great for demos/tests).
- `get_available_agents`, `get_agent_status`, `get_task_progress`, `cancel_task` — lightweight utilities to aid planning and status.

## Adding tools

1) Implement a function and decorate it with `@tool` (LangChain) or wrap it using `tool(name=..., description=...)(func)`.
2) Register it in `OfficeToolRegistry` using `_register_tool(...)` and place it into an appropriate category.
3) Reference the tool name in the relevant agent’s `_initialize_tools()` list.

## Behavior and contracts

- Tools return a JSON-serializable dict with at least `status` and any useful fields (e.g., `file_path`).
- Avoid blocking calls; prefer quick, deterministic behavior.
- Error handling: return `{"status": "error", "error": "..."}` when something fails.
