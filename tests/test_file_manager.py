from __future__ import annotations

import os
from pathlib import Path

from office_ai_agent.utils.file_manager import FileManager


def test_file_manager_text_saves(tmp_path: Path):
    fm = FileManager(base_dir=str(tmp_path / "office_ai_files"))

    r1 = fm.save_text_document("quality_doc", "Hello World")
    r2 = fm.save_text_presentation("quality_pres", ["Slide A", "Slide B"]) 
    r3 = fm.save_text_spreadsheet("quality_sheet", [["A", "B"], [1, 2]])

    for r in (r1, r2, r3):
        assert r["status"] == "ok"
        p = Path(r["file_path"])
        assert p.exists(), f"Expected file to exist: {p}"
        assert p.suffix == ".txt"
