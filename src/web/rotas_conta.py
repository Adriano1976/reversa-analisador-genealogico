"""Rotas da identidade local: cadastro, confirmacao, recuperacao e senha.

## O que mora aqui

So a cola HTTP: ler formulario, chamar o caso de uso, traduzir a excecao de
dominio no literal e escolher a resposta. Nenhuma regra de senha, token ou
armazenamento e decidida nesta camada (`RNF-03`).

## As duas frases genericas sao o contrato

Cadastro e reenvio respondem sempre `Se este e-mail puder ser usado...`;
recuperacao responde sempre `Se este e-mail estiver cadastrado...`. A diferenca
entre conta existente e inexistente viaja **so** por e-mail (`RN-07`).

## Cabecalhos

Toda resposta de identidade leva `no-store` — inclusive as anonimas, que a guarda
da 051 nao cobre. As paginas com token na URL levam tambem `no-referrer`: o link
do e-mail nao pode vazar para terceiros pelo `Referer`.

## Falha de armazenamento nao e 500

Permissao negada, disco cheio ou arquivo corrompido viram mensagem na tela e
linha de log com traceback. O `500` cru apareceu uma vez em uso real — pasta de
contas sem permissao de escrita — e nao e resposta aceitavel para uma condicao
operacional que o operador consegue resolver.
"""
from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.wrappers import Response

from application.cadastro import EmailInvalido
from application.limite import LimiteExcedido
from application.recuperacao import TokenInvalido
from core.conta import (
    ContaNaoEncontrada,
    SenhaForaDaPolitica,
    SenhaJaDefinida,
    SenhasDiferentes,
)
from ports.contas_em_arquivo import ArquivoDeContasCorrompido
from ports.email_smtp import EnvioNaoConfigurado
from utils.auditoria import registrar as auditar
from web.hooks_de_registro import ip_do_cliente, origem_da_requisicao
from web.origem import veio_de_fora
from web.sessao import conta_atual, encerrar_sessao
from web.textos_de_conta import (
    ARMAZENAMENTO_INDISPONIVEL,
    BOTAO_ENTRAR,
    BOTAO_VOLTAR,
    CADASTRO_GENERICO,
    CONFIRMACAO_INVALIDA,
    CONTA_JA_TEM_SENHA,
    DEFINIR_DICA,
    EMAIL_CONFIRMADO,
    EMAIL_INVALIDO,
    ENVIO_INDISPONIVEL,
    GOOGLE_RECUPERACAO,
    ORIGEM_RECUSADA,
    POLITICA,
    RECUPERACAO_GENERICA,
    REDEFINICAO_INVALIDA,
    SENHAS_DIFERENTES,
    SENHA_ALTERADA,
    SENHA_DEFINIDA,
    TITULO_CADASTRO,
    TITULO_DEFINIR,
    TITULO_ENTRADA,
    TITULO_RECUPERAR,
    TITULO_REDEFINIR,
    texto_da_politica,
)

conta_bp = Blueprint("conta", __name__)


# --------------------------------------------------------------------- apoio
def _ext(nome: str):
    return current_app.extensions["analisador"][nome]


def _auditar(acao: str, desfecho: str, conta=None) -> None:
    auditar(
        acao,
        desfecho,
        conta=(getattr(conta, "sub", None) if conta is not None else None),
        ip=ip_do_cliente(),
        origem=origem_da_requisicao(),
    )


#: Falhas de armazenamento que NAO podem virar 500: permissao, disco, arquivo
#: corrompido. O erro de negocio tem tipo proprio e e tratado antes destas.
_FALHAS_DE_ARMAZENAMENTO = (OSError, ArquivoDeContasCorrompido)


def _registrar_falha_de_armazenamento() -> None:
    """Loga a causa com traceback, sem dado pessoal, e devolve o controle a rota."""
    current_app.logger.exception("falha de armazenamento na identidade local")


def _responder(conteudo: str, status: int = 200, *, sem_referencia: bool = False):
    resposta: Response = make_response(conteudo, status)
    resposta.headers["Cache-Control"] = "no-store"
    if sem_referencia:
        resposta.headers["Referrer-Policy"] = "no-referrer"
    return resposta


def _pagina(modelo: str, *, sem_referencia: bool = False, **contexto):
    return _responder(
        render_template(modelo, **contexto), 200, sem_referencia=sem_referencia
    )


