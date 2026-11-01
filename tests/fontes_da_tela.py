"""Receita da folha de fontes da tela (feature 054, `D-05` e `D-14`).

## Por que uma receita, e nao um CSS escrito a mao

A tela usa duas familias do Google Fonts: `Cormorant Garamond` (500, 600 e 700) e
`Manrope` (400, 500, 600, 700 e 800). O CSS que o Google serve traz **45 blocos
`@font-face`** que apontam para apenas **11 arquivos `woff2`**, porque as duas familias
sao **variaveis**: cada bloco declara uma faixa de pesos e o mesmo arquivo cobre a faixa
inteira. Cada arquivo e um **subconjunto** (`unicode-range`), e o navegador baixa so os
subconjuntos que a pagina usa.

Embutir as fontes e, portanto, reescrever as **11 URLs** de `fonts.gstatic.com` para
caminhos locais, preservando os blocos, as faixas de peso, os `unicode-range` e o
`font-display: swap`. Qualquer ajuste de peso no futuro vem de uma nova consulta ao
Google — por isso a transformacao mora aqui, e o derivado e commitado.

## Por que o derivado e commitado, e nao gerado em tempo de execucao

A aplicacao nao pode depender de rede para servir a propria tela — e o defeito que esta
feature fecha. E o `.dockerignore` e **lista de permissao**: so o que esta sob `src/`
entra na imagem, entao a receita roda no host e o resultado e versionado em
`src/assets/fontes.css` e `src/assets/fontes/`.

## Como regenerar

    .\\.venv\\Scripts\\python.exe -m tests.fontes_da_tela

O comando reescreve a folha e os `woff2`, imprime tamanho e `sha256` de cada arquivo, e
falha se a contagem de blocos ou de arquivos divergir do contrato. Ele **precisa de
rede**; o teste (`tests/test_fontes_da_tela.py`) confere so o derivado, sem rede.

## O que esta constante garante

`ARQUIVOS` e a autoridade sobre o conjunto: nome, tamanho e `sha256` de cada um dos 11
`woff2`. O teste compara o derivado com esta tabela, e a rota `/fontes/<arquivo>.woff2`
valida o nome contra ela — um arquivo fora deste conjunto responde `404`.
"""
from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

#: Pasta dos recursos servidos pela aplicacao.
ASSETS = RAIZ / "src" / "assets"

#: Pasta dos arquivos de fonte. Uma pasta propria porque sao 11 arquivos opacos.
FONTES = ASSETS / "fontes"

#: O endereco consultado. Os pesos sao os que a tela usa hoje (`RN-03`).
CSS_URL = (
    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700"
    "&family=Manrope:wght@400;500;600;700;800&display=swap"
)

#: Navegador moderno no `User-Agent`: sem isso o Google serve `ttf` em vez de `woff2`.
NAVEGADOR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

#: Cabecalho da folha derivada. **So ASCII**, porque o CSS nao declara `@charset` e o
#: arquivo nao deve depender de o leitor adivinhar a codificacao.
CABECALHO = (
    "/* Fontes da tela - derivadas do Google Fonts em 2026-10-31 e servidas pela aplicacao.\n"
    "   Fonte: " + CSS_URL + "\n"
    "   Cormorant Garamond (500, 600, 700) e Manrope (400, 500, 600, 700, 800), SIL Open Font License.\n"
    "   Gerado por tests/fontes_da_tela.py - nao editar a mao. */\n"
)

#: Quantos blocos `@font-face` o CSS de origem tem. Se o Google mudar, a receita falha
#: alto em vez de gerar um derivado diferente em silencio.
BLOCOS_ESPERADOS = 45

