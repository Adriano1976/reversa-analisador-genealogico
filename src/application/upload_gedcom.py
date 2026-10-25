"""Caso de uso do upload de GEDCOM: grava, carrega a arvore e devolve o resultado tipado.

O fluxo que vive no ramo `upload_gedcom` da rota, **sem HTTP**: recebe conteudo e nome
original, grava pela porta, carrega a arvore pelo carregador e devolve o que a tela precisa.

O que NAO esta aqui, e por que:

- **A leitura do formulario.** `request`, `request.files` e o nome do campo sao do
  adaptador de entrada.
- **As duas guardas de formulario** ("Nenhum arquivo GEDCOM enviado." e "Nenhum arquivo
  selecionado."): decidem sobre o **formulario**, e nao sobre o arquivo, entao ficam na borda.
- **A montagem das portas.** O caso de uso as recebe por parametro e nunca instancia
  `ArmazenamentoEmDisco` nem `CarregadorDeArvoresGedcom` (`RF-02`).

Reenvio: identico, atualizado ou novo (`RN-17`). Ate 2026-10-10 os tres desfechos davam a
**mesma** resposta, e um era invisivel:

- **mesmo nome, mesmo conteudo.** A chave vem do conteudo, entao o caminho e o mesmo e a
  gravacao nem acontece; a tela dizia "carregado!" e o operador nao sabia que a segunda
  tentativa nao fez nada — agora ela avisa que ja estava armazenado;
- **mesmo nome, conteudo DIFERENTE.** E o "arquivo atualizado": a chave muda, nascia um
  SEGUNDO arquivo ao lado do antigo e a lista ficava com duas linhas do mesmo rotulo (caso
  medido na pasta real) — agora a versao anterior e **aposentada** e a lista fica com UMA;
- **nome novo.** Nada muda: o literal congelado continua sendo `Arquivo '...' carregado!`.

A decisao dos tres casos **nao mora aqui**: esta em `application/reenvio.py`, porque a
`RN-17` passou a valer tambem para o CSV e tem dois chamadores. Aqui fica a **mensagem**,
contrato de tela deste caso de uso.

A substituicao APOSENTA, e nao apaga: o operador escolheu "aposentar o antigo" entre apagar
e aposentar, e a `RN-07` — a aplicacao nunca apaga arquivo enviado — segue valendo: a versao
anterior sai da lista e **continua no disco**, inteira, em `<pasta>/_aposentados/`.
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

    Os cinco campos sao o que a tela precisa, e **nenhum e nome de campo de template**:
    `referencia` e a referencia armazenada que o formulario devolve na requisicao seguinte,
    `nome_exibido` e o nome que o operador reconhece, `nomes` alimenta a sugestao,
    `mensagem` e o literal de contrato congelado e `desfecho` diz **qual** dos tres casos da
    `RN-17` aconteceu.

    `desfecho` existe para a **borda** — que audita sem distinguir o caso pelo texto da
    mensagem (feature 049, `D-07`). Reconhecer `novo` por "a mensagem nao mudou" daria ao
    literal de tela autoridade semantica, que e o que a `RF-20` proibe.
    """

    referencia: str
    nome_exibido: str
    nomes: list[str]
    mensagem: str
    desfecho: str


def upload_gedcom(conteudo: bytes, nome_original: str | None, dono: str,
                  armazenamento, carregador) -> ResultadoDeUpload:
    """Grava o GEDCOM, carrega a arvore e devolve o resultado tipado.

    A ordem e a regra: a validacao de conteudo acontece **antes** da gravacao, dentro da
    porta. Conteudo recusado nao deixa residuo na pasta, e o motivo em texto que a porta
    devolve vira excecao tipada **aqui** — a porta devolve motivo, nao excecao (`RF-03`).

    `dono` **nao** e usado para comportamento: e repassado a `armazenamento.guardar`, e a
    porta o ignora. Esta na assinatura porque e a costura que a Onda 3 preenche, e adiar o
    parametro reabriria toda assinatura de porta depois; nenhum isolamento entre donos e
    implementado aqui, e nenhuma entrega desta feature pode ser citada como tendo implementado.
    """
    armazenado = guardar_com_substituicao(armazenamento, conteudo, nome_original, "gedcom", dono)
    if armazenado.motivo is not None:
        raise GedcomNaoSuportado(armazenado.motivo)

    # A REFERENCIA, e nao o caminho, e o que circula entre as duas portas: e ela que o formulario
    # devolve na requisicao seguinte, e e ela que a `RF-09` separa do caminho de proposito.
    caminho: str | None = armazenado.caminho
    if caminho is None:
        # Inalcancavel pelo contrato de `ResultadoDeArmazenamento`: sem `motivo`, ha caminho.
        # Existe para o checador estreitar o tipo e para o defeito nao passar calado.
        raise RuntimeError("guardar nao devolveu caminho nem motivo")
    referencia: str = os.path.basename(caminho)

    if armazenado.desfecho == SUBSTITUIDO:
        mensagem: str = (
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
        # Inalcancavel em execucao: `guardar` acabou de gravar este arquivo e devolveu o
        # caminho. Existe para o checador estreitar a uniao do retorno, o padrao que a rota ja
        # usava antes da extracao. Nao e excecao de dominio de proposito: falha de releitura
        # apos a gravacao e inesperada e vai para o `except Exception` do ramo de envio.
        raise RuntimeError("a árvore recém-gravada não pôde ser relida")

    return ResultadoDeUpload(
        referencia=referencia,
        nome_exibido=nome_original or "",
        nomes=nomes_de_exibicao(arvore),
        mensagem=mensagem,
        desfecho=armazenado.desfecho,
    )


__all__: list[str] = ["ResultadoDeUpload", "upload_gedcom"]
