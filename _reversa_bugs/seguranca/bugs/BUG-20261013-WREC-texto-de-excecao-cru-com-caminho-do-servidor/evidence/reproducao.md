# Reproducao: texto de excecao cru, com o caminho absoluto do servidor

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5099 em loopback, pasta de upload desviada para um diretorio temporario
por `ANALISADOR_UPLOAD_FOLDER`, dados sinteticos.

## Passos

1. Descobrir a chave de conteudo da fixture: `sha256("arvore_valida.ged")[:16]` =
   `7b682362af68f7c0`.
2. Criar um **diretorio** na pasta de upload com o nome armazenado esperado:
   `<pasta-de-upload>/7b682362af68f7c0__sonda_dir.ged`.
3. `POST /` com `action=upload_gedcom` e o campo `gedcom` com `filename="sonda_dir.ged"` e
   o conteudo de `arvore_valida.ged`.

O passo 2 e o gatilho minimo: como o nome armazenado ja existe, a guarda de existencia
(`src/ports/adaptadores.py:84`) pula a gravacao, e a releitura da arvore tenta abrir um
**diretorio** com o parser de GEDCOM.

## Observado

Resposta **200** com, no HTML:

```
Erro ao processar GEDCOM: [Errno 13] Permission denied:
'C:\Users\venda\AppData\Local\Temp\dsh-cvAZP4\reversa-chec-seg\uploads\7b682362af68f7c0__sonda_dir.ged'
```

A pagina carrega, no corpo da resposta HTTP: o `errno` do sistema operacional, o texto do
sistema (`Permission denied`) e o **caminho absoluto** da pasta de upload, que inclui o
nome de usuario do sistema.

## Origem no codigo

`src/app.py:533-538`:

```python
except Exception as e:
    app.logger.exception("falha inesperada no envio de GEDCOM")
    return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)
```

O mesmo padrao `f"... {e}"` esta em `src/app.py:680` (analise de DNA) e `src/app.py:707-710`
(busca de caminho). O `app.logger.exception` ja registra o rastro no log; o que a medicao
mostra e que o texto **tambem** vai para a resposta.

## Controle negativo

O GEDCOM truncado (`0 HEAD` sem `TRLR`) **nao** entra nesse `except`: o `ged4py` aceitou o
arquivo e a tela respondeu `Arquivo 'arvore_truncada.ged' carregado!`. Ou seja, o caminho
do vazamento exige uma falha que nao seja de dominio (erro de sistema de arquivos, por
exemplo), e nao um arquivo malformado qualquer.

## Evidencia bruta

- `erro.json`: mensagens extraidas da resposta e o texto da excecao na pagina.
- `erro-diretorio-no-lugar-do-arquivo.html`: HTML cru da resposta.
- Sonda: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupo `erro`).
