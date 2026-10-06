"""Evidencia GENETICA: o que o arquivo de DNA afirma, sem o GEDCOM.

Responsabilidade unica: transformar as linhas do CSV de matches em evidencia
genetica descritiva — kit, fonte, cM total, numero de segmentos, maior segmento,
SNPs, cromossomo, posicoes e quantos registros entraram em cada numero.

## Regra do projeto

O DNA determina a evidencia genetica; ele **nao** determina parentesco. Este
modulo nao conhece `people`, nao conhece arvore e nao produz rotulo de
parentesco: quem traduz cM em possibilidades e `core.relationship_hypotheses`, e
quem confronta com o GEDCOM e `core.evidence_comparison`.

## Nunca somar kits diferentes

Duas linhas do CSV com o mesmo nome e kits diferentes sao **duas** evidencias,
nao uma. A chave de agrupamento e sempre (nome normalizado + kit). Quando o CSV
nao traz coluna de kit nem de e-mail, o agrupamento cai para o nome e a evidencia
sai marcada com o aviso `kit_ausente` — sem isso, dois laboratorios distintos
virariam um match so, com cM somado.
"""
from __future__ import annotations

import re

from .name_normalization import norm_name
from utils.text_cleaning import demojibake

# Abaixo disto o segmento e tratado como evidencia fraca: segmentos pequenos
# aparecem com frequencia em pares sem relacao genealogica recente.
LIMITE_SEGMENTO_FRACO = 15.0

# Sentinela do agrupamento sem kit. O ESPACO A ESQUERDA nao e decorativo: `_clean`
# faz strip em todo valor do CSV, entao nenhum kit real pode comecar com espaco -
# era assim que o literal "SEM-KIT" colidia com um kit de verdade (risco E-03).
SEM_KIT = " SEM-KIT"

# Aceita ZL6373425 (GEDmatch), A123456, M123456 e afins. O regex largo so vale
# para coluna cujo NOME fala de kit; para as demais colunas fica a regra estreita
# do legado (duas letras + sete digitos), que e a que o CSV do GEDmatch usa.
_KIT_ESTREITO = re.compile(r"[A-Z]{2}\d{7}")
_KIT_LARGO = re.compile(r"[A-Z]{1,3}\d{4,8}")
_NOME_DE_KIT = re.compile(r"kit|gedmatch|teste|test\b", re.IGNORECASE)


def detect_segment_columns(df) -> dict:
    """Descobre as colunas do CSV por papel, tolerando variacao de cabecalho.

    Construida ao lado de `detect_columns` (que fica intocada, por ser contrato do
    legado) porque a evidencia genetica precisa de mais colunas do que o fluxo
    antigo usava: SNPs, cromossomo, posicao, fonte e kit.
    """
    colunas = {c.strip() for c in df.columns}

    def primeira(opcoes):
        for opcao in opcoes:
            for col in df.columns:
                if col.strip().lower() == opcao:
                    return col
        return None

    name = primeira(["name", "matchedname", "nome"])
    cm = primeira(["cm", "totalcm", "total cm"])
    snps = primeira(["snps", "snp", "snps count"])
    chromosome = primeira(["chromosome", "chr", "cromossomo"])
    start = primeira(["start", "start location", "posicao inicial"])
    end = primeira(["end", "end location", "posicao final"])
    source = primeira(["source", "fonte", "company"])
    email_cols = [c for c in df.columns if "mail" in c.lower()]

    kit = None
    for col in df.columns:
        if not _NOME_DE_KIT.search(col):
            continue
        valores = df[col].astype(str).str.strip().str.upper()
        if valores.str.fullmatch(_KIT_LARGO).mean() > 0.5:
            kit = col
            break
    if kit is None:
        kit = next((c for c in df.columns
                    if df[c].astype(str).str.fullmatch(_KIT_ESTREITO).mean() > 0.3), None)

    return {
        "name": name,
        "cm": cm,
        "snps": snps,
        "chromosome": chromosome,
        "start": start,
        "end": end,
        "source": source,
        "kit": kit,
        "email": email_cols[-1] if email_cols else None,
    }


