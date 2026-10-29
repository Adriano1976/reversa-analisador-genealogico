"""As fontes de nomes da busca (feature 052, `D-02`).

Duas implementacoes da porta `FonteDeNomes`: a **arvore** aberta e o **relatorio de
matches** selecionado. Elas moram num modulo proprio, e nao em `adaptadores.py`, porque
aquele arquivo ja acumula armazenamento em disco, cache de arvore e persistencia
Postgres — quatro razoes para mudar no mesmo lugar. Aqui a razao de mudar e uma so: a
forma de obter nomes de uma fonte.

## O que cada fonte faz, e o que ela NAO faz

Nenhuma das duas casa, ordena ou trunca: isso e do nucleo. Elas entregam candidatos com
`normalizado` e `tokens` **prontos**, cada uma pela sua autoridade de normalizacao
(`core.homonimos.normalizar` na arvore, `utils.name_keys.norm_name` no relatorio), e
montam ficha so dos identificadores que o ranking pedir.

## Custo, e por que ele e pago uma vez

A lista de candidatos da arvore e derivada do indice que `core.homonimos` ja construiu e
fica **presa ao grafo**, como os demais derivados do nucleo. A primeira busca numa
arvore paga a montagem; as seguintes reaproveitam. Sem isso, cada busca varreria 35 mil
pessoas — e o fluxo de DNA ja pagou esse preco uma vez para nao paga-lo 71.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.busca_de_nome import NomeParaBuscar
from core.erros import ErroDeDominio
from core.fichas_da_pessoa import person_summary
from core.homonimos import indice_por_nome, indice_por_token, normalizar
from core.registro import get_name
from parsers.segmentos_gedmatch import ler_segmentos_gedmatch
from utils.name_keys import norm_name

if TYPE_CHECKING:
    # So para o verificador: em execucao as anotacoes sao strings (`from __future__`),
    # e a fonte nao arrasta o parser nem o pacote de portas para dentro de si.
    from parsers.gedcom_parser import Tree

    from ports import ArmazenamentoDeArquivos, CarregadorDeArvores

_log = logging.getLogger(__name__)

#: Atributo do grafo com os candidatos ja montados. Prefixo `_` pela mesma razao dos
#: indices: nao colidir com atributo de `networkx.Graph`.
ATRIBUTO_DOS_CANDIDATOS = "_analisador_candidatos_de_busca"

#: Texto de tela quando o relatorio selecionado nao pode ser lido (`RF-13`). Fixo e
#: curto: o motivo acionavel da excecao de dominio entra no lugar dele quando existe.
AVISO_RELATORIO_ILEGIVEL = (
    "Não foi possível ler o relatório de matches selecionado."
)


def _texto_do_aviso(erro: Exception) -> str:
    """Texto de tela da falha: o da excecao de dominio, ou o literal fixo.

    Excecao inesperada NAO vira texto de tela — o traceback vai para o log. E a mesma
    regra que a borda pratica ao traduzir erro de dominio: o operador recebe uma frase,
    quem depura recebe o rastro.
    """
    if isinstance(erro, ErroDeDominio):
        mensagem = getattr(erro, "mensagem", None) or str(erro)
        texto = str(mensagem).strip()
        if texto:
            return texto
    return AVISO_RELATORIO_ILEGIVEL


class NomesDaArvoreGedcom:
    """`FonteDeNomes` sobre a arvore aberta.

    Entrega TODAS as pessoas da arvore como candidatos — o filtro e do nucleo, nao da
    fonte. O custo e a montagem da tupla, feita uma vez e presa ao grafo.
    """

    identidade = "arvore"
    rotulo = "Árvore GEDCOM"

    def __init__(self, carregador: CarregadorDeArvores) -> None:
        self._carregador: CarregadorDeArvores = carregador

    def normalizar(self, texto: str) -> str:
        return normalizar(texto)

    def _arvore(self, referencia: str | None, dono: str) -> Tree | None:
        if not referencia:
            return None
        return self._carregador.carregar(referencia, dono)

    def nomes(self, referencia: str | None, dono: str):
        if not referencia:
            return (), None
        arvore = self._arvore(referencia, dono)
        if arvore is None:
            return None, None
        return self._candidatos(arvore), None

    def _candidatos(self, arvore: Tree) -> tuple[NomeParaBuscar, ...]:
        grafo = arvore[2]
        if grafo is not None:
            guardados = getattr(grafo, ATRIBUTO_DOS_CANDIDATOS, None)
            if isinstance(guardados, tuple):
                return guardados

        pessoas = arvore[0]
        candidatos: list[NomeParaBuscar] = []
        for chave, ids in indice_por_nome(arvore).items():
            partes = tuple(dict.fromkeys(chave.split()))
            for pid in ids:
                candidatos.append(
                    NomeParaBuscar(
                        identificador=str(pid),
                        nome=get_name(pessoas.get(pid)),
                        normalizado=chave,
                        tokens=partes,
                        origem=self.identidade,
                    )
                )
        resultado = tuple(candidatos)
        if grafo is not None:
            setattr(grafo, ATRIBUTO_DOS_CANDIDATOS, resultado)
        return resultado

    def fichas(self, referencia: str | None, dono: str,
               identificadores: tuple[str, ...]) -> dict[str, dict[str, object]]:
        arvore = self._arvore(referencia, dono)
        if arvore is None:
            return {}
        return {
            str(pid): person_summary(arvore, pid)
            for pid in identificadores
            if pid in arvore[0]
        }


class NomesDoArquivoDeMatches:
    """`FonteDeNomes` sobre o relatorio de matches.

    Le o CSV pelo caminho de leitura que ja existe, agrega os segmentos por nome e
    devolve um candidato por pessoa testada. O `kit` e o `cM` viajam em `dados`, que e o
    que o card precisa mostrar — a fonte nao monta card.
    """

    identidade = "relatorio"
    rotulo = "Relatório de matches"

    def __init__(self, armazenamento: ArmazenamentoDeArquivos) -> None:
        self._armazenamento: ArmazenamentoDeArquivos = armazenamento

    def normalizar(self, texto: str) -> str:
        return norm_name(texto)

    def nomes(self, referencia: str | None, dono: str):
        if not referencia:
            return (), None
        caminho = self._armazenamento.resolver(referencia, dono)
        if caminho is None:
            return None, None
        try:
            leitura = ler_segmentos_gedmatch(caminho)
        except Exception as erro:  # noqa: BLE001 - a fonte nao derruba a busca (RF-13)
            _log.exception("relatorio de matches ilegivel para a busca")
            return (), _texto_do_aviso(erro)

        # Tres mapas paralelos, e nao um dicionario heterogeneo: o verificador precisa
        # saber que a soma e `float` e que o kit e `str | None` em cada ponto de uso.
        nomes: dict[str, str] = {}
        kits: dict[str, str | None] = {}
        soma_cm: dict[str, float] = {}
        ordem: list[str] = []
        for segmento in leitura.segmentos:
            chave = norm_name(segmento.pessoa)
            if not chave:
                continue
            if chave not in nomes:
                nomes[chave] = segmento.pessoa
                kits[chave] = segmento.kit
                soma_cm[chave] = 0.0
                ordem.append(chave)
            soma_cm[chave] += segmento.centimorgans
            if kits[chave] is None:
                kits[chave] = segmento.kit

        candidatos = tuple(
            NomeParaBuscar(
                identificador=chave,
                nome=nomes[chave],
                normalizado=chave,
                tokens=tuple(dict.fromkeys(chave.split())),
                origem=self.identidade,
                dados={
                    "kit": kits[chave],
                    "centimorgans": soma_cm[chave],
                    "arquivo": referencia,
                },
            )
            for chave in ordem
        )
        return candidatos, None

    def fichas(self, referencia: str | None, dono: str,
               identificadores: tuple[str, ...]) -> dict[str, dict[str, object]]:
        """A fonte de matches nao tem ficha: o card e montado do que ja veio."""
        return {}


__all__: list[str] = [
    "ATRIBUTO_DOS_CANDIDATOS",
    "AVISO_RELATORIO_ILEGIVEL",
    "NomesDaArvoreGedcom",
    "NomesDoArquivoDeMatches",
]
