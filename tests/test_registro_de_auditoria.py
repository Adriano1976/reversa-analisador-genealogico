"""Testes da trilha de auditoria (`T011` da feature 049).

Cobrem as duas tentativas de aposentar — a decisao 14 do `gaps.md`, que estava agendada
desde 2026-10-11 —, os tres desfechos do envio (`RN-17`) e a regra de identificacao da
decisao de 2026-10-25: a linha carrega a **chave de conteudo**, nunca o rotulo visivel.
"""
import io
import os
import time

from utils import logs


def _linhas_da_trilha() -> list[str]:
    caminho = os.path.join(logs.pasta_de_logs(), logs.arquivo_de_auditoria_de_hoje())
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read().splitlines()


def _trilha() -> str:
    return "\n".join(_linhas_da_trilha())


def _enviar_gedcom(cliente, nome: str, conteudo: bytes) -> str:
    """Envia o GEDCOM e devolve a referencia gravada (chave + nome visivel)."""
    import re

    pagina = cliente.post(
        "/",
        data={"action": "upload_gedcom", "gedcom": (io.BytesIO(conteudo), nome)},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    achado = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    return achado.group(1) if achado else ""


GEDCOM_A = (
    "0 HEAD\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "0 @I1@ INDI\n"
    "1 NAME Ana /Lima/\n"
    "1 SEX F\n"
    "0 TRLR\n"
)

GEDCOM_B = (
    "0 HEAD\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "0 @I1@ INDI\n"
    "1 NAME Ana /Lima/\n"
    "1 SEX F\n"
    "0 @I2@ INDI\n"
    "1 NAME Bento /Lima/\n"
    "1 SEX M\n"
    "0 TRLR\n"
)


def test_aposentar_com_sucesso_deixa_rastro(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    referencia = _enviar_gedcom(cliente, "arvore-sandro.ged", GEDCOM_A.encode())
    assert referencia

    cliente.post("/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": referencia})

    linhas = [linha for linha in _linhas_da_trilha() if "acao=aposentar" in linha]
    assert any("desfecho=sucesso" in linha for linha in linhas), _trilha()


def test_aposentar_que_falha_tambem_deixa_rastro(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    referencia = _enviar_gedcom(cliente, "arvore-sandro.ged", GEDCOM_A.encode())
    assert referencia

    # Primeira tentativa move o arquivo; a segunda encontra a pasta sem ele.
    cliente.post("/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": referencia})
    cliente.post("/", data={"action": "aposentar_arquivo", "arquivo_a_aposentar": referencia})

    desfecho_de_falha = [
        linha for linha in _linhas_da_trilha()
        if "acao=aposentar" in linha and "desfecho=falha" in linha
    ]
    assert desfecho_de_falha, "a tentativa que falhou nao deixou linha na trilha"


def test_a_linha_identifica_o_arquivo_pela_chave_e_nunca_pelo_rotulo(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    referencia = _enviar_gedcom(cliente, "Backup-Arvore-Sandro.ged", GEDCOM_A.encode())
    chave = referencia.split("__")[0]

    assert chave in _trilha(), "a chave de conteudo nao esta na linha de auditoria"
    assert "Sandro" not in _trilha(), "o rotulo visivel do arquivo entrou na auditoria"
    assert ".ged" in _trilha(), "a extensao do arquivo nao foi registrada"


def test_os_tres_desfechos_do_envio_sao_distinguiveis(cliente_de_upload):
    _, cliente, _ = cliente_de_upload

    _enviar_gedcom(cliente, "arvore.ged", GEDCOM_A.encode())          # novo
    _enviar_gedcom(cliente, "arvore.ged", GEDCOM_A.encode())          # identico
    _enviar_gedcom(cliente, "arvore.ged", GEDCOM_B.encode())          # substituido

    linhas = [linha for linha in _linhas_da_trilha() if "acao=enviar_gedcom" in linha]
    for desfecho in ("novo", "identico", "substituido"):
        assert any(f"desfecho={desfecho}" in linha for linha in linhas), (
            f"o desfecho {desfecho!r} nao apareceu na trilha: {linhas}"
        )


def test_a_linha_carrega_ip_origem_e_identificador(cliente_de_upload):
    _, cliente, _ = cliente_de_upload
    resposta = cliente.post(
        "/",
        data={"action": "aposentar_arquivo", "arquivo_a_aposentar": "nao-existe.ged"},
    )
    identificador = resposta.headers["X-Request-ID"]

    linha = [linha for linha in _linhas_da_trilha() if "acao=aposentar" in linha][-1]
    assert f"[{identificador}]" in linha, "a linha nao carrega o identificador da requisicao"
    assert "ip=127.0.0.1" in linha
    assert "origem=POST /" in linha


def test_as_contagens_saem_em_numero_e_sem_nome(cliente_de_upload):
    """`RF-07`: quantos, nunca quem."""
    _, cliente, _ = cliente_de_upload
    referencia = _enviar_gedcom(cliente, "arvore.ged", GEDCOM_A.encode())

    cliente.post(
        "/",
        data={
            "action": "dna_analysis",
            "gedcom_filename": referencia,
            "root_name": "Ana Lima",
            "matches_csv": (io.BytesIO(b"Name,cM\nAna Lima,150\n"), "matches.csv"),
        },
        content_type="multipart/form-data",
    )

    linhas = [linha for linha in _linhas_da_trilha() if "acao=analisar_dna" in linha]
    assert linhas, "a analise de DNA nao deixou linha de auditoria"
    assert "resultados=" in linhas[-1]
    assert "Ana" not in linhas[-1] and "Lima" not in linhas[-1]


def test_a_trilha_de_hoje_tem_o_nome_datado():
    assert logs.arquivo_de_auditoria_de_hoje() == (
        f"{logs.PREFIXO_DA_AUDITORIA}.{time.strftime('%Y-%m-%d')}.log"
    )
