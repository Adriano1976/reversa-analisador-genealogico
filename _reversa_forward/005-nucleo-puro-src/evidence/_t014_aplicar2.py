"""Segunda parte do T014: corpos que ainda leem as globais."""
import io

ALVO = r"src/core/documentary_relationship.py"

SUBS = [
    # `_indice_por_nome`: chave de invalidacao derivada do VALOR recebido
    ('    if _INDICE_DE_NOMES["versao"] != gedcom_state.versao:\n'
     '        mapa: dict = {}\n'
     '        for pid, pessoa in people.items():\n'
     '            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)\n'
     '        _INDICE_DE_NOMES["mapa"] = mapa\n'
     '        _INDICE_DE_NOMES["versao"] = gedcom_state.versao\n'
     '    return _INDICE_DE_NOMES["mapa"]',
     '    people = arvore[0]\n'
     '    if _INDICE_DE_NOMES["chave"] != id(people):\n'
     '        mapa: dict = {}\n'
     '        for pid, pessoa in people.items():\n'
     '            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)\n'
     '        _INDICE_DE_NOMES["mapa"] = mapa\n'
     '        _INDICE_DE_NOMES["chave"] = id(people)\n'
     '    return _INDICE_DE_NOMES["mapa"]'),

    ('_INDICE_DE_NOMES = {"versao": None, "mapa": None}',
     '_INDICE_DE_NOMES = {"chave": None, "mapa": None}'),

    ('    exatos = list(_indice_por_nome().get(alvo, []))',
     '    exatos = list(_indice_por_nome(arvore).get(alvo, []))'),

    # `hop_evidence`: passa a arvore ao dossie de nomes
    ("def hop_evidence(arvore, child_id, parent_id) -> dict:",
     "def hop_evidence(arvore, child_id, parent_id) -> dict:"),

    # `documentary_relationship` e os auxiliares de caminho
    ("def _ancestor_depths(start_id, max_depth: int) -> dict:",
     "def _ancestor_depths(arvore, start_id, max_depth: int) -> dict:"),
    ("def _cadeias_ate(start_id, alvo, max_depth: int, limite=LIMITE_DE_CADEIAS) -> int:",
     "def _cadeias_ate(arvore, start_id, alvo, max_depth: int, limite=LIMITE_DE_CADEIAS) -> int:"),
    ("def _cadeia_curta(start_id, alvo, max_depth):",
     "def _cadeia_curta(arvore, start_id, alvo, max_depth):"),
    ("def find_all_common_ancestors(a_id, b_id, max_depth=MAX_DEPTH_ALTERNATIVOS, limit=12) -> list:",
     "def find_all_common_ancestors(arvore, a_id, b_id, max_depth=MAX_DEPTH_ALTERNATIVOS, limit=12) -> list:"),
    ("def _caminho_alternativo(a_id, b_id, ancestral_id):",
     "def _caminho_alternativo(arvore, a_id, b_id, ancestral_id):"),
    ("def documentary_relationship(a_id, b_id, homonyms=None) -> dict:",
     "def documentary_relationship(arvore, a_id, b_id, homonyms=None) -> dict:"),

    # chamadas internas de get_parents
    ("get_parents(_arvore_global(), pid)", "get_parents(arvore, pid)"),

    # chamadas internas dentro de documentary_relationship / auxiliares
    ("path, comum = find_ancestral_path(_arvore_global(), a_id, b_id, max_depth=MAX_DEPTH)",
     "path, comum = find_ancestral_path(arvore, a_id, b_id, max_depth=MAX_DEPTH)"),
    ('"name": get_name(people.get(pid)),', '"name": get_name(arvore[0].get(pid)),'),
    ('"birth": birth_date(pid),', '"birth": birth_date(arvore[0], pid),'),
    ('return {"ids": ids, "names": [get_name(people.get(i)) for i in ids], "via": ancestral_id}',
     'return {"ids": ids, "names": [get_name(arvore[0].get(i)) for i in ids], "via": ancestral_id}'),
    ('"person_a": person_summary(a_id),', '"person_a": person_summary(arvore, a_id),'),
    ('"person_b": person_summary(b_id),', '"person_b": person_summary(arvore, b_id),'),
    ('evidencia.append(hop_evidence(path[i], path[i + 1]))',
     'evidencia.append(hop_evidence(arvore, path[i], path[i + 1]))'),
    ('evidencia.append(hop_evidence(path[i + 1], path[i]))',
     'evidencia.append(hop_evidence(arvore, path[i + 1], path[i]))'),
    ("comuns = find_all_common_ancestors(a_id, b_id)",
     "comuns = find_all_common_ancestors(arvore, a_id, b_id)"),
    ('"common_ancestor": {"id": comum, "name": get_name(people.get(comum)), "birth": birth_date(comum)},',
     '"common_ancestor": {"id": comum, "name": get_name(arvore[0].get(comum)), "birth": birth_date(arvore[0], comum)},'),
    ('"path": {"ids": path, "names": [get_name(people.get(p)) for p in path]},',
     '"path": {"ids": path, "names": [get_name(arvore[0].get(p)) for p in path]},'),
]


def main() -> int:
    texto = io.open(ALVO, encoding="utf-8").read()
    for antigo, novo in SUBS:
        if antigo == novo:
            continue
        n = texto.count(antigo)
        if n == 0:
            print("AVISO (0 ocorrencias, ja aplicado?): %r" % antigo[:70])
            continue
        texto = texto.replace(antigo, novo)
        print("  ok (%d)  %s" % (n, antigo[:70].replace("\n", "\\n")))
    io.open(ALVO, "w", encoding="utf-8", newline="").write(texto)
    # relatorio do que sobrou
    restos = [l for l in texto.splitlines() if "_arvore_global()" in l or "gedcom_state." in l]
    print("--- linhas que ainda referenciam estado ---")
    print("\n".join(restos) or "(nenhuma)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
