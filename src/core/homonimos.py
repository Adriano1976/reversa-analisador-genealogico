"""Reconhecer o mesmo nome e montar o dossie de homonimos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele e o dono do unico estado
de modulo do nucleo, o CACHE_DE_NOMES, e o unico lugar que compara nomes ignorando acento.
"""
from __future__ import annotations

import unicodedata

from .fichas_da_pessoa import person_summary
from .registro import get_name
from utils.text_cleaning import demojibake

# ---------------------------------------------------------------------------
# Por que a chave do indice e derivada do CONTEUDO, e nao da identidade
# ---------------------------------------------------------------------------
# Medido em 2026-10-06, enquanto o estado global existia:
# `load_gedcom_and_build_graph` MUTAVA `gedcom_state.people` in place
# (`clear()` + `update()`), entao o `id()` do dicionario era o MESMO em todo o
# processo. Um cache chaveado por identidade nunca invalidaria — e a invalidacao
# e justamente o que `test_6d` cobra.
#
# A tentacao, agora que `T023` removeu o estado e `carregar_arvore` devolve
# dicionarios NOVOS a cada parse, e voltar a usar `id()`. NAO volte: `id()` e
# reciclado. O dicionario da arvore anterior deixa de ser referenciado assim que
# o parse seguinte devolve o novo, o CPython pode reusar o mesmo endereco, e a
# chave coincidiria com a de um GEDCOM DIFERENTE — o cache devolveria o mapa do
# anterior. O defeito apareceria so sob carga, e nao em teste isolado.
#
# A chave e o tamanho mais a primeira e a ultima chave de `people`: barato,
# derivado do valor, e muda quando a arvore muda. A explicacao completa esta em
# `_chave_de`.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Homonimos e o indice de nomes
# ---------------------------------------------------------------------------

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


#: O par (chave, mapa) num valor so. A troca e uma atribuicao de nome, que em
#: CPython e atomica: quem le ve o par inteiro ou o par anterior, nunca a chave de
#: um GEDCOM junto do mapa de outro. Enquanto eram dois campos de um dicionario, a
#: publicacao acontecia em dois tempos e o `return` relia o global, de modo que
#: duas requisicoes simultaneas podiam devolver o indice uma da outra. Medido em
#: 2026-10-24 com duas arvores e duas threads: ver `_reversa_refactor/busca-caminho/`.
_INDICE_DE_NOMES: tuple[tuple, dict] = ((), {})


def _chave_de(people) -> tuple:
    """Chave de invalidacao do indice, derivada do CONTEUDO recebido.

    O indice e um cache de modulo: a chave tem de mudar quando outro GEDCOM chega,
    senao o fluxo seguinte leria os ids do anterior. A IDENTIDADE do dicionario nao
    serve: o parse mutava `people` in place e o `id()` era o mesmo durante todo o
    processo, entao o cache nunca invalidaria — foi o defeito medido em 2026-10-06
    e cobrado por `test_6d`.

    A chave usa contagem, primeira e ultima chave — barato e suficiente para
    distinguir dois GEDCOMs carregados. Ela continua necessaria depois do `T023`,
    que removeu o estado global e a mutacao in place: o parse agora devolve
    dicionarios NOVOS, mas este cache e de modulo, e a chave continua sendo o que
    garante que ele fale do GEDCOM da vez.
    """
    if not people:
        return (0, None, None)
    chaves = sorted(people)
    return (len(people), chaves[0], chaves[-1])


def _indice_por_nome(arvore) -> dict:
    """nome normalizado -> lista de ids, reconstruido a cada GEDCOM carregado.

    A varredura de 35 mil pessoas custa ~0,9 s. Sem este indice, o fluxo de DNA
    (71 nomes distintos no arquivo real) pagava isso 71 vezes. A invalidacao usa o
    CONTEUDO do dicionario de pessoas recebido, e nao um contador
    (`gedcom_state.versao`, removido pela feature 005): dois GEDCOMs diferentes
    podem ter a mesma contagem, e um contador exigiria estado. O detalhe da chave
    esta em `_chave_de`.
    """
    global _INDICE_DE_NOMES

    people = arvore[0]
    chave = _chave_de(people)
    publicado = _INDICE_DE_NOMES
    if publicado[0] != chave:
        mapa: dict = {}
        for pid, pessoa in people.items():
            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)
        publicado = (chave, mapa)
        _INDICE_DE_NOMES = publicado
    return publicado[1]


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
