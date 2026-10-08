
import json, os, re, sys

W = sys.argv[1]; GED = sys.argv[2]; OUT = sys.argv[3]
sys.path.insert(0, os.path.join(W, "src"))
os.chdir(os.path.join(W, ".parity-run-cand"))

from parsers import gedcom_parser as GP
from core.registro import get_name
from core import family_navigation as FN
from core import path_finding as PF
from core import dna_analysis as D
from core.cm_estimator import get_relationships_by_cm as _cm_rel
from utils import text_cleaning as DM

obs = {}
def jsonable(v):
    """Idem ao coletor do oraculo — ver comentario extenso la.

    Os DOIS lados precisam da MESMA normalizacao. Se so um lado ordenar, o diff
    acusa divergencia de ordem que e artefato do coletor, nao do sistema.
    """
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, (set, frozenset)):
        return sorted(jsonable(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    return v

def safo(fn, *a, **k):
    try:
        return {"ok": True, "v": jsonable(fn(*a, **k))}
    except Exception as e:
        return {"ok": False, "e": type(e).__name__}

# A arvore como VALOR: o parse a DEVOLVE (feature 005, `T009`) e nao ha mais
# estado global (`T023`). Todo probe deste coletor le daqui.
#
# `names` era o retorno da casca `GP.load_gedcom_and_build_graph`, removida em
# `T015` da feature 006. A derivacao abaixo e a MESMA que a casca fazia, sobre a
# mesma arvore, entao o probe `names` continua comparando o mesmo valor com o
# oraculo. O ganho colateral e que o coletor deixou de parsear DUAS vezes por
# fixture: antes, a casca parseava uma vez e `carregar_arvore` parseava de novo.
arvore = GP.carregar_arvore(GED)
people, families, graph, child_to_family = arvore
names = sorted([get_name(p) for p in people.values()])
obs["person_count"] = len(people)
obs["family_count"] = len(families)
obs["names"] = names
obs["graph"] = {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()}
obs["child_to_family"] = {k: sorted(v) for k, v in sorted(child_to_family.items())}

ids = sorted(people.keys())
obs["get_name"] = {i: (get_name(people[i]) if get_name(people[i]) is not None else None) for i in ids}
obs["get_parents"] = {i: sorted(FN.get_parents(arvore, i) or []) for i in ids}
obs["get_spouses"] = {i: sorted(FN.get_spouses(arvore, i) or []) for i in ids}

obs["norm_name"] = {n: safo(D.norm_name, n) for n in names}
# ATENCAO — equivalente correto de `strip_bad_utf`:
#   O oraculo tem UMA funcao `strip_bad_utf` (L62-81) que faz o dicionario de fixes
#   de mojibake E a limpeza de nao-alfanumericos.
#   A reconstrucao DIVIDIU isso em duas, e a unificacao veio depois:
#     - `dna_analysis.strip_bad_utf` = copia fiel do oraculo  <-- ESTE e o equivalente
#     - `text_cleaning.strip_bad_utf` e `text_cleaning.demojibake` = a autoridade unica
#
#   HISTORICO, e nao vale mais como aviso: entre a OPP-20260929-ZV52 e a
#   OPP-20260929-B5F2 as duas implementacoes divergiam, e comparar a do modulo de
#   limpeza com o oraculo gerava falso positivo, porque uma delas apenas removia
#   U+FFFD. A B5F2 unificou os corpos. Medido em 2026-10-03:
#       D.strip_bad_utf is DM.strip_bad_utf  ->  True
#       D.demojibake   is DM.demojibake     ->  True
#   Sao o mesmo objeto, entao qualquer um dos dois serve de probe. O probe usado
#   abaixo continua sendo `D.strip_bad_utf`.
obs["strip_bad_utf"] = {n: safo(D.strip_bad_utf, n) for n in names}
obs["demojibake"] = {n: safo(D.demojibake, n) for n in names}
obs["split_name_pt"] = {n: safo(lambda x: list(D.split_name_pt(x)), n) for n in names}
obs["surnames_set"] = {n: safo(lambda x: sorted(D.surnames_set(x)), n) for n in names}
obs["top_given_tokens"] = {n: safo(lambda x: D.top_given_tokens(x), n) for n in names}
obs["token_prefixes"] = {n: safo(lambda x: sorted(D.token_prefixes(x or [])), n) for n in names}
obs["drop_short_tokens"] = {n: safo(lambda x: sorted(D.drop_short_tokens(x or [])), n) for n in names}
obs["surname_core_tokens"] = {n: safo(lambda x: D.surname_core_tokens(x), n) for n in names}

obs["cm"] = {}
for cm in json.loads(sys.argv[4]):
    obs["cm"][str(cm)] = safo(_cm_rel, cm)

obs["ancestral"] = {}
obs["indirect"] = {}
sample = ids[:int(os.environ.get("PARITY_SAMPLE", "40"))]
for a in sample:
    for b in sample:
        r = PF.find_ancestral_path(arvore, a, b)
        obs["ancestral"][a + "|" + b] = [list(r[0]) if r[0] else None, r[1]]
        q = PF.find_indirect_path(arvore, a, b)
        obs["indirect"][a + "|" + b] = list(q) if q else None

# ------------------------------------------------- probe de aceitacao (rota)
# Espelho do probe do oraculo: executa a ROTA do candidato e captura o mesmo
# contexto de dominio. Aqui tambem NAO se chama `match_candidates` diretamente,
# de proposito — o que se compara e o resultado observavel da analise inteira,
# nos dois lados, pela mesma porta de entrada.
import app as APP

_DNA_DIR = sys.argv[5]
_CTX = {}

def _captura(_template, **ctx):
    _CTX.clear(); _CTX.update(ctx)
    return "<captura>"

def modo(mensagem):
    """Classifica o desfecho pelo MODO, nao pela redacao. Ver o lado do oraculo.

    A ordem dos testes importa pelo mesmo motivo: os casos especificos chegam
    embrulhados na mensagem generica do candidato.
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

APP.render_template = _captura
root_name = os.environ.get("PARITY_ROOT", "Ana Silva")

# O nome do arquivo GEDCOM e DERIVADO DO CONTEUDO no candidato
# (`chave_de_armazenamento`, BUG-QMLY), e o formulario devolve esse nome no POST
# seguinte. Reenviar o nome original daria "Arquivo 'probe.ged' nao existe mais"
# — que nao e divergencia de dominio, e erro de encanamento do probe. O probe
# faz o que o navegador faz: sobe, le o nome devolvido e usa o nome devolvido.
_ged_name = "probe.ged"
with open(GED, encoding="latin-1") as _src, open(os.path.join(os.getcwd(), _ged_name), "w", encoding="latin-1") as _dst:
    _dst.write(_src.read())
with APP.app.test_client() as _cli:
    with open(os.path.join(os.getcwd(), _ged_name), "rb") as _fh:
        _cli.post("/", data={"action": "upload_gedcom", "gedcom": (_fh, _ged_name)},
                  content_type="multipart/form-data")
_ged_name = _CTX.get("gedcom_filename") or _ged_name

obs["dna"] = {}
for _fn in sorted(os.listdir(_DNA_DIR)):
    if not _fn.endswith(".csv"):
        continue
    with APP.app.test_client() as _cli:
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
_affinity = os.path.join(os.path.dirname(GED), "affinity.ged")
obs["decomposicao"] = {"pares": {}, "conjuges": {}}
if os.path.exists(_affinity):
    _ids = sorted(people.keys())
    for _a in _ids:
        for _b in _ids:
            obs["decomposicao"]["conjuges"][_a + "|" + _b] = bool(FN.are_spouses(arvore, _a, _b))
    for _a in _ids:
        for _b in _ids:
            _q = PF.find_indirect_path(arvore, _a, _b)
            if not _q:
                continue
            _l, _r, _c = FN.split_path_by_marriage(arvore, _q)
            obs["decomposicao"]["pares"][_a + "|" + _b] = {
                "caminho": list(_q),
                "esquerda": list(_l) if _l else None,
                "direita": list(_r) if _r else None,
                "casal": list(_c) if _c else None,
            }

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(obs, fh, ensure_ascii=False, sort_keys=True)
print("CANDIDATO coletado: %d pessoas, %d familias" % (obs["person_count"], obs["family_count"]))
