"""Regiões compartilhadas do CSV de matches (feature 056).

## O que este módulo decide

Uma **região compartilhada** é um conjunto de três ou mais matches cujos
segmentos, no mesmo cromossomo, têm interseção comum. O que ela afirma é
limitado, e é importante que seja: os matches compartilham aquela faixa **com o
kit do arquivo**; o CSV de matches não diz se eles compartilham entre si. Por
isso o produto não chama isto de triângulo fechado — chama de região, e deixa a
confirmação entre os matches para quando houver o arquivo de pares.

## Por que o piso de 10 cM é FILTRO aqui

No arquivo de pares, o fechamento dos pares sustenta o grupo e o piso podia ser
apenas uma marca. Aqui não há fechamento: o segmento pequeno é a maior fonte de
falso grupo. Medido no `DNA_Nordestino.csv` (606 kits):

- sem piso: 158 grupos e **553 kits** cobertos — quase todo mundo entra em algum;
- com piso de 10 cM: 32 grupos e **108 kits**, tamanho de parentesco.

## O que este módulo NÃO faz

- Não lê arquivo nem conhece GEDCOM: recebe segmentos já tipados.
- Não soma cM: guarda mínimo e máximo por segmento.
- Não decide parentesco: o desfecho é de `regiao_no_cartao`.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

#: Teto de regiões devolvidas por análise. Existe para arquivo anômalo, e o
#: truncamento é declarado na tela.
LIMITE_DE_REGIOES = 200

#: Piso de cM por segmento. É **filtro** (`RF-03` da feature 056): sem a
#: confirmação entre os matches, segmento pequeno é ruído.
PISO_DE_CM = 10.0

#: Limiar de região de acúmulo (heurística declarada): muitos kits numa faixa
#: curta, ou cM baixo demais para sustentar um ancestral comum recente.
ACUMULO_MINIMO_DE_KITS = 8
ACUMULO_EXTENSAO_MAXIMA = 2_000_000
ACUMULO_CM_MAXIMO = 12.0


@dataclass(frozen=True, slots=True)
class SegmentoDaRegiao:
    """Um segmento de um match, já tipado e limpo.

    `kit` é a identidade do membro. Quando o CSV não traz coluna de kit, quem
    monta usa o nome normalizado como identidade — dois matches sem kit não
    podem colapsar num membro só.
    """

    kit: str
    nome: str
    cromossomo: str
    inicio: int
    fim: int
    cm: float
    snps: int | None = None

    def __post_init__(self) -> None:
        if self.fim <= self.inicio:
            raise ValueError("segmento com fim menor ou igual ao início")


@dataclass(frozen=True, slots=True)
class RegiaoCompartilhada:
    """Um conjunto de matches sobre uma faixa comum."""

    cromossomo: str
    inicio: int
    fim: int
    kits: tuple[str, ...]
    membros: tuple[tuple[str, str], ...]
    segmentos: tuple[SegmentoDaRegiao, ...]
    cm_minimo: float
    cm_maximo: float

    @property
    def extensao(self) -> int:
        return self.fim - self.inicio

    @property
    def extensao_mb(self) -> float:
        return round(self.extensao / 1_000_000, 2)

    @property
    def acumulo(self) -> bool:
        return len(self.kits) >= ACUMULO_MINIMO_DE_KITS and (
            self.extensao < ACUMULO_EXTENSAO_MAXIMA
            or self.cm_maximo < ACUMULO_CM_MAXIMO
        )

    @property
    def snps_minimo(self) -> int | None:
        """Menor contagem de SNPs entre os segmentos, quando o arquivo a traz."""
        valores = [segmento.snps for segmento in self.segmentos if segmento.snps]
        return min(valores) if valores else None

    @property
    def snps_maximo(self) -> int | None:
        valores = [segmento.snps for segmento in self.segmentos if segmento.snps]
        return max(valores) if valores else None


@dataclass(frozen=True, slots=True)
class Agrupamento:
    regioes: tuple[RegiaoCompartilhada, ...]
    total: int
    truncado: bool


def _ordem_do_cromossomo(cromossomo: str):
    texto = str(cromossomo).strip().upper()
    return (0, int(texto), "") if texto.isdigit() else (1, 0, texto)


def _nome_mais_comum(nomes: list[str]) -> str:
    contagem = Counter(nome for nome in nomes if nome)
    if not contagem:
        return ""
    return min(contagem.items(), key=lambda item: (-item[1], item[0]))[0]


def _janelas(sub: list[SegmentoDaRegiao]) -> list[tuple[int, int, frozenset[str]]]:
    """Janelas onde três ou mais kits se cruzam, mescladas por conjunto."""
    eventos: list[tuple[int, int, int, str]] = []
    for indice, segmento in enumerate(sub):
        eventos.append((segmento.inicio, 1, indice, segmento.kit))
        eventos.append((segmento.fim, 0, indice, segmento.kit))
    eventos.sort(key=lambda evento: (evento[0], evento[1]))

    ativos: list[tuple[int, str]] = []
    brutas: list[tuple[int, int, frozenset[str]]] = []
    for posicao, tipo, indice, kit in eventos:
        ativos = [ativo for ativo in ativos if ativo[0] > posicao]
        if tipo == 0:
            continue
        ativos.append((sub[indice].fim, kit))
        kits = {ativo[1] for ativo in ativos}
        if len(kits) < 3:
            continue
        fim_comum = min(ativo[0] for ativo in ativos)
        if fim_comum > posicao:
            brutas.append((posicao, fim_comum, frozenset(kits)))

    por_conjunto: dict[frozenset[str], list[tuple[int, int]]] = defaultdict(list)
    for inicio, fim, kits in brutas:
        por_conjunto[kits].append((inicio, fim))

    janelas: list[tuple[int, int, frozenset[str]]] = []
    for kits, faixas in por_conjunto.items():
        faixas.sort()
        inicio_atual, fim_atual = faixas[0]
        for inicio, fim in faixas[1:]:
            if inicio <= fim_atual:
                fim_atual = max(fim_atual, fim)
                continue
            janelas.append((inicio_atual, fim_atual, kits))
            inicio_atual, fim_atual = inicio, fim
        janelas.append((inicio_atual, fim_atual, kits))
    return janelas


def _sobrepoe(primeira: tuple[int, int], segunda: tuple[int, int]) -> bool:
    return primeira[0] < segunda[1] and segunda[0] < primeira[1]


def _montar(cromossomo: str, kits: frozenset[str], janela: tuple[int, int],
            sub: list[SegmentoDaRegiao]) -> RegiaoCompartilhada | None:
    """Monta a região escolhendo, por kit, o segmento mais forte da janela.

    Um match pode ter mais de um segmento no mesmo cromossomo; escolher o de
    maior cM dentro da janela é determinístico e evita que a interseção entre
    dois segmentos distantes do mesmo match zere a região.
    """
    inicio_janela, fim_janela = janela
    candidatos = [
        segmento for segmento in sub
        if segmento.kit in kits
        and segmento.inicio < fim_janela and segmento.fim > inicio_janela
    ]
    escolhidos: dict[str, SegmentoDaRegiao] = {}
    for segmento in candidatos:
        atual = escolhidos.get(segmento.kit)
        if atual is None or (segmento.cm, -segmento.inicio) > (atual.cm, -atual.inicio):
            escolhidos[segmento.kit] = segmento
    if len(escolhidos) < 3:
        return None

    selecionados = [escolhidos[kit] for kit in sorted(escolhidos)]
    inicio = max(segmento.inicio for segmento in selecionados)
    fim = min(segmento.fim for segmento in selecionados)
    if fim <= inicio:
        return None

    nomes: dict[str, list[str]] = defaultdict(list)
    for segmento in selecionados:
        nomes[segmento.kit].append(segmento.nome)
    membros = tuple((kit, _nome_mais_comum(nomes[kit])) for kit in sorted(escolhidos))

    valores = [segmento.cm for segmento in selecionados]
    return RegiaoCompartilhada(
        cromossomo=cromossomo,
        inicio=inicio,
        fim=fim,
        kits=tuple(sorted(escolhidos)),
        membros=membros,
        segmentos=tuple(selecionados),
        cm_minimo=min(valores),
        cm_maximo=max(valores),
    )


def agrupar(segmentos, limite: int = LIMITE_DE_REGIOES) -> Agrupamento:
    """Agrupa os segmentos em regiões maximais, em ordem determinística."""
    utilizaveis = [
        segmento for segmento in segmentos
        if segmento.cm >= PISO_DE_CM
        and str(segmento.cromossomo).strip()
    ]
    por_cromossomo: dict[str, list[SegmentoDaRegiao]] = defaultdict(list)
    for segmento in utilizaveis:
        por_cromossomo[str(segmento.cromossomo).strip().upper()].append(segmento)

    encontradas: list[RegiaoCompartilhada] = []
    for cromossomo, sub in por_cromossomo.items():
        janelas = _janelas(sub)
        janelas.sort(key=lambda item: (-len(item[2]), item[0], item[1]))
        maximais: list[tuple[int, int, frozenset[str]]] = []
        for candidato in janelas:
            contido = any(
                candidato[2] < outro[2] and _sobrepoe(candidato[:2], outro[:2])
                for outro in maximais
            )
            if not contido:
                maximais.append(candidato)

        for inicio, fim, kits in maximais:
            regiao = _montar(cromossomo, kits, (inicio, fim), sub)
            if regiao is not None:
                encontradas.append(regiao)

    encontradas.sort(key=lambda regiao: (
        _ordem_do_cromossomo(regiao.cromossomo), regiao.inicio, regiao.kits,
    ))
    total = len(encontradas)
    visiveis = tuple(encontradas[:limite]) if limite > 0 else tuple(encontradas)
    return Agrupamento(regioes=visiveis, total=total, truncado=total > len(visiveis))


__all__ = [
    "ACUMULO_CM_MAXIMO",
    "ACUMULO_EXTENSAO_MAXIMA",
    "ACUMULO_MINIMO_DE_KITS",
    "Agrupamento",
    "LIMITE_DE_REGIOES",
    "PISO_DE_CM",
    "RegiaoCompartilhada",
    "SegmentoDaRegiao",
    "agrupar",
]
