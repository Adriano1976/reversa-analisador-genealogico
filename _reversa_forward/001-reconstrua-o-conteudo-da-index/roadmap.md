# Roadmap: reconstrua o conteudo da index.html

> Identificador: `001-reconstrua-o-conteudo-da-index`
> Data: `2026-08-11`
> Requirements: `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A abordagem consistirá em reconstruir o arquivo `templates/index.html` de forma fiel ao legado, utilizando Jinja2 e Bootstrap 5 via CDN. O layout será mantido: um formulário inicial para upload do GEDCOM e, após o carregamento, um sistema de abas permitindo a busca de caminhos (Path Search) ou a análise de matches de DNA (DNA Analysis). A única mudança técnica em relação ao comportamento original será o ajuste de segurança na inicialização do Mermaid.js, alterando de `loose` para `strict` para prevenir falhas de segurança (XSS).

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Segurança por Padrão | O ajuste do Mermaid para `strict` atende a premissas básicas de segurança na web. | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Manter Jinja2 + Bootstrap | Preserva compatibilidade com a arquitetura monolítica existente, reduzindo atrito e complexidade. | React, Vue | 🟢 |
| D-02 | Configurar Mermaid com `securityLevel: 'strict'` | Protege contra injeção de tags HTML maliciosas vindas dos arquivos dos usuários (GEDCOM/CSV). | `securityLevel: 'loose'` | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Não haverá mudança no backend de Python (apenas UI). | Seção 1 e 5 | Quebra de integração com as rotas do `app.py`. |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Frontend UI | `_reversa_sdd/architecture.md#2` | regra-alterada | Reconstrução da index.html com alteração de config do Mermaid. |

## 6. Delta no modelo de dados

- Resumo das mudanças: Nenhuma alteração no modelo de dados ou backend, é uma feature estritamente visual.
- Detalhe completo em: `_reversa_forward/001-reconstrua-o-conteudo-da-index/data-delta.md`

## 7. Delta de contratos externos

- n/a

## 8. Plano de migração

- n/a

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O `securityLevel: 'strict'` quebrar a formatação visual dos grafos no Mermaid | médio | médio | Testar a visualização dos grafos com nós que contêm caracteres especiais após a mudança. |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-plan` | reversa |
