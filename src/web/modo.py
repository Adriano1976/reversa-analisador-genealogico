"""Modo de identidade declarado do processo (auditoria de 2026-10-30, P1/P3).

## O defeito que este modulo fecha

Ate 2026-10-30 a autenticacao era **condicional ao entrypoint**. `create_app()`
montava a aplicacao sem guarda nenhuma quando as cinco variaveis do Google
faltavam, e so `python src/app.py` recusava subir. Qualquer outro runner —
`waitress-serve`, um servico do Windows, um `.bat` com `flask run` — subia a
aplicacao ABERTA, com `_dono()` caindo no literal `"unico"`, que aponta para a
raiz da pasta de upload, onde estao todos os arquivos herdados.

O `ANALISADOR_MODO` fecha essa porta por construcao: **nao existe valor de
producao que resulte em app sem guarda**. Quem nao declara nao sobe.

## Os dois modos, e o que cada um significa HOJE

| Modo | O que monta | Para quem |
|---|---|---|
| `google` | OAuth 2.0 (feature 051) + identidade local (feature 053), com a guarda de sessao | instancia compartilhada, varias contas |
| `local` | **sem login**: um dono por maquina, `_dono()` no literal `"unico"` | o app instalado no computador de uma pessoa |

`local` **nao** e "o modo aberto de antes". A diferenca nao esta no que ele monta,
e sim em ser **declarado**: aparece no log, nao depende de como o processo foi
iniciado e nao acontece por esquecimento. Quando a identidade local da 053 passar
a ser oferecida no instalador, ela entra DENTRO deste modo — nao nasce um
terceiro.

## O escape de teste, e por que ele tem nome

A suite e o harness de paridade importam `src/app.py` sem credencial de proposito:
1939 testes dependem do caminho legado, sem identidade e sem guarda. Em vez de o
teste herdar o "sem variavel = aberto", ele DECLARA `ANALISADOR_MODO_TESTE=1` no
`tests/conftest.py`, no import, antes de qualquer modulo de teste ser coletado.

O escape NAO escolhe modo: ele apenas dispensa a declaracao, e o app cai no
caminho legado. E o unico jeito de obter esse caminho, e ele tem nome — o que
transforma um comportamento implicito em uma decisao verificavel.
"""
from __future__ import annotations

import os

#: A variavel que declara o modo. Ausente, vazia ou desconhecida: nao sobe.
VARIAVEL = "ANALISADOR_MODO"

#: O escape da suite e do harness de paridade. Nao e modo: e dispensa de declaracao.
VARIAVEL_DE_TESTE = "ANALISADOR_MODO_TESTE"

LOCAL = "local"
GOOGLE = "google"

#: Conjunto FECHADO, e sem sinonimo. `nenhum` foi recusado de proposito: ele seria
#: um segundo nome para o que `local` ja significa hoje, e duas verdades sobre o
#: mesmo estado e o defeito que o projeto paga caro para nao ter.
MODOS: tuple[str, ...] = (LOCAL, GOOGLE)

#: O unico valor do escape que vale. Qualquer outro deixa o escape desligado.
VALOR_DE_TESTE = "1"


class RecusaDeSubida(RuntimeError):
    """O processo nao pode subir com a configuracao atual.

    A mensagem vai para a tela e para o log: `src/app.py` a converte em
    `SystemExit` no fim do modulo, para o operador — e o `.bat` do instalador —
    lerem uma linha, e nao um traceback.
    """


class ModoNaoDeclarado(RecusaDeSubida):
    """`ANALISADOR_MODO` ausente, vazia ou fora de `MODOS`."""


def ler(ambiente=None) -> str | None:
    """O modo declarado, ou `None` quando o escape de teste esta ligado.

    `ambiente` existe para o teste passar um dicionario no lugar do `os.environ`,
    o mesmo contrato de `web.autenticacao.ConfiguracaoDeEntrada.do_ambiente`.

    A ordem importa: o modo DECLARADO vence o escape. Quem define
    `ANALISADOR_MODO=google` e tambem `ANALISADOR_MODO_TESTE=1` roda em `google`;
    o escape so vale quando nao ha declaracao.

    Levanta `ModoNaoDeclarado` quando nao ha declaracao e o escape esta desligado.
    """
    valores = os.environ if ambiente is None else ambiente
    bruto: str = (valores.get(VARIAVEL) or "").strip().lower()
    if bruto:
        if bruto not in MODOS:
            raise ModoNaoDeclarado(
                f"{VARIAVEL}={bruto!r} nao e um modo conhecido. "
                f"Use um destes: {', '.join(MODOS)}."
            )
        return bruto
    if (valores.get(VARIAVEL_DE_TESTE) or "").strip() == VALOR_DE_TESTE:
        return None
    raise ModoNaoDeclarado(
        f"{VARIAVEL} nao foi declarada. Defina {VARIAVEL}=local (app instalado num "
        f"computador, sem login) ou {VARIAVEL}=google (entrada pelo provedor), e "
        "tente de novo."
    )


__all__: list[str] = [
    "GOOGLE",
    "LOCAL",
    "MODOS",
    "ModoNaoDeclarado",
    "RecusaDeSubida",
    "VALOR_DE_TESTE",
    "VARIAVEL",
    "VARIAVEL_DE_TESTE",
    "ler",
]
