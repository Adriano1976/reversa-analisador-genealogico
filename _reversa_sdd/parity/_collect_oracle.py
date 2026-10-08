
import importlib.util, json, os, re, shutil, sys

W = sys.argv[1]; GED = sys.argv[2]; OUT = sys.argv[3]
tmp = os.path.join(W, ".parity-run-oracle")
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
local = os.path.join(tmp, "oracle.py")
shutil.copyfile(os.path.join(W, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py"), local)
os.chdir(tmp)  # neutraliza os.makedirs("uploads"/"static") relativo do oraculo
spec = importlib.util.spec_from_file_location("oracle", local)
m = importlib.util.module_from_spec(spec); sys.modules["oracle"] = m
spec.loader.exec_module(m)

def jsonable(v):
    """Torna um retorno serializavel E deterministico, recursivamente.

    Por que recursivo: `split_name_pt` devolve a TUPLA (given, surnames, {suffixes}).
    Um `list()` simples no primeiro nivel deixa o `set` de sufixos intacto la dentro,
    e `set` (a) nao e serializavel em JSON e (b) tem ordem de iteracao dependente do
    PYTHONHASHSEED, que varia ENTRE PROCESSOS. Ordenar aqui e obrigatorio, senao a
    mesma entrada produz ordem diferente no subprocesso do oraculo e no do candidato,
    e o diff acusa divergencia de ordem onde nao ha divergencia de comportamento.

    `set`/`frozenset` -> lista ordenada (sem ordem = sem contrato).
    `list`/`tuple`    -> lista na ORDEM ORIGINAL (ordem = contrato, nao alterar).
    """
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, (set, frozenset)):
        return sorted(jsonable(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    return v

obs = {}
def safo(fn, *a, **k):
    try:
        return {"ok": True, "v": jsonable(fn(*a, **k))}
    except Exception as e:
        return {"ok": False, "e": type(e).__name__}

names = m.load_gedcom_and_build_graph(GED)
obs["person_count"] = len(m.people)
obs["family_count"] = len(m.families)
obs["names"] = names
obs["graph"] = {"nodes": m.graph.number_of_nodes(), "edges": m.graph.number_of_edges()}
obs["child_to_family"] = {k: sorted(v) for k, v in sorted(m.child_to_family.items())}

ids = sorted(m.people.keys())
obs["get_name"] = {i: safo(m.get_name, m.people[i])["v"] if m.get_name(m.people[i]) is not None else None for i in ids}
obs["get_parents"] = {i: sorted(m.get_parents(i) or []) for i in ids}
obs["get_spouses"] = {i: sorted(m.get_spouses(i) or []) for i in ids}

obs["norm_name"] = {n: safo(m.norm_name, n) for n in names}
obs["strip_bad_utf"] = {n: safo(m.strip_bad_utf, n) for n in names}
obs["demojibake"] = {n: safo(m.demojibake, n) for n in names}
obs["split_name_pt"] = {n: safo(lambda x: list(m.split_name_pt(x)), n) for n in names}
obs["surnames_set"] = {n: safo(lambda x: sorted(m.surnames_set(x)), n) for n in names}
obs["top_given_tokens"] = {n: safo(lambda x: m.top_given_tokens(x), n) for n in names}
obs["token_prefixes"] = {n: safo(lambda x: sorted(m.token_prefixes(x or [])), n) for n in names}
obs["drop_short_tokens"] = {n: safo(lambda x: sorted(m.drop_short_tokens(x or [])), n) for n in names}
obs["surname_core_tokens"] = {n: safo(lambda x: m.surname_core_tokens(x), n) for n in names}

obs["cm"] = {}
for cm in json.loads(sys.argv[4]):
    obs["cm"][str(cm)] = safo(m.get_relationships_by_cm, cm)

obs["ancestral"] = {}
obs["indirect"] = {}
sample = ids[:int(os.environ.get("PARITY_SAMPLE", "40"))]
for a in sample:
    for b in sample:
        r = m.find_ancestral_path(a, b)
        obs["ancestral"][a + "|" + b] = [list(r[0]) if r[0] else None, r[1]]
        q = m.find_indirect_path(a, b)
        obs["indirect"][a + "|" + b] = list(q) if q else None

shutil.rmtree(tmp, ignore_errors=True)
# ------------------------------------------------- probe de aceitacao (rota)
# A decisao de aceitacao do legado vive INLINE dentro da rota `POST /`
# (app_legacy_e43ca22.py:695-796): o oraculo NAO expoe `match_candidates` nem
# `build_ged_indexes`. Um probe que transcrevesse aquele bloco para o coletor
# seria circular. A saida e executar a ROTA e capturar o contexto de dominio que
# ela entrega ao template, sem renderizar HTML — o que casa com a regra do
# parity_specs.md ("asserir sobre comportamento de dominio, nunca sobre HTML").
_DNA_DIR = sys.argv[5]
_CTX = {}

def _captura(_template, **ctx):
    _CTX.clear(); _CTX.update(ctx)
    return "<captura>"

def modo(mensagem):
    """Classifica o desfecho pelo MODO, nao pela redacao.

    A ORDEM dos testes importa: `raiz_ausente` e `arquivo_ausente` sao casos
    ESPECIFICOS que chegam embrulhados na mensagem generica do candidato
    ("Ocorreu um erro: Seu nome ... nao foi encontrado"). Se o teste generico
    vier primeiro, ele captura os dois e apaga a distincao que interessa.

    O legado fecha a analise com `Ocorreu um erro: None` (a excecao do pandas nao
    tem texto); o candidato nomeia a causa. A decisao de DOMINIO e a mesma, e a
    diferenca e de redacao, que o parity_specs.md manda asserir fora da
    comparacao.
    """
    m = mensagem or ""
    # `seu nome ... nao foi encontrado` e o aviso da RAIZ. Precisa ser especifico:
    # a mensagem de colunas do CSV diz "Colunas de Nome e cM nao encontradas", e
    # "nao encontrada" e SUBSTRING de "nao encontradas" — um teste por substring
    # simples confundiria os dois casos. Foi o que aconteceu na primeira versao.
    if re.search(r"seu nome.*n[ãa]o foi encontrad", m, re.I):
        return "raiz_ausente"
    if "não existe mais" in m or m.startswith("Erro: Arquivo") or "Arquivo GEDCOM" in m:
        return "arquivo_ausente"
    if "Por favor, carregue" in m or "Nenhum arquivo" in m:
        return "sem_arquivo"
    if "Ocorreu um erro" in m or "Erro ao processar GEDCOM" in m:
        return "erro"
    if "conexões encontradas" in m:
        return "ok"
    return "outro"

m.render_template = _captura
m.UPLOAD_FOLDER = tmp
root_name = os.environ.get("PARITY_ROOT", "Ana Silva")

obs["dna"] = {}
for _fn in sorted(os.listdir(_DNA_DIR)):
    if not _fn.endswith(".csv"):
        continue
    _ged_name = "probe.ged"
    with open(GED, encoding="latin-1") as _src, open(os.path.join(tmp, _ged_name), "w", encoding="latin-1") as _dst:
        _dst.write(_src.read())
    with m.app.test_client() as _cli:
        with open(os.path.join(_DNA_DIR, _fn), "rb") as _fh:
            _cli.post("/", data={
                "action": "dna_analysis",
                "gedcom_filename": _ged_name,
                "root_name": root_name,
                "matches_csv": (_fh, _fn),
            })
    obs["dna"][_fn] = {
        "success": _CTX.get("success"),
        "modo": modo(_CTX.get("message")),
        "results": [{
            "match_name": r.get("match_name"),
            "cm": float(r.get("cm")) if r.get("cm") is not None else None,
            "caminho": r.get("text_path"),
        } for r in (_CTX.get("dna_results") or [])],
        "descartados": [{
            "csv_name": s.get("csv_name"),
            "motivo": s.get("motivo"),
        } for s in (_CTX.get("skipped_matches") or [])],
    }

# --------------------------------------- probe de decomposicao do caminho
# `are_spouses` e `split_path_by_marriage` existem NOS DOIS lados com a mesma
# assinatura, entao aqui o probe e direto (ao contrario do de aceitacao). Ele
# existe por causa do RISK-011: nenhum cenario de matching falharia se a
# decomposicao desaparecesse, porque o matching continuaria correto.
_affinity = os.path.join(os.path.dirname(GED), "affinity.ged")
obs["decomposicao"] = {"pares": {}, "conjuges": {}}
if os.path.exists(_affinity):
    _ids = sorted(m.people.keys())
    for _a in _ids:
        for _b in _ids:
            obs["decomposicao"]["conjuges"][_a + "|" + _b] = bool(m.are_spouses(_a, _b))
    for _a in _ids:
        for _b in _ids:
            _q = m.find_indirect_path(_a, _b)
            if not _q:
                continue
            _l, _r, _c = m.split_path_by_marriage(_q)
            obs["decomposicao"]["pares"][_a + "|" + _b] = {
                "caminho": list(_q),
                "esquerda": list(_l) if _l else None,
                "direita": list(_r) if _r else None,
                "casal": list(_c) if _c else None,
            }

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(obs, fh, ensure_ascii=False, sort_keys=True)
print("ORACLE coletado: %d pessoas, %d familias" % (obs["person_count"], obs["family_count"]))
