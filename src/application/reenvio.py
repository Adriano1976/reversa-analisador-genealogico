"""A regra do reenvio de arquivo (`RN-17`), escrita em UM lugar so.

## Por que isto e um modulo, e nao um bloco dentro do caso de uso

A `RN-17` nasceu no envio de GEDCOM. Quando ela passou a valer tambem para o CSV, havia duas
saidas: copiar a classificacao para dentro do ramo `dna_analysis` da rota, ou extrair. Copiar
criaria **duas verdades** sobre a mesma decisao — o defeito que este projeto ja pagou caro para
nao ter —, e foi por isso que a extracao venceu. Hoje os dois caminhos chamam a mesma funcao:

- o envio de GEDCOM (`upload_gedcom`), que acrescenta a mensagem do contrato de tela;
- o envio de CSV, que acontece dentro do formulario de **analise** (`action=dna_analysis`,
  campo `matches_csv`) e nao tem tela de envio propria.

## Os tres desfechos

| Desfecho | Quando | O que acontece no disco |
|---|---|---|
| `identico` | mesmo nome visivel, **mesmo** conteudo | nada: `guardar` nao sobrescreve (`RF-09`) e nada e aposentado |
| `substituido` | mesmo nome visivel, conteudo **diferente** | a versao anterior vai para `<pasta>/_aposentados/` e a nova ocupa o lugar |
| `novo` | nome visivel inedito | nada e aposentado |

A substituicao **aposenta, e nao apaga** (`RN-07`): a versao anterior continua inteira no
disco, e desfazer e mover de volta.

## A ORDEM e a regra: a foto da pasta vem ANTES de guardar

`guardar` nao sobrescreve. Depois dele, um arquivo que ja existia e um que acabou de nascer
ficam **indistinguiveis** na pasta — os dois estao la. So a foto de antes separa os dois casos,
e e ela que permite dizer "ja estava armazenado" em vez de "carregado!". A leitura custa so nome
e atributos, porque a porta nao abre conteudo.

A identidade do "mesmo arquivo" e o **nome visivel completo**, comparado com
`decompor_nome_armazenado`, que e a autoridade unica sobre o formato `<chave>__<nome visivel>`.
Reimplementar o formato aqui seria a segunda verdade que a extracao existe para evitar.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from utils.validate import decompor_nome_armazenado

NOVO = "novo"
IDENTICO = "identico"
SUBSTITUIDO = "substituido"


@dataclass(frozen=True)
class ResultadoDeArmazenamento:
    """A resposta de `guardar` mais o desfecho da `RN-17`.

    `caminho is None` significa **recusa**, e `motivo` diz por que — o mesmo contrato da porta
    de armazenamento. So quando a gravacao passa e que `desfecho`, `aposentadas` e `visivel`
    significam alguma coisa; na recusa eles vem neutros, para nao haver um segundo estado a
    interpretar.
    """

    caminho: str | None
    motivo: str | None
    desfecho: str
    aposentadas: int
    visivel: str


def guardar_com_substituicao(armazenamento, conteudo: bytes, nome_original: str | None,
                             tipo: str, dono: str) -> ResultadoDeArmazenamento:
    """Grava pela porta e aplica a `RN-17`. Nunca levanta: a recusa vem em `motivo`."""
    nomes_antes = {entrada.nome for entrada in armazenamento.listar(dono)}

    caminho, motivo = armazenamento.guardar(conteudo, nome_original, tipo, dono)
    if motivo is not None:
        return ResultadoDeArmazenamento(None, motivo, NOVO, 0, "")

    referencia = os.path.basename(caminho)
    visivel = decompor_nome_armazenado(referencia)[1]
    anteriores = [
        nome for nome in sorted(nomes_antes)
        if _e_versao_anterior(nome, referencia, visivel)
    ]
    aposentadas = sum(1 for nome in anteriores if armazenamento.aposentar(nome, dono))

    return ResultadoDeArmazenamento(caminho, None, _desfecho(referencia, nomes_antes, aposentadas),
                                    aposentadas, visivel)


def _e_versao_anterior(nome: str, referencia: str, visivel: str) -> bool:
    """`nome` e uma versao anterior do arquivo que acabou de ser gravado?

    Duas condicoes, e as duas importam:

    - nao ser o proprio arquivo recem-gravado. Sem esta, o envio **novo** aposentaria o arquivo
      que acabou de entrar, e a lista ficaria vazia;
    - ter o **mesmo nome visivel**. E a escolha conservadora da `RN-17`: um `arvore.csv` nao e
      substituido por um envio de `arvore.ged`. Substituir menos e mais seguro do que
      substituir demais, porque a versao que fica e a que o operador acabou de mandar.
    """
    if nome == referencia:
        return False
    return decompor_nome_armazenado(nome)[1] == visivel


def _desfecho(referencia: str, nomes_antes: set[str], aposentadas: int) -> str:
    """Qual dos tres desfechos o envio teve.

    A ordem dos testes e a regra, e nao estilo: quando **algo foi aposentado**, o envio e uma
    substituicao, ainda que a referencia nova ja existisse na foto (o caso do operador que
    volta para uma versao antiga do mesmo nome — a versao que estava na lista sai, e a que
    volta ocupa o lugar).
    """
    if aposentadas:
        return SUBSTITUIDO
    if referencia in nomes_antes:
        return IDENTICO
    return NOVO


__all__ = [
    "ResultadoDeArmazenamento",
    "guardar_com_substituicao",
    "NOVO",
    "IDENTICO",
    "SUBSTITUIDO",
]
