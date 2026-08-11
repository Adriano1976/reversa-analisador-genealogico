# Regression Watch — 002-integrar-rota-app-modulos

> Identificador da feature: `002-integrar-rota-app-modulos`
> Data: 2026-08-11
> Cenário: legado (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Watch principal

Nenhum watch item gerado nesta rodada: o `legacy-impact.md` não registra regras 🟢 do `domain.md` como "Modificadas" (nenhuma regra de negócio teve comportamento alterado ou removido — a mudança foi estrutural: localização do código).

## Observações

Itens sem peso de regressão (mudanças estruturais/refactor que uma futura extração deverá refletir, mas que não alteram regras 🟢):

| ID | Origem | Item | Tipo |
|----|--------|------|------|
| OBS-01 | `_reversa_sdd/architecture.md#5` (dívida técnica de acoplamento) | `app.py` deixou de conter a lógica inline duplicada; rotas delegam a `analisador-genealogico/reconstructed/`. A extração futura deve descrever o app como camada de rota fina + módulos internos. | presença |
| OBS-02 | `_reversa_sdd/reconstruction-report.md` | Módulos `upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py` agora residem em `analisador-genealogico/reconstructed/` (fora da raiz). Importante para quem ler o mapeamento de arquivos. | presença |
| OBS-03 | `_reversa_sdd/confidence-report.md` (reclassificação do Reviewer) | `HARD_MIN=92` / `GIVEN_MIN=90` como código morto foi preservado nos módulos reconstruídos (declarados, não usados) — comportamento idêntico ao legado. | confidência |

## Histórico de re-extrações

*(Vazio — será preenchido quando `/reversa` rodar novamente sobre o código atualizado.)*

## Arquivadas

*(Vazio.)*
