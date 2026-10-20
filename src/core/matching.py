"""Indices do GEDCOM e decisao de aceitacao de candidatos.

Extraido de `dna_analysis.py` pela OPP-20260929-ZV52. Responsabilidade unica:
construir os indices sobre a arvore carregada e decidir, para cada match do CSV,
quais pessoas do GEDCOM sao candidatas aceitas e por que.

Nao depende de pandas: quem le o CSV e `csv_ingest`.

## A arvore entra por parametro (feature 005, T013)

`build_ged_indexes` e `match_candidates` recebem `arvore` como primeiro
parametro. **Nenhum limiar, peso, ramo de aceitacao ou ordem de avaliacao mudou**
— a migracao toca a assinatura e a origem de `people`, e nada mais. As regras
A/B/C/D, o filtro anti-falso-positivo e o Jaccard adaptativo continuam com os
mesmos literais mapeados em `_reversa_sdd/code-analysis.md` secao 3.5.
"""
from __future__ import annotations

from thefuzz import fuzz

from .motivos_do_descarte import (
    NOME_UNICO,
    SEM_SOBRENOME_COMUM,
    SEM_SOBRENOME_NO_GEDCOM,
    SOBRENOME_CURTO,
    SOBRENOME_LIDO_COMO_PRENOME,
    diagnosticar,
    motivo,
)
from .name_normalization import (
    COMMON_SURNAMES,
    GENERIC_GIVENS,
    STOP_WORDS,
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surnames_set,
    token_prefixes,
)
from .registro import get_name

# Forma da arvore recebida por parametro (feature 005, `T013`). O parametro se
# chama `arvore` e vem primeiro, como em `family_navigation` e `path_finding`.
Arvore = tuple


def build_ged_indexes(arvore: Arvore):
    """Constroi os indices de busca e o cache de atributos normalizados.

    O cache existe porque ``norm_name`` custa cerca de 41 us e ``surnames_set``
    cerca de 72 us: o laco de candidatos de ``match_candidates`` renormalizava o
    mesmo nome aproximadamente 7 vezes por candidato, a cada match do CSV, para
    um valor que nao depende do CSV. Calcular aqui, uma vez por analise, nao
    altera nenhuma decisao: os valores sao os mesmos.
    """
    people = arvore[0]
    ged_index = {}
    surname_index = {}
    features = {}
    for pid, person in people.items():
        nm = get_name(person)
        key = norm_name(nm)
        key_tokens = key.split()
        ged_index.setdefault(key, []).append(pid)
        _given, surnames, _suffixes = split_name_pt(nm)
        for sn in surnames:
            if sn:
                surname_index.setdefault(sn, []).append(pid)
        # `key` ja e norm_name(nm), e norm_name e idempotente sobre os proprios
        # tokens, entao nao ha nada a renormalizar aqui. Reproduz o fallback de
        # top_given_tokens para o caso de todos os tokens serem stop words.
        non_stop = [t for t in key_tokens if t not in STOP_WORDS]
        features[pid] = {
            "norm": key,
            # O nome de exibicao viaja junto (feature 034): a lista dos descartados
            # mostra ao operador QUEM a arvore oferecia, e o id nao diz nada a ele.
            # Guardar aqui evita que o caminho de avaliacao precise da arvore — os
            # testes de aceitacao chamam a funcao com `arvore=None` de proposito.
            "nome": nm,
            "given_tokens": non_stop[:2] or key_tokens[:2],
            "surnames": set(surnames),
            "surnames_list": surnames,
            "tokens": set(key_tokens),
        }
    return ged_index, surname_index, features


