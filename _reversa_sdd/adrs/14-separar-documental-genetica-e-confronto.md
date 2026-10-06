# ADR-14 — Separar parentesco documental, evidência genética e confronto

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-10-04
- **Commit(s):** `7bf2676` (separa os módulos), `cd8d7f3` (orquestra as três etapas), `a4d24df` (apresenta as quatro seções), `2c0ba40` (cobre a regra com dez cenários)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

No sistema anterior (e em toda a documentação produzida até 2026-09-30), o cM e o GEDCOM se misturavam em um único fluxo: o cM era traduzido em "relação prevista" por **faixas escritas à mão**, e esse rótulo era apresentado ao lado do caminho genealógico como se fosse uma conclusão. O usuário via **"Relacionamento Provável (DNA)"** — quando era **o cM decidindo parentesco**, e não a árvore.

Essa é a decisão de negócio mais consequente do sistema, porque a genealogia genética tem uma armadilha conhecida: uma quantidade de DNA compatível **não prova** um caminho, e um caminho documental plausível **não é confirmado** por DNA compatível.

## Decisão

Separar o fluxo em **três eixos independentes** e um **quarto que os confronta, sem alterá-los**:

1. **Parentesco documental** (`core/documentary_relationship.py`) — o que o GEDCOM afirma. **Nunca lê cM.**
2. **Evidência genética** (`core/genetic_evidence.py`) — o que o CSV informa. **Não conhece o GEDCOM.**
3. **Possibilidades** (`core/relationship_hypotheses.py`) — o cM vira **lista** de relações compatíveis pela tabela publicada.
4. **Confronto** (`core/evidence_comparison.py`) — responde **um de quatro estados**, sempre dizendo **por quê**.

**Duas proibições, declaradas literalmente no código** (`core/dna_analysis.py:16-23`), como regra "não regredir":

- O DNA **não** altera o parentesco documental.
- O cM **nunca** é usado sozinho para afirmar parentesco — nominalmente proibidos os antipadrões `if cm == faixa: parentesco = relacionamento_do_GEDCOM` e `if cm == 10.8: relacionamento = "primo de 4º grau"`.

**Consequência de produto:** o rótulo **"Relacionamento Provável (DNA)" foi removido**; o que existe é **"Possibilidades de parentesco pelo DNA"**, dentro da seção de evidência genética.

## Evidência

- `src/core/dna_analysis.py:1-31` — a docstring que enuncia a regra e as proibições.
- `src/core/evidence_comparison.py:8-29` — "este módulo não altera o parentesco documental e não corrige o GEDCOM: ele apenas compara. Um conflito vira aviso e lista de causas, nunca uma reescrita de vínculo."
- `src/core/documentary_relationship.py:10-16` — *"O GEDCOM determina o parentesco documental. O DNA não altera nada do que este módulo devolve."*
- `tests/test_confrontacao_gedcom_dna.py` — **922 linhas, 27 funções**, dez cenários de confronto.
- `templates/index.html` (525 linhas) — **quatro seções de resultado** + o confronto; antes eram bem menos.
- **Nada disso existe em qualquer artefato da extração anterior**: é a capacidade nova que **motivou esta re-extração** (`state.json` → `reextraction_2026_10_05.trigger`).

## Justificativa

A separação é o que torna o sistema **honesto sobre o que sabe**. Antes, um único número produzia uma afirmação de parentesco; agora, cada eixo declara a sua natureza e o confronto declara o **grau de concordância** entre eles, inclusive quando não há concordância nem discordância (`INCONCLUSIVO`).

## Consequências

- ✅ **O `INCONCLUSIVO` é o estado inicial de todo confronto** (`evidence_comparison.py:162`), e os ramos de guarda **retornam sem alterá-lo**: nenhum estado é afirmado por omissão. O caminho de falha é o caminho padrão.
- ✅ **O conflito virou informação de trabalho, não erro:** `CONFLITANTE` carrega o **rol completo de 12 causas** que o operador deve considerar (homônimo, vínculo trocado, colapso de pedigree, endogamia, agregação incorreta, falso positivo…). O código declara que **não é diagnóstico automático**.
- ⚠️ **A separação criou superfície de compatibilidade:** `get_relationships_by_cm` e `SHARED_CM_DATA` **continuam existindo e reexportados**, porque a suíte os exercita — mas o **fluxo e a interface não os usam mais** (ADR-19).
- 🔴 **Nada disso tem adendo no ciclo forward.** As features registradas em `_reversa_forward/` param na `004`; a regra final foi implementada em commits diretos, **sem requisito, sem roadmap e sem adendo**. É a lacuna de rastreabilidade que esta re-extração existe para fechar.
- 🔴 **A decisão não tem registro de alternativas.** É reconstruída de código, commits e docstrings; não há prosa de decisão humana que a justifique formalmente. O que existe é a **regra escrita no código**, que é mais forte que prosa — mas não substitui a decisão.

## Alternativas consideradas

- **Manter um único fluxo e apenas renomear o rótulo.** Descartada: a armadilha não estava no nome, estava em **um número produzir uma afirmação de parentesco**.
- **Deixar o cM rebaixar o parentesco documental (marcar como improvável).** Descartada pela regra: o confronto **compara**, não reescreve. Rebaixar seria a mesma contaminação em sentido oposto.
