import os
import json
import requests
import math
import glob
import logging
from datetime import datetime
from pypdf import PdfReader
from typing import List, Optional

from agent_core import (
    cosine_similarity,
    APP_DIR,
    DEFAULT_MODEL,
    EMBED_MODEL,
    OLLAMA_URL,
    EMBED_URL,
    get_model
)

logger = logging.getLogger(__name__)

class RAGAgent:
    """
    Agente RAG (Retrieval-Augmented Generation) responsável pela indexação semântica,
    geração de embeddings locais (Ollama) e busca de conhecimento no Vault do Felipe.
    """
    def __init__(self, knowledge_sources, cache_path=None):
        """
        Inicializa o RAGAgent com diretórios de conhecimento e arquivo de cache.
        Args:
            knowledge_sources (list): Lista de caminhos para os arquivos do Vault.
            cache_path (str, opcional): Caminho customizado para o cache de embeddings.
        """
        self.knowledge_sources = knowledge_sources
        if cache_path is None:
            self.cache_path = os.path.join(APP_DIR, "vault_embeddings.json")
        else:
            self.cache_path = cache_path
        self.embed_model = EMBED_MODEL
        self.llm_model = get_model()
        self.embed_url = EMBED_URL
        self.ollama_url = OLLAMA_URL
        self.cosine_similarity = cosine_similarity
        self.in_memory_cache = {}
        self.cache_mtime = 0.0
        self.index_progress = 0
        self.total_files = 0
        self.indexed_files = 0
        self.total_questions = 0
        self.areas = {}
        self.scan_files()

    def _get_cache(self) -> dict:
        """
        Retorna o cache de embeddings em memória, recarregando do disco de forma lazy
        apenas se o arquivo físico foi modificado (verificação via mtime).
        Retorna:
            dict: Cache mapeando nome de arquivo -> dados do embedding.
        """
        if not os.path.exists(self.cache_path):
            self.in_memory_cache = {}
            self.cache_mtime = 0.0
            return self.in_memory_cache

        try:
            current_mtime = os.path.getmtime(self.cache_path)
            if current_mtime > self.cache_mtime:
                logger.info("RAGAgent: Carregando cache de embeddings do disco para memória...")
                import fcntl
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    self.in_memory_cache = json.load(f)
                    fcntl.flock(f, fcntl.LOCK_UN)
                self.cache_mtime = current_mtime
        except Exception as e:
            logger.warning(f"RAGAgent: Erro ao ler cache de embeddings do disco: {e}")
        return self.in_memory_cache

    def scan_files(self):
        """
        Varre os diretórios de origem e mapeia arquivos totais, arquivos indexados,
        progresso da indexação e segmentação de áreas do conhecimento (MBA/Work/Tools).
        """
        all_files_info = []
        areas = {}
        for source in self.knowledge_sources:
            if os.path.isdir(source):
                files = glob.glob(os.path.join(source, "**/*.md"), recursive=True) + \
                        glob.glob(os.path.join(source, "**/*.pdf"), recursive=True)
                
                source_name = os.path.basename(source)
                for f in files:
                    rel = os.path.relpath(f, source)
                    area_name = rel.split(os.sep)[0]
                    if area_name.endswith('.md') or area_name.endswith('.pdf'): 
                        area_name = source_name
                    
                    if area_name not in areas: areas[area_name] = {"total": 0, "indexed": 0}
                    areas[area_name]["total"] += 1
                    all_files_info.append((f, area_name))

        self.total_files = len(all_files_info)
        cache = self._get_cache()
        self.indexed_files = len(cache)
        for f_path, area in all_files_info:
            if os.path.basename(f_path) in cache:
                areas[area]["indexed"] += 1
        
        if self.total_files > 0:
            self.index_progress = (self.indexed_files / self.total_files) * 100
        self.total_questions = sum(len(data.get('questions', [])) for data in cache.values())
        self.areas = areas

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Gera o vetor de embedding de 768 dimensões para o texto fornecido através da API local do Ollama.
        Args:
            text (str): Conteúdo textual para vetorização.
        Retorna:
            list[float]: Vetor de embeddings ou None em caso de falha.
        """
        try:
            r = requests.post(self.embed_url, json={"model": self.embed_model, "prompt": text}, timeout=10)
            if r.status_code == 200:
                return r.json().get("embedding")
        except Exception as e:
            logger.warning(f"Erro ao obter embedding: {e}")
        return None


    def update_embeddings(self, last_activity: str, background: bool = False) -> dict:
        all_files = []
        for source in self.knowledge_sources:
            if os.path.isdir(source):
                all_files.extend(glob.glob(os.path.join(source, "**/*.md"), recursive=True))
                all_files.extend(glob.glob(os.path.join(source, "**/*.pdf"), recursive=True))
        
        self.total_files = len(all_files)
        cache = self._get_cache()

        if not background:
            updated = False
            for f_path in all_files:
                filename = os.path.basename(f_path)
                if filename not in cache:
                    content = self._extract_content(f_path, limit_pages=5)
                    if content:
                        emb = self.get_embedding(f"{filename}: {content[:1000]}")
                        if emb:
                            cache[filename] = {"embedding": emb, "mtime": os.path.getmtime(f_path), "path": f_path, "questions": []}
                            updated = True
            if updated:
                import fcntl
                if not os.path.exists(self.cache_path):
                    try:
                        with open(self.cache_path, 'w', encoding='utf-8') as f:
                            json.dump({}, f)
                    except Exception as e:
                        logger.error(f"RAGAgent: Erro ao criar arquivo de cache vazio: {e}")
                
                try:
                    with open(self.cache_path, 'r+', encoding='utf-8') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        try:
                            disk_cache = json.load(f)
                        except Exception:
                            disk_cache = {}
                        disk_cache.update(cache)
                        f.seek(0)
                        f.truncate()
                        json.dump(disk_cache, f, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                        fcntl.flock(f, fcntl.LOCK_UN)
                    self.cache_mtime = os.path.getmtime(self.cache_path)
                except Exception as we:
                    logger.error(f"RAGAgent: Erro ao gravar cache de embeddings: {we}")
            
            self.indexed_files = len(cache)
            if self.total_files > 0:
                self.index_progress = (self.indexed_files / self.total_files) * 100
            return cache

        # Background heavy indexing
        files_to_process = [f for f in all_files if os.path.basename(f) not in cache or not cache[os.path.basename(f)].get('questions')]
        for f_path in files_to_process[:2]:
            filename = os.path.basename(f_path)
            content = self._extract_content(f_path, limit_pages=20)
            if content:
                chunks = [content[i:i+2500] for i in range(0, len(content), 2500)]
                question_embeddings = cache.get(filename, {}).get('questions', [])
                for chunk in chunks[:12]:
                    if (datetime.now() - last_activity).total_seconds() < 1200: break
                    try:
                        question_prompt = (
                            "Gere 10 perguntas variadas em português sobre o conteúdo abaixo. "
                            "Inclua perguntas factuais (quem, o quê, quando), analíticas (como, por quê) "
                            "e comparativas. Cada pergunta em uma linha separada.\n\n"
                            f"CONTEÚDO:\n{chunk}"
                        )
                        resp = requests.post(self.ollama_url, json={"model": self.llm_model, "prompt": question_prompt, "stream": False}, timeout=90)
                        if resp.status_code == 200:
                            qs = resp.json().get("response", "").split("\n")
                            for q in qs:
                                q_str = q.strip()
                                q_emb = self.get_embedding(q_str) if q_str else None
                                if q_emb: question_embeddings.append({"q": q_str, "emb": q_emb})
                    except Exception as e:
                        logger.warning(f"Erro ao gerar perguntas para chunk: {e}")
                        continue
                cache[filename] = {"embedding": self.get_embedding(filename), "mtime": os.path.getmtime(f_path), "path": f_path, "questions": question_embeddings}
                logger.info(f"RAGAgent: Indexado {filename}")
        
        import fcntl
        if not os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception as e:
                logger.error(f"RAGAgent: Erro ao criar arquivo de cache vazio: {e}")
        
        try:
            with open(self.cache_path, 'r+', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    disk_cache = json.load(f)
                except Exception:
                    disk_cache = {}
                disk_cache.update(cache)
                f.seek(0)
                f.truncate()
                json.dump(disk_cache, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f, fcntl.LOCK_UN)
            self.cache_mtime = os.path.getmtime(self.cache_path)
        except Exception as we:
            logger.error(f"RAGAgent: Erro ao gravar cache de embeddings de background: {we}")
        return cache

    def _extract_content(self, f_path: str, limit_pages: int = 5) -> str:
        try:
            if f_path.endswith('.md'):
                with open(f_path, 'r', encoding='utf-8') as f: return f.read()
            elif f_path.endswith('.pdf'):
                reader = PdfReader(f_path)
                return "\n".join([p.extract_text() for p in reader.pages[:limit_pages]])
        except Exception as e:
            logger.warning(f"Erro ao extrair conteudo de {f_path}: {e}")
            return ""

    def search(self, query: str, last_activity: str) -> str:
        query_emb = self.get_embedding(query)
        if not query_emb: return ""
        
        cache = self._get_cache()
        
        results = []
        for name, data in cache.items():
            doc_sim = self.cosine_similarity(query_emb, data['embedding'])
            qs_sim = max([self.cosine_similarity(query_emb, q['emb']) for q in data.get('questions', [])] or [0])
            score = max(doc_sim, qs_sim)
            if score > 0.4: results.append((score, data['path'], name))
        results.sort(reverse=True)
        
        context = []
        for score, path, name in results[:3]:
            content = self._extract_content(path, limit_pages=15)
            context.append(f"ARQUIVO: {name}\n{content[:12000]}")
        return "\n\n---\n\n".join(context)

    def get_index_status(self) -> dict:
        return {
            "percentage": round(self.index_progress, 1),
            "indexed": self.indexed_files,
            "total": self.total_files,
            "questions": self.total_questions,
            "areas": self.areas
        }
