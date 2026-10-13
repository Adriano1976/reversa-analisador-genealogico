# Reproducao: texto do driver do banco na pagina

**Ambiente da medicao:** Windows, Python 3.14.6 do `.venv/` do repositorio, app servido por
waitress na porta 5098 em loopback, pasta de upload desviada para um diretorio temporario,
dados sinteticos.

## Caso 1: driver AUSENTE (estado real do `.venv/` do repositorio)

Confirmacao previa: `import psycopg2` no `.venv/` falha (`ModuleNotFoundError`), embora
`psycopg2-binary==2.9.13` esteja pinado no `requirements.txt` (achado L-26 do proprio
projeto).

1. Subir o app com `DATABASE_URL=postgresql://analisador-sonda:senha-sintetica@127.0.0.1:5432/base-sonda`
   (valores **inventados**; nenhum valor do `.env` foi lido).
2. `POST /` com `action=dna_analysis`, uma arvore sintetica e um CSV sintetico de matches.
3. Ler o bloco `aviso_de_persistencia` da pagina.

**Observado (200):**

```
Historico nao registrado: o driver do banco nao esta instalado neste interpretador
(No module named 'psycopg2').
```

## Caso 2: driver PRESENTE e banco recusando (duble declarado)

O driver real nao esta instalado, entao o caminho "driver instalado e conexao recusada" foi
medido com um **duble sintetico** (`duble-psycopg2.py`, copiado de
`_reversa_bugs/_sondas-seguranca/stub/psycopg2/__init__.py`) colocado no `PYTHONPATH` do
servidor. O duble so implementa `connect`, que levanta `OperationalError` com uma mensagem
no formato do driver real.

1. Subir o app com o mesmo `DATABASE_URL` e `PYTHONPATH` apontando para o duble.
2. Repetir a analise.

**Observado (200):**

```
Historico nao registrado: OperationalError: connection to server at "127.0.0.1", port 5432
failed: FATAL:  password authentication failed for user "analisador-sonda"
```

O texto e do duble (host, porta e usuario inventados). O que a medicao prova e o que a
**aplicacao** faz com o texto de qualquer excecao do driver.

## Origem no codigo

`src/ports/adaptadores.py:294-314`:

```python
except Exception as erro:
    return None, f"Histórico não registrado: {type(erro).__name__}: {erro}"
```

O aviso e renderizado em `src/templates/index.html:401-403` (`<div class="alerta-aviso">`).
A `RN-13` exige que a persistencia nao bloqueie o resultado, e ela e respeitada; o que nao
existe e filtro sobre o **conteudo** do aviso.

## Evidencia bruta

- `persistencia-sem-driver.json` e `persistencia-com-duble.json`.
- `duble-psycopg2.py`: o duble, para conferencia.
- Sonda: `_reversa_bugs/_sondas-seguranca/sondas_http.py` (grupo `persistencia`).
