"""Testes das excecoes de dominio tipadas (`T009`, `T010`; `RF-03`, `RF-04`, `RF-05`).

Dois grupos, com perguntas diferentes:

- **`T009`** pergunta pela FORMA da hierarquia: cada tipo novo e capturavel como
  `ValueError` e a raiz `ErroDeDominio` captura os quatro. Este e o teste que
  impede a heranca de ser removida numa refatoracao futura — e sem ela as quatro
  assercoes de `RF-05` (que exigem `pytest.raises(ValueError)`) param de passar.
- **`T010`** pergunta pelo COMPORTAMENTO dos quatro pontos migrados: cada um
  continua levantando **no mesmo ponto**, com o **mesmo literal de mensagem**.
  Trocar o tipo levantado nao pode ter mudado um caractere do texto.

O segundo grupo e o que da valor ao primeiro. Uma hierarquia bonita e inutil se a
mensagem que o operador le tiver mudado junto.
"""
from __future__ import annotations

import os
import sys

import networkx as nx
import pandas as pd
import pytest

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

from core import dna_analysis as fluxo_dna  # noqa: E402
from core import genetic_evidence  # noqa: E402
from core import erros  # noqa: E402
from parsers import csv_ingest  # noqa: E402

TIPOS = [
    erros.PessoaNaoEncontrada,
    erros.GedcomNaoSuportado,
    erros.DnaCsvSemColunas,
    erros.CsvIlegivel,
]

ARVORE_VAZIA = ({}, {}, nx.Graph(), {})


# ---------------------------------------------------------------------------
# T009 — a forma da hierarquia
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tipo", TIPOS, ids=lambda t: t.__name__)
def test_tipo_de_dominio_e_capturavel_como_value_error(tipo):
    """`RF-05`: as quatro assercoes existentes da suite capturam `ValueError`.

    Este e o teste que sustenta a decisao de `ErroDeDominio` herdar de
    `ValueError`. Remover a heranca quebra a suite existente em quatro pontos
    (`tests/test_confrontacao_gedcom_dna.py:920`, `:936` e
    `tests/test_dna_analysis.py:219`, `:241`), e quebra aqui primeiro.
    """
    assert issubclass(tipo, ValueError), (
        "%s deixou de herdar de ValueError; as quatro assercoes de RF-05 quebram"
        % tipo.__name__
    )


def test_raiz_captura_os_quatro_tipos():
    """`pytest.raises(ErroDeDominio)` tem de pegar cada um dos quatro."""
    for tipo in TIPOS:
        with pytest.raises(erros.ErroDeDominio):
            raise tipo("mensagem qualquer")


def test_raiz_e_capturavel_como_value_error():
    with pytest.raises(ValueError):
        raise erros.ErroDeDominio("mensagem qualquer")


def test_nenhum_tipo_novo_alem_dos_quatro():
    """`A002`: `ArmazenamentoInvalido` foi descartado e nao pode reaparecer.

    Um tipo que nenhum ponto levanta e superficie sem gatilho — a mesma classe de
    defeito que a divida #17 da feature 005 fechou. Se um quinto tipo aparecer,
    este teste falha e obriga a decidir se ele tem gatilho real.
    """
    declarados = {nome for nome in dir(erros) if not nome.startswith("_")}
    tipos = {
        nome for nome in declarados
        if isinstance(getattr(erros, nome), type)
        and issubclass(getattr(erros, nome), erros.ErroDeDominio)
    }
    assert tipos == {"ErroDeDominio"} | {t.__name__ for t in TIPOS}, tipos


def test_tipos_de_dominio_nao_sao_irmaos_de_tipos_da_linguagem():
    """A distincao entre dominio e valor e por TIPO, nunca por mensagem.

    Consequencia declarada em `requirements.md` §4: como as duas linhagens se
    encontram em `ValueError`, um `except ValueError` que tente distinguir pelo
    texto estaria errado por construcao. O que prova a distincao e a assinatura.
    """
    with pytest.raises(ValueError) as capturado:
        raise erros.PessoaNaoEncontrada("x")
    assert isinstance(capturado.value, erros.ErroDeDominio)
    assert not type(capturado.value) is ValueError


# ---------------------------------------------------------------------------
# T010 — os quatro pontos de deteccao continuam levantando no mesmo lugar
# ---------------------------------------------------------------------------

class _DependenciasFalsas:
    """So o que o fluxo de DNA toca antes do ponto que levanta."""

    def __init__(self, df, colunas=(None, None, None, None)):
        self._df = df
        self._colunas = colunas

    def read_csv(self, _caminho):
        return self._df

    def detect_columns(self, _df):
        return self._colunas

    def aggregate_matches(self, *_a, **_k):  # pragma: no cover - nao alcancado
        raise AssertionError("o fluxo passou do ponto que devia levantar")

    def generate_mermaid(self, *_a, **_k):  # pragma: no cover - nao alcancado
        raise AssertionError("o fluxo passou do ponto que devia levantar")

    def generate_mermaid_indirect(self, *_a, **_k):  # pragma: no cover
        raise AssertionError("o fluxo passou do ponto que devia levantar")