# ------------------------------------------------------------------- cadastro
@conta_bp.route("/cadastro", methods=["GET", "POST"])
def cadastrar() -> Response:
    if request.method == "GET":
        return _pagina("cadastro.html", politica=POLITICA)
    if veio_de_fora():
        return _responder(
            render_template("cadastro.html", politica=POLITICA, message=ORIGEM_RECUSADA), 400
        )
    email: str = request.form.get("email", "")
    senha: str = request.form.get("senha", "")
    repeticao: str = request.form.get("repeticao", "")
    try:
        _ext("cadastro").cadastrar(email, senha, repeticao, origem=ip_do_cliente())
    except SenhaForaDaPolitica as erro:
        _auditar("cadastrar", "falha")
        return _pagina(
            "cadastro.html",
            politica=POLITICA,
            message=texto_da_politica(erro.faltas),
            email=email,
        )
    except SenhasDiferentes:
        _auditar("cadastrar", "falha")
        return _pagina("cadastro.html", politica=POLITICA, message=SENHAS_DIFERENTES, email=email)
    except EmailInvalido:
        _auditar("cadastrar", "falha")
        return _pagina("cadastro.html", politica=POLITICA, message=EMAIL_INVALIDO, email=email)
    except LimiteExcedido:
        _auditar("cadastrar", "falha")
        return _pagina("cadastro.html", politica=POLITICA, message=CADASTRO_GENERICO, email=email)
    except EnvioNaoConfigurado:
        return _pagina("cadastro.html", politica=POLITICA, message=ENVIO_INDISPONIVEL, email=email)
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        _auditar("cadastrar", "falha")
        return _pagina(
            "cadastro.html",
            politica=POLITICA,
            message=ARMAZENAMENTO_INDISPONIVEL,
            email=email,
        )
    _auditar("cadastrar", "sucesso")
    return _pagina(
        "mensagem.html",
        titulo=TITULO_CADASTRO,
        mensagem=CADASTRO_GENERICO,
        link=url_for("auth.login"),
        link_texto=BOTAO_VOLTAR,
    )


@conta_bp.route("/confirmar", methods=["GET"])
def confirmar() -> Response:
    token: str = request.args.get("token", "")
    try:
        conta = _ext("cadastro").confirmar(token)
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        _auditar("confirmar", "falha")
        return _pagina(
            "mensagem.html",
            sem_referencia=True,
            titulo=TITULO_ENTRADA,
            mensagem=ARMAZENAMENTO_INDISPONIVEL,
            link=url_for("auth.login"),
            link_texto=BOTAO_ENTRAR,
        )
    if conta is not None:
        _auditar("confirmar", "sucesso", conta)
        return _pagina(
            "mensagem.html",
            sem_referencia=True,
            titulo=TITULO_ENTRADA,
            mensagem=EMAIL_CONFIRMADO,
            link=url_for("auth.login"),
            link_texto=BOTAO_ENTRAR,
        )
    _auditar("confirmar", "falha")
    return _pagina(
        "mensagem.html",
        sem_referencia=True,
        titulo=TITULO_ENTRADA,
        mensagem=CONFIRMACAO_INVALIDA,
        mostrar_reenvio=True,
        link=url_for("auth.login"),
        link_texto=BOTAO_ENTRAR,
    )


@conta_bp.route("/reenviar-confirmacao", methods=["POST"])
def reenviar() -> Response:
    if veio_de_fora():
        return _responder(
            render_template("mensagem.html", titulo=TITULO_ENTRADA, mensagem=CADASTRO_GENERICO), 400
        )
    email: str = request.form.get("email", "")
    mensagem: str = CADASTRO_GENERICO
    try:
        _ext("cadastro").reenviar_confirmacao(email)
    except EnvioNaoConfigurado:
        mensagem = ENVIO_INDISPONIVEL
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        mensagem = ARMAZENAMENTO_INDISPONIVEL
    except (LimiteExcedido, EmailInvalido):
        pass
    _auditar("confirmar", "sucesso" if mensagem == CADASTRO_GENERICO else "falha")
    return _pagina(
        "mensagem.html",
        titulo=TITULO_ENTRADA,
        mensagem=mensagem,
        link=url_for("auth.login"),
        link_texto=BOTAO_ENTRAR,
    )


# ------------------------------------------------------------------ recuperar
@conta_bp.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar() -> Response:
    if request.method == "GET":
        return _pagina("recuperar_senha.html", google=GOOGLE_RECUPERACAO)
    if veio_de_fora():
        return _responder(
            render_template(
                "recuperar_senha.html", google=GOOGLE_RECUPERACAO, message=ORIGEM_RECUSADA
            ),
            400,
        )
    email: str = request.form.get("email", "")
    try:
        _ext("recuperacao").pedir(email)
        mensagem = RECUPERACAO_GENERICA
        _auditar("pedir_senha", "sucesso")
    except EnvioNaoConfigurado:
        mensagem = ENVIO_INDISPONIVEL
        _auditar("pedir_senha", "falha")
    except LimiteExcedido:
        mensagem = RECUPERACAO_GENERICA
        _auditar("pedir_senha", "falha")
    except EmailInvalido:
        return _pagina("recuperar_senha.html", google=GOOGLE_RECUPERACAO, message=EMAIL_INVALIDO)
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        mensagem = ARMAZENAMENTO_INDISPONIVEL
        _auditar("pedir_senha", "falha")
    return _pagina(
        "mensagem.html",
        titulo=TITULO_RECUPERAR,
        mensagem=mensagem,
        link=url_for("auth.login"),
        link_texto=BOTAO_VOLTAR,
    )


