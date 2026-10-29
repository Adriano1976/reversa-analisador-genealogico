"""Caso de uso da busca por nome: uma pergunta, duas fontes (feature 052).

## O que este caso de uso faz, e o que ele delega

Ele **orquestra e nao decide**: pede os candidatos a cada fonte, pede ao nucleo o
ranking, pede a ficha so dos que sobraram e devolve um resultado congelado. Nao
normaliza nome (a fonte e a autoridade), nao casa (o nucleo casa) e nao formata tela
(`reporting.resultado_da_busca` formata).

## Cada fonte com a SUA autoridade de normalizacao

O termo e normalizado **uma vez por fonte**, com o normalizador que a fonte declara.
E o que mantem a busca concordando com o dossie de homonimos na arvore e com o
`matching` no relatorio — e o que impede que unificar normalizadores mude resultado
de analise (`RN-06`, sessao de 2026-10-28).

## `resolve` existe porque 404 nao e resposta de secao

Quando a referencia de uma fonte nao resolve (arquivo inexistente ou de outro dono),
`SecaoDaBusca.resolve` vem `False` e a **rota** traduz isso no `404` com o literal de
inexistencia. A busca nao inventa uma resposta propria para o que a feature 051 ja
decidiu: recurso de outro dono e indistinguivel de inexistente.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from core.busca_de_nome import AcertoDeBusca, BuscadorDeNomes, TermoDeBusca

#: Teto por secao. O mesmo numero que o operador ja conhece do combobox (`RN-07`).
LIMITE_POR_SECAO = 50

#: Aviso da secao cuja fonte nao resolve. Nao chega a tela: vira `404` na rota.
AVISO_DE_REFERENCIA = "referência não resolvida"


@dataclass(frozen=True, slots=True)
class SecaoDaBusca:
    """Uma fonte, o termo normalizado dela e os acertos dela."""

    identidade: str
    rotulo: str
    termo: TermoDeBusca
    acertos: tuple[AcertoDeBusca, ...]
    total: int
    truncado: bool
    aviso: str | None = None
    resolve: bool = True

    @property
    def vazia(self) -> bool:
        return not self.acertos

    @property
    def falhou(self) -> bool:
        """A fonte existe mas nao pode ser lida (`RF-13`)."""
        return self.aviso is not None


@dataclass(frozen=True, slots=True)
class ResultadoDaBusca:
    """O que a tela recebe: o texto digitado e as secoes, rotuladas."""

    texto: str
    secoes: tuple[SecaoDaBusca, ...]

    @property
    def total(self) -> int:
        return sum(secao.total for secao in self.secoes)

    @property
    def encontrou(self) -> bool:
        return self.total > 0

    @property
    def nao_resolveu(self) -> bool:
        return any(not secao.resolve for secao in self.secoes)


class ServicoDeBusca:
    """A busca, com as fontes injetadas na construcao.

    Injetar as fontes em vez de cria-las aqui e o que permite testar com duas fontes
    falsas, e o que faz uma terceira fonte ser um adaptador novo em vez de uma
    alteracao neste arquivo.
    """

    def __init__(self, fontes, *, limite: int = LIMITE_POR_SECAO,
                 buscador: BuscadorDeNomes | None = None) -> None:
        self._fontes = tuple(fontes)
        self._limite = limite
        self._buscador = buscador if buscador is not None else BuscadorDeNomes()

    @property
    def fontes(self) -> tuple:
        return self._fontes

    def buscar(self, texto: str, *, dono: str,
               referencias: dict[str, str | None]) -> ResultadoDaBusca:
        """Executa a busca em todas as fontes. Nao escreve nada (`RN-01`)."""
        secoes: list[SecaoDaBusca] = []
        for fonte in self._fontes:
            termo = TermoDeBusca.de(texto or "", fonte.normalizar)
            referencia = referencias.get(fonte.identidade)
            candidatos, aviso = fonte.nomes(referencia, dono)

            if candidatos is None:
                secoes.append(
                    SecaoDaBusca(
                        identidade=fonte.identidade,
                        rotulo=fonte.rotulo,
                        termo=termo,
                        acertos=(),
                        total=0,
                        truncado=False,
                        aviso=AVISO_DE_REFERENCIA,
                        resolve=False,
                    )
                )
                continue

            acertos, total = self._buscador.acertos(candidatos, termo, self._limite)
            if acertos:
                fichas = fonte.fichas(
                    referencia, dono, tuple(a.identificador for a in acertos)
                )
                acertos = tuple(
                    replace(acerto, ficha=fichas[acerto.identificador])
                    if acerto.identificador in fichas
                    else acerto
                    for acerto in acertos
                )
            secoes.append(
                SecaoDaBusca(
                    identidade=fonte.identidade,
                    rotulo=fonte.rotulo,
                    termo=termo,
                    acertos=acertos,
                    total=total,
                    truncado=total > len(acertos),
                    aviso=aviso,
                )
            )
        return ResultadoDaBusca(texto=texto or "", secoes=tuple(secoes))


__all__: list[str] = [
    "AVISO_DE_REFERENCIA",
    "LIMITE_POR_SECAO",
    "ResultadoDaBusca",
    "SecaoDaBusca",
    "ServicoDeBusca",
]
