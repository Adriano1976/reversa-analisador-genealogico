"""Regras de endogamia do DNA (filtro de ruído, evidência e colapso de pedigree).

Responsabilidade unica: aplicar as tres regras de negocio que separam o sinal
genetico do ruido de populacoes isoladas, e diagnosticar endogamia estrutural no
grafo do GEDCOM. Nao le arquivo, nao formata tela e nao conhece Flask — recebe
segmentos e o grafo, devolve valores.

## Onde ele se encaixa (e por que nao se chama `dna_analysis`)

`core.dna_analysis` e o **orquestrador**: le o CSV pela borda, faz o matching,
monta o parentesco documental, o confronto e o cartao. Este modulo e a
**politica** que o orquestrador consulta: filtro de 10 cM, recálculo do total,
maior bloco e caminhos no grafo. A dependencia e de mao unica
(`dna_analysis` -> `endogamia`), e o nome diz a verificacao — como
`janela_de_vida`, `profundidade_do_caminho` e `identidade_do_match`.

## As tres regras (e por que elas existem)

1. **Filtro rigido de segmentos** (`CM_MINIMO_SEGMENTO = 10.0`). Segmentos
   abaixo de 10 cM aparecem com frequencia entre pessoas sem relacao genealogica
   recente; em populacao isolada eles sao maioria. O segmento e descartado e o
   total e **recalculado** apenas sobre o que sobreviveu (`math.fsum`, para nao
   herdar a cauda de ponto flutuante da soma incremental).
2. **Maior bloco** (`CM_MINIMO_MAIOR_BLOCO = 15.0`). Um total alto pode ser a
   soma de muitos blocos minusculos. Abaixo de 15 cM no maior bloco, o
   diagnostico diz `evidência fraca` e `parentesco distante inflado`.
3. **Endogamia estrutural**. O grafo do GEDCOM e convertido para nao-direcionado
   (`to_undirected`) para que a travessia possa subir por um ramo e descer pelo
   outro — e assim atravessar primos colaterais. `nx.all_shortest_paths` devolve
   todos os caminhos mais curtos entre a raiz e o match; **mais de um** caminho
   mais curto e a assinatura de colapso de pedigree: o diagnostico aponta
   `Endogamia estrutural confirmada na árvore`.

## O que este modulo NAO faz

- Nao altera `result["cm"]` nem o total bruto de `core.genetic_evidence`: a
  paridade contra o oraculo congelado prende aquele valor, e a mitigacao viaja em
  campo proprio (`result["endogamia"]`). O operador ve os dois numeros lado a
  lado — o que o arquivo declara e o que sobra depois do filtro.
- Nao escolhe o match por nome no fluxo principal. `casar_nome` implementa a
  resolucao difusa pedida (`difflib.get_close_matches`, cutoff 0.75, barras do
  GEDCOM limpas) e e usada por `analisar`; `core.matching` continua intocado
  porque as decisoes dele sao contrato de caracterizacao (`tests/`).
- Nao importa `parsers/` nem `reporting/` (`RF-09`). Quem le o CSV e a borda.

## Grafo direcionado x nao-direcionado

A travessia colateral exige um grafo nao-direcionado (subir por um ramo e descer
pelo outro). A conversao e `to_undirected(as_view=True)`: o `as_view` devolve uma
VIEW, e nao uma copia O(V+E) — o fluxo real roda isso por cartao, e o parser ja
entrega `nx.Graph`. A chamada e a mesma para grafo direcionado e nao-direcionado,
entao um `DiGraph` futuro continua funcionando sem ramo condicional.
"""
from __future__ import annotations

import difflib
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import islice
from typing import Protocol, TypeAlias

import networkx as nx

from utils.name_keys import norm_name
from utils.number_format import formatar_cm

# ---------------------------------------------------------------------------
# Limiares. Sao constantes PUBLICAS de proposito: teste e tela citam o mesmo
# numero, e um deles nao pode mudar sozinho.
# ---------------------------------------------------------------------------

#: Segmento abaixo disto e ruido e nao entra na conta (regra 1).
CM_MINIMO_SEGMENTO: float = 10.0

#: Maior bloco abaixo disto torna a evidencia fraca (regra 2).
CM_MINIMO_MAIOR_BLOCO: float = 15.0

#: Corte do `difflib.get_close_matches` no cruzamento de nomes.
CORTE_DIFLIB: float = 0.75

#: Frase exata do diagnostico de endogamia estrutural (contrato de texto).
MENSAGEM_ENDEROGAMIA: str = "Endogamia estrutural confirmada na árvore"

