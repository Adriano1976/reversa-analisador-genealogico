#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório de Auditoria de Segurança
================================================

Lê um arquivo JSON de achados (ver assets/achados.schema.json e
assets/achados.exemplo.json) e gera o relatório final em PDF, em Markdown,
ou em ambos os formatos.

Uso:
    python3 gerar_relatorio.py --achados achados.json --formato pdf
    python3 gerar_relatorio.py --achados achados.json --formato md
    python3 gerar_relatorio.py --achados achados.json --formato ambos

Opcionais:
    --saida-dir docs/security-audit        (padrão)
    --nome-base relatorio-auditoria-seguranca  (padrão, sem extensão)

Dependências: reportlab, matplotlib (apenas necessárias para --formato pdf/ambos).
Nenhuma dependência externa é necessária para --formato md.
"""

import argparse
import json
import os
import sys
import tempfile
from xml.sax.saxutils import escape

# ---------------------------------------------------------------------------
# Vocabulário fixo — mantém a nomenclatura estável entre execuções
# ---------------------------------------------------------------------------

PALETTE = {
    "critica": "#B91C1C",
    "alta": "#EA580C",
    "media": "#D97706",
    "baixa": "#2563EB",
    "informativa": "#6B7280",
    "ponto_forte": "#059669",
}

SEVERIDADE_LABEL = {
    "critica": "Crítica",
    "alta": "Alta",
    "media": "Média",
    "baixa": "Baixa",
    "informativa": "Informativa",
}

CATEGORIA_LABEL = {
    "banco_sem_tranca": "Banco sem tranca (isolamento de inquilino/dono)",
    "permissao_navegador": "Permissão definida no navegador",
    "idor": "IDOR",
    "chaves_expostas": "Chaves expostas (hardcode)",
    "inputs_sem_tratamento": "Inputs sem tratamento (XSS)",
}

SEVERITY_ORDER = ["critica", "alta", "media", "baixa", "informativa"]
CATEGORY_ORDER = list(CATEGORIA_LABEL.keys())

EMOJI = {
    "critica": "🔴",
    "alta": "🟠",
    "media": "🟡",
    "baixa": "🔵",
    "informativa": "⚪",
    "ponto_forte": "🟢",
}

STACK_FIELD_LABELS = {
    "linguagem": "Linguagem",
    "framework": "Framework",
    "orm": "ORM",
    "autenticacao": "Autenticação",
    "frontend": "Frontend",
    "arquivos_deploy": "Arquivos de deploy",
}


def rotulo_campo_stack(campo):
    return STACK_FIELD_LABELS.get(campo, campo.replace("_", " ").capitalize())


# ---------------------------------------------------------------------------
# Carregamento e agregação
# ---------------------------------------------------------------------------

def carregar_achados(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def contar_por_severidade(achados):
    contagem = {s: 0 for s in SEVERITY_ORDER}
    for a in achados:
        sev = a.get("severidade", "informativa")
        contagem[sev] = contagem.get(sev, 0) + 1
    return contagem


def contar_por_categoria(achados):
    contagem = {c: 0 for c in CATEGORY_ORDER}
    for a in achados:
        cat = a.get("categoria")
        if cat in contagem:
            contagem[cat] += 1
    return contagem


def resumir_pontos_fracos(achados):
    """Deriva um resumo executivo de riscos centrais a partir dos achados
    críticos/altos, caso o achados.json não traga um resumo custom em
    dados['pontos_fracos_resumo']."""
    fracos = {}
    for a in achados:
        if a.get("severidade") in ("critica", "alta"):
            cat = a.get("categoria")
            fracos[cat] = fracos.get(cat, 0) + 1
    linhas = []
    for cat in CATEGORY_ORDER:
        if fracos.get(cat):
            linhas.append(
                f"{CATEGORIA_LABEL.get(cat, cat)}: {fracos[cat]} achado(s) "
                f"crítico(s)/alto(s) — ver seção de achados detalhados."
            )
    return linhas


def montar_texto_issue(numero, issue):
    criterios = "\n".join(f"- [ ] {c}" for c in issue.get("criterios_aceite", []))
    labels = ", ".join(f"`{l}`" for l in issue.get("labels", []))
    return (
        f"--- ISSUE {numero} ---\n"
        f"### {issue.get('titulo', '')}\n\n"
        f"**Labels sugeridas:** {labels}\n\n"
        f"**Descrição**\n{issue.get('descricao', '')}\n\n"
        f"**Evidência**\n{issue.get('evidencia', '')}\n\n"
        f"**Impacto**\n{issue.get('impacto', '')}\n\n"
        f"**Sugestão de correção**\n{issue.get('sugestao_correcao', '')}\n\n"
        f"**Critérios de aceite**\n{criterios}\n"
        f"--- FIM ISSUE {numero} ---"
    )


# ---------------------------------------------------------------------------
# Formato Markdown
# ---------------------------------------------------------------------------

def montar_relatorio_md(dados, nome_relatorio):
    projeto = dados.get("projeto", {})
    achados = dados.get("achados", [])
    pontos_fortes = dados.get("pontos_fortes", [])
    nao_aplicaveis = dados.get("categorias_nao_aplicaveis", [])
    recomendacoes = dados.get("recomendacoes_priorizadas", [])
    issues = dados.get("issues_github", [])

    sev_count = contar_por_severidade(achados)
    cat_count = contar_por_categoria(achados)

    linhas = []
    linhas.append(f"# {nome_relatorio} — {projeto.get('nome', '')}")
    linhas.append("")
    linhas.append(f"**Data:** {projeto.get('data', '')}  ")
    linhas.append(f"**Escopo auditado:** {projeto.get('escopo', '')}")
    linhas.append("")

    stack = projeto.get("stack_detectada", {})
    if stack:
        linhas.append("## Stack detectada")
        for campo, valor in stack.items():
            rotulo = rotulo_campo_stack(campo)
            valor_fmt = ", ".join(valor) if isinstance(valor, list) else valor
            linhas.append(f"- **{rotulo}:** {valor_fmt}")
        linhas.append("")

    if projeto.get("nota_metodologica"):
        linhas.append("## Nota metodológica")
        linhas.append(projeto["nota_metodologica"])
        linhas.append("")

    linhas.append("## Resumo executivo")
    linhas.append("")
    linhas.append("| Severidade | Qtde |")
    linhas.append("|---|---|")
    total = 0
    for s in SEVERITY_ORDER:
        if sev_count.get(s, 0):
            linhas.append(f"| {EMOJI[s]} {SEVERIDADE_LABEL[s]} | {sev_count[s]} |")
            total += sev_count[s]
    linhas.append(f"| **Total** | **{total}** |")
    linhas.append("")

    if total:
        linhas.append("```mermaid")
        linhas.append("pie showData")
        linhas.append('    title Achados por severidade')
        for s in SEVERITY_ORDER:
            if sev_count.get(s, 0):
                linhas.append(f'    "{SEVERIDADE_LABEL[s]}" : {sev_count[s]}')
        linhas.append("```")
        linhas.append("")

    linhas.append("| Categoria | Qtde |")
    linhas.append("|---|---|")
    for c in CATEGORY_ORDER:
        linhas.append(f"| {CATEGORIA_LABEL[c]} | {cat_count.get(c, 0)} |")
    linhas.append("")

    linhas.append("## Pontos fortes")
    if pontos_fortes:
        for p in pontos_fortes:
            arq = f" (`{p['arquivo']}`)" if p.get("arquivo") else ""
            cat_nome = CATEGORIA_LABEL.get(p.get("categoria"), p.get("categoria", ""))
            linhas.append(f"- {EMOJI['ponto_forte']} **{cat_nome}**{arq}: {p.get('descricao', '')}")
    else:
        linhas.append("_Nenhum ponto forte registrado._")
    linhas.append("")

    linhas.append("## Pontos fracos (riscos centrais)")
    resumo_fracos = dados.get("pontos_fracos_resumo") or resumir_pontos_fracos(achados)
    if resumo_fracos:
        for linha in resumo_fracos:
            linhas.append(f"- {linha}")
    else:
        linhas.append("_Nenhum risco crítico ou alto identificado._")
    linhas.append("")

    linhas.append("## Achados detalhados por categoria")
    for cat in CATEGORY_ORDER:
        linhas.append(f"### {CATEGORIA_LABEL[cat]}")
        na = next((n for n in nao_aplicaveis if n.get("categoria") == cat), None)
        if na:
            linhas.append(f"_Categoria não aplicável a esta stack: {na.get('motivo', '')}_")
            linhas.append("")
            continue
        achados_cat = [a for a in achados if a.get("categoria") == cat]
        if not achados_cat:
            linhas.append("_Nenhum achado encontrado nesta categoria._")
            linhas.append("")
            continue
        linhas.append("| Severidade | Arquivo:linha | Descrição |")
        linhas.append("|---|---|---|")
        for a in achados_cat:
            sev = a.get("severidade", "informativa")
            linhas.append(
                f"| {EMOJI.get(sev, '')} {SEVERIDADE_LABEL.get(sev, sev)} "
                f"| `{a.get('arquivo', '?')}:{a.get('linhas', '?')}` "
                f"| {a.get('descricao', '')} |"
            )
        linhas.append("")

    if recomendacoes:
        linhas.append("## Recomendações priorizadas")
        for r in recomendacoes:
            linhas.append(f"**{r.get('prioridade', '')} — {r.get('titulo', '')}**  ")
            linhas.append(r.get("descricao", ""))
            linhas.append("")

    if issues:
        linhas.append("## Issues para o GitHub")
        linhas.append("")
        for i, issue in enumerate(issues, start=1):
            linhas.append(montar_texto_issue(i, issue))
            linhas.append("")

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Formato PDF (reportlab + matplotlib)
# ---------------------------------------------------------------------------

def _gerar_grafico_rosca(contagem, caminho_saida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels, sizes, cores = [], [], []
    for sev in SEVERITY_ORDER:
        if contagem.get(sev, 0) > 0:
            labels.append(f"{SEVERIDADE_LABEL[sev]} ({contagem[sev]})")
            sizes.append(contagem[sev])
            cores.append(PALETTE[sev])
    if not sizes:
        labels, sizes, cores = ["Nenhum achado"], [1], ["#E5E7EB"]

    fig, ax = plt.subplots(figsize=(4.2, 3.6), dpi=150)
    wedges, _ = ax.pie(
        sizes, colors=cores, startangle=90,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5),
    )
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
              fontsize=8, frameon=False)
    ax.set_title("Achados por severidade", fontsize=11, fontweight="bold", color="#111827")
    fig.tight_layout()
    fig.savefig(caminho_saida, transparent=True)
    plt.close(fig)


def _gerar_grafico_barras(contagem, caminho_saida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [CATEGORIA_LABEL[c].split(" (")[0] for c in CATEGORY_ORDER]
    valores = [contagem.get(c, 0) for c in CATEGORY_ORDER]

    from matplotlib.ticker import MaxNLocator

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    barras = ax.bar(range(len(labels)), valores, color="#374151", width=0.6)
    ax.set_xticks(range(len(labels)))
    rotulos = [l if len(l) < 24 else l[:22] + "…" for l in labels]
    ax.set_xticklabels(rotulos, rotation=25, ha="right", fontsize=7.5)
    ax.set_ylabel("Nº de achados", fontsize=9)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(bottom=0, top=max(valores) + 1 if max(valores) else 1)
    ax.set_title("Achados por categoria", fontsize=11, fontweight="bold", color="#111827")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for barra, valor in zip(barras, valores):
        if valor:
            ax.text(barra.get_x() + barra.get_width() / 2, valor, str(valor),
                    ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(caminho_saida, transparent=True)
    plt.close(fig)


def _cabecalho_rodape(nome_relatorio):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors

    def desenhar(canvas_obj, doc):
        canvas_obj.saveState()
        largura, altura = A4
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#6B7280"))
        canvas_obj.drawString(2 * cm, altura - 1.3 * cm, nome_relatorio)
        canvas_obj.drawRightString(largura - 2 * cm, 1.3 * cm, f"Página {doc.page}")
        canvas_obj.setStrokeColor(colors.HexColor("#E5E7EB"))
        canvas_obj.line(2 * cm, altura - 1.5 * cm, largura - 2 * cm, altura - 1.5 * cm)
        canvas_obj.line(2 * cm, 1.7 * cm, largura - 2 * cm, 1.7 * cm)
        canvas_obj.restoreState()

    return desenhar


def _texto_mono_paragrafo(texto, estilo):
    escapado = escape(texto).replace("\n", "<br/>")
    from reportlab.platypus import Paragraph
    return Paragraph(escapado, estilo)


def _tabela_achados(achados_categoria, estilos):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle, Paragraph

    dados = [["Severidade", "Arquivo:linha", "Descrição"]]
    severidades_por_linha = []
    for a in achados_categoria:
        sev = a.get("severidade", "informativa")
        dados.append([
            SEVERIDADE_LABEL.get(sev, sev).upper(),
            Paragraph(f"{a.get('arquivo', '?')}:{a.get('linhas', '?')}", estilos["CelulaMono"]),
            Paragraph(a.get("descricao", ""), estilos["Celula"]),
        ])
        severidades_por_linha.append(sev)

    tabela = Table(dados, colWidths=[2.6 * cm, 4.4 * cm, 9.5 * cm], repeatRows=1)
    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, sev in enumerate(severidades_por_linha, start=1):
        cor = colors.HexColor(PALETTE.get(sev, "#6B7280"))
        comandos.append(("BACKGROUND", (0, i), (0, i), cor))
        comandos.append(("TEXTCOLOR", (0, i), (0, i), colors.white))
        comandos.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        comandos.append(("ALIGN", (0, i), (0, i), "CENTER"))
    tabela.setStyle(TableStyle(comandos))
    return tabela


def montar_pdf(dados, nome_relatorio, caminho_saida):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
        TableStyle, Image, PageBreak, ListFlowable, ListItem,
    )

    projeto = dados.get("projeto", {})
    achados = dados.get("achados", [])
    pontos_fortes = dados.get("pontos_fortes", [])
    nao_aplicaveis = dados.get("categorias_nao_aplicaveis", [])
    recomendacoes = dados.get("recomendacoes_priorizadas", [])
    issues = dados.get("issues_github", [])

    sev_count = contar_por_severidade(achados)
    cat_count = contar_por_categoria(achados)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TituloCapa", parent=styles["Title"], fontSize=22, leading=26,
                               textColor=colors.HexColor("#111827")))
    styles.add(ParagraphStyle("Subtitulo", parent=styles["Normal"], fontSize=11, leading=15,
                               textColor=colors.HexColor("#374151"), spaceAfter=4))
    styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, spaceBefore=14,
                               spaceAfter=8, textColor=colors.HexColor("#111827")))
    styles.add(ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11.5, spaceBefore=10,
                               spaceAfter=6, textColor=colors.HexColor("#1F2937")))
    styles.add(ParagraphStyle("Corpo", parent=styles["Normal"], fontSize=9.5, leading=13.5))
    styles.add(ParagraphStyle("Celula", parent=styles["Normal"], fontSize=8, leading=10.5))
    styles.add(ParagraphStyle("CelulaMono", parent=styles["Normal"], fontName="Courier",
                               fontSize=7.5, leading=10))
    styles.add(ParagraphStyle("Mono", parent=styles["Normal"], fontName="Courier", fontSize=7.8,
                               leading=10.5, backColor=colors.HexColor("#F3F4F6"),
                               borderPadding=6))
    styles.add(ParagraphStyle("ItalicoFraco", parent=styles["Normal"], fontSize=9,
                               textColor=colors.HexColor("#6B7280")))

    doc = BaseDocTemplate(caminho_saida, pagesize=A4,
                           leftMargin=2 * cm, rightMargin=2 * cm,
                           topMargin=2 * cm, bottomMargin=2 * cm,
                           title=f"{nome_relatorio} — {projeto.get('nome', '')}")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    template = PageTemplate(id="padrao", frames=[frame], onPage=_cabecalho_rodape(nome_relatorio))
    doc.addPageTemplates([template])

    story = []

    # --- Capa ---------------------------------------------------------
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(f"{nome_relatorio}", styles["TituloCapa"]))
    story.append(Paragraph(f"— {projeto.get('nome', '')}", styles["TituloCapa"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"<b>Data:</b> {projeto.get('data', '')}", styles["Subtitulo"]))
    story.append(Paragraph(f"<b>Escopo auditado:</b> {projeto.get('escopo', '')}", styles["Subtitulo"]))
    stack = projeto.get("stack_detectada", {})
    if stack:
        partes = []
        for campo, valor in stack.items():
            rotulo = rotulo_campo_stack(campo)
            valor_fmt = ", ".join(valor) if isinstance(valor, list) else valor
            partes.append(f"<b>{rotulo}:</b> {valor_fmt}")
        story.append(Spacer(1, 0.4 * cm))
        for p in partes:
            story.append(Paragraph(p, styles["Subtitulo"]))
    if projeto.get("nota_metodologica"):
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("<b>Nota metodológica</b>", styles["H3"]))
        story.append(Paragraph(projeto["nota_metodologica"], styles["Corpo"]))
    story.append(PageBreak())

    # --- Resumo executivo ---------------------------------------------
    story.append(Paragraph("Resumo executivo", styles["H2"]))
    total = sum(sev_count.values())
    linhas_resumo = [["Severidade", "Qtde"]]
    for s in SEVERITY_ORDER:
        if sev_count.get(s, 0):
            linhas_resumo.append([SEVERIDADE_LABEL[s], str(sev_count[s])])
    linhas_resumo.append(["Total", str(total)])
    tabela_resumo = Table(linhas_resumo, colWidths=[4 * cm, 2 * cm])
    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(tabela_resumo)
    story.append(Spacer(1, 0.4 * cm))

    tmp = tempfile.mkdtemp(prefix="auditoria-seguranca-")
    caminho_rosca = os.path.join(tmp, "rosca.png")
    caminho_barras = os.path.join(tmp, "barras.png")
    _gerar_grafico_rosca(sev_count, caminho_rosca)
    _gerar_grafico_barras(cat_count, caminho_barras)
    img_rosca = Image(caminho_rosca, width=8 * cm, height=6.9 * cm)
    img_barras = Image(caminho_barras, width=9.5 * cm, height=5.7 * cm)
    graficos = Table([[img_rosca, img_barras]], colWidths=[8.2 * cm, 9.5 * cm])
    graficos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(graficos)

    # --- Pontos fortes / fracos ----------------------------------------
    story.append(Paragraph("Pontos fortes", styles["H2"]))
    if pontos_fortes:
        itens = []
        for p in pontos_fortes:
            arq = f" (<font face='Courier'>{p['arquivo']}</font>)" if p.get("arquivo") else ""
            cat_nome = CATEGORIA_LABEL.get(p.get("categoria"), p.get("categoria", ""))
            itens.append(ListItem(Paragraph(f"<b>{cat_nome}</b>{arq}: {p.get('descricao', '')}",
                                             styles["Corpo"])))
        story.append(ListFlowable(itens, bulletColor=colors.HexColor(PALETTE["ponto_forte"]),
                                   bulletType="bullet"))
    else:
        story.append(Paragraph("Nenhum ponto forte registrado.", styles["ItalicoFraco"]))

    story.append(Paragraph("Pontos fracos (riscos centrais)", styles["H2"]))
    resumo_fracos = dados.get("pontos_fracos_resumo") or resumir_pontos_fracos(achados)
    if resumo_fracos:
        itens = [ListItem(Paragraph(linha, styles["Corpo"])) for linha in resumo_fracos]
        story.append(ListFlowable(itens, bulletColor=colors.HexColor(PALETTE["critica"]),
                                   bulletType="bullet"))
    else:
        story.append(Paragraph("Nenhum risco crítico ou alto identificado.", styles["ItalicoFraco"]))
    story.append(PageBreak())

    # --- Achados detalhados ---------------------------------------------
    story.append(Paragraph("Achados detalhados por categoria", styles["H2"]))
    for cat in CATEGORY_ORDER:
        story.append(Paragraph(CATEGORIA_LABEL[cat], styles["H3"]))
        na = next((n for n in nao_aplicaveis if n.get("categoria") == cat), None)
        if na:
            story.append(Paragraph(f"Categoria não aplicável a esta stack: {na.get('motivo', '')}",
                                    styles["ItalicoFraco"]))
            continue
        achados_cat = [a for a in achados if a.get("categoria") == cat]
        if not achados_cat:
            story.append(Paragraph("Nenhum achado encontrado nesta categoria.", styles["ItalicoFraco"]))
            continue
        story.append(_tabela_achados(achados_cat, styles))
        story.append(Spacer(1, 0.3 * cm))

    # --- Recomendações ---------------------------------------------------
    if recomendacoes:
        story.append(PageBreak())
        story.append(Paragraph("Recomendações priorizadas", styles["H2"]))
        for r in recomendacoes:
            story.append(Paragraph(f"{r.get('prioridade', '')} — {r.get('titulo', '')}", styles["H3"]))
            story.append(Paragraph(r.get("descricao", ""), styles["Corpo"]))

    # --- Issues para o GitHub ---------------------------------------------
    if issues:
        story.append(PageBreak())
        story.append(Paragraph("Issues para o GitHub", styles["H2"]))
        story.append(Paragraph(
            "Texto pronto para copiar e colar na criação de cada issue.",
            styles["ItalicoFraco"]))
        story.append(Spacer(1, 0.2 * cm))
        for i, issue in enumerate(issues, start=1):
            texto = montar_texto_issue(i, issue)
            story.append(_texto_mono_paragrafo(texto, styles["Mono"]))
            story.append(Spacer(1, 0.35 * cm))

    try:
        doc.build(story)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gera o relatório de auditoria de segurança.")
    parser.add_argument("--achados", required=True, help="Caminho para o achados.json")
    parser.add_argument("--formato", choices=["pdf", "md", "ambos"], required=True)
    parser.add_argument("--saida-dir", default="docs/security-audit")
    parser.add_argument("--nome-base", default="relatorio-auditoria-seguranca")
    parser.add_argument("--nome-relatorio", default="Relatório de Auditoria de Segurança",
                         help="Título usado no cabeçalho de cada página do PDF e no topo do Markdown.")
    args = parser.parse_args()

    dados = carregar_achados(args.achados)
    os.makedirs(args.saida_dir, exist_ok=True)

    gerados = []

    if args.formato in ("md", "ambos"):
        caminho_md = os.path.join(args.saida_dir, f"{args.nome_base}.md")
        conteudo = montar_relatorio_md(dados, args.nome_relatorio)
        with open(caminho_md, "w", encoding="utf-8") as f:
            f.write(conteudo)
        gerados.append(caminho_md)
        print(f"[ok] Markdown gerado: {caminho_md}")

    if args.formato in ("pdf", "ambos"):
        caminho_pdf = os.path.join(args.saida_dir, f"{args.nome_base}.pdf")
        montar_pdf(dados, args.nome_relatorio, caminho_pdf)
        gerados.append(caminho_pdf)
        print(f"[ok] PDF gerado: {caminho_pdf}")

        # Verificação básica: número de páginas (a checagem visual/rasterização
        # fica a cargo de quem chama o script — ver instruções no SKILL.md).
        try:
            from pypdf import PdfReader
            paginas = len(PdfReader(caminho_pdf).pages)
            print(f"[info] O PDF tem {paginas} página(s).")
        except Exception as exc:  # biblioteca de verificação é opcional
            print(f"[aviso] Não foi possível verificar o número de páginas automaticamente: {exc}")

    print("\nArquivos gerados:")
    for g in gerados:
        print(f"  - {os.path.abspath(g)}")


if __name__ == "__main__":
    main()
