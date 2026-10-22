"""Testes dos cartões "DNA sem correspondência na árvore" (feature 039, E001/E002/E003).

Duas camadas, de propósito:

1. **A regra** (`core.sem_correspondencia`): o que entra, o que fica de fora e a garantia
   de que o cartão sem correspondência não exclui o próprio item. A regra não ordena nem
   projeta — quem faz isso é o núcleo, ao montar os cartões.
2. **O cartão na lista de resultados**: o mesmo tratamento dos cartões "Parentesco
   documental não encontrado" (rótulo, cabeçalho, seções), sem diagrama e sem promoção, e
   o item continuando na lista completa de descartes.

Nenhum teste usa nome, kit ou cM de arquivo real; os casos são sintéticos. A medição do
arquivo real está em `onboarding.md` e `investigation.md`, não aqui.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.dna_analysis import dna_analysis  # noqa: E402
from core.sem_correspondencia import (  # noqa: E402
    CM_MINIMO_SEM_CORRESPONDENCIA,
    elegivel,
    nomes_com_cartao_aceito,
)
from parsers import gedcom_parser  # noqa: E402
from tests.fixtures.helpers import arvore_de, deps  # noqa: E402
from tests.fixtures.sample_dna import DNA_CSV_NO_INTERSECTION, DNA_GED  # noqa: E402

# O mesmo caso de 150 cM, com a coluna MRCA que o relatório real traz; o cartão
# precisa mostrar o valor estimado, não só o cM.
CSV_150_COM_MRCA = "Name,cM,MRCA\nZzz Ninguem dos Santos,150,3.27\n"
CSV_DOIS_SEM_CORRESPONDENCIA = (
    "Name,cM\nZzz Ninguem dos Santos,25\nYyy Outro Ninguem,80\n"
)


def _descarte(nome, cm, kit="TG0000001", candidatos=None):
    """Um item de `skipped_matches` com o formato que o núcleo produz."""
    return {
        "csv_name": nome,
        "kit": kit,
        "cm": cm,
        "motivo": "motivo sintético",
        "motivo_codigo": "sem_sobrenome_no_gedcom",
        "motivo_detalhe": "",
        "candidatos": list(candidatos or ()),
    }


def _cartao(nome, sem=False):
    cartao = {"csv_name": nome, "cm": 25.0}
    if sem:
        cartao["sem_correspondencia"] = True
    return cartao


# ---------------------------------------------------------------------------
# A regra
# ---------------------------------------------------------------------------

class TestRegra:
    def test_o_limiar_e_inclusivo_e_o_abaixo_fica_fora(self):
        nomes = nomes_com_cartao_aceito([])

        assert elegivel(_descarte("No limite", CM_MINIMO_SEM_CORRESPONDENCIA), nomes)
        assert not elegivel(_descarte("Abaixo", CM_MINIMO_SEM_CORRESPONDENCIA - 0.1), nomes)

    def test_candidato_compativel_nao_entra(self):
        nomes = nomes_com_cartao_aceito([])

        assert not elegivel(
            _descarte("Com compatível", 150.0,
                      candidatos=[{"nome": "Alguém", "compativel": True}]),
            nomes,
        )

    def test_candidato_incompativel_nao_exclui(self):
        nomes = nomes_com_cartao_aceito([])

        assert elegivel(
            _descarte("Sem compatível", 150.0,
                      candidatos=[{"nome": "Alguém", "compativel": False}]),
            nomes,
        )

    def test_cartao_aceito_exclui_o_descarte_do_mesmo_nome(self):
        nomes = nomes_com_cartao_aceito([_cartao("Clezia Santos")])

        assert not elegivel(_descarte("clezia santos", 154.5, kit="OUTRO"), nomes)

    def test_cartao_sem_correspondencia_nao_exclui_o_proprio_item(self):
        nomes = nomes_com_cartao_aceito([_cartao("Clezia Santos", sem=True)])

        assert nomes == set()
        assert elegivel(_descarte("Clezia Santos", 154.5, kit="AZ4078391"), nomes)

    def test_dois_kits_do_mesmo_nome_sem_cartao_sao_dois_elegiveis(self):
        nomes = nomes_com_cartao_aceito([])

        assert elegivel(_descarte("Clezia Santos", 154.5, kit="KIT-A"), nomes)
        assert elegivel(_descarte("Clezia Santos", 80.0, kit="KIT-B"), nomes)


# ---------------------------------------------------------------------------
# O cartão na lista de resultados
# ---------------------------------------------------------------------------

def _analisar(texto_csv):
    """Roda o núcleo sobre a fixture sintética e devolve (cartões, descartes, sem, msg).

    `sem` são os **próprios cartões** marcados, na ordem da tela; é daqui que a
    aplicação deriva a contagem do resumo.
    """
    fd, caminho_ged = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    fd, caminho_csv = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto_csv)
    try:
        arvore = arvore_de(gedcom_parser.carregar_arvore(caminho_ged))
        resultados, descartados, mensagem = dna_analysis(
            caminho_csv, "Carlos Silva Souza", deps(), arvore)
        sem = tuple(r for r in resultados if r.get("sem_correspondencia"))
        return resultados, descartados, sem, mensagem
    finally:
        os.remove(caminho_ged)
        os.remove(caminho_csv)


def _render(resultados, descartados, sem_correspondencia):
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        return render_template(
            "index.html",
            dna_results=list(resultados),
            skipped_matches=list(descartados),
            sem_correspondencia=list(sem_correspondencia),
            gedcom_filename="arvore.ged",
            root_name_usado="carlos",
            csv_filename_usado="matches.csv",
        )


class TestCartaoNaLista:
    def test_o_match_de_150_cm_vira_cartao_com_o_rotulo_de_nao_encontrado(self):
        resultados, descartados, sem, mensagem = _analisar(CSV_150_COM_MRCA)

        assert mensagem == "1 conexões encontradas. 1 descartadas."
        assert len(resultados) == 1
        assert len(descartados) == 1
        assert len(sem) == 1
        cartao = resultados[0]
        assert cartao["match_name"] == "Zzz Ninguem dos Santos"
        assert cartao["sem_correspondencia"] is True
        assert cartao["documentary"]["label"] == "Parentesco documental não encontrado"
        assert cartao["documentary"]["status"] == "not_found"
        assert cartao["documentary"]["path"] is None
        assert cartao["identidade"] == "a_confirmar"
        assert cartao["mermaid_data"] is None
        assert cartao["text_path"] == ""
        assert cartao["genetic_evidence"]["kits"][0]["mrca_generations"] == 3.27

    def test_o_item_continua_na_lista_completa_de_descartes(self):
        _resultados, descartados, sem, _mensagem = _analisar(DNA_CSV_NO_INTERSECTION)

        assert descartados[0]["csv_name"] == "Zzz Ninguem dos Santos"
        assert descartados[0]["motivo"] == "nenhum sobrenome do nome existe no GEDCOM"
        assert sem[0]["csv_name"] == "Zzz Ninguem dos Santos"

    def test_25_entra_e_19_9_fica_fora(self):
        resultados_25, _desc_25, sem_25, _msg_25 = _analisar(
            "Name,cM\nZzz Ninguem dos Santos,25\n")
        resultados_19, desc_19, sem_19, _msg_19 = _analisar(
            "Name,cM\nZzz Ninguem dos Santos,19.9\n")

        assert len(resultados_25) == 1
        assert sem_25
        assert resultados_19 == []
        assert len(desc_19) == 1
        assert sem_19 == ()

    def test_a_tela_mostra_o_cartao_na_lista_e_nao_um_bloco(self):
        resultados, descartados, sem, _mensagem = _analisar(CSV_150_COM_MRCA)
        pagina = _render(resultados, descartados, sem)

        assert "Análise de conexão com" in pagina
        assert "Zzz Ninguem dos Santos" in pagina
        assert "Parentesco documental não encontrado" in pagina
        assert "MRCA estimado" in pagina
        assert "3,27 gerações" in pagina
        assert "sem correspondência na árvore" in pagina
        assert 'id="sem-correspondencia"' not in pagina
        assert "Matches descartados (1)" in pagina

    def test_o_cartao_nao_tem_diagrama_nem_promocao(self):
        resultados, descartados, sem, _mensagem = _analisar(DNA_CSV_NO_INTERSECTION)
        cartao = resultados[0]
        pagina = _render(resultados, descartados, sem)

        assert cartao["mermaid_data"] is None
        assert cartao["text_path"] == ""
        assert "usar este candidato" not in pagina

    def test_o_cartao_tem_as_secoes_do_tratamento_de_nao_encontrado(self):
        resultados, descartados, sem, _mensagem = _analisar(DNA_CSV_NO_INTERSECTION)
        pagina = _render(resultados, descartados, sem)

        assert "Parentesco documental" in pagina
        assert "Observações" in pagina
        assert "Identidade a confirmar" in pagina

    def test_a_projecao_historica_ignora_o_cartao_sem_correspondencia(self):
        from application.dna_analysis import projetar_analise

        resultados, descartados, _sem, _mensagem = _analisar(CSV_150_COM_MRCA)
        analise = projetar_analise(
            resultados, descartados, "1 conexões encontradas. 1 descartadas.",
            "arvore.ged", "matches.csv", "carlos")

        # O cartão sem correspondência não tem pessoa para `match_result`
        # (`matched_person_xref` NOT NULL/FK); ele fica em `skipped_match`.
        assert analise.accepted_count == 0
        assert analise.skipped_count == 1
        assert analise.conexoes == ()
        assert len(analise.descartados) == 1
        assert analise.descartados[0].csv_name == "Zzz Ninguem dos Santos"

    def test_sem_item_o_resultado_nao_mostra_o_rotulo(self):
        _resultados, descartados, _sem, _mensagem = _analisar(DNA_CSV_NO_INTERSECTION)
        pagina = _render([], descartados, [])

        assert "Análise de conexão com" not in pagina
        assert "Matches descartados (1)" in pagina

    def test_os_cartoes_sem_correspondencia_ficam_por_cm_decrescente(self):
        resultados, _descartados, sem, _mensagem = _analisar(
            CSV_DOIS_SEM_CORRESPONDENCIA)

        assert len(resultados) == 2
        assert len(sem) == 2
        assert all(cartao["sem_correspondencia"] for cartao in resultados)
        assert [cartao["cm"] for cartao in resultados] == [80, 25]
