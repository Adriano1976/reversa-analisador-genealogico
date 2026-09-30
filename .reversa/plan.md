# Plano de Exploração — teste_reversa

> Criado pelo Reversa em 2026-07-23
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

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
