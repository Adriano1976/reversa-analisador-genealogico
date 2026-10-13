"""Gera as views do registro de bugs seguindo o protocolo do `/reversa-debugger-graph`.

Este script e a implementacao do protocolo descrito em
`.agents/skills/reversa-debugger-graph/SKILL.md`: validar invariantes de forma GLOBAL,
gerar as views do contexto pedido e o espelho do lado da spec.

Escopo desta execucao: `seguranca` (o unico contexto novo) mais o espelho global
`_reversa_sdd/traceability/bugs.md`. Os contextos `upload-gedcom`, `analise-dna` e
`busca-caminho` NAO sao regenerados aqui: as views deles ja existem de 2026-10-10 e o
protocolo permite escopo por contexto ("com argumento, regenere so aquele contexto").

Nao depende de PyYAML (nao esta instalado no `.venv/`): o front matter e lido por um
subconjunto proprio, suficiente para o schema do `bug.md` (mapas por indentacao, listas,
`- chave: valor` e escalares de bloco `>` e `|`).

Uso:
    python gerar_views.py [--contexto seguranca] [--somente-espelho]
"""
from __future__ import annotations

import argparse
import html
import json
import os
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRO = os.path.join(RAIZ, "_reversa_bugs")
ESPELHO = os.path.join(RAIZ, "_reversa_sdd", "traceability", "bugs.md")

CORES = {
    "critical": "#f2545b",
    "high": "#f2545b",
    "medium": "#e6b422",
    "low": "#7f8c8d",
}


# ---------------------------------------------------------------------------
# Leitura do front matter
# ---------------------------------------------------------------------------

def _indentacao(linha):
    return len(linha) - len(linha.lstrip(" "))


def _e_linha_vazia(linha):
    return not linha.strip() or linha.strip().startswith("#")


def _valor_escalar(texto):
    texto = texto.strip()
    if texto.startswith('"') and texto.endswith('"'):
        return texto[1:-1]
    if texto.startswith("'") and texto.endswith("'"):
        return texto[1:-1]
    if texto in ("null", "~", ""):
        return None
    if texto == "true":
        return True
    if texto == "false":
        return False
    if texto.startswith("[") and texto.endswith("]"):
        interno = texto[1:-1].strip()
        if not interno:
            return []
        return [_valor_escalar(parte) for parte in interno.split(",")]
    if texto.isdigit():
        return int(texto)
    return texto


def _ler_bloco(linhas, indice, indentacao):
    """Le um escalar de bloco (`>`, `>-`, `|`, `|-`) a partir da linha seguinte."""
    coletado = []
    while indice < len(linhas):
        linha = linhas[indice]
        if _e_linha_vazia(linha):
            coletado.append("")
            indice += 1
            continue
        if _indentacao(linha) <= indentacao:
            break
        coletado.append(linha.strip())
        indice += 1
    while coletado and not coletado[-1]:
        coletado.pop()
    return " ".join(parte for parte in coletado if parte), indice


def _ler_mapa(linhas, indice, indentacao):
    resultado = {}
    while indice < len(linhas):
        linha = linhas[indice]
        if _e_linha_vazia(linha):
            indice += 1
            continue
        if _indentacao(linha) < indentacao:
            break
        texto = linha.strip()
        if texto.startswith("- "):
            break
        if ":" not in texto:
            indice += 1
            continue
        chave, _, resto = texto.partition(":")
        chave = chave.strip()
        resto = resto.strip()
        indice += 1
        if resto in (">", ">-", "|", "|-", ">+", "|+"):
            valor, indice = _ler_bloco(linhas, indice, _indentacao(linha))
            resultado[chave] = valor
            continue
        if resto:
            resultado[chave] = _valor_escalar(resto)
            continue
        # chave sem valor: mapa ou lista, decidido pela proxima linha util
        proximo = indice
        while proximo < len(linhas) and _e_linha_vazia(linhas[proximo]):
            proximo += 1
        if proximo < len(linhas) and _indentacao(linhas[proximo]) > _indentacao(linha):
            if linhas[proximo].strip().startswith("- "):
                valor, indice = _ler_lista(linhas, proximo, _indentacao(linhas[proximo]))
            else:
                valor, indice = _ler_mapa(linhas, proximo, _indentacao(linhas[proximo]))
            resultado[chave] = valor
        else:
            resultado[chave] = None
    return resultado, indice


