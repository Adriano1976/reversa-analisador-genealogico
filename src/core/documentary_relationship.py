"""Parentesco DOCUMENTAL: o que o GEDCOM afirma, sem nenhum DNA.

Responsabilidade unica: dado duas pessoas da arvore carregada, responder o que o
**documento** diz sobre elas — caminho, ancestrais comuns, distancia geracional,
parentesco, homonimos, caminhos multiplos, colapso de pedigree e as evidencias
(registro de familia, datas, idade dos genitores) usadas em cada salto.

## Regra do projeto

O GEDCOM determina o parentesco documental. O DNA **nao** altera nada do que este
modulo devolve: nenhuma funcao daqui aceita cM nem le o CSV. Quem confronta as
duas evidencias e `core.evidence_comparison`, depois e separadamente.

## Por que datas entram aqui

`_reversa_sdd/busca-caminho` documenta que o legado nunca olhou data: o BFS sobe
por pais e aceita qualquer salto. Medido em 2026-10 no GEDCOM real
`Arvore_Unificada_Oficial_V1_2.ged`, isso produz caminho com mae nascida 11 anos
DEPOIS do filho (`@F6@`: Celso Gomes Gama, n. 1961, filho de Maria Auxiliadora,
n. 1972) apresentado como "conexao direta por ancestral comum".

Uma data impossivel **nao** invalida o vinculo nem muda o parentesco: o dado e do
documento, e cabe ao operador julgar. O que este modulo faz e **registrar a
evidencia** (`evidence[].age_at_birth`, `plausible`) e **avisar**
(`warnings[].code == "data_impossivel"`). Corrigir o GEDCOM nao e papel de agente.
"""
from __future__ import annotations

import re
import unicodedata
from collections import deque

from .family_navigation import get_parents
from .registro import get_name, ref_id
from .path_finding import MAX_DEPTH, find_ancestral_path
from utils.text_cleaning import demojibake

# Idade minima/maxima de um genitor no nascimento do filho. Fora disso o salto e
# registrado como suspeito. Nao e regra biologica: e filtro de evidencia.
IDADE_MINIMA_GENITOR = 12
IDADE_MAXIMA_GENITOR = 70

# Teto de expansao da busca por TODOS os ancestrais comuns. O caminho principal
# continua vindo de `find_ancestral_path` (contrato congelado); a enumeracao
# completa existe para contar caminhos alternativos e detectar colapso.
MAX_DEPTH_ALTERNATIVOS = 12
LIMITE_DE_CADEIAS = 8


# ---------------------------------------------------------------------------
# Por que a chave do indice e derivada do CONTEUDO, e nao da identidade
# ---------------------------------------------------------------------------
# Medido em 2026-10-06, enquanto o estado global existia:
# `load_gedcom_and_build_graph` MUTAVA `gedcom_state.people` in place
# (`clear()` + `update()`), entao o `id()` do dicionario era o MESMO em todo o
# processo. Um cache chaveado por identidade nunca invalidaria — e a invalidacao
# e justamente o que `test_6d` cobra.
#
# A tentacao, agora que `T023` removeu o estado e `carregar_arvore` devolve
# dicionarios NOVOS a cada parse, e voltar a usar `id()`. NAO volte: `id()` e
# reciclado. O dicionario da arvore anterior deixa de ser referenciado assim que
# o parse seguinte devolve o novo, o CPython pode reusar o mesmo endereco, e a
# chave coincidiria com a de um GEDCOM DIFERENTE — o cache devolveria o mapa do
# anterior. O defeito apareceria so sob carga, e nao em teste isolado.
#
# A chave e o tamanho mais a primeira e a ultima chave de `people`: barato,
# derivado do valor, e muda quando a arvore muda. A explicacao completa esta em
# `_chave_de`.
# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------

_ANO = re.compile(r"(\d{3,4})")


