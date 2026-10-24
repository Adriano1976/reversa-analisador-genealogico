"""Cirurgia do grafo: desacoplar a junção e injetar gerações virtuais.

O que este módulo responde: quando `core.validator` devolve ``ERRO CRONICO / QUEBRA DE
LINHA``, o operador sabe **que** a linha documental quebrou, mas não tem o que fazer com o
diagnóstico. Este módulo transforma o veredito em uma **árvore sugerida**: uma cópia do
grafo em que a ligação provada errada é cortada e as gerações que faltam aparecem como nós
virtuais numerados.

As três garantias, e por que cada uma existe:

1. **O ramo do doador é imutável.** O conjunto protegido são as arestas internas do caminho
   entre o doador e o ancestral histórico, **excluída a aresta da junção** — a única que a
   cirurgia remove. Ids, rótulos e datas do ramo não são reescritos.
2. **A árvore recebida não é mutada.** Toda a cirurgia acontece sobre ``grafo.copy()``: a
   estrutura é nova, os atributos são compartilhados e **nunca** mutados (por isso a cópia
   rasa basta, e é O(V+E) em vez do custo do `deepcopy`).
3. **A identidade é separada, não apagada.** Nenhum nó do GEDCOM sai da cópia; o que muda é
   a quem o registro histórico se liga.

A representação do grafo manda no desenho: o grafo é bipartido pessoa↔família
(``parsers.gedcom_parser``) e **não existe aresta pessoa↔pessoa**. Por isso cada geração
virtual precisa de duas coisas: um nó de pessoa (``type="virtual"``) e um nó de família
(``type="virtual-family"``) fazendo o papel de aresta. Cortar "a linha" é remover a aresta
entre a família de junção e o genitor histórico — não uma aresta pessoa↔pessoa.

A fórmula do hiato é ``hiato = floor(geracoes_estimadas + 0.5) - geracoes_documentais``. O
arredondamento é **meio para cima** e explícito: ``round()`` do Python usa arredondamento
bancário e faria ``2.5`` virar ``2``, perdendo uma geração sem aviso. Só se injeta quando
``hiato >= 1``; quando é zero ou negativo, a inconsistência não é de profundidade faltante,
e "remover geração" está proibido pelas garantias 1 e 3.

O que a sugestão NÃO é: não é correção do GEDCOM (nada é escrito em disco, em banco ou em
tela); não é uma árvore para os leitores existentes — os nós virtuais existem só no grafo,
``get_parents`` e ``documentary_relationship`` consultam os dicionários
``people``/``families``, e devolveriam ``[]`` em silêncio para eles, e quem quiser validar a
sugestão precisa de uma feature que materialize os registros; e não inventa pessoa — o nó
virtual não tem nome, sexo nem data exata: tem rótulo ``Geração <k>``,
``origem="estimado"``, uma faixa de nascimento e uma justificativa.

Fontes: faixa 12–70 anos por salto em ``core.documentary_relationship`` (a mesma que
``hop_evidence`` usa); gerações estimadas em ``core.validator.estimar_mrca`` (Shared cM
Project 4.0), da feature `028`; e prior de 25 anos por geração em Fenner, J. N. Am J Phys
Anthropol. 2005;128(2):415–423, DOI 10.1002/ajpa.20188, consultado em 2026-10-18.
"""
from __future__ import annotations

import math

from .documentary_relationship import (
    IDADE_MAXIMA_GENITOR,
    IDADE_MINIMA_GENITOR,
    birth_date,
    parse_year,
)
from .identidade_do_match import A_CONFIRMAR
from .janela_de_vida import IMPOSSIVEL
from .registro import get_name, ref_id
from .validator import ERRO_CRONICO

#: Tipos de nó. Os dois primeiros são os que o parser produz.
TIPO_PESSOA = "person"
TIPO_FAMILIA = "family"
TIPO_VIRTUAL = "virtual"
TIPO_FAMILIA_VIRTUAL = "virtual-family"

#: Prefixo dos ids sintéticos. O id é derivado do CONTEÚDO, não de `uuid` nem de `id()`.
PREFIXO_VIRTUAL = "VIRTUAL"

#: Lados do caminho documental.
LADO_DOADOR = "doador"
LADO_MATCH = "match"

#: O literal que marca a saída como hipótese, e não como resultado.
NATUREZA = "sugestao"

SUGESTAO_INDISPONIVEL = "SUGESTAO_INDISPONIVEL"
HIATO_NAO_POSITIVO = "HIATO_NAO_POSITIVO"
SEM_MRCA_ESTIMADO = "SEM_MRCA_ESTIMADO"
SEM_CAMINHO_DOCUMENTAL = "SEM_CAMINHO_DOCUMENTAL"
AFINIDADE_NAO_INJETAVEL = "AFINIDADE_NAO_INJETAVEL"
JUNCAO_NAO_LOCALIZADA = "JUNCAO_NAO_LOCALIZADA"
DOIS_LADOS_ACUSADOS = "DOIS_LADOS_ACUSADOS"
SUGESTAO_INSUFICIENTE = "SUGESTAO_INSUFICIENTE"
RAMO_BASE_VIOLADO = "RAMO_BASE_VIOLADO"

