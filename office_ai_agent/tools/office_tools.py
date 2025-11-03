from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from . import simple_tools as st


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., dict]

    def __call__(self, *args, **kwargs) -> dict:  # pragma: no cover - thin wrapper
        return self.func(*args, **kwargs)


class OfficeToolRegistry:
    """Registry for tools used by agents and orchestrator."""

    def __init__(self) -> None:
        self._tools: List[Tool] = []
        self._tool_map: Dict[str, Tool] = {}
        self._register_simple_tools()

    def _register(self, name: str, func: Callable[..., dict], description: str) -> None:
        t = Tool(name=name, description=description, func=func)
        self._tools.append(t)
        self._tool_map[name] = t

    def _register_simple_tools(self) -> None:
        # Documents
        self._register("create_document", st.create_document, "Create a new document composition session.")
        self._register("add_heading", st.add_heading, "Add a heading (or first paragraph) to a document.")
        self._register("add_paragraph", st.add_paragraph, "Add a paragraph to a document.")
        self._register("save_document", st.save_document, "Save a composed document to DOCX or TXT.")

        # Presentations
        self._register("create_presentation", st.create_presentation, "Create a new presentation session.")
        self._register("add_slide", st.add_slide, "Add a new slide with text content.")
        self._register("add_text_to_slide", st.add_text_to_slide, "Append text to an existing slide.")
        self._register("save_presentation", st.save_presentation, "Save a composed presentation to PPTX or TXT.")

        # Spreadsheets
        self._register("create_workbook", st.create_workbook, "Create a new spreadsheet session.")
        self._register("write_cell", st.write_cell, "Write a cell value using 1-based row/col indexing.")
        self._register("save_workbook", st.save_workbook, "Save a composed workbook to XLSX or TXT.")

        # FS helpers
        self._register("list_files", st.list_files, "List files in a workspace subfolder.")
        self._register("get_file_info", st.get_file_info, "Get information about a specific file.")
        self._register("create_folder", st.create_folder, "Create a folder under a workspace subfolder.")

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools)

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tool_map.get(name)
