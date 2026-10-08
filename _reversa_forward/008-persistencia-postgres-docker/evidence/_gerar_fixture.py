"""Gera fixtures sinteticos de tamanho controlado (`T026`).

## Por que isto existe

O `T026` mediu `8,14x` e o parecia defeito de desempenho da persistencia. Nao era: o
fixture tinha cinco pessoas, a analise levava **5,1 ms**, e qualquer trabalho de banco
maior que isso "dobra" o tempo. O criterio do RNF — "a gravacao nao pode dobrar o tempo
da analise" — fala da analise REAL, de 71 conexoes sobre uma arvore de 35.460 pessoas.

Medir com o dado real e proibido pelo Principio I. **Gerar um equivalente sintetico nao
e.** Este script gera arvores do tamanho que se quiser, com descendentes da raiz — para
que os caminhos documentais existam — e um CSV de matches com nomes que o matching aceita
por construcao (nome do CSV igual ao nome de exibicao no GEDCOM).

Rodado no host, sem Docker: gera os arquivos para o `_t026_medir_custo.py` consumir.
"""
import io
import os
import sys

FILHOS_POR_CASAL = 3


def gerar(geracoes: int, n_matches: int) -> tuple[str, str]:
    """Devolve `(gedcom, csv)` sinteticos com descendentes da raiz."""
    individuos: dict[str, dict] = {}
    ordem: list[str] = []
    familias: list[tuple[str, str, str, list[str]]] = []
    contador = [0]

    def xid() -> str:
        contador[0] += 1
        return "@I%d@" % contador[0]

    def pessoa(nome: str, sexo: str, famc: str | None = None) -> str:
        x = xid()
        individuos[x] = {"nome": nome, "sexo": sexo, "famc": famc, "fams": []}
        ordem.append(x)
        return x

    raiz = pessoa("Raiz Queiroz", "M")
    conjuge = pessoa("Conjuge Primeira Queiroz", "F")
    casais = [(raiz, conjuge)]
    descendentes: list[str] = []

    for _ in range(geracoes):
        proximos = []
        for husb, wife in casais:
            fid = "@F%d@" % (len(familias) + 1)
            individuos[husb]["fams"].append(fid)
            individuos[wife]["fams"].append(fid)
            filhos = []
            for k in range(FILHOS_POR_CASAL):
                sexo = "M" if k % 2 == 0 else "F"
                filho = pessoa("Pessoa%05d Queiroz" % (contador[0] + 1), sexo, fid)
                filhos.append(filho)
                descendentes.append(filho)
                conj = pessoa("Conjuge%05d Queiroz" % (contador[0] + 1),
                              "F" if sexo == "M" else "M")
                proximos.append((filho, conj))
            familias.append((fid, husb, wife, filhos))
        casais = proximos

    linhas = ["0 HEAD", "1 SOUR TESTE", "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED"]
    for x in ordem:
        d = individuos[x]
        partes = d["nome"].rsplit(" ", 1)
        linhas.append("0 %s INDI" % x)
        linhas.append("1 NAME %s /%s/" % (partes[0], partes[1]))
        linhas.append("1 SEX %s" % d["sexo"])
        if d["famc"]:
            linhas.append("1 FAMC %s" % d["famc"])
        for f in d["fams"]:
            linhas.append("1 FAMS %s" % f)
    for fid, husb, wife, filhos in familias:
        linhas.append("0 %s FAM" % fid)
        linhas.append("1 HUSB %s" % husb)
        linhas.append("1 WIFE %s" % wife)
        for filho in filhos:
            linhas.append("1 CHIL %s" % filho)
    linhas.append("0 TRLR")

    # Os matches saem dos descendentes, espalhados: caminho documental curto e variado.
    passo = max(1, len(descendentes) // n_matches)
    escolhidos = descendentes[::passo][:n_matches]
    csv = ["Name,cM,Kit"]
    for i, x in enumerate(escolhidos):
        csv.append("%s,%d,AA%07d" % (individuos[x]["nome"], 100 + i, 1000000 + i))

    return "\n".join(linhas) + "\n", "\n".join(csv) + "\n"


def main() -> None:
    destino = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(destino, exist_ok=True)
    for rotulo, geracoes, matches in (("media", 5, 21), ("grande", 8, 71)):
        gedcom, csv = gerar(geracoes, matches)
        nome_ged = os.path.join(destino, "arvore_%s.ged" % rotulo)
        nome_csv = os.path.join(destino, "matches_%s.csv" % rotulo)
        with io.open(nome_ged, "w", encoding="utf-8", newline="\n") as f:
            f.write(gedcom)
        with io.open(nome_csv, "w", encoding="utf-8", newline="\n") as f:
            f.write(csv)
        pessoas = gedcom.count(" INDI")
        print("%-8s geracoes=%-2d pessoas=%-6d matches=%-3d ged=%6.1f kB csv=%d bytes"
              % (rotulo, geracoes, pessoas, matches,
                 os.path.getsize(nome_ged) / 1024, os.path.getsize(nome_csv)))


main()
