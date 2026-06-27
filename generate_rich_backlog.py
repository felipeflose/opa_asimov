import os
import json
import random
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')

def generate_backlog():
    # Estruturas ricas para gerar dados realistas e contextuais
    components_info = {
        "RAGAgent": {
            "adjusts": [
                "Indexação de vetores em memória no cache vetorial",
                "Fatiamento de texto (chunking) utilizando delimitadores de cabeçalho Markdown",
                "Carregamento lazy das bases de embeddings de PDFs",
                "Estratégia de limpeza periódica de mtime inválidos"
            ],
            "justifications": [
                "Evita estouros de buffer ao lidar com PDFs densos das matérias de MBA.",
                "Reduz a latência de busca semântica para manter interações no Telegram abaixo de 2s.",
                "Impede falhas de consistência quando notas do Obsidian são alteradas simultaneamente.",
                "Garante que o contexto enviado ao Ollama contenha apenas trechos altamente relevantes."
            ]
        },
        "Telegram Bot": {
            "adjusts": [
                "Fila SQLite de diagramas técnicos Napkin",
                "Mecanismo de transcrição de áudio via Whisper local com divisão em lotes",
                "Tratamento de rate limits de APIs externas",
                "Cache local para sessões de histórico de conversação do Felipe"
            ],
            "justifications": [
                "Evita perda de solicitações de diagramas caso o bot sofra quedas ou reinicializações.",
                "Garante que anotações de voz longas não causem travamentos no event loop do bot.",
                "Mantém a responsividade mesmo em cenários de alta concorrência de mensagens.",
                "Garante segurança no tráfego de dados e respeito às cotas de mensagens da API do Telegram."
            ]
        },
        "D3.js Graph": {
            "adjusts": [
                "Força de colisão e distância de links do layout D3.js",
                "Filtro de visualização para esconder links redundantes e cross-links",
                "Sistema de busca autocompletável com pulsação visual no nó selecionado",
                "Persistência local de posições customizadas arrastadas no localStorage"
            ],
            "justifications": [
                "Reduz o ruído visual no dashboard em grafos densos com mais de 500 nós.",
                "Melhora o tempo de carregamento da interface removendo loops de renderização infinitos.",
                "Permite navegação interativa e focada nas competências mais relevantes do Felipe.",
                "Evita que o usuário perca arranjos manuais estratégicos do grafo ao recarregar."
            ]
        },
        "Flask App Dashboard": {
            "adjusts": [
                "Endpoint de telemetria HTTP assíncrona do Bot",
                "Rate limit por IP e chave de acesso administrativa X-API-Key",
                "Transmissão SSE (Server-Sent Events) para logs do gerador em tempo real",
                "Compressão GZIP de pacotes JSON para o frontend"
            ],
            "justifications": [
                "Desacopla a escrita em disco e previne race conditions críticas.",
                "Impede acessos não autorizados a endpoints de execução do pipeline.",
                "Oferece feedback visual imediato ao Felipe durante a sincronização das notas.",
                "Reduz o consumo de banda de rede de 800KB para menos de 150KB por requisição."
            ]
        },
        "SQLite Persistent Queue": {
            "adjusts": [
                "Estrutura de tabelas e indexação de timestamp na fila de tarefas",
                "Tratamento de locks e timeouts em cenários concorrentes de gravação",
                "Lógica de reprocessamento automático de tarefas falhas",
                "Cleanup de registros antigos para evitar crescimento indefinido do banco"
            ],
            "justifications": [
                "Garante a durabilidade das tarefas de indexação em lote do Obsidian.",
                "Previne falhas de gravação concorrente quando o RAG e o Bot gravam ao mesmo tempo.",
                "Melhora a integridade das tarefas complexas e falhas temporárias do Ollama.",
                "Mantém a performance das consultas do banco de dados em níveis sub-milissegundo."
            ]
        },
        "Ollama Local Integration": {
            "adjusts": [
                "Prompts estruturados de saída JSON estrita",
                "Mecanismo de retries com backoff exponencial no Ollama",
                "Ajuste da temperatura e limites de tokens de contexto",
                "Fallback transparente para a API da Groq em falhas locais"
            ],
            "justifications": [
                "Previne que saídas malformadas do LLM quebrem o gerador do grafo.",
                "Torna a integração resiliente a indisponibilidades rápidas da GPU local.",
                "Melhora a consistência na classificação de notas em MBA, Work ou Tool.",
                "Garante o funcionamento do sistema mesmo em viagens ou indisponibilidade local."
            ]
        },
        "Docling PDF Converter": {
            "adjusts": [
                "Conversão e extração de tabelas de cronogramas HTML das aulas",
                "Rotina de tratamento de codificação de texto UTF-8",
                "Identificação de novos arquivos PDFs com prioridade na fila",
                "Limpeza de metadados redundantes no markdown final"
            ],
            "justifications": [
                "Garante a conversão precisa de materiais acadêmicos complexos.",
                "Impede falhas de renderização de caracteres acentuados comuns em português.",
                "Acelera a disponibilidade de resumos recém-adicionados no Google Drive.",
                "Reduz o tamanho dos documentos finais facilitando a geração de embeddings."
            ]
        },
        "Lineage Auditor": {
            "adjusts": [
                "Cálculo de similaridade de cosseno vetorizado com Numpy",
                "Busca e reconexão de nós órfãos no grafo Obsidian",
                "Detecção e deduplicação de nós conceitualmente idênticos",
                "Limitação de cross-links redundantes por nó"
            ],
            "justifications": [
                "Reduz o processamento matemático do grafo de minutos para milissegundos.",
                "Previne fragmentação e isolamento de conceitos no mapa de competências.",
                "Mantém o grafo limpo e semanticamente coerente ao longo do tempo.",
                "Evita o visual de 'teia de aranha' saturado de conexões desnecessárias."
            ]
        },
        "Health Monitor": {
            "adjusts": [
                "Checagem de processos ativos usando PIDs do sistema",
                "Log circular e salvamento de telemetria histórica de hardware",
                "Tratamento de alertas críticos via canal do Telegram",
                "Checagem de temperatura de CPU e uso de memória RAM do Flask"
            ],
            "justifications": [
                "Oferece visibilidade imediata de falhas críticas nos agentes em background.",
                "Permite analisar vazamentos de memória na execução prolongada do Flask.",
                "Previne superaquecimento e lentidão da máquina de desenvolvimento local.",
                "Garante que o Felipe seja alertado de forma proativa sobre problemas na infraestrutura."
            ]
        },
        "Sanitizer Pipeline": {
            "adjusts": [
                "Fusão de nós duplicados com preservação de arestas adjacentes",
                "Remoção física de arestas circulares (self-loops) redundantes",
                "Criação automática de backups rotativos em disco com limite de tamanho",
                "Validação de integridade do arquivo físico obsidian_graph.json"
            ],
            "justifications": [
                "Evita a perda de histórico de conexões do grafo durante higienizações.",
                "Impede travamentos visuais na renderização D3.js.",
                "Protege a base contra corrupção inesperada gerando pontos de restauração.",
                "Garante conformidade com o esquema JSON esperado pelo ecossistema."
            ]
        }
    }

    techniques = [
        "caching LRU em memória",
        "processamento paralelo",
        "estruturação JSON estrita",
        "debounce e throttling",
        "compressão de pacotes",
        "fallback resiliente",
        "logs centralizados",
        "álgebra linear vetorizada",
        "persistência assíncrona",
        "locks de concorrência"
    ]

    random.seed(42)
    improvements = []
    
    components = list(components_info.keys())
    
    # Gerar exatamente 10.000 melhorias estruturadas e ricas
    for i in range(1, 10001):
        comp = random.choice(components)
        comp_data = components_info[comp]
        
        adjust = random.choice(comp_data["adjusts"])
        justification = random.choice(comp_data["justifications"])
        technique = random.choice(techniques)
        
        # Criação de títulos e descrições ricos e dinâmicos
        priority = random.choice(["high", "medium", "low"])
        category = random.choice(["Performance", "RAG", "UI/UX", "Telegram", "Segurança", "DevOps", "Arquitetura"])
        difficulty = random.choice(["easy", "medium", "hard"])
        impact = random.choice(["low", "medium", "high"])
        
        title = f"IMP-{i:05d}: Otimização em {comp} ({category})"
        
        # Campos ricos solicitados pelo usuário
        description = f"Ajustar {adjust.lower()} aplicando {technique}."
        detail = f"Será implementado um módulo de refatoração no componente '{comp}' focado em '{adjust}'. O escopo do ajuste visa integrar melhores práticas de '{technique}', garantindo modularidade."
        motivation = f"Necessidade de mitigar problemas de consistência interna e vazamento de recursos. {justification}"
        
        status = "todo"
        if i <= 3:
            status = "in_progress"
        elif i <= 15:
            status = "done"
            
        improvements.append({
            "id": f"IMP-{i:05d}",
            "title": title,
            "description": description,
            "details": detail,
            "motivation_justification": motivation,
            "category": category,
            "status": status,
            "priority": priority,
            "difficulty": difficulty,
            "impact": impact,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat() if status == "done" else None
        })
        
    try:
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(improvements, f, ensure_ascii=False, indent=2)
        print(f"Sucesso: 10.000 melhorias ricas gravadas em {IMPROVEMENTS_FILE}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

if __name__ == '__main__':
    generate_backlog()