def avaliar_candidatos(arvore: Arvore, match_name, cm_value, ged_index, surname_index,
                       features, limite=3):
    """Retorna `(candidate_pids, motivo, proximos)` — a avaliacao completa.

    Desde a feature 038, `motivo` e' um `Motivo` (codigo estavel, texto humano e detalhe
    tecnico) ou `None` quando o candidato foi aceito. Quem so' quer o texto usa
    `match_candidates`, que preserva o contrato antigo.

    `proximos` são os `limite` melhores candidatos **avaliados**, mesmo quando nenhum
    foi aceito. A ordem deles é a do **operador**, não a da decisão: compatível primeiro
    (prenome parecido e sobrenome em comum), depois prenome, nota e interseção.

    As duas ordens são diferentes de propósito. A decisão desempata por interseção de
    sobrenomes primeiro; para a tela, isso enterrava o candidato certo atrás de homônimos
    de sobrenome — medido no GEDCOM real em 2026-10-19: ordenando pela decisão, 50 dos
    366 descartes mostravam um compatível; ordenando pelo que o operador precisa ver, 76.

    Existe separada de `match_candidates` (feature 034) porque a lista dos descartados
    precisa mostrar quem a árvore oferecia — e o vencedor sozinho não basta: no caso
    real `*Maria de Fátima Oliveira de Jesus` o vencedor era outra pessoa, e a
    candidata compatível estava em segundo. `match_candidates` mantém o contrato de
    dois valores para não quebrar quem só quer a decisão.
    """
    key = norm_name(match_name)
    candidate_pids = ged_index.get(key, [])
    reason = None
    proximos = []

    if not candidate_pids:
        given_csv, surn_csv, csv_suffixes = split_name_pt(match_name)
        given_norm = norm_name(given_csv)
        csv_surn_all = drop_short_tokens(surnames_set(match_name))

        pool = set()
        for sn in surn_csv:
            pool.update(surname_index.get(sn, []))

        if not pool and surn_csv:
            pref = token_prefixes(surn_csv, min_len=3)
            for sn, pids in surname_index.items():
                if any(sn.startswith(p) for p in pref):
                    pool.update(pids)

        if not pool:
            # O motivo antigo era um so': "sem candidatos por sobrenome
            # (abreviação/corrupção?)", e ele acusava o ARQUIVO. Medido no arquivo real
            # do operador (13.716 pessoas, 454 nomes): dos 94 grupos com pool vazio, 86
            # nao tinham sobrenome NENHUM para procurar — e so' 2 eram mesmo abreviacao
            # (`*Roger S`, `A CF`). `Marcos Antonio de Melo` nao e' abreviacao nem
            # corrupcao: "marcos" e "antonio" sao os dois genericos, e "melo" virou o
            # prenome.
            #
            # A DECISAO nao muda: pool vazio descarta o nome nas quatro causas. Muda so'
            # o texto, que passa a dizer qual delas aconteceu. Ver o adendo 024.
            primeiros = [t for t in norm_name(match_name).split() if t not in STOP_WORDS]
            if not surn_csv:
                # Sobrou mais de um token: HAVIA um sobrenome para achar, e ele foi
                # empurrado para a casa do prenome. Acontece por dois caminhos, e o
                # criterio e' o mesmo nos dois:
                #   - o primeiro token esta' em GENERIC_GIVENS e foi pulado
                #     ("Maria Pacheco" -> prenome "pacheco");
                #   - o ultimo token e' sufixo de sobrenome e foi consumido por
                #     `surname_core_tokens` ("*Coutinho Neto" -> "neto" sai como sufixo,
                #     e "coutinho" sobra como prenome).
                # E' limitacao da decomposicao, nao defeito do arquivo enviado.
                if len(primeiros) > 1:
                    reason = motivo(SOBRENOME_LIDO_COMO_PRENOME)
                # Um token so': nao havia sobrenome nenhum para perder.
                else:
                    reason = motivo(NOME_UNICO)
            elif not csv_surn_all:
                # O nome TEM sobrenome, mas nenhum token chega a 3 letras: virou inicial,
                # e inicial nao e' chave de busca (o fallback por prefixo tambem exige 3).
                # Aqui — e so' aqui — o motivo antigo ("abreviação") estava certo.
                reason = motivo(SOBRENOME_CURTO)
            else:
                # O nome tem sobrenome utilizavel, e ele nao esta' na arvore — nem por
                # prefixo de 3 caracteres. Aqui sim cabe conferir grafia e o GEDCOM.
                reason = motivo(SEM_SOBRENOME_NO_GEDCOM)
        else:
            best_pid = None
            best_score = best_g = -1
            best_inter = -1
            avaliados = []
            key_norm = norm_name(match_name)

            for pid in pool:
                feat = features[pid]
                s_given = max((fuzz.ratio(given_norm, gg) for gg in feat["given_tokens"]), default=0)
                s_token = fuzz.token_sort_ratio(key_norm, feat["norm"])
                s_part = fuzz.partial_ratio(key_norm, feat["norm"])
                ged_surn_set = feat["surnames"]
                inter_set = csv_surn_all & ged_surn_set
                inter_cnt_local = len(inter_set)
                common_penalty = sum(1 for s in inter_set if s in COMMON_SURNAMES)
                inter_bonus = 8.0 * inter_cnt_local - 4.0 * common_penalty
                score = round(0.55 * s_token + 0.25 * s_part + 0.20 * s_given + inter_bonus, 2)
                avaliados.append((pid, score, s_given, inter_cnt_local))

                # 4o criterio de desempate: menor `xref_id` no empate triplo.
                # Decisao de 2026-10-05 (_reversa_sdd/questions.md#pergunta-1 e
                # adrs/23): sem ele, empate exato nos tres criterios caia na
                # ordem de iteracao de `pool`, que e um `set`.
                if (inter_cnt_local > best_inter or
                        (inter_cnt_local == best_inter and s_given > best_g) or
                        (inter_cnt_local == best_inter and s_given == best_g and score > best_score) or
                        (inter_cnt_local == best_inter and s_given == best_g and score == best_score
                         and best_pid is not None and pid < best_pid)):
                    best_pid, best_score, best_g, best_inter = pid, score, s_given, inter_cnt_local

            if best_pid is not None:
                # Os melhores para o OPERADOR: compatível primeiro, depois prenome, nota
                # e interseção. Não é a ordem da decisão (que desempata por interseção
                # antes de tudo) — ver a docstring de `avaliar_candidatos`.
                proximos = [
                    {"id": pid_, "nome": features[pid_].get("nome") or pid_,
                     "nota": nota, "prenome": given, "intersecao": inter,
                     "compativel": given >= 85 and inter >= 1}
                    for pid_, nota, given, inter
                    in sorted(avaliados,
                              key=lambda t: (0 if (t[2] >= 85 and t[3] >= 1) else 1,
                                             -t[2], -t[1], -t[3], t[0]))[:limite]
                ]
                feat_best = features[best_pid]
                ged_surn_best = feat_best["surnames"]
                inter_best = csv_surn_all & ged_surn_best
                inter_cnt = len(inter_best)

                ged_tokens = feat_best["tokens"]
                suffix_hit = bool(csv_suffixes & ged_tokens)
                if csv_surn_all and ged_surn_best and inter_cnt == 0 and not suffix_hit:
                    candidate_pids = []
                    reason = motivo(SEM_SOBRENOME_COMUM)
                else:
                    required_intersection = 1
                    if given_norm in GENERIC_GIVENS and len(csv_surn_all) >= 2:
                        required_intersection = 2

                    jacc = soft_prefix_jaccard(csv_surn_all, ged_surn_best, min_pref=4)
                    jacc_ok = True
                    if len(csv_surn_all) >= 2:
                        threshold = 0.5
                        if float(cm_value or 0) >= 150 and given_norm not in GENERIC_GIVENS:
                            threshold = 0.33
                        jacc_ok = jacc >= threshold

                    ACCEPT = False

                    if (given_norm in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.67 and best_score >= 100):
                        ACCEPT = True
                    elif (given_norm not in GENERIC_GIVENS and inter_cnt >= 2 and jacc >= 0.50 and best_g >= 85 and best_score >= 80):
                        ACCEPT = True
                    elif (given_norm not in GENERIC_GIVENS and inter_cnt >= 1 and jacc >= 0.80 and best_score >= 86):
                        ACCEPT = True
                    elif (best_g >= 90 and best_score >= 92 and inter_cnt >= required_intersection and jacc_ok):
                        ACCEPT = True
                    elif (best_g >= 95 and best_score >= 88 and inter_cnt >= required_intersection and jacc_ok):
                        ACCEPT = True
                    else:
                        pref_csv = token_prefixes(surn_csv, min_len=3)
                        if pref_csv:
                            cand_surns = feat_best["surnames_list"]
                            if any(sn.startswith(tuple(pref_csv)) for sn in cand_surns) and best_g >= 90 and best_score >= 86 and inter_cnt >= 1 and jacc_ok:
                                ACCEPT = True

                    # O SETIMO PORTAO (feature 038). Quando o nome do CSV tem uma parte que
                    # nao existe na arvore, o aceite ja' obtido e' DESFEITO, a menos que a nota
                    # seja altissima. Ele so' age depois de todos os outros passarem — e e' por
                    # isso que ele vem primeiro no diagnostico, e por isso o caso do operador
                    # (`given=100, final=88.25, inter=1/1, jacc=0.50`) era recusado por ele
                    # sem que a mensagem antiga dissesse isso.
                    csv_tokens = drop_short_tokens({t for t in norm_name(match_name).split() if t not in STOP_WORDS})
                    csv_middle = csv_tokens - {given_norm} - csv_surn_all
                    meio_ausente = bool(csv_middle and csv_middle.isdisjoint(ged_tokens))
                    aceito_antes_do_veto = ACCEPT
                    if ACCEPT and meio_ausente:
                        ACCEPT = (best_score >= 96 and best_g >= 92 and inter_cnt >= required_intersection and jacc_ok)

                    candidate_pids = [best_pid] if ACCEPT else []
                    if not candidate_pids:
                        # O TEXTO NAO E' MAIS MONTADO AQUI (feature 038): quem escolhe a causa
                        # e' `motivos_do_descarte.diagnosticar`, sobre os mesmos valores que a
                        # decisao acabou de usar. Nenhum limiar foi tocado.
                        reason = diagnosticar(
                            prenome=best_g, nota=best_score,
                            intersecao=inter_cnt, exigidas=required_intersection,
                            grafia=jacc, grafia_ok=jacc_ok,
                            meio_vetado=bool(aceito_antes_do_veto and meio_ausente))

    return candidate_pids, reason, proximos


def match_candidates(arvore: Arvore, match_name, cm_value, ged_index, surname_index, features):
    """Retorna `(candidate_pids, reason)` seguindo o bloco de scoring do legado.

    Assinatura historica, mantida de proposito: quem so quer a decisao nao precisa
    saber que a avaliacao tambem produz os melhores candidatos. Ver
    `avaliar_candidatos`.

    Desde a feature 038 o motivo viaja como `Motivo` (codigo + texto + detalhe) em
    `avaliar_candidatos`, mas **aqui ele continua saindo como texto**: este e' o contrato de
    dois valores que `application/validacao.py` e a caracterizacao de 2026-09-29 consomem.
    """
    pids, motivo_do_descarte, _ = avaliar_candidatos(arvore, match_name, cm_value, ged_index,
                                                     surname_index, features)
    return pids, (motivo_do_descarte.texto if motivo_do_descarte is not None else None)
