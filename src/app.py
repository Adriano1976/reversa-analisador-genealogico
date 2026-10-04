import errno
import os
import socket
import sys

from flask import Flask, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from core.dna_analysis import dna_analysis as dna_analysis_flow
from core.path_search import path_search as path_search_flow
from parsers.gedcom_parser import load_gedcom_and_build_graph
from utils.validate import (
    chave_de_armazenamento,
    chave_recebida_e_valida,
    nome_do_arquivo_armazenado,
    validar_conteudo_gedcom,
)

# --- Configuração ---
app = Flask(__name__)
app.secret_key = 'f@milyse@rch_dna_edition_v16'

# Teto de corpo de requisicao. Ausente no legado, e a ausencia fazia o multipart
# inteiro ser gravado em disco antes de qualquer verificacao de negocio
# (BUG-20260929-QMLY). Acima do teto o Flask aborta com 413 antes de ler o corpo.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

UPLOAD_FOLDER = "uploads"


def _pasta_uploads() -> str:
    """Pasta de upload, ancorada no arquivo do app.

    Era relativa ao diretorio corrente, o que dava dois nomes para o mesmo
    arquivo: o caminho de escrita e o de leitura podiam divergir quando o CWD
    mudava. Foi o que quebrou a analise de DNA na correcao do BUG-20260929-QMLY
    (o CSV era gravado em `uploads/<chave>` e procurado como `<chave>`).
    Ancorar no arquivo torna escrita e leitura o MESMO caminho, sempre.

    `ANALISADOR_UPLOAD_FOLDER` permite apontar a pasta para outro lugar, o que e
    usado pelos testes para nao escreverem na pasta real.
    """
    apontada = os.environ.get("ANALISADOR_UPLOAD_FOLDER")
    if apontada:
        return apontada
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), UPLOAD_FOLDER)


# A pasta e criada a partir da MESMA funcao que a resolve, para o diretorio
# criado no import e o procurado nas requisicoes nao poderem divergir.
os.makedirs(_pasta_uploads(), exist_ok=True)


@app.errorhandler(RequestEntityTooLarge)
def _requisicao_grande(_erro):
    limite_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return render_template(
        "index.html",
        message=f"Arquivo maior que o limite de {limite_mb} MB.",
        success=False,
    ), 413


def _guardar_upload(arquivo, kind: str):
    """Valida e grava o upload sob chave gerada pelo servidor.

    Devolve `(caminho, motivo)`. `motivo` e None em caso de sucesso, e `caminho`
    e o CAMINHO COMPLETO do arquivo gravado. Devolver o caminho, e nao o nome, e
    deliberado: quem le depois usa exatamente o que foi escrito, sem remontar o
    caminho. A versao anterior devolvia o nome e a rota de DNA o passava direto
    ao parser, que procurava o CSV no diretorio corrente e falhava com
    `No such file or directory`. Nome e caminho nunca devem ser intercambiaveis.
    """
    conteudo = arquivo.read()
    motivo = validar_conteudo_gedcom(conteudo) if kind == "gedcom" else None
    if motivo is not None:
        return None, f"Arquivo não reconhecido como GEDCOM: {motivo}."

    chave = chave_de_armazenamento(conteudo)
    nome_armazenado = nome_do_arquivo_armazenado(chave, arquivo.filename)
    caminho = os.path.join(_pasta_uploads(), nome_armazenado)
    if not os.path.exists(caminho):
        with open(caminho, "wb") as destino:
            destino.write(conteudo)
    return caminho, None


def _resolver_caminho_armazenado(nome_recebido):
    """Caminho do arquivo ja armazenado, ou None quando o valor e invalido.

    A validacao de forma e o que impede um `gedcom_filename` manipulado de
    apontar para fora da pasta de upload (BUG-20260929-QMLY, criterio 5).
    """
    if not chave_recebida_e_valida(nome_recebido):
        return None
    caminho = os.path.join(_pasta_uploads(), nome_recebido)
    return caminho if os.path.exists(caminho) else None


# --- Rota Principal ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "upload_gedcom":
            if "gedcom" not in request.files:
                return render_template("index.html", message="Nenhum arquivo GEDCOM enviado.", success=False)
            gedcom_file = request.files["gedcom"]
            if gedcom_file.filename == '':
                return render_template("index.html", message="Nenhum arquivo selecionado.", success=False)
            try:
                caminho_armazenado, motivo = _guardar_upload(gedcom_file, "gedcom")
                if motivo is not None:
                    return render_template("index.html", message=motivo, success=False)
                all_names = load_gedcom_and_build_graph(caminho_armazenado)
                return render_template("index.html", gedcom_filename=os.path.basename(caminho_armazenado), all_names=all_names, message=f"Arquivo '{gedcom_file.filename}' carregado!", success=True)
            except Exception as e:
                return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)

        gedcom_filename = request.form.get("gedcom_filename")
        if not gedcom_filename:
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        gedcom_path = _resolver_caminho_armazenado(gedcom_filename)
        if gedcom_path is None:
            return render_template("index.html", message=f"Erro: Arquivo '{gedcom_filename}' não existe mais.", success=False)
        all_names = load_gedcom_and_build_graph(gedcom_path)

        if action == "dna_analysis":
            try:
                if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                matches_file, root_name = request.files["matches_csv"], request.form["root_name"]
                matches_path, motivo = _guardar_upload(matches_file, "csv")
                if motivo is not None:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=motivo, success=False)

                results_list_sorted, skipped_matches, message = dna_analysis_flow(matches_path, root_name)
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    dna_results=results_list_sorted,
                    skipped_matches=skipped_matches,
                    message=message,
                    success=True
                )
            except Exception as e:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=f"Ocorreu um erro: {e}", success=False)

        if action == "path_search":
            try:
                person1_name = request.form["person1_name"].strip()
                person2_name = request.form["person2_name"].strip()

                path_result, msg, success = path_search_flow(person1_name, person2_name)
                if not success and path_result is None:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                           message=msg, success=False)
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       path_result=path_result, message=msg, success=True)
            except Exception as e:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       message=f"Ocorreu um erro: {e}", success=False)

    return render_template("index.html")


