# Plano de Exploração — teste_reversa

> Criado pelo Reversa em 2026-07-23
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

---

## Re-extração de 2026-10-05 🔁

> Disparada porque o `_reversa_sdd/` estava congelado em 2026-09-30 e o código andou muito desde então: a raiz `analisador-genealogico/` virou `src/`, o pacote `reconstructed/` foi substituído por `core/` + `parsers/` + `reporting/` + `utils/`, o `app.py` passou de 84 para 227 linhas, e a capacidade de **confronto GEDCOM × DNA** (quatro estados) nasceu sem nenhuma spec. Nenhuma feature 005+ existe em `_reversa_forward/`, então não há adendo que registre esse trabalho.
> Nível de documentação: **a definir no checkpoint pós-Scout** (o `state.json` dizia `essencial`; o `config.toml` diz `completo`).
> Snapshot da extração anterior: `.reversa/snapshots/2026-10-05-pre-reextracao/` (33 arquivos, 349 KB, sha256 por arquivo no `_MANIFEST.txt`).
> Preservados sem regeneração: `_reversa_sdd/migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`.
> Pós-extração: regenerar `_reversa_docs/` e revisar as matrizes de rastreabilidade dos bugs.

### Fase 1: Reconhecimento 🔍

- [x] **Scout** — Estrutura, tecnologias, entry points, dependências e cobertura de testes ✅
- [x] **Scout** — Sugestão de organização das specs (confirmou `endpoint` já persistido; passo 3 pulado) ✅

### Fase 2: Escavação 🏗️

- [x] **Arqueólogo** — Análise do módulo `upload-gedcom` (parsers/gedcom_parser.py, core/gedcom_state.py, utils/text_cleaning.py, utils/validate.py) ✅ 20 regras, `flowcharts/upload-gedcom.md`
- [x] **Arqueólogo** — Análise do módulo `analise-dna` (core/dna_analysis.py, genetic_evidence, relationship_hypotheses, evidence_comparison, matching, name_normalization, cm_estimator, parsers/csv_ingest.py) ✅ 62 regras, `flowcharts/analise-dna.md`
- [x] **Arqueólogo** — Análise do módulo `busca-caminho` (core/path_search.py, path_finding, family_navigation, documentary_relationship, reporting/mermaid_render.py) ✅ 36 regras, `flowcharts/busca-caminho.md`
- [x] **Arqueólogo** — Artefatos transversais do nível completo: `data-dictionary.md`, `flowcharts/{upload-gedcom,analise-dna,busca-caminho}.md`, `code-analysis.md` (§1 a §6) e `.reversa/context/modules.json` ✅ 118 regras, 77 funções, 27 estruturas

### Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos ✅ 23 ADRs em `adrs/` (125 commits; 8 herdadas revalidadas + 15 novas)
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado ✅ 7 famílias de regras; `state-machines.md` com 2 máquinas de decisão e 11 códigos de aviso
- [x] **Detetive** — Matriz de permissões (RBAC/ACL) ✅ `permissions.md`: nenhum papel, nenhuma sessão; `app.secret_key` sem consumidor
- [x] **Arquiteto** — Diagramas C4 (Contexto) ✅ `c4-context.md` reescrito + `c4-containers.md` (3 containers) e `c4-components.md` (19 módulos) criados
- [x] **Arquiteto** — ERD e integrações externas ✅ `erd-complete.md` com 27 estruturas em 4 diagramas; **zero** integrações de rede
- [x] **Arquiteto** — Spec Impact Matrix (conforme o nível escolhido) ✅ `traceability/spec-impact-matrix.md` com 5 matrizes, 20 constantes mapeadas e 4 lacunas

### Fase 4: Geração 📝

- [x] **Redator** — Specs SDD da unit `upload-gedcom` ✅ 19 RF, 20 tarefas, 13 testes e `contracts.md`
- [x] **Redator** — Specs SDD da unit `analise-dna` ✅ 26 RF, 32 tarefas, 18 testes e `contracts.md` (com a divergência viva `RF-26` do determinismo)
- [x] **Redator** — Specs SDD da unit `busca-caminho` ✅ 24 RF, 29 tarefas, 18 testes e `contracts.md` (com o contrato de escape como item crítico)
- [x] **Redator** — Artefatos globais do nível completo ✅ `openapi/index.yaml` (contrato de formulário), 3 `user-stories/` e `traceability/code-spec-matrix.md`

