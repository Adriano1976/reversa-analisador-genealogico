---
schema_version: 1
id: OPP-20261003-DWJC
verb: decouple
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
measurement:
  before: path_search com 1 consumidor interno (dna_analysis); dna_analysis com fan-out interno 6; 22 arestas internas no pacote
  after: path_search com 0 consumidores internos; dna_analysis com fan-out interno 7; 23 arestas internas no pacote
change_set:
  - chg: CHG-001
    file: src/reconstructed/dna_analysis.py
    purpose: os dois nomes passam a vir dos modulos que os definem, e nao da fachada que apenas os reexporta
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-dna-analysis.diff
---

## O que foi feito

`dna_analysis.py` importava dois nomes da fachada `path_search.py`. Nenhum dos dois e definido nela:

| Nome | Definido em | A fachada so reexportava |
|---|---|---|
| `find_ancestral_path` | `path_finding.py:51` | sim |
| `generate_mermaid_graph` | `mermaid_render.py:63` | sim |

A costura aplicada foi trocar a origem do import, sem tocar na fachada:

| Antes | Depois |
|---|---|
| `from .path_search import find_ancestral_path, generate_mermaid_graph` | `from .path_finding import find_ancestral_path` e `from .mermaid_render import generate_mermaid_graph` |

## Acoplamento medido, antes e depois

Medido por leitura de AST, com o medidor arquivado nesta pasta (`medir-acoplamento.py`), nao estimado.

| Metrica | Antes | Depois | Leitura |
|---|---|---|---|
| Consumidores internos de `path_search` | 1 | **0** | melhora, e o objetivo da oportunidade |
| Fan-out interno de `dna_analysis` | 6 | 7 | piora |
| Arestas internas do pacote | 22 | 23 | piora |
| Superficie externa de `path_search` | 5 arquivos | 5 arquivos | inalterada |

**O numero nao melhora em todas as dimensoes, e isso fica registrado.** Esta transformacao aumenta o total de arestas internas em uma unidade, porque o `dna_analysis` passa a nomear os dois provedores reais em vez de um intermediario. O ganho e estrutural: a fachada perde o ultimo consumidor interno, o que destrava a reorganizacao em subpacotes (`OPP-20261003-GUE7`) e a aposentadoria futura dela. Se o criterio fosse reducao estrita de arestas, a decisao correta seria nao fazer, e o plano registra isso explicitamente.

## Efeito alem do numero

Antes, enxugar a lista de reexportacao da fachada quebraria o `dna_analysis`, com um erro de importacao apontando para o lugar errado. Agora, a lista de reexportacao da fachada serve somente aos consumidores externos, e mexer nela nao alcanca mais o nucleo.

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento | **100 por cento, zero divergencia em 6 fixtures** |
| Consistencia entre o aplicado e o diff | nao se aplica | **linhas novas presentes e linha antiga removida** |

## Nota de metodo

A medicao tem um ponto cego declarado: o import do harness de paridade vive dentro de uma string, porque o coletor do candidato e um script embutido. A leitura por AST nao o enxerga, e por isso a superficie de compatibilidade aparece como 4 arquivos na medicao e como 5 na contagem manual. O numero correto e 5, e os dois estao registrados nas evidencias.
