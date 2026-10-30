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
delega para ela devolvendo `pathlib.Path`.

**A raiz mudou para o temporario do sistema em 2026-10-19 (feature 034).** Ela ficava em
`tests/.tmp/` com tres justificativas: ficar sob `tests/**`, nao depender do temporario do
sistema e preservar a raiz que `pasta_temporaria` ja usava. A primeira caiu por medicao: o
sandbox de escrita do harness recusa **criar subdiretorio** dentro do workspace, e
`os.makedirs(tests/.tmp/<uuid>)` passou a levantar `PermissionError` — 408 testes morriam no
preparo, antes de qualquer assercao. A segunda nao se sustenta: o que quebrava no temporario do
sistema era o `getbasetemp()` do pytest criando a raiz com `mode=0o700` (§1), e esse caminho
nao e mais usado desde que `tmp_path` e declarado aqui; criar a pasta com `os.makedirs` (o que
`pasta_temporaria` faz) funciona. A terceira e irrelevante: a raiz e interna ao fixture, e
nenhum teste a recebe pronta.

**Consequencia declarada:** o `tmp_path` da suite fica em `%TEMP%/reversa-analisador-testes`,
e nao sob `tests/`. A entrada `tests/.tmp/` do `.gitignore` fica como historico.

## 3. A segunda armadilha: remover com o CWD dentro

O `finally` de `pasta_temporaria` **sai do diretorio antes de remover**, e isso e
requisito, nao capricho. `app_cliente` faz `monkeypatch.chdir(tmp_path)`, e o
pytest desmonta o `tmp_path` **antes** de o `monkeypatch` desfazer o `chdir`: o
`rmtree` do teardown roda com o diretorio corrente DENTRO do diretorio a remover, o
Windows recusa, e o `ignore_errors=True` engole a recusa. Medido: **15 diretorios
vazios sobrevivem por execucao**. Com a saida, medido: **zero residuo**.

## 4. A cicatriz datada, fechada em 2026-10-08

`tests/_basetemp_probe/` nasceu de `python -m pytest --basetemp=tests/_basetemp_probe`,
executado em 2026-10-07 durante a feature `006-fronteira-aplicacao-ports`, e ficou preso
nesta maquina. Enquanto ele existiu, o `collect_ignore` era obrigatorio: o pytest desce no
diretorio, a ACL recusa o `os.scandir` e a COLETA INTEIRA aborta com `PermissionError`, o
que deixaria a suite cega por causa de um diretorio vazio.

**O diretorio foi removido e a linha `collect_ignore` saiu junto.** O procedimento que
funcionou, medido naquele dia: `takeown /f <dir> /a` seguido de `icacls <dir> /reset`, os
dois num shell elevado, o que devolve as permissoes herdadas ao diretorio. A remocao em si
funciona depois, sem elevacao. Registro completo, com o inventario daquele dia e a
armadilha do `rd` do PowerShell, em
`_reversa_forward/006-fronteira-aplicacao-ports/evidence/limpeza-2026-10-08-diretorios-presos.md`.

**Se um diretorio preso voltar a aparecer sob `tests/`**, o sintoma e a coleta inteira
abortando com `PermissionError` num diretorio que parece vazio. A saida e a mesma receita
acima, e nao reintroduzir `collect_ignore`.

## 5. `cliente_de_upload`

App Flask com a pasta de upload apontada para `pasta_temporaria`, para um teste de
rota nao escrever na pasta real nem depender do modo do diretorio temporario.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PASTA_APP = os.path.join(_RAIZ, "src")

# Os modulos de `src/` sao importados pelo nome curto (`utils.logs`, `core.erros`,
# `ports.adaptadores`). Vários arquivos de teste repetiam a insercao no topo; declarar aqui,
# no import do `conftest` (que o pytest faz antes de coletar), garante que qualquer modulo
# novo possa importar `src/` sem repetir a cerimonia.
for _caminho in (_RAIZ, _PASTA_APP):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

# Ver §2 do docstring: a raiz temporaria vive no temporario do sistema desde a
# feature 034, porque o sandbox de escrita do harness recusa criar subdiretorio
# dentro do workspace — e era ali que `tests/.tmp/` ficava.
_RAIZ_TEMPORARIA = os.path.join(tempfile.gettempdir(), "reversa-analisador-testes")

# Feature 049: a pasta de log da aplicacao e ancorada na RAIZ do projeto, e o
# `configurar()` a cria no primeiro `create_app()` — que acontece na IMPORTACAO de
# `src/app.py`. Como varios testes importam o app no nivel do modulo (antes de qualquer
# fixture), isolar por fixture chegaria tarde: a pasta `logs/` nasceria na raiz do
# repositorio. Por isso a variavel e fixada AQUI, no import do `conftest`, que o pytest
# faz antes de coletar os modulos de teste.
os.environ.setdefault(
    "ANALISADOR_LOG_DIR", os.path.join(_RAIZ_TEMPORARIA, "logs-da-suite")
)

