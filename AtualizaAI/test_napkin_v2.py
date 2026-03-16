import httpx
import asyncio

async def test_napkin():
    url = "https://api.napkin.ai/api/create-visual-request"
    key = "sk-411843048d48c67b65d0b74af4b4c83fb742dc420e116bc1f3f2a4163f4ed6be"
    headers = {
        "x-api-key": key, # Tentar x-api-key também
        "Content-Type": "application/json"
    }
    payload = {
        "text": "A multi-agent AI system for business automation. Agents specialize in different tasks like research, legal audit, and devops.",
    }
    
    async with httpx.AsyncClient() as client:
        # Tentativa 1: x-api-key
        print("Testing with x-api-key...")
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Tentativa 2: NAPKIN-ACCOUNT-API-KEY
        print("\nTesting with NAPKIN-ACCOUNT-API-KEY...")
        headers = {
            "NAPKIN-ACCOUNT-API-KEY": key,
            "Content-Type": "application/json"
        }
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_napkin())