def parse_year(date_value) -> int | None:
    """Primeiro ano de 4 (ou 3) digitos de uma data GEDCOM, ou None.

    Tolera `12 OCT 1976`, `ABOUT 1920`, `BEFORE 1812`, `1815` e `DateValueSimple`
    do ged4py (convertido com `str`). Nao normaliza `BEFORE/AFTER` para aproximar
    o ano: quem le decide, e a evidencia mostra o texto original.
    """
    if date_value is None:
        return None
    texto = str(date_value)
    achado = _ANO.search(texto)
    return int(achado.group(1)) if achado else None


def _data_de(people, pid, tag):
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == "DATE":
                    return str(sub.value)
    return None


def birth_date(people, pid):
    return _data_de(people, pid, "BIRT")


def death_date(people, pid):
    return _data_de(people, pid, "DEAT")


def _local_de(people, pid, tag):
    pessoa = people.get(pid)
    if not pessoa:
        return None
    for rec in pessoa.sub_records:
        if rec.tag == tag:
            for sub in rec.sub_records:
                if sub.tag == "PLAC":
                    return str(sub.value)
    return None


# ---------------------------------------------------------------------------
# Fichas de pessoa
# ---------------------------------------------------------------------------

def _ids(people, sub_tag, pid):
    return [ref_id(r.value) for r in people[pid].sub_records if r.tag == sub_tag] if pid in people else []


def get_children(arvore, person_id):
    """Filhos declarados em qualquer familia em que a pessoa seja HUSB ou WIFE."""
    filhos = []
    people, families = arvore[0], arvore[1]
    for fam in families.values():
        husb = next((ref_id(r.value) for r in fam.sub_records if r.tag == "HUSB"), None)
        wife = next((ref_id(r.value) for r in fam.sub_records if r.tag == "WIFE"), None)
        if person_id in (husb, wife):
            for rec in fam.sub_records:
                if rec.tag == "CHIL":
                    cid = ref_id(rec.value)
                    if cid not in filhos:
                        filhos.append(cid)
    return filhos


def person_summary(arvore, person_id) -> dict:
    """Ficha comparavel de uma pessoa, para desambiguar homonimos."""
    return {
        "id": person_id,
        "name": get_name(arvore[0].get(person_id)),
        "sex": next((r.value for r in arvore[0][person_id].sub_records if r.tag == "SEX"), None) if person_id in arvore[0] else None,
        "birth": birth_date(arvore[0], person_id),
        "birth_year": parse_year(birth_date(arvore[0], person_id)),
        "birth_place": _local_de(arvore[0], person_id, "BIRT"),
        "death": death_date(arvore[0], person_id),
        "death_year": parse_year(death_date(arvore[0], person_id)),
        "parents": get_parents(arvore, person_id),
        "parent_names": [get_name(arvore[0].get(p)) for p in get_parents(arvore, person_id)],
        "spouses": _ids(arvore[0], "FAMS", person_id),
        "children": get_children(arvore, person_id),
        "family_as_child": arvore[3].get(person_id, []),
    }


# ---------------------------------------------------------------------------
# Homonimos
# ---------------------------------------------------------------------------

def normalizar(nome: str) -> str:
    """Minusculas sem acento, para comparar nomes do GEDCOM e do CSV.

    Aplica antes a correcao de mojibake do projeto (`utils.text_cleaning`), a
    autoridade unica dessa limpeza. Sem isso, um GEDCOM sem `1 CHAR UTF-8` — que
    o ged4py le como latin-1 — faz "José" chegar como "JosÃ©" e o mesmo nome
    deixar de ser reconhecido como o mesmo: era o caso de um arquivo real
    (`Arvore_Unificada_Oficial_V1_2.ged`), onde a regra de homonimos ficaria cega.
    """
    sem_acento = unicodedata.normalize("NFKD", demojibake(str(nome or "")))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def _diferencas(arvore, ids) -> list:
    """Campos em que as fichas divergem — o que o operador precisa olhar."""
    campos = [
        ("birth", "data de nascimento"),
        ("birth_place", "local de nascimento"),
        ("death", "data de falecimento"),
        ("parents", "pais"),
        ("children", "filhos"),
        ("sex", "sexo"),
    ]
    # As fichas sao montadas UMA vez: `person_summary` varre as familias do
    # arquivo, e refazer isso por campo custava 6x por homonimo.
    fichas = [person_summary(arvore, i) for i in ids]
    divergencias = []
    for campo, rotulo in campos:
        valores = {str(ficha.get(campo)) for ficha in fichas}
        if len(valores) > 1:
            divergencias.append({"campo": campo, "rotulo": rotulo})
    return divergencias


