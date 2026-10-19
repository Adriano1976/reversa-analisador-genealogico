"""Sonda descartavel: quantos descartes tem candidato plausivel COM caminho e COM idade viavel?

Corrige o vies da versao anterior, que truncava o conjunto de candidatos e parava no
primeiro caminho encontrado: aqui todos os candidatos plausiveis sao avaliados, e o nome
so' conta se ALGUM deles tiver caminho documental ate o doador E janela de vida viavel.

"Plausivel" e' condicao necessaria (prenome >= 85 e sobrenome em comum), nao prova de que
seja a mesma pessoa. Imprime agregados e anos de nascimento; nomes nao vao para a saida.
"""
import sys

sys.path.insert(0, "src")

from core.documentary_relationship import birth_date, documentary_relationship
from core.janela_de_vida import conferir_janela_de_vida
from core.matching import (build_ged_indexes, drop_short_tokens, fuzz, match_candidates,
                           norm_name, split_name_pt, surnames_set, token_prefixes)
from core.registro import get_name
from parsers.csv_ingest import read_csv_with_fallback
from parsers.gedcom_parser import carregar_arvore

CSV = "src/uploads/54f4887e89705735__Famílias_Sergipanas.csv"
ARVORES = [
    ("src/uploads/34735d8ec19c23d5__Arvore_Unificada_Oficial_V1_2_Tratado.ged", "TRATADO"),
    ("src/uploads/21439b0645133804__Adriano_Santos_V2_tratado.ged", "ADRIANO_V2"),
]

csv = read_csv_with_fallback(CSV)
nome_col = next(c for c in csv.columns if str(c).lower() == "name")
cm_col = next(c for c in csv.columns if str(c).lower() == "cm")
kits = list(csv.assign(**{nome_col: csv[nome_col].astype(str)})
            .groupby(nome_col)[cm_col].sum().items())

for ged, rotulo in ARVORES:
    arvore = carregar_arvore(ged)
    pessoas = arvore[0]
    raiz = next(pid for pid, p in pessoas.items() if "adriano" in get_name(p).lower())
    ged_index, surname_index, features = build_ged_indexes(arvore)

    com_plausivel = com_caminho = viaveis = 0
    anos = []
    for nome, cm in kits:
        pids, _ = match_candidates(arvore, nome, float(cm), ged_index, surname_index, features)
        if pids:
            continue
        given_csv, surn_csv, _ = split_name_pt(nome)
        given_norm = norm_name(given_csv)
        csv_surn = drop_short_tokens(surnames_set(nome))
        pool = set()
        for sn in surn_csv:
            pool.update(surname_index.get(sn, []))
        if not pool and surn_csv:
            pref = token_prefixes(surn_csv, min_len=3)
            for sn, ids in surname_index.items():
                if any(sn.startswith(p) for p in pref):
                    pool.update(ids)

        plausiveis = []
        for pid in pool:
            feat = features[pid]
            s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
            if s_given >= 85 and (csv_surn & feat["surnames"]):
                plausiveis.append(pid)
        if not plausiveis:
            continue
        com_plausivel += 1

        achou_caminho = achou_viavel = False
        for pid in plausiveis:
            doc = documentary_relationship(arvore, raiz, pid)
            if not (doc.get("path") or {}).get("ids"):
                continue
            achou_caminho = True
            janela, _, _ = conferir_janela_de_vida(birth_date(pessoas, pid), 2026)
            if janela != "impossivel":
                achou_viavel = True
                anos.append((birth_date(pessoas, pid) or "?"))
                break
        if achou_caminho:
            com_caminho += 1
        if achou_viavel:
            viaveis += 1

    print(f"{rotulo}: descartados_com_plausivel={com_plausivel} "
          f"com_caminho={com_caminho} com_caminho_e_idade_viavel={viaveis}")
    print("   nascimentos dos viaveis:", sorted(anos))
