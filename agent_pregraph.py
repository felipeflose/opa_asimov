import os
import json
import logging
from agent_core import local_ollama_call, DEFAULT_MODEL
from agent_parser import parse_filename

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Arquiteto de Grafos. Sua missão é ler uma lista de dezenas de arquivos e criar um "Dicionário Global de Taxonomia".
Você deve organizar a bagunça! Encontre os padrões lógicos e agrupe os arquivos.

Os arquivos estão listados no formato: [Categoria Original] -> Nome do Arquivo

Sua tarefa:
1. Extrair os "Super Nós" (Grouping Hubs) ideais que agrupam esses arquivos.
   - Para empregos, o Super Nó deve ser o NOME REAL DA EMPRESA (ex: "Leega", "Profarma", "Talent Group"). NÃO crie um hub genérico chamado "Empresa".
   - Para tecnologias, o Super Nó deve ser a ÁREA REAL (ex: "Engenharia de Dados", "Cloud", "Inteligência Artificial").
   - Para cursos/MBA, o Super Nó deve ser o MÓDULO REAL (ex: "Machine Learning Aplicado", "Fundamentos de IA").
2. Extrair as Tags Globais mais importantes que circundam esses arquivos.

**MUITO IMPORTANTE:** Não liste apenas empresas! Você deve listar cerca de 30 Grouping Hubs no total, mesclando Empresas, Áreas de Tecnologia e Módulos de MBA.

Retorne EXCLUSIVAMENTE um JSON válido neste formato:
{{
  "grouping_hubs": [
    "Leega",
    "Talent Group",
    "Engenharia de Dados",
    "Cloud Computing",
    "Machine Learning Aplicado"
  ],
  "global_tags": [
    "PYTHON",
    "AWS",
    "N8N",
    "SNOWFLAKE"
  ]
}}
NENHUM TEXTO ADICIONAL ALÉM DO JSON.
"""

def generate_global_taxonomy(vault_path: str, model: str = None) -> dict:
    if not model:
        model = DEFAULT_MODEL
        
    logger.info("Iniciando Fase 1: Varredura Global (Pre-Graph)...")
    
    files = [f for f in os.listdir(vault_path) if f.endswith('.md')]
    
    # Prepara a lista para o LLM
    file_list = []
    for f in files:
        parsed = parse_filename(f)
        file_list.append(f"[{parsed['category_hub_title']}] -> {parsed['name']}")
        
    # Como são 72 arquivos, podemos enviar em um único prompt
    prompt = "Lista de Arquivos do Cofre:\n" + "\n".join(file_list)
    
    try:
        taxonomy = local_ollama_call(prompt=prompt, system_prompt=SYSTEM_PROMPT, model=model)
        
        if not taxonomy:
            raise ValueError("Ollama retornou None ou vazio.")
            
        # Salva o arquivo localmente
        out_path = os.path.join(os.path.dirname(vault_path), "taxonomy_map.json")
        with open(out_path, 'w', encoding='utf-8') as fw:
            json.dump(taxonomy, fw, indent=2, ensure_ascii=False)
            
        logger.info(f"Taxonomia global gerada com sucesso! {len(taxonomy.get('grouping_hubs', []))} hubs encontrados.")
        return taxonomy
        
    except Exception as e:
        logger.error(f"Falha ao gerar Taxonomia Global: {e}")
        return {"grouping_hubs": [], "global_tags": []}

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    from agent_core import VAULT_PATH
    generate_global_taxonomy(VAULT_PATH)