def _ler_lista(linhas, indice, indentacao):
    itens = []
    while indice < len(linhas):
        linha = linhas[indice]
        if _e_linha_vazia(linha):
            indice += 1
            continue
        if _indentacao(linha) < indentacao or not linha.strip().startswith("- "):
            break
        resto = linha.strip()[2:].strip()
        indice += 1
        if ":" in resto and not resto.startswith(("http", '"')):
            chave, _, valor = resto.partition(":")
            item = {}
            if valor.strip():
                item[chave.strip()] = _valor_escalar(valor)
            else:
                proximo = indice
                while proximo < len(linhas) and _e_linha_vazia(linhas[proximo]):
                    proximo += 1
                if proximo < len(linhas) and _indentacao(linhas[proximo]) > indentacao:
                    if linhas[proximo].strip().startswith("- "):
                        valor, indice = _ler_lista(linhas, proximo, _indentacao(linhas[proximo]))
                    else:
                        valor, indice = _ler_mapa(linhas, proximo, _indentacao(linhas[proximo]))
                    item[chave.strip()] = valor
                else:
                    item[chave.strip()] = None
            # continuacao do MESMO item (chaves irmaos mais indentados que o "- ")
            while indice < len(linhas):
                seguinte = linhas[indice]
                if _e_linha_vazia(seguinte) or _indentacao(seguinte) <= indentacao:
                    break
                if seguinte.strip().startswith("- "):
                    break
                extra, indice = _ler_mapa(linhas, indice, _indentacao(seguinte))
                item.update(extra)
                break
            itens.append(item)
        else:
            itens.append(_valor_escalar(resto))
    return itens, indice


def ler_front_matter(caminho):
    with open(caminho, encoding="utf-8") as fh:
        linhas = fh.read().splitlines()
    if not linhas or linhas[0].strip() != "---":
        return {}
    fim = 1
    while fim < len(linhas) and linhas[fim].strip() != "---":
        fim += 1
    dados, _ = _ler_mapa(linhas[1:fim], 0, 0)
    return dados


def carregar_bugs():
    bugs = []
    for contexto in sorted(os.listdir(REGISTRO)):
        pasta_contexto = os.path.join(REGISTRO, contexto)
        pasta_bugs = os.path.join(pasta_contexto, "bugs")
        if not os.path.isdir(pasta_bugs):
            continue
        for pasta in sorted(os.listdir(pasta_bugs)):
            caminho = os.path.join(pasta_bugs, pasta, "bug.md")
            if not os.path.isfile(caminho):
                continue
            dados = ler_front_matter(caminho)
            dados["_contexto"] = contexto
            dados["_pasta"] = os.path.join(pasta_bugs, pasta)
            dados["_caminho"] = caminho
            dados["_relativo"] = os.path.relpath(caminho, RAIZ).replace("\\", "/")
            dados["_pasta_relativa"] = os.path.relpath(
                os.path.join(pasta_bugs, pasta), RAIZ).replace("\\", "/")
            dados["_travado"] = os.path.isfile(os.path.join(pasta_bugs, pasta, "DONE.md"))
            bugs.append(dados)
    return bugs


# ---------------------------------------------------------------------------
# Validacao de invariantes (sempre global)
# ---------------------------------------------------------------------------

def validar(bugs):
    erros = []
    vistos = {}
    for bug in bugs:
        identificador = bug.get("id")
        if identificador in vistos:
            erros.append(f"ID duplicado: {identificador} em {bug['_relativo']} e {vistos[identificador]}")
        vistos[identificador] = bug["_relativo"]
        if bug.get("schema_version") != 1:
            erros.append(f"{identificador}: schema_version desconhecida ({bug.get('schema_version')})")
        if bug.get("status") == "resolved":
            if not bug.get("resolution_kind"):
                erros.append(f"{identificador}: resolved sem resolution_kind")
            if not (bug.get("closure") or {}).get("satisfied"):
                erros.append(f"{identificador}: resolved sem closure.satisfied")
        if bug.get("resolution_kind") == "fixed":
            rastreio = bug.get("traceability") or {}
            causa = rastreio.get("root_cause")
            if not (isinstance(causa, dict) and causa.get("state") == "confirmed"):
                erros.append(f"{identificador}: resolution_kind fixed sem root_cause confirmed")
            if not rastreio.get("regression_tests"):
                erros.append(f"{identificador}: resolution_kind fixed sem regression_tests")
            if not bug.get("spec_verdict"):
                erros.append(f"{identificador}: resolution_kind fixed sem spec_verdict")
        if bug["_travado"] and bug.get("status") != "resolved":
            erros.append(f"{identificador}: DONE.md com status {bug.get('status')}")
        if not bug["_travado"] and bug.get("status") == "resolved" \
                and (bug.get("closure") or {}).get("satisfied"):
            erros.append(f"{identificador}: resolved satisfeito sem DONE.md")

    for bug in bugs:
        for relacao in bug.get("relationships") or []:
            if not isinstance(relacao, dict):
                continue
            alvo = relacao.get("bug")
            if alvo == bug.get("id"):
                erros.append(f"{bug.get('id')}: autorrelacao")
            elif alvo not in vistos:
                erros.append(f"{bug.get('id')}: relacao com ID inexistente ({alvo})")
    return erros


