import os
import google.generativeai as genai

class EvolutionJob:
    def __init__(self, gcs_client, orchestrator):
        self.gcs = gcs_client
        self.orchestrator = orchestrator

    def run(self):
        print("🧬 Iniciando Evolution Job...")
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        
        for agent in registry["agents"]:
            name = agent["agent_name"]
            perf = self.gcs.read_json(f"agents/performance/{name}.json")
            
            if not perf or not perf.get("history"): continue
            
            # Pega últimas 5 execuções
            recent = perf["history"][-5:]
            avg_conf = sum(e.get("confidence", 0.5) for e in recent) / len(recent)
            
            if avg_conf < 0.7:
                print(f"⚠️ Agente '{name}' com baixa performance ({avg_conf:.2f}). Iniciando evolução...")
                
                # Coleta feedbacks de melhoria
                improvements = [e.get("improvement") for e in recent if e.get("improvement")]
                
                # Cria tarefa de evolução no orquestrador
                task_desc = f"""
                O Agente '{name}' está falhando em atingir confiança alta (Média: {avg_conf:.2f}).
                Feedbacks coletados: {improvements}
                
                AÇÃO REQUERIDA:
                1. Analise o prompt atual do agente.
                2. Sugira uma nova versão do system_prompt que corrija as falhas.
                3. O orchestrator deve então chamar UPDATE_AGENT com o novo prompt.
                """
                
                # O Cérebro decide o que fazer
                self.orchestrator.process_command(f"[EVOLUTION SYSTEM]: {task_desc}")

        return "Evolution checks complete."
