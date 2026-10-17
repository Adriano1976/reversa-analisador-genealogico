# Legacy Impact — feature `025-desempenho-carga-arvore`

> Data: `2026-10-17`
> Requirements: `_reversa_forward/025-desempenho-carga-arvore/requirements.md`
> Roadmap: `_reversa_forward/025-desempenho-carga-arvore/roadmap.md`
> Âncora: **legado** (`_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/parsers/gedcom_parser.py` | `gedcom_parser` (`architecture.md#3`; `c4-components.md#3`) | `contrato-alterado` | **LOW** | `build_graph_from_parser` deixa de receber o `GedcomReader` e passa a receber a lista de registros `FAM`; `carregar_arvore` materializa essa lista uma vez. **Nenhuma regra de negócio muda**: mesma árvore, mesmos nós, mesmas arestas, mesma ordem, mesmo `child_to_family` |
| `tests/test_upload.py` | área de teste do parser (`architecture.md#7`, dívida #23) | `regra-alterada` | **LOW** | Dois testes passam a entregar `list(parser.records0("FAM"))` ao grafo. A cobertura é a mesma; nenhum teste removido |
| `tests/test_carga_da_arvore.py` | área de teste do parser | `regra-nova` | **LOW** | Prende a `RN-02`: uma materialização por registro de nível 0, e o invariante de `read_record` |
| `_reversa_sdd/parity/_perfil_da_carga.py` | **fora do runtime** — instrumento de desenvolvimento, irmão de `_profile_big.py` | `componente-novo` | **LOW** | Mede o código de produção (carga + DNA) e conta chamadas ao `ged4py`. Não é importado por `src/` |
| `_reversa_forward/025-desempenho-carga-arvore/evidence/_impressao_da_arvore.py` | **fora do runtime** — instrumento de prova | `componente-novo` | **LOW** | Impressão digital da árvore e do resultado, para comparação exata sem transcrever dado pessoal |
| `.reversa/active-requirements.json` | metadado do Reversa, não é legado | — | — | Registro do estágio da feature |

**Nenhum outro arquivo de produção foi tocado** — medido por `git diff --stat` (`evidence/depois/escopo.txt`):
`ports/`, `application/`, `app.py`, `core/`, `reporting/`, `utils/`, `templates/`, `docker/`,
`init.sql` e `requirements.txt` estão intactos. `_reversa_sdd/parity/_profile_big.py` e
`harness.py` mantêm o mesmo `sha256`.

## 2. Diff conceitual por componente

### `gedcom_parser` — a única mudança de produção

**Antes.** `carregar_arvore` percorria `records0("FAM")` para montar `families` e passava o
`GedcomReader` a `build_graph_from_parser`, que percorria `records0("FAM")` **de novo**. Cada registro de
família era materializado duas vezes — na árvore real, 13.860 objetos em vez de 6.930, e 49.321
`read_record` em vez de 42.391.

**Depois.** `carregar_arvore` materializa a lista **uma vez** e a entrega ao grafo. A função do grafo
deixa de conhecer o `GedcomReader`: recebe dado e devolve grafo (`RN-03`). O índice de nível 0 do
`ged4py` continua sendo construído uma única vez, como sempre foi — a feature removeu a **reiteração**,
não a indexação.

**O que não mudou, e é o essencial.** A forma da tupla devolvida, a ordem de inserção de nós e arestas
(`@ordem`), o tratamento de família sem `xref_id` (`BR-U-18`), a aresta só para nó existente, o
`child_to_family` como lista por filho e o texto de qualquer mensagem.

**Risco declarado e contido.** A lista é compartilhada com o dicionário `families`; o invariante é que
a construção do grafo só **lê** `xref_id` e `sub_records`. Está escrito no docstring da função.

### Instrumentos (fora do runtime)

Dois scripts novos, nenhum importado por `src/`. O primeiro é irmão de `_profile_big.py`, que continua
byte a byte medindo o oráculo; o segundo produz a impressão digital usada na prova de identidade.

## 3. Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` e contratos que **continuam intactos**, verificados nesta rodada:

| Regra / contrato | Onde vive | Como foi verificada |
|---|---|---|
| `RF-11` a `RF-14` de `upload-gedcom` — parsear `INDI`/`FAM`, indexar por `xref_id`, construir o grafo bipartido, devolver a árvore como valor | `_reversa_sdd/upload-gedcom/requirements.md#5` | impressão digital da árvore idêntica; suíte verde |
| `BR-U-18` — família sem `xref_id` é ignorada; aresta só para nó existente | `_reversa_sdd/code-analysis.md#4` | `tests/test_upload.py::test_family_without_id_skipped` e o teste do grafo passam |
| `@ordem` — a ordem de inserção das arestas decide o caminho do `nx.shortest_path` | `_reversa_sdd/migration/parity_specs.md#4` | `list(graph.nodes())` e `list(graph.edges())` idênticos antes/depois |
| Os três eixos que não se contaminam e o confronto em quatro estados | `_reversa_sdd/architecture.md#5` | resultado de DNA idêntico: 93 cartões, 363 descartes, mesmas ordens |
| Matching, RapidFuzz, janela de vida e busca de caminho | `src/core/` | `git diff --stat` sem esses arquivos |
| `ged4py==0.5.5` no pin | `requirements.txt` | `git diff -- requirements.txt` vazio |

## 4. Modificadas

**Nenhuma regra de negócio foi alterada ou removida.** A única modificação é de **contrato interno de
função** (`build_graph_from_parser`), com severidade LOW, e ela não atravessa fronteira nenhuma: a porta
`CarregadorDeArvores` continua chamando `carregar_arvore(caminho)` e recebendo a mesma tupla.

A manifestação externa da mudança é uma só: **menos trabalho por carga**, com o mesmo resultado. Medido:
`read_record` 49.321 → 42.391, e o custo removido tem mediana de **1,59 s** na árvore real.