#: Frase para o match que ainda nao tem ligacao documental no grafo.
MENSAGEM_SEM_LIGACAO: str = (
    "O match ainda não possui nenhuma ligação documental mapeada no grafo da árvore."
)

#: Os dois rotulos que o diagnostico de bloco pequeno precisa conter.
ROTULO_EVIDENCIA_FRACA: str = "evidência fraca"
ROTULO_PARENTESCO_INFLADO: str = "parentesco distante inflado"

#: Chaves aceitas para o cM de um segmento. A primeira e a do fluxo real
#: (`genetic_evidence`); as outras cobrem CSV/serializacoes externas.
CHAVES_DE_CM: tuple[str, ...] = ("cm", "centimorgans", "cM", "total_cm")

#: Teto de caminhos mais curtos materializados. Sem ele, um pedigree com
#: muitas ligacoes equivalentes poderia enumerar caminhos sem fim: o objetivo
#: aqui e detectar "mais de um", nao listar todos.
LIMITE_DE_CAMINHOS: int = 8


class SegmentoTipado(Protocol):
    """Forma estrutural minima de um segmento vindo de um adapter externo."""

    centimorgans: float


#: Tipo aceito por `avaliar_segmentos`: o dict que `genetic_evidence` produz, um
#: numero solto (testes e chamadas programaticas) ou um objeto com o atributo
#: `centimorgans` — a forma tipada de `parsers.segmentos_gedmatch`, que atravessa
#: a fronteira sem o nucleo importar o parser (`RF-09`).
SegmentoDeEntrada: TypeAlias = Mapping[str, object] | float | int | SegmentoTipado