#: Portões da sugestão na TELA (decisão de 2026-10-21). O código diz qual foi o
#: primeiro motivo que impediu a árvore; a mensagem lista todos os que se aplicam.
#: Sem eles, todo cartão em que o cM estima mais gerações do que a árvore documenta
#: ganhava uma "árvore sugerida" mesmo sem saber ONDE a linha quebrou.
SUGESTAO_SEM_CONFLITO = "SUGESTAO_SEM_CONFLITO"
IDENTIDADE_A_CONFIRMAR = "IDENTIDADE_A_CONFIRMAR"
JANELA_INCOMPATIVEL = "JANELA_INCOMPATIVEL"
JUNCAO_NAO_EVIDENCIADA = "JUNCAO_NAO_EVIDENCIADA"

#: Ordem de saída dos avisos, a mesma da tabela de códigos do requirements (§4.4).
_ORDEM_DOS_AVISOS = {
    SUGESTAO_INDISPONIVEL: 0,
    HIATO_NAO_POSITIVO: 1,
    SEM_MRCA_ESTIMADO: 2,
    SEM_CAMINHO_DOCUMENTAL: 3,
    AFINIDADE_NAO_INJETAVEL: 4,
    JUNCAO_NAO_LOCALIZADA: 5,
    DOIS_LADOS_ACUSADOS: 6,
    SUGESTAO_INSUFICIENTE: 7,
    SUGESTAO_SEM_CONFLITO: 8,
    IDENTIDADE_A_CONFIRMAR: 9,
    JANELA_INCOMPATIVEL: 10,
    JUNCAO_NAO_EVIDENCIADA: 11,
    RAMO_BASE_VIOLADO: 12,
}


def _aviso(codigo: str, mensagem: str) -> dict:
    return {"codigo": codigo, "mensagem": mensagem}


def _ordenar_avisos(avisos: list) -> list:
    return sorted(avisos, key=lambda item: (_ORDEM_DOS_AVISOS.get(item["codigo"], 99), item["codigo"]))


def _par(a, b) -> tuple:
    """Par ordenado, para que a ordem não dependa da iteração do grafo."""
    return (a, b) if str(a) <= str(b) else (b, a)


def _rotulo_virtual(ordem: int) -> str:
    return f"Geração {ordem}"


def _id_virtual(doador_id, ancestral_id, lado: str, ordem: int) -> str:
    """Id determinístico da geração virtual: derivado do conteúdo, nunca de `uuid`/`id()`."""
    return f"{PREFIXO_VIRTUAL}:{doador_id}:{ancestral_id}:{lado}:{ordem}"


def _id_familia_virtual(doador_id, ancestral_id, lado: str, ordem: int) -> str:
    return f"{PREFIXO_VIRTUAL}-FAM:{doador_id}:{ancestral_id}:{lado}:{ordem}"


# Índice de famílias

def _indice_de_familias(arvore) -> dict:
    """Índice filho→famílias e família→genitores, montado UMA vez por chamada.

    O legado resolve esse par com `hop_evidence`, que varre as famílias do arquivo a
    cada salto — a lacuna `L-20`. Aqui a varredura é O(F) uma vez, e cada salto vira
    uma interseção de listas.
    """
    people, families, _grafo, child_to_family = arvore
    por_filho: dict = {}
    genitores: dict = {}
    for fam_id, familia in families.items():
        pais = set()
        filhos = []
        for registro in familia.sub_records:
            if registro.tag in ("HUSB", "WIFE"):
                pid = ref_id(registro.value)
                if pid:
                    pais.add(pid)
            elif registro.tag == "CHIL":
                cid = ref_id(registro.value)
                if cid:
                    filhos.append(cid)
        if pais:
            genitores[fam_id] = pais
        for filho in filhos:
            lista = por_filho.setdefault(filho, [])
            if fam_id not in lista:
                lista.append(fam_id)
    for filho, fams in (child_to_family or {}).items():
        lista = por_filho.setdefault(filho, [])
        for fam_id in fams:
            if fam_id not in lista:
                lista.append(fam_id)
    return {"por_filho": por_filho, "genitores": genitores}


def _familia_do_salto(indice: dict, pai_id, filho_id):
    """A família em que `filho_id` é `CHIL` e `pai_id` é `HUSB`/`WIFE`, ou `None`."""
    for fam_id in indice["por_filho"].get(filho_id, []):
        if pai_id in indice["genitores"].get(fam_id, set()):
            return fam_id
    return None


# Ramo base

