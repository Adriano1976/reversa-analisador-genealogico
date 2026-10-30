"""As rotas da entrada: `/login`, `/callback` e `/logout` (features 051 e 053).

## O que mora aqui

So a cola HTTP do fluxo: ler parametros, chamar o servico de entrada, gravar a
sessao e escolher a resposta. A troca do codigo e a leitura do perfil ficam em
`web/autenticacao.py`; a credencial local, em `application/entrada_com_senha.py`;
a sessao e a guarda, em `web/sessao.py`; a adocao dos dados anteriores, em
`application/dono_inicial.py`.

## Dois caminhos no mesmo cartao (feature 053)

`GET /login` mostra o cartao com o botao do Google e o formulario de e-mail e
senha. `GET /login?iniciar=1` inicia o OAuth; `POST /login` autentica a credencial
local. O caminho Google continua byte a byte o da 051, com uma diferenca interna:
o callback passa pelo vinculo de identidade antes de gravar a sessao (`RN-20`), e
falha do vinculo **nao** impede a entrada.

## As frases de falha

As tres do Google continuam as da 051. A entrada local usa duas: a generica
(`E-mail ou senha inválidos.`) e a de conta nao confirmada, que so aparece depois
de a senha conferir (`RN-05`).
"""

from __future__ import annotations
from werkzeug.wrappers.response import Response
from typing import Literal

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
from application.entrada_com_senha import CredenciaisInvalidas, EmailNaoConfirmado
from application.limite import LimiteExcedido
from ports.contas_em_arquivo import ArquivoDeContasCorrompido
from utils.auditoria import registrar as auditar
from web.autenticacao import ErroDeEntrada
from web.hooks_de_registro import ip_do_cliente, origem_da_requisicao
from web.origem import veio_de_fora
from web.sessao import (
    CHAVE_DO_STATE,
    Conta,
    conta_atual,
    encerrar_sessao,
    guardar_conta,
)
from web.textos_de_conta import (
    ARMAZENAMENTO_INDISPONIVEL,
    ENTRADA_INVALIDA,
    ENTRADA_NAO_CONFIRMADA,
    ORIGEM_RECUSADA,
)

auth_bp = Blueprint("auth", __name__)

#: Literais de tela da entrada Google. Congelados por teste desde a 051.
ENTRADA_CANCELADA = "A entrada foi cancelada."
ENTRADA_EXPIRADA = "A entrada expirou. Tente de novo."
ENTRADA_FALHOU = "Não foi possível concluir a entrada agora."


def _servico():
    return current_app.extensions["analisador"]["autenticacao"]


def _contas(nome: str):
    return current_app.extensions["analisador"][nome]


def _tela(mensagem: str | None = None, **extra) -> tuple[str, Literal[200]]:
    return render_template("login.html", message=mensagem, success=False, **extra), 200


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Response | tuple[str, Literal[200]] | tuple[str, Literal[400]]:
    """Mostra a tela de entrada, comeca o fluxo do Google ou autentica a senha."""
    if conta_atual() is not None:
        return redirect(url_for("index"))
    if request.method == "POST":
        return _entrar_com_senha()
    if request.args.get("iniciar"):
        servico = _servico()
        state = servico.provedor.novo_state()
        session[CHAVE_DO_STATE] = state
        return redirect(servico.provedor.url_de_autorizacao(state))
    return _tela()


def _entrar_com_senha() -> Response | tuple[str, Literal[200]] | tuple[str, Literal[400]]:
    """Autentica a credencial local e abre a sessao, ou explica a falha generica."""
    if veio_de_fora():
        return _tela(ORIGEM_RECUSADA)[0], 400
    email: str = request.form.get("email", "")
    senha: str = request.form.get("senha", "")
    try:
        registro = _contas("entrada_local").autenticar(
            email, senha, origem=ip_do_cliente()
        )
    except EmailNaoConfirmado:
        _auditar_falha()
        return _tela(ENTRADA_NAO_CONFIRMADA, mostrar_reenvio=True)
    except (CredenciaisInvalidas, LimiteExcedido):
        _auditar_falha()
        return _tela(ENTRADA_INVALIDA)
    except (OSError, ArquivoDeContasCorrompido):
        # Pasta de contas sem permissao, disco cheio ou arquivo corrompido: a tela
        # pede para tentar de novo e o log guarda a causa, sem 500.
        current_app.logger.exception("falha de armazenamento na entrada local")
        _auditar_falha()
        return _tela(ARMAZENAMENTO_INDISPONIVEL)

    conta = Conta(
        sub=registro.sub,
        email=registro.email,
        nome=registro.nome,
        versao=registro.versao_de_credencial,
    )
    guardar_conta(conta)
    _garantir_dados_da_conta(conta)
    auditar(
        "entrar",
        "sucesso",
        conta=conta.sub,
        ip=ip_do_cliente(),
        origem=origem_da_requisicao(),
    )
    return redirect(url_for("index"), code=303)


@auth_bp.route("/callback", methods=["GET"])
def callback() -> Response | tuple[str, Literal[200]] | tuple[str, Literal[400]]:
    """Recebe o retorno do provedor, vincula a identidade e abre a sessao."""
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
        conta_google = servico.entrar(codigo)
    except ErroDeEntrada as erro:
        current_app.logger.warning("entrada recusada: %s", erro.motivo)
        _auditar_falha()
        return _tela(ENTRADA_FALHOU)

    conta: Conta = _vincular_identidade(conta_google)
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


def _vincular_identidade(conta_google: Conta) -> Conta:
    """Aplica o vinculo por e-mail verificado; falha nao impede a entrada.

    A escrita no arquivo de contas e beneficio, nunca condicao: se o repositorio
    estiver indisponivel, o login Google segue com o `sub` do provedor, que e o
    comportamento da 051 (`RN-20`).
    """
    try:
        registro = _contas("vinculo").ao_entrar_com_google(
            conta_google.sub, conta_google.email, conta_google.nome
        )
    except Exception:
        current_app.logger.exception("vinculo de identidade falhou")
        return conta_google
    return Conta(
        sub=registro.sub,
        email=registro.email or conta_google.email,
        nome=conta_google.nome or registro.nome,
        versao=registro.versao_de_credencial,
    )


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Response | tuple[str, Literal[200]]:
    """Encerra a sessao. Idempotente: sem sessao, tambem devolve a entrada."""
    conta: Conta | None = conta_atual()
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
