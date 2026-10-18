"""Renderização da árvore sugerida em PNG/SVG, via Graphviz.

## O que este módulo desenha

O dicionário que a feature `029` devolve (`sugestao`) contém a árvore sugerida como grafo,
mas não o caminho nem a pessoa do match — esses vivem no `documental`, que vem de
`core.documentary_relationship`. Por isso as funções públicas recebem **os dois**, mais o
`resultado` da validação, de onde saem o cM e as gerações estimadas.

## Por que o DOT é montado à mão

O pacote `graphviz` sabe construir o DOT e chamar o binário. Aqui ele é usado **só para
chamar o binário**: o texto é escrito por este módulo. Assim o desenho inteiro — cores,
arestas, rótulos, escape — é testável em máquina sem Graphviz, e a ordem dos nós e arestas
não depende da versão do pacote.

O import do pacote é **preguiçoso**, dentro de `_importar_graphviz`, pelo mesmo motivo do
`psycopg2` (`L-26` da extração): dependência ausente não pode derrubar `import app` nem a
suíte inteira.

## Por que as famílias não aparecem

O grafo da árvore é bipartido pessoa↔família: a direção genitor→filho **não está na
aresta**, está no registro da família, que este módulo não pode ler sem importar `core`
(ADR-34 fechou esse ciclo de propósito). Por isso o desenho é **reconstruído** do caminho
documental (`path.ids`, já ordenado doador → ancestral → match), das gerações virtuais e
das junções. A compressão deixa a imagem hierárquica e legível, como pedido.

## O que a imagem mostra

- nó do doador em verde, nós documentais em cinza/branco, gerações sugeridas em pêssego;
- a aresta rompida em vermelho tracejado, com o rótulo `DESVIO DE CONEXÃO / QUEBRA DE LINHA`;
- a cadeia sugerida entre o ancestral e o filho documental, ao lado da aresta rompida;
- uma caixa de nota com `"<cM> cM, <gerações> gerações - <veredito>"`.

Nada é gravado fora do `destino` informado, e a imagem não é servida pela aplicação.
"""
from __future__ import annotations

import os
import shutil

VERDE_BASE = "#a8e6cf"
BORDA_BASE = "#4a7c68"
CINZA_DOCUMENTAL = "#f5f5f5"
BORDA_DOCUMENTAL = "#666666"
AMARELO_VIRTUAL = "#ffd3b6"
BORDA_VIRTUAL = "#a8724a"
COR_FONTE = "#333333"
COR_FILIACAO = "#555555"
COR_CADEIA = "#a8724a"
COR_QUEBRA = "red"

ROTULO_QUEBRA = "DESVIO DE CONEXÃO / QUEBRA DE LINHA"
TITULO_EVIDENCIA = "Evidência genética"

#: Formatos aceitos. O pedido nomeia dois; um a mais seria superfície sem uso declarado.
FORMATOS = ("png", "svg")

#: Identificador do nó da caixa de evidência. Sem `@` de propósito: não é pessoa.
NO_EVIDENCIA = "EVIDENCIA"

SEM_SUGESTAO_PARA_DESENHAR = "SEM_SUGESTAO_PARA_DESENHAR"
FORMATO_NAO_SUPORTADO = "FORMATO_NAO_SUPORTADO"
DESTINO_OBRIGATORIO = "DESTINO_OBRIGATORIO"
GRAPHVIZ_AUSENTE = "GRAPHVIZ_AUSENTE"
DOT_AUSENTE = "DOT_AUSENTE"

#: Frase de negócio por código crítico. O primeiro crítico decide o texto da caixa.
VEREDITOS = {
    "PROFUNDIDADE_TEMPORAL_INCOMPATIVEL": "Incompatibilidade Biológica",
    "GENITOR_FORA_DA_JANELA_BIOLOGICA": "Idade de genitor impossível",
    "CM_INCOMPATIVEL_COM_PROFUNDIDADE": "cM incompatível com a profundidade",
    "MRCA_POSTERIOR_A_DESCENDENTE": "MRCA posterior ao descendente",
    "DOADOR_VIVO_EM_LINHA_INCOMPATIVEL": "Doador vivo em linha incompatível",
    "CONFLITO_CM_DOCUMENTAL": "Conflito entre cM e documento",
}
VEREDITO_PADRAO = "Quebra de linha documental"