def ramo_base(arvore, doador_id, ancestral_id, caminho, juncao=None, indice_familias=None) -> dict:
    """O conjunto protegido: o caminho do doador até o ancestral, menos a junção.

    Devolve ``ids`` na ordem do caminho (pessoas intercaladas com as famílias),
    ``pessoas``, ``familias`` e ``arestas`` — as arestas **internas** ao ramo, já sem
    a aresta da junção, que é a única que a cirurgia remove.
    """
    pessoas = list(caminho or [])
    if not pessoas or doador_id not in pessoas or ancestral_id not in pessoas:
        return {"ids": [], "pessoas": [], "familias": [], "arestas": [],
                "ancestral_id": ancestral_id, "indice_ancestral": None}

    indice_ancestral = pessoas.index(ancestral_id)
    indice = indice_familias or _indice_de_familias(arvore)
    grafo = arvore[2]

    ids: list = []
    familias: list = []
    for pos in range(indice_ancestral):
        filho, pai = pessoas[pos], pessoas[pos + 1]
        familia_id = _familia_do_salto(indice, pai, filho)
        ids.append(filho)
        if familia_id:
            ids.append(familia_id)
            familias.append(familia_id)
    ids.append(ancestral_id)

    dentro = set(ids)
    protegidas = [_par(u, v) for u, v in grafo.edges() if u in dentro and v in dentro]

    removida = None
    if juncao and juncao.get("aresta_removida"):
        removida = tuple(juncao["aresta_removida"])
    protegidas = sorted({ar for ar in protegidas if ar != removida})

    return {
        "ids": ids,
        "pessoas": pessoas[: indice_ancestral + 1],
        "familias": familias,
        "arestas": protegidas,
        "ancestral_id": ancestral_id,
        "indice_ancestral": indice_ancestral,
    }


def ramo_base_intacto(original, sugerida, ramo) -> list:
    """Violações do ramo base: nó ausente, atributo alterado ou aresta interna removida.

    Lista vazia significa intacto. É a verificação que roda **depois** da cirurgia, e
    não só no teste: se ela acusar, o resultado é descartado.
    """
    violacoes = []
    for no in ramo.get("ids") or []:
        if no not in original or no not in sugerida:
            violacoes.append({"id": no, "motivo": "nó ausente da árvore sugerida"})
            continue
        if dict(original.nodes[no]) != dict(sugerida.nodes[no]):
            violacoes.append({"id": no, "motivo": "atributos do nó mudaram"})
    for aresta in ramo.get("arestas") or []:
        if not sugerida.has_edge(*aresta):
            violacoes.append({"id": "{}--{}".format(*aresta),
                              "motivo": "aresta interna do ramo removida"})
    return violacoes


# Junção

def _lados_acusados(documental, indice_ancestral) -> list:
    """Lados com salto implausível, na ordem do caminho.

    A evidência de `documentary_relationship` vem na ordem do caminho: índices antes
    do ancestral são do lado do doador, depois são do lado do match. Ler a posição é
    mais estável do que interpretar o texto da mensagem do validador.
    """
    lados: list = []
    for posicao, salto in enumerate(documental.get("evidence") or []):
        if salto.get("plausible") is False:
            lado = LADO_DOADOR if posicao < indice_ancestral else LADO_MATCH
            if lado not in lados:
                lados.append(lado)
    return lados


def juncao(arvore, documental, indice_familias=None) -> tuple:
    """Localiza a(s) junção(ões): ``(lista_de_juncoes, avisos)``.

    Uma junção por lado acusado. Cada uma é o par ``família × ancestral`` que a
    cirurgia vai cortar, mais o filho daquele lado — que continua no lugar e passa a
    pendurar na cadeia virtual.

    ## Sem salto implausível não há junção (decisão de 2026-10-21)

    Quando NENHUM salto do caminho é biologicamente impossível, não há evidência de
    onde as gerações faltam — e cortar o lado do doador por padrão era um palpite com
    cara de diagnóstico. Antes, ``_lados_acusados`` vazio caía em ``[LADO_DOADOR]``;
    agora a função devolve ``JUNCAO_NAO_EVIDENCIADA`` e a cirurgia não emite árvore.

    A busca pela família continua acontecendo antes do portão de propósito: um caminho
    que nem tem família ligando o salto é outro defeito (``JUNCAO_NAO_LOCALIZADA``), e
    o código não pode escondê-lo atrás do portão novo.
    """
    documental = documental or {}
    caminho = (documental.get("path") or {}).get("ids") or []
    ancestral_id = (documental.get("common_ancestor") or {}).get("id")

    if not caminho or not ancestral_id or ancestral_id not in caminho:
        return [], [_aviso(SEM_CAMINHO_DOCUMENTAL,
                           "Nenhum caminho documental liga o doador ao match.")]

    indice_ancestral = caminho.index(ancestral_id)
    indice = indice_familias or _indice_de_familias(arvore)
    lados = _lados_acusados(documental, indice_ancestral)
    sem_evidencia = not lados
    lados = lados or [LADO_DOADOR]

    juncoes: list = []
    for lado in lados:
        posicao = indice_ancestral - 1 if lado == LADO_DOADOR else indice_ancestral + 1
        if posicao < 0 or posicao >= len(caminho):
            continue
        filho_id = caminho[posicao]
        familia_id = _familia_do_salto(indice, ancestral_id, filho_id)
        if not familia_id:
            return [], [_aviso(
                JUNCAO_NAO_LOCALIZADA,
                f"O salto entre {ancestral_id} e {filho_id} não tem família que os ligue.")]
        juncoes.append({
            "familia_id": familia_id,
            "pai_id": ancestral_id,
            "filho_id": filho_id,
            "lado": lado,
            "aresta_removida": _par(familia_id, ancestral_id),
        })

    if not juncoes:
        return [], [_aviso(JUNCAO_NAO_LOCALIZADA,
                           "O ancestral é uma das pontas do caminho; não há junção a cortar.")]

    if sem_evidencia:
        return [], [_aviso(
            JUNCAO_NAO_EVIDENCIADA,
            "Nenhum salto do caminho é biologicamente impossível; não há evidência de "
            "onde faltam gerações.")]

    # Dois lados acusados podem compartilhar a MESMA família de junção (dois filhos do
    # mesmo ancestral). Cortar a mesma aresta duas vezes falharia na segunda, então a
    # lista é deduplicada — e a cadeia, nesse caso, é uma só.
    vistos = set()
    unicas: list = []
    for item in juncoes:
        chave = (item["familia_id"], item["pai_id"])
        if chave in vistos:
            continue
        vistos.add(chave)
        unicas.append(item)
    return unicas, []


