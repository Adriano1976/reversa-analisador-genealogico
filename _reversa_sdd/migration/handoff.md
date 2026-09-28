---
schemaVersion: 1
generatedAt: "2026-09-28T04:25:30Z"
reversa:
  version: "1.2.58"
kind: handoff
producedBy: orchestrator
hash: "sha256:9e6d4e2ab2d46fda591df55786086d4d72ba1896911b0e18d28603dfc8fe7b6c"
---

# Handoff para o Agente de Codificação

> Sistema novo a ser construído em paradigma **OO com DI sobre funções puras**, topologia **híbrida (núcleo puro e plano + fronteira hexagonal)**, telas em modo **híbrido (8 literais + 5 modernizadas)**.
> **Antes de qualquer linha de código, leia `paradigm_decision.md`, `topology_decision.md` e `screen_modernization_decision.md`.**

## ⚠️ Leitura obrigatória primeiro

1. **`paradigm_decision.md`** — leitura inegociável. **Não é "só uma mudança sintática"**: o legado é `procedural` (funções top-level + estado global mutável) e o alvo é `OO com DI` (**gap alto**). Este documento define a **regra de fronteira** que governa todo o resto: *algoritmo de negócio → núcleo, função pura, fidelidade absoluta; plumbing → borda, modernização livre*.
2. **`topology_decision.md`** — leitura inegociável. A topologia é **híbrida**: `core/` **puro e plano** (sem subpastas de bounded context), fronteira hexagonal completa. Define a árvore de pastas e **proíbe** que `core/` importe framework.
3. **`screen_modernization_decision.md`** — leitura inegociável (o legado **tem** UI). O modo é **híbrido**: as 5 telas legadas em **literal** (invariante de diff textual zero, com uma única exceção autorizada) e as 5 telas novas em **modernizado**.

## Ordem de leitura recomendada

1. `paradigm_decision.md` (obrigatório, primeiro)
2. `topology_decision.md` (obrigatório, segundo)
3. `screen_modernization_decision.md` (obrigatório — o legado tem UI)
4. `migration_brief.md`
5. `target_business_rules.md`
6. `migration_strategy.md`
7. `target_architecture.md`
8. `target_domain_model.md`
9. `target_data_model.md`
10. `data_migration_plan.md`
11. `target_screens.md`
12. `parity_specs.md` + `parity_tests/`
13. `screen_deviation_log.md` (consultivo)
14. `risk_register.md` + `cutover_plan.md`
15. `discard_log.md` (consultivo)
16. `ambiguity_log.md` (consultivo)

## Lista de artefatos produzidos

| Artefato | Produzido por | Status |
|---|---|---|
| `migration_brief.md` | orchestrator | criado |
| `paradigm_decision.md` | paradigm_advisor | criado |
| `target_business_rules.md` | curator | criado (49 regras: 34 MIGRAR / 7 DESCARTAR / 8 DECISÃO HUMANA resolvidas) |
| `discard_log.md` | curator | criado (7 itens; 5 vinculados a paradigma) |
| `migration_strategy.md` | strategist | criado (estratégia **C — Parallel Run em ondas**, confirmada) |
| `risk_register.md` | strategist | criado (12 riscos: 3 críticos, 5 altos, 4 médios) |
| `cutover_plan.md` | strategist | criado (7 ondas; janela 2–4h; sem ETL) |
| `topology_decision.md` | designer (Fase 1) | criado e **aprovado** (opção 3 — híbrido) |
| `target_architecture.md` | designer (Fase 2) | criado (5 bounded contexts, 6 ADRs, 2 seções de honra) |
| `target_domain_model.md` | designer (Fase 2) | criado (3 aggregates; **34 regras MIGRAR mapeadas**; 0 eventos de domínio) |
| `target_data_model.md` | designer (Fase 2) | criado (14 tabelas PostgreSQL; `owner_id` em `NOT NULL`) |
| `data_migration_plan.md` | designer (Fase 2) | criado (**documenta ausência de ETL**: volume 0) |
| `screen_modernization_decision.md` | screen_translator (Fase 1) | criado e **aprovado** (modo híbrido) |
| `target_screens.md` | screen_translator (Fase 2) | criado (**13 entradas**: 8 literais + 5 modernizadas) |
| `screen_deviation_log.md` | screen_translator (Fase 2) | criado (**10 deviations, todas aprovadas**) |
| `_reversa_sdd/screens/inventory.json` | screen_translator | criado (5 telas, 4 rotas, inventário textual) |
| `_reversa_sdd/screens/golden/manifest.yaml` | screen_translator | criado (**0 goldens capturados** — captura manual) |
| `_reversa_sdd/design-system/tokens-derived.md` | screen_translator | criado (derivado; `design-system/` catalogado não existe) |
| `parity_specs.md` | inspector | criado (modos, critérios, cobertura adaptada, 10 exceções) |
| `parity_tests/*.feature` | inspector | criado (**12 arquivos, 99 cenários** Gherkin) |
| `ambiguity_log.md` | orchestrator | consolidado (**22 itens: 0 pendentes**, 12 resolvidos, 10 referidos à codificação) |
| `.state.json` | orchestrator | mantido (6/6 agentes concluídos) |
| `.logs/<timestamp>-migrate.log` | orchestrator | criado (log completo do pipeline) |

