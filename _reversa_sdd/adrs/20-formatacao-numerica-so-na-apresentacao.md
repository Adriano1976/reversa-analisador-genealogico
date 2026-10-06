# ADR-20 — Formatação numérica: autoridade única e **somente** na apresentação

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10-04
- **Commit(s):** `07d53fd` — "fix(dna): formata o total de cM e corrige a politica de escrita no README"
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `BUG-20261004-EWSJ` registra um defeito visível: o **badge de cM na tela exibia ruído de ponto flutuante** — o clássico `19.200000000000003` nascendo da soma de segmentos. O defeito é de **apresentação**, mas a tentação natural de corrigi-lo seria arredondar **no núcleo**, onde o valor é somado.

Fazer isso mudaria o valor usado nas comparações e quebraria a **paridade exata** com o oráculo congelado (ADR-04), que é a métrica primária do projeto.

## Decisão

1. **O núcleo NUNCA arredonda.** A soma de cM permanece o float exato.
2. **O arredondamento acontece SOMENTE na apresentação**, e a autoridade única disso é `src/utils/number_format.py` (`formatar_cm`, `formatar_inteiro`), exposta ao template por **filtros** Flask (`cm_br`, `inteiro_br`).

## Evidência

- `src/app.py:34-37` — o comentário nomeia o bug e declara que **"a regra mora em `utils/number_format.py`, que é a autoridade única"**.
- `src/utils/number_format.py` — `CASAS = 2` é **teto** de casas decimais, não formato fixo.
- `src/core/genetic_evidence.py:162-166` — `registrada["total_cm"] + cm`, **sem `round`**.
- `tests/test_formatacao_cm.py` — o contrato está **congelado**: o float somado permanece exato (`19.200000000000003`) porque a paridade contra o oráculo exige **igualdade exata**.
- `_reversa_bugs/analise-dna/bugs/BUG-20261004-EWSJ-badge-de-cm-com-ruido-de-ponto-flutuante/` — reprodução com captura de tela, três change sets, portões de teste e paridade.

## Justificativa

**A separação entre valor e exibição é a condição da paridade.** O harness compara **estruturas serializadas com igualdade exata**; um único `round` no núcleo introduziria divergência sistemática contra o oráculo em toda análise com segmentos fracionários. O defeito era **visual**, e a correção tinha de ser **visual** — corrigi-lo no núcleo seria trocar um defeito cosmético por uma divergência funcional.

## Consequências

- ✅ **Paridade preservada** e defeito visual corrigido — os portões do bug registram teste falhando **antes** e passando **depois**, mais a verificação de paridade.
- ✅ **Passa a existir uma única autoridade de formato numérico.** Antes, o formato era decidido no template; agora, o template **pede o filtro** e não decide nada.
- 🟢 **Detalhe de contrato:** `CASAS = 2` é **teto**, e não número fixo — `formatar_cm` não força duas casas em valor inteiro.
- ⚠️ **A lição generaliza para quem reimplementar:** em um sistema cujo contrato é **igualdade exata** contra um oráculo, **toda** transformação de valor precisa ser justificada — e "arredondar para ficar bonito" é a transformação mais fácil de introduzir sem perceber. O código protege isso com um teste de contrato dedicado, e não com um comentário.

## Alternativas consideradas

- **Arredondar no núcleo e ajustar o harness.** Descartada: mudaria o comportamento funcional para corrigir um defeito de tela e enfraqueceria a métrica de paridade, que é a única prova objetiva do projeto.
- **Formatar no template, com `format` inline.** Descartada: foi o que produziu o bug, e não havia autoridade única.
