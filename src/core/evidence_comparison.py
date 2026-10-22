"""Confronto GEDCOM x DNA: as duas evidencias sao compativeis entre si?

Responsabilidade unica: receber o parentesco **documental** (que veio do GEDCOM),
a **evidencia genetica** (que veio do CSV) e as **possibilidades** estatisticas, e
responder em um dos quatro estados — COMPATIVEL, POSSIVEL, CONFLITANTE ou
INCONCLUSIVO — dizendo sempre POR QUE.

## Regra do projeto

Este modulo nao altera o parentesco documental e nao corrige o GEDCOM: ele apenas
compara. Um conflito vira aviso e lista de causas, nunca uma reescrita de vinculo.

## Como o estado e decidido (transparencia, ver o campo `method`)

1. A relacao documental vira uma chave (`1C6R`, `SIBLINGS`, ...) em
   `core.documentary_relationship`.
2. Se o Shared cM Project 4.0 publica a faixa dessa relacao, a janela e essa faixa
   (`method = "scp40:<nome>"`).
3. Se a 4.0 **nao** publica essa relacao (caso de 1C6R, 1C4R, 1C5R, 3C2R e dos
   bisavos mais distantes), a janela passa a ser a envoltoria das relacoes
   publicadas com o MESMO numero de meioses (`method = "scp40:meioses=<n>"`).
   Nenhum numero e inventado: se nao houver relacao publicada naquele numero de
   meioses, nao ha janela e o estado e INCONCLUSIVO.
4. cM dentro da janela -> COMPATIVEL. Fora dela -> POSSIVEL quando alguma relacao
   publicada que contem o valor tem faixa que SE SOBREPOE a janela documental (as
   distribuicoes se tocam e o cM nao separa as duas leituras); caso contrario,
   CONFLITANTE.
5. Sem DNA, sem caminho documental ou com identidade ambigua -> INCONCLUSIVO.
"""
from __future__ import annotations

from .relationship_hypotheses import (
    meioses_maximo_publicado,
    meioses_publicados,
    meioses_window,
    row_for_key,
)
from .profundidade_do_caminho import ATENCAO, DIVERGENCIA, conferir_profundidade


def _numero(valor) -> str:
    """Decimal com virgula, como o resto da tela (`cm_br`). Nao ha formatador de borda aqui."""
    return f"{valor:.1f}".replace(".", ",")

STATUS_LABEL = {
    "COMPATIVEL": "Compatível",
    "POSSIVEL": "Possível",
    "CONFLITANTE": "Conflitante",
    "INCONCLUSIVO": "Inconclusivo",
}

MENSAGENS = {
    "COMPATIVEL": ("Compatível: o parentesco documental encontrado no GEDCOM não entra em conflito "
                   "evidente com a quantidade de DNA compartilhada."),
    "POSSIVEL": ("Possível: a evidência genética permite esse relacionamento, mas não é suficiente "
                 "para confirmar o caminho documental."),
    "CONFLITANTE": ("Conflitante: a quantidade de DNA observada apresenta incompatibilidade "
                    "significativa com o parentesco documental encontrado. Verifique homônimos, "
                    "vínculos incorretos, pedigree collapse, endogamia ou outro caminho ancestral."),
    "INCONCLUSIVO": ("Inconclusivo: os dados disponíveis não permitem avaliar adequadamente a "
                     "compatibilidade entre o caminho documental e a evidência genética."),
}

# Lista pedida pela regra do projeto para quando as evidencias discordam. Nao e
# diagnostico automatico: e o rol de causas que o operador deve considerar.
CAUSAS_POSSIVEIS = [
    "homônimo: o nome do CSV pode corresponder a outro registro do GEDCOM",
    "pessoa incorreta no GEDCOM (registro duplicado ou mesclado)",
    "vínculo parental incorreto (HUSB/WIFE/CHIL trocado ou ausente)",
    "caminho genealógico alternativo ainda não cadastrado",
    "colapso de pedigree",
    "endogamia",
    "relacionamento múltiplo entre as mesmas famílias",
    "segmento compartilhado pertencente a outro ramo",
    "erro ou limitação da fonte genética",
    "agregação incorreta dos dados (segmentos ou kits somados indevidamente)",
    "falso positivo, especialmente em segmentos pequenos",
    "ausência de evidência genética suficiente para sustentar o caminho",
]

