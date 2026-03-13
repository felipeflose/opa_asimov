import faiss
import numpy as np
import pandas as pd
import google.generativeai as genai
import os

class VectorStore:
    def __init__(self, model_name='models/embedding-001'):
        self.model_name = model_name
        self.index = None
        self.dimension = None
        self.metadata = pd.DataFrame(columns=['id', 'text', 'source'])

    def initialize(self, dimension=768):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)

    def _get_embeddings(self, texts):
        # Usando a API do Gemini para embeddings (Leve e rápido!)
        result = genai.embed_content(
            model=self.model_name,
            content=texts,
            task_type="retrieval_document"
        )
        return np.array(result['embedding'])

    def add_texts(self, texts, sources=None):
        if not texts:
            return
        embeddings = self._get_embeddings(texts)
        if self.index is None:
            self.initialize(embeddings.shape[1])
        
        start_id = len(self.metadata)
        ids = np.arange(start_id, start_id + len(texts)).astype('int64')
        
        self.index.add(np.array(embeddings).astype('float32'))
        
        new_metadata = pd.DataFrame({
            'id': ids,
            'text': texts,
            'source': sources if sources else ['unknown'] * len(texts)
        })
        self.metadata = pd.concat([self.metadata, new_metadata], ignore_index=True)

    def search(self, query, top_k=5):
        if self.index is None:
            return []
        
        # Embedding da query via Gemini API
        query_result = genai.embed_content(
            model=self.model_name,
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = np.array([query_result['embedding']])
        
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                results.append({
                    'text': self.metadata.iloc[idx]['text'],
                    'source': self.metadata.iloc[idx]['source'],
                    'distance': float(distances[0][i])
                })
        return results

    def save(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        faiss.write_index(self.index, os.path.join(folder_path, 'index.faiss'))
        self.metadata.to_parquet(os.path.join(folder_path, 'embeddings.parquet'))

    def load(self, folder_path):
        self.index = faiss.read_index(os.path.join(folder_path, 'index.faiss'))
        self.metadata = pd.read_parquet(os.path.join(folder_path, 'embeddings.parquet'))
        self.dimension = self.index.d