# ---------------------------------------------------------------------------
# Helpers de prosa
# ---------------------------------------------------------------------------

def cabecalho(quantidade, momento):
    return ("<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-debugger-graph em "
            f"{momento} a partir de {quantidade} bugs -->")


def _prioridade(bug):
    return bug.get("priority") or "-"


def _resumo(bug):
    return f"{bug.get('area')}/{bug.get('module')}/{bug.get('feature')}"


def _bloqueado(bug):
    return "sim" if bug.get("blocking") else "nao"


def _rotulo_restrito(bug):
    return f"`{bug.get('id')}` | restrito"


# ---------------------------------------------------------------------------
# Views do contexto
# ---------------------------------------------------------------------------

def gerar_catalog(bugs_contexto, contexto, momento):
    linhas = [cabecalho(len(bugs_contexto), momento)]
    for bug in sorted(bugs_contexto, key=lambda b: b.get("display_number") or 0):
        if bug.get("visibility") == "restricted":
            registro = {
                "schema_version": bug.get("schema_version"),
                "id": bug.get("id"),
                "display_number": bug.get("display_number"),
                "status": bug.get("status"),
                "severity": bug.get("severity"),
                "priority": bug.get("priority"),
                "visibility": "restricted",
                "security_suspected": bug.get("security_suspected"),
                "contexto": contexto,
                "path": bug["_relativo"],
                "restrito": True,
            }
        else:
            registro = {
                "schema_version": bug.get("schema_version"),
                "id": bug.get("id"),
                "display_number": bug.get("display_number"),
                "title": bug.get("title"),
                "status": bug.get("status"),
                "phase": bug.get("phase"),
                "severity": bug.get("severity"),
                "priority": bug.get("priority"),
                "created": bug.get("created"),
                "updated": bug.get("updated"),
                "origin": bug.get("origin"),
                "area": bug.get("area"),
                "module": bug.get("module"),
                "feature": bug.get("feature"),
                "labels": bug.get("labels"),
                "visibility": bug.get("visibility"),
                "security_suspected": bug.get("security_suspected"),
                "reproduction": bug.get("reproduction"),
                "blocking": bug.get("blocking"),
                "relationships": bug.get("relationships"),
                "traceability": bug.get("traceability"),
                "spec_verdict": bug.get("spec_verdict"),
                "closure": bug.get("closure"),
                "resolution_kind": bug.get("resolution_kind"),
                "contexto": contexto,
                "path": bug["_relativo"],
                "restrito": False,
            }
        linhas.append(json.dumps(registro, ensure_ascii=False))
    return "\n".join(linhas) + "\n"


