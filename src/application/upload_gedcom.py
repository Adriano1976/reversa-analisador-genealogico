"""Caso de uso do upload de GEDCOM: grava, carrega a arvore e devolve o resultado tipado.

O fluxo que vive no ramo `upload_gedcom` da rota, **sem HTTP**: recebe o conteudo e o nome
original, grava pela porta, carrega a arvore pelo carregador e devolve o que a tela precisa.

## O que NAO esta aqui, e por que

- **A leitura do formulario.** `request`, `request.files` e o nome do campo sao do adaptador
  de entrada.
- **As duas guardas de formulario** ("Nenhum arquivo GEDCOM enviado." e "Nenhum arquivo
  selecionado."): elas decidem sobre o **formulario**, e nao sobre o arquivo, entao continuam
  na borda.
- **A montagem das portas.** O caso de uso recebe as duas por parametro e nunca instancia
  `ArmazenamentoEmDisco` nem `CarregadorDeArvoresGedcom` (`RF-02`).

## Reenvio: identico, atualizado ou novo (`RN-17`)

Ate 2026-10-10, os tres desfechos que existem de fato davam a **mesma** resposta, e um deles era
invisivel para quem enviava:

- **mesmo nome, mesmo conteudo.** A chave vem do conteudo, entao o caminho e o mesmo e a
  gravacao nem acontece. A tela dizia "carregado!" e o operador nao tinha como saber que a
  segunda tentativa nao fez nada — agora ela avisa que ja estava armazenado;
- **mesmo nome, conteudo DIFERENTE.** E o "arquivo atualizado". A chave muda, entao nascia um
  SEGUNDO arquivo ao lado do antigo, e a lista passava a ter duas linhas com o mesmo rotulo —
  caso medido na pasta real do operador. Agora a versao anterior e **aposentada** e a lista fica
  com UMA linha;
- **nome novo.** Nada muda: o literal congelado continua sendo `Arquivo '...' carregado!`.

A decisao dos tres casos **nao mora aqui**: ela esta em `application/reenvio.py`, porque desde
que a `RN-17` passou a valer tambem para o CSV ela tem dois chamadores. O que fica neste arquivo
e a **mensagem**, que e contrato de tela e pertence a este caso de uso.

## A substituicao APOSENTA, e nao apaga

O operador escolheu "aposentar o antigo" entre apagar e aposentar. A `RN-07` — a aplicacao nunca
apaga arquivo enviado — segue valendo: a versao anterior sai da lista e **continua no disco**,
inteira, em `<pasta>/_aposentados/`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.erros import GedcomNaoSuportado

from application import nomes_de_exibicao
from application.reenvio import IDENTICO, SUBSTITUIDO, guardar_com_substituicao


@dataclass(frozen=True)
class ResultadoDeUpload:
    """O que o upload devolve ao adaptador de entrada.

    Os quatro campos sao o que a tela precisa, e **nenhum deles e nome de campo de template**:
    `referencia` e a referencia armazenada que o formulario devolve na requisicao seguinte,
    `nome_exibido` e o nome que o operador reconhece, `nomes` alimenta o campo de sugestao, e
    `mensagem` e o literal de contrato congelado.
    """

    referencia: str
    nome_exibido: str
    nomes: list[str]
    mensagem: str


def upload_gedcom(conteudo: bytes, nome_original: str | None, dono: str,
                  armazenamento, carregador) -> ResultadoDeUpload:
    """Grava o GEDCOM, carrega a arvore e devolve o resultado tipado.

    A ordem e a regra: a validacao de conteudo acontece **antes** da gravacao, dentro da porta.
    Um conteudo recusado nao deixa residuo na pasta, e o motivo em texto que a porta devolve
    vira a excecao tipada **aqui** — a porta devolve motivo, nao excecao (`RF-03`).

    `dono` **nao** e usado para comportamento: ele e repassado a `armazenamento.guardar`, e a
    porta o ignora. Ele esta na assinatura porque e a costura que a Onda 3 preenche, e adiar o
    parametro reabriria toda assinatura de porta depois. Nenhum isolamento entre donos e
    implementado aqui, e nenhuma entrega desta feature pode ser citada como tendo implementado.
    """
    armazenado = guardar_com_substituicao(armazenamento, conteudo, nome_original, "gedcom", dono)
    if armazenado.motivo is not None:
        raise GedcomNaoSuportado(armazenado.motivo)

    # A REFERENCIA, e nao o caminho, e o que circula entre as duas portas: e ela que o formulario
    # devolve na requisicao seguinte, e e ela que a `RF-09` separa do caminho de proposito.
    referencia = os.path.basename(armazenado.caminho)

    if armazenado.desfecho == SUBSTITUIDO:
        mensagem = (
            f"Arquivo '{armazenado.visivel}' atualizado: a versão anterior saiu da lista e "
            "continua guardada, inteira, na pasta de aposentados."
        )
    elif armazenado.desfecho == IDENTICO:
        mensagem = (
            f"Arquivo '{armazenado.visivel}' já estava armazenado com o mesmo conteúdo: "
            "nada mudou."
        )
    else:
        # O literal CONGELADO do caminho comum, de antes desta feature: quem envia um arquivo
        # NOVO continua vendo exatamente o que sempre viu.
        mensagem = f"Arquivo '{nome_original}' carregado!"

    arvore = carregador.carregar(referencia, dono)
    if arvore is None:
        # Inalcancavel em execucao: `guardar` acabou de gravar o arquivo desta referencia e
        # devolveu o caminho dele. Existe para o checador estreitar a uniao do retorno, o mesmo
        # padrao que a rota ja usava antes da extracao. Nao e excecao de dominio de proposito:
        # uma falha de releitura depois da gravacao e falha inesperada, e vai para o
        # `except Exception` do ramo de envio, que e o caminho de hoje.
        raise RuntimeError("a árvore recém-gravada não pôde ser relida")

    return ResultadoDeUpload(
        referencia=referencia,
        nome_exibido=nome_original or "",
        nomes=nomes_de_exibicao(arvore),
        mensagem=mensagem,
    )


__all__ = ["ResultadoDeUpload", "upload_gedcom"]
