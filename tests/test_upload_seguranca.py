"""Testes do BUG-20260929-QMLY — upload sem limite de tamanho, sem validação de
extensão ou conteúdo e sem sanitização de nome.

Escritos no Gate 1, ANTES do change set. Os testes de reprodução provam que o
defeito relatado aparece no código atual; os de regressão protegem o
comportamento que não pode voltar a quebrar.

Conceitos distintos, ainda que vivam no mesmo arquivo: reprodução prova o
defeito; regressão protege o que funciona.
"""
import importlib.util
import io
import os
import re
import sys

import pytest

PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJETO)
sys.path.insert(0, os.path.join(PROJETO, "src"))

_PASTA_APP = os.path.join(PROJETO, "src")
_CAMINHO_APP = os.path.join(_PASTA_APP, "app.py")


def _carregar_app():
    """Importa `app.py` pelo caminho e fixa o `root_path` da aplicação.

    Medido: `spec_from_file_location` não define `__file__`, e o Flask resolve
    `root_path` pelo diretório corrente. Como cada teste troca de CWD para isolar
    `uploads/`, o Flask deixaria de achar `templates/` e tudo falharia por
    `TemplateNotFound`, o que não tem relação alguma com o defeito medido. Fixar
    `root_path` foi a abordagem verificada nesta mesma sessão.
    """
    spec = importlib.util.spec_from_file_location("_app_qmly", _CAMINHO_APP)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = _CAMINHO_APP
    spec.loader.exec_module(modulo)
    modulo.app.root_path = _PASTA_APP
    return modulo.app

def _validate():
    """Import tardio de `reconstructed.validate`.

    O módulo nasce no CHG-001. Importá-lo no topo faria a coleta inteira
    abortar por ImportError, escondendo a falha real dos testes de rota. Com o
    import aqui, cada teste falha pelo seu próprio motivo.
    """
    from reconstructed import validate as modulo

    return modulo

GEDCOM_VALIDO = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Joao /Silva/\n"
    "1 SEX M\n"
    "0 @I2@ INDI\n"
    "1 NAME Maria /Souza/\n"
    "1 SEX F\n"
    "0 @F1@ FAM\n"
    "1 HUSB @I1@\n"
    "1 WIFE @I2@\n"
    "0 TRLR\n"
)


CSV_MATCHES_DNA = b"Name,cM\nJoao Silva,150\n"


def _enviar(client, nome_arquivo, conteudo, action="upload_gedcom", campo="gedcom"):
    """POST multipart no formato que o navegador envia."""
    return client.post(
        "/",
        data={"action": action, campo: (io.BytesIO(conteudo), nome_arquivo)},
        content_type="multipart/form-data",
    )


def _enviar_dna(client, chave, nome_csv=("matches.csv", CSV_MATCHES_DNA),
                root_name="Joao Silva"):
    """POST do fluxo de analise de DNA, com a chave da arvore ja carregada."""
    return client.post(
        "/",
        data={"action": "dna_analysis", "gedcom_filename": chave,
              "root_name": root_name,
              "matches_csv": (io.BytesIO(nome_csv[1]), nome_csv[0])},
        content_type="multipart/form-data",
    )


def _carregar_arvore(client, nome="arvore.ged", conteudo=None):
    """Faz o upload do GEDCOM e devolve a chave armazenada."""
    pagina = _enviar(client, nome, conteudo if conteudo is not None
                     else GEDCOM_VALIDO.encode()).get_data(as_text=True)
    m = re.search(r'name="gedcom_filename" value="([^"]+)"', pagina)
    assert m, "o upload não devolveu a chave gedcom_filename"
    return m.group(1)


# ---------------------------------------------------------------------------
# Fixtures de ambiente
# ---------------------------------------------------------------------------

