import asyncio
from pathlib import Path

from fastmcp import Client

caminho_servidor = Path(__file__).parent / "06_servidor.py"
cliente_mcp = Client(caminho_servidor)


async def testar_servidor(cliente, nome_usuario, id_usuario):
    async with cliente:
        argumentos = {'nome_usuario': nome_usuario, "id_usuario": id_usuario}
        resultado = await cliente.call_tool("dar_bom_dia", arguments=argumentos)
        print(f'Resultado obtido do servidor MCP: {resultado}')


if __name__ == '__main__':
    # testar_servidor(cliente=cliente_mcp, nome_usuario="Juliano", id_usuario=5)  # Precisa ser async!
    asyncio.run(testar_servidor(cliente=cliente_mcp, nome_usuario="Flose", id_usuario=5))
