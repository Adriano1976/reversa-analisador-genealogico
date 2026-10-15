"""Contraste dos selos da tela, resolvendo a CASCATA e nao so a regra de cada um.

## Por que este instrumento existe

Em 2026-10-14 o operador relatou que o selo combinado do cabecalho estava "em branco". A
causa nao era a regra do selo: era `.badge[class*="estado-"]{color:#fff}`, especificidade
(0,2,0), vencendo `.estado-identidade_impossivel`, especificidade (0,1,0). O selo saiu com
texto BRANCO sobre creme — 1,10:1.

Um teste que lesse apenas a regra do selo teria passado, com o texto ilegivel na tela. Por
isso aqui a cor efetiva e obtida resolvendo a cascata: todas as regras que casam com o
elemento, a de maior especificidade (e a ultima, no empate) vence.

Le a folha de verdade. Nao escreve nada.
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
FOLHA = os.path.join(RAIZ, "src", "assets", "app.css")

_BLOCO = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)

#: Os selos que o template emite hoje, na forma exata em que ele os emite (`class="..."`).
SELOS = (
    "badge estado-COMPATIVEL",
    "badge estado-POSSIVEL",
    "badge estado-CONFLITANTE",
    "badge estado-INCONCLUSIVO",
    "badge identidade-a-confirmar",
    "badge janela-impossivel",
    "badge janela-suspeita",
    "badge janela-imprecisa",
    "badge profundidade-divergencia",
    "badge profundidade-atencao",
    # O nome ANTIGO, que era o defeito, fica comentado para a sonda poder reproduzi-lo:
    # "badge estado-identidade_impossivel",
    "badge identidade-impossivel",
)


def _sem_comentario(css: str) -> str:
    """Os COMENTARIOS saem antes de tudo.

    Sem isso o regex de bloco engole o comentario que precede a regra e o seletor vira
    `/* ... */ .badge[...]`, que nao casa com nada. Foi assim que a primeira versao desta
    sonda mediu o selo e devolveu "?" para todos — o instrumento mentia, e nao a folha.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _sem_media(css: str) -> str:
    """Remove os blocos `@media`: nenhum deles toca em selo, e o parser nao os entende."""
    saida, i = [], 0
    while i < len(css):
        if css.startswith("@media", i):
            j = css.index("{", i)
            profundidade = 0
            while j < len(css):
                if css[j] == "{":
                    profundidade += 1
                elif css[j] == "}":
                    profundidade -= 1
                    if profundidade == 0:
                        break
                j += 1
            i = j + 1
            continue
        saida.append(css[i])
        i += 1
    return "".join(saida)


def _regras(css: str):
    return [(_limpo(sel), corpo)
            for sel, corpo in _BLOCO.findall(_sem_media(_sem_comentario(css)))]


def _limpo(seletor: str) -> str:
    return " ".join(seletor.split())


def _variaveis(css: str, tema: str) -> dict:
    """As custom properties do `:root`, com o bloco escuro por cima quando for o caso."""
    valores = {}
    for seletor, corpo in _regras(css):
        if seletor == ":root":
            for decl in corpo.split(";"):
                nome, _, valor = decl.partition(":")
                if nome.strip().startswith("--"):
                    valores[nome.strip()] = valor.strip()
        elif seletor == ':root[data-bs-theme="dark"]' and tema == "escuro":
            for decl in corpo.split(";"):
                nome, _, valor = decl.partition(":")
                if nome.strip().startswith("--"):
                    valores[nome.strip()] = valor.strip()
    return valores


def _resolve(valor: str, variaveis: dict) -> str:
    anterior = None
    while anterior != valor:
        anterior = valor
        valor = re.sub(r"var\((--[\w-]+)\)", lambda m: variaveis.get(m.group(1), m.group(0)), valor)
    return valor.strip()


def _casa(seletor: str, classes: str) -> bool:
    """O seletor casa com um elemento de `class="..."`? So as formas que a folha usa em selo."""
    if not seletor or seletor.startswith(("@", ":")) or " " in seletor or ">" in seletor:
        return False
    nomes = re.findall(r"\.([\w-]+)", seletor)
    atributos = re.findall(r'\[class\*="([^"]+)"\]', seletor)
    # Sem classe nem atributo o seletor e de ELEMENTO (`body`, `h1,h2,h3`) e casaria com tudo —
    # foi o segundo erro do instrumento, que fazia todo selo herdar a cor do `h5`.
    if not nomes and not atributos:
        return False
    if not all(nome in classes.split() for nome in nomes):
        return False
    return all(alvo in classes for alvo in atributos)


def _especificidade(seletor: str) -> int:
    return len(re.findall(r"\.([\w-]+)", seletor)) + len(re.findall(r"\[class", seletor))


def _valor(css: str, classes: str, propriedade: str, variaveis: dict):
    vencedor = None
    for indice, (seletor, corpo) in enumerate(_regras(css)):
        if not _casa(seletor, classes):
            continue
        for decl in corpo.split(";"):
            nome, _, valor = decl.partition(":")
            nome = nome.strip()
            if nome == propriedade or (propriedade == "background-color" and nome == "background"):
                chave = (_especificidade(seletor), indice)
                if vencedor is None or chave >= vencedor[0]:
                    vencedor = (chave, valor.strip())
    return _resolve(vencedor[1], variaveis) if vencedor else None


def _rgb(cor: str):
    cor = cor.strip().lower()
    if cor in ("transparent", "none", "inherit"):
        return None
    if cor.startswith("#"):
        hexa = cor[1:]
        if len(hexa) == 3:
            hexa = "".join(c * 2 for c in hexa)
        return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", cor)
    return tuple(int(m.group(i)) for i in (1, 2, 3)) if m else None


def _luminancia(cor) -> float:
    def canal(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = cor
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _contraste(a, b) -> float:
    la, lb = _luminancia(a), _luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


with open(FOLHA, encoding="utf-8") as arquivo:
    CSS = arquivo.read()

for tema in ("claro", "escuro"):
    variaveis = _variaveis(CSS, tema)
    fundo_da_pagina = _rgb(_resolve("var(--surface)", variaveis))
    print("=" * 92)
    print(f"TEMA {tema.upper()}")
    print("=" * 92)
    print(f"   {'classe do selo':<40}{'texto':<12}{'fundo':<12}{'contraste':>9}")
    for classes in SELOS:
        cor = _rgb(_valor(CSS, classes, "color", variaveis))
        fundo = _rgb(_valor(CSS, classes, "background-color", variaveis))
        resolvido = "herdado"
        if fundo is None:
            fundo = fundo_da_pagina
            resolvido = "(fundo do cartao)"
        razao = _contraste(cor, fundo) if cor and fundo else None
        marca = ""
        if razao is not None:
            marca = "  <-- ILEGIVEL" if razao < 4.5 else ""
        print(f"   {classes:<40}{str(cor):<12}{str(fundo):<12}"
              f"{(f'{razao:.2f}:1' if razao else '?'):>9}{marca}"
              + (f"  {resolvido}" if resolvido != 'herdado' else ""))
    print()
