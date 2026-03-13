import os
from google.cloud import storage
import json

class GCSClient:
    def __init__(self, bucket_name, project_id=None, credentials_path=None):
        # Proteção extra para o project_id
        project_id = project_id or os.getenv("GCP_PROJECT_ID")
        
        # Defesa contra troca de ordem de parâmetros:
        if credentials_path and not str(credentials_path).endswith(".json"):
            credentials_path = None
            
        if credentials_path:
            self.client = storage.Client.from_service_account_json(credentials_path)
        else:
            # Forçamos o project_id aqui para evitar OSError no Windows
            self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(self, local_path, remote_path):
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        print(f"Uploaded {local_path} to {remote_path}")

    def upload_json(self, data, remote_path):
        blob = self.bucket.blob(remote_path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        print(f"Uploaded JSON to {remote_path}")

    def download_file(self, remote_path, local_path):
        blob = self.bucket.blob(remote_path)
        blob.download_to_filename(local_path)
        print(f"Downloaded {remote_path} to {local_path}")

    def read_json(self, remote_path):
        blob = self.bucket.blob(remote_path)
        if not blob.exists():
            return None
        content = blob.download_as_text()
        return json.loads(content)

    def list_files(self, prefix):
        blobs = self.client.list_blobs(self.bucket, prefix=prefix)
        return [blob.name for blob in blobs]

    def exists(self, path):
        blob = self.bucket.blob(path)
        return blob.exists()
