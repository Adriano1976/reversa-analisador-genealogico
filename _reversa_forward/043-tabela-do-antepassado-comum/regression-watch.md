# Regression watch: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/core/relationship_hypotheses.py` (`GRAUS_ATE_O_MRCA`) | Os graus de cada relação continuam devolvendo a **mesma chave** em `documentary_label` | ida e volta | uma relação passa a apontar para o grau de outra, e o cartão diz "trisavós" onde deveria dizer "bisavós" |
| W002 | `src/core/relationship_hypotheses.py` (`GRAUS_DAS_MEIAS_RELACOES`) | As três meias-relações ficam **fora** de `GRAUS_ATE_O_MRCA` e mantêm "(um de dois)" e a nota de compartilhamento | presença | `HALF_1C` entra na tabela dos graus completos e perde a ressalva |
| W003 | `src/core/relationship_hypotheses.py` e `src/templates/index.html` | Nenhuma candidata carrega probabilidade, e a tela não exibe a palavra `Probabilidade` | ausência | a coluna de percentual volta, ou aparece uma chave `probability`/`probabilidade` no payload |
| W004 | `src/core/graus_de_parentesco.py` | O módulo continua **sem import** além de `from __future__ import annotations` | presença/ausência | ele passa a importar `networkx` por tabela, e o caminho do CSV arrasta o grafo |
| W005 | `src/templates/index.html` (bloco 3) | A tabela mantém as quatro colunas e a frase que diz que o antepassado é definição, não estatística | presença | o rodapé some e a coluna passa a ser lida como se fosse medida da fonte |
| W006 | `src/templates/index.html` (bloco 3) | Sem candidata publicada, o cartão **não** renderiza tabela | presença/ausência | aparece uma tabela vazia com cabeçalho só |
| W007 | `src/core/documentary_relationship.py` | `nome_do_grau` continua importável **deste** módulo (reexportação) | presença | quem importava daqui quebra, e `test_rotulos_de_parentesco.py` falha na importação |

## Observações (sem peso de regressão)

- 🟢 **A redação é do projeto, não da fonte:** `avós e trisavós`, `na ponta inferior`,
  `um de dois` — nenhuma dessas frases é terminologia publicada, e as palavras podem
  mudar sem que a regra mude.
- 🟡 **Os cortes da posição (15/40/60/85%) são escolha do projeto.** A fonte não define
  "centro" de faixa; os cinco rótulos existem para o operador ver o que a lista
  escondia, e não para medir probabilidade. Mudar os cortes não muda parentesco.
- 🟡 **`nome_do_grau(1)` passou a devolver `pai/mãe`** (antes caía no ramo `graus <= 2`
  e devolvia `avô/avó`). Nenhum chamador usava o grau 1 — `documentary_label` trata
  `(0,1)` com o literal `Pai/Mãe ↔ Filho(a)` —, então a correção não altera rótulo de
  cartão nenhum.
- 🟡 **A coluna do antepassado é a única sem fonte externa no bloco 3.** Ela não
  envelhece com a versão 5.0 do Shared cM Project; o que envelhece é `SCP40_ROWS`.
- 🟡 **`meioses` das linhas de primos não é o mesmo número de `documentary_label`.**
  Achado durante a investigação desta feature, **não tratado**: `1C` guarda 2 na tabela
  e `documentary_label(2,2)` devolve 4. Só alcança o caminho de envoltória por meioses,
  usado nas relações não publicadas (`1C6R` e companhia), onde a janela sai deslocada
  para mais fundo. Requer decisão humana.
