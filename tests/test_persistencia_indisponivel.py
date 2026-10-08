"""Estado de FALHA da persistencia historica (`T019`; `RN-13`, `RF-10`, `RF-17`).

Com `DATABASE_URL` presente e a gravacao **recusada**, o que tem de continuar
verdadeiro e o que o `Q-03` decidiu:

- a analise **conclui** e o resultado **aparece** — o historico e beneficio, nunca
  condicao para ver a resposta;
- o operador recebe um **aviso nao bloqueante**, e nao uma tela de erro;
- o HTTP continua `200`, e nao `500`.

## Qual causa de falha este arquivo exercita, e por que

O `actions.md` escreve "gravacao recusada por alvo invalido — `DATABASE_URL`
apontando para uma porta fechada". No interpretador do host, a causa exercitada e
**outra**: o `psycopg2` nao esta instalado no `.venv/` (defeito de `0o700` no
`pip`, `OBS-02`/`OBS-15`), e o adaptador transforma isso no mesmo aviso.

O teste afirma a **invariante**, e nao a causa: `registrar` nunca levanta e nunca
bloqueia. E por isso que ele mede o que importa nos dois interpretadores — no host
ele exercita a ausencia do driver, e dentro do conteiner (no `T020`) a mesma
propriedade e exercitada com o driver presente e a conexao recusada de verdade.
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PASTA_APP = os.path.join(_RAIZ, "src")
sys.path.insert(0, _RAIZ)
sys.path.insert(0, _PASTA_APP)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fixtures.sample_dna import DNA_CSV_UTF8, DNA_GED  # noqa: E402

_URL_DE_ALVO_INVALIDO = "postgresql://ninguem:ninguem@127.0.0.1:1/inexistente"


def _carregar_app(nome: str):
    """Carrega `src/app.py` como modulo NOVO, lendo o ambiente do momento do import."""
    caminho = os.path.join(_PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    return modulo


def _carregar_arvore(client) -> str:
    pagina = client.post(
        "/",
        data={"action": "upload_gedcom",
              "gedcom": (io.BytesIO(DNA_GED.encode()), "arvore.ged")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    chave = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    assert chave, "o upload não devolveu a chave"
    return chave.group(1)


def _analisar(client, chave):
    return client.post(
        "/",
        data={"action": "dna_analysis", "gedcom_filename": chave,
              "root_name": "Carlos Silva Souza",
              "matches_csv": (io.BytesIO(DNA_CSV_UTF8.encode()), "matches.csv")},
        content_type="multipart/form-data",
    )


@pytest.fixture
def cliente_com_url_invalida(cliente_de_upload, monkeypatch):
    """Cliente cujo `app.py` foi carregado **com** a `DATABASE_URL` invalida.

    ⚠️ **A ordem das fixtures importa, e este e o motivo de o app ser recarregado
    aqui.** `cliente_de_upload` e **dependencia** desta fixture, entao o corpo dela
    executa `src/app.py` **antes** de o corpo desta rodar — e um
    `monkeypatch.setenv` aqui dentro chegaria tarde, deixando `_REGISTRO` nulo e o
    teste medindo o estado DESABILITADO em vez do estado de falha.

    Recarregar o modulo depois de definir a variavel resolve, e deixa explicito que
    a borda le o ambiente no import (`D-02`). A pasta de upload e a mesma que
    `cliente_de_upload` ja apontou para o diretorio temporario.
    """
    _, _, pasta_de_uploads = cliente_de_upload
    monkeypatch.setenv("DATABASE_URL", _URL_DE_ALVO_INVALIDO)
    modulo = _carregar_app("_app_persistencia_indisponivel")
    modulo.app.root_path = _PASTA_APP
    return modulo.app, modulo.app.test_client(), pasta_de_uploads


def test_a_analise_conclui_e_o_resultado_aparece(cliente_com_url_invalida):
    """`RF-17`: com a gravacao recusada, a tela mostra o MESMO resultado."""
    _, client, _ = cliente_com_url_invalida
    chave = _carregar_arvore(client)
    resposta = _analisar(client, chave)
    pagina = resposta.get_data(as_text=True)

    assert resposta.status_code == 200, (
        "a falha de persistencia virou erro HTTP — a RN-13 proibe"
    )
    assert "Ana Silva Souza" in pagina, "a persistencia bloqueou o resultado"
    assert "Ocorreu um erro" not in pagina, "a tela mostra erro cru"


def test_o_aviso_nao_bloqueante_aparece(cliente_com_url_invalida):
    """`RF-17`: e o aviso e o UNICO sinal — sem ele, a falha seria indistinguivel."""
    _, client, _ = cliente_com_url_invalida
    chave = _carregar_arvore(client)
    pagina = _analisar(client, chave).get_data(as_text=True)

    assert "Histórico não registrado" in pagina, (
        "a analise saiu sem gravacao e SEM aviso — o operador nao tem como saber"
    )
    assert "alerta-aviso" in pagina, (
        "o aviso saiu sem a classe de alerta NAO bloqueante que o resto da tela usa"
    )


def test_o_aviso_aparece_uma_vez_e_nao_uma_por_conexao(cliente_com_url_invalida):
    """O aviso e da ANALISE, e nao de cada resultado — a gravacao e uma so."""
    _, client, _ = cliente_com_url_invalida
    chave = _carregar_arvore(client)
    pagina = _analisar(client, chave).get_data(as_text=True)

    assert pagina.count("Histórico não registrado") == 1, (
        "o aviso se repetiu: ele esta sendo emitido por conexao em vez de por analise"
    )


# ---------------------------------------------------------------------------
# A mesma invariante, um nivel abaixo: no ADAPTADOR, sem rota e sem banco.
#
# Aqui a projecao entrega uma analise vazia — o adaptador nao chega a escrever
# nada, porque a conexao ja falha. O que se mede e exatamente o que a `RN-13`
# exige dele: **nao propagar excecao**, e devolver o motivo em texto.
# ---------------------------------------------------------------------------


def test_o_adaptador_nao_levanta_e_devolve_o_motivo_em_texto():
    from application.dna_analysis import projetar_analise
    from ports.adaptadores import RegistroDeAnalisesPostgres

    registro = RegistroDeAnalisesPostgres(_URL_DE_ALVO_INVALIDO)
    analise = projetar_analise([], [], "0 conexões encontradas. 0 descartadas.",
                               "chave__arvore.ged", "chave2__matches.csv", "Carlos")

    referencia, aviso = registro.registrar(analise, "unico")

    assert referencia is None, "o adaptador devolveu referencia sem ter gravado"
    assert aviso, "o adaptador engoliu a falha em silencio"
    assert "Histórico não registrado" in aviso, aviso
    assert aviso == aviso.strip() and len(aviso) > 30, (
        "o aviso nao diz nada de util ao operador"
    )