def gerar_index(bugs_contexto, contexto, momento, erros):
    visiveis = [b for b in bugs_contexto if b.get("visibility") != "restricted"]
    restritos = [b for b in bugs_contexto if b.get("visibility") == "restricted"]
    por_status, por_phase = {}, {}
    for bug in bugs_contexto:
        por_status[bug.get("status")] = por_status.get(bug.get("status"), 0) + 1
        por_phase[bug.get("phase")] = por_phase.get(bug.get("phase"), 0) + 1

    linhas = [cabecalho(len(bugs_contexto), momento), "", f"# Indice de bugs: {contexto}", ""]
    linhas.append("## Resumo")
    linhas.append("")
    linhas.append("| Status | Quantidade |")
    linhas.append("|---|---|")
    for chave in sorted(por_status):
        linhas.append(f"| `{chave}` | {por_status[chave]} |")
    linhas.append("")
    linhas.append("| Phase | Quantidade |")
    linhas.append("|---|---|")
    for chave in sorted(por_phase, key=lambda c: str(c)):
        linhas.append(f"| `{chave}` | {por_phase[chave]} |")
    linhas.append("")

    abertos = [b for b in visiveis if b.get("status") in ("open", "active")]
    linhas.append("## Bugs abertos / ativos")
    linhas.append("")
    if abertos:
        linhas.append("| # | ID | Prioridade | Severidade | area/module/feature | Titulo | Caminho | Bloqueado |")
        linhas.append("|---|---|---|---|---|---|---|---|")
        for bug in sorted(abertos, key=lambda b: b.get("display_number") or 0):
            linhas.append(
                f"| {bug.get('display_number')} | `{bug.get('id')}` | {_prioridade(bug)} | "
                f"{bug.get('severity')} | {_resumo(bug)} | {bug.get('title')} | "
                f"`{bug['_pasta_relativa']}` | {_bloqueado(bug)} |")
    else:
        linhas.append("Nenhum bug aberto ou ativo visivel neste contexto.")
    linhas.append("")

    resolvidos = [b for b in visiveis if b.get("status") == "resolved"]
    linhas.append("## Resolvidos")
    linhas.append("")
    if resolvidos:
        contagem = {}
        for bug in resolvidos:
            contagem[bug.get("resolution_kind")] = contagem.get(bug.get("resolution_kind"), 0) + 1
        linhas.append("| resolution_kind | Quantidade |")
        linhas.append("|---|---|")
        for chave in sorted(contagem, key=lambda c: str(c)):
            linhas.append(f"| `{chave}` | {contagem[chave]} |")
        linhas.append("")
        for bug in sorted(resolvidos, key=lambda b: b.get("display_number") or 0):
            linhas.append(f"- `{bug.get('id')}` ({bug.get('resolution_kind')}): {bug.get('title')}")
    else:
        linhas.append("Nenhum bug resolvido neste contexto.")
    linhas.append("")

    linhas.append("## Bugs com visibilidade restrita")
    linhas.append("")
    if restritos:
        linhas.append("Estes aparecem apenas como identificador, sem titulo nem detalhe, "
                      "conforme o contrato do registro.")
        linhas.append("")
        for bug in sorted(restritos, key=lambda b: b.get("display_number") or 0):
            linhas.append(f"- {_rotulo_restrito(bug)}")
    else:
        linhas.append("Nenhum.")
    linhas.append("")

    if erros:
        linhas.append("## Inconsistencias")
        linhas.append("")
        for erro in erros:
            linhas.append(f"- {erro}")
        linhas.append("")
    return "\n".join(linhas)


def gerar_matrix(bugs_contexto, todos, momento):
    por_id = {b.get("id"): b for b in todos}
    linhas = [cabecalho(len(bugs_contexto), momento), "", "# Matriz de relacoes BUG a BUG", ""]
    linhas.append("| Origem | Tipo | Destino | Estado | Contexto do destino | Evidencia |")
    linhas.append("|---|---|---|---|---|---|")
    total = 0
    for bug in sorted(bugs_contexto, key=lambda b: b.get("display_number") or 0):
        if bug.get("visibility") == "restricted":
            continue
        for relacao in bug.get("relationships") or []:
            if not isinstance(relacao, dict):
                continue
            alvo = por_id.get(relacao.get("bug"))
            if alvo is None or alvo.get("visibility") == "restricted":
                continue
            evidencias = relacao.get("evidence") or []
            referencia = evidencias[0].get("ref") if evidencias and isinstance(evidencias[0], dict) else ""
            total += 1
            linhas.append(
                f"| `{bug.get('id')}` | {relacao.get('type')} | `{relacao.get('bug')}` | "
                f"{relacao.get('state')} | {alvo.get('_contexto')} | `{referencia}` |")
    if total == 0:
        linhas.append("| - | - | - | - | - | - |")
    linhas.append("")
    derivadas = []
    for bug in bugs_contexto:
        if bug.get("visibility") == "restricted":
            continue
        for outro in todos:
            if outro.get("visibility") == "restricted":
                continue
            for relacao in outro.get("relationships") or []:
                if isinstance(relacao, dict) and relacao.get("bug") == bug.get("id") \
                        and relacao.get("type") in ("caused-by", "blocked-by", "duplicate-of",
                                                    "regression-of", "related-to", "conflicts-with"):
                    derivadas.append(
                        f"| `{bug.get('id')}` | {relacao.get('type')} (derivada) | "
                        f"`{outro.get('id')}` | {relacao.get('state')} | {outro.get('_contexto')} | - |")
    linhas.append("## Inversas derivadas")
    linhas.append("")
    linhas.append("| Origem | Tipo | Destino | Estado | Contexto do destino | Evidencia |")
    linhas.append("|---|---|---|---|---|---|")
    if derivadas:
        linhas.extend(derivadas)
    else:
        linhas.append("| - | - | - | - | - | - |")
    linhas.append("")
    return "\n".join(linhas)


