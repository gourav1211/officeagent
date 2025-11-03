"""Simple file-producing tools and in-memory composition sessions.

These are lightweight implementations that expose tool-like callables used by the
registry. They do not require LangChain at this stage; later we can wrap them as
LangChain tools without changing their core behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ..utils.file_manager import FileManager


# -------------------------- Document composition ---------------------------

@dataclass
class _DocumentSession:
	title: str
	paragraphs: List[str] = field(default_factory=list)


_DOC_SESSIONS: Dict[str, _DocumentSession] = {}


def create_document(title: str) -> dict:
	doc_id = FileManager._slugify(title)  # reuse slug for id
	if doc_id in _DOC_SESSIONS:
		# create a unique id by suffixing
		i = 1
		while f"{doc_id}_{i}" in _DOC_SESSIONS:
			i += 1
		doc_id = f"{doc_id}_{i}"
	_DOC_SESSIONS[doc_id] = _DocumentSession(title=title)
	return {"status": "ok", "doc_id": doc_id}


def add_heading(doc_id: str, text: str) -> dict:
	sess = _DOC_SESSIONS.get(doc_id)
	if not sess:
		return {"status": "error", "error": f"unknown doc_id: {doc_id}"}
	# First paragraph will be treated as heading by FileManager.save_docx_document
	sess.paragraphs.insert(0, str(text)) if not sess.paragraphs else sess.paragraphs.append(str(text))
	return {"status": "ok", "doc_id": doc_id}


def add_paragraph(doc_id: str, text: str) -> dict:
	sess = _DOC_SESSIONS.get(doc_id)
	if not sess:
		return {"status": "error", "error": f"unknown doc_id: {doc_id}"}
	sess.paragraphs.append(str(text))
	return {"status": "ok", "doc_id": doc_id}


def save_document(doc_id: str) -> dict:
	sess = _DOC_SESSIONS.pop(doc_id, None)
	if not sess:
		return {"status": "error", "error": f"unknown doc_id: {doc_id}"}
	fm = FileManager()
	return fm.save_docx_document(sess.title, sess.paragraphs or [sess.title, "(empty)"])


# ----------------------- Presentation composition -------------------------

@dataclass
class _PresentationSession:
	title: str
	slides: List[str] = field(default_factory=list)


_PRES_SESSIONS: Dict[str, _PresentationSession] = {}


def create_presentation(title: str) -> dict:
	pres_id = FileManager._slugify(title)
	if pres_id in _PRES_SESSIONS:
		i = 1
		while f"{pres_id}_{i}" in _PRES_SESSIONS:
			i += 1
		pres_id = f"{pres_id}_{i}"
	_PRES_SESSIONS[pres_id] = _PresentationSession(title=title)
	return {"status": "ok", "presentation_id": pres_id}


def add_slide(presentation_id: str, text: str) -> dict:
	sess = _PRES_SESSIONS.get(presentation_id)
	if not sess:
		return {"status": "error", "error": f"unknown presentation_id: {presentation_id}"}
	sess.slides.append(str(text))
	return {"status": "ok", "presentation_id": presentation_id}


def add_text_to_slide(presentation_id: str, slide_index: int, text: str) -> dict:
	sess = _PRES_SESSIONS.get(presentation_id)
	if not sess:
		return {"status": "error", "error": f"unknown presentation_id: {presentation_id}"}
	idx = int(slide_index)
	if idx < 1 or idx > len(sess.slides):
		return {"status": "error", "error": f"slide_index out of range: {slide_index}"}
	# Append to existing content for that slide
	sess.slides[idx - 1] = f"{sess.slides[idx - 1]}\n{text}"
	return {"status": "ok", "presentation_id": presentation_id}


def save_presentation(presentation_id: str) -> dict:
	sess = _PRES_SESSIONS.pop(presentation_id, None)
	if not sess:
		return {"status": "error", "error": f"unknown presentation_id: {presentation_id}"}
	fm = FileManager()
	slides = sess.slides or ["(empty)"]
	return fm.save_pptx_presentation(sess.title, slides)


# -------------------------- Spreadsheet composition -----------------------

@dataclass
class _WorkbookSession:
	title: str
	rows: List[List[object]] = field(default_factory=list)


_WB_SESSIONS: Dict[str, _WorkbookSession] = {}


def create_workbook(title: str) -> dict:
	wb_id = FileManager._slugify(title)
	if wb_id in _WB_SESSIONS:
		i = 1
		while f"{wb_id}_{i}" in _WB_SESSIONS:
			i += 1
		wb_id = f"{wb_id}_{i}"
	_WB_SESSIONS[wb_id] = _WorkbookSession(title=title)
	return {"status": "ok", "workbook_id": wb_id}


def write_cell(workbook_id: str, row: int, col: int, value: object) -> dict:
	sess = _WB_SESSIONS.get(workbook_id)
	if not sess:
		return {"status": "error", "error": f"unknown workbook_id: {workbook_id}"}
	r = int(row)
	c = int(col)
	if r < 1 or c < 1:
		return {"status": "error", "error": "row and col must be >= 1"}
	# expand rows structure
	while len(sess.rows) < r:
		sess.rows.append([])
	while len(sess.rows[r - 1]) < c:
		sess.rows[r - 1].append("")
	sess.rows[r - 1][c - 1] = value
	return {"status": "ok", "workbook_id": workbook_id}


def save_workbook(workbook_id: str) -> dict:
	sess = _WB_SESSIONS.pop(workbook_id, None)
	if not sess:
		return {"status": "error", "error": f"unknown workbook_id: {workbook_id}"}
	fm = FileManager()
	rows = sess.rows or [["(empty)"]]
	return fm.save_xlsx_workbook(sess.title, rows)


# ------------------------------ FS helpers ---------------------------------

def list_files(kind: str) -> dict:
	"""List files within a workspace subfolder (documents/presentations/spreadsheets/templates/exports)."""
	fm = FileManager()
	kind = str(kind).lower()
	folder_map = {
		"documents": fm.DOCUMENTS,
		"presentations": fm.PRESENTATIONS,
		"spreadsheets": fm.SPREADSHEETS,
		"templates": fm.TEMPLATES,
		"exports": fm.EXPORTS,
	}
	sub = folder_map.get(kind)
	if not sub:
		return {"status": "error", "error": f"unknown kind: {kind}"}
	base = fm.base_dir / sub
	items = sorted([str(p) for p in base.glob("**/*") if p.is_file()])
	return {"status": "ok", "files": items}


def get_file_info(file_path: str) -> dict:
	p = Path(file_path)
	if not p.exists() or not p.is_file():
		return {"status": "error", "error": f"file not found: {file_path}"}
	st = p.stat()
	return {
		"status": "ok",
		"file_path": str(p.resolve()),
		"size": st.st_size,
		"modified": st.st_mtime,
	}


def create_folder(kind: str, name: str) -> dict:
	fm = FileManager()
	kind = str(kind).lower()
	folder_map = {
		"documents": fm.DOCUMENTS,
		"presentations": fm.PRESENTATIONS,
		"spreadsheets": fm.SPREADSHEETS,
		"templates": fm.TEMPLATES,
		"exports": fm.EXPORTS,
	}
	sub = folder_map.get(kind)
	if not sub:
		return {"status": "error", "error": f"unknown kind: {kind}"}
	target = fm.base_dir / sub / FileManager._slugify(name)
	target.mkdir(parents=True, exist_ok=True)
	return {"status": "ok", "folder_path": str(target)}