# ---------------------------------------------------------------------------
# Resultados tipados
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenciaMitigada:
    """O que sobra de um kit depois do filtro rigido de 10 cM.

    `total_cm` e o numero RECALCULADO (so os segmentos mantidos) e `cm_bruto` e
    o que o arquivo declarava. Os dois viajam juntos: separar total e bruto e o
    que permite a tela explicar a diferenca sem esconder o dado original.
    """

    total_cm: float
    cm_bruto: float
    maior_segmento_cm: float | None
    maior_segmento_bruto_cm: float | None
    segmentos_mantidos: int
    segmentos_descartados: int
    segmentos_sem_valor: int
    cm_descartado: float
    evidencia_fraca: bool
    mensagem: str

    def para_dicionario(self) -> dict[str, object]:
        """Forma serializavel que entra em `result["endogamia"]` e na tela."""
        return {
            "total_cm": self.total_cm,
            "cm_bruto": self.cm_bruto,
            "maior_segmento_cm": self.maior_segmento_cm,
            "maior_segmento_bruto_cm": self.maior_segmento_bruto_cm,
            "segmentos_mantidos": self.segmentos_mantidos,
            "segmentos_descartados": self.segmentos_descartados,
            "segmentos_sem_valor": self.segmentos_sem_valor,
            "cm_descartado": self.cm_descartado,
            "evidencia_fraca": self.evidencia_fraca,
            "mensagem": self.mensagem,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticoDeEndogamia:
    """Caminhos mais curtos no grafo e o veredito de endogamia estrutural."""

    origem: str
    destino: str
    caminhos: tuple[tuple[str, ...], ...]
    mrca_ids: tuple[str, ...]
    endogamia_estrutural: bool
    truncado: bool
    mensagem: str

    @property
    def quantidade_de_caminhos(self) -> int:
        return len(self.caminhos)

    def para_dicionario(self) -> dict[str, object]:
        return {
            "origem": self.origem,
            "destino": self.destino,
            "caminhos": [list(caminho) for caminho in self.caminhos],
            "mrca_ids": list(self.mrca_ids),
            "quantidade_de_caminhos": self.quantidade_de_caminhos,
            "endogamia_estrutural": self.endogamia_estrutural,
            "truncado": self.truncado,
            "mensagem": self.mensagem,
        }


@dataclass(frozen=True, slots=True)
class CorrespondenciaDeNome:
    """Um no do GEDCOM que o `difflib` considerou proximo do nome do CSV."""

    id: str
    nome: str
    nome_normalizado: str
    similaridade: float


@dataclass(frozen=True, slots=True)
class AnaliseDeEndogamia:
    """As tres regras aplicadas a UM match, na ordem em que elas valem."""

    match_id: str | None
    correspondencias: tuple[CorrespondenciaDeNome, ...]
    evidencia: EvidenciaMitigada
    diagnostico: DiagnosticoDeEndogamia | None


# ---------------------------------------------------------------------------
# Leitura tolerante dos numeros
# ---------------------------------------------------------------------------


def _para_float(valor: object) -> float | None:
    """Converte para float sem levantar: dado invalido vira `None`."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def _cm_do_segmento(segmento: SegmentoDeEntrada) -> float | None:
    """Extrai o cM de um segmento em qualquer das formas aceitas.

    Aceita o dict de `genetic_evidence`, um numero solto e um objeto com o
    atributo `centimorgans` (a forma tipada de `parsers.segmentos_gedmatch`).
    O atributo e lido por `getattr` de proposito: o nucleo nao importa o parser
    (`RF-09`), e a forma tipada atravessa a fronteira por duck typing.
    """
    if isinstance(segmento, Mapping):
        for chave in CHAVES_DE_CM:
            if chave in segmento:
                return _para_float(segmento[chave])
        return None
    atributo = getattr(segmento, "centimorgans", None)
    if atributo is not None:
        return _para_float(atributo)
    return _para_float(segmento)


# ---------------------------------------------------------------------------
# O servico de dominio
# ---------------------------------------------------------------------------


class DNAAnalyzer:
    """Aplica as regras de endogamia sobre segmentos e sobre o grafo do GEDCOM.

    A classe nao guarda estado de analise: limiares entram no construtor (para
    teste e para outra politica), e segmentos/grafo entram em cada chamada. Duas
    analises simultaneas nao compartilham nada, pela mesma razao que o nucleo
    deixou de ter estado global (`RF-01`).

    ## Exemplo

    >>> analisador = DNAAnalyzer()
    >>> evidencia = analisador.avaliar_segmentos([6.4, 6.4, 20.0])
    >>> evidencia.total_cm
    20.0
    >>> evidencia.segmentos_descartados
    2
    >>> evidencia.evidencia_fraca
    False
    """

    def __init__(
        self,
        *,
        cm_minimo_segmento: float = CM_MINIMO_SEGMENTO,
        cm_minimo_maior_bloco: float = CM_MINIMO_MAIOR_BLOCO,
        corte_difflib: float = CORTE_DIFLIB,
        limite_de_caminhos: int = LIMITE_DE_CAMINHOS,
    ) -> None:
        if cm_minimo_segmento < 0:
            raise ValueError("cm_minimo_segmento não pode ser negativo")
        if cm_minimo_maior_bloco < 0:
            raise ValueError("cm_minimo_maior_bloco não pode ser negativo")
        if not 0.0 <= corte_difflib <= 1.0:
            raise ValueError("corte_difflib precisa estar entre 0 e 1")
        if limite_de_caminhos < 2:
            # 2 e o menor valor que ainda distingue "um caminho" de "endogamia".
            raise ValueError("limite_de_caminhos precisa ser >= 2")
        self.cm_minimo_segmento = float(cm_minimo_segmento)
        self.cm_minimo_maior_bloco = float(cm_minimo_maior_bloco)
        self.corte_difflib = float(corte_difflib)
        self.limite_de_caminhos = int(limite_de_caminhos)

    # -- Regras 1 e 2: filtro e recálculo ----------------------------------

    def avaliar_segmentos(
        self,
        segmentos: Iterable[SegmentoDeEntrada] | None,
    ) -> EvidenciaMitigada:
        """Descarta segmentos abaixo do minimo e recalcula o total.

        O total e `math.fsum` — soma exata —, e nao `sum` incremental: o valor
        nasce aqui, sem contrato de paridade, e nao ha motivo para carregar a
        cauda de ponto flutuante que o fluxo legado preserva de proposito.

        Segmento sem cM numerico (`None`, `NaN`, texto invalido) e contabilizado
        em `segmentos_sem_valor` e **nao** entra em nenhuma soma: um null nao e
        zero, e tratar null como zero inventaria um segmento.
        """
        mantidos: list[float] = []
        brutos: list[float] = []
        descartados = 0
        sem_valor = 0
        cm_descartado: list[float] = []

        for segmento in segmentos or ():
            cm = _cm_do_segmento(segmento)
            if cm is None:
                sem_valor += 1
                continue
            brutos.append(cm)
            if cm < self.cm_minimo_segmento:
                descartados += 1
                cm_descartado.append(cm)
                continue
            mantidos.append(cm)

        total = math.fsum(mantidos)
        cm_bruto = math.fsum(brutos)
        maior = max(mantidos) if mantidos else None
        maior_bruto = max(brutos) if brutos else None
        # Sem bloco acima do limite nao ha evidencia utilizavel: a mesma
        # condicao de "fraco", e o texto abaixo diz qual dos dois casos ocorreu.
        fraca = maior is None or maior < self.cm_minimo_maior_bloco

        return EvidenciaMitigada(
            total_cm=total,
            cm_bruto=cm_bruto,
            maior_segmento_cm=maior,
            maior_segmento_bruto_cm=maior_bruto,
            segmentos_mantidos=len(mantidos),
            segmentos_descartados=descartados,
            segmentos_sem_valor=sem_valor,
            cm_descartado=math.fsum(cm_descartado),
            evidencia_fraca=fraca,
            mensagem=self._mensagem_da_evidencia(
                total=total,
                cm_bruto=cm_bruto,
                maior=maior,
                descartados=descartados,
                cm_descartado=math.fsum(cm_descartado),
                sem_valor=sem_valor,
            ),
        )

    def _mensagem_da_evidencia(
        self,
        *,
        total: float,
        cm_bruto: float,
        maior: float | None,
        descartados: int,
        cm_descartado: float,
        sem_valor: int,
    ) -> str:
        """Diagnostico em texto, montado no nucleo (o template nao remonta frase).

        A frase e vazia quando nada aconteceu: cartao sem ruido nao ganha aviso.
        """
        partes: list[str] = []
        if descartados:
            partes.append(
                f"{descartados} segmento(s) abaixo de {formatar_cm(self.cm_minimo_segmento)} cM "
                f"descartado(s) ({formatar_cm(cm_descartado)} cM no total)."
            )
        if sem_valor:
            partes.append(
                f"{sem_valor} segmento(s) sem cM numérico foram ignorados."
            )
        if maior is None:
            partes.append(
                "Nenhum segmento sobreviveu ao filtro: "
                f"{ROTULO_EVIDENCIA_FRACA}, sem base genética para parentesco "
                f"(total bruto declarado: {formatar_cm(cm_bruto)} cM). "
                f"Leitura possível: {ROTULO_PARENTESCO_INFLADO}."
            )
        elif maior < self.cm_minimo_maior_bloco:
            partes.append(
                f"Maior bloco após o filtro: {formatar_cm(maior)} cM, abaixo de "
                f"{formatar_cm(self.cm_minimo_maior_bloco)} cM — "
                f"{ROTULO_EVIDENCIA_FRACA} e possível {ROTULO_PARENTESCO_INFLADO}."
            )
        if not partes:
            return ""
        if descartados or sem_valor:
            partes.append(
                f"Total recalculado só com os segmentos que sobreviveram: "
                f"{formatar_cm(total)} cM (bruto: {formatar_cm(cm_bruto)} cM)."
            )
        return " ".join(partes)

    # -- Regra 3: caminhos e endogamia estrutural --------------------------

    def caminhos_mais_curtos(
        self,
        grafo: nx.Graph | None,
        origem: str | None,
        destino: str | None,
    ) -> tuple[tuple[str, ...], ...]:
        """Todos os caminhos mais curtos entre dois nos, sem levantar erro.

        Devolve tupla vazia quando nao ha grafo, quando um dos nos nao existe ou
        quando `nx.NetworkXNoPath` acontece — e este ultimo o caso real do match
        genetico que ainda nao tem ligacao documental mapeada, e ele **nao** pode
        derrubar a analise.

        O grafo e convertido com `to_undirected(as_view=True)` — a view evita a
        copia O(V+E) do grafo que o parser ja entrega nao-direcionado, e a
        chamada vale tambem para um `DiGraph`.
        """
        caminhos, _truncado = self._caminhos_com_truncamento(grafo, origem, destino)
        return caminhos

    def _caminhos_com_truncamento(
        self,
        grafo: nx.Graph | None,
        origem: str | None,
        destino: str | None,
    ) -> tuple[tuple[tuple[str, ...], ...], bool]:
        """Caminhos mais curtos (ate o limite) e o indicador de truncamento.

        A enumeracao para no `limite + 1`: o caminho extra e o que permite saber
        que havia mais sem percorrer um pedigree patologico por inteiro. Feita
        numa passada so para nao repetir o BFS em `diagnosticar_endogamia`.
        """
        if grafo is None or origem is None or destino is None:
            return (), False
        if origem not in grafo or destino not in grafo:
            return (), False
        # `as_view=True`: a conversao para nao-direcionado NAO copia o grafo.
        # Sem o view, cada cartao pagaria O(V+E) para uma operacao que so precisa
        # de travessia — medido no GEDCOM real, e o mesmo motivo pelo qual
        # `core.dna_analysis` evita copiar a arvore por cartao.
        nao_direcionado = grafo.to_undirected(as_view=True)
        try:
            gerador = nx.all_shortest_paths(nao_direcionado, source=origem, target=destino)
            coletados = tuple(
                tuple(caminho)
                for caminho in islice(gerador, self.limite_de_caminhos + 1)
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return (), False
        truncado = len(coletados) > self.limite_de_caminhos
        return coletados[: self.limite_de_caminhos], truncado

    def diagnosticar_endogamia(
        self,
        grafo: nx.Graph | None,
        origem: str,
        destino: str,
        mrca_id: str | None = None,
    ) -> DiagnosticoDeEndogamia:
        """Classifica o par (raiz, match) quanto a endogamia estrutural.

        ## O criterio e literal, e e o pedido

        **Mais de um caminho mais curto** entre as duas pessoas e a assinatura de
        colapso de pedigree: a mesma distancia genealogica chegando por dois
        ramos significa que os ramos se cruzaram antes. O diagnostico aponta
        `Endogamia estrutural confirmada na árvore`.

        ## MRCA

        Quando `mrca_id` e informado pelo parentesco documental, ele vence — e o
        mesmo no que a secao 1 do cartao ja mostra. Sem ele, os candidatos sao os
        nos de pessoa comuns a **todos** os caminhos (a interseccao), que e o que
        "o mesmo ancestral comum" significa quando ha mais de um caminho.

        ## Sem caminho

        `NetworkXNoPath` e `NodeNotFound` sao tratados como ausencia de ligacao
        documental, e nao como falha: o cartao continua sendo montado, com o DNA
        e o parentesco declarado "nao encontrado".
        """
        caminhos, truncado = self._caminhos_com_truncamento(grafo, origem, destino)
        endogamia = len(caminhos) > 1
        if not caminhos:
            mensagem = MENSAGEM_SEM_LIGACAO
        elif endogamia:
            mensagem = MENSAGEM_ENDEROGAMIA
        else:
            mensagem = "Nenhuma endogamia estrutural detectada na árvore."

        return DiagnosticoDeEndogamia(
            origem=origem,
            destino=destino,
            caminhos=caminhos,
            mrca_ids=self._mrca_dos_caminhos(grafo, caminhos, origem, destino, mrca_id),
            endogamia_estrutural=endogamia,
            truncado=truncado,
            mensagem=mensagem,
        )

    @staticmethod
    def _mrca_dos_caminhos(
        grafo: nx.Graph | None,
        caminhos: Sequence[Sequence[str]],
        origem: str,
        destino: str,
        mrca_id: str | None,
    ) -> tuple[str, ...]:
        """Ancestral comum informado, ou a interseccao dos caminhos."""
        if not caminhos:
            return ()
        # O MRCA do parentesco documental VENCE quando aparece em algum caminho:
        # ele e o no que a secao 1 do cartao ja mostra, e dois caminhos podem
        # chegar a ele por familias diferentes (o que e exatamente o colapso).
        if mrca_id and any(mrca_id in caminho for caminho in caminhos):
            return (mrca_id,)

        comuns = set(caminhos[0])
        for caminho in caminhos[1:]:
            comuns &= set(caminho)
        comuns -= {origem, destino}

        def e_pessoa(no: str) -> bool:
            if grafo is None:
                return True
            tipo = grafo.nodes[no].get("type") if no in grafo else None
            # Sem atributo de tipo (grafo sintetico de teste), nao da para
            # distinguir: e mais honesto listar do que esconder.
            return tipo in (None, "person")

        return tuple(sorted(no for no in comuns if e_pessoa(no)))

    # -- Cruzamento difuso de nomes ----------------------------------------

    @staticmethod
    def limpar_nome_gedcom(nome: str | None) -> str:
        """Remove as barras do GEDCOM e colapsa espacos.

        `Adriano /Santos/` vira `Adriano Santos`. As barras nunca sao parte do
        nome: no GEDCOM elas delimitam o sobrenome de familia, e deixa-las na
        string faria o `difflib` comparar pontuacao em vez de nome.
        """
        if not nome:
            return ""
        return " ".join(str(nome).replace("/", " ").split())

    def indice_de_nomes(
        self,
        nomes_por_id: Mapping[str, str | None],
    ) -> dict[str, list[tuple[str, str]]]:
        """Indice `nome normalizado -> [(id, nome limpo), ...]`.

        Um nome normalizado pode apontar para varios ids (homonimos). O indice
        preserva todos: a resolucao devolve todos os candidatos daquela grafia,
        e nao escolhe um em silencio.
        """
        indice: dict[str, list[tuple[str, str]]] = {}
        for pid, nome in nomes_por_id.items():
            limpo = self.limpar_nome_gedcom(nome)
            chave = norm_name(limpo)
            if not chave:
                continue
            indice.setdefault(chave, []).append((pid, limpo))
        return indice

    def casar_nome(
        self,
        nome_csv: str | None,
        nomes_por_id: Mapping[str, str | None],
        *,
        limite: int = 5,
    ) -> tuple[CorrespondenciaDeNome, ...]:
        """Resolve o nome do CSV contra os nos do GEDCOM com `difflib`.

        Usa `difflib.get_close_matches` sobre formas normalizadas (sem acento,
        minusculas, barras removidas) com `cutoff` 0.75, e devolve todos os ids
        daquela grafia — nao apenas o primeiro. A similaridade reportada e a
        razao do `SequenceMatcher`, para a tela poder dizer "95% parecido" em vez
        de apresentar o palpite como certeza.
        """
        if limite < 1:
            return ()
        alvo = norm_name(self.limpar_nome_gedcom(nome_csv))
        if not alvo:
            return ()
        indice = self.indice_de_nomes(nomes_por_id)
        if not indice:
            return ()
        chaves = difflib.get_close_matches(
            alvo, list(indice), n=limite, cutoff=self.corte_difflib
        )
        correspondencias: list[CorrespondenciaDeNome] = []
        for chave in chaves:
            similaridade = difflib.SequenceMatcher(None, alvo, chave).ratio()
            for pid, nome_limpo in indice[chave]:
                correspondencias.append(
                    CorrespondenciaDeNome(
                        id=pid,
                        nome=nome_limpo,
                        nome_normalizado=chave,
                        similaridade=similaridade,
                    )
                )
        correspondencias.sort(key=lambda item: (-item.similaridade, item.id))
        return tuple(correspondencias)

    # -- O caminho completo de um match ------------------------------------

    def analisar(
        self,
        *,
        nome_csv: str | None,
        nomes_por_id: Mapping[str, str | None],
        segmentos: Iterable[SegmentoDeEntrada] | None,
        grafo: nx.Graph | None,
        origem_id: str,
        match_id: str | None = None,
    ) -> AnaliseDeEndogamia:
        """Aplica as tres regras a um match, resolvendo o no se preciso.

        Quando `match_id` vem informado (o fluxo principal ja o escolheu pelo
        `core.matching`), a resolucao difusa nao roda — e o comportamento
        continua sendo o do fluxo. Quando nao vem, `casar_nome` e a porta de
        entrada, e o primeiro candidato aceito alimenta o diagnostico de grafo.
        """
        correspondencias: tuple[CorrespondenciaDeNome, ...] = ()
        alvo = match_id
        if alvo is None:
            correspondencias = self.casar_nome(nome_csv, nomes_por_id)
            alvo = correspondencias[0].id if correspondencias else None

        evidencia = self.avaliar_segmentos(segmentos)
        # Sem grafo nao ha o que diagnosticar: devolver "sem ligacao" seria
        # afirmar sobre uma arvore que nao foi entregue.
        diagnostico = (
            self.diagnosticar_endogamia(grafo, origem_id, alvo)
            if alvo is not None and grafo is not None
            else None
        )
        return AnaliseDeEndogamia(
            match_id=alvo,
            correspondencias=correspondencias,
            evidencia=evidencia,
            diagnostico=diagnostico,
        )


__all__ = [
    "DNAAnalyzer",
    "EvidenciaMitigada",
    "DiagnosticoDeEndogamia",
    "CorrespondenciaDeNome",
    "AnaliseDeEndogamia",
    "CM_MINIMO_SEGMENTO",
    "CM_MINIMO_MAIOR_BLOCO",
    "CORTE_DIFLIB",
    "MENSAGEM_ENDEROGAMIA",
    "MENSAGEM_SEM_LIGACAO",
    "ROTULO_EVIDENCIA_FRACA",
    "ROTULO_PARENTESCO_INFLADO",
    "SegmentoDeEntrada",
    "SegmentoTipado",
]
