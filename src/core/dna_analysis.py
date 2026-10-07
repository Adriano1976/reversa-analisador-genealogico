"""Tarefa 04 - Analise de DNA (regra final: GEDCOM, DNA e confronto separados).

Este modulo passou a **orquestrar** tres etapas independentes, que antes estavam
misturadas em uma so:

1. **Parentesco documental** (`core.documentary_relationship`) — o que o GEDCOM
   afirma: caminho, ancestrais comuns, distancia geracional, parentesco, homonimos,
   caminhos multiplos, colapso de pedigree e a evidencia de cada salto. Nao le cM.
2. **Evidencia genetica** (`core.genetic_evidence`) — kit, fonte, cM, segmentos,
   maior segmento, SNPs, cromossomo e posicoes. Nao le o GEDCOM.
3. **Possibilidades e confronto** (`core.relationship_hypotheses` +
   `core.evidence_comparison`) — o cM vira uma LISTA de possibilidades pelo Shared
   cM Project 4.0, e o confronto devolve COMPATIVEL / POSSIVEL / CONFLITANTE /
   INCONCLUSIVO.

## Regra absoluta (nao regredir)

- O DNA **nao** altera o parentesco documental, e o cM **nao** e usado sozinho para
  afirmar parentesco.
- Nunca `if cm == faixa: parentesco = relacionamento_do_GEDCOM`, e nunca
  `if cm == 10.8: relacionamento = "primo de 4º grau"`.
- O rotulo "Relacionamento Provável (DNA)" foi removido: o que existe agora e
  "Possibilidades de parentesco pelo DNA", dentro da secao de evidencia genetica.

## Compatibilidade

`get_relationships_by_cm` e `SHARED_CM_DATA` continuam existindo em
`core.cm_estimator`, mas a superficie de compatibilidade que os trazia para ca
SAIU em `T022` — o import e a declaracao em `__all__`. Eram faixas escritas a mao,
sem fonte verificavel, marcadas como legado, e nem o fluxo nem a interface as usam
(ADR-19): medido, o modulo nao referenciava nenhum dos dois no corpo. Quem as
exercita — `tests/test_dna_analysis.py` — as importa do modulo canonico, como o
harness ja fazia.
"""
from __future__ import annotations

from .diagram_domain import resolvedor_de_diagrama
from .documentary_relationship import documentary_relationship, homonym_dossier
from .evidence_comparison import compare
from .genetic_evidence import build_genetic_evidence, evidence_for
from .matching import build_ged_indexes, match_candidates
from .name_normalization import (
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surname_core_tokens,
    surnames_set,
    token_prefixes,
    top_given_tokens,
)
from .relationship_hypotheses import hypotheses_for_evidence
from utils.text_cleaning import demojibake, strip_bad_utf
from .registro import get_name


# ---------------------------------------------------------------------------
# A arvore entra por parametro (feature 005, T020).
#
# `dna_analysis` recebe `arvore`, montada pela borda (`src/app.py`) a partir de
# `parsers.gedcom_parser.carregar_arvore`. O modulo NAO le estado de processo.
# ---------------------------------------------------------------------------


class Dependencias:
    """O que a analise de DNA consome de FORA do nucleo (RF-09, `T016`).

    A leitura do CSV e a emissao do diagrama sao borda, e a borda as entrega. O
    nucleo chama as funcoes, sem importar `parsers/csv_ingest` nem
    `reporting/mermaid_render` — que e o que a guarda de dependencias cobra.

    A classe existe porque sao QUATRO dependencias relacionadas, e quatro
    parametros soltos na assinatura de `dna_analysis` convidariam a trocar a
    ordem por engano. Ela nao guarda estado de dominio: so carrega as funcoes.
    """

    __slots__ = ("read_csv", "detect_columns", "aggregate_matches", "generate_mermaid",
                 "generate_mermaid_indirect")

    def __init__(self, read_csv, detect_columns, aggregate_matches, generate_mermaid,
                 generate_mermaid_indirect=None):
        self.read_csv = read_csv
        self.detect_columns = detect_columns
        self.aggregate_matches = aggregate_matches
        self.generate_mermaid = generate_mermaid
        self.generate_mermaid_indirect = generate_mermaid_indirect



def _montar_diagrama(deps, documentary: dict, root_id: str, pid: str, dominio: dict):
    """Mermaid do caminho DOCUMENTAL (ou None quando nao ha caminho)."""
    caminho = (documentary or {}).get("path") or {}
    if not caminho.get("ids"):
        return None
    ancestral = (documentary.get("common_ancestor") or {}).get("id")
    return deps.generate_mermaid(caminho["ids"], root_id, pid, ancestral, dominio)


