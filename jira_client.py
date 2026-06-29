import os
import json
import re
import logging
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, '.env'))

class JiraClient:
    def __init__(self):
        self.host = os.environ.get("JIRA_HOST", "").rstrip("/")
        self.email = os.environ.get("JIRA_EMAIL")
        self.token = os.environ.get("JIRA_API_TOKEN")
        self.project_key = "KAN"
        self.issue_type = "Tarefa"
        
        if not self.host or not self.email or not self.token:
            logging.warning("JiraClient inicializado com credenciais incompletas!")
            
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_issue(self, summary, description, details="", motivation_justification="", category="Arquitetura", priority="medium", difficulty="medium", impact="medium", source_user="", fingerprint=""):
        """Cria uma tarefa no Jira com os metadados embutidos na descrição."""
        url = f"{self.host}/rest/api/3/issue"
        
        metadata = {
            "details": details,
            "motivation_justification": motivation_justification,
            "category": category,
            "priority": priority,
            "difficulty": difficulty,
            "impact": impact,
            "source_user": source_user,
            "fingerprint": fingerprint
        }
        
        metadata_str = f"\n\n--- METADADOS ---\n{json.dumps(metadata, ensure_ascii=False, indent=2)}"
        full_description = description + metadata_str

        payload = {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": full_description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": self.issue_type
                }
            }
        }
        
        try:
            r = requests.post(url, headers=self.headers, auth=self.auth, json=payload, timeout=15)
            if r.status_code == 201:
                data = r.json()
                logging.info(f"Issue {data.get('key')} criada no Jira com sucesso.")
                return data.get("key")
            else:
                logging.error(f"Erro ao criar issue no Jira (Status {r.status_code}): {r.text}")
        except Exception as e:
            logging.error(f"Erro ao fazer request de criação no Jira: {e}")
        return None

    def get_issues(self):
        """Busca todas as issues do projeto KAN no Jira e reconstrói o formato local."""
        url = f"{self.host}/rest/api/3/search/jql"
        
        # Queremos buscar todas as issues do projeto KAN
        params = {
            "jql": f"project = {self.project_key}",
            "maxResults": 100,
            "fields": "summary,description,status,created,updated"
        }
        
        try:
            r = requests.get(url, headers=self.headers, auth=self.auth, params=params, timeout=20)
            if r.status_code != 200:
                logging.error(f"Erro ao buscar issues no Jira (Status {r.status_code}): {r.text}")
                return []
                
            issues_data = r.json().get("issues", [])
            local_backlog = []
            
            for issue in issues_data:
                key = issue.get("key")
                fields = issue.get("fields", {})
                summary = fields.get("summary", "")
                
                # Extrai descrição
                description_text = ""
                description_obj = fields.get("description")
                if description_obj and isinstance(description_obj, dict):
                    # No Jira v3 doc, o texto está aninhado
                    contents = description_obj.get("content", [])
                    texts = []
                    for content in contents:
                        for item in content.get("content", []):
                            if item.get("type") == "text":
                                texts.append(item.get("text", ""))
                    description_text = "\n".join(texts)
                elif isinstance(description_obj, str):
                    description_text = description_obj
                
                # Extrai metadados do final da descrição
                metadata = {}
                if "--- METADADOS ---" in description_text:
                    parts = description_text.split("--- METADADOS ---")
                    description_text = parts[0].strip()
                    try:
                        metadata = json.loads(parts[1].strip())
                    except Exception:
                        pass
                
                # Mapeia status do Jira para local
                jira_status = fields.get("status", {}).get("name", "A fazer")
                status_map = {
                    "A fazer": "todo",
                    "Em andamento": "in_progress",
                    "Em análise": "in_progress", # Se houver status intermediários
                    "Concluído": "done"
                }
                status = status_map.get(jira_status, "todo")
                
                # Cria o objeto de backlog local correspondente
                task = {
                    "id": key,
                    "title": summary,
                    "description": description_text,
                    "details": metadata.get("details", ""),
                    "motivation_justification": metadata.get("motivation_justification", ""),
                    "category": metadata.get("category", "Arquitetura"),
                    "status": status,
                    "priority": metadata.get("priority", "medium"),
                    "difficulty": metadata.get("difficulty", "medium"),
                    "impact": metadata.get("impact", "medium"),
                    "qualified": True,
                    "fingerprint": metadata.get("fingerprint", ""),
                    "source_user": metadata.get("source_user", ""),
                    "created_at": fields.get("created"),
                    "completed_at": fields.get("updated") if status == "done" else None
                }
                local_backlog.append(task)
                
            return local_backlog
        except Exception as e:
            logging.error(f"Erro ao buscar/mapear issues do Jira: {e}")
        return []

    def transition_issue(self, issue_key, status_name):
        """Muda o status da issue baseado no nome do status (A fazer, Em andamento, Concluído)."""
        # Primeiro, buscamos as transições disponíveis da issue para achar o transition ID
        url_trans = f"{self.host}/rest/api/3/issue/{issue_key}/transitions"
        try:
            r = requests.get(url_trans, headers=self.headers, auth=self.auth, timeout=10)
            if r.status_code != 200:
                logging.error(f"Erro ao obter transições para {issue_key}: {r.text}")
                return False
                
            transitions = r.json().get("transitions", [])
            transition_id = None
            for t in transitions:
                # Compara o nome do status de destino
                to_name = t.get("to", {}).get("name", "").lower()
                target_name = status_name.lower()
                
                # Mapeamento ou igualdade direta
                if target_name in to_name or to_name in target_name:
                    transition_id = t.get("id")
                    break
                    
            if not transition_id:
                logging.warning(f"Transição para '{status_name}' não encontrada para a issue {issue_key}.")
                return False
                
            # Executa a transição
            payload = {
                "transition": {
                    "id": transition_id
                }
            }
            r_post = requests.post(url_trans, headers=self.headers, auth=self.auth, json=payload, timeout=15)
            if r_post.status_code in [204, 200]:
                logging.info(f"Issue {issue_key} transicionada para '{status_name}' com sucesso.")
                return True
            else:
                logging.error(f"Falha ao transicionar issue {issue_key} (Status {r_post.status_code}): {r_post.text}")
        except Exception as e:
            logging.error(f"Erro ao transicionar issue no Jira: {e}")
        return False

    def add_comment(self, issue_key, comment_text):
        """Adiciona um comentário a uma issue no Jira (V3 REST API)."""
        url = f"{self.host}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment_text
                            }
                        ]
                    }
                ]
            }
        }
        try:
            r = requests.post(url, headers=self.headers, auth=self.auth, json=payload, timeout=15)
            if r.status_code == 201:
                logging.info(f"Comentário adicionado à issue {issue_key} no Jira.")
                return True
            else:
                logging.error(f"Erro ao adicionar comentário no Jira em {issue_key} (Status {r.status_code}): {r.text}")
        except Exception as e:
            logging.error(f"Erro ao fazer request de comentário no Jira para {issue_key}: {e}")
        return False
