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
4. **Mitigacao de endogamia** (`core.endogamia`) — roda ao lado e NAO reescreve
   as tres acima: descarta segmento abaixo de 10 cM, recalcula o total so com o
   que sobreviveu, sinaliza maior bloco abaixo de 15 cM como `evidência fraca` /
   `parentesco distante inflado` e aponta `Endogamia estrutural confirmada na
   árvore` quando ha mais de um caminho mais curto no grafo. O valor bruto
   continua em `result["cm"]` (contrato de paridade); o mitigado viaja em
   `result["endogamia"]`.

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

from dataclasses import dataclass
from datetime import datetime

from .diagram_domain import resolvedor_de_diagrama
from .endogamia import (
    CM_MINIMO_SEGMENTO,
    DNAAnalyzer,
    EvidenciaMitigada,
    MENSAGEM_ENDEROGAMIA,
)
from . import cobertura_do_arquivo
from .documentary_relationship import (
    birth_date,
    documental_nao_encontrado,
    documentary_relationship,
    homonym_dossier,
    intervalo_de_geracao_mediano,
    person_summary,
)
from .erros import DnaCsvSemColunas, PessoaNaoEncontrada
from .evidence_comparison import compare
from .genetic_evidence import build_genetic_evidence, evidence_for
from .identidade_do_match import conferir, nomes_divergentes
from .path_finding import MAX_DEPTH
from .janela_de_vida import (
    IMPOSSIVEL,
    ano_de_referencia,
    aviso_da_janela,
    conferir_janela_de_vida,
)
from .profundidade_do_caminho import (
    ATENCAO,
    DIVERGENCIA,
    aviso_da_profundidade,
    conferir_profundidade,
    no_na_profundidade_sugerida,
    resumo_da_profundidade,
)
from .matching import avaliar_candidatos, build_ged_indexes, match_candidates
from .motivos_do_descarte import NAO_ENCONTRADO, Motivo
from .sem_correspondencia import elegivel, nomes_com_cartao_aceito
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
from .registro import get_name, ref_id
from .cirurgia_do_grafo import resumo_da_sugestao
from .validator import (
    ERRO_CRONICO,
    VALIDADO,
    ComparacaoParaValidar,
    validar_comparacao,
)


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
                 "generate_mermaid_indirect", "anotar_profundidade",
                 "gerar_mermaid_da_sugestao")

    def __init__(self, read_csv, detect_columns, aggregate_matches, generate_mermaid,
                 generate_mermaid_indirect=None, anotar_profundidade=None,
                 gerar_mermaid_da_sugestao=None):
        self.read_csv = read_csv
        self.detect_columns = detect_columns
        self.aggregate_matches = aggregate_matches
        self.generate_mermaid = generate_mermaid
        self.generate_mermaid_indirect = generate_mermaid_indirect
        # Opcional de proposito: e a unica dependencia que so acrescenta DESENHO ao
        # diagrama ja pronto, e sem ela o fluxo continua inteiro. Ver
        # `reporting.mermaid_render.anotar_profundidade`.
        self.anotar_profundidade = anotar_profundidade
        # Opcional pelo mesmo motivo (feature 032): sem ela o cartao mostra o resumo da
        # arvore sugerida e nao o desenho. `core/` nao pode importar `reporting/`
        # (ADR-34), entao o emissor entra pela borda.
        self.gerar_mermaid_da_sugestao = gerar_mermaid_da_sugestao


@dataclass(frozen=True, slots=True)
class _ContextoDaAnalise:
    """O que a analise de DNA consome igual em todo kit, mais os dois caches.

    A classe existe por uma razao medida: o laco por kit capturava dezoito nomes
    do escopo de `dna_analysis`. Extrair o passo por kit sem ela produziria uma
    assinatura de dezoito parametros, que e o mesmo acoplamento com outra roupa.

    Congelada de proposito: os campos nao sao reatribuidos. Os dois dicionarios
    de cache (`documental_por_pessoa` e `dossie_por_nome`) sao preenchidos na
    primeira consulta e reaproveitados pelos kits seguintes, e e isso que evita
    repetir a varredura de cerca de 35 mil nomes a cada cartao.

    Nao e agregado de dominio: nao guarda invariante, nao decide nada e nao
    reifica o casamento nem a busca. E o mesmo formato que `core.endogamia` ja
    usa nos seus value objects.
    """

    arvore: tuple
    root_id: str
    deps: Dependencias
    ged_index: dict
    surname_index: dict
    features: dict
    dominio: dict
    ano_base: int
    intervalo_de_geracao: int
    analisador: DNAAnalyzer
    candidatos_fixos: dict
    documental_por_pessoa: dict
    dossie_por_nome: dict


def _montar_diagrama(deps, documentary: dict, root_id: str, pid: str, dominio: dict,
                     anotacao: dict | None = None):
    """Mermaid do caminho DOCUMENTAL (ou None quando nao ha caminho).

    Com `anotacao`, o desenho ganha as marcas de profundidade DEPOIS de pronto, e nao
    dentro do renderizador: assim a assinatura de `generate_mermaid_graph` — que o
    `_reversa_sdd/busca-caminho/contracts.md` prende e o legado compartilha — nao muda.
    """
    caminho = (documentary or {}).get("path") or {}
    if not caminho.get("ids"):
        return None
    ancestral = (documentary.get("common_ancestor") or {}).get("id")
    texto = deps.generate_mermaid(caminho["ids"], root_id, pid, ancestral, dominio)
    anotar = getattr(deps, "anotar_profundidade", None)
    if anotacao and anotar:
        texto = anotar(texto, anotacao)
    return texto


