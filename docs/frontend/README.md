# Frontend (Intentionally Minimal)

Per requirements, the Electron/Vite/TypeScript frontend is excluded from this rebuild. You can interact with the system via:

- Desktop GUI: `python launcher.py`
- REST API: start the FastAPI server and call endpoints from any client.

If you later want a basic web UI:
- Build a small HTML/JS page that POSTs to `/execute` and displays results.
- Or scaffold a minimal FastAPI Jinja template to call the same endpoints.

The server already supports CORS for `http://localhost:5173` (used by the original Electron dev setup), but you don’t need it for this rebuild.

- tkinter if feasible can also be a good option
