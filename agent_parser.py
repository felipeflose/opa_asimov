import re
from agent_core import slugify

def parse_filename(filename: str) -> dict:
    """
    Extrai estrutura hierárquica diretamente do nome do arquivo.
    """
    clean_name = filename.replace('.md', '')
    
    # Lida com bug de exportação onde o nome é duplicado
    parts = clean_name.split('_')
    
    prefix = parts[0] if len(parts) > 0 else 'Desconhecido'
    section = parts[1] if len(parts) > 1 else 'Geral'
    
    # O nome do arquivo (leaf node) é o restante
    if len(parts) > 2:
        name = '_'.join(parts[2:])
    else:
        name = section
        
    # Desduplicação do nome (caso do bug do Obsidian onde section == name)
    if name.startswith(section + "_") or name == section:
        pass # Sometimes section is part of the name, we handle known cases below
        
    # Limpa duplicata se a primeira metade for igual a segunda (e.g. "Analisando Dados_Analisando Dados")
    half = len(name) // 2
    if name[:half] == name[half+1:] and name[half] == '_':
        name = name[:half]

    node_type = "classificar"
    category_hub_id = "classificar_hub"
    category_hub_title = "🔍 CLASSIFICAR"
    type_hub_id = "classificar_hub"

    if prefix == 'CV':
        if 'Habilidades' in section or 'Competencias' in section:
            node_type = "tool"
            category_hub_id = "habilidades_hub"
            category_hub_title = "🔧 HABILIDADES"
            type_hub_id = "tool_hub"
        elif 'Certificacoes' in section:
            node_type = "tool"
            category_hub_id = "certificacoes_hub"
            category_hub_title = "🏆 CERTIFICAÇÕES"
            type_hub_id = "tool_hub"
        elif 'Experiencia' in section:
            node_type = "work"
            category_hub_id = "experiencia_hub"
            category_hub_title = "💼 EXPERIÊNCIA"
            type_hub_id = "work_hub"
        elif 'Formacao' in section:
            node_type = "work"
            category_hub_id = "formacao_hub"
            category_hub_title = "🎓 FORMAÇÃO"
            type_hub_id = "work_hub"
        elif 'Idiomas' in section:
            node_type = "tool"
            category_hub_id = "idiomas_hub"
            category_hub_title = "🌐 IDIOMAS"
            type_hub_id = "tool_hub"
        elif 'Contato' in section:
            node_type = "work"
            category_hub_id = "perfil_hub"
            category_hub_title = "👤 PERFIL"
            type_hub_id = "work_hub"
    elif prefix == 'MBA':
        node_type = "mba"
        type_hub_id = "mba_hub"
        if section == 'Geral':
            category_hub_id = "mba_geral_hub"
            category_hub_title = "📚 MBA GERAL"
        else:
            category_hub_id = f"mba_{slugify(section)}_hub"
            category_hub_title = f"📚 MBA {section.upper()}"
    elif prefix == 'OpenClaw':
        node_type = "tool"
        category_hub_id = "openclaw_hub"
        category_hub_title = "🤖 OPENCLAW"
        type_hub_id = "tool_hub"

    # Seção pode estar vazia
    if not name:
        name = clean_name

    return {
        "prefix": prefix,
        "section": section,
        "name": name,
        "type": node_type,
        "category_hub_id": category_hub_id,
        "category_hub_title": category_hub_title,
        "type_hub_id": type_hub_id
    }

if __name__ == "__main__":
    tests = [
        "CV_Habilidades e Competencias_Amazon Web Services (AWS).md",
        "CV_Experiencia Profissional_Leega Arquiteto de Solucoes.md",
        "MBA_Geral_Analisando Dados com Pandas_Analisando Dados com Pandas.md",
        "OpenClaw_AGENTS.md"
    ]
    for t in tests:
        print(f"{t} -> {parse_filename(t)}")
