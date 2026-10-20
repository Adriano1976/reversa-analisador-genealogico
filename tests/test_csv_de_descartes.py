"""Testes da lista de trabalho dos descartes em CSV (feature 035).

Duas metades: o formatador puro (`reporting`, sem `core/`) e a rota que devolve o arquivo
com o que a tela renderizou.
"""
from __future__ import annotations

import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from reporting.csv_de_descartes import CABECALHO, csv_de_descartes  # noqa: E402

DESCARTE = {
    "csv_name": "Maria José de Souza Santos",
    "kit": "TG0000001",
    "cm": 12.3,
    "motivo": "o prenome é diferente do que está na árvore",
    "motivo_codigo": "prenome_diferente",
    "motivo_detalhe": ("prenome 55 · nota 80,05 · sobrenomes em comum 1 de 1 · "
                       "grafia do sobrenome 0,5"),
    "candidatos": [
        {"id": "@I1@", "nome": "Angelica Maria De Jesus De Oliveira", "prenome": 55.0,
         "nota": 80.05, "nascimento": "6 AUG 1966", "compativel": False},
        {"id": "@I2@", "nome": "Mariza Souza Santos", "prenome": 100.0,
         "nota": 88.25, "nascimento": "26 AUG 1970", "compativel": True},
    ],
}


def _linhas(texto: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(texto.lstrip("\ufeff")), delimiter=";"))


# ---------------------------------------------------------------------------
# O formatador
# ---------------------------------------------------------------------------

def test_a_planilha_comeca_pelo_cabecalho():
    linhas = _linhas(csv_de_descartes([]))

    assert tuple(linhas[0]) == CABECALHO


def test_uma_linha_por_descarte():
    linhas = _linhas(csv_de_descartes([DESCARTE, {**DESCARTE, "csv_name": "Outro Nome"}]))

    assert len(linhas) == 3
    assert linhas[1][0] == "Maria José de Souza Santos"
    assert linhas[2][0] == "Outro Nome"


def test_o_candidato_compativel_e_o_exportado():
    linha = _linhas(csv_de_descartes([DESCARTE]))[1]

    assert linha[4] == "Mariza Souza Santos"
    assert linha[5] == "26 AUG 1970"
    assert linha[6] == "100"
    assert linha[7] == "88,25"


def test_sem_candidato_as_colunas_ficam_vazias():
    sem = {k: v for k, v in DESCARTE.items() if k != "candidatos"}
    linha = _linhas(csv_de_descartes([sem]))[1]

    assert linha[4:8] == ["", "", "", ""]
    # A nona coluna e' o detalhe tecnico (feature 038), e ela nao depende de candidato.
    assert linha[8].startswith("prenome 55")


def test_sem_detalhe_a_nona_coluna_fica_vazia():
    """Recusa por sobrenome nao mede nada: o detalhe nasce vazio, e nao com zero."""
    sem = {k: v for k, v in DESCARTE.items() if k != "motivo_detalhe"}
    linha = _linhas(csv_de_descartes([sem]))[1]

    assert linha[8] == ""


def test_candidato_incompativel_nao_entra_na_planilha():
    """A lista é de nomes a cadastrar; homônimo de outro século não é endereço de ninguém."""
    so_fraco = {**DESCARTE, "candidatos": [
        {"nome": "Luzia Martins dos Santos", "prenome": 73.0, "nota": 68.55,
         "nascimento": "1798", "compativel": False},
    ]}
    linha = _linhas(csv_de_descartes([so_fraco]))[1]

    assert linha[4:8] == ["", "", "", ""]
    assert linha[8] == DESCARTE["motivo_detalhe"]


def test_o_decimal_sai_com_virgula():
    linha = _linhas(csv_de_descartes([DESCARTE]))[1]

    assert linha[2] == "12,3"


def test_o_acento_sobrevive_ao_arquivo():
    texto = csv_de_descartes([DESCARTE])

    assert texto.startswith("\ufeff"), "sem BOM o Excel abre em ANSI e os acentos quebram"
    assert "José" in texto


def test_nome_que_parece_formula_e_desarmado():
    perigoso = {"csv_name": "=HYPERLINK(\"http://x\")", "kit": None, "cm": None,
                "motivo": "+soma", "candidatos": []}
    linha = _linhas(csv_de_descartes([perigoso]))[1]

    assert linha[0].startswith("'=")
    assert linha[3].startswith("'+")


# ---------------------------------------------------------------------------
# A rota
# ---------------------------------------------------------------------------

def _post(dados_json):
    from app import app

    cliente = app.test_client()
    return cliente.post("/descartes.csv", data={"dados": dados_json})


def test_a_rota_devolve_arquivo_csv():
    resposta = _post('[{"csv_name": "Fulano de Tal", "kit": "TG1", "cm": 9.5, '
                     '"motivo": "sem sobrenome em comum", "candidatos": []}]')

    assert resposta.status_code == 200
    assert "text/csv" in resposta.headers["Content-Type"]
    assert "attachment" in resposta.headers["Content-Disposition"]
    assert "Fulano de Tal" in resposta.get_data(as_text=True)


def test_a_rota_aceita_corpo_invalido_sem_estourar():
    resposta = _post("isto nao e json")

    assert resposta.status_code == 200
    assert resposta.get_data(as_text=True).lstrip("\ufeff").startswith("Nome no CSV")


def test_a_rota_ignora_json_que_nao_e_lista():
    resposta = _post('{"a": 1}')

    assert resposta.status_code == 200
    assert resposta.get_data(as_text=True).lstrip("\ufeff").startswith("Nome no CSV")


# ---------------------------------------------------------------------------
# A tela
# ---------------------------------------------------------------------------

def test_o_bloco_oferece_o_download():
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html", skipped_matches=[DESCARTE])
    bloco = pagina[pagina.index("bloco-descartados"):]
    bloco = bloco[:bloco.index("</details>")]

    assert "Baixar lista de trabalho (CSV)" in bloco
    assert 'name="dados"' in bloco
    assert "Mariza Souza Santos" in bloco


def test_sem_descartes_nao_ha_download():
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html")

    assert "Baixar lista de trabalho" not in pagina
