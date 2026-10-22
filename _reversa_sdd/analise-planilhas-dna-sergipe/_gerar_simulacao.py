"""Gera a simulação estática do pacote mínimo SEM FamilySearch.

Lê o CSV real de `src/uploads` (o tipo de arquivo que o operador envia), calcula os
números do painel de cobertura e monta um HTML autocontido com ANTES e DEPOIS.

Não é o app: é uma simulação de tela. Os números vêm todos do arquivo real.
Uso: python _gerar_simulacao.py
"""
from __future__ import annotations

import collections
import glob
import html
import os
import statistics
import sys
import unicodedata
import warnings

warnings.filterwarnings("ignore")

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.genetic_evidence import build_genetic_evidence  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402

PASTA = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(PASTA, "simulacao-sem-familysearch.html")

# Piso do filtro de endogamia, lido do proprio nucleo.
from core.endogamia import CM_MINIMO_MAIOR_BLOCO, CM_MINIMO_SEGMENTO  # noqa: E402

# ---------------------------------------------------------------------------
# inventario do arquivo real
# ---------------------------------------------------------------------------


def _ascii(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


PLACEHOLDERS = {
    "-", "", "outro (insira o nome abaixo)", "outros", "other (enter name below)",
    "selecione uma empresa ou fonte", "select a company or source",
}

LABORATORIOS = (
    ("genera", "Genera"),
    ("myheritage", "MyHeritage"),
    ("my heritage", "MyHeritage"),
    ("minha heran", "MyHeritage"),
    ("meudna", "meuDNA"),
    ("meu dna", "meuDNA"),
    ("meudna-mandelics", "meuDNA"),
    ("23andme", "23andMe"),
    ("23eeu", "23andMe"),
    ("ftdna", "FTDNA"),
    ("ancestry", "Ancestry"),
    ("familytree", "FamilyTreeDNA"),
    ("living dna", "Living DNA"),
    ("genos", "Genos"),
    ("dna land", "DNA Land"),
    ("mundodna", "MundoDNA"),
)


def canonizar_fonte(valor: str | None) -> tuple[str, str]:
    """Devolve (rotulo, motivo). Motivo explica por que nao virou laboratorio."""
    bruto = "" if valor is None else str(valor)
    chave = _ascii(bruto)
    if not chave or chave in PLACEHOLDERS:
        return "não declarada", "texto de formulário"
    if chave in ("l1b1a", "h", "b2", "a2"):
        return "não declarada", "haplogrupo na coluna de fonte"
    if chave.startswith("migration") or chave in ("ancestralidade", "meu patrimonio"):
        return "não declarada", "nome de projeto, não de laboratório"
    for prefixo, rotulo in LABORATORIOS:
        if prefixo in chave:
            return rotulo, ""
    return "outro", "não reconhecido"


def main() -> None:
    caminho = [p for p in glob.glob(os.path.join(RAIZ, "src", "uploads", "*.csv"))
               if "Sergipanas" in p][0]
    df = read_csv_with_fallback(caminho)
    evidencias, _avisos = build_genetic_evidence(df)
    pessoas = [e for por_kit in evidencias.values() for e in por_kit.values()]
    segmentos = [s for e in pessoas for s in e["segments"]]

    dados = {
        "arquivo": os.path.basename(caminho).split("__")[-1],
        "linhas": df.shape[0],
        "pessoas": len(pessoas),
        "kits": len({e["kit"] for e in pessoas}),
        "segmentos": len(segmentos),
        "abaixo_piso": sum(1 for s in segmentos if s["cm"] < CM_MINIMO_SEGMENTO),
        "maior_abaixo": sum(1 for e in pessoas if (e["largest_segment_cm"] or 0) < CM_MINIMO_MAIOR_BLOCO),
        "snps_abaixo": sum(1 for e in pessoas if (e["snps_total"] or 0) < 900),
        "total_acima_com_maior_abaixo": sum(
            1 for e in pessoas
            if e["total_cm"] >= CM_MINIMO_MAIOR_BLOCO and (e["largest_segment_cm"] or 0) < CM_MINIMO_MAIOR_BLOCO
        ),
        "total_acima": sum(1 for e in pessoas if e["total_cm"] >= CM_MINIMO_MAIOR_BLOCO),
        "mediana": statistics.median([e["total_cm"] for e in pessoas]),
        "cromossomos": len({s["chromosome"] for s in segmentos if s["chromosome"]}),
        "chr_x": sum(1 for s in segmentos if str(s["chromosome"]).upper() in ("X", "23")),
        "sem_cm": 0,
    }

    brutos = collections.Counter(e["source"] for e in pessoas)
    canonicos = collections.Counter(canonizar_fonte(e["source"])[0] for e in pessoas)
    motivos = collections.Counter(canonizar_fonte(e["source"])[1] for e in pessoas if canonizar_fonte(e["source"])[1])
    dados["grafias"] = len(brutos)
    dados["laboratorios"] = len([k for k in canonicos if k not in ("não declarada", "outro")])
    dados["sem_fonte"] = canonicos.get("não declarada", 0) + canonicos.get("outro", 0)

    def cartao(nome: str) -> dict:
        e = next(x for x in pessoas if x["person_name_csv"] == nome)
        acima = [s["cm"] for s in e["segments"] if s["cm"] >= CM_MINIMO_SEGMENTO]
        abaixo = [s["cm"] for s in e["segments"] if s["cm"] < CM_MINIMO_SEGMENTO]
        rotulo, motivo = canonizar_fonte(e["source"])
        return {
            "nome": e["person_name_csv"],
            "total": e["total_cm"],
            "maior": e["largest_segment_cm"],
            "segmentos": e["segment_count"],
            "snps": e["snps_total"] or 0,
            "mrca": e["mrca_generations"],
            "cromossomos": e["chromosomes"],
            "fonte_bruta": e["source"],
            "fonte": rotulo,
            "motivo": motivo,
            "kit": e["kit"],
            "acima": round(sum(acima), 1),
            "abaixo": round(sum(abaixo), 1),
            "n_abaixo": len(abaixo),
            "cm_mediana": statistics.median([s["cm"] for s in e["segments"]]),
        }

    forte = cartao("Clezia Santos")
    parcial = cartao("Airton Passos Vasconcelos")
    dados["forte"] = forte
    dados["parcial"] = parcial
    dados["fontes_tabela"] = canonicos.most_common()
    dados["motivos"] = motivos.most_common()

    pagina = _html(dados)
    try:
        with open(SAIDA, "w", encoding="utf-8") as fh:
            fh.write(pagina)
        print(f"gerado: {SAIDA}")
    except OSError as erro:
        # Ambiente sem permissao de escrita (ex.: sandbox somente-leitura): o HTML vai
        # para a saida padrao, e o chamador decide onde gravar.
        print(f"# nao foi possivel gravar ({erro}); HTML na saida padrao", file=sys.stderr)
        print(pagina)
        return
    print(f"  {dados['linhas']} linhas | {dados['pessoas']} pessoas | {dados['grafias']} grafias de fonte "
          f"| {dados['laboratorios']} laboratórios | {dados['sem_fonte']} sem laboratório")


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#F5F1E6;--surface:#fff;--surface-2:#F8F4E9;--ink:#2A2418;--head:#4A3B1A;
--muted:#6A6150;--line:#DDD4BF;--primary:#3F6B2E;--danger:#A8321F;--aviso-bg:#FBF3DC;
--aviso-line:#A8741F;--sucesso-bg:#EDF4E6;--sucesso-line:#3F6B2E}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 Manrope,system-ui,-apple-system,'Segoe UI',sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:40px 24px 64px}
h1,h2,h3{font-family:'Cormorant Garamond',Georgia,'Times New Roman',serif;color:var(--head);line-height:1.15}
h1{font-size:42px;margin:4px 0 8px}
h2{font-size:29px;margin:0 0 6px}
h3{font-size:21px;margin:0 0 4px}
p{margin:0 0 12px}
code{font-family:ui-monospace,Consolas,monospace;font-size:.88em;background:#EDE7D6;padding:1px 5px;border-radius:4px}
.olho{letter-spacing:.14em;text-transform:uppercase;font-size:12px;color:var(--muted);margin-bottom:6px}
.sub{color:var(--muted);font-size:17px;max-width:72ch}
.secao{margin-top:44px}
.rotulo{display:inline-block;font-size:12px;letter-spacing:.1em;text-transform:uppercase;
padding:3px 9px;border-radius:999px;border:1px solid var(--line);color:var(--muted);margin-bottom:10px}
.rotulo.antes{border-color:#C9BBA0;background:#F1EAD9}
.rotulo.depois{border-color:var(--sucesso-line);background:var(--sucesso-bg);color:var(--primary)}
.cartao{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:22px 24px;
box-shadow:0 1px 0 rgba(0,0,0,.02)}
.cartao + .cartao{margin-top:18px}
.cabeca{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between;
border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:16px}
.fonte{font-size:14px;color:var(--muted)}
.fonte b{color:var(--ink);font-weight:600}
.grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px 18px}
.campo .k{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.campo .v{font-size:19px;font-weight:600}
.campo .v.pequeno{font-size:15px;font-weight:500}
.aviso{border:1px solid var(--aviso-line);background:var(--aviso-bg);border-radius:10px;
padding:12px 14px;margin-top:16px;font-size:14.5px}
.ok{border:1px solid var(--sucesso-line);background:var(--sucesso-bg);border-radius:10px;
padding:10px 14px;margin-top:16px;font-size:14.5px}
.painel{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--primary);
border-radius:12px;padding:20px 24px;margin-bottom:18px}
.painel h3{margin-bottom:12px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:12px}
.tile{background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.tile .n{font-family:'Cormorant Garamond',Georgia,serif;font-size:30px;line-height:1.05;color:var(--head)}
.tile .l{font-size:12.5px;color:var(--muted);margin-top:2px}
.frases{margin-top:16px;padding-top:14px;border-top:1px dashed var(--line);font-size:14.5px}
.frases li{margin-bottom:6px}
table{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--line);
border-radius:12px;overflow:hidden;font-size:14.5px}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--surface-2);font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
tr:last-child td{border-bottom:0}
td.hoje{color:var(--danger)}
td.depois{color:var(--primary);font-weight:600}
.rodape{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13.5px}
.tag{display:inline-block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;
border-radius:999px;padding:2px 8px;border:1px solid var(--line);color:var(--muted)}
"""


def _f(valor, casas=1):
    if valor is None:
        return "não informado"
    if isinstance(valor, str):
        return valor
    return f"{valor:.{casas}f}".replace(".", ",")


def _tile(numero, rotulo):
    return f'<div class="tile"><div class="n">{numero}</div><div class="l">{rotulo}</div></div>'


def _campo(rotulo, valor, pequeno=False):
    classe = "v pequeno" if pequeno else "v"
    return f'<div class="campo"><div class="k">{rotulo}</div><div class="{classe}">{valor}</div></div>'


def _cartao(d, *, depois: bool) -> str:
    fonte_bruta = html.escape(str(d["fonte_bruta"]))

    if depois:
        if d["motivo"]:
            linha_fonte = (f'<b>{html.escape(d["fonte"])}</b> — o arquivo traz '
                           f'<span class="tag">{fonte_bruta}</span> {html.escape(d["motivo"])}')
        else:
            linha_fonte = f'<b>{html.escape(d["fonte"])}</b>'
    else:
        linha_fonte = f'<b>{fonte_bruta}</b>'

    snps_txt = f'{d["snps"]:,}'.replace(",", ".")

    # estado da medida (so no DEPOIS)
    if depois:
        if d["snps"] >= 900 and d["total"] >= CM_MINIMO_MAIOR_BLOCO and d["maior"] >= CM_MINIMO_MAIOR_BLOCO:
            estado = ('<div class="ok"><b>Medida robusta</b> — total '
                      f'{_f(d["total"])} cM, maior segmento {_f(d["maior"])} cM e {snps_txt} SNPs. '
                      'Qualidade da <i>medida</i>, não do parentesco.</div>')
        else:
            faltas = []
            if d["maior"] < CM_MINIMO_MAIOR_BLOCO:
                faltas.append(f'menor bloco de {_f(d["maior"])} cM (abaixo de {_f(CM_MINIMO_MAIOR_BLOCO, 0)})')
            if d["snps"] < 900:
                faltas.append(f'{snps_txt} SNPs (abaixo de 900)')
            if d["total"] < CM_MINIMO_MAIOR_BLOCO:
                faltas.append(f'total de {_f(d["total"])} cM')
            estado = ('<div class="aviso"><b>Medida parcial</b> — ' + "; ".join(faltas) +
                      '. Sustenta menos conclusão que um bloco contíguo grande. '
                      'Qualidade da <i>medida</i>, não do parentesco.</div>')
    else:
        estado = ""

    return f"""
<article class="cartao">
  <div class="cabeca">
    <div><h3>{html.escape(d["nome"])}</h3>
    <div class="fonte">Fonte: {linha_fonte} · Kit <code>{html.escape(str(d["kit"]))}</code></div></div>
  </div>
  <div class="grade">
    {_campo("DNA compartilhado", f'{_f(d["total"])} cM')}
    {_campo("Maior segmento", f'{_f(d["maior"])} cM')}
    {_campo("Segmentos", d["segmentos"])}
    {_campo("SNPs", str(d["snps"]).replace(",", "."))}
    {_campo("MRCA estimado", f'{_f(d["mrca"], 2)} gerações')}
    {_campo("Cromossomo(s)", ", ".join(d["cromossomos"]))}
  </div>
  <div class="aviso">
    <b>Filtro de endogamia</b> — total bruto {_f(d["total"])} cM; após o filtro de
    ≥ {_f(CM_MINIMO_SEGMENTO, 0)} cM por segmento: {_f(d["acima"])} cM.
    {d["n_abaixo"]} segmento(s) abaixo do piso somam {_f(d["abaixo"])} cM.
  </div>
  {estado}
</article>"""


def _html(d) -> str:
    fontes = "".join(
        f'<tr><td>{html.escape(nome)}</td><td class="depois">{n}</td></tr>'
        for nome, n in d["fontes_tabela"]
    )
    motivos = ", ".join(f"{m} ({n})" for m, n in d["motivos"] if m)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Simulação — o arquivo fala de si mesmo (sem FamilySearch)</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<p class="olho">Simulação estática · dados reais de <code>{html.escape(d["arquivo"])}</code></p>
<h1>O arquivo fala de si mesmo</h1>
<p class="sub">Pacote mínimo <b>sem</b> FamilySearch e <b>sem</b> link: vocabulário de fonte,
painel de cobertura do arquivo e estado da medida. Nenhum veredito muda — o que muda é o que a
tela sabe dizer sobre o próprio arquivo.</p>

<section class="secao">
  <span class="rotulo antes">Hoje</span>
  <h2>O cartão mostra o campo como veio</h2>
  <p class="sub">A “Fonte” é exibida literalmente; o texto de formulário
  <code>Outro (insira o nome abaixo)</code> aparece como se fosse o nome do laboratório.
  E o arquivo não diz nada sobre si mesmo: para saber que {d["abaixo_piso"]} de {d["segmentos"]}
  segmentos ficaram abaixo do piso, é preciso abrir o CSV.</p>
  {_cartao(d["parcial"], depois=False)}
</section>

<section class="secao">
  <span class="rotulo depois">Depois</span>
  <h2>Um painel antes dos cartões, e uma linha de qualidade em cada um</h2>

  <div class="painel">
    <h3>O que este arquivo cobre</h3>
    <div class="tiles">
      {_tile(d["linhas"], "linhas no CSV")}
      {_tile(d["pessoas"], "pessoas (nome + kit)")}
      {_tile(d["kits"], "kits distintos")}
      {_tile(f'{d["laboratorios"]}', f'laboratórios em {d["grafias"]} grafias')}
      {_tile(d["cromossomos"], "cromossomos cobertos")}
      {_tile(_f(d["mediana"]), "mediana de cM por pessoa")}
      {_tile(f'{d["abaixo_piso"]/d["segmentos"]*100:.0f}%', f'segmentos abaixo de {_f(CM_MINIMO_SEGMENTO, 0)} cM')}
      {_tile(f'{d["maior_abaixo"]/d["pessoas"]*100:.0f}%', f'sem bloco de {_f(CM_MINIMO_MAIOR_BLOCO, 0)} cM')}
    </div>
    <ul class="frases">
      <li><b>{d["abaixo_piso"]} de {d["segmentos"]}</b> segmentos estão abaixo do piso de
        {_f(CM_MINIMO_SEGMENTO, 0)} cM e são descartados pelo filtro de endogamia.</li>
      <li><b>{d["total_acima_com_maior_abaixo"]} de {d["total_acima"]}</b> pessoas passam de
        {_f(CM_MINIMO_MAIOR_BLOCO, 0)} cM <i>somados</i>, mas nenhum bloco chega a
        {_f(CM_MINIMO_MAIOR_BLOCO, 0)} cM — o total vem de vários blocos pequenos.</li>
      <li><b>{d["snps_abaixo"]}</b> pessoas têm menos de 900 SNPs somados: a chamada do segmento é
        mais frágil que o cM sugere.</li>
      <li>O arquivo <b>não declara o corte</b> usado na busca que o gerou. Ausência de um nome aqui
        não é ausência de parentesco — é ausência <i>neste arquivo</i>.</li>
      <li>{d["sem_fonte"]} células de fonte são texto de formulário, haplogrupo ou nome de projeto:
        {html.escape(motivos)}.</li>
    </ul>
  </div>

  {_cartao(d["parcial"], depois=True)}
  {_cartao(d["forte"], depois=True)}
</section>

<section class="secao">
  <h2>O que muda, campo por campo</h2>
  <table>
    <tr><th>Onde</th><th>Hoje</th><th>Depois</th></tr>
    <tr><td>Fonte do cartão</td><td class="hoje">“Outro (insira o nome abaixo)”</td>
        <td class="depois">“não declarada” + o texto original em etiqueta</td></tr>
    <tr><td>Fonte, no arquivo</td><td class="hoje">{d["grafias"]} grafias para ~{d["laboratorios"]} laboratórios</td>
        <td class="depois">{d["grafias"]} grafias → {d["laboratorios"]} laboratórios + {d["sem_fonte"]} sem laboratório</td></tr>
    <tr><td>Qualidade da medida</td><td class="hoje">ausente (só “segmento fraco” abaixo de 15 cM)</td>
        <td class="depois">robusta · parcial · insuficiente, com os três números</td></tr>
    <tr><td>Cobertura do arquivo</td><td class="hoje">só por cartão</td>
        <td class="depois">painel antes dos cartões, com 8 números e 5 frases</td></tr>
    <tr><td>Corte da busca</td><td class="hoje">não é mencionado</td>
        <td class="depois">“não declarado pelo arquivo”</td></tr>
    <tr><td>Caminho, cM, confronto, viabilidade</td><td class="hoje">como estão</td>
        <td class="depois">inalterados — nenhuma regra de parentesco muda</td></tr>
  </table>
</section>

<section class="secao">
  <h2>Distribuição de fonte, depois de normalizar</h2>
  <table>
    <tr><th>Rótulo exibido</th><th>Pessoas</th></tr>
    {fontes}
  </table>
</section>

<p class="rodape">Simulação estática, sem Bootstrap e sem CDN: abre offline. Números calculados a partir de
<code>{html.escape(d["arquivo"])}</code> com os mesmos módulos do app
(<code>parsers.csv_ingest</code>, <code>core.genetic_evidence</code>) e os pisos de
<code>core.endogamia</code>. O texto da tela real obedece ao template
<code>src/templates/index.html</code>; esta página é uma maquete, não uma captura do app.</p>

</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