_SEM_DADO = "—"


class ErroDeRenderizacao(Exception):
    """Falha de renderização, com um `codigo` estável para o chamador.

    Mora aqui, e não em `core.erros`, porque `reporting/` não importa `core` (ADR-34).
    """

    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------

def _escapar(texto) -> str:
    """Escapa barra e aspas para dentro de um rótulo DOT entre aspas duplas.

    O modo `label=<...>` é HTML e transformaria `&`/`<` de um nome de pessoa em marcação.
    Aqui o texto é sempre dado, nunca gramática.
    """
    return (str(texto if texto is not None else "")
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", " ")
            .replace("\n", "\\n"))


def _numero(valor) -> str:
    """Uma casa decimal, ponto decimal, ou `—` quando o dado não existe."""
    try:
        return f"{float(valor):.1f}"
    except (TypeError, ValueError):
        return _SEM_DADO


def veredito(resultado) -> str:
    """A frase de negócio do primeiro código crítico, ou o texto padrão."""
    for codigo in (resultado or {}).get("codigos") or []:
        if codigo.get("severidade") == "critico":
            return VEREDITOS.get(codigo.get("codigo"), VEREDITO_PADRAO)
    return VEREDITO_PADRAO


def resumo_evidencia(resultado) -> str:
    """`"21.6 cM, 5.7 gerações - Incompatibilidade Biológica"`, como no pedido."""
    estimativa = (resultado or {}).get("mrca_estimado") or {}
    return (f"{_numero((resultado or {}).get('cm'))} cM, "
            f"{_numero(estimativa.get('geracoes'))} gerações - {veredito(resultado)}")


def _rotulo_de(grafo, no_id) -> str:
    """Rótulo do nó no grafo; sem grafo, usa o próprio id."""
    try:
        atributos = grafo.nodes[no_id]
    except (KeyError, TypeError):
        return str(no_id)
    return atributos.get("label") or str(no_id)


def _validar_destino(destino) -> str:
    if not destino or not str(destino).strip():
        raise ErroDeRenderizacao(
            DESTINO_OBRIGATORIO,
            "Informe o caminho completo do arquivo de imagem, com extensão .png ou .svg.")
    destino = str(destino)
    if not os.path.splitext(destino)[1].lstrip("."):
        raise ErroDeRenderizacao(
            DESTINO_OBRIGATORIO,
            f"O destino {destino!r} não tem extensão; use .png ou .svg.")
    pasta = os.path.dirname(os.path.abspath(destino))
    if not os.path.isdir(pasta):
        raise ErroDeRenderizacao(
            DESTINO_OBRIGATORIO, f"A pasta de destino não existe: {pasta!r}.")
    return destino


def _validar_formato(destino: str, formato) -> str:
    extensao = os.path.splitext(destino)[1].lstrip(".").lower()
    escolhido = (formato or extensao or "").lower()
    if escolhido not in FORMATOS:
        raise ErroDeRenderizacao(
            FORMATO_NAO_SUPORTADO,
            f"Formato {escolhido or 'desconhecido'!r} não suportado; use 'png' ou 'svg'.")
    if extensao and extensao != escolhido:
        raise ErroDeRenderizacao(
            FORMATO_NAO_SUPORTADO,
            f"O destino termina em .{extensao} mas o formato pedido é {escolhido!r}.")
    return escolhido


def _importar_graphviz():
    """Import preguiçoso do binding, traduzindo a ausência em código de domínio."""
    try:
        import graphviz  # noqa: PLC0415 — preguiçoso de propósito (L-26)
    except ImportError as erro:  # pragma: no cover - depende de ambiente sem o pacote
        raise ErroDeRenderizacao(
            GRAPHVIZ_AUSENTE,
            "O pacote Python 'graphviz' não está instalado. Rode "
            "`.venv\\Scripts\\python -m pip install graphviz`.") from erro
    return graphviz


# ---------------------------------------------------------------------------
# Recorte
# ---------------------------------------------------------------------------

