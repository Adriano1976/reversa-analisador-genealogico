"""Emissao do diagrama Mermaid e o contrato de escape do rotulo.

Extraido de `path_search.py` pela OPP-20260929-UXEF. Responsabilidade unica: transformar um
caminho de parentesco no texto do diagrama.

Este e o modulo onde o contrato de escape vive. `_LABEL_SEGURO` e a lista branca que
substituiu a lista negra furada pela crase, e o comentario que a documenta veio junto com
ela. Ver BUG-20260929-J6PQ.

Contrato de dominio (OPP-20261006-ULVW): este modulo NAO importa `core`. Ele recebe
`dominio`, o mapeamento devolvido por `core.diagram_domain.resolvedor_de_diagrama`, no qual
faz as consultas de que o desenho precisa. Antes desta costura o renderizador importava
`core.family_navigation`, `core.path_finding` e `core.gedcom_state`, o que fechava o ciclo
`core/` <-> `reporting/`.

As decisoes de LAYOUT continuam aqui, e isso e deliberado: `reporting/` nao e folha e nao
pode ser, porque decidir o casal do ancestral comum, o ancestral que ancora o ramo e o
ponto de corte por casamento e decisao de negocio (`_reversa_sdd/architecture.md` secao 3 e
ADR-11). O que mudou foi apenas quem busca o dado.
"""
from __future__ import annotations

import re
import unicodedata
from contextlib import contextmanager


def _mermaid_sid(raw) -> str:
    """Identificador de no Mermaid: apenas [A-Za-z0-9_], prefixado com N_."""
    if isinstance(raw, (list, tuple, set)):
        raw = next(iter(raw), "")
    safe_str = str(raw).replace('@', '').replace('+', '_')
    return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)