def _observacoes(documentary, evidence, comparison, codigos_suprimidos=None):
    """Secao 5 do cartao: o que o operador precisa saber SOBRE ESTA CONEXAO.

    Os avisos de arquivo (`nivel == "arquivo"` em `build_genetic_evidence`, mais os
    da raiz e os do proprio CSV) **nao** entram aqui: eles valem para a analise
    inteira e vao para o bloco unico de observacoes do arquivo. Enquanto eram
    despejados no cartao, o aviso de multiplos kits ocupava 710 das 1010 linhas
    desta secao na analise real de 142 cartoes e aparecia em 142 de 142 cartoes.
    Ver `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md`.

    `codigos_suprimidos` existe para o aviso `segmento_fraco` quando o bloco de
    endogamia da secao 2 ja diz o mesmo com mais detalhe (total bruto x mitigado,
    maior bloco, caminhos). A informacao NAO some do cartao: muda de secao. Sem
    isso, o operador lia a mesma conclusao duas vezes na mesma conexao.
    """
    suprimidos = codigos_suprimidos or frozenset()
    textos = []
    for aviso in (documentary or {}).get("warnings") or []:
        textos.append(aviso["message"])
    for aviso in (evidence or {}).get("warnings") or []:
        if aviso.get("code") in suprimidos:
            continue
        textos.append(aviso["message"])
    textos.extend((comparison or {}).get("observations") or [])
    vistos, unicos = set(), []
    for texto in textos:
        if texto and texto not in vistos:
            vistos.add(texto)
            unicos.append(texto)
    return unicos


# ---------------------------------------------------------------------------
# Veredito de validacao no cartao (feature 031)
# ---------------------------------------------------------------------------

#: Status -> (rotulo visivel, classe CSS). O mapa mora aqui, e nao no template,
#: porque decidir texto e cor e regra: o Jinja so testa se ha rotulo.
#:
#: `INCONCLUSIVO` NAO entra no mapa de proposito. Numa analise real sao 142 cartoes e
#: o inconclusivo e o caso mais comum; marcar quase todos nao marcaria nenhum. A
#: ausencia de selo significa "nao concluido", e a lista declara isso.
ROTULOS_DE_VALIDACAO = {
    VALIDADO: ("Validado", "validacao-valido"),
    ERRO_CRONICO: ("Linha em conflito", "validacao-conflito"),
}


def _aviso_da_validacao(resultado) -> str | None:
    """Status + motivo + primeiro codigo critico, para o `title` do selo.

    O literal de maquina vai AQUI, e nao no texto visivel: `ERRO CRONICO / QUEBRA DE
    LINHA` tem 31 caracteres sem acento, nao cabe num selo e e ruim de ler. Quem audita
    le no `title`, que e onde o literal continua disponivel.
    """
    status = (resultado or {}).get("status") or ""
    motivo = (resultado or {}).get("motivo") or ""
    criticos = [item for item in (resultado or {}).get("codigos") or []
                if item.get("severidade") == "critico"]
    if criticos:
        codigo = criticos[0].get("codigo")
        detalhe = f"{motivo} ({codigo})" if motivo else codigo
    else:
        detalhe = motivo
    if not detalhe:
        return status or None
    return f"{status}: {detalhe}" if status else detalhe


def _nome_do_no(arvore, no) -> str:
    """Nome de exibicao de um no do grafo: pessoa, casal de familia ou o id.

    O diagnostico de reconvergencia pode cair num no de familia (o casal), e nao
    numa pessoa. Trocar o id por "HUSB × WIFE" e o que evita a tela mostrar
    `@F123@` para o operador.
    """
    if not no:
        return ""
    pessoas = arvore[0] if arvore else {}
    if no in pessoas:
        return get_name(pessoas[no])
    familias = arvore[1] if arvore and len(arvore) > 1 else {}
    familia = familias.get(no)
    if familia is not None:
        nomes = []
        for rec in familia.sub_records:
            if rec.tag in ("HUSB", "WIFE"):
                pid = ref_id(rec.value)
                if pid in pessoas:
                    nomes.append(get_name(pessoas[pid]))
        return " × ".join(nomes) if nomes else "Família"
    return no


def _explicacao_da_endogamia(diagnostico, tem_caminho_documental: bool) -> str:
    """Frase que separa o achado ESTRUTURAL do parentesco documental.

    O caso que motivou o texto: um cartao dizia "Parentesco documental nao
    encontrado" na secao 1 e "Endogamia estrutural" no cabecalho. Os dois eram
    verdadeiros sobre eixos diferentes — a busca documental tem teto de
    `MAX_DEPTH` iteracoes, a de grafo nao —, mas lidos juntos pareciam
    contradicao. A frase diz qual e qual.
    """
    if diagnostico is None or not diagnostico.endogamia_estrutural:
        return ""
    if tem_caminho_documental:
        return ("Os caminhos mais curtos se bifurcam e voltam ao mesmo ancestral. "
                "Isso é colapso de pedigree (endogamia): o cM esperado sobe e a "
                "leitura do grau de parentesco fica menos confiável.")
    return (f"Sinal estrutural no grafo: há mais de um caminho mais curto, mas o "
            f"parentesco documental não foi encontrado dentro do limite de {MAX_DEPTH} "
            "iterações da busca documental. Isto não confirma um parentesco específico.")


def _observacao_estrutural(diagnostico, tem_caminho_documental: bool) -> str:
    """A frase da secao 5, qualificada pelo que a secao 1 conseguiu afirmar.

    Com caminho documental, a frase e a de contrato: `Endogamia estrutural
    confirmada na árvore`. Sem ele, a mesma estrutura existe, mas chamar de
    "confirmada" ao lado de "Parentesco documental nao encontrado" foi o que
    confundiu o operador no caso da Edneide — a frase passa a dizer o que foi e
    o que NAO foi encontrado.
    """
    if diagnostico is None or not diagnostico.endogamia_estrutural:
        return ""
    if tem_caminho_documental:
        return MENSAGEM_ENDEROGAMIA
    return (f"Sinal estrutural na árvore: {diagnostico.quantidade_de_caminhos} "
            f"caminhos mais curtos, mas o parentesco documental não foi encontrado "
            f"dentro do limite de {MAX_DEPTH} iterações. Isto não confirma um "
            "parentesco específico.")


