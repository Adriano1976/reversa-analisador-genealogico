# Sondas de seguranca (ferramenta de medicao)

Este diretorio guarda o **utilitario** que executa as sondas do checklist de seguranca,
e nao o resultado delas. O resultado esta em
`../seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` e as evidencias
brutas ao lado dele, em `../seguranca/inspections/checklist-20261013/evidencias/`.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `gerar_fixtures.py` | Gera as arvores e os CSVs **sinteticos** e o `manifesto.json` com sha256 e chave de conteudo de cada um |
| `sondas_http.py` | Sondas por HTTP, uma por grupo: `estatico`, `origem`, `identidade`, `lan`, `nomes`, `ads`, `erro`, `parse`, `dna`, `persistencia` |
| `concorrencia.py` | Curva de N selecoes simultaneas da mesma arvore, com a latencia de `GET /` no meio da carga |
| `linha_de_base.py` | Uma requisicao por vez: arvore pequena contra arvore grande, mais `GET /` ocioso |
| `calibrar.py` | Mede o nucleo sem HTTP (parse e analise de DNA por matriz de linhas x pool) |
| `stub/psycopg2/__init__.py` | **Duble declarado** do driver do banco, usado so na sonda do item 9 porque o driver real nao esta instalado no `.venv/` |

## Como rodar

```powershell
$py = 'D:\Projetos\reversa_analisador_gelealogico\.venv\Scripts\python.exe'
$s  = Join-Path $env:TEMP 'reversa-chec-seg'

& $py gerar_fixtures.py "$s\fixtures"

$env:ANALISADOR_UPLOAD_FOLDER = "$s\uploads"   # obrigatorio: nao escrever em src/uploads/
$env:ANALISADOR_PORT = '5099'
$env:ANALISADOR_HOST = '127.0.0.1'
$env:ANALISADOR_THREADS = '4'
& $py ..\..\..\src\app.py                       # em outro terminal, ou como job em segundo plano

& $py sondas_http.py nomes --porta 5099 --uploads "$s\uploads" --fixtures "$s\fixtures" --outdir "$s\out"
```

## Regras que valem para qualquer reuso

1. **Nunca** aponte `ANALISADOR_UPLOAD_FOLDER` para `src/uploads/`: ali vivem os arquivos
   reais do operador.
2. Use somente dados sinteticos de `gerar_fixtures.py`. Nenhuma sonda le `.env` ou
   `src/uploads/`.
3. Prefira loopback. A sonda `lan` usa um segundo endereco de loopback (`127.0.0.2`) em
   vez do IP da rede local, para nao expor a maquina.
4. Os envios usam conteudo **variado por caso** (`variante`): sem isso, varios nomes com o
   mesmo conteudo viram uma linha so na lista, porque o armazenamento e por chave de
   conteudo, e o teste fica confundido.