_INDICE_DE_NOMES = {"chave": None, "mapa": None}


def _chave_de(people) -> tuple:
    """Chave de invalidacao do indice, derivada do CONTEUDO recebido.

    O indice e um cache de modulo: a chave tem de mudar quando outro GEDCOM chega,
    senao o fluxo seguinte leria os ids do anterior. A IDENTIDADE do dicionario nao
    serve: o parse mutava `people` in place e o `id()` era o mesmo durante todo o
    processo, entao o cache nunca invalidaria — foi o defeito medido em 2026-10-06
    e cobrado por `test_6d`.

    A chave usa contagem, primeira e ultima chave — barato e suficiente para
    distinguir dois GEDCOMs carregados. Ela continua necessaria depois do `T023`,
    que removeu o estado global e a mutacao in place: o parse agora devolve
    dicionarios NOVOS, mas este cache e de modulo, e a chave continua sendo o que
    garante que ele fale do GEDCOM da vez.
    """
    if not people:
        return (0, None, None)
    chaves = sorted(people)
    return (len(people), chaves[0], chaves[-1])


def _indice_por_nome(arvore) -> dict:
    """nome normalizado -> lista de ids, reconstruido a cada GEDCOM carregado.

    A varredura de 35 mil pessoas custa ~0,9 s. Sem este indice, o fluxo de DNA
    (71 nomes distintos no arquivo real) pagava isso 71 vezes. A invalidacao usa o
    CONTEUDO do dicionario de pessoas recebido, e nao um contador
    (`gedcom_state.versao`, removido pela feature 005): dois GEDCOMs diferentes
    podem ter a mesma contagem, e um contador exigiria estado. O detalhe da chave
    esta em `_chave_de`.
    """
    people = arvore[0]
    chave = _chave_de(people)
    if _INDICE_DE_NOMES["chave"] != chave:
        mapa: dict = {}
        for pid, pessoa in people.items():
            mapa.setdefault(normalizar(get_name(pessoa)), []).append(pid)
        _INDICE_DE_NOMES["mapa"] = mapa
        _INDICE_DE_NOMES["chave"] = chave
    return _INDICE_DE_NOMES["mapa"]


def homonym_dossier(arvore, name_query: str, similar_ids=None) -> dict:
    """Todos os registros que podem ser a pessoa consultada, com ficha e ID.

    Nao escolhe: devolve o conjunto. `ambiguous` e True quando existe mais de um
    registro com o MESMO nome normalizado (homonimo direto) ou quando o chamador
    informa candidatos semelhantes (`similar_ids`). A comparacao ignora acento,
    entao "Jose Vicente de Souza" e "José Vicente de Souza" sao o mesmo nome.
    """
    alvo = normalizar(name_query)
    exatos = list(_indice_por_nome(arvore).get(alvo, []))
    parecidos = [pid for pid in (similar_ids or []) if pid not in exatos]
    fichas = [person_summary(arvore, pid) for pid in exatos]
    return {
        "query": name_query,
        "exact_count": len(exatos),
        "exact_matches": fichas,
        "similar_count": len(parecidos),
        "similar_matches": [person_summary(arvore, pid) for pid in parecidos[:5]],
        "ambiguous": len(exatos) > 1,
        "differences": _diferencas(arvore, exatos) if len(exatos) > 1 else [],
        "identical_data": bool(len(exatos) > 1 and not _diferencas(arvore, exatos)),
    }


