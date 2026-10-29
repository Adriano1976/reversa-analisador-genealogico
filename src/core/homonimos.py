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

#: Atributo da SEGUNDA visao, a de tokens (feature 052). Nome proprio, e nao uma
#: chave de conteudo: as duas visoes nascem juntas e morrem com o grafo.
_ATRIBUTO_DO_INDICE_DE_TOKENS = "_analisador_indice_de_tokens"


def _varrer_nomes(arvore) -> tuple[dict, dict]:
    """As DUAS visoes do indice, presas ao grafo da arvore, numa varredura so.

    A visao por nome inteiro responde "esta pessoa existe?"; a visao por token
    responde "quem tem Silva no nome?", que e a pergunta da busca (feature 052).
    As duas nascem no mesmo laco porque o nome ja esta normalizado e os tokens sao
    um `split` — separar custaria uma segunda varredura de 35 mil pessoas.

    Nenhuma das duas tem chave: a vida do mapa e a vida do grafo, e e o que a
    feature 048 fixou ao enterrar a chave `(len, primeiro xref, ultimo xref)`.
    """
    grafo = arvore[2]
    if grafo is not None:
        guardado_nome = getattr(grafo, _ATRIBUTO_DO_INDICE, None)
        guardado_token = getattr(grafo, _ATRIBUTO_DO_INDICE_DE_TOKENS, None)
        # `isinstance`, e nao `is not None`: o atributo e escrito por `setattr` no grafo,
        # e um objeto estranho pendurado ali nao pode virar retorno desta funcao. O
        # estreitamento tambem e o que diz ao verificador que o que sai daqui e `dict`.
        if isinstance(guardado_nome, dict) and isinstance(guardado_token, dict):
            return guardado_nome, guardado_token

    mapa: dict = {}
    tokens: dict = {}
    for pid, pessoa in arvore[0].items():
        chave: str = normalizar(get_name(pessoa))
        mapa.setdefault(chave, []).append(pid)
        for token in dict.fromkeys(chave.split()):
            tokens.setdefault(token, []).append(pid)

    if grafo is not None:
        setattr(grafo, _ATRIBUTO_DO_INDICE, mapa)
        setattr(grafo, _ATRIBUTO_DO_INDICE_DE_TOKENS, tokens)
    return mapa, tokens


def indice_por_nome(arvore) -> dict:
    """Visao PUBLICA do mapa nome normalizado -> ids (feature 052).

    Existe porque a busca precisa das duas visoes e nao pode depender de nome privado:
    `_indice_por_nome` continua sendo o acessor interno do dossie de homonimos.
    """
    return _indice_por_nome(arvore)


def indice_por_token(arvore) -> dict:
    """token normalizado -> lista de ids, preso ao mesmo grafo (feature 052).

    Segunda visao do indice, construida na mesma varredura da visao por nome. Existe
    porque o mapa por nome inteiro nao responde "quem tem Silva no nome" — e essa e a
    pergunta que a busca faz, com o mesmo casamento por trecho que o combobox ja pratica.
    """
    return _varrer_nomes(arvore)[1]


def _indice_por_nome(arvore) -> dict:
    """nome normalizado -> lista de ids, preso ao grafo da arvore.

    A varredura de 35 mil pessoas custa ~0,9 s. Sem este indice, o fluxo de DNA (71 nomes
    distintos no arquivo real) pagava isso 71 vezes. Com o mapa preso ao grafo, a segunda
    consulta na mesma arvore devolve o MESMO objeto; a arvore seguinte monta o dela, porque o
    grafo e outro. Nao ha chave: a vida do mapa e a vida da arvore.

    Arvore sem grafo (sonda, teste) constroi o mapa e nao guarda — nao ha onde prender.
    """
    return _varrer_nomes(arvore)[0]


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

__all__: list[str] = ["normalizar", "homonym_dossier", "indice_por_token"]
