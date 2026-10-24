"""_lib.py - nucleo da skill token-reduce-universal (somente biblioteca padrao).

Contem: estimativa de tokens, protecao de trechos criticos, compressao
deterministica em niveis (engine "lite") e inventario/verificacao de fidelidade.
Nada aqui acessa rede nem instala pacotes.
"""
from __future__ import annotations

import math
import re
from collections import Counter

# --------------------------------------------------------------------------
# Estimativa de tokens
# --------------------------------------------------------------------------

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_PIECE = re.compile(r"[^\W\d_]+|\d{1,3}|[^\w\s]|_", re.UNICODE)


def count_tokens(text: str) -> tuple[int, str]:
    """Retorna (tokens, metodo). Usa tiktoken se funcionar offline; senao estima."""
    try:  # tiktoken pode existir mas precisar baixar o vocabulario
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("o200k_base")
        return len(enc.encode(text)), "tiktoken:o200k_base"
    except Exception:
        pass
    total = 0
    for piece in _PIECE.findall(text):
        if _WORD.fullmatch(piece):
            total += max(1, math.ceil(len(piece) / 5))
        else:
            total += 1
    return total, "estimado"


# --------------------------------------------------------------------------
# Listas de palavras (pt / en / es)
# --------------------------------------------------------------------------

NEGATIONS = {
    "pt": {"não", "nao", "nunca", "nem", "nenhum", "nenhuma", "nenhuns", "nenhumas",
           "sem", "jamais", "nada", "ninguém", "ninguem"},
    "en": {"not", "no", "never", "none", "neither", "nor", "without", "nothing",
           "nobody", "cannot", "can't", "don't", "doesn't", "won't", "isn't",
           "aren't", "shouldn't", "mustn't"},
    "es": {"no", "nunca", "ni", "ningún", "ningun", "ninguna", "ninguno", "sin",
           "jamás", "jamas", "nada", "nadie"},
}
MODALS = {
    "pt": {"deve", "devem", "dever", "obrigatório", "obrigatória", "obrigatorio",
           "proibido", "proibida", "somente", "apenas", "exceto", "salvo", "sempre"},
    "en": {"must", "shall", "should", "required", "mandatory", "forbidden",
           "only", "except", "unless", "always"},
    "es": {"debe", "deben", "obligatorio", "obligatoria", "prohibido", "prohibida",
           "solo", "sólo", "excepto", "salvo", "siempre"},
}

_STOP_HINT = {
    "pt": {"de", "que", "para", "com", "uma", "não", "os", "as", "é", "do", "da",
           "em", "por", "um", "mais", "como", "isso"},
    "en": {"the", "of", "and", "to", "in", "is", "that", "for", "with", "this",
           "are", "be", "it", "on", "as"},
    "es": {"de", "que", "el", "la", "en", "y", "los", "las", "una", "por", "con",
           "para", "es", "un", "se"},
}

ARTICLES = {
    "pt": {"o", "os", "as", "um", "uma", "uns", "umas"},   # "a" omitido: ambiguo (preposicao)
    "en": {"the", "a", "an"},
    "es": {"el", "la", "los", "las", "un", "una", "unos", "unas"},
}
STOP_EXTRA = {  # so no nivel 4 (com perda). Nenhuma palavra de NEGATIONS/MODALS/logica.
    "pt": {"é", "são", "está", "estão", "ser", "estar", "esse", "essa", "esses",
           "essas", "este", "esta", "estes", "estas", "isso", "isto", "muito", "também"},
    "en": {"is", "are", "was", "were", "be", "been", "being", "that", "which",
           "this", "these", "those", "its", "very", "really", "just", "also"},
    "es": {"es", "son", "está", "están", "ser", "estar", "ese", "esa", "esos",
           "esas", "este", "esta", "estos", "estas", "eso", "esto", "muy", "también"},
}

