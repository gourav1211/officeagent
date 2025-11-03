from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from .base_agent import BaseOfficeAgent


class SpreadsheetAgent(BaseOfficeAgent):
    """Excel-focused agent that writes a simple 2x2 table."""

    def _initialize_tools(self):
        return [
            "create_workbook",
            "write_cell",
            "save_workbook",
        ]

    def _get_system_prompt(self) -> str:
        return "Create simple, readable spreadsheets with headers and minimal rows."

    def execute(self, task, context=None, user_id=None, task_id=None):
        title = (context or {}).get("title") or self._extract_title(str(task)) or "Generated Sheet"
        create = self._tool("create_workbook")
        write = self._tool("write_cell")
        save = self._tool("save_workbook")

        spec = self._generate_table_with_gemini(task=str(task), title=title)

        wb = create(title=title)["workbook_id"]
        if spec:
            headers = spec.get("headers") if isinstance(spec.get("headers"), list) else []
            rows = spec.get("rows") if isinstance(spec.get("rows"), list) else []
            # write headers
            for c, h in enumerate(headers, start=1):
                write(workbook_id=wb, row=1, col=c, value=str(h))
            # write rows
            for r_idx, row in enumerate(rows, start=2):
                if not isinstance(row, list):
                    row = [row]
                for c_idx, val in enumerate(row, start=1):
                    write(workbook_id=wb, row=r_idx, col=c_idx, value=str(val))
        else:
            # deterministic fallback
            write(workbook_id=wb, row=1, col=1, value="Item")
            write(workbook_id=wb, row=1, col=2, value="Value")
            write(workbook_id=wb, row=2, col=1, value="Example")
            write(workbook_id=wb, row=2, col=2, value=1)
        return save(workbook_id=wb)

    # --------------------- Gemini draft generation ---------------------
    def _generate_table_with_gemini(self, task: str, title: str) -> Optional[Dict[str, Any]]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=api_key)
            primary = os.getenv("LLM_MODEL", "gemini-1.5-pro")
            candidates = [primary, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            seen, fallbacks = set(), []
            for m in candidates:
                if m not in seen:
                    seen.add(m)
                    fallbacks.append(m)

            prompt = (
                "You are a data assistant. Create a compact table suitable for a spreadsheet titled '"
                + title
                + "'. Return ONLY valid JSON with this schema and no extra text:\n"
                "{\n  \"headers\": [\"Header1\", \"Header2\"],\n  \"rows\": [ [\"r1c1\", \"r1c2\"], [\"r2c1\", \"r2c2\"] ]\n}\n"
                f"Task: {task}"
            )
            last_err = None
            for model_name in fallbacks:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    last_err = None
                    break
                except Exception as _e:
                    last_err = _e
                    continue
            if last_err:
                raise last_err
            text = getattr(resp, "text", None) or getattr(resp, "candidates", None)
            if isinstance(text, list):
                text = "\n".join(str(x) for x in text)
            if not isinstance(text, str):
                text = str(resp)
            data = self._extract_json(text)
            if not isinstance(data, dict):
                return None
            headers = data.get("headers") if isinstance(data.get("headers"), list) else []
            rows = data.get("rows") if isinstance(data.get("rows"), list) else []
            return {"headers": headers, "rows": rows}
        except Exception as e:  # pragma: no cover
            self.logger.warning("Gemini table generation failed: %s", e)
            return None

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    @staticmethod
    def _extract_title(task: str) -> Optional[str]:
        m = re.search(r"(?:about|on)\s+(.+)$", str(task), re.IGNORECASE)
        return m.group(1).strip().rstrip(".") if m else None