# Auditoria de 2026-10-30 (P1/P3): a aplicacao passou a exigir modo de identidade
# DECLARADO, e a declaracao mora em `create_app`, nao no `__main__`. A suite importa
# `src/app.py` sem credencial de proposito — os 1939 testes dependem do caminho legado —,
# e por isso declara o escape de teste AQUI, no import do conftest, antes de qualquer
# modulo de teste ser coletado. Sem estas linhas, `import app` levanta "Recusando subir".
#
# `pop` e `=`, e nao `setdefault`: se a maquina tiver `ANALISADOR_MODO` exportado, a
# suite inteira mudaria de caminho por causa do ambiente. O caminho da suite e o legado,
# sempre, e ele e declarado aqui — nao herdado.
os.environ.pop("ANALISADOR_MODO", None)
os.environ["ANALISADOR_MODO_TESTE"] = "1"


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


@pytest.fixture
def app_autenticado(pasta_temporaria, monkeypatch):
    """App com a entrada LIGADA e provedor falso (feature 051).

    Devolve um namespace com `app`, `cliente`, `pasta`, `provedor` e `entrar(conta)`.
    O provedor falso e o que impede a suite de falar com a rede: nenhum teste desta
    feature chama o Google. A pasta de upload e temporaria, como no
    `cliente_de_upload`, e o modulo e importado de novo para a borda nascer com a
    autenticacao injetada.
    """
    from types import SimpleNamespace

    from tests.fixtures.autenticacao import ProvedorFalso, entrar_como, servico_de_teste
    from tests.fixtures.identidade import ContasEmMemoria, EmailDesligado, RelogioFalso

    pasta_de_uploads = os.path.join(pasta_temporaria, "uploads")
    monkeypatch.setenv("ANALISADOR_UPLOAD_FOLDER", pasta_de_uploads)
    for _caminho in (_RAIZ, _PASTA_APP):
        if _caminho not in sys.path:
            sys.path.insert(0, _caminho)

    caminho = os.path.join(_PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location("_app_conftest051", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = _PASTA_APP

    provedor = ProvedorFalso()
    aplicacao = modulo.create_app(
        autenticacao=servico_de_teste(provedor),
        contas=ContasEmMemoria(),
        email=EmailDesligado(),
        relogio=RelogioFalso(),
    )
    # `create_app` monta uma instancia NOVA: o `root_path` do modulo nao chega nela,
    # e sem isto o Jinja nao acha `templates/` (o mesmo motivo do `cliente_de_upload`).
    aplicacao.root_path = _PASTA_APP
    os.makedirs(pasta_de_uploads, exist_ok=True)

    cliente = aplicacao.test_client()
    return SimpleNamespace(
        app=aplicacao,
        cliente=cliente,
        pasta=pasta_de_uploads,
        provedor=provedor,
        entrar=lambda conta: entrar_como(cliente, provedor, conta),
    )


@pytest.fixture
def app_com_contas(pasta_temporaria, monkeypatch):
    """App com a entrada e as contas LIGADAS, sobre dubles (feature 053).

    Devolve um namespace com `app`, `cliente`, `pasta`, `provedor`, `contas`,
    `email`, `relogio` e `entrar(conta)`. Nenhum teste desta feature escreve no
    arquivo real, fala com SMTP ou espera o relogio: as tres dependencias entram
    pelas portas, pelo mesmo `create_app` que a producao usa.
    """
    from types import SimpleNamespace

    from tests.fixtures.autenticacao import ProvedorFalso, entrar_como, servico_de_teste
    from tests.fixtures.identidade import ContasEmMemoria, EmailQueGrava, RelogioFalso

    pasta_de_uploads = os.path.join(pasta_temporaria, "uploads")
    monkeypatch.setenv("ANALISADOR_UPLOAD_FOLDER", pasta_de_uploads)
    for _caminho in (_RAIZ, _PASTA_APP):
        if _caminho not in sys.path:
            sys.path.insert(0, _caminho)

    caminho = os.path.join(_PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location("_app_conftest053", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = _PASTA_APP

    provedor = ProvedorFalso()
    relogio = RelogioFalso()
    contas = ContasEmMemoria(relogio=relogio)
    email = EmailQueGrava()

    aplicacao = modulo.create_app(
        autenticacao=servico_de_teste(provedor),
        contas=contas,
        email=email,
        relogio=relogio,
    )
    aplicacao.root_path = _PASTA_APP
    os.makedirs(pasta_de_uploads, exist_ok=True)

    cliente = aplicacao.test_client()
    return SimpleNamespace(
        app=aplicacao,
        cliente=cliente,
        pasta=pasta_de_uploads,
        provedor=provedor,
        contas=contas,
        email=email,
        relogio=relogio,
        entrar=lambda conta: entrar_como(cliente, provedor, conta),
    )
