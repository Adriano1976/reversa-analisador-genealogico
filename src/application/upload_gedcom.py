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

## Reenvio: identico, atualizado, ou novo (`RN-17`, `T037`)

Pedido do operador em 2026-10-10. Ate aqui, reenviar um arquivo tinha sempre a MESMA
resposta ("carregado!") nos tres desfechos que existem de fato, e um deles era invisivel:

- **`guarda` no nome, conteudo igual.** A chave vem do conteudo, entao o caminho e o mesmo e a
  gravacao nem acontece (`RF-09`). Antes, a tela dizia "carregado!" e o operador nao tinha como
  saber que a segunda tentativa nao fez nada;
- **mesmo nome, conteudo DIFERENTE.** E o "arquivo atualizado". A chave muda, entao nascia um
  SEGUNDO arquivo ao lado do antigo, e a lista passava a ter duas linhas com o mesmo rotulo —
  medido na pasta real, que tem dois `Familias_Sergipanas.csv`. Agora a versao anterior vai
  para a pasta de aposentados, e a lista fica com UMA;
- **nome novo.** Nada muda: o literal congelado continua sendo `Arquivo '...' carregado!`.

## A substituicao APOSENTA, e nao apaga

O operador escolheu explicitamente "aposentar o antigo" entre apagar e aposentar. A `RN-07`
diz que a aplicacao nunca apaga arquivo enviado, e ela segue valendo: a versao anterior sai da
lista e **continua no disco**, inteira, em `<pasta>/_aposentados/`. Desfazer e mover de volta.

A identidade do "mesmo arquivo" e o **nome visivel** — o nome que o operador deu. A comparacao
usa `decompor_nome_armazenado`, de `utils.validate`, que e a autoridade unica sobre o formato
`<chave>__<nome visivel>`; reimplementar o formato aqui criaria uma segunda verdade sobre o
mesmo contrato, que e o defeito que a `RN-02` proibe.
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

    `dono` **nao** e usado para comportamento (`RN-06`, `RF-08`): ele e repassado a
    `armazenamento.guardar`, e a porta o ignora. Esta na assinatura porque e a
    costura que a Onda 3 preenche, e adiar o parametro reabriria toda assinatura de
    porta depois. Nenhum isolamento entre donos e implementado aqui, e nenhuma
    entrega desta feature pode ser citada como tendo implementado.
    """
    # A REGRA DO REENVIO MORA EM `application/reenvio.py`, e nao aqui: desde que a `RN-17`
    # passou a valer tambem para o CSV, ela tem DOIS chamadores, e manter o bloco neste arquivo
    # criaria duas verdades sobre a mesma decisao. O que fica aqui e so a MENSAGEM, que e
    # contrato de tela e pertence a este caso de uso.
    armazenado = guardar_com_substituicao(armazenamento, conteudo, nome_original, "gedcom", dono)
    if armazenado.motivo is not None:
        raise GedcomNaoSuportado(armazenado.motivo)

    # A REFERENCIA, e nao o caminho, e o que circula entre as duas portas: e ela
    # que o formulario devolve na requisicao seguinte, e e ela que a `RF-09`
    # separa do caminho de propósito.
    referencia = os.path.basename(armazenado.caminho)

    if armazenado.desfecho == SUBSTITUIDO:
        mensagem = (
            f"Arquivo '{armazenado.visivel}' atualizado: a versão anterior saiu da lista e "
            "continua guardada, inteira, na pasta de aposentados."
        )
    elif armazenado.desfecho == IDENTICO:
        mensagem = (
            f"Arquivo '{armazenado.visivel}' já estava armazenado com o mesmo conteúdo: nada mudou."
        )
    else:
        # O literal CONGELADO do caminho comum. Ele e contrato de tela de antes desta feature,
        # e a `RN-17` nao o toca: quem reenvia um arquivo NOVO continua vendo o que sempre viu.
        mensagem = f"Arquivo '{nome_original}' carregado!"

    arvore = carregador.carregar(referencia, dono)
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
        mensagem=mensagem,
    )


__all__ = ["ResultadoDeUpload", "upload_gedcom"]