# ------------------------------------------------------------------ redefinir
@conta_bp.route("/redefinir-senha", methods=["GET", "POST"])
def redefinir():
    servico = _ext("recuperacao")
    if request.method == "GET":
        token: str = request.args.get("token", "")
        try:
            link_valido = servico.link_valido(token)
        except _FALHAS_DE_ARMAZENAMENTO:
            _registrar_falha_de_armazenamento()
            return _pagina(
                "mensagem.html",
                sem_referencia=True,
                titulo=TITULO_REDEFINIR,
                mensagem=ARMAZENAMENTO_INDISPONIVEL,
                link=url_for("auth.login"),
                link_texto=BOTAO_VOLTAR,
            )
        if not link_valido:
            return _pagina(
                "mensagem.html",
                sem_referencia=True,
                titulo=TITULO_REDEFINIR,
                mensagem=REDEFINICAO_INVALIDA,
                link=url_for("conta.recuperar"),
                link_texto="Pedir outro link",
            )
        return _pagina("redefinir_senha.html", token=token, politica=POLITICA)

    if veio_de_fora():
        return _responder(
            render_template("mensagem.html", titulo=TITULO_REDEFINIR, mensagem=ORIGEM_RECUSADA), 400
        )
    token = request.form.get("token", "")
    senha: str = request.form.get("senha", "")
    repeticao: str = request.form.get("repeticao", "")
    try:
        servico.redefinir(token, senha, repeticao)
    except SenhaForaDaPolitica as erro:
        _auditar("redefinir_senha", "falha")
        return _pagina(
            "redefinir_senha.html", token=token, politica=POLITICA,
            message=texto_da_politica(erro.faltas),
        )
    except SenhasDiferentes:
        _auditar("redefinir_senha", "falha")
        return _pagina(
            "redefinir_senha.html", token=token, politica=POLITICA, message=SENHAS_DIFERENTES
        )
    except TokenInvalido:
        _auditar("redefinir_senha", "falha")
        return _pagina(
            "mensagem.html",
            sem_referencia=True,
            titulo=TITULO_REDEFINIR,
            mensagem=REDEFINICAO_INVALIDA,
            link=url_for("conta.recuperar"),
            link_texto="Pedir outro link",
        )
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        _auditar("redefinir_senha", "falha")
        return _pagina(
            "mensagem.html",
            sem_referencia=True,
            titulo=TITULO_REDEFINIR,
            mensagem=ARMAZENAMENTO_INDISPONIVEL,
            link=url_for("auth.login"),
            link_texto=BOTAO_VOLTAR,
        )
    _auditar("redefinir_senha", "sucesso")
    encerrar_sessao()
    flash(SENHA_ALTERADA)
    return redirect(url_for("auth.login"), code=303)


# -------------------------------------------------------------------- definir
@conta_bp.route("/definir-senha", methods=["GET", "POST"])
def definir():
    conta = conta_atual()
    if conta is None:
        return redirect(url_for("auth.login"))
    servico = _ext("definir_senha")
    if request.method == "GET":
        try:
            ja_tem = servico.ja_tem_senha(conta.sub)
        except _FALHAS_DE_ARMAZENAMENTO:
            _registrar_falha_de_armazenamento()
            return _pagina(
                "mensagem.html",
                titulo=TITULO_DEFINIR,
                mensagem=ARMAZENAMENTO_INDISPONIVEL,
                link=url_for("index"),
                link_texto="Voltar para a tela principal",
            )
        if ja_tem:
            flash(CONTA_JA_TEM_SENHA)
            return redirect(url_for("index"))
        return _pagina("definir_senha.html", dica=DEFINIR_DICA, politica=POLITICA)
    if veio_de_fora():
        return _responder(
            render_template("definir_senha.html", dica=DEFINIR_DICA, politica=POLITICA,
                            message=ORIGEM_RECUSADA),
            400,
        )
    senha: str = request.form.get("senha", "")
    repeticao: str = request.form.get("repeticao", "")
    try:
        servico.definir(conta.sub, senha, repeticao)
    except SenhaForaDaPolitica as erro:
        _auditar("definir_senha", "falha", conta)
        return _pagina(
            "definir_senha.html", dica=DEFINIR_DICA, politica=POLITICA,
            message=texto_da_politica(erro.faltas),
        )
    except SenhasDiferentes:
        _auditar("definir_senha", "falha", conta)
        return _pagina(
            "definir_senha.html", dica=DEFINIR_DICA, politica=POLITICA,
            message=SENHAS_DIFERENTES,
        )
    except (ContaNaoEncontrada, SenhaJaDefinida):
        # Conta sumiu ou ja tinha senha: o ato nao se aplica mais.
        _auditar("definir_senha", "falha", conta)
        flash(CONTA_JA_TEM_SENHA)
        return redirect(url_for("index"))
    except _FALHAS_DE_ARMAZENAMENTO:
        _registrar_falha_de_armazenamento()
        _auditar("definir_senha", "falha", conta)
        return _pagina(
            "definir_senha.html", dica=DEFINIR_DICA, politica=POLITICA,
            message=ARMAZENAMENTO_INDISPONIVEL,
        )
    _auditar("definir_senha", "sucesso", conta)
    flash(SENHA_DEFINIDA)
    return redirect(url_for("index"), code=303)


__all__: list[str] = ["conta_bp"]
