import os

import dotenv
import requests
from fastmcp import FastMCP

servidor_mcp = FastMCP('mcp-tempo')


@servidor_mcp.tool()
async def buscar_tempo_atual(local: str) -> str:
    dotenv.load_dotenv()
    app_id = os.environ['CHAVE_API_OPENWEATHER']
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': local,
        'appid': app_id,
        'units': 'metric',
        'lang': 'pt_br',
    }
    resposta = requests.get(url=url, params=params)
    return resposta.json()


@servidor_mcp.tool()
async def buscar_previsao_tempo(local: str) -> str:
    dotenv.load_dotenv()
    app_id = os.environ['CHAVE_API_OPENWEATHER']
    url = f"https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': local,
        'appid': app_id,
        'units': 'metric',
        'lang': 'pt_br',
    }
    resposta = requests.get(url=url, params=params)
    return resposta.json()


if __name__ == "__main__":
    servidor_mcp.run(transport='sse')
