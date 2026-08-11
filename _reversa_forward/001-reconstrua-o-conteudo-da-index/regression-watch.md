# Regression Watch — 001-reconstrua-o-conteudo-da-index

> Identificador da feature: `001-reconstrua-o-conteudo-da-index`
> Data: 2026-08-11
> Cenário: legado (âncora em `_reversa_sdd/architecture.md` + `domain.md`)

## Watch principal

Nenhum watch item gerado nesta rodada: o `legacy-impact.md` não registra regras 🟢 do `domain.md` como "Modificadas" (nenhuma regra de negócio foi alterada ou removida).

> Registro de contexto: a alteração funcional desta feature (Mermaid `securityLevel: 'strict'`) é decisão de frontend/segurança (D-02), não regra de domínio, e portanto não ganha peso de regressão no watch principal.

## Observações

Itens sem peso de regressão (originalmente 🟡/🔴 ou não derivados de regra 🟢 modificada):

| ID | Origem | Item | Tipo |
|----|--------|------|------|
| OBS-01 | `_reversa_sdd/confidence-report.md` (reclassificação do Reviewer) | `HARD_MIN=92` e `GIVEN_MIN=90` em `app.py` são código morto — os limiares reais são literais nas regras A/B/C/D. Reclassificado de 🟢 para 🟡. | confidência |
| OBS-02 | `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9` | Mermaid inicializado com `securityLevel: 'strict'` no `templates/index.html` (antes `'loose'`). Não é regra de domínio; será confirmado como 🟢 numa futura re-extração sobre o código atualizado. | presença |

## Histórico de re-extrações

*(Vazio — será preenchido quando `/reversa` rodar novamente sobre o código atualizado.)*

## Arquivadas

*(Vazio.)*
