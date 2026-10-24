"""Tarefa 04 - Analise de DNA (regra final: GEDCOM, DNA e confronto separados).

Este modulo passou a **orquestrar** tres etapas independentes, que antes estavam misturadas
em uma so: 1. **Parentesco documental** (`core.documentary_relationship`) — o que o GEDCOM
afirma: caminho, ancestrais comuns, distancia geracional, parentesco, homonimos, caminhos
multiplos, colapso de pedigree e a evidencia de cada salto. Nao le cM. 2. **Evidencia
genetica** (`core.genetic_evidence`) — kit, fonte, cM, segmentos, maior segmento, SNPs,
cromossomo e posicoes. Nao le o GEDCOM. 3. **Possibilidades e confronto**
(`core.relationship_hypotheses` + `core.evidence_comparison`) — o cM vira uma LISTA de
possibilidades pelo Shared cM Project 4.0, e o confronto devolve COMPATIVEL / POSSIVEL /
CONFLITANTE / INCONCLUSIVO. 4. **Mitigacao de endogamia** (`core.endogamia`) — roda ao lado
e NAO reescreve as tres acima: descarta segmento abaixo de 10 cM, recalcula o total so com o
que sobreviveu, sinaliza maior bloco abaixo de 15 cM como `evidência fraca` / `parentesco
distante inflado` e aponta `Endogamia estrutural confirmada na árvore` quando ha mais de um
caminho mais curto no grafo; o valor bruto continua em `result["cm"]` (contrato de paridade)
e o mitigado viaja em `result["endogamia"]`.

Regra absoluta (nao regredir): o DNA **nao** altera o parentesco documental, e o cM **nao**
e usado sozinho para afirmar parentesco; nunca `if cm == faixa: parentesco =
relacionamento_do_GEDCOM`, e nunca `if cm == 10.8: relacionamento = "primo de 4º grau"`; e
o rotulo "Relacionamento Provável (DNA)" foi removido — o que existe agora e "Possibilidades
de parentesco pelo DNA", dentro da secao de evidencia genetica.

Compatibilidade: `get_relationships_by_cm` e `SHARED_CM_DATA` continuam existindo em
`core.cm_estimator`, mas a superficie de compatibilidade que os trazia para ca SAIU em
`T022` — o import e a declaracao em `__all__`. Eram faixas escritas a mao, sem fonte
verificavel, marcadas como legado, e nem o fluxo nem a interface as usam (ADR-19): medido,
o modulo nao referenciava nenhum dos dois no corpo. Quem as exercita —
`tests/test_dna_analysis.py` — as importa do modulo canonico, como o harness ja fazia.
"""
from __future__ import annotations

from datetime import datetime
from .cartao_sem_correspondencia import _cartao_sem_correspondencia
from .contexto_da_analise import _ContextoDaAnalise
from .dependencias import Dependencias
from .diagram_domain import resolvedor_de_diagrama
from .documentary_relationship import (
    birth_date,
    homonym_dossier,
    intervalo_de_geracao_mediano,
)
from .endogamia import DNAAnalyzer
from .erros import (
    DnaCsvSemColunas,
    PessoaNaoEncontrada,
)
from .genetic_evidence import build_genetic_evidence
from .janela_de_vida import ano_de_referencia
from .matching import (
    build_ged_indexes,
    match_candidates,
)
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
from .passo_por_kit import (
    _cartao_do_kit,
    _montar_diagrama,
    _observacoes,
)
from .registro import get_name
from .rotulos_do_cartao import (
    _observacao_estrutural,
    _selo_da_endogamia,
)
from .sem_correspondencia import (
    elegivel,
    nomes_com_cartao_aceito,
)
from . import cobertura_do_arquivo
from utils.text_cleaning import (
    demojibake,
    strip_bad_utf,
)

# Reexportacoes de compatibilidade. Os instrumentos congelados de
# `_reversa_sdd/parity/` e as sondas de bug importam estes nomes daqui, e a
# linha de `analise-dna/requirements.md` que aponta `_montar_diagrama` e
# `_observacoes` para este arquivo continua valida por este caminho.


