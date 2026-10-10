"""A regra do reenvio de arquivo (`RN-17`), em UM lugar so.

## Por que isto e um modulo, e nao codigo dentro do caso de uso

A `RN-17` nasceu no envio de GEDCOM (`application/upload_gedcom.py`). Quando o operador pediu
que ela valesse tambem para o CSV, a escolha era copiar o bloco de classificacao para dentro do
ramo `dna_analysis` da rota ou extrair. Copiar criaria **duas verdades** sobre a mesma regra —
o defeito que a `RN-02` proibe e que este projeto ja pagou caro para nao ter. Entao a decisao
mora aqui, e os dois caminhos chamam a mesma funcao:

- o envio de GEDCOM (`upload_gedcom`), que monta a mensagem do contrato de tela;
- o envio de CSV, que hoje acontece dentro do formulario de ANALISE
  (`action=dna_analysis`, campo `matches_csv`) e nao tem tela de envio propria.

## O que a regra decide

1. **`identico`** — mesmo nome visivel e mesmo conteudo. `guardar` nao sobrescreve (`RF-09`),
   entao nada e gravado e nada muda.
2. **`substituido`** — mesmo nome visivel, conteudo DIFERENTE. Cada versao anterior daquele
   nome e **aposentada** para `<pasta>/_aposentados/`, e a nova ocupa o lugar. A lista fica com
   UMA linha.
3. **`novo`** — nome visivel inedito. Nada e aposentado.

A substituicao **aposenta, e nao apaga** (`RN-07`): o operador escolheu essa alternativa entre
apagar e aposentar, e a versao anterior continua inteira no disco.

## A ordem e a regra: listar ANTES de guardar

`guardar` nao sobrescreve, entao depois dele um arquivo que ja existia e um que acabou de
nascer ficam indistinguiveis na pasta. So a foto de ANTES separa os dois casos. A leitura e so
de nome e atributos — a porta nao abre conteudo —, e acontece uma vez por envio.

A identidade e o **nome visivel completo**, comparado com `decompor_nome_armazenado` de
`utils.validate`, que e a autoridade unica sobre o formato `<chave>__<nome visivel>`.
"""
from __future__ import annotations

from dataclasses import dataclass

from utils.validate import decompor_nome_armazenado

NOVO = "novo"
IDENTICO = "identico"
SUBSTITUIDO = "substituido"


@dataclass(frozen=True)
class ResultadoDeArmazenamento:
    """`(caminho, motivo)` de `guardar`, mais o desfecho da `RN-17`.

    `caminho is None` significa recusa, e `motivo` explica — o mesmo contrato da porta. So
    quando a gravacao passa e que `desfecho`, `aposentadas` e `visivel` fazem sentido.
    """

    caminho: str | None
    motivo: str | None
    desfecho: str
    aposentadas: int
    visivel: str


def guardar_com_substituicao(armazenamento, conteudo: bytes, nome_original: str | None,
                             tipo: str, dono: str) -> ResultadoDeArmazenamento:
    """Grava pelo port e aplica a `RN-17`. Nunca levanta: a recusa vem em `motivo`."""
    import os

    # A FOTO DE ANTES. Ver a nota do modulo sobre por que ela nao pode vir depois.
    nomes_antes = {entrada.nome for entrada in armazenamento.listar(dono)}

    caminho, motivo = armazenamento.guardar(conteudo, nome_original, tipo, dono)
    if motivo is not None:
        return ResultadoDeArmazenamento(None, motivo, NOVO, 0, "")

    referencia = os.path.basename(caminho)
    _chave, visivel = decompor_nome_armazenado(referencia)
    ja_existia = referencia in nomes_antes

    versoes_anteriores = [
        nome for nome in sorted(nomes_antes)
        if nome != referencia and decompor_nome_armazenado(nome)[1] == visivel
    ]
    aposentadas = sum(1 for nome in versoes_anteriores if armazenamento.aposentar(nome, dono))

    if aposentadas:
        desfecho = SUBSTITUIDO
    elif ja_existia:
        desfecho = IDENTICO
    else:
        desfecho = NOVO
    return ResultadoDeArmazenamento(caminho, None, desfecho, aposentadas, visivel)


__all__ = [
    "ResultadoDeArmazenamento",
    "guardar_com_substituicao",
    "NOVO",
    "IDENTICO",
    "SUBSTITUIDO",
]
