"""As rotas da entrada: `/login`, `/callback` e `/logout` (feature 051).

## O que mora aqui

So a cola HTTP do fluxo: ler parametros, chamar o servico de entrada, gravar a
sessao e escolher a resposta. A troca do codigo e a leitura do perfil ficam em
`web/autenticacao.py`; a sessao e a guarda, em `web/sessao.py`; a adocao dos dados
anteriores, em `application/dono_inicial.py`.

## As tres frases de falha sao poucas de proposito

O operador precisa saber se cancelou, se expirou ou se o provedor falhou — e mais
nada. O detalhe tecnico vai para o log como rotulo curto, nunca o codigo, o token
ou o segredo.
"""
from __future__ import annotations

import hmac

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from application.dono_inicial import garantir_dados_do_dono, ha_dados_nao_atribuidos
from utils.auditoria import registrar as auditar
from web.autenticacao import ErroDeEntrada
from web.hooks_de_registro import ip_do_cliente, origem_da_requisicao
from web.sessao import (
    CHAVE_DO_STATE,
    conta_atual,
    encerrar_sessao,
    guardar_conta,
)

auth_bp = Blueprint("auth", __name__)

#: Literais de tela da entrada. Congelados por teste.
ENTRADA_CANCELADA = "A entrada foi cancelada."
ENTRADA_EXPIRADA = "A entrada expirou. Tente de novo."
ENTRADA_FALHOU = "Não foi possível concluir a entrada agora."


def _servico():
    return current_app.extensions["analisador"]["autenticacao"]


def _tela(mensagem: str | None = None):
    return render_template("login.html", message=mensagem, success=False), 200


@auth_bp.route("/login", methods=["GET"])
def login():
    """Mostra a tela de entrada, ou comeca o fluxo quando `?iniciar=1`."""
    if conta_atual() is not None:
        return redirect(url_for("index"))
    if request.args.get("iniciar"):
        servico = _servico()
        state = servico.provedor.novo_state()
        session[CHAVE_DO_STATE] = state
        return redirect(servico.provedor.url_de_autorizacao(state))
    return _tela()


@auth_bp.route("/callback", methods=["GET"])
def callback():
    """Recebe o retorno do provedor e abre a sessao, ou explica a falha."""
    if request.args.get("error"):
        session.pop(CHAVE_DO_STATE, None)
        _auditar_falha()
        return _tela(ENTRADA_CANCELADA)

    esperado = session.pop(CHAVE_DO_STATE, None)
    recebido: str = request.args.get("state") or ""
    if not esperado or not recebido or not hmac.compare_digest(esperado, recebido):
        _auditar_falha()
        return _tela(ENTRADA_EXPIRADA)

    codigo: str = request.args.get("code") or ""
    if not codigo:
        _auditar_falha()
        return _tela(ENTRADA_FALHOU)

    servico = _servico()
    try:
        conta = servico.entrar(codigo)
    except ErroDeEntrada as erro:
        current_app.logger.warning("entrada recusada: %s", erro.motivo)
        _auditar_falha()
        return _tela(ENTRADA_FALHOU)

    guardar_conta(conta)
    _garantir_dados_da_conta(conta)
    auditar(
        "entrar",
        "sucesso",
        conta=conta.sub,
        ip=ip_do_cliente(),
        origem=origem_da_requisicao(),
    )
    return redirect(url_for("index"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Encerra a sessao. Idempotente: sem sessao, tambem devolve a entrada."""
    conta = conta_atual()
    encerrar_sessao()
    if conta is not None:
        auditar(
            "sair",
            "sucesso",
            conta=conta.sub,
            ip=ip_do_cliente(),
            origem=origem_da_requisicao(),
        )
    return redirect(url_for("auth.login"), code=303)


def _auditar_falha() -> None:
    """Registra a tentativa recusada sem identificar quem tentou."""
    auditar(
        "entrar",
        "falha",
        ip=ip_do_cliente(),
        origem=origem_da_requisicao(),
    )


def _garantir_dados_da_conta(conta) -> None:
    """Adota os dados anteriores quando a conta e a declarada; avisa quando nao e."""
    servico = _servico()
    borda = current_app.extensions["analisador"]
    pasta = borda.get("pasta_de_uploads")
    configuracao = servico.configuracao

    if conta.email.casefold() == configuracao.dono_inicial.casefold():
        try:
            garantir_dados_do_dono(pasta, conta.sub, borda.get("registro"))
        except Exception:
            current_app.logger.exception("falha ao adotar os dados anteriores")
        return

    if ha_dados_nao_atribuidos(pasta):
        # Sem e-mail na linha: o log identifica pelo `sub`, e o e-mail e dado pessoal.
        current_app.logger.warning(
            "ha dados anteriores sem dono; a conta %s nao e a declarada em "
            "ANALISADOR_DONO_INICIAL",
            conta.sub,
        )


__all__: list[str] = ["auth_bp", "ENTRADA_CANCELADA", "ENTRADA_EXPIRADA", "ENTRADA_FALHOU"]
