from __future__ import annotations

import json
import os
import re
from typing import List, Optional

from .base_agent import BaseOfficeAgent


class PresentationAgent(BaseOfficeAgent):
    """PowerPoint-focused agent that composes a presentation.

    Attempts to draft slide content via Gemini when GEMINI_API_KEY is available.
    Falls back to a deterministic outline otherwise.
    """

    def _initialize_tools(self):
        return [
            "create_presentation",
            "add_slide",
            "add_text_to_slide",
            "save_presentation",
        ]

    def _get_system_prompt(self) -> str:
        return "Create clear, minimal slides with a short title and a single main point per slide."

    def execute(self, task, context=None, user_id=None, task_id=None):
        title = (context or {}).get("title") or self._extract_title(task) or "Generated Presentation"
        n = self._extract_int(task) or 3
        create = self._tool("create_presentation")
        add_slide = self._tool("add_slide")
        save = self._tool("save_presentation")

        # Try Gemini first
        slides_spec = self._generate_slides_with_gemini(task=str(task), n=n, title=title)

        pid = create(title=title)["presentation_id"]
        if slides_spec:
            for slide in slides_spec[:n]:
                stitle = str(slide.get("title") or title)
                bullets = slide.get("bullets") or []
                if not isinstance(bullets, list):
                    bullets = [str(bullets)]
                text = stitle + "\n" + "\n".join(f"- {str(b)}" for b in bullets)
                add_slide(presentation_id=pid, text=text)
        else:
            # Fallback deterministic content
            for i in range(1, n + 1):
                add_slide(presentation_id=pid, text=f"{title} — Slide {i}")
        return save(presentation_id=pid)

    # --------------------- Gemini draft generation ---------------------
    def _generate_slides_with_gemini(self, task: str, n: int, title: str) -> Optional[List[dict]]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=api_key)
            primary = os.getenv("LLM_MODEL", "gemini-1.5-pro")
            # Try a robust fallback list prioritizing the requested model
            candidates = [primary,
                          "gemini-2.5-flash",
                          "gemini-2.0-flash",
                          "gemini-1.5-flash",
                          "gemini-1.5-pro"]
            # de-duplicate while preserving order
            seen = set()
            fallbacks = []
            for m in candidates:
                if m not in seen:
                    seen.add(m)
                    fallbacks.append(m)
            prompt = (
                "You are a presentation assistant. Create an outline with up to "
                f"{int(n)} slides for a presentation titled '{title}'.\n"
                "Return ONLY valid JSON with this schema and no extra text:\n"
                "{\n  \"slides\": [\n    { \"title\": \"Slide title\", \"bullets\": [\"point 1\", \"point 2\"] },\n    ...\n  ]\n}\n"
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
            slides = data.get("slides")
            if not isinstance(slides, list):
                return None
            # Coerce into expected shape
            cleaned = []
            for s in slides:
                if not isinstance(s, dict):
                    continue
                cleaned.append({
                    "title": s.get("title") or title,
                    "bullets": s.get("bullets") if isinstance(s.get("bullets"), list) else [],
                })
            return cleaned or None
        except Exception as e:  # pragma: no cover - external dependency variability
            self.logger.warning("Gemini slide generation failed: %s", e)
            return None

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        # Try direct load
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to find first JSON object
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    # -------------------------- Utilities -----------------------------
    @staticmethod
    def _extract_int(s: str):
        m = re.search(r"(\d+)", str(s))
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_title(task: str):
        import re as _re

        m = _re.search(r"(?:about|on)\s+(.+)$", str(task), _re.IGNORECASE)
        return m.group(1).strip().rstrip(".") if m else None
