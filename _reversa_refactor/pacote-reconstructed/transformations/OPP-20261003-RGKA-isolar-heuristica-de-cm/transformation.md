---
schema_version: 1
id: OPP-20261003-RGKA
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/suite-depois.txt
    - safety-net/paridade-depois.txt
    - safety-net/equivalencia-cm.txt
    - safety-net/pyrefly-contagem.txt
measurement:
  before: "dna_analysis.py com 137 linhas e 4 definicoes de topo, a tabela de cM e a traducao entre elas; pacote com 13 modulos, 1376 linhas e 23 arestas internas; fan-out interno de dna_analysis 7"
  after: "core/cm_estimator.py com 57 linhas, 2 definicoes e fan-out 0; dna_analysis.py com 122 linhas e 2 definicoes; pacote com 15 modulos, 1419 linhas e 24 arestas internas; fan-out interno de dna_analysis 8"
change_set:
  - chg: CHG-001
    file: src/reconstructed/core/__init__.py
    purpose: tornar `reconstructed.core` pacote regular, que e o que a RN-01 permite (a proibicao e sobre `src/__init__.py`)
  - chg: CHG-002
    file: src/reconstructed/core/cm_estimator.py
    purpose: receber a tabela de nove faixas e a traducao de cM em parentesco, com a origem da tabela declarada no proprio arquivo
  - chg: CHG-003
    file: src/reconstructed/dna_analysis.py
    purpose: deixar de definir a tabela e a funcao, e continuar a reexporta-las para os consumidores externos
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-core-init.diff
  - CHG-002-core-cm-estimator.diff
  - CHG-003-dna-analysis.diff
---

## O que foi feito

`dna_analysis.py` tinha 137 linhas e quatro coisas de naturezas diferentes. As duas de dominio puro, que nao dependem de nada, sairam:

| Antes | Depois |
|---|---|
| `SHARED_CM_DATA` definida dentro de `dna_analysis.py` | definida em `core/cm_estimator.py` |
| `get_relationships_by_cm` definida dentro de `dna_analysis.py` | definida em `core/cm_estimator.py` |
| a fachada definia e reexportava | a fachada so reexporta |

A costura aplicada foi uma linha:

    from .core.cm_estimator import SHARED_CM_DATA, get_relationships_by_cm

Nenhum arquivo fora de `src/reconstructed/` foi tocado. A lista de `__all__` da fachada continua com os mesmos 18 nomes, na mesma ordem, provado por AST contra a copia pristina.

## Coesao medida, antes e depois

Medido por leitura de AST, com o medidor arquivado nesta pasta (`medir-coesao.py`), nao estimado. Os dois retratos estao em `before-after/coesao-antes.txt` e `before-after/coesao-depois.txt`.

| Metrica | Antes | Depois | Leitura |
|---|---|---|---|
| Definicoes de topo de `dna_analysis.py` | 4 | **2** | melhora, e o objetivo da oportunidade: o orquestrador deixa de abrigar conhecimento de dominio que nao orquestra |
| Quem define o conhecimento de cM | `dna_analysis.py` | `core/cm_estimator.py` | melhora: passa a existir um lugar unico cuja responsabilidade e exatamente essa |
| Fan-out interno de `dna_analysis.py` | 7 | 8 | piora, uma aresta: ele nomeia o novo provedor |
| Arestas internas do pacote | 23 | 24 | piora, uma aresta |
| Modulos do pacote | 13 | 15 | dois arquivos novos, o subpacote `core/` e o modulo |
| Linhas do pacote | 1376 | 1419 | mais 43: o docstring de origem da tabela e a declaracao do modulo |

O numero nao melhora em todas as dimensoes, e isso fica registrado: esta transformacao **aumenta** o total de arestas internas em uma unidade, e aumenta o total de linhas em 43. O que ela entrega e coesao: o modulo que orquestra o cruzamento deixa de ser tambem o dono da heuristica de cM.

O modulo novo tem **fan-out interno 0**: nao importa nada do pacote. E o unico modulo de dominio puro criado por esta serie de transformacoes.

## A origem da tabela, e o que NAO foi possivel cumprir

Este era o segundo objetivo da oportunidade, e ele precisa ser lido com precisao.

O que foi feito: `core/cm_estimator.py` declara, no proprio arquivo e antes dos numeros, que **as nove faixas foram escritas a mao** e nao tem fonte externa verificavel, com a data da decisao humana (`_reversa_sdd/questions.md`, pergunta 5, de 2026-09-30), a regra que a spec fixou (`RF-10a`, heuristicas sem fonte verificavel) e o registro da lacuna (`_reversa_sdd/domain.md` L-07). Declara tambem que a sobreposicao de ate quatro faixas e consequencia do metodo manual, e nao do Shared cM Project.

