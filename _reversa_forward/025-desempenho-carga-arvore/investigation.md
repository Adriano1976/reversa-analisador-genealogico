# Investigation: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/025-desempenho-carga-arvore/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. A pergunta que precisava ser respondida antes do plano

O pedido afirmava duas coisas: que a carga de uma árvore de 35 mil pessoas levava **8,4 s**, e que a
indexação do `ged4py` era **repetida três vezes**. As duas foram checadas antes de qualquer decisão,
porque a segunda é o alvo da mudança e a primeira é o que dá sentido a ela.

## 2. Como o `ged4py` funciona por dentro (fonte primária)

Fonte lida: `.venv/Lib/site-packages/ged4py/parser.py` (versão **0.5.5**, a do pin).

- `index0` é uma **propriedade com cache**. O corpo é `if self._index0 is None: self._init_index()`
  e devolve a lista já construída. Consequência: quantas vezes o código acessar `index0`, a
  varredura do arquivo acontece **uma única vez** por `GedcomReader`.
- `_init_index` é quem varre o arquivo linha a linha e monta `_index0` (posição + tag de cada
  registro de nível 0) e `_xref0`. Ele também lê o `HEAD` no fim.
- `records0(tag)` **itera sobre a lista em cache** e chama `read_record(offset)` para cada registro
  que casa com a tag. Ou seja: o índice é barato e reaproveitado; o caro é **materializar o
  registro** a cada iteração.

**Portanto a expressão "indexação repetida" descreve o sintoma errado.** O que se repete é a
**materialização** dos registros `FAM`: `carregar_arvore` percorre `records0("FAM")` para montar
`families`, e `build_graph_from_parser` percorre `records0("FAM")` de novo para montar o grafo.

## 3. Medições que sustentam o plano (2026-10-17, esta máquina)

Árvore real `src/uploads/0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged` (5.508.014 bytes,
35.460 pessoas, 6.930 famílias, grafo de 42.390 nós e 36.807 arestas), `.venv` Python 3.14.6,
`DATABASE_URL` ausente.

**Contagem de chamadas, por instrumentação do `GedcomReader`:**

| Contador | Valor | Leitura |
|---|---:|---|
| `records0("INDI")` | 1 | ok |
| `records0("FAM")` | **2** | o desperdício |
| `index0` (acesso à propriedade) | 3 | 3 acessos, **1** varredura |
| `_init_index` (execução) | **1** | a indexação **não** se repete |
| `read_record` | **49.321** | 1 `HEAD` + 35.460 `INDI` + 2 × 6.930 `FAM` |

O total de `read_record` fecha exatamente com a aritmética dos registros, o que prova que o segundo
`records0("FAM")` **relê** cada família, e não reaproveita o objeto já lido.

**Tempo por etapa:**

| Etapa | Tempo |
|---|---:|
| `carregar_arvore` — 3 execuções no mesmo processo | 26,55 / 28,02 / 32,71 s (mediana 28,02) |
| `carregar_arvore` — 1ª execução em processo novo | 51,68 s |
| passada `INDI` | 19,32 s |
| passada `FAM` (montar `families`) | 2,06 s |
| `build_graph_from_parser` (2ª passada `FAM` + grafo) | 2,39 s |
| 2ª materialização dos `FAM`, isolada | **1,80 s** |
| grafo montado sobre as famílias já lidas | 0,90 s |
| `dna_analysis` (CSV `Famílias Sergipanas`, raiz `Adriano Santos`) | 54,05 s |

**Dispersão:** 23 % entre execuções do mesmo processo e quase 2× entre cache frio e quente. Foi o
que obrigou o protocolo de `D-05` (aquecimento descartado + 3 repetições em processo próprio).

**A verificação decisiva:** montar o grafo a partir das famílias já lidas, na mesma árvore real,
devolveu **mesmo número de nós, mesmo número de arestas, mesmo `child_to_family`, a mesma
`list(graph.nodes())` e a mesma `list(graph.edges())`** — igualdade booleana nas quatro comparações.
É essa medição que autoriza o plano, não uma suposição sobre o que o `networkx` faria.

## 4. Alternativas avaliadas

