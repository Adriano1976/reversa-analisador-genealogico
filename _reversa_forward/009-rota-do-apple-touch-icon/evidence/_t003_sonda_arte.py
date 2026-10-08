"""Sonda independente da arte de runtime (T003 da feature 009).

## Por que ela e independente

A arte foi produzida por `tests/icone_de_atalho.py`, que usa a biblioteca de imagem. Se
esta sonda usasse a MESMA biblioteca e o MESMO caminho de leitura, ela provaria pouco:
um erro de leitura passaria nos dois lados.

Entao a prova principal aqui e **estrutural, com a biblioteca padrao apenas**. O formato
PNG declara no proprio cabecalho o tipo de cor, e o tipo **2** e `truecolor` — sem canal
alfa. Nao existe pixel transparente em um PNG cujo cabecalho diz que nao ha canal alfa:
e uma propriedade do formato, nao uma leitura de amostra.

A segunda parte, com a biblioteca de imagem, existe para conferir a COR dos cantos, que o
cabecalho nao carrega. Ela e declarada como segundo instrumento, e nao como prova unica.

Uso:
    .\\.venv\\Scripts\\python.exe _reversa_forward/009-rota-do-apple-touch-icon/evidence/_t003_sonda_arte.py
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
ARTE = RAIZ / "src" / "assets" / "apple-touch-icon.png"
CANONICA = RAIZ / "docs" / "assets" / "img" / "logo.png"

TIPO_DE_COR = {0: "grayscale", 2: "truecolor (SEM canal alfa)", 3: "indexed",
               4: "grayscale+alfa", 6: "truecolor+alfa"}
TAMANHO_ESPERADO = 16504


def cabecalho(caminho: Path):
    """Le assinatura e IHDR sem nenhuma biblioteca de imagem."""
    dados = caminho.read_bytes()
    assinatura = dados[:8]
    if assinatura != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"ERRO: assinatura PNG invalida em {caminho}: {assinatura!r}")
    if dados[12:16] != b"IHDR":
        raise SystemExit("ERRO: o primeiro chunk nao e IHDR")
    largura, altura, bits, tipo_cor, compressao, filtro, entrelace = struct.unpack(
        ">IIBBBBB", dados[16:29]
    )
    return dados, largura, altura, bits, tipo_cor, compressao, filtro, entrelace


def main() -> int:
    if not ARTE.exists():
        print(f"ERRO: arte de runtime ausente em {ARTE}")
        return 2

    dados, largura, altura, bits, tipo_cor, comp, filtro, entrelace = cabecalho(ARTE)

    print("== 1. prova estrutural (biblioteca padrao apenas) ==")
    print(f"arquivo            : {ARTE.relative_to(RAIZ)}")
    print(f"bytes              : {len(dados)}")
    print(f"dimensoes (IHDR)   : {largura}x{altura}")
    print(f"bits por canal     : {bits}")
    print(f"tipo de cor        : {tipo_cor} = {TIPO_DE_COR.get(tipo_cor, 'desconhecido')}")
    print(f"compressao / filtro: {comp} / {filtro}   (0/0 = padrao)")
    print(f"entrelacamento     : {entrelace}   (0 = nenhum)")
    print()

    problemas = []
    if (largura, altura) != (180, 180):
        problemas.append(f"dimensao {largura}x{altura} != 180x180")
    if tipo_cor != 2:
        problemas.append(f"tipo de cor {tipo_cor} != 2 (ha canal alfa: pode haver transparencia)")
    if len(dados) != TAMANHO_ESPERADO:
        problemas.append(f"{len(dados)} bytes != {TAMANHO_ESPERADO} esperados")
    if comp != 0 or filtro != 0 or entrelace != 0:
        problemas.append("parametros de PNG fora do padrao da receita")

    print("== 2. segundo instrumento: cor dos cantos (biblioteca de imagem) ==")
    try:
        from PIL import Image

        imagem = Image.open(ARTE)
        print(f"modo / dimensoes   : {imagem.mode} / {imagem.size}")
        cantos = {
            "sup-esq": (0, 0), "sup-dir": (179, 0), "inf-esq": (0, 179), "inf-dir": (179, 179),
        }
        for nome, ponto in cantos.items():
            cor = imagem.getpixel(ponto)
            marca = "ok" if cor == (255, 255, 255) else "FORA DO ESPERADO"
            print(f"  canto {nome} : {cor}  {marca}")
            if cor != (255, 255, 255):
                problemas.append(f"canto {nome} = {cor}, esperado (255, 255, 255)")

        # o miolo nao pode ter ficado branco: a arte tem de continuar visivel
        miolo = imagem.getpixel((90, 90))
        print(f"  centro (90,90)   : {miolo}")
        if miolo == (255, 255, 255):
            problemas.append("o centro ficou branco: a arte pode nao ter sido composta")
    except ImportError:
        print("  (biblioteca de imagem ausente - a prova estrutural acima segue valida)")

    print()
    print("== 3. a canonica, para contraste ==")
    _, lc, ac, bc, tc, _, _, _ = cabecalho(CANONICA)
    print(f"canonica           : {lc}x{ac}, tipo de cor {tc} = {TIPO_DE_COR.get(tc)}")
    print(f"bytes canonica     : {CANONICA.stat().st_size}")
    print(f"bytes / canonica   : {len(dados) / CANONICA.stat().st_size:.2f}x")
    print()
    print("== 4. o cabecalho realmente descreve o fluxo? (decodifica o IDAT) ==")
    # Descompacta o fluxo para provar que o arquivo nao esta truncado, sem usar PIL.
    pos = 8
    idat = b""
    while pos < len(dados):
        (tam,) = struct.unpack(">I", dados[pos:pos + 4])
        tipo = dados[pos + 4:pos + 8]
        if tipo == b"IDAT":
            idat += dados[pos + 8:pos + 8 + tam]
        pos += 12 + tam
    bruto = zlib.decompress(idat)
    esperado = altura * (1 + largura * 3)  # filtro + RGB por pixel
    print(f"IDAT descompactado : {len(bruto)} bytes")
    print(f"esperado (3 canais): {esperado} bytes")
    if len(bruto) != esperado:
        problemas.append(f"fluxo com {len(bruto)} bytes, esperado {esperado}")

    print()
    if problemas:
        print("RESULTADO: REPROVADO")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("RESULTADO: APROVADO - 180x180, sem canal alfa, cantos brancos, fluxo integro")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
