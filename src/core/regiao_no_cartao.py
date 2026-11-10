"""Desfecho documental de uma região compartilhada (feature 056).

A região diz **quem** compartilha o quê; este módulo diz **o que a árvore tem a
respeito**. Sem rodar um segundo matching: cada membro é procurado nos cartões
que a análise de DNA já produziu (chave primária: kit; alternativa: nome
normalizado), e o desfecho sai do ancestral comum que o cartão já aponta.

## O que os desfechos significam, e o que eles NÃO significam

- **convergente**: todos os membros com caminho apontam o mesmo ancestral comum.
  Corrobora o ramo; não prova o parentesco.
- **dividido**: membros com caminho apontam ancestrais distintos. Um segmento não
  vem de dois ancestrais: ou um caminho está errado, ou o segmento é falso positivo.
- **parcial**: parte dos membros tem caminho, parte não.
- **sem ancestral documentado**: nenhum membro tem caminho. É a saída mais útil —
  a evidência aponta um ancestral que a árvore não tem.

Nenhum deles altera o parentesco documental.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.regioes import RegiaoCompartilhada
from utils.name_keys import norm_name

DESFECHO_CONVERGENTE = "convergente"
DESFECHO_DIVIDIDO = "dividido"
DESFECHO_PARCIAL = "parcial"
DESFECHO_SEM_ANCESTRAL = "sem_ancestral"

ROTULOS = {
    DESFECHO_CONVERGENTE: "Convergente",
    DESFECHO_DIVIDIDO: "Dividido",
    DESFECHO_PARCIAL: "Parcial",
    DESFECHO_SEM_ANCESTRAL: "Sem ancestral documentado",
}


@dataclass(frozen=True, slots=True)
class MembroDaRegiao:
    """Um match da região, com o que a árvore sabe dele (ou não)."""

    kit: str
    nome: str
    tem_cartao: bool
    ancestral_id: str | None = None
    ancestral_nome: str | None = None
    cm: float | None = None


@dataclass(frozen=True, slots=True)
class RegiaoClassificada:
    """A região mais o desfecho documental, com o motivo escrito."""

    regiao: RegiaoCompartilhada
    membros: tuple[MembroDaRegiao, ...]
    desfecho: str | None
    motivo: str

    @property
    def rotulo(self) -> str:
        if self.desfecho is None:
            return "Sem desfecho"
        return ROTULOS.get(self.desfecho, self.desfecho)


def _ancestral(cartao: dict) -> tuple[str | None, str | None]:
    documental = cartao.get("documentary") or {}
    if documental.get("status") not in ("found", "ambiguous"):
        return None, None
    comum = documental.get("common_ancestor") or {}
    identificador = comum.get("id")
    if not identificador:
        return None, None
    return identificador, comum.get("name")


def _indices(cartoes) -> tuple[dict[str, dict], dict[str, dict]]:
    por_kit: dict[str, dict] = {}
    por_nome: dict[str, dict] = {}
    for cartao in cartoes or ():
        if not isinstance(cartao, dict):
            continue
        kit = str(cartao.get("kit") or "").strip().upper()
        if kit:
            por_kit.setdefault(kit, cartao)
        for chave in (cartao.get("match_name"), cartao.get("csv_name")):
            if not chave:
                continue
            normalizado = norm_name(str(chave))
            if normalizado:
                por_nome.setdefault(normalizado, cartao)
    return por_kit, por_nome


def _nomes_dos_ancestrais(membros: list[MembroDaRegiao]) -> str:
    """Nomes distintos dos ancestrais, em ordem, para a frase do motivo."""
    nomes: list[str] = []
    for membro in membros:
        nome = membro.ancestral_nome or membro.ancestral_id
        if nome:
            nomes.append(nome)
    return ", ".join(sorted(set(nomes)))


def _motivo(desfecho: str, membros: tuple[MembroDaRegiao, ...]) -> str:
    com_caminho = [membro for membro in membros if membro.ancestral_id]
    if desfecho == DESFECHO_SEM_ANCESTRAL:
        return ("Nenhum membro da região tem caminho documental até um ancestral comum. "
                "A evidência genética aponta para um ancestral que a árvore não tem.")
    if desfecho == DESFECHO_CONVERGENTE:
        nomes = _nomes_dos_ancestrais(com_caminho)
        return (f"Os {len(com_caminho)} membros com caminho apontam para o mesmo ancestral "
                f"comum ({nomes}). Isso corrobora o ramo; não prova o parentesco.")
    if desfecho == DESFECHO_DIVIDIDO:
        nomes = _nomes_dos_ancestrais(com_caminho)
        return ("Os membros com caminho apontam ancestrais distintos "
                f"({nomes}). Um segmento não vem de dois ancestrais: "
                "ou um caminho está errado, ou o segmento é falso positivo.")
    return (f"{len(com_caminho)} de {len(membros)} membros têm caminho documental; os demais "
            "não. A região fica parcial até que a identidade dos que faltam seja resolvida.")


def classificar(regiao: RegiaoCompartilhada, cartoes) -> RegiaoClassificada:
    """Classifica uma região contra os cartões já produzidos.

    `cartoes` são os dicionários de `resultados` da análise de DNA. Sem cartões
    — o modo sem árvore, que a feature 056 não usa —, o desfecho é `None`.
    """
    por_kit, por_nome = _indices(cartoes)

    membros = []
    for kit, nome in regiao.membros:
        cartao = por_kit.get(kit.strip().upper()) or por_nome.get(norm_name(nome))
        ancestral_id, ancestral_nome = _ancestral(cartao) if cartao else (None, None)
        membros.append(MembroDaRegiao(
            kit=kit,
            nome=nome,
            tem_cartao=cartao is not None,
            ancestral_id=ancestral_id,
            ancestral_nome=ancestral_nome,
            cm=(cartao or {}).get("cm"),
        ))
    membros_tupla = tuple(membros)

    if cartoes is None:
        return RegiaoClassificada(
            regiao=regiao,
            membros=membros_tupla,
            desfecho=None,
            motivo="O desfecho documental depende da árvore carregada e da análise de DNA.",
        )

    com_caminho = [membro for membro in membros_tupla if membro.ancestral_id]
    if not com_caminho:
        desfecho = DESFECHO_SEM_ANCESTRAL
    elif len(com_caminho) < len(membros_tupla):
        desfecho = DESFECHO_PARCIAL
    elif len({membro.ancestral_id for membro in com_caminho}) == 1:
        desfecho = DESFECHO_CONVERGENTE
    else:
        desfecho = DESFECHO_DIVIDIDO

    return RegiaoClassificada(
        regiao=regiao,
        membros=membros_tupla,
        desfecho=desfecho,
        motivo=_motivo(desfecho, membros_tupla),
    )


__all__ = [
    "DESFECHO_CONVERGENTE",
    "DESFECHO_DIVIDIDO",
    "DESFECHO_PARCIAL",
    "DESFECHO_SEM_ANCESTRAL",
    "MembroDaRegiao",
    "ROTULOS",
    "RegiaoClassificada",
    "classificar",
]