### Fase 5: Revisão ✅

- [x] **Revisor** — Revisão de consistência ✅ 10 verificações; `L-06` fechada por verificação no template
- [x] **Revisor** — Resolução de lacunas com o usuário ✅ **16 de 16 respondidas**; 4 decisões mudaram código, 1 mudou o pin e 4 viraram requisitos do alvo
- [x] **Revisor** — Relatório de confiança final ✅ 92,4% na extração completa (1.918 afirmações); `gaps.md` com 25 lacunas remanescentes

### Passo 4 — Verificação de regressão semântica 🔁

- [x] **Reversa** — Verificação contra `_reversa_forward/*/regression-watch.md` ✅ 4 features, **13 watch items: 12 🟢 e 1 🟡, zero vermelhos**; paridade remedida em 100% (6/6 fixtures)
- [x] **Reversa** — Reconciliação de adendos ✅ **6 adendos** marcados como superados pela re-extração de 2026-10-05 (9 no total; 3 já estavam de rodada anterior)

---

## ✅ Re-extração concluída em 2026-10-05

> 6 agentes, nível **completo**, **1.922 afirmações e 92,8% de confiança geral**.
> Snapshot da extração anterior: `.reversa/snapshots/2026-10-05-pre-reextracao/` (33 arquivos, 349 KB)
> Preservados: `migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`, `design-system/`, `traceability/bugs.md`
> **16 perguntas de validação humana, todas respondidas** — 4 decisões mudaram código e 1 mudou o pin
> Verificação por execução: suíte **179 itens / 164 passam**; paridade **100% (6/6 fixtures)**; cobertura **83% de `src/`**
> Lacunas: **14 linhas em aberto**, **1 crítica** (corrida entre threads)
> Próximos passos: `/reversa-docs` (regenerar o mini-site), regenerar as matrizes de bugs, e levar os **4 requisitos encaminhados ao alvo** para o próximo ciclo forward

---

## Re-extração de 2026-09-30 🔁

> Disparada porque o `_reversa_sdd/` estava congelado em 2026-08-03 e contradizia o código atual (app.py 887 → 84 linhas, `reconstructed/` criado, 95 testes adicionados, pyvis/matplotlib removidos).
> Nível de documentação: **essencial** (decisão do usuário; `config.toml` dizia `completo`).
> Snapshot da extração anterior: `.reversa/snapshots/2026-09-30-pre-reextracao/` (28 arquivos, 115 KB).
> Preservados sem regeneração: `_reversa_sdd/migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`.

### Fase 1: Reconhecimento 🔍

- [x] **Scout** — Estrutura, tecnologias, entry points, dependências e cobertura de testes ✅
- [x] **Scout** — Sugestão de organização das specs (confirmou `endpoint` já persistido) ✅

### Fase 2: Escavação 🏗️

- [x] **Arqueólogo** — Análise do módulo `upload-gedcom` (11 regras) ✅
- [x] **Arqueólogo** — Análise do módulo `busca-caminho` (17 regras) ✅
- [x] **Arqueólogo** — Análise do módulo `analise-dna` (25 regras) ✅

### Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos ✅ (8 ADRs reconstruídos de 66 commits)
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado ✅ (12 regras; nenhuma máquina de estado existe)
- [x] **Detetive** — Matriz de permissões (RBAC/ACL) ✅ (inexistente — sem auth; consequência de negócio registrada)
- [x] **Arquiteto** — Diagramas C4 (Contexto) ✅
- [x] **Arquiteto** — ERD e integrações externas ✅ (9 entidades, 0 integrações de API)
- [x] **Arquiteto** — Spec Impact Matrix ✅ (não aplicável no nível essencial)

### Fase 4: Geração 📝

- [x] **Redator** — Specs SDD da unit `upload-gedcom` ✅ (12 RF, 14 tarefas)
- [x] **Redator** — Specs SDD da unit `analise-dna` ✅ (13 RF, 18 tarefas)
- [x] **Redator** — Specs SDD da unit `busca-caminho` ✅ (15 RF, 20 tarefas)
- [x] **Redator** — OpenAPI / User Stories / Code-Spec Matrix ✅ (não aplicáveis no nível essencial)

### Fase 5: Revisão ✅

