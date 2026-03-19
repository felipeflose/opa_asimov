# opa_asimov


ao iniciar um dia de aula, fazer:

1 - git pull origin main

2 - git checkout -b aula_assunto_dia
    exemplo:
    aula_eng_24112025
	
3 - Faça as aulas e anotações:
    git add .
	
4 - git push origin nome_branch


------------------


.venv\Scripts\activate

------------------

## CI/CD Pipeline
Este repositório está configurado com **GitHub Actions** para CI/CD automático.
- Qualquer `push` ou `merge` na branch `main` dispara o deploy no **Google Cloud Run**.
- O Webhook do Telegram é atualizado automaticamente na esteira de deploy.



