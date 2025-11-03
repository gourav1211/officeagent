from __future__ import annotations

from fastapi.testclient import TestClient

from office_ai_agent.server import app


def test_server_agents_and_execute(monkeypatch, tmp_path):
    # Run server in-process with TestClient; ensure working dir isolation
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)

    r = client.get("/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data and isinstance(data["agents"], list)

    # Run a simple task via document agent (deterministic and fast)
    payload = {"task": "Create a short doc about tests", "context": {"agent": "document"}}
    r2 = client.post("/execute", json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2.get("status") == "completed"
    assert isinstance(data2.get("result"), dict)
