import os
import shutil
import pytest
from agent_core import load_graph, save_graph
from agent_sanitizer import sanitize_graph, _backup_graph

def test_backup_graph_disk_warning(temp_graph_path, monkeypatch, caplog):
    """Valida se o aviso de espaço em disco é emitido se o armazenamento livre for menor que 500 MB."""
    # Primeiro grava algo para poder fazer backup
    save_graph([{"id": "a"}], [])
    
    # Mock do shutil.disk_usage para retornar menos de 500 MB (ex: 100 MB)
    def mock_disk_usage(path):
        return (1000 * 1024 * 1024, 900 * 1024 * 1024, 100 * 1024 * 1024)
        
    monkeypatch.setattr(shutil, "disk_usage", mock_disk_usage)
    
    # Importante: limpar caplog e setar level de log
    import logging
    caplog.set_level(logging.WARNING)
    
    _backup_graph()
    
    # Verifica se apareceu warning
    warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("Espaço em disco criticamente baixo" in w for w in warnings)

def test_sanitize_graph_deduplication(temp_graph_path):
    """Testa se sanitize_graph funde nós de mesmo tipo e título normalizado."""
    # Grava estado inicial
    nodes = [
        {"id": "mestre", "type": "classificar", "title": "Mestre"},
        {"id": "tool_hub", "type": "classificar", "title": "Ferramentas"},
        {"id": "python_1", "type": "tool", "title": "Python"},
        {"id": "python_2", "type": "tool", "title": "python"},  # Duplicado (case insensitive)
        {"id": "habilidade_a", "type": "mba", "title": "Habilidade A"}
    ]
    edges = [
        {"source": "mestre", "target": "python_1", "reasoning": "conecta"},
        {"source": "mestre", "target": "python_2", "reasoning": "conecta duplicado"},
        {"source": "python_1", "target": "habilidade_a", "reasoning": "outra"}
    ]
    save_graph(nodes, edges)
    
    sanitize_graph()
    
    # Verifica resultado
    graph = load_graph()
    new_nodes = graph["nodes"]
    new_edges = graph["edges"]
    
    # O nó duplicado "python_2" deve ter sido fundido em "python_1"
    # Portando, o número de nós totais deve ser menor
    ids = {n["id"] for n in new_nodes}
    assert "python_1" in ids
    assert "python_2" not in ids
    
    # As edges que apontavam para "python_2" devem ter sido redirecionadas para "python_1"
    # E deduplicadas (evitando links idênticos de mestre -> python_1)
    # Então teremos mestre -> python_1 (1 link) e python_1 -> habilidade_a (1 link)
    assert len(new_edges) == 2
    for e in new_edges:
        assert e["source"] != "python_2"
        assert e["target"] != "python_2"

def test_sanitize_graph_root_map_merges(temp_graph_path):
    """Testa se nós que batem em ROOT_MAP (ex: WORK, TRABALHO) são mesclados aos super-hubs corretos."""
    nodes = [
        {"id": "work_hub", "type": "classificar", "title": "Trabalho Hub"},
        {"id": "node_trab", "type": "work", "title": "TRABALHO"}, # Deve fundir com work_hub
        {"id": "node_outros", "type": "work", "title": "Outro Nó"}
    ]
    edges = [
        {"source": "node_trab", "target": "node_outros", "reasoning": "conecta"}
    ]
    save_graph(nodes, edges)
    
    sanitize_graph()
    
    graph = load_graph()
    new_nodes = graph["nodes"]
    new_edges = graph["edges"]
    
    # O nó "node_trab" foi removido
    ids = {n["id"] for n in new_nodes}
    assert "node_trab" not in ids
    
    # A edge originária de "node_trab" deve ser redirecionada para "work_hub"
    assert len(new_edges) == 1
    assert new_edges[0]["source"] == "work_hub"
    assert new_edges[0]["target"] == "node_outros"
