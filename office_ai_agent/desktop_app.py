from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional

from .core.agent_orchestrator import OfficeAIAgent
from .core.config import Config


class DesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Office AI Agent")
        self.geometry("760x520")
        self.minsize(700, 480)

        self._agent = OfficeAIAgent(Config.load())
        self._queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None

        self._build_ui()
        self._poll_queue()

    # ------------------------------ UI layout ------------------------------
    def _build_ui(self) -> None:
        # Top: Task and controls
        top = ttk.Frame(self, padding=(10, 10))
        top.pack(fill=tk.X)

        ttk.Label(top, text="Task:").grid(row=0, column=0, sticky=tk.W)
        self.task_var = tk.StringVar()
        self.task_entry = ttk.Entry(top, textvariable=self.task_var)
        self.task_entry.grid(row=0, column=1, sticky=tk.EW, padx=(6, 6))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Agent:").grid(row=0, column=2, sticky=tk.W)
        self.agent_var = tk.StringVar(value="auto")
        self.agent_combo = ttk.Combobox(
            top,
            textvariable=self.agent_var,
            state="readonly",
            values=["auto", "document", "presentation", "spreadsheet", "communication", "workflow"],
            width=16,
        )
        self.agent_combo.grid(row=0, column=3, sticky=tk.W)

        self.run_btn = ttk.Button(top, text="Execute Task", command=self._on_execute)
        self.run_btn.grid(row=0, column=4, sticky=tk.E, padx=(6, 0))

        # Middle: Results and status
        mid = ttk.Frame(self, padding=(10, 10))
        mid.pack(fill=tk.BOTH, expand=True)

        ttk.Label(mid, text="Output:")
        self.output = tk.Text(mid, height=16, wrap=tk.WORD)
        self.output.configure(state=tk.DISABLED)
        self.output.pack(fill=tk.BOTH, expand=True)

        # Bottom: actions row
        bottom = ttk.Frame(self, padding=(10, 10))
        bottom.pack(fill=tk.X)

        self.metrics_btn = ttk.Button(bottom, text="Show Metrics", command=self._on_show_metrics)
        self.metrics_btn.pack(side=tk.LEFT)

        self.open_folder_btn = ttk.Button(bottom, text="Open Output Folder", command=self._on_open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        self.status = ttk.Label(bottom, textvariable=self.status_var, anchor=tk.W)
        self.status.pack(side=tk.RIGHT)

    # ------------------------------ Actions --------------------------------
    def _on_execute(self) -> None:
        task = self.task_var.get().strip()
        if not task:
            messagebox.showwarning("Missing Task", "Please enter a task to execute.")
            return

        context: Dict[str, Any] = {}
        agent_name = self.agent_var.get()
        if agent_name != "auto":
            context["agent"] = agent_name

        self._append_output(f"Executing: {task}\n")
        self._set_status("Running...")
        self.run_btn.config(state=tk.DISABLED)

        def worker() -> None:
            try:
                result = self._agent.execute(task=task, context=context)
                self._queue.put({"type": "result", "data": result})
            except Exception as e:  # pragma: no cover - UI safety
                self._queue.put({"type": "error", "data": str(e)})

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _on_show_metrics(self) -> None:
        snap = self._agent.metrics.snapshot()
        self._append_output(f"Metrics: {snap}\n")

    def _on_open_folder(self) -> None:
        base = os.path.join(os.getcwd(), "office_ai_files")
        try:
            if os.name == "nt":
                os.startfile(base)  # type: ignore[attr-defined]
            else:
                messagebox.showinfo("Open Folder", f"Output folder: {base}")
        except Exception as e:  # pragma: no cover - UI safety
            messagebox.showerror("Open Folder", str(e))

    # ------------------------------ Helpers --------------------------------
    def _append_output(self, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg["type"] == "result":
                    data = msg["data"]
                    self._append_output(f"Result: {data}\n")
                    self._set_status("Completed")
                    self.run_btn.config(state=tk.NORMAL)
                elif msg["type"] == "error":
                    self._append_output(f"Error: {msg['data']}\n")
                    self._set_status("Error")
                    self.run_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        finally:
            self.after(150, self._poll_queue)


def main() -> None:
    app = DesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
