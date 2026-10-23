"""O estado que nao muda entre kits, com os dois caches da analise.

`_ContextoDaAnalise` e um involucro congelado de entradas, nao um agregado de
dominio: nao guarda invariante e nao decide nada. `_dossie` opera o cache de
homonimos que vive nele, e existia como closure antes da OPP-20261023-ORQA.
"""
from __future__ import annotations

from dataclasses import dataclass
from .dependencias import Dependencias
from .documentary_relationship import homonym_dossier
from .endogamia import DNAAnalyzer


@dataclass(frozen=True, slots=True)
class _ContextoDaAnalise:
    """O que a analise de DNA consome igual em todo kit, mais os dois caches.

    A classe existe por uma razao medida: o laco por kit capturava dezoito nomes
    do escopo de `dna_analysis`. Extrair o passo por kit sem ela produziria uma
    assinatura de dezoito parametros, que e o mesmo acoplamento com outra roupa.

    Congelada de proposito: os campos nao sao reatribuidos. Os dois dicionarios
    de cache (`documental_por_pessoa` e `dossie_por_nome`) sao preenchidos na
    primeira consulta e reaproveitados pelos kits seguintes, e e isso que evita
    repetir a varredura de cerca de 35 mil nomes a cada cartao.

    Nao e agregado de dominio: nao guarda invariante, nao decide nada e nao
    reifica o casamento nem a busca. E o mesmo formato que `core.endogamia` ja
    usa nos seus value objects.
    """

    arvore: tuple
    root_id: str
    deps: Dependencias
    ged_index: dict
    surname_index: dict
    features: dict
    dominio: dict
    ano_base: int
    intervalo_de_geracao: int
    analisador: DNAAnalyzer
    candidatos_fixos: dict
    documental_por_pessoa: dict
    dossie_por_nome: dict

def _dossie(contexto: _ContextoDaAnalise, nome: str, candidatos) -> dict:
    """Dossie de homonimos, uma vez por nome (a varredura custa ~35k nomes).

    Era uma closure de `dna_analysis`. Virou funcao de modulo porque o cache
    passou a viver no contexto: uma closure sobre uma variavel local de uma
    funcao de 539 linhas nao tinha como ser exercitada sozinha.
    """
    if nome not in contexto.dossie_por_nome:
        contexto.dossie_por_nome[nome] = homonym_dossier(
            contexto.arvore, nome, similar_ids=candidatos)
    return contexto.dossie_por_nome[nome]
