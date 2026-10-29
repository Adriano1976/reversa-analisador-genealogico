"""View-model do resultado da busca (feature 052).

Funcao pura, sem Flask e sem HTML: recebe o resultado do caso de uso e devolve os
dicionarios que o template le. O template nao decide formato, e este modulo nao
decide regra — a separacao e a mesma de `reporting/lista_de_arquivos.py`.

## O que o card da arvore mostra, e o que ele NAO inventa

Nome, nascimento, falecimento, pais, filhos e identificador (`RF-05`). Campo que a
ficha nao tem vira texto vazio, e nao "desconhecido": inventar valor num dado
genealogico e pior do que deixar a celula em branco.

## O card do relatorio e outro card, de proposito

Ele mostra nome, kit, cM e o rotulo do arquivo de origem (`RF-06`). Sao duas perguntas
diferentes e o painel as mantem separadas (`RN-05`) — por isso o card nao tenta parecer
com o da arvore.
"""
from __future__ import annotations

from application.busca_de_nome import ResultadoDaBusca, SecaoDaBusca
from core.busca_de_nome import AcertoDeBusca
from reporting.lista_de_arquivos import rotulo_de_referencia
from utils.number_format import formatar_cm


def _texto(valor: object) -> str:
    """Celula de exibicao: `None` vira vazio, e nunca a palavra 'desconhecido'."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() in ("none", "nan", "<na>") else texto


def _ficha_para_tela(acerto: AcertoDeBusca) -> dict:
    """O card da arvore: a ficha da pessoa, do jeito que o operador le."""
    ficha = acerto.ficha or {}
    # A ficha chega como `Mapping[str, object]` porque vem de `person_summary`, que
    # devolve um dicionario heterogeneo. Cada campo e estreitado AQUI, e nao com `Any`:
    # o que nao for lista vira lista vazia, e o que nao for numero vira texto vazio.
    parent_names = ficha.get("parent_names")
    nomes_dos_pais = (
        tuple(_texto(nome) for nome in parent_names if _texto(nome))
        if isinstance(parent_names, (list, tuple))
        else ()
    )
    children = ficha.get("children")
    quantidade_de_filhos = len(children) if isinstance(children, (list, tuple)) else 0
    return {
        "tipo": "arvore",
        "identificador": _texto(ficha.get("id")) or acerto.identificador,
        "nome": _texto(acerto.nome),
        "nascimento": _texto(ficha.get("birth")),
        "local_nascimento": _texto(ficha.get("birth_place")),
        "falecimento": _texto(ficha.get("death")),
        "sexo": _texto(ficha.get("sex")),
        "pais": ", ".join(nomes_dos_pais),
        "filhos": quantidade_de_filhos,
        "kit": "",
        "centimorgans": "",
        "arquivo": "",
    }


def _linha_para_tela(acerto: AcertoDeBusca) -> dict:
    """O card do relatorio: a linha do match, com kit e cM."""
    dados = acerto.dados or {}
    cm = dados.get("centimorgans")
    centimorgans = formatar_cm(float(cm)) if isinstance(cm, (int, float)) else ""
    arquivo = dados.get("arquivo")
    return {
        "tipo": "relatorio",
        "identificador": _texto(dados.get("kit")) or acerto.identificador,
        "nome": _texto(acerto.nome),
        "nascimento": "",
        "local_nascimento": "",
        "falecimento": "",
        "sexo": "",
        "pais": "",
        "filhos": 0,
        "kit": _texto(dados.get("kit")),
        "centimorgans": centimorgans,
        "arquivo": rotulo_de_referencia(arquivo) if isinstance(arquivo, str) else "",
    }


def _secao_para_tela(secao: SecaoDaBusca, limite: int) -> dict:
    montar = _ficha_para_tela if secao.identidade == "arvore" else _linha_para_tela
    return {
        "identidade": secao.identidade,
        "rotulo": secao.rotulo,
        "total": secao.total,
        "truncado": secao.truncado,
        "limite": limite,
        "vazia": secao.vazia,
        "aviso": secao.aviso if secao.resolve else None,
        "acertos": [montar(acerto) for acerto in secao.acertos],
    }


def resultado_para_tela(resultado: ResultadoDaBusca) -> dict:
    """O dicionario que o partial `_busca.html` consome."""
    limite: int = max(
        (len(secao.acertos) for secao in resultado.secoes if secao.truncado),
        default=0,
    )
    return {
        "texto": resultado.texto,
        "total": resultado.total,
        "encontrou": resultado.encontrou,
        "secoes": [
            _secao_para_tela(secao, limite) for secao in resultado.secoes
        ],
    }


__all__: list[str] = ["resultado_para_tela"]
