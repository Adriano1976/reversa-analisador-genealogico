"""O indice de nomes e preso a arvore, e nao um cache de modulo (feature 048).

## O defeito que este arquivo guarda

Ate a feature 048 o indice era um cache de modulo chaveado por
`(len(people), primeira chave, ultima chave)`. Duas arvores com o mesmo numero de pessoas e os
mesmos xrefs extremos produziam a mesma chave, e o dossie da segunda citava xrefs da primeira —
sem excecao e sem aviso. Confirmado por execucao em 2026-10-10: o dossie da segunda respondeu
`exact_count: 1` citando `@I2@`, que **nao existia nela**, e a ficha degradou para "Sem Nome".

## O que passou a valer

O mapa e preso ao grafo da arvore (`arvore[2]`), como `fichas_da_pessoa._indice_de_filhos` e os
indices de matching da feature 047. Nao ha chave, entao nao ha o que colidir.

## O que este arquivo substitui

As guardas de 2026-10-24 liam o modulo por AST e exigiam a tupla `_INDICE_DE_NOMES` publicada num
unico gesto — elas protegiam a CORRIDA daquele desenho. Sem estado de modulo nao ha publicacao,
nao ha janela e nao ha o que trocar; a guarda estrutural agora e a **ausencia** do estado.
"""
from __future__ import annotations

import ast
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import homonimos  # noqa: E402

CAMINHO_DO_MODULO = os.path.join(RAIZ, "src", "core", "homonimos.py")


class _Nome:
    """A unica coisa que `get_name` usa de um nome: `.format()`."""

    def __init__(self, texto: str) -> None:
        self._texto = texto

    def format(self) -> str:
        return self._texto


class _Pessoa:
    """A unica coisa que o indice de nomes usa de uma pessoa: `.name`."""

    def __init__(self, nome: str) -> None:
        self.name = _Nome(nome)


class _Grafo:
    """O unico uso que o indice faz do grafo: guardar o mapa como atributo."""


def _arvore_de(*nomes: str, prefixo: str = "I"):
    """Arvore minima com grafo de verdade — e nele que o indice passa a morar."""
    people = {f"@{prefixo}{indice}@": _Pessoa(nome) for indice, nome in enumerate(nomes, 1)}
    return (people, {}, _Grafo(), {})


def _arvore_sem_grafo(*nomes: str):
    """Arvore degenerada, como a que aparece em sonda: sem grafo."""
    people = {f"@I{indice}@": _Pessoa(nome) for indice, nome in enumerate(nomes, 1)}
    return (people, {}, None, {})


def _fonte() -> str:
    with open(CAMINHO_DO_MODULO, encoding="utf-8") as arquivo:
        return arquivo.read()


# ---------------------------------------------------------------------------
# O defeito: duas arvores de mesma assinatura
# ---------------------------------------------------------------------------


def test_duas_arvores_de_mesmo_tamanho_nao_compartilham_o_mapa():
    """TT-20: a assinatura (3, '@I1@', '@I3@') e igual, e o conteudo nao."""
    alfa = _arvore_de("Ana Alfa", "Bia Alfa", "Caio Alfa")
    beta = _arvore_de("Ana Alfa", "Dora Beta", "Caio Alfa")

    assert sorted(alfa[0]) == ["@I1@", "@I2@", "@I3@"]
    assert sorted(beta[0]) == ["@I1@", "@I2@", "@I3@"]

    mapa_alfa = homonimos._indice_por_nome(alfa)
    mapa_beta = homonimos._indice_por_nome(beta)

    assert mapa_beta is not mapa_alfa
    assert set(mapa_alfa) == {"ana alfa", "bia alfa", "caio alfa"}
    assert set(mapa_beta) == {"ana alfa", "dora beta", "caio alfa"}
    assert "bia alfa" not in mapa_beta, "a arvore B ficou com o indice da arvore A"
    assert "dora beta" not in mapa_alfa, "a arvore A ficou com o indice da arvore B"


def test_trocar_de_arvore_e_voltar_nao_contamina():
    """A ordem A, B, A nao pode deixar residuo de B no mapa de A."""
    alfa = _arvore_de("Ana Alfa", "Bia Alfa", "Caio Alfa")
    beta = _arvore_de("Ana Alfa", "Dora Beta", "Caio Alfa")

    primeiro = homonimos._indice_por_nome(alfa)
    homonimos._indice_por_nome(beta)
    de_novo = homonimos._indice_por_nome(alfa)

    assert de_novo is primeiro
    assert set(de_novo) == {"ana alfa", "bia alfa", "caio alfa"}


# ---------------------------------------------------------------------------
# O memo por arvore
# ---------------------------------------------------------------------------


def test_duas_chamadas_com_a_mesma_arvore_devolvem_o_mesmo_mapa():
    arvore = _arvore_de("Ana Alfa", "Zeca Alfa")

    primeiro = homonimos._indice_por_nome(arvore)
    segundo = homonimos._indice_por_nome(arvore)

    assert segundo is primeiro
    assert set(primeiro) == {"ana alfa", "zeca alfa"}


def test_a_segunda_chamada_nao_percorre_as_pessoas(monkeypatch):
    arvore = _arvore_de("Ana Alfa", "Zeca Alfa")
    chamadas = {"n": 0}
    original = homonimos.get_name

    def contar(pessoa):
        chamadas["n"] += 1
        return original(pessoa)

    monkeypatch.setattr(homonimos, "get_name", contar)

    homonimos._indice_por_nome(arvore)
    depois_da_primeira = chamadas["n"]
    homonimos._indice_por_nome(arvore)

    assert depois_da_primeira == 2
    assert chamadas["n"] == depois_da_primeira, "a segunda chamada percorreu as pessoas de novo"


def test_arvore_sem_grafo_constroi_sem_estourar():
    arvore = _arvore_sem_grafo("Ana Alfa", "Zeca Alfa")

    mapa = homonimos._indice_por_nome(arvore)

    assert set(mapa) == {"ana alfa", "zeca alfa"}


# ---------------------------------------------------------------------------
# A guarda estrutural: o estado de modulo nao pode voltar
# ---------------------------------------------------------------------------


def test_modulo_nao_declara_cache_de_modulo():
    """Sem `_INDICE_DE_NOMES` e sem `_chave_de`: a colisao nao tem onde nascer."""
    arvore = ast.parse(_fonte())
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, (ast.Assign, ast.AnnAssign)):
            alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
            for alvo in alvos:
                if isinstance(alvo, ast.Name):
                    nomes.add(alvo.id)
        elif isinstance(no, ast.FunctionDef):
            nomes.add(no.name)

    assert "_INDICE_DE_NOMES" not in nomes, "o cache de modulo voltou ao arquivo"
    assert "_chave_de" not in nomes, "a chave de invalidacao voltou ao arquivo"


def test_a_funcao_do_indice_nao_usa_global():
    arvore = ast.parse(_fonte())
    funcao = next(
        no for no in ast.walk(arvore)
        if isinstance(no, ast.FunctionDef) and no.name == "_indice_por_nome"
    )
    usos = [no.lineno for no in ast.walk(funcao) if isinstance(no, ast.Global)]

    assert usos == [], f"`_indice_por_nome` voltou a escrever em global nas linhas {usos}"
