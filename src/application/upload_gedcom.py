"""Caso de uso do upload de GEDCOM (`T011`; `RF-01`, `RF-09`, `RF-10`).

O fluxo que hoje vive no ramo `upload_gedcom` de `index()`, sem HTTP: recebe o
conteudo e o nome original, grava pelo port, carrega a arvore pelo carregador e
devolve o resultado tipado que o adaptador de entrada renderiza.

## O que NAO esta aqui

- **A leitura do formulario.** `request`, `request.files` e o nome do campo sao
  do adaptador de entrada.
- **As duas guardas de formulario** ("Nenhum arquivo GEDCOM enviado." e "Nenhum
  arquivo selecionado."): elas decidem sobre o *formulario*, nao sobre o arquivo,
  e continuam na borda.
- **A montagem do port.** O caso de uso recebe as portas por parametro e nunca
  instancia `ArmazenamentoEmDisco` nem `CarregadorDeArvoresGedcom` (`RF-02`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.erros import GedcomNaoSuportado

from application import nomes_de_exibicao


@dataclass(frozen=True)
class ResultadoDeUpload:
    """O que o upload devolve ao adaptador de entrada.

    Os quatro campos sao o que a tela precisa, e **nenhum deles e nome de campo de
    template** (`RF-20`): `referencia` e a referencia armazenada que o formulario
    devolve na requisicao seguinte, `nome_exibido` e o nome que o operador
    reconhece, `nomes` alimenta o campo de sugestao e `mensagem` e o literal de
    contrato congelado.
    """

    referencia: str
    nome_exibido: str
    nomes: list[str]
    mensagem: str


def upload_gedcom(conteudo: bytes, nome_original: str | None, dono: str,
                  armazenamento, carregador) -> ResultadoDeUpload:
    """Grava o GEDCOM, carrega a arvore e devolve o resultado tipado.

    A ordem e a regra (`RF-10`): a validacao de conteudo acontece **antes** da
    gravacao, dentro do port. Um conteudo recusado nao deixa residuo na pasta, e o
    motivo em texto que o port devolve vira a excecao tipada **aqui** — o port
    devolve motivo, nao excecao (`RF-03`, achado `A002`).

    `dono` **nao** e usado para comportamento nesta onda (`RN-06`, `RF-08`): ele
    esta na assinatura porque e a costura que a Onda 3 preenche, e adiar o
    parametro reabriria toda assinatura de porta depois. Nenhum isolamento entre
    donos e implementado aqui, e nenhuma entrega desta feature pode ser citada
    como tendo implementado.
    """
    caminho, motivo = armazenamento.guardar(conteudo, nome_original, "gedcom")
    if motivo is not None:
        raise GedcomNaoSuportado(motivo)

    # A REFERENCIA, e nao o caminho, e o que circula entre as duas portas: e ela
    # que o formulario devolve na requisicao seguinte, e e ela que a `RF-09`
    # separa do caminho de propósito.
    referencia = os.path.basename(caminho)
    arvore = carregador.carregar(referencia)
    if arvore is None:
        # Inalcancavel em execucao: `guardar` acabou de gravar o arquivo desta
        # referencia e devolveu o caminho dele. Existe para o checador estreitar
        # a uniao do retorno, o mesmo padrao que a rota ja usava antes da
        # extracao. Nao e excecao de dominio de proposito: uma falha de releitura
        # depois da gravacao e falha inesperada, e vai para o
        # `except Exception` do ramo de upload, que e o caminho de hoje.
        raise RuntimeError("a árvore recém-gravada não pôde ser relida")

    return ResultadoDeUpload(
        referencia=referencia,
        nome_exibido=nome_original or "",
        nomes=nomes_de_exibicao(arvore),
        mensagem=f"Arquivo '{nome_original}' carregado!",
    )


__all__ = ["ResultadoDeUpload", "upload_gedcom"]
