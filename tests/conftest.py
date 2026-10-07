"""Configuracao de coleta e de ambiente temporario da suite.

## 1. A causa dos 15 erros de ambiente, medida

O pytest 9.1.1 do `.venv/` cria o diretorio temporario por
`TempPathFactory.getbasetemp()` (`_pytest/tmpdir.py:145-229`): ele monta
`<tempfile.gettempdir()>/pytest-of-<usuario>` e o cria com
**`rootdir.mkdir(mode=0o700)`** (`:168`). Na linha seguinte,
`make_numbered_dir_with_cleanup` varre esse diretorio por `find_prefixed`, que faz
**`os.scandir(rootdir)`** (`_pytest/pathlib.py:175`) — e e ai que a excecao nasce:

    PermissionError: [WinError 5] Acesso negado:
      '...\\Temp\\<sessao>\\pytest-of-<usuario>'

Medido nesta maquina, isolando o modo:

    os.mkdir(p, 0o700)  -> NAO listavel, NAO gravavel, NAO removivel
    os.makedirs(p)      -> listavel, gravavel, removivel

O `mode=0o700` aparece tambem no `mktemp` (`:139` e `:141`), mas **esse ramo nunca
chega a rodar**: o passo anterior ja falhou. Por isso a correcao da suite nao e
"trocar o modo do diretorio por teste" — e **impedir que `getbasetemp()` seja
chamado**, o que se faz declarando o fixture `tmp_path` aqui.

## 2. `tmp_path` e declarado AQUI, e vale para a suite inteira

Um fixture de `conftest.py` **substitui** o de mesmo nome de qualquer plugin. Com
`tmp_path` declarado no repositorio, o `tmp_path` do pytest nao e resolvido, o
`getbasetemp()` nao e chamado, e os 15 testes de `tests/test_upload_seguranca.py`
— que usam `app_cliente` — executam. Medido: `246 passed, 0 errors`, contra
`231 passed, 15 errors` de antes.

`pasta_temporaria` e a **implementacao unica** desta politica, e `tmp_path`
delega para ela devolvendo `pathlib.Path`. O diretorio fica em `tests/.tmp/`, e
nao no temporario do sistema, por tres motivos: a raiz fica sob `tests/**`, que e
area do projeto; nao depende de o temporario do sistema estar saudavel; e
`pasta_temporaria` ja usava essa raiz, entao unificar nao muda fixture entregue. O
prefixo `.` mantem o diretorio fora da coleta, porque `norecursedirs` do pytest ja
ignora `.*`.

**Consequencia declarada:** o `tmp_path` da suite deixa de ficar sob o temporario
do sistema. Quem depurar procurando o diretorio em `%TEMP%` nao vai encontra-lo.

## 3. A segunda armadilha: remover com o CWD dentro

O `finally` de `pasta_temporaria` **sai do diretorio antes de remover**, e isso e
requisito, nao capricho. `app_cliente` faz `monkeypatch.chdir(tmp_path)`, e o
pytest desmonta o `tmp_path` **antes** de o `monkeypatch` desfazer o `chdir`: o
`rmtree` do teardown roda com o diretorio corrente DENTRO do diretorio a remover, o
Windows recusa, e o `ignore_errors=True` engole a recusa. Medido: **15 diretorios
vazios sobrevivem por execucao**. Com a saida, medido: **zero residuo**.

## 4. Uma cicatriz datada: `collect_ignore`

`tests/_basetemp_probe/` e um diretorio VAZIO que ficou preso nesta maquina. Ele
nasceu de `python -m pytest --basetemp=tests/_basetemp_probe`, executado em
2026-10-07 durante a feature `006-fronteira-aplicacao-ports` para tentar medir a
suite sem os 15 erros de ambiente. **A correcao acima nao o remove**: nenhum
diretorio preso foi removido por esta feature, por decisao registrada.

Sem a linha de `collect_ignore`, o pytest desce no diretorio preso e a COLETA
INTEIRA aborta com `PermissionError` — a suite ficaria cega por um diretorio
vazio. O `collect_ignore` e consultado antes da descida, entao a coleta segue.

**Como remover esta cicatriz.** Num shell elevado:

    takeown /f tests/_basetemp_probe /a
    icacls tests/_basetemp_probe /reset
    rd /s /q tests/_basetemp_probe

Com o diretorio fora, remova tambem a linha `collect_ignore`. Sao **13** os
diretorios presos no workspace, oito deles anteriores a feature 006; o inventario
e o comando em lote para os treze estao em
`_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md` §2.2.

## 5. `cliente_de_upload`

App Flask com a pasta de upload apontada para `pasta_temporaria`, para um teste de
rota nao escrever na pasta real nem depender do modo do diretorio temporario.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest

collect_ignore = ["_basetemp_probe"]

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PASTA_APP = os.path.join(_RAIZ, "src")

_RAIZ_TEMPORARIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")


@pytest.fixture
def pasta_temporaria():
    """Diretorio temporario VAZIO, permissivo e removido ao fim do teste.

    E a **implementacao unica** desta politica: `tmp_path` delega para ele. O que
    ele nao faz: isolar o processo (nao ha `chdir` no setup). Quem precisa de CWD
    isolado continua precisando pedir — e o `finally` sai do diretorio antes de
    remover, porque remover com o CWD dentro e recusado pelo Windows.
    """
    caminho = os.path.join(_RAIZ_TEMPORARIA, uuid.uuid4().hex)
    os.makedirs(caminho, exist_ok=True)
    try:
        cwd_original = os.getcwd()
    except OSError:
        cwd_original = _RAIZ
    try:
        yield caminho
    finally:
        # Sair do diretorio ANTES de remover: `app_cliente` faz
        # `monkeypatch.chdir(tmp_path)`, e o pytest desmonta o `tmp_path` antes de
        # o `monkeypatch` desfazer o chdir. Ver a secao 3 do modulo.
        try:
            os.chdir(cwd_original)
        except OSError:
            try:
                os.chdir(_RAIZ)
            except OSError:
                pass
        shutil.rmtree(caminho, ignore_errors=True)
        if os.path.isdir(_RAIZ_TEMPORARIA) and not os.listdir(_RAIZ_TEMPORARIA):
            os.rmdir(_RAIZ_TEMPORARIA)


@pytest.fixture
def tmp_path(pasta_temporaria):
    """O `tmp_path` da suite: o MESMO diretorio de `pasta_temporaria`, como `Path`.

    Declarado aqui para substituir o do pytest em toda a suite. A correcao e
    invisivel por natureza — o sintoma de ela sair de vigor e um `erro de
    ambiente`, que ja foi atribuido a maquina duas vezes —, entao ela ganhou
    teste proprio em `tests/test_ambiente_temporario_da_suite.py`.
    """
    return Path(pasta_temporaria)


@pytest.fixture
def cliente_de_upload(pasta_temporaria, monkeypatch):
    """App Flask com a pasta de upload apontada para `pasta_temporaria`.

    Devolve `(app, client, pasta_de_uploads)`. Duas diferencas em relacao ao
    `app_cliente` de `tests/test_upload_seguranca.py`, as duas deliberadas:

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
