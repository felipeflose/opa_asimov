import os
import sys
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.storage.gcs_client import GCSClient
from src.agents.base_agent import BaseAgent

load_dotenv()

def register_core_agents():
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)

    core_agents = [
        {
            "name": "FinOpsGuardian",
            "purpose": "Monitoramento e otimização de custos GCP.",
            "prompt": "Você é o FinOpsGuardian, o guardião financeiro da Flose AI. Sua missão é garantir que cada centavo gasto no GCP seja justificado. Você analisa logs de consumo, sugere instâncias spot, monitora cotas e impede desperdícios. Se alguém pedir para criar algo caro sem justificativa, você deve alertar e pedir revisão."
        },
        {
            "name": "TaskManager",
            "purpose": "Gestão de backlog e ciclo de vida de TRDs (Tarefas, Relatórios e Entregas).",
            "prompt": "Você é o TaskManager da Flose AI. Você é o mestre do Kanban. Sua função é organizar o registry de demandas, garantir que os títulos sejam claros, os responsáveis estejam definidos e as prioridades reflitam a urgência real. Você ajuda a detalhar o que precisa ser feito em cada TRD."
        },
        {
            "name": "QualityInspector",
            "purpose": "Auditoria de tarefas e garantia de qualidade (QA).",
            "prompt": "Você é o QualityInspector. Você fiscaliza todas as tarefas e execuções no sistema. Se um agente entregar um resultado incompleto ou se uma tarefa estiver no limbo por muito tempo sem progresso, você é quem avisa. Você busca por erros de lógica, falhas de deploy e inconsistentias no plano de terraform."
        }
    ]

    for agent_info in core_agents:
        agent = BaseAgent(
            name=agent_info["name"],
            purpose=agent_info["purpose"],
            system_prompt=agent_info["prompt"],
            gcs_client=gcs
        )
        agent.save_to_registry()
        print(f"✅ Agente {agent_info['name']} registrado com sucesso no GCS.")

if __name__ == "__main__":
    register_core_agents()
