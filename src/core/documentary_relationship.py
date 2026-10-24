"""Parentesco DOCUMENTAL: a fachada publica e a montagem do cartao.

Por que este arquivo continua sendo o endereco: ele era o modulo inteiro ate 2026-10-24,
quando a `OPP-20261024-SEPM` separou o que ele faz em quatro modulos de responsabilidade
unica — `core.datas_do_gedcom` le data e local do registro; `core.fichas_da_pessoa` monta a
ficha comparavel e o indice pai para filhos; `core.homonimos` reconhece o mesmo nome e
monta o dossie; e `core.caminhos_alternativos` enumera ancestrais comuns, cadeias e
caminhos alternativos. O que sobrou aqui e o cartao: a decisao de qual caminho apresentar, a
evidencia de cada salto, os avisos e o dicionario final. A fachada reexporta os dezoito
nomes de `__all__` para que os quinze consumidores nao mudem de endereco.

Regra do projeto: o GEDCOM determina o parentesco documental. O DNA **nao** altera nada do
que este modulo devolve — nenhuma funcao daqui aceita cM nem le o CSV. Quem confronta as
duas evidencias e `core.evidence_comparison`, depois e separadamente.

Por que datas entram aqui: `_reversa_sdd/busca-caminho` documenta que o legado nunca olhou
data, e o BFS sobe por pais e aceita qualquer salto. Medido em 2026-10 no GEDCOM real
`Arvore_Unificada_Oficial_V1_2.ged`, isso produz caminho com mae nascida 11 anos DEPOIS do
filho (`@F6@`: Celso Gomes Gama, n. 1961, filho de Maria Auxiliadora, n. 1972) apresentado
como "conexao direta por ancestral comum". Uma data impossivel **nao** invalida o vinculo
nem muda o parentesco: o dado e do documento, e cabe ao operador julgar — o cartao
**registra a evidencia** (`evidence[].age_at_birth`, `plausible`) e **avisa**
(`warnings[].code == "data_impossivel"`).
"""
from __future__ import annotations

from .caminhos_alternativos import (
    MAX_DEPTH_ALTERNATIVOS,
    _cadeias_ate,
    _caminho_alternativo,
    find_all_common_ancestors,
)
from .datas_do_gedcom import (
    IDADE_MAXIMA_GENITOR,
    IDADE_MINIMA_GENITOR,
    birth_date,
    death_date,
    intervalo_de_geracao_mediano,
    parse_year,
)
from .fichas_da_pessoa import get_children, ids_com_tag, person_summary
from .graus_de_parentesco import ROMANO, nome_do_grau, nome_do_primo  # reexportados
from .homonimos import homonym_dossier, normalizar
from .path_finding import MAX_DEPTH, find_ancestral_path
from .registro import get_name, ref_id

# Evidencia de cada salto

def _pais_da_familia(familia) -> set:
    """Os ids declarados como HUSB e WIFE na familia."""
    return {ref_id(r.value) for r in familia.sub_records if r.tag in ("HUSB", "WIFE")}


def _familia_que_liga(families, candidatos, parent_id):
    """A primeira familia de `candidatos` em que `parent_id` e HUSB ou WIFE."""
    for fam_id in candidatos:
        familia = families.get(fam_id)
        if familia and parent_id in _pais_da_familia(familia):
            return fam_id
    return None


def hop_evidence(arvore, child_id, parent_id) -> dict:
    """O registro cru que liga `child_id` a `parent_id`, com a idade implicada.

    Devolve a familia (FAM), o casal declarado nela e as datas, para que a tela
    possa mostrar POR QUE o sistema afirmou aquele salto. `plausible` e False
    quando a idade do genitor no nascimento do filho sai da faixa tolerada, e
    `None` quando falta data para julgar.
    """
    people, families = arvore[0], arvore[1]
    familia_id = _familia_que_liga(families, ids_com_tag(people, "FAMC", child_id), parent_id)
    if familia_id is None:
        familia_id = _familia_que_liga(families, arvore[3].get(child_id, []), parent_id)
    husb = wife = None
    if familia_id:
        fam = families.get(familia_id)
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


