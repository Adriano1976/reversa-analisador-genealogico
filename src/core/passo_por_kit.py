"""Um kit do CSV vira cartao, ou vira descarte quando nao ha candidato.

E o pipeline de um unico kit, do casamento de nome a montagem do dicionario de 40
chaves. Cada etapa tem nome proprio e recebe o contexto da analise, que carrega o
estado compartilhado entre kits.
"""
from __future__ import annotations

from .cirurgia_do_grafo import resumo_da_sugestao
from .contexto_da_analise import (
    _ContextoDaAnalise,
    _dossie,
)
from .documentary_relationship import (
    birth_date,
    documental_nao_encontrado,
    documentary_relationship,
)
from .endogamia import EvidenciaMitigada
from .endogamia_no_cartao import _endogamia_estrutural
from .evidence_comparison import compare
from .genetic_evidence import evidence_for
from .identidade_do_match import (
    conferir,
    nomes_divergentes,
)
from .janela_de_vida import (
    IMPOSSIVEL,
    aviso_da_janela,
    conferir_janela_de_vida,
)
from .matching import avaliar_candidatos
from .motivos_do_descarte import (
    Motivo,
    NAO_ENCONTRADO,
)
from .profundidade_do_caminho import (
    ATENCAO,
    DIVERGENCIA,
    aviso_da_profundidade,
    conferir_profundidade,
    no_na_profundidade_sugerida,
    resumo_da_profundidade,
)
from .registro import get_name
from .relationship_hypotheses import hypotheses_for_evidence
from .validacao_no_cartao import _validacao_do_cartao


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

    Os avisos de arquivo (`nivel == "arquivo"` em `build_genetic_evidence`, mais os da raiz
    e os do proprio CSV) **nao** entram aqui: eles valem para a analise inteira e vao para o
    bloco unico de observacoes do arquivo. Enquanto eram despejados no cartao, o aviso de
    multiplos kits ocupava 710 das 1010 linhas desta secao e aparecia em 142 de 142 cartoes.
    Ver `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md`.

    `codigos_suprimidos` existe para o aviso `segmento_fraco` quando o bloco de endogamia da
    secao 2 ja diz o mesmo com mais detalhe (total bruto x mitigado, maior bloco, caminhos). A
    informacao NAO some do cartao: muda de secao — sem isso, o operador lia a mesma conclusao
    duas vezes na mesma conexao.
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
