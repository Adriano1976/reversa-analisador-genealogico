"""Configuracao de coleta e de ambiente temporario da suite.

## Por que este arquivo existe (duas razoes, as duas medidas)

### 1. Uma cicatriz datada: `collect_ignore`

`tests/_basetemp_probe/` e um diretorio VAZIO que ficou preso nesta maquina. Ele
nasceu de `python -m pytest --basetemp=tests/_basetemp_probe`, executado em
2026-10-07 durante a feature `006-fronteira-aplicacao-ports` para tentar medir a
suite sem os 15 erros de ambiente.

Nesta maquina, `os.mkdir(caminho, 0o700)` cria um diretorio que **nao pode ser
listado nem apagado** — nem pelo dono, nem por `icacls /reset`, nem por
`takeown`, nem por `rd /s /q`. Verificado com um diretorio novo, fora de qualquer
duvida: o defeito e da combinacao Windows + Python 3.14 desta estacao, e nao do
projeto. E **a mesma causa** dos 15 erros de ambiente de
`tests/test_upload_seguranca.py`, porque o `tmp_path_factory` do pytest cria o
diretorio-base com `mode=0o700`.

Sem a linha de `collect_ignore`, o pytest desce no diretorio preso e a COLETA
INTEIRA aborta com `PermissionError` — a suite ficaria cega por um diretorio
vazio. O `collect_ignore` e consultado antes da descida, entao a coleta segue.

**Como remover esta cicatriz.** Num shell elevado:

    takeown /f tests/_basetemp_probe /a
    icacls tests/_basetemp_probe /reset
    rd /s /q tests/_basetemp_probe

Com o diretorio fora, remova tambem a linha `collect_ignore`.

### 2. `pasta_temporaria`: diretorio temporario que funciona NESTA maquina

`tmp_path` e o idioma da casa e continua sendo o certo em ambiente saudavel — mas
aqui ele nao funciona: o `0o700` do pytest deixa o diretorio inacessivel, e o
teste que dependa dele nem chega a rodar. `pasta_temporaria` cria o diretorio com
`os.makedirs` no modo padrao, que e listavel, gravavel e removivel de verdade.

O diretorio fica em `tests/.tmp/`, e nao no temporario do sistema, por dois
motivos: o sandbox desta sessao e o `0o700` tornam o temporario do sistema
inutilizavel, e `tests/**` e area do projeto. O prefixo `.` mantem o diretorio
fora da coleta, porque `norecursedirs` do pytest ja ignora `.*`.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import uuid

import pytest

collect_ignore = ["_basetemp_probe"]

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PASTA_APP = os.path.join(_RAIZ, "src")

_RAIZ_TEMPORARIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")


@pytest.fixture
def pasta_temporaria():
    """Diretorio temporario VAZIO, permissivo e removido ao fim do teste.

    Use no lugar de `tmp_path` em teste novo. O que ele nao faz: isolar o
    processo (nao ha `chdir`). Quem precisa de CWD isolado continua precisando
    pedir — e nessa maquina nao consegue, pelo mesmo defeito de `0o700`.
    """
    caminho = os.path.join(_RAIZ_TEMPORARIA, uuid.uuid4().hex)
    os.makedirs(caminho, exist_ok=True)
    try:
        yield caminho
    finally:
        shutil.rmtree(caminho, ignore_errors=True)
        if os.path.isdir(_RAIZ_TEMPORARIA) and not os.listdir(_RAIZ_TEMPORARIA):
            os.rmdir(_RAIZ_TEMPORARIA)


@pytest.fixture
def cliente_de_upload(pasta_temporaria, monkeypatch):
    """App Flask com a pasta de upload apontada para `pasta_temporaria`.

    Devolve `(app, client, pasta_de_uploads)`. Existe porque o fixture
    `app_cliente` de `tests/test_upload_seguranca.py` depende de `tmp_path`, que
    **nao funciona nesta maquina** (`0o700`) — os 15 erros de ambiente da linha de
    base sao exatamente isso. Um teste novo que use `app_cliente` nasce quebrado
    aqui e nao mede nada; este nasce funcionando.

    Duas diferencas em relacao ao `app_cliente`, as duas deliberadas:

    - **Sem `chdir`.** A pasta de upload e apontada por caminho ABSOLUTO, entao o
      diretorio corrente nao participa da resolucao. O `chdir` do outro fixture
      vem de quando a pasta era relativa ao CWD; nao e mais necessario.
    - **`root_path` fixado no `app.py`.** `spec_from_file_location` nao define
      `__file__`, e sem ele o Flask nao acha `templates/`. O outro fixture resolve
      isso do mesmo jeito.
    """
    pasta_de_uploads = os.path.join(pasta_temporaria, "uploads")
    monkeypatch.setenv("ANALISADOR_UPLOAD_FOLDER", pasta_de_uploads)
    if _RAIZ not in sys.path:
        sys.path.insert(0, _RAIZ)
    if _PASTA_APP not in sys.path:
        sys.path.insert(0, _PASTA_APP)

    caminho = os.path.join(_PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location("_app_conftest006", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = _PASTA_APP
    # O import acima cria a pasta; garantir aqui tambem cobre o caso de o app
    # passar a resolve-la de outro jeito.
    os.makedirs(pasta_de_uploads, exist_ok=True)
    return modulo.app, modulo.app.test_client(), pasta_de_uploads
