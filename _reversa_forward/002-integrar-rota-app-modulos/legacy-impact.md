# Legacy Impact — 002-integrar-rota-app-modulos

> Data: 2026-08-11
> Feature: `002-integrar-rota-app-modulos`
> Âncora: `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `analisador-genealogico/app.py` | Roteamento Flask (architecture.md#2) | regra-alterada | HIGH | Todas as ~35 funções/constantes de lógica (matching, mermaid, cM, helpers de nome) removidas do app.py; as rotas agora delegam aos módulos movidos. |
| `reconstructed/*.py` → `analisador-genealogico/reconstructed/*.py` | Módulos de lógica (reconstruction-report.md) | componente-novo | MEDIUM | Módulos promovidos da raiz para dentro do pacote da aplicação. |
| `tests/test_upload.py`, `tests/test_path_search.py`, `tests/test_dna_analysis.py`, `tests/test_domain.py` | Suíte de testes (inventory.md#6) | regra-alterada | LOW | `sys.path` atualizado para apontar ao novo local dos módulos; nenhum teste alterado em conteúdo. |

## Diff conceitual por componente

### Roteamento Flask — `app.py`

O `app.py` (887 linhas) foi reduzido a uma camada de rota fina (~70 linhas). A lógica duplicada inline foi integralmente removida:
- Helpers de nome (strip_bad_utf, norm_name, split_name_pt, etc.) → agora vivem em `dna_analysis.py`.
- Geração de Mermaid (direct + indirect bridge) → agora em `path_search.py`.
- Tabela de faixas de cM (`SHARED_CM_DATA`) → agora em `dna_analysis.py`.
- Parsing do GEDCOM e construção do grafo → agora em `upload.py`.

As rotas `upload_gedcom`, `path_search` e `dna_analysis` mantêm o mesmo contrato de renderização com `templates/index.html` (mesmas variáveis Jinja2, mesmas mensagens de sucesso/erro). Comportamento observável idêntico, validado por smoke test de ponta a ponta (GET, upload, path_search feliz+erro, dna_analysis feliz+erro).

### Módulos de lógica — movimentação

`reconstructed/` foi movido de `analisador-genealogico/` (pacote da aplicação), preservando imports relativos internos. A pasta raiz `reconstructed/` deixou de existir; os testes atualizam o `sys.path` para o novo local.

## Preservadas

Regras 🟢 do `domain.md` que continuam intactas:

- **2.1** Relação prevista por faixa de cM (`SHARED_CM_DATA`) — intacta (agora em `dna_analysis.py`).
- **2.3** Regras de namespace de nome / matching viral — intactas (agora em `dna_analysis.py`).
- **2.4** Limites de busca (ancestral 20, indireta 40 hops) — intactos (agora em `path_search.py`).
- **3** Regras de decisão e fluxo (DNA Analysis, Path Search, descartados) — intactas; os fluxos foram revalidados via smoke test.

## Modificadas

Nenhuma regra 🟢 do `domain.md` foi alterada ou removida em comportamento. A mudança é estrutural (localização do código), não semântica.
