# TASK-33 | Loading Screen com Animação Orbital

## Metadata
| Campo | Valor |
|---|---|
| ID | TASK-33 |
| Grupo | UX / Design |
| Prioridade | Média |
| Responsável | FrontendAgent |
| Status | Aberto |

## Problema Identificado
O app carrega em branco por 1-3 segundos antes de mostrar qualquer conteúdo. Não existe feedback visual de que o sistema está inicializando. Isso transmite a percepção de lentidão e quebra a experiência premium.

## Objetivo
Criar uma splash screen de carregamento que aparece entre o login e o dashboard principal, com animação que reflita a identidade visual do Flose AI.

## Cenário Real
Usuário faz login → tela preta → dashboard aparece abruptamente.
Com a task: login → splash animada com logo + texto "Iniciando sistemas..." → dashboard com fade-in suave.

## Prompt para Antigravity

```
No `frontend/src/App.jsx`, criar um componente `<SplashScreen />` 
que renderiza quando `isAuthenticated` acabou de mudar para `true` 
e o primeiro `fetchData()` ainda não retornou.

Visual: fundo preto com o texto "Flose AI" em gradiente cyan/purple 
animando com `scale` de 0.8 → 1.0, três anéis orbitais girando em 
velocidades diferentes (CSS keyframes `rotate`), e texto 
"INITIALIZING COGNITIVE SYSTEMS..." piscando com opacity.

Duração: desaparecer automaticamente quando `stats.agents > 0` 
ou após 3 segundos (timeout fallback), com fade-out de 0.5s.

Adicionar estado booleano `isBooting` no `App`, setado para `true` 
após login bem-sucedido, setado para `false` no callback do primeiro 
`fetchData` completo.
```

## Arquivos Envolvidos
- `frontend/src/App.jsx`
- `frontend/src/index.css` (keyframes dos anéis orbitais)

## Critério de Conclusão
- Splash aparece toda vez após login
- Desaparece automaticamente com fade-out suave
- Não bloqueia o app se o fetchData demorar mais de 3s
- Animação roda sem travar em 60fps
