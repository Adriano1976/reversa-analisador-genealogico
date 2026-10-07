"""Contrato de escape do rotulo Mermaid.

Reproducao do BUG-20260929-J6PQ: um nome vindo do GEDCOM consegue impedir o
diagrama de renderizar. O gatilho confirmado em navegador e a sequencia aspa
mais crase, produzida por nome que comeca com crase, que desvia o lexer do
Mermaid para o modo markdown-string e faz o fecha-colchete nunca virar o token
que a gramatica exige.

O que a gramatica do flowchart prova sobre um rotulo entre aspas:
  - dentro do estado `string`, o lexer consome tudo com `<string>[^"]+`, entao
    colchete, crase no meio, dois pontos e palavra-chave sao inertes;
  - o unico caractere que encerra o rotulo antes do fim e a propria aspa dupla;
  - a crase so e perigosa quando vem imediatamente depois da aspa de abertura.

Estes testes sao de REGRESSAO permanente, nao prova de paridade com o legado.
"""
import os
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parsers import gedcom_parser
from reporting.mermaid_render import _mermaid_label
from core.path_search import path_search
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps

# Forma exata de uma linha de no: identificador, rotulo entre aspas, e nada mais.
LINHA_DE_NO = re.compile(r'^N_[A-Za-z0-9_]+\["[^"]*"\]$')

# Payloads sem barra e sem quebra de linha, que quebrariam o GEDCOM antes de
# chegarem ao rotulo. O primeiro e o gatilho confirmado em navegador.
NOMES_HOSTIS = [
    "`pwn",
    "Joao] --> N_evil",
    'Joao] --> N_evil["pwn',
    "Ana subgraph",
    "Pedro end",
]


def _gedcom_com_nome(nome_hostil: str) -> str:
    """GEDCOM minimo: Ana Raiz -> <nome hostil> -> Alvo Filho."""
    return "\n".join([
        "0 HEAD",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
        "0 @I1@ INDI",
        "1 NAME Ana /Raiz/",
        "0 @I2@ INDI",
        "1 NAME %s /Hostil/" % nome_hostil,
        "0 @I3@ INDI",
        "1 NAME Alvo /Filho/",
        "0 @F1@ FAM",
        "1 HUSB @I1@",
        "1 CHIL @I2@",
        "0 @F2@ FAM",
        "1 HUSB @I2@",
        "1 CHIL @I3@",
        "0 TRLR",
        "",
    ])


def _carregar(conteudo: str):
    """Carrega o GEDCOM e devolve a ARVORE que o parse devolveu.

    Devolvia a lista de nomes, que nao serve para navegar: quem chamava recorria
    ao modulo de estado. O parse ja devolve a arvore (feature 005, `T009`).
    """
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return gedcom_parser.carregar_arvore(path)
    finally:
        os.remove(path)


def _rotulos_do_diagrama(mermaid: str):
    """Devolve o texto de cada rotulo, e a linha crua de cada no."""
    linhas = [ln for ln in mermaid.splitlines() if '["' in ln]
    rotulos = []
    for ln in linhas:
        rotulos.append(ln.split('["', 1)[1].rsplit('"]', 1)[0])
    return linhas, rotulos


# ---------------------------------------------------------------------------
# Reproducao: prova que o defeito relatado aparece. Falha antes da correcao.
# ---------------------------------------------------------------------------

def test_rotulo_neutraliza_crase():
    """A crase dispara o modo markdown-string quando abre o rotulo. Nao pode sair."""
    assert "`" not in _mermaid_label("`pwn")


@pytest.mark.parametrize("nome_hostil", NOMES_HOSTIS)
def test_diagrama_nao_carrega_caractere_que_quebra_a_gramatica(nome_hostil):
    """Nenhum nome hostil pode deixar no rotulo um caractere capaz de quebrar o diagrama."""
    arvore = _carregar(_gedcom_com_nome(nome_hostil))
    result, msg, success = path_search("Ana Raiz", "Alvo Filho", _deps(), _arvore_de(arvore))

    assert success is True, msg
    mermaid = result["mermaid_data"]
    linhas, rotulos = _rotulos_do_diagrama(mermaid)

    assert linhas, "o diagrama precisa ter ao menos um no"
    for ln, rotulo in zip(linhas, rotulos):
        assert LINHA_DE_NO.match(ln), "forma de no invalida: %r" % ln
        assert '"' not in rotulo, "aspa dupla encerraria o rotulo: %r" % rotulo
        assert "`" not in rotulo, "crase desvia o lexer para markdown: %r" % rotulo


