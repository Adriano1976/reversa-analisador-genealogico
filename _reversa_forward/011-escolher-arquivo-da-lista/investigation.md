# Investigation: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/011-escolher-arquivo-da-lista/requirements.md`

## 1. O que foi investigado, e por quê

Esta feature muda **a tela** e o **contrato de formulário** ao mesmo tempo, e as duas coisas têm
instrumentos que medem o comportamento atual. Antes de planejar, foi preciso responder a quatro
perguntas: (a) onde a listagem pode morar sem desfazer a fronteira construída pelas features 006/007;
(b) a mudança de template **quebra a paridade de 100 %**?; (c) o golden da tela inicial **deixa mesmo de
valer**?; (d) o que a lista vai mostrar, exatamente, com a pasta de hoje.

As respostas a (b) e (c) contrariaram o que o `requirements.md` supunha, e estão registradas como
`D-05` e `D-06` no roadmap.

## 2. Onde a listagem pode morar

A fronteira foi estabelecida pela feature 006 e está no código, não só no documento:

- `_arvore_do_formulario()` (`src/app.py:161-189`) **não** resolve caminho: ela entrega a referência ao
  `CarregadorDeArvoresGedcom`, que resolve e parseia;
- o comentário da própria função registra que, até o `T016` da 006, ela resolvia o caminho por
  `_resolver_caminho_armazenado` e chamava o carregador direto — "as duas coisas que a `RF-01` tira do
  adaptador de entrada";
- `src/ports/__init__.py` tem as portas, e `src/ports/adaptadores.py` tem o `ArmazenamentoEmDisco`.

Conclusão: fazer `os.listdir` na rota desfaria uma fronteira **medida e comentada**, e a listagem não
seria testável sem pasta real. Daí a `D-01`: a listagem entra como capacidade da **porta**.

## 3. A paridade é insensível ao template — medido

O `requirements.md` §6 afirma que a compatibilidade depende de as três `action` manterem nome e campos.
Foi verificado o que o harness de fato mede:

| Verificação | Resultado |
|---|---|
| O harness compara HTML renderizado? | **Não.** `harness.py:191` faz `m.render_template = _captura` — ele **substitui** a renderização por uma captura de contexto |
| O que ele lê do contexto? | **Chaves nomeadas** (`harness.py:211-221`): `success`, `message`, `dna_results`, `skipped_matches`, `gedcom_filename`. Chave a mais é invisível |
| O harness faz `GET /`? | **Não.** Os coletores usam `APP.test_client()` (`:202`, `:399`, `:409`) e fazem `POST` com `action` |
| O harness envia `matches_csv` como? | **Arquivo** (`files`), como hoje |

**Consequência para o plano:** a mudança de template e a variável de contexto nova são
**paridade-neutras**. O que a paridade vigia são os três ramos de `action` e as chaves de contexto
existentes — e é isso que a `RN-08` protege. Ainda assim a paridade é medida **antes e depois** (é a
premissa de §4 do roadmap, com verificação, não confiança).

## 4. O golden da tela inicial **não** deixa de valer — medido

O `requirements.md` §9 registra a dúvida de que o golden `SCR-001-initial-upload.html.txt` "deixa de
valer, exigindo recaptura". A leitura dos instrumentos mostra o contrário:

| Evidência | O que ela diz |
|---|---|
| `screens/golden/manifest.yaml`, entrada `SCR-001-initial-upload` | `legacyOrigin: "analisador-genealogico/templates/index.html:41-52"` — a origem é o **legado** |
| o mesmo manifesto, `capture.command` | `curl -s http://127.0.0.1:5001/ …` — a porta **5001**, onde sobe o oráculo congelado (`legacy_oracle.py`) |
| o mesmo manifesto, `captureBy` | `orchestrator (_reversa_sdd/parity/_golden_capture.py)`, cujo docstring diz "captura os golden files de tela do **oráculo legado**" |
| `screens/inventory.json` | cita `analisador-genealogico` **9 vezes** e `src/templates` **zero** |
| a nota do manifesto | "é exatamente o estado `{% if not gedcom_filename %}`" — o estado **do legado** |

Um oráculo congelado existe para não mudar quando o candidato muda. **O golden permanece válido**, e o
custo de recaptura que a §9 supunha **não existe** (`D-05`).

**O que existe de verdade** é a consequência que a §9 não enxergou: a aplicação **atual** deixa de ter o
estado inicial do legado, e o pipeline de migração foi desenhado sobre ele — `_reversa_sdd/migration/`
tem 35 arquivos e cenários `@paridade-visual` ancorados em `SCR-001` (`parity_specs.md`). Nada disso
fica errado; o que passa a ser necessário é **declarar a divergência** (`D-06`).

## 5. O contrato HTTP de hoje

Medido, para o delta ser preciso:

| Fonte | O que fixa |
|---|---|
| `_reversa_sdd/openapi/index.yaml:167-179` | `action=dna_analysis` exige `[action, gedcom_filename, root_name, matches_csv]`; `matches_csv` está em `files` |
| `_reversa_sdd/openapi/index.yaml:150-155` | `action=path_search` exige `[action, gedcom_filename, person1_name, person2_name]` — a árvore **já** chega por referência |
| `_reversa_sdd/analise-dna/contracts.md#1.1` | `matches_csv` em `files`, obrigatório; "não passa por validação de conteúdo" |
| `src/templates/index.html:96-102` | o formulário de DNA tem `enctype="multipart/form-data"` e `matches_csv` como `type="file" required` |
| `src/templates/index.html:52-63` | o ramo `{% if not gedcom_filename %}` é um formulário de envio, e **nada mais** |

