"""Aplicador de diff unificado, com modo de reversao.

Existe por dois motivos:

1. Cumprir a invariante do registro de refactor: "toda transformacao aplicada e
   revertivel pelo diff guardado". Este script torna essa promessa mecanica em
   vez de declarativa.
2. Reverter com precisao a aplicacao da OPP-20261003-TWNT, que ficou vermelha na
   rede de seguranca, sem depender de `git checkout` (que desfaria tambem as
   mudancas da feature 003, ainda nao commitadas).

Uso:
    python aplicar-diff.py --reverter <pasta-dos-CHG>

Posicionamento: cada trecho e localizado pela linha do lado NOVO (`+c`), porque e
esse lado que existe no arquivo atual. A primeira versao usava a linha do lado
antigo e errava o deslocamento em arquivos com mais de um trecho.

Idempotencia: se o trecho nao casar com o lado novo mas o lado antigo estiver
presente, o arquivo e tratado como ja revertido e a execucao segue. Qualquer outro
caso aborta sem escrever.
"""
from __future__ import annotations

import pathlib
import re
import sys

CABECALHO = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class JaRevertido(Exception):
    pass


def ler_hunks(texto):
    """Devolve [(inicio_antigo, inicio_novo, linhas_antigas, linhas_novas)]."""
    hunks = []
    atual = None
    for linha in texto.split("\n"):
        if linha.startswith("---") or linha.startswith("+++"):
            continue
        m = CABECALHO.match(linha)
        if m:
            if atual:
                hunks.append(atual)
            atual = [int(m.group(1)), int(m.group(3)), [], []]
            continue
        if atual is None or not linha:
            continue
        marca, conteudo = linha[0], linha[1:]
        if marca == "-":
            atual[2].append(conteudo)
        elif marca == "+":
            atual[3].append(conteudo)
        elif marca == " ":
            atual[2].append(conteudo)
            atual[3].append(conteudo)
    if atual:
        hunks.append(atual)
    return hunks


def caminho_alvo(texto):
    for linha in texto.split("\n"):
        if linha.startswith("+++ b/"):
            return linha[6:].strip()
    raise SystemExit("ABORTADO: nao encontrei o caminho de destino no diff")


def ja_esta_no_lado_antigo(texto_atual, hunks):
    """True se todas as linhas do lado antigo aparecem, em ordem, no arquivo."""
    pos = 0
    for _a, _c, orig, _novo in hunks:
        for linha in orig:
            achou = texto_atual.find(linha, pos)
            if achou < 0:
                return False
            pos = achou + len(linha)
    return True


def reverter_arquivo(caminho, texto_diff):
    hunks = ler_hunks(texto_diff)
    p = pathlib.Path(caminho)
    if p.exists():
        atual = p.read_text(encoding="utf-8").split("\n")
        if atual and atual[-1] == "":
            atual = atual[:-1]
    else:
        atual = []
    texto_atual = "\n".join(atual)

    # Caso do diff que apenas removia o arquivo: o hunk tem lado novo vazio, e
    # reverter significa recriar o arquivo com o lado antigo. Se o arquivo ja
    # TEM exatamente esse conteudo, ja foi revertido. Sem esta guarda o algoritmo
    # anexava o conteudo atual depois do antigo e duplicava o arquivo.
    if len(hunks) == 1 and not hunks[0][3] and atual == hunks[0][2]:
        raise JaRevertido()

    saida = []
    cursor = 0
    for _a, c, orig, novo in hunks:
        alvo = c - 1  # posicao no arquivo ATUAL
        if alvo > cursor:
            saida.extend(atual[cursor:alvo])
            cursor = alvo
        janela = atual[cursor:cursor + len(novo)]
        if janela != novo:
            if ja_esta_no_lado_antigo(texto_atual, hunks):
                raise JaRevertido()
            raise SystemExit(
                "ABORTADO: %s nao casa com o lado + do diff na linha %d.\n"
                "  esperado : %r\n  encontrado: %r" % (caminho, c, novo[:3], janela[:3])
            )
        cursor += len(novo)
        saida.extend(orig)

    saida.extend(atual[cursor:])
    novo_texto = "\n".join(saida)
    if novo_texto and not novo_texto.endswith("\n"):
        novo_texto += "\n"

    if not saida:
        if p.exists():
            p.unlink()
            return "removido"
        return "ja ausente"
    p.write_text(novo_texto, encoding="utf-8", newline="")
    return "restaurado"


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--reverter":
        raise SystemExit(__doc__)
    pasta = pathlib.Path(sys.argv[2])
    arquivos = sorted(pasta.glob("CHG-*.diff"))
    if not arquivos:
        raise SystemExit("ABORTADO: nenhum CHG-*.diff em %s" % pasta)

    feitos = []
    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8")
        caminho = caminho_alvo(texto)
        try:
            situacao = reverter_arquivo(caminho, texto)
        except JaRevertido:
            situacao = "ja revertido"
        feitos.append((situacao, caminho))

    for situacao, caminho in feitos:
        print("   %-14s %s" % (situacao, caminho))
    print()
    print("arquivos processados = %d" % len(feitos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
