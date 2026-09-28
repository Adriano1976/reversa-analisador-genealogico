---
schemaVersion: 1
generatedAt: 2026-09-28T02:45:48Z
reversa:
  version: "1.2.58"
kind: paradigm_decision
producedBy: paradigm_advisor
hash: "sha256:1500a7fdfd7835a58d57a09d52eae03d30acefbfec7e724adb68cec31e2c818f"
---

# Paradigm Decision

> Decisão consciente sobre como tratar a mudança (ou ausência) de paradigma entre o legado e a stack alvo.
> Este artefato é leitura obrigatória primeiro para qualquer agente posterior e para o agente de codificação.

## Paradigma do legado detectado

- **Paradigma principal**: procedural
- **Confiança**: 🟢 CONFIRMADO
- **Evidências**:
  - `architecture.md` §5 (Dívidas Técnicas, #5): *"Código monolítico (app.py ~887 linhas) com rotas + lógica acopladas — Responsabilidades de parsing, matching e renderização num único módulo."* 🟢
  - `code-analysis.md` §3: funções **top-level** sem classes de domínio — `load_gedcom_and_build_graph(file_path)`, `build_graph_from_parser(people_dict, parser)`, `find_ancestral_path(start_id, end_id, max_depth=20)`, `find_indirect_path(start_id, end_id, max_hops=40)`. Assinaturas recebem e devolvem estruturas cruas (`dict`, `list[str]`, tuplas). 🟢
  - `architecture.md` §1: *"todo o estado é mantido em memória (dicionários e grafo `networkx`) durante a sessão"* — estado global mutável compartilhado entre requisições, sem fronteira de transação. 🟢
  - `code-analysis.md` §5 e `architecture.md` §3 (ERD): entidades representadas como **dicionários** — `Person.sub_records: List`, `DnaMatchRecord._group_key`, `cM`, `matched_name`. Não há aggregate com invariantes; a "entidade" é a forma do dict. 🟢
  - `architecture.md` §1: *"análise sob demanda: a cada requisição `POST`, o GEDCOM é re-parsado e o grafo reconstruído"* — fluxo linear dirigido por requisição, sem camada de aplicação. 🟢
  - `code-analysis.md` §3 (`process_dna_action`): o bloco de rota executa o pipeline inteiro — carrega GEDCOM, lê CSV, identifica colunas, `groupby.agg`, busca fuzzy, cálculo de caminho e renderiza o template. **Controller que contém o domínio** — assinatura clássica do procedural. 🟢
  - `domain.md` §5 e `architecture.md` §2: ausência de RBAC/permissões e de máquinas de estado — nenhuma entidade de domínio com ciclo de vida próprio. 🟢
- **Variações observadas** (evidência de OO menor, insuficiente para classificar como híbrido):
  - `inventory.md` §3 e `code-analysis.md` §1: uso de `pandas.DataFrame` e `networkx.Graph`/`DiGraph` como containers ricos e `thefuzz` como biblioteca. 🟢
  - **Por que não é híbrido**: esses tipos são **estruturas de dados e utilitários de biblioteca**, não um paradigma de modelagem adotado. Não há classes próprias, herança, polimorfismo, interfaces ou injeção. O modelo mental organizador do sistema é "funções que operam sobre estado global" — procedural.

## Stack alvo declarada

- Linguagem: Python 3.12+ (do `migration_brief.md` § Stack alvo)
- Framework: FastAPI
- Banco: PostgreSQL
- Front-end: React + TypeScript (SPA)
- Infra: não definida no brief; requisito implícito de criptografia em repouso e em trânsito (dados genéticos / LGPD)
- Mensageria: não definida — nenhuma necessária identificada (processamento síncrono por requisição no legado)

## Paradigma natural inferido

- **Paradigma**: OO com DI
- **Justificativa**: o catálogo mapeia *"Python moderno (FastAPI, Django 5) → OO com DI ou procedural rico — escolha depende do framework"*. FastAPI inclina a balança para **OO com DI** por três mecanismos estruturais: (1) `Depends()` é injeção de dependência de primeira classe, não um padrão improvisado; (2) `pydantic.BaseModel` fornece aggregates com invariantes validadas na fronteira; (3) o par `APIRouter` + camada de serviços substitui o controller anêmico, deixando a rota responsável apenas por traduzir HTTP ↔ domínio.
- **Alternativas viáveis**:
  - **Procedural rico** (funções puras em módulos, sem classes): é a leitura mais próxima do legado e reduz o custo de tradução. Viável, mas desperdiça o sistema de DI do framework e deixa o escopo por tenant (requisito de isolamento multi-tenant) sem um lugar natural para viver — viraria parâmetro repassado manualmente por toda a cadeia de chamadas.
  - **Orientação a objetos completa com aggregates ricos** (transformacional): viável, mas exigiria reificar o matching viral e a busca de caminho como objetos com estado, o que é pior para testabilidade e cria superfície de divergência sobre algoritmos congelados.

## Gap identificado

- **Severidade**: alto
- **Par de referência** (catálogo): `procedural → OO com DI` — *"dados como dict → aggregates; invariantes ficam dentro de aggregates; lógica deixa de viver em controllers; dependências via interfaces"*.
- **Implicações concretas**:
  - **Implicação 1 — O estado global vira dependência injetada, e o re-parse por requisição desaparece.**
    No legado, `people` e `families` são dicionários globais e o grafo `networkx` é reconstruído a cada requisição (`architecture.md` §1 e dívida #4: *"Estado em memória + re-parse a cada requisição — Ineficiente; recálculo integral a cada POST"*). A reconstrução atual (`reconstructed/upload.py`) precisou mutar esses globais **in-place** (`clear` + `update`) só para que `path_search` e `dna_analysis` enxergassem a carga — prova direta de que o acoplamento é por variável global, não por contrato. No alvo, a árvore passa a ser um aggregate (`GedcomTree`: pessoas + famílias + grafo) construído no upload e carregado por repositório, injetado no serviço. Isso não é preferência de estilo: em SaaS, dois uploads concorrentes de contas diferentes escrevem no mesmo global hoje.
  - **Implicação 2 — Tratamento de erro deixa de ser flash/template e vira exceção de domínio + status HTTP.**
    No legado, falhas de entrada (GEDCOM ilegível, `root_name` não encontrado — `domain.md` §3: *"Exige GEDCOM carregado + CSV + `root_name` encontrado no GEDCOM"*) e o `try/except` com fallback de encoding Latin-1 (`code-analysis.md` §3, passo 2) terminam em alerta renderizado na `index.html`. No alvo, viram exceções tipadas (`RootPersonNotFound`, `UnsupportedGedcom`, `DnaCsvMissingColumns`) mapeadas por exception handler para `404`/`422` com payload estruturado consumido pelo React. O fallback Latin-1, porém, é **comportamento de negócio congelado** e deve sobreviver como estratégia explícita de codec, não como `try/except` incidental.
  - **Implicação 3 — Lógica embutida na rota migra para serviços de domínio, com os limiares virando constantes nomeadas.**
    Hoje o pipeline vive dentro de `process_dna_action`: mistura `pandas.groupby.agg` para agregar cM, `thefuzz` para o score e **literais mágicos espalhados** — limiares A/B/C/D (92, 90, 86, 100), pesos do score (`0.55 × token_sort + 0.25 × partial + 0.20 × given`), `InterBonus` (`8.0 × intersecção − 4.0 × sobrenomes comuns`), relaxamento de Jaccard (0.5 → 0.33), `max_depth=20`, `max_hops=40`. No alvo isso vira `MatchScorer` / `RelationshipPredictor` com constantes nomeadas. ⚠️ **Restrição dura**: nomear as constantes **não pode alterar nenhum valor**. Este é o risco #1 do brief (fidelidade do matching) e o ponto onde um refactor "de limpeza" muda resultados silenciosamente.
  - **Implicação 4 — "Dono do dado" deixa de ser inexistente e vira invariante do aggregate, não filtro de rota.**
    `domain.md` §4 registra como lacuna: *"Sem autenticação/autorização: sistema não possui RBAC — qualquer acesso via web possui todas funcionalidades"*, e `architecture.md` §3 mostra `DNA_MATCH` como *"entidade derivada do CSV agregado em memória — s/ persistência"*. Não existe noção de proprietário em lugar nenhum. No alvo, `owner_id` pertence ao aggregate (árvore, upload, análise) e o repositório é **sempre** escopado por tenant. Tratar isolamento como um `WHERE user_id = ?` adicionado depois é precisamente o modo como vazamento de dado genético acontece — e dado genético é irrevogável.
  - **Implicação 5 (derivada da stack) — A renderização server-side some, e com ela o transporte de estado pela `index.html`.**
    `inventory.md` §3 descreve a UI como `templates/index.html` (Jinja2 + Bootstrap 5) e `static/graph_path_search.html` (pyvis), com os resultados **renderizados no servidor** e ordenados por cM decrescente (`code-analysis.md` §3, passo 7). Com React + FastAPI, esse canal deixa de existir: os resultados passam a ser payload JSON e a visualização pyvis precisa de equivalente no cliente. Note que a visualização de grafo está **dentro** do escopo declarado (a entrevista recusou excluí-la).

## Opções apresentadas ao usuário

1. **Adotar paradigma natural da stack** (transformacional)
   - Consequências: núcleo reescrito como serviços/aggregates com DI completo. Ganha isolamento por tenant natural e testabilidade sem manipulação de global. Custo: os módulos da reconstrução (`reconstructed/domain.py`, `upload.py`, `path_search.py`, `dna_analysis.py` — 47 testes) passam a ser **referência de comportamento**, não código reaproveitado, exigindo `parity_tests/` desde o primeiro dia. Paga reescrita sobre algoritmos declarados congelados.
2. **Forçar paradigma similar ao legado** (conservador)
   - Consequências: módulos de funções puras + um `GraphStore` global protegido por lock. Migração mais barata e paridade quase automática. Mas o estado global compartilhado é **incompatível com multiusuário** — empurra o isolamento entre contas para depois e cria dívida de segurança sobre dado sensível. O re-parse por requisição permaneceria.
3. **Híbrido** (equilibrado)
   - Consequências: DI, serviços e repositórios nas **bordas** (API, persistência, auth, escopo por tenant); **funções puras preservadas** no núcleo de cálculo (score de matching, regras A/B/C/D, caminho ancestral, tabela de cM), onde funções puras já são a escolha natural e onde a paridade é a métrica #1.

## Decisão do usuário

- **Escolha**: 3 — Híbrido (equilibrado)
- **Justificativa do usuário**: selecionou a opção 3 na apresentação das três opções, sem texto adicional. Justificativa reconstruída pelo agente a partir das restrições que o próprio usuário declarou no `migration_brief.md`, sujeita a correção:
  - O brief declara **matching congelado** como restrição técnica inegociável → o núcleo algorítmico não deve ser reescrito em objetos com estado; funções puras preservam paridade e testabilidade.
  - O brief declara **auth/isolamento por tenant/persistência dentro do escopo** desta migração → a borda *precisa* de DI, repositórios e aggregates com `owner_id`, porque não há como isolar contas sobre estado global.
  - O brief declara **dados genéticos sensíveis (LGPD/GDPR)** → isolamento deve ser invariante de domínio, não filtro de rota aplicado tardiamente.
  - O brief declara **sem prazo, qualidade sobre velocidade** → não há pressão para escolher o caminho mais barato (opção 2) nem para maximizar modernização (opção 1).
  - A opção 3 é a única que trata o multiusuário como problema de arquitetura **sem** trade-off contra a paridade do matching, que é o risco #1 declarado.
- **Decidido em**: 2026-09-28T02:45:48Z

## Apetite derivado

- `derived_appetite`: **balanced**

> Consumido pelo Curator (o que migrar/descartar), pelo Strategist (fatia de ondas) e pelo Designer (quanto de reescrita é legítima). `balanced` significa: **modernizar a fronteira, preservar o núcleo**. Não autoriza reescrita de algoritmos congelados; não tolera perpetuação de estado global.

## Implicações pendentes para próximos agentes

| Agente | Implicação | Como honrar |
|---|---|---|
| **Curator** | O núcleo de cálculo (score fuzzy, regras A/B/C/D, tabela de cM, limite `max_depth=20` / `max_hops=40`) é `balanced` → **MIGRAR com fidelidade**, nunca reinterpretar. | Marcar cada regra dessas como MIGRAR; só classificar como DECISÃO HUMANA o que for genuinamente indefinido, não o que já está congelado pelo brief. |
| **Curator** | As 4 respostas de `questions.md` (registradas em `reconstruction-plan.md` § Alertas) **não são lacunas abertas** — são comportamento congelado. | Classificá-las como MIGRAR, conforme `ambiguity_log.md` AMB-004. Não reabrir como DECISÃO HUMANA. |
| **Curator** | Onde há defeito informal do legado (upload sem validação de extensão/tamanho, colisão de nomes em `uploads/` sobrescreve, homônimos resolvidos pelo 1º ID, caminho por pais ignora famílias adotivas). | Decidir explicitamente por item: preservar por paridade **ou** corrigir por ser fronteira (validação de upload é fronteira → corrigir). Não deixar ambíguo. |
| **Strategist** | A fronteira (auth, tenant, persistência, API, SPA) é reescrita; o núcleo é portado. São **dois riscos e dois ritmos diferentes**. | Fatiar em ondas que separem "portar núcleo com paridade" de "construir fronteira multiusuário", para que a paridade seja provada antes de a fronteira crescer. |
| **Strategist** | `ambiguity_log.md` AMB-003: escopo integral + multiusuário + conformidade, sem prazo/orçamento e com decisor único. | Endereçar com ondas entregáveis e critério de paridade por onda; nunca big bang. Registrar no `risk_register.md` o risco de execução. |
| **Designer** (Fase 2) | O núcleo de funções puras + borda com DI é a **forma arquitetural decidida**, não uma sugestão. | Modelar o núcleo como funções puras de domínio (sem dependência de I/O) e a borda com repositórios/ serviços injetados. Não introduzir aggregates com estado no núcleo de cálculo. |
| **Designer** (Fase 2) | O estado global e a mutação in-place da reconstrução (`clear` + `update`) **não devem ser transportados** — mas o comportamento observável sim. | Modelar `GedcomTree`/upload/análise como aggregates com `owner_id`; documentar a mudança de mecanismo como intencional e coberta por paridade. |
| **Designer** (Fase 2) | Restrição LGPD/GDPR e visualização de grafo (pyvis) estão no escopo. | Incluir requisitos de consentimento/retenção/expurgo/criptografia no modelo de dados e um equivalente client-side do grafo na arquitetura alvo. |
| **Inspector** | Paridade é a métrica #1, mas o alvo **muda mecanismos de propósito** (persistência, tenancy, sem render server-side). | Definir paridade em termos de **comportamento observável do domínio** (matches, scores, caminhos, relações por cM), não de estrutura de código ou de HTML. |
| **Inspector** | Os 47 testes de `tests/` testam a **reconstrução**, não o legado. | Decidir explicitamente o que é oráculo válido; não elevar a suíte existente a oráculo sem verificar que ela reflete o comportamento do legado. |

## Notas

- **Fronteira de decisão (regra operacional para todos os agentes posteriores)**: se o artefato é *algoritmo de negócio* (score, matching, regras A/B/C/D, caminho, cM) → núcleo, **função pura, fidelidade absoluta**. Se o artefato é *plumbing* (HTTP, persistência, auth, tenancy, fila, config, observabilidade) → borda, **DI/serviços/repositórios, modernização livre**. Ambiguidade sobre qual lado um item cai deve subir para `ambiguity_log.md`, não ser resolvida silenciosamente.
- **O que `balanced` explicitamente NÃO autoriza**: (a) renomear/reorganizar o matching de um modo que altere resultados; (b) manter variável global de estado como mecanismo de compartilhamento; (c) deixar `owner_id` como filtro de query em vez de invariante.
- **O que `balanced` explicitamente autoriza**: (a) descartar a estrutura de `app.py` inteiramente; (b) não reaproveitar `reconstructed/*.py` como código, usando-os como referência de comportamento; (c) substituir renderização server-side por API + SPA; (d) introduzir persistência onde o legado tinha memória volátil.
- **Dívidas técnicas do legado que a migração deve resolver por serem de fronteira** (`architecture.md` §5): #1 dependências sem versão fixada (pins obrigatórios), #3 ausência de CI/CD e Docker, #6 `secret_key` hardcoded (`'f@milyse@rch_dna_edition_v16'`) — em produto multiusuário isso é crítico, #4 estado em memória + re-parse, #5 monólito acoplado.
- **Dívida #7 (correções de mojibake heurísticas) é núcleo**, não fronteira: `strip_bad_utf`/`demojibake` afetam o resultado do matching e devem ser portados com fidelidade, mesmo sendo heurísticos e incompletos.
