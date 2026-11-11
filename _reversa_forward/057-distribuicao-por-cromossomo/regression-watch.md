# Regression Watch: distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`

## Itens

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W057-01 | `src/reporting/distribuicao.py` (`_eixo`) | O eixo sempre parte de **zero** e o topo é múltiplo do passo | presença | Primeira marca com valor maior que zero, ou barra mais alta acima do topo |
| W057-02 | `src/core/distribuicao.py` | "Matches" conta **kits distintos** por cromossomo; o mesmo kit em duas regiões conta uma vez | presença | Contagem maior que o número de kits distintos do cromossomo |
| W057-03 | `src/core/distribuicao.py` (`D-12`) | O cM médio usa **um segmento por kit**, o de maior cM | presença | Média com denominador maior que o número de kits |
| W057-04 | `src/templates/index.html` (bloco) | O gráfico fica **depois da legenda do ideograma** e **antes da lista de regiões** | presença | Sub-bloco em outra posição no cartão |
| W057-05 | `src/templates/index.html` (bloco) | Nenhum cM é somado; o valor exibido é a média | presença | Rótulo de "cM total" ou valor que cresce com o número de regiões |
| W057-06 | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | `0b926895…` (52.497 bytes) até mudança declarada | presença | Hash divergente sem delta em `evidence/` |
| W057-07 | `src/core/distribuicao.py` (`_ordem_do_cromossomo`) | Ordem natural: `9` antes de `10`, depois `X`, `Y`, `MT` | presença | Cromossomo fora de ordem no eixo |
| W057-08 | `src/templates/index.html` (cartão do cromossomo) | O cartão do hover mostra **só agregados** | ausência | Nome, kit ou coordenada de match no cartão |

## Observações sem peso de regressão

- **Topo "redondo"** (`D-08`): a escolha do passo é desenho, não domínio; um passo diferente não
  torna nenhum número errado, só a escala menos legível.
- **Cores das séries** (`D-07`): `--primary` e `--ink` são escolha de apresentação; trocar não muda
  a conta.
- **Altura fixa do gráfico** (9 rem): decisão de layout.

## Histórico de re-extrações

| Data | Extração | Resultado |
|------|----------|-----------|
| — | — | Ainda não houve re-extração depois desta entrega |

## Arquivadas

Nenhum item arquivado.
