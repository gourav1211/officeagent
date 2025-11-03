"""Orchestrator helper utilities.

These functions provide minimal behavior useful for demos/tests before the full
orchestrator is implemented. They can later be wrapped as LangChain tools.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..utils.file_manager import FileManager


def get_available_agents() -> dict:
	"""Return the names of supported agents as described in docs."""
	return {
		"status": "ok",
		"agents": [
			"document",
			"presentation",
			"spreadsheet",
			"communication",
			"workflow",
		],
	}


_TASK_STATUS: Dict[str, dict] = {}


def get_agent_status(task_id: str) -> dict:
	return _TASK_STATUS.get(task_id, {"status": "unknown", "task_id": task_id})


def get_task_progress(task_id: str) -> dict:
	st = _TASK_STATUS.get(task_id)
	if not st:
		return {"status": "unknown", "task_id": task_id}
	return {"status": st.get("status", "unknown"), "progress": st.get("progress", 0)}


def cancel_task(task_id: str) -> dict:
	if task_id in _TASK_STATUS:
		_TASK_STATUS[task_id]["status"] = "cancelled"
		return {"status": "ok", "task_id": task_id}
	return {"status": "unknown", "task_id": task_id}


def delegate_to_agent(agent_type: str, task: str, context: Optional[dict] = None) -> dict:
	"""Very small demo implementation that writes a text document with the task.

	This is a stand-in for true delegation to specialized agents.
	"""
	fm = FileManager()
	title = f"{agent_type or 'agent'}_task"
	content = f"Task: {task}\nContext: {context or {}}\n"
	return fm.save_text_document(title, content)
