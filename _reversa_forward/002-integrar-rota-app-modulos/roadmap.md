# Roadmap: integrar a rota index() do app.py com os modulos reconstruidos

> Identificador: `002-integrar-rota-app-modulos`
> Data: `2026-08-11`
> Requirements: `_reversa_forward/002-integrar-rota-app-modulos/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Os módulos reconstruídos (`reconstructed/upload.py`, `path_search.py`, `dna_analysis.py`, `domain.py`) são promovidos para dentro do pacote da aplicação (`analisador-genealogico/`), e o `app.py` deixa de conter a lógica duplicada inline: cada ação do `index()` passa a importar e chamar os módulos movidos, mantendo o contrato Jinja2 com `templates/index.html` intacto. A movimentação preserva o estado global em memória (re-parse a cada `POST`) e reaproveita a suíte de 47 testes como rede de segurança.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Fonte única de verdade | Regras de matching, busca e cM passam a viver em um único lugar, com testes | respeita |
| Compatibilidade preservada | Contrato de renderização com `index.html` não muda; comportamento observável idêntico | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Mover `reconstructed/*` para `analisador-genealogico/` (subpacote `reconstructed/` ou `core/`) | Os módulos passam a fazer parte do pacote da aplicação, importáveis como pacote interno; mantém nomes de módulo já testados | Import direto mantendo `reconstructed/` na raiz (decisão do usuário) | 🟢 |
| D-02 | Rotas do `index()` delegam aos módulos movidos | Elimina a duplicação apontada em `_reversa_sdd/architecture.md#5`; rota vira orquestração fina + renderização | Manter helpers inline órfãos | 🟢 |
| D-03 | Preservar globals compartilhadas (`people`, `families`, `graph`, `child_to_family`) e re-parse a cada `POST` | Comportamento idêntico ao legado (RF-06), já validado pelos testes | Injeção de dependência / estado por request (mudaria comportamento) | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Nenhuma — todos os `[DÚVIDA]` foram resolvidos em 2026-08-11 (remoção total da duplicação; módulos movidos para `analisador-genealogico/`) | Seções 9 e 10 | n/a |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `app.py` (roteamento) | `_reversa_sdd/architecture.md#2` | regra-alterada | Lógica inline removida; rotas passam a delegar aos módulos movidos. |
| Módulos de lógica (`upload`, `path_search`, `dna_analysis`, `domain`) | `_reversa_sdd/reconstruction-report.md` | componente-novo | Promovidos de `reconstructed/` (raiz) para dentro de `analisador-genealogico/`. |
| Frontend UI (`templates/index.html`) | `_reversa_sdd/architecture.md#2` | regra-alterada (mantida) | Contrato Jinja2 permanece; nenhuma alteração no template. |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhum** — o modelo continua 100% em memória (dicionários + grafo networkx), sem persistência, sem novos campos.
- Detalhe completo em: `_reversa_forward/002-integrar-rota-app-modulos/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a | — | Sem contratos HTTP/fila/gRPC externos afetados; as rotas Flask e o contrato Jinja2 com `index.html` são internos e permanecem idênticos. |

## 8. Plano de migração

1. Mover os módulos de `reconstructed/` para `analisador-genealogico/` (mantendo os imports relativos funcionando).
2. Ajustar `app.py` para importar dos módulos movidos e remover a lógica inline duplicada.
3. Rodar a suíte de testes (47) para confirmar ausência de regressão.
4. Execução manual/smoke via navegador (onboarding.md) validando os três fluxos.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Diferença sutil entre a lógica inline do `app.py` e a dos módulos reconstruídos | alto | médio | Suíte de 47 testes + smoke manual dos 3 fluxos (onboarding.md) |
| Quebra de import relativo ao mover os módulos | médio | médio | Ajustar imports junto com a movimentação; validar com `python -c "import ..."` |
| `reconstructed/` na raiz usada por testes existentes (fixtures/imports) | médio | baixo | Os testes referenciam `reconstructed.*`; manter aliases ou atualizar imports dos testes em paralelo |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Suíte de testes existente passa sem regressão
- [ ] Smoke manual dos 3 fluxos (upload, path_search, dna_analysis) via `onboarding.md`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-08-11 | Versão inicial gerada por `/reversa-plan` | reversa |
