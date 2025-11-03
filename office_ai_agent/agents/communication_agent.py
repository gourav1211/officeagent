from __future__ import annotations

from .base_agent import BaseOfficeAgent


class CommunicationAgent(BaseOfficeAgent):
    """Communication agent (stub): writes a summary document for now.

    Real email/Teams integrations are out-of-scope for this rebuild; we produce a
    document representing the communication content.
    """

    def _initialize_tools(self):
        return [
            "create_document",
            "add_heading",
            "add_paragraph",
            "save_document",
        ]

    def _get_system_prompt(self) -> str:
        return "Draft clear, concise communications; summarize key points and actions."

    def execute(self, task, context=None, user_id=None, task_id=None):
        title = (context or {}).get("title") or "Communication Summary"
        create = self._tool("create_document")
        add_h = self._tool("add_heading")
        add_p = self._tool("add_paragraph")
        save = self._tool("save_document")
        doc_id = create(title=title)["doc_id"]
        add_h(doc_id=doc_id, text=title)
        add_p(doc_id=doc_id, text=str(task))
        add_p(doc_id=doc_id, text="Summary prepared by CommunicationAgent")
        return save(doc_id=doc_id)
