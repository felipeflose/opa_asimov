import pytest
import numpy as np
from agent_edge import detect_orphans, fix_orphan, detect_duplicates, discover_cross_links

def test_detect_orphans():
    """Valida se detect_orphans identifica nós com depth >= 2 sem conexões de entrada."""
    nodes = [
        {"id": "mestre", "depth": 0},
        {"id": "work_hub", "depth": 1},
        {"id": "projeto_a", "depth": 2},  # Órfão
        {"id": "projeto_b", "depth": 2}   # Conectado
    ]
    edges = [
        {"source": "work_hub", "target": "projeto_b"}
    ]
    
    orphans = detect_orphans(nodes, edges)
    assert "projeto_a" in orphans
    assert "projeto_b" not in orphans
    assert "work_hub" not in orphans

def test_fix_orphan():
    """Valida se fix_orphan reconecta o nó órfão ao hub da sua categoria."""
    nodes = [
        {"id": "work_hub", "type": "work"},
        {"id": "projeto_a", "id": "projeto_a", "type": "work"}
    ]
    edges = []
    existing_links = set()
    
    changed = fix_orphan({"id": "projeto_a", "type": "work"}, nodes, edges, existing_links)
    assert changed is True
    assert len(edges) == 1
    assert edges[0]["source"] == "work_hub"
    assert edges[0]["target"] == "projeto_a"

def test_detect_duplicates_textual():
    """Valida a detecção de duplicatas por similaridade textual de strings."""
    nodes = [
        {"id": "no1", "title": "Desenvolvimento com Python", "path": "x.md", "type": "tool"},
        {"id": "no2", "title": "Desenvolvimento com Pythn", "path": "y.md", "type": "tool"} # Muito similar
    ]
    
    dups = detect_duplicates(nodes)
    assert len(dups) >= 1
    # Verifica se a tupla retornada contém os nós e o tipo TEXTUAL
    assert dups[0][3] == "TEXTUAL"

def test_detect_duplicates_semantic(monkeypatch):
    """Valida a detecção de duplicatas semânticas usando Numpy."""
    nodes = [
        {"id": "no_a", "title": "Engenharia de Dados", "path": "a.md", "type": "work", "embedding": [0.5] * 768},
        {"id": "no_b", "title": "Data Engineering", "path": "b.md", "type": "work", "embedding": [0.51] * 768}
    ]
    
    # Mock do Ollama embedding para não chamar de verdade (já que a fixture global mocka requests, 
    # mas o embedding já está nos nós, então o Numpy usará direto)
    dups = detect_duplicates(nodes)
    assert len(dups) >= 1
    assert dups[0][3] == "SEMÂNTICA"

def test_discover_cross_links(monkeypatch):
    """Valida o scout e criação de links semânticos cross (ex: Work para Tool)."""
    import agent_edge
    def mock_ollama_call(prompt, system_prompt, model=None):
        return {"should_link": True, "reasoning": "Relação direta"}
    monkeypatch.setattr(agent_edge, "local_ollama_call", mock_ollama_call)
    
    nodes = [
        {"id": "proj_a", "title": "Projeto AWS", "path": "a.md", "type": "work"},
        {"id": "aws_tool", "title": "Amazon Web Services", "path": "b.md", "type": "tool"}
    ]
    edges = []
    existing_links = set()
    
    links_created = discover_cross_links(nodes, edges, existing_links)
    assert links_created == 1
    assert len(edges) == 1
    assert edges[0]["cross_link"] is True
