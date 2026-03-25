import os
from google.cloud import storage
import json
from datetime import datetime

class GCSClient:
    def __init__(self, bucket_name, project_id=None, credentials_path=None, user_id="fflose"):
        # Proteção extra para o project_id
        project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.user_id = user_id
        
        # Defesa contra troca de ordem de parâmetros:
        if credentials_path and not str(credentials_path).endswith(".json"):
            credentials_path = None
            
        if credentials_path:
            self.client = storage.Client.from_service_account_json(credentials_path)
        else:
            self.client = storage.Client(project=project_id)
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
        self._cache = {}

    def _full_path(self, path):
        # Ideia 9: Namespace por usuário
        return f"users/{self.user_id}/{path}"

    def upload_file(self, local_path, remote_path):
        try:
            path = self._full_path(remote_path)
            blob = self.bucket.blob(path)
            blob.upload_from_filename(local_path)
            if path in self._cache:
                del self._cache[path]
            print(f"Uploaded {local_path} to {path}")
            return True
        except Exception as e:
            print(f"Error uploading file {local_path}: {e}")
            return False

    def upload_json(self, data, remote_path):
        try:
            path = self._full_path(remote_path)
            blob = self.bucket.blob(path)
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
            self._cache[path] = (data, datetime.now())
            print(f"Uploaded JSON to {path}")
            return True
        except Exception as e:
            print(f"Error uploading JSON to {remote_path}: {e}")
            return False

    def download_file(self, remote_path, local_path):
        try:
            blob = self.bucket.blob(self._full_path(remote_path))
            blob.download_to_filename(local_path)
            return True
        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
            return False

    def read_json(self, remote_path, ttl=30):
        try:
            path = self._full_path(remote_path)
            now = datetime.now()
            if path in self._cache:
                cached_data, timestamp = self._cache[path]
                if (now - timestamp).seconds < ttl:
                    return cached_data

            blob = self.bucket.blob(path)
            if not blob.exists():
                return None
            content = blob.download_as_text()
            data = json.loads(content)
            self._cache[path] = (data, now)
            return data
        except Exception as e:
            print(f"Error reading JSON from {remote_path}: {e}")
            return None

    def list_files(self, prefix):
        blobs = self.client.list_blobs(self.bucket, prefix=self._full_path(prefix))
        return [blob.name for blob in blobs]

    def exists(self, path):
        blob = self.bucket.blob(self._full_path(path))
        return blob.exists()
