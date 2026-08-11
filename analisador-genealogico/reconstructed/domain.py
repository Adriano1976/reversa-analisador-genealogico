"""Tarefa 01 — Entidades de Domínio.

Representação em memória das entidades do analisador-genealogico:
PERSON, FAMILIA e DNA_MATCH, sem persistência (estado em memória).
Inclui as rotinas de limpeza de mojibake documentadas em domain.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Correção de mojibake (encoding corrompido Latin-1 lido como UTF-8)
# ---------------------------------------------------------------------------

# Pares de substituição heurística para acentos portugueses corrompidos.
MOJIBAKE_MAP = {
    # Combinações de caractere de composição (\u0303 til combinante).
    "A\u0303": "Ã",
    "O\u0303": "Õ",
    "N\u0303v": "Ñ",
    "a\u0303o": "ão",
    "A\u0303o": "ão",
    "O\u0303": "Ão",
}


def strip_bad_utf(text: str) -> str:
    """Remove bytes/caracteres inválidos de encodings quebrados.

    Substituições manuais incompletas de caracteres corrompidos por acento.
    Mantém apenas texto minimamente sanitizado para matching.
    """
    if not text:
        return text
    cleaned = text
    # Fallback de control chars e markers de substituição.
    cleaned = cleaned.replace("\ufffd", "")
    return cleaned


def demojibake(text: str) -> str:
    """Corrige encoding corrompido de acentos portugueses (mojibake).

    Converte seqüências corrompidas típicas de nomes (ex.: "Ã§" -> "ç",
    "JoA�o" -> "João") para a forma esperada.
    """
    if not text:
        return text
    out = text
    for broken, fixed in MOJIBAKE_MAP.items():
        out = out.replace(broken, fixed)
    # Corrige "Ã§" e variantes usando a decomposição de cedilha.
    out = out.replace("Ã§", "ç")
    out = out.replace("Ã\u00e7", "ç")
    return out


# ---------------------------------------------------------------------------
# Entidades de domínio
# ---------------------------------------------------------------------------

@dataclass
class Family:
    """Entidade lógica FAMILIA (registro FAM do GEDCOM).

    Contém referências ao marido (HUSB), esposa (WIFE) e filhos (CHIL),
    todos representados por xref_id de PERSON.
    """
    xref_id: str
    husb: str = ""
    wife: str = ""
    chil: list = field(default_factory=list)


class GenealogyGraph:
    """Grafo pessoa<->família construído em memória.

    Encapsula os dicionários de pessoas/famílias e o networkx.MultiGraph
    que liga indivíduos entre si, permitindo buscas de caminho.
    """

    def __init__(self) -> None:
        # PERSON:  xref_id -> dict(campos INDI)
        self.persons: dict = {}
        # FAMILIA: xref_id -> Family
        self.families: dict = {}
        # Grafo de parentesco (nós = pessoas).
        self.graph = None  # networkx.MultiGraph, construído em tarefa 02

    def register_person(self, xref_id: str, name: str, sub_records=None) -> None:
        """Registra uma pessoa na árvore, normalizando 'name'.."""
        if xref_id in self.persons:
            return
        self.persons[xref_id] = {
            "xref_id": xref_id,
            "name": name,
            "name_clean": demojibake(name).strip(),
            "sub_records": sub_records or [],
        }

    def get_person(self, xref_id: str):
        return self.persons.get(xref_id)

    def register_family(self, familie: Family) -> None:
        self.families[familie.xref_id] = familie

    @property
    def g(self):
        """Retorna o grafo (lazy) — definido na Tarefa 02."""
        return self.conexoes


@dataclass
class DNAGroup:
    """Entidade DNA_MATCH — agregação de segmentos de um mesmo match.

    _group_key = nome normalizado + ID/email; cm é a soma de centiMorgans.
    """
    _group_key: str
    cm: float
    matched_name: str = ""
    aux: str = ""