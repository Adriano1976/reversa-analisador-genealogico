"""A rota da busca por nome: `POST /busca` (feature 052).

## Por que uma rota propria, e por que POST

A rota `/` despacha por `action` e ja tem 23 `render_template`, 12 deles passando
`gedcom_filename` (`domain.md#3.6`). Mais um `action` multiplicaria os pontos de render e
de guarda; aqui o Blueprint tem um ponto de render so.

O metodo e `POST` porque o termo pode conter nome de pessoa: em `GET` ele iria para o log
de acesso e para o historico do navegador.

## O que esta rota faz

So a cola HTTP: le o formulario, chama o caso de uso, escolhe a resposta. O casamento e do
nucleo (`core.busca_de_nome`), a orquestracao e do caso de uso
(`application.busca_de_nome`) e o formato e de `reporting.resultado_da_busca`.

## A recusa de referencia e a da 051

Referencia que nao resolve — arquivo inexistente **ou de outro dono** — responde `404` com
o literal de inexistencia, nunca `403`: a resposta nao pode confirmar que o arquivo existe
(`RN-06` da feature 051).
"""
from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from reporting.lista_de_arquivos import rotulo_de_referencia
from reporting.resultado_da_busca import resultado_para_tela
from web.sessao import dono_atual

busca_bp = Blueprint("busca", __name__)

#: Teto do termo. Nao e regra de negocio: e a defesa contra uma consulta gigante varrer o
#: indice inteiro por nada.
TETO_DO_TERMO = 120

#: Literais de tela. O primeiro e NOVO (entra no contrato de mensagens); os outros dois
#: sao os que a borda ja usa, reaproveitados para nao nascer uma segunda redacao.
TERMO_VAZIO = "Digite um nome ou sobrenome para buscar."
REFERENCIA_AUSENTE = "Erro: Arquivo GEDCOM não encontrado."
REFERENCIA_SUMIU = "Erro: Arquivo '{rotulo}' não existe mais."

#: Resultado vazio, para o caso de termo em branco: a tela mostra o campo e a mensagem,
#: e nenhuma secao e produzida.
_SEM_RESULTADO: dict = {"texto": "", "total": 0, "encontrou": False, "secoes": []}


def _dono() -> str:
    """O dono da requisicao: o `sub` quando ha sessao; o marcador quando nao ha.

    Mesma regra da borda (`app._dono`): sem autenticacao o processo e de um dono so, e o
    literal vem da configuracao montada por `create_app`.
    """
    return dono_atual() or current_app.config.get("DONO_LEGADO", "unico")


@busca_bp.get("/busca")
def rever():
    """Recarregar a pagina depois de uma busca nao pode dar `405`.

    O resultado e uma resposta de `POST`; a URL que fica no navegador, porem, e `/busca`,
    e um `F5` faria um `GET` nela. Devolver para a tela e o que evita transformar um
    recarregamento em erro — a tela e a mesma, sem o resultado, e o operador busca de novo.
    """
    return redirect(url_for("index"))


@busca_bp.post("/busca")
def buscar():
    texto = (request.form.get("termo") or "").strip()[:TETO_DO_TERMO]
    referencia_da_arvore = (request.form.get("gedcom_filename") or "").strip() or None
    referencia_do_relatorio = (request.form.get("matches_csv_ref") or "").strip() or None

    if not referencia_da_arvore:
        # Sem arvore nao ha busca: o bloco so e renderizado com uma aberta, entao este
        # caminho e anomalia de formulario, e nao um estado de tela.
        return redirect(url_for("index"))

    if not texto:
        return render_template(
            "index.html",
            gedcom_filename=referencia_da_arvore,
            busca=dict(_SEM_RESULTADO),
            message=TERMO_VAZIO,
            success=False,
        )

    servico = current_app.extensions.get("busca")
    if servico is None:
        # `create_app` sempre monta o servico; se ele nao esta aqui, o defeito e de
        # montagem da aplicacao, e nao do operador. Estourar e melhor do que virar uma
        # tela de "nada encontrado" que esconde o problema.
        raise RuntimeError("a busca nao foi montada nesta aplicacao")
    resultado = servico.buscar(
        texto,
        dono=_dono(),
        referencias={
            "arvore": referencia_da_arvore,
            "relatorio": referencia_do_relatorio,
        },
    )

    if resultado.nao_resolveu:
        return (
            render_template(
                "index.html",
                message=REFERENCIA_SUMIU.format(
                    rotulo=rotulo_de_referencia(referencia_da_arvore)
                ),
                success=False,
            ),
            404,
        )

    return render_template(
        "index.html",
        gedcom_filename=referencia_da_arvore,
        busca=resultado_para_tela(resultado),
    )


__all__: list[str] = [
    "REFERENCIA_AUSENTE",
    "REFERENCIA_SUMIU",
    "TERMO_VAZIO",
    "busca_bp",
]