def _recorte(sugestao, documental) -> dict:
    """Nós e arestas que a imagem desenha.

    Devolve `{"nos": [(id, classe)], "arestas": [(origem, destino, classe)]}`. As classes
    são `base`, `documental`, `virtual`, `filiacao`, `cadeia` e `quebra`.
    """
    documental = documental or {}
    caminho = list((documental.get("path") or {}).get("ids") or [])
    ancestral_id = (documental.get("common_ancestor") or {}).get("id")

    if not caminho or not ancestral_id or ancestral_id not in caminho:
        raise ErroDeRenderizacao(
            SEM_SUGESTAO_PARA_DESENHAR,
            "Não há caminho documental para desenhar; rode a validação e a correção antes.")

    doador_id = ((sugestao or {}).get("doador") or {}).get("id") or caminho[0]
    indice = caminho.index(ancestral_id)
    grafo = (sugestao or {}).get("grafo")

    juncoes = list((sugestao or {}).get("juncoes") or [])
    if not juncoes and (sugestao or {}).get("juncao"):
        juncoes = [sugestao["juncao"]]

    saltos_rompidos = {(item.get("pai_id"), item.get("filho_id")) for item in juncoes}

    nos = []
    vistos = set()

    def _adicionar(no_id, classe):
        if no_id and no_id not in vistos:
            vistos.add(no_id)
            nos.append((no_id, classe))

    for posicao, pessoa_id in enumerate(caminho):
        if pessoa_id == doador_id:
            _adicionar(pessoa_id, "base")
        else:
            _adicionar(pessoa_id, "documental")

    arestas = []
    for posicao in range(len(caminho) - 1):
        if posicao < indice:
            pai_id, filho_id = caminho[posicao + 1], caminho[posicao]
        else:
            pai_id, filho_id = caminho[posicao], caminho[posicao + 1]
        if (pai_id, filho_id) in saltos_rompidos:
            # O salto é justamente o que a cirurgia cortou: desenhado como quebra.
            continue
        arestas.append((pai_id, filho_id, "filiacao"))

    geracoes = list((sugestao or {}).get("geracoes_virtuais") or [])
    for juncao_dados in juncoes:
        pai_id = juncao_dados.get("pai_id")
        filho_id = juncao_dados.get("filho_id")
        lado = juncao_dados.get("lado")
        cadeia = sorted(
            (item for item in geracoes if item.get("lado") == lado),
            key=lambda item: item.get("ordem") or 0)
        anterior = pai_id
        for geracao in cadeia:
            _adicionar(geracao["id"], "virtual")
            arestas.append((anterior, geracao["id"], "cadeia"))
            anterior = geracao["id"]
        if cadeia:
            arestas.append((anterior, filho_id, "cadeia"))
        arestas.append((pai_id, filho_id, "quebra"))

    return {"nos": nos, "arestas": arestas, "grafo": grafo, "doador": doador_id,
            "virtual_por_id": {item["id"]: item for item in geracoes}}


# ---------------------------------------------------------------------------
# Texto DOT
# ---------------------------------------------------------------------------

_ESTILO_NO = ('node [shape=box, style="filled,rounded", fontname="Helvetica", '
              'fontcolor="{fonte}"];')

_ATRIBUTOS_POR_CLASSE = {
    "base": 'fillcolor="{preenchimento}", color="{borda}", penwidth=2',
    "documental": 'fillcolor="{preenchimento}", color="{borda}"',
    "virtual": 'fillcolor="{preenchimento}", color="{borda}", style="filled,dashed"',
}

_CORES_POR_CLASSE = {
    "base": (VERDE_BASE, BORDA_BASE),
    "documental": (CINZA_DOCUMENTAL, BORDA_DOCUMENTAL),
    "virtual": (AMARELO_VIRTUAL, BORDA_VIRTUAL),
}


