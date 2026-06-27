import os
import json
import pytest
import tempfile
from agent_rag import RAGAgent

@pytest.fixture
def temp_rag_setup():
    """Cria arquivos de origem temporários e caminho do cache temporário para o RAGAgent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_dir = os.path.join(tmpdir, "vault")
        os.makedirs(vault_dir, exist_ok=True)
        
        # Cria arquivos fake
        doc_path = os.path.join(vault_dir, "projeto_ia.md")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("Conteúdo sobre inteligência artificial e engenharia de dados.")
            
        cache_path = os.path.join(tmpdir, "embeddings_cache.json")
        yield [vault_dir], cache_path

def test_rag_agent_init(temp_rag_setup):
    sources, cache_path = temp_rag_setup
    agent = RAGAgent(sources, cache_path=cache_path)
    
    assert agent.cache_path == cache_path
    assert agent.total_files == 1
    assert agent.indexed_files == 0

def test_rag_agent_get_embedding(temp_rag_setup):
    sources, cache_path = temp_rag_setup
    agent = RAGAgent(sources, cache_path=cache_path)
    
    emb = agent.get_embedding("Teste de prompt")
    assert isinstance(emb, list)
    assert len(emb) == 768
    assert emb[0] == 0.1

def test_rag_agent_update_embeddings(temp_rag_setup):
    sources, cache_path = temp_rag_setup
    agent = RAGAgent(sources, cache_path=cache_path)
    
    cache = agent.update_embeddings(None, background=False)
    
    # O arquivo 'projeto_ia.md' deve ter sido indexado
    assert "projeto_ia.md" in cache
    assert len(cache["projeto_ia.md"]["embedding"]) == 768
    assert os.path.exists(cache_path)

def test_rag_agent_search(temp_rag_setup):
    sources, cache_path = temp_rag_setup
    agent = RAGAgent(sources, cache_path=cache_path)
    
    # Prepara cache fictício diretamente
    emb1 = [0.1] * 768
    emb2 = [0.9] * 768
    
    # Cria os arquivos que serão referenciados pelo cache_data no search
    os.makedirs(sources[0], exist_ok=True)
    with open(os.path.join(sources[0], "file1.md"), "w") as f:
        f.write("Conteúdo do arquivo 1")
    with open(os.path.join(sources[0], "file2.md"), "w") as f:
        f.write("Conteúdo do arquivo 2")
        
    cache_data = {
        "file1.md": {
            "embedding": emb1,
            "path": os.path.join(sources[0], "file1.md"),
            "questions": []
        },
        "file2.md": {
            "embedding": emb2,
            "path": os.path.join(sources[0], "file2.md"),
            "questions": []
        }
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)
        
    # Recarrega o RAGAgent
    agent = RAGAgent(sources, cache_path=cache_path)
    
    # Faz uma pesquisa simulada. O mock de get_embedding retorna [0.1]*768
    # A similaridade com 'file1.md' (que também tem [0.1]*768) será alta.
    from datetime import datetime
    result_context = agent.search("minha query de teste", datetime.now())
    
    # O resultado deve ser uma string contendo o conteúdo de file1.md
    assert "ARQUIVO: file1.md" in result_context
