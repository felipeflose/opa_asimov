import asyncio
import os

import dotenv
from fastmcp import Client
from google import genai
from google.genai import types 

# 1. PRINT: Mostra o caminho do servidor sendo usado
caminho_servidor = 'http://localhost:8000/sse'
print(f"1. Caminho do servidor MCP: {caminho_servidor}")

# 2. PRINT: Mostra que o objeto Client foi criado
cliente_mcp = Client(caminho_servidor)
print("2. Objeto cliente_mcp criado.")


# --- BLOCO: LISTAGEM DE MODELOS (SÍNCRONA) ---
def listar_modelos(api_key):
    """Lista e exibe os modelos disponíveis com a API Key fornecida."""
    try:
        # Inicializa o cliente GenAI para a listagem
        list_client = genai.Client(api_key=api_key)
        
        print("\n--- INÍCIO DA LISTAGEM DE MODELOS DISPONÍVEIS ---")
        
        # O método client.models.list() retorna uma lista de objetos Model
        models = list_client.models.list()
        
        model_names = [model.name for model in models]
        
        # 14. PRINT: Exibe a lista
        print(f"14. Modelos disponíveis com este token (total: {len(model_names)}):")
        
        # Filtra e exibe os modelos de interesse (chat e vision/pro)
        chat_models = [name for name in model_names if 'gemini-2.5-flash' in name or 'gemini-2.5-pro' in name]
        
        print("\n   🤖 Modelos de Chat/Geração de Conteúdo:")
        for name in sorted(chat_models):
            # 15. PRINT: Modelo listado
            print(f"      - {name}")
            
        print("--- FIM DA LISTAGEM DE MODELOS DISPONÍVEIS ---")
        
    except Exception as e:
        print(f"\n[ERRO NA LISTAGEM DE MODELOS] Não foi possível listar os modelos. Verifique o token e a conexão. Erro: {e}")
# ------------------------------------------------


async def testar_servidor(cliente, busca, api_key): # A chave foi passada como argumento
    # 3. PRINT: Indica o início da função assíncrona
    print(f"\n3. Iniciando testar_servidor com busca: '{busca}'")

    # Inicializa o cliente GenAI SÍNCRONO (sem await na chamada principal)
    client = genai.Client(api_key=api_key)
    
    async with cliente:
        print("6. Conexão assíncrona com o servidor MCP estabelecida.")
        
        # 7. PRINT: Mostra qual ferramenta e argumentos estão sendo chamados
        print(f"7. Chamando tool 'buscar_wikipedia' com argumentos: {{'busca': '{busca}'}}...")
        # Esta chamada *deve* ter 'await' porque o cliente_mcp é assíncrono
        resultado = await cliente.call_tool("buscar_wikipedia", arguments={'busca': busca})
        
        # 8. PRINT: Mostra o resultado bruto retornado pela ferramenta
        print("\n8. Resultado bruto da ferramenta 'buscar_wikipedia':")
        print(resultado)
        print("---")

        # PARÂMETRO DA MENSAGEM DO SISTEMA (para Gemini)
        mensagem_sistema = f"""
        Você é um bot que faz buscas no wikipedia e sintetiza a resposta.
        O usuário buscou pelo seguinte tema: "{busca}".
        Para esta busca, você recebeu a seguinte resposta: "{resultado}".
        Com base nesse conteúdo, formate uma resposta amigável ao usuário.
        """
        # 9. PRINT: Mostra a mensagem de sistema que será enviada ao Gemini
        print("9. Mensagem de Sistema (Instructions) preparada para o Gemini.")

        # CHAMADA CORRIGIDA: Removido o 'await' para usar o cliente síncrono.
        response = client.models.generate_content(
            # MODELO ALTERADO: Usando um modelo Gemini rápido e disponível
            model="gemini-2.5-flash", 
            # CONTEÚDO (INPUT)
            contents="Pode me falar mais sobre este assunto?",
            # INSTRUÇÃO DO SISTEMA
            config=types.GenerateContentConfig(
                system_instruction=mensagem_sistema,
            ),
        )
        
        # 10. PRINT: Resultado final (texto sintetizado) do Gemini
        # O resultado do Gemini é acessado via .text
        print("\n10. Resposta sintetizada pelo Gemini (response.text):")
        print(response.text)


if __name__ == '__main__':
    dotenv.load_dotenv()
    print("4. Variáveis de ambiente carregadas (dotenv.load_dotenv()).")

    try:
        # Lendo a chave de ambiente do Gemini
        gemini_api_key = os.environ['GEMINI_API_KEY']
        print(f"5. GEMINI_API_KEY lida (termina em ...{gemini_api_key[-4:]}).")
        
        # Executa a função de listagem antes da chamada assíncrona principal
        listar_modelos(gemini_api_key)
        
        # 11. PRINT: Define a busca principal
        busca = 'Isaac Asimov'
        print(f"\n11. Variável de busca definida como: '{busca}'")
        
        # 12. PRINT: Inicia a execução do asyncio
        print("12. Iniciando loop de eventos com asyncio.run().")
        # Passando a chave para a função assíncrona
        asyncio.run(testar_servidor(cliente=cliente_mcp, busca=busca, api_key=gemini_api_key))
        print("\n13. Execução do script concluída.")
        
    except KeyError:
        print("\n[ERRO FATAL] A chave GEMINI_API_KEY não foi encontrada nas variáveis de ambiente. Verifique seu arquivo .env.")