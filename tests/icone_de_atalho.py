"""Receita de derivacao da arte do icone de atalho (`D-02`, feature 009).

## Por que este modulo existe

A arte que a rota serve **nao e** a arte canonica. Ela e uma **renderizacao derivada**:
a arte canonica (`docs/assets/img/logo.png`, 512x512, com transparencia) composta sobre
branco e reamostrada para 180x180. As tres transformacoes tem motivo medido:

1. **Compor sobre branco.** A arte tem 32,5 % de pixels totalmente transparentes e os
   quatro cantos em `(0, 0, 0, 0)`. O sistema movel compoe transparencia sobre PRETO no
   icone de atalho, entao servir a arte crua produziria um quadrado preto com o desenho
   por cima - incluindo as aberturas internas entre folhas e galhos (`RN-04`).
2. **180x180.** E o tamanho que o sistema espera; outra medida e reamostrada por ele e
   perde nitidez (`RF-02`).
3. **Cantos retos.** O sistema aplica a propria mascara arredondada. Arredondar aqui
   produziria arredondamento duplo, com um anel de fundo no canto (`RN-04`).

## Por que a arte e commitada, e nao gerada em tempo de execucao

A fonte canonica mora em `docs/`, e o `.dockerignore` deste projeto e **lista de
permissao**: so `requirements.txt` e `src/**` entram na imagem. Dentro do container
**nao existe fonte para gerar nada**. Gerar no host a cada partida seria I/O no import
de `src/app.py`, modulo que a suite e o harness de paridade importam.

Entao a arte derivada e **commitada** em `src/assets/apple-touch-icon.png`, e este modulo
e a **fonte unica da receita**: o teste de deriva (`tests/test_deriva_da_arte.py`) importa
`arte_derivada` daqui e compara com o arquivo commitado. Uma receita, um lugar.

## Como regenerar a arte

    .\\.venv\\Scripts\\python.exe -m tests.icone_de_atalho

O comando reescreve `src/assets/apple-touch-icon.png` e imprime tamanho e medidas. Ele so
precisa rodar quando a arte canonica mudar; o teste de deriva acusa quando isso acontecer
e ninguem regenerar.

## Dependencia

Usa a biblioteca de imagem que ja esta no `.venv/`. Ela **nao** entra em
`requirements.txt`, que e a lista de **runtime**: o container nao precisa dela, porque a
arte chega pronta dentro da imagem (`D-09`). O import e preguicoso, dentro das funcoes,
para que importar este modulo nao exija a biblioteca.
"""
from __future__ import annotations

import io
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

#: A fonte canonica. **Nao sai de `docs/`**: o mini-site publicado consome o mesmo
#: arquivo, e as duas copias servem a dois alvos de publicacao distintos (`RN-05`).
ARTE_CANONICA = RAIZ / "docs" / "assets" / "img" / "logo.png"

#: A arte de runtime. Dentro de `src/` porque e o unico caminho que entra na imagem.
ARTE_DE_RUNTIME = RAIZ / "src" / "assets" / "apple-touch-icon.png"

#: Lado do icone, em pixels (`RF-02`).
LADO = 180

#: Fundo opaco. Branco por contraste: a arte tem 51,5 % de creme em DUAS tonalidades
#: (`#f5efca` e `#f9eab0`), e eleger uma delas faria a outra pagina parecer errada.
FUNDO = (255, 255, 255, 255)

#: Tamanho do PNG derivado, medido da receita executada. Nao e decoracao: e a ancora que
#: denuncia reamostragem com outro filtro, fundo de outra cor ou compressao diferente.
#: E 21 % menor que os 20.954 bytes da mesma arte TRANSPARENTE, porque fundo branco
#: chapado comprime melhor.
TAMANHO_ESPERADO = 16504


def arte_derivada(caminho_canonico: Path = ARTE_CANONICA):
    """A imagem derivada, pronta para serializar. Nao escreve nada em disco.

    Funcao pura em relacao ao sistema de arquivos: le a canonica e devolve o objeto de
    imagem. E a **mesma** transformacao que produziu o arquivo commitado, e por isso o
    teste de deriva pode compara-la com ele.
    """
    from PIL import Image

    origem = Image.open(caminho_canonico).convert("RGBA")
    fundo = Image.new("RGBA", origem.size, FUNDO)
    opaca = Image.alpha_composite(fundo, origem).convert("RGB")
    return opaca.resize((LADO, LADO), Image.LANCZOS)


def bytes_da_arte(caminho_canonico: Path = ARTE_CANONICA) -> bytes:
    """Os bytes exatos do PNG derivado, com a compressao da receita."""
    buffer = io.BytesIO()
    arte_derivada(caminho_canonico).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def gravar_arte(
    caminho_destino: Path = ARTE_DE_RUNTIME,
    caminho_canonico: Path = ARTE_CANONICA,
) -> int:
    """Regenera a arte de runtime e devolve quantos bytes foram gravados."""
    conteudo = bytes_da_arte(caminho_canonico)
    caminho_destino.parent.mkdir(parents=True, exist_ok=True)
    caminho_destino.write_bytes(conteudo)
    return len(conteudo)


def _principal() -> int:
    origem = ARTE_CANONICA
    if not origem.exists():
        print(f"ERRO: arte canonica nao encontrada em {origem}")
        return 2
    gravados = gravar_arte()
    imagem = arte_derivada()
    alfa = imagem.convert("RGBA").getchannel("A").getextrema()
    cantos = [imagem.getpixel(p) for p in ((0, 0), (LADO - 1, 0), (0, LADO - 1), (LADO - 1, LADO - 1))]
    print(f"canonica : {origem} ({origem.stat().st_size} bytes)")
    print(f"destino  : {ARTE_DE_RUNTIME}")
    print(f"gravado  : {gravados} bytes (esperado {TAMANHO_ESPERADO})")
    print(f"dimensao : {imagem.size}")
    print(f"canal a  : {alfa}")
    print(f"cantos   : {cantos}")
    return 0 if gravados == TAMANHO_ESPERADO else 1


if __name__ == "__main__":
    raise SystemExit(_principal())