# Subconjunto que faz sentido quando o estado e POSSIVEL: nao ha conflito, mas
# tambem nao ha confirmacao.
CAUSAS_POSSIVEL = CAUSAS_POSSIVEIS[:1] + CAUSAS_POSSIVEIS[3:8] + CAUSAS_POSSIVEIS[10:]


def _avaliar_kit(bloco: dict, janela: dict, meioses_documental) -> dict:
    """Estado de UM kit contra a janela do parentesco documental."""
    cm = bloco.get("total_cm")
    if cm is None:
        return {"status": "INCONCLUSIVO", "cm": None,
                "note": "Sem total de cM utilizável para este kit."}

    dentro = janela["range_low"] <= cm <= janela["range_high"]
    candidatas = bloco.get("possible_relationships", [])

    if dentro:
        return {"status": "COMPATIVEL", "cm": cm,
                "note": f"{cm:g} cM está dentro da faixa {janela['range_low']}–{janela['range_high']} cM."}

    # Fora da janela: sobra POSSIVEL apenas quando alguma relacao publicada que
    # contem o valor TEM FAIXA QUE SE SOBREPOE a janela documental — isto e,
    # quando as duas distribuicoes se tocam e o cM nao consegue separa-las.
    # Distancia em meioses NAO serve de criterio aqui: irmaos (1613–3488) e
    # primos de 1o grau com uma geracao de diferenca (102–980) estao a uma meiosa de
    # distancia e mesmo assim nao se sobrepoem.
    sobrepostas = [
        c for c in candidatas
        if c["range_low"] <= janela["range_high"] and c["range_high"] >= janela["range_low"]
    ]
    if sobrepostas:
        vizinha = min(sobrepostas, key=lambda c: abs(c["average"] - cm))
        return {"status": "POSSIVEL", "cm": cm,
                "note": (f"{cm:g} cM está fora da faixa {janela['range_low']}–{janela['range_high']} cM, "
                         f"mas cabe em {vizinha['name_pt']} ({vizinha['range_low']}–"
                         f"{vizinha['range_high']} cM), cuja distribuição se sobrepõe à do parentesco "
                         "documental. O cM sozinho não separa as duas leituras.")}

    mais_proxima = min(candidatas, key=lambda c: abs(c["average"] - cm)) if candidatas else None
    detalhe = (f"o valor cabe em {mais_proxima['name_pt']} ({mais_proxima['range_low']}–"
               f"{mais_proxima['range_high']} cM), cuja faixa NÃO alcança a do parentesco documental"
               if mais_proxima else "o valor não cabe em nenhuma relação publicada na versão 4.0")
    return {"status": "CONFLITANTE", "cm": cm,
            "note": (f"{cm:g} cM está fora da faixa {janela['range_low']}–{janela['range_high']} cM do "
                     f"parentesco documental e {detalhe}.")}


def _janela_do_documental(documentary: dict):
    """Janela de cM esperada para o parentesco documental, e de onde ela veio."""
    chave = documentary.get("relationship_key")
    meioses = documentary.get("meioses")

    linha = row_for_key(chave) if chave else None
    if linha:
        return {
            "range_low": linha["range_low"], "range_high": linha["range_high"],
            "average": linha["average"],
            "method": f"scp40:{linha['name_en']}",
            "method_label": (f"Shared cM Project 4.0, relação “{linha['name_pt']}” "
                             f"(média {linha['average']} cM)"),
        }, None

    if meioses:
        janela = meioses_window(meioses)
        if janela:
            motivo = (f"a versão 4.0 do Shared cM Project não publica faixa para "
                      f"“{documentary.get('label')}”; a referência usada é a envoltoria das relações "
                      f"publicadas com o mesmo número de meioses ({janela['meioses']}): "
                      + ", ".join(janela["rows"]))
            return {
                "range_low": janela["range_low"], "range_high": janela["range_high"],
                "average": janela["average"],
                "method": f"scp40:meioses={janela['meioses']}",
                "method_label": (f"Shared cM Project 4.0, {janela['meioses']} meioses "
                                 f"({janela['range_low']}–{janela['range_high']} cM)"),
            }, motivo

    return None, (f"a versão 4.0 do Shared cM Project não publica faixa para "
                  f"“{documentary.get('label')}” nem para {meioses} meioses")


