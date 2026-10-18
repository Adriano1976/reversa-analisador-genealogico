"""Fachada de leitura e cruzamento do validador de dados.

O núcleo (`core.validator`) é puro e não conhece árvore, arquivo nem relógio. Esta
camada faz o trabalho de borda: carrega o GEDCOM uma vez, lê o CSV, monta a
evidência genética, resolve o match pelo mesmo `core.matching` do fluxo de DNA,
monta o parentesco documental com `core.documentary_relationship` e entrega uma
`ComparacaoParaValidar` pronta ao núcleo.

## O que NÃO acontece aqui

- Nenhum parser novo: usa `parsers.gedcom_parser.carregar_arvore` e
  `parsers.csv_ingest.read_csv_with_fallback`.
- Nenhum matching novo: usa `core.matching.build_ged_indexes` e
  `match_candidates`.
- Nenhuma regra de status: a decisão é toda de `core.validator`.
- Nenhuma escrita em banco, template ou `app.py`. O resultado é efêmero.

## Política de raiz e de match

A raiz (doador) é resolvida como no fluxo de DNA: o nome informado casa por
substring, sem diferenciar maiúsculas, e o primeiro registro é usado; se o nome
não existir, `PessoaNaoEncontrada` sobe com a mesma mensagem do fluxo. O match é
o primeiro candidato que tem caminho documental — a mesma política do
`core.dna_analysis`. O doador nunca é candidato a match.

## Por que a árvore é parseada uma vez

O fluxo de DNA atual reparseia a árvore a cada requisição. Aqui a fachada carrega
uma vez e reutiliza o valor para todos os kits e para o intervalo de geração.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Callable

from core.documentary_relationship import (
    IDADE_MAXIMA_GENITOR,
    IDADE_MINIMA_GENITOR,
    birth_date,
    documentary_relationship,
    homonym_dossier,
    parse_year,
)
from core.erros import PessoaNaoEncontrada
from core.evidence_comparison import compare
from core.genetic_evidence import evidence_for
from core.janela_de_vida import ano_de_referencia
from core.matching import build_ged_indexes, match_candidates
from core.registro import get_name, ref_id
from core.relationship_hypotheses import hypotheses_for_evidence
from core.validator import (
    ComparacaoParaValidar,
    agregar_resultados,
    validar_comparacao,
)


@dataclass(frozen=True)
class DependenciasDeValidacao:
    """Funções de borda que a fachada consome, injetáveis nos testes."""

    carregar_arvore: Callable
    ler_csv: Callable
    construir_evidencia: Callable


def _dependencias_padrao() -> DependenciasDeValidacao:
    """As dependências reais, importadas só quando a fachada é chamada."""
    from core.genetic_evidence import build_genetic_evidence
    from parsers.csv_ingest import read_csv_with_fallback
    from parsers.gedcom_parser import carregar_arvore

    return DependenciasDeValidacao(
        carregar_arvore=carregar_arvore,
        ler_csv=read_csv_with_fallback,
        construir_evidencia=build_genetic_evidence,
    )


def _ref(familia, tag: str):
    """xref_id de HUSB/WIFE/CHIL em um registro FAM, ou None."""
    for registro in familia.sub_records:
        if registro.tag == tag:
            return ref_id(registro.value)
    return None


def intervalo_de_geracao_mediano(arvore) -> float | None:
    """Mediana dos intervalos pai-filho datados da árvore, em anos.

    Só entram intervalos com as duas datas e dentro de 12–70. Com menos de 3
    amostras devolve `None`; o núcleo cai para o prior declarado de 25 anos.
    """
    people, families = arvore[0], arvore[1]
    intervalos: list[int] = []

    for familia in families.values():
        pais = [p for p in (_ref(familia, "HUSB"), _ref(familia, "WIFE")) if p]
        if not pais:
            continue
        filhos = [ref_id(registro.value) for registro in familia.sub_records
                  if registro.tag == "CHIL"]
        for filho in filhos:
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


def _resolver_raiz(arvore, nome_doador: str) -> str:
    """Primeiro registro cujo nome contém o nome informado, como no fluxo de DNA."""
    candidatos = [pid for pid, pessoa in arvore[0].items()
                  if nome_doador.lower() in get_name(pessoa).lower()]
    if not candidatos:
        raise PessoaNaoEncontrada(f"Seu nome '{nome_doador}' não foi encontrado no GEDCOM.")
    return candidatos[0]


def _documental_sem_caminho() -> dict:
    """A forma que `validar_comparacao` entende como 'não há caminho'."""
    return {
        "status": "not_found",
        "label": "Parentesco documental não encontrado",
        "relationship_key": None,
        "meioses": None,
        "degrees": {"a_up": 0, "b_up": 0},
        "common_ancestor": None,
        "path": {"ids": [], "names": []},
        "evidence": [],
        "ambiguous_identity": False,
        "homonyms": {},
    }


def validar_arquivos(caminho_gedcom: str, caminho_dna: str, nome_doador: str,
                     ano_referencia: int | None = None,
                     deps: DependenciasDeValidacao | None = None,
                     incluir_documental: bool = False) -> dict:
    """Lê GEDCOM e CSV, cruza cada kit e devolve um resultado por kit.

    O retorno é ``{"doador", "comparacoes", "resumo", "ano_referencia",
    "intervalo_de_geracao"}``. ``resumo`` usa o pior status entre os kits; a
    árvore é parseada uma vez e o intervalo de geração é calculado uma vez.

    ## `incluir_documental` existe para a etapa de correção

    O resultado de `validar_comparacao` **não** carrega `path.ids` nem `evidence`:
    os campos que dizem ONDE cortar vivem só no dicionário `documental`. Com o
    parâmetro em `True`, cada item de `comparacoes` ganha a chave `documental` (o
    mesmo objeto já montado, não uma cópia) e o retorno ganha a chave `arvore` — a
    tupla já parseada, para a cirurgia não reparsear o arquivo.

    Sem o parâmetro, o retorno é exatamente o de antes: a emenda é aditiva e
    desligada por padrão.
    """
    deps = deps or _dependencias_padrao()
    arvore = deps.carregar_arvore(caminho_gedcom)
    raiz_id = _resolver_raiz(arvore, nome_doador)
    raiz_nascimento = birth_date(arvore[0], raiz_id)
    ano_base = (ano_referencia if ano_referencia is not None
                else ano_de_referencia(datetime.now().year, raiz_nascimento))
    intervalo = intervalo_de_geracao_mediano(arvore)

    data_frame = deps.ler_csv(caminho_dna)
    evidencias, _avisos = deps.construir_evidencia(data_frame)
    ged_index, surname_index, features = build_ged_indexes(arvore)

    dossie_por_nome: dict[str, dict] = {}
    documental_por_pessoa: dict[str, dict] = {}
    resultados: list[dict] = []

    def dossie(nome: str, candidatos: list[str]) -> dict:
        if nome not in dossie_por_nome:
            dossie_por_nome[nome] = homonym_dossier(arvore, nome, similar_ids=candidatos)
        return dossie_por_nome[nome]

    for _nome_csv, por_kit in evidencias.items():
        for chave_kit, kit in por_kit.items():
            candidatos, _motivo = match_candidates(
                arvore, kit["person_name_csv"], kit["total_cm"],
                ged_index, surname_index, features)
            candidatos = [c for c in candidatos if c != raiz_id]

            if candidatos:
                documentais = []
                for candidato in candidatos:
                    if candidato not in documental_por_pessoa:
                        documental_por_pessoa[candidato] = documentary_relationship(
                            arvore, raiz_id, candidato,
                            homonyms=dossie(kit["person_name_csv"], candidatos))
                    documentais.append((candidato, documental_por_pessoa[candidato]))
                match_id, documental = next(
                    ((c, d) for c, d in documentais if (d.get("path") or {}).get("ids")),
                    documentais[0])
            else:
                match_id, documental = None, _documental_sem_caminho()

            evidencia = evidence_for(por_kit, kit_key=chave_kit)
            hipoteses = hypotheses_for_evidence(evidencia)
            comparacao = compare(documental, hipoteses, evidencia)

            doador = {
                "id": raiz_id,
                "nome": get_name(arvore[0][raiz_id]),
                "nascimento": raiz_nascimento,
            }
            match = {
                "id": match_id,
                "nome": (get_name(arvore[0][match_id]) if match_id
                         else kit["person_name_csv"]),
                "nascimento": birth_date(arvore[0], match_id) if match_id else None,
            }

            resultado = validar_comparacao(ComparacaoParaValidar(
                doador=doador,
                match=match,
                documental=documental,
                kit=kit,
                ano_referencia=ano_base,
                intervalo_de_geracao=intervalo,
                comparacao_existente=comparacao,
            ))
            if incluir_documental:
                # O MESMO dicionario ja montado acima: nenhuma copia, nenhuma segunda
                # passada. Sem isso, a cirurgia do grafo nao teria `path.ids`.
                resultado = {**resultado, "documental": documental}
            resultados.append(resultado)

    resposta = {
        "doador": {
            "id": raiz_id,
            "nome": get_name(arvore[0][raiz_id]),
            "nascimento": raiz_nascimento,
        },
        "comparacoes": resultados,
        "resumo": agregar_resultados(resultados),
        "ano_referencia": ano_base,
        "intervalo_de_geracao": intervalo,
    }
    if incluir_documental:
        resposta["arvore"] = arvore
    return resposta


__all__ = [
    "DependenciasDeValidacao",
    "intervalo_de_geracao_mediano",
    "validar_arquivos",
]
