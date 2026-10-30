"""Adaptador de contas em arquivo JSON (feature 053, `D-06`).

## Por que arquivo, e nao SQLite nem Postgres

O `requirements.md` decidiu arquivo local (`D2`), e o `roadmap.md` fixou o motivo:
o Postgres e opcional e o driver **nao esta no `.venv`** (`L-26`), entao uma conta
que so existisse la nao entraria no ambiente oficial. SQLite resolveria
concorrencia e atomicidade, mas exige esquema e um runner de migracao que o
projeto nao tem; o documento JSON cabe na memoria com folga na escala de dezenas
de contas (`data-delta.md` §9).

## O que garante a integridade

1. **Trava unica** (`RLock`) em torno de toda leitura-para-escrita: o processo
   atende em quatro threads (`ANALISADOR_THREADS`), e o documento e reescrito
   inteiro.
2. **Escrita atomica**: temporario no mesmo diretorio, `flush` + `fsync`, e
   `os.replace`, que troca o arquivo de uma vez no NTFS e no POSIX.
3. **Permissao restrita** depois da escrita, quando o sistema operacional permite
   — no Windows o `chmod` e praticamente inocuo, e isso esta declarado no
   `data-delta.md`.
4. **Cache por assinatura** `(mtime_ns, tamanho)`: a guarda da 053 confere a versao
   de credencial a cada requisicao autenticada, e reler o JSON a cada uma seria
   pagar o documento inteiro por causa de um inteiro. A escrita do proprio processo
   atualiza o cache na mao, sem depender da granularidade do `mtime`.

## O que este adaptador NAO promete

Coordenacao entre **processos**. A aplicacao e instancia unica por construcao
(`ADR-12`), e a limitacao esta declarada no `data-delta.md` §9.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Any

from core.conta import ContaDeAcesso, ContaDuplicada

VERSAO_DO_DOCUMENTO = 1

#: Prefixo do arquivo temporario de escrita. O ponto inicial o esconde do glob.
_PREFIXO_DO_TEMPORARIO = ".contas-"


class ArquivoDeContasCorrompido(ValueError):
    """O arquivo existe mas nao e o documento esperado.

    E falha de operacao, nao condicao de negocio: a aplicacao prefere recusar a
    ler a adivinhar. O arquivo e preservado para inspecao.
    """


class ContasEmArquivo:
    """`RepositorioDeContas` sobre um documento JSON local."""

    def __init__(self, caminho: str) -> None:
        self._caminho: str = os.path.abspath(os.fspath(caminho))
        self._trava = threading.RLock()
        self._documento_em_memoria: dict[str, Any] | None = None
        self._assinatura: tuple[int, int] | None = None

    @property
    def caminho(self) -> str:
        return self._caminho

    # ------------------------------------------------------------------ leitura
    def _assinatura_do_arquivo(self) -> tuple[int, int] | None:
        try:
            info: os.stat_result = os.stat(self._caminho)
        except OSError:
            return None
        return info.st_mtime_ns, info.st_size

    def _documento(self) -> dict[str, Any]:
        with self._trava:
            assinatura: tuple[int, int] | None = self._assinatura_do_arquivo()
            if self._documento_em_memoria is not None and assinatura == self._assinatura:
                return self._documento_em_memoria
            self._documento_em_memoria = self._ler()
            self._assinatura = assinatura
            return self._documento_em_memoria

    def _ler(self) -> dict[str, Any]:
        try:
            with open(self._caminho, encoding="utf-8") as arquivo:
                bruto = json.load(arquivo)
        except FileNotFoundError:
            return {"versao": VERSAO_DO_DOCUMENTO, "contas": {}, "tokens": {}}
        except (json.JSONDecodeError, UnicodeDecodeError) as erro:
            raise ArquivoDeContasCorrompido(self._caminho) from erro
        if not isinstance(bruto, dict):
            raise ArquivoDeContasCorrompido(self._caminho)
        contas = bruto.get("contas") or {}
        tokens = bruto.get("tokens") or {}
        if not isinstance(contas, dict) or not isinstance(tokens, dict):
            raise ArquivoDeContasCorrompido(self._caminho)
        return {
            "versao": int(bruto.get("versao") or VERSAO_DO_DOCUMENTO),
            "contas": contas,
            "tokens": tokens,
        }

    # ------------------------------------------------------------------ escrita
    def _gravar(self, documento: dict[str, Any]) -> None:
        pasta: str = os.path.dirname(self._caminho)
        os.makedirs(pasta, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(
            dir=pasta, prefix=_PREFIXO_DO_TEMPORARIO, suffix=".tmp"
        )
        try:
            with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
                json.dump(documento, arquivo, ensure_ascii=False, indent=2, sort_keys=True)
                arquivo.write("\n")
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, self._caminho)
        except BaseException:
            try:
                os.unlink(temporario)
            except OSError:
                pass
            raise
        try:
            os.chmod(self._caminho, 0o600)
        except OSError:
            # Windows: a ACL da pasta manda, e o chmod e quase sempre no-op.
            pass
        self._documento_em_memoria = documento
        self._assinatura = self._assinatura_do_arquivo()

    # ------------------------------------------------------------------ porta
    def criar(self, conta: ContaDeAcesso) -> ContaDeAcesso:
        with self._trava:
            documento: dict[str, Any] = self._documento()
            if self._por_email_em(documento, conta.email_normalizado) is not None:
                raise ContaDuplicada(conta.email_normalizado)
            if conta.google_sub and self._por_google_em(documento, conta.google_sub) is not None:
                raise ContaDuplicada(conta.google_sub)
            documento["contas"][conta.sub] = conta.para_dicionario()
            self._gravar(documento)
            return conta

    def por_email(self, email_normalizado: str) -> ContaDeAcesso | None:
        return self._por_email_em(self._documento(), email_normalizado)

    def por_sub(self, sub: str) -> ContaDeAcesso | None:
        return self._conta_de(self._documento()["contas"].get(sub))

    def por_google_sub(self, google_sub: str) -> ContaDeAcesso | None:
        return self._por_google_em(self._documento(), google_sub)

    def salvar(self, conta: ContaDeAcesso) -> None:
        with self._trava:
            documento: dict[str, Any] = self._documento()
            documento["contas"][conta.sub] = conta.para_dicionario()
            self._gravar(documento)

    def anexar_token(self, sub: str, tipo: str, hash_token: str,
                     expira_em: datetime) -> None:
        campo: str = _campo_do_token(tipo)
        with self._trava:
            documento: dict[str, Any] = self._documento()
            bruto: dict[str, Any] | None = documento["contas"].get(sub)
            if bruto is None:
                return
            anterior: Any | None = bruto.get(campo)
            if anterior:
                documento["tokens"].pop(anterior, None)
            documento["tokens"][hash_token] = {
                "sub": sub,
                "tipo": tipo,
                "expira_em": expira_em.isoformat(),
            }
            bruto[campo] = hash_token
            self._gravar(documento)

    def consumir_token(self, hash_token: str, agora: datetime) -> tuple[str, str] | None:
        with self._trava:
            documento: dict[str, Any] = self._documento()
            registro = documento["tokens"].pop(hash_token, None)
            if registro is None:
                return None
            sub = str(registro.get("sub") or "")
            tipo = str(registro.get("tipo") or "")
            bruto = documento["contas"].get(sub)
            if bruto is not None and tipo in ("confirmacao", "redefinicao"):
                bruto[_campo_do_token(tipo)] = None
            self._gravar(documento)
            try:
                expira_em: datetime = datetime.fromisoformat(str(registro.get("expira_em")))
            except ValueError:
                return None
            if expira_em <= agora or not sub or tipo not in ("confirmacao", "redefinicao"):
                return None
            return sub, tipo

    def token_vigente(self, hash_token: str, agora: datetime) -> tuple[str, str] | None:
        with self._trava:
            documento: dict[str, Any] = self._documento()
            registro: dict[str, Any] | None = documento["tokens"].get(hash_token)
        if registro is None:
            return None
        try:
            expira_em: datetime = datetime.fromisoformat(str(registro.get("expira_em")))
        except ValueError:
            return None
        if expira_em <= agora:
            return None
        sub: str = str(registro.get("sub") or "")
        tipo: str = str(registro.get("tipo") or "")
        if not sub or tipo not in ("confirmacao", "redefinicao"):
            return None
        return sub, tipo

    # ------------------------------------------------------------------ internos
    def _por_email_em(self, documento: dict[str, Any], email_normalizado: str) -> ContaDeAcesso | None:
        for bruto in documento["contas"].values():
            if str(bruto.get("email_normalizado") or "") == email_normalizado:
                return self._conta_de(bruto)
        return None

    def _por_google_em(self, documento: dict[str, Any], google_sub: str) -> ContaDeAcesso | None:
        for bruto in documento["contas"].values():
            if str(bruto.get("google_sub") or "") == google_sub:
                return self._conta_de(bruto)
        return None

    def _conta_de(self, bruto: dict[str, Any] | None) -> ContaDeAcesso | None:
        if bruto is None:
            return None
        try:
            return ContaDeAcesso.de_dicionario(bruto)
        except (KeyError, TypeError, ValueError) as erro:
            raise ArquivoDeContasCorrompido(self._caminho) from erro


def _campo_do_token(tipo: str) -> str:
    if tipo == "confirmacao":
        return "token_confirmacao"
    if tipo == "redefinicao":
        return "token_redefinicao"
    raise ValueError(f"tipo de token desconhecido: {tipo}")


__all__: list[str] = [
    "ArquivoDeContasCorrompido",
    "ContasEmArquivo",
    "VERSAO_DO_DOCUMENTO",
]
