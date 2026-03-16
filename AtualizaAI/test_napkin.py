import httpx
import asyncio

async def test_napkin():
    url = "https://api.napkin.ai/api/create-visual-request"
    key = "sk-411843048d48c67b65d0b74af4b4c83fb742dc420e116bc1f3f2a4163f4ed6be"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": "A multi-agent AI system for business automation. Agents specialize in different tasks like research, legal audit, and devops.",
        "style": "Sketch"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=60)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_napkin())