def desacoplar_identidade(arvore, juncao_dados) -> tuple:
    """Corta a aresta de filiação da junção numa cópia: ``(grafo, avisos)``.

    Recusa qualquer par que não seja filiação de verdade — o filho tem de ser `CHIL`
    da família e o pai tem de ser `HUSB`/`WIFE` dela. É o que impede uma aresta de
    casamento de ser tratada como linha consanguínea.
    """
    people, families, grafo, _c2f = arvore
    familia_id = (juncao_dados or {}).get("familia_id")
    pai_id = (juncao_dados or {}).get("pai_id")
    filho_id = (juncao_dados or {}).get("filho_id")

    if not familia_id or not pai_id or not filho_id:
        return None, [_aviso(JUNCAO_NAO_LOCALIZADA, "Junção incompleta: falta família, pai ou filho.")]

    familia = families.get(familia_id)
    if familia is None:
        return None, [_aviso(JUNCAO_NAO_LOCALIZADA, f"A família {familia_id} não existe na árvore.")]

    filhos = {ref_id(registro.value) for registro in familia.sub_records if registro.tag == "CHIL"}
    genitores = {ref_id(registro.value) for registro in familia.sub_records
                 if registro.tag in ("HUSB", "WIFE")}
    if filho_id not in filhos or pai_id not in genitores:
        return None, [_aviso(
            AFINIDADE_NAO_INJETAVEL,
            f"{pai_id} e {filho_id} não são genitor e filho em {familia_id}; "
            "a cirurgia só corta filiação, nunca casamento.")]

    sugerida = grafo.copy()
    if sugerida.has_edge(familia_id, pai_id):
        sugerida.remove_edge(familia_id, pai_id)
    else:
        return None, [_aviso(JUNCAO_NAO_LOCALIZADA,
                             f"A aresta {familia_id}–{pai_id} não existe no grafo.")]
    return sugerida, []


# Injeção

def _faixa_estimada(ano, meio) -> dict:
    if ano is None:
        return {"ano_min": None, "ano_max": None}
    margem = int(meio or 0)
    return {"ano_min": ano - margem, "ano_max": ano + margem}


def injetar_geracoes(grafo, juncao_dados, k, doador_id=None, nasc_ancestral=None,
                     nasc_filho=None, intervalo=None) -> dict:
    """Cria `k` gerações virtuais em cadeia e devolve o que foi criado.

    Cada geração é um nó de pessoa virtual mais um nó-família sintético, porque o
    grafo não tem aresta pessoa↔pessoa. A última geração liga-se à família de origem,
    que continua no lugar — a cirurgia não reescreve a composição de família nenhuma.

    ## O grafo recebido É alterado, de propósito

    `desacoplar_identidade` devolve uma cópia; esta função opera **sobre** o grafo que
    recebe, e é o único ponto da cirurgia que escreve. O chamador passa a cópia
    (`grafo.copy()`), nunca `arvore[2]`. Manter a escrita num lugar só é o que torna a
    garantia "a árvore recebida não é mutada" verificável por leitura.
    """
    nada = {"grafo": grafo, "geracoes_virtuais": [], "familias_virtuais": [],
            "nos_adicionados": [], "arestas_adicionadas": []}
    if k is None or k <= 0:
        return nada

    familia_origem = juncao_dados["familia_id"]
    pai_id = juncao_dados["pai_id"]
    lado = juncao_dados["lado"]

    passo = None
    if nasc_ancestral is not None and nasc_filho is not None:
        passo = (nasc_filho - nasc_ancestral) / (k + 1)
    meio = (intervalo / 2) if intervalo else 0

    geracoes: list = []
    familias: list = []
    arestas: list = []
    anterior = pai_id

    for ordem in range(1, k + 1):
        pessoa_id = _id_virtual(doador_id, pai_id, lado, ordem)
        familia_id = _id_familia_virtual(doador_id, pai_id, lado, ordem)
        ano = None if passo is None else round(nasc_ancestral + passo * ordem)
        faixa = _faixa_estimada(ano, meio)

        grafo.add_node(pessoa_id, label=_rotulo_virtual(ordem), type=TIPO_VIRTUAL,
                       origem="estimado",
                       justificativa=(f"Posição estimada pelo cM entre {pai_id} e o ramo "
                                      f"documentado; nenhuma pessoa identificada."),
                       nascimento_estimado=faixa)
        grafo.add_node(familia_id, label="Familia virtual", type=TIPO_FAMILIA_VIRTUAL)
        grafo.add_edge(anterior, familia_id)
        grafo.add_edge(familia_id, pessoa_id)
        arestas.extend([(anterior, familia_id), (familia_id, pessoa_id)])

        geracoes.append({"id": pessoa_id, "label": _rotulo_virtual(ordem), "lado": lado,
                         "ordem": ordem, "nascimento_estimado": faixa})
        familias.append(familia_id)
        anterior = pessoa_id

    grafo.add_edge(anterior, familia_origem)
    arestas.append((anterior, familia_origem))

    return {"grafo": grafo, "geracoes_virtuais": geracoes, "familias_virtuais": familias,
            "nos_adicionados": [item["id"] for item in geracoes] + familias,
            "arestas_adicionadas": arestas}