def _selo_da_endogamia(evidencia, diagnostico, tem_caminho_documental: bool) -> dict | None:
    """Rotulo, classe e `title` do selo de endogamia do cabecalho.

    O selo e a UNICA parte da mitigacao visivel com o cartao fechado: o detalhe
    numerico fica na secao 2, e a frase estrutural completa fica na secao 5.
    Devolver `None` quando nao ha fato e o que impede a tela de marcar os 142
    cartoes com um selo que nao diz nada.

    A prioridade e o colapso de pedigree, que e o achado mais forte. Sem ele, o
    filtro aparece pelo numero de segmentos descartados; sem descarte, o bloco
    pequeno vira "Evidência fraca". A classe NAO pode conter `estado-`: a regra
    `.badge[class*="estado-"]` pinta o texto de branco, e os dois selos sao de
    aviso (fundo creme).

    ## "Endogamia" x "Sinal estrutural"

    Sem caminho documental, o selo diz **Sinal estrutural na árvore**: o grafo
    tem mais de uma rota, mas a secao 1 nao encontrou parentesco dentro do teto.
    Chamar isso de "Endogamia estrutural" sem a ressalva foi o que confundiu o
    operador no caso real da Edneide.
    """
    if diagnostico is not None and diagnostico.endogamia_estrutural:
        caminhos = diagnostico.quantidade_de_caminhos
        rotulo = ("Endogamia estrutural" if tem_caminho_documental
                  else "Sinal estrutural na árvore")
        if tem_caminho_documental:
            titulo = (f"{MENSAGEM_ENDEROGAMIA}: {caminhos} caminho(s) mais curto(s) "
                      "entre a raiz e o match.")
        else:
            # O `title` acompanha o rotulo: nao adianta o selo dizer "sinal" e o
            # tooltip dizer "confirmada" quando a secao 1 nao encontrou caminho.
            titulo = (f"Sinal estrutural na árvore: {caminhos} caminho(s) mais curto(s). "
                      f"O parentesco documental não foi encontrado dentro do limite de "
                      f"{MAX_DEPTH} iterações.")
        if evidencia.mensagem:
            titulo = f"{titulo} {evidencia.mensagem}"
        return {
            "rotulo": rotulo,
            "classe": "endogamia-estrutural",
            "titulo": titulo,
        }
    if evidencia.segmentos_descartados:
        return {
            "rotulo": (f"Filtro: {evidencia.segmentos_descartados} seg. abaixo de "
                       f"{CM_MINIMO_SEGMENTO:g} cM"),
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    if evidencia.evidencia_fraca:
        return {
            "rotulo": "Evidência fraca",
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    if evidencia.segmentos_sem_valor:
        return {
            "rotulo": "Segmentos sem cM",
            "classe": "endogamia-filtro",
            "titulo": evidencia.mensagem,
        }
    return None


def _validacao_do_cartao(arvore, root_id, documental, comparacao, kit, geracoes_do_kit,
                         ano_base, intervalo):
    """As quatro chaves que o cartao le, a partir do veredito da feature 028.

    ## Por que o veredito viaja no dicionario

    O template itera os dicionarios de resultado (`app.py` passa `resultado.resultados`
    para `dna_results`), e le `result.cm`, `result.comparison`, `result.documentary`.
    Um campo que nao esteja no dicionario nao aparece na tela. O precedente e o
    `confrontacao_rotulo`, que ja e rotulo humano produzido aqui.

    ## Por que `documental` e o ORIGINAL, e nao o apresentado

    Quando a janela de vida e impossivel, a tela troca o parentesco pelo "nao
    encontrado" (`documentary_do_registro` guarda o original). O veredito temporal e
    sobre a LINHA DOCUMENTAL, entao ele olha o caminho de verdade: julgar o cartao pelo
    texto que a tela mostra daria "inconclusivo" justamente nos casos em que a linha
    existe e esta quebrada.
    """
    pessoa_a = (documental or {}).get("person_a") or {}
    pessoa_b = (documental or {}).get("person_b") or {}
    doador = {
        "id": root_id,
        "nome": pessoa_a.get("name") or get_name(arvore[0].get(root_id)),
        "nascimento": pessoa_a.get("birth") or birth_date(arvore[0], root_id),
    }
    match = {
        "id": pessoa_b.get("id"),
        "nome": pessoa_b.get("name"),
        "nascimento": pessoa_b.get("birth"),
    }
    resultado = validar_comparacao(ComparacaoParaValidar(
        doador=doador,
        match=match,
        documental=documental,
        kit={"kit": kit.get("kit"), "total_cm": kit.get("total_cm"),
             "mrca_generations": geracoes_do_kit},
        ano_referencia=ano_base,
        intervalo_de_geracao=intervalo,
        comparacao_existente=comparacao,
    ))
    status = resultado.get("status") or ""
    rotulo, classe = ROTULOS_DE_VALIDACAO.get(status) or (None, None)
    chaves = {
        "validacao_status": status,
        "validacao_rotulo": rotulo,
        "validacao_classe": classe,
        # O aviso existe para o `title` do selo. Sem selo, ele nao teria onde aparecer, e
        # carregar texto que nenhuma tela le e a definicao de dado morto.
        "validacao_aviso": _aviso_da_validacao(resultado) if rotulo else None,
    }
    return chaves, resultado


def _cartao_sem_correspondencia(*, arvore, root_id, ano_base, kit, chave_nome, chave_kit,
                                por_kit, evidencia_mitigada, descarte, avisos, analisador):
    """Monta o cartao de um match sem nenhuma pessoa compativel na arvore (emenda 039/E002).

    O cartao tem o **mesmo tratamento** dos classificados "Parentesco documental nao
    encontrado": mesmo cabecalho, mesmo rotulo, as cinco secoes e o mesmo comportamento
    de recolhimento. O que ele NAO tem e pessoa do GEDCOM: `documentary.person_b` fica
    ausente, o caminho fica `None` e o diagrama nao existe.

    Nao decide nada: recebe o kit e o descarte ja produzidos, le a evidencia genetica do
    proprio kit e devolve o dicionario que a tela consome. A lista completa de descartes
    continua intacta; este cartao e' uma leitura dela, nao uma promocao.
    """
    pessoa_ausente = {
        "id": None, "name": None, "sex": None, "birth": None, "birth_year": None,
        "birth_place": None, "death": None, "death_year": None,
        "parents": [], "parent_names": [], "spouses": [], "children": [],
        "family_as_child": [],
    }
    aviso_sem = {
        "code": "sem_correspondencia",
        "message": ("Nenhuma pessoa com nome compatível foi encontrada no GEDCOM para este "
                    "match. O cM é um sinal de DNA; não há parentesco documental a afirmar."),
    }
    documentary = {
        "status": "not_found",
        "source": "GEDCOM",
        "label": "Parentesco documental não encontrado",
        "relationship_key": None,
        "meioses": None,
        "degrees": None,
        "person_a": person_summary(arvore, root_id),
        "person_b": pessoa_ausente,
        "common_ancestor": None,
        "path": None,
        "common_ancestors": [],
        "additional_paths": [],
        "evidence": [],
        "homonyms": {},
        "ambiguous_identity": False,
        "warnings": [aviso_sem],
    }

    evidence = evidence_for(por_kit, avisos=avisos, kit_key=chave_kit)
    hypotheses = hypotheses_for_evidence(evidence)
    comparison = compare(documentary, hypotheses, evidence)
    comparison["detail"] = (
        "Há evidência genética, mas nenhuma pessoa com nome compatível foi encontrada no "
        "GEDCOM. Nenhum caminho foi inventado a partir do DNA."
    )
    comparison["causes"] = [
        "o nome do CSV não corresponde a nenhum registro do GEDCOM",
        "o ramo do match pode não estar cadastrado na árvore",
        "nome de casada, grafia ou abreviação fora do GEDCOM",
    ]

    geracoes_do_kit = next(
        (k.get("mrca_generations") for k in ((evidence or {}).get("kits") or [])
         if k.get("mrca_generations")), None)
    arvore_da_endogamia = {
        "endogamia_estrutural": False,
        "explicacao": "Sem pessoa na árvore para diagnosticar endogamia estrutural.",
        "reconvergencias": [],
        "mrca_nomes": [],
        "tronco_comum_nomes": [],
    }
    endogamia = {
        **evidencia_mitigada.para_dicionario(),
        "selo": None,
        "limiares": {
            "segmento": analisador.cm_minimo_segmento,
            "maior_bloco": analisador.cm_minimo_maior_bloco,
        },
        "arvore": arvore_da_endogamia,
    }
    observations = list(_observacoes(documentary, evidence, comparison))

    return {
        "match_name": descarte["csv_name"],
        "csv_name": descarte["csv_name"],
        "identidade": "a_confirmar",
        "identidade_aviso": ("Nenhuma pessoa com nome compatível na árvore; não há registro "
                             "para comparar."),
        "janela_de_vida": "sem_dado",
        "idade_na_arvore": None,
        "data_de_nascimento": None,
        "data_imprecisa": False,
        "ano_de_referencia": ano_base,
        "janela_aviso": None,
        "profundidade": "sem_dado",
        "profundidade_razao": None,
        "geracoes_documentais": None,
        "geracoes_do_kit": geracoes_do_kit,
        "profundidade_no_sugerido": None,
        "profundidade_resumo": "Sem caminho documental para comparar.",
        "profundidade_aviso": None,
        "confrontacao_efetiva": (comparison or {}).get("status"),
        "confrontacao_rotulo": (comparison or {}).get("label"),
        "validacao_status": "INCONCLUSIVO",
        "validacao_rotulo": None,
        "validacao_classe": None,
        "validacao_aviso": None,
        "sugestao_geracoes": 0,
        "sugestao_resumo": None,
        "sugestao_mermaid": None,
        "sugestao_aviso": ("Sem pessoa na árvore, não há caminho documental para sugerir "
                           "correção."),
        "cm": kit["total_cm"],
        "kit": kit["kit"],
        "text_path": "",
        "mermaid_data": None,
        "documentary": documentary,
        "documentary_do_registro": None,
        "genetic_evidence": evidence,
        "hypotheses": hypotheses,
        "comparison": comparison,
        "endogamia": endogamia,
        "observations": observations,
        "promovido": None,
        # A marca que separa este cartao de um cartao ACEITO. `nomes_com_cartao_aceito`
        # a ignora (o item nao exclui a si mesmo) e a aplicacao a usa para contar.
        "sem_correspondencia": True,
        "warnings": (documentary.get("warnings") or []) + (evidence.get("warnings") or []),
    }


def _dossie(contexto: _ContextoDaAnalise, nome: str, candidatos) -> dict:
    """Dossie de homonimos, uma vez por nome (a varredura custa ~35k nomes).

    Era uma closure de `dna_analysis`. Virou funcao de modulo porque o cache
    passou a viver no contexto: uma closure sobre uma variavel local de uma
    funcao de 539 linhas nao tinha como ser exercitada sozinha.
    """
    if nome not in contexto.dossie_por_nome:
        contexto.dossie_por_nome[nome] = homonym_dossier(
            contexto.arvore, nome, similar_ids=candidatos)
    return contexto.dossie_por_nome[nome]


def _recusa_do_kit(contexto, kit, reason, proximos, evidencia_mitigada):
    """O descarte de um kit sem candidato, com os tres melhores recusados.

    Extraida pela OPP-20261023-ETAP. O bloco respondia "por que este kit nao
    entrou", e tem regra propria (o motivo virou objeto na feature 038) que nao
    se mistura com a montagem do cartao.
    """
    # A QUEM a arvore oferecia (feature 034): quem cai aqui passa a ver os
    # tres melhores avaliados, com ano de nascimento. O ano e' o dado que
    # separa "quase acertou" de "homônimo de outro seculo" — sem ele, o
    # operador nao tem como decidir se vale promover.
    candidatos_do_descarte = [
        {**candidato, "nascimento": birth_date(contexto.arvore[0], candidato["id"])}
        for candidato in proximos
    ]
    # O MOTIVO VIROU OBJETO (feature 038): o texto humano vai para a tela e para a
    # planilha; o codigo da causa e o detalhe tecnico viajam ao lado, para quem
    # precisar conferir o calculo. `None` continua sendo "nao encontrado" — e' o
    # que acontece quando a decisao nao produziu recusa nenhuma.
    motivo_do_descarte = reason if isinstance(reason, Motivo) else None
    descarte = {
        "csv_name": kit["person_name_csv"],
        "kit": kit["kit"],
        "cm": kit["total_cm"],
        "motivo": (motivo_do_descarte.texto if motivo_do_descarte
                   else (reason or "não encontrado")),
        "motivo_codigo": (motivo_do_descarte.codigo if motivo_do_descarte
                          else NAO_ENCONTRADO),
        "motivo_detalhe": motivo_do_descarte.detalhe if motivo_do_descarte else "",
        "candidatos": candidatos_do_descarte,
        # FEATURE 039: o MRCA estimado do kit viaja ao lado do descarte. E' o
        # mesmo valor que a profundidade do cartao usa; aqui ele nao decide
        # nada, so' da contexto ao operador. `None` quando o CSV nao traz a
        # coluna.
        "mrca_generations": kit.get("mrca_generations"),
    }
    return descarte


def _parentesco_do_kit(contexto, kit, candidate_pids):
    """Escolhe o candidato com caminho e devolve o dossie de homonimos.

    Extraida pela OPP-20261023-ETAP. Devolve `(pid, documentary, homonimos)`;
    `documentary` ja vem do cache por pessoa que vive no contexto.
    """
    # O legado percorria TODOS os candidatos e ficava com o primeiro que
    # tivesse caminho. Isso e preservado — e e o que salva os casos de
    # registro duplicado em que so um dos homonimos tem pais no GEDCOM.
    # A escolha, porem, deixa de ser silenciosa: o dossie de homonimos
    # marca o resultado como identidade ambigua.
    documentais = []
    for candidato in candidate_pids:
        if candidato not in contexto.documental_por_pessoa:
            contexto.documental_por_pessoa[candidato] = documentary_relationship(
                contexto.arvore, contexto.root_id, candidato,
                homonyms=_dossie(contexto, kit["person_name_csv"], candidate_pids))
        documentais.append((candidato, contexto.documental_por_pessoa[candidato]))
    pid, documentary = next(
        ((c, d) for c, d in documentais if (d.get("path") or {}).get("ids")),
        documentais[0])
    homonimos = documentary.get("homonyms") or {}
    return pid, documentary, homonimos


def _endogamia_estrutural(contexto, pid, documentary, evidencia_mitigada):
    """Diagnostico de endogamia no grafo, selo do cabecalho e frase da secao 5.

    Extraida pela OPP-20261023-ETAP. Devolve
    `(arvore, selo, tem_caminho_documental, observacoes)`. O ultimo item e a
    frase que so existe quando o diagnostico estrutural acusou.
    """
    # A ENDOGAMIA ESTRUTURAL, no grafo do GEDCOM. Recebe o grafo por
    # parametro, converte para nao-direcionado quando preciso (o parser ja
    # entrega `nx.Graph`) e usa `nx.all_shortest_paths` entre a raiz e o
    # match. `NetworkXNoPath` e o caso do match sem ligacao documental: o
    # diagnostico volta vazio e o cartao continua sendo montado.
    diagnostico_de_endogamia = contexto.analisador.diagnosticar_endogamia(
        contexto.arvore[2], contexto.root_id, pid,
        mrca_id=(documentary.get("common_ancestor") or {}).get("id"))
    # O caminho DOCUMENTAL decide como o achado e apresentado: com ele, a
    # secao 1 e a secao 2 falam do mesmo par; sem ele, o selo vira "Sinal
    # estrutural na árvore" e o bloco explica que a busca documental parou
    # no teto de `MAX_DEPTH`, em vez de fingir que confirmou parentesco.
    tem_caminho_documental = bool((documentary.get("path") or {}).get("ids"))
    arvore_da_endogamia = diagnostico_de_endogamia.para_dicionario()
    # Nomes resolvidos: as reconvergencias sao o que a tela mostra; o
    # tronco comum fica no `details` recolhido. `mrca_nomes` permanece
    # como alias do tronco para nao quebrar consumidor do campo antigo.
    arvore_da_endogamia["mrca_nomes"] = [
        _nome_do_no(contexto.arvore, no) for no in diagnostico_de_endogamia.mrca_ids
    ]
    arvore_da_endogamia["tronco_comum_nomes"] = [
        _nome_do_no(contexto.arvore, no)
        for no in diagnostico_de_endogamia.tronco_comum_ids
    ]
    arvore_da_endogamia["reconvergencias"] = [
        {
            "divergencia_id": reconvergencia.divergencia_id,
            "divergencia_nome": _nome_do_no(contexto.arvore, reconvergencia.divergencia_id),
            "convergencia_id": reconvergencia.convergencia_id,
            "convergencia_nome": _nome_do_no(contexto.arvore, reconvergencia.convergencia_id),
            "trechos": [
                {
                    "ids": list(trecho),
                    "nomes": [_nome_do_no(contexto.arvore, no) for no in trecho],
                }
                for trecho in reconvergencia.trechos
            ],
        }
        for reconvergencia in diagnostico_de_endogamia.reconvergencias
    ]
    arvore_da_endogamia["explicacao"] = _explicacao_da_endogamia(
        diagnostico_de_endogamia, tem_caminho_documental)
    # O selo do cabecalho e decidido AQUI (o template so le os tres
    # campos), pela mesma razao dos rotulos de validacao: texto de tela
    # e regra, e o Jinja nao monta frase de dominio.
    selo_da_endogamia = _selo_da_endogamia(
        evidencia_mitigada, diagnostico_de_endogamia, tem_caminho_documental)

    # A SECAO 5 GUARDA SO O DIAGNOSTICO ESTRUTURAL. O detalhe numerico
    # do filtro (total bruto x mitigado, descartados, maior bloco) vive
    # no bloco proprio da secao 2. Repeti-lo aqui era a duplicacao que o
    # operador lia duas vezes no mesmo cartao.
    observacoes_da_endogamia = (
        [_observacao_estrutural(diagnostico_de_endogamia,
                                tem_caminho_documental)]
        if diagnostico_de_endogamia.endogamia_estrutural else []
    )
    return (arvore_da_endogamia, selo_da_endogamia,
            tem_caminho_documental, observacoes_da_endogamia)


def _confronto_do_kit(por_kit, chave_kit, avisos_deste_cartao, documentary):
    """Evidencia genetica, possibilidades e confronto, com os nomes do caminho.

    Extraida pela OPP-20261023-ETAP. Roda depois da regra do operador, de
    proposito: com o documental apresentado como nao encontrado, o confronto
    responde o que responde para esse grupo.
    """
    # O CONFRONTO VEM DEPOIS DA REGRA, de proposito: com o documental apresentado
    # como nao encontrado, ele responde o que responde para esse grupo. Inverter a
    # ordem faria o cartao dizer "nao encontrado" na secao 1 e comparar o cM com um
    # parentesco na secao 4 — a contradicao que esta regra existe para eliminar.
    evidence = evidence_for(por_kit, avisos=avisos_deste_cartao, kit_key=chave_kit)
    hypotheses = hypotheses_for_evidence(evidence)
    comparison = compare(documentary, hypotheses, evidence)

    nomes_do_caminho = (documentary.get("path") or {}).get("names") or []
    return evidence, hypotheses, comparison, nomes_do_caminho


def _profundidade_do_caminho(documentary, evidence):
    """A profundidade do caminho contra a estimativa do proprio kit.

    Extraida pela OPP-20261023-ETAP. Devolve
    `(geracoes_do_kit, estado, razao, geracoes_documentais, anotacao)`.
    `anotacao` e None quando nao ha o que marcar no diagrama.
    """
    # A PROFUNDIDADE DO CAMINHO contra a estimativa do PROPRIO kit. E a terceira
    # verificacao, e a unica que fala quando nenhuma das outras duas tem o que
    # dizer: medido, o cartao `XS4787142` (19,2 cM) casa com uma doadora nascida em
    # 1976 — idade plausivel, entao a janela de vida se cala — e a versao 4.0 nao
    # publica faixa para "Primos de 8º grau (duas gerações de diferença)", entao o confronto se
    # cala. Ainda assim a arvore afirma 10,0 geracoes contra as 4,77 que o proprio
    # relatorio de DNA estima. Ver `core.profundidade_do_caminho`.
    geracoes_do_kit = next(
        (k.get("mrca_generations") for k in ((evidence or {}).get("kits") or [])
         if k.get("mrca_generations")), None)
    profundidade, razao_da_profundidade, geracoes_documentais = conferir_profundidade(
        (documentary.get("path") or {}).get("ids") and documentary.get("meioses"),
        geracoes_do_kit)

    # Anotacao do DIAGRAMA: so quando ha o que marcar. `no_sugerido` e sempre uma
    # pessoa que ja esta no caminho — nenhum no e criado.
    anotacao = None
    if profundidade in (ATENCAO, DIVERGENCIA):
        ids_do_caminho = (documentary.get("path") or {}).get("ids") or []
        ancestral_id = (documentary.get("common_ancestor") or {}).get("id")
        try:
            indice_ancestral = ids_do_caminho.index(ancestral_id)
        except ValueError:
            indice_ancestral = -1
        anotacao = {
            "estado": profundidade,
            "geracoes_documentais": geracoes_documentais,
            "geracoes_do_kit": geracoes_do_kit,
            "razao": razao_da_profundidade,
            "no_sugerido": no_na_profundidade_sugerida(
                ids_do_caminho, indice_ancestral, geracoes_do_kit),
        }

    return (geracoes_do_kit, profundidade, razao_da_profundidade,
            geracoes_documentais, anotacao)


def _rotulo_do_confronto(comparison, janela):
    """O rotulo que o cabecalho mostra, que nao pode contradizer o aviso.

    Extraida pela OPP-20261023-ETAP. Devolve `(efetiva, rotulo)`. Quando a
    janela de vida e impossivel, o selo do cM deixa de dizer "compativel": os
    dois lados estavam certos sobre eixos diferentes, mas o selo era o mais
    visivel dos dois.
    """
    # O SELO DO CABECALHO NAO PODE CONTRADIZER O AVISO LOGO ABAIXO. Medido, um
    # cartao dizia "Compatível" no cabecalho e, no aviso seguinte, "nenhuma pessoa
    # com essa idade pode ter doado DNA" — os dois lados estavam certos sobre eixos
    # diferentes (o cM cabe na faixa; a identidade nao fecha), mas o selo era o mais
    # visivel dos dois. O veredito do confronto continua o mesmo em todos os campos
    # (`comparison`); o que muda e o rotulo que o cabecalho mostra.
    confrontacao_efetiva = (comparison or {}).get("status")
    confrontacao_rotulo = (comparison or {}).get("label")
    if janela == IMPOSSIVEL and confrontacao_efetiva in ("COMPATIVEL", "POSSIVEL"):
        confrontacao_efetiva = "identidade_impossivel"
        # "no cM", e nao "cM compativel": o cabecalho ja mostra o selo
        # "DNA: 25,4 cM" imediatamente antes, e repetir a unidade lia como gagueira.
        confrontacao_rotulo = (str((comparison or {}).get("label", "")).lower()
                               + " no cM, identidade impossível")

    return confrontacao_efetiva, confrontacao_rotulo


def _cartao_do_kit(
    contexto: _ContextoDaAnalise,
    por_kit: dict,
    chave_kit: str,
    kit: dict,
    avisos_deste_cartao: list,
) -> tuple[dict | None, dict | None, EvidenciaMitigada]:
    """Um kit vira cartao, ou vira descarte quando nao ha candidato.

    Devolve `(cartao, descarte, evidencia_mitigada)`: exatamente um dos dois
    primeiros e `None`. O terceiro volta sempre porque o cartao sem
    correspondencia, montado depois do laco, precisa dele.

    As dezoito coisas que o corpo consumia do escopo de `dna_analysis` chegam
    por `contexto`; o que muda de um kit para outro chega por parametro.
    """

    # AS REGRAS DE ENDOGAMIA (filtro de 10 cM, total recalculado e maior
    # bloco) rodam sobre o kit, ANTES do matching. O total BRUTO continua
    # alimentando `avaliar_candidatos` e `result["cm"]`: a paridade contra
    # o oraculo congela esse numero e troca-lo aqui mudaria decisoes de
    # aceitacao. O valor mitigado viaja em `result["endogamia"]`, ao lado
    # do bruto, para a tela explicar os dois.
    evidencia_mitigada = contexto.analisador.avaliar_segmentos(
        kit.get("segments") or [])
    kit["endogamia"] = evidencia_mitigada.para_dicionario()

    # O matching continua recebendo o cM DO KIT (nunca a soma de kits
    # diferentes), preservando as decisões do fluxo anterior.
    candidate_pids, reason, proximos = avaliar_candidatos(
        contexto.arvore, kit["person_name_csv"], kit["total_cm"], contexto.ged_index, contexto.surname_index, contexto.features)

    # A PROMOCAO (feature 034) vem ANTES da recusa: se o operador escolheu um nó,
    # a decisão do casamento é substituída — e o resto do fluxo é o mesmo, para o
    # cartão promovido não nascer com menos informação que os outros.
    promovido = contexto.candidatos_fixos.get(kit["person_name_csv"])
    if promovido:
        candidate_pids = [promovido[0]]
        reason = None
        proximos = []

    if not candidate_pids:
        descarte = _recusa_do_kit(
            contexto, kit, reason, proximos, evidencia_mitigada)
        return None, descarte, evidencia_mitigada

    pid, documentary, homonimos = _parentesco_do_kit(contexto, kit, candidate_pids)

    (arvore_da_endogamia, selo_da_endogamia, tem_caminho_documental,
     observacoes_da_endogamia) = _endogamia_estrutural(
        contexto, pid, documentary, evidencia_mitigada)

    # A pessoa da arvore foi escolhida por NOME, e o nome pode ter casado pelo
    # sobrenome e nao pela pessoa. O estado da identificacao NAO muda a escolha —
    # `matching.py` fica intacto —, mas deixa de ser silencioso: o cartao passa a
    # poder dizer que o nome do CSV e outro. Ver `identidade_do_match`.
    nome_na_arvore = get_name(contexto.arvore[0][pid])
    identidade = conferir(kit["person_name_csv"], nome_na_arvore)

    # A JANELA DE VIDA. O casamento e por nome, e nome casa com gente de outro
    # seculo: medido, 8 dos 62 cartoes da analise real tem escolhido com idade
    # impossivel para quem doou DNA. Ver `core.janela_de_vida`.
    data_na_arvore = birth_date(contexto.arvore[0], pid)
    janela, idade_na_arvore, data_imprecisa = conferir_janela_de_vida(
        data_na_arvore, contexto.ano_base)

    # A REGRA DO OPERADOR, declarada em 2026-10-14 (adendo 016): idade acima de
    # `IDADE_IMPOSSIVEL` NAO e apresentada como parentesco — o cartao passa a ser
    # tratado como o grupo "Parentesco documental nao encontrado", com todas as
    # regras desse grupo, e o diagrama e desconsiderado.
    #
    # MEDIDO, e declarado porque e consequencia e nao acidente: a arvore TEM este
    # caminho. Nos 3 cartoes alcancados hoje (11, 12 e 10 meioses), apresentar como
    # "nao encontrado" diz algo falso sobre a ARVORE, e o efeito pratico e mandar o
    # operador procurar registro faltando quando o trabalho e procurar homonimo.
    # Custo medido: a unica comparacao de cM da analise (`TG8027863`, que sai de
    # COMPATIVEL para INCONCLUSIVO) e 1 dos 5 cartoes que apontam para o mesmo
    # ancestral. A decisao e do operador.
    #
    # O documental ORIGINAL nao e destruido: vai para `documentary_do_registro`, no
    # proprio resultado e fora da tela. E o que permite auditar a regra e reverte-la.
    documentary_do_registro = None
    if janela == IMPOSSIVEL and (documentary.get("path") or {}).get("ids"):
        documentary_do_registro = documentary
        documentary = documental_nao_encontrado(contexto.arvore, contexto.root_id, pid,
                                                homonimos=homonimos)

    evidence, hypotheses, comparison, nomes_do_caminho = _confronto_do_kit(
        por_kit, chave_kit, avisos_deste_cartao, documentary)

    (geracoes_do_kit, profundidade, razao_da_profundidade,
     geracoes_documentais, anotacao) = _profundidade_do_caminho(documentary, evidence)

    confrontacao_efetiva, confrontacao_rotulo = _rotulo_do_confronto(
        comparison, janela)

    # O VEREDITO DE VIABILIDADE TEMPORAL sobe para o cartao (feature 031). Ele
    # olha o documental ORIGINAL: quando a janela de vida e impossivel, a tela
    # troca o parentesco pelo "nao encontrado", mas a linha existe — e e sobre ela
    # que o veredito fala. Julgar o texto apresentado daria "inconclusivo"
    # exatamente nos casos em que ha uma linha para julgar.
    documento_da_validacao = documentary_do_registro or documentary
    comparacao_da_validacao = comparison
    if documentary_do_registro is not None:
        comparacao_da_validacao = compare(documento_da_validacao, hypotheses, evidence)
    validacao, resultado_da_validacao = _validacao_do_cartao(
        contexto.arvore, contexto.root_id, documento_da_validacao, comparacao_da_validacao,
        kit, geracoes_do_kit, contexto.ano_base, contexto.intervalo_de_geracao)

    # A ÁRVORE SUGERIDA NA TELA (feature 032). O resumo é O(1) e não copia o
    # grafo: `arvore_sugerida` faria uma cópia de O(V+E) por cartão, e a análise
    # real tem 142. O desenho só é montado quando há geração a inserir e o
    # emissor foi injetado.
    #
    # A IDENTIDADE E A JANELA ENTRAM COMO PORTÃO (decisão de 2026-10-21). Um
    # cartão cujo nome do CSV não confirma a pessoa do GEDCOM — ou cuja pessoa
    # não poderia ter doado DNA — não recebe árvore sugerida: a correção seria
    # construída sobre a pessoa errada. O estado já era calculado e mostrado;
    # o que faltava era ele ter consequência.
    resumo_da_arvore = resumo_da_sugestao(resultado_da_validacao,
                                          documento_da_validacao,
                                          identidade=identidade, janela=janela)
    desenho_da_arvore = None
    if resumo_da_arvore["geracoes"] > 0 and contexto.deps.gerar_mermaid_da_sugestao:
        desenho_da_arvore = contexto.deps.gerar_mermaid_da_sugestao(
            documento_da_validacao, resumo_da_arvore)


    return {
        "match_name": nome_na_arvore,
        "csv_name": kit["person_name_csv"],
        "identidade": identidade,
        "identidade_aviso": nomes_divergentes(kit["person_name_csv"], nome_na_arvore),
        "janela_de_vida": janela,
        "idade_na_arvore": idade_na_arvore,
        "data_de_nascimento": data_na_arvore,
        "data_imprecisa": data_imprecisa,
        "ano_de_referencia": contexto.ano_base,
        "janela_aviso": aviso_da_janela(janela, idade_na_arvore,
                                        kit["person_name_csv"], nome_na_arvore,
                                        data_na_arvore, contexto.ano_base),
        "profundidade": profundidade,
        "profundidade_razao": razao_da_profundidade,
        "geracoes_documentais": geracoes_documentais,
        "geracoes_do_kit": geracoes_do_kit,
        # O no que o diagrama marca em roxo, ou None. Exposto porque a LEGENDA
        # depende dele: quando o GEDCOM nao alcanca a profundidade sugerida nao ha
        # marca roxa no desenho, e a legenda nao pode descrever uma cor ausente.
        "profundidade_no_sugerido": (anotacao or {}).get("no_sugerido"),
        # A leitura CURTA do diagrama. Nao vai mais dentro do grafo: num `flowchart`
        # toda caixa parece um parente. Ver `core.profundidade_do_caminho`.
        "profundidade_resumo": resumo_da_profundidade(
            profundidade, geracoes_documentais, geracoes_do_kit),
        "profundidade_aviso": aviso_da_profundidade(
            profundidade, kit["person_name_csv"], nome_na_arvore,
            geracoes_documentais, geracoes_do_kit, razao_da_profundidade),
        "confrontacao_efetiva": confrontacao_efetiva,
        "confrontacao_rotulo": confrontacao_rotulo,
        # O veredito de validacao temporal (feature 028), agora visivel no cartao.
        # Quatro chaves: status e dado de dominio; rotulo e classe sao vocabulario
        # de tela, decididos aqui para o template nao ter regra (RF-12).
        "validacao_status": validacao["validacao_status"],
        "validacao_rotulo": validacao["validacao_rotulo"],
        "validacao_classe": validacao["validacao_classe"],
        "validacao_aviso": validacao["validacao_aviso"],
        # A arvore sugerida na tela (feature 032): quatro chaves, sendo a ultima
        # a unica que aparece em cartao SEM sugestao — e so' em cartao em conflito.
        "sugestao_geracoes": resumo_da_arvore["geracoes"],
        "sugestao_resumo": resumo_da_arvore["resumo"],
        "sugestao_mermaid": desenho_da_arvore,
        "sugestao_aviso": resumo_da_arvore["aviso"],
        "cm": kit["total_cm"],
        "kit": kit["kit"],
        "text_path": " → ".join(nomes_do_caminho),
        "mermaid_data": _montar_diagrama(contexto.deps, documentary, contexto.root_id, pid, contexto.dominio,
                                         anotacao),
        "documentary": documentary,
        # O parentesco que a regra da janela de vida TIRA da tela. Guardado para que
        # a decisao possa ser auditada e revertida sem recarregar a arvore: nao e
        # renderizado por template nenhum. Ver `core.documental_nao_encontrado`.
        "documentary_do_registro": documentary_do_registro,
        "genetic_evidence": evidence,
        "hypotheses": hypotheses,
        "comparison": comparison,
        # A MITIGACAO DE ENDOGAMIA (regras de 10 cM/15 cM e caminhos no
        # grafo). `cm` continua sendo o bruto do arquivo; aqui viajam o
        # total recalculado, o maior bloco pos-filtro e o diagnostico
        # estrutural. Ver `core.endogamia`.
        "endogamia": {
            **evidencia_mitigada.para_dicionario(),
            # O que o cabecalho mostra com o cartao fechado: rotulo,
            # classe e `title` ja decididos aqui. `None` quando nao ha
            # fato, e o template nao renderiza nada.
            "selo": selo_da_endogamia,
            # Os limiares efetivos do analisador, para a secao 2 citar
            # o numero real em vez de repetir 10/15 no HTML.
            "limiares": {
                "segmento": contexto.analisador.cm_minimo_segmento,
                "maior_bloco": contexto.analisador.cm_minimo_maior_bloco,
            },
            "arvore": arvore_da_endogamia,
        },
        "observations": list(_observacoes(
            documentary, evidence, comparison,
            # O bloco da secao 2 ja mostra o bloco pequeno com os numeros;
            # repetir o aviso `segmento_fraco` aqui era a segunda leitura
            # da mesma conclusao no mesmo cartao.
            codigos_suprimidos=(
                frozenset({"segmento_fraco"})
                if evidencia_mitigada.evidencia_fraca else frozenset()
            ),
        ))
        + observacoes_da_endogamia
        + (
            # A promocao nao apaga a recusa: o cartao diz que nasceu de uma
            # decisao do operador e repete o motivo que o sistema tinha dado.
            [f"Conexão promovida manualmente a partir da lista de descartes "
             f"(o sistema havia recusado: {promovido[1]})."] if promovido else []),
        # O que a TELA precisa para reenviar as promocoes na proxima analise:
        # sem isso, promover a segunda conexao apagaria a primeira.
        "promovido": ({"csv_name": kit["person_name_csv"], "pid": promovido[0],
                       "motivo": promovido[1]} if promovido else None),
        "warnings": (documentary.get("warnings") or []) + (evidence.get("warnings") or []),
    }, None, evidencia_mitigada


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
