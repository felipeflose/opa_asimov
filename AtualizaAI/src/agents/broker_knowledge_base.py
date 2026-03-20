PREREQUISITES_KB = {
    "elevenlabs": {
        "requires_account": True,
        "requires_api_key": True,
        "free_plan_limits": "10k caracteres/mês",
        "paid_plan": "Starter $5/mês",
        "api_endpoint": "https://api.elevenlabs.io/v1",
        "key_operations": ["text-to-speech", "voice-cloning", "list-voices"],
        "notes": "Voice cloning requer plano Creator ou superior"
    },
    "stripe": {
        "requires_account": True,
        "requires_api_key": True,
        "key_types": ["publishable_key", "secret_key"],
        "webhook": "Requer configuração de endpoint e secret para verificação",
        "notes": "Webhook precisa de raw body — não parsear JSON antes de verificar assinatura"
    },
    "openai": {
        "requires_account": True,
        "requires_api_key": True,
        "billing": "Pay-per-use, cartão de crédito obrigatório após trial",
        "notes": "Rate limits variam por tier. GPT-4 tem custo 30x maior que GPT-3.5"
    },
    "gcp": {
        "requires_account": True,
        "requires_billing": True,
        "notes": "Billing precisa estar ativado mesmo para serviços gratuitos. APIs precisam ser habilitadas individualmente no Console."
    },
    "telegram": {
        "requires_bot_token": True,
        "how_to_get": "Criar bot via @BotFather",
        "webhook_vs_polling": "Webhook requer URL HTTPS pública. Polling funciona localmente.",
        "notes": "Limite de 30 mensagens/segundo por bot"
    },
    "napkin": {
        "requires_account": True,
        "requires_api_key": True,
        "notes": "API ainda em beta, pode ter instabilidades. Bearer token no header."
    }
}