def _observacoes(documentary, evidence, comparison, extra=None):
    """Secao 5 da tela: tudo que o operador precisa saber e nenhum veredito."""
    textos = []
    for aviso in (documentary or {}).get("warnings") or []:
        textos.append(aviso["message"])
    for aviso in (evidence or {}).get("warnings") or []:
        textos.append(aviso["message"])
    textos.extend((comparison or {}).get("observations") or [])
    for aviso in extra or []:
        textos.append(aviso)
    vistos, unicos = set(), []
    for texto in textos:
        if texto and texto not in vistos:
            vistos.add(texto)
            unicos.append(texto)
    return unicos


def dna_analysis(csv_path: str, root_name: str, deps, arvore):
    """Executa o fluxo completo da analise de DNA.

    Retorna `(results_sorted, skipped, message)`. Cada resultado traz, lado a lado
    e sem misturar: `documentary` (GEDCOM), `genetic_evidence` (DNA),
    `hypotheses` (possibilidades) e `comparison` (confronto).
    """
    root_person_ids = [pid for pid, p in arvore[0].items()
                       if root_name.lower() in get_name(p).lower()]
    if not root_person_ids:
        raise ValueError(f"Seu nome '{root_name}' não foi encontrado no GEDCOM.")
    root_id = root_person_ids[0]

    df = deps.read_csv(csv_path)
    linhas_ignoradas = df.attrs.get("linhas_ignoradas") or []
    linhas_de_preambulo = df.attrs.get("linhas_antes_do_cabecalho") or 0
    detalhe_linhas = ""
    if linhas_ignoradas:
        numeros = ", ".join(str(numero) for numero in linhas_ignoradas[:10])
        if len(linhas_ignoradas) > 10:
            numeros += "…"
        detalhe_linhas += (f" Há {len(linhas_ignoradas)} linha(s) com número de campos diferente do "
                           f"cabeçalho (linha(s) {numeros}), o que costuma indicar separador diferente "
                           "do esperado, aspas desbalanceadas ou arquivo de outro tipo.")
    if linhas_de_preambulo:
        detalhe_linhas += (f" O cabeçalho foi localizado na linha {linhas_de_preambulo + 1}: "
                           f"{linhas_de_preambulo} linha(s) antes dele foram ignoradas.")

    name_col, cm_col, match_id_col, match_email_col = deps.detect_columns(df)
    if not name_col or not cm_col:
        # Erro acionavel: diz o separador usado, as colunas encontradas e o que
        # havia de estranho no arquivo. Antes o operador via "Colunas de Nome e cM
        # não encontradas" — ou, quando o arquivo era torto, o erro cru do pandas
        # em ingles ("Error tokenizing data. C error: Expected 1 fields in line
        # 4, saw 2") — sem saber o que conferir.
        raise ValueError(
            "Colunas de Nome e cM não encontradas no CSV. "
            f"O arquivo foi lido com o separador {df.attrs.get('separador')!r} e as colunas "
            f"encontradas foram: {list(df.columns)[:8]}." + detalhe_linhas
            + " Confira se o arquivo enviado é a lista de matches de DNA (exportação do "
              "GEDmatch/MyHeritage/FamilyTreeDNA) e não o GEDCOM ou outro CSV."
        )

    avisos_do_arquivo = []
    if linhas_de_preambulo:
        avisos_do_arquivo.append(
            f"O arquivo CSV tem {linhas_de_preambulo} linha(s) antes do cabeçalho "
            f"(título do export): a leitura começou na linha {linhas_de_preambulo + 1}, onde estão "
            "as colunas."
        )
    if linhas_ignoradas:
        avisos_do_arquivo.append(
            "O arquivo CSV tem "
            f"{len(linhas_ignoradas)} linha(s) com número de campos diferente do cabeçalho"
            + (f" (linha(s) {', '.join(str(numero) for numero in linhas_ignoradas[:10])}"
               + ("…" if len(linhas_ignoradas) > 10 else "") + ")")
            + ". Elas foram descartadas para que a análise prosseguisse com o separador "
              f"{df.attrs.get('separador')!r}. Se o número de matches parecer menor do que o "
              "esperado, confira o arquivo de origem."
        )

    evidencias, avisos_da_evidencia = build_genetic_evidence(df)
    ged_index, surname_index, features = build_ged_indexes(arvore)

    raiz_ambigua = homonym_dossier(arvore, root_name)
    avisos_da_raiz = []
    if raiz_ambigua["ambiguous"]:
        avisos_da_raiz.append(
            f"O nome informado como raiz ('{root_name}') corresponde a {raiz_ambigua['exact_count']} "
            f"registros no GEDCOM ({', '.join(f['id'] for f in raiz_ambigua['exact_matches'])}). "
            "A análise usou o primeiro; confira se é a pessoa certa."
        )

    results_list = []
    skipped_matches = []
    documental_por_pessoa = {}
    dossie_por_nome = {}

    def _dossie(nome, candidatos):
        """Dossie de homonimos, uma vez por nome (a varredura custa ~35k nomes)."""
        if nome not in dossie_por_nome:
            dossie_por_nome[nome] = homonym_dossier(arvore, nome, similar_ids=candidatos)
        return dossie_por_nome[nome]

    # A costura da OPP-20261006-ULVW: resolvido UMA vez por analise, e nao dentro
    # do laco, porque o mapeamento so aponta para funcoes do proprio pacote.
    dominio = resolvedor_de_diagrama(arvore)

    for chave_nome, por_kit in evidencias.items():
        for chave_kit, kit in por_kit.items():
            # O matching continua recebendo o cM DO KIT (nunca a soma de kits
            # diferentes), preservando as decisões do fluxo anterior.
            candidate_pids, reason = match_candidates(
                arvore, kit["person_name_csv"], kit["total_cm"], ged_index, surname_index, features)

            if not candidate_pids:
                skipped_matches.append({
                    "csv_name": kit["person_name_csv"],
                    "kit": kit["kit"],
                    "cm": kit["total_cm"],
                    "motivo": reason or "não encontrado",
                })
                continue

            # O legado percorria TODOS os candidatos e ficava com o primeiro que
            # tivesse caminho. Isso e preservado — e e o que salva os casos de
            # registro duplicado em que so um dos homonimos tem pais no GEDCOM.
            # A escolha, porem, deixa de ser silenciosa: o dossie de homonimos
            # marca o resultado como identidade ambigua.
            documentais = []
            for candidato in candidate_pids:
                if candidato not in documental_por_pessoa:
                    documental_por_pessoa[candidato] = documentary_relationship(
                        arvore, root_id, candidato,
                        homonyms=_dossie(kit["person_name_csv"], candidate_pids))
                documentais.append((candidato, documental_por_pessoa[candidato]))
            pid, documentary = next(
                ((c, d) for c, d in documentais if (d.get("path") or {}).get("ids")),
                documentais[0])
            homonimos = documentary.get("homonyms") or {}

            evidence = evidence_for(por_kit, avisos=avisos_da_evidencia, kit_key=chave_kit)
            hypotheses = hypotheses_for_evidence(evidence)
            comparison = compare(documentary, hypotheses, evidence)

            nomes_do_caminho = (documentary.get("path") or {}).get("names") or []
            results_list.append({
                "match_name": get_name(arvore[0][pid]),
                "csv_name": kit["person_name_csv"],
                "cm": kit["total_cm"],
                "kit": kit["kit"],
                "text_path": " → ".join(nomes_do_caminho),
                "mermaid_data": _montar_diagrama(deps, documentary, root_id, pid, dominio),
                "documentary": documentary,
                "genetic_evidence": evidence,
                "hypotheses": hypotheses,
                "comparison": comparison,
                "observations": _observacoes(documentary, evidence, comparison,
                                             avisos_da_raiz + avisos_do_arquivo),
                "warnings": (documentary.get("warnings") or []) + (evidence.get("warnings") or []),
            })

    # Ordem de apresentacao (nao e ordem de confianca): primeiro o que tem
    # caminho documental ou identidade a esclarecer, depois o que so tem DNA.
    # Dentro de cada grupo, cM decrescente — a ordem que o fluxo sempre usou.
    # Medido em 2026-10 no GEDCOM real: 71 conexoes, das quais 64 sem caminho no
    # GEDCOM (antes eram descartadas em silencio por nao terem caminho). Ordenar
    # so por cM enterraria as 7 conexoes documentais no meio das 64.
    def _ordem(resultado):
        tem_caminho = bool((resultado["documentary"].get("path") or {}).get("ids"))
        return (0 if tem_caminho else 1, -(resultado.get("cm") or 0))

    results_sorted = sorted(results_list, key=_ordem)
    message = f"{len(results_sorted)} conexões encontradas. {len(skipped_matches)} descartadas."
    if avisos_do_arquivo and not results_sorted:
        # Sem cartao na tela, o alerta da mensagem e o unico lugar onde o aviso do
        # arquivo pode aparecer — e ele nao pode se perder.
        message += " " + " ".join(avisos_do_arquivo)
    return results_sorted, skipped_matches, message


# ---------------------------------------------------------------------------
# Nomes publicos do modulo.
#
# A superficie de compatibilidade que reexportava `aggregate_matches`,
# `detect_columns` e `read_csv_with_fallback` SAIU em `T016`: os tres passaram a
# ser injetados pela borda, e reexporta-los aqui obrigaria o modulo a importar
# `parsers/csv_ingest` — que e exatamente a dependencia que a RF-09 remove.
# ---------------------------------------------------------------------------
__all__ = [
    "dna_analysis", "Dependencias",
    "build_ged_indexes", "match_candidates",
    "norm_name", "split_name_pt", "surnames_set", "top_given_tokens",
    "token_prefixes", "drop_short_tokens", "surname_core_tokens",
    "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
]
