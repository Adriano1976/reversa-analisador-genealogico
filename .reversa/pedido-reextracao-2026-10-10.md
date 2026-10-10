# Pedido de re-extração — 2026-10-10

> Autorização dada por Adriano em 2026-10-10, para a quarta rodada de extração.
> Este arquivo é a mensagem a apresentar ao `/reversa` quando ele perguntar
> "Continuamos de onde paramos?". **Não responda `CONTINUAR`.**

## Texto do pedido

Re-extração nova, não retomada. O ciclo de 2026-10-05 está fechado — as 5 fases estão em `completed`, o `pending` está vazio e não há tarefa `[ ]` nas fases do plano. O `phase: revisao` é campo residual.

Autorizo a re-extração integral de 2026-10-10.

Motivo, medido: o `_reversa_sdd/` é de 2026-10-05 e depois dele entraram 9 features no `_reversa_forward/`, mais os adendos correspondentes em `_reversa_sdd/addenda/`. Nesse intervalo nasceram `src/ports/`, a persistência Postgres, o armazenamento por conteúdo com `aposentar` e a substituição no reenvio, e a lista de arquivos da tela de entrada. Nada disso tem spec: os adendos registram o trabalho, mas o `_reversa_sdd/` não o reflete.

Decisões já tomadas, para não reperguntar:

- doc_level: **completo** — igual ao `config.toml [analysis]`. Desta vez não há conflito, ao contrário de 2026-09-30, quando o state dizia `essencial` e o config dizia `completo`.
- Organização das specs: seção `[specs]` já decidida (feature-folder / endpoint, 2026-08-03) — passo 3 pulado automaticamente.
- Preservar sem regenerar: `migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`, `design-system/` e `traceability/bugs.md`.
- Tirar snapshot antes de sobrescrever, como nas rodadas anteriores.

A entrada do passo 4 está limpa: os 13 itens de watch de 003 e 004 estão datados de 2026-10-10, e o `004/W003` foi corrigido.

Pode começar pelo Scout.

Se o menu de nível de documentação aparecer, a resposta é `2` (Completo).

## Estado medido na véspera

| item | valor |
| --- | --- |
| `phase` no `state.json` | `revisao` — residual, o ciclo de 2026-10-05 está inteiro em `completed` |
| `pending` | vazio |
| tarefas `[ ]` nas fases do `plan.md` | nenhuma (só os 4 Agentes Independentes, fora do plano) |
| `doc_level` | `completo`, igual ao `config.toml [analysis]` |
| seção `[specs]` | decidida — feature-folder / endpoint, 2026-08-03 |
| `.reversa/version` | 1.3.4 |
| suíte | 527 passam, 9 pulados, 0 falhas |
| árvore de trabalho | limpa |

## Features posteriores à extração de 2026-10-05

Data do primeiro commit de cada pasta em `_reversa_forward/`.

| feature | primeiro commit |
| --- | --- |
| 005-nucleo-puro-src | 2026-10-07 |
| 007-dono-no-port-e-baseline | 2026-10-07 |
| 003-renomear-pasta-app-para-src | 2026-10-08 |
| 006-fronteira-aplicacao-ports | 2026-10-08 |
| 008-persistencia-postgres-docker | 2026-10-08 |
| 009-rota-do-apple-touch-icon | 2026-10-08 |
| 010-uploads-fora-do-repositorio | 2026-10-09 |
| 012-pasta-canonica-no-repositorio | 2026-10-09 |
| 011-escolher-arquivo-da-lista | 2026-10-10 |

Anteriores à extração, portanto já cobertas: 001 e 002 (2026-08-11) e 004 (2026-10-04).

## Depois da extração

1. `/reversa-docs` e depois `python publicar_docs.py` — o mini-site é de 2026-10-05 e o gerador **não lê** `_reversa_sdd/addenda/`.
2. `/reversa-debugger-graph` — ler `.agents/skills/reversa-debugger-graph/SKILL.md` direto do disco; ele tem `disable-model-invocation: true` no front matter, e é **só por isso** que não aparece no catálogo de skills. Não precisa de PyYAML: o skill manda ler o front matter dos `bug.md`, o que é leitura de texto, não parseamento por programa. Deve ser o **último**, porque o `spec-matrix.md` que ele gera ancora em `_reversa_sdd/upload-gedcom/contracts.md#2.1` e `_reversa_sdd/domain.md#3.5`, que a re-extração reescreve.
