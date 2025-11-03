# Data and File Workspace

All generated files go into `office_ai_files/` at the project root. This folder is part of the app’s runtime state and safe to version-control or ignore depending on your workflow.

## Structure

```
office_ai_files/
  documents/
  presentations/
  spreadsheets/
  templates/
  exports/
```

`utils/file_manager.py` creates these on startup if missing. If the specific document libraries aren’t installed, files are saved as `.txt` with structured content so you still get a usable output.

## Format specifics

- Documents: `.docx` when `python-docx` is installed; `.txt` fallback.
- Presentations: `.pptx` when `python-pptx` is installed; `.txt` fallback (includes slide sections).
- Spreadsheets: `.xlsx` when `openpyxl` is installed; `.txt` fallback (tabular rows rendered as text).

## Changing the base folder

`FileManager(base_dir=...)` controls where the `office_ai_files` folder is created. By default it’s the current working directory.

## Examples

- After a presentation task, check `office_ai_files/presentations/` for a file named after the requested title.
- Use the `list_files` and `get_file_info` tools to inspect contents programmatically.