# Resumo para a tela

def _anos_da_juncao(documental, a_up, hiato):
    """Anos do salto documentado da junção e do salto que a cadeia proporia.

    O salto documentado é o que liga o ancestral ao primeiro descendente do lado do
    doador — o mesmo que a cirurgia corta. Devolve ``None`` quando falta data em uma
    das pontas, quando o filho é mais velho que o pai ou quando o caminho não tem
    esse salto. A leitura é do dicionário ``documental``; nenhuma árvore é tocada.
    """
    evidencia = documental.get("evidence") or []
    if a_up <= 0 or a_up > len(evidencia):
        return None
    salto = evidencia[a_up - 1] or {}
    pai = parse_year(salto.get("parent_birth"))
    filho = parse_year(salto.get("child_birth"))
    if pai is None or filho is None or filho <= pai:
        return None
    return filho - pai, (filho - pai) / (hiato + 1)


def _bloqueios_da_sugestao(resultado, documental, a_up, hiato, *, identidade, janela):
    """Motivos para NÃO emitir a árvore, e o código do primeiro deles.

    A ordem é a da gravidade para o operador: veredito, identidade, janela, junção
    sem salto impossível e, por último, a cadeia que criaria uma idade impossível.
    Todos os motivos aplicáveis entram na mensagem; só o primeiro vira ``codigo``.

    ## Por que a cadeia é medida no TRECHO, e não no caminho inteiro

    A guarda antiga da ``arvore_sugerida`` dividia os anos do doador pelo caminho
    todo. No caso medido em 2026-10-21 (Joaquim, depois de 1886; Maria José, 1928),
    isso dava ``(1976 - 1886) / 6 = 15`` anos por geração e a cadeia passava — embora
    as quatro gerações entre o pai e a filha coubessem em 42 anos, ~10,5 cada. Aqui
    a conta é a do trecho: ``(filho - ancestral) / (hiato + 1)``. Só bloqueia quando
    o salto documentado era possível e a cadeia o torna impossível; se o salto já
    era impossível, a sugestão melhora o quadro e a guarda da cirurgia a declara
    insuficiente em vez de escondê-la.
    """
    status = resultado.get("status")
    motivos: list = []
    codigo = None

    def bloquear(novo, motivo):
        nonlocal codigo
        codigo = codigo or novo
        motivos.append(motivo)

    if status != ERRO_CRONICO:
        bloquear(SUGESTAO_SEM_CONFLITO, f"o veredito é {status}")
    if identidade == A_CONFIRMAR:
        bloquear(IDENTIDADE_A_CONFIRMAR, "a identidade do match está a confirmar")
    if janela == IMPOSSIVEL:
        bloquear(JANELA_INCOMPATIVEL, "a pessoa do GEDCOM não poderia ter doado DNA")
    if not any(salto.get("plausible") is False
               for salto in documental.get("evidence") or []):
        bloquear(JUNCAO_NAO_EVIDENCIADA,
                 "nenhum salto documentado é biologicamente impossível")

    anos = _anos_da_juncao(documental, a_up, hiato)
    if anos is not None:
        documentado, proposto = anos
        if (IDADE_MINIMA_GENITOR <= documentado <= IDADE_MAXIMA_GENITOR
                and not (IDADE_MINIMA_GENITOR <= proposto <= IDADE_MAXIMA_GENITOR)):
            bloquear(
                SUGESTAO_INSUFICIENTE,
                f"a cadeia de {hiato} geração(ões) daria {proposto:.1f} anos por geração, "
                f"fora de {IDADE_MINIMA_GENITOR}–{IDADE_MAXIMA_GENITOR}")

    return motivos, codigo


