# Cross-check: Escolher arquivo da lista

> Identificador da feature: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Artefatos analisados:
> `_reversa_forward/011-escolher-arquivo-da-lista/requirements.md` ·
> `_reversa_forward/011-escolher-arquivo-da-lista/roadmap.md` ·
> `_reversa_forward/011-escolher-arquivo-da-lista/actions.md`
> Apoio: `data-delta.md`, `investigation.md`, `interfaces/formulario-http.md`, `onboarding.md` e o
> `_reversa_sdd/` (`domain.md`, `architecture.md`, `openapi/index.yaml`, `screens/golden/`).
> Auditoria **estritamente leitora**: nenhum dos artefatos analisados foi alterado por este passo.

## 0. Limite declarado desta auditoria

O auditor e o autor dos três artefatos são **a mesma sessão**. Isso enfraquece justamente o eixo mais
valioso de uma auditoria — o de quem não participou das decisões. O que compensa parcialmente: todas as
verificações abaixo foram feitas por **varredura e medição** (grep sobre os arquivos, existência de
caminho, recálculo do grafo de dependências por instrumento), e não por leitura de memória. Onde a
severidade depende de julgamento, o critério está escrito na própria linha, para você poder discordar.

A severidade segue a **tabela de categorias** do `/reversa-audit`, e não uma escala de impacto própria.
Por isso cada finding `CRITICAL`/`HIGH` traz, abaixo da tabela, o impacto real **e o que já mitiga o
risco** — em três dos casos, existe rede de segurança, e ela está declarada em vez de escondida.

## 1. Resumo

| Severidade | Quantidade |
|------------|-----------:|
| CRITICAL | **0** |
| HIGH | **3** |
| MEDIUM | **2** |
| LOW | **1** |
| **Total** | **6** |

Nenhum `CRITICAL`: não há ciclo de dependência, nenhum contrato externo quebrado e nenhuma regra 🟢 do
legado **removida** ou contradita de forma silenciosa.

## 2. Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | HIGH | Cobertura | `RN-03` — "a aba de árvore lista o que termina em `.ged`, a de DNA o que termina em `.csv`" — é citada **apenas na própria definição**. Nenhuma das 9 decisões do roadmap a cobre, e nenhuma das 32 ações a implementa | `requirements.md:56-57`; **zero ocorrências** em `roadmap.md`, `actions.md`, `data-delta.md`, `interfaces/` e `onboarding.md` |
| A002 | HIGH | Cobertura | `D-08` ("o arquivo que não serve ao uso **não** é filtrado na lista; a recusa continua no uso") não tem ação correspondente: `D-08` aparece **0 vezes** em `actions.md`. O cenário negativo da §7, que é a expressão operacional dessa decisão, também não tem ação | `roadmap.md:49` (e `:126`); `actions.md` — 0 ocorrências; `requirements.md:171-175` |
| A003 | HIGH | Coerência com o legado | `D-03` amplia a pré-condição 🟢 de `domain.md` §4 — de "CSV presente" para "CSV presente **ou** referenciado" — e **nenhum artefato declara `domain.md` §4 como alterado**. O `roadmap.md` §5 declara esse mesmo delta contra o artefato irmão (`openapi/index.yaml:167-179`), mas não contra a tabela de fluxo do domínio | `_reversa_sdd/domain.md:168`; `roadmap.md:44` e §5 (a tabela de delta **não tem linha** para `domain.md`) |
| A004 | MEDIUM | Coerência com o legado | O `requirements.md` chama a dívida 8 de `architecture.md#7` de "propriedade **deliberada**" e de "propriedade **preservada**", e marca a linha como 🟢 CONFIRMADO. O artefato citado diz o oposto: gravidade **🟡 Média** e **"não há decisão de negócio sobre isso"** | `requirements.md:31` e `:66`; `_reversa_sdd/architecture.md:144` |
| A005 | MEDIUM | Consistência | Dois nomes para o mesmo objeto. `requirements.md` usa os **rótulos de tela** ("Buscar Conexão no GEDCOM", "Analisador de DNA"); o plano inteiro usa **"aba de árvore"** e **"aba de DNA"**. Nenhum artefato fixa qual rótulo literal a tela nova tem de manter — e os rótulos de hoje são texto de contrato em `index.html:67` e `:70` | `requirements.md:13-14` vs. `roadmap.md:131`, `actions.md:60`; `src/templates/index.html:67,70` |
| A006 | LOW | Consistência | `RF-01`, `RF-03`, `RN-06`, `RN-07` e `RN-09` não são citadas por ID em `actions.md`. A cobertura **existe** (por `T003`/`T025` no caso de `RN-06`/`RN-07`, por `T013`/`T015` no de `RN-09`, e por `T015`/`T019`/`T020` no de `RF-01`/`RF-03`), mas a rastreabilidade por ID se perde na leitura | `actions.md`; `requirements.md` §4 e §5 |

