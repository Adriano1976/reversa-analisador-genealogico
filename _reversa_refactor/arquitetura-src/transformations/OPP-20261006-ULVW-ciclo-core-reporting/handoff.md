# Handoff para `/reversa-decouple`

> Gerado pelo `/reversa-refactor` em 2026-10-06, a pedido do usuário.
> Este documento é a passagem de bastão: ele **não** aplica transformação nenhuma.

## Oportunidade

| Campo | Valor |
|---|---|
| ID | `OPP-20261006-ULVW` |
| display_number | 28 |
| Contexto | `arquitetura-src` |
| Verbo | `decouple` |
| Arquivo da oportunidade | `_reversa_refactor/arquitetura-src/opportunities/OPP-20261006-ULVW.md` |
| Pasta de destino | `_reversa_refactor/arquitetura-src/transformations/OPP-20261006-ULVW-<slug>/` |
| Padrão de aceite | a string Mermaid gerada permanece idêntica, byte a byte |

## Por que este verbo

O alvo é **topologia de dependência**, não distribuição de responsabilidade: o ciclo existe porque
o renderizador consulta o domínio em vez de receber o que precisa desenhar. É por isso que o verbo é
`decouple` e não `modularize`.

## Medição do acoplamento ANTES (passo 2 do fluxo do especialista)

Arestas de import entre pacotes, medidas por AST em `src/`:

```text
core       -> reporting   2
reporting  -> core        3
```

**O ciclo é exatamente `core/` ↔ `reporting/`.** Nenhum outro par de pacotes forma ciclo:
`core/ -> parsers` (1) e `parsers/ -> core` (3) formam o segundo ciclo, que é alvo da
`OPP-20261006-LIGH` e **não** desta oportunidade.

### Fan-out de `reporting/mermaid_render.py` para `core/` (3 imports, no topo)

| Linha | Módulo | Símbolos |
|---|---|---|
| 16 | `core.family_navigation` | `exclude_tail`, `get_spouses`, `pick_spouse_for_couple`, `split_path_by_marriage` |
| 22 | `core.path_finding` | `find_ancestral_path` |
| 23 | `core.gedcom_state` | `get_name`, `people` |

### Fan-in de `core/` para `reporting/` (2 imports)

| Arquivo | Linha | Símbolos |
|---|---|---|
| `src/core/path_search.py` | 51 | `_LABEL_SEGURO`, `_mermaid_label`, `_mermaid_sid`, `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge` |
| `src/core/dna_analysis.py` | 51 | `generate_mermaid_graph` |

### Pontos de chamada acoplados (21 no total)

O que precisa ser resolvido pela costura, por função que os contém:

| Função | Linha | Símbolo do core chamado |
|---|---|---|
| `generate_mermaid_graph` | 78 | `get_spouses` |
| `generate_mermaid_graph` | 83, 84, 92 | `get_name` (e `people[...]` em 83 e 84) |
| `generate_mermaid_graph_indirect_bridge` | 126 | `split_path_by_marriage` |
| `generate_mermaid_graph_indirect_bridge` | 135 | `find_ancestral_path` |
| `generate_mermaid_graph_indirect_bridge` | 139 | `pick_spouse_for_couple` |
| `generate_mermaid_graph_indirect_bridge` | 213, 214 | `exclude_tail` |
| `generate_mermaid_graph_indirect_bridge` | 231 | `find_ancestral_path` |
| `generate_mermaid_graph_indirect_bridge` | 235 | `pick_spouse_for_couple` |
| `generate_mermaid_graph_indirect_bridge` | 246, 247 | `exclude_tail` |
| `generate_mermaid_graph_indirect_bridge` | 155, 242 | `get_name` (duas chamadas em cada linha) |
| `add_node` (aninhada) | 181 | `get_name` mais `people.get(pid)` |

Total: **19 chamadas de função** mais **2 acessos diretos a `people`** (nas linhas 83 e 84), somando
21 pontos de acoplamento.