def resumo_da_sugestao(resultado, documental, *, identidade=None, janela=None) -> dict:
    """Hiato e rótulos das gerações, **sem tocar no grafo**.

    Por que existe separada de `arvore_sugerida`: a tela precisa de um único número — quantas
    gerações faltam — e `arvore_sugerida` resolve isso copiando o grafo inteiro
    (`grafo.copy()`, O(V+E)). Numa análise real de 142 cartões sobre uma árvore de 35.460
    pessoas, isso é a requisição inviável. Aqui a conta é a MESMA fórmula da
    `arvore_sugerida` (RN-07 da `029`), em O(1): `hiato = floor(geracoes + 0.5) - a_up` — uma
    casa só para o número, para o cartão e a imagem nunca darem respostas diferentes.

    Devolve `geracoes` (int), `resumo` (texto do bloco, ou `None`), `rotulos` (as `Geração
    k`), `aviso` (a frase de ausência) e `codigo`.

    Os portões (decisão de 2026-10-21): o número do hiato existe sempre que o cM estima mais
    gerações do que a árvore documenta; a **árvore sugerida** não — ela só é emitida quando há
    evidência de onde a linha quebrou (ver `_bloqueios_da_sugestao`). Sem os portões, um cartão
    INCONCLUSIVO exibia "3 gerações sugeridas" e mandava o operador cavar o ramo errado (caso
    medido: Maria Cândida de Jesus, 15,1 cM, contra uma tia-avó de 850 cM esperados). O
    `aviso` continua restrito ao cartão em conflito **quando não há o que sugerir** (§9 da
    `032`): repetir a explicação em 142 cartões trocaria um silêncio ruidoso por um ruído
    constante — e quando HÁ hiato mas um portão o barra, a frase aparece mesmo fora do
    conflito, porque sumir em silêncio faria o operador ler "não implementado", que é o
    problema que a `032` nasceu para resolver.
    """
    resultado = resultado or {}
    documental = documental or {}
    degrees = documental.get("degrees") or {}
    a_up = int(degrees.get("a_up") or 0)
    geracoes = (resultado.get("mrca_estimado") or {}).get("geracoes")
    em_conflito = resultado.get("status") == ERRO_CRONICO

    def _sem_sugestao(codigo, aviso, mostrar=None):
        if mostrar is None:
            mostrar = em_conflito
        return {"geracoes": 0, "resumo": None, "rotulos": [], "lado": LADO_DOADOR,
                "codigo": codigo, "aviso": aviso if mostrar else None}

    if geracoes is None:
        return _sem_sugestao(
            SEM_MRCA_ESTIMADO,
            "O cM deste kit não caiu em nenhuma relação publicada, então não há como "
            "estimar quantas gerações faltam.")

    hiato = math.floor(float(geracoes) + 0.5) - a_up
    if hiato <= 0:
        return _sem_sugestao(
            HIATO_NAO_POSITIVO,
            f"O cM estima {math.floor(float(geracoes) + 0.5)} geração(ões) e a árvore já "
            f"documenta {a_up}: as duas medidas concordam, não há geração a inserir.")

    motivos, codigo = _bloqueios_da_sugestao(resultado, documental, a_up, hiato,
                                             identidade=identidade, janela=janela)
    if motivos:
        return _sem_sugestao(
            codigo,
            "Não é possível localizar a quebra: " + "; ".join(motivos) + ".",
            mostrar=True)

    rotulos = [_rotulo_virtual(ordem) for ordem in range(1, hiato + 1)]
    resumo = (f"{hiato} geração sugerida" if hiato == 1
              else f"{hiato} gerações sugeridas")
    return {"geracoes": hiato, "resumo": resumo, "rotulos": rotulos, "lado": LADO_DOADOR,
            "codigo": "SUGESTAO_DISPONIVEL", "aviso": None}


# Orquestração

def _nula(status_origem, doador, aviso: dict) -> dict:
    """A forma da sugestão quando não há o que sugerir."""
    return {
        "natureza": NATUREZA,
        "status_origem": status_origem,
        "grafo": None,
        "doador": doador,
        "ancestral": None,
        "juncao": None,
        "juncoes": [],
        "hiato": {"calculado": 0, "aplicado": 0,
                  "por_lado": {LADO_DOADOR: 0, LADO_MATCH: 0}},
        "geracoes_virtuais": [],
        "familias_virtuais": [],
        "nos_adicionados": [],
        "arestas_adicionadas": [],
        "arestas_removidas": [],
        "ramo_base": {"ids": [], "pessoas": [], "familias": [], "arestas": [],
                      "ancestral_id": None, "indice_ancestral": None, "intacto": True},
        "justificativa": aviso["mensagem"],
        "avisos": [aviso],
    }


def _deficit(anos, geracoes) -> float:
    """Anos que excedem o máximo tolerado para o número de gerações daquele lado."""
    if anos is None:
        return 0.0
    return max(0.0, float(anos) - IDADE_MAXIMA_GENITOR * max(int(geracoes or 0), 1))


