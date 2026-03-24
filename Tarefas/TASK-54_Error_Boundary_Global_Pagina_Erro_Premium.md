# TASK-54 | Error Boundary Global e Página de Erro Premium

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-54 |
| Grupo | Estabilidade / UX |
| Prioridade | Alta |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O `App.jsx` atual não tem nenhum Error Boundary. Se qualquer componente filho lançar um erro JavaScript não tratado (ex: `agentList.map is not a function` quando a API retorna erro), o React desmonta toda a árvore e mostra uma tela em branco.

Não há:
- Página de erro amigável com informações úteis
- Capacidade de tentar novamente sem reload completo
- Log do erro enviado para o GCS para diagnóstico

## Objetivo
Implementar um Error Boundary de classe React envolvendo o App, com uma página de erro premium que mostra o erro, opções de recuperação e registra o problema no GCS.

## Cenário Real
Um componente crasha → ao invés de tela branca, aparece uma página elegante: "SYSTEM_ERROR_DETECTED" com o stack trace mascarado, botão "Tentar Novamente" e botão "Reportar para Felipe". O erro é automaticamente salvo no GCS.

## Prompt para Antigravity

```
No `frontend/src/App.jsx` (ou novo arquivo `ErrorBoundary.jsx`):

1. COMPONENTE ERROR BOUNDARY (classe React):
```jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log para GCS via fetch não-bloqueante
    fetch('/api/errors/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
      })
    }).catch(() => {});
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorPage 
        error={this.state.error}
        onRetry={() => this.setState({ hasError: false, error: null })}
      />;
    }
    return this.props.children;
  }
}
```

2. COMPONENTE `<ErrorPage />`:
   Visual premium, full-screen:
   - Fundo: `radial-gradient(circle at center, #1a0505, #050505)`
   - Ícone grande: `⚠` em vermelho com `filter: drop-shadow(0 0 20px #ff4d4d)`
   - Título: "SYSTEM_ERROR_DETECTED" em fonte monospace, vermelho
   - Subtítulo: "Um componente falhou inesperadamente."
   - Código de erro mascarado: primeiros 100 chars do `error.message`
   - Timestamp do erro
   
   Botões:
   - `[↺ Tentar Novamente]` → chama `onRetry()`
   - `[⟳ Recarregar Página]` → `window.location.reload()`
   - `[📋 Copiar Diagnóstico]` → copia error.stack completo
   
   Rodapé: "Este erro foi registrado automaticamente."

3. NO `entrypoint.py`, criar `POST /api/errors/report`:
   - Salva o payload em `logs/frontend_errors/{timestamp}.json`
   - Retorna `{ logged: true }`

4. ENVOLVER o `<App />` no `main.jsx`:
```jsx
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

5. GUARDRAILS adicionais no App.jsx:
   - Trocar todos os `.map()` por `(array || []).map()`
   - Trocar todos `data.agents` por `data?.agents ?? []`
   - Verificar `agentList` e `tasks` antes de qualquer acesso
```

## Arquivos Envolvidos
- `frontend/src/main.jsx`
- `frontend/src/App.jsx` (ou novo `ErrorBoundary.jsx`)
- `entrypoint.py` (endpoint POST /api/errors/report)

## Critério de Conclusão
- Nenhum crash resulta em tela branca
- Página de erro visualmente consistente com o produto
- Botão "Tentar Novamente" funciona sem reload
- Erros logados no GCS automaticamente
- Optional chaining aplicado em todos os data accesses
