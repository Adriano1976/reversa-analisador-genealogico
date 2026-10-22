"""Estado de qualidade de UMA medida de DNA (total, maior bloco e SNPs).

## A pergunta que este modulo responde

"Esta medida sustenta alguma conclusao?" — e **nao** "estes dois sao parentes". O estado
descreve a robustez do dado que veio do arquivo; ele nao substitui, nao contradiz e nao
recolore o confronto GEDCOM x DNA (`domain.md` 2). A tela sempre exibe a ressalva junto.

## De onde vem cada piso

- **15,0 cM** para o total e para o maior bloco — sao os mesmos 15,0 cM que
  `genetic_evidence.LIMITE_SEGMENTO_FRACO` ja usa e que o `code-analysis.md` 4.6 registra
  como **criterio do projeto, nao da fonte**. O maior bloco reusa a constante para o
  numero ter um dono so.
- **900 SNPs** — **corte de triagem declarado** pelo operador, com a mesma natureza do
  corte de 20,0 cM da feature 039: nao e faixa publicada por nenhuma fonte e nao afirma
  parentesco. Medido no arquivo real de 2026-10-22: 232 de 456 evidencias ficam abaixo
  dele, e 4 das 50 "robustas" por cM caem para `parcial` por causa dele.

## Por que a ausencia de SNPs nao penaliza

`snps_total is None` significa "o arquivo nao declarou SNPs", e ausencia de dado nao e
dado ruim (`architecture.md` 4). Ja o maior bloco ausente conta como abaixo do piso: sem
nenhum segmento com cM, nao ha bloco que sustente nada.
"""
from __future__ import annotations

#: Pisos. Total e maior bloco reaproveitam o criterio de 15,0 cM do projeto.
PISO_TOTAL_CM = 15.0
PISO_MAIOR_BLOCO_CM = 15.0
#: Teto de SNPs do criterio de triagem; **declarado**, nao publicado.
PISO_SNPS = 900

ROBUSTA = "robusta"
PARCIAL = "parcial"
INSUFICIENTE = "insuficiente"

ROTULOS = {
    ROBUSTA: "Medida robusta",
    PARCIAL: "Medida parcial",
    INSUFICIENTE: "Medida insuficiente",
}

MOTIVO_TOTAL_BAIXO = "total_baixo"
MOTIVO_BLOCO_PEQUENO = "bloco_pequeno"
MOTIVO_POUCOS_SNPS = "poucos_snps"

MOTIVOS_TEXTO = {
    MOTIVO_TOTAL_BAIXO: f"total abaixo de {PISO_TOTAL_CM:.1f} cM".replace(".", ","),
    MOTIVO_BLOCO_PEQUENO: f"menor bloco abaixo de {PISO_MAIOR_BLOCO_CM:.1f} cM".replace(".", ","),
    MOTIVO_POUCOS_SNPS: f"menos de {PISO_SNPS} SNPs somados",
}

#: Frase fixa que acompanha todo estado. Mora aqui para ter dono unico e teste proprio.
RESSALVA = "Qualidade da medida, não do parentesco."


def _numero(valor) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def avaliar(total_cm, largest_segment_cm=None, snps_total=None) -> dict:
    """Devolve `{estado, rotulo, motivos, motivos_texto, numeros, ressalva}`.

    - `insuficiente` — total abaixo de 15,0 cM;
    - `parcial` — total suficiente, mas o maior bloco abaixo de 15,0 cM, ou SNPs abaixo
      de 900;
    - `robusta` — total e bloco em 15,0 cM ou mais, e SNPs em 900 ou mais (ou ausentes).
    """
    total = _numero(total_cm)
    bloco = None if largest_segment_cm is None else _numero(largest_segment_cm)
    bloco_efetivo = 0.0 if bloco is None else bloco
    snps = None if snps_total is None else int(_numero(snps_total))

    motivos: tuple[str, ...] = ()
    if total < PISO_TOTAL_CM:
        estado = INSUFICIENTE
        motivos = (MOTIVO_TOTAL_BAIXO,)
    elif bloco_efetivo < PISO_MAIOR_BLOCO_CM:
        estado = PARCIAL
        motivos = (MOTIVO_BLOCO_PEQUENO,)
    elif snps is not None and snps < PISO_SNPS:
        estado = PARCIAL
        motivos = (MOTIVO_POUCOS_SNPS,)
    else:
        estado = ROBUSTA

    return {
        "estado": estado,
        "rotulo": ROTULOS[estado],
        "motivos": motivos,
        "motivos_texto": tuple(MOTIVOS_TEXTO[m] for m in motivos),
        "numeros": {"total_cm": total, "maior_bloco_cm": bloco, "snps": snps},
        "ressalva": RESSALVA,
    }


__all__ = [
    "PISO_TOTAL_CM",
    "PISO_MAIOR_BLOCO_CM",
    "PISO_SNPS",
    "ROBUSTA",
    "PARCIAL",
    "INSUFICIENTE",
    "ROTULOS",
    "MOTIVOS_TEXTO",
    "RESSALVA",
    "avaliar",
]
