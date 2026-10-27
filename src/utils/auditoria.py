"""A linha de auditoria: acao, desfecho, arquivo, contagens, IP e identificador (feature 049).

## Por que esta linha existe

A extracao registrava, com todas as letras, que a unica acao da tela capaz de mover arquivo
do operador **nao deixava rastro nenhum** (`_reversa_sdd/tela-de-entrada/tasks.md`, lacuna 5).
A decisao 14 do `gaps.md` mandou logar as duas tentativas — sucesso e falha — e a feature
049 generalizou: tudo que mexe em arquivo ou produz resultado deixa linha.

## O que a linha identifica, e o que ela NAO pode carregar

O arquivo e identificado pela **chave de conteudo mais a extensao**, nunca pelo rotulo
visivel. O rotulo e o nome que o operador deu ao arquivo, e os nomes reais da pasta incluem
nome de pessoa (`Backup-Arvore-Sandro.ged`); o arquivo de auditoria sobrevive a requisicao,
entao um nome ali seria dado pessoal permanente — o que o Principio I proibe e o que a
decisao de 2026-10-25 fechou.

A separacao entre chave e rotulo **nao e reimplementada aqui**: `decompor_nome_armazenado`
(`utils/validate.py`) ja e a autoridade que faz isso, e duplicar a regra criaria a segunda
copia que o projeto ja pagou caro para nao ter.

## Quem chama

So a borda (`src/app.py`). IP e identificador de requisicao sao HTTP, e o nucleo nao
conhece HTTP (`ADR-24`, `ADR-25`): levar a auditoria para dentro dos casos de uso obrigaria
a passar IP por parametro por toda a fronteira.
"""
from __future__ import annotations

import logging
import os

from utils.logs import LOGGER_DE_AUDITORIA, texto_seguro
from utils.validate import decompor_nome_armazenado

# Conjunto fechado. A linha de auditoria e lida por uma pessoa e comparada entre dias: acao
# escrita a mao em cada chamada faria a mesma coisa aparecer com dois nomes.
ACOES: frozenset[str] = frozenset({
    "enviar_gedcom", "substituir_csv", "aposentar", "analisar_dna", "buscar_caminho",
    "entrar", "sair",
})

# Os desfechos ja existem no dominio: `reenvio.NOVO/IDENTICO/SUBSTITUIDO` para o envio e
# `Desfecho` tres valores para a busca. Aqui entram tambem os dois do desfecho binario que
# a tela ja usa em `success=True/False`.
DESFECHOS: frozenset[str] = frozenset({
    "novo", "identico", "substituido",
    "sucesso", "falha",
    "resultado", "sem_resultado", "erro_de_entrada",
})

_log: logging.Logger = logging.getLogger(LOGGER_DE_AUDITORIA)


def registrar(acao: str, desfecho: str, referencia=None, contagens=None,
              ip=None, origem=None, conta=None) -> None:
    """Escreve uma linha na trilha de auditoria.

    Nunca levanta excecao: auditoria que derruba a operacao que ela audita seria pior do
    que auditoria ausente. Valor fora dos conjuntos fechados vira aviso e a linha sai
    mesmo assim — perder o registro e o unico desfecho inaceitavel.

    `conta` e o identificador da conta autenticada (`sub`), nunca o e-mail: a linha
    sobrevive a requisicao, e o e-mail e dado pessoal (`RN-12`). Quando ele nao vem,
    a linha sai exatamente como antes da feature 051.
    """
    linha_de_conta = ""
    if conta:
        linha_de_conta = f" conta={texto_seguro(conta)}"
    _log.info(
        "acao=%s desfecho=%s arquivo=%s ip=%s origem=%s%s%s",
        _do_conjunto(acao, ACOES, "acao"),
        _do_conjunto(desfecho, DESFECHOS, "desfecho"),
        _arquivo(referencia),
        texto_seguro(ip) or "-",
        texto_seguro(origem) or "-",
        _contagens(contagens),
        linha_de_conta,
    )


def _do_conjunto(valor, permitidos: frozenset[str], campo: str) -> str:
    """Sanitiza e confere o valor; fora do conjunto, avisa e escreve `desconhecido`."""
    limpo: str = texto_seguro(valor).strip()
    if limpo in permitidos:
        return limpo
    logging.getLogger(__name__).warning(
        "%s de auditoria fora do conjunto fechado: %r", campo, limpo
    )
    return "desconhecido"


def _arquivo(referencia) -> str:
    """`<chave><extensao>` — ou `-` quando a referencia nao tem chave.

    A extensao vem do nome visivel, e o nome visivel **nao** e escrito: e dele que sai o
    sufixo, e nada mais.
    """
    if not referencia:
        return "-"
    chave, visivel = decompor_nome_armazenado(referencia)
    extensao: str = os.path.splitext(visivel)[1].lower()
    if not chave:
        # Arquivo sem chave e um fato do legado (`TM-02`), nao um erro: a linha registra que
        # ele nao tem chave e segue, porque o operador consegue aposentar esses arquivos.
        return f"sem-chave{extensao}"
    return f"{chave}{extensao}"


def _contagens(contagens) -> str:
    """` nome=valor ...` com numeros inteiros apenas; texto nao entra por este caminho."""
    if not contagens:
        return ""
    pares: list[str] = []
    for nome, valor in contagens.items():
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            continue
        pares.append(f"{texto_seguro(nome)}={numero}")
    return (" " + " ".join(pares)) if pares else ""


__all__: list[str] = ["ACOES", "DESFECHOS", "registrar"]