### Tamanho do alvo

| Arquivo | Linhas |
|---|---|
| `src/reporting/mermaid_render.py` | 289 |
| `src/core/path_search.py` | 219 |
| `src/core/dna_analysis.py` | 250 |

### Superfície pública hoje

`mermaid_render.py` define exatamente quatro funções: `_mermaid_sid` (26), `_mermaid_label` (50),
`generate_mermaid_graph` (63) e `generate_mermaid_graph_indirect_bridge` (112).
Nenhuma classe, nenhum estado de módulo.

## Costura sugerida, para o especialista avaliar

A direção da dependência que quebra o ciclo é uma só: **o núcleo monta a estrutura do diagrama e o
renderizador apenas serializa**. A oportunidade registra o desenho; a escolha da costura é do
especialista.

Duas observações que medem o risco de cada caminho:

1. **`_LABEL_SEGURO`, `_mermaid_label` e `_mermaid_sid` são importados pelo núcleo**
   (`path_search.py:51`), e o docstring de `path_search` explica que isso existe porque
   `tests/test_mermaid_escape.py` e as sondas do BUG-20260929-J6PQ importam esses nomes **de lá**.
   Ou seja: parte do fan-in de `core/` para `reporting/` é superfície de compatibilidade de teste,
   não dependência de produção. Isso é a matéria-prima da `OPP-20261006-ESKO` (#30), e o
   especialista deve decidir se ataca aqui ou lá, sem duplicar o trabalho.
2. **O contrato de escape do rótulo é o ponto mais sensível do sistema.** É o componente com mais
   defeitos registrados (BUG-20260929-J6PQ e BUG-20261002-T4ZM) e o único cuja correção precisou
   ser refeita. A lista branca `_LABEL_SEGURO` não pode mudar de valor.

## Rede de segurança disponível

| Recurso | Situação |
|---|---|
| Suíte `tests/` | 164 passam, 15 erros de ambiente (`PermissionError` do sandbox em `tmp_path`) |
| Verificação de tipos | `pyrefly check src` reporta 27 erros. Critério: não aumentar |
| Caracterização da string Mermaid | `tests/test_characterization_mermaid.py` (goldens comparados) |
| Contrato de escape | `tests/test_mermaid_escape.py` |
| Prova por AST | usada nas transformações anteriores: corpo das funções movidas comparado por AST contra cópia congelada |

A rede exigida pelo especialista **existe** para esta oportunidade. Não é necessário criar
caracterização nova, apenas confirmar que os dois arquivos de caracterização ficam verdes antes.

## Gate de edição do legado

`.reversa/reversa-config.json` está com `allowLegacyEdits: true` e `allowedPaths` cobrindo
`src/**` e `tests/**`, que são os caminhos desta transformação. **O gate está liberado.**

## O que o especialista NÃO deve fazer

| Proibição | Motivo |
|---|---|
| Alterar o valor de `_LABEL_SEGURO` ou a ordem dos caracteres de escape | Muda a string gerada e o contrato travado pelo BUG-20261002-T4ZM |
| Mover `norm_name` ou mexer em `parsers/` | É a `OPP-20261006-LIGH`, transformação separada |
| Aplicar as duas mudanças de estado global | É a `OPP-20261006-3WR5`, e ela para no gate por falta de caracterização de concorrência |
| Reduzir o `__all__` de `path_search` sem migrar consumidor | É a `OPP-20261006-ESKO`; ver a observação 1 da costura |

## Como acionar

O especialista tem `disable-model-invocation: true`, então **esta sessão não pode invocá-lo**. O
acionamento é do usuário:

```text
/reversa-decouple OPP-20261006-ULVW
```

Sequência acordada com o usuário nesta sessão: **uma transformação por vez, parando no gate de
cada uma**.

---
*Gerado pelo Reversa-Refactor em 2026-10-06.*
