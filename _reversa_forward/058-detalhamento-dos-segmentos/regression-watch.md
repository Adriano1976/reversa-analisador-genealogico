# Regression Watch: detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`

## Itens

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W058-01 | `src/core/segmentos.py` (`RN-02`) | Uma linha por **par (região, kit)**; uma coluna de kit, nunca duas | presença | Linha por região, ou coluna "Kit 2" aparecendo |
| W058-02 | `src/core/segmentos.py` (`RN-03`) | Ordem: cromossomo natural, depois posição inicial, depois kit | presença | `10` antes de `9`, ou linha fora de ordem por início |
| W058-03 | `src/core/segmentos.py` (`D-02`) | O `regiao_indice` é gravado **antes** da ordenação da tabela | presença | Linha apontando para a faixa de outra região |
| W058-04 | `src/templates/index.html` | O `href="#regiao-N"` de cada linha tem `id="regiao-N"` correspondente no ideograma | presença | Âncora órfã (clique não destaca nada) |
| W058-05 | `src/templates/index.html` | A tabela fica **depois da distribuição** e **antes da lista de regiões** | presença | Seção em outra posição no cartão |
| W058-06 | `src/templates/index.html` (script) | Filtro e paginação **não fazem requisição**: só marcam `hidden` | ausência | `fetch`/`form` novo no bloco da tabela |
| W058-07 | `src/templates/index.html` | O script e o comentário da tabela estão **dentro** do `{% if segmentos %}` | presença | `GET /` mudando de bytes (o hash acusa) |
| W058-08 | `src/assets/app.css` (`@media print`) | Na impressão, as linhas escondidas pela paginação voltam | presença | Resultado impresso com menos linhas que o total |
| W058-09 | `src/templates/index.html` (cartão da tabela) | A tabela só repete dado que a lista de regiões já mostra | ausência | Nome, kit ou coordenada que não exista na região |

## Observações sem peso de regressão

- **Tamanhos de página** (10/20/30) e o padrão 20: escolha de apresentação; outro conjunto não
  invalida número nenhum.
- **Coluna "Copiar"**: conveniência; a tabela é legível sem ela.
- **Selo de desfecho por linha**: repetir o selo em cada linha da mesma região é redundante de
  propósito — a linha precisa se explicar sozinha quando filtrada.

## Histórico de re-extrações

| Data | Extração | Resultado |
|------|----------|-----------|
| — | — | Ainda não houve re-extração depois desta entrega |

## Arquivadas

Nenhum item arquivado.
