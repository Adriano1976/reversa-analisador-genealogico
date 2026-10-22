"""Medida do arquivo inteiro: o que o CSV cobre, e nao o que um cartao afirma.

## O que este modulo responde

Antes de ler dezenas de cartoes, o operador precisa saber **de que e feito o arquivo**:
quantas linhas, quantas pessoas, quantos kits e laboratorios, quantos cromossomos, qual a
mediana de cM e quanto do arquivo fica abaixo dos pisos que o projeto usa. Medido no
arquivo real de 2026-10-22: 617 linhas, 456 evidencias, **74%** dos segmentos abaixo do
piso de 10 cM, **88%** das evidencias sem bloco de 15 cM e mediana de **9,05 cM**.

## Ele nao decide, nao relê e nao soma

A medida e derivada das evidencias **ja montadas** por `core.genetic_evidence`: nenhuma
linha do CSV e relida, nenhum cM e recalculado e nada e somado entre kits — o total por
evidencia continua sendo o do seu proprio kit (`domain.md` 3.2). O modulo tambem nao le o
GEDCOM e nao sabe o que e parentesco.

## Por que a tela nao calcula

Percentual e mediana sao regra, e regra mora no nucleo (`architecture.md` 3). O template
recebe os numeros prontos e so interpola; as frases que os explicam sao compostas la, como
a contagem em tres faixas da feature 033.
"""
from __future__ import annotations

from statistics import median

from .endogamia import CM_MINIMO_SEGMENTO
from .fontes_de_laboratorio import LABORATORIOS, MOTIVOS_TEXTO, NAO_DECLARADA, OUTRO
from .qualidade_da_medida import PISO_MAIOR_BLOCO_CM, PISO_SNPS


def _percentual(parte: int, total: int) -> int:
    """Percentual inteiro; arquivo vazio devolve 0, e nao divisao por zero."""
    if not total:
        return 0
    return round(100 * parte / total)


def _ordenados(contagem: dict) -> tuple[tuple[str, int], ...]:
    """Contagem em ordem decrescente e, no empate, alfabetica — determinismo explicito."""
    return tuple(sorted(contagem.items(), key=lambda par: (-par[1], par[0])))


def medir(evidencias, linhas: int) -> dict:
    """Mede o arquivo a partir do dicionario `evidencias` e do numero de linhas do CSV.

    `evidencias` e `{nome_normalizado: {chave_kit: evidencia}}`, a mesma estrutura que
    `build_genetic_evidence` devolve. `linhas` e o tamanho do CSV lido; ele entra por
    parametro porque a medicao nao pode reler o arquivo.
    """
    kits = [kit for por_nome in evidencias.values() for kit in por_nome.values()]
    segmentos = [segmento for kit in kits for segmento in kit.get("segments", ())]
    cromossomos = {s.get("chromosome") for s in segmentos if s.get("chromosome")}

    fontes = {}
    motivos = {}
    for kit in kits:
        rotulo = kit.get("source")
        if rotulo is not None:
            fontes[rotulo] = fontes.get(rotulo, 0) + 1
        motivo = kit.get("source_motivo")
        if motivo:
            motivos[motivo] = motivos.get(motivo, 0) + 1

    tem_coluna = any(kit.get("source") is not None for kit in kits)
    grafias = (
        len({(kit.get("source_raw") or "") for kit in kits}) if tem_coluna else 0
    )
    abaixo = sum(1 for s in segmentos if (s.get("cm") or 0.0) < CM_MINIMO_SEGMENTO)
    sem_bloco = sum(
        1 for kit in kits if (kit.get("largest_segment_cm") or 0.0) < PISO_MAIOR_BLOCO_CM
    )
    snps_baixo = sum(
        1 for kit in kits
        if kit.get("snps_total") is not None and kit["snps_total"] < PISO_SNPS
    )
    acima = sum(1 for kit in kits if (kit.get("total_cm") or 0.0) >= PISO_MAIOR_BLOCO_CM)
    acima_sem_bloco = sum(
        1 for kit in kits
        if (kit.get("total_cm") or 0.0) >= PISO_MAIOR_BLOCO_CM
        and (kit.get("largest_segment_cm") or 0.0) < PISO_MAIOR_BLOCO_CM
    )

    return {
        "linhas": int(linhas),
        "evidencias": len(kits),
        "kits": len({kit.get("kit") for kit in kits}),
        "laboratorios": _ordenados(fontes),
        "quantidade_de_laboratorios": sum(1 for r in fontes if r in LABORATORIOS),
        "grafias": grafias,
        "cromossomos": len(cromossomos),
        "mediana_cm": float(median([kit.get("total_cm") or 0.0 for kit in kits])) if kits else 0.0,
        "segmentos": len(segmentos),
        "segmentos_abaixo_do_piso": abaixo,
        "percentual_abaixo_do_piso": _percentual(abaixo, len(segmentos)),
        "evidencias_sem_bloco": sem_bloco,
        "percentual_sem_bloco": _percentual(sem_bloco, len(kits)),
        "evidencias_snps_baixo": snps_baixo,
        "total_acima_com_bloco_abaixo": acima_sem_bloco,
        "total_acima": acima,
        "sem_laboratorio": tuple(
            (MOTIVOS_TEXTO.get(motivo, motivo), quantidade)
            for motivo, quantidade in _ordenados(motivos)
        ),
        "sem_laboratorio_total": sum(motivos.values()),
        "tem_coluna_de_fonte": tem_coluna,
    }


__all__ = ["medir", "NAO_DECLARADA", "OUTRO"]
