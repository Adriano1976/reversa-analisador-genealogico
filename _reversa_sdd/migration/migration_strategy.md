---
schemaVersion: 1
generatedAt: 2026-09-28T03:00:12Z
reversa:
  version: "1.2.58"
kind: migration_strategy
producedBy: strategist
hash: "sha256:237433895c1e0f4f53b059ad3ec325ead2a54d3bca45a7b5bb610e84d42cf673"
---

# Migration Strategy

> Estratégias de migração avaliadas com trade-offs explícitos. A estratégia recomendada é a sugestão do Strategist; a decisão final é humana.

## Contexto sintetizado

| Dimensão | Valor | Fonte |
|---|---|---|
| **Tamanho do legado** | 1 monolito Flask, `app.py` ~888 linhas; 3 units funcionais (`upload-gedcom`, `busca-caminho`, `analise-dna`); 1 tela | `architecture.md` §1, `inventory.md` §3 |
| **Integrações externas vivas** | **Nenhuma.** Sem API REST/GraphQL consumida ou produzida. Apenas leitura local de `.ged`/`.csv` e assets de CDN | `architecture.md` §4, §6 |
| **Volume de dados a migrar** | **Zero.** Estado 100% em memória (dicionários + grafo `networkx`); nenhum SGBD; sem `data-dictionary.md` | `architecture.md` §1, §5; `inventory.md` §5 |
| **Schema legado a preservar** | **Nenhum.** Não há banco — o `data_migration_plan.md` será de **modelagem nova** | `migration_brief.md` § Notas livres |
| **Legado em produção?** | **NÃO.** Sem CI/CD, sem Docker, sem workflow. `gunicorn` no `requirements.txt` é 🟡 INFERIDO | `architecture.md` §5 (dívida #3), §6; `inventory.md` §6 |
| **Usuários reais hoje** | **Nenhum.** Uso local single-user, sem autenticação | `domain.md` §4 |
| **Apetite derivado** | `balanced` (opção 3 — híbrido) | `paradigm_decision.md` § Apetite derivado |
| **Severidade do gap de paradigma** | **alto** (`procedural → OO com DI`) | `paradigm_decision.md` § Gap identificado |
| **Restrições do brief** | Prazo **indefinido**; orçamento **indefinido**; **LGPD/GDPR** p/ dado genético; matching **congelado**; **GEDCOM/CSV inegociável**; escopo **integral** | `migration_brief.md` § Restrições |
| **Regras críticas do Curator** | 34 MIGRAR (todo o núcleo congelado), 7 DESCARTAR (plumbing), 8 DECISÃO HUMANA **resolvidas** | `target_business_rules.md` § Resumo |
| **Reconstrução existente** | `reconstructed/{domain,upload,path_search,dna_analysis}.py` + 47 testes passando | `reconstruction-report.md` |
| **Motor de paridade do alvo** | Python 3.12+ (mesma linguagem do legado) | `migration_brief.md` § Stack alvo |

**Três fatos que dominam a decisão estratégica:**

1. **Não existe sistema em produção a estrangular.** O Strangler Fig pressupõe um sistema vivo, com tráfego, onde se substitui comportamento incrementalmente atrás de um roteador. Aqui não há tráfego, não há usuários, não há deploy. *Strangler Fig não tem o que estrangular.*

2. **Não há dados a migrar.** Sem banco, sem schema, sem volume. A única "migração de dados" é o **estado em memória virar modelo persistido** — o que é *modelagem nova*, não conversão. Isso remove a classe inteira de riscos de ETL (Perda de dados, divergência de schema, janela de congelamento de escrita).

3. **O alvo é a mesma linguagem do legado.** O núcleo algorítmico (BR-MIGRAR-006 a BR-MIGRAR-034) pode ser **portado e executado lado a lado com o legado no mesmo processo Python**. Isso torna a validação de paridade — a métrica primária do brief — **executável de forma direta e barata**, e não uma aspiração.

## Estratégias avaliadas

### Estratégia A: Strangler Fig
- **Descrição**: manter o Flask rodando e substituir comportamento incrementalmente atrás de um proxy/gateway, roteando funcionalidade por funcionalidade para o sistema novo até o legado ficar oco.
- **Quando aplica** (catálogo): *"sistema em produção, não pode parar; necessidade de incrementalidade; possibilidade de roteamento (proxy / API gateway)"*.
- **Custo**: médio. **Risco**: baixo. **Tempo**: longo.
- **Adequação ao apetite derivado** (`balanced`): o catálogo favorece Strangler para `balanced` — **mas apenas sob a premissa de sistema em produção**.
- **Trade-offs**:
  - Prós: risco de regressão contido por construção; permite convivência; rollback trivial por rota.
  - Contras: **nenhuma das três premissas do catálogo se verifica**. Não há produção (sem deploy, sem CI/CD), não há tráfego a rotear, e as duas UIs são radicalmente diferentes (Jinja2 SSR vs SPA React) — não há como rotear *parte* de uma tela entre dois front-ends sem construir a UI duas vezes. O custo real seria montar infraestrutura de proxy para estrangular um sistema que **ninguém está usando**. Adiciona maquinário sem reduzir risco real.

### Estratégia B: Big Bang
- **Descrição**: construir o sistema novo por completo e substituir o legado de uma vez, no cutover.
- **Quando aplica** (catálogo): *"sistema pequeno; janela tolerada; apetite transformacional; poucas integrações vivas"*.
- **Custo**: baixo. **Risco**: alto. **Tempo**: curto.
- **Adequação ao apetite derivado** (`balanced`): **parcialmente inadequada** — o catálogo reserva Big Bang para apetite `transformational` em sistemas pequenos.
- **Trade-offs**:
  - Prós: **três de quatro premissas se verificam** — o sistema é genuinamente pequeno (`app.py` ~888 linhas), há janela total (não há produção a parar) e não há integrações vivas. Custo mais baixo e tempo mais curto.
  - Contras: **a quarta premissa falha, e é a decisiva** — o apetite é `balanced`, não `transformacional`. Além disso o legado tem lógica crítica e o catálogo é categórico: *"sistema com integrações regulatórias → nunca recomendar Big Bang"*. Aqui há restrição **regulatória** explícita (LGPD/GDPR para dado genético) **e** lógica crítica congelada (matching A/B/C/D) que o brief elege como métrica #1. Um Big Bang entregaria tudo de uma vez, incluindo o núcleo congelado **sem prova de paridade acumulada** — exatamente o risco #1 declarado pelo usuário.

### Estratégia C: Parallel Run
- **Descrição**: executar o sistema novo em paralelo ao legado sobre as mesmas entradas e comparar resultados, acumulando evidência de equivalência antes de trocar.
- **Quando aplica** (catálogo): *"lógica crítica (financeiro / fiscal / regulatório); precisa de prova de equivalência por longo período"*.
- **Custo**: alto. **Risco**: médio. **Tempo**: médio.
- **Adequação ao apetite derivado** (`balanced`): **alta** — é a estratégia que o catálogo pareia com `balanced`.
- **Trade-offs**:
  - Prós: **é a única estratégia que ataca diretamente o risco #1 e a métrica #1 do brief.** O brief exige *"paridade de matching ≥ 100% nos casos de teste"*; Parallel Run produz essa evidência por construção. E aqui ele é **anormalmente barato**: o legado é Python e o alvo é Python — as duas implementações rodam no mesmo harness de teste, sem infraestrutura de comparação, sem tráfego espelhado, sem dual-write. O `app.py` está no disco e é executável.
  - Contras: custo "alto" no catálogo refere-se ao custo de **manter dois sistemas em produção simultânea** (dual-write, reconciliação contínua). **Esse custo não existe aqui**, porque não há produção: a "execução paralela" é **em lote, sobre fixtures**, não em tempo real sobre tráfego. Sem usuários, não há dois sistemas a operar — há um oráculo e um candidato.

### Estratégia D: Branch by Abstraction
- **Descrição**: introduzir uma abstração estável e trocar a implementação por trás dela, mantendo o domínio no lugar.
- **Quando aplica** (catálogo): *"migração interna (linguagem ou framework muda, domínio fica); apetite conservador"*.
- **Custo**: baixo. **Risco**: baixo. **Tempo**: médio.
- **Adequação ao apetite derivado** (`balanced`): adequada, mas **apenas como mecanismo interno**.
- **Trade-offs**:
  - Prós: é o mecanismo correto **para a fronteira** — substituir Flask por FastAPI atrás de uma camada de aplicação é literalmente trocar implementação atrás de abstração. Já está autorizado pelo `paradigm_decision.md` (DI/repositórios na borda).
  - Contras: **não é uma estratégia de migração completa** — não endereça paridade do núcleo, sequenciamento, nem cutover. É um padrão de substituição, não um plano. Recomendá-la como *a* estratégia deixaria o risco #1 (fidelidade do matching) sem tratamento, e o catálogo é claro que ela é favorecida por apetite `conservative`, não `balanced`.

## Comparativo

| Critério | A — Strangler Fig | B — Big Bang | C — Parallel Run | D — Branch by Abstraction |
|---|---|---|---|---|
| Custo | médio | baixo | **alto no catálogo → baixo aqui** (sem produção; mesmo runtime) | baixo |
| Risco | baixo | **alto** | médio | baixo |
| Tempo | longo | curto | médio | médio |
| Aderência ao apetite (`balanced`) | média (catálogo favorece, premissa ausente) | **baixa** (catálogo pede `transformational`) | **alta** (par do catálogo p/ `balanced`) | média (catálogo pede `conservative`) |
| Premissas verificadas | **0 de 3** | 3 de 4 | **n/a — 2 de 2** (lógica crítica + prova de equivalência) | 1 de 2 |
| Ataca o risco #1 (fidelidade do matching) | não | **não** | **sim** | não |
| Ataca a métrica #1 (paridade ≥ 100%) | não | não | **sim** | não |
| Compatibilidade com mudança de paradigma (alto) | sim | sim | sim | **sim** (é o mecanismo da fronteira) |
| Aplicável com escopo integral + LGPD | parcial | **viola regra do catálogo** | sim | parcial |

## Recomendação do Strategist

- **Estratégia recomendada**: **C — Parallel Run**, materializada como **ondas incrementais com validação diferencial obrigatória** (Parallel Run é o *mecanismo de verificação*; as ondas são o *sequenciamento*). Usar **D — Branch by Abstraction** como padrão interno da fronteira, conforme já decidido em `paradigm_decision.md`.

- **Justificativa** (rastreada a brief + paradigma + apetite):

  1. **O brief declara paridade de matching ≥ 100% como métrica primária.** Só Parallel Run a produz de forma verificável. Big Bang a deixa como esperança; Strangler não a endereça.

  2. **O apetite é `balanced`.** O catálogo pareia `balanced` com *"Strangler Fig + Parallel Run"*. Strangler está fora por premissa ausente (não há produção) — sobra Parallel Run, e a recomendação é literalmente o par prescrito.

  3. **O catálogo proíbe Big Bang** para sistemas com integrações regulatórias, e há restrição regulatória explícita (LGPD/GDPR). Somado ao risco #1 declarado pelo próprio usuário, Big Bang está duplamente excluído.

  4. **Parallel Run tem aqui um custo marginal quase nulo**, o que inverte sua posição no catálogo: o custo "alto" pressupõe operar dois sistemas em produção sobre tráfego real. Aqui as duas implementações são Python, o legado está no disco, e a comparação é **em lote sobre fixtures**. É a rara situação em que a estratégia de maior rigor é também a mais barata.

  5. **O gap de paradigma é alto, o que dispara o sinal explícito do SKILL.md** — *"mudança grande de paradigma sempre dispara registro explícito de risco operacional"* — e o catálogo manda recomendar Parallel Run para validar paridade nas regras críticas. Ambos convergem para a mesma conclusão.

  6. **O sistema é genuinamente pequeno** (~888 linhas, 3 units, sem integrações), então o número de ondas é baixo e o custo total permanece modesto — o argumento que favoreceria Big Bang por tamanho é atendido pelas ondas curtas, sem seu risco.

- **Sequenciamento proposto** (as ondas são parte da recomendação, não um detalhe de implementação):

  | Onda | Entrega | Validação | Depende de |
  |---|---|---|---|
  | **0** | **Oráculo congelado**: harness diferencial + golden files extraídos do `app.py` sobre fixtures | n/a (é a fundação da validação) | — |
  | **1** | **Núcleo portado como funções puras** (mojibake, score, A/B/C/D, Jaccard, tabela de cM, caminho, agregação) | **Diferencial 100% contra o oráculo.** Nenhuma feature nova. | Onda 0 |
  | **2** | **Fronteira de aplicação**: FastAPI, Pydantic, exceções de domínio tipadas, status HTTP | Contrato + paridade de mensagens/comportamento de erro | Onda 1 |
  | **3** | **Multiusuário**: auth, `owner_id` como invariante, persistência PostgreSQL, repositórios escopados | Isolamento por tenant (teste negativo: usuário A não vê dado de B) | Onda 2 |
  | **4** | **SPA React** + visualização de grafo (preservando `split_path_by_marriage`/`are_spouses` como funções puras) | Paridade da decomposição do caminho | Onda 3 |
  | **5** | **Conformidade LGPD/GDPR**: criptografia, consentimento, retenção/expurgo, direito de exclusão | Requisitos regulatórios + auditoria | Onda 3 (criptografia/isolamento) / Onda 4 (fluxos de consentimento) |
  | **6** | **Cutover** e operação; legado preservado como oráculo congelado | Go/no-go do `cutover_plan.md` | Ondas 1–5 |

  A ordem é deliberada: **a Onda 1 concentra todo o risco de paridade e não depende de nada além do oráculo.** Ela pode ser executada e provada antes de qualquer decisão de infraestrutura, de UI ou de conformidade. Se a Onda 1 falhar em atingir paridade, descobre-se isso com custo baixo e antes de construir o resto.

- **Por que não recomendo A nem B, em uma linha cada**: **A** montaria infraestrutura de roteamento para estrangular um sistema sem tráfego e exigiria construir a UI duas vezes; **B** entregaria o núcleo congelado sem prova de paridade e viola a regra do catálogo sobre sistemas regulados.

## Sinais de alerta específicos

- **Gap alto + `balanced`** → Parallel Run é obrigatório para as regras críticas (A/B/C/D, score, Jaccard, tabela de cM). Já incorporado na recomendação como Onda 0 + Onda 1.
- **⚠️ Risco de o oráculo ser frágil**: se os golden files forem gerados a partir da **reconstrução** (`reconstructed/*.py`) em vez do **legado** (`analisador-genealogico/app.py`), a validação vira circular — a reconstrução seria validada contra si mesma. Os 47 testes existentes **já têm esse defeito** (testam a reconstrução, não o legado). O oráculo **deve** ser extraído do `app.py` original. Registrado como RISK-002.
- **⚠️ Transcrição a partir de código, não de specs**: BR-MIGRAR-011 (lista de primeiros nomes genéricos) e BR-MIGRAR-012 (tabela de equivalentes de grafia) existem **somente em `app.py`**. Se o port os reconstruir de memória, a paridade quebra silenciosamente e o oráculo é a única defesa. Registrado como RISK-003.
- **⚠️ Aritmética de ponto flutuante**: agregação de cM (BR-MIGRAR-016), ordem de soma do score (BR-MIGRAR-009) e desempate (BR-MIGRAR-015) são não-associativos. Introduzir persistência com `SUM` do PostgreSQL pode alterar o último dígito e cruzar um limite de faixa de cM. O diferencial deve comparar **valores exatos**, não aproximados. Registrado como RISK-004.
- **⚠️ Escopo integral sem prazo e com decisor único** (AMB-003) → risco de execução, mitigado pelo fatiamento em ondas com paridade por onda.
- **⚠️ Regulatório sem definição de negócio**: falta base legal e prazo de retenção (BR-HUMANA-007). A Onda 5 não pode ser especificada completamente até o usuário declarar isso.
- **Sensibilidade ao prazo**: o brief é explicitamente *"sem prazo"* e *"qualidade sobre velocidade"*. A recomendação, portanto, **não** é sensível a prazo — o que reforça Parallel Run sobre Big Bang. Se o usuário introduzir prazo agressivo depois, **esta recomendação precisa ser revisitada**: a estratégia de menor tempo é B (Big Bang), e a mitigação do risco de paridade teria que vir de revisão linha-a-linha em vez de diferencial executável.

## Decisão humana

- **Estratégia escolhida**: **C — Parallel Run**, materializada como ondas incrementais com validação diferencial obrigatória, usando **Branch by Abstraction** como padrão interno da fronteira.
- **Quem decidiu**: Adriano
- **Quando**: 2026-09-28T03:02:10Z
- **Justificativa do decisor**: selecionou a opção recomendada pelo Strategist. Justificativa reconstruída pelo orquestrador a partir do diagnóstico apresentado, sujeita a correção:
  - É a única estratégia que produz a evidência exigida pela **métrica primária do brief** (paridade de matching ≥ 100%), em vez de deixá-la como esperança.
  - É o par prescrito pelo catálogo para o apetite `balanced` que o usuário escolheu (opção 3 — híbrido).
  - **Big Bang está duplamente excluído**: o apetite não é `transformational` e o catálogo proíbe Big Bang para sistemas com integrações regulatórias (há LGPD/GDPR).
  - **Strangler Fig não tem premissa**: o legado nunca esteve em produção e as duas UIs são incompatíveis com roteamento parcial.
  - O custo marginal do Parallel Run neste projeto é quase nulo (mesmo runtime Python, validação em lote sobre fixtures, sem produção a operar em paralelo), o que inverte sua posição no catálogo.
  - O sequenciamento em ondas com paridade por onda endereça AMB-003 (escopo integral, sem prazo, decisor único) sem reduzir escopo unilateralmente.
- **Consequências registradas**:
  - As **7 ondas** da tabela acima tornam-se o sequenciamento vinculante. `cutover_plan.md` passa a valer como escrito.
  - A **regra de sequenciamento rígida**: nenhuma onda avança com paridade pendente (mitigação de RISK-008).
  - A **Onda 0 é o primeiro trabalho a executar** e não depende de nenhuma decisão de negócio em aberto.
  - Se o usuário introduzir prazo agressivo posteriormente, esta decisão precisa ser revisitada — o caminho mais curto seria cortar as Ondas 4–5.

## Notas

- **A recomendação tem uma consequência que o usuário deve encarar explicitamente**: a Onda 1 preserva o núcleo **copiando o comportamento do legado, inclusive os defeitos** — a lista incompleta de mojibake (BR-HUMANA-005), o 1º ID cego para homônimos (BR-HUMANA-003, mitigado por sinalização), o caminho por pais que ignora famílias adotivas. Isso é intencional e foi decidido. O que **não** deve ser copiado é o *mecanismo*: funções puras, não estado global.
- **O legado nunca será modificado.** Ele é usado como oráculo (executado, nunca escrito). A regra absoluta do Reversa é preservada: nada fora de `_reversa_sdd/migration/` é tocado.
- **`cutover_plan.md` foi escrito para a estratégia recomendada** (Parallel Run em ondas). Se o usuário escolher outra, o plano precisa ser reescrito — registrado no topo daquele artefato.
