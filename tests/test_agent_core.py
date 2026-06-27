import os
import pytest
from agent_core import slugify, cosine_similarity, load_graph, save_graph

def test_slugify_basic():
    assert slugify("Hello World") == "hello_world"

def test_slugify_special_chars():
    assert slugify("Café & Résumé!") == "caf_r_sum"

def test_slugify_empty():
    assert slugify("") == ""

def test_slugify_numbers():
    assert slugify("Python 3.12") == "python_3_12"


def test_cosine_similarity_identical():
    v = [1.0, 0.0, 1.0]
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-5

def test_cosine_similarity_orthogonal():
    assert abs(cosine_similarity([1, 0], [0, 1]) - 0.0) < 1e-5

def test_cosine_similarity_empty():
    assert cosine_similarity([], [1, 2]) == 0.0
    assert cosine_similarity([1, 2], []) == 0.0

def test_cosine_similarity_opposite():
    assert abs(cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-5


def test_load_missing_file(temp_graph_path):
    """load_graph retorna estrutura vazia se arquivo nao existe."""
    result = load_graph()
    assert result == {"nodes": [], "edges": [], "metadata": {}}

def test_save_and_load_roundtrip(temp_graph_path):
    """save_graph + load_graph preserva dados."""
    nodes = [{"id": "root", "title": "Root"}, {"id": "node1", "title": "Test Node"}]
    edges = [{"source": "root", "target": "node1", "reasoning": "test"}]
    save_graph(nodes, edges, "test status")

    result = load_graph()
    assert len(result["nodes"]) == 2
    ids = {n["id"] for n in result["nodes"]}
    assert "node1" in ids
    assert len(result["edges"]) == 1
    assert result["metadata"]["status"] == "test status"

def test_save_merge_preserves_existing(temp_graph_path):
    """save_graph faz merge e nao sobrescreve nos existentes no disco."""
    # First save
    nodes1 = [{"id": "root", "title": "Root"}, {"id": "a", "title": "Node A"}]
    edges1 = [{"source": "root", "target": "a", "reasoning": "first"}]
    save_graph(nodes1, edges1, "first")

    # Second save with different node
    nodes2 = [{"id": "b", "title": "Node B"}]
    edges2 = [{"source": "root", "target": "b", "reasoning": "second"}]
    save_graph(nodes2, edges2, "second")

    result = load_graph()
    ids = {n["id"] for n in result["nodes"]}
    assert "a" in ids
    assert "b" in ids
    assert "root" in ids
    assert len(result["edges"]) == 2
