"""Publica o mini-site do Reversa em `docs/`, aplicando os ajustes de publicacao.

## O problema que este script resolve, e como ele foi medido

`docs/` e a pasta publicada pelo GitHub Pages, e ela **espelha** `_reversa_docs/`. So que ela
**nao e copia fiel**: em 2026-10-10 a comparacao byte a byte mostrou que os **10 HTMLs** de `docs/`
diferem do gerado, sempre nos mesmos quatro pontos. O diff, medido arquivo por arquivo:

    1. <title>X — analisador-genealogico</title>   ->  <title>X — Analisador Genealogico</title>
    2. <link rel="icon" ... sizes="64x64" logo-mini.png>
                                                   ->  sizes="512x512" logo.png
                                                       + <link rel="apple-touch-icon" ...>
    3. <span class="brand">analisador-genealogico</span>  ->  ... Analisador Genealogico ...
    4. <h1>analisador-genealogico</h1>             ->  <h1>Analisador Genealogico</h1>

O item 4 so aparece em `index.html` e `deck.html`; os outros tres, em todos.

**Isso e um passo manual, e nada o registrava.** A consequencia medida: rodar `/reversa-docs` e
copiar o resultado para `docs/` **regride o site publicado** para os nomes em slug e perde o
`apple-touch-icon` — o pipeline nao sabe desses ajustes, e nao ha onde ele os aprenda.

## O que este script faz, e o que ele NAO faz

Faz: copia `_reversa_docs/` para `docs/` e aplica as quatro transformacoes em todo `*.html`, mais o
`apple-touch-icon` do app (que e byte a byte o mesmo arquivo de `src/assets/`). Nao toca em
`_reversa_docs/`: o gerado continua sendo a saida crua do pipeline.

**Nao apaga nada.** Arquivo que exista em `docs/` e nao em `_reversa_docs/` e preservado — e ha um
caso real: `docs/assets/img/banner-analisador.png` e a **fonte canonica da arte do topo** do app, que
mora ali por convencao do projeto, e nao um ativo do mini-site.

## Como usar

    .venv\\Scripts\\python.exe publicar_docs.py --conferir   # so compara, nao escreve
    .venv\\Scripts\\python.exe publicar_docs.py              # publica

`--conferir` e o modo que PROVA o script: ele monta o resultado em memoria e compara com `docs/`
byte a byte. Enquanto ele disser `identico`, este script reproduz a publicacao exatamente.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
GERADO = os.path.join(RAIZ, "_reversa_docs")
PUBLICADO = os.path.join(RAIZ, "docs")

# O icone de atalho do mini-site e o MESMO arquivo do app. A origem e a unica: `src/assets/`.
ICONE_DE_ATALHO = os.path.join(RAIZ, "src", "assets", "apple-touch-icon.png")
DESTINO_DO_ICONE = os.path.join(PUBLICADO, "assets", "img", "apple-touch-icon.png")

# As quatro transformacoes. Elas sao aplicadas LINHA A LINHA, e nao com regex `re.M`: os arquivos
# do mini-site sao **CRLF**, e com `re.M` o `$` casa antes do `\n`, de modo que o `\r` fica dentro
# da linha e `>[ \t]*$` NUNCA casa. Foi o defeito da primeira versao deste script, medido: nenhuma
# das quatro transformacoes era aplicada, e a publicacao saia 72 bytes menor por arquivo.
ICONE = re.compile(
    r'^(?P<recuo>[ \t]*)<link rel="icon" type="image/png" sizes="64x64" '
    r'href="(?P<base>(?:\.\./)*)assets/img/logo-mini\.png">[ \t]*$'
)

# O nome do projeto no gerado e o SLUG; no publicado e o nome humano.
SLUG = "analisador-genealogico"
NOME = "Analisador Geneal\u00f3gico"

# Os tres contextos em que o slug vira nome humano: o titulo de cada pagina, a marca do topo e o
# `h1`. Fora deles o slug nao e tocado.
CONTEXTOS = ("<title>", '<span class="brand">', "<h1>")

# O rotulo humano de cada pagina de feature. **Isto e CURADORIA, e nao derivacao** — medido: o
# `_reversa_docs/assets/js/data.js` traz `"Analise de DNA e confronto"` e
# `"Busca de caminho genealogico"`, sem acento e mais longos, enquanto o publicado tem
# `Analise de DNA` e `Busca de caminho genealogico` COM acento. Nao ha de onde derivar: o script
# declara. Feature nova que nao esteja aqui e publicada com o proprio slug, e o modo `--conferir`
# acusa a diferenca antes de qualquer escrita.
ROTULOS_DE_FEATURE = {
    "upload-gedcom": "Upload e parsing de GEDCOM",
    "analise-dna": "An\u00e1lise de DNA",
    "busca-caminho": "Busca de caminho geneal\u00f3gico",
    "tela-de-entrada": "Tela de entrada",
    "recursos-da-tela": "Artes da tela",
}

# Artefatos de INSTRUMENTO do Publisher, e nao conteudo do site: ficam em `_reversa_docs/` e nao
# sao publicados. Medido na conferencia: sao exatamente estes dois, e sao ocultos.
NAO_PUBLICAR = {".links-result.json", ".smoke-result.json"}


def _slug_da_feature(rel: str) -> str | None:
    """O slug da feature quando a pagina e `features/<slug>.html`, senao `None`."""
    partes = rel.replace("\\", "/").split("/")
    if len(partes) == 2 and partes[0] == "features" and partes[1].endswith(".html"):
        return partes[1][:-5]
    return None


def _transformar_linha(linha: str, rel: str) -> list[str]:
    """Uma linha vira uma ou duas, com o terminador preservado (`\\n` ou `\\r\\n`)."""
    fim = ""
    corpo = linha
    if corpo.endswith("\r\n"):
        corpo, fim = corpo[:-2], "\r\n"
    elif corpo.endswith("\n"):
        corpo, fim = corpo[:-1], "\n"

    achado = ICONE.match(corpo)
    if achado:
        recuo, base = achado.group("recuo"), achado.group("base")
        return [
            f'{recuo}<link rel="icon" type="image/png" sizes="512x512" '
            f'href="{base}assets/img/logo.png">{fim}',
            f'{recuo}<link rel="apple-touch-icon" '
            f'href="{base}assets/img/apple-touch-icon.png">{fim}',
        ]

    # So nos tres contextos, e nunca no arquivo inteiro: uma troca cega do slug poderia alcancar
    # caminho, `id` ou chave de dado.
    if any(c in corpo for c in CONTEXTOS):
        feature = _slug_da_feature(rel)
        if feature:
            # O PRIMEIRO slug da linha e o da feature; o que sobra e o do projeto, no fim do
            # `<title>`. A ordem importa: `upload-gedcom` nao contem `analisador-genealogico`.
            corpo = corpo.replace(feature, ROTULOS_DE_FEATURE.get(feature, feature), 1)
        corpo = corpo.replace(SLUG, NOME)
    return [corpo + fim]


def transformar(rel: str, texto: str) -> str:
    """Transforma o conteudo de UM arquivo, identificado pelo caminho RELATIVO a `_reversa_docs/`.

    O caminho e relativo de proposito, e nao absoluto: `_slug_da_feature` o divide em partes para
    reconhecer `features/<slug>.html`, e com um caminho absoluto essa divisao nunca da dois
    elementos — foi o defeito medido na primeira versao, em que o rotulo curado da feature nao era
    aplicado e as tres paginas de feature divergiam.
    """
    saida = []
    for linha in texto.splitlines(keepends=True):
        saida.extend(_transformar_linha(linha, rel))
    return "".join(saida)


def _relativos(base: str) -> list[str]:
    """Todos os arquivos sob `base`, MENOS os que a publicacao nao leva.

    `os.walk` e nao `glob`: a primeira medicao deste trabalho usou `glob("**/*")`, que **nao lista
    arquivo oculto**, e por isso os dois `.json` do Publisher nao apareceram na comparacao. O
    script os encontrou, e a diferenca era real.
    """
    saida = []
    for raiz, _dirs, arquivos in os.walk(base):
        for a in arquivos:
            if a in NAO_PUBLICAR:
                continue
            saida.append(os.path.relpath(os.path.join(raiz, a), base))
    return sorted(saida)


def montar() -> dict[str, bytes]:
    """O que a publicacao produziria, em memoria. Nao escreve nada."""
    resultado: dict[str, bytes] = {}
    for rel in _relativos(GERADO):
        origem = os.path.join(GERADO, rel)
        dados = io.open(origem, "rb").read()
        if rel.endswith(".html"):
            texto = dados.decode("utf-8")
            # `rel`, e nao `origem`: ver a nota em `transformar`.
            dados = transformar(rel, texto).encode("utf-8")
        resultado[rel] = dados
    if os.path.isfile(ICONE_DE_ATALHO):
        resultado[os.path.relpath(DESTINO_DO_ICONE, PUBLICADO)] = io.open(ICONE_DE_ATALHO, "rb").read()
    return resultado


def conferir() -> int:
    esperado = montar()
    problemas = []
    for rel, dados in sorted(esperado.items()):
        destino = os.path.join(PUBLICADO, rel)
        if not os.path.isfile(destino):
            problemas.append(f"AUSENTE em docs/: {rel}")
            continue
        atual = io.open(destino, "rb").read()
        if atual != dados:
            problemas.append(f"DIVERGE: {rel} ({len(atual)} b em docs/, {len(dados)} b no esperado)")
    for rel in _relativos(PUBLICADO):
        if rel not in esperado:
            print(f"  preservado (nao vem do gerado): {rel}")
    if problemas:
        print("RESULTADO: o script NAO reproduz docs/ hoje:")
        for p in problemas:
            print("  -", p)
        return 1
    print(f"RESULTADO: identico. Os {len(esperado)} arquivos de docs/ sao exatamente o que este script produz.")
    return 0


def publicar() -> int:
    esperado = montar()
    escritos = 0
    for rel, dados in sorted(esperado.items()):
        destino = os.path.join(PUBLICADO, rel)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        if os.path.isfile(destino) and io.open(destino, "rb").read() == dados:
            continue
        with io.open(destino, "wb") as fh:
            fh.write(dados)
        escritos += 1
    print(f"publicado: {escritos} arquivo(s) escrito(s) de {len(esperado)}, em {PUBLICADO}")
    print("  nada foi apagado: os arquivos que nao vem do gerado continuam onde estavam")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Publica _reversa_docs/ em docs/ com os ajustes de publicacao.")
    p.add_argument("--conferir", action="store_true",
                   help="nao escreve: compara o que seria produzido com o que esta em docs/")
    args = p.parse_args()
    if not os.path.isdir(GERADO):
        print(f"nao existe {GERADO}: nada a publicar")
        return 2
    return conferir() if args.conferir else publicar()


if __name__ == "__main__":
    raise SystemExit(main())
