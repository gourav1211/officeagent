from __future__ import annotations

from pathlib import Path

from office_ai_agent.tools.office_tools import OfficeToolRegistry


def test_tools_registry_basic_document(tmp_path: Path, monkeypatch):
    # Ensure office_ai_files is under tmp to avoid polluting workspace
    monkeypatch.chdir(tmp_path)
    reg = OfficeToolRegistry()
    create = reg.get_tool("create_document")
    add_p = reg.get_tool("add_paragraph")
    save = reg.get_tool("save_document")

    assert create and add_p and save

    doc = create(title="Registry Test Doc")
    doc_id = doc["doc_id"]
    add_p(doc_id=doc_id, text="Line 1")
    add_p(doc_id=doc_id, text="Line 2")
    out = save(doc_id=doc_id)
    path = Path(out["file_path"])
    assert path.exists(), f"Expected output document at {path}"
