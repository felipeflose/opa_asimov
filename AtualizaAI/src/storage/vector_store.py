import faiss
import numpy as np
import pandas as pd
import google.generativeai as genai
import os
from sklearn.decomposition import PCA

class VectorStore:
    def __init__(self, model_name='models/gemini-embedding-001', gcs_client=None):
        self.model_name = model_name
        self.gcs_client = gcs_client
        self.index = None
        self.dimension = None
        self.metadata = pd.DataFrame(columns=['id', 'text', 'source', 'type'])
        self.local_path = "tmp_vectors"
        
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)

    def initialize(self, dimension=768):
        self.dimension = dimension
        # Usamos IndexIDMap para manter IDs consistentes se necessário, ou IndexFlatL2 simples
        self.index = faiss.IndexFlatL2(dimension)

    def _get_embeddings(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        
        result = genai.embed_content(
            model=self.model_name,
            content=texts,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'])

    def add_texts(self, texts, sources=None, types=None):
        if not texts:
            return
        
        embeddings = self._get_embeddings(texts)
        if self.index is None:
            self.initialize(embeddings.shape[1])
        
        start_id = len(self.metadata)
        ids = np.arange(start_id, start_id + len(texts)).astype('int64')
        
        self.index.add(np.array(embeddings).astype('float32'))
        
        if sources and len(sources) == 1:
            sources = sources * len(texts)
        if types and len(types) == 1:
            types = types * len(texts)

        new_metadata = pd.DataFrame({
            'id': ids,
            'text': texts,
            'source': sources if sources else ['unknown'] * len(texts),
            'type': types if types else ['interaction'] * len(texts)
        })
        self.metadata = pd.concat([self.metadata, new_metadata], ignore_index=True)
        self.save()

    def search(self, query, top_k=5):
        if self.index is None or self.index.ntotal == 0:
            return []
        
        query_result = genai.embed_content(
            model=self.model_name,
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = np.array([query_result['embedding']])
        
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                meta = self.metadata.iloc[idx]
                results.append({
                    'text': meta['text'],
                    'source': meta['source'],
                    'type': meta['type'],
                    'distance': float(distances[0][i])
                })
        return results

    def save(self):
        idx_file = os.path.join(self.local_path, 'index.faiss')
        meta_file = os.path.join(self.local_path, 'metadata.parquet')
        
        faiss.write_index(self.index, idx_file)
        self.metadata.to_parquet(meta_file)
        
        if self.gcs_client:
            self.gcs_client.upload_file(idx_file, "vectors/index.faiss")
            self.gcs_client.upload_file(meta_file, "vectors/metadata.parquet")

    def load(self):
        if self.gcs_client:
            try:
                if self.gcs_client.exists("vectors/index.faiss"):
                    self.gcs_client.download_file("vectors/index.faiss", os.path.join(self.local_path, 'index.faiss'))
                    self.gcs_client.download_file("vectors/metadata.parquet", os.path.join(self.local_path, 'metadata.parquet'))
                    
                    self.index = faiss.read_index(os.path.join(self.local_path, 'index.faiss'))
                    self.metadata = pd.read_parquet(os.path.join(self.local_path, 'metadata.parquet'))
                    self.dimension = self.index.d
                    return True
            except Exception as e:
                print(f"Erro ao carregar vetores do GCS: {e}")
        return False

    def get_projections(self):
        """Retorna os dados projetados em 2D para visualização no dashboard."""
        if self.index is None or self.index.ntotal < 2:
            return None
        
        # Reconstrói os embeddings do índice (IndexFlat permite isso)
        embeddings = []
        for i in range(self.index.ntotal):
            embeddings.append(self.index.reconstruct(i))
        
        embeddings = np.array(embeddings)
        
        # Redução de dimensionalidade PCA
        pca = PCA(n_components=2)
        projections = pca.fit_transform(embeddings)
        
        df = self.metadata.copy()
        df['x'] = projections[:, 0]
        df['y'] = projections[:, 1]
        return df
