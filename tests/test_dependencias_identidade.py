"""Guardas estruturais da identidade local (`RNF-03`, `RNF-04`).

Inspecao por AST, e nao por import: a pergunta e textual ("que imports este
arquivo declara?"), e importar executaria efeitos colaterais. Mesmo metodo de
`tests/test_dependencias_nucleo.py`.
"""
from __future__ import annotations

import ast
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")

FRAMEWORKS = {"flask", "waitress", "werkzeug"}
BANCO = {"sqlite3", "psycopg2"}
CORREIO = {"smtplib", "imaplib"}
PACOTES_DE_BORDA = {"web", "ports", "application", "parsers", "reporting"}


def _imports(caminho: str) -> set[str]:
    with open(caminho, encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read(), filename=caminho)
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                nomes.add(alias.name.split(".")[0])
        elif isinstance(no, ast.ImportFrom):
            if no.level == 0 and no.module:
                nomes.add(no.module.split(".")[0])
    return nomes


def test_o_nucleo_da_identidade_nao_importa_borda_nem_infraestrutura():
    for nome in ("conta.py", "token_de_uso_unico.py"):
        imports = _imports(os.path.join(SRC, "core", nome))
        proibidos = FRAMEWORKS | BANCO | CORREIO | PACOTES_DE_BORDA
        assert not (imports & proibidos), f"{nome} importa {imports & proibidos}"


def test_o_nucleo_da_identidade_nao_abre_arquivo():
    for nome in ("conta.py", "token_de_uso_unico.py"):
        caminho = os.path.join(SRC, "core", nome)
        with open(caminho, encoding="utf-8") as arquivo:
            arvore = ast.parse(arquivo.read(), filename=caminho)
        chamadas = {
            no.func.id
            for no in ast.walk(arvore)
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name)
        }
        assert "open" not in chamadas, f"{nome} abre arquivo"


def test_as_rotas_de_conta_nao_falam_smtp_direto():
    imports = _imports(os.path.join(SRC, "web", "rotas_conta.py"))
    assert not (imports & CORREIO)


def test_o_adaptador_de_contas_nao_conhece_flask():
    imports = _imports(os.path.join(SRC, "ports", "contas_em_arquivo.py"))
    assert not (imports & FRAMEWORKS)


def test_o_adaptador_de_email_nao_conhece_a_camada_web():
    imports = _imports(os.path.join(SRC, "ports", "email_smtp.py"))
    assert "web" not in imports
    assert "application" not in imports


def test_a_aplicacao_nao_importa_correio():
    # A aplicacao consome a PORTA; quem fala SMTP e o adaptador.
    for nome in ("cadastro.py", "recuperacao.py", "definir_senha.py", "vinculo.py"):
        imports = _imports(os.path.join(SRC, "application", nome))
        assert not (imports & CORREIO), nome