# Parentesco documental

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
    # O rotulo tem FONTE UNICA em `nome_do_primo`: a mesma relacao aparece na tabela
    # publicada (bloco 3) e aqui, e as duas versoes nao podem divergir. Ver 045.
    rotulo = nome_do_primo(grau, removidos)
    return {"key": chave, "label": rotulo, "meioses": meioses,
            "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": grau, "removed": removidos}}


def _aviso_de_homonimo(homonimos, com_caminho: bool = True) -> dict | None:
    """Aviso de identidade ambigua, com o acrescimo que so faz sentido havendo caminho.

    A mensagem existe aqui uma vez so. O ramo de nao encontrado usa o mesmo texto, sem o
    acrescimo final, porque ali nao ha caminho exibido para conferir.
    """
    if not homonimos.get("ambiguous"):
        return None
    mensagem = ("Identidade ambígua — análise não conclusiva. Existem "
                f"{homonimos.get('exact_count')} registros envolvendo "
                f"'{homonimos.get('query')}' no GEDCOM e não é possível determinar qual "
                "deles é a pessoa procurada.")
    if com_caminho:
        mensagem += (" O caminho exibido pertence a um deles: confira as fichas (ID, datas, "
                     "locais, pais, cônjuges, filhos) antes de aceitar o parentesco.")
    return {"code": "homonimo", "message": mensagem}


def _evidencia_do_caminho(arvore, path, indice) -> list:
    """A evidencia de cada salto: sobe ate o MRCA e desce depois dele."""
    evidencia = []
    for i in range(len(path) - 1):
        if i < indice:
            evidencia.append(hop_evidence(arvore, path[i], path[i + 1]))
        else:
            evidencia.append(hop_evidence(arvore, path[i + 1], path[i]))
    return evidencia


def _aviso_de_data_impossivel(item) -> dict:
    """O aviso de um salto cuja idade do genitor sai da faixa tolerada."""
    return {
        "code": "data_impossivel",
        "message": (f"Vínculo cronologicamente incompatível: {item['parent_name']} "
                    f"({item['parent_birth'] or 'sem data'}) declarado como genitor de "
                    f"{item['child_name']} ({item['child_birth'] or 'sem data'}), "
                    f"diferença de {item['age_at_birth']} anos. O caminho foi mantido como o "
                    "GEDCOM o declara — confira o registro antes de aceitar a conexão."),
        "family_id": item["family_id"],
    }


def _avisos_de_data(evidencia) -> list:
    """Um aviso por salto implausivel, na ordem do caminho."""
    return [_aviso_de_data_impossivel(item) for item in evidencia if item["plausible"] is False]


def _caminhos_alternativos(arvore, a_id, b_id, comuns, comum) -> list:
    """Os caminhos que passam por outros ancestrais comuns, um por ancestral."""
    alternativos = []
    for c in comuns:
        if c["id"] == comum:
            continue
        caminho = _caminho_alternativo(arvore, a_id, b_id, c["id"])
        if caminho:
            alternativos.append({**caminho, "distance_a": c["distance_a"], "distance_b": c["distance_b"],
                                 "total_meioses": c["total_meioses"], "ancestor_name": c["name"]})
    return alternativos


def _colapso_de_pedigree(arvore, a_id, comuns) -> list:
    """Ancestrais alcancados por mais de uma cadeia de pais, ate o limite."""
    colapso = []
    for c in comuns:
        cadeias = _cadeias_ate(arvore, a_id, c["id"], MAX_DEPTH_ALTERNATIVOS)
        if cadeias > 1:
            colapso.append({"ancestor_id": c["id"], "ancestor_name": c["name"], "chains": cadeias})
    return colapso


def _aviso_de_caminhos_multiplos(alternativos) -> dict | None:
    """O aviso de que existem caminhos alem do exibido, ou None."""
    if not alternativos:
        return None
    return {
        "code": "caminhos_multiplos",
        "message": (f"Foram encontrados {len(alternativos) + 1} caminhos genealógicos distintos "
                    "(inclusive por outros ancestrais comuns). O caminho exibido é o de menor "
                    "distância total; os demais estão listados e nenhum foi descartado."),
    }


