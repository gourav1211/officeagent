# Deployment: Options and Tips

This application is primarily intended for local desktop use and local API testing. If you want to deploy parts of it, here are options.

## Desktop app

- Local-only. Consider packaging with PyInstaller if you need a single executable. This is outside the current scope but feasible.

## API server

- Run behind a reverse proxy (nginx/IIS) if exposing outside localhost.
- Ensure `GEMINI_API_KEY` is set securely in the environment.
- Persist the `office_ai_files/` directory to a volume if running in a container.

### Bare-metal/VM service

Use a process manager (e.g., NSSM or Windows Task Scheduler) to keep `python -m office_ai_agent.server` alive.

### Containerization (outline)

- Base image: `python:3.11-slim`
- Copy in `requirements_server.txt` and install deps
- Copy package code
- Expose `8765`
- Entry: `python -m office_ai_agent.server`

Set environment variables (`OPENAI_API_KEY`, etc.) at runtime.

## Security

- Treat API keys as secrets; never commit them.
- If exposing the server, add auth in front of the FastAPI app (API keys, OAuth, or a gateway).

## Observability

- `utils/metrics.py` provides an in-process metric store and JSON export via `/metrics`.
- Integrate with Sentry by setting `SENTRY_DSN` (errors are still logged locally).
