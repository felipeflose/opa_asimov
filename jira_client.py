import os
import json
import re
import logging
import requests
from typing import Optional
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, '.env'))

EPIC_CACHE_FILE = os.path.join(APP_DIR, 'epic_cache.json')

EPIC_CATEGORIES = [
    "Performance", "Security", "RAG/AI", "UI/UX",
    "DevOps", "Arquitetura", "Mobile", "QA", "Telegram"
]


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
        self._epic_cache = self._load_epic_cache()

    # ── Epic cache ────────────────────────────────────────────────────────────

    def _load_epic_cache(self) -> dict:
        """Carrega cache de épicos do disco."""
        if os.path.exists(EPIC_CACHE_FILE):
            try:
                with open(EPIC_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_epic_cache(self):
        """Persiste cache de épicos no disco."""
        try:
            with open(EPIC_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._epic_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"Não foi possível salvar epic_cache.json: {e}")

    # ── Epics ─────────────────────────────────────────────────────────────────

    def get_epics(self) -> list:
        """Busca todas as issues do tipo Epic no projeto."""
        url = f"{self.host}/rest/api/3/search/jql"
        params = {
            "jql": f"project = {self.project_key} AND issuetype = Epic",
            "maxResults": 100,
            "fields": "summary,status"
        }
        try:
            r = requests.get(url, headers=self.headers, auth=self.auth, params=params, timeout=15)
            if r.status_code == 200:
                return r.json().get("issues", [])
            logging.warning(f"Não foi possível buscar épicos (Status {r.status_code}).")
        except Exception as e:
            logging.warning(f"Erro ao buscar épicos no Jira: {e}")
        return []

    def _create_epic(self, categoria: str) -> Optional[str]:
        """Tenta criar um Epic no Jira. Retorna a key ou None."""
        url = f"{self.host}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"[ÉPICO] {categoria}",
                "issuetype": {"name": "Epic"},
            }
        }
        # Alguns Jira exigem o campo Epic Name
        try:
            # Tenta com campo customfield_10011 (Epic Name) — comum em Jira Cloud
            payload_with_name = json.loads(json.dumps(payload))
            payload_with_name["fields"]["customfield_10011"] = f"[ÉPICO] {categoria}"
            r = requests.post(url, headers=self.headers, auth=self.auth,
                              json=payload_with_name, timeout=15)
            if r.status_code == 201:
                key = r.json().get("key")
                logging.info(f"Épico '{categoria}' criado: {key}")
                return key
            # Tenta sem o campo customfield
            r2 = requests.post(url, headers=self.headers, auth=self.auth,
                               json=payload, timeout=15)
            if r2.status_code == 201:
                key = r2.json().get("key")
                logging.info(f"Épico '{categoria}' criado: {key}")
                return key
            logging.warning(f"Não foi possível criar épico '{categoria}' "
                            f"(Status {r2.status_code}): {r2.text[:200]}")
        except Exception as e:
            logging.warning(f"Erro ao criar épico '{categoria}': {e}")
        return None

    def ensure_epics(self) -> dict:
        """
        Garante que todos os épicos existem no Jira. Retorna dict {categoria: epic_key}.
        Usa cache em epic_cache.json para evitar duplicatas.
        Se Epic issue type não existir, usa label 'epic:{categoria}' como fallback.
        """
        # Verifica cache — só re-busca se faltarem categorias
        cached = {k: v for k, v in self._epic_cache.items() if k in EPIC_CATEGORIES}
        missing = [c for c in EPIC_CATEGORIES if c not in cached]

        if not missing:
            return cached

        # Busca épicos já existentes no Jira para evitar duplicar
        existing_epics = self.get_epics()
        for issue in existing_epics:
            summary = issue.get("fields", {}).get("summary", "")
            key = issue.get("key", "")
            for cat in EPIC_CATEGORIES:
                if f"[ÉPICO] {cat}" in summary and cat not in cached:
                    cached[cat] = key

        # Cria os que ainda faltam
        for cat in missing:
            if cat in cached:
                continue
            epic_key = self._create_epic(cat)
            if epic_key:
                cached[cat] = epic_key
            else:
                # Fallback: usa label como identificador virtual
                cached[cat] = f"label:epic:{cat}"
                logging.info(f"Usando label fallback para épico '{cat}'.")

        self._epic_cache.update(cached)
        self._save_epic_cache()
        return cached

    def add_epic_label(self, issue_key: str, categoria: str) -> bool:
        """Fallback: adiciona label 'epic:{categoria}' a uma issue existente."""
        url = f"{self.host}/rest/api/3/issue/{issue_key}"
        payload = {"update": {"labels": [{"add": f"epic:{categoria}"}]}}
        try:
            r = requests.put(url, headers=self.headers, auth=self.auth,
                             json=payload, timeout=15)
            if r.status_code in [200, 204]:
                logging.info(f"Label epic:{categoria} adicionada a {issue_key}.")
                return True
            logging.warning(f"Falha ao adicionar label em {issue_key} "
                            f"(Status {r.status_code}): {r.text[:200]}")
        except Exception as e:
            logging.warning(f"Erro ao adicionar label de épico em {issue_key}: {e}")
        return False

    # ── Issue ─────────────────────────────────────────────────────────────────

    def create_issue(self, summary, description, details="",
                     motivation_justification="", category="Arquitetura",
                     priority="medium", difficulty="medium", impact="medium",
                     source_user="", fingerprint="", epic_key: str = None):
        """Cria uma tarefa no Jira com metadados embutidos na descrição.

        Args:
            epic_key: key do épico pai (ex: 'KAN-5') ou 'label:epic:Categoria'.
                      Se começar com 'label:', usa label como fallback.
        """
        url = f"{self.host}/rest/api/3/issue"

        metadata = {
            "details": details,
            "motivation_justification": motivation_justification,
            "category": category,
            "priority": priority,
            "difficulty": difficulty,
            "impact": impact,
            "source_user": source_user,
            "fingerprint": fingerprint,
            "epic_key": epic_key or "",
        }

        metadata_str = f"\n\n--- METADADOS ---\n{json.dumps(metadata, ensure_ascii=False, indent=2)}"
        full_description = description + metadata_str

        fields: dict = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": full_description}]
                    }
                ]
            },
            "issuetype": {"name": self.issue_type},
        }

        # Vincula ao épico se existir chave real (não label-fallback)
        if epic_key and not epic_key.startswith("label:"):
            # Jira Cloud moderno usa "parent"
            fields["parent"] = {"key": epic_key}

        payload = {"fields": fields}

        try:
            r = requests.post(url, headers=self.headers, auth=self.auth,
                              json=payload, timeout=15)
            if r.status_code == 201:
                data = r.json()
                key = data.get("key")
                logging.info(f"Issue {key} criada no Jira com sucesso.")

                # Se épico é fallback por label, adiciona a label
                if epic_key and epic_key.startswith("label:"):
                    cat = epic_key.replace("label:epic:", "")
                    self.add_epic_label(key, cat)

                return key
            else:
                logging.error(f"Erro ao criar issue no Jira (Status {r.status_code}): {r.text}")
        except Exception as e:
            logging.error(f"Erro ao fazer request de criação no Jira: {e}")
        return None

    # ── Issues ────────────────────────────────────────────────────────────────

    def get_issues(self):
        """Busca todas as issues do projeto KAN no Jira e reconstrói o formato local."""
        url = f"{self.host}/rest/api/3/search/jql"

        params = {
            "jql": f"project = {self.project_key}",
            "maxResults": 100,
            "fields": "summary,description,status,created,updated,parent,labels"
        }

        try:
            r = requests.get(url, headers=self.headers, auth=self.auth,
                             params=params, timeout=20)
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
                    "Em análise": "in_analysis",
                    "Concluído": "done"
                }
                status = status_map.get(jira_status, "todo")

                # Epic key via parent
                parent_key = ""
                parent = fields.get("parent")
                if parent:
                    parent_key = parent.get("key", "")

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
                    "epic_key": metadata.get("epic_key", parent_key),
                    "created_at": fields.get("created"),
                    "completed_at": fields.get("updated") if status == "done" else None
                }
                local_backlog.append(task)

            return local_backlog
        except Exception as e:
            logging.error(f"Erro ao buscar/mapear issues do Jira: {e}")
        return []

    # ── Transition ────────────────────────────────────────────────────────────

    def transition_issue(self, issue_key, status_name):
        """Muda o status da issue baseado no nome do status."""
        url_trans = f"{self.host}/rest/api/3/issue/{issue_key}/transitions"
        try:
            r = requests.get(url_trans, headers=self.headers, auth=self.auth, timeout=10)
            if r.status_code != 200:
                logging.error(f"Erro ao obter transições para {issue_key}: {r.text}")
                return False

            transitions = r.json().get("transitions", [])
            transition_id = None
            for t in transitions:
                to_name = t.get("to", {}).get("name", "").lower()
                target_name = status_name.lower()
                if target_name in to_name or to_name in target_name:
                    transition_id = t.get("id")
                    break

            if not transition_id:
                logging.warning(f"Transição para '{status_name}' não encontrada para {issue_key}.")
                return False

            payload = {"transition": {"id": transition_id}}
            r_post = requests.post(url_trans, headers=self.headers, auth=self.auth,
                                   json=payload, timeout=15)
            if r_post.status_code in [204, 200]:
                logging.info(f"Issue {issue_key} transicionada para '{status_name}'.")
                return True
            else:
                logging.error(f"Falha ao transicionar {issue_key} "
                              f"(Status {r_post.status_code}): {r_post.text}")
        except Exception as e:
            logging.error(f"Erro ao transicionar issue no Jira: {e}")
        return False

    # ── Comment ───────────────────────────────────────────────────────────────

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
                        "content": [{"type": "text", "text": comment_text}]
                    }
                ]
            }
        }
        try:
            r = requests.post(url, headers=self.headers, auth=self.auth,
                              json=payload, timeout=15)
            if r.status_code == 201:
                logging.info(f"Comentário adicionado à issue {issue_key} no Jira.")
                return True
            else:
                logging.error(f"Erro ao adicionar comentário em {issue_key} "
                              f"(Status {r.status_code}): {r.text}")
        except Exception as e:
            logging.error(f"Erro ao fazer request de comentário no Jira para {issue_key}: {e}")
        return False
