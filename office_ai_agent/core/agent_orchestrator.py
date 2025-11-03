from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Dict, Iterable, Optional

from ..tools.office_tools import OfficeToolRegistry
from ..utils.logger import get_logger
from ..utils.metrics import Metrics
from ..agents.document_agent import DocumentAgent
from ..agents.presentation_agent import PresentationAgent
from ..agents.spreadsheet_agent import SpreadsheetAgent
from ..agents.communication_agent import CommunicationAgent
from ..agents.workflow_agent import WorkflowAgent


class OfficeAIAgent:
    """Core orchestrator (Step 5 minimal implementation).

    This version wires a tool registry and a tiny heuristic planner so that
    execute() produces real files via tools without depending on the LLM. It
    prepares for Gemini integration; LLM initialization is lazy and optional.
    """

    def __init__(self, config=None):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.metrics = Metrics()
        self.tools = OfficeToolRegistry()
        self._llm = None  # lazy init for Gemini
        self.agents = self._initialize_agents()

    # ---------------------------- Public API -----------------------------
    def execute(self, task: str, context: Optional[dict] = None, user_id: Optional[str] = None, task_id: Optional[str] = None) -> dict:
        start = time.perf_counter()
        tid = task_id or self._make_task_id()
        self.logger.info("execute task_id=%s task=%s", tid, task)

        try:
            with self.metrics.timer("execute_total"):
                # If a specific agent is requested in context, delegate
                ctx = context or {}
                agent_name = (ctx.get("agent") or "").strip().lower()
                if agent_name and agent_name in self.agents:
                    result = self.agents[agent_name].execute(task, context=ctx, user_id=user_id, task_id=tid)
                else:
                    result = self._run_minimal_plan(task, ctx)
            elapsed = time.perf_counter() - start
            return {
                "task_id": tid,
                "status": "completed",
                "result": result,
                "execution_time": round(elapsed, 3),
            }
        except Exception as e:  # pragma: no cover - defensive
            self.logger.exception("execute failed: %s", e)
            elapsed = time.perf_counter() - start
            return {
                "task_id": tid,
                "status": "error",
                "error": str(e),
                "execution_time": round(elapsed, 3),
            }

    def execute_streaming(self, task: str, context: Optional[dict] = None, user_id: Optional[str] = None, task_id: Optional[str] = None):
        """Yield minimal progress events as a generator."""
        tid = task_id or self._make_task_id()
        yield {"event": "start", "task_id": tid}
        yield {"event": "planning", "message": "Selecting plan based on task keywords"}
        result = self._run_minimal_plan(task, context or {})
        yield {"event": "result", "result": result}
        yield {"event": "end", "status": "completed"}

    # --------------------------- Internal impl ---------------------------
    def _make_task_id(self) -> str:
        now = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"task_{now}"

    def _init_llm(self):  # pragma: no cover - optional until we use it
        if self._llm is not None:
            return self._llm
        try:
            # Lazy import to avoid hard dependency until needed
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = (self.config.llm.model if self.config and self.config.llm else "gemini-1.5-pro")
            temperature = (self.config.llm.temperature if self.config and self.config.llm else 0.7)
            self._llm = ChatGoogleGenerativeAI(model=model, temperature=temperature)
            self.logger.info("Initialized Gemini LLM model=%s temp=%s", model, temperature)
        except Exception as e:
            self.logger.warning("Could not initialize Gemini LLM yet: %s", e)
            self._llm = None
        return self._llm

    def _run_minimal_plan(self, task: str, context: dict) -> dict:
        """Very small heuristic plan to exercise tools and create real files.

        Heuristics:
        - if 'slide' or 'presentation' in task -> create presentation with N slides
        - elif 'sheet' or 'spreadsheet' or 'excel' in task -> create a simple workbook
        - else -> create a simple document
        """
        t = task.lower()
        if any(k in t for k in ("slide", "presentation", "ppt")):
            # Delegate to PresentationAgent so it can use Gemini when available
            return self.agents["presentation"].execute(task, context=context)
        if any(k in t for k in ("sheet", "spreadsheet", "excel", "table")):
            # Delegate to SpreadsheetAgent to allow Gemini-driven table generation
            return self.agents["spreadsheet"].execute(task, context=context)
        # Default to DocumentAgent
        return self.agents["document"].execute(task, context=context)

    @staticmethod
    def _extract_int(s: str) -> Optional[int]:
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_title(task: str) -> Optional[str]:
        # naive extraction after 'about' or 'on'
        m = re.search(r"(?:about|on)\s+(.+)$", task, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".")
        return None

    # --------------------------- Tool helpers ----------------------------
    def _tool(self, name: str):
        t = self.tools.get_tool(name)
        if not t:
            raise RuntimeError(f"tool not found: {name}")
        return t

    def _make_document(self, title: str) -> dict:
        create = self._tool("create_document")
        add_h = self._tool("add_heading")
        add_p = self._tool("add_paragraph")
        save = self._tool("save_document")
        doc_id = create(title=title)["doc_id"]
        add_h(doc_id=doc_id, text=title)
        add_p(doc_id=doc_id, text="This document was generated by OfficeAIAgent.")
        return save(doc_id=doc_id)

    def _make_presentation(self, title: str, slides: int) -> dict:
        create = self._tool("create_presentation")
        add_slide = self._tool("add_slide")
        save = self._tool("save_presentation")
        pid = create(title=title)["presentation_id"]
        for i in range(1, slides + 1):
            add_slide(presentation_id=pid, text=f"{title} — Slide {i}")
        return save(presentation_id=pid)

    def _make_workbook(self, title: str) -> dict:
        create = self._tool("create_workbook")
        write = self._tool("write_cell")
        save = self._tool("save_workbook")
        wb = create(title=title)["workbook_id"]
        write(workbook_id=wb, row=1, col=1, value="Item")
        write(workbook_id=wb, row=1, col=2, value="Value")
        write(workbook_id=wb, row=2, col=1, value="Example")
        write(workbook_id=wb, row=2, col=2, value=42)
        return save(workbook_id=wb)

    # --------------------------- Agents init ------------------------------
    def _initialize_agents(self):
        return {
            "document": DocumentAgent(self.tools, name="DocumentAgent"),
            "presentation": PresentationAgent(self.tools, name="PresentationAgent"),
            "spreadsheet": SpreadsheetAgent(self.tools, name="SpreadsheetAgent"),
            "communication": CommunicationAgent(self.tools, name="CommunicationAgent"),
            "workflow": WorkflowAgent(self.tools, name="WorkflowAgent"),
        }
