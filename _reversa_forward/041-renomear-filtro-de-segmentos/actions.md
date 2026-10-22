# Actions: Renomear o filtro de segmentos no título do bloco

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/041-renomear-filtro-de-segmentos/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 3 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 2 (T001 → T002) |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Trocar o título de queda do bloco por `Filtro de segmentos ({{ result.endogamia.limiares.segmento \| cm_br }} cM)`, mantendo o ramo estrutural intocado | - | `[//]` | `src/templates/index.html` | 🟢 | `[X]` |
| T002 | Atualizar o literal preso no teste de "sem fato nenhum" para o título novo | T001 | `[//]` | `tests/test_endogamia.py` | 🟢 | `[X]` |
| T003 | Rodar `test_endogamia.py` e a suíte completa, conferindo que "Filtro de endogamia" sumiu do HTML e que o selo estrutural não mudou | T002 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

- **T001:** o ramo estrutural (`{{ result.endogamia.selo.rotulo }}`) ficou intocado; só a queda
  (`{% else %}`) mudou. O limite vem de `result.endogamia.limiares.segmento | cm_br`, então o
  template não guarda um segundo `10`.
- **T002:** além de trocar o literal do teste de "sem fato nenhum", o teste
  `test_filtro_tem_selo_no_cabecalho_e_bloco_na_secao_2` ganhou a asserção **positiva** do título
  novo e a negativa do antigo — sem isso, o teste antigo continuaria passando por ausência.
- **T003:** `test_endogamia.py` 46 passed; suíte completa **1492 passed, 9 skipped** (mesma contagem
  de antes: as asserções novas entraram dentro de um teste existente). Os rótulos
  `Sinal estrutural na árvore`, `Endogamia estrutural`, `Evidência fraca` e
  `Filtro: N seg. abaixo de 10 cM` continuam presos pelos testes que já existiam.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-code-express` | reversa |
| 2026-10-22 | Execução: 3/3 ações concluídas | reversa |
