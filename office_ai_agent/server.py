from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.agent_orchestrator import OfficeAIAgent
from .core.config import Config
from .utils.logger import get_logger


# --------------------------- App and Orchestrator ---------------------------
config = Config.load()
logger = get_logger("server")
agent = OfficeAIAgent(config=config)
_TASKS: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Office AI Agent API", version="0.1.0")

# CORS for local frontend/dev (aligns with docs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------ Models (light) ------------------------------
def _ok(data: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=data)


class ExecuteRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None


# ------------------------------- Endpoints ---------------------------------
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/agents")
def list_agents() -> Dict[str, Any]:
    return {"agents": sorted(list(agent.agents.keys()))}


@app.post("/execute")
async def execute(req: ExecuteRequest) -> JSONResponse:
    logger.info("/execute task_id=%s", req.task_id or "<auto>")
    result = agent.execute(
        task=req.task,
        context=req.context or {},
        user_id=req.user_id,
        task_id=req.task_id,
    )
    if isinstance(result, dict) and result.get("task_id"):
        _TASKS[result["task_id"]] = result
    return _ok(result)


def _to_sse(event: Dict[str, Any]) -> str:
    # Format as Server-Sent Events line
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.get("/execute_stream")
async def execute_stream(task: str, user_id: Optional[str] = None) -> StreamingResponse:
    logger.info("/execute_stream task='%s'", task)

    async def gen() -> AsyncGenerator[bytes, None]:
        # Use the synchronous generator from orchestrator in a thread-friendly loop
        loop = agent.execute_streaming(task=task, context={}, user_id=user_id)
        for event in loop:
            yield _to_sse(event).encode("utf-8")
            # slight pause to avoid flooding the client
            await asyncio.sleep(0.01)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return {"metrics": agent.metrics.snapshot()}


@app.get("/status/{task_id}")
def status(task_id: str) -> Dict[str, Any]:
    if task_id in _TASKS:
        return _TASKS[task_id]
    raise HTTPException(status_code=404, detail="task_id not found")


# ------------------------------- Entrypoint --------------------------------
def run(host: str = "127.0.0.1", port: Optional[int] = None) -> None:
    """Launch the FastAPI server with Uvicorn."""
    import uvicorn

    p = port or (config.server.api_port if config and config.server else 8765)
    logger.info("Starting API server on %s:%s", host, p)
    uvicorn.run(app, host=host, port=p, log_level=(config.monitoring.log_level.lower() if config and config.monitoring else "info"))


if __name__ == "__main__":
    run()
