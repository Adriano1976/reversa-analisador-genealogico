---
schemaVersion: 1
generatedAt: 2026-09-28T02:52:40Z
reversa:
  version: "1.2.58"
kind: discard_log
producedBy: curator
hash: "sha256:0a5729fac66499ab4610ba1ace51c50c819b8ed95192ca92e779e5f00ebe5cf2"
---

# Discard Log

> Registro completo do que foi descartado da migração e por quê. Cada item tem rastreabilidade para a origem no legado.

## Itens descartados

### BR-DESCARTAR-001
- **Origem**: `_reversa_sdd/upload-gedcom/design.md` § "Estado Interno" e § "Decisões de Design" (`app.py:20-23`, `app.py:582`); `_reversa_sdd/architecture.md` §1 e §5 (dívida #4)
- **Descrição**: Estado global mutável em memória (`people`, `families`, `graph`, `child_to_family`) compartilhado por todo o processo e **sobrescrito a cada parse**, com re-parse do GEDCOM a cada requisição POST.
- **Justificativa**: É simultaneamente (a) mecanismo do paradigma procedural — singleton implícito em variável de módulo — e (b) incompatível com o `migration_brief.md`, que exige isolamento de dados por usuário e persistência. Dois usuários no mesmo processo escrevem no mesmo global; em servidor multi-worker, duas requisições concorrentes corrompem a análise uma da outra (`upload-gedcom/design.md` § Riscos 🔴).
- **Vinculado a paradigma**: **sim**
  - Legado: procedural, com estado compartilhado por variável de módulo e identificação implícita de "a árvore atual".
  - Como o paradigma alvo absorve: em OO com DI, a árvore é um **aggregate** (`GedcomTree`: pessoas + famílias + grafo + índice filho→família) com `owner_id`, construído no upload e carregado por **repositório escopado por tenant**. Não existe "a árvore atual": existe *a árvore de fulano*. O re-parse por requisição desaparece porque a árvore é persistida uma vez e carregada por identidade — não reconstruída a cada POST.
- **Reposição no sistema novo**: substituído por aggregate `GedcomTree` persistido em PostgreSQL + repositório escopado por `owner_id`. Nota de implementação: o `networkx.Graph` pode sobreviver como detalhe interno do aggregate (não é mecanismo de paradigma, é estrutura de dados), desde que o carregamento/serialização seja explícito e o objeto nunca seja global.
- **Risco de descartar**: **baixo** para paridade de negócio (nenhum cálculo muda), **crítico se não descartado** (vazamento de dados genéticos entre contas + corrupção de análise concorrente). ⚠️ Cuidado de implementação: a reconstrução atual dependia de mutação in-place (`clear` + `update`) das globais para que os módulos se enxergassem — esse acoplamento **não** deve ser transportado.

### BR-DESCARTAR-002
- **Origem**: `_reversa_sdd/analise-dna/design.md` § "Estado Interno" e § passo 8 (`app.py:617-635`)
- **Descrição**: Agregação de segmentos de DNA em memória por requisição (`dna_matches_df` como `pandas.DataFrame` local, `groupby.agg` + `merge`), sem persistência de resultados entre requisições.
- **Justificativa**: `architecture.md` §5 (dívida #8) registra *"Colunas calculadas em memória, sem persistência de resultados"*. O brief inclui explicitamente **persistência de análises e resultados** no escopo. Uma análise de DNA cara recalculada integralmente a cada POST é inaceitável quando o resultado precisa sobreviver ao restart e ser consultável depois.
- **Vinculado a paradigma**: **sim**
  - Legado: procedural — o DataFrame é o container universal de domínio e vive e morre com a requisição.
  - Como o paradigma alvo absorve: o resultado da análise vira um aggregate persistido (`DnaAnalysis` com matches aceitos, `skipped_matches` com motivo tipado, relação prevista e caminho). A agregação em si (BR-MIGRAR-016) continua existindo como **função pura** — o que morre é o *container* DataFrame como modelo de dados e o *escopo* por requisição.
- **Reposição no sistema novo**: substituído por entidades persistidas + repositório. ⚠️ **Alerta de paridade**: a soma de cM deve preservar a ordem de acumulação (ponto flutuante não é associativo); agregar com `SUM` do PostgreSQL pode diferir no último dígito do `groupby.agg` do pandas e cruzar um limite de faixa de cM. Ver BR-MIGRAR-016.
- **Risco de descartar**: **médio** — a persistência é o objetivo, mas o caminho de agregação precisa ser reimplementado sem alterar aritmética.

### BR-DESCARTAR-003
- **Origem**: `_reversa_sdd/upload-gedcom/design.md` § "Decisões de Design" (`app.py:569`); `architecture.md` §1 e §5 (dívidas #6, #7)
- **Descrição**: Salvar o arquivo enviado em `uploads/` **com o nome original fornecido pelo cliente**, em pasta fixa criada no boot, sem escopo por usuário.
- **Justificativa**: Incompatível com o brief em três frentes. (1) **Isolamento**: pasta única compartilhada significa que o arquivo de um usuário é sobrescrevível pelo de outro (colisão de nome) e legível por ambos. (2) **Multiusuário**: não há como associar um arquivo a um dono. (3) **Regulatório**: `confidence-report.md` registra 🔴 *"Sem validação de extensão/tamanho"* e `analise-dna/requirements.md` § Riscos 🔴 *"Sem sanitização de nomes de arquivos recebidos"* — nomes controlados pelo cliente em produção pública são vetor de path traversal e de abuso.
- **Vinculado a paradigma**: **sim**
  - Legado: procedural — o sistema de arquivos local é simultaneamente armazenamento e estado de sessão; o "nome do arquivo" é a chave de referência (`gedcom_filename`).
  - Como o paradigma alvo absorve: armazenamento de objeto (ou volume por tenant) com **chave gerada pelo servidor** (UUID) e caminho derivado de `owner_id`. O nome original do cliente passa a ser **metadado** (para exibição), nunca identificador nem parte do caminho.
- **Reposição no sistema novo**: substituído por object storage escopado por usuário + metadados em banco. A referência `gedcom_filename` do legado vira referência por ID de árvore.
- **Risco de descartar**: **médio** — é plumbing e o parsing não muda, mas a **semântica de referência** muda (`gedcom_filename` → `tree_id`), o que exige interpretar corretamente BR-MIGRAR-033 no novo contexto. Ver BR-HUMANA-001 e BR-HUMANA-004.

### BR-DESCARTAR-004
- **Origem**: `_reversa_sdd/{upload-gedcom,busca-caminho,analise-dna}/design.md` § Interface (todas: `status 200 (sempre; sem redirects)`); `architecture.md` §1
- **Descrição**: Transporte de resultados e erros por **renderização server-side** do `index.html` (Jinja2 + Bootstrap) com variáveis de contexto (`dna_results`, `skipped_matches`, `path_result`, `message`), sempre com **HTTP 200** — inclusive em erro.
- **Justificativa**: O brief declara **React + TypeScript** como front-end e API desacoplada. Renderização server-side é o mecanismo pelo qual o paradigma procedural entrega resultado; com SPA ele deixa de existir. O `200 (sempre)` é especialmente incompatível: um cliente React precisa distinguir erro de sucesso por status/código, não por presença de uma chave de template.
- **Vinculado a paradigma**: **sim**
  - Legado: procedural — o controller calcula, escolhe o template e injeta strings de mensagem; o HTML é o contrato.
  - Como o paradigma alvo absorve: o contrato passa a ser **payload tipado** (Pydantic) + **status HTTP semântico** (`200`/`404`/`422`) + erros como exceções de domínio mapeadas por exception handler. A informação transmitida é a **mesma**; o canal é que muda.
- **Reposição no sistema novo**: substituído por endpoints REST/JSON consumidos pelo SPA. ⚠️ As **mensagens** (BR-MIGRAR-028) e os **critérios de aceitação Gherkin** das três units devem sobreviver como conteúdo de domínio/i18n — descartar o transporte não autoriza descartar o texto nem a distinção entre os casos de erro.
- **Risco de descartar**: **baixo** para o domínio (nenhuma regra se perde), **alto para a UX** se as mensagens não forem preservadas — os critérios de aceitação das três units são escritos em termos dessas strings.

### BR-DESCARTAR-005
- **Origem**: `_reversa_sdd/busca-caminho/design.md` § Interface (`generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge`); `_reversa_sdd/analise-dna/design.md` § Interface e § passo 12; `inventory.md` §3 (`static/graph_path_search.html`, pyvis)
- **Descrição**: Geração de diagramas **Mermaid no servidor** como string, e página **pyvis** estática, injetadas no template para visualização do grafo de parentesco.
- **Justificativa**: Com React no cliente, gerar sintaxe Mermaid no servidor mantém acoplamento a uma tecnologia de diagramação específica e impede a UI de ser interativa — o oposto do objetivo do SPA. `pyvis` (que gera uma página HTML autônoma) é ainda menos compatível com uma SPA.
- **Vinculado a paradigma**: **sim**
  - Legado: procedural/server-side — o servidor é responsável por montar a representação visual final.
  - Como o paradigma alvo absorve: o servidor passa a emitir **estrutura de domínio** (ramos do caminho, MRCA, par de cônjuges que ancora a afinidade, tipo de conexão) e o cliente decide como desenhar. A tecnologia de renderização vira escolha de front-end.
- **Reposição no sistema novo**: substituído por payload estruturado do caminho + biblioteca de grafo no cliente. ⚠️ **CRÍTICO — não descartar as regras junto com a tecnologia**: `split_path_by_marriage` (divide o caminho no **1º par de cônjuges adjacentes`), `are_spouses` (verifica casamento) e as âncoras de casamento codificam **como o parentesco é decomposto** — são regras de negócio puras e estão cobertas por BR-HUMANA-008 — **decidida** em 2026-09-28T02:56:00Z (opção 1: preservar a lógica, redesenhar a apresentação). O `decision-rubric.md` é explícito: *"O que NUNCA descartar por paradigma: regras de negócio puras (cálculos, condições, derivações)."* Portanto essas funções **migram** como funções puras; apenas a emissão de Mermaid/pyvis no servidor é descartada.
- **Risco de descartar**: **médio** — risco real de perda silenciosa das regras de decomposição do caminho se a implementação tratar "grafo" inteiramente como preocupação de UI. Sinalizado para o Designer e para o Inspector.

### BR-DESCARTAR-006
- **Origem**: `_reversa_sdd/questions.md` Pergunta 3 (resposta humana); `_reversa_sdd/upload-gedcom/requirements.md` § Requisitos Não Funcionais (🔴) e § MoSCoW ("Validação de extensão/tamanho | Could | Não implementado no legado 🔴"); `_reversa_sdd/analise-dna/requirements.md` § Riscos (🔴)
- **Descrição**: Aceitação explícita da ausência de política de upload — sem validação de extensão, sem limite de tamanho, sobrescrita de arquivos de mesmo nome, sem tratamento de concorrência. A resposta registrada em `questions.md` é: *"Limitação aceita para uso local — manter sem política de segurança (documenta-se como limitação)."*
- **Justificativa**: A resposta foi dada no contexto de **uso local single-user**, explicitamente ("para uso local"). O `migration_brief.md` **muda esse contexto**: produto multiusuário para **usuários externos** com **dados genéticos sensíveis** sob **LGPD/GDPR**. Manter a limitação significaria publicar um endpoint público sem validação de upload — a decisão anterior não cobre este cenário, e uma decisão de segurança não deve ser transportada silenciosamente para um contexto de risco diferente.
- **Vinculado a paradigma**: **não** — este item não é mecanismo de paradigma. É uma decisão de escopo/segurança cujo contexto mudou.
- **Reposição no sistema novo**: **DESCARTE EFETIVADO** por decisão do usuário em 2026-09-28T02:56:00Z (ver `target_business_rules.md` **BR-HUMANA-001**, opção 3 — meio-termo). A limitação histórica deixa de ser preservada: passa a haver validação de extensão/MIME e tamanho máximo na fronteira, nomes de arquivo gerados pelo servidor e escopo por usuário. O **parsing do conteúdo permanece intocado** — nenhum GEDCOM válido passa a ser rejeitado.
- **Risco de descartar**: **médio** — descartar melhora a segurança e não altera paridade de parsing, mas contradiz uma resposta humana anterior dada no contexto de "uso local". Por isso **não** foi descartado unilateralmente pelo Curator: foi **reaberto** e o usuário decidiu. A contradição está resolvida e registrada; não há pendência residual.

### BR-DESCARTAR-007
- **Origem**: `_reversa_sdd/architecture.md` §5 (Dívidas Técnicas, #6); `_reversa_sdd/upload-gedcom/requirements.md` § Requisitos Não Funcionais (🟡); `_reversa_sdd/analise-dna/requirements.md` § Requisitos Não Funcionais (🟡)
- **Descrição**: `app.secret_key = 'f@milyse@rch_dna_edition_v16'` declarado **hardcoded** no código-fonte, com a versão do artefato ("v16") embutida no próprio segredo.
- **Justificativa**: A chave de sessão é **segredo de configuração**, não regra de negócio — não descreve comportamento de domínio, não tem valor de paridade. No legado o risco é nulo (sessão local, single-user, sem autenticação). No alvo o risco é crítico e assimétrico: a chave assina a sessão autenticada que dá acesso a **dados genéticos**, e um segredo público conhecido permite **forjar sessão de qualquer usuário**. Além disso, embutir a versão no segredo impede rotação sem alterar código.
- **Vinculado a paradigma**: **não** — é configuração/segurança, não mecanismo de paradigma.
- **Reposição no sistema novo**: substituído por segredo injetado em runtime (variável de ambiente / secret manager), com rotação suportada. **Nenhum comportamento de domínio muda.**
- **Risco de descartar**: **nulo para paridade, alto se preservado**. Não há trade-off a ponderar: manter um segredo público num produto multiusuário com dado sensível é uma falha de segurança, não uma escolha de arquitetura.
- **Decisão**: descarte **efetivado** por decisão do usuário em 2026-09-28T02:56:00Z (ver `target_business_rules.md` **BR-HUMANA-002**, opção 1).

## Itens descartados por mudança de paradigma (subseção dedicada)

> Lista apenas dos itens cujo `Vinculado a paradigma = sim`. Auditoria explícita para o agente de codificação.

| ID | Origem | Paradigma legado | Substituto no paradigma alvo |
|---|---|---|---|
| BR-DESCARTAR-001 | `upload-gedcom/design.md` § Estado Interno; `app.py:20-23,582` | Estado global mutável em módulo + re-parse por requisição | Aggregate `GedcomTree` com `owner_id`, persistido, carregado por repositório escopado por tenant |
| BR-DESCARTAR-002 | `analise-dna/design.md` § Estado Interno; `app.py:617-635` | `DataFrame` local à requisição como container de domínio, sem persistência | Aggregate `DnaAnalysis` persistido + repositório; agregação preservada como função pura |
| BR-DESCARTAR-003 | `upload-gedcom/design.md` § Decisões; `app.py:569` | Sistema de arquivos local como estado de sessão; nome do cliente como chave | Object storage escopado por `owner_id` com chave gerada pelo servidor; nome original vira metadado |
| BR-DESCARTAR-004 | `{3 units}/design.md` § Interface | Render server-side de `index.html`, `status 200` sempre | Endpoints REST/JSON + status HTTP semântico + exceções de domínio mapeadas; mensagens preservadas como i18n |
| BR-DESCARTAR-005 | `busca-caminho/design.md`, `analise-dna/design.md` § Interface | Geração de Mermaid/pyvis no servidor como representação final | Payload estruturado do caminho (ramos, MRCA, par de cônjuges) + render no cliente. **Regras de decomposição migram** (`split_path_by_marriage`, `are_spouses`) — ver BR-HUMANA-008 |

## Notas

- **5 dos 7 itens são vinculados a paradigma** e todos os 5 são de *plumbing* (estado, persistência, armazenamento, transporte, apresentação). Nenhum cálculo, condição ou derivação de negócio foi perdido. Isso é coerente com `derived_appetite = balanced`: a fronteira é modernizada, o núcleo é preservado.
- **BR-DESCARTAR-006 foi a exceção e a mais delicada**: não é paradigma, é uma resposta humana anterior que o novo contexto invalida. Foi deliberadamente **encaminhado** como decisão humana em vez de descartado, porque descartar em silêncio uma decisão explícita do usuário — ainda que superada — seria agir sem aval. O Curator não descarta decisões humanas; ele as reabre. **Desfecho**: o usuário decidiu descartar (opção 3, meio-termo) em 2026-09-28T02:56:00Z.
- **BR-DESCARTAR-007 é descarte sem trade-off**: o `secret_key` hardcoded não descreve comportamento de domínio. Preservá-lo não seria fidelidade, seria publicar um segredo de sessão que dá acesso a dados genéticos.
- **Risco transversal a vigiar pelo Inspector**: BR-DESCARTAR-005 é o item com maior chance de perda silenciosa de regra de negócio, porque a fronteira entre "tecnologia de desenho" (descartável) e "regra de decomposição do parentesco" (migrável) é sutil. Os `parity_tests/` devem cobrir explicitamente a decomposição do caminho em conexões indiretas por casamento.
- **Nada aqui foi descartado por conveniência de reescrita.** Cada item tem justificativa checável contra uma restrição explícita do `migration_brief.md` ou contra um mecanismo de paradigma nomeado no `paradigm_decision.md`.

---
*Gerado pelo Reversa-Curator em 2026-09-28.*
