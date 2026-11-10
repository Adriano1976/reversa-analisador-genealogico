"""Testes de contrato e de integração das regiões compartilhadas (feature 056).

A integração roda o caso de uso de verdade: GEDCOM sintético + CSV de matches com
segmentos, e confere que a região nasce do CSV — sem arquivo de triangulação.
"""
from __future__ import annotations

import os

from application.dna_analysis import ResultadoDeAnalise, dna_analysis
from application.regioes import projetar_regioes
from core.dependencias import Dependencias
from core.regiao_no_cartao import classificar
from core.regioes import RegiaoCompartilhada, SegmentoDaRegiao
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
from parsers.gedcom_parser import carregar_arvore
from tests.fixtures.sample_dna import DNA_GED

CSV = (
    "Name,cM,Kit,Chromosome,Start,End\n"
    "Ana Silva Souza,45,A111111,7,21000000,39000000\n"
    "Zzz Um,40,B222222,7,21500000,38500000\n"
    "Zzz Dois,35,C333333,7,22000000,38000000\n"
)


def _deps() -> Dependencias:
    return Dependencias(
        read_csv=read_csv_with_fallback,
        detect_columns=detect_columns,
        aggregate_matches=aggregate_matches,
        generate_mermaid=lambda *a, **k: "flowchart BT",
    )


def _analisar(tmp_path, conteudo=CSV):
    caminho_ged = tmp_path / "arvore.ged"
    caminho_ged.write_text(DNA_GED, encoding="utf-8")
    caminho_csv = tmp_path / "matches.csv"
    caminho_csv.write_text(conteudo, encoding="utf-8")
    arvore = carregar_arvore(str(caminho_ged))
    return dna_analysis(str(caminho_csv), "Carlos", arvore, _deps(), "dono")


def test_a_regiao_nasce_do_csv_de_matches(tmp_path):
    resultado = _analisar(tmp_path)

    assert resultado.regioes, "nenhuma região saiu do CSV de matches"
    regiao = resultado.regioes[0]
    assert regiao.regiao.cromossomo == "7"
    assert len(regiao.regiao.kits) == 3
    assert regiao.regiao.inicio == 22000000
    assert regiao.regiao.fim == 38000000


def test_regiao_com_um_caminho_e_parcial(tmp_path):
    resultado = _analisar(tmp_path)

    assert resultado.regioes[0].desfecho == "parcial"


def test_projecao_leva_o_desfecho_para_a_tela(tmp_path):
    resultado = _analisar(tmp_path)

    projetadas = projetar_regioes(resultado.regioes)

    assert len(projetadas) == 1
    assert projetadas[0]["cromossomo"] == "7"
    assert projetadas[0]["desfecho"] == "Parcial"
    assert "A111111" in projetadas[0]["membros"]


def test_segmentos_abaixo_do_piso_nao_produzem_regiao(tmp_path):
    conteudo = (
        "Name,cM,Kit,Chromosome,Start,End\n"
        "Ana Silva Souza,9,A111111,7,21000000,39000000\n"
        "Zzz Um,9,B222222,7,21500000,38500000\n"
        "Zzz Dois,9,C333333,7,22000000,38000000\n"
    )

    resultado = _analisar(tmp_path, conteudo)

    assert resultado.regioes == ()


def test_resultado_sem_regiao_tem_padrao_vazio():
    resultado = ResultadoDeAnalise(resultados=[], descartados=[], mensagem="0 conexões.")

    assert resultado.regioes == ()


def test_o_cabecalho_distingue_regioes_do_mesmo_cromossomo(cliente_de_upload):
    _app, cliente, pasta = cliente_de_upload
    arvore = "080e7943572d2652__arvore.ged"
    relatorio = "94e2402671702cac__matches.csv"
    csv_chr16 = (
        "Name,cM,Kit,Chromosome,Start,End\n"
        "Ana Silva Souza,45,A111111,16,53070036,55316496\n"
        "Zzz Um,40,B222222,16,53000000,55400000\n"
        "Zzz Dois,35,C333333,16,53050000,55350000\n"
    )
    with open(os.path.join(pasta, arvore), "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    with open(os.path.join(pasta, relatorio), "w", encoding="utf-8") as arquivo:
        arquivo.write(csv_chr16)

    resposta = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": arvore,
        "matches_csv_filename": relatorio,
        "root_name": "Carlos Silva Souza",
    })
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Regiões compartilhadas" in html
    assert "Cromossomo 16 · 53,07–55,32 Mb" in html, (
        "o cabeçalho não mostra a faixa em Mb, e regiões do mesmo cromossomo "
        "continuam parecendo duplicadas"
    )
    assert "53.070.036–55.316.496 pb (2,25 Mb)" in html, (
        "o cabeçalho perdeu a faixa exata em pb"
    )

    inicio = html.index('class="card regioes-compartilhadas')
    abertura = html[inicio:html.index(">", inicio) + 1]
    assert "open" not in abertura, (
        "o bloco de regiões nasceu ABERTO: o padrão pedido é fechado"
    )


def test_projecao_nao_muta_a_regiao():
    segmentos = tuple(
        SegmentoDaRegiao(kit=kit, nome=nome, cromossomo="7",
                         inicio=22000000, fim=38000000, cm=40.0)
        for kit, nome in (("A1", "Maria"), ("B2", "João"), ("C3", "Ana"))
    )
    regiao = RegiaoCompartilhada(
        cromossomo="7", inicio=22000000, fim=38000000,
        kits=("A1", "B2", "C3"), membros=(("A1", "Maria"), ("B2", "João"), ("C3", "Ana")),
        segmentos=segmentos, cm_minimo=35.0, cm_maximo=45.0,
    )
    classificada = classificar(regiao, ())
    antes = (classificada.desfecho, len(classificada.membros), regiao.inicio)

    projetar_regioes([classificada])

    assert (classificada.desfecho, len(classificada.membros), regiao.inicio) == antes
