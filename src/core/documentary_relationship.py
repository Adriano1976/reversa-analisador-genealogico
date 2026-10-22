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
from statistics import median

from .family_navigation import get_parents
from .graus_de_parentesco import ROMANO, nome_do_grau  # reexportados: `nome_do_grau` e publico daqui
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


def intervalo_de_geracao_mediano(arvore) -> float | None:
    """Mediana dos intervalos pai-filho datados da arvore, em anos.

    ## Por que esta funcao mora aqui, e nao na fachada de validacao

    Ela nasceu em `application.validacao` (feature `028`), onde so a fachada a usava.
    A feature `031` precisou do MESMO numero dentro do fluxo de DNA, para o cartao
    mostrar o veredito de viabilidade temporal. Duplicar aqui seria pior do que mover:
    duas implementacoes de `G` podem divergir em silencio, e o mesmo kit passaria a ter
    dois vereditos — um no cartao, outro na fachada.

    O lugar e este porque o dado e todo documental: datas de nascimento e vinculos de
    filiacao, que este modulo ja le com `parse_year` e `birth_date`.

    So entram intervalos com as duas datas e dentro de 12-70 anos (a mesma faixa de
    `IDADE_MINIMA_GENITOR`/`IDADE_MAXIMA_GENITOR`). Com menos de 3 amostras devolve
    `None`, e quem chama cai para o prior declarado de 25 anos — `None` aqui significa
    "a arvore nao tem amostra suficiente", nunca zero.
    """
    people, families = arvore[0], arvore[1]
    intervalos: list[int] = []

    for familia in families.values():
        pais = []
        for registro in familia.sub_records:
            if registro.tag in ("HUSB", "WIFE"):
                pid = ref_id(registro.value)
                if pid:
                    pais.append(pid)
        if not pais:
            continue
        for registro in familia.sub_records:
            if registro.tag != "CHIL":
                continue
            filho = ref_id(registro.value)
            ano_filho = parse_year(birth_date(people, filho))
            if ano_filho is None:
                continue
            for pai in pais:
                ano_pai = parse_year(birth_date(people, pai))
                if ano_pai is None:
                    continue
                intervalo = ano_filho - ano_pai
                if IDADE_MINIMA_GENITOR <= intervalo <= IDADE_MAXIMA_GENITOR:
                    intervalos.append(intervalo)

    if len(intervalos) < 3:
        return None
    return float(median(intervalos))


# ---------------------------------------------------------------------------
# Fichas de pessoa
# ---------------------------------------------------------------------------

def _ids(people, sub_tag, pid):
    return [ref_id(r.value) for r in people[pid].sub_records if r.tag == sub_tag] if pid in people else []


#: Nome do atributo privado onde o indice pai -> filhos fica preso ao GRAFO da
#: arvore. Nao e estado de modulo: o indice nasce e morre com a arvore daquela
#: requisicao, entao nao ha retencao entre requisicoes nem chave de conteudo
#: para colidir (o problema do L-24). Duas threads que compartilhem a mesma
#: arvore montam o mesmo mapa; a atribuicao e atomica e o mapa e somente leitura.
_ATRIBUTO_DE_FILHOS = "_indice_de_filhos_do_documental"


def _construir_indice_de_filhos(families) -> dict:
    """Pai -> filhos, na ordem em que a varredura de familias os encontra.

    Reproduz `get_children` de antes: percorre as familias na ordem do dicionario,
    acrescenta os filhos de cada familia ao pai e a mae e deduplica por pessoa. A
    ordem e contrato observavel, por isso a construcao nao reordena nada.
    """
    mapa = {}
    for fam in families.values():
        husb = wife = None
        filhos = []
        for rec in fam.sub_records:
            tag = rec.tag
            if tag == "HUSB":
                husb = ref_id(rec.value)
            elif tag == "WIFE":
                wife = ref_id(rec.value)
            elif tag == "CHIL":
                filhos.append(rec.value)
        for pai in (husb, wife):
            if not pai:
                continue
            destino = mapa.setdefault(pai, [])
            for valor in filhos:
                cid = ref_id(valor)
                if cid not in destino:
                    destino.append(cid)
    return mapa