# ---------------------------------------------------------------------------
# Evidencia de cada salto
# ---------------------------------------------------------------------------

def hop_evidence(arvore, child_id, parent_id) -> dict:
    """O registro cru que liga `child_id` a `parent_id`, com a idade implicada.

    Devolve a familia (FAM), o casal declarado nela e as datas, para que a tela
    possa mostrar POR QUE o sistema afirmou aquele salto. `plausible` e False
    quando a idade do genitor no nascimento do filho sai da faixa tolerada, e
    `None` quando falta data para julgar.
    """
    familia_id = None
    husb = wife = None
    people, families = arvore[0], arvore[1]
    for famc in _ids(people, "FAMC", child_id):
        candidata = families.get(famc)
        if candidata and parent_id in {ref_id(r.value) for r in candidata.sub_records if r.tag in ("HUSB", "WIFE")}:
            familia_id = famc
            break
    if familia_id is None:
        for fam_id in arvore[3].get(child_id, []):
            fam = families.get(fam_id)
            if not fam:
                continue
            pais = {ref_id(r.value) for r in fam.sub_records if r.tag in ("HUSB", "WIFE")}
            if parent_id in pais:
                familia_id = fam_id
                break
    if familia_id:
        fam = arvore[1].get(familia_id)
        husb = next((ref_id(r.value) for r in fam.sub_records if r.tag == "HUSB"), None)
        wife = next((ref_id(r.value) for r in fam.sub_records if r.tag == "WIFE"), None)

    ano_filho = parse_year(birth_date(arvore[0], child_id))
    ano_genitor = parse_year(birth_date(arvore[0], parent_id))
    idade = (ano_filho - ano_genitor) if (ano_filho and ano_genitor) else None
    plausivel = None if idade is None else (IDADE_MINIMA_GENITOR <= idade <= IDADE_MAXIMA_GENITOR)

    return {
        "child_id": child_id,
        "child_name": get_name(arvore[0].get(child_id)),
        "child_birth": birth_date(arvore[0], child_id),
        "parent_id": parent_id,
        "parent_name": get_name(arvore[0].get(parent_id)),
        "parent_birth": birth_date(arvore[0], parent_id),
        "family_id": familia_id,
        "family_husband": {"id": husb, "name": get_name(arvore[0].get(husb))} if husb else None,
        "family_wife": {"id": wife, "name": get_name(arvore[0].get(wife))} if wife else None,
        "age_at_birth": idade,
        "plausible": plausivel,
        "link_source": "FAMC/CHIL do GEDCOM" if familia_id else "sem registro de familia localizado",
    }


# ---------------------------------------------------------------------------
# Parentesco documental
# ---------------------------------------------------------------------------

_ROMANO = {1: "1º", 2: "2º", 3: "3º", 4: "4º", 5: "5º", 6: "6º", 7: "7º", 8: "8º", 9: "9º", 10: "10º"}


