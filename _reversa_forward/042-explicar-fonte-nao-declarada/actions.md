# Actions: Explicar a fonte não declarada no cartão

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/042-explicar-fonte-nao-declarada/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 4 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 3 (T001 → T002 → T003 → T004) |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar `EXPLICACOES` e a função pura `explicacao(motivo, bruto)` a `fontes_de_laboratorio`, com a variante para célula vazia ou `-` | - | `[//]` | `src/core/fontes_de_laboratorio.py` | 🟢 | `[X]` |
| T002 | Expor `source_motivo` e `source_explicacao` em `evidence_for` | T001 | - | `src/core/genetic_evidence.py` | 🟢 | `[X]` |
| T003 | Renderizar a explicação na linha `Fonte:` do bloco 2 e omitir a etiqueta quando o texto for `-` ou vazio | T002 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T004 | Cobrir com testes a explicação por motivo (unidade) e a linha `Fonte:` no cartão (tela), e rodar a suíte completa | T003 | `[//]` | `tests/test_fontes_de_laboratorio.py`, `tests/test_fonte_e_cobertura_na_tela.py` | 🟢 | `[X]` |

## Notas de execução

- **T001:** `MOTIVOS_TEXTO` (contagem do painel) e `EXPLICACOES` (frase do cartão) ficaram **separados**
  de propósito: o primeiro é rótulo ao lado de um número, o segundo responde "então o que é isso?".
  Fundi-los obrigaria o painel a exibir uma frase longa.
- **T003:** a etiqueta do texto original passou a ser omitida quando o valor é `-` ou vazio — não há o que
  mostrar, e `[-]` era ruído. A explicação continua nesses casos.
- **T004:** 6 testes de unidade da `explicacao` + 2 testes de tela; suíte completa em **1500 passed,
  9 skipped** (antes: 1492/9, delta de +8).
- **Conferência na análise real** (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`): os 8
  cartões com fonte não declarada passaram a exibir, por exemplo,
  `Fonte: não declarada Migration - F2 - T — nome de projeto de pesquisa, não de laboratório`;
  `Fonte: não declarada — o arquivo não traz uma fonte utilizável nesta coluna`;
  `Fonte: não declarada Outro (insira o nome abaixo) — texto de formulário do site de origem, não um laboratório`.
  Nenhum cartão com laboratório reconhecido ganhou texto extra.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-code-express` | reversa |
| 2026-10-22 | Execução: 4/4 ações concluídas | reversa |