# (regex, substituicao) - conservadoras: so remove cortesia/enchimento.
FILLERS = {
    "en": [
        (r"\b(?:please|kindly)\b,?\s*", ""),
        (r"\bin order to\b", "to"),
        (r"\bdue to the fact that\b", "because"),
        (r"\bat this point in time\b", "now"),
        (r"\bin the event that\b", "if"),
        (r"\b(?:it is important to note that|it should be noted that|needless to say,?|as a matter of fact,?)\s*", ""),
        (r"\b(?:basically|essentially|actually),\s*", ""),
        (r"\bi (?:would like|want) you to\s+", ""),
        (r"\bwith (?:regard|respect) to\b", "regarding"),
    ],
    "pt": [
        (r"\bpor favor\b,?\s*", ""),
        (r"\b(?:a fim de|com o objetivo de|com a finalidade de)\b", "para"),
        (r"\bdevido ao fato de que\b", "porque"),
        (r"\btendo em vista que\b", "pois"),
        (r"\bno momento atual\b", "agora"),
        (r"\b[ée] importante (?:ressaltar|destacar|notar|observar|salientar) que\s*", ""),
        (r"\b(?:basicamente|essencialmente|na verdade|de fato),\s*", ""),
        (r"\bgostaria (?:de )?que voc[êe]\s+", ""),
        (r"\b(?:com rela[çc][ãa]o a|em rela[çc][ãa]o a|no que diz respeito a|no que se refere a)\b", "sobre"),
        (r"\bbem como\b", "e"),
    ],
    "es": [
        (r"\bpor favor\b,?\s*", ""),
        (r"\b(?:con el fin de|a fin de)\b", "para"),
        (r"\bdebido a que\b", "porque"),
        (r"\bes importante (?:se[ñn]alar|destacar|notar) que\s*", ""),
        (r"\b(?:b[aá]sicamente|esencialmente|en realidad),\s*", ""),
        (r"\b(?:con respecto a|en relaci[óo]n con|en lo que respecta a)\b", "sobre"),
    ],
}


def detect_lang(text: str) -> str:
    words = re.findall(r"[^\W\d_]+", text.lower())
    if not words:
        return "en"
    sample = Counter(words)
    scores = {lang: sum(sample[w] for w in hints) for lang, hints in _STOP_HINT.items()}
    return max(scores, key=scores.get)


# --------------------------------------------------------------------------
# Protecao de trechos criticos (placeholders em area de uso privado do Unicode)
# --------------------------------------------------------------------------

PH_L, PH_R = "\ue000", "\ue001"
_PH_RE = re.compile(PH_L + "([\ue100-\ue109]+)" + PH_R)


def _ph(i: int) -> str:
    return PH_L + "".join(chr(0xE100 + int(d)) for d in str(i)) + PH_R


def _unph(code: str) -> int:
    return int("".join(str(ord(c) - 0xE100) for c in code))


_TRAIL = ".,;:!?)]}\"'”’"
_LEAD = "([{\"'“‘"