def _to_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _to_int(valor):
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def _clean(valor):
    texto = str(valor).strip()
    return "" if texto.lower() in ("nan", "none") else texto


def build_genetic_evidence(df):
    """Agrega o DataFrame do CSV em evidencia genetica por (pessoa, kit).

    Devolve `(evidencias, avisos)`, com `evidencias = {nome_normalizado: {kit:
    evidencia}}`. Cada evidencia carrega os segmentos individuais, o maior
    segmento, a soma de SNPs, os cromossomos e o metodo usado — para que qualquer
    numero exibido possa ser reconstruido a partir da fonte.
    """
    colunas = detect_segment_columns(df)
    if not colunas["name"] or not colunas["cm"]:
        raise ValueError("Colunas de Nome e cM não encontradas no CSV.")

    kit_col = colunas["kit"]
    evidencias: dict = {}
    avisos: list = []
    vistos = set()

    for _, linha in df.iterrows():
        nome_csv = _clean(linha[colunas["name"]])
        if not nome_csv:
            continue
        nome = demojibake(nome_csv)
        chave_nome = norm_name(nome)

        if kit_col:
            kit = _clean(linha[kit_col]).upper()
        elif colunas["email"]:
            kit = _clean(linha[colunas["email"]])
        else:
            kit = ""
        chave_kit = kit or SEM_KIT

        cm = _to_float(linha[colunas["cm"]]) or 0.0
        snps = _to_int(linha[colunas["snps"]]) if colunas["snps"] else None
        cromossomo = _clean(linha[colunas["chromosome"]]) if colunas["chromosome"] else ""
        pos_inicio = _to_int(linha[colunas["start"]]) if colunas["start"] else None
        pos_fim = _to_int(linha[colunas["end"]]) if colunas["end"] else None
        fonte = _clean(linha[colunas["source"]]) if colunas["source"] else ""

        registrada = evidencias.setdefault(chave_nome, {}).setdefault(chave_kit, {
            "kit": kit or None,
            "person_name_csv": nome,
            "source": fonte or None,
            "total_cm": 0.0,
            "segments": [],
            "records_used": 0,
        })
        # SEM `round` no acumulado: `tests/test_formatacao_cm.py` congela o
        # contrato de que o float somado permanece exato (19.200000000000003) e
        # que o arredondamento acontece so na formatacao de saida. Arredondar
        # aqui quebraria a paridade contra o oraculo congelado.
        registrada["total_cm"] = registrada["total_cm"] + cm
        registrada["records_used"] += 1
        registrada["segments"].append({
            "chromosome": cromossomo or None,
            "start": pos_inicio,
            "end": pos_fim,
            "cm": cm,
            "snps": snps,
        })
        if fonte and not registrada["source"]:
            registrada["source"] = fonte

    for chave_nome, por_kit in evidencias.items():
        kits = list(por_kit)
        if len(kits) > 1 and ("multiplos_kits", chave_nome) not in vistos:
            vistos.add(("multiplos_kits", chave_nome))
            avisos.append({
                "code": "multiplos_kits",
                "message": ("O mesmo nome aparece associado a mais de um kit "
                            f"({', '.join(k for k in kits if k != SEM_KIT) or 'kit não informado'}). "
                            "Cada combinação pessoa + kit foi mantida separada; os segmentos nunca "
                            "foram somados entre kits diferentes."),
            })
        if kits == [SEM_KIT] and ("kit_ausente", chave_nome) not in vistos:
            vistos.add(("kit_ausente", chave_nome))
            avisos.append({
                "code": "kit_ausente",
                "message": ("O CSV não traz coluna de kit nem de e-mail: os segmentos foram agrupados "
                            "apenas pelo nome. Se duas pessoas diferentes compartilharem o nome, os "
                            "valores podem estar somados indevidamente."),
            })
        for ev in por_kit.values():
            ev["segments"].sort(key=lambda s: (s["cm"] is None, -(s["cm"] or 0)))
            com_cm = [s for s in ev["segments"] if s["cm"] is not None]
            ev["segment_count"] = len(ev["segments"])
            ev["largest_segment_cm"] = com_cm[0]["cm"] if com_cm else None
            ev["snps_total"] = sum(s["snps"] for s in ev["segments"] if s["snps"]) or None
            ev["snps_largest_segment"] = com_cm[0]["snps"] if com_cm else None
            ev["chromosomes"] = sorted({s["chromosome"] for s in ev["segments"] if s["chromosome"]},
                                       key=lambda c: (len(c), c))
            ev["method"] = (f"soma de {ev['records_used']} linha(s) do CSV com o mesmo nome e o mesmo kit"
                            if ev["records_used"] > 1 else "valor da única linha do CSV para este kit")
            if ev["largest_segment_cm"] is not None and ev["largest_segment_cm"] < LIMITE_SEGMENTO_FRACO:
                ev["weak_segment"] = True

    return evidencias, avisos


