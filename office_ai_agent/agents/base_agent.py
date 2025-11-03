from __future__ import annotations

from typing import Dict, List, Optional

from ..tools.office_tools import OfficeToolRegistry, Tool
from ..utils.logger import get_logger
from ..utils.metrics import Metrics


class BaseOfficeAgent:
    """Base class for specialized agents.

    Subclasses should implement `_initialize_tools()` and `_get_system_prompt()`.
    They may override `execute` for custom behaviors.
    """

    def __init__(self, registry: Optional[OfficeToolRegistry] = None, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.name)
        self.metrics = Metrics()
        self.registry = registry or OfficeToolRegistry()
        self._tool_names = self._initialize_tools()
        self._tool_map: Dict[str, Tool] = {}
        for n in self._tool_names:
            t = self.registry.get_tool(n)
            if t:
                self._tool_map[n] = t

    # ---- subclass API ----
    def _initialize_tools(self) -> List[str]:  # pragma: no cover - abstract
        return []

    def _get_system_prompt(self) -> str:  # pragma: no cover - abstract
        return ""

    # ---- helpers ----
    def _tool(self, name: str) -> Tool:
        t = self._tool_map.get(name) or self.registry.get_tool(name)
        if not t:
            raise RuntimeError(f"tool not found: {name}")
        return t

    # ---- execution ----
    def execute(self, task, context=None, user_id=None, task_id=None):  # pragma: no cover - to be overridden
        raise NotImplementedError

    def execute_streaming(self, task, context=None, user_id=None, task_id=None):  # pragma: no cover
        # Minimal streaming wrapper around execute
        yield {"event": "start", "agent": self.name}
        result = self.execute(task, context=context, user_id=user_id, task_id=task_id)
        yield {"event": "result", "result": result}
        yield {"event": "end", "status": "completed"}
