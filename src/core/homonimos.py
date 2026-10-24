"""Reconhecer o mesmo nome e montar o dossie de homonimos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele e o unico lugar que compara
nomes ignorando acento. O indice de nomes que ele mantem **nao e estado de modulo**: mora preso
ao grafo da arvore (feature 048), como os demais derivados do nucleo.
"""
from __future__ import annotations

import unicodedata

from .fichas_da_pessoa import person_summary
from .registro import get_name
from utils.text_cleaning import demojibake

# Por que o indice mora na arvore, e nao numa chave de conteudo
# Ate a feature 048 o indice era um cache de modulo chaveado por
# `(len(people), primeira chave, ultima chave)`. A chave era barata, mas colidia:
# duas arvores com o mesmo numero de pessoas e os mesmos xrefs extremos produziam
# a MESMA chave, e o dossie da segunda citava xrefs da primeira. Confirmado por
# execucao em 2026-10-10 — o dossie da segunda respondeu `exact_count: 1` citando
# `@I2@`, que nao existia nela, e a ficha degradou para "Sem Nome".
#
# Derivar a chave dos NOMES custaria a mesma varredura que construir o mapa, e
# derivar so dos xrefs colide em reexportacao que mantem os identificadores. A
# saida foi tirar a chave da jogada: o mapa e preso ao grafo da arvore, como
# `fichas_da_pessoa._indice_de_filhos` e os indices de matching da feature 047.
# Nao ha estado compartilhado, entao nao ha colisao possivel — e nenhum `id()`
# entra na decisao.

# Homonimos e o indice de nomes

def normalizar(nome: str) -> str:
    """Minusculas sem acento, para comparar nomes do GEDCOM e do CSV.

    Aplica antes a correcao de mojibake do projeto (`utils.text_cleaning`), a
    autoridade unica dessa limpeza. Sem isso, um GEDCOM sem `1 CHAR UTF-8` — que
    o ged4py le como latin-1 — faz "José" chegar como "JosÃ©" e o mesmo nome
    deixar de ser reconhecido como o mesmo: era o caso de um arquivo real
    (`Arvore_Unificada_Oficial_V1_2.ged`), onde a regra de homonimos ficaria cega.
    """
    sem_acento = unicodedata.normalize("NFKD", demojibake(str(nome or ""))) # type: ignore
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def _diferencas_de_fichas(fichas) -> list:
    """Campos em que as fichas JA MONTADAS divergem, o que o operador precisa olhar."""
    campos = [
        ("birth", "data de nascimento"),
        ("birth_place", "local de nascimento"),
        ("death", "data de falecimento"),
        ("parents", "pais"),
        ("children", "filhos"),
        ("sex", "sexo"),
    ]
    divergencias = []
    for campo, rotulo in campos:
        valores = {str(ficha.get(campo)) for ficha in fichas}
        if len(valores) > 1:
            divergencias.append({"campo": campo, "rotulo": rotulo})
    return divergencias


# Atributo preso ao grafo da arvore com o mapa de nomes. O nome comeca com `_` para nao colidir
# com atributo de `networkx.Graph`; o sufixo diz de que feature ele veio.
_ATRIBUTO_DO_INDICE = "_analisador_indice_de_nomes"


def _indice_por_nome(arvore) -> dict:
    """nome normalizado -> lista de ids, preso ao grafo da arvore.

    A varredura de 35 mil pessoas custa ~0,9 s. Sem este indice, o fluxo de DNA (71 nomes
    distintos no arquivo real) pagava isso 71 vezes. Com o mapa preso ao grafo, a segunda
    consulta na mesma arvore devolve o MESMO objeto; a arvore seguinte monta o dela, porque o
    grafo e outro. Nao ha chave: a vida do mapa e a vida da arvore.

    Arvore sem grafo (sonda, teste) constroi o mapa e nao guarda — nao ha onde prender.
    """
    grafo = arvore[2]
    if grafo is not None:
        guardado = getattr(grafo, _ATRIBUTO_DO_INDICE, None)
        if guardado is not None:
            return guardado

    mapa: dict = {}
    for pid, pessoa in arvore[0].items():
        mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)

    if grafo is not None:
        setattr(grafo, _ATRIBUTO_DO_INDICE, mapa)
    return mapa


def homonym_dossier(arvore, name_query: str, similar_ids=None) -> dict:
    """Todos os registros que podem ser a pessoa consultada, com ficha e ID.

    Nao escolhe: devolve o conjunto. `ambiguous` e True quando existe mais de um
    registro com o MESMO nome normalizado (homonimo direto) ou quando o chamador
    informa candidatos semelhantes (`similar_ids`). A comparacao ignora acento,
    entao "Jose Vicente de Souza" e "José Vicente de Souza" sao o mesmo nome.
    """
    alvo = normalizar(name_query)
    exatos = list(_indice_por_nome(arvore).get(alvo, []))
    parecidos = [pid for pid in (similar_ids or []) if pid not in exatos]
    fichas = [person_summary(arvore, pid) for pid in exatos]
    # As duas leituras saem da MESMA lista de fichas: `_diferencas` era chamado
    # uma vez para `differences` e outra dentro de `identical_data`, e cada
    # chamada remontava todas as fichas (medido: 6 para 2 homonimos).
    differences = _diferencas_de_fichas(fichas) if len(exatos) > 1 else []
    return {
        "query": name_query,
        "exact_count": len(exatos),
        "exact_matches": fichas,
        "similar_count": len(parecidos),
        "similar_matches": [person_summary(arvore, pid) for pid in parecidos[:5]],
        "ambiguous": len(exatos) > 1,
        "differences": differences,
        "identical_data": bool(len(exatos) > 1 and not differences), # type: ignore
    }

__all__ = ["normalizar", "homonym_dossier"]
