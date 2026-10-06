# ADR-19 — Declarar as heurísticas do projeto **como heurísticas**, e manter `cm_estimator` fora do fluxo

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-09-30 (resposta 5) e 2026-10-04 (rebaixamento do módulo)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Três números do sistema **parecem** publicados e **não são**:

1. As **9 faixas de cM** de `SHARED_CM_DATA`, escritas à mão, **sem fonte verificável** e — anomalia reveladora — **sobrepondo-se até 4 vezes**, o que é atípico para uma tabela derivada de percentis.
2. O **limite de 15 cM** para "segmento fraco".
3. O **grau de confiança** da lista de possibilidades (`indeterminada` / `baixa` / `muito baixa`).

O risco não é o número estar errado: é ele ser apresentado **ao lado de números publicados** (a tabela do Shared cM Project 4.0) e ser lido como se tivesse a mesma autoridade.

## Decisão

1. **As 9 faixas escritas à mão passam a ser declaradas heurística**, e não tabela canônica. O módulo que as contém (`core/cm_estimator.py`) é **rebaixado a LEGADO fora do fluxo**, mantido apenas como superfície de compatibilidade.
2. **O limite de 15 cM é critério do projeto**, declarado como tal no próprio código, e a tela deve apresentá-lo assim.
3. **A confiança da lista é heurística do projeto** — porque a fonte **não define** grau de confiança —, declarada no código e no resultado.

## Evidência

- `_reversa_sdd/questions.md#pergunta-5` — resposta do usuário: *"escritas à mão — declarar como heurística"*.
- `src/core/cm_estimator.py:1` — `"""Estimador de parentesco por faixas de cM — LEGADO, fora do fluxo.` e `:21` — *"determina declará-las como heurística, não como tabela canônica"*.
- `src/core/dna_analysis.py:25-30` — **"o fluxo e a interface NÃO os usam mais"**; continuam reexportados porque `tests/test_dna_analysis.py` os exercita.
- `src/core/genetic_evidence.py:31` — `LIMITE_SEGMENTO_FRACO = 15.0`, com "Critério do projeto, não da fonte" em `code-analysis.md` §3.6.
- `src/core/relationship_hypotheses.py:140-158` — 0 candidatas → `indeterminada`; 1 a 3 → `baixa`; 4 a 6 → `muito baixa`; mais de 6 → `muito baixa`; com a leitura de que **quanto mais relações contêm o valor, menos o valor discrimina**.
- **Verificação por varredura de imports:** quem importa `cm_estimator` é o `__all__` de `dna_analysis`, o harness de paridade e a suíte de testes — **não** o fluxo nem a interface.

## Justificativa

Um número sem fonte que é apresentado como se tivesse fonte **não é imprecisão, é desinformação**: o operador calibra a confiança dele no resultado a partir de uma autoridade que não existe. Declarar a origem é mais valioso do que o número em si.

**Por que manter o módulo em vez de removê-lo.** Diferente das entidades decorativas removidas no ADR-09, aqui existe **superfície de compatibilidade real**: o harness de paridade e a suíte dependem dele, e removê-lo quebraria a verificação. É a diferença entre **código morto sem consumidor** (remover) e **código legado com consumidor de verificação** (declarar e isolar).

## Consequências

- ✅ **A autoridade dos números caiu; a mecânica permaneceu.** `BR-D-62` segue 🟢 no que é **mecânica** (a função devolve **lista**; `cM ≤ 0` ou não numérico devolvem **lista vazia**; o literal de relação distante só aparece com valor **positivo** fora de todas as faixas). O que caiu foi o valor probatório das faixas.
- ✅ **`L-07` fechada** (fonte das faixas de cM) em `domain.md` da extração de 2026-09-30.
- ⚠️ **Ficou pendente, e continua pendente:** `LIMITE_SEGMENTO_FRACO` **é heurística do projeto apresentada ao lado de números publicados**, e a verificação de que a tela a apresenta como tal é da **interface**, não do módulo. Nenhum artefato desta rodada confirma essa apresentação.
- 🔴 **Risco residual declarado:** as faixas continuam **acessíveis por importação** e são reexportadas por `dna_analysis`. Um reimplementador pode encontrá-las pelo `__all__` e tratá-las como canônicas **apesar** do docstring — a defesa é textual, não estrutural.

## Alternativas consideradas

- **Remover `cm_estimator` completamente.** Descartada: quebraria o harness de paridade e a suíte, ou seja, destruiria verificação para ganhar limpeza.
- **Corrigir as faixas com dados da fonte.** Descartada nesta rodada: a tabela publicada já está implementada em `relationship_hypotheses.py` e é ela que o fluxo usa. Recalibrar as faixas antigas seria trabalho sem consumidor.
