# Regression Watch — feature `025-desempenho-carga-arvore`

> Data: `2026-10-17`
> Requirements: `_reversa_forward/025-desempenho-carga-arvore/requirements.md`
> Legacy impact: `_reversa_forward/025-desempenho-carga-arvore/legacy-impact.md`
> Âncora: **legado** (`_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

O que este arquivo vigia: as regras que **precisam continuar verdadeiras** nas próximas
extrações e nas próximas features. Cada item nasce de uma regra que esta feature tocou, e o
sinal de violação é o que se observa quando ela deixa de valer.

> **Adaptação declarada.** A seção "Modificadas" do `legacy-impact.md` está **vazia**: nenhuma
> regra de negócio mudou. Os itens abaixo vigiam as **invariantes que a mudança poderia ter
> quebrado** — uma por uma, todas verificadas por medição nesta rodada. Os números estão em
> `evidence/RELATORIO.md`.

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| **W001** | `_reversa_sdd/upload-gedcom/requirements.md#5` (`RF-11`, `RF-14`); `src/parsers/gedcom_parser.py` | Cada registro de nível 0 é materializado **uma vez** por carga: `records0("INDI")` = 1 e `records0("FAM")` = 1 | presença | Uma carga voltar a chamar `records0("FAM")` duas vezes; `tests/test_carga_da_arvore.py` falhar com "materializados 2 vezes" |
| **W002** | `src/parsers/gedcom_parser.py`; `evidence/depois/carga.txt` | `read_record` = 1 (`HEAD`) + número de `INDI` + número de `FAM`, na árvore real **42.391**, e `_init_index` = 1 | presença | `read_record` voltar a 49.321 (ou a qualquer valor que some uma passada `FAM` extra); `_init_index` deixar de ser 1 |
| **W003** | `_reversa_sdd/migration/parity_specs.md#4` (`@ordem`) | A ordem de inserção de nós e arestas do grafo é a mesma de antes da feature, e `child_to_family` mantém as listas na ordem | redação | `list(graph.nodes())` ou `list(graph.edges())` mudarem; `child_to_family` ganhar ou perder entradas; a impressão digital da árvore deixar de ser `8bf55afb…cc1d925` |
| **W004** | `_reversa_sdd/architecture.md#5`; `_reversa_sdd/upload-gedcom/requirements.md#5` | O resultado da análise de DNA é idêntico: **93 cartões** e **363 descartes**, na mesma ordem e com os mesmos valores | redação | A impressão digital do DNA deixar de ser `d369611f…585c5163`; o número de cartões ou de descartes mudar sem mudança declarada |
| **W005** | `evidence/antes/paridade.txt`; `evidence/depois/paridade.txt` | A paridade contra o oráculo produz **as mesmas 24 divergências** (8, 6, 4, 2, 4 e 0 por fixture) — nenhuma nova, nenhuma fixture nova divergente | presença | O total subir acima de 24, uma fixture que estava em 0 divergir, ou uma fixture nova aparecer divergente |
| **W006** | `tests/test_upload.py`; `tests/test_carga_da_arvore.py` | Existe teste que falha se a carga materializar `FAM` duas vezes, e ele continua coletado | presença | O arquivo de teste desaparecer, o teste virar `xfail`/`skip`, ou a asserção de contagem ser removida |
| **W007** | `_reversa_sdd/parity/harness.py`; `_reversa_sdd/parity/_profile_big.py` | Os dois continuam **byte a byte** — são a régua da paridade e do oráculo | presença | `sha256` de qualquer um mudar (`33e45b05…fe14d37` e `50c27b09…03f47d1`) |
| **W008** | `requirements.txt` | `ged4py` continua fixado em `0.5.5` | presença | A linha sair, a versão mudar, ou o parser ser substituído |

## Observações (sem peso de regressão)

| ID | Achado | Origem | Por que não tem peso |
|----|--------|--------|---------------------|
| **OBS-01** | A paridade está **vermelha desde antes desta feature** (24 divergências, 5 de 6 fixtures), por mudanças declaradas de matching e janela de vida posteriores a 2026-10-13 | `evidence/antes/paridade.txt`; `state.json` (checkpoint de 2026-10-13 registrava 100 %) | Não é regra de domínio nem defeito desta feature: é dívida pré-existente. O valor de `W005` é o **conjunto exato** de hoje, não "100 %" |
| **OBS-02** | O tempo da carga varia muito nesta máquina: 83 % entre repetições na rodada "antes" e 6 % na "depois" | `evidence/antes/carga.txt`; `evidence/depois/carga.txt` | É característica do ambiente, não regra. Por isso a asserção de desempenho é a **contagem de chamadas** (`W001`, `W002`), e o ganho declarado vem do custo da fase removida (mediana 1,59 s) |
| **OBS-03** | A passada `INDI` responde por ~19 s e a análise de DNA por 22 a 54 s, conforme o cache da máquina — muito acima do que esta feature removeu | `evidence/antes/carga.txt`; `RELATORIO.md` §4 | Fora do escopo declarado. O candidato natural para uma próxima feature é a `INDI`, e ele depende de decisão do operador |
| **OBS-04** | A chave do cache de nomes continua sendo `(len(people), primeira chave, última chave)`, e duas árvores do mesmo tamanho colidem (`L-24` / `E-05`) | `_reversa_sdd/architecture.md#7`, dívida #1 | Dívida alheia a esta feature, e o contrato de cache não foi tocado |

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar de novo.

## Arquivadas

> Preenchido quando itens forem arquivados por decisão humana.