def documentary_label(deg_a: int, deg_b: int) -> dict:
    """Traduz (subidas ate o MRCA em cada lado) no parentesco documental.

    `deg_a` conta saltos de A ate o ancestral comum; `deg_b` o mesmo para B. O
    resultado traz o rotulo legivel, a chave canonica (usada depois para casar
    com a tabela do Shared cM Project) e o numero de meioses (saltos pai-filho
    entre as duas pessoas), que e a grandeza que o cM efetivamente mede.
    """
    meioses = deg_a + deg_b
    if deg_a == 0 and deg_b == 0:
        return {"key": "SELF", "label": "A mesma pessoa", "meioses": 0,
                "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": None}}
    if deg_a == 0 or deg_b == 0:
        acima = max(deg_a, deg_b)
        if acima == 1:
            chave, rotulo = "PARENT_CHILD", "Pai/Mãe ↔ Filho(a)"
        elif acima == 2:
            chave, rotulo = "GRANDPARENT", "Avô/Avó ↔ Neto(a)"
        else:
            bis = "bis" * (acima - 2)
            chave, rotulo = f"DIRECT_{acima}", f"{bis}avô/avó ↔ {bis}neto(a)"
        sentido = "A é ascendente direto de B" if deg_a else "A é descendente direto de B"
        return {"key": chave, "label": rotulo, "detail": sentido, "meioses": meioses,
                "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": None}}

    menor, maior = min(deg_a, deg_b), max(deg_a, deg_b)

    if menor == 1:
        # (1,1) sao irmaos; (1,2) tio/tia; (1,3) tio/tia-avo; (1,4) tio/tia-bisavo.
        # Contar `maior` a partir de 2 e o mesmo que contar meioses a partir de 3.
        if maior == 1:
            return {"key": "SIBLINGS", "label": "Irmãos", "meioses": meioses,
                    "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": None}}
        removidos = maior - 2
        if removidos == 0:
            return {"key": "AUNT_UNCLE", "label": "Tio/Tia ↔ Sobrinho(a)", "meioses": meioses,
                    "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": 0}}
        prefixo = "Tio/Tia-avô/avó ↔ Sobrinho(a)-neto(a)" if removidos == 1 else \
            f"Tio/Tia-{'bis' * (removidos - 1)}avô/avó ↔ Sobrinho(a)-{'bis' * (removidos - 1)}neto(a)"
        return {"key": f"GREAT_AUNT_{removidos}", "label": prefixo, "meioses": meioses,
                "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": removidos}}

    grau, removidos = menor - 1, maior - menor
    chave = f"{grau}C" + (f"{removidos}R" if removidos else "")
    rotulo = f"Primos de {_ROMANO.get(grau, str(grau))} grau"
    if removidos == 1:
        rotulo += " (1× removido)"
    elif removidos > 1:
        rotulo += f" com {removidos}× remoção"
    return {"key": chave, "label": rotulo, "meioses": meioses,
            "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": grau, "removed": removidos}}


def _ancestor_depths(arvore, start_id, max_depth: int) -> dict:
    """Menor numero de saltos de `start_id` ate cada ancestral (BFS por pais)."""
    profundidades = {}
    fronteira = [start_id]
    for nivel in range(1, max_depth + 1):
        proxima = []
        for pid in fronteira:
            for pai in get_parents(arvore, pid):
                if pai == start_id or pai in profundidades:
                    continue
                profundidades[pai] = nivel
                proxima.append(pai)
        if not proxima:
            break
        fronteira = proxima
    return profundidades


def _cadeias_ate(arvore, start_id, alvo, max_depth: int, limite=LIMITE_DE_CADEIAS) -> int:
    """Quantas cadeias distintas de pais levam de `start_id` ate `alvo`.

    Mais de uma cadeia ate o MESMO ancestral e a assinatura de colapso de
    pedigree (primos que se casam, endogamia). A contagem para no `limite`.
    """
    if start_id == alvo:
        return 1
    total = 0
    pilha = deque([(start_id, 0)])
    while pilha:
        pid, nivel = pilha.popleft()
        if nivel >= max_depth:
            continue
        for pai in get_parents(arvore, pid):
            if pai == alvo:
                total += 1
                if total >= limite:
                    return total
            else:
                pilha.append((pai, nivel + 1))
    return total


def _cadeia_curta(arvore, start_id, alvo, max_depth):
    """Caminho mais curto de `start_id` ate `alvo` subindo por pais."""
    anterior = {start_id: None}
    fila = deque([(start_id, 0)])
    while fila:
        pid, nivel = fila.popleft()
        if pid == alvo:
            break
        if nivel >= max_depth:
            continue
        for pai in get_parents(arvore, pid):
            if pai not in anterior:
                anterior[pai] = pid
                fila.append((pai, nivel + 1))
    if alvo not in anterior:
        return None
    cadeia, atual = [], alvo
    while atual is not None:
        cadeia.append(atual)
        atual = anterior[atual]
    return cadeia[::-1]


