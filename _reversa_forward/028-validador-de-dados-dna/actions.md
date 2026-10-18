# Actions: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Roadmap: `_reversa_forward/028-validador-de-dados-dna/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 19 |
| Paralelizáveis (`[//]`) | 5 |
| Maior cadeia de dependência | 12 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar `data_imprecisa(texto)` público em `janela_de_vida.py`, reutilizando `_e_imprecisa`, e incluí-lo em `__all__`; nenhum comportamento existente muda | - | `[//]` | `src/core/janela_de_vida.py` | 🟢 | `[X]` |
| T002 | Criar `tests/fixtures/arvore_com_datas.py` com três GEDCOMs sintéticos: linha válida com datas completas, doador vivo com MRCA de 1650 e linha sem data; nenhum nome ou kit real | - | `[//]` | `tests/fixtures/arvore_com_datas.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever os testes de `estimar_mrca`: prioridade para `mrca_do_kit`, mediana SCP40 ÷ 2, janela por meioses, fallback de 25 anos e ausência de cM | - | `[//]` | `tests/test_validator.py` | 🟢 | `[X]` |
| T004 | Escrever os testes de `validar_comparacao` para os três status e para os códigos críticos de temporalidade (salto, MRCA posterior, idade por lado, cM × profundidade, MRCA fora da janela e doador vivo) | T003 | - | `tests/test_validator.py` | 🟢 | `[X]` |
| T005 | Escrever os testes de borda: data ausente, data estimada, sem cobertura de cM, sem caminho, afinidade, múltiplos kits, precedência e `SEM_EVIDENCIA` | T004 | - | `tests/test_validator.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Criar `src/core/validator.py` com constantes, `ComparacaoParaValidar`, `MrcaEstimado`, helpers de código/motivo e `__all__` | T001 | - | `src/core/validator.py` | 🟢 | `[X]` |
| T007 | Implementar `estimar_mrca` com prioridade para `mrca_do_kit`, mediana SCP40 ÷ 2, janela por meioses e fallback de 25 anos | T006 | - | `src/core/validator.py` | 🟢 | `[X]` |
| T008 | Implementar as checagens temporais por salto e por lado: 12–70, MRCA posterior ao descendente e códigos correspondentes | T007 | - | `src/core/validator.py` | 🟢 | `[X]` |
| T009 | Implementar a coerência cM × profundidade e o confronto do MRCA documentado com a janela estimada, com tolerância de 2 meioses/2 gerações e data estimada como atenção | T008 | - | `src/core/validator.py` | 🟡 | `[X]` |
| T010 | Implementar a precedência dos três status, a condição estrita de `VALIDADO`, a checagem de doador vivo e a ordenação/deduplicação dos códigos | T009 | - | `src/core/validator.py` | 🟢 | `[X]` |
| T011 | Implementar `agregar_resultados` com pior status entre kits, resumo por status e `SEM_EVIDENCIA` para lista vazia | T010 | - | `src/core/validator.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Criar `src/application/validacao.py` com `DependenciasDeValidacao`, `intervalo_de_geracao_mediano(arvore)` e resolução da raiz pelo nome | T011, T002 | - | `src/application/validacao.py` | 🟢 | `[X]` |
| T013 | Implementar a carga de `validar_arquivos`: `carregar_arvore` uma vez, leitura do CSV, `build_genetic_evidence` e `match_candidates` por kit | T012 | - | `src/application/validacao.py` | 🟢 | `[X]` |
| T014 | Completar `validar_arquivos`: montar `ComparacaoParaValidar` por kit, chamar `validar_comparacao` e agregar o resultado | T013 | - | `src/application/validacao.py` | 🟢 | `[X]` |
| T015 | Criar `tests/test_validacao_de_arquivos.py` com GEDCOM/CSV sintéticos: um kit, múltiplos kits, ausência de evidência, afinidade e parse único da árvore | T014, T002 | - | `tests/test_validacao_de_arquivos.py` | 🟢 | `[X]` |
| T016 | Criar `tests/test_fronteira_do_validador.py` garantindo que `core/validator.py` não importa `parsers`, `application`, `reporting` nem a borda HTTP | T012 | - | `tests/test_fronteira_do_validador.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Completar as docstrings de `core/validator.py` com as fórmulas, os limiares 12–70/122/25 e as fontes SCP 4.0/Fenner | T011 | `[//]` | `src/core/validator.py` | 🟢 | `[X]` |
| T018 | Completar as docstrings de `application/validacao.py` com o fluxo de leitura, a política de raiz e a reutilização do legado | T013 | `[//]` | `src/application/validacao.py` | 🟢 | `[X]` |
| T019 | Rodar a suíte completa no `.venv`, conferir `git status`/`git diff --stat` e confirmar que `app.py`, template, CSS, `init.sql`, `requirements.txt` e banco não mudaram | T015, T016, T017, T018 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

> Reservado para o `/reversa-coding` registrar avisos ou observações surgidos durante a execução.
> Não use este espaço para corrigir ações.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-to-do` | reversa |