#: Os 11 subconjuntos, com tamanho e `sha256` medidos em 2026-10-31.
ARQUIVOS: dict[str, tuple[int, str]] = {
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYp3tKgS4.woff2": (
        33736, "cfa9a397d86f66c5c51775a2500a712d5f632a04f0c5eca6930dfaf612d4566d"),
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpHtKgS4.woff2": (
        23416, "a4d7cf345b8091e1d2c8c5c8fa3bd0f9bb9d00bc8988185471db398ddb5ae4c4"),
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYpntKgS4.woff2": (
        11220, "6252e819a7665ae512c2d046308a9016ada63c06d0d8f96984c4b29f6c9e1bd2"),
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYqXtK.woff2": (
        37640, "d80df8ff5aecd299a61549f9e29ab1ed0b9b05f4ea71d50fe978e07d5240b235"),
    "co3bmX5slCNuHLi8bLeY9MK7whWMhyjYrXtKgS4.woff2": (
        21168, "017fab69b4be8ffc08ca312823327989ade6dc3d948f0afa125e12ec2e5e7ca1"),
    "xn7gYHE41ni1AdIRggOxSuXd.woff2": (
        14352, "447c49583b1b735cc6f566151db1d24354cec41076c55dd98455cfbde9e806c1"),
    "xn7gYHE41ni1AdIRggSxSuXd.woff2": (
        9268, "e507c109c31789b33994646b457ee288639324516357250607c9b1398186e069"),
    "xn7gYHE41ni1AdIRggexSg.woff2": (
        24532, "8c2def024c1bf31aacf3624ae3c4d701269b4ec3dc765c04830839f0d36b2d9e"),
    "xn7gYHE41ni1AdIRggixSuXd.woff2": (
        8388, "dbf64d973b3987844df30992c93f47d24ac8935ee8c9b1e320942aeb1b367703"),
    "xn7gYHE41ni1AdIRggmxSuXd.woff2": (
        15160, "2f7335119075b2079f1d882530bbc18728461612bf90743203d73a74a48f4d9b"),
    "xn7gYHE41ni1AdIRggqxSuXd.woff2": (
        2588, "3c09135e88bbfcd848e99be137710afbb615a8d9a73c5c48e6cb0245a162af1d"),
}

#: A folha derivada, ao lado das artes e de `app.css`.
FOLHA = ASSETS / "fontes.css"

#: Regex dos enderecos de fonte no CSS de origem.
_URL_DE_FONTE = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)")


def baixar(url: str) -> bytes:
    """Baixa `url` como um navegador baixaria. So a receita chama isto."""
    pedido = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR})
    with urllib.request.urlopen(pedido, timeout=90) as resposta:
        return resposta.read()


def derivar() -> tuple[str, dict[str, bytes]]:
    """Consulta o Google, reescreve as 11 URLs e devolve `(css, {nome: bytes})`.

    Nao escreve nada em disco: quem escreve e o `main()`, para a derivacao poder ser
    testada isoladamente se algum dia isso fizer sentido.
    """
    css = baixar(CSS_URL).decode("utf-8")
    enderecos = sorted(set(_URL_DE_FONTE.findall(css)))
    if len(enderecos) != len(ARQUIVOS):
        raise RuntimeError(
            f"o CSS de origem aponta para {len(enderecos)} arquivos, e o contrato diz "
            f"{len(ARQUIVOS)}: o Google mudou os subconjuntos. Revise a receita."
        )
    arquivos: dict[str, bytes] = {}
    for endereco in enderecos:
        nome = endereco.rsplit("/", 1)[-1]
        dados = baixar(endereco)
        if nome not in ARQUIVOS:
            raise RuntimeError(
                f"o arquivo {nome!r} nao esta no contrato de ARQUIVOS: revise a receita."
            )
        arquivos[nome] = dados
        css = css.replace("url(" + endereco + ")", "url(/fontes/" + nome + ")")
    if css.count("@font-face") != BLOCOS_ESPERADOS:
        raise RuntimeError(
            f"o CSS de origem tem {css.count('@font-face')} blocos @font-face, e o contrato "
            f"diz {BLOCOS_ESPERADOS}: o Google mudou a folha."
        )
    return CABECALHO + css, arquivos


def main() -> int:
    """Regenera a folha e os `woff2`; imprime o que gravou. Codigo de saida 1 se divergir."""
    css, arquivos = derivar()
    FONTES.mkdir(parents=True, exist_ok=True)
    problemas: list[str] = []
    for nome, dados in sorted(arquivos.items()):
        tamanho, esperado = ARQUIVOS[nome]
        resumo = hashlib.sha256(dados).hexdigest()
        situacao = "ok" if (len(dados) == tamanho and resumo == esperado) else "DIVERGE"
        if situacao == "DIVERGE":
            problemas.append(nome)
        print(f"  {situacao:7} {nome} {len(dados)} {resumo[:16]}")
        (FONTES / nome).write_bytes(dados)
    if not css.isascii():
        problemas.append("fontes.css")
        print("  DIVERGE fontes.css nao e ASCII")
    FOLHA.write_bytes(css.encode("ascii"))
    print(
        f"  folha   {FOLHA.name} {len(css.encode('ascii'))} bytes, "
        f"{css.count('@font-face')} blocos, {len(arquivos)} arquivos de fonte"
    )
    if problemas:
        print("FALHOU: " + ", ".join(problemas))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