def find_all_common_ancestors(arvore, a_id, b_id, max_depth=MAX_DEPTH_ALTERNATIVOS, limit=12) -> list:
    """Todos os ancestrais comuns dentro do teto, ordenados por distancia total."""
    de_a = _ancestor_depths(arvore, a_id, max_depth)
    de_b = _ancestor_depths(arvore, b_id, max_depth)
    comuns = []
    for pid in set(de_a) & set(de_b):
        da, db = de_a[pid], de_b[pid]
        comuns.append({
            "id": pid,
            "name": get_name(arvore[0].get(pid)),
            "distance_a": da,
            "distance_b": db,
            "total_meioses": da + db,
            "birth": birth_date(arvore[0], pid),
        })
    comuns.sort(key=lambda c: (c["total_meioses"], max(c["distance_a"], c["distance_b"]), c["name"] or ""))
    return comuns[:limit]


def _caminho_alternativo(arvore, a_id, b_id, ancestral_id):
    subida = _cadeia_curta(arvore, a_id, ancestral_id, MAX_DEPTH_ALTERNATIVOS)
    descida = _cadeia_curta(arvore, b_id, ancestral_id, MAX_DEPTH_ALTERNATIVOS)
    if not subida or not descida:
        return None
    ids = subida + descida[::-1][1:]
    return {"ids": ids, "names": [get_name(arvore[0].get(i)) for i in ids], "via": ancestral_id}


