"""Testes da promoção de um descarte a cartão (feature 034, Fase 3).

A promoção não é atalho de tela: o nó escolhido entra na análise como se o casamento
o tivesse aceitado, e o cartão passa por todo o resto do fluxo. Estes testes fixam isso,
o registro do motivo original e o reenvio das promoções anteriores.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import pytest  # noqa: E402

from core.dna_analysis import dna_analysis  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers import gedcom_parser  # noqa: E402
from tests.fixtures import resultado_para_cartao as fixo  # noqa: E402
from tests.fixtures.helpers import arvore_de, deps  # noqa: E402
from tests.fixtures.sample_dna import DNA_CSV_NO_INTERSECTION, DNA_GED  # noqa: E402

NOME = "Zzz Ninguem dos Santos"
MOTIVO = "nenhum sobrenome do nome existe no GEDCOM"


@pytest.fixture(scope="module")
def tree():
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            arquivo.write(DNA_GED)
        return arvore_de(gedcom_parser.carregar_arvore(path))
    finally:
        os.remove(path)


@pytest.fixture
def csv_no_intersecao():
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(DNA_CSV_NO_INTERSECTION)
        yield path
    finally:
        os.remove(path)


def _pessoa(tree, trecho="Ana"):
    return next(pid for pid, p in tree[0].items() if trecho in get_name(p))


# ---------------------------------------------------------------------------
# A decisão do núcleo
# ---------------------------------------------------------------------------

def test_sem_promocao_o_nome_continua_descartado(tree, csv_no_intersecao):
    resultados, descartados, _ = dna_analysis(csv_no_intersecao, "Carlos Silva Souza",
                                              deps(), tree)

    # Feature 039/E002: o descarte de cM alto sem correspondencia tambem ganha um
    # cartao na lista de resultados. O que este teste prende e' que ele NAO foi
    # promovido: o cartao e' o de sem correspondencia, e o item continua descartado.
    assert len(resultados) == 1
    assert resultados[0]["sem_correspondencia"] is True
    assert resultados[0]["match_name"] == NOME
    assert descartados[0]["csv_name"] == NOME
    assert descartados[0]["motivo"] == MOTIVO


def test_com_promocao_o_nome_vira_cartao(tree, csv_no_intersecao):
    pid = _pessoa(tree)
    resultados, descartados, _ = dna_analysis(
        csv_no_intersecao, "Carlos Silva Souza", deps(), tree,
        candidatos_fixos={NOME: (pid, MOTIVO)})

    assert descartados == []
    assert len(resultados) == 1
    assert resultados[0]["match_name"] == get_name(tree[0][pid])


def test_o_cartao_promovido_registra_a_promocao(tree, csv_no_intersecao):
    pid = _pessoa(tree)
    resultados, _, _ = dna_analysis(
        csv_no_intersecao, "Carlos Silva Souza", deps(), tree,
        candidatos_fixos={NOME: (pid, MOTIVO)})

    cartao = resultados[0]
    assert cartao["promovido"] == {"csv_name": NOME, "pid": pid, "motivo": MOTIVO}
    assert any("promovida manualmente" in o and MOTIVO in o for o in cartao["observations"])


def test_promocao_de_outro_nome_nao_afeta_este(tree, csv_no_intersecao):
    """O mapa de promoções é por nome: promover um não promove outro."""
    resultados, descartados, _ = dna_analysis(
        csv_no_intersecao, "Carlos Silva Souza", deps(), tree,
        candidatos_fixos={"Outro Nome Qualquer": (_pessoa(tree), MOTIVO)})

    assert len(resultados) == 1
    assert resultados[0]["sem_correspondencia"] is True
    assert descartados[0]["csv_name"] == NOME


# ---------------------------------------------------------------------------
# A tela
# ---------------------------------------------------------------------------

CARTAO_PROMOVIDO = {
    **fixo.resultado(),
    "promovido": {"csv_name": "Maria José de Souza Santos", "pid": "@I123@",
                  "motivo": "score insuficiente"},
}


def _bloco(com_candidato=True):
    from flask import render_template

    from app import app

    descartes = [{
        "csv_name": "Maria José de Souza Santos", "kit": "TG1", "cm": 12.0,
        "motivo": "score insuficiente",
        "candidatos": [{"id": "@I999@", "nome": "Mariza Souza Santos", "prenome": 100.0,
                        "nota": 88.25, "nascimento": "26 AUG 1970",
                        "compativel": com_candidato}],
    }]
    with app.test_request_context("/"):
        pagina = render_template("index.html", skipped_matches=descartes,
                                 dna_results=[CARTAO_PROMOVIDO],
                                 gedcom_filename="arvore.ged",
                                 root_name_usado="adriano",
                                 csv_filename_usado="matches.csv")
    inicio = pagina.index("bloco-descartados")
    return pagina[inicio:pagina.index("</details>", inicio)]


def test_a_tela_oferece_o_botao_de_promover():
    bloco = _bloco()

    assert "usar este candidato" in bloco
    assert 'name="promover" value="Maria José de Souza Santos|@I999@|score insuficiente"' in bloco


def test_o_formulario_reenvia_a_analise_original():
    bloco = _bloco()

    assert 'name="gedcom_filename" value="arvore.ged"' in bloco
    assert 'name="matches_csv_filename" value="matches.csv"' in bloco
    assert 'name="root_name" value="adriano"' in bloco


def test_o_formulario_carrega_as_promocoes_anteriores():
    bloco = _bloco()

    assert 'name="promover" value="Maria José de Souza Santos|@I123@|score insuficiente"' in bloco


def test_candidato_incompativel_nao_ganha_botao():
    bloco = _bloco(com_candidato=False)

    assert "usar este candidato" not in bloco


# ---------------------------------------------------------------------------
# A rota: o que o navegador manda chega inteiro ao caso de uso
# ---------------------------------------------------------------------------

class _ResultadoFalso:
    resultados = ()
    descartados = ()
    observacoes_do_arquivo = ()
    mensagem = "ok"
    aviso_de_persistencia = None
    sem_correspondencia = ()


def test_a_rota_entrega_as_promocoes_ao_caso_de_uso(monkeypatch):
    """O meio do caminho: `app.py` lê `promover` e repassa o mapa.

    Sem este teste, trocar o nome do campo passaria pela suíte: o formulário seria
    renderizado (testes de tela) e o núcleo saberia promover (testes de núcleo), mas o
    clique não promoveria nada.
    """
    import app as modulo_app

    recebido = {}

    def espiao(*args, **kwargs):
        recebido.update(kwargs)
        return _ResultadoFalso()

    monkeypatch.setattr(modulo_app, "caso_de_uso_dna", espiao)
    monkeypatch.setattr(modulo_app, "_arvore_do_formulario",
                        lambda: ("arvore.ged", ({"@I1@": None}, {}, None, {}), None))
    monkeypatch.setattr(modulo_app, "nomes_de_exibicao", lambda arvore: ["Adriano"])
    monkeypatch.setattr(type(modulo_app._ARMAZENAMENTO), "resolver",
                        lambda self, referencia, dono: "C:/tmp/matches.csv")

    cliente = modulo_app.app.test_client()
    resposta = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": "arvore.ged",
        "root_name": "adriano",
        "matches_csv_filename": "matches.csv",
        "promover": ["Maria Silva|@I10@|score insuficiente",
                     "Joao Souza|@I20@|sem sobrenome em comum"],
    })

    assert resposta.status_code == 200
    assert recebido["candidatos_fixos"] == {
        "Maria Silva": ("@I10@", "score insuficiente"),
        "Joao Souza": ("@I20@", "sem sobrenome em comum"),
    }