def _impacto(bug, todos):
    pesos = {"caused-by": 3, "blocked-by": 2, "regression-of": 4, "related-to": 1}
    total, relacionados = 0, 0
    for relacao in bug.get("relationships") or []:
        if not isinstance(relacao, dict):
            continue
        if relacao.get("state") not in ("supported", "confirmed"):
            continue
        peso = pesos.get(relacao.get("type"), 0)
        if relacao.get("type") == "related-to":
            if relacionados >= 3:
                continue
            relacionados += 1
        total += peso
    for outro in todos:
        for relacao in outro.get("relationships") or []:
            if isinstance(relacao, dict) and relacao.get("bug") == bug.get("id") \
                    and relacao.get("state") in ("supported", "confirmed"):
                total += pesos.get(relacao.get("type"), 0)
    return total


def gerar_graph_md(bugs_contexto, todos, momento):
    por_id = {b.get("id"): b for b in todos}
    visiveis = [b for b in bugs_contexto if b.get("visibility") != "restricted"]
    arestas = []
    for bug in visiveis:
        for relacao in bug.get("relationships") or []:
            if not isinstance(relacao, dict):
                continue
            alvo = por_id.get(relacao.get("bug"))
            if alvo is None or alvo.get("visibility") == "restricted":
                continue
            arestas.append((bug, relacao, alvo))

    linhas = [cabecalho(len(bugs_contexto), momento), "", "# Grafo de relacoes", "", "```mermaid", "graph LR"]
    nos = set()
    for bug, relacao, alvo in arestas:
        nos.add(bug.get("id"))
        nos.add(alvo.get("id"))
    for identificador in sorted(nos):
        bug = por_id.get(identificador)
        rotulo = f"{bug.get('id')} {bug.get('severity')}"
        linhas.append(f'    {identificador.replace("-", "_")}["{rotulo}"]')
    for bug, relacao, alvo in arestas:
        origem = bug.get("id").replace("-", "_")
        destino = alvo.get("id").replace("-", "_")
        seta = "-->" if relacao.get("state") in ("supported", "confirmed") else "-.->"
        linhas.append(f"    {origem} {seta}|{relacao.get('type')}| {destino}")
    if not arestas:
        linhas.append("    vazio[\"nenhuma relacao visivel neste contexto\"]")
    linhas.extend(["```", ""])

    linhas.append("## Clusters")
    linhas.append("")
    if arestas:
        for bug, relacao, alvo in arestas:
            linhas.append(
                f"- `{bug.get('id')}` converge com `{alvo.get('id')}` ({alvo.get('_contexto')}) "
                f"por `{relacao.get('type')}` no estado `{relacao.get('state')}`.")
    else:
        linhas.append("- Nenhuma aresta visivel: os bugs restritos deste contexto nao entram nas views.")
    linhas.append("")

    linhas.append("## Impact score")
    linhas.append("")
    linhas.append("Heuristica de triagem (`causados*3 + bloqueados*2 + regressoes*4 + relacionados*1`, "
                  "somando apenas arestas `supported`/`confirmed`, com `related-to` limitado a 3). "
                  "Nao substitui `priority` nem `severity`.")
    linhas.append("")
    linhas.append("| Bug | Impact score |")
    linhas.append("|---|---|")
    for bug in sorted(visiveis, key=lambda b: -_impacto(b, todos)):
        linhas.append(f"| `{bug.get('id')}` | {_impacto(bug, todos)} |")
    if not visiveis:
        linhas.append("| - | 0 |")
    linhas.append("")
    return "\n".join(linhas)


