# Regression Watch: regiões compartilhadas

> Identificador: `056-regioes-compartilhadas`
> Data: `2026-11-09`

## Itens

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W056-01 | `src/core/regioes.py` (`PISO_DE_CM`) | Só segmento de **10 cM ou mais** entra na região | presença | Segmento de 9 cM formando região |
| W056-02 | `src/core/regioes.py` (`_montar`) | A faixa da região é a **interseção** e está contida em cada segmento membro | presença | Faixa maior que a de algum membro |
| W056-03 | `src/core/regiao_no_cartao.py` | O desfecho vem dos cartões já calculados, sem segundo matching | presença | Região classificada por cM ou por nome sem cartão |
| W056-04 | `src/templates/index.html` (bloco) | O bloco declara que o compartilhamento é **com o kit do arquivo** | presença | Texto afirmando triângulo fechado |
| W056-05 | `src/core/regioes.py` | Nenhum cM é somado: mínimo e máximo por segmento | presença | Campo de cM total da região |
| W056-06 | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | `0b926895…` (52.497 bytes) até mudança declarada | presença | Hash divergente sem delta em `evidence/` |
| W056-07 | `src/app.py` | Não existe ação de triangulação nem campo `triangulacao_csv` | presença | Formulário ou ação de arquivo de pares reaparecendo |
| W056-08 | `src/assets/app.css` (`details.card.regioes-compartilhadas`) | O cartão do hover **não é recortado** pelo raio do card; o recorte fica no cabeçalho | presença | `overflow:hidden` de volta no bloco, ou cartão do hover com o topo cortado |

## Observações sem peso de regressão

- **Limiar de acúmulo** (≥ 8 kits e (< 2 Mb ou cM máx < 12)): heurística declarada, ancorada na amostra.
- **Limite de 200 regiões**: existe para arquivo anômalo, não para o caso real.
- **Custo**: 783 segmentos → 32 regiões em 0,005 s; não há medição com arquivo de 100 mil linhas.

## Histórico de re-extrações

| Data | Extração | Resultado |
|------|----------|-----------|
| — | — | Ainda não houve re-extração depois desta entrega |

## Arquivadas

Nenhum item arquivado.
