# Actions: integrar a rota index() do app.py com os modulos reconstruidos

> Identificador: `002-integrar-rota-app-modulos`
> Data: `2026-08-11`
> Roadmap: `_reversa_forward/002-integrar-rota-app-modulos/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 8 |
| Paralelizáveis (`[//]`) | 1 |
| Maior cadeia de dependência | 7 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Mover os módulos `reconstructed/domain.py`, `upload.py`, `path_search.py`, `dna_analysis.py` e `__init__.py` para `analisador-genealogico/reconstructed/`, preservando os imports relativos internos (`from .upload import ...`) | - | `[//]` | `analisador-genealogico/reconstructed/*` | 🟢 | `[ ]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Atualizar os imports dos testes (`tests/test_*.py`) para apontar ao novo local dos módulos (adicionar `analisador-genealogico/` ao `sys.path` e manter `from reconstructed import ...`) | T001 | - | `tests/test_upload.py`, `tests/test_path_search.py`, `tests/test_dna_analysis.py`, `tests/test_domain.py` | 🟢 | `[ ]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | `app.py`: rota `upload_gedcom` passa a usar `reconstructed.upload.load_gedcom_and_build_graph` e remove os helpers inline de upload (grafo/nomes) | T001 | - | `analisador-genealogico/app.py` | 🟢 | `[ ]` |
| T004 | `app.py`: rota `path_search` passa a usar `reconstructed.path_search.path_search`, mantendo mensagens e contrato de `path_result` idênticos | T003 | - | `analisador-genealogico/app.py` | 🟢 | `[ ]` |
| T005 | `app.py`: rota `dna_analysis` passa a usar `reconstructed.dna_analysis.dna_analysis` com captura de `ValueError` e renderização de `message`/`success=False` | T004 | - | `analisador-genealogico/app.py` | 🟡 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | `app.py`: remover TODA a lógica duplicada restante (helpers de nome/matching, geração de Mermaid, `SHARED_CM_DATA`, constantes), deixando apenas as rotas e a renderização | T005 | - | `analisador-genealogico/app.py` | 🟢 | `[ ]` |
| T007 | Rodar a suíte de testes (esperado 47 passed) e corrigir eventuais regressões de import ou comportamento | T002, T006 | - | `tests/` | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Validar o contrato Jinja2 com `templates/index.html`: todas as variáveis (`gedcom_filename`, `message`, `success`, `all_names`, `path_result`, `dna_results`, `skipped_matches`) continuam sendo passadas pela rota | T007 | - | `analisador-genealogico/app.py` | 🟢 | `[ ]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-to-do` | reversa |