def gerar_spec_matrix(bugs_contexto, momento):
    visiveis = [b for b in bugs_contexto if b.get("visibility") != "restricted"]
    linhas = [cabecalho(len(bugs_contexto), momento), "", "# Matriz BUG a SPEC", ""]
    linhas.append("| Secao de spec | open | active | resolved |")
    linhas.append("|---|---|---|---|")
    secoes = {}
    sem_spec = []
    for bug in visiveis:
        specs = (bug.get("traceability") or {}).get("specs") or []
        rotulos = bug.get("labels") or []
        if not specs or "spec-gap" in rotulos:
            sem_spec.append(bug)
        if not specs:
            continue
        for spec in specs:
            secoes.setdefault(spec, {"open": [], "active": [], "resolved": []})
            estado = bug.get("status") if bug.get("status") in ("open", "active", "resolved") else "open"
            secoes[spec][estado].append(bug.get("id"))
    for spec in sorted(secoes):
        colunas = secoes[spec]
        linhas.append(
            f"| `{spec}` | {', '.join(colunas['open']) or '-'} | "
            f"{', '.join(colunas['active']) or '-'} | {', '.join(colunas['resolved']) or '-'} |")
    linhas.append(f"| **spec-gap** (sem spec) | {', '.join(b.get('id') for b in sem_spec) or '-'} | - | - |")
    linhas.append("")
    return "\n".join(linhas)


