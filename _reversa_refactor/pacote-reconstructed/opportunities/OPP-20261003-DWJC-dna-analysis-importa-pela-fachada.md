---
schema_version: 1
id: OPP-20261003-DWJC
display_number: 20
context: pacote-reconstructed
verb: decouple
title: dna_analysis importa pela fachada path_search, o que impede aposenta-la
target:
  files: [src/reconstructed/dna_analysis.py, src/reconstructed/path_search.py]
  symbol: linha 43 de dna_analysis.py, `from .path_search import find_ancestral_path, generate_mermaid_graph`
roi:
  confidence: green
  impact: acoplamento estrutural. A fachada `path_search` existe apenas para consumidores externos, mas um modulo **interno** importa por ela. Enquanto isso existir, a fachada nao pode ser removida nem reorganizada, e a reorganizacao em subpacotes fica travada por uma dependencia que nao deveria existir
  cost: low
  est_return: a fachada volta a existir so para consumidores externos, o que libera a reorganizacao do pacote e a aposentadoria futura da fachada
state: applied
traceability:
  soul:
    - .reversa/soul.md#decisoes-fundadoras
  specs:
    - _reversa_sdd/code-analysis.md#1
    - _reversa_sdd/addenda/003-renomear-pasta-app-para-src.md#2
---

## Antes observado

`path_search.py` e uma fachada de compatibilidade. O docstring dela declara nominalmente quem importa nomes dali: `app.py`, `dna_analysis.py`, `tests/test_path_search.py`, `tests/test_mermaid_escape.py`, `tests/test_characterization_mermaid.py`, `_reversa_sdd/parity/harness.py` e as sondas do defeito de escape do rotulo.

Dos consumidores listados, `dna_analysis.py` e o unico **interno ao pacote**. Os nomes que ele importa da fachada, `find_ancestral_path` e `generate_mermaid_graph`, nao sao definidos nela: sao reexportados de `path_finding.py` e `mermaid_render.py`. Ou seja, um modulo do nucleo atravessa uma camada de compatibilidade para chegar a outro modulo do nucleo.

## Transformacao proposta

Trocar a origem do import em `dna_analysis.py`:

| Antes | Depois |
|---|---|
| `from .path_search import find_ancestral_path, generate_mermaid_graph` | `from .path_finding import find_ancestral_path` e `from .mermaid_render import generate_mermaid_graph` |

A fachada permanece intacta, com o mesmo `__all__`, servindo os consumidores externos. O que muda e apenas a origem de duas importacoes.

**Efeito colateral desejado.** Com isso, `path_search.py` deixa de ter consumidor interno, e a coluna "Superficie de compatibilidade" do docstring dela passa a ser inteiramente sobre consumidores externos. Isso e o que torna possivel, numa transformacao futura, aposentar a fachada ou move-la sem arrastar o nucleo.

**Rede de seguranca.** A suite importa os dois nomes pelos dois caminhos: `tests/test_path_search.py` e `tests/test_characterization_mermaid.py` exercitam a fachada, e `dna_analysis` e exercitado por `tests/test_dna_analysis.py` e `tests/test_characterization_matching.py`. A paridade diferencial cobre o efeito no resultado final.