É desse conjunto que sai a `D-03`: escolher o CSV exige um campo **novo**, porque o campo de hoje está
em `files` e dois `input` do mesmo nome no mesmo formulário se atropelam.

## 6. O trade-off do agrupamento, com números

| Medição | Resultado |
|---|---|
| Arquivos na pasta | 19 (8 `.ged`, 10 `.csv`, 1 `.xlsx`) |
| Aba de árvore | 8 arquivos → **7 itens** |
| Aba de DNA | 10 arquivos → **10 itens** — o agrupamento **não reduz nada** |
| Arquivos sem chave no nome | **3**, e o agrupamento **não os alcança** |
| Nomes visíveis repetidos | 3 arquivos chamados `Arvore_Unificada_Oficial_V1_2.ged` (2 conteúdos) e 3 chamados `Famílias_Sergipanas.csv` (2 conteúdos) |
| Par com e sem chave de **mesmo conteúdo** | `94e2402671702cac__Famílias_Sergipanas.csv` e `Famílias_Sergipanas.csv` — **mesmo `sha256`**, dois itens na lista |
| Chave vazada em nome visível | `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` |

O último item da tabela é o mais revelador: o agrupamento por chave, que é a razão de a lista não ler
conteúdo, **produz duplicação visível** exatamente nos três arquivos que ficaram fora do regime da
chave. É o custo declarado na §9, e ele virou a `D-09` e um risco com probabilidade **alta — já
ocorre**.

## 7. Alternativas avaliadas

| Tema | Alternativas descartadas | Onde está a decisão |
|---|---|---|
| De onde a lista vem | (a) `os.listdir` na rota; (b) porta nova só para listar; (c) capacidade na porta existente | `D-01` |
| Onde o agrupamento mora | (a) no adaptador; (b) no template; (c) função pura em `src/reporting/`; (d) reimplementar a forma do nome | `D-02` |
| Como o CSV escolhido viaja | (a) reaproveitar `matches_csv`; (b) `action` nova; (c) campo novo opcional | `D-03` |
| O que fazer com a tela de entrada | (a) manter como está; (b) abas e envio acima; (c) abas com o envio dentro | `D-04` |
| O golden da tela inicial | (a) recapturar; (b) apagar; (c) não tocar e declarar a divergência | `D-05`, `D-06` |
| Arquivo que não serve ao uso | (a) validar na listagem; (b) esconder; (c) listar e recusar no uso | `D-08` |
| Nome exibido do grupo | (a) primeiro em ordem alfabética; (b) todos os nomes; (c) o mais recente; (d) o sem chave vazada | `D-09` |

## 8. Padrões aplicados

1. **A borda não fala com o disco.** Padrão da feature 006, preservado pela `D-01`.
2. **Regra pura fora do template.** O agrupamento é função pura em `src/reporting/`, testável sem
   disco — o mesmo movimento que a feature 005 fez com o núcleo.
3. **Mudança aditiva de contrato.** A `D-03` acrescenta campo em vez de sobrecarregar o existente, para
   que a paridade e os testes de rota continuem exercitando o caminho antigo **exatamente** como está.
4. **Prova por medição, não por afirmação.** Paridade antes e depois; inventário por `sha256` antes e
   depois; suíte antes e depois.

## 9. Limites desta investigação

| Não verificado aqui | Onde é verificado |
|---|---|
| A paridade **executando** depois da mudança de template | Passo 7 do plano e `onboarding.md`; a insensibilidade foi lida no código, e leitura não é execução |
| O comportamento do `GET /` novo em navegador | `onboarding.md`, com a aplicação no ar |
| A ordenação e a apresentação da data nas duas abas | Desenho e teste da função pura; aqui só foi medido **o que** existe, não **como** vai aparecer |
| Se o pipeline de migração precisa de ação além da declaração | Registrado como divergência (`D-06`); decidir sobre o alvo da migração é de outra pipeline |

## 10. Fontes

- `src/app.py:161-189` (`_arvore_do_formulario`), `src/ports/__init__.py`, `src/ports/adaptadores.py`
- `src/templates/index.html:41-63`, `:96-102`
- `_reversa_sdd/upload-gedcom/contracts.md#1`, `#2.1`, `#3`; `_reversa_sdd/analise-dna/contracts.md#1`
- `_reversa_sdd/openapi/index.yaml:62-180`
- `_reversa_sdd/parity/harness.py:191`, `:202`, `:211-221`, `:399`, `:409`
- `_reversa_sdd/screens/golden/manifest.yaml` (entrada `SCR-001-initial-upload`); `_reversa_sdd/screens/inventory.json`
- `_reversa_sdd/parity/_golden_capture.py`; `_reversa_sdd/migration/parity_specs.md`
- `_reversa_sdd/architecture.md#7`; `_reversa_sdd/domain.md#3.5`
- Medições desta rodada: inventário por `sha256` da pasta, itens por aba, nomes visíveis repetidos
