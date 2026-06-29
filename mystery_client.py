import os
import random
import requests
import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_LOG_FILE = os.path.join(APP_DIR, 'improvements_run_log.txt')

# Lista de arquivos elegíveis para alterações aleatórias de refatoração do cliente oculto
CANDIDATE_FILES = [
    "agent_sanitizer.py",
    "agent_health.py",
    "agent_core.py",
    "agent_rag.py"
]

def get_refactoring_from_llm(filepath, file_code):
    """Solicita ao LLM uma refatoração menor, limpa e segura ou adição de helper no arquivo."""
    prompt = f"""Você é o Cliente Oculto da AI Factory. Seu papel é fazer uma refatoração menor, otimização ou adicionar um helper útil e 100% seguro no código abaixo.

REGRAS:
1. O código gerado DEVE manter a compatibilidade completa e passar nos testes unitários.
2. Não altere comportamento existente, apenas otimize loops, adicione documentação robusta ou crie funções utilitárias menores de suporte.
3. Retorne APENAS o código completo do arquivo atualizado, sem nenhuma explicação ou blocos markdown.

---
ARQUIVO: {os.path.basename(filepath)}
CÓDIGO ATUAL:
{file_code}
---
CÓDIGO REFATORADO:"""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "gemma2-9b-it",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=30
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # Fallback Ollama Local
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4-fast:latest",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=60
        )
        if r.status_code == 200:
            return r.json()["response"].strip()
    except Exception:
        pass
        
    return ""

def main():
    # 25% de chance de rodar a cada execução do cron (para ser imprevisível e esporádico)
    if random.random() > 0.25:
        logging.info("Cliente Oculto ativo, mas decidiu pular esta rodada (probabilidade).")
        return

    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    # Escolhe um arquivo aleatório para auditar e alterar
    target_filename = random.choice(CANDIDATE_FILES)
    target_path = os.path.join(APP_DIR, target_filename)

    if not os.path.exists(target_path):
        return

    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        logging.info(f"Cliente Oculto selecionou o arquivo: {target_filename} para refatoração.")
        new_code = get_refactoring_from_llm(target_path, original_code)

        if not new_code or len(new_code) < 100 or "import" not in new_code:
            logging.error("Falha ao obter código refatorado válido do LLM.")
            return

        # Escreve o código alterado temporariamente no disco
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_code)

        # Roda os testes para validar se a alteração é segura
        pytest_path = os.path.join(APP_DIR, ".venv", "bin", "pytest")
        test_run = subprocess.run([pytest_path, "tests/"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if test_run.returncode == 0:
            # Testes passaram! Salva e comita direto na main silenciosamente
            logging.info("Refatoração validada com sucesso na suite de testes! Comitando na main...")
            
            subprocess.run(["git", "add", target_filename], cwd=APP_DIR)
            commit_msg = f"refactor({target_filename.split('_')[1].split('.')[0]}): silent optimization by mystery client"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR)
            
            # Registra no log de melhorias para visualização do backlog
            with open(RUN_LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MYSTERY-CLIENT] Refatoração aplicada em {target_filename}\n")
                
        else:
            # Testes falharam! Reverte a alteração imediatamente
            logging.warning("Refatoração quebrou os testes unitários! Revertendo arquivo...")
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(original_code)

    except Exception as e:
        logging.error(f"Erro na rotina do Cliente Oculto: {e}")

if __name__ == '__main__':
    main()
