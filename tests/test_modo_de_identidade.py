"""O modo de identidade declarado (auditoria de 2026-10-30, P1/P3).

## O que este arquivo prende

- sem `ANALISADOR_MODO` e sem o escape de teste, `create_app` NAO monta aplicacao;
- valor desconhecido tambem nao;
- `local` sobe sem login, e nao registra `/login` nem `/cadastro`;
- `google` sem as cinco variaveis recusa, nomeando o que falta.

## Por que a recusa e testada na FABRICA, e nao no `__main__`

Porque era exatamente ai que o defeito vivia: `create_app()` montava a aplicacao
aberta e so `python src/app.py` recusava. Um teste na fabrica prende o
comportamento de QUALQUER runner — `waitress-serve`, servico do Windows, `.bat`.
"""
from __future__ import annotations

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_APP = os.path.join(RAIZ, "src")
for _caminho in (RAIZ, PASTA_APP):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import app as modulo  # noqa: E402
from web import modo as modulo_modo  # noqa: E402


# --------------------------------------------------------------------- fabrica
def test_sem_modo_declarado_a_fabrica_recusa(monkeypatch):
    monkeypatch.delenv(modulo_modo.VARIAVEL, raising=False)
    monkeypatch.delenv(modulo_modo.VARIAVEL_DE_TESTE, raising=False)

    with pytest.raises(modulo_modo.ModoNaoDeclarado) as erro:
        modulo.create_app()

    assert modulo_modo.VARIAVEL in str(erro.value), "a mensagem tem de nomear a variavel"


def test_modo_desconhecido_recusa(monkeypatch):
    monkeypatch.setenv(modulo_modo.VARIAVEL, "nenhum")
    monkeypatch.delenv(modulo_modo.VARIAVEL_DE_TESTE, raising=False)

    with pytest.raises(modulo_modo.ModoNaoDeclarado):
        modulo.create_app()


def test_local_sobe_sem_login_e_sem_rota_de_entrada(monkeypatch, pasta_temporaria):
    from ports.adaptadores import ArmazenamentoEmDisco

    monkeypatch.setenv(modulo_modo.VARIAVEL, modulo_modo.LOCAL)
    pasta = os.path.join(pasta_temporaria, "uploads")
    aplicacao = modulo.create_app(armazenamento=ArmazenamentoEmDisco(pasta))

    regras = {regra.rule for regra in aplicacao.url_map.iter_rules()}
    assert "/login" not in regras
    assert "/cadastro" not in regras
    assert aplicacao.config["MODO_DE_IDENTIDADE"] == modulo_modo.LOCAL
    assert aplicacao.test_client().get("/").status_code == 200, (
        "o modo local tem de servir a tela; o que ele nao tem e login"
    )


def test_google_sem_credencial_recusa_nomeando_o_que_falta(monkeypatch):
    monkeypatch.setenv(modulo_modo.VARIAVEL, modulo_modo.GOOGLE)
    monkeypatch.setattr(
        modulo, "_FALTANTES", ["GOOGLE_CLIENT_ID", "ANALISADOR_SECRET_KEY"]
    )

    with pytest.raises(modulo_modo.RecusaDeSubida) as erro:
        modulo.create_app()

    assert "GOOGLE_CLIENT_ID" in str(erro.value)
    assert "ANALISADOR_SECRET_KEY" in str(erro.value)


def test_o_escape_de_teste_dispensa_a_declaracao(monkeypatch, pasta_temporaria):
    from ports.adaptadores import ArmazenamentoEmDisco

    monkeypatch.delenv(modulo_modo.VARIAVEL, raising=False)
    monkeypatch.setenv(modulo_modo.VARIAVEL_DE_TESTE, "1")
    pasta = os.path.join(pasta_temporaria, "uploads")
    aplicacao = modulo.create_app(armazenamento=ArmazenamentoEmDisco(pasta))

    assert aplicacao.config["MODO_DE_IDENTIDADE"] is None
    assert aplicacao.test_client().get("/").status_code == 200


# -------------------------------------------------------------------- leitura
class TestALeituraDoAmbiente:
    def test_le_o_modo_declarado(self):
        assert modulo_modo.ler({"ANALISADOR_MODO": "local"}) == "local"
        assert modulo_modo.ler({"ANALISADOR_MODO": " Google "}) == "google", (
            "espaco e caixa nao podem tornar o modo irreconhecivel"
        )

    def test_o_modo_declarado_vence_o_escape(self):
        assert modulo_modo.ler(
            {"ANALISADOR_MODO": "local", "ANALISADOR_MODO_TESTE": "1"}
        ) == "local"

    def test_o_escape_dispensa_a_declaracao(self):
        assert modulo_modo.ler({"ANALISADOR_MODO_TESTE": "1"}) is None

    def test_sem_nada_levanta(self):
        with pytest.raises(modulo_modo.ModoNaoDeclarado):
            modulo_modo.ler({})

    def test_escape_com_outro_valor_nao_vale(self):
        """`ANALISADOR_MODO_TESTE=sim` nao e escape: so o literal `1` vale."""
        with pytest.raises(modulo_modo.ModoNaoDeclarado):
            modulo_modo.ler({"ANALISADOR_MODO_TESTE": "sim"})