def arvore_sugerida(arvore, documental, resultado, doador_id=None) -> dict:
    """Monta a árvore sugerida a partir do veredito, do parentesco e da árvore.

    Fluxo (requirements §4.6): status → recusas → junção → cópia → desacoplar →
    hiato → injetar → conferir a janela → verificar o ramo → emitir.

    O resultado segue o contrato de §4.7. ``grafo`` é ``None`` sempre que não há o que
    sugerir, e nesse caso ``avisos[0]`` diz por quê.
    """
    documental = documental or {}
    resultado = resultado or {}
    status = resultado.get("status")
    pessoa_a = documental.get("person_a") or {}
    doador = {"id": doador_id or pessoa_a.get("id"), "nome": pessoa_a.get("name")}

    if status != ERRO_CRONICO:
        return _nula(status, doador, _aviso(
            SUGESTAO_INDISPONIVEL,
            f"O status é {status}; só há sugestão para {ERRO_CRONICO}."))

    if documental.get("status") == "affinity":
        return _nula(status, doador, _aviso(
            AFINIDADE_NAO_INJETAVEL,
            "O caminho chega ao outro ramo por casamento, não por filiação; "
            "casamento não é linhagem e não se injeta geração nele."))

    caminho = (documental.get("path") or {}).get("ids") or []
    ancestral = documental.get("common_ancestor") or {}
    ancestral_id = ancestral.get("id")
    if not caminho or not ancestral_id or ancestral_id not in caminho:
        return _nula(status, doador, _aviso(
            SEM_CAMINHO_DOCUMENTAL,
            "Nenhum caminho documental por filiação liga o doador ao match."))

    geracoes = (resultado.get("mrca_estimado") or {}).get("geracoes")
    if geracoes is None:
        return _nula(status, doador, _aviso(
            SEM_MRCA_ESTIMADO,
            "O cM não permitiu estimar gerações até o MRCA; sem estimativa não há hiato."))

    degrees = documental.get("degrees") or {}
    a_up = int(degrees.get("a_up") or 0)
    b_up = int(degrees.get("b_up") or 0)
    hiato = math.floor(float(geracoes) + 0.5) - a_up
    if hiato <= 0:
        return _nula(status, doador, _aviso(
            HIATO_NAO_POSITIVO,
            f"O cM estima {math.floor(float(geracoes) + 0.5)} geração(ões) e o caminho já "
            f"tem {a_up}; a inconsistência não é de geração faltante."))

    indice = _indice_de_familias(arvore)
    juncoes, avisos = juncao(arvore, documental, indice_familias=indice)
    if not juncoes:
        return _nula(status, doador, avisos[0])

    lados = _lados_acusados(documental, caminho.index(ancestral_id))
    if len(lados) > 1 and len(juncoes) == 1:
        avisos.append(_aviso(
            DOIS_LADOS_ACUSADOS,
            "Os dois lados têm salto implausível, mas compartilham a mesma família de "
            "junção; nesse caso a cadeia é única e cobre as duas pontas."))

    nasc_doador = pessoa_a.get("birth_year")
    if nasc_doador is None:
        nasc_doador = parse_year(pessoa_a.get("birth"))
    pessoa_b = documental.get("person_b") or {}
    nasc_match = pessoa_b.get("birth_year")
    if nasc_match is None:
        nasc_match = parse_year(pessoa_b.get("birth"))
    nasc_ancestral = parse_year(ancestral.get("birth"))

    por_lado = {LADO_DOADOR: 0, LADO_MATCH: 0}
    if len(juncoes) == 1:
        por_lado[juncoes[0]["lado"]] = hiato
    else:
        anos_a = None if (nasc_doador is None or nasc_ancestral is None) else nasc_doador - nasc_ancestral
        anos_b = None if (nasc_match is None or nasc_ancestral is None) else nasc_match - nasc_ancestral
        deficit_a = _deficit(anos_a, a_up)
        deficit_b = _deficit(anos_b, b_up)
        total = deficit_a + deficit_b
        no_doador = hiato if total <= 0 else math.floor(hiato * deficit_a / total + 0.5)
        por_lado[LADO_DOADOR] = no_doador
        por_lado[LADO_MATCH] = hiato - no_doador
        avisos.append(_aviso(
            DOIS_LADOS_ACUSADOS,
            "Os dois lados têm salto implausível; as gerações foram divididas "
            "proporcionalmente ao excesso de anos de cada lado."))

    ramo = ramo_base(arvore, doador["id"], ancestral_id, caminho,
                     juncao=juncoes[0], indice_familias=indice)

    grafo = arvore[2].copy()
    geracoes_virtuais: list = []
    familias_virtuais: list = []
    nos_adicionados: list = []
    arestas_adicionadas: list = []
    arestas_removidas: list = []

    for dados_juncao in juncoes:
        k = por_lado.get(dados_juncao["lado"], 0)
        if k <= 0:
            continue
        desacoplado, recusas = desacoplar_identidade((arvore[0], arvore[1], grafo, arvore[3]),
                                                     dados_juncao)
        if desacoplado is None:
            return _nula(status, doador, recusas[0])
        grafo = desacoplado
        arestas_removidas.append(dados_juncao["aresta_removida"])

        injetado = injetar_geracoes(
            grafo, dados_juncao, k,
            doador_id=doador["id"],
            nasc_ancestral=nasc_ancestral,
            nasc_filho=parse_year(birth_date(arvore[0], dados_juncao["filho_id"])),
            intervalo=resultado.get("intervalo_de_geracao"),
        )
        grafo = injetado["grafo"]
        geracoes_virtuais.extend(injetado["geracoes_virtuais"])
        familias_virtuais.extend(injetado["familias_virtuais"])
        nos_adicionados.extend(injetado["nos_adicionados"])
        arestas_adicionadas.extend(injetado["arestas_adicionadas"])

    violacoes = ramo_base_intacto(arvore[2], grafo, ramo)
    if violacoes:
        aviso = _aviso(RAMO_BASE_VIOLADO,
                       f"A cirurgia alterou o ramo base: {violacoes[0]['id']} "
                       f"({violacoes[0]['motivo']}). A sugestão foi descartada.")
        nula = _nula(status, doador, aviso)
        nula["avisos"] = [aviso]
        return nula

    nome_ancestral = get_name(arvore[0][ancestral_id]) if ancestral_id in arvore[0] else ancestral_id

    for dados_juncao in juncoes:
        k = por_lado.get(dados_juncao["lado"], 0)
        if k <= 0:
            continue
        # A IDADE É MEDIDA NO TRECHO, não no caminho inteiro. Dividir os anos do
        # doador pelo total de gerações diluía a cadeia: em 2026-10-21, Joaquim
        # (depois de 1886) e Maria José (1928) com 3 gerações inseridas davam
        # (1976 - 1886) / 6 = 15 anos por geração, dentro de 12–70, embora as
        # quatro gerações entre o pai e a filha coubessem em 42 anos (~10,5 cada).
        ano_filho = parse_year(birth_date(arvore[0], dados_juncao["filho_id"]))
        total_geracoes = k + 1
        if ano_filho is None or nasc_ancestral is None or total_geracoes <= 0:
            continue
        idade = (ano_filho - nasc_ancestral) / total_geracoes
        if not (IDADE_MINIMA_GENITOR <= idade <= IDADE_MAXIMA_GENITOR):
            nome_filho = (get_name(arvore[0][dados_juncao["filho_id"]])
                          if dados_juncao["filho_id"] in arvore[0]
                          else dados_juncao["filho_id"])
            avisos.append(_aviso(
                SUGESTAO_INSUFICIENTE,
                f"Com {total_geracoes} geração(ões) entre {nome_ancestral} e {nome_filho}, "
                f"sobram {idade:.1f} anos por geração, fora de "
                f"{IDADE_MINIMA_GENITOR}–{IDADE_MAXIMA_GENITOR}: a sugestão não resolve a "
                "contradição temporal que o validador acusou."))

    aplicado = sum(por_lado.values())
    justificativa = (
        f"A linha documental declara {a_up} geração(ões) entre o doador e "
        f"{nome_ancestral}, e o cM estima {math.floor(float(geracoes) + 0.5)}: "
        f"{aplicado} geração(ões) foram inseridas como sugestão, no ponto de junção.")

    ramo["intacto"] = True
    return {
        "natureza": NATUREZA,
        "status_origem": status,
        "grafo": grafo,
        "doador": doador,
        "ancestral": {"id": ancestral_id, "nome": nome_ancestral, "ano": nasc_ancestral},
        "juncao": juncoes[0],
        "juncoes": juncoes,
        "hiato": {"calculado": hiato, "aplicado": aplicado, "por_lado": por_lado},
        "geracoes_virtuais": geracoes_virtuais,
        "familias_virtuais": familias_virtuais,
        "nos_adicionados": nos_adicionados,
        "arestas_adicionadas": arestas_adicionadas,
        "arestas_removidas": arestas_removidas,
        "ramo_base": ramo,
        "justificativa": justificativa,
        "avisos": _ordenar_avisos(avisos),
    }


__all__ = [
    "TIPO_PESSOA",
    "TIPO_FAMILIA",
    "TIPO_VIRTUAL",
    "TIPO_FAMILIA_VIRTUAL",
    "PREFIXO_VIRTUAL",
    "LADO_DOADOR",
    "LADO_MATCH",
    "NATUREZA",
    "SUGESTAO_INDISPONIVEL",
    "HIATO_NAO_POSITIVO",
    "SEM_MRCA_ESTIMADO",
    "SEM_CAMINHO_DOCUMENTAL",
    "AFINIDADE_NAO_INJETAVEL",
    "JUNCAO_NAO_LOCALIZADA",
    "DOIS_LADOS_ACUSADOS",
    "SUGESTAO_INSUFICIENTE",
    "RAMO_BASE_VIOLADO",
    "SUGESTAO_SEM_CONFLITO",
    "IDENTIDADE_A_CONFIRMAR",
    "JANELA_INCOMPATIVEL",
    "JUNCAO_NAO_EVIDENCIADA",
    "ramo_base",
    "ramo_base_intacto",
    "juncao",
    "desacoplar_identidade",
    "injetar_geracoes",
    "resumo_da_sugestao",
    "arvore_sugerida",
]