# Caracteres que podem sobreviver num rotulo entre aspas do Mermaid. A gramatica do
# flowchart prova que, dentro do estado `string`, o lexer consome tudo com `<string>[^"]+`,
# entao colchete, dois pontos, barra e palavra-chave sao inertes. O que nao pode passar e a
# aspa dupla, que encerra o rotulo, e a crase, que logo apos a aspa de abertura desvia o
# lexer para markdown-string e faz o fecha-colchete nunca virar o token que a gramatica
# exige. Lista branca, e nao negra: a negra anterior foi furada justamente pela crase.
#
# A amplitude segue o criterio de INERTE, e nao o de "seguro": tudo que a gramatica tolera
# dentro das aspas e que o legado preservava continua passando. A versao anterior desta
# lista era estreita demais e descartava 14 caracteres sem que isso fosse pretendido. Ver
# BUG-20261002-T4ZM.
#
_LABEL_SEGURO = re.compile(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ .,'()&<>:;/\[\]!?@#$%*+=^_{|}~\\-]")


def _mermaid_label(txt) -> str:
    """Rotulo de no Mermaid: NFC, lista branca de caracteres seguros, com &, < e > em entidade."""
    s = unicodedata.normalize("NFC", str(txt))
    s = (s.replace('\u00A0', ' ')
           .replace('\u2013', '-')
           .replace('\u2014', '-')
           .replace('\u201c', "'").replace('\u201d', "'").replace('\u2019', "'"))
    s = s.replace('"', "'")
    s = re.sub(r'[\r\n]+', ' ', s)
    s = _LABEL_SEGURO.sub('', s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# AS CAIXAS DE TAMANHO FIXO (2026-10-26)
#
# O desenho passa a ter duas medidas, e so duas: pessoa e casal. Sem largura fixa, cada
# nome esticava o proprio retangulo e o diagrama ficava irregular conforme a sorte dos
# nomes; com ela, um nome comprido quebra em duas linhas dentro da mesma caixa e o
# esqueleto do desenho nao muda.
#
# A largura vai num `<div>` dentro do rotulo HTML. O Mermaid mede o rotulo antes de
# posicionar os nos, entao a caixa nasce com a largura certa e as setas chegam na borda —
# diferente de ajustar o SVG depois, que deixaria as setas apontando para o retangulo
# antigo. Medido no Mermaid 10 com `securityLevel: 'strict'`: 190 vira 205 px de caixa e
# 230 vira 245. O `min-height` garante a mesma ALTURA quando o registro nao tem data; a
# linha de detalhe fica vazia (`&nbsp;`) em vez de sumir.
#
# A cor e o corpo do detalhe sao literais e nao `var(--muted)`: o desenho roda dentro do
# SVG do Mermaid, sobre a placa branca, nos dois temas — os tokens do tema escuro
# clareariam o texto sobre o branco.
_LARGURA_DA_PESSOA = 230
_LARGURA_DO_CASAL = 230
_ALTURA_MINIMA = 44
_ALTURA_MINIMA_DO_CASAL = 66
_DETALHE = "font-size:12.5px;color:#6A6150"


def _caixa(conteudo, largura, altura_minima) -> str:
    return (
        f"<div style='width:{largura}px;min-height:{altura_minima}px;"
        f"text-align:center;line-height:1.3'>{conteudo}</div>"
    )


def _anos_de(pid, dominio):
    """(nascimento, obito) do registro, ou (None, None) quando o dominio nao os tem."""
    get_anos = dominio.get("get_anos")
    if not get_anos:
        return (None, None)
    try:
        nasc, obito = get_anos(pid)
    except Exception:
        return (None, None)
    return (nasc, obito)


def _faixa_de_anos(pid, dominio) -> str:
    """'1912-1995', 'n. 1912', 'm. 1995' ou vazio."""
    nasc, obito = _anos_de(pid, dominio)
    if nasc and obito:
        return f"{nasc}\u2013{obito}"
    if nasc:
        return f"n. {nasc}"
    if obito:
        return f"m. {obito}"
    return ""


def _detalhe(pid, dominio, papel=None) -> str:
    """A segunda linha do no: papel, datas, os dois, ou um espaco que segura a altura."""
    faixa = _faixa_de_anos(pid, dominio)
    if papel and faixa:
        return f"{papel} · {faixa}"
    return papel or faixa or "&nbsp;"


def _rotulo_de_pessoa(pid, dominio, papel=None) -> str:
    people = dominio["people"]
    nome = _mermaid_label(dominio["get_name"](people.get(pid)))
    return _caixa(
        f"<strong>{nome}</strong><br/>"
        f"<span style='{_DETALHE}'>{_detalhe(pid, dominio, papel)}</span>",
        _LARGURA_DA_PESSOA, _ALTURA_MINIMA,
    )


def _rotulo_de_casal(pid1, pid2, dominio) -> str:
    """O casal em duas linhas, com as duas datas de nascimento embaixo.

    Antes os dois nomes vinham numa linha so, ligados por `&amp;`, e o resultado se lia
    como uma pessoa de nome composto. Duas linhas com o xis entre elas dizem o que e':
    duas pessoas, um casal — e o numero de linhas e' o que justifica a caixa maior.
    """
    people = dominio["people"]
    nome1 = _mermaid_label(dominio["get_name"](people.get(pid1)))
    nome2 = _mermaid_label(dominio["get_name"](people.get(pid2)))
    anos = [str(nasc) for nasc, _ in (_anos_de(pid1, dominio), _anos_de(pid2, dominio)) if nasc]
    faixa = " · ".join(anos) if anos else "&nbsp;"
    return _caixa(
        f"<strong>{nome1}</strong><br/><strong>\u00d7 {nome2}</strong><br/>"
        f"<span style='{_DETALHE}'>{faixa}</span>",
        _LARGURA_DO_CASAL, _ALTURA_MINIMA_DO_CASAL,
    )


def _papel(pid, p1_id, p2_id, papeis) -> str | None:
    """O papel do no, quando o chamador declarou um (o cartao de DNA declara VOCE/MATCH)."""
    if not papeis:
        return None
    alvo = _mermaid_sid(pid)
    if alvo == _mermaid_sid(p1_id):
        return papeis.get("p1")
    if alvo == _mermaid_sid(p2_id):
        return papeis.get("p2")
    return None


def generate_mermaid_graph(path, p1_id, p2_id, common_ancestor_id, dominio, papeis=None):
    sid = _mermaid_sid

    lines = ["flowchart BT"]
    seen_nodes = set()
    ac_idx = -1
    if common_ancestor_id and common_ancestor_id in path:
        try:
            ac_idx = path.index(common_ancestor_id)
        except ValueError:
            pass
    is_direct_ancestry = (ac_idx == -1 or ac_idx == 0 or ac_idx == len(path) - 1)
    couple_members_to_skip = set()
    ancestor_id_for_arrows = sid(common_ancestor_id)
    if not is_direct_ancestry:
        spouses = dominio["get_spouses"](common_ancestor_id)
        if spouses:
            couple_members_to_skip.update({common_ancestor_id, spouses[0]})
            couple_id_str = "+".join(sorted(list(couple_members_to_skip)))
            ancestor_id_for_arrows = sid(couple_id_str)
            lines.append(
                f'{ancestor_id_for_arrows}["'
                f'{_rotulo_de_casal(common_ancestor_id, spouses[0], dominio)}"]'
            )
            seen_nodes.add(ancestor_id_for_arrows)
    for node_id in path:
        if node_id in couple_members_to_skip:
            continue
        node_sid = sid(node_id)
        if node_sid not in seen_nodes:
            lines.append(
                f'{node_sid}["'
                f'{_rotulo_de_pessoa(node_id, dominio, _papel(node_id, p1_id, p2_id, papeis))}"]'
            )
            seen_nodes.add(node_sid)
    if is_direct_ancestry:
        for i in range(len(path) - 1):
            lines.append(f'{sid(path[i])} --> {sid(path[i + 1])}')
    elif ac_idx > 0:
        for i in range(ac_idx - 1):
            lines.append(f'{sid(path[i])} --> {sid(path[i + 1])}')
        lines.append(f'{sid(path[ac_idx - 1])} --> {ancestor_id_for_arrows}')
        for i in range(len(path) - 1, ac_idx + 1, -1):
            lines.append(f'{sid(path[i])} --> {sid(path[i - 1])}')
        lines.append(f'{sid(path[ac_idx + 1])} --> {ancestor_id_for_arrows}')
    lines.append(f'style {sid(p1_id)} fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px')
    lines.append(f'style {sid(p2_id)} fill:#ffebee,stroke:#ef5350,stroke-width:2px')
    if common_ancestor_id:
        lines.append(f'style {ancestor_id_for_arrows} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    return "\n".join(lines)


# O estilo que o renderizador emite para o ancestral comum do caminho direto. E por ele
# que `anotar_profundidade` encontra o alvo, e nao por um id recebido de fora: com casal, o
# no emitido e `A+B` e o id do ancestral sozinho nem existe no diagrama. Ver a docstring.
_ESTILO_DO_ANCESTRAL = re.compile(
    r"^style (\S+) fill:#fff9c4,stroke:#fbc02d,stroke-width:2px$", re.MULTILINE)


def anotar_profundidade(texto: str, anotacao: dict) -> str:
    """Acrescenta ao Mermaid JA PRONTO as marcas de profundidade.

    Recebe o diagrama pronto em vez de participar da montagem por uma razao pratica: a
    assinatura de `generate_mermaid_graph` e contrato declarado
    (`_reversa_sdd/busca-caminho/contracts.md`) e o legado a compartilha. Anotar depois
    deixa o renderizador intacto e mantem a dependencia opcional — sem ela, o diagrama sai
    exatamente como sempre saiu.

    O ancestral comum e marcado TROCANDO o estilo que ja esta la: a tentacao e receber o id
    do ancestral e emitir um `style` novo para ele. Nao serve: quando o ancestral **nao**
    esta numa das pontas do caminho, o renderizador o funde com o conjuge num no unico
    (`A+B`), e o id do ancestral sozinho nao existe no diagrama — o `style` cairia no vazio,
    sem erro nenhum, e a marca sumiria justamente nos casos com casal. Reimplementar aqui a
    decisao do casal duplicaria regra de negocio que o `ADR-11` mantem no renderizador.
    Entao o alvo e encontrado pelo estilo de ancestral que o renderizador **ja emitiu**:
    `fill:#fff9c4,stroke:#fbc02d`, que aparece uma unica vez no diagrama direto.

    O que as marcas dizem, e o que elas NAO fazem: o **ancestral comum documental** continua
    amarelo e ganha contorno vermelho tracejado: e o no que a arvore propoe e que o cM nao
    sustenta; quando o caminho TEM um no na profundidade que o kit sugere, ele ganha
    contorno roxo tracejado. Esse no e uma pessoa **que ja estava no caminho documental** —
    nenhum no e criado, e nenhuma geracao e inventada. E o oposto da interpolacao de
    "Geração 1, Geração 2": o desenho mostra onde o DNA sugere o ancestral e onde a arvore o
    colocou, sem preencher o meio; quando o GEDCOM nao alcanca a profundidade sugerida, so o
    ancestral documental e marcado, e o texto da legenda diz que a arvore para antes.

    Nenhum TEXTO entra no diagrama: a leitura da profundidade ("a arvore afirma 7,5
    geracoes...") nasceu aqui, como um no solto ao lado do desenho, e saiu: num `flowchart`
    toda caixa parece um parente, e o operador que ve uma caixa no grafo espera que ela seja
    uma pessoa ou um vinculo. Ela e hoje um bloco de texto na legenda, montado por
    `core.profundidade_do_caminho.resumo_da_profundidade`. Este modulo **so marca no**, e
    nada que ele emite afirma ligacao nem carrega frase.
    """
    if not texto or not anotacao:
        return texto

    linhas = []

    def _marcar_ancestral(encontrado):
        return ("style " + encontrado.group(1) + " fill:#fff9c4,stroke:#c62828,"
                "stroke-width:3px,stroke-dasharray: 6 4")

    texto, trocas = _ESTILO_DO_ANCESTRAL.subn(_marcar_ancestral, texto)

    no_sugerido = anotacao.get("no_sugerido")
    if no_sugerido:
        linhas.append(f"style {_mermaid_sid(no_sugerido)} fill:#f3e5f5,stroke:#8e24aa,"
                      "stroke-width:3px,stroke-dasharray: 6 4")

    # Sem o estilo de ancestral no texto nao ha o que anotar: o diagrama nao veio do
    # caminho direto. Devolver o original e melhor que devolver meia anotacao.
    if not trocas:
        return texto
    if not linhas:
        return texto
    return texto + "\n" + "\n".join(linhas)


def generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path, dominio, papeis=None):
    sid = _mermaid_sid
    exclude_tail = dominio["exclude_tail"]
    split_path_by_marriage = dominio["split_path_by_marriage"]
    find_ancestral_path = dominio["find_ancestral_path"]
    pick_spouse_for_couple = dominio["pick_spouse_for_couple"]

    def norm_ids(seq):
        out = []
        if not seq:
            return out
        for x in seq:
            if isinstance(x, (list, tuple, set)):
                out.extend([str(y) for y in x])
            else:
                out.append(str(x))
        return out

    left, right, spouses = split_path_by_marriage(person_path)
    if not spouses:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None, dominio, papeis)

    A, B = map(str, spouses)
    p1_id, p2_id = str(p1_id), str(p2_id)

    is_direct_connection_to_p2 = (p2_id == B)

    path_p1_A, ca1 = find_ancestral_path(p1_id, A)
    if not path_p1_A:
        return generate_mermaid_graph(person_path, p1_id, p2_id, None, dominio, papeis)

    spouse_ca1 = pick_spouse_for_couple(ca1, candidate_path=path_p1_A)

    def split_at(path, mid):
        path = norm_ids(path)
        mid = str(mid)
        i = path.index(mid)
        down = path[:i + 1]
        up_rev = list(reversed(path[i:]))
        return down, up_rev

    r1_down, r1_up_from_A = split_at(path_p1_A, ca1)

    couple1_id = None
    couple1_label = None
    if spouse_ca1:
        couple1_id = sid("+".join(sorted([str(ca1), str(spouse_ca1)])))
        couple1_label = _rotulo_de_casal(ca1, spouse_ca1, dominio)

    lines = ["flowchart BT"]
    seen = set()

    @contextmanager
    def subgrafo(header):
        """Abre o subgrafo, escreve a direcao e o fecha ao fim do bloco.

        O fechamento deixa de ser uma linha que alguem precisa posicionar no meio
        do fluxo: ele e o fim do `with`. Um `end` a mais ou a menos muda a arvore
        do diagrama sem levantar erro nenhum, e era exatamente esse o risco
        registrado na OPP-20260929-H2YY.

        Sem try/finally de proposito: `end` so e escrito se o corpo terminar, que
        e o comportamento da sequencia de append que este helper substitui.
        """
        lines.append("subgraph %s" % header)
        lines.append("direction BT")
        yield
        lines.append("end")

    def add_node(pid, label=None):
        pid = str(pid)
        node = sid(pid)
        if node not in seen:
            conteudo = label if label is not None else _rotulo_de_pessoa(
                pid, dominio, _papel(pid, p1_id, p2_id, papeis))
            lines.append(f'{node}["{conteudo}"]')
            seen.add(node)
        return node

    def add_chain(seq):
        seq = norm_ids(seq)
        for i in range(len(seq)):
            add_node(seq[i])
            if i < len(seq) - 1:
                lines.append(f'{sid(seq[i])} --> {sid(seq[i + 1])}')

    def emit_couple_or_ancestor(couple_id, couple_label, ca, left_col, right_col):
        """Emite o par de conjuge, ou o ancestral quando nao ha par, e liga as colunas.

        O destino das setas difere: o par ja chega como id de no, e o ancestral ainda passa
        por `sid`. Assumir o mesmo id muda a saida nos casos com conjuge.
        """
        if couple_id:
            lines.append(f'{couple_id}["{couple_label}"]')
            alvo = couple_id
        else:
            add_node(ca)
            alvo = sid(ca)
        if left_col:
            lines.append(f'{sid(left_col[-1])} --> {alvo}')
        if right_col:
            lines.append(f'{sid(right_col[-1])} --> {alvo}')

    with subgrafo("COLUMNS"):
        with subgrafo("ESQ[Ramo 1]"):
            with subgrafo("ESQ_COLS"):
                left_col_r1 = exclude_tail(r1_down, n=1)
                right_col_r1 = exclude_tail(r1_up_from_A, n=1)

                if left_col_r1:
                    with subgrafo("ESQ_L[ ]"):
                        add_chain(left_col_r1)
                if right_col_r1:
                    with subgrafo("ESQ_R[ ]"):
                        add_chain(right_col_r1)

            emit_couple_or_ancestor(couple1_id, couple1_label, ca1, left_col_r1, right_col_r1)

        if is_direct_connection_to_p2:
            with subgrafo("DIR[Ramo 2]"):
                add_node(p2_id)
            right_col_r2 = []
            couple2_id, ca2 = None, None
        else:
            path_p2_B, ca2 = find_ancestral_path(p2_id, B)
            if not path_p2_B:
                return generate_mermaid_graph(person_path, p1_id, p2_id, None, dominio, papeis)

            spouse_ca2 = pick_spouse_for_couple(ca2, candidate_path=path_p2_B)
            r2_down, r2_up_from_B = split_at(path_p2_B, ca2)

            couple2_id = None
            couple2_label = None
            if spouse_ca2:
                couple2_id = sid("+".join(sorted([str(ca2), str(spouse_ca2)])))
                couple2_label = _rotulo_de_casal(ca2, spouse_ca2, dominio)

            with subgrafo("DIR[Ramo 2]"):
                with subgrafo("DIR_COLS"):
                    left_col_r2 = exclude_tail(r2_up_from_B, n=1)
                    right_col_r2 = exclude_tail(r2_down, n=1)

                    if left_col_r2:
                        with subgrafo("DIR_L[ ]"):
                            add_chain(left_col_r2)
                    if right_col_r2:
                        with subgrafo("DIR_R[ ]"):
                            add_chain(right_col_r2)

                emit_couple_or_ancestor(couple2_id, couple2_label, ca2, left_col_r2, right_col_r2)

        A_anchor = sid(f"{A}_anc")
        B_anchor = sid(f"{B}_anc")
        lines += [
            f'{A_anchor}[" "]',
            f'{B_anchor}[" "]',
            f'style {A_anchor} fill:transparent,stroke:transparent,stroke-width:0',
            f'style {B_anchor} fill:transparent,stroke:transparent,stroke-width:0',
            f'{sid(A)} --- {A_anchor}',
            f'{B_anchor} --- {sid(B)}',
            f'{A_anchor} --- |Casamento| {B_anchor}',
        ]

    if left_col_r1:
        lines.append(f'style {sid(p1_id)} fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px')

    if is_direct_connection_to_p2 or right_col_r2:
        lines.append(f'style {sid(p2_id)} fill:#ffebee,stroke:#ef5350,stroke-width:2px')

    if couple1_id:
        lines.append(f'style {couple1_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca1:
        lines.append(f'style {sid(ca1)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    if couple2_id:
        lines.append(f'style {couple2_id} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')
    elif ca2:
        lines.append(f'style {sid(ca2)} fill:#fff9c4,stroke:#fbc02d,stroke-width:2px')

    lines.append(f'style {sid(A)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')
    lines.append(f'style {sid(B)} fill:#fff8e1,stroke:#f6a821,stroke-width:2px')

    return "\n".join(lines)

# A arvore sugerida (feature 032)

def mermaid_da_sugestao(documental, resumo):
    """Desenho Mermaid da arvore sugerida: caminho + geracoes virtuais + quebra.

    O que entra, e o que NAO entra: so o caminho documental (`path.ids`) mais as geracoes
    virtuais. Nenhum no de familia: a familia e' a aresta, e desenha-la dobraria o numero de
    nos sem dizer nada sobre a linha. A compressao e' a mesma da imagem da feature 030.

    Por que `flowchart BT`, e nao `graph TD` (corrigido em 2026-10-21): o diagrama
    DOCUMENTADO logo acima usa `flowchart BT` com as arestas do filho para o pai: o ancestral
    fica em cima e o doador embaixo. A sugestao usava `graph TD` com as MESMAS arestas, e o
    resultado era um desenho com duas convencoes ao mesmo tempo — a metade do doador virava
    de cabeca para baixo e o operador lia a cadeia no sentido errado. Agora as duas usam BT,
    e TODA seta aponta do descendente para o ascendente.

    O match e' vermelho, como no diagrama documentado: o ultimo no do caminho e' a pessoa
    alcancada (o match). Ele recebe a mesma cor que `generate_mermaid_graph` usa para `p2`,
    para que os dois desenhos — o que o GEDCOM afirma e o que a hipotese proporia — possam
    ser comparados sem legenda nova.

    Por que `classDef`, se o resto do modulo usa `style`: aqui ha exatamente QUATRO classes
    repetidas em muitos nos; `classDef` diz isso em quatro linhas. No diagrama do caminho
    documentado cada no tem cor propria, e `style` por no e' mais direto. Os dois sao Mermaid
    valido, e cada um serve ao seu caso.

    A aresta rompida e' a ULTIMA, e isso nao e' estilo: `linkStyle` indexa as arestas por
    POSICAO de declaracao, nao por id. Emitir a aresta rompida por ultimo e' o que torna o
    indice previsivel — e o teste fixa esse indice, porque uma reordenacao mandaria o
    vermelho tracejado para a aresta errada, em silencio.

    Devolve `None` quando nao ha o que desenhar (sem caminho, sem ancestral ou sem geracao a
    inserir).
    """
    from .visualizer import ROTULO_QUEBRA

    documental = documental or {}
    resumo = resumo or {}
    caminho = list((documental.get("path") or {}).get("ids") or [])
    ancestro = (documental.get("common_ancestor") or {}).get("id")
    geracoes = int(resumo.get("geracoes") or 0)
    rotulos = list(resumo.get("rotulos") or [])

    if not caminho or not ancestro or ancestro not in caminho or geracoes <= 0:
        return None

    nomes = list((documental.get("path") or {}).get("names") or [])
    sid, lab = _mermaid_sid, _mermaid_label
    indice = caminho.index(ancestro)
    filho = caminho[indice - 1] if indice > 0 else None
    match = caminho[-1]

    def nome(posicao):
        return nomes[posicao] if posicao < len(nomes) else caminho[posicao]

    linhas = [
        "flowchart BT",
        "  classDef base fill:#a8e6cf,stroke:#4a7c68,stroke-width:2px",
        "  classDef doc fill:#f5f5f5,stroke:#666666",
        "  classDef match fill:#ffebee,stroke:#ef5350,stroke-width:2px",
        "  classDef virt fill:#ffd3b6,stroke:#a8724a,stroke-dasharray:4 3",
    ]

    for posicao, pessoa_id in enumerate(caminho):
        if posicao == 0:
            classe = "base"
        elif pessoa_id == match:
            classe = "match"
        else:
            classe = "doc"
        linhas.append(f'  {sid(pessoa_id)}["{lab(nome(posicao))}"]:::{classe}')

    virtuais = []
    for ordem in range(1, geracoes + 1):
        identificador = f"V{ordem}"
        rotulo = rotulos[ordem - 1] if ordem - 1 < len(rotulos) else f"Geração {ordem}"
        linhas.append(f'  {identificador}["{lab(rotulo)}"]:::virt')
        virtuais.append(identificador)

    arestas = []
    for posicao in range(len(caminho) - 1):
        if filho and posicao == indice - 1:
            continue  # a aresta rompida e' desenhada no fim, marcada
        # Antes do ancestral o caminho SOBE (filho -> pai) e depois DESCE (pai -> filho);
        # a aresta e invertida para TODA seta apontar para o ascendente — sem isso, o ramo
        # do match sai ao contrario dentro do mesmo grafico.
        if posicao < indice:
            arestas.append(f"  {sid(caminho[posicao])} --> {sid(caminho[posicao + 1])}")
        else:
            arestas.append(f"  {sid(caminho[posicao + 1])} --> {sid(caminho[posicao])}")

    # Em BT a seta sobe. A cadeia e' emitida do descendente para o ancestral, como as
    # arestas do caminho: `V1 --> Joaquim` le "Geração 1 e' filha de Joaquim".
    anterior = sid(ancestro)
    for identificador in virtuais:
        arestas.append(f"  {identificador} --> {anterior}")
        anterior = identificador
    if filho:
        arestas.append(f"  {sid(filho)} --> {anterior}")
        arestas.append(f'  {sid(filho)} -.->|{lab(ROTULO_QUEBRA)}| {sid(ancestro)}')

    linhas.extend(arestas)
    if filho:
        linhas.append(
            f"  linkStyle {len(arestas) - 1} stroke:red,stroke-width:2px,"
            "stroke-dasharray:5 5")
    return "\n".join(linhas)
