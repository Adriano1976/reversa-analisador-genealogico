"""Regra final da analise: GEDCOM, DNA e confronto, com os 10 cenarios exigidos.

Cada cenario da regra tem um teste com o numero no nome, para que a cobertura
pedida seja auditavel:

- TESTE 1  caminho no GEDCOM + DNA -> as quatro secoes aparecem
- TESTE 2  parentesco proximo + DNA incompativel -> CONFLITANTE
- TESTE 3  parentesco distante + DNA compativel com varias relacoes -> POSSIVEL
- TESTE 4  sem DNA -> parentesco documental segue, genetica "sem evidencia"
- TESTE 5  DNA sem caminho no GEDCOM -> documental "nao encontrado", sem invento
- TESTE 6  homonimos -> identidade ambigua, sem escolha silenciosa
- TESTE 7  multiplos caminhos -> todos os ancestrais comuns sao reportados
- TESTE 8  mesmo nome em mais de um kit -> cada kit separado, nunca somados
- TESTE 9  cM pequeno -> nenhum parentesco especifico afirmado
- TESTE 10 cM dentro de varias faixas -> varias possibilidades listadas

Ha ainda testes de regressao do defeito que motivou a regra (vinculo com data
cronologicamente impossivel) e do texto da interface.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import dna_analysis
from core.documentary_relationship import documentary_relationship, homonym_dossier
from core.evidence_comparison import compare
from core.genetic_evidence import SEM_KIT, build_genetic_evidence, evidence_for
from core.path_search import path_search
from core.relationship_hypotheses import hypotheses_for_evidence, possible_relationships
from parsers import gedcom_parser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GED_FAMILIA = """0 HEAD
1 SOUR TESTE-CONFRONTACAO
1 CHAR UTF-8
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @T1@ INDI
1 NAME Tomas /Vieira/
1 SEX M
1 BIRT
2 DATE 1840
1 FAMS @FT@
0 @T2@ INDI
1 NAME Ursula /Souza/
1 SEX F
1 BIRT
2 DATE 1845
1 FAMS @FT@
0 @H1@ INDI
1 NAME Aurelio /Vieira/
1 SEX M
1 BIRT
2 DATE 1870
1 FAMC @FT@
1 FAMS @FH@
0 @H2@ INDI
1 NAME Benta /Souza/
1 SEX F
1 BIRT
2 DATE 1875
1 FAMS @FH@
0 @G1@ INDI
1 NAME Goncalo /Vieira/
1 SEX M
1 BIRT
2 DATE 1900
1 FAMC @FH@
1 FAMS @FG@
0 @G2@ INDI
1 NAME Mariana /Souza/
1 SEX F
1 BIRT
2 DATE 1905
1 FAMS @FG@
0 @G3@ INDI
1 NAME Zacarias /Vieira/
1 SEX M
1 BIRT
2 DATE 1902
1 FAMC @FH@
1 FAMS @FZ@
0 @G4@ INDI
1 NAME Anna /Souza/
1 SEX F
1 BIRT
2 DATE 1905
1 FAMS @FZ@
0 @P1@ INDI
1 NAME Pedro /Vieira/
1 SEX M
1 BIRT
2 DATE 1930
1 FAMC @FG@
1 FAMS @FP@
0 @M1@ INDI
1 NAME Marta /Souza/
1 SEX F
1 BIRT
2 DATE 1935
1 FAMS @FP@
0 @R1@ INDI
1 NAME Rita /Vieira/
1 SEX F
1 BIRT
2 DATE 1935
1 FAMC @FG@
1 FAMS @FR@
0 @L1@ INDI
1 NAME Jorge /Lima/
1 SEX M
1 FAMS @FR@
0 @ROOT@ INDI
1 NAME Adriano /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1960
1 FAMC @FP@
0 @S1@ INDI
1 NAME Soraia /Vieira/ Souza
1 SEX F
1 BIRT
2 DATE 1965
1 FAMC @FP@
0 @C1@ INDI
1 NAME Helena /Vieira/ Lima
1 SEX F
1 BIRT
2 DATE 1965
1 FAMC @FR@
0 @Z1@ INDI
1 NAME Jose Zacarias /Vieira/
1 SEX M
1 BIRT
2 DATE 1930
1 FAMC @FZ@
1 FAMS @FZZ@
0 @Z2@ INDI
1 NAME Clara /Souza/
1 SEX F
1 BIRT
2 DATE 1935
1 FAMS @FZZ@
0 @Z3@ INDI
1 NAME Vicente /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1960
1 FAMC @FZZ@
0 @J1@ INDI
1 NAME Joao /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1955
1 FAMC @FP@
0 @J2@ INDI
1 NAME Joao /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1958
1 FAMC @FR@
0 @LONELY@ INDI
1 NAME Lone /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1970
0 @A1@ INDI
1 NAME José Zacarias /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1968
1 FAMC @FP@
0 @A2@ INDI
1 NAME Jose Zacarias /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 1971
0 @FT@ FAM
1 HUSB @T1@
1 WIFE @T2@
1 CHIL @H1@
0 @FH@ FAM
1 HUSB @H1@
1 WIFE @H2@
1 CHIL @G1@
1 CHIL @G3@
0 @FG@ FAM
1 HUSB @G1@
1 WIFE @G2@
1 CHIL @P1@
1 CHIL @R1@
0 @FP@ FAM
1 HUSB @P1@
1 WIFE @M1@
1 CHIL @ROOT@
1 CHIL @S1@
1 CHIL @J1@
0 @FR@ FAM
1 HUSB @L1@
1 WIFE @R1@
1 CHIL @C1@
1 CHIL @J2@
0 @FZ@ FAM
1 HUSB @G3@
1 WIFE @G4@
1 CHIL @Z1@
0 @FZZ@ FAM
1 HUSB @Z1@
1 WIFE @Z2@
1 CHIL @Z3@
0 TRLR
"""

# Colapso de pedigree: Diego e Elena sao primos e se casam. Gustavo (raiz)
# alcanca o casal fundador por DUAS cadeias distintas.
GED_PEDIGREE_COLLAPSE = """0 HEAD
1 SOUR TESTE-COLAPSO
1 CHAR UTF-8
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @K1@ INDI
1 NAME Avoh /Vieira/
1 SEX M
1 FAMS @FA@
0 @K2@ INDI
1 NAME Avoh /Souza/
1 SEX F
1 FAMS @FA@
0 @K3@ INDI
1 NAME Carlos /Vieira/ Souza
1 SEX M
1 FAMC @FA@
1 FAMS @FB@
0 @K5@ INDI
1 NAME Nair /Lima/
1 SEX F
1 FAMS @FB@
0 @K4@ INDI
1 NAME Rita /Vieira/ Souza
1 SEX F
1 FAMC @FA@
1 FAMS @FC@
0 @K7@ INDI
1 NAME Jorge /Lima/
1 SEX M
1 FAMS @FC@
0 @K6@ INDI
1 NAME Diego /Vieira/ Lima
1 SEX M
1 FAMC @FB@
1 FAMS @FD@
0 @K8@ INDI
1 NAME Elena /Vieira/ Souza
1 SEX F
1 FAMC @FC@
1 FAMS @FD@
0 @K9@ INDI
1 NAME Fabio /Vieira/ Lima
1 SEX M
1 FAMC @FD@
1 FAMS @FE@
0 @K10@ INDI
1 NAME Zelia /Souza/
1 SEX F
1 FAMS @FE@
0 @K11@ INDI
1 NAME Gustavo /Vieira/ Lima
1 SEX M
1 FAMC @FE@
0 @K12@ INDI
1 NAME Tiago /Vieira/ Lima
1 SEX M
1 FAMC @FB@
0 @FA@ FAM
1 HUSB @K1@
1 WIFE @K2@
1 CHIL @K3@
1 CHIL @K4@
0 @FB@ FAM
1 HUSB @K3@
1 WIFE @K5@
1 CHIL @K6@
1 CHIL @K12@
0 @FC@ FAM
1 HUSB @K7@
1 WIFE @K4@
1 CHIL @K8@
0 @FD@ FAM
1 HUSB @K6@
1 WIFE @K8@
1 CHIL @K9@
0 @FE@ FAM
1 HUSB @K9@
1 WIFE @K10@
1 CHIL @K11@
0 TRLR
"""

# Vinculo cronologicamente impossivel: a mae nasce 11 anos DEPOIS do filho.
# Reproduz, em miniatura, o defeito medido no GEDCOM real (@F6@).
GED_DATA_IMPOSSIVEL = """0 HEAD
1 SOUR TESTE-DATA
1 CHAR UTF-8
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @X8@ INDI
1 NAME Benta /Vieira/
1 SEX F
1 BIRT
2 DATE 1945
1 FAMS @FX2@
0 @X9@ INDI
1 NAME Osvaldo /Souza/
1 SEX M
1 BIRT
2 DATE 1940
1 FAMS @FX2@
0 @X1@ INDI
1 NAME Maria /Vieira/ Souza
1 SEX F
1 BIRT
2 DATE 17 FEB 1972
1 FAMC @FX2@
1 FAMS @FX@
0 @X2@ INDI
1 NAME Florivaldo /Vieira/
1 SEX M
1 BIRT
2 DATE 1935
1 FAMS @FX@
0 @X3@ INDI
1 NAME Celso /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 25 MAR 1961
1 FAMC @FX@
1 FAMS @FY@
0 @X4@ INDI
1 NAME Ester /Souza/
1 SEX F
1 FAMS @FY@
0 @X5@ INDI
1 NAME Adriano /Vieira/ Souza
1 SEX M
1 BIRT
2 DATE 12 OCT 1976
1 FAMC @FY@
0 @FX2@ FAM
1 HUSB @X9@
1 WIFE @X8@
1 CHIL @X1@
0 @FX@ FAM
1 HUSB @X2@
1 WIFE @X1@
1 CHIL @X3@
0 @FY@ FAM
1 HUSB @X3@
1 WIFE @X4@
1 CHIL @X5@
0 TRLR
"""


def _carregar(ged_texto):
    fd, caminho = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(ged_texto)
        gedcom_parser.load_gedcom_and_build_graph(caminho)
    finally:
        os.remove(caminho)


def _csv(texto):
    fd, caminho = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
        fh.write(texto)
    return caminho


def _analisar(csv_texto, ged_texto=GED_FAMILIA, raiz="Adriano Vieira Souza"):
    _carregar(ged_texto)
    caminho = _csv(csv_texto)
    try:
        return dna_analysis(caminho, raiz)
    finally:
        os.remove(caminho)


def _so_basico(**kwargs):
    """CSV no formato legado (so Name,cM) — usado quando o kit nao importa."""
    linhas = "\n".join(f"{nome},{cm}" for nome, cm in kwargs.items())
    return "Name,cM\n" + linhas + "\n"


# ---------------------------------------------------------------------------
# TESTE 1 — GEDCOM com caminho + DNA: as quatro secoes existem
# ---------------------------------------------------------------------------

def test_1_caminho_documental_e_evidencia_separados():
    resultados, descartados, mensagem = _analisar(_so_basico(**{"Vicente Vieira Souza": 10.8}))

    assert mensagem.startswith("1 conexões encontradas")
    assert descartados == []
    resultado = resultados[0]

    # 1. parentesco documental (o GEDCOM decide)
    assert resultado["documentary"]["source"] == "GEDCOM"
    assert resultado["documentary"]["status"] == "found"
    assert resultado["documentary"]["label"]
    assert resultado["documentary"]["path"]["names"][0] == "Adriano Vieira Souza"
    assert resultado["documentary"]["path"]["names"][-1] == "Vicente Vieira Souza"
    assert resultado["documentary"]["common_ancestor"]["name"]
    assert resultado["documentary"]["evidence"], "cada salto tem de trazer a evidencia do registro"

    # 2. evidencia genetica (o CSV decide)
    assert resultado["genetic_evidence"]["available"] is True
    assert resultado["genetic_evidence"]["kits"][0]["total_cm"] == 10.8

    # 3. possibilidades (Shared cM Project) — lista, nunca um parentesco unico
    assert isinstance(resultado["hypotheses"], list) and resultado["hypotheses"]
    assert isinstance(resultado["hypotheses"][0]["possible_relationships"], list)

    # 4. confrontacao com um dos quatro estados
    assert resultado["comparison"]["status"] in (
        "COMPATIVEL", "POSSIVEL", "CONFLITANTE", "INCONCLUSIVO")
    assert resultado["comparison"]["message"]

    # a analise genetica NAO alterou o parentesco documental
    assert resultado["documentary"]["label"] == "Primos de 2º grau"


# ---------------------------------------------------------------------------
# TESTE 2 — parentesco proximo + DNA claramente incompativel -> CONFLITANTE
# ---------------------------------------------------------------------------

def test_2_parentesco_proximo_com_dna_incompativel_e_conflitante():
    resultados, _, _ = _analisar(_so_basico(**{"Soraia Vieira Souza": 50}))
    resultado = resultados[0]

    assert resultado["documentary"]["label"] == "Irmãos"
    assert resultado["comparison"]["status"] == "CONFLITANTE"
    assert "incompatibilidade" in resultado["comparison"]["message"]
    assert resultado["comparison"]["causes"], "conflito precisa listar as causas a verificar"
    assert any("homônimo" in causa for causa in resultado["comparison"]["causes"])


def test_2b_parentesco_proximo_com_dna_compativel_e_compativel():
    """Contraprova do TESTE 2: o mesmo parentesco com cM plausivel nao conflita."""
    resultados, _, _ = _analisar(_so_basico(**{"Soraia Vieira Souza": 2600}))
    assert resultados[0]["comparison"]["status"] == "COMPATIVEL"


# ---------------------------------------------------------------------------
# TESTE 3 — parentesco distante + DNA compativel com varias relacoes -> POSSIVEL
# ---------------------------------------------------------------------------

def test_3_parentesco_distante_nunca_vira_certeza():
    resultados, _, _ = _analisar(_so_basico(**{"Vicente Vieira Souza": 10.8}))
    resultado = resultados[0]

    assert resultado["comparison"]["status"] in ("POSSIVEL", "COMPATIVEL")
    assert len(resultado["hypotheses"][0]["possible_relationships"]) > 1, (
        "10,8 cM cabe em varias relacoes publicadas: a resposta nao pode ser uma so")
    assert resultado["hypotheses"][0]["confidence"] in ("baixa", "muito baixa")
    assert "não identifica qual delas é a verdadeira" in resultado["hypotheses"][0]["interpretation"]


# ---------------------------------------------------------------------------
# TESTE 4 — sem DNA: documental continua, genetica nao inventa compatibilidade
# ---------------------------------------------------------------------------

def test_4_sem_dna_documental_segue_e_genetica_e_inconclusiva():
    _carregar(GED_FAMILIA)
    # Unidade: o confronto sem evidencia genetica nao pode inventar compatibilidade.
    documental = documentary_relationship("@ROOT@", "@S1@")
    assert documental["label"] == "Irmãos"
    confronto = compare(documental, hypotheses=[], evidence={"available": False, "kits": [], "totals": {}})
    assert confronto["status"] == "INCONCLUSIVO"
    assert "Sem evidência genética" in confronto["detail"]

    # Tela sem DNA: a busca documental continua entregando o parentesco.
    resultado, mensagem, sucesso = path_search("Adriano Vieira Souza", "Soraia Vieira Souza")
    assert sucesso is True
    assert mensagem == "Conexão direta encontrada (ancestral comum)."
    assert resultado["documentary"]["label"] == "Irmãos"
    assert "genetic_evidence" not in resultado, "a tela sem DNA não inventa evidência genética"


# ---------------------------------------------------------------------------
# TESTE 5 — DNA sem caminho no GEDCOM: nao inventar caminho
# ---------------------------------------------------------------------------

def test_5_dna_sem_caminho_documental():
    resultados, descartados, _ = _analisar(_so_basico(**{"Lone Vieira Souza": 120}))
    assert descartados == []
    resultado = resultados[0]

    assert resultado["documentary"]["status"] == "not_found"
    assert resultado["documentary"]["path"] is None
    assert resultado["text_path"] == ""
    assert resultado["mermaid_data"] is None
    assert resultado["genetic_evidence"]["kits"][0]["total_cm"] == 120
    assert resultado["comparison"]["status"] == "INCONCLUSIVO"
    assert "Nenhum caminho foi inventado" in resultado["comparison"]["detail"]


# ---------------------------------------------------------------------------
# TESTE 6 — homonimos: identidade ambigua, sem escolha silenciosa
# ---------------------------------------------------------------------------

def test_6_homonimos_nao_sao_escolhidos_em_silencio():
    resultados, _, _ = _analisar(_so_basico(**{"Joao Vieira Souza": 120}))
    resultado = resultados[0]
    dossie = resultado["documentary"]["homonyms"]

    assert dossie["exact_count"] == 2
    assert dossie["ambiguous"] is True
    assert resultado["documentary"]["status"] == "ambiguous"
    assert resultado["documentary"]["ambiguous_identity"] is True
    # o operador recebe os IDs e as fichas para decidir
    assert {ficha["id"] for ficha in dossie["exact_matches"]} == {"@J1@", "@J2@"}
    assert dossie["differences"], "as fichas divergem (datas/pais) e isso tem de aparecer"
    assert any(aviso["code"] == "homonimo" for aviso in resultado["documentary"]["warnings"])
    assert any("Identidade ambígua — análise não conclusiva." in o for o in resultado["observations"])
    assert resultado["comparison"]["status"] == "INCONCLUSIVO"


def test_6b_dossie_de_homonimo_traz_id_datas_locais_pais_conjuges_filhos():
    _carregar(GED_FAMILIA)
    dossie = homonym_dossier("Joao Vieira Souza")
    assert dossie["exact_count"] == 2
    for ficha in dossie["exact_matches"]:
        assert ficha["id"] and ficha["birth"] and ficha["parent_names"] is not None
        assert "children" in ficha and "spouses" in ficha and "birth_place" in ficha


def test_6c_homonimo_que_difere_so_no_acento_nao_e_escolhido_em_silencio():
    """O CSV e o GEDCOM divergem em acento; a busca tem de olhar os dois.

    "Jose Zacarias Vieira Souza" (sem acento) existe sem pais no GEDCOM, e
    "José Zacarias Vieira Souza" existe com pais. Antes, a busca respondia
    "nenhuma conexão" porque usava só o registro do acento exato — e escolhia o
    primeiro em silêncio.
    """
    _carregar(GED_FAMILIA)
    resultado, mensagem, sucesso = path_search("Adriano Vieira Souza", "Jose Zacarias Vieira Souza")

    assert sucesso is True
    assert mensagem == "Conexão direta encontrada (ancestral comum)."
    assert resultado["documentary"]["status"] == "ambiguous"
    assert resultado["documentary"]["label"] == "Irmãos"
    assert resultado["documentary"]["homonyms"]["exact_count"] == 2
    assert {ficha["id"] for ficha in resultado["documentary"]["homonyms"]["exact_matches"]} == {"@A1@", "@A2@"}
    assert any("Identidade ambígua" in o for o in resultado["observations"])


def test_6d_indice_de_nomes_e_invalidado_a_cada_gedcom_carregado():
    """Dois GEDCOMs diferentes não podem compartilhar o índice em cache."""
    _carregar(GED_FAMILIA)
    assert homonym_dossier("Joao Vieira Souza")["exact_count"] == 2

    _carregar(GED_PEDIGREE_COLLAPSE)
    assert homonym_dossier("Joao Vieira Souza")["exact_count"] == 0

    _carregar(GED_FAMILIA)
    assert homonym_dossier("Joao Vieira Souza")["exact_count"] == 2


def test_6e_normalizacao_de_nome_tolera_acento_e_mojibake():
    """Mesmo nome com acento, sem acento e com mojibake tem de ser o mesmo nome."""
    from core.documentary_relationship import normalizar

    variantes = [
        "José Vicente de Souza",
        "Jose Vicente de Souza",
        "Jos\u00c3\u00a9 Vicente de Souza",  # "José" lido como latin-1
        "JOSÉ VICENTE DE SOUZA",
    ]
    assert len({normalizar(v) for v in variantes}) == 1
    assert normalizar(None) == ""
    assert normalizar("") == ""


# ---------------------------------------------------------------------------
# TESTE 7 — multiplos caminhos: nenhum caminho e descartado
# ---------------------------------------------------------------------------

def test_7_multiplos_caminhos_sao_identificados():
    _carregar(GED_PEDIGREE_COLLAPSE)
    documental = documentary_relationship("@K11@", "@K12@")

    assert documental["status"] == "found"
    assert len(documental["common_ancestors"]) > 1, "o casal fundador é ancestral comum dos dois"
    assert documental["additional_paths"], "os caminhos alternativos têm de ser listados"
    codigos = {aviso["code"] for aviso in documental["warnings"]}
    assert "caminhos_multiplos" in codigos
    assert "colapso_de_pedigree" in codigos, "primos que se casam produzem colapso de pedigree"
    for caminho in documental["additional_paths"]:
        assert caminho["names"][0] and caminho["names"][-1]
        assert caminho["ancestor_name"]


# ---------------------------------------------------------------------------
# TESTE 8 — mesmo nome em mais de um kit: nunca somar kits
# ---------------------------------------------------------------------------

CSV_DOIS_KITS = (
    "Kit number,Name,Chromosome,Start,End,cM,SNPs,Source\n"
    "A1111111,Soraia Vieira Souza,1,1000,2000,100,600,GEDmatch\n"
    "B2222222,Soraia Vieira Souza,2,3000,4000,50,300,GEDmatch\n"
)


def test_8_mesmo_nome_em_dois_kits_nao_soma_segmentos():
    resultados, _, mensagem = _analisar(CSV_DOIS_KITS)

    assert mensagem.startswith("2 conexões encontradas")
    assert {r["kit"] for r in resultados} == {"A1111111", "B2222222"}
    assert sorted(r["cm"] for r in resultados) == [50, 100]
    for resultado in resultados:
        assert resultado["genetic_evidence"]["totals"]["cm"] == resultado["cm"]
        assert len(resultado["genetic_evidence"]["kits"]) == 1
        assert any("mais de um kit" in o for o in resultado["observations"])
    # o cM de cada kit foi avaliado sozinho: nenhuma hipotese sobre 150 cM
    for resultado in resultados:
        assert all(bloco["total_cm"] != 150 for bloco in resultado["hypotheses"])


def test_8b_sem_coluna_de_kit_a_evidencia_avisa():
    import pandas as pd

    caminho = _csv("Name,cM\nSoraia Vieira Souza,100\nSoraia Vieira Souza,50\n")
    try:
        df = pd.read_csv(caminho)
    finally:
        os.remove(caminho)

    evidencias, avisos = build_genetic_evidence(df)
    assert any(aviso["code"] == "kit_ausente" for aviso in avisos)
    dossie = evidencias["soraia vieira souza"]
    assert list(dossie) == [SEM_KIT]
    evidencia = evidence_for(dossie, avisos=avisos)
    # Sem kit identificado, a soma so e legitima se for mesmo a mesma pessoa.
    assert evidencia["totals"]["cm"] == 150
    assert any(aviso["code"] == "kit_ausente" for aviso in evidencia["warnings"])


def test_8c_kit_chamado_SEM_KIT_nao_colide_com_a_ausencia_de_kit():
    """A sentinela do agrupamento nao pode colidir com um kit real.

    Risco E-03, fechado em 2026-10-05: antes a sentinela era o literal
    "SEM-KIT", e um CSV que trouxesse um kit com esse texto exato fazia as
    linhas SEM kit caírem no mesmo grupo das linhas COM ele - somando cM de
    origens diferentes. A sentinela passou a levar um espaco a esquerda, que
    `_clean` remove de todo valor real do CSV.
    """
    import pandas as pd

    caminho = _csv(
        "Name,cM,Kit\n"
        "Soraia Vieira Souza,100,ZL6373425\n"
        "Soraia Vieira Souza,50,ZL6373425\n"
        "Soraia Vieira Souza,25,\n"
        "Soraia Vieira Souza,10,SEM-KIT\n"
    )
    try:
        df = pd.read_csv(caminho)
    finally:
        os.remove(caminho)

    evidencias, _avisos = build_genetic_evidence(df)
    dossie = evidencias["soraia vieira souza"]

    assert len(dossie) == 3, (
        "os tres casos precisam ficar separados: kit real, ausencia de kit e "
        "um kit literalmente chamado SEM-KIT"
    )
    assert dossie["ZL6373425"]["total_cm"] == 150
    assert dossie[SEM_KIT]["total_cm"] == 25, "ausencia de kit nao pode somar com o kit homonimo"
    assert dossie["SEM-KIT"]["total_cm"] == 10, "o kit real de nome SEM-KIT preserva o proprio total"


# ---------------------------------------------------------------------------
# TESTE 9 — cM pequeno nao vira parentesco especifico
# ---------------------------------------------------------------------------

def test_9_cm_pequeno_nao_classifica_parentesco():
    bloco = possible_relationships(6.4)
    assert len(bloco["possible_relationships"]) > 1
    assert bloco["confidence"] != "alta"
    nomes = {c["name_pt"] for c in bloco["possible_relationships"]}
    assert "Primos de 4º grau" in nomes and "Primos de 2º grau (2× removidos)" in nomes

    resultados, _, _ = _analisar(_so_basico(**{"Vicente Vieira Souza": 6.4}))
    resultado = resultados[0]
    # o parentesco exibido continua sendo o do GEDCOM, nao o do cM
    assert resultado["documentary"]["label"] == "Primos de 2º grau"
    assert resultado["comparison"]["status"] in ("POSSIVEL", "CONFLITANTE", "INCONCLUSIVO")
    assert len(resultado["hypotheses"][0]["possible_relationships"]) > 1


# ---------------------------------------------------------------------------
# TESTE 10 — cM dentro de varias faixas: varias possibilidades
# ---------------------------------------------------------------------------

def test_10_cm_dentro_de_varias_faixas_lista_varias_possibilidades():
    bloco = possible_relationships(100)
    assert len(bloco["possible_relationships"]) >= 5
    assert bloco["confidence"] == "muito baixa"
    for candidata in bloco["possible_relationships"]:
        assert candidata["range_low"] <= 100 <= candidata["range_high"]
    assert bloco["reference"]["version"] == "4.0"
    assert "sobrepostas" in bloco["interpretation"]

    resultados, _, _ = _analisar(_so_basico(**{"Helena Vieira Lima": 100}))
    resultado = resultados[0]
    assert len(resultado["hypotheses"][0]["possible_relationships"]) >= 5
    assert resultado["documentary"]["label"] == "Primos de 1º grau"


# ---------------------------------------------------------------------------
# Regressao do defeito que motivou a regra: data impossivel no GEDCOM
# ---------------------------------------------------------------------------

def test_rotulo_documental_cobre_toda_a_tabela_de_parentesco():
    """(subidas em cada lado) -> rotulo. Bug real: (1,1) saiu como tio/tia."""
    from core.documentary_relationship import documentary_label

    casos = {
        (0, 0): "A mesma pessoa",
        (1, 0): "Pai/Mãe ↔ Filho(a)",
        (2, 0): "Avô/Avó ↔ Neto(a)",
        (3, 0): "bisavô/avó ↔ bisneto(a)",
        (1, 1): "Irmãos",
        (1, 2): "Tio/Tia ↔ Sobrinho(a)",
        (1, 3): "Tio/Tia-avô/avó ↔ Sobrinho(a)-neto(a)",
        (1, 4): "Tio/Tia-bisavô/avó ↔ Sobrinho(a)-bisneto(a)",
        (2, 2): "Primos de 1º grau",
        (2, 3): "Primos de 1º grau (1× removido)",
        (2, 4): "Primos de 1º grau com 2× remoção",
        (3, 3): "Primos de 2º grau",
        (4, 4): "Primos de 3º grau",
        (5, 5): "Primos de 4º grau",
        (4, 8): "Primos de 3º grau com 4× remoção",
    }
    for (a, b), esperado in casos.items():
        assert documentary_label(a, b)["label"] == esperado, (a, b)
        assert documentary_label(b, a)["label"] == esperado, (b, a)
        assert documentary_label(a, b)["meioses"] == a + b, (a, b)

    assert documentary_label(1, 1)["key"] == "SIBLINGS"
    assert documentary_label(2, 2)["key"] == "1C"
    assert documentary_label(3, 3)["key"] == "2C"
    assert documentary_label(1, 2)["key"] == "AUNT_UNCLE"
    assert documentary_label(1, 2)["meioses"] == 3
    assert documentary_label(3, 1)["key"] == "GREAT_AUNT_1", "3 subidas x 1 = tio-avô (4 meioses)"
    assert documentary_label(3, 1)["meioses"] == 4
    assert documentary_label(1, 4)["key"] == "GREAT_AUNT_2"
    assert documentary_label(1, 4)["meioses"] == 5
    assert documentary_label(4, 4)["meioses"] == 8
    # Caso real deste repositorio: 8 subidas de um lado, 2 do outro = 1C6R, 10 meioses.
    assert documentary_label(8, 2)["key"] == "1C6R"
    assert documentary_label(8, 2)["meioses"] == 10


def test_vinculo_cronologicamente_impossivel_e_avisado_sem_reescrever_o_gedcom():
    _carregar(GED_DATA_IMPOSSIVEL)
    # Adriano (@X5@) e a avo Maria (@X1@), que o GEDCOM declara mae de Celso.
    documental = documentary_relationship("@X5@", "@X1@")

    # O GEDCOM continua determinando o parentesco: nada foi corrigido nem apagado.
    assert documental["status"] == "found"
    assert documental["label"] == "Avô/Avó ↔ Neto(a)"
    assert documental["path"]["ids"] == ["@X5@", "@X3@", "@X1@"]

    # O salto com data impossivel aparece na evidencia e vira aviso.
    impossiveis = [e for e in documental["evidence"] if e["plausible"] is False]
    assert impossiveis, "a mãe nascida depois do filho tem de aparecer como evidência"
    salto = impossiveis[0]
    assert salto["child_name"] == "Celso Vieira Souza"
    assert salto["parent_name"] == "Maria Vieira Souza"
    assert salto["age_at_birth"] == -11
    assert salto["family_id"] == "@FX@"
    assert any(aviso["code"] == "data_impossivel" for aviso in documental["warnings"])


def test_afinidade_nao_e_apresentada_como_parentesco():
    _carregar(GED_FAMILIA)
    # Marta (esposa de Pedro) e Jorge (marido de Rita): ligados só por casamento.
    resultado, mensagem, sucesso = path_search("Marta Souza", "Jorge Lima")
    assert sucesso is True
    assert mensagem == "Conexão indireta encontrada (via casamento/afinidade)."
    assert resultado["documentary"]["status"] == "affinity"
    assert "afinidade" in resultado["documentary"]["label"]
    assert any(aviso["code"] == "afinidade" for aviso in resultado["documentary"]["warnings"])


# ---------------------------------------------------------------------------
# Leitura do CSV: separador, linha torta e arquivo trocado
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("separador", [",", ";", "\t"])
def test_csv_com_outro_separador_e_lido_e_analisado(separador):
    """Export com ponto e vírgula ou TAB não pode virar uma coluna só."""
    from parsers.csv_ingest import read_csv_with_fallback

    texto = (separador.join(["Name", "cM"]) + "\n"
             + separador.join(["Soraia Vieira Souza", "2600"]) + "\n")
    caminho = _csv(texto)
    try:
        df = read_csv_with_fallback(caminho)
    finally:
        os.remove(caminho)

    assert df.attrs["separador"] == separador
    assert list(df.columns) == ["Name", "cM"]

    resultados, _, mensagem = _analisar(texto)
    assert mensagem.startswith("1 conexões encontradas")
    assert resultados[0]["cm"] == 2600
    assert resultados[0]["comparison"]["status"] == "COMPATIVEL"


def test_leitura_tolera_linha_torta_e_reporta_a_linha():
    """O erro cru do pandas ('Expected 1 fields in line 4, saw 2') não pode subir."""
    from parsers.csv_ingest import read_csv_with_fallback

    texto = "Name,cM\nSoraia Vieira Souza,100\nSoraia Vieira Souza,100,CAMPO-A-MAIS\n"
    caminho = _csv(texto)
    try:
        df = read_csv_with_fallback(caminho)
    finally:
        os.remove(caminho)

    assert len(df) == 1, "a linha boa continua no DataFrame; só a torta sai"
    assert df.attrs["linhas_ignoradas"] == [3]
    assert df.attrs["erro_de_leitura"], "o erro original do pandas fica registrado"


def test_linha_torta_nao_derruba_a_analise_e_aparece_nas_observacoes():
    texto = ("Kit number,Name,Chromosome,Start,End,cM,SNPs\n"
             "A1111111,Soraia Vieira Souza,1,10,20,2600,500\n"
             "A1111111,Soraia Vieira Souza,1,10,20,2600,500,CAMPO-A-MAIS\n")
    resultados, descartados, mensagem = _analisar(texto)

    assert mensagem.startswith("1 conexões encontradas")
    assert descartados == []
    assert resultados[0]["cm"] == 2600
    assert any("número de campos diferente do cabeçalho" in o for o in resultados[0]["observations"])
    assert any("linha(s) 3" in o for o in resultados[0]["observations"])


def test_csv_com_preambulo_de_export_e_lido_a_partir_do_cabecalho():
    """Export que traz linhas de título antes das colunas não pode virar erro."""
    from parsers.csv_ingest import localizar_cabecalho, read_csv_with_fallback

    texto = ("Relatório de matches - GEDmatch\n"
             "Gerado em 2026-10-05\n"
             "Kit number,Name,Chromosome,Start,End,cM,SNPs\n"
             "A1111111,Soraia Vieira Souza,1,10,20,2600,500\n")
    caminho = _csv(texto)
    try:
        assert localizar_cabecalho(caminho, ",") == 2
        df = read_csv_with_fallback(caminho)
    finally:
        os.remove(caminho)

    assert df.attrs["linhas_antes_do_cabecalho"] == 2
    assert list(df.columns)[:3] == ["Kit number", "Name", "Chromosome"]
    assert len(df) == 1

    resultados, _, mensagem = _analisar(texto)
    assert mensagem.startswith("1 conexões encontradas")
    assert resultados[0]["cm"] == 2600
    assert any("antes do cabeçalho" in o for o in resultados[0]["observations"])


def test_arquivo_sem_cabecalho_nao_ganha_cabecalho_inventado():
    """Guarda do detector: tabela sem cabeçalho não pode ter a 1ª linha pulada."""
    from parsers.csv_ingest import localizar_cabecalho

    caminho = _csv("Soraia Vieira Souza,2600\nJoao Vieira Souza,100\n")
    try:
        assert localizar_cabecalho(caminho, ",") == 0
    finally:
        os.remove(caminho)


def test_arquivo_que_nao_e_lista_de_matches_explica_o_problema_em_portugues():
    """Reprodução do relato: GEDCOM enviado no campo do CSV.

    Antes, a tela mostrava `Ocorreu um erro: Error tokenizing data. C error:
    Expected 1 fields in line 4, saw 2`. Agora o erro nomeia o separador usado,
    as colunas encontradas e a linha divergente, e diz o que conferir.
    """
    ged_como_csv = "0 HEAD\n1 SOUR TESTE\n1 GEDC\n2 DATE 1 JAN 1900, Sao Paulo\n0 TRLR\n"
    _carregar(GED_FAMILIA)
    caminho = _csv(ged_como_csv)
    try:
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(caminho, "Adriano Vieira Souza")
    finally:
        os.remove(caminho)

    mensagem = str(excinfo.value)
    assert "Error tokenizing" not in mensagem, "o texto cru do pandas não pode chegar ao operador"
    assert "separador" in mensagem
    assert "GEDCOM" in mensagem
    assert "linha(s) 4" in mensagem, "a linha que o pandas apontava tem de aparecer"


def test_csv_vazio_ou_sem_colunas_nao_estoura_erro_cru():
    _carregar(GED_FAMILIA)
    caminho = _csv("X,Y\n1,2\n")
    try:
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(caminho, "Adriano Vieira Souza")
    finally:
        os.remove(caminho)
    assert "não encontradas" in str(excinfo.value)
    assert "separador" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Texto da interface: o rotulo antigo nao pode reaparecer
# ---------------------------------------------------------------------------

def test_nenhuma_tela_apresenta_relacionamento_provavel():
    pasta = os.path.join(RAIZ, "src", "templates")
    for arquivo in os.listdir(pasta):
        with open(os.path.join(pasta, arquivo), encoding="utf-8") as fh:
            conteudo = fh.read()
        assert not re.search(r"Relacionamento\s+Prov[áa]vel", conteudo, re.IGNORECASE), (
            f"{arquivo} ainda apresenta o rótulo antigo")

    with open(os.path.join(pasta, "index.html"), encoding="utf-8") as fh:
        html = fh.read()
    for obrigatorio in ("Parentesco documental", "Evidência genética",
                        "Possibilidades de parentesco pelo DNA", "Confrontação GEDCOM × DNA",
                        "Observações", "Parentesco documental encontrado no GEDCOM"):
        assert obrigatorio in html, f"a tela perdeu a seção '{obrigatorio}'"
