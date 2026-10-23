"""O cartao de analise tem um conjunto de chaves, e os dois construtores o respeitam.

## Por que este arquivo existe

`OPP-20261023-UNCA`. Dois construtores montam o mesmo cartao:

- `core.passo_por_kit._cartao_do_kit`, com 40 chaves;
- `core.cartao_sem_correspondencia._cartao_sem_correspondencia`, com as mesmas 40 mais
  a marca `sem_correspondencia`.

Nenhum teste fixava esse conjunto, e as duas listas ja tinham divergido na ORDEM. Como
o template le por nome, uma chave criada em um construtor e esquecida no outro virava
campo vazio na tela para metade dos cartoes, sem erro nenhum.

O teste produz um cartao de cada tipo pelas fixtures que ja existem e compara o
conjunto de chaves com `CHAVES_DO_CARTAO`. A tupla sozinha nao impede nada; e esta
comparacao que transforma a divergencia em falha.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.contrato_do_cartao import (  # noqa: E402
    CHAVE_SEM_CORRESPONDENCIA,
    CHAVES_DO_CARTAO,
)
from core.dna_analysis import dna_analysis  # noqa: E402
from parsers import gedcom_parser  # noqa: E402
from tests.fixtures.helpers import arvore_de, deps  # noqa: E402
from tests.fixtures.sample_dna import (  # noqa: E402
    DNA_CSV_NO_INTERSECTION,
    DNA_CSV_UTF8,
    DNA_GED,
)


def _cartoes(csv: str) -> list[dict]:
    """Roda a analise de DNA sobre a fixture sintetica e devolve os cartoes."""
    descritor, caminho_ged = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write(DNA_GED)
        arvore = arvore_de(gedcom_parser.carregar_arvore(caminho_ged))
    finally:
        os.remove(caminho_ged)

    descritor, caminho_csv = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(csv)
        resultados, _descartados, _mensagem = dna_analysis(
            caminho_csv, "Carlos Silva Souza", deps(), arvore
        )
    finally:
        os.remove(caminho_csv)
    return resultados


def test_o_cartao_normal_tem_exatamente_as_chaves_do_contrato():
    cartoes = _cartoes(DNA_CSV_UTF8)
    normais = [cartao for cartao in cartoes if not cartao.get(CHAVE_SEM_CORRESPONDENCIA)]

    assert len(normais) == 1
    assert set(normais[0]) == set(CHAVES_DO_CARTAO)


def test_o_cartao_sem_correspondencia_acrescenta_so_a_marca():
    cartoes = _cartoes(DNA_CSV_NO_INTERSECTION)
    especiais = [cartao for cartao in cartoes if cartao.get(CHAVE_SEM_CORRESPONDENCIA)]

    assert len(especiais) == 1
    assert set(especiais[0]) == set(CHAVES_DO_CARTAO) | {CHAVE_SEM_CORRESPONDENCIA}
