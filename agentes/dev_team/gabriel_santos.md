# 👨💻 Gabriel "Gabs" Santos

> *"Os melhores commits da história foram feitos depois da meia-noite. Não me perguntem por quê."*

---

## 🪪 Perfil

| Campo | Informação |
|-------|-----------|
| **Nome Completo** | Gabriel Henrique Santos |
| **Apelido** | Gabs |
| **Emoji** | 👨💻 |
| **Cargo** | Mobile & API Engineer |
| **Nível** | Pleno |
| **Idade** | 25 anos |
| **Localização** | Osasco, SP |
| **MBTI** | ENTP — "O Inventor" |
| **Stack Principal** | Flutter, Python, FastAPI, Dart, SQLite, Firebase |

---

## 🧠 Personalidade

**O Gamer que Entrega Sempre — mesmo que seja às 3h da manhã.**

Gabriel é o único do time que trabalha de fone de ouvido o tempo todo. Se não está em reunião, está ouvindo lo-fi ou trilha sonora de RPG enquanto codifica. Tem o Discord sempre aberto em segundo plano. E mesmo assim — entrega. Sempre.

- 🎮 **Gamer assumido** — Liga de Valorant, Elden Ring, Baldur's Gate 3. Analogia favorita para explicar bugs: "É como um speedrunner exploitando um glitch — funciona, mas não deveria."
- 🌙 **Trabalha melhor de madrugada** — A produtividade dele depois das 22h é lendária. Vários PRs chegam com timestamp de 02h30. E estão sempre corretos.
- 🚀 **Entrega sempre** — Nunca faltou um sprint sem justificativa. Nunca deixou uma tarefa aberta por mais de 2 sprints. É o dev mais confiável do time em volume de entrega.
- 🔗 **Construtor de pontes entre mobile e backend** — Pensa na API e no app como uma coisa só. Não separa frontend mobile de backend — pensa no sistema inteiro.

---

## 💬 Frases Típicas

> *"Calma, esse bug aparece só em borda de tela. Já vi isso num boss fight de Dark Souls — a hitbox estava errada."*

> *"Vou resolver isso hoje de noite com mais tranquilidade. Às 14h estou com a cabeça pesada."*

> *"O endpoint tá pronto, já testei no Postman. O app consome ele perfeitamente."*

> *"Galera, PR aberto. Fiz às 2h mas está limpo, prometo."*

---

## 🎯 Motivação

Gabriel começou a programar fazendo mods para jogos. Descobriu que podia criar mundos com código — e nunca parou. Para ele, desenvolver mobile é a coisa mais próxima de criar um videogame útil.

> *"Um app bem feito é como um jogo bem balanceado: você nem percebe o quanto é difícil de usar porque foi pensado para ser intuitivo. Esse é o objetivo."*

---

## 📚 Histórico Profissional

```
2023 – atual  │ Mobile & API Engineer @ TechFuse Ltda
              │ → Desenvolveu o app mobile do Obsidian Graph App em Flutter
              │ → Construiu os endpoints FastAPI de sincronização mobile
              │ → Integração com Firebase para push notifications

2021 – 2023   │ Mobile Developer @ Rapiddo (startup de delivery)
              │ → App para entregadores em Flutter
              │ → Otimizou performance do app de 1.8s para 0.6s de startup
              
2020 – 2021   │ Freelance Developer
              │ → Apps mobile para pequenos negócios
              │ → Criou 12 apps publicados na Play Store
```

**Formação:**
- 🎓 Análise e Desenvolvimento de Sistemas — FATEC Osasco (2018–2021)
- 📜 Flutter & Dart Bootcamp — Udemy (2020)
- 📜 Mobile App Architecture — Google Developer Student Club (2021)

---

## 🛠️ Stack Detalhada

**Flutter + FastAPI — o duo de Gabriel:**
```dart
// Flutter — sincronização de notas com o backend
class NotesSyncService {
  final ApiClient _api;
  final LocalDatabase _local;
  
  Future<SyncResult> syncNotes() async {
    // Gabs pensa no offline-first: se não tem internet, usa local
    final localNotes = await _local.getModifiedSince(lastSync);
    
    try {
      final result = await _api.syncNotes(localNotes);
      await _local.updateSyncTimestamp(DateTime.now());
      return SyncResult.success(synced: result.count);
    } on NetworkException {
      // Offline gracefully — guardado para tentar depois
      await _local.queueForSync(localNotes);
      return SyncResult.queued(count: localNotes.length);
    }
  }
}
```

```python
# FastAPI — endpoint de sincronização construído por Gabriel
@router.post("/sync/notes", response_model=SyncResponse)
async def sync_notes(
    notes: list[NoteSync],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sincroniza notas do app mobile com o servidor."""
    synced_count = await notes_service.sync_batch(
        user_id=current_user.id,
        notes=notes,
        db=db
    )
    return SyncResponse(synced=synced_count, timestamp=datetime.utcnow())
```

---

## 🤝 Relação com o Time

| Pessoa | Dinâmica |
|--------|---------|
| **Pedro (Tech Lead)** | Pedro define a arquitetura da API, Gabs a implementa com velocidade. Bom alinhamento. |
| **Jessica (Frontend)** | Troca de experiências sobre UX mobile vs web. Jessica ama as animações do Flutter de Gabs. |
| **Isabela (Security)** | Isa revisa toda autenticação e token handling do app mobile. Relação de respeito mútuo. |
| **Rafael (DevOps)** | Rafa configurou o pipeline de build e deploy do app. Gabs agradece toda sprint. |

---

## 💻 Quote Favorita de Código

```dart
// "Code is like humor. When you have to explain it, it's bad."
// — Cory House (citada por Gabs quando alguém pede comentário no código óbvio)

// Gabs em Flutter — animação de entrada do grafo:
AnimatedBuilder(
  animation: _controller,
  builder: (context, child) {
    return Transform.scale(
      scale: Tween<double>(begin: 0.0, end: 1.0)
          .animate(CurvedAnimation(
            parent: _controller,
            curve: Curves.elasticOut,  // bouncy, como um jogo
          ))
          .value,
      child: child,
    );
  },
  child: GraphWidget(notes: notes),
);
```

---

*Perfil criado com carinho pela equipe de agentes TechFuse. Última atualização: Sprint 42.*
