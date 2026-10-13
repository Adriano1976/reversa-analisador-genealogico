"""Gera as fixtures SINTETICAS usadas pelas sondas do checklist de seguranca.

Nenhum dado real do operador entra aqui: arvores, pessoas e CSVs sao inventados por
este script. O unico insumo externo e o texto do proprio codigo auditado.

Uso:
    python gerar_fixtures.py <pasta-de-saida>

Escreve os arquivos e imprime um JSON com o manifesto (nome, bytes, sha256, e a
chave de conteudo de 16 hexadecimais que o armazenamento usa).
"""
import hashlib
import json
import os
import sys

CABECALHO = (
    "0 HEAD\n"
    "1 SOUR sonda-sintetica\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "1 CHAR UTF-8\n"
)

# Nomes inventados. O nucleo familiar e o mesmo em toda arvore com pool: ele e o que
# permite um caminho documental (Carlos e Primo sao primos de primeiro grau via F3).
CORE = [
    ("I1", "Carlos /Silva Souza/", "M", [], ["F1"]),
    ("I2", "Jose /Silva/", "M", ["F1"], ["F3"]),
    ("I3", "Ana /Souza Lima/", "F", ["F1"], []),
    ("I4", "Pedro /Silva/", "M", ["F2"], ["F3"]),
    ("I5", "Rita /Souza/", "F", ["F2"], []),
    ("I6", "Primo /Silva Souza/", "M", [], ["F2"]),
    ("I7", "Antonio /Silva/", "M", ["F3"], []),
    ("I8", "Maria /Souza/", "F", ["F3"], []),
]
CORE_FAM = [
    ("F1", "I2", "I3", ["I1"]),
    ("F2", "I4", "I5", ["I6"]),
    ("F3", "I7", "I8", ["I2", "I4"]),
]

ROOT = "Carlos Silva Souza"


def _indi(xref, nome, sexo, fams, famc):
    linhas = [f"0 @{xref}@ INDI", f"1 NAME {nome}", f"1 SEX {sexo}"]
    if fams:
        linhas.append(f"1 FAMS @{fams[0]}@")
    for f in famc:
        linhas.append(f"1 FAMC @{f}@")
    return "\n".join(linhas) + "\n"


def _fam(xref, husb, wife, filhos):
    linhas = [f"0 @{xref}@ FAM", f"1 HUSB @{husb}@", f"1 WIFE @{wife}@"]
    for c in filhos:
        linhas.append(f"1 CHIL @{c}@")
    return "\n".join(linhas) + "\n"


def arvore_com_pool(n_silva):
    """Nucleo familiar + `n_silva` pessoas ISOLADAS de sobrenome Silva.

    As isoladas existem para inflar `surname_index["silva"]`, que e o pool que o
    `match_candidates` percorre quando o nome do CSV nao casa exatamente. Elas nao
    tem familia de proposito: o custo medido e o do laco de candidatos.
    """
    partes = [CABECALHO]
    for xref, nome, sexo, fams, famc in CORE:
        partes.append(_indi(xref, nome, sexo, fams, famc))
    for xref, husb, wife, filhos in CORE_FAM:
        partes.append(_fam(xref, husb, wife, filhos))
    for k in range(n_silva):
        partes.append(_indi(f"I{1000 + k}", f"Alguem{k} /Silva/", "U", [], []))
    partes.append("0 TRLR\n")
    return "".join(partes)


def arvore_grande(n_pessoas):
    """Arvore de `n_pessoas` individuos em familias de cinco (pai, mae, 3 filhos).

    O formato e o de um GEDCOM comum; o que interessa aqui e o tamanho, porque a
    medicao do item 3 e o custo de reprocessar o arquivo inteiro a cada requisicao.
    """
    partes = [CABECALHO]
    xref = 0
    fam = 0
    while xref < n_pessoas:
        pai, mae = xref + 1, xref + 2
        filhos = [xref + 3, xref + 4, xref + 5]
        sobrenome = f"Sobrenome{fam % 50:02d}"
        partes.append(_indi(f"I{pai}", f"Pai{fam} /{sobrenome}/", "M", [f"F{fam}"], []))
        partes.append(_indi(f"I{mae}", f"Mae{fam} /{sobrenome}/", "F", [f"F{fam}"], []))
        for k, filho in enumerate(filhos, start=1):
            partes.append(_indi(f"I{filho}", f"Filho{fam}_{k} /{sobrenome}/", "U", [], [f"F{fam}"]))
        partes.append(_fam(f"F{fam}", f"I{pai}", f"I{mae}", [f"I{f}" for f in filhos]))
        xref += 5
        fam += 1
    partes.append("0 TRLR\n")
    return "".join(partes)


def matches(linhas_de_fanout):
    """CSV no formato que o `detect_columns` aceita: colunas `Name` e `cM`.

    A primeira linha e o caso funcional (nome que EXISTE no GEDCOM, casamento
    exato). As demais sao nomes que NAO existem e que carregam o sobrenome Silva:
    e por elas que o pool de sobrenomes e percorrido inteiro, uma vez por linha.
    """
    linhas = ["Name,cM", f"{ROOT},120.0"]
    for k in range(linhas_de_fanout):
        linhas.append(f"Candidato{k} Silva,{20 + (k % 15)}.5")
    return "\n".join(linhas) + "\n"


def gedcom_valido_minimo():
    """GEDCOM pequeno e valido: usado nos testes de upload, origem e nome de arquivo."""
    return arvore_com_pool(0)


def gedcom_truncado():
    """Comeca com `0 HEAD` (portanto PASSA pelo portao de conteudo) e nao tem TRLR."""
    return "0 HEAD\n1 SOUR sonda-sintetica\n1 CHAR UTF-8\n"


def chave_de_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()[:16]


def escrever(pasta, nome, conteudo):
    caminho = os.path.join(pasta, nome)
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo)
    dados = conteudo.encode("utf-8")
    return {
        "nome": nome,
        "caminho": caminho,
        "bytes": len(dados),
        "sha256": hashlib.sha256(dados).hexdigest(),
        "chave": chave_de_conteudo(conteudo),
    }


def main(pasta):
    os.makedirs(pasta, exist_ok=True)
    manifesto = {}

    manifesto["arvore_valida"] = escrever(pasta, "arvore_valida.ged", gedcom_valido_minimo())
    manifesto["arvore_truncada"] = escrever(pasta, "arvore_truncada.ged", gedcom_truncado())
    manifesto["arvore_pool150"] = escrever(pasta, "arvore_pool150.ged", arvore_com_pool(150))
    manifesto["arvore_pool600"] = escrever(pasta, "arvore_pool600.ged", arvore_com_pool(600))
    manifesto["arvore_grande_15000"] = escrever(
        pasta, "arvore_grande_15000.ged", arvore_grande(15000))
    manifesto["matches_r24"] = escrever(pasta, "matches_r24.csv", matches(24))
    manifesto["matches_r49"] = escrever(pasta, "matches_r49.csv", matches(49))
    manifesto["matches_r199"] = escrever(pasta, "matches_r199.csv", matches(199))
    manifesto["raiz"] = ROOT

    destino = os.path.join(pasta, "manifesto.json")
    with open(destino, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifesto, fh, ensure_ascii=False, indent=2)
    print(json.dumps(manifesto, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
