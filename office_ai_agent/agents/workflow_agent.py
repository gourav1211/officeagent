from __future__ import annotations

from .base_agent import BaseOfficeAgent


class WorkflowAgent(BaseOfficeAgent):
    """Cross-application agent (stub): produces a plan document for now."""

    def _initialize_tools(self):
        return [
            "create_document",
            "add_heading",
            "add_paragraph",
            "save_document",
        ]

    def _get_system_prompt(self) -> str:
        return "Plan multi-step workflows and summarize outputs across Office apps."

    def execute(self, task, context=None, user_id=None, task_id=None):
        title = (context or {}).get("title") or "Workflow Plan"
        create = self._tool("create_document")
        add_h = self._tool("add_heading")
        add_p = self._tool("add_paragraph")
        save = self._tool("save_document")
        doc_id = create(title=title)["doc_id"]
        add_h(doc_id=doc_id, text=title)
        add_p(doc_id=doc_id, text="1) Prepare presentation\n2) Draft summary\n3) Share results")
        add_p(doc_id=doc_id, text=f"Task context: {str(task)}")
        return save(doc_id=doc_id)