def gerar_graph_html(bugs_contexto, todos, contexto, momento, erros):
    por_id = {b.get("id"): b for b in todos}
    visiveis = [b for b in bugs_contexto if b.get("visibility") != "restricted"]
    restritos = [b for b in bugs_contexto if b.get("visibility") == "restricted"]

    nos, arestas = [], []
    for bug in visiveis:
        nos.append({"id": bug.get("id"), "numero": bug.get("display_number"),
                    "titulo": bug.get("title"), "severidade": bug.get("severity"),
                    "status": bug.get("status"), "resolucao": bug.get("resolution_kind"),
                    "contexto": bug.get("_contexto"), "caminho": bug["_relativo"],
                    "externo": False})
        for relacao in bug.get("relationships") or []:
            if not isinstance(relacao, dict):
                continue
            alvo = por_id.get(relacao.get("bug"))
            if alvo is None or alvo.get("visibility") == "restricted":
                continue
            if alvo.get("id") not in [n["id"] for n in nos]:
                nos.append({"id": alvo.get("id"), "numero": alvo.get("display_number"),
                            "titulo": alvo.get("title"), "severidade": alvo.get("severity"),
                            "status": alvo.get("status"), "resolucao": alvo.get("resolution_kind"),
                            "contexto": alvo.get("_contexto"), "caminho": alvo["_relativo"],
                            "externo": True})
            arestas.append({"de": bug.get("id"), "para": alvo.get("id"),
                            "tipo": relacao.get("type"), "estado": relacao.get("state")})

    largura, altura = 1000, 380
    posicoes = {}
    colunas = max(len(nos), 1)
    for indice, no in enumerate(nos):
        x = int((indice + 0.5) * (largura / colunas))
        y = 190 if indice % 2 == 0 else 110
        posicoes[no["id"]] = (x, y)

    svg = [f'<svg viewBox="0 0 {largura} {altura}" width="100%" height="auto" role="img" '
           f'aria-label="Grafo de bugs do contexto {html.escape(contexto)}">',
           '<defs><marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
           'markerHeight="7" orient="auto-start-reverse">'
           '<path d="M 0 0 L 10 5 L 0 10 z" fill="#8fa3b8"/></marker></defs>']
    for aresta in arestas:
        if aresta["de"] not in posicoes or aresta["para"] not in posicoes:
            continue
        x1, y1 = posicoes[aresta["de"]]
        x2, y2 = posicoes[aresta["para"]]
        tracejado = ' stroke-dasharray="6 4"' if aresta["estado"] == "proposed" else ""
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#8fa3b8" '
                   f'stroke-width="1.6" marker-end="url(#seta)"{tracejado}/>')
        svg.append(f'<text x="{(x1 + x2) // 2}" y="{(y1 + y2) // 2 - 6}" fill="#8fa3b8" '
                   f'font-size="11" text-anchor="middle">{html.escape(str(aresta["tipo"]))}'
                   f' ({html.escape(str(aresta["estado"]))})</text>')
    for no in nos:
        x, y = posicoes[no["id"]]
        cor = CORES.get(no["severidade"], "#7f8c8d")
        if no["status"] == "resolved":
            estado_cor = "#2ecc71"
        elif no["status"] == "active":
            estado_cor = "#e6b422"
        else:
            estado_cor = "#f2545b"
        sufixo = str(no["id"]).split("-")[-1]
        titulo = html.escape(str(no["titulo"])[:44])
        svg.append(f'<a href="../../../{no["caminho"]}">')
        svg.append(f'<rect x="{x - 130}" y="{y - 34}" width="260" height="70" rx="9" '
                   f'fill="#16202b" stroke="{cor}" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y - 14}" fill="#e8eef5" font-size="13" '
                   f'text-anchor="middle">#{no["numero"]} {html.escape(sufixo)}'
                   f'{" (contexto " + html.escape(str(no["contexto"])) + ")" if no["externo"] else ""}</text>')
        svg.append(f'<text x="{x}" y="{y + 4}" fill="#c7d3e0" font-size="11" '
                   f'text-anchor="middle">{titulo}</text>')
        rotulo_estado = (f'{no["status"]} · {no["resolucao"]}' if no["resolucao"]
                         else str(no["status"]))
        svg.append(f'<text x="{x}" y="{y + 22}" fill="{estado_cor}" font-size="11" '
                   f'text-anchor="middle">{html.escape(rotulo_estado)} · '
                   f'{html.escape(str(no["severidade"]))}</text>')
        svg.append("</a>")
    svg.append("</svg>")

    abertos = [b for b in visiveis if b.get("status") in ("open", "active")]
    travados = [b for b in visiveis if b["_travado"]]
    linhas_tabela = []
    for bug in sorted(abertos, key=lambda b: b.get("display_number") or 0):
        linhas_tabela.append(
            f'<tr><td>{bug.get("display_number")}</td>'
            f'<td><a href="../../../{bug["_relativo"]}">{html.escape(str(bug.get("id")))}</a></td>'
            f'<td>{html.escape(str(bug.get("severity")))}</td>'
            f'<td>{html.escape(str(bug.get("priority")))}</td>'
            f'<td>{html.escape(str(bug.get("title")))}</td>'
            f'<td>{html.escape(_resumo(bug))}</td>'
            f'<td>{html.escape(str(bug.get("status")))}</td></tr>')

    documento = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grafo de Bugs · {html.escape(contexto)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; padding: 24px; background: #0d151d; color: #e8eef5;
         font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; }}
  h2 {{ font-size: 16px; margin: 28px 0 10px; color: #c7d3e0; }}
  .meta {{ color: #8fa3b8; font-size: 13px; margin-bottom: 18px; }}
  .cards {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 8px; }}
  .card {{ background: #16202b; border: 1px solid #24313f; border-radius: 10px;
           padding: 12px 16px; min-width: 140px; }}
  .card .n {{ font-size: 24px; font-weight: 600; }}
  .card .r {{ color: #8fa3b8; font-size: 12px; }}
  .grafo {{ background: #111a23; border: 1px solid #24313f; border-radius: 10px;
            padding: 12px; overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border-bottom: 1px solid #24313f; padding: 7px 9px; text-align: left; }}
  th {{ color: #8fa3b8; font-weight: 600; }}
  a {{ color: #6fb3ff; }}
  .legenda {{ color: #8fa3b8; font-size: 12px; margin-top: 10px; }}
  .restrito {{ color: #e6b422; }}
</style>
</head>
<body>
<h1>Grafo de Bugs · {html.escape(contexto)}</h1>
<div class="meta">Gerado por <code>/reversa-debugger-graph</code> em {html.escape(momento)} ·
{len(bugs_contexto)} bugs no contexto · {len(erros)} inconsistencias ·
legenda: arestas tracejadas = relacao <code>proposed</code> (hipotese)</div>

<div class="cards">
  <div class="card"><div class="n">{len(bugs_contexto)}</div><div class="r">bugs no contexto</div></div>
  <div class="card"><div class="n">{len([b for b in bugs_contexto if b.get("status") == "resolved"])}</div><div class="r">resolved</div></div>
  <div class="card"><div class="n">{len(abertos)}</div><div class="r">abertos / ativos visiveis</div></div>
  <div class="card"><div class="n">{len(restritos)}</div><div class="r">restritos (fora das views)</div></div>
  <div class="card"><div class="n">{len(erros)}</div><div class="r">inconsistencias</div></div>
</div>

<h2>Grafo</h2>
<div class="grafo">
{chr(10).join(svg)}
<div class="legenda">Cada no e um link para o <code>bug.md</code> correspondente. Borda vermelha:
severidade <code>high</code> ou <code>critical</code>; amarela: <code>medium</code>. Nos com
"(contexto ...)" vivem em outro contexto e aparecem aqui por causa da relacao.</div>
</div>

<h2>Bugs abertos / ativos</h2>
<table>
<thead><tr><th>#</th><th>ID</th><th>Severidade</th><th>Prioridade</th><th>Titulo</th>
<th>area/module/feature</th><th>Status</th></tr></thead>
<tbody>
{chr(10).join(linhas_tabela) if linhas_tabela else '<tr><td colspan="7">Nenhum bug aberto visivel.</td></tr>'}
</tbody>
</table>

<h2>Concluidos (travados)</h2>
<table>
<thead><tr><th>#</th><th>ID</th><th>resolution_kind</th><th>Titulo</th></tr></thead>
<tbody>
{chr(10).join(f'<tr><td>{b.get("display_number")}</td><td><a href="../../../{b["_relativo"]}">{html.escape(str(b.get("id")))}</a></td><td>{html.escape(str(b.get("resolution_kind")))}</td><td>{html.escape(str(b.get("title")))}</td></tr>' for b in travados) if travados else '<tr><td colspan="4">Nenhum bug travado neste contexto.</td></tr>'}
</tbody>
</table>
<p class="legenda restrito">{len(restritos)} bug(s) com <code>visibility: restricted</code> ficam
fora desta view; no <code>index.md</code> do contexto eles aparecem apenas como identificador.</p>
</body>
</html>
"""
    return documento


# ---------------------------------------------------------------------------
# Espelho do lado da spec
# ---------------------------------------------------------------------------

def gerar_espelho(todos, momento):
    visiveis = [b for b in todos if b.get("visibility") != "restricted"]
    excluidos = len(todos) - len(visiveis)
    por_spec = {}
    for bug in visiveis:
        for spec in (bug.get("traceability") or {}).get("specs") or []:
            por_spec.setdefault(spec, []).append(bug)
    linhas = [cabecalho(len(todos), momento), "", "# Bugs por artefato de spec", ""]
    linhas.append(f"> Gerado em `{momento}`. Espelho derivado de `_reversa_bugs/*/bugs/*/bug.md`.")
    if excluidos:
        linhas.append(f"> Bugs com `visibility: restricted` nao entram neste espelho: "
                      f"{excluidos} dos {len(todos)} bugs varridos foram excluidos.")
    linhas.append("")
    for spec in sorted(por_spec):
        linhas.append(f"## `{spec}`")
        linhas.append("")
        for bug in sorted(por_spec[spec], key=lambda b: b.get("display_number") or 0):
            estado = bug.get("resolution_kind") or bug.get("status")
            situacao = (f"{bug.get('status')}/{estado}" if bug.get("resolution_kind")
                        else str(bug.get("status")))
            linhas.append(
                f"- `{bug.get('id')}` ({situacao}, {_prioridade(bug)}): "
                f"{bug.get('title')} -> `{bug['_relativo']}`")
        linhas.append("")
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------

def gravar(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(conteudo)


def main():
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--contexto", default="seguranca")
    analisador.add_argument("--somente-espelho", action="store_true")
    argumentos = analisador.parse_args()

    momento = datetime.now().astimezone().isoformat(timespec="seconds")
    todos = carregar_bugs()
    erros = validar(todos)
    contexto = argumentos.contexto
    bugs_contexto = [b for b in todos if b["_contexto"] == contexto]
    if not bugs_contexto:
        raise SystemExit(f"nenhum bug no contexto {contexto}")

    destino = os.path.join(REGISTRO, contexto, "generated")
    if not argumentos.somente_espelho:
        gravar(os.path.join(destino, "catalog.jsonl"),
               gerar_catalog(bugs_contexto, contexto, momento))
        gravar(os.path.join(destino, "index.md"),
               gerar_index(bugs_contexto, contexto, momento, erros))
        gravar(os.path.join(destino, "matrix.md"),
               gerar_matrix(bugs_contexto, todos, momento))
        gravar(os.path.join(destino, "graph.md"),
               gerar_graph_md(bugs_contexto, todos, momento))
        gravar(os.path.join(destino, "graph.html"),
               gerar_graph_html(bugs_contexto, todos, contexto, momento, erros))
        gravar(os.path.join(destino, "spec-matrix.md"),
               gerar_spec_matrix(bugs_contexto, momento))
    gravar(ESPELHO, gerar_espelho(todos, momento))

    print(json.dumps({
        "contexto": contexto,
        "bugs_varridos": len(todos),
        "bugs_no_contexto": len(bugs_contexto),
        "inconsistencias": erros,
        "views": sorted(os.listdir(destino)) if not argumentos.somente_espelho else [],
        "espelho": os.path.relpath(ESPELHO, RAIZ).replace("\\", "/"),
        "momento": momento,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
