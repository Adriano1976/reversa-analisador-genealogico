"""Portas da fronteira de aplicacao da Onda 2 (RF-02, RF-08, D-02, D-03).

Uma **porta** aqui e um `Protocol` — a interface que o caso de uso consome por
parametro, sem nunca instanciar a implementacao concreta. Quem implementa mora em
`ports/adaptadores.py` e e montado na borda (`src/app.py`).

## Quais portas existem, e por que sao estas

| Porta | O que a fronteira consome | Metodos |
|-------|---------------------------|---------|
| `ArmazenamentoDeArquivos` | gravar o upload e resolver a referencia recebida | 2 |
| `CarregadorDeArvores` | entregar a arvore a partir da referencia | 1 |
| `RepositorioDeArvores` | persistencia da arvore — **Onda 3, sem implementacao** | 2 |

`RF-02` nomeia as duas primeiras como "armazenamento de arquivo" e "repositorio de
arvore". `CarregadorDeArvores` e a **terceira**, acrescentada pela `D-02` e nao
prevista no `requirements.md`: sem ela, ou o caso de uso importaria
`parsers.gedcom_parser` (acoplando a aplicacao a um pacote de borda) ou cada ramo
da rota repetiria a resolucao de caminho e o parse. Fica declarado como desvio.

Nesta onda **nao** existe Protocolo para leitura de CSV nem para emissao de
diagrama: o contrato entre nucleo e fronteira para essas duas continua sendo a
classe concreta `Dependencias`, de `core/dna_analysis.py`, como a feature 005 a
estabilizou.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    # Import so para o checador de tipos. Em execucao a anotacao e uma string
    # (`from __future__ import annotations`), e a porta nao arrasta o parser para
    # dentro de quem so quer o contrato.
    from parsers.gedcom_parser import Tree


class ArmazenamentoDeArquivos(Protocol):
    """Grava o upload sob chave derivada do conteudo e resolve a referencia de volta.

    As duas operacoes vivem na mesma porta porque sao o mesmo ciclo de vida: quem
    grava e quem le depois usam exatamente o mesmo identificador, e a `RF-09`
    proibe que o nome e o caminho voltem a ser intercambiaveis.
    """

    def guardar(self, conteudo: bytes, nome_original: str | None,
                tipo: str) -> tuple[str | None, str | None]:
        """Valida ANTES de gravar e devolve `(referencia, motivo)`.

        `motivo is None` significa aceito, e `referencia` e o **caminho completo**
        do arquivo gravado — nunca um nome a ser remontado por quem chama.

        `motivo` preenchido significa recusado, e nesse caso **nada foi gravado**
        (`RF-10`). O motivo e texto, nao excecao: transforma-lo na excecao de
        dominio tipada e trabalho do caso de uso, nao do adaptador (`RF-03`,
        achado `A002`).

        `tipo` e o que decide se ha validacao de conteudo — hoje `"gedcom"` valida
        o cabecalho e `"csv"` nao valida conteudo nenhum. A assimetria e a divida
        #10, preservada de proposito nesta onda.
        """
        ...

    def resolver(self, referencia: str | None) -> str | None:
        """Caminho do arquivo ja armazenado, ou `None`.

        `None` cobre as duas recusas, e cobre-as pelo mesmo motivo: nos dois casos
        nao existe arquivo a ler. Sao elas a **forma invalida** — o que impede um
        `gedcom_filename` manipulado de apontar para fora da pasta de upload — e o
        **arquivo ausente** no disco.
        """
        ...


class CarregadorDeArvores(Protocol):
    """Entrega a arvore a partir de uma referencia recebida (`D-02`).

    **Um unico metodo, e essa e a condicao declarada da `D-02`:** se esta porta
    precisar de um segundo metodo, a decisao esta errada e o `/reversa-audit` deve
    ser reexecutado para reabri-la. O executor da feature nao tem autoridade para
    acrescentar o segundo metodo por conveniencia.
    """

    def carregar(self, referencia: str) -> Tree | None:
        """Arvore da referencia, ou `None` quando ela nao resolve para arquivo existente.

        `None` significa "nao ha o que carregar", e nao "arvore vazia": quem chama
        ja distinguiu o campo de formulario ausente antes de chegar aqui, e
        traduz o `None` na mensagem de referencia que nao existe mais.
        """
        ...


class RepositorioDeArvores(Protocol):
    """Contrato de persistencia da arvore para a **Onda 3**. Sem implementacao.

    Declarado e **sem consumidor**, de proposito (`D-03`): ele existe para dar
    lugar tipado onde a persistencia vai encaixar, sem inventar comportamento
    agora. Nenhum caso de uso o chama nesta onda, e **nao** existe adaptador em
    memoria — um adaptador em memoria reintroduziria, com outro nome, o estado
    global de processo que a feature 005 removeu.

    `dono` e parametro **obrigatorio** em todo metodo desde ja (`RF-08`). Adiar o
    dono reabriria toda assinatura de porta na Onda 3, que e o custo que esta
    decisao existe para nao pagar. Nenhum comportamento de isolamento e
    implementado nesta onda (`RN-06`, divida #4): o parametro e a costura, nao a
    funcionalidade.
    """

    def guardar(self, arvore: Tree, dono: str) -> str:
        """Persiste a arvore do dono e devolve a referencia armazenada."""
        ...

    def obter(self, referencia: str, dono: str) -> Tree | None:
        """Arvore do dono para a referencia, ou `None` quando nao ha essa arvore."""
        ...


__all__ = [
    "ArmazenamentoDeArquivos",
    "CarregadorDeArvores",
    "RepositorioDeArvores",
]
