"""Catalogo de laboratorios para o valor da coluna de fonte.

O CSV de segmentos declara a empresa em uma coluna (`Source`, `Fonte` ou `Company`), e o
valor vem como o operador (ou o formulario do site de origem) digitou. Medido no arquivo
real do projeto em 2026-10-22: **45 valores distintos** para **11 laboratorios** — a
variacao e ortografica (`GENERA`, `genera`, `Genera Brasil`), nao semantica.

Sem traducao, a tela exibe `Selecione uma empresa ou fonte` como se fosse o nome de uma
empresa. Este modulo separa tres desfechos: **laboratorio** (reconhecido no catalogo);
**nao declarada** (vazio, `-`, texto de formulario, haplogrupo, nome de projeto ou empresa
nao confirmada); e **outro** (valor nao reconhecido que nao e claramente nenhum dos
anteriores). Nos tres casos o **texto original e preservado** para exibicao: descartar o
valor sim, esconder nao (`domain.md` 3.8).

Por que tabela literal, e nao heuristica: `Genos` e `Genera` ficam a uma edicao de distancia
e sao empresas diferentes, e `Minha heranca` e `Meu Patrimonio` nao tem laboratorio
confirmado (decisao do operador em 2026-10-22). Distancia de edicao e prefixo casariam
errado e em silencio. A tabela e auditavel, reversivel e nao depende de servico externo — o
sistema nao tem nenhum.

O catalogo e do projeto, e nao um registro oficial: nao existe lista publica estavel de
nomes de laboratorio consumida por este codigo; o catalogo abaixo e **declarado pelo
projeto** (Principio V) e cresce por decisao, com teste.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

#: Rotulos canonicos. Ordem alfabetica, sem acento e sem caixa — e o que a tela exibe.
LABORATORIOS = (
    "23andMe",
    "Ancestry",
    "DNA Land",
    "FTDNA",
    "FamilyTreeDNA",
    "Genera",
    "Genos",
    "Living DNA",
    "MundoDNA",
    "MyHeritage",
    "meuDNA",
)

#: Desfechos que nao sao laboratorio. `NAO_DECLARADA` e `OUTRO` sao os rotulos de tela.
NAO_DECLARADA = "não declarada"
OUTRO = "outro"

#: Motivos de um valor nao ser laboratorio. Viram texto na tela e contagem no painel.
TEXTO_DE_FORMULARIO = "texto_de_formulario"
EMPRESA_NAO_CONFIRMADA = "empresa_nao_confirmada"
NOME_DE_PROJETO = "nome_de_projeto"
HAPLOGRUPO = "haplogrupo"
NAO_RECONHECIDA = "nao_reconhecida"

#: Texto de cada motivo, para a tela e para o painel de cobertura.
MOTIVOS_TEXTO = {
    TEXTO_DE_FORMULARIO: "texto de formulário",
    EMPRESA_NAO_CONFIRMADA: "empresa não confirmada",
    NOME_DE_PROJETO: "nome de projeto",
    HAPLOGRUPO: "haplogrupo na coluna de fonte",
    NAO_RECONHECIDA: "valor não reconhecido",
}

#: Frase curta que explica, NO CARTAO, por que aquele valor nao e' laboratorio.
#:
#: `MOTIVOS_TEXTO` e' rotulo de contagem (vai no painel, ao lado de um numero);
#: `EXPLICACOES` e' a frase que o operador le na secao 2. Sao textos diferentes
#: porque a frase precisa responder "entao o que e' isso?" sem o contexto do painel.
EXPLICACOES = {
    TEXTO_DE_FORMULARIO: "texto de formulário do site de origem, não um laboratório",
    EMPRESA_NAO_CONFIRMADA: "empresa não confirmada pelo projeto, que não presume o laboratório",
    NOME_DE_PROJETO: "nome de projeto de pesquisa, não de laboratório",
    HAPLOGRUPO: "haplogrupo na coluna de fonte, não um laboratório",
    NAO_RECONHECIDA: "valor não reconhecido como laboratório",
}

#: Frase para a celula vazia ou `-`: nao ha texto original que valha mostrar.
SEM_VALOR_UTIL = "o arquivo não traz uma fonte utilizável nesta coluna"

#: Celulas que sao texto de formulario vazado para o dado.
_PLACEHOLDERS = frozenset({
    "-",
    "",
    "outro (insira o nome abaixo)",
    "outros",
    "other (enter name below)",
    "selecione uma empresa ou fonte",
    "select a company or source",
})

#: Haplogrupos que aparecem na coluna errada. Medido: `L1b1a`.
_HAPLOGRUPOS = frozenset({"l1b1a", "h", "b2", "a2", "h6a1b2", "v7a", "l3"})

#: Nomes de projeto ou de campo que nao sao empresa.
_NOMES_DE_PROJETO = frozenset({"ancestralidade"})

#: Empresas que o operador decidiu NAO presumir (2026-10-22): sem confirmacao, `nao declarada`.
_EMPRESAS_NAO_CONFIRMADAS = ("minha heran", "meu patrimonio")

#: Alias normalizado -> rotulo canonico. A comparacao e por conteudo (`in`), e o
#: `GEN` sozinho ganha tratamento exato para nao casar com qualquer palavra.
_ALIAS = (
    ("genera", "Genera"),
    ("myheritage", "MyHeritage"),
    ("my heritage", "MyHeritage"),
    ("meudna-mandelics", "meuDNA"),
    ("meu dna", "meuDNA"),
    ("meudna", "meuDNA"),
    ("23andme", "23andMe"),
    ("23eeu", "23andMe"),
    ("ftdna", "FTDNA"),
    ("familytree", "FamilyTreeDNA"),
    ("ancestry", "Ancestry"),
    ("living dna", "Living DNA"),
    ("dna land", "DNA Land"),
    ("genos", "Genos"),
    ("mundodna", "MundoDNA"),
)


def _normalizar(texto: str) -> str:
    """Sem acento, sem caixa, espacos colapsados. O `bruto` nunca e normalizado."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


