# ADR-34 — Quebra dos ciclos `core↔reporting` e `core↔parsers`, e remoção das superfícies de compatibilidade

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-06
- **Commit(s):** `2443273` (`OPP-20261006-LIGH`, move `norm_name`), `87bcea5` (`OPP-20261006-ULVW`, injeta o resolvedor de diagrama), `d062c20` (`OPP-20261006-ESKO`, remove a superfície do `path_search`), `16154d4` (unifica a guarda da árvore pedida pelo formulário)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `ADR-11` tinha estabelecido que `reporting/` **não é folha e não pode ser** — as decisões de layout do diagrama são decisão de negócio e moram no renderizador. Isso deixou dois **ciclos de pacote** no grafo de importação, ambos reais e nenhum deles quebrando teste:

1. **`core/` ↔ `reporting/`.** `reporting/mermaid_render.py` importava `core.family_navigation`, `core.path_finding` e `core.gedcom_state` para obter **sete consultas** de domínio. Em troca, `core/path_search.py` e `core/dna_analysis.py` o importavam.
2. **`core/` ↔ `parsers/`.** `parsers/csv_ingest.py` importava `core.erros` e — pior para o acoplamento — obtinha `norm_name` de `core/name_normalization.py`, que é **normalização de texto pura, sem domínio**.

Havia ainda um terceiro problema, de natureza diferente: **superfícies de compatibilidade** (`__all__` reexportando nomes por motivo histórico) espalhadas por vários módulos, justificadas por listas de consumidores que **não existiam**. A maior estava em `core/path_search.py`: **17 nomes**.

## Decisão

1. **Inverter a direção do dado, não mover a decisão.** `core/diagram_domain.py` passa a expor `resolvedor_de_diagrama(arvore)`, um **dict de sete funções já ligadas à árvore** por `functools.partial`. O renderizador recebe o resolvedor **por parâmetro** e **nunca mais importa `core`**. A assinatura que ele chama não mudou: ele continua chamando `get_spouses(pid)`, e não `get_spouses(arvore, pid)`.
2. **Mover o que é puro para onde é puro.** `norm_name` sai de `core/name_normalization.py` para `utils/name_keys.py`, e continua importável do lugar antigo por reexportação — mas agora **`parsers/` importa `utils/`**, e o ciclo fecha.
3. **Remover as superfícies sem consumidor.** Em `core/path_search.py`, os 17 nomes reexportados foram retirados e `__all__` passou a declarar **apenas** `path_search`. Os consumidores reais — três arquivos de teste e o harness de paridade — foram migrados para o módulo canônico.
4. **Não introduzir classe nem `Protocol` no núcleo.** O resolvedor é um `dict` de funções: o `paradigm_decision.md` manda o núcleo permanecer em funções puras e proíbe objetos com estado no cálculo.

## Evidência

- `src/reporting/mermaid_render.py` **não tem nenhum import de `core`**. O docstring declara o contrato e o motivo.
- `src/core/diagram_domain.py` (62 linhas úteis) devolve exatamente sete entradas: `get_name`, `people`, `get_spouses`, `split_path_by_marriage`, `pick_spouse_for_couple`, `exclude_tail` e `find_ancestral_path`.
- `src/utils/name_keys.py` (27 linhas úteis) contém `norm_name`; `core/name_normalization.py` a reexporta.
- `src/core/path_search.py` termina com `__all__ = ["path_search"]`, e o comentário registra os quatro consumidores que foram migrados.
- **O `RISK-011` continua coberto:** `are_spouses` e `split_path_by_marriage` existem como funções **separadas**, e `split_path_by_marriage` continua chegando ao renderizador pelo resolvedor. Nenhum cenário de matching falharia se essa decomposição desaparecesse — por isso ela tem probe diferencial dedicado.
- O resolvedor **captura a árvore recebida**, e é isso que preserva a costura sem arrastar o renderizador para a migração do `ADR-24`: ele não soube que as consultas passaram a receber a árvore.

## Justificativa

**Ciclo de pacote é acoplamento que não aparece em teste.** Nenhum dos dois ciclos quebrava comportamento — o que os torna perigosos: eles só se manifestam quando alguém tenta mover um arquivo, e aí a mudança vira uma cascata. Quebrá-los **antes** de a migração precisar foi o que permitiu o `ADR-24` mover a árvore para parâmetro sem tocar no renderizador.

**Superfície de compatibilidade sem consumidor é dívida disfarçada de cuidado.** A reexportação de 17 nomes era justificada por "consumidores" que uma varredura desmentiu: `app.py` importava apenas `path_search`, e `core/dna_analysis.py` **não importava nada** daquele módulo. Manter a superfície significa que todo leitor futuro precisa descobrir que ela não é usada.

## Consequências

- 🟢 **O núcleo ficou com dependências estritamente descendentes**, sem ciclo e sem import tardio novo.
- 🟢 **As sete consultas de domínio estão agora em um lugar nomeado**, com contrato explícito, em vez de implícitas nos imports do renderizador.
- 🟢 **A remoção da superfície do `path_search` foi o precedente** para a do `cm_estimator` (`ADR-24`), feita no dia seguinte.
- 🟡 **`reporting/` continua não sendo folha, e isso é decisão declarada** (`ADR-11`), não resíduo. Quem tentar "limpar" o grafo movendo o layout para `core/` estará revertendo o `ADR-11`.
- 🟡 **A reexportação de `norm_name` foi mantida em `core/name_normalization.py`.** É a única superfície de compatibilidade que **sobreviveu** a esta decisão, e o motivo é que ela ainda tem consumidores legítimos — mas ela precisa ser lida como exceção, e não como padrão.
