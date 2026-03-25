import os
import json
import time
from typing import Optional, Any, List, Dict
from google.cloud import storage
from google.cloud.exceptions import NotFound
import structlog

logger = structlog.get_logger()

class StorageError(Exception):
    """Erro customizado de storage"""
    pass

class GCSClient:
    def __init__(self, bucket_name: str, cache_ttl: int = 30):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_from_cache(self, path: str) -> Optional[Any]:
        if path in self._cache:
            entry = self._cache[path]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._cache[path]
        return None

    def _save_to_cache(self, path: str, data: Any):
        self._cache[path] = {
            "data": data,
            "timestamp": time.time()
        }

    def get_json(self, path: str) -> Optional[Dict]:
        """Lê um arquivo JSON do GCS com cache"""
        cached = self._get_from_cache(path)
        if cached is not None:
            return cached

        try:
            blob = self.bucket.blob(path)
            content = blob.download_as_text()
            data = json.loads(content)
            self._save_to_cache(path, data)
            return data
        except NotFound:
            return None
        except Exception as e:
            logger.error("gcs_get_error", path=path, error=str(e))
            raise StorageError(f"Falha ao ler {path}: {str(e)}")

    def upload_json(self, data: Dict, path: str) -> bool:
        """Salva um dicionário como JSON no GCS"""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string(
                data=json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            self._save_to_cache(path, data)
            return True
        except Exception as e:
            logger.error("gcs_upload_error", path=path, error=str(e))
            raise StorageError(f"Falha ao salvar {path}: {str(e)}")

    def list_files(self, prefix: str) -> List[str]:
        """Lista arquivos com um prefixo"""
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error("gcs_list_error", prefix=prefix, error=str(e))
            raise StorageError(f"Falha ao listar {prefix}: {str(e)}")

    def delete(self, path: str) -> bool:
        """Deleta um arquivo do GCS"""
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            if path in self._cache:
                del self._cache[path]
            return True
        except NotFound:
            return False
        except Exception as e:
            logger.error("gcs_delete_error", path=path, error=str(e))
            raise StorageError(f"Falha ao deletar {path}: {str(e)}")
