"""Data e local do registro GEDCOM, sem nenhum parentesco.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele responde uma coisa so: o
que o registro diz sobre data e local. Nao sabe de arvore, de caminho nem de cartao.

Mora separado porque tres consumidores diferentes precisam da mesma leitura: a ficha da
pessoa, o dossie de homonimos e o proprio cartao documental.
"""
from __future__ import annotations

import re
from statistics import median

from .registro import ref_id

# Idade minima/maxima de um genitor no nascimento do filho. Fora disso o salto e
# registrado como suspeito. Nao e regra biologica: e filtro de evidencia.
IDADE_MINIMA_GENITOR = 12
IDADE_MAXIMA_GENITOR = 70

# Data e local

_ANO = re.compile(r"(\d{3,4})")


def parse_year(date_value) -> int | None:
    """Primeiro ano de 4 (ou 3) digitos de uma data GEDCOM, ou None.

    Tolera `12 OCT 1976`, `ABOUT 1920`, `BEFORE 1812`, `1815` e `DateValueSimple`
    do ged4py (convertido com `str`). Nao normaliza `BEFORE/AFTER` para aproximar
    o ano: quem le decide, e a evidencia mostra o texto original.
    """
    if date_value is None:
        return None
    texto = str(date_value)
    achado = _ANO.search(texto)
    return int(achado.group(1)) if achado else None


def _sub_valor(people, pid, tag, sub_tag):
    """Primeiro valor do sub-registro `sub_tag` dentro do registro `tag`, ou None.

    `_data_de` e `_local_de` sao a mesma varredura com outra constante. Ficam como
    duas linhas de nome para que uma correcao numa nao deixe a outra para tras.
    """
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == sub_tag:
                    return str(sub.value)
    return None


def _data_de(people, pid, tag):
    return _sub_valor(people, pid, tag, "DATE")


def birth_date(people, pid):
    return _data_de(people, pid, "BIRT")


def death_date(people, pid):
    return _data_de(people, pid, "DEAT")


def _local_de(people, pid, tag):
    return _sub_valor(people, pid, tag, "PLAC")


def intervalo_de_geracao_mediano(arvore) -> float | None:
    """Mediana dos intervalos pai-filho datados da arvore, em anos.

    ## Por que esta funcao mora aqui, e nao na fachada de validacao

    Ela nasceu em `application.validacao` (feature `028`), onde so a fachada a usava.
    A feature `031` precisou do MESMO numero dentro do fluxo de DNA, para o cartao
    mostrar o veredito de viabilidade temporal. Duplicar aqui seria pior do que mover:
    duas implementacoes de `G` podem divergir em silencio, e o mesmo kit passaria a ter
    dois vereditos — um no cartao, outro na fachada.

    O lugar e este porque o dado e todo documental: datas de nascimento e vinculos de
    filiacao, que este modulo ja le com `parse_year` e `birth_date`.

    So entram intervalos com as duas datas e dentro de 12-70 anos (a mesma faixa de
    `IDADE_MINIMA_GENITOR`/`IDADE_MAXIMA_GENITOR`). Com menos de 3 amostras devolve
    `None`, e quem chama cai para o prior declarado de 25 anos — `None` aqui significa
    "a arvore nao tem amostra suficiente", nunca zero.
    """
    people, families = arvore[0], arvore[1]
    intervalos: list[int] = []

    for familia in families.values():
        pais = []
        for registro in familia.sub_records:
            if registro.tag in ("HUSB", "WIFE"):
                pid = ref_id(registro.value)
                if pid:
                    pais.append(pid)
        if not pais:
            continue
        for registro in familia.sub_records:
            if registro.tag != "CHIL":
                continue
            filho = ref_id(registro.value)
            ano_filho = parse_year(birth_date(people, filho))
            if ano_filho is None:
                continue
            for pai in pais:
                ano_pai = parse_year(birth_date(people, pai))
                if ano_pai is None:
                    continue
                intervalo = ano_filho - ano_pai
                if IDADE_MINIMA_GENITOR <= intervalo <= IDADE_MAXIMA_GENITOR:
                    intervalos.append(intervalo)

    if len(intervalos) < 3:
        return None
    return float(median(intervalos))

def birth_place(people, pid):
    """Local de nascimento, ou None. Espelha `birth_date` na forma."""
    return _sub_valor(people, pid, "BIRT", "PLAC")


__all__ = [
    "IDADE_MINIMA_GENITOR", "IDADE_MAXIMA_GENITOR",
    "parse_year", "birth_date", "death_date", "birth_place",
    "intervalo_de_geracao_mediano",
]
