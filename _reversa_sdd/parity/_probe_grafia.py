"""Sonda descartavel: quantos descartes acham o parente com o sobrenome escrito diferente?

Os 288 descartes sem candidato compativel sao os que o indice de sobrenomes nao alcanca:
nenhum token do nome do CSV existe na arvore, nem por prefixo de 3 letras. A pergunta e'
se existe um sobrenome PARECIDO (ratio >= 85) — e, se existir, se o prenome tambem casa.

Grafia parecida NAO e' prova de mesma familia: sobrenomes proximos podem ser familias
distintas. Por isso a sonda mede tamanho de oportunidade, nao verdade.

Imprime agregados e alguns pares (nome do CSV -> nome na arvore), que e' o que o operador
precisaria julgar.
"""
import sys

sys.path.insert(0, "src")

from rapidfuzz import fuzz, process

from core.documentary_relationship import documentary_relationship
from core.matching import (build_ged_indexes, drop_short_tokens, match_candidates,
                           norm_name, split_name_pt, surnames_set)
from core.registro import get_name
from parsers.csv_ingest import read_csv_with_fallback
from parsers.gedcom_parser import carregar_arvore

CSV = "src/uploads/54f4887e89705735__Famílias_Sergipanas.csv"
GED = "src/uploads/34735d8ec19c23d5__Arvore_Unificada_Oficial_V1_2_Tratado.ged"

csv = read_csv_with_fallback(CSV)
nome_col = next(c for c in csv.columns if str(c).lower() == "name")
cm_col = next(c for c in csv.columns if str(c).lower() == "cm")
kits = list(csv.assign(**{nome_col: csv[nome_col].astype(str)})
            .groupby(nome_col)[cm_col].sum().items())

arvore = carregar_arvore(GED)
pessoas = arvore[0]
raiz = next(pid for pid, p in pessoas.items() if "adriano" in get_name(p).lower())
ged_index, surname_index, features = build_ged_indexes(arvore)
todos_sobrenomes = list(surname_index.keys())

sem_candidato = 0
com_grafia = 0
com_sobrenome_parecido = 0
com_grafia_e_prenome = 0
com_grafia_prenome_e_caminho = 0
exemplos = []
pares_fracos = []

for nome, cm in kits:
    pids, _ = match_candidates(arvore, nome, float(cm), ged_index, surname_index, features)
    if pids:
        continue
    given_csv, surn_csv, _ = split_name_pt(nome)
    given_norm = norm_name(given_csv)
    sobrenomes_csv = drop_short_tokens(surnames_set(nome))

    # So' interessa quem o indice NAO alcanca: nome cujo sobrenome existe na arvore ja
    # passou pela avaliacao normal e foi recusado por outro motivo.
    if any(sn in surname_index for sn in sobrenomes_csv):
        continue
    sem_candidato += 1

    achado = None
    melhor_prenome = 0
    for sn in sobrenomes_csv:
        par = process.extractOne(sn, todos_sobrenomes, scorer=fuzz.ratio, score_cutoff=85)
        if not par:
            continue
        parecido, nota, _ = par
        for pid in surname_index[parecido]:
            feat = features[pid]
            s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
            melhor_prenome = max(melhor_prenome, s_given)
            if s_given >= 85 and achado is None:
                achado = (sn, parecido, nota, pid, s_given)
        if achado:
            break
    if melhor_prenome:
        com_sobrenome_parecido += 1
        if melhor_prenome < 85 and len(pares_fracos) < 8:
            pares_fracos.append((nome, sn, parecido, int(melhor_prenome)))

    if achado:
        com_grafia += 1
        sn, parecido, nota, pid, s_given = achado
        doc = documentary_relationship(arvore, raiz, pid)
        tem_caminho = bool((doc.get("path") or {}).get("ids"))
        if s_given >= 85:
            com_grafia_e_prenome += 1
        if tem_caminho:
            com_grafia_prenome_e_caminho += 1
        if len(exemplos) < 8:
            exemplos.append((nome, get_name(pessoas[pid]), f"{sn}~{parecido}", round(nota, 1),
                             int(s_given), tem_caminho))

print(f"descartes_sem_sobrenome_na_arvore={sem_candidato}")
print(f"com_sobrenome_parecido={com_sobrenome_parecido} "
      f"| com sobrenome parecido E prenome>=85={com_grafia_e_prenome} "
      f"(desses, com caminho={com_grafia_prenome_e_caminho})")
for nome, cand, par, nota, given, caminho in exemplos:
    print(f'  "{nome}" -> "{cand}" | {par} ({nota}) | prenome {given} | caminho={caminho}')
print("--- parecidos, mas prenome nao casa ---")
for nome, sn, parecido, given in pares_fracos:
    print(f'  "{nome}" | sobrenome {sn}~{parecido} | melhor prenome {given}')
