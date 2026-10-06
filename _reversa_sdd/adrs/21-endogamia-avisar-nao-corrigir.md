# ADR-21 — Endogamia e colapso de pedigree: avisar, não corrigir

- **Status:** Aceito e vigente — ✅ **CONFIRMADO pelo usuário em 2026-10-05** (`questions.md#pergunta-7`): avisar é suficiente, sem rebaixar o veredito
- **Data da decisão:** 2026-10-04 (implícita na construção do confronto)
- **Commit(s):** `7bf2676`
- **Confiança:** 🟢 CONFIRMADO para a decisão; 🟡 para a intencionalidade

## Contexto

A fonte estatística usada pelo confronto — o **Shared cM Project 4.0** — **declara** que suas estatísticas *"não atendem colapso de pedigree ou endogamia"*. Em uma árvore com colapso (o mesmo ancestral alcançado por mais de uma cadeia de pais), o cM esperado é **inflado**, e uma leitura ingênua do valor tende a **subestimar** a distância real entre as duas pessoas.

O sistema novo tem como detectar colapso no lado **documental** — e o faz.

## Decisão

**Detectar e avisar no lado documental; NÃO corrigir o valor genético nem alterar o veredito.**

1. O lado documental detecta colapso por **contagem de cadeias** até o mesmo ancestral (teto de **8** cadeias) e emite o aviso `colapso_de_pedigree`, nomeando o ancestral e o número de cadeias.
2. O lado do confronto **lista** "colapso de pedigree" e "endogamia" entre as **causas possíveis** de conflito — na lista de 12 causas de `CONFLITANTE` e no subconjunto de 9 de `POSSIVEL`.
3. **O veredito não é alterado pelo aviso de colapso.**

## Evidência

- `src/core/documentary_relationship.py:361-382` e `:527-539` — o cálculo e o aviso, com teto `LIMITE_DE_CADEIAS = 8`.
- `src/core/documentary_relationship.py:538` — o texto declara o efeito: *"Isso infla o cM esperado e enfraquece a leitura do valor compartilhado."*
- `src/core/evidence_comparison.py:55-68` — `CAUSAS_POSSIVEIS` inclui **"colapso de pedigree"** e **"endogamia"**.
- `src/core/relationship_hypotheses.py:48-58` — `SCP40_META` registra a limitação declarada pela fonte.

## Justificativa

**Corrigir exigiria um modelo que o projeto não tem.** Não há coeficiente de endogamia, pedigree completo confiável nem base para calcular o **fator de inflação**. Aplicar uma correção aproximada introduziria um número inventado no ponto mais sensível do sistema — exatamente o que o ADR-15 proíbe ao recusar inventar faixas para relações não publicadas.

**Avisar é a resposta honesta:** o operador é informado de que aquele valor é um **teto otimista**, e a decisão fica com quem conhece a árvore.

## Consequências

- 🟢 **O aviso é acionável e específico:** nomeia o **ancestral** e **quantas cadeias** o alcançam, não apenas "possível endogamia".
- ⚠️ **O aviso vive em paralelo ao veredito, e não dentro dele.** Um caso com colapso detectado pode sair `COMPATIVEL` **sem** que o estado reflita a ressalva. O `state-machines.md` §3.2 registra isso: nenhuma transição de estado considera o colapso.
- 🔴 **A detecção tem teto, e o aviso não distingue os dois motivos de ausência.** `_cadeias_ate` sobe por pais com teto de **12**, então colapso além desse teto **não é detectado** — e o silêncio é idêntico a "não há colapso".
- 🔴 **Endogamia não é detectada, apenas listada como causa.** Diferente do colapso, não há nem contagem de cadeias: a palavra aparece na lista de causas e em nenhum cálculo.
- 🔴 **`L-17` em `domain.md` §7 permanece aberta:** não há decisão humana registrada sobre se avisar é suficiente. É a diferença entre uma **decisão** e uma **consequência aceita por omissão** — e a confiança desta ADR é 🟡 exatamente por isso.

## Alternativas consideradas

- **Aplicar fator de correção por número de cadeias.** Descartada: seria um número inventado com aparência de rigor.
- **Suprimir ou desqualificar o veredito quando há colapso.** Descartada na prática: o colapso é detectado **antes** do confronto estar montado, e rebaixar tudo para `INCONCLUSIVO` tornaria o estado inútil nas árvores reais deste repositório, que têm colapso.
- **Não detectar e apenas listar como causa.** Descartada: a contagem de cadeias é barata e produz aviso acionável.
