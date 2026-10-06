# ADR-01 — Reconstruir o sistema em módulos, sem reescrever o legado

- **Status:** Aceito e **superado em forma** (o monolito deixou de ser o objeto de trabalho; a decisão de método permanece vigente)
- **Data da decisão:** 2026-08-03 a 2026-08-07
- **Commit(s):** `6b6483d` (2026-08-03, inicialização), `d2ea17a` e `5ee57c9` (2026-08-07, módulos com testes)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O sistema legado era um **monolito Flask de ~887 linhas** em um único `app.py`, com rotas, regras de domínio, leitura de arquivo e formatação de tela convivendo no mesmo arquivo, e **sem nenhum teste**. Reimplementar sem referência de comportamento perderia décadas de decisões de negócio enterradas em condicionais.

## Decisão

Extrair o núcleo em **módulos independentes e testáveis** (`domain.py`, `upload.py`, `path_search.py`, `dna_analysis.py`), como **reconstrução fiel** do comportamento observado, **sem editar o monolito**. O comportamento do legado é a especificação; o código novo é o candidato.

## Evidência

- `_reversa_sdd/oracle/ORACLE_MANIFEST.md` — a política de não tocar no monolito é o que **permitiu** congelá-lo depois.
- `_reversa_sdd/reconstruction-plan.md` e `reconstruction-report.md`.
- `_reversa_sdd/migration/parity_harness.md` — a paridade só pôde ser provada porque havia **dois** artefatos: o legado intocado e a reconstrução.

## Justificativa

A diretiva não-destrutiva do Reversa e a decisão explícita de usar o legado como **referência de comportamento**, e não como código a corrigir. Reconstruir em módulos também torna cada regra de negócio **testável isoladamente** — o que o monolito não permitia.

## Consequências

- **A consequência mais importante foi não planejada:** manter o monolito intacto viabilizou o **oráculo congelado** (ADR-04) e, com ele, a prova de **paridade 100%** e a descoberta de `DIV-001` — a única divergência de comportamento real entre legado e reconstrução.
- O monolito **já não existe como código vivo**: a raiz virou `src/` (ADR-10). O que resta é a **cópia congelada, somente leitura**, em `_reversa_sdd/oracle/app_legacy_e43ca22.py`.
- Custo assumido: passaram a existir **dois** artefatos a manter em mente, com o risco de validação circular que só foi tratado no ADR-04.

## Alternativas consideradas

- **Editar o monolito diretamente.** Descartada: misturaria correção com extração e destruiria a referência de comportamento.
- **Reescrever do zero a partir das specs.** Descartada pela lição registrada no `ORACLE_MANIFEST.md`: *"a spec do legado não era oráculo; o código era"* — seis agentes e sete portões humanos operaram sobre specs e deixaram passar um erro factual que a primeira execução do oráculo desmentiu.
