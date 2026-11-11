"""Normalizacao de um nome para forma comparavel. Modulo puro, sem dominio.

Nasceu da OPP-20261006-LIGH: `norm_name` vivia em `core.name_normalization`, e
`parsers/csv_ingest.py` o importava de la para montar a chave de agrupamento dos
matches — uma das duas arestas do ciclo `core/` <-> `parsers/`.

Por isso a funcao e de `utils/`, e nao de `core/`: ela nao sabe nada de genealogia,
so recebe um texto e devolve o mesmo texto em forma comparavel (sem acento, sem
pontuacao, minusculo, espacos colapsados). A unica dependencia e `strip_bad_utf`,
do proprio `utils/`; o vocabulario de dominio — particulas, prenomes genericos,
sufixos de sobrenome e as equivalencias — ficou em `core.name_normalization`.

`core.name_normalization` reexporta este nome, de modo que `norm_name` continua
importavel do endereco antigo: `core.dna_analysis.__all__` e o harness de paridade
o alcancam por la.
"""
from __future__ import annotations

import string
import unicodedata
from functools import lru_cache

from .text_cleaning import strip_bad_utf


@lru_cache(maxsize=50_000)
def _norm_name_texto(texto: str) -> str:
    """Corpo da normalizacao, memoizado pela string de entrada.

    A analise de DNA do arquivo real chama `norm_name` ~69 mil vezes, e a maior
    parte delas repete o mesmo nome: o indice do GEDCOM normaliza cada pessoa
    uma vez, e o laco de candidatos renormaliza os mesmos nomes a cada match. O
    valor nao depende de nada alem do texto, entao o cache nao muda decisao
    nenhuma — muda o custo. Teto de 50 mil entradas: o GEDCOM real tem 19.403
    pessoas, e o teto cabe com folga sem crescer sem limite em processo longo.
    """
    s = strip_bad_utf(texto)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("/", " ")
    s = "".join(ch if ch not in set(string.punctuation) else " " for ch in s)
    s = " ".join(s.lower().split())
    return s


def norm_name(s):
    """Forma comparavel do nome; a mesma string devolve o mesmo valor (cache)."""
    return _norm_name_texto(str(s))


__all__ = ["norm_name"]
