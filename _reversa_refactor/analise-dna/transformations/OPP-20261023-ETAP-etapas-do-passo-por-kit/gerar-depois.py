"""Fase 2 da OPP-20261023-ORQA (OPP-20261023-ETAP), gerada fora do projeto.

Le `src/core/dna_analysis.py` e escreve `before-after/depois.py` com seis
extracoes dentro de `_cartao_do_kit`:

  E1 `_recusa_do_kit`            o descarte de um kit sem candidato
  E2 `_parentesco_do_kit`        escolha do candidato e dossie de homonimos
  E3 `_endogamia_estrutural`     diagnostico no grafo, selo e observacao
  E4 `_confronto_do_kit`         evidencia, possibilidades e confronto
  E5 `_profundidade_do_caminho`  profundidade, razao e anotacao do diagrama
  E6 `_rotulo_do_confronto`      o rotulo do cabecalho

Cada bloco e movido VERBATIM, com a indentacao que ja tem, porque o corpo da
funcao e as novas funcoes ficam no mesmo nivel (4 espacos) e os nomes locais
viram parametros de mesmo nome. Nao ha rescrita nem reordenacao de efeito.

Nao toca no projeto. Roda da raiz:  python <este arquivo>
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[4]
ALVO = RAIZ / "src" / "core" / "dna_analysis.py"
SAIDA = pathlib.Path(__file__).resolve().parent / "before-after" / "depois.py"

# Blocos (1-based, inclusive), medidos no arquivo depois da ORQA.
E1 = (632, 660)   # corpo do `if not candidate_pids:`, sem o return
E2 = (663, 678)   # comentario do legado + escolha do candidato
E3A = (680, 726)  # diagnostico estrutural, nomes e selo
E3B = (852, 860)  # a frase da secao 5
E4 = (763, 771)   # evidencia, hipoteses, confronto e nomes do caminho
E5 = (773, 805)   # profundidade + anotacao do diagrama (inclui a linha em branco)
E6 = (806, 820)   # rotulo efetivo do confronto (inclui a linha em branco)

CABECALHOS = {
    "E1": '''def _recusa_do_kit(contexto, kit, reason, proximos, evidencia_mitigada):
    """O descarte de um kit sem candidato, com os tres melhores recusados.

    Extraida pela OPP-20261023-ETAP. O bloco respondia "por que este kit nao
    entrou", e tem regra propria (o motivo virou objeto na feature 038) que nao
    se mistura com a montagem do cartao.
    """
''',
    "E2": '''def _parentesco_do_kit(contexto, kit, candidate_pids):
    """Escolhe o candidato com caminho e devolve o dossie de homonimos.

    Extraida pela OPP-20261023-ETAP. Devolve `(pid, documentary, homonimos)`;
    `documentary` ja vem do cache por pessoa que vive no contexto.
    """
''',
    "E3": '''def _endogamia_estrutural(contexto, pid, documentary, evidencia_mitigada):
    """Diagnostico de endogamia no grafo, selo do cabecalho e frase da secao 5.

    Extraida pela OPP-20261023-ETAP. Devolve
    `(arvore, selo, tem_caminho_documental, observacoes)`. O ultimo item e a
    frase que so existe quando o diagnostico estrutural acusou.
    """
''',
    "E4": '''def _confronto_do_kit(por_kit, chave_kit, avisos_deste_cartao, documentary):
    """Evidencia genetica, possibilidades e confronto, com os nomes do caminho.

    Extraida pela OPP-20261023-ETAP. Roda depois da regra do operador, de
    proposito: com o documental apresentado como nao encontrado, o confronto
    responde o que responde para esse grupo.
    """
''',
    "E5": '''def _profundidade_do_caminho(documentary, evidence):
    """A profundidade do caminho contra a estimativa do proprio kit.

    Extraida pela OPP-20261023-ETAP. Devolve
    `(geracoes_do_kit, estado, razao, geracoes_documentais, anotacao)`.
    `anotacao` e None quando nao ha o que marcar no diagrama.
    """
''',
    "E6": '''def _rotulo_do_confronto(comparison, janela):
    """O rotulo que o cabecalho mostra, que nao pode contradizer o aviso.

    Extraida pela OPP-20261023-ETAP. Devolve `(efetiva, rotulo)`. Quando a
    janela de vida e impossivel, o selo do cM deixa de dizer "compativel": os
    dois lados estavam certos sobre eixos diferentes, mas o selo era o mais
    visivel dos dois.
    """
''',
}

RETORNOS = {
    "E1": "    return descarte\n",
    "E2": "    return pid, documentary, homonimos\n",
    "E3": (
        "    return (arvore_da_endogamia, selo_da_endogamia,\n"
        "            tem_caminho_documental, observacoes_da_endogamia)\n"
    ),
    "E4": "    return evidence, hypotheses, comparison, nomes_do_caminho\n",
    "E5": (
        "    return (geracoes_do_kit, profundidade, razao_da_profundidade,\n"
        "            geracoes_documentais, anotacao)\n"
    ),
    "E6": "    return confrontacao_efetiva, confrontacao_rotulo\n",
}

CHAMADAS = {
    "E1": (
        "        descarte = _recusa_do_kit(\n"
        "            contexto, kit, reason, proximos, evidencia_mitigada)\n"
    ),
    "E2": "    pid, documentary, homonimos = _parentesco_do_kit(contexto, kit, candidate_pids)\n",
    "E3": (
        "    (arvore_da_endogamia, selo_da_endogamia, tem_caminho_documental,\n"
        "     observacoes_da_endogamia) = _endogamia_estrutural(\n"
        "        contexto, pid, documentary, evidencia_mitigada)\n"
    ),
    "E3B": "",
    "E4": (
        "    evidence, hypotheses, comparison, nomes_do_caminho = _confronto_do_kit(\n"
        "        por_kit, chave_kit, avisos_deste_cartao, documentary)\n"
    ),
    "E5": (
        "    (geracoes_do_kit, profundidade, razao_da_profundidade,\n"
        "     geracoes_documentais, anotacao) = _profundidade_do_caminho(documentary, evidence)\n"
        "\n"
    ),
    "E6": (
        "    confrontacao_efetiva, confrontacao_rotulo = _rotulo_do_confronto(\n"
        "        comparison, janela)\n"
        "\n"
    ),
}


def bloco(linhas, faixa):
    inicio, fim = faixa
    return "".join(linhas[inicio - 1 : fim])


def recuar(texto: str, espacos: int) -> str:
    """Remove `espacos` de indentacao das linhas nao vazias."""
    saida = []
    for linha in texto.splitlines(keepends=True):
        if not linha.strip():
            saida.append(linha)
        elif linha.startswith(" " * espacos):
            saida.append(linha[espacos:])
        else:
            raise SystemExit(f"ABORTA: linha sem recuo esperado: {linha!r}")
    return "".join(saida)


def main() -> int:
    original = ALVO.read_text(encoding="utf-8")
    linhas = original.splitlines(keepends=True)

    trechos = {
        "E1": bloco(linhas, E1),
        "E2": bloco(linhas, E2),
        "E3A": bloco(linhas, E3A),
        "E3B": bloco(linhas, E3B),
        "E4": bloco(linhas, E4),
        "E5": bloco(linhas, E5),
        "E6": bloco(linhas, E6),
    }

    esperado = {
        "E1": "        # A QUEM a arvore oferecia (feature 034)",
        "E2": "    # O legado percorria TODOS os candidatos",
        "E3A": "    # A ENDOGAMIA ESTRUTURAL, no grafo do GEDCOM",
        "E3B": "    # A SECAO 5 GUARDA SO O DIAGNOSTICO ESTRUTURAL",
        "E4": "    # O CONFRONTO VEM DEPOIS DA REGRA",
        "E5": "    # A PROFUNDIDADE DO CAMINHO contra a estimativa do PROPRIO kit",
        "E6": "    # O SELO DO CABECALHO NAO PODE CONTRADIZER O AVISO",
    }
    for chave, inicio in esperado.items():
        if not trechos[chave].startswith(inicio):
            raise SystemExit(
                f"ABORTA: bloco {chave} nao comeca com {inicio!r}: "
                f"{trechos[chave][:60]!r}"
            )

    novo = original
    substituicoes = [
        (trechos["E1"], CHAMADAS["E1"]),
        (trechos["E2"], CHAMADAS["E2"]),
        (trechos["E3A"], CHAMADAS["E3"]),
        (trechos["E3B"], CHAMADAS["E3B"]),
        (trechos["E4"], CHAMADAS["E4"]),
        (trechos["E5"], CHAMADAS["E5"]),
        (trechos["E6"], CHAMADAS["E6"]),
    ]
    for antigo, substituto in substituicoes:
        if antigo.count("_cartao_do_kit") or novo.count(antigo) != 1:
            raise SystemExit("ABORTA: bloco nao unico ou contendo a funcao")
        novo = novo.replace(antigo, substituto)

    funcoes = []
    for chave in ("E1", "E2", "E3", "E4", "E5", "E6"):
        corpo = CABECALHOS[chave]
        if chave == "E3":
            corpo += trechos["E3A"] + "\n" + trechos["E3B"]
        elif chave == "E1":
            # O unico bloco que morava dentro de um `if`, portanto a 8 espacos.
            corpo += recuar(trechos["E1"], 4)
        else:
            corpo += trechos[chave]
        corpo += RETORNOS[chave]
        funcoes.append(corpo + "\n\n")

    ancora = "\n\ndef _cartao_do_kit(\n"
    if novo.count(ancora) != 1:
        raise SystemExit("ABORTA: ancora de _cartao_do_kit nao unica")
    novo = novo.replace(ancora, "\n\n" + "".join(funcoes) + "def _cartao_do_kit(\n")

    compile(novo, str(SAIDA), "exec")
    SAIDA.write_bytes(novo.encode("utf-8"))
    print(f"depois: {SAIDA} ({len(novo.splitlines())} linhas, compila)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
