"""Verificacao das correcoes da auditoria (A001, A002, A003, A007, A008).

Confere: cobertura de IDs entre os artefatos, contagens do actions.md, integridade das tabelas
Markdown que eu editei a mao, e o front matter YAML do bug registrado.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
FEATURE = RAIZ / "_reversa_forward" / "011-escolher-arquivo-da-lista"
BUG = RAIZ / "_reversa_bugs" / "upload-gedcom" / "bugs" / "BUG-20261009-6RKP-nome-com-acento-nao-resolve"

falhas: list[str] = []


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def conferir(condicao: bool, mensagem: str) -> None:
    print(("  OK    " if condicao else "  FALHA ") + mensagem)
    if not condicao:
        falhas.append(mensagem)


# ---------------------------------------------------------------- 1. IDs definidos x citados
print("1. Cobertura de identificadores")

req = ler(FEATURE / "requirements.md")
road = ler(FEATURE / "roadmap.md")
act = ler(FEATURE / "actions.md")

rfs = sorted(set(re.findall(r"\bRF-0\d\b", req)))
rns = sorted(set(re.findall(r"\bRN-\d\d\b", req)))
ds = sorted(set(re.findall(r"\bD-\d\d\b", road)))

print("   definidos em requirements.md:", " ".join(rfs), "|", " ".join(rns))
print("   definidos em roadmap.md:", " ".join(ds))

for alvo in rfs:
    conferir(alvo in road, f"{alvo} citado no roadmap.md")

# Uma RN pode ser coberta por uma decisao (roadmap) OU diretamente por uma acao (actions):
# o eixo 1.1 da auditoria exige que todo RF vire decisao, e nao que toda RN seja citada no roadmap.
orfa_de_plano = [alvo for alvo in rns if alvo not in road and alvo not in act]
for alvo in rns:
    onde = "roadmap.md" if alvo in road else ("actions.md" if alvo in act else "NENHUM")
    if onde == "NENHUM":
        # Nao conta como falha DESTA verificacao: e o achado A006 (LOW) da auditoria, deixado
        # em aberto de proposito pelo operador, que autorizou corrigir apenas os tres HIGH.
        print(f"  ABERTO  {alvo} sem citacao no plano (achado A006, LOW, nao autorizado)")
    else:
        conferir(True, f"{alvo} citado no plano (em {onde})")
if orfa_de_plano:
    print(f"   OBSERVACAO: sem citacao no plano -> {orfa_de_plano}  (achado A006 da auditoria, LOW, em aberto)")
for alvo in ds:
    conferir(alvo in act, f"{alvo} citado no actions.md")

# ---------------------------------------------------------------- 2. contagens do actions.md
print("2. Contagens do actions.md")
linhas = act.splitlines()
acoes = []
for linha in linhas:
    if re.search(r"\|\s*\[[ X]\]\s*\|\s*$", linha):
        c = [x.strip() for x in linha.strip().strip("|").split("|")]
        if len(c) == 7:
            acoes.append(c)
conferir(len(acoes) == 43, f"43 acoes reconhecidas pelo detector (achei {len(acoes)})")
marcadas = [c[0] for c in acoes if c[3].strip("`") == "[//]"]
conferir(len(marcadas) == 24, f"24 marcadas [//] (achei {len(marcadas)})")

deps = {c[0]: ([] if c[2].strip() in ("-", "") else [d.strip() for d in c[2].split(",")]) for c in acoes}
ids = {c[0] for c in acoes}
orfaos = {d for lista in deps.values() for d in lista} - ids
conferir(not orfaos, f"nenhuma dependencia orfa (achei {sorted(orfaos)})")

prof: dict[str, int] = {}


def medir(t: str, pilha: tuple[str, ...] = ()) -> int:
    if t in prof:
        return prof[t]
    if t in pilha:
        raise SystemExit("ciclo em " + t)
    prof[t] = 1 if not deps[t] else 1 + max(medir(d, pilha + (t,)) for d in deps[t])
    return prof[t]


maior = max(medir(t) for t in ids)
conferir(maior == 12, f"maior cadeia = 12 (achei {maior})")

alvos: dict[str, list[str]] = {}
for c in acoes:
    if c[0] in marcadas:
        alvos.setdefault(c[4], []).append(c[0])
colisao = {a: v for a, v in alvos.items() if len(v) > 1}
conferir(not colisao, f"nenhuma colisao de arquivo alvo entre [//] (achei {colisao})")

# ---------------------------------------------------------------- 3. integridade das tabelas
print("3. Integridade das tabelas Markdown editadas a mao")
for nome in ("requirements.md", "roadmap.md", "actions.md", "data-delta.md",
             "interfaces/formulario-http.md", "onboarding.md", "audit/cross-check.md"):
    texto = ler(FEATURE / nome)
    linhas_t = texto.splitlines()
    largura: int | None = None
    problemas = []
    for i, linha in enumerate(linhas_t, 1):
        s = linha.strip()
        if not (s.startswith("|") and s.endswith("|")):
            largura = None
            continue
        colunas = len(s.strip("|").split("|"))
        if set(s.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            continue
        if largura is None:
            largura = colunas
        elif colunas != largura:
            problemas.append(f"linha {i}: {colunas} colunas, esperado {largura}")
    conferir(not problemas, f"{nome}: tabelas com largura consistente" + (f" -> {problemas}" if problemas else ""))

# ---------------------------------------------------------------- 4. bug registrado
print("4. Bug registrado")
conferir(BUG.is_dir(), f"pasta do bug existe: {BUG.name}")
bug_md = BUG / "bug.md"
conferir(bug_md.is_file(), "bug.md existe")
texto_bug = ler(bug_md)
m = re.match(r"^---\n(.*?)\n---\n", texto_bug, re.S)
conferir(m is not None, "front matter delimitado por ---")
if m:
    bruto = m.group(1)
    conferir('id: BUG-20261009-6RKP' in bruto, "id canonico presente")
    conferir('display_number: 6' in bruto, "display_number: 6 (maior existente era 5)")
    conferir('status: open' in bruto, "status: open")
    conferir('policy: local-software' in bruto, "closure.policy do README")
    try:
        import yaml  # type: ignore
        dados = yaml.safe_load(bruto)
        conferir(isinstance(dados, dict), "front matter e YAML valido (PyYAML)")
        conferir(dados.get("traceability", {}).get("specs"), "traceability.specs preenchido")
        conferir(dados.get("relationships"), "relacao proposta presente")
    except ImportError:
        print("  (PyYAML ausente; validacao de YAML pulada)")

    # Sem biblioteca YAML no ambiente (conferido nos dois interpretadores), a validacao possivel e
    # ESTRUTURAL: nenhuma tabulacao, e o mesmo conjunto de chaves de topo dos bugs ja registrados.
    conferir("\t" not in bruto, "front matter sem tabulacao (YAML proibe tab para indentar)")
    chaves_novas = {l.split(":")[0] for l in bruto.splitlines() if l and not l.startswith((" ", "-"))}
    referencia = RAIZ / "_reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-upload-sem-limites/bug.md"
    if referencia.is_file():
        ref_txt = ler(referencia)
        mref = re.match(r"^---\n(.*?)\n---\n", ref_txt, re.S)
        if mref:
            chaves_ref = {l.split(":")[0] for l in mref.group(1).splitlines()
                          if l and not l.startswith((" ", "-"))}
            faltando = chaves_ref - chaves_novas
            # `approval` so existe quando ha veredito de spec aprovado por humano (conferido em
            # BUG-20260929-QMLY): o registro novo ainda tem spec_verdict: null.
            if "spec_verdict: null" in bruto:
                faltando.discard("approval")
            conferir(not faltando, f"mesmas chaves de topo do bug ja registrado (faltam: {sorted(faltando)})")

for ev in ("_sonda_forma_do_nome.py", "_sonda_caso_negativo_real.py",
           "_sonda_caso_negativo.py", "cross-check-A007.md"):
    conferir((BUG / "evidence" / ev).is_file(), f"evidence/{ev}")

# ---------------------------------------------------------------- 5. BOM e fontes
print("5. BOM nos arquivos escritos")
for p in [FEATURE / n for n in ("requirements.md", "roadmap.md", "actions.md", "data-delta.md",
                                "onboarding.md", "audit/cross-check.md",
                                "interfaces/formulario-http.md")] + [bug_md,
                                RAIZ / "_reversa_bugs/upload-gedcom/intake/relato-20261009-1526.md"]:
    conferir(not p.read_bytes().startswith(b"\xef\xbb\xbf"), f"sem BOM: {p.name}")

print()
if falhas:
    print(f"RESULTADO: {len(falhas)} FALHA(S)")
    for f in falhas:
        print("  -", f)
    raise SystemExit(1)
print("RESULTADO: tudo conferido")