def texto_dot(sugestao, resultado, documental) -> str:
    """O texto DOT da árvore sugerida, sem tocar disco e sem importar Graphviz."""
    if not sugestao or (sugestao or {}).get("grafo") is None:
        avisos = (sugestao or {}).get("avisos") or []
        motivo = avisos[0]["mensagem"] if avisos else "a correção não gerou árvore sugerida"
        raise ErroDeRenderizacao(
            SEM_SUGESTAO_PARA_DESENHAR,
            f"Não há árvore sugerida para desenhar: {motivo}.")

    recorte = _recorte(sugestao, documental)
    grafo = recorte["grafo"]
    doador_id = recorte["doador"]

    linhas = [
        "digraph arvore_sugerida {",
        "  rankdir=TB;",
        '  labelloc="t";',
        f'  label="{_escapar("Árvore sugerida — " + _rotulo_de(grafo, doador_id))}";',
        '  bgcolor="white";',
        '  fontname="Helvetica";',
        f'  fontcolor="{COR_FONTE}";',
        "  " + _ESTILO_NO.format(fonte=COR_FONTE),
        "  edge [fontname=\"Helvetica\", fontcolor=\"" + COR_FONTE + "\"];",
        "",
    ]

    for no_id, classe in recorte["nos"]:
        preenchimento, borda = _CORES_POR_CLASSE[classe]
        atributos = _ATRIBUTOS_POR_CLASSE[classe].format(
            preenchimento=preenchimento, borda=borda)
        if classe == "virtual":
            rotulo = (recorte["virtual_por_id"].get(no_id) or {}).get("label") or no_id
        else:
            rotulo = _rotulo_de(grafo, no_id)
        linhas.append(f'  "{_escapar(no_id)}" [label="{_escapar(rotulo)}", {atributos}];')

    linhas.append("")

    for origem, destino, classe in recorte["arestas"]:
        if classe == "filiacao":
            linhas.append(f'  "{_escapar(origem)}" -> "{_escapar(destino)}" '
                          f'[color="{COR_FILIACAO}"];')
        elif classe == "cadeia":
            linhas.append(f'  "{_escapar(origem)}" -> "{_escapar(destino)}" '
                          f'[color="{COR_CADEIA}", penwidth=2];')
        else:
            linhas.append(
                f'  "{_escapar(origem)}" -> "{_escapar(destino)}" '
                f'[style=dashed, color={COR_QUEBRA}, penwidth=2, '
                f'label="{_escapar(ROTULO_QUEBRA)}", fontcolor="{COR_QUEBRA}"];')

    resumo = resumo_evidencia(resultado)
    linhas.extend([
        "",
        f'  "{NO_EVIDENCIA}" [shape=note, style=filled, fillcolor="white", '
        f'color="{BORDA_DOCUMENTAL}", fontcolor="{COR_FONTE}", '
        f'label="{_escapar(TITULO_EVIDENCIA + chr(10) + resumo)}"];',
        f'  "{NO_EVIDENCIA}" -> "{_escapar(doador_id)}" [style=invis];',
        "}",
    ])
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# Renderização
# ---------------------------------------------------------------------------

def renderizar_arvore_sugerida(sugestao, resultado, documental, destino,
                               formato=None) -> str:
    """Grava a imagem no `destino` e devolve o caminho gravado.

    Só PNG e SVG. O destino é obrigatório, precisa ter extensão coerente com o formato e
    a pasta tem de existir — o renderizador não cria pasta nem escolhe caminho.
    """
    destino = _validar_destino(destino)
    formato = _validar_formato(destino, formato)
    texto = texto_dot(sugestao, resultado, documental)

    if shutil.which("dot") is None:
        raise ErroDeRenderizacao(
            DOT_AUSENTE,
            "O binário 'dot' do Graphviz não está no PATH. Instale o Graphviz "
            "(https://graphviz.org/download/), reabra o terminal e confira com `dot -V`.")

    graphviz = _importar_graphviz()
    base = destino[: -len(formato) - 1]
    try:
        graphviz.Source(texto).render(filename=base, format=formato, cleanup=True)
    except getattr(graphviz, "ExecutableNotFound", OSError) as erro:  # pragma: no cover
        raise ErroDeRenderizacao(
            DOT_AUSENTE,
            "O Graphviz respondeu, mas não conseguiu executar o 'dot'. "
            "Confira a instalação e o PATH.") from erro

    if not os.path.isfile(destino):  # pragma: no cover - defensivo
        raise ErroDeRenderizacao(
            DOT_AUSENTE, f"O Graphviz não produziu o arquivo {destino!r}.")
    return destino


__all__ = [
    "ErroDeRenderizacao",
    "FORMATOS",
    "NO_EVIDENCIA",
    "ROTULO_QUEBRA",
    "TITULO_EVIDENCIA",
    "SEM_SUGESTAO_PARA_DESENHAR",
    "FORMATO_NAO_SUPORTADO",
    "DESTINO_OBRIGATORIO",
    "GRAPHVIZ_AUSENTE",
    "DOT_AUSENTE",
    "VEREDITOS",
    "renderizar_arvore_sugerida",
    "resumo_evidencia",
    "texto_dot",
    "veredito",
]
