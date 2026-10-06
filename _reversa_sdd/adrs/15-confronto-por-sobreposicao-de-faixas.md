# ADR-15 — Decidir o confronto por sobreposição de faixas, e agregar pelo mais conservador

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10-04
- **Commit(s):** `7bf2676`, `2c0ba40`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Com os três eixos separados (ADR-14), faltava decidir **como** o confronto compara um cM observado com um parentesco documental que **não é um número** — é uma relação ("primos de 1º grau com uma remoção", "tio-avô"). A comparação precisa de uma **janela em cM** para cada relação.

Havia mais de um critério plausível para decidir o que fazer quando o cM cai **fora** dessa janela — e a escolha errada produziria vereditos falsos de conflito.

## Decisão

**Dois critérios, ambos explícitos:**

1. **Fora da janela → `POSSIVEL` apenas se alguma relação publicada que contém o valor tiver faixa que SE SOBREPÕE à janela documental.** Caso contrário → `CONFLITANTE`.
2. **Com mais de um kit, o estado final é o MAIS CONSERVADOR**, na ordem literal `CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`.

## Evidência

- `src/core/evidence_comparison.py:89-113` — o cálculo de sobreposição e o comentário que **registra o contraexemplo medido**.
- `src/core/evidence_comparison.py:225-227` — a ordem de conservadorismo como lista literal e a seleção do primeiro estado presente.
- `src/core/evidence_comparison.py:236-238` — o aviso em tela: *"Mais de um kit para este nome: o estado final é o mais conservador entre eles"*, com o estado **por kit**.
- `tests/test_confrontacao_gedcom_dna.py`.

## Justificativa

**Por que sobreposição, e não distância em meioses.** A intuição natural — "se as duas pessoas estão a poucas meioses de distância, o cM fora da janela é aceitável" — é **falsa**, e o código registra o contraexemplo: **irmãos (1613–3488 cM)** e **primos de 1º grau com uma remoção (102–980 cM)** estão a **uma** meioses de distância e **mesmo assim não se sobrepõem**. Distância em meioses, portanto, **não serve** como critério de tolerância.

Sobreposição de faixas é o critério correto porque tem significado estatístico direto: quando as distribuições **se tocam**, o cM **não consegue separar** as duas leituras, e afirmar conflito seria afirmar mais do que o dado permite.

**Por que o mais conservador entre kits.** Kits diferentes são evidências **independentes** sobre a mesma pessoa, e a agregação por média ou maioria permitiria que um kit conflitante fosse **diluído** por kits compatíveis — exatamente o inverso do que a regra do domínio pede (avisar antes de concluir). O mais conservador é a escolha que **preserva o alerta**.

## Consequências

- 🟢 **`POSSIVEL` é um estado largo, e isso é deliberado.** Ele cobre tanto "a genética permite, mas não confirma" quanto "está fora da janela, mas as distribuições se tocam". O detalhe por kit e a nota de qual relação vizinha acomoda o valor (**a mais próxima da média**) é o que dá ao operador a informação para julgar.
- 🟢 **O estado final pode ser mais severo que a maioria dos kits.** Um único kit `CONFLITANTE` entre cinco torna o veredito `CONFLITANTE`. É intencional, e a tela **mostra o estado por kit** para que a severidade seja auditável.
- ⚠️ **A janela herda as limitações da fonte:** a coluna *Range* do Shared cM Project exclui 1% dos envios, e a fonte **não publica mediana**. A janela **não é** o intervalo observado completo.
- 🔴 **A sobreposição não considera endogamia** — a própria fonte declara que suas estatísticas não atendem colapso de pedigree nem endogamia. Nesses casos o cM lido é um **teto otimista**, e o critério de sobreposição pode concluir `COMPATIVEL` com mais facilidade do que deveria (`L-17` em `domain.md` §7, ADR-21).
- 🔴 **Sem faixa publicada, não há veredito:** se a relação documental não é publicada na 4.0 **e** não há relação publicada com o mesmo número de meioses, o estado é `INCONCLUSIVO`. **Nenhum número é inventado** — e é justamente nas relações mais distantes que o caso real deste repositório cai (`L-18`).

## Alternativas consideradas

- **Tolerar cM fora da janela quando a distância em meioses é pequena.** Descartada pelo contraexemplo medido (irmãos × primos de 1º grau com 1 remoção, ambos a uma meioses, sem sobreposição).
- **Agregar kits pela média ou pela maioria.** Descartada: diluiria o alerta de conflito.
- **Inventar faixas para as relações não publicadas.** Descartada por princípio e implementada como envoltória de meioses: quando não há base publicada, a resposta honesta é **não ter janela**.
