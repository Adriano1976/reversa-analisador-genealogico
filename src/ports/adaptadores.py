"""Adaptadores concretos das portas de `ports/` (`D-07`).

O adaptador **nao reimplementa a regra**: ele chama `utils/validate.py`, que
continua sendo a autoridade unica sobre o que pode ser gravado. Repetir a
derivacao de chave ou a validacao de conteudo aqui criaria uma segunda copia da
mesma regra, e as duas divergiriam no primeiro ajuste.

Nenhum adaptador levanta excecao de dominio. `validar_conteudo_gedcom` devolve
**motivo em texto**, e quem transforma o motivo na excecao de GEDCOM nao
reconhecido e o caso de uso `upload_gedcom` (`RF-03`, achado `A002`).

## `AnalisadorDeUpload` da `D-07` e `ArmazenamentoEmDisco` sao o mesmo papel

A `D-07` nomeia dois adaptadores concretos: `AnalisadorDeUpload` e
`ArmazenamentoEmDisco`, e descreve **os dois** como delegacoes para
`utils/validate.py` (chave por conteudo, nome armazenado, validacao de forma,
validacao de conteudo). Sao a mesma responsabilidade com dois nomes, e o `T007`
fixou um so: `ArmazenamentoEmDisco`. Nao existe componente faltando aqui — ver a
nota de execucao em `actions.md`.
"""
from __future__ import annotations

import os

from parsers.gedcom_parser import Tree, carregar_arvore
from utils.validate import (
    chave_de_armazenamento,
    chave_recebida_e_valida,
    nome_do_arquivo_armazenado,
    validar_conteudo_gedcom,
)


class ArmazenamentoEmDisco:
    """`ArmazenamentoDeArquivos` sobre a pasta de upload do processo.

    A pasta entra por parametro, e nao e lida do ambiente aqui dentro: quem
    resolve o caminho de upload e a borda (`src/app.py`), que ja responde a
    `ANALISADOR_UPLOAD_FOLDER` e ja garante que escrita e leitura usam o MESMO
    caminho. O adaptador nao sabe de ambiente nem de Flask.
    """

    def __init__(self, pasta: str):
        self._pasta = pasta

    def guardar(self, conteudo: bytes, nome_original: str | None,
                tipo: str) -> tuple[str | None, str | None]:
        """Valida antes de gravar; devolve `(caminho, motivo)`.

        A ordem e a regra (`RF-10`): a validacao de conteudo acontece **antes** de
        qualquer escrita, e uma recusa nao deixa residuo na pasta. Tambem e aqui
        que o conteudo ja armazenado **nao** e regravado (`RF-09`) — a chave vem do
        conteudo, entao o mesmo envio reencontra o mesmo arquivo.
        """
        motivo = validar_conteudo_gedcom(conteudo) if tipo == "gedcom" else None
        if motivo is not None:
            return None, motivo

        chave = chave_de_armazenamento(conteudo)
        nome_armazenado = nome_do_arquivo_armazenado(chave, nome_original)
        caminho = os.path.join(self._pasta, nome_armazenado)
        if not os.path.exists(caminho):
            with open(caminho, "wb") as destino:
                destino.write(conteudo)
        return caminho, None

    def resolver(self, referencia: str | None) -> str | None:
        """Caminho completo do arquivo armazenado, ou `None`.

        A validacao de forma e o que impede um `gedcom_filename` manipulado de
        apontar para fora da pasta (BUG-20260929-QMLY, criterio 5), e ela vem
        antes de qualquer `os.path.exists`.
        """
        if not chave_recebida_e_valida(referencia):
            return None
        caminho = os.path.join(self._pasta, referencia)
        return caminho if os.path.exists(caminho) else None


class CarregadorDeArvoresGedcom:
    """`CarregadorDeArvores` sobre o parser de GEDCOM.

    Resolve a referencia pelo armazenamento recebido e chama `carregar_arvore`. E
    o **unico** lugar da fronteira que parseia: a rota entrega a referencia e
    recebe a arvore, e nenhum caso de uso importa `parsers/`.
    """

    def __init__(self, armazenamento: ArmazenamentoEmDisco):
        self._armazenamento = armazenamento

    def carregar(self, referencia: str) -> Tree | None:
        caminho = self._armazenamento.resolver(referencia)
        if caminho is None:
            return None
        return carregar_arvore(caminho)


__all__ = ["ArmazenamentoEmDisco", "CarregadorDeArvoresGedcom"]