def _indice_de_filhos(arvore) -> dict:
    """O indice da arvore, montado uma vez e preso ao grafo dela."""
    grafo = arvore[2]
    mapa = getattr(grafo, _ATRIBUTO_DE_FILHOS, None)
    if mapa is None:
        mapa = _construir_indice_de_filhos(arvore[1])
        setattr(grafo, _ATRIBUTO_DE_FILHOS, mapa)
    return mapa


def get_children(arvore, person_id):
    """Filhos declarados em qualquer familia em que a pessoa seja HUSB ou WIFE."""
    return list(_indice_de_filhos(arvore).get(person_id, []))


def person_summary(arvore, person_id) -> dict:
    """Ficha comparavel de uma pessoa, para desambiguar homonimos."""
    people = arvore[0]
    birth = birth_date(people, person_id)
    death = death_date(people, person_id)
    parents = get_parents(arvore, person_id)
    return {
        "id": person_id,
        "name": get_name(people.get(person_id)),
        "sex": next((r.value for r in people[person_id].sub_records if r.tag == "SEX"), None) if person_id in people else None,
        "birth": birth,
        "birth_year": parse_year(birth),
        "birth_place": _local_de(people, person_id, "BIRT"),
        "death": death,
        "death_year": parse_year(death),
        "parents": parents,
        "parent_names": [get_name(people.get(p)) for p in parents],
        "spouses": _ids(people, "FAMS", person_id),
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


def _diferencas_de_fichas(fichas) -> list:
    """Campos em que as fichas JA MONTADAS divergem, o que o operador precisa olhar."""
    campos = [
        ("birth", "data de nascimento"),
        ("birth_place", "local de nascimento"),
        ("death", "data de falecimento"),
        ("parents", "pais"),
        ("children", "filhos"),
        ("sex", "sexo"),
    ]
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
    # As duas leituras saem da MESMA lista de fichas: `_diferencas` era chamado
    # uma vez para `differences` e outra dentro de `identical_data`, e cada
    # chamada remontava todas as fichas (medido: 6 para 2 homonimos).
    differences = _diferencas_de_fichas(fichas) if len(exatos) > 1 else []
    return {
        "query": name_query,
        "exact_count": len(exatos),
        "exact_matches": fichas,
        "similar_count": len(parecidos),
        "similar_matches": [person_summary(arvore, pid) for pid in parecidos[:5]],
        "ambiguous": len(exatos) > 1,
        "differences": differences,
        "identical_data": bool(len(exatos) > 1 and not differences),
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

# ---------------------------------------------------------------------------
# O nome do avo, do neto e dos antepassados comuns, por grau
#
# A serie inteira — e o racional dela, incluindo o defeito de 2026-10-14 que a
# tabela de palavras inteiras corrige — mora em `core.graus_de_parentesco` desde
# 2026-10-22. A mudanca de casa nao mudou palavra nenhuma: `nome_do_grau` e
# `ROMANO` sao importados no topo deste modulo e continuam publicos daqui.
#
# ## Por que saiu daqui
#
# `core.relationship_hypotheses` e a tabela do Shared cM Project: um modulo SEM
# IMPORT NENHUM, que traduz cM em possibilidades no caminho do CSV. A coluna do
# antepassado comum mais recente precisa da terceira forma da serie — o plural
# `bisavós`, e nao `bisavô/avó`. Importar `documentary_relationship` de la
# arrastaria `path_finding` e `networkx` para dentro daquele caminho; duplicar as
# palavras criaria uma segunda fonte para a mesma serie. Um modulo que nao
# importa nada resolve as duas coisas, e e por isso que ele existe.
# ---------------------------------------------------------------------------


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
            chave = f"DIRECT_{acima}"
            rotulo = f"{nome_do_grau(acima)} ↔ {nome_do_grau(acima, plural_neto=True)}"
        sentido = "A é ascendente direto de B" if deg_a else "A é descendente direto de B"
        return {"key": chave, "label": rotulo, "detail": sentido, "meioses": meioses,
                "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": None}}

    menor, maior = min(deg_a, deg_b), max(deg_a, deg_b)

    if menor == 1:
        # (1,1) sao irmaos; (1,2) tio/tia; (1,3) tio/tia-avo; (1,4) tio/tia-bisavo;
        # (1,5) tio/tia-trisavo. Contar `maior` a partir de 2 e o mesmo que contar
        # meioses a partir de 3.
        if maior == 1:
            return {"key": "SIBLINGS", "label": "Irmãos", "meioses": meioses,
                    "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": None}}
        removidos = maior - 2
        if removidos == 0:
            return {"key": "AUNT_UNCLE", "label": "Tio/Tia ↔ Sobrinho(a)", "meioses": meioses,
                    "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": 0}}
        grau_do_tio = maior - 1
        rotulo = (f"Tio/Tia-{nome_do_grau(grau_do_tio)} ↔ "
                  f"Sobrinho(a)-{nome_do_grau(grau_do_tio, plural_neto=True)}")
        return {"key": f"GREAT_AUNT_{removidos}", "label": rotulo, "meioses": meioses,
                "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": None, "removed": removidos}}

    grau, removidos = menor - 1, maior - menor
    chave = f"{grau}C" + (f"{removidos}R" if removidos else "")
    rotulo = f"Primos de {ROMANO.get(grau, str(grau))} grau"
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