def documentary_relationship(arvore, a_id, b_id, homonyms=None) -> dict:
    """Parentesco documental completo entre duas pessoas do GEDCOM.

    Nunca le cM. Devolve caminho principal (o mesmo que o legado produzia),
    caminhos alternativos, ancestrais comuns, distancia geracional, rotulo,
    evidencias por salto e avisos.
    """
    if a_id not in arvore[0] or b_id not in arvore[0]:
        return {"status": "not_found", "source": "GEDCOM",
                "label": "Pessoas não encontradas no GEDCOM",
                "warnings": [{"code": "pessoa_ausente", "message": "Registro ausente no GEDCOM carregado."}]}

    path, comum = find_ancestral_path(arvore, a_id, b_id, max_depth=MAX_DEPTH)
    avisos = []
    homonimos = homonyms or {}

    if not path:
        avisos_sem_caminho = [{
            "code": "sem_caminho",
            "message": "Nenhum caminho subindo por pais liga as duas pessoas dentro do teto "
                       f"de {MAX_DEPTH} iterações. Isso não prova ausência de parentesco: "
                       "pode faltar vínculo no GEDCOM.",
        }]
        if homonimos.get("ambiguous"):
            avisos_sem_caminho.append({
                "code": "homonimo",
                "message": (f"Identidade ambígua — análise não conclusiva. Existem "
                            f"{homonimos.get('exact_count')} registros envolvendo "
                            f"'{homonimos.get('query')}' no GEDCOM e não é possível determinar qual "
                            "deles é a pessoa procurada."),
            })
        return {
            "status": "not_found",
            "source": "GEDCOM",
            "label": "Parentesco documental não encontrado",
            "relationship_key": None,
            "meioses": None,
            "degrees": None,
            "person_a": person_summary(arvore, a_id),
            "person_b": person_summary(arvore, b_id),
            "common_ancestor": None,
            "path": None,
            "common_ancestors": [],
            "additional_paths": [],
            "evidence": [],
            "homonyms": homonimos,
            "ambiguous_identity": bool(homonimos.get("ambiguous")),
            "warnings": avisos_sem_caminho,
        }

    indice = path.index(comum) if comum in path else 0
    deg_a, deg_b = indice, len(path) - 1 - indice
    parentesco = documentary_label(deg_a, deg_b)

    evidencia = []
    for i in range(len(path) - 1):
        if i < indice:
            evidencia.append(hop_evidence(arvore, path[i], path[i + 1]))
        else:
            evidencia.append(hop_evidence(arvore, path[i + 1], path[i]))

    for item in evidencia:
        if item["plausible"] is False:
            avisos.append({
                "code": "data_impossivel",
                "message": (f"Vínculo cronologicamente incompatível: {item['parent_name']} "
                            f"({item['parent_birth'] or 'sem data'}) declarado como genitor de "
                            f"{item['child_name']} ({item['child_birth'] or 'sem data'}), "
                            f"diferença de {item['age_at_birth']} anos. O caminho foi mantido como o "
                            "GEDCOM o declara — confira o registro antes de aceitar a conexão."),
                "family_id": item["family_id"],
            })

    comuns = find_all_common_ancestors(arvore, a_id, b_id)
    alternativos = []
    for c in comuns:
        if c["id"] == comum:
            continue
        caminho = _caminho_alternativo(arvore, a_id, b_id, c["id"])
        if caminho:
            alternativos.append({**caminho, "distance_a": c["distance_a"], "distance_b": c["distance_b"],
                                 "total_meioses": c["total_meioses"], "ancestor_name": c["name"]})

    if alternativos:
        avisos.append({
            "code": "caminhos_multiplos",
            "message": (f"Foram encontrados {len(alternativos) + 1} caminhos genealógicos distintos "
                        "(inclusive por outros ancestrais comuns). O caminho exibido é o de menor "
                        "distância total; os demais estão listados e nenhum foi descartado."),
        })

    colapso = []
    for c in comuns:
        cadeias = _cadeias_ate(arvore, a_id, c["id"], MAX_DEPTH_ALTERNATIVOS)
        if cadeias > 1:
            colapso.append({"ancestor_id": c["id"], "ancestor_name": c["name"], "chains": cadeias})
    if colapso:
        avisos.append({
            "code": "colapso_de_pedigree",
            "message": ("Possível colapso de pedigree/endogamia: "
                        + "; ".join(f"{c['ancestor_name']} é alcançado por {c['chains']} cadeias distintas"
                                    for c in colapso[:3])
                        + ". Isso infla o cM esperado e enfraquece a leitura do valor compartilhado."),
        })

    if homonimos.get("ambiguous"):
        avisos.append({
            "code": "homonimo",
            "message": (f"Identidade ambígua — análise não conclusiva. Existem "
                        f"{homonimos['exact_count']} registros envolvendo '{homonimos['query']}' no "
                        "GEDCOM e não é possível determinar qual deles é a pessoa procurada. O caminho "
                        "exibido pertence a um deles: confira as fichas (ID, datas, locais, pais, "
                        "cônjuges, filhos) antes de aceitar o parentesco."),
        })

    return {
        "status": "ambiguous" if homonimos.get("ambiguous") else "found",
        "source": "GEDCOM",
        "label": parentesco["label"],
        "relationship_key": parentesco["key"],
        "meioses": parentesco["meioses"],
        "degrees": parentesco["degrees"],
        "person_a": person_summary(arvore, a_id),
        "person_b": person_summary(arvore, b_id),
        "common_ancestor": {"id": comum, "name": get_name(arvore[0].get(comum)), "birth": birth_date(arvore[0], comum)},
        "common_ancestors": comuns,
        "path": {"ids": path, "names": [get_name(arvore[0].get(p)) for p in path]},
        "additional_paths": alternativos,
        "evidence": evidencia,
        "homonyms": homonimos,
        "ambiguous_identity": bool(homonimos.get("ambiguous")),
        "warnings": avisos,
    }


__all__ = [
    "documentary_relationship", "documentary_label", "person_summary",
    "homonym_dossier", "hop_evidence", "find_all_common_ancestors",
    "parse_year", "birth_date", "death_date", "get_children", "normalizar",
    "MAX_DEPTH", "IDADE_MINIMA_GENITOR", "IDADE_MAXIMA_GENITOR",
]
