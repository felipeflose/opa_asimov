import os
import json
import asyncio
from src.storage.gcs_client import GCSClient
from dotenv import load_dotenv

load_dotenv()

async def find_chat_id():
    # Usando o nome do bucket encontrado no main.py
    bucket_name = "flose-ai-platform"
    client = GCSClient(bucket_name)
    
    print(f"Buscando logs em: users/fflose/logs/telegram/")
    files = client.list_files("logs/telegram/")
    if not files:
        print("Nenhum log de Telegram encontrado.")
        return

    # Busca o log mais recente que tenha chat_id ou similar
    # O GCSClient.list_files retorna o caminho completo: users/fflose/logs/telegram/...
    # Precisamos remover o prefixo para ler via read_json se ele for mantido internamente.
    # Mas wait, o GCSClient.read_json já adiciona users/fflose/.
    
    for f in sorted(files, reverse=True)[:5]: # Tenta os 5 últimos
        path_in_user = f.replace("users/fflose/", "")
        data = client.read_json(path_in_user)
        if data and "chat_id" in data:
            print(f"CHAT_ID ENCONTRADO: {data['chat_id']}")
            return data['chat_id']
        elif data:
            # Talvez o chat_id esteja dentro de algum outro campo?
            print(f"Conteúdo do log {f}: {list(data.keys())}")
            
    print("Chat ID não encontrado nos logs recentes.")

if __name__ == "__main__":
    asyncio.run(find_chat_id())
