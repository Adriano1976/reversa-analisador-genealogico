# Verificacao local - T014
# Gerado em (UTC): 2026-10-09T14:47:48Z
# Aplicacao subida com ANALISADOR_UPLOAD_FOLDER = D:\dados-genealogicos\uploads
# Fixtures SINTETICAS: basic.ged (com marcador unico) e cm_boundaries.csv
#   conteudo unico + nome visivel proprio, para a escrita criar arquivo NOVO e a
#   contagem das pastas provar ONDE ela caiu
# exit code da sonda: 0
# src\uploads (repositorio): 36 -> 36 arquivos
# destino canonico:         36 -> 38 arquivos

1) upload da arvore sintetica (conteudo unico, nome visivel proprio)
   HTTP 200 | alerta: Arquivo &#39;sonda_t014.ged&#39; carregado!
   referencia devolvida: 5ecee1e84e8365f4__sonda_t014.ged
2) busca de caminho entre Carlos Silva e Diego Silva
   HTTP 200 | alerta: Conexão direta encontrada (ancestral comum). | Foram encontrados 3 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado.
   mermaid presente: True
3) analise de DNA com a fixture de CSV, em nome visivel proprio
   HTTP 200 | alerta: 1 conexões encontradas. 0 descartadas. |  | Foram encontrados 2 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado. | O CSV não traz coluna de kit nem de e-mail: os segmentos foram agrupados apenas pelo nome. Se duas pessoas diferentes compartilharem o nome, os valores podem estar somados indevidamente.
4) varredura do sintoma de referencia quebrada
   OK: nenhuma resposta diz 'nao existe mais'
