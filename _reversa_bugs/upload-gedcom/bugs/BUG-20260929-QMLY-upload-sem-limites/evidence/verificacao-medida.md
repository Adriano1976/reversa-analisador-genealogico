# Verificação de código medida: BUG-20260929-QMLY

Evidência produzida pelo `/reversa-debugger-fix` em 2026-10-02. Complementa o
`verificacao-codigo.md` de 2026-09-29 (leitura de código) com medição executada.
Nenhum arquivo do projeto foi alterado.

Sonda: `.pytest-tmp/probe-qmly.py`. Saída bruta: `.pytest-tmp/probe-qmly-saida.txt`.

## 1. Limite de tamanho: ausente

```text
app.config[MAX_CONTENT_LENGTH]     None
limite ausente?                    True
```

`MAX_CONTENT_LENGTH` não existe em `app.py` nem em nenhum outro arquivo do projeto. Sem ele, o
Flask não impõe teto de corpo de requisição: o multipart é gravado em disco antes de qualquer
verificação de negócio. Não há `accept` nos dois inputs de arquivo de `templates/index.html`
(linhas 47 e 90), então nem sequer existe filtro de cliente.

## 2. Nome do cliente na composição de caminho: escape provado

Composição de `os.path.join("uploads", <nome do cliente>)`:

| Nome enviado | Caminho real resolvido | Escapa de `uploads/`? |
|---|---|---|
| `arvore.ged` | `.../uploads/arvore.ged` | não |
| `../fora.ged` | `.../qmly-run/fora.ged` | **sim** |
| `..\fora.ged` | `.../qmly-run/fora.ged` | **sim** |
| `sub/dir.ged` | `.../uploads/sub/dir.ged` | não (subpasta inexistente) |
| `C:\Windows\Temp\abs.ged` | `ValueError: path is on mount 'C:', start on mount 'D:'` | falha em vez de escrever |
| `....//....//fora.ged` | `.../uploads/..../fora.ged` | não |
| `nome_com_espacos_e_acentos_ção.ged` | preservado literalmente | não |
| `\x00nulo.ged` | composto sem erro (o NUL só falha no `open`) | não |

### Prova por gravação real

Envio com o nome `../ESCAPIU.ged`:

```text
status                             200
gravou FORA de uploads/?           True
caminho do arquivo fora            '...\.pytest-tmp\qmly-run\ESCAPIU.ged'
sobrou algo em uploads/            []
```

O arquivo nasce fora da pasta de upload e `uploads/` fica vazia. O escape é fato medido.

## 3. Extensão e conteúdo: nenhuma validação antes do parse

| Arquivo enviado | Conteúdo | Aceito? | Erro de parse? | Gravado em disco? |
|---|---|---|---|---|
| `conteudo_gedcom.txt` | GEDCOM válido | **sim** | não | sim |
| `conteudo_gedcom.sem_extensao` | GEDCOM válido | **sim** | não | sim |
| `lixo.bin` | bytes arbitrários | não | **sim** | **sim** |
| `vazio.ged` | vazio | não | **sim** | **sim** |

Duas conclusões que a leitura de código não dava:

1. **A gravação acontece antes do parse.** `lixo.bin` e `vazio.ged` falham no parse e mesmo assim
   ficam em disco. O erro não impede a escrita; o arquivo rejeitado permanece, e é recuperável pelo
   campo `gedcom_filename` na requisição seguinte.
2. **A extensão não filtra nada.** GEDCOM válido com `.txt` ou sem extensão alguma é aceito e
   parseado com sucesso. O caminho de código é o mesmo independentemente do nome.

## 4. Colisão: o primeiro envio é perdido sem aviso

```text
apos primeiro envio, disco         b'0 HEAD\n1 SOUR PRIMEIRO\n0 TRLR\n'
apos primeiro envio, == enviado?   True
apos segundo envio, disco          b'0 HEAD\n1 SOUR SEGUNDO\n0 TRLR\n'
o primeiro sobreviveu?             False
```

Métricas de erro do lado do servidor: nenhuma. Mensagem ao usuário no segundo envio: a mesma de
sucesso. A perda é silenciosa.

## 5. `gedcom_filename`: chave de recuperação controlada pelo cliente

`templates/index.html:68` e `:87` enviam `gedcom_filename` como **campo oculto**, preenchido com o
valor que o servidor devolveu. Nada impede o cliente de alterá-lo. A sonda confirma que um
`gedcom_filename` arbitrário é aceito no `POST` de `path_search` e a requisição responde `200`,
carregando o arquivo correspondente de `uploads/` sem qualquer verificação de propriedade.

Este é o ponto de contato com o `BUG-20260929-BJJH`: o mesmo nome de arquivo funciona como
identificador de sessão. A aresta `related-to` que o registro marca como `proposed` fica
**confirmada** por medição (ver `evidence/causacao-medida.txt`).

## 6. Causa raiz é herdada do legado, não introduzida pela reconstrução

O oráculo congelado `_reversa_sdd/oracle/app_legacy_e43ca22.py` (sha256
`44370b2339a645c4d9ce732ac3962811b16b35f587ece3507dad4fc3d87646bb`, conferido nesta sessão) contém:

```python
15: UPLOAD_FOLDER = "uploads"
17: os.makedirs(UPLOAD_FOLDER, exist_ok=True)
569:                gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_file.filename)
570:                gedcom_file.save(gedcom_path)
579:        gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_filename)
589:                matches_path = os.path.join(UPLOAD_FOLDER, matches_file.filename)
590:                matches_file.save(matches_path)
```

Varredura por `MAX_CONTENT_LENGTH` e `secure_filename` no oráculo: **zero ocorrências**. Portanto
a limitação nasceu no legado e a reconstrução a preservou fielmente, como o docstring de
`reconstructed/upload.py:1-7` declara. Corrigir a limitação é, por definição, uma **divergência
deliberada** do legado, e é por isso que o veredito de spec é obrigatório.

---
*Gerado pelo Reversa-Debugger-Fix em 2026-10-02.*