# ---------------------------------------------------------------------------
# Regressao: protegem o comportamento legitimo que nao pode voltar a quebrar.
# Passam antes e depois da correcao.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entrada,esperado", [
    ("A & B", "A &amp; B"),
    ("A < B", "A &lt; B"),
    ("A > B", "A &gt; B"),
])
def test_entidades_html_preservadas(entrada, esperado):
    """`&`, `<` e `>` continuam saindo como entidade, para serem exibidos como texto."""
    assert _mermaid_label(entrada) == esperado


@pytest.mark.parametrize("entrada,esperado", [
    ("Joao Silva", "Joao Silva"),
    ("João D'Ávila", "João D'Ávila"),
    ("Ana – Maria", "Ana - Maria"),
    ("Ana — Maria", "Ana - Maria"),
    ("Maria (Dona) Silva Jr.", "Maria (Dona) Silva Jr."),
])
def test_caracteres_legitimos_sobrevivem(entrada, esperado):
    """Acento, apostrofo, hifen e espaco atravessam o escape sem alteracao."""
    assert _mermaid_label(entrada) == esperado


@pytest.mark.parametrize("entrada,esperado", [
    ('Jose "Zeca"', "Jose 'Zeca'"),
    ("Ana\r\nMaria", "Ana Maria"),
    ("Ana\nMaria", "Ana Maria"),
    ("Ana\u00a0Maria", "Ana Maria"),
])
def test_neutralizacoes_que_ja_existiam(entrada, esperado):
    """Aspas curvas, aspa dupla, quebra de linha e espaco inquebravel seguem tratados."""
    assert _mermaid_label(entrada) == esperado


def test_rotulo_vazio_continua_vazio():
    """O diagrama indireto usa um no de rotulo vazio, e ele nao pode ganhar conteudo."""
    assert _mermaid_label(" ") == " "


# ---------------------------------------------------------------------------
# Reproducao do BUG-20261002-T4ZM: a lista branca enumerava por "seguro" em vez
# de por "inerte", e 14 caracteres imprimiveis sumiam do nome exibido.
#
# Estes dois casos FALHAM antes da correcao. O segundo tambem serve de travas
# permanente da amplitude: depois de corrigido, ele impede que a lista volte a
# estreitar em silencio.
#
# O lado da regressao desta correcao nao precisa de caso novo: os testes do
# BUG-20260929-J6PQ, acima, ja congelam que a crase sai, que a aspa dupla vira
# apostrofo e que &, < e > saem como entidade. Eles tem de seguir verdes.
# ---------------------------------------------------------------------------

CARACTERES_INERTES = "#$%*+=@\\^_{|}~"


@pytest.mark.parametrize("ch", list(CARACTERES_INERTES))
def test_caractere_inerte_sobrevive_ao_rotulo(ch):
    """Caractere inerte dentro das aspas nao pode ser descartado do rotulo.

    A gramatica do Mermaid consome tudo com `<string>[^"]+` no estado `string`,
    entao estes 14 caracteres nao tem como alterar o diagrama. O legado os
    preservava, e o candidato passou a descarta-los.
    """
    entrada = "Ana%sSilva" % ch
    assert _mermaid_label(entrada) == entrada, (
        "o caractere %r foi descartado do rotulo" % ch)


def test_lista_branca_preserva_todo_ascii_imprimivel_menos_a_crase():
    """O contrato de amplitude, medido caractere a caractere nos 95 imprimiveis.

    O unico descarte admitido e a crase, porque aspa seguida de crase desvia o
    lexer do Mermaid para markdown-string e o diagrama inteiro deixa de
    renderizar, que foi o BUG-20260929-J6PQ.

    Ficam fora da checagem `&`, `<` e `>` porque saem como entidade HTML, e a
    aspa dupla porque vira apostrofo antes de a lista ser aplicada.
    """
    descartados = []
    for codigo in range(0x20, 0x7F):
        ch = chr(codigo)
        if ch in '&<>"':
            continue
        if ch not in _mermaid_label("Ana%sSilva" % ch):
            descartados.append(ch)
    assert descartados == ["`"], "descartes inesperados: %r" % descartados
