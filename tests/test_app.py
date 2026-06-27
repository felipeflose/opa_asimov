import os
import json
import pytest
from app import app, validate_bot_state

@pytest.fixture
def client(monkeypatch):
    """Cria um cliente de testes para o Flask."""
    app.config["TESTING"] = True
    # Limpa o tracker de rate limit para evitar erros de 429 Too Many Requests durante os testes
    from app import _rate_limit_tracker
    _rate_limit_tracker.clear()
    # Define uma API key estática para testar a autenticação
    monkeypatch.setattr("app.API_KEY", "minha_chave_secreta_teste")
    monkeypatch.setattr("app.API_KEY_PREVIOUS", "chave_antiga")
    with app.test_client() as client:
        yield client

def test_validate_bot_state():
    """Valida se validate_bot_state limpa e corrige o schema de estado do bot."""
    # Entrada totalmente corrompida
    bad_data = "texto_invalido"
    state = validate_bot_state(bad_data)
    assert state["status"] == "offline"
    assert isinstance(state["last_messages"], list)

    # Dicionário parcialmente preenchido
    partial_data = {"status": "online", "msg_in": "deveria_ser_int"}
    state = validate_bot_state(partial_data)
    assert state["status"] == "online"
    # msg_in foi descartada/resetada por erro de tipo (deveria ser int)
    assert state["msg_in"] == 0

def test_api_health(client, temp_graph_path):
    """Valida o endpoint de health check."""
    # Grava um grafo básico
    from agent_core import save_graph
    save_graph([{"id": "mestre"}], [])

    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "status" in data
    assert "checks" in data
    assert data["checks"]["graph"]["status"] == "ok"

def test_api_status(client, temp_graph_path):
    """Valida o endpoint /api/status."""
    from agent_core import save_graph
    save_graph([{"id": "mestre"}], [])

    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "telemetry" in data
    assert "graph" in data

def test_api_metrics_history(client):
    """Valida o endpoint /api/metrics-history."""
    resp = client.get("/api/metrics-history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)

def test_require_auth_missing_key(client):
    """Valida que endpoints administrativos retornam 401 caso a chave esteja ausente."""
    resp = client.post("/api/run-update")
    assert resp.status_code == 401
    data = resp.get_json()
    assert "API key ausente" in data["msg"]

def test_require_auth_invalid_key(client):
    """Valida que endpoints administrativos retornam 401 caso a chave esteja incorreta."""
    resp = client.post("/api/run-update", headers={"X-API-Key": "chave_incorreta"})
    assert resp.status_code == 401

def test_require_auth_valid_key(client, monkeypatch):
    """Valida que endpoints administrativos aceitam chaves válidas."""
    # Mock do subprocess.Popen para não disparar um processo de verdade
    class DummyProcess:
        pid = 12345
        def poll(self):
            return None
    
    monkeypatch.setattr("app._launch_graph", lambda args: DummyProcess())
    
    resp = client.post("/api/run-update", headers={"X-API-Key": "minha_chave_secreta_teste"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "started"

def test_require_auth_previous_key(client, monkeypatch):
    """Valida que o bypass de rotação funciona com chaves anteriores."""
    class DummyProcess:
        pid = 12345
        def poll(self):
            return None
    
    monkeypatch.setattr("app._launch_graph", lambda args: DummyProcess())
    
    from app import _rate_limit_tracker
    _rate_limit_tracker.clear()
    
    # Executa usando FLOSE_API_KEY_PREVIOUS
    resp = client.post("/api/run-update", headers={"X-API-Key": "chave_antiga"})
    assert resp.status_code == 200

def test_api_improvements(client):
    """Valida o carregamento e filtros do backlog de melhorias."""
    resp = client.get("/api/improvements")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "stats" in data
    assert "todo" in data
    assert "in_progress" in data
    assert "done" in data
    assert data["stats"]["total"] == 10000

def test_api_improvements_move(client):
    """Valida a movimentação de status de melhorias."""
    # Move item de todo para in_progress
    resp = client.post("/api/improvements/move", headers={"X-API-Key": "minha_chave_secreta_teste"}, json={"id": "IMP-00004", "status": "in_progress"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    # Move item para status inválido
    resp = client.post("/api/improvements/move", headers={"X-API-Key": "minha_chave_secreta_teste"}, json={"id": "IMP-00004", "status": "invalid_status"})
    assert resp.status_code == 400

def test_api_improvements_apply_daily(client):
    """Valida a aplicação da cota diária de 3 melhorias."""
    resp = client.post("/api/improvements/apply-daily", headers={"X-API-Key": "minha_chave_secreta_teste"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert len(data["applied"]) == 3

