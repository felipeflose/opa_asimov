import os
import tempfile
import pytest
import requests
import agent_core

@pytest.fixture(autouse=True)
def mock_all_requests(monkeypatch):
    """Garante que todas as chamadas http reais sejam interceptadas durante os testes."""
    def mock_post(url, *args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = str(json_data)
            
            def json(self):
                return self.json_data

            def iter_lines(self):
                # Para ollama chunk stream
                import json
                yield json.dumps({"response": "{}", "done": True}).encode("utf-8")

            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        # Respostas fake baseadas nas URLs
        if "embeddings" in url:
            return MockResponse({"embedding": [0.1] * 768}, 200)
        elif "generate" in url:
            return MockResponse({"response": '{"test": "ok"}', "done": True}, 200)
        elif "groq" in url:
            return MockResponse({
                "choices": [{
                    "message": {
                        "content": "insight fake da groq"
                    }
                }]
            }, 200)
        elif "telegram" in url:
            return MockResponse({"ok": True}, 200)
        
        return MockResponse({"status": "ok"}, 200)

    def mock_get(url, *args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.text = str(json_data)
            def json(self):
                return self.json_data
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        if "tags" in url or "11434" in url:
            return MockResponse({"models": [{"name": "gemma4:latest"}]}, 200)
        return MockResponse({"status": "ok"}, 200)

    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setattr(requests, "get", mock_get)

@pytest.fixture
def temp_graph_path(monkeypatch):
    """Cria um arquivo de grafo temporário para evitar alterar o obsidian_graph.json real."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "obsidian_graph_temp.json")
        original_json_path = agent_core.JSON_PATH
        monkeypatch.setattr(agent_core, "JSON_PATH", temp_file)
        yield temp_file
        # Garante que volte ao original
        agent_core.JSON_PATH = original_json_path
