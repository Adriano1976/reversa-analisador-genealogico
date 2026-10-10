"""Instrumento: os rotulos REAIS que a tela passa a mostrar, medidos na pasta do operador.

Feature `011-escolher-arquivo-da-lista`, emenda `RN-13` (formatacao do rotulo).

## Por que este instrumento existe

Os testes da `RN-13` usam nomes SINTETICOS, e isso e correto (Principio I): a pasta real do
operador nao entra em teste nenhum. Mas o pedido que originou a `RN-13` e sobre os nomes
REAIS, entao a verificacao no conteudo real precisa existir em algum lugar — e o lugar e
aqui, um instrumento de leitura, e nao uma assercao de suite.

## O que ele faz, e o que ele NAO faz

Le `src/uploads` e imprime, para cada aba, o rotulo ANTES e DEPOIS da formatacao. **Nao
escreve, nao renomeia e nao abre conteudo** — so `os.stat`, exatamente como o adaptador.

## Como rodar

    .venv\\Scripts\\python.exe _reversa_forward/011-escolher-arquivo-da-lista/evidence/_rotulos_reais.py
"""
from __future__ import annotations

import os
import re
import sys

# As duas formas que o rotulo NAO pode conter: chave de conteudo (16 hexadecimais) e simbolo
# de nome de arquivo (`_`, `-`, `.`). Sao as duas metades da `RN-13`, e as duas sao medidas
# sobre o rotulo FINAL.
_HEX16 = re.compile(r"[0-9a-f]{16}")
_SIMBOLO_NO_ROTULO = re.compile(r"[_\-.]")


def _raiz_do_projeto(inicio: str) -> str:
    """Sobe ate achar `src/uploads`, sem depender da profundidade de quem chamou.

    A primeira versao dos instrumentos desta feature cravava `parents[3]`, e quebrou quando
    foi copiada para dentro de `_reversa_bugs/`. A busca por marcador nao tem esse defeito.
    """
    atual = os.path.abspath(inicio)
    while True:
        if os.path.isdir(os.path.join(atual, "src", "uploads")):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:
            raise SystemExit("nao achei a raiz do projeto (src/uploads) a partir de " + inicio)
        atual = pai


RAIZ = _raiz_do_projeto(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from ports import EntradaArmazenada  # noqa: E402
from reporting.lista_de_arquivos import itens_da_aba, rotulo_limpo  # noqa: E402
from utils.validate import decompor_nome_armazenado  # noqa: E402

PASTA = os.path.join(RAIZ, "src", "uploads")


def _entradas():
    """As MESMAS entradas que o adaptador produz: nome, bytes e data. Sem ler conteudo."""
    itens = []
    for entrada in sorted(os.scandir(PASTA), key=lambda e: e.name):
        if not entrada.is_file():
            continue
        info = entrada.stat()
        itens.append(EntradaArmazenada(
            nome=entrada.name, bytes=info.st_size, modificado_em=info.st_mtime,
        ))
    return itens


def _aba(entradas, extensao: str, titulo: str) -> None:
    itens = itens_da_aba(entradas, extensao)
    print()
    print("=" * 78)
    print(f"{titulo}  (extensao {extensao}) -- {len(itens)} itens")
    print("=" * 78)
    if not itens:
        print("  (nenhum)")
        return
    for item in itens:
        _, visivel = decompor_nome_armazenado(item.nome_armazenado)
        marca = "OK " if item.disponivel else "NAO"
        contagem = f" x{item.quantidade}" if item.quantidade > 1 else ""
        print(f"  [{marca}]{contagem} {visivel!r}")
        print(f"         antes -> {visivel}")
        print(f"         tela  -> {item.nome_exibido!r}")


def main() -> int:
    entradas = _entradas()
    print(f"pasta: {PASTA}")
    print(f"arquivos no disco: {len(entradas)}")
    _aba(entradas, ".ged", "ABA: Buscar Conexao no GEDCOM")
    _aba(entradas, ".csv", "ABA: Analisador de DNA")

    print()
    print("=" * 78)
    print("CONFERENCIA: o rotulo nao pode ser vazio, e nao pode carregar chave")
    print("=" * 78)
    problemas = 0
    todas = itens_da_aba(entradas, ".ged") + itens_da_aba(entradas, ".csv")
    for item in todas:
        if not item.nome_exibido.strip():
            print(f"  VAZIO: {item.nome_armazenado!r}")
            problemas += 1
        # A checagem e sobre o ROTULO FINAL, e nao sobre uma recontagem a partir do nome
        # armazenado. A primeira versao deste instrumento recalculava o rotulo com um unico
        # `decompor_nome_armazenado` e acusava o arquivo de chave DUPLA
        # (`080e...__080e...__Arvore...`) como divergente -- mas o rotulo dele e resolvido
        # pelo GRUPO (`_rotulo_do_grupo`), que descarta o nome visivel ainda chaveado. O item
        # estava certo e o instrumento e que estava ingenuo. Este e o defeito que a checagem
        # reconstruida nao repete.
        if _HEX16.search(item.nome_exibido):
            print(f"  CHAVE VAZADA: {item.nome_armazenado!r} -> {item.nome_exibido!r}")
            problemas += 1
        if _SIMBOLO_NO_ROTULO.search(item.nome_exibido):
            print(f"  SIMBOLO RESTOU: {item.nome_armazenado!r} -> {item.nome_exibido!r}")
            problemas += 1
    print(f"  problemas encontrados: {problemas}")

    # Os nomes que o operador mais reconhece, lado a lado, para conferencia visual.
    print()
    print("=" * 78)
    print("OS NOMES REAIS DA PASTA, FORMATADOS")
    print("=" * 78)
    vistos = set()
    for entrada in entradas:
        _, visivel = decompor_nome_armazenado(entrada.nome)
        # Nome visivel que AINDA comeca com chave e o caso de reenvio duplo: o rotulo dele nao
        # sai daqui, sai do grupo, e por isso ele nao entra nesta listagem.
        if visivel in vistos or _HEX16.match(visivel):
            continue
        vistos.add(visivel)
        print(f"  {visivel}")
        print(f"      -> {rotulo_limpo(visivel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