def test_raiz_ausente_levanta_pessoa_nao_encontrada_com_o_mesmo_texto():
    """Ponto 1 de 4: `core/dna_analysis.py`, busca da pessoa-raiz por nome."""
    with pytest.raises(erros.PessoaNaoEncontrada) as capturado:
        fluxo_dna.dna_analysis("nao_importa.csv", "Zzz Ninguem",
                               _DependenciasFalsas(pd.DataFrame()), ARVORE_VAZIA)
    assert str(capturado.value) == "Seu nome 'Zzz Ninguem' não foi encontrado no GEDCOM."


def test_csv_sem_colunas_no_fluxo_levanta_dna_csv_sem_colunas():
    """Ponto 2 de 4: `core/dna_analysis.py`, colunas obrigatorias ausentes.

    O texto e o acionavel, e nao o curto: ele diz o separador usado e as colunas
    encontradas. A interpolacao muda com o arquivo, entao o que este teste prende
    e a MOLDURA + os valores do caso montado — que e o que a tela mostra.
    """
    arvore = ({"@I1@": _pessoa("Joao Silva")}, {}, nx.Graph(), {})
    df = pd.DataFrame({"alfa": [1], "beta": [2]})
    df.attrs["separador"] = ","
    with pytest.raises(erros.DnaCsvSemColunas) as capturado:
        fluxo_dna.dna_analysis("nao_importa.csv", "Joao Silva",
                               _DependenciasFalsas(df), arvore)
    texto = str(capturado.value)
    assert texto.startswith("Colunas de Nome e cM não encontradas no CSV. ")
    assert "O arquivo foi lido com o separador ','" in texto
    assert "['alfa', 'beta']" in texto
    assert texto.endswith(
        "Confira se o arquivo enviado é a lista de matches de DNA "
        "(exportação do GEDmatch/MyHeritage/FamilyTreeDNA) e não o GEDCOM ou outro CSV."
    )


def test_evidencia_sem_colunas_levanta_dna_csv_sem_colunas_curto():
    """Ponto 3 de 4: `core/genetic_evidence.py`, mensagem curta.

    Dois pontos levantam o MESMO tipo com textos diferentes de proposito. Este
    teste prende o curto; o de cima prende o acionavel.
    """
    with pytest.raises(erros.DnaCsvSemColunas) as capturado:
        genetic_evidence.build_genetic_evidence(pd.DataFrame({"alfa": [1]}))
    assert str(capturado.value) == "Colunas de Nome e cM não encontradas no CSV."


def test_csv_ilegivel_levanta_csv_ilegivel_com_o_mesmo_texto(monkeypatch):
    """Ponto 4 de 4: `parsers/csv_ingest.py`, nenhuma tentativa produz tabela.

    O caminho real exige que utf-8 **e** latin-1 falhem, e latin-1 aceita
    praticamente qualquer byte: alcancar o `raise` de verdade por um arquivo seria
    depender de um acidente do pandas. O teste substitui a leitura para forcar a
    condicao — o que ele mede e o TEXTO do ponto de levantamento, que e o que a
    tela exibe, e nao a capacidade do pandas de falhar.
    """
    def recusa(*_a, **_k):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(csv_ingest.pd, "read_csv", recusa)
    monkeypatch.setattr(csv_ingest, "detectar_separador", lambda *_a: ",")
    monkeypatch.setattr(csv_ingest, "localizar_cabecalho", lambda *_a: 0)
    monkeypatch.setattr(csv_ingest, "_linhas_csv", lambda *_a: [])

    with pytest.raises(erros.CsvIlegivel) as capturado:
        csv_ingest.read_csv_with_fallback("nao_importa.csv")
    texto = str(capturado.value)
    assert texto.startswith("Não foi possível ler o arquivo CSV. Tentativas feitas: ")
    assert "encoding utf-8 recusado (invalid start byte)" in texto
    assert "encoding latin-1 recusado (invalid start byte)" in texto
    assert texto.endswith(
        "Confira se o arquivo enviado é a lista de matches de DNA "
        "(CSV com colunas de nome e de cM) e não o GEDCOM ou outro arquivo."
    )


def test_teto_de_upload_nao_mudou_de_valor():
    """`T004`/`D-10`: nomear a constante nao pode ter mudado o numero.

    O valor e o literal do `app.py:52` antes da extração. Se ele mudar, a mensagem
    de `413` muda junto e a paridade da tela cai — e a `RN-01` proibe.
    """
    from app import TETO_DE_UPLOAD_EM_BYTES, TETO_DE_UPLOAD_EM_MB

    assert TETO_DE_UPLOAD_EM_BYTES == 16 * 1024 * 1024
    assert TETO_DE_UPLOAD_EM_MB == 16


def _pessoa(nome):
    """Registro minimo com o que `get_name` le (`core/registro.py`).

    `get_name` chama `person.name.format()`, e nao `str(person.name)` — a copia
    fiel do oraculo. O duplo precisa expor `format()`, senao o teste falha por
    `AttributeError` antes de chegar no ponto que quer medir.
    """
    class _Nome:
        def __init__(self, valor):
            self.value = valor

        def format(self):
            return self.value

    class _Pessoa:
        def __init__(self, valor):
            self.name = _Nome(valor)
            self.sub_records = []

    return _Pessoa(nome)