_PROTECT = [
    ("frontmatter", re.compile(r"\A---\n.*?\n---[ \t]*(?:\n|\Z)", re.S)),
    ("fence", re.compile(r"(?:```|~~~).*?(?:```|~~~)", re.S)),
    ("icode", re.compile(r"`[^`\n]+`")),
    ("url", re.compile(r"https?://[^\s)>\]\"']+|www\.[^\s)>\]\"']+")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("path", re.compile(r"(?<![\w/])(?:[A-Za-z]:\\|~/|\./|\.\./|/)[\w./\\~-]{2,}")),
    ("quoted", re.compile(r"\"[^\"\n]{1,200}\"|“[^”\n]{1,200}”")),
    ("call", re.compile(r"\b[\w.]+\([^()\n]*\)")),
    ("ident", re.compile(
        r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b"            # camelCase
        r"|\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b"   # PascalCase
        r"|\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b"      # snake_case
        r"|\b[A-Z]{2,}[A-Z0-9_]*\b"                 # SIGLAS
    )),
]
_DIGIT_TOKEN = re.compile(r"\S*\d\S*")


def protect(text: str) -> tuple[str, list[str]]:
    store: list[str] = []
    index: dict[str, int] = {}  # mesmo valor -> mesmo marcador (permite achar duplicatas)

    def stash(val: str) -> str:
        if val not in index:
            store.append(val)
            index[val] = len(store) - 1
        return _ph(index[val])

    for _name, rx in _PROTECT:
        text = rx.sub(lambda m: stash(m.group(0)), text)

    def digit_cb(m: re.Match) -> str:
        tok = m.group(0)
        lead = ""
        while tok and tok[0] in _LEAD:
            lead, tok = lead + tok[0], tok[1:]
        trail = ""
        while tok and tok[-1] in _TRAIL:
            tok, trail = tok[:-1], tok[-1] + trail
        if not tok or not re.search(r"\d", tok):
            return m.group(0)
        return lead + stash(tok) + trail

    text = _DIGIT_TOKEN.sub(digit_cb, text)
    return text, store


def restore(text: str, store: list[str]) -> str:
    for _ in range(10):  # protecoes aninhadas
        new = _PH_RE.sub(lambda m: store[_unph(m.group(1))], text)
        if new == text:
            break
        text = new
    return text


# --------------------------------------------------------------------------
# Passos de compressao (operam sobre texto JA com placeholders)
# --------------------------------------------------------------------------

_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _compact_tables(text: str, notes: Counter) -> str:
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                if j != i + 1:
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    out.append("|".join(cells))
                j += 1
            notes["tabelas compactadas"] += 1
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def _level1(text: str, notes: Counter) -> str:
    n0 = len(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\u2060]", "", text)
    text = text.replace("\u00a0", " ").replace("\t", " ")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = _compact_tables(text, notes)
    text = re.sub(r"^\s*(?:[-*_=~#.]\s*){4,}$", "", text, flags=re.M)         # separadores
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"\1", text)                 # **negrito**
    text = re.sub(r"__(?=\S)(.+?)(?<=\S)__", r"\1", text)                     # __negrito__
    text = re.sub(r"(?<![\*\w])\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?![\*\w])", r"\1", text)  # *italico*
    text = re.sub(r"\.{4,}", "...", text)
    text = re.sub(r"([!?])\1+", r"\1", text)
    text = re.sub(r"(?<=\S)[ ]{2,}", " ", text)                               # preserva indentacao
    text = re.sub(r"[ ]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # duplicatas consecutivas
    lines, out = text.split("\n"), []
    for ln in lines:
        if out and ln.strip() and ln.strip() == out[-1].strip() and len(ln.strip()) >= 12:
            notes["linhas duplicadas"] += 1
            continue
        out.append(ln)
    text = "\n".join(out).strip()
    notes["chars removidos (n1)"] += n0 - len(text)
    return text


def _level2(text: str, lang: str, notes: Counter) -> str:
    # cabecalhos '## Titulo' -> 'Titulo:'
    def head(m: re.Match) -> str:
        t = m.group(1).strip()
        return t if t.endswith(":") else t + ":"
    text = re.sub(r"^#{1,6}[ ]+(.+?)[ ]*#*[ ]*$", head, text, flags=re.M)
    for rx, rep in FILLERS.get(lang, []):
        text, n = re.subn(rx, rep, text, flags=re.I)
        if n:
            notes["enchimento removido"] += n
    # duplicatas globais (linhas longas)
    seen, out = set(), []
    for ln in text.split("\n"):
        key = ln.strip().lower()
        if len(key) >= 30 and key in seen:
            notes["linhas duplicadas"] += 1
            continue
        seen.add(key)
        out.append(ln)
    text = "\n".join(out)
    text = re.sub(r"[ ]{2,}", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _drop_words(text: str, words: set[str], notes: Counter, label: str) -> str:
    if not words:
        return text
    rx = re.compile(r"(?<![\w])(?:" + "|".join(sorted(map(re.escape, words), key=len, reverse=True)) + r")(?![\w])[ ]?", re.I)
    text, n = rx.subn("", text)
    if n:
        notes[label] += n
    return text


_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")


def _level3(text: str, lang: str, notes: Counter) -> str:
    text = re.sub(r"\n{2,}", "\n", text)
    text = _drop_words(text, ARTICLES.get(lang, set()), notes, "artigos removidos")
    return re.sub(r"[ ]{2,}", " ", text).strip()


def _level4(text: str, lang: str, notes: Counter) -> str:
    text = _EMOJI.sub("", text)
    text = _drop_words(text, STOP_EXTRA.get(lang, set()), notes, "palavras de baixa informacao")
    return re.sub(r"[ ]{2,}", " ", text).strip()


LEVEL_DOC = {
    1: "seguro: espacos, markdown decorativo, tabelas compactas, duplicatas consecutivas",
    2: "+ enchimento/cortesia, cabecalhos 'Titulo:', duplicatas globais",
    3: "+ sem linhas em branco, artigos removidos (estilo telegrafico leve)",
    4: "+ emojis e palavras de baixa informacao (COM PERDA - revisar)",
}


def apply_level(text: str, level: int, lang: str) -> tuple[str, Counter]:
    """Aplica niveis 1..level sobre `text` (original, sem placeholders)."""
    notes: Counter = Counter()
    work, store = protect(text)
    work = _level1(work, notes)
    if level >= 2:
        work = _level2(work, lang, notes)
    if level >= 3:
        work = _level3(work, lang, notes)
    if level >= 4:
        work = _level4(work, lang, notes)
    return restore(work, store), notes


def compress_lite(text: str, rate: float | None = None, level: int | None = None,
                  lang: str = "auto") -> dict:
    lang = detect_lang(text) if lang == "auto" else lang
    before, method = count_tokens(text)
    chosen = level or 2
    result, notes = apply_level(text, chosen, lang)
    if rate is not None and level is None:
        for lv in (1, 2, 3, 4):
            result, notes = apply_level(text, lv, lang)
            chosen = lv
            if before and count_tokens(result)[0] / before <= rate:
                break
    after, _ = count_tokens(result)
    return {
        "engine": "lite", "text": result, "level": chosen, "lang": lang,
        "tokens_before": before, "tokens_after": after, "token_method": method,
        "kept_fraction": round(after / before, 3) if before else 1.0,
        "saved_tokens": before - after,
        "rate_requested": rate, "rate_reached": (rate is None) or (before == 0) or (after / before <= rate),
        "notes": dict(notes),
    }


# --------------------------------------------------------------------------
# Inventario e verificacao de fidelidade
# --------------------------------------------------------------------------

_WORDS_LOWER = re.compile(r"[\w'’]+", re.UNICODE)
CRITICAL = ("numbers", "urls", "emails", "paths", "code", "negations")
WARN = ("idents", "quoted", "modals")


def inventory(text: str) -> dict:
    inv: dict = {k: [] for k in ("numbers", "urls", "emails", "paths", "code", "idents", "quoted")}
    work = text
    # codigo primeiro (blocos e inline), removendo do texto para nao duplicar nas outras categorias
    for rx in (_PROTECT[0][1], _PROTECT[1][1], _PROTECT[2][1]):
        for m in rx.finditer(work):
            inv["code"].append(m.group(0))
        work = rx.sub(" ", work)
    for key, name in (("urls", "url"), ("emails", "email"), ("paths", "path"), ("quoted", "quoted")):
        rx = dict(_PROTECT)[name]
        inv[key] = [m.group(0) for m in rx.finditer(work)]
        work = rx.sub(" ", work)
    inv["idents"] = [m.group(0) for m in dict(_PROTECT)["ident"].finditer(work)]
    for m in _DIGIT_TOKEN.finditer(work):
        tok = m.group(0).strip(_TRAIL + _LEAD)
        if tok and re.search(r"\d", tok):
            inv["numbers"].append(tok)
    for k in inv:
        inv[k] = sorted(set(inv[k]))
    words = [w.lower() for w in _WORDS_LOWER.findall(text)]
    neg_all = set().union(*NEGATIONS.values())
    mod_all = set().union(*MODALS.values())
    inv["negations"] = dict(Counter(w for w in words if w in neg_all))
    inv["modals"] = dict(Counter(w for w in words if w in mod_all))
    return inv


def _present(item: str, ctext: str, cnorm: str) -> bool:
    return item in ctext or re.sub(r"\s+", "", item) in cnorm


def verify(original: str, compressed: str, ignore: set[str] | None = None) -> dict:
    ignore = ignore or set()
    inv, cinv = inventory(original), inventory(compressed)
    ctext = compressed
    cnorm = re.sub(r"\s+", "", compressed)
    issues: dict[str, object] = {}
    for key in ("numbers", "urls", "emails", "paths", "code", "idents", "quoted"):
        if key in ignore:
            continue
        missing = [x for x in inv[key] if not _present(x, ctext, cnorm)]
        if missing:
            issues[key] = missing
    for key in ("negations", "modals"):
        if key in ignore:
            continue
        a, b = sum(inv[key].values()), sum(cinv[key].values())
        if b < a:
            issues[key] = {"original": inv[key], "compressed": cinv[key]}
    critical = [k for k in issues if k in CRITICAL]
    status = "FAIL" if critical else ("WARN" if issues else "PASS")
    return {"status": status, "critical": critical, "issues": issues,
            "checked": {k: (len(v) if isinstance(v, list) else sum(v.values())) for k, v in inv.items()}}
