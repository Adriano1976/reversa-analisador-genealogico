# Compatibilidade com harnesses

A skill segue o formato aberto de Agent Skills: uma pasta com `SKILL.md` (frontmatter `name` + `description`),
mais `scripts/`, `references/`, `assets/`. O harness lê só nome+descrição até decidir usar a skill; então carrega o
corpo e os arquivos auxiliares sob demanda. Por isso o conteúdo é todo relativo a `<skill-dir>`.

| Harness | Onde colocar a pasta `token-reduce-universal/` | Observações |
|---|---|---|
| Claude Code | `~/.claude/skills/` (global) ou `.claude/skills/` (projeto) | pode usar o `.skill`/`.zip` gerado |
| Claude.ai / app | Configurações → Capacidades/Skills → enviar o `.skill` ou `.zip` | confira o menu da sua versão |
| OpenAI Codex (CLI/desktop/IDE) | `.agents/skills/` ou `.codex/skills/` no projeto; no usuário `~/.agents/skills/` ou `~/.codex/skills/` | invocação explícita com `$token-reduce-universal`; `/skills` lista |
| ChatGPT | skills nativas estão em liberação por plano (beta); sem elas, use Projects ou Custom GPT | veja "Modo sem skills" |
| Google Antigravity | projeto: `.agents/skills/` (novo padrão) ou `.agent/skills/` (legado); global: `~/.gemini/antigravity/skills/` | reinicie a sessão para redetectar; skill do projeto vence a global de mesmo nome |
| Gemini CLI, Cursor, outros | pasta de skills própria do produto, se houver; senão "Modo sem skills" | |

Caminhos conferidos em documentação/guias públicos em out/2026; produtos mudam rápido, confirme na
documentação da sua versão. O que não depende de caminho: `python <skill-dir>/scripts/compress.py ...` funciona
em qualquer terminal.

## Modo sem skills (qualquer chat/agente)
1. Cole `assets/universal-instructions.md` nas instruções do Custom GPT / Project / `AGENTS.md` / `GEMINI.md` /
   regras do Cursor. Ele descreve o fluxo e as regras de fidelidade em ~40 linhas.
2. Se o ambiente executa código (code interpreter, terminal), suba também a pasta `scripts/` e peça para rodar
   `compress.py`. Sem execução de código, use o engine "agent" manualmente: cole o prompt de
   `references/prompt-templates.md` e confira números/negações no resultado.

## Dicas por ambiente
- Sandbox sem rede ou com pasta de skill somente-leitura: nada a configurar; o engine `lite` não escreve na pasta da skill.
- Windows: `python`; PowerShell exibe UTF-8 corretamente (o script força UTF-8).
- Ao empacotar para equipe, não inclua `.venv`/caches (a skill nunca cria venv dentro da própria pasta).