## 3. Impacto dos findings `HIGH`

### A001 — a partição por extensão não tem dono

`RN-03` é a regra que decide **qual aba recebe qual arquivo**. Sem ela implementada, o resultado não é
ambíguo no papel — mas fica sem responsável: `T019` diz "as duas abas com as listas" e `T015` descreve o
agrupamento pela chave, e **nenhuma das duas diz onde a extensão entra**. O executor precisa tomar essa
decisão sozinho, e ela tem consequência medida: a pasta tem um `.xlsx` (`Familias Sergipanas.xlsx`) que
**não pode aparecer em aba nenhuma**, e um `Famílias_Sergipanas.csv.ged` que precisa aparecer na aba de
árvore apesar do conteúdo ser CSV.

**O que mitiga:** o `onboarding.md:93-94` verifica os números que só fecham se a partição estiver certa
("7 itens para os 8 arquivos `.ged`", "10 itens para os 10 arquivos `.csv`"). A partição **não** pode
quebrar em silêncio — ela quebra a verificação manual. É por isso que a rede existe e a falha é de
atribuição, não de detecção.

**Direção da correção:** uma linha no `roadmap.md` (ou um acréscimo explícito à `T015`, que é a ação da
função pura) resolvem. `RN-03` é regra de negócio, e regra sem decisão é o que a §1.1 do eixo de
cobertura existe para pegar. Sugestão: `/reversa-clarify` não é necessário — é edição direta do
`roadmap.md`/`actions.md`, que este skill não faz.

### A002 — a decisão que proíbe filtrar não tem ação

`D-08` proíbe validar conteúdo na listagem, e a §7 do `requirements.md` fixa o cenário negativo
correspondente: escolher `Famílias_Sergipanas.csv.ged` na aba de árvore tem de responder com a mensagem
de conteúdo não reconhecido. Nenhuma ação do `actions.md` cita `D-08`, e nenhuma escreve esse teste.

**O que mitiga:** o `onboarding.md:134-136` tem o passo manual do caso negativo ("Escolha-o"), e o
comportamento de recusa é **pré-existente** e já tem teste próprio (`tests/test_upload_seguranca.py`,
`tests/test_traducao_de_erros.py`). O que falta é o teste da **combinação nova** — escolher da lista um
item cujo conteúdo não corresponde.

**Direção da correção:** acrescentar o caso à `T005` (o teste da função pura) ou à `T009` (o teste de
rota). Decisão sem ação é o `HIGH` literal da tabela de severidade, e este é o mais barato dos três.

### A003 — a pré-condição 🟢 do domínio perde validade sem declaração

`domain.md` §4 é a tabela de fluxo de decisão do domínio, marcada 🟢, e a linha de `dna_analysis` diz:
**"CSV presente"** + `root_name` resolvível. Depois de `D-03`, um pedido pode trazer o CSV como
**referência** (`matches_csv_filename`) e nenhum arquivo — de modo que a linha deixa de ser literalmente
verdadeira, e passa a ser uma disjunção.

O `roadmap.md` §5 declara a mudança de contrato contra `openapi/index.yaml:167-179` (onde
`required: [action, gedcom_filename, root_name, matches_csv]` também muda), e o §7 manda o detalhe para
`interfaces/formulario-http.md` §2.2. **O que não existe é a linha de `domain.md` na tabela de delta** —
nem uma marca de "regra alterada" para a §4.

