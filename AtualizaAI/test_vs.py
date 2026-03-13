import sys
import os
sys.path.append(os.getcwd())
from src.storage.vector_store import VectorStore
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    vs = VectorStore()
    print("VectorStore initialized!")
    # Test small add
    try:
        vs.add_texts(["Olá mundo", "Teste de memória"], sources=["test"], types=["debug"])
        print("Texts added!")
        res = vs.search("Olá")
        print(f"Search result: {res}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("GEMINI_API_KEY not found")
