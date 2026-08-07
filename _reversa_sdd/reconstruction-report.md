# Relatório Final de Reconstrução — teste_reversa

> Gerado pelo Reconstructor em 2026-08-07
> Fonte: **original** · Stack: Python 3 · ged4py · networkx · pandas · thefuzz · python-Levenshtein

---

## Tarefas executadas (4/4 ✅)

| # | Tarefa | Módulo | Status |
|---|--------|--------|--------|
| 01 | Entidades de Domínio | `reconstructed/domain.py` | ✅ |
| 02 | Upload GEDCOM | `reconstructed/upload.py` | ✅ |
| 03 | Busca de Caminho | `reconstructed/path_search.py` | ✅ |
| 04 | Análise de DNA | `reconstructed/dna_analysis.py` | ✅ |

## Testes — 20 passed

- `tests/test_path_search.py` (9) — TT-01..TT-05: conexão direta, indireta, pessoa inexistente, sem conexão, pessoas idênticas.
- `tests/test_dna_analysis.py` (11) — TT-01..TT-07: happy path, agregação de segmentos, encoding Latin-1, anti-falso-positivo, raiz inexistente, colunas ausentes, match sem caminho; + relação por faixa de cM.
- Fixtures GEDCOM sintéticos: `tests/fixtures/sample_gedcom.py`, `tests/fixtures/sample_dna.py`.

## Decisões de fidelidade preservadas

- Homônimos → usa o 1º ID; famílias adotivas/complexas → caminho por pais.
- Regras A/B/C/D de aceitação com limiares literais (92, 90, 86, 100).
- `HARD_MIN`/`GIVEN_MIN` mantidos como código morto (não implementados como limiar principal).
- Relaxamento de Jaccard 0.5 → 0.33 para cM ≥ 150 e dado não-genérico.
- Regex de ID de match `[A-Z]{2}\d{7}`.
- Estado global em memória (sem persistência), idêntico ao legado.

## Correções aplicadas durante a reconstrução

- `upload.py`: `load_gedcom_and_build_graph` agora muta as globais in-place (`clear` + `update`) em vez de reassigná-las. Isso mantém válidas as referências importadas por `path_search` (e `dna_analysis`) entre cargas do GEDCOM — requisito para os testes passarem com múltiplos fixtures.

## Commits

- `fa607b5` — feat: implementa modulos domain.py, path_search.py e upload.py com testes realizados
- `5af2274` — feat: implementa modulo dna_analysis.py com testes da analise de DNA

## Não aplicáveis (nível essencial / sem banco)

- Camada de API REST (Flask renderiza server-side).
- User stories / fluxos de usuário (uso local single-user).
- Máquinas de estado (sem `state-machines.md`).
- Schema de banco de dados (estado 100% em memória).

## Pendência opcional

- Baixo acoplamento: o código mantém o estado global do legado (decisão do usuário de preservar fidelidade). Um refactor futuro poderia injetar dependências (ex.: `GraphStore`), sem alterar comportamento.
