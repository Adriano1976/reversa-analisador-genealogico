# Modo conteiner - T016
# Gerado em (UTC): 2026-10-09T14:54:40Z
# Montagem: D:/dados-genealogicos/uploads -> /app/src/uploads (D-02)
# Estado inicial da composicao: app e db JA estavam no ar; o estado foi preservado ao final
# canonico antes: 38 | depois da 1a sonda: 39 | depois do ciclo down/up: 40
# exit code sonda 1 (antes do ciclo): 0
# exit code sonda 2 (depois do ciclo): 0

## Sonda 1 - continuidade pela porta publicada

1) upload da arvore sintetica (conteudo unico, nome visivel proprio)
   HTTP 200 | alerta: Arquivo &#39;sonda_t014.ged&#39; carregado!
   referencia devolvida: 0646f8431ba58cca__sonda_t014.ged
2) busca de caminho entre Carlos Silva e Diego Silva
   HTTP 200 | alerta: Conexão direta encontrada (ancestral comum). | Foram encontrados 3 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado.
   mermaid presente: True
3) analise de DNA com a fixture de CSV, em nome visivel proprio
   HTTP 200 | alerta: 1 conexões encontradas. 0 descartadas. |  | Foram encontrados 2 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado. | O CSV não traz coluna de kit nem de e-mail: os segmentos foram agrupados apenas pelo nome. Se duas pessoas diferentes compartilharem o nome, os valores podem estar somados indevidamente.
4) varredura do sintoma de referencia quebrada
   OK: nenhuma resposta diz 'nao existe mais'

## docker compose down

 Container genealogia-db-1 Removing 
 Container genealogia-db-1 Removed 
 Network genealogia_default Removing 
 Network genealogia_default Removed 

## docker compose up -d

 Container genealogia-db-1 Starting 
 Container genealogia-db-1 Started 
 Container genealogia-app-1 Starting 
 Container genealogia-app-1 Started 

## Sonda 2 - depois de derrubar e subir

1) upload da arvore sintetica (conteudo unico, nome visivel proprio)
   HTTP 200 | alerta: Arquivo &#39;sonda_t014.ged&#39; carregado!
   referencia devolvida: dbc25ecc1cb17db3__sonda_t014.ged
2) busca de caminho entre Carlos Silva e Diego Silva
   HTTP 200 | alerta: Conexão direta encontrada (ancestral comum). | Foram encontrados 3 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado.
   mermaid presente: True
3) analise de DNA com a fixture de CSV, em nome visivel proprio
   HTTP 200 | alerta: 1 conexões encontradas. 0 descartadas. |  | Foram encontrados 2 caminhos genealógicos distintos (inclusive por outros ancestrais comuns). O caminho exibido é o de menor distância total; os demais estão listados e nenhum foi descartado. | O CSV não traz coluna de kit nem de e-mail: os segmentos foram agrupados apenas pelo nome. Se duas pessoas diferentes compartilharem o nome, os valores podem estar somados indevidamente.
4) varredura do sintoma de referencia quebrada
   OK: nenhuma resposta diz 'nao existe mais'