**Por que `HIGH` e não `CRITICAL`:** `CRITICAL` é "conflito direto com regra 🟢 do legado", e aqui o
conflito é **de ampliação, não de remoção** — o caminho antigo continua válido, o `interfaces/` preserva
literalmente a mensagem `"Por favor, carregue o arquivo CSV de matches."` (`domain.md:192`) e o delta está
declarado contra o artefato irmão. Nada do legado é quebrado; o risco é de **leitura**: quem
reimplementar lendo só a §4 do `domain.md` constrói um ramo `dna_analysis` que **recusa** o pedido por
referência — ou seja, quebra o `RF-04` inteiro.

**Se você considerar a §4 do `domain.md` um conjunto de regras 🟢 de primeira classe** — e ela é uma
tabela de fluxo de decisão, marcada 🟢 — então leia este finding como `CRITICAL` e resolva antes de
codificar. A diferença é de leitura, e prefiro deixá-la explícita a escolher por você.

**Direção da correção:** acrescentar `_reversa_sdd/domain.md` §4 à tabela de delta do `roadmap.md` §5 com
tipo `regra-alterada`, e registrar a pré-condição nova (`CSV presente **ou** referência presente`). O
adendo da `T032` é onde isso converge na extração, mas o roadmap precisa dizê-lo antes.

## 4. Verificado e aprovado

### Eixo 1 — Cobertura

- **Os 8 requisitos funcionais** (`RF-01`…`RF-08`) aparecem no `roadmap.md`; o §10 cita os oito, e os
  mecanismos têm decisão: `RF-01`/`RF-03` em `D-02`/`D-09`, `RF-04` em `D-03`, `RF-05`/`RF-06` em
  `D-04`, `RF-07` em `D-07`, `RF-08` no §6.
- **9 das 10 regras** `RN-01`…`RN-10` têm dono na implementação: `RN-01`/`RN-02`/`RN-10` em
  `T005`/`T015`/`T016`/`T020`; `RN-04` em `T009`/`T018`/`T021`; `RN-05` em `T017`; `RN-06`/`RN-07` em
  `T003`/`T025` (a guarda de escopo); `RN-08` em `T009`/`T018` (aditividade) e `T024` (paridade); `RN-09`
  em `T013`/`T015` e no passo 10 do `onboarding.md`. A exceção é `RN-03` (`A001`).
- **9 dos 10 cenários Gherkin** da §7 têm ação: 1→`T010`/`T019`; 2→`T005`/`T015`; 3→`T005`/`T015`/`T019`;
  4→`T009`; 5→`T011`; 6→`T008`/`T022`; 7→`T007`/`T017`/`T019`, com a cláusula de divergência em `T029`;
  8→`T005`/`T016`/`T020`; 10→`T003`/`T025`. O 9º é o `A002`.
- **Os 15 itens do "Critério de pronto"** (§10) têm ação, incluindo os dois que não são automatizáveis:
  as contagens de 8 arquivos/7 itens e 10 arquivos/10 itens têm passo de verificação no `onboarding.md`
  (`:93-94`), e o "nada é apagado nem alterado" tem inventário antes (`T003`) e depois (`T025`).
- **8 das 9 decisões** (`D-01`…`D-07` e `D-09`) têm ação que as cita. A exceção é `D-08` (`A002`).

### Eixo 2 — Consistência

- **Nenhum identificador fantasma.** Varredura feita em `roadmap.md` e `actions.md`: todo `RF-xx`,
  `RN-xx` e `D-xx` citado existe no documento de origem, e todo `Txxx` citado em dependência existe.
- **Os contratos de `interfaces/` aparecem no roadmap** (§7, com o arquivo nomeado), e o delta de
  contrato do `openapi/index.yaml:167` está declarado no §5 — inclusive a parte que muda o `required`.
- **Os números batem entre os artefatos:** 19 arquivos = 8 `.ged` + 10 `.csv` + 1 `.xlsx`;
  29.166.183 bytes; árvore 8 arquivos → 7 itens; DNA 10 → 10; três arquivos sem chave. As mesmas
  contagens estão em `requirements.md` (`RF-01`, `RF-03`), `data-delta.md` §3, `roadmap.md` §10 e
  `onboarding.md`.
