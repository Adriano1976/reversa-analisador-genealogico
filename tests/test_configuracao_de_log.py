"""Testes da configuracao de registro (`T008` da feature 049).

O que estes testes protegem, e por que cada um existe:

1. **Idempotencia.** A suite reexecuta `src/app.py` a cada fixture e o registro de handlers
   do `logging` e global do processo. Sem idempotencia, cada import acrescentaria um
   handler e a mesma linha sairia duas, tres, dez vezes — e nenhum teste falharia, porque o
   conteudo continuaria certo.
2. **A trilha de auditoria nao propaga.** `RN-01`: uma acao auditada aparece na trilha e
   **nao** vira eco no arquivo geral.
3. **A degradacao nao derruba nada.** Pasta inutilizavel e o caso do container sem volume
   montado: a aplicacao precisa subir, servir e avisar — nao morrer.
"""
import logging
import os
import time

from utils import logs


def _ler(nome: str) -> str:
    caminho = os.path.join(logs.pasta_de_logs(), nome)
    if not os.path.isfile(caminho):
        return ""
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read()


def _trilha_de_hoje() -> str:
    return _ler(f"{logs.PREFIXO_DA_AUDITORIA}.{time.strftime('%Y-%m-%d')}.log")


def test_configurar_e_idempotente():
    logs.configurar()
    antes = len(logging.getLogger().handlers)
    logs.configurar()
    logs.configurar()
    assert len(logging.getLogger().handlers) == antes, (
        "cada chamada de configurar() acrescentou um handler: a mesma linha sairia repetida"
    )


def test_a_auditoria_nao_propaga_para_os_outros_destinos():
    logs.configurar()
    assert logging.getLogger(logs.LOGGER_DE_AUDITORIA).propagate is False


def test_a_linha_de_auditoria_vai_para_a_trilha_e_nao_para_o_arquivo_geral():
    from utils.auditoria import registrar

    logs.configurar()
    marcador = "acao=aposentar desfecho=sucesso arquivo=94e2402671702cac.ged"
    registrar(
        "aposentar",
        "sucesso",
        referencia="94e2402671702cac__Arvore_Sergipana.ged",
        ip="127.0.0.1",
        origem="POST /",
    )

    assert marcador in _trilha_de_hoje(), "a linha de auditoria nao chegou na trilha"
    assert "acao=aposentar" not in _ler(logs.ARQUIVO_GERAL), (
        "a linha de auditoria vazou para o arquivo geral"
    )


def test_o_nivel_padrao_e_informativo():
    logs.configurar()
    assert logging.getLogger().level == logging.INFO


def test_o_nivel_por_modulo_vem_do_ambiente(monkeypatch):
    monkeypatch.setenv(logs.VARIAVEL_DO_NIVEL, "WARNING,parsers=DEBUG")
    nivel, por_modulo = logs.nivel_do_ambiente()
    assert nivel == logging.WARNING
    assert por_modulo == {"parsers": logging.DEBUG}


def test_nivel_invalido_cai_no_padrao(monkeypatch):
    monkeypatch.setenv(logs.VARIAVEL_DO_NIVEL, "nao-existe")
    nivel, por_modulo = logs.nivel_do_ambiente()
    assert nivel == logging.INFO
    assert por_modulo == {}


def test_pasta_inutilizavel_degrada_sem_derrubar(tmp_path):
    """Pasta que nao pode ser criada: sem arquivos, auditoria propagando, nada explode."""
    arquivo = tmp_path / "nao-e-pasta"
    arquivo.write_text("x", encoding="utf-8")

    raiz = logging.getLogger("teste049.raiz")
    auditoria = logging.getLogger("teste049.auditoria")

    assert logs.anexar_arquivos(str(arquivo), raiz, auditoria) is False
    assert auditoria.handlers == [], "anexou arquivo em pasta inutilizavel"
    assert raiz.handlers == []


def test_a_suite_nao_aponta_a_pasta_de_log_para_a_raiz_do_projeto():
    """A suite inteira roda com `ANALISADOR_LOG_DIR` desviado (ver `tests/conftest.py`).

    Sem o desvio, a pasta `logs/` nasceria na raiz do repositorio no primeiro import de
    `src/app.py` — que acontece durante a COLETA, antes de qualquer fixture. A assercao e
    sobre o caminho resolvido, e nao sobre o disco: um desenvolvedor que rodou a aplicacao
    tem `logs/` na raiz, e isso nao pode reprovar a suite.
    """
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(logs.__file__))))
    assert os.path.abspath(logs.pasta_de_logs()) != os.path.join(raiz, logs.PASTA_PADRAO)
