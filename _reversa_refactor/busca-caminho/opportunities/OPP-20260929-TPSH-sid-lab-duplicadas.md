---
schema_version: 1
id: OPP-20260929-TPSH
display_number: 5
context: busca-caminho
verb: restructure
title: sid e lab duplicadas textualmente em duas funções
target:
  files: [analisador-genealogico/reconstructed/path_search.py]
  symbol: generate_mermaid_graph, generate_mermaid_graph_indirect_bridge
smell: código duplicado no nível de função, com divergência já iniciada entre as cópias
roi:
  confidence: green
  impact: risco de correção pela metade. Existem dois caminhos de render e uma correção pode pegar só um
  cost: low
  est_return: uma única autoridade de escape e de id de nó, eliminando a divergência em curso
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/busca-caminho/design.md#interface, _reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas]
---

## Roteamento

- Destino: `/reversa-restructure OPP-20260929-TPSH`
- Ordem de encadeamento: **1 de 4**.
- Aprovada pelo usuário em 2026-09-29 para roteamento, com execução parando no gate.
- Motivo da posição: é a única que desbloqueia outra correção. Feita primeiro, o
  `BUG-20260929-J6PQ` passa a ter um único ponto de escape para corrigir.

## Antes observado

`sid()` e `lab()` estão definidas **duas vezes**, como funções internas:

- `generate_mermaid_graph` (linhas 185-244): `sid` em 186-188, `lab` em 190-199.
- `generate_mermaid_graph_indirect_bridge` (linhas 247-451): `sid` em 248-252, `lab` em 254-262.

As duas `lab` são equivalentes para fins de escape. As duas `sid` **não** são idênticas: a segunda
trata explicitamente o caso de entrada ser lista, tupla ou conjunto, antes de converter para texto;
a primeira não. É divergência já em curso, não apenas duplicação.

Consequência prática e verificável: o defeito registrado em `BUG-20260929-J6PQ` (escape incompleto de
nomes no rótulo Mermaid) existe nas duas cópias, e uma correção aplicada em apenas uma delas deixaria
metade dos caminhos de render desprotegida.

## Transformação proposta

Extrair as duas para o nível do módulo, com um único corpo cada:

1. `_mermaid_sid(raw)` com o tratamento de sequência unificado.
2. `_mermaid_label(txt)` com o escape único.

Atualizar as quatro chamadas internas. Nenhum corpo de função de negócio muda, nenhuma string gerada
muda, exceto onde a divergência de `sid` já produzia saída diferente entre os dois caminhos.

## Rede de segurança exigida

- `tests/test_path_search.py` (9 testes) verde antes e depois.
- Caracterização recomendada: comparar a string Mermaid gerada pelos dois caminhos para as fixtures de
  `_reversa_sdd/parity/fixtures/gedcom/`, antes e depois, garantindo igualdade byte a byte.

## Risco

Baixo. O único ponto de atenção é a unificação de `sid`: se algum teste depender da diferença atual,
ele vai falhar, e a falha é informativa, não um defeito novo.

## Estado do gate

Especialista acionado em 2026-09-29 em `control_mode: gated`. O plano e a rede de segurança estão
prontos em `../transformations/OPP-20260929-TPSH-unificar-sid-lab/`, e a equivalência **já foi
provada** contra uma cópia sombra do pacote, sem tocar no projeto:

| Rede | Projeto (antes) | Sombra transformada |
|------|-----------------|---------------------|
| Caracterização Mermaid, 4 casos / 40 linhas | verde | verde, saída idêntica |
| Suíte completa | 50 passed | 50 passed |

A aplicação está **bloqueada** por `.reversa/reversa-config.json` em `allowLegacyEdits: false` com
`allowedPaths: []`. O arquivo alvo é `analisador-genealogico/reconstructed/path_search.py`.

## Ordem sugerida

Executar **antes** da correção do `BUG-20260929-J6PQ`. Unificar primeiro reduz a correção de segurança
a um único ponto.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
