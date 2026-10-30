"""Literais da identidade local (feature 053, `RN-13`).

## Por que um modulo de texto, e nao strings espalhadas

Texto de tela e **contrato**: o teste prende o literal, o harness de paridade
compara a tela, e a `RN-13` lista cada frase. Espalhar as mesmas frases por tres
rotas e cinco templates faria a troca de uma virar cinco. O projeto ja usa esse
padrao em `rotas_auth.py` (`ENTRADA_CANCELADA` etc.).

## O que NAO mora aqui

Os 36 literais anteriores (29 da extracao + 7 da 051) continuam nas rotas e no
proprio template da tela principal; este modulo so acrescenta os novos.
"""
from __future__ import annotations

TITULO_ENTRADA = "Entre na sua conta"
TITULO_CADASTRO = "Crie sua conta"
TITULO_RECUPERAR = "Recupere sua senha"
TITULO_REDEFINIR = "Defina uma nova senha"
TITULO_DEFINIR = "Definir senha"

BOTAO_ENTRAR = "Entrar"
BOTAO_GOOGLE = "Entrar com Google"
BOTAO_CADASTRAR = "Criar conta"
BOTAO_SOLICITAR = "Solicitar instruções"
BOTAO_REENVIAR = "Reenviar o link de confirmação"
BOTAO_DEFINIR = "Definir senha"
BOTAO_VOLTAR = "Voltar para entrar"

LINK_ESQUECI = "Esqueci minha senha"
LINK_CRIAR = "Criar conta"
LINK_VOLTAR = "Voltar para entrar"

ROTULO_EMAIL = "E-mail"
ROTULO_SENHA = "Senha"
ROTULO_REPETICAO = "Repita a senha"

#: A frase da politica, exatamente como a `RN-02` a define.
POLITICA = (
    "A senha precisa ter ao menos 8 caracteres, com maiúscula, minúscula, "
    "número e caractere especial."
)

ENTRADA_INVALIDA = "E-mail ou senha inválidos."
ENTRADA_NAO_CONFIRMADA = (
    "Confirme seu e-mail para entrar. Enviamos um link para o endereço informado."
)

#: A frase do cadastro e do reenvio: identica exista ou nao conta.
CADASTRO_GENERICO = "Se este e-mail puder ser usado, enviaremos as instruções."

EMAIL_CONFIRMADO = "E-mail confirmado. Entre com a sua senha."
CONFIRMACAO_INVALIDA = "Este link de confirmação expirou ou já foi usado. Peça outro."

RECUPERACAO_GENERICA = "Se este e-mail estiver cadastrado, enviaremos as instruções."
ENVIO_INDISPONIVEL = "O envio de e-mail não está configurado nesta instalação."

REDEFINICAO_INVALIDA = "Este link expirou ou já foi usado. Peça outro."
SENHA_ALTERADA = "Senha alterada. Entre com a nova senha."

DEFINIR_DICA = "Defina uma senha para entrar sem depender do Google."
SENHA_DEFINIDA = "Senha definida. Você já pode entrar com e-mail e senha."
CONTA_JA_TEM_SENHA = "Sua conta já tem senha."

GOOGLE_RECUPERACAO = (
    "Se você entra apenas com Google, recupere o acesso na sua conta Google."
)

SENHAS_DIFERENTES = "As senhas não conferem."
EMAIL_INVALIDO = "Informe um e-mail válido."
ORIGEM_RECUSADA = "Não foi possível concluir a operação agora."

#: Falha de armazenamento (permissão, disco, arquivo corrompido). Nao e erro de
#: negocio e nao pode virar 500: a tela pede para tentar de novo e o log guarda a causa.
ARMAZENAMENTO_INDISPONIVEL = "Não foi possível concluir agora. Tente de novo em instantes."

#: Como cada codigo de falta da politica e nomeado para o operador.
_PALAVRAS_DAS_FALTAS: dict[str, str] = {
    "tamanho": "no mínimo 8 e no máximo 128 caracteres",
    "minuscula": "uma letra minúscula",
    "maiuscula": "uma letra maiúscula",
    "numero": "um número",
    "especial": "um caractere especial",
}


def texto_da_politica(faltas) -> str:
    """A frase da politica com o que falta, sem repetir a senha digitada."""
    if not faltas:
        return POLITICA
    partes = [_PALAVRAS_DAS_FALTAS.get(codigo, codigo) for codigo in faltas]
    return f"{POLITICA} Falta: {', '.join(partes)}."


__all__: list[str] = [
    "BOTAO_CADASTRAR",
    "BOTAO_DEFINIR",
    "BOTAO_ENTRAR",
    "BOTAO_GOOGLE",
    "BOTAO_REENVIAR",
    "BOTAO_SOLICITAR",
    "BOTAO_VOLTAR",
    "ARMAZENAMENTO_INDISPONIVEL",
    "CADASTRO_GENERICO",
    "CONFIRMACAO_INVALIDA",
    "CONTA_JA_TEM_SENHA",
    "DEFINIR_DICA",
    "EMAIL_CONFIRMADO",
    "EMAIL_INVALIDO",
    "ENTRADA_INVALIDA",
    "ENTRADA_NAO_CONFIRMADA",
    "ENVIO_INDISPONIVEL",
    "GOOGLE_RECUPERACAO",
    "LINK_CRIAR",
    "LINK_ESQUECI",
    "LINK_VOLTAR",
    "ORIGEM_RECUSADA",
    "POLITICA",
    "RECUPERACAO_GENERICA",
    "REDEFINICAO_INVALIDA",
    "ROTULO_EMAIL",
    "ROTULO_REPETICAO",
    "ROTULO_SENHA",
    "SENHAS_DIFERENTES",
    "SENHA_ALTERADA",
    "SENHA_DEFINIDA",
    "TITULO_CADASTRO",
    "TITULO_DEFINIR",
    "TITULO_ENTRADA",
    "TITULO_RECUPERAR",
    "TITULO_REDEFINIR",
    "texto_da_politica",
]