def evidence_for(dossie: dict, avisos=None, kit_key: str = None) -> dict:
    """Evidencia de UM dossie (o dict por kit de `build_genetic_evidence`).

    Sem `kit_key`, junta todos os kits **sem somar cM entre eles**: devolve a
    lista de kits separada e deixa `totals["cm"]` como None quando ha mais de um,
    que e o numero honesto quando nao se sabe qual kit e a pessoa do GEDCOM.
    """
    if not dossie:
        return {
            "available": False,
            "source": None,
            "kits": [],
            "totals": {"cm": None, "cm_por_kit": {}, "segments": 0, "largest_segment_cm": None,
                       "chromosomes": [], "records_used": 0},
            "warnings": [{"code": "sem_evidencia",
                          "message": "Sem evidência genética disponível para esta pessoa."}],
        }

    escolhidos = [dossie[kit_key]] if kit_key and kit_key in dossie else list(dossie.values())
    kits = sorted(escolhidos, key=lambda e: e["total_cm"], reverse=True)
    total = kits[0]["total_cm"] if len(kits) == 1 else None

    avisos_do_kit = []
    if len(kits) > 1:
        avisos_do_kit.append({
            "code": "multiplos_kits",
            "message": ("Há mais de um kit para este nome e não é possível dizer qual deles é a pessoa "
                        "do GEDCOM. Cada kit aparece separado e nenhum total foi somado entre kits."),
        })
    for k in kits:
        if k.get("weak_segment"):
            avisos_do_kit.append({
                "code": "segmento_fraco",
                "message": (f"O maior segmento do kit {k['kit'] or 'sem kit'} tem menos de "
                            f"{LIMITE_SEGMENTO_FRACO:g} cM. Segmentos pequenos podem ser falso positivo "
                            "e sustentam mal qualquer conclusão de parentesco."),
            })

    return {
        "available": True,
        "source": kits[0]["source"] or "fonte não identificada no CSV",
        "kits": kits,
        "totals": {
            "cm": total,
            "cm_por_kit": {k["kit"] or SEM_KIT: k["total_cm"] for k in kits},
            "segments": sum(k["segment_count"] for k in kits),
            "largest_segment_cm": max((k["largest_segment_cm"] or 0) for k in kits) or None,
            "chromosomes": sorted({c for k in kits for c in k["chromosomes"]}, key=lambda c: (len(c), c)),
            "records_used": sum(k["records_used"] for k in kits),
        },
        "warnings": avisos_do_kit + list(avisos or []),
    }


__all__ = ["build_genetic_evidence", "evidence_for", "detect_segment_columns",
           "LIMITE_SEGMENTO_FRACO", "SEM_KIT"]