- **A dívida 8 existe e diz o que a feature supõe que ela diz** ("nada é persistido entre requisições").
  A divergência é de **qualificação** da dívida, não de conteúdo (`A004`).

### Eixo 3 — Coerência com o legado

- `domain.md:139` — forma fechada do nome (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`): é exatamente o que `D-02`
  manda reusar, e `T014` proíbe escrever um segundo padrão. **Coerente, e é a decisão que evita duas
  verdades sobre o contrato de segurança do armazenamento.**
- `domain.md:140` — extensão original preservada, não fixada em `.ged`: é a base factual de `RN-03` e
  `RN-09`. **Coerente.**
- `domain.md:141` — a chave de conteúdo é o identificador que circula entre requisições, porque o
  formulário devolve `gedcom_filename` no POST seguinte: é o mecanismo que `D-03`/`RN-04` **estendem** ao
  CSV. **Coerente** — a feature aplica a regra existente em vez de inventar um segundo mecanismo.
- `domain.md:164` — "Abrir `/` (GET): renderiza **a única tela**, sem estado" 🟢: a feature **não** cria
  rota nova nem estado; muda o que a tela única renderiza. **Sem contradição** — e vale registrar, porque
  era o candidato natural a conflito.
- `domain.md:166` — "qualquer outro `action` exige `gedcom_filename` com forma válida e arquivo
  existente": preservado, e `T018` não toca nessa premissa.
- `domain.md:192` — `"Por favor, carregue o arquivo CSV de matches."`: preservada literalmente por
  `interfaces/formulario-http.md` §2.2 ("a mesma mensagem atual de arquivo ausente"). **Coerente.**
- **Os componentes citados existem**, verificado por caminho: `src/ports/__init__.py`,
  `src/ports/adaptadores.py`, `src/reporting/`, `src/app.py`, `src/templates/index.html`,
  `src/utils/validate.py`, `src/core/`, `src/parsers/`, `src/application/`, `_reversa_sdd/parity/harness.py`,
  `_reversa_sdd/screens/golden/SCR-001-initial-upload.html.txt`, `_reversa_sdd/migration/parity_specs.md`
  e `_reversa_sdd/openapi/index.yaml`. Os três alvos que ainda não existem
  (`src/reporting/lista_de_arquivos.py`, `tests/test_lista_de_arquivos.py`, `tests/test_lista_na_tela.py`)
  são **criações** declaradas pelas ações, não referências quebradas.

### Eixo 4 — Sanidade do `actions.md` (medido por instrumento, não por leitura)

- 32 ações, **IDs únicos**, todas reconhecidas pelo detector de estágio.
- **Nenhuma dependência aponta para ID inexistente.**
- **Nenhum ciclo de dependência** (recálculo com guarda de ciclo).
- **Nenhum arquivo alvo compartilhado entre duas ações `[//]`.**
- **Nenhuma dependência entre duas `[//]` da mesma fase** — a convenção declarada nas notas de execução
  se sustenta na medição.
- **Maior cadeia = 12**, e é exatamente a declarada no resumo
  (`T001 → T005 → T014 → T015 → T016 → T019 → T020 → T021 → T022 → T023 → T031 → T032`).

## 5. O que este relatório não cobre

- **Não avaliou a qualidade das decisões** (`D-01`…`D-09`), só a consistência entre elas e os outros
  artefatos. Se a leitura de `listar(dono)` que a `T012` fixou é a certa, isso continua sendo julgamento
  seu — ela está declarada nas notas de execução do `actions.md` justamente por ser decisão tomada no
  `to-do`, e não no `plan`.
- **Não mediu o comportamento do sistema**: paridade, suíte e inventário são medições da Fase 1 e da
  Fase 5 do `actions.md`, e nenhuma delas foi executada aqui.
- **Não auditou o `onboarding.md`** quanto a executabilidade passo a passo — ele foi lido apenas como
  evidência de cobertura.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-audit` | reversa |
