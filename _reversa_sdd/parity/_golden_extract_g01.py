"""Extrai o golden da mensagem de SUCESSO (SCR-G01) a partir do golden do hub (SCR-002).

## Por que extrair em vez de recapturar

O manifesto descreve SCR-G01 como "capturado como parte de SCR-002 ou SCR-005" — nao
existe requisicao propria que produza so a mensagem de sucesso. Recapturar o hub daria
byte a byte o mesmo documento de SCR-002, e o golden perderia a utilidade: o que o
codificador precisa e a REGIAO da mensagem, isolada, nao o hub inteiro de novo.

Entao este script recorta o bloco de alerta do documento ja capturado. O resultado e
um golden menor, focado e verificavel: a regiao exata que a paridade deve comparar.

## Normalizacao

Aplica as regras de `normalizationRules` do manifesto que fazem sentido para um recorte
de uma linha de HTML (lineEndings=LF, trimTrailingSpaces) e nada alem — nenhuma regra
deve ser aplicada aqui que tambem nao seja aplicada na comparacao futura, senao o
golden e a comparacao divergem por construcao.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GOLDEN = os.path.join(ROOT, "_reversa_sdd", "screens", "golden")
FONTE = os.path.join(GOLDEN, "SCR-002-loaded-hub.html.txt")
DESTINO = os.path.join(GOLDEN, "SCR-G01-alert-success.html.txt")


def main() -> int:
    txt = open(FONTE, encoding="utf-8").read()
    # Recorta o bloco de alerta completo: do <div class="alert alert-success...> ate o
    # </div> que fecha, incluindo o botao de dismiss.
    # NAO ancorar com `^` + re.M: o <div> e indentado por 4 espacos no template, entao a
    # ancora de inicio de linha nunca casa (erro que custou uma rodada).
    m = re.search(r'(?s)(<div class="alert alert-success.*?</div>)', txt)
    if not m:
        print("ERRO: bloco de alerta de sucesso nao encontrado em %s" % os.path.basename(FONTE))
        return 1
    bloco = m.group(1).replace("\r\n", "\n").rstrip()
    # Normaliza a indentacao. O template legado mistura TABS e espacos nessa regiao
    # (registrado no proprio manifest: normalizationRules.trimTrailingSpaces, DEV-010),
    # entao a indentacao crua e acidental e nao sobrevive a comparacao. Padronizar aqui
    # evita que o golden carregue um artefato de formatacao que a comparacao vai remover.
    bloco = "\n".join(ln.strip() for ln in bloco.split("\n"))
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(bloco + "\n")
    h = hashlib.sha256(open(DESTINO, "rb").read()).hexdigest()
    print("=" * 74)
    print("SCR-G01 EXTRAIDO de %s" % os.path.basename(FONTE))
    print("=" * 74)
    print("  arquivo : %s" % os.path.basename(DESTINO))
    print("  bytes   : %d" % len(bloco.encode("utf-8")))
    print("  sha256  : %s" % h)
    print("  conteudo:")
    for linha in bloco.split("\n"):
        print("    " + linha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
