"""Testes de contrato e de integração das regiões compartilhadas (feature 056).

A integração roda o caso de uso de verdade: GEDCOM sintético + CSV de matches com
segmentos, e confere que a região nasce do CSV — sem arquivo de triangulação.
"""
from __future__ import annotations

import io
import os

from application.dna_analysis import ResultadoDeAnalise, dna_analysis
from application.regioes import projetar_regioes
from core.dependencias import Dependencias
from core.regiao_no_cartao import classificar
from core.regioes import RegiaoCompartilhada, SegmentoDaRegiao
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
from parsers.gedcom_parser import carregar_arvore
from tests.fixtures.sample_dna import DNA_GED, DNA_CSV_SEGMENTOS_DISTRIBUICAO

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
    assert "Cromossomo 16" in html
    # A faixa em Mb saiu do cabecalho a pedido do operador; quem distingue duas
    # regioes do mesmo cromossomo e' a faixa exata em pb, que continua na linha
    # de baixo.
    assert "53.070.036–55.316.496 pb (2,25 Mb)" in html, (
        "o cabeçalho perdeu a faixa exata em pb"
    )
    assert "53,07–55,32 Mb" not in html, (
        "a faixa em Mb voltou ao cabeçalho da região"
    )
    # O ideograma por cromossomo (feature 056): uma faixa posicionada por
    # coordenada, com o cartão do hover, e a régua declarada na legenda.
    assert 'class="ideograma"' in html, "o mapa por cromossomo não renderizou"
    assert 'class="faixa faixa-' in html, "nenhuma faixa do ideograma foi posicionada"
    assert "GRCh37" in html, "a legenda deixou de declarar a régua"

    inicio = html.index('class="card regioes-compartilhadas')
    abertura = html[inicio:html.index(">", inicio) + 1]
    assert "open" not in abertura, (
        "o bloco de regiões nasceu ABERTO: o padrão pedido é fechado"
    )


def test_o_cartao_do_hover_nao_e_recortado_pelo_card():
    """Regressão do corte no topo (2026-11-10).

    O cartão do hover abre ACIMA da faixa e o `overflow:hidden` de `details.card`
    recortava no raio da borda: nas duas primeiras linhas — cromossomos 1 e 2 — o
    operador via o cartão começando em "Tamanho:", sem título e sem a posição. A
    correção é do escopo deste bloco: o recorte fica só no cabeçalho.
    """
    caminho = os.path.join(
        os.path.dirname(__file__), "..", "src", "assets", "app.css"
    )
    with open(caminho, encoding="utf-8") as folha:
        css = folha.read()

    assert "details.card.regioes-compartilhadas{overflow:visible}" in css, (
        "o bloco das regiões voltou a recortar o cartão do hover no raio da borda"
    )
    assert "details.card.regioes-compartilhadas > summary.sumario-do-cartao{" in css, (
        "o cabeçalho perdeu o raio próprio: o recorte tirado do cartão não foi para ele"
    )
    assert ".dica-direita{left:0}" in css, (
        "a dica não tem lado para a borda esquerda do trilho"
    )


def test_o_grafico_de_distribuicao_entra_entre_o_ideograma_e_a_lista(cliente_de_upload):
    """Feature 057: posicao, eixos e legenda do grafico de distribuicao."""
    _app, cliente, pasta = cliente_de_upload
    arvore = "080e7943572d2652__arvore.ged"
    relatorio = "94e2402671702cac__matches.csv"
    with open(os.path.join(pasta, arvore), "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    with open(os.path.join(pasta, relatorio), "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_CSV_SEGMENTOS_DISTRIBUICAO)

    resposta = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": arvore,
        "matches_csv_filename": relatorio,
        "root_name": "Carlos Silva Souza",
    })
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert 'class="distribuicao"' in html, "o gráfico por cromossomo não renderizou"
    # A decisão 3b do clarify: depois do ideograma e da legenda dele, antes da lista.
    assert (
        html.index("Régua: GRCh37")
        < html.index("Distribuição por cromossomo")
        < html.index('<article class="regiao"')
    ), "o gráfico saiu da posição fixada entre a legenda do ideograma e a lista"
    # Os dois eixos, cada um com o seu nome, e a legenda declarando as séries.
    assert 'class="eixo-nome eixo-nome-matches" aria-hidden="true">Matches' in html
    assert 'class="eixo-nome eixo-nome-cm" aria-hidden="true">cM médio' in html
    assert "kits distintos com região no cromossomo" in html
    assert "Cada série tem a sua escala" in html
    # Uma coluna por cromossomo com região, na ordem natural da fixture (1, 7, 16).
    assert html.count('class="coluna"') == 3, (
        "o gráfico não tem uma coluna por cromossomo"
    )
    assert html.index("Chr 1") < html.index("Chr 7") < html.index("Chr 16")
    # O cartão do hover diz os dois números, e o cM médio do cromossomo 1 é 16,75.
    assert "Matches: 4" in html
    assert "cM médio: 16,75" in html


def test_sem_regiao_nao_existe_grafico(cliente_de_upload):
    """Feature 057: sem região, nem o bloco nem o gráfico entram no HTML."""
    _app, cliente, pasta = cliente_de_upload
    arvore = "080e7943572d2652__arvore.ged"
    relatorio = "94e2402671702cac__matches.csv"
    csv_sem_regiao = (
        "Name,cM,Kit,Chromosome,Start,End\n"
        "Ana Silva Souza,45,A111111,7,21000000,39000000\n"
        "Zzz Um,40,B222222,8,21500000,38500000\n"
    )
    with open(os.path.join(pasta, arvore), "w", encoding="utf-8") as arquivo:
        arquivo.write(DNA_GED)
    with open(os.path.join(pasta, relatorio), "w", encoding="utf-8") as arquivo:
        arquivo.write(csv_sem_regiao)

    resposta = cliente.post("/", data={
        "action": "dna_analysis",
        "gedcom_filename": arvore,
        "matches_csv_filename": relatorio,
        "root_name": "Carlos Silva Souza",
    })
    html = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Regiões compartilhadas" not in html
    assert 'class="distribuicao"' not in html


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
