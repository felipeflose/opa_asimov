import pytest
from agent_classifier import classify_content

def test_heuristic_work_filename():
    """Valida se nomes que batem na heurística de work funcionam."""
    ctype, reasoning = classify_content("", "Minha Experiencia Profissional.md")
    assert ctype == "work"
    assert "Heurística" in reasoning

    ctype, reasoning = classify_content("", "Contato.md")
    assert ctype == "work"

def test_heuristic_tool_filename():
    """Valida se nomes que batem na heurística de tool funcionam."""
    ctype, reasoning = classify_content("", "habilidades e competencias do Felipe.md")
    assert ctype == "tool"
    assert "Heurística" in reasoning

def test_heuristic_mba_filename():
    """Valida se nomes que batem na heurística de mba funcionam."""
    ctype, reasoning = classify_content("", "Aula MBA IA.md")
    assert ctype == "mba"
    assert "Heurística" in reasoning

def test_ollama_classification(monkeypatch):
    """Valida a classificação semântica via chamada simulada do Ollama."""
    import agent_classifier
    def mock_ollama_call(prompt, system_prompt, model=None):
        return {"type": "tool", "reasoning": "Identificado tom técnico de documentação"}
    
    monkeypatch.setattr(agent_classifier, "local_ollama_call", mock_ollama_call)
    
    ctype, reasoning = classify_content("Texto aleatório", "QualquerArquivo.md")
    assert ctype == "tool"
    assert reasoning == "Identificado tom técnico de documentação"

def test_ollama_fallback_on_invalid_response(monkeypatch):
    """Valida o fallback para 'classificar' em caso de resposta inválida do LLM."""
    import agent_classifier
    def mock_ollama_call(prompt, system_prompt, model=None):
        return {"type": "invalido", "reasoning": "bla"}
    
    monkeypatch.setattr(agent_classifier, "local_ollama_call", mock_ollama_call)
    
    ctype, reasoning = classify_content("Texto aleatório", "QualquerArquivo.md")
    assert ctype == "classificar"
    assert "Fallback" in reasoning
