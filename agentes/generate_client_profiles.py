import os
import sys

# Garante que o diretório raiz está no path para importar annoying_user
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from annoying_user import USER_PERSONAS
except ImportError as e:
    print(f"Erro ao importar USER_PERSONAS: {e}")
    sys.exit(1)

CLIENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clientes')
os.makedirs(CLIENTS_DIR, exist_ok=True)

# Lista de localizações plausíveis no Brasil para dar variedade
LOCATIONS = [
    "São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG",
    "Porto Alegre, RS", "Curitiba, PR", "Florianópolis, SC",
    "Salvador, BA", "Recife, PE", "Fortaleza, CE", "Brasília, DF",
    "Campinas, SP", "São José dos Campos, SP", "Vitória, ES"
]

# Personalidades e Backstory baseados nas áreas
PERSONALITY_TRAITS = {
    "UI/UX": [
        "Visualmente obsessiva. Detesta desalinhamento de 1px.",
        "Advogada da acessibilidade e boas práticas do Fitts's Law.",
        "Sempre testando contrastes de cores no Figma."
    ],
    "Backend": [
        "Focada em performance e eficiência de algoritmos.",
        "Odeia race conditions e conexões não fechadas.",
        "Ama diagramas de arquitetura hexagonal."
    ],
    "Security": [
        "Paranoica de segurança (de forma profissional).",
        "Testa limites de payload e vetores de injeção.",
        "Sempre atenta ao rate limiting e encriptação."
    ],
    "Mobile": [
        "Focada em experiência em dispositivos móveis.",
        "Sempre testando consumo de bateria e comportamento em conexões instáveis.",
        "Advogada de PWAs e responsividade."
    ],
    "RAG/AI": [
        "Fascinada por embeddings e modelos de linguagem locais.",
        "Sempre avaliando a precisão do contexto do RAG.",
        "Odeia alucinações e perda de precisão de busca."
    ],
    "DevOps": [
        "Obsessiva com automação e pipelines de CI/CD.",
        "Detesta deploys manuais e scripts não documentados.",
        "Advogada de logs estruturados e monitoramento."
    ],
    "Frontend": [
        "Especialista em D3.js e interfaces dinâmicas.",
        "Detesta re-renderizações desnecessárias e travamentos na UI.",
        "Focada em performance de render no browser."
    ],
    "Data": [
        "Ama pipelines de dados estruturados e esquemas limpos.",
        "Focada em indexação de tabelas e performance do SQLite.",
        "Sempre atenta a vazamentos de memória em conjuntos de dados."
    ],
    "QA": [
        "Meticulosa ao extremo. Testa cada caso limite com afinco.",
        "Ama fixtures e mocks de banco de dados.",
        "Focada em cobertura de testes e prevenção de regressões."
    ],
    "Product": [
        "Focada na experiência geral e métricas de retenção.",
        "Detesta a falta de loops de feedback e bad user experience.",
        "Advogada de metodologias ágeis e metas claras."
    ],
    "SRE": [
        "Focada em observabilidade e monitoramento de saúde.",
        "Mede tempos de resposta p95 e p99 constantemente.",
        "Advogada de logs estruturados em JSON."
    ],
    "Full Stack": [
        "Fascinada pela integração de ponta a ponta.",
        "Gosta de ver fluxos de dados limpos do backend ao frontend.",
        "Sempre focada em modularização de código."
    ]
}

def generate_profiles():
    print(f"Iniciando geração autônoma de {len(USER_PERSONAS)} perfis de clientes...")
    
    for idx, persona in enumerate(USER_PERSONAS):
        name = persona["name"]
        emoji = persona["emoji"]
        role = persona["role"]
        area = persona["area"]
        meta = persona["meta"]
        templates = persona.get("templates", [])
        
        # Nome limpo para o arquivo
        filename = name.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ã", "a").replace("õ", "o").replace("ç", "c") + ".md"
        filepath = os.path.join(CLIENTS_DIR, filename)
        
        # Localização e características
        location = LOCATIONS[idx % len(LOCATIONS)]
        traits = PERSONALITY_TRAITS.get(area, [
            "Focada em melhorias contínuas de software.",
            "Testadora dedicada do Obsidian Graph App.",
            "Gosta de feedbacks estruturados e claros."
        ])
        
        # Conteúdo do perfil
        content = f"""Nome: {name}
Emoji: {emoji}
Cargo: {role}
Idade: {25 + (idx % 15)}
Localização: {location}
Área de Atuação: {area}
Meta de Demandas Aceitas: {meta:,}

Personalidade:
"""
        for trait in traits:
            content += f"- {trait}\n"
            
        content += f"""
Motivação:
- "Quero que o Obsidian Graph App chegue ao estado da arte em {area.lower()}."

Perfil de Demanda:
- Sempre embasa seus pedidos com evidências métricas sólidas.
- Foca em resolver gargalos críticos da área de {area.lower()}.
- Busca evoluir suas demandas rejeitadas adicionando dados de performance e I/O.

Modelos de Reclamações Comuns (Templates):
"""
        for template in templates:
            content += f"- \"{template}\"\n"
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"  [CRIADO] {emoji} {name} -> {filename}")
        
    print("Processo autônomo concluído com sucesso!")

if __name__ == '__main__':
    generate_profiles()
