import httpx
import asyncio

async def test_napkin_v1():
    url = "https://api.napkin.ai/v1/visual"
    key = "sk-411843048d48c67b65d0b74af4b4c83fb742dc420e116bc1f3f2a4163f4ed6be"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "content": "A multi-agent AI system for business automation. Agents specialize in different tasks like research, legal audit, and devops.",
        "format": "png",
        "transparent_background": True
    }
    
    async with httpx.AsyncClient() as client:
        print("Testing v1/visual endpoint...")
        response = await client.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_napkin_v1())
