# Legacy impact: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Modo: **express**
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**` e
> `tests/**`. Todos os arquivos tocados estão dentro desses globs.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/graus_de_parentesco.py` | — | regra-nova | LOW | `geracoes_de_diferenca` e `nome_do_primo`, na folha sem import |
| `src/core/documentary_relationship.py` | `busca-caminho` | contrato-alterado | LOW | `documentary_label` usa `nome_do_primo` no ramo dos primos; reexporta a função |
| `src/core/relationship_hypotheses.py` | `analise-dna` | contrato-alterado | LOW | Nove linhas de `SCP40_ROWS` deixam de ter `name_pt` literal |
| `src/core/{profundidade_do_caminho,path_finding,janela_de_vida,dna_analysis,evidence_comparison}.py` | — | redação | LOW | Docstrings e comentários que citavam o rótulo antigo como exemplo |
| `tests/test_rotulos_de_parentesco.py` | — | contrato-alterado | LOW | Série da geração de diferença (11 casos) e a igualdade entre as duas superfícies |
| `tests/{test_confrontacao_gedcom_dna,test_tabela_do_bloco_3,test_destaque_da_hipotese,test_destaque_na_tela}.py` | — | contrato-alterado | LOW | Rótulos presos atualizados |
| `tests/fixtures/sample_dna.py` | — | redação | LOW | Comentário da fixture de 42,6 cM |

## 2. Diff conceitual

**A folha.** `geracoes_de_diferenca(1)` devolve `uma geração de diferença`; `(3)` devolve `três
gerações de diferença`. **`nome_do_primo(grau, removidos)`** compõe `Primos de 2º grau` e, quando há
diferença, acrescenta o parêntese — uma forma só, sem a oscilação de concordância que existia.

**`documentary_label`.** Deixa de montar o rótulo do primo: chama `nome_do_primo(grau, removidos)`. A
chave (`1C2R`), as meioses (total do caminho) e `degrees` **não** mudam.

**`SCP40_ROWS`.** Nove `name_pt` literais viram `nome_do_primo(n, r)`. O resto da linha — chave,
nome na fonte, meioses, média, faixa — está intocado.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.3 — o cM vira **lista**, nunca um parentesco único | a mudança é de texto; nenhuma regra de seleção ou ordem foi tocada |
| §3.3 — nenhum número inventado | as faixas, médias e meioses continuam as da fonte |
| §3.1 — a chave canônica casa documental com a tabela | `1C2R` e companhia continuam iguais, e há teste de ilha: chave → meioses → rótulo |
| §3.2 — o DNA não decide parentesco | nenhum veredito, caminho ou confronto foi tocado |
| `core/validator._meioses_totais_da_relacao` | lê a **chave**, não o rótulo — verificado no código: a mudança não a alcança |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| Texto do rótulo do primo | `(1× removido)` / `com N× remoção` → `(uma geração de diferença)` / `(N gerações de diferença)` | `src/core/graus_de_parentesco.py`, usado por `documentary_relationship` e `relationship_hypotheses` |
| Fonte do rótulo | era duplicada (tabela publicada e documental); passou a ser única | `src/core/graus_de_parentesco.py` |

> **O que NÃO mudou, e é o que mais importa:** a chave canônica, as meioses, a ordenação, o destaque,
> os vereditos do confronto e qualquer número. `core/cm_estimator.py` (legado, fora do fluxo) mantém
> os literais antigos de propósito: ele não é exibido, e é superfície de compatibilidade do harness de
> paridade.

> **Para o `/reversa-sync`:** `_reversa_sdd/domain.md#33` descreve o rótulo da relação dentro da lista
> de possibilidades; `_reversa_sdd/data-dictionary.md#62` documenta `name_pt` como "nome em português
> exibido na tela" — agora derivado, e não literal. `_reversa_sdd/busca-caminho/design.md` e
> `flowcharts/busca-caminho.md` citam o formato do rótulo do `documentary_label`.