def dna_analysis(csv_path: str, root_name: str, deps, arvore, observacoes_do_arquivo=None,
                 candidatos_fixos=None, cobertura=None):
    """Executa a analise de DNA e devolve `(resultados, descartados, mensagem)`.

    ## `candidatos_fixos` (feature 034)

    Mapa `nome no CSV -> (pid, motivo original)`. Quando o operador promove um descarte, a
    escolha dele **substitui** a decisão do casamento para aquele nome: o cartão nasce do
    nó indicado e passa por todo o resto do fluxo (parentesco, veredito, janela, sugestão).

    Por que um mapa, e não um parâmetro por chamada: a análise é sem estado de sessão, então
    a promoção precisa viajar no formulário. O mapa é o que permite várias promoções na
    mesma página sem gravar nada no disco.
    """
    candidatos_fixos = candidatos_fixos or {}
    # As regras de endogamia sao puras e sem estado: uma instancia por analise e
    # o suficiente. Os limiares ficam no construtor (`core.endogamia`), e nao
    # espalhados por literais neste arquivo.
    analisador_de_dna = DNAAnalyzer()
    root_person_ids = [pid for pid, p in arvore[0].items()
                       if root_name.lower() in get_name(p).lower()]
    if not root_person_ids:
        raise PessoaNaoEncontrada(f"Seu nome '{root_name}' não foi encontrado no GEDCOM.")
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
        raise DnaCsvSemColunas(
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
    # FEATURE 040 — o retrato do ARQUIVO, derivado das evidencias ja' montadas. O coletor
    # opcional existe pelo mesmo motivo de `observacoes_do_arquivo`: o retorno de tres
    # posicoes e' contrato de paridade, e um quarto valor quebraria todos os chamadores.
    if cobertura is not None:
        cobertura.update(cobertura_do_arquivo.medir(evidencias, len(df)))
    ged_index, surname_index, features = build_ged_indexes(arvore)

    raiz_ambigua = homonym_dossier(arvore, root_name)
    avisos_da_raiz = []
    if raiz_ambigua["ambiguous"]:
        avisos_da_raiz.append(
            f"O nome informado como raiz ('{root_name}') corresponde a {raiz_ambigua['exact_count']} "
            f"registros no GEDCOM ({', '.join(f['id'] for f in raiz_ambigua['exact_matches'])}). "
            "A análise usou o primeiro; confira se é a pessoa certa."
        )

    # A SEPARACAO POR NIVEL, feita na origem e nao na tela. O aviso de arquivo vale
    # para o CSV inteiro, entao o cartao nao e o lugar dele: ele era copiado para
    # dentro de cada um por `evidence_for` e virava a maior parte da secao 5 de todos
    # os cartoes, inclusive falando de nomes que a triagem descartou. Ver o adendo 017.
    avisos_de_arquivo = [aviso["message"] for aviso in avisos_da_evidencia
                         if aviso.get("nivel") == "arquivo"]
    avisos_de_cartao = [aviso for aviso in avisos_da_evidencia
                        if aviso.get("nivel") != "arquivo"]
    observacoes_do_arquivo_da_analise = avisos_da_raiz + avisos_de_arquivo + avisos_do_arquivo

    results_list = []
    skipped_matches = []
    sem_candidatos = []
    # A costura da OPP-20261006-ULVW: resolvido UMA vez por analise, e nao dentro
    # do laco, porque o mapeamento so aponta para funcoes do proprio pacote.
    dominio = resolvedor_de_diagrama(arvore)

    # O ano de referencia da janela de vida e resolvido UMA vez por analise: ele
    # depende do nascimento da raiz, que nao muda entre os matches. Ver
    # `core.janela_de_vida` para a ancora e os dois limiares.
    ano_atual = datetime.now().year
    ano_base = ano_de_referencia(ano_atual, birth_date(arvore[0], root_id))

    # O intervalo de geracao (G) tambem e resolvido UMA vez por analise, pela mesma
    # razao do ano de referencia — e por uma a mais: ele sai de uma varredura das
    # familias, e refazer isso por cartao custaria 142 varreduras por analise. Mais
    # importante: e o MESMO valor que `application.validacao` usa, entao o cartao e a
    # fachada nunca dao vereditos diferentes para o mesmo kit.
    intervalo_de_geracao = intervalo_de_geracao_mediano(arvore)

    # O contexto carrega o que nao muda entre kits e os dois caches que
    # sobrevivem de um cartao para o outro: o parentesco documental por pessoa e
    # o dossie de homonimos. Montado UMA vez, e depois do ano de referencia e do
    # intervalo de geracao, que sao entradas dele.
    contexto = _ContextoDaAnalise(
        arvore=arvore,
        root_id=root_id,
        deps=deps,
        ged_index=ged_index,
        surname_index=surname_index,
        features=features,
        dominio=dominio,
        ano_base=ano_base,
        intervalo_de_geracao=intervalo_de_geracao,
        analisador=analisador_de_dna,
        candidatos_fixos=candidatos_fixos,
        documental_por_pessoa={},
        dossie_por_nome={},
    )

    for chave_nome, por_kit in evidencias.items():
        for chave_kit, kit in por_kit.items():
            avisos_deste_cartao = [aviso for aviso in avisos_de_cartao
                                   if aviso.get("chave_nome") == chave_nome
                                   and aviso.get("chave_kit") == chave_kit]

            cartao, descarte, evidencia_mitigada = _cartao_do_kit(
                contexto, por_kit, chave_kit, kit, avisos_deste_cartao)
            if cartao is not None:
                results_list.append(cartao)
                continue

            skipped_matches.append(descarte)
            # FEATURE 039/E002: o mesmo item pode virar cartao na lista de resultados,
            # com o tratamento de "Parentesco documental nao encontrado". A lista
            # completa de descartes continua intacta; o cartao e' uma leitura dela.
            sem_candidatos.append({
                "kit": kit,
                "chave_nome": chave_nome,
                "chave_kit": chave_kit,
                "por_kit": por_kit,
                "evidencia_mitigada": evidencia_mitigada,
                "descarte": descarte,
                "avisos": avisos_deste_cartao,
            })

    # FEATURE 039: o cartao sem correspondencia nasce da MESMA regra da triagem
    # (`core.sem_correspondencia.elegivel`). O conjunto de nomes com cartao aceito e'
    # calculado uma vez; o cartao sem correspondencia nao exclui o proprio item. A lista
    # completa de descartes nao e' filtrada; o cartao e' uma leitura dela.
    nomes_com_cartao = nomes_com_cartao_aceito(results_list)
    for candidato in sem_candidatos:
        descarte = candidato["descarte"]
        if not elegivel(descarte, nomes_com_cartao):
            continue
        results_list.append(_cartao_sem_correspondencia(
            arvore=arvore, root_id=root_id, ano_base=ano_base,
            kit=candidato["kit"], chave_nome=candidato["chave_nome"],
            chave_kit=candidato["chave_kit"], por_kit=candidato["por_kit"],
            evidencia_mitigada=candidato["evidencia_mitigada"],
            descarte=descarte, avisos=candidato["avisos"],
            analisador=analisador_de_dna))

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
    if observacoes_do_arquivo is not None:
        observacoes_do_arquivo.extend(observacoes_do_arquivo_da_analise)
    if avisos_do_arquivo and not results_sorted:
        # A mensagem de contrato continua falando SO dos avisos do proprio CSV
        # (preambulo e linhas ignoradas): e o que o oraculo congelado
        # (`tests/test_characterization_matching.py`) prende, e amplia-la aqui
        # mudaria um contrato de tela por tabela. Os demais avisos de arquivo
        # aparecem no bloco proprio da tela, que renderiza mesmo sem cartao nenhum.
        message += " " + " ".join(avisos_do_arquivo)
    return results_sorted, skipped_matches, message

# Nomes publicos do modulo.
#
# A superficie de compatibilidade que reexportava `aggregate_matches`,
# `detect_columns` e `read_csv_with_fallback` SAIU em `T016`: os tres passaram a
# ser injetados pela borda, e reexporta-los aqui obrigaria o modulo a importar
# `parsers/csv_ingest` — que e exatamente a dependencia que a RF-09 remove.
__all__ = [
    "dna_analysis", "Dependencias",
    "build_ged_indexes", "match_candidates",
    "norm_name", "split_name_pt", "surnames_set", "top_given_tokens",
    "token_prefixes", "drop_short_tokens", "surname_core_tokens",
    "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
]