@pytest.fixture
def app_cliente(monkeypatch, tmp_path):
    """App Flask com a pasta de upload redirecionada para um diretório temporário.

    `app.py` ancora a pasta no próprio arquivo, então o teste aponta
    `ANALISADOR_UPLOAD_FOLDER` para `tmp_path` e o app resolve escrita e leitura
    pelo mesmo caminho. Antes da correção da regressão de DNA, a pasta era
    relativa ao CWD, e escrita e leitura podiam divergir.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANALISADOR_UPLOAD_FOLDER", str(tmp_path / "uploads"))
    app = _carregar_app()

    original = app.config.get("MAX_CONTENT_LENGTH")
    app.config["MAX_CONTENT_LENGTH"] = original
    yield app, app.test_client(), tmp_path
    app.config["MAX_CONTENT_LENGTH"] = original


def _pasta_uploads(base):
    return base / "uploads"


@pytest.fixture
def valida():
    """O módulo de validação, no nível do módulo: duas classes o consomem."""
    return _validate()


# ===========================================================================
# REPRODUÇÃO — devem FALHAR no código atual
# ===========================================================================

class TestReproducao:
    """Cada teste aqui falha hoje e passa depois do change set."""

    def test_existe_teto_de_tamanho_de_requisicao(self, app_cliente):
        """Critério 1. O projeto não define MAX_CONTENT_LENGTH em lugar nenhum."""
        app, _, _ = app_cliente
        assert app.config.get("MAX_CONTENT_LENGTH") is not None, (
            "sem teto de tamanho, o multipart é gravado em disco antes de "
            "qualquer verificação de negócio"
        )

    def test_requisicao_acima_do_teto_e_rejeitada(self, app_cliente):
        """Critério 1. Acima do teto, com mensagem própria e sem gravar nada."""
        app, client, base = app_cliente
        if app.config.get("MAX_CONTENT_LENGTH") is None:
            pytest.fail("pré-condição ausente: não há teto de tamanho definido")

        teto = app.config["MAX_CONTENT_LENGTH"]
        resposta = client.post(
            "/",
            data={"action": "upload_gedcom",
                  "gedcom": (io.BytesIO(b"x" * (teto + 1024)), "grande.ged")},
            content_type="multipart/form-data",
        )
        assert resposta.status_code == 413
        uploads = _pasta_uploads(base)
        assert not uploads.exists() or not list(uploads.iterdir())

    def test_nome_com_aspas_e_barra_nao_escapa_da_pasta(self, app_cliente):
        """Critério 5. O nome do cliente não pode decidir o caminho no disco."""
        _, client, base = app_cliente
        resposta = _enviar(client, "../malicioso.ged", GEDCOM_VALIDO.encode())
        assert resposta.status_code != 500
        assert not (base / "malicioso.ged").exists(), (
            "o arquivo foi gravado FORA de uploads/, por escape de caminho"
        )

    def test_nome_com_barra_invertida_nao_escapa_da_pasta(self, app_cliente):
        """Critério 5, variante Windows."""
        _, client, base = app_cliente
        _enviar(client, "..\\malicioso2.ged", GEDCOM_VALIDO.encode())
        assert not (base / "malicioso2.ged").exists()

    def test_chave_de_armazenamento_e_gerada_pelo_servidor(self, app_cliente):
        """Critério 3. A chave não pode ser igual ao nome que o cliente escolheu."""
        _, client, base = app_cliente
        nome = "minha_arvore.ged"
        resposta = _enviar(client, nome, GEDCOM_VALIDO.encode())
        assert resposta.status_code == 200

        uploads = _pasta_uploads(base)
        assert uploads.exists(), "o upload válido deveria ter gravado algo"
        gravados = sorted(p.name for p in uploads.iterdir())
        assert nome not in gravados, (
            f"o arquivo em disco usa o nome do cliente: {gravados}"
        )
        assert any(nome.replace(".ged", "") in g or "__" in g for g in gravados), (
            "o nome visível deveria sobreviver como metadado, depois da chave"
        )

    def test_conteudo_invalido_e_recusado_antes_do_parse(self, app_cliente):
        """Critério 2. Conteúdo que não é GEDCOM não deve chegar ao parser."""
        _, client, base = app_cliente
        resposta = _enviar(client, "lixo.ged", b"\x00\x01\x02isto nao e gedcom\xff\xfe")
        texto = resposta.get_data(as_text=True)
        assert "não reconhecido como GEDCOM" in texto or "nao reconhecido como GEDCOM" in texto

    def test_conteudo_invalido_nao_fica_em_disco(self, app_cliente):
        """Critério 2, medido. Hoje o arquivo rejeitado permanece em uploads/."""
        _, client, base = app_cliente
        _enviar(client, "lixo2.ged", b"\x00\x01\x02isto nao e gedcom\xff\xfe")
        uploads = _pasta_uploads(base)
        restaram = sorted(p.name for p in uploads.iterdir()) if uploads.exists() else []
        assert restaram == [], (
            f"arquivo inválido ficou em disco e é recuperável por gedcom_filename: {restaram}"
        )

    def test_arquivo_vazio_e_recusado_e_nao_fica_em_disco(self, app_cliente):
        """Critério 2, caso de borda: conteúdo vazio."""
        _, client, base = app_cliente
        _enviar(client, "vazio.ged", b"")
        uploads = _pasta_uploads(base)
        restaram = sorted(p.name for p in uploads.iterdir()) if uploads.exists() else []
        assert restaram == []

    def test_dois_envios_de_mesmo_nome_nao_se_perdem(self, app_cliente):
        """Critério 4. Hoje o segundo envio sobrescreve o primeiro, em silêncio."""
        _, client, base = app_cliente
        primeiro = b"0 HEAD\n1 SOUR PRIMEIRO\n1 GEDC\n2 VERS 5.5.1\n0 TRLR\n"
        segundo = b"0 HEAD\n1 SOUR SEGUNDO\n1 GEDC\n2 VERS 5.5.1\n0 TRLR\n"

        assert _enviar(client, "colisao.ged", primeiro).status_code == 200
        assert _enviar(client, "colisao.ged", segundo).status_code == 200

        uploads = _pasta_uploads(base)
        conteudos = [p.read_bytes() for p in uploads.iterdir()] if uploads.exists() else []
        assert primeiro in conteudos, "o conteúdo do primeiro envio foi perdido"
        assert segundo in conteudos, "o conteúdo do segundo envio não foi gravado"


class TestModuloDeValidacao:
    """O módulo de validação precisa existir e ser puro (sem Flask, sem disco)."""

    def test_nome_visivel_remove_separadores_de_caminho(self, valida):
        assert "/" not in valida.nome_visivel_seguro("../../etc/passwd")
        assert "\\" not in valida.nome_visivel_seguro("..\\windows\\system32")

    def test_nome_visivel_preserva_acentos_e_espacos(self, valida):
        assert valida.nome_visivel_seguro("árvore da família.ged") == "árvore da família.ged"

    def test_nome_visivel_nunca_fica_vazio(self, valida):
        assert valida.nome_visivel_seguro("") != ""
        assert valida.nome_visivel_seguro("...") != ""

    def test_chave_e_derivada_do_conteudo_e_estavel(self, valida):
        a = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        b = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        assert a == b, "a mesma árvore reenviada precisa gerar a mesma chave"

    def test_chave_muda_com_o_conteudo(self, valida):
        a = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        b = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode() + b"0 @I3@ INDI\n")
        assert a != b

    def test_chave_nao_contem_separador_de_caminho(self, valida):
        chave = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        assert "/" not in chave and "\\" not in chave and ".." not in chave

    def test_valida_gedcom_aceita_o_fixture(self, valida):
        assert valida.validar_conteudo_gedcom(GEDCOM_VALIDO.encode()) is None

    def test_valida_gedcom_recusa_vazio(self, valida):
        assert valida.validar_conteudo_gedcom(b"") is not None

    def test_valida_gedcom_recusa_binario(self, valida):
        assert valida.validar_conteudo_gedcom(b"\x00\x01\x02\xff\xfe") is not None

    def test_valida_gedcom_recusa_texto_sem_cabecalho(self, valida):
        assert valida.validar_conteudo_gedcom(b"isto e um texto qualquer\nnada aqui\n") is not None

    def test_valida_gedcom_aceita_bom_e_linhas_em_branco(self, valida):
        """GEDCOM de exportador real pode começar com BOM ou linha vazia."""
        assert valida.validar_conteudo_gedcom(b"\xef\xbb\xbf" + GEDCOM_VALIDO.encode()) is None
        assert valida.validar_conteudo_gedcom(b"\n\n" + GEDCOM_VALIDO.encode()) is None

    def test_chave_recebida_do_formulario_e_aceita(self, valida):
        chave = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        nome = valida.nome_do_arquivo_armazenado(chave, "arvore.ged")
        assert valida.chave_recebida_e_valida(nome) is True

    def test_chave_recebida_recusa_escape(self, valida):
        assert valida.chave_recebida_e_valida("../etc/passwd") is False
        assert valida.chave_recebida_e_valida("uploads\\..\\x.ged") is False
        assert valida.chave_recebida_e_valida("nome_do_cliente.ged") is False
        assert valida.chave_recebida_e_valida("") is False
        assert valida.chave_recebida_e_valida(None) is False


# ===========================================================================
# REGRESSÃO — protegem o comportamento que não pode quebrar
# ===========================================================================

class TestRegressao:
    """Devem passar hoje E depois do change set."""

    def test_gedcom_valido_continua_aceito_e_parseado(self, app_cliente):
        _, client, _ = app_cliente
        resposta = _enviar(client, "valido.ged", GEDCOM_VALIDO.encode())
        texto = resposta.get_data(as_text=True)
        assert resposta.status_code == 200
        assert "carregado!" in texto, "o upload de GEDCOM válido precisa continuar funcionando"

    def test_gedcom_valido_sem_extensao_ged_continua_aceito(self, app_cliente):
        """A validação é de conteúdo, não de extensão (contingência do RISK-007)."""
        _, client, _ = app_cliente
        resposta = _enviar(client, "valido.txt", GEDCOM_VALIDO.encode())
        texto = resposta.get_data(as_text=True)
        assert resposta.status_code == 200
        assert "carregado!" in texto, (
            "GEDCOM válido com outra extensão não pode ser recusado: quebraria a "
            "paridade de parsing com o legado"
        )

    def test_arvore_continua_encontravel_na_requisicao_seguinte(self, app_cliente):
        """O contrato do campo oculto gedcom_filename precisa sobreviver."""
        _, client, base = app_cliente
        r1 = _enviar(client, "arvore.ged", GEDCOM_VALIDO.encode())
        assert r1.status_code == 200

        uploads = _pasta_uploads(base)
        assert uploads.exists()
        gravados = sorted(p.name for p in uploads.iterdir())
        assert len(gravados) >= 1
        chave = gravados[0]

        r2 = client.post(
            "/",
            data={"action": "path_search", "gedcom_filename": chave,
                  "person1_name": "Joao Silva", "person2_name": "Maria Souza"},
            content_type="multipart/form-data",
        )
        texto = r2.get_data(as_text=True)
        assert "não existe mais" not in texto, (
            "a requisição seguinte não conseguiu carregar a árvore pela chave armazenada"
        )

    def test_uploads_vazio_antes_do_upload(self, app_cliente):
        """Guarda contra teste vacuamente verde: a pasta começa vazia."""
        _, _, base = app_cliente
        uploads = _pasta_uploads(base)
        assert not uploads.exists() or not list(uploads.iterdir())

    def test_fixtures_de_paridade_continuam_validas(self, valida):
        """As 6 fixtures do harness de paridade precisam passar na validação nova."""
        pasta = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "_reversa_sdd", "parity", "fixtures", "gedcom",
        )
        if not os.path.isdir(pasta):
            pytest.skip("fixtures de paridade ausentes neste checkout")
        arquivos = [f for f in sorted(os.listdir(pasta)) if f.endswith(".ged")]
        assert arquivos, "nenhuma fixture encontrada"
        for nome in arquivos:
            with open(os.path.join(pasta, nome), "rb") as fh:
                conteudo = fh.read()
            motivo = valida.validar_conteudo_gedcom(conteudo)
            assert motivo is None, f"fixture de paridade recusada: {nome} ({motivo})"


# ===========================================================================
# REGRESSÃO DA CORREÇÃO — a extensão do CSV de DNA
# ===========================================================================

class TestExtensaoPreservada:
    """A correção do QMLY quebrou o fluxo de DNA, e isto trava a volta.

    O `_guardar_upload` serve ao GEDCOM e ao CSV. A primeira versão de
    `nome_visivel_seguro` fixava a extensão em `.ged`, então o CSV era gravado
    como `<...>.csv.ged` e a análise de DNA falhava com
    `No such file or directory: '94e2402671702cac__Famílias_Sergipanas.csv.ged'`.
    """

    def test_csv_de_dna_nao_vira_ged(self, valida):
        chave = valida.chave_de_armazenamento(CSV_MATCHES_DNA)
        nome = valida.nome_do_arquivo_armazenado(chave, "Famílias_Sergipanas.csv")
        assert nome.endswith("__Famílias_Sergipanas.csv"), nome
        assert not nome.endswith(".csv.ged"), "a extensão do CSV foi sobrescrita"

    def test_extensao_do_gedcom_e_preservada(self, valida):
        chave = valida.chave_de_armazenamento(GEDCOM_VALIDO.encode())
        assert valida.nome_do_arquivo_armazenado(chave, "arvore.ged").endswith("__arvore.ged")

    def test_nome_sem_extensao_recebe_ged(self, valida):
        chave = valida.chave_de_armazenamento(b"x")
        assert valida.nome_do_arquivo_armazenado(chave, "arvore").endswith("__arvore.ged")

    def test_extensao_em_maiuscula_e_preservada(self, valida):
        chave = valida.chave_de_armazenamento(b"x")
        assert valida.nome_do_arquivo_armazenado(chave, "ARVORE.GED").endswith("__ARVORE.GED")

    def test_fluxo_completo_de_analise_de_dna(self, app_cliente):
        """O caminho que o usuário usa: carregar a árvore e analisar o CSV."""
        _, client, base = app_cliente
        chave = _carregar_arvore(client)
        resposta = _enviar_dna(client, chave)
        texto = resposta.get_data(as_text=True)
        assert "No such file or directory" not in texto, (
            "o arquivo do CSV não foi encontrado pelo nome com que foi gravado"
        )
        assert "Ocorreu um erro" not in texto, texto[
            texto.find("Ocorreu um erro"):texto.find("Ocorreu um erro") + 220
        ]

    def test_csv_fica_gravado_com_a_extensao_original(self, app_cliente):
        _, client, base = app_cliente
        chave = _carregar_arvore(client)
        _enviar_dna(client, chave)
        uploads = _pasta_uploads(base)
        nomes = sorted(p.name for p in uploads.iterdir())
        assert any(n.endswith("__matches.csv") for n in nomes), (
            f"o CSV não foi gravado com a extensão original: {nomes}"
        )
        assert not any(n.endswith(".csv.ged") for n in nomes), nomes
