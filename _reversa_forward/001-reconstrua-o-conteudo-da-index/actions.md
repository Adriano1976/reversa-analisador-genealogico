# Actions: reconstrua o conteudo da index.html

> Identificador: `001-reconstrua-o-conteudo-da-index`
> Data: `2026-08-11`
> Roadmap: `_reversa_forward/001-reconstrua-o-conteudo-da-index/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 4 |
| Paralelizáveis (`[//]`) | 0 |
| Maior cadeia de dependência | 4 |

## Fase 1, Preparação

*(Nenhuma ação)*

## Fase 2, Testes

*(Nenhuma ação)*

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Reconstruir estrutura base do HTML (Bootstrap 5 CDN) e formulário inicial de GEDCOM | - | - | `analisador-genealogico/templates/index.html` | 🟢 | `[X]` |
| T002 | Estruturar abas (Path Search / DNA Analysis) e blocos condicionais do Jinja2 para exibir os resultados | T001 | - | `analisador-genealogico/templates/index.html` | 🟢 | `[X]` |
| T003 | Atualizar o script de inicialização do Mermaid para incluir `securityLevel: 'strict'` | T002 | - | `analisador-genealogico/templates/index.html` | 🟢 | `[X]` |

## Fase 4, Integração

*(Nenhuma ação)*

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Adicionar lógica visual de spinner de loading (feedback) durante a submissão dos formulários | T003 | - | `analisador-genealogico/templates/index.html` | 🟢 | `[X]` |

## Notas de execução

- T001, T002 e T004 já estavam implementados no `templates/index.html` existente; verificados contra os critérios e marcados como concluídos.
- T003: único delta real aplicado — Mermaid `securityLevel` alterado de `'loose'` para `'strict'` (index.html:182), conforme D-02 do roadmap.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-to-do` | reversa |
