---
schema_version: 1
id: OPP-20260929-UXEF
display_number: 6
context: busca-caminho
verb: modularize
title: path_search concentra cinco responsabilidades em 501 linhas
target:
  files: [analisador-genealogico/reconstructed/path_search.py]
  symbol: módulo inteiro, 501 linhas
smell: arquivo que faz coisas demais, misturando navegação de grafo, algoritmo de busca e renderização
roi:
  confidence: yellow
  impact: acoplamento e testabilidade. O algoritmo de busca não pode ser exercitado sem carregar o render
  cost: medium
  est_return: busca testável sem render, e o render isolado como o ponto onde o escape vive
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras, .reversa/soul.md#entidades-centrais]
  specs: [_reversa_sdd/busca-caminho/design.md#interface, _reversa_sdd/busca-caminho/design.md#detalhe-da-conexão-direta-find_ancestral_path]
---

## Antes observado

Mapa de responsabilidades, com as linhas verificadas:

| Faixa | Responsabilidade | Símbolos |
|-------|------------------|----------|
| 12-23 | Imports e constantes | `MAX_DEPTH`, `MAX_HOPS` |
| 30-35 | Resolução de pessoa por nome | `find_person_by_name` |
| 42-114 | Navegação familiar | `get_parents`, `get_spouses`, `are_spouses`, `split_path_by_marriage`, `pick_spouse_for_couple` |
| 117-124 | Utilidade de lista | `exclude_tail` |
| 126-142 | Busca indireta por afinidade | `find_indirect_path` |
| 144-178 | Busca direta por ancestral comum | `find_ancestral_path` |
| 185-451 | Renderização Mermaid | `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge` |
| 458-497 | Orquestração | `path_search` |

O bloco de renderização ocupa **267 das 501 linhas (53%)**, e é ele que carrega `unicodedata` e as
regras de escape. A busca em si, que é o que a spec `busca-caminho/design.md` descreve como
comportamento, ocupa 52 linhas.

Dois sinais de fronteira já borrada no próprio arquivo:

- Linha 131: `from .upload import graph` **dentro de uma função**, enquanto `people`, `families`,
  `child_to_family` e `get_name` são importados no topo (linha 20). O motivo é semântica de binding:
  `people` é mutado in place e continua válido, `graph` é reatribuído e precisaria de reimport. Duas
  regras de import no mesmo arquivo, sem comentário explicando a diferença.
- Linha 501: `from .upload import ref_id  # noqa: E402`, import no rodapé do arquivo, com supressão de
  aviso do linter.

## Transformação proposta

Extrair em três módulos, sem alterar nenhum corpo de função:

1. `family_navigation.py`: `get_parents`, `get_spouses`, `are_spouses`, `split_path_by_marriage`,
   `pick_spouse_for_couple`, `exclude_tail`, `find_person_by_name`.
2. `path_search.py`: `find_ancestral_path`, `find_indirect_path`, `path_search`, `MAX_DEPTH`, `MAX_HOPS`.
3. `mermaid_render.py`: `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge` e, depois da
   `OPP-20260929-TPSH`, os helpers `_mermaid_sid` e `_mermaid_label`.

Trocar os dois imports anômalos por imports normais no topo, e mover o reexport de `ref_id` para o topo.

## Rede de segurança exigida

- `tests/test_path_search.py` (9 testes) verde.
- `tests/test_dna_analysis.py` verde, porque `dna_analysis` importa `find_ancestral_path` e
  `generate_mermaid_graph` deste módulo (linha 24). A extração **precisa** reexportar os nomes antigos
  em `path_search`, senão o módulo de análise quebra por import.
- Harness de paridade verde.

## Risco

Médio. Dois consumidores dependem dos nomes atuais no namespace de `path_search`:
`dna_analysis.py:24` e os testes. Reexportar durante a transição é obrigatório.

## Ordem sugerida

Depois da `OPP-20260929-TPSH`. Separar o render é mais fácil quando as duas cópias de `sid` e `lab`
já viraram uma só.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
