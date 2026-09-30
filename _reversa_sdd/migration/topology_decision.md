---
schemaVersion: 1
generatedAt: 2026-09-28T03:05:30Z
reversa:
  version: "1.2.58"
kind: topology_decision
producedBy: designer
hash: "sha256:b74af37922a0a255330108551a59c679c9414f42641e6124a32141e320acf8ba"
---

# Topology Decision

> Decisão consciente sobre como organizar o sistema novo: preservar a topologia do legado, adotar uma topologia moderna ou aplicar um híbrido.
> Este artefato é leitura obrigatória do próprio Designer (para decompor bounded contexts) e do agente de codificação (para criar a árvore de pastas).

## Topologia do legado detectada

- **Padrão organizacional**: **monolito sem fronteiras claras** (single-module monolith), com organização por camada apenas nos assets estáticos.
- **Confiança**: 🟢 CONFIRMADO
- **Evidências**:
  - `inventory.md` §2 (Estrutura de Árvore de Diretórios): **todo o código Python vive em um único arquivo**, `app.py`. Não existem pacotes, módulos por domínio, camadas de código ou bounded contexts.
  - `architecture.md` §5 (dívida #5): *"Código monolítico (app.py ~887 linhas) com rotas + lógica acopladas — Responsabilidades de parsing, matching e renderização num único módulo."*
  - `inventory.md` §3 (Mapeamento por Módulo): as fronteiras declaradas são **tipos de arquivo**, não domínios — 1 arquivo Python (`app.py`), 1 template (`templates/index.html`), 1 página estática (`static/graph_path_search.html`), 1 pasta de dados (`uploads/`).
  - `code-analysis.md` §2 (Estrutura e Modularidade): a "arquitetura lógica" é descrita como **blocos funcionais internos ao módulo** — `[Entrada HTTP: Flask Routes]` acima de dois `Action` (`process_dna` e `path_search`) com funções aninhadas. É a ausência de topologia explícita, retratada como hierarquia de chamadas.
  - `inventory.md` §4 (Pontos de Entrada): **as 3 rotas do sistema estão no mesmo `POST /`**, despachadas por um campo `action` do formulário (`upload_gedcom`, `dna_analysis`, `path_search`). Não há separação nem sequer no nível do roteamento HTTP — o que confirma ausência de fronteira em qualquer nível.
  - `dependencies.md` §1: gerenciador único (`pip` + `requirements.txt`), sem workspace, sem monorepo, sem publicação de pacote.
- **Mapa da árvore legada** (resumido):
  ```
  analisador-genealogico/
  ├── app.py                      # TODO o sistema: rotas + parsing + matching + grafos + render
  ├── requirements.txt            # 9 dependências, nenhuma com versão fixada
  ├── README.md
  ├── .gitignore.txt
  ├── templates/
  │   └── index.html              # única tela (Bootstrap 5 + Mermaid via CDN)
  ├── static/
  │   └── graph_path_search.html  # página gerada pelo pyvis
  └── uploads/                    # arquivos .ged/.csv salvos com o nome do cliente
  ```
  **Não existe nenhum diretório de código.** A árvore não expressa domínio, camada nem fronteira — expressa apenas tipo de artefato.

## Diagnóstico estrutural

- **Acoplamento**: **alto**. Evidências convergentes: (a) estado global mutável de processo (`people`, `families`, `graph`, `child_to_family`) compartilhado por todas as funções — `upload-gedcom/design.md` § Estado Interno; (b) a reconstrução precisou mutar esses globais **in-place** (`clear` + `update`) para que `path_search` e `dna_analysis` enxergassem a carga de `upload` (`reconstruction-report.md` § Correções aplicadas) — prova de acoplamento por variável de módulo, não por contrato; (c) `dna_analysis` chama `find_ancestral_path`, que pertence conceitualmente a `busca-caminho` — o núcleo de caminho é compartilhado entre duas unidades de negócio sem interface declarada; (d) `analise-dna/design.md` § passo 1 mostra a análise de DNA **re-parseando o GEDCOM**, duplicando responsabilidade do upload.
- **Coesão por módulo**: **alta como bloco único, inexistente como módulo**. O sistema inteiro serve **um** caso de uso (cruzar árvore GEDCOM com matches de DNA e explicar o parentesco), então o monolito é coeso no propósito. Mas como não há módulos, não há unidade sobre a qual medir coesão — a granularidade é `app.py` inteiro. Isso é relevante: **não há débito de "módulos coesos misturados", há ausência de módulos.**
- **Módulos órfãos / mortos**: **1**. `HARD_MIN = 92` e `GIVEN_MIN = 90` declarados e nunca usados (`analise-dna/design.md` § Decisões; `confidence-report.md` § Reclassificações 🟢→🟡). Confirmado como código morto. Nenhum outro.
- **Camadas redundantes**: **nenhuma em código** — não há camadas. Em assets, `static/graph_path_search.html` (pyvis) e `templates/index.html` (Mermaid) são **duas tecnologias de visualização de grafo coexistindo** para o mesmo propósito, o que é redundância funcional, não de camada (`inventory.md` §3; `dependencies.md` §2 lista `pyvis` e `matplotlib` ambas para visualização).
- **Violações de fronteira**: **todas, pela inexistência de fronteiras**. As mais materiais: (a) o **controller contém o domínio** — `process_dna_action` executa o pipeline completo incluindo `groupby.agg` de cM e o scoring difuso (`code-analysis.md` §3); (b) o **domínio emite apresentação** — `generate_mermaid_graph` produz sintaxe de diagrama dentro da lógica de caminho (`busca-caminho/design.md` § Interface); (c) **persistência implícita** — `uploads/` é simultaneamente armazenamento e estado de sessão, com o nome do arquivo do cliente como chave de referência (`upload-gedcom/design.md` § Decisões, `app.py:569`).
- **Mistura de paradigmas/estilos**: **homogêneo no modelo mental, misto nas ferramentas**. O estilo é uniformemente procedural (funções top-level + estado global, conforme `paradigm_decision.md` § Paradigma do legado, 🟢 CONFIRMADO). Não há mistura de paradigmas. O que há é uso de containers ricos (`pandas.DataFrame`, `networkx.Graph`) que dão aparência de estrutura onde não existe camada.
- **Avaliação geral**: **problemática** — mas por **ausência**, não por confusão. A causa principal em uma linha: *não existem fronteiras, e as três que importam (domínio vs. aplicação, domínio vs. apresentação, domínio vs. persistência) estão todas violadas dentro de um único arquivo*. A consequência prática é a que o próprio `architecture.md` §5 registra: *"Ausência total de testes"* e *"re-parse a cada requisição"* — ambas sintomas diretos de não haver núcleo isolável.

> **Nota importante para a decisão**: como o diagnóstico é "problemática por ausência de topologia", as opções 1 (preservar) e 2 (modernizar) **não são simétricas** neste caso. Preservar significaria perpetuar a ausência de fronteiras — o que colidiria com o paradigma já decidido (`OO com DI`, `paradigm_decision.md`) e com a estratégia já confirmada (Parallel Run, que **exige** o núcleo isolável para comparação — `designer/SKILL.md` § Princípios, item 5). A opção 1 está, portanto, tecnicamente disponível mas materialmente incompatível com duas decisões humanas já tomadas.

## Topologia moderna proposta

- **Padrão**: **Arquitetura hexagonal (ports & adapters) com bounded contexts por capacidade de análise na camada de domínio** — núcleo puro cercado por adaptadores, e o núcleo subdividido por capacidade (árvore, matching, caminho) em vez de por camada técnica.
- **Justificativa** (encadeada às decisões já tomadas, não a preferência estética):
  - **Honra o paradigma `OO com DI` + apetite `balanced`** (`paradigm_decision.md`): a fronteira ganha ports/adapters e injeção; o núcleo permanece funções puras. É literalmente a "regra de fronteira" registrada no `paradigm_decision.md`: *algoritmo de negócio → núcleo puro; plumbing → borda com DI*.
  - **Honra a estratégia `Parallel Run`** (`migration_strategy.md`): `designer/SKILL.md` § Princípios item 5 diz que Parallel Run exige *"componentes críticos isoláveis para comparação"*. Sem núcleo puro e sem dependência de I/O, o harness diferencial não pode executar o candidato sobre as mesmas fixtures do legado. **A estratégia confirmada pelo usuário torna o núcleo isolável um requisito, não uma preferência.**
  - **Ataca a causa raiz do diagnóstico**: as três violações de fronteira mapeadas (controller contém domínio; domínio emite apresentação; persistência implícita) são exatamente o que ports & adapters elimina por construção.
  - **Adequado ao tamanho**: ~888 linhas, 3 capacidades, 1 desenvolvedor. Uma topologia pesada (DDD completo com 6+ bounded contexts, event sourcing, monorepo) seria desproporcional. Hexagonal com núcleo enxuto é o menor padrão que resolve a causa raiz.
  - **Subdividir o núcleo por capacidade (não por camada)** é justificado porque as três capacidades têm **ciclos de mudança e donos de invariante distintos**: a árvore GEDCOM é estrutura de dados; o matching é heurística estatística; o caminho é algoritmo de grafo. `busca-caminho` depende de `matching`? Não — mas `analise-dna` depende de `pathfinding` (chama `find_ancestral_path`), o que **prova** que são capacidades separáveis com dependência direcional, não um bloco.
- **Ganhos concretos esperados**:
  - **Testabilidade diferencial** (o ganho decisivo): o núcleo puro é executável sobre fixtures sem HTTP, sem Flask, sem banco — condição para a Onda 0/1 do `cutover_plan.md`.
  - **Isolamento da paridade**: uma mudança na fronteira (auth, persistência, UI) **não pode** alterar o resultado do matching, porque a fronteira não tem caminho de código até o núcleo além dos ports.
  - **Onboarding**: a árvore passa a explicar o sistema. Hoje, entender `app.py` exige ler 888 linhas; a proposta permite ler `domain/tree` para entender árvore e ignorar o resto.
  - **Eliminação das violações de fronteira**: apresentação sai do domínio (o núcleo devolve estrutura de caminho tipada — decidido em BR-HUMANA-008), persistência vira port, controller vira caso de uso fino.
- **Custo / risco**:
  - **Curva de aprendizado** em hexagonal/ports & adapters (mitigado por ser um padrão pequeno e bem documentado — ver RISK-012).
  - **Esforço de reorganização**: todo o `app.py` precisa ser desmontado e redistribuído. É o custo real e ele é **concentrado na Onda 1**, que é justamente a onda com oráculo para guiar (RISK-001).
  - **Risco de over-engineering**: mitigado mantendo o núcleo em **funções puras** (não classes com estado) e evitando bounded contexts artificiais — apenas 3, todos derivados de capacidades que já existem como units de fato.
  - **Risco de cerimônia excessiva nos ports**: mitigado aceitando que ports de leitura podem ser interfaces mínimas (1–2 métodos).
- **Esboço da árvore proposta**:
  ```
  analisador/                       # projeto novo (não toca o legado)
  ├── core/                         # NÚCLEO — funções puras, zero I/O, zero framework
  │   ├── names/                    # BR-MIGRAR-006,007,012 — mojibake, normalização, equivalentes
  │   │   ├── mojibake.py           # strip_bad_utf, demojibake  (transcrição literal)
  │   │   └── normalization.py      # norm_name, split_name_pt, surnames_set
  │   ├── matching/                 # BR-MIGRAR-008..015 — scoring e aceitação
  │   │   ├── score.py              # 0.55/0.25/0.20 + InterBonus
  │   │   ├── acceptance.py         # regras A/B/C/D + Jaccard relaxado
  │   │   └── relationship.py       # tabela de cM (9 faixas)
  │   ├── tree/                     # BR-MIGRAR-001..004 — GEDCOM => estrutura de domínio
  │   │   ├── model.py              # Person, Family, GedcomTree (sem persistência)
  │   │   └── parser.py             # ged4py => GedcomTree (função pura: bytes -> árvore)
  │   ├── pathfinding/              # BR-MIGRAR-022..027,029..031
  │   │   ├── ancestral.py          # BFS bidirecional, max_depth=20
  │   │   ├── indirect.py           # shortest_path + compressão, max_hops=40
  │   │   └── decomposition.py      # split_path_by_marriage, are_spouses (BR-HUMANA-008)
  │   ├── dna/                      # BR-MIGRAR-016..021 — CSV => matches agregados
  │   │   ├── csv_reader.py         # fallback UTF-8/Latin-1, detecção de colunas
  │   │   └── aggregation.py        # _group_key, soma de cM (ordem preservada)
  │   └── shared/                   # kernel compartilhado, sem dono de capacidade
  │       └── constants.py          # TODOS os limiares, com referência a app.py:<linha>
  ├── application/                  # CASOS DE USO — orquestram o núcleo, sem I/O direto
  │   ├── upload_tree.py
  │   ├── analyze_dna.py
  │   └── search_path.py
  ├── ports/                        # INTERFACES — o contrato da fronteira
  │   ├── tree_repository.py        # escopado por owner_id (RISK-005)
  │   ├── file_storage.py
  │   └── unit_of_work.py
  ├── adapters/                     # INFRAESTRUTURA DE SAÍDA
  │   ├── persistence/              # PostgreSQL: repositórios + migrations
  │   └── storage/                  # object storage, chave gerada pelo servidor
  ├── api/                          # ADAPTADOR DE ENTRADA HTTP
  │   ├── routers/                  # FastAPI routers (um por caso de uso)
  │   ├── schemas/                  # Pydantic: payloads e erros tipados
  │   └── errors.py                 # exceções de domínio => status HTTP
  ├── presentation/                 # REACT SPA (front-end)
  └── tests/
      ├── parity/                   # ONDA 0 — harness diferencial + golden files
      └── unit/                     # testes do núcleo puro
  ```
  **Nota de rastreabilidade do esboço**: `core/tree`, `core/dna` e `core/pathfinding` **não** são renomeações dos units `upload-gedcom`, `busca-caminho` e `analise-dna`. Diferem deliberadamente — ver § Mapeamento legado → novo e as justificativas de fusão/divisão.

## Opções apresentadas ao usuário

1. **Preservar topologia legada** (conservador)
   - Consequências: manter tudo em um módulo (ou reproduzir a divisão por tipo de artefato: `routes.py`, `services.py`, `models.py`). Reduz o risco de reorganização ao mínimo e torna o port quase mecânico. **Perpetua a ausência de fronteiras** e, com ela, as três violações mapeadas. ⚠️ É **materialmente incompatível** com duas decisões já tomadas: o paradigma `OO com DI` (`paradigm_decision.md`) e a estratégia Parallel Run, que exige núcleo isolável para comparação (`designer/SKILL.md` § Princípios item 5). Sem núcleo puro, a Onda 1 do `cutover_plan.md` não é executável.
2. **Adotar topologia moderna proposta** (transformacional)
   - Consequências: hexagonal completo com núcleo subdividido por capacidade. Rompe integralmente com o débito estrutural e maximiza o ganho de testabilidade diferencial. Exige desmontar `app.py` por inteiro e distribuir ~888 linhas em ~20 arquivos; maior esforço de reorganização, todo ele concentrado na Onda 1 (que tem oráculo para guiar).
3. **Híbrido** (equilibrado)
   - Consequências: adotar o **núcleo puro** e a **separação domínio/aplicação/apresentação/persistência** (as três violações de fronteira são eliminadas — são o que a migração existe para corrigir), mas **sem subdividir o núcleo em bounded contexts por capacidade**: `core/` fica plano porém puro (`core/mojibake.py`, `core/matching.py`, `core/tree.py`, `core/pathfinding.py`, `core/dna.py`, `core/constants.py`). Preserva-se a coesão do bloco único, que o diagnóstico reconheceu como **alta**, e evita-se decidir agora fronteiras internas que só a evolução vai justificar. Adaptadores, ports e API seguem o desenho moderno (são modernização livre, sem risco de paridade).

## Recomendação do Designer

- **Opção 3 (Híbrido)**, por três razões encadeadas:
  1. **É a única opção coerente com a sequência de decisões já tomada.** O usuário escolheu `balanced` no paradigma e Parallel Run na estratégia; ambos apontam para "modernizar a fronteira, preservar o núcleo". A opção 1 contradiz essas decisões; a opção 2 entrega ao núcleo uma estrutura interna que **nenhuma decisão pediu**.
  2. **Elimina 100% das violações de fronteira sem tocar na coerência do núcleo.** As três violações (controller com domínio, domínio com apresentação, persistência implícita) são resolvidas pela separação de camadas, não pela subdivisão do núcleo. O ganho de testabilidade diferencial — o ganho decisivo — vem do núcleo ser **puro**, não de ele ser **subdividido**.
  3. **O diagnóstico registrou coesão alta e nenhum módulo órfão.** Subdividir o núcleo em 3 bounded contexts seria criar fronteiras **sem evidência de necessidade** — exatamente a "decomposição por modernidade" que o `designer/SKILL.md` § Princípios item 2 manda evitar. Manter `core/` plano é a leitura fiel do diagnóstico; a subdivisão pode vir depois, quando houver pressão real de evolução, sem custo de paridade (o núcleo é puro e testado).

- **O que o híbrido explicitamente preserva do legado**: a **coesão do núcleo algorítmico como bloco único**, e a ordem de avaliação interna das regras — ambas são ativos de paridade, não débitos.
- **O que o híbrido explicitamente moderniza**: tudo que é fronteira — ports, adapters, casos de uso, API, ausência de estado global, ausência de render server-side. Nada disso tem risco de paridade, conforme a regra de fronteira do `paradigm_decision.md`.
- **Nota de honestidade sobre o custo**: a diferença de esforço entre as opções 2 e 3 é pequena na Onda 1 (criar `core/` plano vs. `core/` com 3 subpastas é quase o mesmo trabalho) e **cresce** nas ondas seguintes, onde a subdivisão criaria imports entre bounded contexts que ainda não têm razão de existir. A opção 3 é mais barata **e** menos arriscada; a opção 2 compraria opcionalidade de evolução ao preço de estrutura especulativa.

## Decisão do usuário

- **Escolha**: **3 — Híbrido** (núcleo puro e plano + fronteira hexagonal completa)
- **Justificativa do usuário**: selecionou a opção recomendada pelo Designer, sem texto adicional. Justificativa reconstruída pelo orquestrador a partir do diagnóstico apresentado, sujeita a correção:
  - O diagnóstico registrou **coesão alta, nenhum módulo órfão e nenhuma camada redundante em código**. As três violações de fronteira mapeadas são resolvidas pela **separação de camadas**, não pela subdivisão do núcleo — subdividir seria criar fronteiras sem evidência de necessidade, o que o `designer/SKILL.md` § Princípios item 2 proíbe.
  - O ganho decisivo — a **testabilidade diferencial** exigida pelas Ondas 0 e 1 do `cutover_plan.md` — decorre do núcleo ser **puro**, não de ele ser subdividido. A opção 3 entrega esse ganho integralmente.
  - A opção 2 compraria opcionalidade de evolução ao preço de estrutura especulativa, com custo maior nas ondas seguintes (imports entre bounded contexts sem razão de existir).
  - A opção 1 estava materialmente excluída: contradiz o paradigma `OO com DI` já decidido e torna a estratégia `Parallel Run` inexequível por falta de núcleo isolável.
- **Decidido em**: 2026-09-28T03:06:40Z
- **Consequências registradas**:
  - `core/` é **plano e puro**: `mojibake.py`, `normalization.py`, `matching.py`, `relationship.py`, `tree.py`, `parser.py`, `pathfinding.py`, `decomposition.py`, `dna.py`, `constants.py`. Nenhuma subpasta de bounded context dentro de `core/`.
  - A proibição de subdividir é **vinculante para a Fase 2**: os bounded contexts de `target_architecture.md` devem refletir **capacidades de negócio**, não espelhar arquivos de `core/`.
  - A fronteira (`application/`, `ports/`, `adapters/`, `api/`, `presentation/`) segue o desenho moderno sem restrição — é modernização livre conforme o `paradigm_decision.md`.
  - Restrição de dependência do núcleo: `core/` **não pode** importar `fastapi`, `sqlalchemy`, `pydantic` nem `flask`. Violação invalida a Onda 0 e deve ser detectada por teste automático.
  - O mapeamento legado → novo abaixo **permanece válido como está** (a opção 2 apenas acrescentaria subpastas a `core/`, sem alterar as linhas).

## Mapeamento legado → novo

> **Decomposição 1-para-1 proibida** (`designer/SKILL.md` § Regras absolutas). Cada linha é um **tipo** de mapeamento, e nenhuma é uma coluna renomeada. O mapeamento abaixo é o da **opção 3 (recomendada)**; se o usuário escolher a opção 2, `core/*` ganha subpastas por capacidade sem alterar as demais linhas.

| Módulo / pasta legada | Destino novo | Tipo | Observações |
|---|---|---|---|
| `app.py` (bloco `upload_gedcom`) + `load_gedcom_and_build_graph` + `build_graph_from_parser` + `get_name` | `core/tree/` + `application/upload_tree.py` + `adapters/storage/` | **dividido (3 destinos)** | O bloco misturava três responsabilidades: parse (→ `core/tree`), orquestração e ciclo de vida (→ `application`), e escrita em disco com nome do cliente (→ `adapters`, descartado em BR-DESCARTAR-003). A divisão é justificada pela regra de fronteira, não por preferência. |
| `app.py` (bloco `path_search`) + `find_person_by_name` + `find_ancestral_path` + `find_indirect_path` | `core/pathfinding/` + `core/tree/` (resolução de nome) + `application/search_path.py` | **dividido + fundido** | Dividido porque `find_person_by_name` é busca em índice de árvore (pertence a `core/tree`, junto do índice), enquanto os algoritmos de caminho formam um núcleo próprio. **Fundido** porque `find_ancestral_path` é usado por **duas** units do legado (`busca-caminho` e `analise-dna`) — no alvo vira **um** módulo de núcleo compartilhado, eliminando a duplicação conceitual. |
| `app.py` (bloco `dna_analysis`) + `build_group_key` + bloco de scoring + regras A/B/C/D + `get_relationships_by_cm` | `core/dna/` + `core/matching/` + `core/names/` + `application/analyze_dna.py` | **dividido (4 destinos)** | O maior bloco do legado concentrava 4 capacidades distintas: leitura/agregação de CSV (→ `core/dna`), limpeza e normalização de nomes (→ `core/names`), scoring e aceitação (→ `core/matching`) e relação por cM (→ `core/matching/relationship.py`, junto do matching por ser a mesma cadeia de decisão). Justificativa: são as capacidades com **ciclos de mudança distintos** e são as que o harness diferencial precisa exercitar isoladamente. |
| `demojibake`, `norm_name`, `split_name_pt`, `surnames_set`, `strip_bad_utf` | `core/names/` | **preservado** | Único mapeamento sem divisão. É uma capacidade autocontida, sem dependências de I/O, e é pré-requisito de `core/matching` e `core/dna`. Preservado como bloco porque **separá-lo não teria justificativa** — todos os seus elementos falham juntos (BR-MIGRAR-006, 007, 012). |
| `generate_mermaid_graph` + `generate_mermaid_graph_indirect_bridge` + `split_path_by_marriage` + `are_spouses` | `core/pathfinding/decomposition.py` (regras) + `presentation/` (desenho) | **dividido (2 destinos) com regras preservadas** | **Ponto mais delicado de todo o mapeamento.** As funções faziam duas coisas: decompor o parentesco (regra de negócio) e emitir sintaxe Mermaid (apresentação). BR-DESCARTAR-005 descarta a **emissão**; BR-HUMANA-008 (decidida) manda **preservar a decomposição** como função pura. `split_path_by_marriage` e `are_spouses` migram para o núcleo; `generate_mermaid_*` é removido e substituído por payload estruturado. Ver RISK-011. |
| `SHARED_CM_DATA` (tabela de cM) | `core/matching/relationship.py` | **preservado** | Tabela de domínio puro. Migra como dado, **com a ordem de avaliação preservada** (as 9 faixas se sobrepõem — BR-MIGRAR-020). |
| `HARD_MIN` / `GIVEN_MIN` (código morto) | — | **removido** | Código morto confirmado (`confidence-report.md`, `analise-dna/design.md`). Não é regra de negócio; não entra no alvo. Decisão já registrada na reconstrução e reafirmada pelo Curator. |
| Globais `people`, `families`, `graph`, `child_to_family` + re-parse por POST | `core/tree/model.py` (`GedcomTree`) + `ports/tree_repository.py` + `adapters/persistence/` | **removido e substituído** | Ver `discard_log.md` BR-DESCARTAR-001. O aggregate `GedcomTree` com `owner_id` substitui o estado global; o re-parse por requisição desaparece (árvore persistida e carregada por identidade). |
| `templates/index.html` + Bootstrap/CDN + `static/graph_path_search.html` (pyvis) | `presentation/` (React + TS) | **removido e substituído** | Ver `discard_log.md` BR-DESCARTAR-004 e BR-DESCARTAR-005. As **duas** tecnologias de visualização (Mermaid + pyvis) colapsam em uma só no cliente — resolve a redundância funcional identificada no diagnóstico. |
| `uploads/` (pasta fixa, nome do cliente) | `adapters/storage/` | **removido e substituído** | Ver `discard_log.md` BR-DESCARTAR-003 e BR-HUMANA-001/RISK-007. Chave gerada pelo servidor, escopo por `owner_id`, nome original como metadado. |
| `app.secret_key` hardcoded | configuração de runtime | **removido** | Ver `discard_log.md` BR-DESCARTAR-007. |
| (vazio) | `tests/parity/` | **novo** | Não existe no legado (`architecture.md` §5 dívida #2: *"Ausência total de testes"*). É a Onda 0 da estratégia confirmada e a materialização da métrica primária do brief. **Justificativa**: sem oráculo, a migração não tem como provar o que promete (RISK-002). |
| (vazio) | `core/shared/constants.py` | **novo** | Extração deliberada: hoje os limiares (92, 90, 86, 100, 0.55/0.25/0.20, 8.0/−4.0, 0.5, 0.33, 150, 20, 40) estão **espalhados** pelo bloco de rota (`analise-dna/design.md` § Decisões). Centralizá-los com referência de linha ao `app.py` é o mecanismo de defesa contra RISK-003 (transcrição incompleta). **Justificativa do agrupamento**: são valores de parâmetro da mesma família de decisões e precisam ser auditados em conjunto contra o oráculo. |
| (vazio) | `ports/`, `application/`, `api/`, `adapters/persistence/` | **novo** | Não existem no legado — são a fronteira modernizada (auth, tenancy, persistência, API) exigida pelo brief e autorizada pelo `paradigm_decision.md`. Sem risco de paridade. |

## Implicações pendentes para próximos passos do Designer

| Etapa do Designer | Implicação | Como honrar |
|---|---|---|
| Bounded contexts (Fase 2) | A topologia decidida define **quantos** bounded contexts existem e onde. Se a opção 3 for escolhida, `core/` é um núcleo único e os bounded contexts da Fase 2 devem refletir **capacidades de negócio**, não subpastas de `core/`. | Não transformar `core/tree`, `core/dna`, `core/pathfinding` em 3 bounded contexts só porque são 3 arquivos — isso reintroduziria a decomposição que o diagnóstico não justificou. |
| Bounded contexts (Fase 2) | `find_ancestral_path` é compartilhado entre `busca-caminho` e `analise-dna` e vira **um** módulo de núcleo. | Modelar o caminho como capacidade de núcleo consumida por **dois** casos de uso (`search_path`, `analyze_dna`), sem duplicar o aggregate nem criar um "serviço de caminho" com estado. |
| `target_architecture` (Fase 2) | Seção obrigatória "Honra ao paradigma escolhido" precisa materializar as 5 implicações do `paradigm_decision.md`. A nº 5 (render server-side some) e a nº 4 (`owner_id` como invariante) são as mais estruturais. | Listar cada implicação com o componente concreto que a realiza. A separação `core/` ↔ `ports/` ↔ `adapters/` é o que torna a implicação 1 (estado global vira dependência injetada) verdadeira por construção. |
| `target_architecture` (Fase 2) | Seção obrigatória "Honra à topologia escolhida" com o esboço final da árvore. | Reproduzir a árvore da opção escolhida, ajustada por qualquer feedback do usuário no gate. |
| `target_domain_model` (Fase 2) | O núcleo é **funções puras**, não classes com estado. Aggregates existem na fronteira de persistência (`GedcomTree` com `owner_id`, `DnaAnalysis`), não no cálculo. | Modelar aggregates com invariantes e comandos onde há **ciclo de vida persistido**; modelar os cálculos como funções. Não criar `MatchScorer` como objeto com estado (era exatamente o risco registrado no `paradigm_decision.md` § Alternativas). |
| `target_domain_model` (Fase 2) | PARADIGMA NÃO É EVENT-DRIVEN. | **Não inventar eventos de domínio.** O paradigma é OO com DI sobre funções puras; o catálogo exige eventos apenas para event-driven/híbrido-eventos. Criar eventos aqui seria cerimônia sem consumidor — o legado é síncrono por requisição e não há mensageria no brief. |
| `target_data_model` (Fase 2) | Nenhum schema legado a preservar — o modelo é **novo**. Duas restrições herdadas mandam: `owner_id` em todo aggregate (RISK-005) e **estratégia de acumulação de cM** explícita (RISK-004). | Documentar por que cada tabela existe (não há origem no legado para a maioria); declarar que a soma de cM é calculada em aplicação e persistida já calculada, para não delegar a `SUM` cego. |
| `target_data_model` (Fase 2) | Requisitos LGPD/GDPR (BR-HUMANA-007, opção 2) entram como estrutura desde já. | Incluir campos de consentimento, marcação de retenção/expurgo e suporte a exclusão de titular no schema, mesmo que os fluxos venham na Onda 5 — retrofitar criptografia e isolamento é caro. |
| `data_migration_plan` (Fase 2) | **Não há dados a migrar.** O artefato é de modelagem nova, não de conversão. | Registrar explicitamente "sem ETL, sem backfill, sem captura de delta" e usar o artefato para o **mapeamento conceitual** e para o plano de carga inicial (que não existe). Não inventar ETL para preencher template. |

## Notas

- **O legado não é tocado.** Este artefato descreve a árvore do **projeto novo** (`analisador/`). Nenhum arquivo em `analisador-genealogico/` é criado, movido, renomeado ou removido — regra absoluta do Reversa.
- **A árvore proposta não é uma meta a ser atingida no dia 1.** As ondas do `cutover_plan.md` entregam progressivamente: Onda 1 cria `core/` + `tests/parity/`; Onda 2 cria `application/`, `api/`, `ports/`; Onda 3 cria `adapters/persistence/`; Onda 4 cria `presentation/`; Onda 5 toca `adapters/persistence/` e `api/` para conformidade. Nada de `adapters/` precisa existir para a Onda 1 ser concluída — e é isso que mantém o risco concentrado e barato.
- **Toda constante transcrita deve trazer referência de linha ao legado** (`# analisador-genealogico/app.py:759`). Este é o mecanismo mais eficaz contra RISK-003 e deve ser exigido na revisão de código da Onda 1.
- **Alerta para o agente de codificação**: o maior risco desta topologia não é criar as pastas — é **não** deixar a fronteira vazar para o núcleo. Se `core/` importar `fastapi`, `sqlalchemy`, `pydantic` ou `flask`, a paridade deixa de ser isolável e a Onda 0 perde valor. Sugestão de verificação automática: um teste que falha se qualquer módulo em `core/` importar algo fora da biblioteca padrão e das dependências de núcleo (`ged4py`, `networkx`, `pandas`, `thefuzz`).

---
*Gerado pelo Reversa-Designer em 2026-09-28.*
