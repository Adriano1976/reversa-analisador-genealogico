# Reproducao: nome de arquivo com dois pontos (`:`)

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5099 em loopback, pasta de upload desviada para um diretorio temporario
por `ANALISADOR_UPLOAD_FOLDER`, dados sinteticos (`gerar_fixtures.py`).

Conteudo enviado em todos os casos: `arvore_valida.ged` (GEDCOM sintetico de 8 pessoas,
706 a 709 bytes), com um byte de variacao por caso para que cada envio tenha **chave de
conteudo propria** (sem isso, varios nomes com o mesmo conteudo viram uma linha so na
lista, porque o armazenamento e por chave, e o teste fica confundido).

## Caso A: `teste:1.ged`

1. `POST /` com `action=upload_gedcom` e o campo `gedcom` com `filename="teste:1.ged"`.
2. Ler a resposta e a pasta de upload.

**Observado**

- Tela: `Arquivo 'teste:1.ged' carregado!`, e o formulario devolve
  `gedcom_filename = bee820c034ef143d__teste:1.ged`.
- Disco: nasce **um** arquivo, `bee820c034ef143d__teste`, com **0 byte**.
- Os 709 bytes enviados existem no **fluxo alternativo NTFS** `:1.ged`:
  `os.path.exists("<pasta>/bee820c034ef143d__teste:1.ged")` devolve `True`,
  `os.stat` reporta 709 e a leitura devolve os 709 bytes.
- A lista da tela **nao oferece** nem `bee820c034ef143d__teste:1.ged` nem
  `bee820c034ef143d__teste`: o nome do arquivo real nao tem extensao reconhecida por
  nenhuma das duas abas.

## Caso B: `teste.ged:ads`

**Observado**

- Tela: `Arquivo 'teste.ged:ads' carregado!`
- Disco: arquivo `86b1ccc63ccda05a__teste.ged` com **0 byte**; os bytes no fluxo `:ads`.
- A lista **oferece** `86b1ccc63ccda05a__teste.ged` (a extensao `.ged` entra na aba de
  arvores) com 0 byte; clicar nele responde
  `Erro: o arquivo 'teste.ged' nao pode ser lido como GEDCOM. Ele pode estar corrompido,
  vazio, ou nao ser um GEDCOM de verdade.`

## Caso C: `C:\escape.ged`

O nome chega ao servidor como `C:escape.ged` (o par entre aspas do cabecalho multipart
come a barra invertida: `\e` vira `e`).

**Observado**

- Tela: `Erro ao processar GEDCOM: a arvore recem-gravada nao pode ser relida`.
- Disco: **arquivo orfao** `993a6adffa751f16__C` com 0 byte, com os bytes no fluxo
  `:escape.ged`.
- Causa: `chave_recebida_e_valida("993a6adffa751f16__C:escape.ged")` e falso, porque
  `os.path.basename("C:escape.ged")` devolve `escape.ged`, que e diferente do proprio
  nome. O resolvedor devolve `None`, `carregar` devolve `None` e
  `upload_gedcom` levanta `RuntimeError` (`src/application/upload_gedcom.py:110`).

## Controles negativos (mesma bateria)

| Nome enviado | Resultado |
|---|---|
| `con.ged`, `CON.ged`, `nul.ged`, `aux.ged`, `com1.ged`, `lpt1.ged`, `CON` | arquivo regular, 706 bytes, conteudo integro, alcancavel |
| `../../escape.ged` | `97d11d7e434252a7___.._escape.ged` dentro da pasta, 707 bytes, alcancavel |
| `..\escape.ged` (chega como `..escape.ged`) | `143baa23f465657e__escape.ged`, 707 bytes, alcancavel |
| `nome.` | `8f44365fe0efb29b__nome.ged`, 706 bytes, alcancavel |

Nenhum caminho saiu da pasta de upload em nenhum dos 14 nomes testados.

## Evidencia bruta

- `nomes.json`: bateria completa dos 14 nomes, com o que nasceu no disco e o que a tela
  passou a oferecer.
- `ads.json`: os tres casos com dois pontos, com `os.path.exists`, `os.path.isfile`,
  tamanho de `stat` e bytes lidos para cada forma do nome.
- `ads-listagem.html` e `nomes-listagem-final.html`: HTML cru das respostas.
- Sondas: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupos `nomes` e `ads`).