def documental_nao_encontrado(arvore, a_id, b_id, homonimos=None) -> dict:
    """A forma do parentesco documental quando NAO se apresenta caminho nenhum.

    ## Por que isto e uma funcao, e nao um literal dentro de `documentary_relationship`

    Porque ha DUAS razoes para apresentar um cartao assim, e so uma delas e a ausencia de
    caminho:

    1. **nao existe caminho** — a busca subiu por pais e nao ligou as duas pessoas. E o caso
       que `documentary_relationship` encontra sozinho;
    2. **existe caminho, e ele nao e apresentado** — a politica de janela de vida: quando a
       idade do registro escolhido passa de `IDADE_IMPOSSIVEL`, o cartao passa a ser tratado
       como este grupo e o diagrama e desconsiderado (`core.dna_analysis`).

    As duas tem de sair com a MESMA forma, palavra por palavra: e isso que faz a segunda ser,
    de fato, "tratada como" a primeira. Se a forma fosse copiada, as duas divergiriam na
    primeira correcao de texto.

    ## O que esta funcao NAO decide

    Ela nao decide nada: recebe ids e devolve a forma. Quem decide apresentar assim e quem a
    chama. No caso (1) a decisao e do proprio caminho; no caso (2), do operador, e ela esta
    declarada em `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`.
    """
    homonimos = homonimos or {}
    avisos = [{
        "code": "sem_caminho",
        "message": "Nenhum caminho subindo por pais liga as duas pessoas dentro do teto "
                   f"de {MAX_DEPTH} iterações. Isso não prova ausência de parentesco: as "
                   "duas podem ser ligadas por irmandade, por outro ramo colateral que o "
                   "GEDCOM não registra, ou por um vínculo que falte no arquivo.",
    }]
    if homonimos.get("ambiguous"):
        avisos.append({
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
        "warnings": avisos,
    }


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
        return documental_nao_encontrado(arvore, a_id, b_id, homonimos=homonimos)

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
    "documentary_relationship", "documental_nao_encontrado",
    "documentary_label", "person_summary",
    "homonym_dossier", "hop_evidence", "find_all_common_ancestors",
    "parse_year", "birth_date", "death_date", "get_children", "normalizar",
    "intervalo_de_geracao_mediano",
    # Reexportados de `core.graus_de_parentesco` desde 2026-10-22: continuam publicos
    # daqui para quem ja os importava, e e o que impede que a linha de import seja
    # lida como codigo morto e apagada.
    "nome_do_grau", "ROMANO",
    "MAX_DEPTH", "IDADE_MINIMA_GENITOR", "IDADE_MAXIMA_GENITOR",
]