def _aviso_de_colapso(colapso) -> dict | None:
    """O aviso de colapso de pedigree, citando no maximo tres ancestrais, ou None."""
    if not colapso:
        return None
    return {
        "code": "colapso_de_pedigree",
        "message": ("Possível colapso de pedigree/endogamia: "
                    + "; ".join(f"{c['ancestor_name']} é alcançado por {c['chains']} cadeias distintas"
                                for c in colapso[:3])
                    + ". Isso infla o cM esperado e enfraquece a leitura do valor compartilhado."),
    }


def documental_nao_encontrado(arvore, a_id, b_id, homonimos=None) -> dict:
    """A forma do parentesco documental quando NAO se apresenta caminho nenhum.

    Por que isto e uma funcao, e nao um literal: ha DUAS razoes para apresentar um cartao
    assim, e so uma delas e a ausencia de caminho — (1) **nao existe caminho**: a busca subiu
    por pais e nao ligou as duas pessoas, caso que `documentary_relationship` encontra
    sozinho; e (2) **existe caminho, e ele nao e apresentado**: a politica de janela de vida,
    quando a idade do registro escolhido passa de `IDADE_IMPOSSIVEL`, trata o cartao como este
    grupo e desconsidera o diagrama (`core.dna_analysis`). As duas tem de sair com a MESMA
    forma, palavra por palavra: e isso que faz a segunda ser, de fato, "tratada como" a
    primeira — se a forma fosse copiada, as duas divergiriam na primeira correcao de texto.

    O que esta funcao NAO decide: ela nao decide nada — recebe ids e devolve a forma; quem
    decide apresentar assim e quem a chama. No caso (1) a decisao e do proprio caminho; no
    caso (2), do operador, e ela esta declarada em
    `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`.
    """
    homonimos = homonimos or {}
    avisos = [{
        "code": "sem_caminho",
        "message": "Nenhum caminho subindo por pais liga as duas pessoas dentro do teto "
                   f"de {MAX_DEPTH} iterações. Isso não prova ausência de parentesco: as "
                   "duas podem ser ligadas por irmandade, por outro ramo colateral que o "
                   "GEDCOM não registra, ou por um vínculo que falte no arquivo.",
    }]
    aviso = _aviso_de_homonimo(homonimos, com_caminho=False)
    if aviso is not None:
        avisos.append(aviso)
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
    homonimos = homonyms or {}

    if not path:
        return documental_nao_encontrado(arvore, a_id, b_id, homonimos=homonimos)

    indice = path.index(comum) if comum in path else 0
    deg_a, deg_b = indice, len(path) - 1 - indice
    parentesco = documentary_label(deg_a, deg_b)

    evidencia = _evidencia_do_caminho(arvore, path, indice)
    comuns = find_all_common_ancestors(arvore, a_id, b_id)
    alternativos = _caminhos_alternativos(arvore, a_id, b_id, comuns, comum)
    colapso = _colapso_de_pedigree(arvore, a_id, comuns)

    avisos = _avisos_de_data(evidencia)
    for aviso in (
        _aviso_de_caminhos_multiplos(alternativos),
        _aviso_de_colapso(colapso),
        _aviso_de_homonimo(homonimos),
    ):
        if aviso is not None:
            avisos.append(aviso)

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
    "homonym_dossier",
    "parse_year", "birth_date", "death_date", "get_children", "normalizar",
    "intervalo_de_geracao_mediano",
    # Reexportado de `core.graus_de_parentesco` desde 2026-10-22: continua publico daqui
    # para quem ja o importava (dois testes), e e o que impede que a linha de import seja
    # lida como codigo morto e apagada. `ROMANO`, do mesmo import, continua importavel
    # daqui, mas nao e anunciado porque nenhum consumidor o importa.
    "nome_do_grau",
    "IDADE_MINIMA_GENITOR", "IDADE_MAXIMA_GENITOR",
]
