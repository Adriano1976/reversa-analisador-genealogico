"""Guardas estruturais do nucleo puro de `src/core/` (RF-01, RF-08, RF-09).

Estes testes NAO exercitam comportamento de dominio — para isso existe o harness
diferencial. O que eles guardam e a FORMA do nucleo, que e o objeto da feature
`005-nucleo-puro-src` (Onda 1 do cutover): sem estado global, sem I/O, sem
framework e sem dependencia de `parsers/` ou `reporting/`.

## Por que inspecao por AST, e nao import

Importar cada modulo executaria efeitos colaterais e faria o teste depender de
poder importar o modulo. A pergunta aqui e textual — "que imports este arquivo
declara?" — e a AST responde isso sem executar nada. E o mesmo metodo que
`tests/test_servidor_producao.py` usa para a camada de rota.

## Por que T007 nasceu com xfail

A afirmacao de estado global foi escrita para FALHAR enquanto o estado existia, e
passar ao final da migracao. Uma falha deliberada e permanente deixaria a suite
vermelha entre `T007` e `T023`, o que cegaria as verificacoes seguintes: a
proxima acao que rodar a suite nao distinguiria a falha esperada de uma
regressao real.

`xfail(strict=True)` resolveu as duas pontas: a suite ficou verde, e a afirmacao
continuou DISCRIMINANTE — escrita frouxa, ela passaria por engano e o `strict`
transformaria o XPASS em falha. O `T023` removeu o marcador, e o teste passa por
merito proprio.
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(RAIZ, "src", "core")

# Pacotes de infraestrutura que o nucleo NAO pode importar. A decisao esta em
# `_reversa_sdd/migration/topology_decision.md` secao "Decisao do usuario":
# "core/ nao pode importar fastapi, sqlalchemy, pydantic nem flask. Violacao
# invalida a Onda 0 e deve ser detectada por teste automatico."
FRAMEWORKS_PROIBIDOS = {"flask", "fastapi", "sqlalchemy", "pydantic", "waitress"}

# Pacotes do proprio projeto dos quais o nucleo deve se desacoplar (RF-09). A
# leitura de CSV e a emissao de diagrama passam a ser entregues pela borda.
PACOTES_PROIBIDOS = {"parsers", "reporting"}

# Efeitos de I/O e de plataforma proibidos no nucleo (RN-04, RNF de portabilidade).
FUNCOES_IO = {"open", "input"}
MODULOS_IO = {"socket", "requests", "urllib", "http", "shutil"}
ATRIBUTOS_IO = {
    ("os", "environ"), ("os", "getenv"), ("os", "makedirs"), ("os", "remove"),
    ("os", "system"), ("os", "popen"), ("os", "listdir"), ("os", "chdir"),
    ("os", "path"), ("os", "mkdir", ),
}

# Nomes que materializam o estado global que a feature remove (RF-01).
NOMES_DE_ESTADO = {"people", "families", "graph", "child_to_family", "versao"}


def _modulos_do_core():
    if not os.path.isdir(CORE):
        raise AssertionError("diretorio do nucleo nao encontrado: %s" % CORE)
    return sorted(f for f in os.listdir(CORE) if f.endswith(".py"))


def _arvore(nome):
    caminho = os.path.join(CORE, nome)
    with open(caminho, encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=caminho)


def _imports(tree):
    """Devolve os modulos importados, absolutos e relativos.

    Import relativo (`from .gedcom_state import x`) nao e dependencia de fora do
    pacote e nao entra aqui: o alvo desta guarda e o que VEM DE FORA do core.
    """
    nomes = set()
    for no in ast.walk(tree):
        if isinstance(no, ast.Import):
            for alias in no.names:
                nomes.add(alias.name.split(".")[0])
        elif isinstance(no, ast.ImportFrom):
            if no.level == 0 and no.module:
                nomes.add(no.module.split(".")[0])
    return nomes


# --------------------------------------------------------------------------
# T005 — nenhum framework de infraestrutura no nucleo (RF-08)
# --------------------------------------------------------------------------

def test_core_nao_importa_framework():
    achados = []
    for nome in _modulos_do_core():
        proibidos = sorted(_imports(_arvore(nome)) & FRAMEWORKS_PROIBIDOS)
        if proibidos:
            achados.append("%s importa %s" % (nome, ", ".join(proibidos)))
    assert not achados, (
        "o nucleo passou a depender de infraestrutura; a paridade deixa de ser "
        "isolavel e a Onda 0 perde valor:\n  " + "\n  ".join(achados)
    )


def test_guarda_detecta_framework_quando_introduzido():
    """Caminho negativo: a guarda acima precisa ser capaz de FALHAR.

    Sem esta prova, a assercao poderia estar olhando para o lugar errado e
    passando por vacuidade — que e o defeito que o `parity_harness.md` registrou
    na suite antiga (a assercao `in ("Sem Nome", "")` nao podia falhar).
    """
    fonte = "import flask\n"
    arvore = ast.parse(fonte)
    assert _imports(arvore) & FRAMEWORKS_PROIBIDOS == {"flask"}


# --------------------------------------------------------------------------
# T006 — nenhum I/O e nenhuma dependencia de plataforma no nucleo (RN-04)
# --------------------------------------------------------------------------

def test_core_nao_faz_io():
    achados = []
    for nome in _modulos_do_core():
        arvore = _arvore(nome)
        for no in ast.walk(arvore):
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name):
                if no.func.id in FUNCOES_IO:
                    achados.append("%s chama %s()" % (nome, no.func.id))
            elif isinstance(no, ast.Attribute) and isinstance(no.value, ast.Name):
                if (no.value.id, no.attr) in ATRIBUTOS_IO:
                    achados.append("%s usa %s.%s" % (nome, no.value.id, no.attr))
        proibidos = sorted(_imports(arvore) & MODULOS_IO)
        if proibidos:
            achados.append("%s importa %s" % (nome, ", ".join(proibidos)))
    assert not achados, (
        "o nucleo passou a fazer I/O ou a depender de plataforma; ele deve ser "
        "executavel sobre estruturas em memoria:\n  " + "\n  ".join(achados)
    )


def test_guarda_de_io_detecta_open():
    arvore = ast.parse("dados = open('x')\n")
    chamadas = [n.func.id for n in ast.walk(arvore)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "open" in chamadas


# --------------------------------------------------------------------------
# T007 — nenhum estado mutavel de modulo no nucleo (RF-01)
# --------------------------------------------------------------------------

def _nomes_de_estado_no_modulo(nome):
    """Nomes de estado atribuidos no NIVEL DO MODULO, em qualquer forma.

    Cobre `x = {}`, `x: dict = {}` e `x = y = {}`, porque as tres materializam
    estado. Nao olha dentro de funcoes: um dicionario local e valor, nao estado.
    """
    achados = []
    for no in _arvore(nome).body:
        alvos = []
        if isinstance(no, ast.Assign):
            alvos = no.targets
        elif isinstance(no, ast.AnnAssign):
            alvos = [no.target]
        for alvo in alvos:
            if isinstance(alvo, ast.Name) and alvo.id in NOMES_DE_ESTADO:
                achados.append("%s:%d  %s" % (nome, no.lineno, alvo.id))
    return achados


def test_guarda_de_estado_detecta_atribuicao_no_nivel_do_modulo():
    """Caminho negativo da guarda de T007 — esta e a parte que NAO pode falhar.

    Ela prova que a afirmacao abaixo e discrimina: aplicada a uma fonte que
    declara estado, ela encontra.
    """
    arvore = ast.parse("people = {}\nfamilies: dict = {}\ngraph = None\n")
    encontrados = set()
    for no in arvore.body:
        alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
        for alvo in alvos:
            if isinstance(alvo, ast.Name) and alvo.id in NOMES_DE_ESTADO:
                encontrados.add(alvo.id)
    assert encontrados == {"people", "families", "graph"}


def test_core_nao_declara_estado_mutavel_de_modulo():
    """`RF-01`: nenhum modulo do nucleo declara estado mutavel de modulo.

    Nasceu em `T007` com `xfail(strict=True)`, porque a condicao era falsa: o
    estado existia em `core/gedcom_state.py`. O `T023` apagou o modulo depois de
    migrar os consumidores para a arvore por parametro, e o marcador saiu aqui —
    o teste passa por merito proprio.

    O que ele guarda, daqui em diante: o nucleo e um conjunto de FUNCOES sobre a
    arvore que o chamador entrega. Uma variavel de modulo com um destes nomes
    reintroduziria o acoplamento por efeito colateral que custou a `D-11`.
    """
    achados = []
    for nome in _modulos_do_core():
        achados.extend(_nomes_de_estado_no_modulo(nome))
    assert not achados, (
        "o nucleo voltou a declarar estado mutavel de modulo. Ele deve receber a "
        "arvore por parametro (RF-01):\n  " + "\n  ".join(achados)
    )


# --------------------------------------------------------------------------
# T005 (parte) — nenhuma dependencia de `parsers/` ou `reporting/` (RF-09)
# --------------------------------------------------------------------------

def test_core_nao_importa_parsers_nem_reporting():
    """`RF-09`: o nucleo nao depende de `parsers/` nem de `reporting/`.

    Este teste nasceu em `T007` com `xfail(strict=True)`, porque a condicao era
    falsa: medido em 2026-10-06, `dna_analysis.py` importava os dois e
    `path_search.py` importava `reporting`. O `T016` e o `T017` injetaram a
    leitura de CSV e a emissao do diagrama pela borda, e o marcador foi removido
    aqui — o teste passa por merito proprio.

    O `strict` cumpriu o papel: no instante em que o import proibido sumiu, o
    XPASS virou falha e avisou que era hora de tirar o marcador. Sem ele, um
    `xfail` esquecido esconderia a regressao de volta.
    """
    achados = []
    for nome in _modulos_do_core():
        proibidos = sorted(_imports(_arvore(nome)) & PACOTES_PROIBIDOS)
        if proibidos:
            achados.append("%s importa %s" % (nome, ", ".join(proibidos)))
    assert not achados, (
        "o nucleo voltou a depender de `parsers/` ou `reporting/` (RF-09):\n  "
        + "\n  ".join(achados)
    )


# --------------------------------------------------------------------------
# T030 — o harness RECUSA paridade quando ha divergencia
# --------------------------------------------------------------------------
# O `cutover_plan.md` e categorico: qualquer divergencia de paridade em aberto e
# No-go absoluto, "mesmo com aparencia de melhoria sobre o legado". Isso so vale
# se o instrumento realmente falhar quando encontra divergencia. Medir 100% sem
# provar que o instrumento consegue reprovar seria confiar num detector nao
# testado — o mesmo defeito da assercao que nao podia falhar.

_HARNESS = os.path.join(RAIZ, "_reversa_sdd", "parity", "harness.py")


def _importar_comparador():
    """Carrega `compare` do harness sem executar a coleta."""
    import importlib.util

    argv = sys.argv
    # O harness le os argumentos no nivel do modulo. Passamos um conjunto valido
    # so para o import nao falhar; nenhuma coleta chega a rodar.
    sys.argv = ["harness.py", "--gedcom", "", "--json", "", "[]", ""]
    try:
        spec = importlib.util.spec_from_file_location("_parity_harness", _HARNESS)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    finally:
        sys.argv = argv
    return modulo.compare


def test_comparador_aprova_observacoes_iguais():
    compare = _importar_comparador()
    obs = {
        "person_count": 3, "family_count": 1, "names": ["Ana Silva"],
        "graph": {"nodes": 3, "edges": 2}, "child_to_family": {"@I2@": ["@F1@"]},
        "cm": {"300": ["Primos de 1o grau"]}, "ancestral": {}, "indirect": {}, "dna": {},
    }
    assert compare(obs, obs) == [], (
        "o comparador acusou divergencia entre observacoes IDENTICAS; ele esta "
        "produzindo falso positivo, e todo relatorio de paridade fica suspeito"
    )


def test_comparador_reprova_divergencia_de_um_unico_valor():
    """A prova central: um unico valor diferente tem de aparecer como divergencia."""
    compare = _importar_comparador()
    base = {
        "person_count": 3, "family_count": 1, "names": ["Ana Silva"],
        "graph": {"nodes": 3, "edges": 2}, "child_to_family": {},
        "cm": {"300": ["Primos de 1o grau"]}, "ancestral": {}, "indirect": {}, "dna": {},
    }
    divergente = dict(base, person_count=4)
    diffs = compare(base, divergente)
    assert diffs, "divergencia de person_count NAO foi reportada — o detector esta cego"
    assert any("person_count" in chave for chave, _ in diffs), diffs


def test_comparador_reprova_divergencia_na_analise_de_dna():
    """Divergencia dentro do probe `dna`, que e o mais novo e o mais fundo."""
    compare = _importar_comparador()
    base = {
        "person_count": 3, "family_count": 1, "names": [], "graph": {},
        "child_to_family": {}, "cm": {}, "ancestral": {}, "indirect": {},
        "dna": {"utf8.csv": {"success": True, "modo": "ok",
                             "results": [{"match_name": "Ana Silva", "cm": 200, "caminho": "Ana Silva"}],
                             "descartados": []}},
    }
    divergente = {
        "person_count": 3, "family_count": 1, "names": [], "graph": {},
        "child_to_family": {}, "cm": {}, "ancestral": {}, "indirect": {},
        "dna": {"utf8.csv": {"success": True, "modo": "ok",
                             "results": [{"match_name": "Ana Silva", "cm": 201, "caminho": "Ana Silva"}],
                             "descartados": []}},
    }
    diffs = compare(base, divergente)
    assert diffs, "um centimo de diferenca no cM do probe `dna` NAO foi reportado"
    assert any(chave.startswith("dna[utf8.csv]") for chave, _ in diffs), diffs
