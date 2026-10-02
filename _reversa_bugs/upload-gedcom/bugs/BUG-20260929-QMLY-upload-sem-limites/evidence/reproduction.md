# Reprodução: BUG-20260929-QMLY

Cápsula de reprodução medida em 2026-10-02. Substitui a classificação por leitura de código que
constava no registro original ("nenhuma reprodução end-to-end foi executada nesta sessão").

## Ambiente

| Item | Valor |
|---|---|
| Commit base | `95d87fc` (working tree limpo em `analisador-genealogico/` e `tests/`) |
| Branch | `melhorias-reversa` |
| Sistema | Windows, `py -3.14` |
| Framework | Flask 3.1.3 |
| Cliente | `app.test_client()` do próprio Flask, dentro de um diretório contido em `.pytest-tmp/qmly-run` |
| Sonda | `.pytest-tmp/probe-qmly.py` |
| Saída bruta | `.pytest-tmp/probe-qmly-saida.txt` |

## Comando

```powershell
py -3.14 .pytest-tmp/probe-qmly.py
```

## Resultado

| Medida | Valor |
|---|---|
| Exit code | `0` |
| Tentativas / falhas | 1 / 0 |
| Classificação | **deterministic** (confirmada, não mais inferida) |

Determinismo justificado por execução: todos os seis grupos de asserção produziram o mesmo
resultado, sem ramo dependente de ambiente, tempo ou aleatoriedade. A sonda foi executada duas
vezes, com saída idêntica.

## Como a reprodução foi feita, e por que assim

A app roda no diretório corrente, não no diretório do script: `UPLOAD_FOLDER` é o literal
`"uploads"`, resolvido contra o CWD, e `app.py:14` cria a pasta no momento do `import`. Por isso a
sonda troca para um diretório contido **antes** de importar `app`, e limpa tudo ao final. Nenhum
arquivo do projeto foi tocado.

O `tempfile.mkdtemp` do sistema foi tentado primeiro e falhou com `PermissionError: [WinError 5]`
sob o sandbox. A sonda usa `.pytest-tmp/qmly-run`, que é ignorado pelo Git.

## Achado que o registro original não tinha

O registro afirmava que o nome controlado pelo cliente em `os.path.join` "abre caminho para escrita
fora da pasta de upload", mas classificava isso como leitura de código. A sonda **provou por
gravação real**: enviar o nome `../ESCAPIU.ged` grava o arquivo em `qmly-run/ESCAPIU.ged`, **fora de
`uploads/`**, que fica vazia. O escape não é teórico.

---
*Gerado pelo Reversa-Debugger-Fix em 2026-10-02.*
