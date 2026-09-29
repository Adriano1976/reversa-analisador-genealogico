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

# Limpeza de nome: autoridade unica do projeto.
#
# Estes dois corpos vieram de `dna_analysis` por extracao, porque era ele quem os
# usava de fato. A versao anterior deste modulo apenas removia U+FFFD e nao era
# consumida por nenhum caminho de producao, o que fazia as duas implementacoes
# divergirem em 5 de 9 casos. Ver `_reversa_sdd/addenda/003-refactor-code-quality.md`.


def strip_bad_utf(s):
    if s is None:
        return ""
    s = str(s)
    fixes = {
        "A�": "ç", "Ã§": "ç",
        "Ã£": "ã", "Ã¡": "á", "Ã¢": "â",
        "Ã©": "é", "Ãª": "ê", "Ã¨": "è",
        "Ã­": "í", "Ã³": "ó", "Ã´": "ô", "Ãº": "ú",
        "Ã": "Ã",
        "GouvA�": "Gouvê",
        "A�": "ç",
        "JoA�o": "João", "SA�": "Sá", "GonA�": "Gonç",
    }
    for bad, good in fixes.items():
        s = s.replace(bad, good)
    return re.sub(r"[^\w\sÁ-ú'-]", " ", s)


def demojibake(s):
    if not s:
        return s
    if any(p in s for p in ("Ã", "Â", "A�", "�")):
        try:
            fixed = s.encode("latin1").decode("utf-8")
            if "�" not in fixed and "Ã" not in fixed and "A�" not in fixed:
                return fixed
        except Exception:
            pass
    return s


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

@dataclass
class DNAGroup:
    """Entidade DNA_MATCH — agregação de segmentos de um mesmo match.

    _group_key = nome normalizado + ID/email; cm é a soma de centiMorgans.
    """
    _group_key: str
    cm: float
    matched_name: str = ""
    aux: str = ""