"""Conta de acesso, politica de senha e credencial (feature 053).

## O que mora aqui, e por que aqui

Identidade e **regra de negocio**, nao HTTP: a politica de senha (`RN-02`), a
derivacao da credencial (`RN-04`) e o valor que representa uma conta. O pacote
`core/` continua sem Flask, sem banco e sem SMTP (`ADR-24`, `ADR-25`), e este
modulo nao abre arquivo nem le ambiente.

## A politica tem autoridade unica

`PoliticaDeSenha` e o unico lugar que sabe o que e senha aceitavel. A tela mostra
a mesma frase da `RN-02`, e a rota nao reimplementa a checagem: ela chama
`exigir` e traduz a excecao. O projeto ja pagou caro por duas copias da mesma
regra (autoridade unica de limpeza de nome, `ADR-07`).

## A credencial guarda os parametros junto do hash

`Credencial` carrega algoritmo, `n`, `r`, `p`, sal e hash. Guardar os parametros
permite endurecer o custo depois sem invalidar contas antigas: a verificacao usa
os parametros **daquela** credencial, e nao os do codigo de hoje.

## Senha com acento conta, e conta como caractere

A contagem e `len` sobre a string, e a comparacao e sobre os bytes UTF-8. Senha
de 8 caracteres acentuados tem 8 caracteres e 16 bytes; o limite e de caracteres,
como a `RN-02` declara.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass, replace

ALGORITMO = "scrypt"

#: Limites da `RN-02`.
TAMANHO_MINIMO = 8
TAMANHO_MAXIMO = 128

TAMANHO_DO_SAL = 16
TAMANHO_DO_HASH = 32

FALTA_TAMANHO = "tamanho"
FALTA_MINUSCULA = "minuscula"
FALTA_MAIUSCULA = "maiuscula"
FALTA_NUMERO = "numero"
FALTA_ESPECIAL = "especial"


class ErroDeConta(ValueError):
    """Raiz das condicoes de negocio da identidade local."""


class ContaDuplicada(ErroDeConta):
    """O e-mail normalizado ou o `google_sub` ja pertence a outra conta."""


class ContaNaoEncontrada(ErroDeConta):
    """Nao existe conta para o identificador informado."""


class SenhaForaDaPolitica(ErroDeConta):
    """A senha nao atende a `RN-02`. Carrega a lista do que falta."""

    def __init__(self, faltas) -> None:
        self.faltas: tuple[str, ...] = tuple(faltas)
        super().__init__(",".join(self.faltas))


class SenhasDiferentes(ErroDeConta):
    """A repeticao nao confere com a senha digitada."""


class SenhaJaDefinida(ErroDeConta):
    """A conta ja tem credencial; esta entrega nao troca senha pela tela autenticada."""


@dataclass(frozen=True)
class ParametrosDeDerivacao:
    """Custo da derivacao. O padrao e o de producao; o teste injeta um barato."""

    n: int = 2 ** 14
    r: int = 8
    p: int = 1


@dataclass(frozen=True)
class ResultadoDaPolitica:
    """O que falta para a senha ser aceita, em codigos estaveis e sem a senha."""

    faltas: tuple[str, ...]

    @property
    def atendida(self) -> bool:
        return not self.faltas


def _e_especial(caractere: str) -> bool:
    """Simbolo ASCII imprimivel que nao e letra nem digito; espaco nao conta."""
    return (
        caractere.isascii()
        and caractere.isprintable()
        and not caractere.isalnum()
        and caractere != " "
    )


class PoliticaDeSenha:
    """A autoridade unica da `RN-02`.

    Instancia sem estado: existe como classe para ser injetada e substituida em
    teste, e para o nome carregar a responsabilidade.
    """

    def avaliar(self, senha: str) -> ResultadoDaPolitica:
        faltas: list[str] = []
        if len(senha) < TAMANHO_MINIMO or len(senha) > TAMANHO_MAXIMO:
            faltas.append(FALTA_TAMANHO)
        if not any(c.islower() for c in senha):
            faltas.append(FALTA_MINUSCULA)
        if not any(c.isupper() for c in senha):
            faltas.append(FALTA_MAIUSCULA)
        if not any(c.isdigit() for c in senha):
            faltas.append(FALTA_NUMERO)
        if not any(_e_especial(c) for c in senha):
            faltas.append(FALTA_ESPECIAL)
        return ResultadoDaPolitica(tuple(faltas))

    def exigir(self, senha: str) -> None:
        """Levanta `SenhaForaDaPolitica` quando a senha nao atende."""
        resultado: ResultadoDaPolitica = self.avaliar(senha)
        if resultado.faltas:
            raise SenhaForaDaPolitica(resultado.faltas)


@dataclass(frozen=True)
class Credencial:
    """A derivacao da senha, com sal e parametros, pronta para ser gravada.

    Nao existe senha em claro neste tipo, e nao existe metodo que a devolva.
    """

    algoritmo: str
    n: int
    r: int
    p: int
    sal: str
    hash: str

    def para_dicionario(self) -> dict:
        return {
            "algoritmo": self.algoritmo,
            "n": self.n,
            "r": self.r,
            "p": self.p,
            "sal": self.sal,
            "hash": self.hash,
        }

    @classmethod
    def de_dicionario(cls, dados: dict) -> "Credencial":
        try:
            return cls(
                algoritmo=str(dados["algoritmo"]),
                n=int(dados["n"]),
                r=int(dados["r"]),
                p=int(dados["p"]),
                sal=str(dados["sal"]),
                hash=str(dados["hash"]),
            )
        except (KeyError, TypeError, ValueError) as erro:
            raise ValueError("credencial incompleta no armazenamento") from erro


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def _de_b64(texto: str) -> bytes:
    return base64.b64decode(texto.encode("ascii"))


def derivar_senha(
    senha: str,
    *,
    parametros: ParametrosDeDerivacao | None = None,
    sal: bytes | None = None,
) -> Credencial:
    """Deriva a senha com scrypt. `sal` existe para o teste ser deterministico."""
    efetivos: ParametrosDeDerivacao = parametros or ParametrosDeDerivacao()
    sal_bytes: bytes = sal if sal is not None else secrets.token_bytes(TAMANHO_DO_SAL)
    derivado: bytes = hashlib.scrypt(
        senha.encode("utf-8"),
        salt=sal_bytes,
        n=efetivos.n,
        r=efetivos.r,
        p=efetivos.p,
        dklen=TAMANHO_DO_HASH,
    )
    return Credencial(
        algoritmo=ALGORITMO,
        n=efetivos.n,
        r=efetivos.r,
        p=efetivos.p,
        sal=_b64(sal_bytes),
        hash=_b64(derivado),
    )


def conferir_senha(senha: str, credencial: Credencial | None) -> bool:
    """Compara em tempo constante. Credencial ausente ou estranha devolve `False`."""
    if credencial is None or credencial.algoritmo != ALGORITMO:
        return False
    try:
        sal: bytes = _de_b64(credencial.sal)
        esperado: bytes = _de_b64(credencial.hash)
    except (ValueError, TypeError):
        return False
    try:
        derivado: bytes = hashlib.scrypt(
            senha.encode("utf-8"),
            salt=sal,
            n=credencial.n,
            r=credencial.r,
            p=credencial.p,
            dklen=len(esperado),
        )
    except ValueError:
        # Parametros fora da faixa que o proprio hashlib aceita: credencial invalida.
        return False
    return hmac.compare_digest(derivado, esperado)


def credencial_falsa(parametros: ParametrosDeDerivacao | None = None) -> Credencial:
    """Credencial de custo igual, para o caminho de e-mail inexistente.

    Sem ela, a resposta sai rapido quando o e-mail nao existe e devagar quando
    existe — o tempo passa a ser um oraculo de contas (`RN-05`).
    """
    return derivar_senha(secrets.token_urlsafe(32), parametros=parametros)


def normalizar_email(email: str) -> str:
    """Aparar espaços e baixar a caixa. E a chave de busca da conta."""
    return (email or "").strip().casefold()


def novo_sub() -> str:
    """Identificador opaco e estavel do dono local, seguro como nome de pasta."""
    return "local-" + secrets.token_hex(16)


@dataclass(frozen=True)
class ContaDeAcesso:
    """O registro da conta. Congelado: mudar conta e `replace` mais `salvar`."""

    sub: str
    email: str
    email_normalizado: str
    credencial: Credencial | None = None
    google_sub: str | None = None
    nome: str = ""
    #: Instante ISO 8601 da confirmacao do e-mail; `None` = conta nao confirmada.
    verificado_em: str | None = None
    criado_em: str = ""
    versao_de_credencial: int = 0
    token_confirmacao: str | None = None
    token_redefinicao: str | None = None

    @property
    def confirmada(self) -> bool:
        return self.verificado_em is not None

    @property
    def tem_senha(self) -> bool:
        return self.credencial is not None

    def confirmar(self, agora_iso: str) -> "ContaDeAcesso":
        return replace(self, verificado_em=agora_iso)

    def com_credencial(self, credencial: Credencial) -> "ContaDeAcesso":
        return replace(self, credencial=credencial)

    def com_versao_incrementada(self) -> "ContaDeAcesso":
        return replace(self, versao_de_credencial=self.versao_de_credencial + 1)

    def para_dicionario(self) -> dict:
        return {
            "sub": self.sub,
            "email": self.email,
            "email_normalizado": self.email_normalizado,
            "credencial": self.credencial.para_dicionario() if self.credencial else None,
            "google_sub": self.google_sub,
            "nome": self.nome,
            "verificado_em": self.verificado_em,
            "criado_em": self.criado_em,
            "versao_de_credencial": self.versao_de_credencial,
            "token_confirmacao": self.token_confirmacao,
            "token_redefinicao": self.token_redefinicao,
        }

    @classmethod
    def de_dicionario(cls, dados: dict) -> "ContaDeAcesso":
        credencial = dados.get("credencial")
        return cls(
            sub=str(dados["sub"]),
            email=str(dados.get("email") or ""),
            email_normalizado=str(dados["email_normalizado"]),
            credencial=Credencial.de_dicionario(credencial) if credencial else None,
            google_sub=(str(dados["google_sub"]) if dados.get("google_sub") else None),
            nome=str(dados.get("nome") or ""),
            verificado_em=dados.get("verificado_em"),
            criado_em=str(dados.get("criado_em") or ""),
            versao_de_credencial=int(dados.get("versao_de_credencial") or 0),
            token_confirmacao=dados.get("token_confirmacao"),
            token_redefinicao=dados.get("token_redefinicao"),
        )


__all__: list[str] = [
    "ALGORITMO",
    "ContaDeAcesso",
    "ContaDuplicada",
    "ContaNaoEncontrada",
    "Credencial",
    "ErroDeConta",
    "FALTA_ESPECIAL",
    "FALTA_MAIUSCULA",
    "FALTA_MINUSCULA",
    "FALTA_NUMERO",
    "FALTA_TAMANHO",
    "ParametrosDeDerivacao",
    "PoliticaDeSenha",
    "ResultadoDaPolitica",
    "SenhaForaDaPolitica",
    "SenhaJaDefinida",
    "SenhasDiferentes",
    "TAMANHO_MAXIMO",
    "TAMANHO_MINIMO",
    "conferir_senha",
    "credencial_falsa",
    "derivar_senha",
    "normalizar_email",
    "novo_sub",
]
