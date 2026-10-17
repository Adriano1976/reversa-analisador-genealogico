# Plano de Exploração — teste_reversa

> Criado pelo Reversa em 2026-07-23
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

---

## Re-extração de 2026-10-10 🔁

> **Re-extração nova, não retomada.** Disparada porque o `_reversa_sdd/` está congelado em 2026-10-05 e depois dele entraram 9 features em `_reversa_forward/` (005 a 012) mais os adendos correspondentes: nasceram `src/ports/`, a persistência Postgres/Docker, o armazenamento por conteúdo com `aposentar` e a substituição no reenvio, a lista de arquivos da tela de entrada, a tradução de erros e o registro de análises. Os adendos registram o trabalho, mas o `_reversa_sdd/` não o reflete.
> Autorização: Adriano, 2026-10-10 (`.reversa/pedido-reextracao-2026-10-10.md`).
> Nível de documentação: **completo** (já decidido; igual a `config.toml [analysis]`, sem conflito nesta rodada).
> Organização das specs: seção `[specs]` já decidida (feature-folder / endpoint, 2026-08-03) — passo 3 pulado automaticamente.
> Snapshot da extração anterior: `.reversa/snapshots/2026-10-10-pre-reextracao/` (83 arquivos, 967 KB, sha256 por arquivo no `_MANIFEST.txt`).
> Preservados sem regeneração: `migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`, `design-system/` e `traceability/bugs.md`.

### Fase 1: Reconhecimento 🔍

- [x] **Scout** — Estrutura, tecnologias, entry points, dependências e cobertura de testes ✅ 8 rotas/ações, 5.130 linhas em `src/`, 536 itens de teste (527 passam)
- [x] **Scout** — Sugestão de organização das specs ✅ confirmou `endpoint` já persistido; passo 3 pulado (sem override em `config.user.toml`)

### Fase 2: Escavação 🏗️

- [x] **Arqueólogo** — Análise do módulo `upload-gedcom` (envio, validação de conteúdo, chave por conteúdo, reenvio com substituição) ✅ 22 regras, `flowcharts/upload-gedcom.md`
- [x] **Arqueólogo** — Análise do módulo `tela-de-entrada` (as duas abas, escolher da lista, aposentar) ✅ 19 regras, `flowcharts/tela-de-entrada.md`
- [x] **Arqueólogo** — Análise do módulo `analise-dna` (três eixos + confronto + registro histórico) ✅ 95 regras, `flowcharts/analise-dna.md`; **fechou a divergência viva do determinismo** de 2026-10-05
- [x] **Arqueólogo** — Análise do módulo `busca-caminho` (parentesco documental e diagrama Mermaid) ✅ 67 regras, `flowcharts/busca-caminho.md`; achado novo da colisão de chave do cache de nomes
- [x] **Arqueólogo** — Análise do módulo `recursos-da-tela` (`GET /banner.png` e `GET /apple-touch-icon.png`) ✅ 30 regras, `flowcharts/recursos-da-tela.md` (unit nova, zero linhas próprias — as duas rotas vivem em `app.py`)
- [x] **Arqueólogo** — Artefatos transversais do nível completo: `code-analysis.md`, `data-dictionary.md`, `flowcharts/` (5) e `.reversa/context/modules.json` ✅ 233 regras em 5 unidades, 81 funções, 38 entidades, 37 algoritmos, 28 dívidas consolidadas

### Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos ✅ 13 ADRs novos (24 a 36), sobre 126 commits desde 2026-10-05; inclui a revalidação das 23 herdadas e a única decisão revertida do projeto (010 → 012)
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado ✅ `state-machines.md`: **1 ciclo de vida de verdade** (a posição do arquivo), 4 máquinas de decisão e 11 códigos de aviso
- [x] **Detetive** — Matriz de permissões (RBAC/ACL) ✅ `permissions.md`: nenhum papel; o `dono` existe e não isola; a **corrida entre threads deixou de existir** estruturalmente
- [x] **Arquiteto** — Diagramas C4 (Contexto, Containers, Componentes) ✅ 4 containers (entrou o Postgres opcional), 31 componentes em 7 unidades, e os **dois ciclos de pacote fechados**
- [x] **Arquiteto** — ERD e integrações externas ✅ 42 estruturas em 5 diagramas, incluindo o **Diagrama E — o primeiro esquema físico do projeto** (6 tabelas, FK real); zero integrações de rede com terceiros
- [x] **Arquiteto** — Spec Impact Matrix ✅ 5 unidades, matrizes A a E, 3 achados novos e 7 lacunas (`X-01`..`X-07`)

### Fase 4: Geração 📝