| Alternativa | Situação | Por quê |
|---|---|---|
| **Entregar as famílias já lidas ao grafo** | **escolhida** | Remove 6.930 materializações, é local, mantém a ordem exata e já foi provada idêntica na árvore real |
| `families.values()` como fonte do grafo | descartada | O dicionário é chaveado por `ref_id`; famílias sem `xref_id` colapsam na chave `None` e a sequência iterada deixaria de ser a de hoje (`D-02`) |
| Cache de árvore por `sha256` | **fora de escopo declarado** | Exige ADR próprio, trava de concorrência e limite de memória; muda o desenho de "sem estado" (`architecture.md#1`) |
| Substituir o `ged4py` por parser próprio | **fora de escopo** | Depende do resultado desta medição; a passada `INDI` (19,3 s) é o custo dominante e tem risco de paridade alto |
| `functools.lru_cache` sobre `records0` | descartada | `records0` devolve **gerador**, e cachear gerador não é cache; materializar por tag dentro do `GedcomReader` seria um cache paralelo ao índice do próprio `ged4py` |
| Índice próprio por tag no parser | descartada | Duplica o que o `ged4py` já faz bem; o problema nunca foi localizar o registro, foi materializá-lo duas vezes |
| Paralelizar `INDI` e `FAM` | descartada | O `GedcomReader` é um só e não é thread-safe para leitura concorrente; o ganho teórico não paga o risco |
| Perfilar com `cProfile` | descartada como instrumento oficial | Mede função, não etapa de negócio; e não devolve a contagem por tag que o `RF-03` exige |

## 5. Por que o instrumento existente não serve

`_reversa_sdd/parity/_profile_big.py` monta um coletor que **copia** `_reversa_sdd/oracle/app_legacy_e43ca22.py`
para uma pasta temporária, importa o arquivo como módulo `oracle` e chama
`m.load_gedcom_and_build_graph(GED)`. Ele mede o **legado congelado**, e o que ele isola são as
funções de nome (`get_name`, `norm_name`, `demojibake`, …) e o custo unitário de
`find_ancestral_path`. Ele não toca `carregar_arvore`, não toca a fronteira de aplicação e **não mede
a análise de DNA** do código atual.

Daí a decisão `D-01`: um irmão novo mede o alvo certo, e o `_profile_big.py` continua sendo a régua
do oráculo — inclusive porque a paridade depende de ele não mudar de comportamento.

## 6. O que a leitura do código confirma sobre o contrato

- `build_graph_from_parser` tem **um** chamador de produção: `carregar_arvore`
  (`src/parsers/gedcom_parser.py:75`). Os demais chamadores são dois testes
  (`tests/test_upload.py:217` e `:263`).
- `carregar_arvore` tem **um** chamador de produção: o adaptador da porta
  (`src/ports/adaptadores.py:257`), que passa o caminho e devolve a tupla intacta.
- O harness de paridade chama `GP.carregar_arvore(GED)` (`_reversa_sdd/parity/harness.py:298`) e
  depende da tupla, não da assinatura interna do grafo. Ele **não** precisa de edição.
- Nenhum código muta registro do `ged4py`; a construção do grafo só lê `xref_id` e `sub_records`.

## 7. Padrões aplicáveis

- **Passar dado, não a fonte de I/O**: quem lê o arquivo é o parser; quem transforma recebe dado.
  É a mesma direção que o projeto já tomou no `ADR-24` (a árvore entra por parâmetro, não por
  estado global) e no `ADR-34` (o renderizador recebe consultas ligadas, não importa `core`).
- **Materialização única por carga**: um registro de nível 0 é lido do arquivo uma vez e o objeto
  resultante é compartilhado por leitura.
- **Prova por impressão digital**: comparar um hash determinístico de uma serialização canônica é o
  jeito de afirmar igualdade exata sem transcrever dado pessoal.

## 8. Fontes

- `src/parsers/gedcom_parser.py:26-76` — o código sob mudança.
- `.venv/Lib/site-packages/ged4py/parser.py` — `index0`, `xref0`, `_init_index`, `records0`
  (ged4py 0.5.5, o pin do projeto). Documentação do projeto: <https://ged4py.readthedocs.io/>.
- `src/core/registro.py:35-37` — `ref_id` e o caso `None`.
- `_reversa_sdd/migration/parity_specs.md#4` — `@ordem` e a ordem de inserção das arestas.
- `_reversa_sdd/migration/risk_register.md#RISK-004` — comparação exata, sem tolerância.
- `_reversa_sdd/architecture.md#1` — parse a cada requisição, sem cache.
- `_reversa_sdd/parity/_profile_big.py` — o instrumento irmão, que mede o oráculo.
- `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#por-que-a-escala-medida` — a árvore
  de 35.460 pessoas e o risco de colisão de cache entre versões.