- [x] **Revisor** — Revisão cruzada de specs ✅ (não oferecida no nível essencial; 7 verificações de consistência executadas)
- [x] **Revisor** — Resolução de lacunas com o usuário ✅ (6 perguntas geradas, 3 bloqueantes — aguardando resposta)
- [x] **Revisor** — Relatório de confiança final ✅ (88,8% na extração completa)

---

## ✅ Re-extração concluída em 2026-09-30

> 6 agentes, nível **essencial**, 826 afirmações, 88,8% de confiança geral.
> Snapshot da extração anterior: `.reversa/snapshots/2026-09-30-pre-reextracao/`
> Preservados: `migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`, `design-system/`, `traceability/bugs.md`
> Pendente: 6 perguntas em `_reversa_sdd/questions.md` (3 bloqueantes)
> Próximos passos possíveis: `/reversa-forward` (evoluir), `/reversa-migrate` (reavaliar migração), `/reversa-docs` (regenerar mini-site)

### Passo 4 — Verificação de regressão semântica 🔁

- [x] **Reversa** — Verificação contra `_reversa_forward/*/regression-watch.md` ✅ (2026-09-30, 0 watch items, 4 amarelos, 1 vermelho)
- [x] **Reversa** — Reconciliação de adendos ✅ (001, 002 e 003 marcados; `bug-J6PQ` preservado por decisão do usuário)

---

## Extração original de 2026-08-03 (histórico)

> Mantida como registro. Os artefatos desta rodada foram substituídos pela re-extração acima.

## Fase 1: Reconhecimento 🔍

- [x] **Scout** — Mapeamento de estrutura de pastas e tecnologias ✅
- [x] **Scout** — Análise de dependências e gerenciadores de pacotes ✅
- [x] **Scout** — Identificação de entry points, CI/CD e configurações ✅

## Decisão de organização das specs 🗂️

> Entre o Scout e o Arqueólogo, o Reversa pergunta como você quer organizar as specs (por módulo, caso de uso, endpoint, híbrida, por features ou customizada). A escolha fica persistida em `.reversa/config.toml` na seção `[specs]` e não será reperguntada em execuções futuras. Para reapresentar o menu, remova manualmente a seção.

## Fase 2: Escavação 🏗️

- [x] **Arqueólogo** — Análise do módulo `analisador-genealogico` ✅

## Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos ✅
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado ✅
- [x] **Detetive** — Matriz de permissões (RBAC/ACL) ✅
- [x] **Arquiteto** — Diagramas C4 (Contexto, Containers, Componentes) ✅
- [x] **Arquiteto** — ERD completo e integrações externas ✅
- [x] **Arquiteto** — Spec Impact Matrix ✅

## Fase 4: Geração 📝

- [x] **Redator** — Specs SDD por componente ✅
- [x] **Redator** — OpenAPI (se aplicável) ✅ (não aplicável no nível essencial)
- [x] **Redator** — User Stories (se aplicável) ✅ (não aplicável no nível essencial)
- [x] **Redator** — Code/Spec Matrix ✅ (não aplicável no nível essencial)

## Fase 5: Revisão ✅

- [x] **Revisor** — Revisão cruzada de specs ✅
- [x] **Revisor** — Resolução de lacunas com o usuário ✅ (pulado pelo usuário — lacunas registradas em questions.md)
- [x] **Revisor** — Relatório de confiança final ✅

---

## Agentes Independentes

> Execute estes agentes quando os recursos estiverem disponíveis — podem rodar em qualquer fase.

- [ ] **Visor** — Análise de interface via screenshots
- [ ] **Data Master** — Análise completa do banco de dados
- [ ] **Design System** — Extração de tokens de design
- [ ] **Tracer** — Análise dinâmica (requer sistema acessível)

---

## Próximo passo

Após o Time de Descoberta concluir e o `_reversa_sdd/` estar populado, você pode disparar um dos fluxos seguintes:

- `/reversa-migrate`: orquestrador do **Time de Migração** (Paradigm Advisor → Curator → Strategist → Designer → Screen Translator → Inspector). Gera as specs do sistema novo. Saída em `_reversa_sdd/migration/` e `_reversa_sdd/screens/`.
- `/reversa-reconstructor`: gera plano bottom-up para reimplementar o software a partir das specs do legado (uma tarefa por sessão).