## Bloqueadores para começar a implementação

- **Nenhum bloqueador. Prosseguir.**

Justificativa verificada item a item:
- **6 de 6 agentes** concluídos, sem `failed`.
- **`ambiguity_log.md` com 0 itens PENDENTES** (requisito do Passo 7 satisfeito).
- **`screen_deviation_log.md` com 0 deviations pendentes** (10 de 10 aprovadas) — o handoff ao Inspector não está bloqueado.
- **Todas as decisões humanas dos 4 gates estão tomadas e registradas**: paradigma, regras (Curator), estratégia, topologia, modo de telas, DEV-010.
- **Nenhuma operação destrutiva foi necessária**; nenhum backup precisou ser restaurado; nenhuma modificação manual de artefato gerado foi detectada (todos os hashes de `.state.json` conferem com os arquivos).

> ⚠️ **Distinção importante**: os 10 itens **REFERIDOS À CODIFICAÇÃO** (seção abaixo) **não são bloqueadores**. São decisões de implementação que o pipeline não pode tomar — nenhuma delas impede o início da Onda 0 ou da Onda 1. Duas delas, porém, **bloqueiam o go-live** (não a codificação): AMB-018 e AMB-022.

## Próximos passos para o agente de codificação

1. **Ler `paradigm_decision.md` e internalizar**: o paradigma alvo é **`OO com DI` sobre funções puras**, com `derived_appetite = balanced` (opção 3 — híbrido). A regra que governa cada decisão de código: **se é algoritmo de negócio** (score, regras A/B/C/D, caminho, cM, mojibake) → **núcleo puro, fidelidade absoluta**; **se é plumbing** (HTTP, persistência, auth, tenancy, config) → **borda, modernização livre**.
2. **Ler `topology_decision.md` e internalizar**: a topologia é **híbrida** — `core/` é **puro e plano** (`mojibake.py`, `normalization.py`, `tree.py`, `parser.py`, `matching.py`, `relationship.py`, `pathfinding.py`, `decomposition.py`, `dna.py`, `constants.py`), e a fronteira é hexagonal. **`core/` não pode importar `fastapi`, `sqlalchemy`, `pydantic` nem `flask`.** Use o esboço da árvore do `target_architecture.md § Honra à topologia escolhida` como base do repositório novo.
3. **Ler `screen_modernization_decision.md` e internalizar**: modo **híbrido**. As 8 entradas literais (SCR-001 a SCR-005 + SCR-G01 a G03) exigem **paridade textual estrita**; as 5 modernizadas (SCR-006 a SCR-010) exigem os **4 estados** e a hierarquia de componentes. ⚠️ Em modo literal, o texto é **congelado** — a **única** exceção autorizada é `aria-label="Close"` → `"Fechar"` (DEV-005).
4. **Configurar o repositório novo** com a stack do `migration_brief.md` (**Python 3.12+ · FastAPI · PostgreSQL · React + TypeScript**) e **fixar todas as dependências** (`pins` — resolve a dívida #1 do legado e mitiga RISK-009). **Nunca** copiar o `secret_key` hardcoded do legado (BR-DESCARTAR-007).
5. **Implementar bottom-up, respeitando a ordem das ondas do `cutover_plan.md`**:
   - **Onda 0** — harness diferencial + goldens (ver passo 7 abaixo). **Não tem código de produto.**
   - **Onda 1** — `core/` puro + `tests/parity/`. **Nenhuma feature nova.** Porta o comportamento, inclusive os defeitos.
   - **Onda 2** — `application/`, `ports/`, `api/` (FastAPI, Pydantic, exceções de domínio → status HTTP).
   - **Onda 3** — auth, `owner_id` como invariante, `adapters/persistence/` (PostgreSQL), teste negativo de isolamento.
   - **Onda 4** — `presentation/` (React + TS) + visualização de grafo.
   - **Onda 5** — conformidade LGPD/GDPR (criptografia, consentimento, retenção, exclusão).
6. **Regra de sequenciamento rígida**: **nenhuma onda avança com paridade pendente.** Se a Onda 1 não fechar 100%, **não** iniciar a Onda 2. Mitigação direta de RISK-008.
7. **Escrever os testes desde a Onda 0**, a partir de `parity_specs.md` e `parity_tests/*.feature` (12 arquivos, 99 cenários). Honrar `parity_specs.md § Exceções`, que reflete as 10 deviations aprovadas.
   - ⚠️ **O ato mais importante de todo o projeto**: o harness deve executar **`analisador-genealogico/app.py`** (o legado), **nunca** `reconstructed/*.py`. Os 47 testes existentes em `tests/` testam a **reconstrução** — usá-los como oráculo criaria **validação circular** (RISK-002). Comparação **exata**, sem `pytest.approx`.
8. **Transcrever — não reconstruir — os dados que só existem em `app.py`** (RISK-003): a lista de primeiros nomes genéricos (BR-MIGRAR-011), a tabela de equivalentes de grafia, a lista de sobrenomes comuns e os sufixos salvadores (BR-MIGRAR-012), e a tabela de substituições de mojibake (BR-HUMANA-005). **Extraia mecanicamente e registre a linha de origem** (`# analisador-genealogico/app.py:759`). Uma lista plausível-mas-errada produz divergência **silenciosa**.
9. **Preservar as ordens que decidem resultado** (`target_data_model.md` § Considerações): `person.source_ordinal`, `gedcom_tree.graph_edge_order_version` e `match_result.result_ordinal`. Em SQL, ordem **não é garantida** — torná-la coluna é a única forma de assegurar paridade.
10. **Manter a aritmética intacta** (RISK-004): use os mesmos literais e a **mesma ordem de soma**. `total_cm` é calculado no núcleo e **persistido já calculado** — **não** use `SUM` do PostgreSQL como autoridade (AD-03).
11. **Não transportar o estado global** (BR-DESCARTAR-001), inclusive o mecanismo de mutação in-place (`clear` + `update`) que a reconstrução usou. `owner_id` é **invariante de aggregate**, não filtro de query (AD-02).
12. **Para o cutover**, seguir `cutover_plan.md` e os critérios go/no-go. O `data_migration_plan.md` confirma: **não há ETL, não há dados a migrar, não há janela de dados a congelar**.

## Itens referidos à codificação

> Os 10 itens abaixo são decisões de implementação — **não bloqueiam o início da codificação**. Detalhamento completo em `ambiguity_log.md`.

| ID | Item | Onde decidir | Bloqueia go-live? |
|---|---|---|---|
| **AMB-002** | Necessidades dos usuários externos (UX, onboarding, consentimento) **não foram validadas** por nenhum usuário real — o stakeholder declarado é único | Antes de abrir cadastro | **Sim** |
| **AMB-003** | Escopo integral + multiusuário + conformidade, sem prazo/orçamento e com decisor único | Disciplina de ondas | Não |
| **AMB-015** | GEDCOM com **referência pendente**: o legado aceitava, o alvo tende a rejeitar. Rejeitar quebra paridade. Recomendação: aceitar e **sinalizar** | Onda 1 (parse) | Não |
| **AMB-016** | O que `gedcom_filename` referencia no alvo — **tradução semântica mais delicada** do pipeline | Onda 3 (BC-02/BC-03) | Não |
| **AMB-017** | Algoritmo e parâmetros de **criptografia** em repouso/trânsito para dado genético | Onda 3, antes do go-live | **Sim** |
| **AMB-018** | **Base legal e prazo de retenção** para dado genético | **Pelo usuário**, antes da Onda 5 | **Sim (No-go absoluto)** |
| **AMB-019** | Ferramenta de migrations (recomendação: Alembic) | Onda 2/3 | Não |
| **AMB-020** | Política de **reprocessamento** quando o GEDCOM é reimportado | Onda 3/4 | Não |
| **AMB-021** | **Determinismo explícito** do núcleo: injeção de relógio e de aleatoriedade | Ondas 0/1 | Não |
| **AMB-022** | **Nenhum golden file de tela capturado** — paridade visual especificada mas **não provada** | Onda 0 (captura manual) | **Sim** |

> ⚠️ **Dois itens exigem atenção imediata do usuário, não do codificador**: **AMB-018** (a única pergunta que só o usuário pode responder — base legal e prazo de retenção) e **AMB-002** (validação com um usuário externo real antes de abrir cadastro). Ambos são **No-go de go-live** no `cutover_plan.md`.

## Itens auto-decididos (apenas se executado em --auto)

- **Nenhum item auto-decidido.** O pipeline foi executado em **modo interativo**, com **4 pausas humanas** (Paradigm Advisor, Curator, Strategist, Designer Fase 1) mais **3 checkpoints intra-agente** (Designer Fase 2, Screen Translator Fase 1 e Fase 2) — **7 gates no total**. Nenhum default de `references/auto-defaults.md` foi aplicado.

## Ressalvas e transparência do orquestrador

> Registrado por honestidade metodológica: o pipeline produziu artefatos confiáveis, mas **três fatos devem ser conhecidos** antes de confiar cegamente neles.

1. **O pré-requisito `gaps.md` estava ausente.** O pipeline foi bloqueado na verificação do Passo 1 e prosseguiu por **decisão explícita do usuário**, usando `confidence-report.md § Lacunas Pendentes (🔴)` + `questions.md` como substitutos. O Curator operou sobre fonte substituta (AMB-001). Não houve prejuízo identificável — o `confidence-report.md` continha as 17 lacunas agrupadas — mas a rastreabilidade é indireta.

2. **Dois pré-requisitos do Screen Translator estavam ausentes** (`design-system/` e `ui/inventory.md`). Contornados com o código-fonte legado (mitigação prevista nos casos de borda EC-17/EC-18). Consequência: os tokens são **derivados** (DEV-006) e o inventário é **fonte primária** (DEV-007), não reconciliado com um artefato de Discovery. Se você rodar `reversa-visor` ou `reversa-design-system` depois, **reconcilie**.

3. **Duas correções foram necessárias durante o pipeline**, ambas registradas em `.state.json § corrections`:
   - **AMB-004**: o orquestrador inferiu o conteúdo de `questions.md` a partir de um resumo antes de ler o arquivo, e afirmou incorretamente que as respostas estavam "apenas em prosa no `reconstruction-plan.md`". O Curator **corrigiu**: as respostas estão no próprio `questions.md`, nas linhas 16, 27, 38 e 49. **A conclusão não mudou** (são comportamento congelado → MIGRAR); a rastreabilidade **melhorou**.
   - **Encoding**: um script PowerShell introduziu mojibake (`DECISÃƒO`) ao fechar as decisões do Curator. **Corrigido** por round-trip UTF-8 explícito e **verificado** por varredura de assinaturas em todos os artefatos. A única ocorrência remanescente é **intencional** (o exemplo `Ã§` em BR-MIGRAR-006, que documenta o próprio mojibake).

4. **Uma lacuna de catálogo foi contornada**: o par de adapter detectado (`server-rendered-jinja2-bootstrap` → `web-spa`) **não existe** no `adapter-pairs.md` v1. Foi usado `html_legacy__spa` como **proxy** (DEV-001), por o propósito ser idêntico. Registrado para o mantenedor do catálogo.

5. **A métrica primária do brief está especificada mas não executada.** `parity_specs.md` e os 99 cenários existem, mas **nada foi executado**: não há harness, não há fixtures materializadas, não há goldens de tela. **A paridade de 100% é o objetivo, não um resultado.** Ela só se torna um fato depois da Onda 0.

## Notas finais

- **O que este pipeline entregou**: specs executáveis que dispensam o codificador de inventar arquitetura, modelo de dados, texto de tela, critério de paridade ou plano de corte. Toda decisão tem rastreabilidade para o legado ou para uma decisão humana registrada.
- **O que este pipeline NÃO entregou**: código, e **nenhuma prova empírica de paridade**. A estratégia escolhida (Parallel Run) torna a prova **possível e barata** — não a torna feita.
- **Onde está o risco real**: **não** na arquitetura, no schema ou nas telas — essas são decisões de fronteira, reversíveis e modernizáveis. O risco está concentrado em **dois pontos**: (1) o **oráculo ser válido** (RISK-002 — precisa apontar para `app.py`, não para a reconstrução); e (2) **transcrever corretamente** os dados que só existem no código do legado (RISK-003). Ambos são endereçados pela **Onda 0** e pela **Onda 1**.
- **O núcleo é a única coisa que não pode ser corrigida depois com baixo custo.** A fronteira pode ser refatorada, a UI redesenhada, o schema migrado. O matching, uma vez em produção com resultados divergentes, contamina a confiança de todos os resultados já produzidos — e dado genético não permite "reprocessar a confiança". Por isso a ordem das ondas coloca o núcleo primeiro.
- **Recomendação de sequenciamento prático**: comece pela **Onda 0**, e comece pelo golden mais barato do `manifest.yaml` — `SCR-G02` (submeter o formulário sem arquivo), que prova uma **mensagem congelada** sem exigir **nenhuma fixture**. É o menor passo possível que produz evidência real de paridade, e ele valida que o harness funciona antes de você investir na materialização das fixtures de GEDCOM e CSV.
- **O legado está intacto.** Nenhum arquivo em `analisador-genealogico/` foi criado, modificado, movido ou removido em nenhum momento do pipeline. Ele permanece a **especificação executável** do comportamento congelado e deve ser preservado mesmo após o cutover (o `cutover_plan.md` recomenda não removê-lo no decommission).