- [x] **Redator** — Specs SDD da unit `upload-gedcom` ✅ 24 RF, 26 tarefas, 20 testes e `contracts.md` (a unit deixou de publicar estado; ganhou reenvio e a forma de nome)
- [x] **Redator** — Specs SDD da unit `tela-de-entrada` (unit nova: as duas abas, escolher da lista, aposentar) ✅ 24 RF, 22 tarefas, 14 testes e `contracts.md`; achado novo `L-30` (o motivo "fora da forma" ficou inalcançável depois da `RN-20`)
- [x] **Redator** — Specs SDD da unit `analise-dna` (três eixos + projeção + registro histórico) ✅ 34 RF, 46 tarefas, 27 testes e `contracts.md`; a unit ganhou fronteira, projeção pura e persistência opcional, e **o catálogo foi corrigido em duas contagens** (causas de `POSSIVEL` = 8, não 9; `COMMON_SURNAMES` = 16 literais / 15 efetivas)
- [x] **Redator** — Specs SDD da unit `busca-caminho` (parentesco documental e diagrama) ✅ 43 RF, 38 tarefas, 24 testes e `contracts.md`; **duas regras reescritas** (o grafo vem da árvore por parâmetro; o índice é invalidado por chave de conteúdo) e o achado `L-24` da colisão do cache ganhou teste que hoje falharia
- [x] **Redator** — Specs SDD da unit `recursos-da-tela` (unit nova: as duas rotas de arte) ✅ 25 RF, 22 tarefas, 17 testes e `contracts.md`; achado novo `L-33` (não há verificação de que a arte servida é a correta **dentro do container**)
- [x] **Redator** — Artefatos globais do nível completo (`openapi/index.yaml`, 5 `user-stories/` e `traceability/code-spec-matrix.md`) ✅ `openapi` regenerado (5 ações + as 2 rotas de arte + schema por forma de nome); 2 user-stories **novas** e 3 regeneradas; matriz de **5 units** e **35 arquivos** com `CS-05` superada

### Fase 5: Revisão 🔄

- [x] **Revisor** — Revisão de consistência ✅ 20 canônicos + 3 globais lidos; **13 medições** contra o código; **10 defeitos corrigidos** em 11 arquivos — incluindo o `openapi/index.yaml`, que **não era YAML válido**; `L-24` alcança `analise-dna`
- [x] **Revisor** — Resolução de lacunas com o usuário ✅ **18 de 18 respondidas** com a recomendação do Revisor — **uma passada única**; 4 delas eram **experimentos** e foram executados: `L-24` **confirmado por execução**, `L-31` **negativo**, `L-20` **medido**, cobertura **remedida** (89 %)
- [x] **Revisor** — Relatório de confiança final ✅ **90,4 %** em **3.420** marcadores; **zero lacunas críticas** — a corrida entre threads (`L-16`) foi **eliminada por construção** (`ADR-24`); `gaps.md` com **22 itens em aberto**, nenhum crítico

### Passo 4 — Verificação de regressão semântica 🔁

- [x] **Reversa** — Verificação contra `_reversa_forward/*/regression-watch.md` ✅ **12 features, 67 watch items: 59 🟢 · 7 🟡 · 1 🔴**; paridade remedida em **100 % (6/6, exit 0)** e suíte em **527 passam / 9 pulados / 0 falham**
- [x] **Reversa** — Reconciliação de adendos ✅ **8 adendos** marcados como superados pela re-extração de 2026-10-10 (17 no total; 9 já estavam de rodadas anteriores)
- [x] **Reversa** — **Re-verificação suplementar em 2026-10-13** (o código mudou depois da re-extração; nenhuma spec foi regerada) ✅ **12 features, 67 watch items: 61 🟢 · 5 🟡 · 1 🔴** — o vermelho é o mesmo `010-W008`, com triagem humana pendente; paridade **100 % (6/6, exit 0)** e suíte **605 passam / 9 pulados / 0 falham**; `_t020_varredura.py` e `_t011_varredura.py` **APROVADOS**; a sonda de mensagens acusa 5 divergências, todas por mudança declarada; bloco datado gravado no histórico das 9 features que têm itens
- [x] **Reversa** — **Reconciliação de adendos, complemento de 2026-10-13** ✅ o adendo `011-escolher-arquivo-da-lista` **era o oitavo** de 2026-10-10 e não carregava a linha de superação: marcado agora, o que fecha a contagem registrada acima. Os adendos `013` (2026-10-12) e `014` (2026-10-11) são **posteriores** à re-extração e seguem vigentes
- [x] **Reversa** — **Absorção editorial do adendo `025` em 2026-10-17** ✅ o adendo registra o delta da feature 025 (`build_graph_from_parser` recebe as famílias já materializadas, não o `GedcomReader`); absorvido em `architecture.md#3` e `c4-components.md` (nível 3), com a ficha do `gedcom_parser.py` corrigida. **Nenhum código foi tocado**

---

## ✅ Re-extração concluída em 2026-10-10

> 6 agentes, nível **completo**, **3.420 afirmações e 90,4 % de confiança geral**.
> Snapshot da extração anterior: `.reversa/snapshots/2026-10-10-pre-reextracao/` (83 arquivos, 967 KB, sha256 por arquivo)
> Preservados: `migration/`, `oracle/`, `parity/`, `screens/`, `addenda/`, `design-system/`, `traceability/bugs.md`
> **18 perguntas de validação humana, todas respondidas** — 4 eram **experimentos** e foram executados
> Verificação por execução: suíte **527 passam / 9 pulados / 0 falham**; paridade **100 % (6/6 fixtures)**; cobertura de `src/` **89 %**
> Lacunas: **0 críticas**, 12 moderadas, 10 cosméticas — a única crítica das rodadas anteriores (`L-16`) foi **eliminada por construção** (`ADR-24`)
> **10 defeitos de consistência corrigidos**, incluindo o `openapi/index.yaml`, que **não era YAML válido**
> Próximos passos: `/reversa-docs` + `python publicar_docs.py`; regenerar as matrizes de `_reversa_bugs/*/generated/`; `/reversa-debugger-graph` **por último**; e as **5 correções de código agendadas** (ver `state.json`)

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