if __name__ == "__main__":
    # Configuracao de execucao lida do ambiente, com os padroes declarados aqui.
    # Mesmo padrao ja praticado pelo projeto em `ANALISADOR_UPLOAD_FOLDER`.
    #
    # O padrao do endereco e a maquina local (RF-02). A aplicacao nao tem
    # autenticacao alguma, entao atender a rede passa a ser ato explicito de quem
    # opera, e nao o comportamento que acontece por omissao.
    endereco_de_escuta = os.environ.get("ANALISADOR_HOST", "127.0.0.1")
    porta_de_escuta = int(os.environ.get("ANALISADOR_PORT", "5000"))
    concorrencia = int(os.environ.get("ANALISADOR_THREADS", "4"))

    # O import fica aqui dentro de proposito. Este modulo e importado pela suite de
    # testes e pela instrumentacao de paridade, e um import no topo obrigaria o
    # servidor de producao instalado em quem so quer a aplicacao como objeto.
    try:
        from waitress import serve
    except ImportError:
        # A mensagem nomeia o pacote e o interpretador exato (D-08) e aponta para o
        # arquivo de dependencias, e nao para o pacote solto: desde a fixacao das
        # versoes, instalar o pacote avulso traria uma versao diferente da validada.
        raise SystemExit(
            "Servidor de producao ausente neste interpretador: o pacote waitress nao "
            "esta instalado. Instale a partir do arquivo de dependencias, com: "
            f"{sys.executable} -m pip install -r requirements.txt"
        )

    # --- Guarda de exclusividade (RN-05, RF-08) ---
    #
    # A medicao de 2026-10-04 mostrou que a plataforma NAO impede a coexistencia:
    # o servidor pede SO_REUSEADDR, e no Windows duas instancias escutam na mesma
    # porta ao mesmo tempo. Como cada processo tem o SEU proprio estado global da
    # arvore (core/gedcom_state.py), duas instancias atendendo fazem requisicoes do
    # mesmo operador cairem em estados diferentes. A exclusividade e, portanto,
    # responsabilidade daqui.
    #
    # O socket e criado, marcado e LIGADO aqui, e entregue ja pronto ao servidor.
    # Com socket pronto o servidor nao faz bind (bind_socket=False), entao quem liga
    # e este bloco. O socket fica aberto ate o processo terminar: fechar para so
    # entao servir abriria uma janela entre fechar e servir, que e exatamente o que
    # a marca de uso exclusivo existe para nao ter.
    socket_de_escuta = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        # Windows: a porta fica exclusiva deste processo, e outra instancia recebe
        # erro no bind mesmo pedindo SO_REUSEADDR.
        socket_de_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        # Fora do Windows a marca nao existe, e o padrao da plataforma ja recusa a
        # segunda ligacao. Reintroduzir SO_REUSEADDR aqui traria de volta a
        # coexistencia que esta guarda existe para impedir.
        socket_de_escuta.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    # O servidor deixa o socket que ele mesmo cria em modo nao bloqueante; o socket
    # entra no lugar dele, e entra com a mesma postura.
    socket_de_escuta.setblocking(False)

    try:
        socket_de_escuta.bind((endereco_de_escuta, porta_de_escuta))
        socket_de_escuta.listen(socket.SOMAXCONN)
    except OSError as erro:
        socket_de_escuta.close()
        # O diagnostico separa os dois motivos porque eles pedem acoes diferentes:
        # porta ocupada se resolve encerrando quem esta no ar ou trocando de porta,
        # e endereco indisponivel se resolve corrigindo ANALISADOR_HOST. Medido em
        # 2026-10-04: porta ocupada chega com errno.EADDRINUSE, e endereco que nao
        # existe nesta maquina chega com 10049, que nao e EADDRINUSE.
        if erro.errno == errno.EADDRINUSE:
            motivo = f"{endereco_de_escuta}:{porta_de_escuta} ja esta em uso"
            saida = (
                "Encerre o processo que ja esta no ar, ou suba esta instancia em "
                "outra porta com ANALISADOR_PORT."
            )
        else:
            motivo = f"nao foi possivel escutar em {endereco_de_escuta}:{porta_de_escuta}"
            saida = (
                "Confira se ANALISADOR_HOST aponta para um endereco desta maquina e "
                "se ANALISADOR_PORT e uma porta valida."
            )
        # A mensagem nao afirma quem ocupa a porta: pode ser uma instancia anterior
        # desta aplicacao ou qualquer outro processo.
        raise SystemExit(f"Recusando subir: {motivo} ({erro.strerror or erro}). {saida}")

    print(
        f"Servindo com waitress em http://{endereco_de_escuta}:{porta_de_escuta} "
        f"com {concorrencia} threads",
        flush=True,
    )
    # `sockets` e mutuamente exclusivo de `host` e `port`: o servidor levanta
    # ValueError se receber `sockets` junto de qualquer um dos dois. Endereco e
    # porta ja estao no socket ligado.
    serve(app, sockets=[socket_de_escuta], threads=concorrencia)
