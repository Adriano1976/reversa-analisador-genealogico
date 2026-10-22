# Actions: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/043-tabela-do-antepassado-comum/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 6 |
| Paralelizáveis (`[//]`) | 3 |
| Maior cadeia de dependência | 4 (T001 → T002 → T003 → T005) |

## Fase 1, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Mover a série de graus para `core.graus_de_parentesco` (sem import nenhum) e acrescentar o plural `bisavós` | - | `[//]` | `src/core/graus_de_parentesco.py`, `src/core/documentary_relationship.py` | 🟢 | `[X]` |
| T002 | Ligar cada relação publicada ao par de graus do antepassado comum e calcular a posição do valor na faixa | T001 | - | `src/core/relationship_hypotheses.py` | 🟢 | `[X]` |

## Fase 2, Apresentação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Trocar a lista do bloco 3 por tabela de quatro colunas, com a barra da faixa e o rodapé do sentido da ordem | T002 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T004 | Estilos da tabela, da barra da faixa e do rótulo da posição | T003 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |

## Fase 3, Verificação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Cobrir a ida e volta dos graus, o plural, as cinco posições, o payload e a proibição da probabilidade; e a tabela na tela | T003 | `[//]` | `tests/test_mrca_e_posicao_na_faixa.py`, `tests/test_tabela_do_bloco_3.py`, `tests/test_rotulos_de_parentesco.py` | 🟢 | `[X]` |
| T006 | Rodar a suíte completa e conferir na análise real | T005 | - | — | 🟢 | `[X]` |

## Notas de execução

- **T001:** o módulo novo nasceu **sem import nenhum** (só `from __future__`), e há teste que falha
  se ele ganhar um. A razão é concreta: `core.relationship_hypotheses` é importado no caminho da
  leitura do CSV e precisa do plural `bisavós`; importar `documentary_relationship` de lá arrastaria
  `path_finding` e `networkx`. `documentary_relationship` reexporta `nome_do_grau`, e `_ROMANO`
  virou `ROMANO` (público no módulo novo) — nenhuma palavra mudou de forma.
- **T001 (efeito colateral medido):** `nome_do_grau(1)` devolvia `avô/avó` pelo ramo `graus <= 2`;
  passou a devolver `pai/mãe`. Nenhum chamador usava o grau 1 (`documentary_label` trata `(0,1)`
  com o literal `Pai/Mãe ↔ Filho(a)`), e os 53 casos de `test_rotulos_de_parentesco.py` seguem verdes.
- **T002:** `GRAUS_ATE_O_MRCA` tem **24** entradas — as mesmas 24 que a varredura de (0,0) a (12,12)
  consegue derivar de `documentary_label` — e `GRAUS_DAS_MEIAS_RELACOES` tem as **3** restantes
  (`HALF_SIBLINGS`, `HALF_1C`, `HALF_2C`), que `documentary_label` não produz porque o grau delas é o
  do equivalente completo. O teste de ida e volta fecha as 24: os graus daqui devolvem a mesma chave
  lá. **Zero divergências.**
- **T002 (o plural):** `avô` faz `avós`, e não `avôs`: o plural está escrito na tabela, na terceira
  coluna, e há teste que procura `ôs` para pegar a tentação do `+ "s"`.
- **T003:** a tabela tem quatro colunas (`Relação`, `Faixa na fonte`, `Onde o valor cai`,
  `Antepassado comum mais recente`) e o rodapé diz duas coisas que faltavam: o sentido da ordem
  (que já existia no núcleo e era invisível) e que o antepassado comum é **definição**, não
  estatística. O aviso amarelo do rodapé não mudou.
- **T003 (decisão registrada):** a coluna `Probabilidade` da referência do operador foi **recusada**.
  A 4.0 não publica probabilidade por relação; os percentuais somariam 100% e fechariam o mundo num
  conjunto que o projeto recusa fechar (`1C6R`, `3C2R` e companhia ficam de fora); e na profundidade
  real do caso — 9 a 51 cM — a lista tem **13 a 15** relações, então o maior percentual seria lido
  como resposta. `posicao_na_faixa` ocupa o lugar sem inventar número.
- **T004:** a barra usa `left` inline com o percentual calculado no núcleo (0 a 100, preso nas pontas
  por `min`/`max`), e há teste de que um valor fora da faixa não estoura a barra.
- **T005:** 68 casos novos — 40 em `test_mrca_e_posicao_na_faixa.py`, 8 em `test_tabela_do_bloco_3.py`
  e 20 no plural dentro de `test_rotulos_de_parentesco.py`.
- **T006:** suíte completa em **1548 passed, 9 skipped** (1.557 coletados). `SHA_DA_TELA` **inalterado**
  — a mudança só alcança o bloco de resultados, e `test_icone_de_atalho` segue verde.

## Conferência na análise real

`Adriano_Santos_v3_tratado.ged` (19.403 pessoas) + `Famílias_Sergipanas.csv` (617 linhas), raiz
`Adriano Santos`:

| Medida | Valor |
|---|---:|
| Cartões | **68** |
| Descartes | **448** |
| Cartões com possibilidades | **68** |
| Linhas de tabela na página | **919** |
| Carga da árvore | 71,5 s |
| Análise | 31,0 s |
| HTML servido | 3.888.456 caracteres |

Os 68 cartões e 448 descartes são **os mesmos** da 039 e da 040: a 043 não mexe em aceitação, ordem
nem contagem. Nas 919 linhas: **0** sem antepassado comum; **514** (56%) têm dois lados ou
meia-relação, que é exatamente o caso em que a coluna precisa mostrar dois números.

Linhas por bloco — a razão de a tabela ter sido recusada *com percentual*:

```
 9 linhas x  1      13 linhas x 32
11 linhas x  2      14 linhas x 15
12 linhas x  3      15 linhas x 14
                    16 linhas x  1
```

Posição do valor na faixa (919 linhas): 386 `na ponta inferior`, 385 `abaixo do centro`, 98 `no
centro`, 41 `acima do centro`, 9 `na ponta superior`. A maioria na metade de baixo é a leitura
honesta do arquivo: metade dos pares está em ~9 cM, e a faixa publicada das relações distantes
começa em 0.

Custo das duas colunas, medido à parte: **~8 ms** nas 919 linhas, contra os 31 s da análise inteira
— a diferença de tempo em relação à 040 (12,7 s) é do ambiente, não da feature.

Amostras do que o cartão passou a dizer:

```
Maria Candida de Jesus / kit BN8387325 / 15,1 cM
   Primos de 7º grau           0-57   26% abaixo do centro   heptavós     | 8 gerações acima, nos dois lados
   Primos de 6º grau           0-71   21% abaixo do centro   hexavós      | 7 gerações acima, nos dois lados

Clezia Santos / kit AZ4078391 / 154,5 cM
   Primos de 2º grau (1× removido)  14-353  41% no centro   bisavós e trisavós  | 3 e 4 gerações acima
   Meio-primos de 2º grau           10-325  46% no centro   bisavós (um de dois) | ... só um dos bisavós é compartilhado
```

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-code-express` | reversa |
| 2026-10-22 | Execução: 6/6 ações concluídas | reversa |