O que **nao** foi feito, e o registro nao vai fingir que foi: o principio V pede **referencia e data de consulta**, e nao existe referencia a citar. O comentario declara a ausencia dela, que e o que protege o leitor de tomar as faixas por calibradas, mas o principio V continua **formalmente aberto**. Fecha-lo exigiria um dado que o repositorio nao tem.

Se a versao usada como inspiracao for recuperada algum dia, `core/cm_estimator.py` e o unico lugar a atualizar.

## Fronteira da alma

| Fonte | O que diz | Situacao |
|---|---|---|
| `.reversa/soul.md#decisoes-fundadoras` (3) | a predicao de relacao e feita por faixas de cM | preservada: a predicao continua, pela mesma tabela, sem alterar um numero |
| `.reversa/soul.md#entidades-centrais` | `SHARED_CM_DATA` e a autoridade unica das faixas | preservada: continua sendo uma tabela, em um so lugar |
| principio II | refatoracao nao muda comportamento observavel | preservado, com prova direta abaixo |

Nenhuma fronteira da alma foi violada. A alma nao define `dna_analysis.py` como modulo coeso, e a separacao nao funde nada que ela separe.

Uma imprecisao da alma fica registrada sem ser corrigida, porque corrigir a alma nao e deste verbo: `.reversa/soul.md` linha 39 chama a tabela de "padrao do Shared cM Project", e a decisao humana de 2026-09-30 diz o contrario, que as faixas foram escritas a mao. A linha 51 da mesma alma ja registra a lacuna. O conflito e anterior a esta transformacao e deve ir para `/reversa-sync` ou para uma nova extracao da alma.

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento em 6 fixtures | **100 por cento, zero divergencia em 6 fixtures** |
| Equivalencia direta da costura | nao se aplica | **zero divergencia em 51 sondagens** |
| Identidade dos objetos expostos pela fachada | nao se aplica | **`SHARED_CM_DATA` e `get_relationships_by_cm` sao os mesmos objetos** |
| Tabela preservada byte a byte | nao se aplica | **sim, conferido por comparacao de texto** |
| Pyrefly | 5 diagnosticos nas duas partes | **5 diagnosticos nas duas partes** |

A prova de equivalencia (`verificar-costura.py`) nao depende do oraculo: ela extrai a tabela e a funcao da copia pristina e compara as duas versoes lado a lado para os 40 valores de cM do harness mais 11 bordas de tipo (`None`, `"300"`, `[]`, `True`, `False`, `0.0`, `1e9`). Toda a saida esta em `safety-net/equivalencia-cm.txt`. Ela importa porque o harness de paridade prova o sistema contra o oraculo, e esta prova isola a costura.

## Divergencia declarada em relacao ao plano aprovado

O conteudo aplicado e o conteudo aprovado, com **uma** diferenca, e ela e de acentuacao:

O docstring do modulo novo foi escrito **sem acentos**, seguindo a convencao dos modulos irmaos do pacote (`csv_ingest.py`, `gedcom_state.py`, `path_finding.py`, `matching.py` e o proprio `dna_analysis.py`, cujos docstrings de modulo sao ASCII). O plano o mostrava acentuado. O texto e o mesmo, a ordem das secoes e a mesma, e nenhuma linha de codigo foi afetada. O docstring da funcao `get_relationships_by_cm` ficou acentuado, que e a convencao dos docstrings internos do pacote.

## Risco residual

Uma diferenca semantica real, do mesmo tipo que o projeto ja documentou para `graph`: a lista passa a ser lida de `core.cm_estimator`. Quem **reatribuir** `dna_analysis.SHARED_CM_DATA = outra_lista` deixa de influenciar `get_relationships_by_cm`. Mutar em lugar continua identico, e a identidade do objeto e a mesma.

Medido: existe **uma** ocorrencia de `SHARED_CM_DATA =` no repositorio, que e a definicao. Nenhum teste faz monkeypatch da tabela. O cenario e hipotetico hoje.

## O que ficou pendente, e nao e desta transformacao

- `OPP-20261003-LMAY` segue com o registro apontando para `upload.py`, que nao existe mais.
- `OPP-20261003-GUE7` agora tem `core/` criado com um modulo; o inventario dele continua dizendo 12 arquivos e 1363 linhas, quando o pacote tem 15 arquivos e 1419 linhas.
- As linhas 14 e 18 do `dna_analysis.py` citam a `OPP-20261003-RGKA` e a `OPP-20260929-ZV52`; a secao de layout do proprio pacote agora tem dois donos de modulo em `core/` previstos pela GUE7, e so um existe.