@dataclass(frozen=True, slots=True)
class RotuloDeFonte:
    """Desfecho da traducao de UMA celula de fonte.

    `canonico` e o laboratorio ou `None`; `texto` e o que a tela exibe (`Genera`,
    `não declarada` ou `outro`); `bruto` e a celula como veio; `motivo` explica por que
    nao e laboratorio — `None` quando e.
    """

    canonico: str | None
    texto: str
    bruto: str | None
    motivo: str | None

    @property
    def e_laboratorio(self) -> bool:
        return self.canonico is not None


def _nao_declarada(bruto: str | None, motivo: str) -> RotuloDeFonte:
    return RotuloDeFonte(canonico=None, texto=NAO_DECLARADA, bruto=bruto, motivo=motivo)


def rotulo(valor) -> RotuloDeFonte:
    """Traduz o valor de UMA celula em laboratorio, `nao declarada` ou `outro`.

    A ordem das regras importa: texto de formulario e vazio antes de tudo (sao o caso
    mais comum), depois haplogrupo e nome de projeto, depois empresa nao confirmada, e
    so entao o catalogo. Um valor que nao casa com nada e `outro`, nunca um laboratorio
    suposto.
    """
    bruto = None if valor is None else str(valor).strip()
    chave = _normalizar(bruto or "")

    if chave in _PLACEHOLDERS:
        return _nao_declarada(bruto, TEXTO_DE_FORMULARIO)
    if chave in _HAPLOGRUPOS:
        return _nao_declarada(bruto, HAPLOGRUPO)
    if chave.startswith("migration") or chave in _NOMES_DE_PROJETO:
        return _nao_declarada(bruto, NOME_DE_PROJETO)
    if any(chave.startswith(prefixo) for prefixo in _EMPRESAS_NAO_CONFIRMADAS):
        return _nao_declarada(bruto, EMPRESA_NAO_CONFIRMADA)

    if chave == "gen":
        return RotuloDeFonte(canonico="Genera", texto="Genera", bruto=bruto, motivo=None)
    for alias, canonico in _ALIAS:
        if alias in chave:
            return RotuloDeFonte(canonico=canonico, texto=canonico, bruto=bruto, motivo=None)

    return RotuloDeFonte(canonico=None, texto=OUTRO, bruto=bruto, motivo=NAO_RECONHECIDA)


def explicacao(motivo, bruto=None) -> str | None:
    """A frase que o cartao exibe ao lado do texto original. `None` quando e' laboratorio.

    A celula vazia e o `-` nao tem texto que valha mostrar: nesses casos a frase
    e' a de ausencia de valor (`SEM_VALOR_UTIL`), e nao a de "texto de formulario" —
    o operador nao precisa saber que o campo estava vazio, precisa saber que nao ha
    fonte utilizavel ali.
    """
    if not motivo:
        return None
    texto = "" if bruto is None else str(bruto).strip()
    if motivo == TEXTO_DE_FORMULARIO and texto in ("", "-"):
        return SEM_VALOR_UTIL
    return EXPLICACOES.get(motivo)


def escolher(valores) -> tuple[RotuloDeFonte, tuple[str, ...]]:
    """Escolhe o rotulo do kit e devolve `(escolhido, outros_laboratorios)`.

    A escolha prefere a **primeira linha com laboratorio reconhecido**; sem nenhuma, cai
    para o primeiro valor nao vazio, ja traduzido. Antes desta regra, um `-` na primeira
    linha do kit escondia um `Genera` declarado adiante.

    `outros_laboratorios` traz os demais rotulos distintos, na ordem em que apareceram —
    e o que o aviso `fontes_divergentes` cita. Sem divergencia, a tupla e vazia.
    """
    rotulos = [rotulo(valor) for valor in valores if str(valor or "").strip()]
    if not rotulos:
        return _nao_declarada(None, TEXTO_DE_FORMULARIO), ()

    laboratorios = [r for r in rotulos if r.e_laboratorio]
    escolhido = laboratorios[0] if laboratorios else rotulos[0]

    distintos: list[str] = []
    for r in laboratorios:
        if r.canonico is None:
            # `e_laboratorio` ja garante o contrario; o guarda existe para o
            # checador enxergar o estreitamento `str | None` -> `str`.
            continue
        if r.canonico not in distintos:
            distintos.append(r.canonico)
    if escolhido.e_laboratorio:
        distintos = [nome for nome in distintos if nome != escolhido.canonico]
    return escolhido, tuple(distintos)


__all__: list[str] = [
    "LABORATORIOS",
    "NAO_DECLARADA",
    "OUTRO",
    "MOTIVOS_TEXTO",
    "EXPLICACOES",
    "SEM_VALOR_UTIL",
    "TEXTO_DE_FORMULARIO",
    "EMPRESA_NAO_CONFIRMADA",
    "NOME_DE_PROJETO",
    "HAPLOGRUPO",
    "NAO_RECONHECIDA",
    "RotuloDeFonte",
    "rotulo",
    "explicacao",
    "escolher",
]