def compare(documentary: dict, hypotheses: list, evidence: dict) -> dict:
    """Estado final do confronto, com a explicacao de como ele foi obtido.

    `documentary` vem de `core.documentary_relationship`, `hypotheses` de
    `core.relationship_hypotheses.hypotheses_for_evidence` (uma por kit) e
    `evidence` de `core.genetic_evidence.evidence_for`.
    """
    documental = documentary or {}
    tem_dna = bool(evidence and evidence.get("available"))

    notas = []
    base = {
        "status": "INCONCLUSIVO",
        "label": STATUS_LABEL["INCONCLUSIVO"],
        "message": MENSAGENS["INCONCLUSIVO"],
        "causes": [],
        "per_kit": [],
        "method": None,
        "expected_range": None,
        "detail": None,
        "observations": notas,
    }

    for aviso in (documental.get("warnings") or []):
        if aviso.get("code") in ("data_impossivel", "colapso_de_pedigree", "caminhos_multiplos"):
            notas.append(aviso["message"])

    if not tem_dna:
        base["detail"] = "Sem evidência genética disponível para esta pessoa no arquivo analisado."
        base["observations"] = notas + ["O parentesco documental continua valendo por si; "
                                        "não há DNA para confrontar."]
        return base

    if documental.get("status") == "not_found" or not documental.get("path"):
        base["detail"] = ("Há evidência genética, mas nenhum caminho genealógico foi encontrado no "
                          "GEDCOM entre as duas pessoas. Nenhum caminho foi inventado a partir do DNA.")
        base["causes"] = ["ausência de evidência genética suficiente para sustentar o caminho",
                          "vínculo parental incorreto (HUSB/WIFE/CHIL trocado ou ausente)",
                          "pessoa incorreta no GEDCOM (registro duplicado ou mesclado)"]
        base["observations"] = notas
        return base

    if documental.get("ambiguous_identity") or documental.get("status") == "ambiguous":
        homonimos = documental.get("homonyms") or {}
        base["detail"] = ("Identidade ambígua no GEDCOM: não é possível afirmar a qual registro o match "
                          "corresponde, e sem isso a comparação não conclui.")
        base["causes"] = ["homônimo: o nome do CSV pode corresponder a outro registro do GEDCOM"]
        base["observations"] = notas + [
            f"Registros com o mesmo nome: {', '.join(f['id'] for f in homonimos.get('exact_matches', []))}"
            if homonimos.get("exact_matches") else ""]
        base["observations"] = [o for o in base["observations"] if o]
        return base

    janela, motivo = _janela_do_documental(documental)
    if janela is None:
        meioses = documental.get("meioses")
        limite = meioses_maximo_publicado()
        base["detail"] = (f"Não há faixa publicada para comparar: {motivo}. O parentesco documental "
                          "segue registrado, mas a evidência genética não pode ser confrontada com ele.")

        # DUAS razoes diferentes de nao haver janela, e a tela precisa dizer qual e.
        #
        # A fonte nao cobrir a relacao e uma coisa; a relacao ser mais PROFUNDA do que
        # qualquer coisa que a fonte calibra e outra. Na segunda, o silencio nao e
        # concordancia: medido em 2026-10-14, 7 dos 11 cartoes com caminho documental caem
        # aqui, e sao 3 alem do alcance (18, 19 e 20 meioses, contra um teto publicado de
        # 16) e 4 em lacuna da tabela (13 e 15 meioses, entre 12 e 14 e entre 14 e 16).
        # Antes desta distincao os 7 diziam apenas "Inconclusivo", que na tela se le como
        # "sem objecao".
        #
        # O veredito NAO muda: continua `INCONCLUSIVO`, como decidem RF-19, BR-D-27 e o
        # ADR-15 ("nenhum numero e inventado"). O que muda e o texto, que passa a nomear o
        # limite estrutural da fonte. Emprestar a janela do numero de meioses mais proximo
        # — que daria um veredito aos 7 — seria exatamente inventar numero, e por isso nao
        # foi feito.
        if meioses:
            publicados = meioses_publicados()
            if meioses > limite:
                base["detail"] += (
                    f" A relação documental tem {meioses} meioses — mais profunda que a relação "
                    f"mais distante que a versão 4.0 do Shared cM Project calibra ({limite} "
                    "meioses). Nessa profundidade a fonte não publica distribuição nenhuma, e o "
                    "silêncio não é concordância: nenhum caminho foi inventado a partir do DNA."
                )
            elif meioses not in publicados:
                abaixo = max((m for m in publicados if m < meioses), default=None)
                acima = min((m for m in publicados if m > meioses), default=None)
                vizinhos = " e ".join(str(m) for m in (abaixo, acima) if m is not None)
                base["detail"] += (
                    f" A versão 4.0 não publica faixa para {meioses} meioses "
                    f"(as publicadas mais próximas são {vizinhos}). A envoltória por meioses só "
                    "vale para o MESMO número de meioses: nenhuma janela foi emprestada por "
                    "proximidade, e nenhum número foi inventado."
                )

        # O numero que o proprio arquivo de DNA traz para a profundidade, que e o unico
        # disponivel quando a fonte nao calibra a relacao. Ver `core.profundidade_do_caminho`.
        geracoes_do_kit = next(
            (b.get("mrca_generations") for b in (hypotheses or []) if b.get("mrca_generations")),
            None)
        if meioses and geracoes_do_kit:
            estado, _razao, _doc = conferir_profundidade(meioses, geracoes_do_kit)
            texto = ("Sem faixa publicada para a relação documental, o cM não foi confrontado com "
                     "ela. O relatório de DNA estima "
                     + f"{geracoes_do_kit:.2f}".replace(".", ",")
                     + " gerações até o MRCA deste kit, contra "
                     + _numero(meioses / 2)
                     + " gerações médias que a árvore afirma")
            if estado in (ATENCAO, DIVERGENCIA):
                notas.append(texto + " — veja o aviso de profundidade no topo do cartão.")
            else:
                notas.append(texto + ".")

        base["observations"] = notas
        return base

    base["method"] = janela["method"]
    base["expected_range"] = {"low": janela["range_low"], "high": janela["range_high"],
                              "average": janela["average"], "label": janela["method_label"]}
    if motivo:
        notas.append(motivo + ".")

    avaliacoes = [_avaliar_kit(bloco, janela, documental.get("meioses") or 0) for bloco in (hypotheses or [])]
    if not avaliacoes:
        base["detail"] = "Há arquivo de DNA, mas nenhum valor de cM utilizável para confrontar."
        base["observations"] = notas
        return base

    for bloco, avaliacao in zip(hypotheses or [], avaliacoes):
        base["per_kit"].append({"kit": bloco.get("kit"), **avaliacao})

    ordem = ["CONFLITANTE", "POSSIVEL", "COMPATIVEL", "INCONCLUSIVO"]
    estados = [a["status"] for a in avaliacoes]
    final = next((e for e in ordem if e in estados), "INCONCLUSIVO")

    base["status"] = final
    base["label"] = STATUS_LABEL[final]
    base["message"] = MENSAGENS[final]
    if final == "CONFLITANTE":
        base["causes"] = CAUSAS_POSSIVEIS
    elif final == "POSSIVEL":
        base["causes"] = CAUSAS_POSSIVEL
    if len(estados) > 1:
        notas.append("Mais de um kit para este nome: o estado final é o mais conservador entre eles — "
                     + "; ".join(f"kit {a.get('kit') or 'sem kit'}: {a['status']}" for a in base["per_kit"]))

    base["detail"] = ("Parentesco documental: " + str(documental.get("label"))
                      + f" ({documental.get('meioses')} meioses). Janela esperada: "
                      + janela["method_label"] + ". " + " ".join(a["note"] for a in avaliacoes))
    base["observations"] = notas
    return base


__all__ = ["compare", "MENSAGENS", "STATUS_LABEL", "CAUSAS_POSSIVEIS", "CAUSAS_POSSIVEL"]
