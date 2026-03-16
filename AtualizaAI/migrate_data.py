import os
from google.cloud import storage

def migrate_to_multitenancy(bucket_name, user_id="fflose"):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Lista todos os arquivos que NÃO estão em users/
    blobs = client.list_blobs(bucket)
    
    for blob in blobs:
        if not blob.name.startswith("users/"):
            new_name = f"users/{user_id}/{blob.name}"
            print(f"Migrating: {blob.name} -> {new_name}")
            
            # Copy to new location
            bucket.copy_blob(blob, bucket, new_name)
            # Optional: delete old location
            # blob.delete()

if __name__ == "__main__":
    project_id = "api-gemini-oficial" # Do .env
    bucket_name = f"flose-ai-platform-{project_id}"
    migrate_to_multitenancy(bucket_name)
    print("Migração concluída.")
