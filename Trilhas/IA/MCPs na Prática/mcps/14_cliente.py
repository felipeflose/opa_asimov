import asyncio
import os
from pathlib import Path

import dotenv
from fastmcp import Client
from openai import OpenAI

caminho_servidor = Path(__file__).parent / "14_servidor_previsao_tempo.py"
cliente_mcp = Client(caminho_servidor)


async def testar_servidor(cliente, local):
    dotenv.load_dotenv()
    api_key = os.environ['CHAVE_API_OPENAI']
    async with cliente:
        resultado_atual = await cliente.call_tool("buscar_tempo_atual", arguments={'local': local})
        resultado_previsao = await cliente.call_tool("buscar_previsao_tempo", arguments={'local': local})
        mensagem_sistema = f"""
        Você é um bot que faz buscas de previsão de tempo e sintetiza a resposta.
        O usuário buscou pela previsão de tempo no seguinte local: "{local}".
        Para esta busca, você recebeu as seguintes respostas: 
        - tempo atual: {resultado_atual}
        - previsão para os próximos dias: {resultado_previsao}.
        Com base nesse conteúdo, formate uma resposta amigável ao usuário.
        """
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=mensagem_sistema,
            input="Qual a previsão do tempo no local indicado?",
        )
        print(response.output_text)


if __name__ == '__main__':
    local = 'Porto Alegre'
    asyncio.run(testar_servidor(cliente=cliente_mcp, local=local))
