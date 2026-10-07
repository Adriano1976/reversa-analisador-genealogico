"""Testes do diretorio temporario da suite (acao `T003`).

Este arquivo existe porque a correcao que ele prende e **invisivel**: o sintoma de
ela sair de vigor e um `erro de ambiente` no *setup*, e nao uma falha de
asserção. Esse sintoma ja foi atribuido a maquina **duas vezes** — na feature 005
e na 006 —, e o custo foi a suite inteira cega em 15 testes da superficie que a
Onda 2 tinha acabado de reescrever.

O que se mede aqui e a **propriedade**, nao a implementacao: onde o diretorio vive
e o que da para fazer com ele. Um upgrade do pytest, ou alguem removendo o fixture
`tmp_path` de `tests/conftest.py` por ele parecer redundante com o do pytest,
quebra estes testes antes de quebrar a suite em silencio.

A causa medida esta na secao 1 do docstring de `tests/conftest.py`: o
`TempPathFactory.getbasetemp()` do pytest cria `pytest-of-<usuario>` com
`mode=0o700`, e nesta maquina um diretorio `0o700` nao pode ser **listado** — o
`os.scandir` de `_pytest/pathlib.py:175` levanta `PermissionError [WinError 5]`.
"""
import os
import sys
import tempfile
from pathlib import Path

RAIZ_DO_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_TEMPORARIA_ESPERADA = Path(RAIZ_DO_PROJETO) / "tests" / ".tmp"


def test_tmp_path_vive_sob_o_projeto(tmp_path):
    """O `tmp_path` da suite e o do projeto, e nao o diretorio-base do pytest.

    Duas assercoes, e as duas sao necessarias:

    - `RAIZ_TEMPORARIA_ESPERADA in tmp_path.parents` fixa **onde** o diretorio
      vive. E o que prova que o fixture de `tests/conftest.py` esta em vigor: o
      `tmp_path` do pytest nunca produziria um caminho sob `tests/`.
    - Nenhuma parte do caminho pode ser `pytest-of-*`. E a assercão que nomeia o
      defeito: e exatamente esse diretorio, criado com `0o700`, que o `os.scandir`
      nao consegue ler. Sem ela, uma mudanca futura que apontasse a raiz para
      `<temp>/pytest-of-<usuario>` continuaria passando pela primeira assercao se
      ela fosse reescrita por engano.
    """
    assert RAIZ_TEMPORARIA_ESPERADA in tmp_path.parents, (
        "o tmp_path da suite saiu de tests/.tmp/: o fixture declarado em "
        "tests/conftest.py nao esta em vigor, e o do pytest — que cria o "
        "diretorio-base com 0o700 e falha ao lista-lo nesta maquina — voltou a "
        "ser resolvido"
    )
    assert not any(p.startswith("pytest-of-") for p in tmp_path.parts), (
        f"o tmp_path aponta para o diretorio-base do pytest: {tmp_path}. E esse "
        "diretorio que nao pode ser listado nesta maquina (PermissionError "
        "[WinError 5] em _pytest/pathlib.py:175)"
    )


def test_tmp_path_e_listavel_gravavel_e_removivel(tmp_path):
    """As tres operacoes que o diretorio `0o700` do pytest recusa, uma a uma.

    A sonda que mediu a causa produziu exatamente esta tabela:

        os.mkdir(p, 0o700)  -> NAO listavel, NAO gravavel, NAO removivel
        os.makedirs(p)      -> listavel, gravavel, removivel

    Este teste exige a segunda linha da tabela, e nao uma impressao sobre ela.
    `os.listdir` e o mesmo `os.scandir` que levanta no pytest, entao ele mede a
    operacao exata que falhava.
    """
    assert tmp_path.is_dir(), "o diretorio temporario nao foi criado"

    assert os.listdir(tmp_path) == [], "o diretorio temporario nasceu sujo"

    arquivo = tmp_path / "sonda.txt"
    arquivo.write_text("ok", encoding="utf-8")
    assert arquivo.read_text(encoding="utf-8") == "ok"
    assert os.listdir(tmp_path) == ["sonda.txt"]

    arquivo.unlink()
    assert os.listdir(tmp_path) == []


def test_tmp_path_e_pasta_temporaria_sao_a_mesma_politica(tmp_path, pasta_temporaria):
    """As duas portas de entrada levam ao MESMO diretorio, e a uma raiz so.

    **Esta assercao nasceu errada, e a suite provou.** A primeira versao exigia
    `tmp_path != Path(pasta_temporaria)`, supondo dois diretorios independentes no
    mesmo teste. Nao sao: o pytest **cacheia a instancia do fixture** por teste,
    entao pedir `tmp_path` e `pasta_temporaria` no mesmo teste devolve o **mesmo**
    objeto — e isso e exatamente o que `D-02` quis dizer com "implementacao unica".
    Cada teste continua recebendo um diretorio proprio, porque `pasta_temporaria` e
    de escopo de funcao; o que nao existe e um diretorio *por nome de fixture*.

    As tres assercoes prendem, cada uma, uma coisa distinta:

    - `Path(pasta_temporaria) == tmp_path` — os dois nomes sao a mesma politica, e
      `tmp_path` de fato delega para `pasta_temporaria`.
    - `os.path.dirname(pasta_temporaria) == tmp_path.parent` — a raiz e unica, e
      nao duas raizes que por acaso coincidem.
    - a raiz nao esta sob o temporario do sistema — `D-02` ancorou em
      `tests/.tmp/`, e nao em `tempfile.gettempdir()`, para a politica nao depender
      de o temporario do sistema estar saudavel nem de ele conter um
      `pytest-of-<usuario>` preso de execucao anterior.
    """
    assert isinstance(pasta_temporaria, str), (
        "pasta_temporaria deixou de devolver str; cliente_de_upload e os testes "
        "existentes a usam com os.path.join"
    )
    assert Path(pasta_temporaria) == tmp_path, (
        "tmp_path e pasta_temporaria apontaram para diretorios diferentes no "
        "mesmo teste: os dois deixaram de ser a mesma politica (D-02)"
    )
    assert os.path.dirname(pasta_temporaria) == str(tmp_path.parent), (
        "tmp_path e pasta_temporaria deixaram de compartilhar a raiz: a politica "
        "de diretorio temporario da suite se dividiu em duas"
    )
    assert Path(tempfile.gettempdir()).resolve() not in tmp_path.resolve().parents, (
        f"o tmp_path da suite foi para o temporario do sistema: {tmp_path}. "
        "D-02 ancorou a raiz em tests/.tmp/"
    )
