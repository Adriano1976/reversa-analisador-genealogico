"""Busca de nomes na arvore e no relatorio de matches. Modulo PURO.

## Por que ele existe, e o que ele NAO faz

A tela sabia preencher um nome (o combobox da feature 037), e nao sabia responder
"quem e esta pessoa". Este modulo e a resposta: recebe um termo e uma sequencia de
`NomeParaBuscar` ja preparados pela fonte, e devolve os acertos ORDENADOS.

Ele nao sabe de onde os nomes vem (arvore aberta, relatorio de matches, um banco
futuro), nao normaliza nome de fonte nenhuma e nao conhece HTTP, disco nem
`pandas`. Quem normaliza e a FONTE, com a autoridade que ela ja usa — e e o que
mantem a busca concordando com o dossie de homonimos na arvore e com o `matching`
no relatorio (`RN-06`).

## O casamento: filtro largo, ordem que separa o ruido

`RN-09` decidiu que o casamento e por TRECHO em qualquer posicao do token — o
mesmo comportamento que o combobox ja pratica no cliente —, e que o prefixo pontua
ACIMA do meio de token. As estrategias rodam em ordem declarada e a primeira que
casa vence; a pontuacao so serve para a ordenacao, nunca para descartar.

A ordem final e TOTAL: `(-pontuacao, nome_normalizado, identificador)`. Sem isso,
dois acertos empatados herdariam a iteracao de um `set` e a lista mudaria entre
duas buscas iguais — a mesma classe de defeito que a `L-25` registra em
`common_ancestors` e que o `matching` fechou em 2026-10-05.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Protocol, Sequence

#: Tetos de pontuacao. Sao constantes NOMEADAS porque a ordem entre elas e a
#: politica de produto: o prefixo precisa vencer o meio de token, e o nome inteiro
#: precisa vencer os dois. Trocar um numero aqui troca a ordem na tela.
PONTUACAO_EXATA = 1.0
PONTUACAO_COMPLETA = 0.7
PONTUACAO_PREFIXO = 0.5
PONTUACAO_TRECHO = 0.3

#: Escopos do termo, derivados da contagem de tokens. Nunca escolhidos na tela.
ESCOPO_DE_TOKEN = "token"
ESCOPO_DE_NOME = "nome"


@dataclass(frozen=True, slots=True)
class TermoDeBusca:
    """O texto do operador, preservado, mais as formas derivadas dele.

    `texto` e o que foi digitado, sem alteracao: e ele que volta para o campo
    depois da busca (`RF-09`). `normalizado` e `tokens` saem da autoridade da
    FONTE — por isso o termo e construido com o normalizador dela, e nao com um
    normalizador global.
    """

    texto: str
    normalizado: str
    tokens: tuple[str, ...]

    @classmethod
    def de(cls, texto: str, normalizar: Callable[[str], str]) -> "TermoDeBusca":
        """Constroi o termo pela autoridade de normalizacao da fonte."""
        cru = texto or ""
        forma = normalizar(cru)
        tokens = tuple(t for t in dict.fromkeys(forma.split()) if t)
        return cls(texto=cru, normalizado=forma, tokens=tokens)

    @property
    def escopo(self) -> str:
        """`token` para um unico token; `nome` para dois ou mais (`RN-02`)."""
        return ESCOPO_DE_TOKEN if len(self.tokens) == 1 else ESCOPO_DE_NOME

    @property
    def vazio(self) -> bool:
        return not self.tokens


@dataclass(frozen=True, slots=True)
class NomeParaBuscar:
    """Um candidato, ja preparado pela fonte.

    `normalizado` e `tokens` vem prontos porque a fonte os tem de graca: a arvore
    os tira do indice que ja construiu, e o relatorio os tira de `norm_name`. Fazer
    o nucleo normalizar de novo custaria uma varredura inteira por busca.
    """

    identificador: str
    nome: str
    normalizado: str
    tokens: tuple[str, ...]
    origem: str
    dados: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AcertoDeBusca:
    """Um resultado. `pontuacao` e `nome_normalizado` existem para a ORDEM."""

    identificador: str
    nome: str
    normalizado: str
    pontuacao: float
    origem: str
    dados: Mapping[str, object] = field(default_factory=dict)
    ficha: Mapping[str, object] | None = None


class EstrategiaDeCasamento(Protocol):
    """Um criterio de casamento. Substituivel; a ORDEM entre eles e politica."""

    rotulo: str

    def pontuar(self, nome: str, tokens: Sequence[str],
                termo: TermoDeBusca) -> float | None:
        """Pontuacao, ou `None` quando o candidato nao casa por este criterio."""
        ...


class CasamentoExato:
    """O nome inteiro, normalizado, e igual ao termo inteiro."""

    rotulo = "exato"

    def pontuar(self, nome: str, tokens: Sequence[str],
                termo: TermoDeBusca) -> float | None:
        return PONTUACAO_EXATA if nome == termo.normalizado else None


class CasamentoCompleto:
    """Todos os tokens do termo aparecem como PARTe inteira do nome."""

    rotulo = "completo"

    def pontuar(self, nome: str, tokens: Sequence[str],
                termo: TermoDeBusca) -> float | None:
        conjunto = set(tokens)
        if termo.tokens and all(t in conjunto for t in termo.tokens):
            return PONTUACAO_COMPLETA
        return None


class CasamentoPorPrefixo:
    """Cada token do termo INICIA algum token do nome (`RN-09`)."""

    rotulo = "prefixo"

    def pontuar(self, nome: str, tokens: Sequence[str],
                termo: TermoDeBusca) -> float | None:
        if not termo.tokens:
            return None
        if all(any(c.startswith(t) for c in tokens) for t in termo.tokens):
            return PONTUACAO_PREFIXO
        return None


class CasamentoPorTrecho:
    """Cada token do termo aparece em QUALQUER posicao de algum token do nome."""

    rotulo = "trecho"

    def pontuar(self, nome: str, tokens: Sequence[str],
                termo: TermoDeBusca) -> float | None:
        if not termo.tokens:
            return None
        if all(any(t in c for c in tokens) for t in termo.tokens):
            return PONTUACAO_TRECHO
        return None


#: A ordem declarada: do criterio mais forte para o mais fraco (`D-05`).
ESTRATEGIAS_PADRAO: tuple[EstrategiaDeCasamento, ...] = (
    CasamentoExato(),
    CasamentoCompleto(),
    CasamentoPorPrefixo(),
    CasamentoPorTrecho(),
)


class BuscadorDeNomes:
    """Aplica as estrategias e devolve os acertos em ordem total.

    A ordem dos criterios entra na CONSTRUCAO, e nao no codigo: e o que permite
    testar "prefixo antes de trecho" sem tocar na implementacao, e o que deixa a
    politica num lugar so.
    """

    def __init__(self, estrategias: Sequence[EstrategiaDeCasamento] | None = None) -> None:
        self._estrategias: tuple[EstrategiaDeCasamento, ...] = tuple(
            ESTRATEGIAS_PADRAO if estrategias is None else estrategias
        )

    @property
    def estrategias(self) -> tuple[EstrategiaDeCasamento, ...]:
        return self._estrategias

    def _pontuacao(self, candidato: NomeParaBuscar,
                   termo: TermoDeBusca) -> float | None:
        for estrategia in self._estrategias:
            valor = estrategia.pontuar(candidato.normalizado, candidato.tokens, termo)
            if valor is not None:
                return valor
        return None

    def acertos(self, candidatos: Sequence[NomeParaBuscar],
                termo: TermoDeBusca,
                limite: int | None = None) -> tuple[tuple[AcertoDeBusca, ...], int]:
        """`(acertos, total)` — a lista pode vir truncada; o TOTAL nunca mente.

        `RN-07`: o limite existe para a tela, e o total encontrado e declarado
        mesmo quando a lista e cortada.
        """
        achados: list[AcertoDeBusca] = []
        if not termo.vazio:
            for candidato in candidatos:
                valor = self._pontuacao(candidato, termo)
                if valor is None:
                    continue
                achados.append(
                    AcertoDeBusca(
                        identificador=candidato.identificador,
                        nome=candidato.nome,
                        normalizado=candidato.normalizado,
                        pontuacao=valor,
                        origem=candidato.origem,
                        dados=candidato.dados,
                    )
                )
        achados.sort(key=lambda a: (-a.pontuacao, a.normalizado, a.identificador))
        total: int = len(achados)
        if limite is not None:
            achados = achados[:limite]
        return tuple(achados), total


__all__: list[str] = [
    "AcertoDeBusca",
    "BuscadorDeNomes",
    "CasamentoCompleto",
    "CasamentoExato",
    "CasamentoPorPrefixo",
    "CasamentoPorTrecho",
    "ESCOPO_DE_NOME",
    "ESCOPO_DE_TOKEN",
    "ESTRATEGIAS_PADRAO",
    "EstrategiaDeCasamento",
    "NomeParaBuscar",
    "TermoDeBusca",
]
