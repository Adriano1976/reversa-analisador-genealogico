# Regression Watch: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Âncora: `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`
> Este arquivo nasceu nesta feature. As execuções seguintes fazem append nas seções, sem reescrever
> IDs ou histórico.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `src/core/janela_de_vida.py`; `legacy-impact.md#4-modificadas` | `data_imprecisa(texto)` continua público, com a mesma lista de qualificadores (`ABT`, `EST`, `CAL`, `BEF`, `AFT`, `CIRCA`, `APPROX`), e `conferir_janela_de_vida` mantém 105/122 e o mesmo retorno | presença | Função ausente de `__all__`, import quebrado, qualificador removido ou mudança no estado devolvido por `conferir_janela_de_vida` |

## Observações

> Invariantes novos, ainda sem peso de regressão até uma extração futura confirmá-los como 🟢.
> Não entram no watch principal porque não são regra pré-existente modificada.

- **O-01 — pureza do núcleo.** `core.validator` não importa `parsers`, `application`, `reporting`,
  a borda HTTP nem relógio (`datetime`/`time`). Sinal: `tests/test_fronteira_do_validador.py`
  falha.
- **O-02 — literais do status.** `validar_comparacao` devolve exatamente `VALIDADO`,
  `INCONCLUSIVO` ou `ERRO CRONICO / QUEBRA DE LINHA`, sem variação de caixa ou acento. Sinal:
  status fora do conjunto em qualquer teste.
- **O-03 — quatro estados preservados.** `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e `INCONCLUSIVO`
  continuam existindo, com o mesmo texto e a mesma classe CSS, e a tela não é tocada. Sinal:
  renomeação de estado, mudança de mensagem ou diff em `src/app.py`/template/CSS.
- **O-04 — cM por kit.** Nenhum total é somado entre kits; cada kit tem seu próprio resultado e o
  resumo usa o pior status. Sinal: `cm` igual à soma de dois kits ou `comparacoes` com menos itens
  que kits.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|------|-------------|-----------|
| - | - | - |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| - | - | - |
