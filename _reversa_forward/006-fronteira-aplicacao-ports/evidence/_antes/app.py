import errno
import os
import socket
import sys

from flask import Flask, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from core.dna_analysis import Dependencias, dna_analysis as dna_analysis_flow
from parsers.csv_ingest import (
    aggregate_matches,
    detect_columns as detectar_colunas,
    read_csv_with_fallback,
)
from reporting.mermaid_render import (
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from core.path_search import path_search as path_search_flow
from core.registro import get_name
from parsers.gedcom_parser import carregar_arvore
from utils.number_format import formatar_cm, formatar_inteiro
from utils.validate import (
    chave_de_armazenamento,
    chave_recebida_e_valida,
    nome_do_arquivo_armazenado,
    validar_conteudo_gedcom,
)

# As dependencias de borda que o nucleo consome (RF-09): leitura de CSV e
# emissao de diagrama. Montadas uma vez, aqui na borda, e injetadas nos fluxos.
_DEPENDENCIAS = Dependencias(
    read_csv_with_fallback,
    detectar_colunas,
    aggregate_matches,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

# --- Configuração ---
app = Flask(__name__)
# `app.secret_key` foi REMOVIDO em 2026-10-05 por decisao do usuario
# (_reversa_sdd/questions.md#pergunta-2). Ele nao tinha consumidor: `flask.session`
# nunca foi importado e nenhum cookie era emitido. O literal estava versionado no
# repositorio e seria a chave de forja de sessao no instante em que alguem
# introduzisse sessao para tratar isolamento entre usuarios - exatamente a Rota 2
# descartada do BUG-20260929-BJJH. Ver _reversa_sdd/permissions.md (P-04).

# Teto de corpo de requisicao. Ausente no legado, e a ausencia fazia o multipart
# inteiro ser gravado em disco antes de qualquer verificacao de negocio
# (BUG-20260929-QMLY). Acima do teto o Flask aborta com 413 antes de ler o corpo.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Formato dos numeros que o operador le (BUG-20261004-EWSJ). O template pede o
# filtro; a regra mora em `utils/number_format.py`, que e a autoridade unica.
app.add_template_filter(formatar_cm, "cm_br")
app.add_template_filter(formatar_inteiro, "inteiro_br")

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


def _gedcom_do_formulario() -> tuple[str | None, str | None, str | None]:
    """Arvore pedida pelo formulario: devolve `(nome, caminho, mensagem)`.

    Fonte unica das duas guardas de entrada dos fluxos pos-upload (analise de
    DNA e busca de caminho). Antes da OPP-20261006-4KMB o mesmo par de guardas
    estava escrito em `index()` com as duas mensagens duplicadas.

    O `nome` volta junto porque e ele que o template devolve no campo oculto
    `gedcom_filename`, para a requisicao seguinte. E o valor RECEBIDO do
    formulario, e nao uma forma derivada do caminho: e assim que o contrato de
    continuidade entre requisicoes sempre funcionou.

    A uniao e explicita de proposito, e o chamador repete a guarda de `None`.
    O checador nao estreita o segundo elemento da tupla por `erro is not None`,
    entao sem as duas a chamada de `load_gedcom_and_build_graph` recebe
    `str | None`. Medido com pyrefly 1.3.2: sem a guarda, os erros de `src/`
    sobem de 27 para 28.

    O parse NAO acontece aqui de proposito: `load_gedcom_and_build_graph`
    substitui o estado global do processo, e cada ramo o chama no ponto exato em
    que chamava antes. Devolver a arvore pronta mudaria esse instante.
    """
    nome_recebido = request.form.get("gedcom_filename")
    if not nome_recebido:
        return None, None, "Erro: Arquivo GEDCOM não encontrado."
    caminho: str | None = _resolver_caminho_armazenado(nome_recebido)
    if caminho is None:
        return None, None, f"Erro: Arquivo '{nome_recebido}' não existe mais."
    return nome_recebido, caminho, None


def _nomes_da_arvore(arvore) -> list[str]:
    """Nomes de exibicao, ordenados — a lista que alimenta o campo de sugestao.

    Era o retorno de carregar_arvore. Com o parse devolvendo a
    arvore (T009/T020), a lista passa a ser derivada AQUI, na borda, e a
    ordenacao tem de ser a mesma: sorted, sobre get_name de cada pessoa.
    """
    return sorted([get_name(p) for p in arvore[0].values()])


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
                arvore = carregar_arvore(caminho_armazenado)
                all_names = _nomes_da_arvore(arvore)
                return render_template("index.html", gedcom_filename=os.path.basename(caminho_armazenado), all_names=all_names, message=f"Arquivo '{gedcom_file.filename}' carregado!", success=True)
            except Exception as e:
                return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)

        gedcom_filename, gedcom_path, erro = _gedcom_do_formulario()
        if erro is not None:
            return render_template("index.html", message=erro, success=False)
        if gedcom_path is None:
            # Inalcancavel em execucao: `erro` e `caminho` sao preenchidos juntos.
            # Existe para o checador de tipos estreitar a uniao do retorno.
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        arvore = carregar_arvore(gedcom_path)
        all_names = _nomes_da_arvore(arvore)

        if action == "dna_analysis":
            try:
                if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                matches_file, root_name = request.files["matches_csv"], request.form["root_name"]
                matches_path, motivo = _guardar_upload(matches_file, "csv")
                if motivo is not None:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=motivo, success=False)

                results_list_sorted, skipped_matches, message = dna_analysis_flow(
                    matches_path,
                    root_name,
                    # A borda monta as dependencias: leitura de CSV e diagrama
                    # sao de fora do nucleo (RF-09, T016).
                    Dependencias(read_csv_with_fallback, detectar_colunas,
                                 aggregate_matches, generate_mermaid_graph,
                                 generate_mermaid_graph_indirect_bridge),
                    arvore,
                )
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

                path_result, msg, success = path_search_flow(person1_name, person2_name, _DEPENDENCIAS, arvore)
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
    # porta ao mesmo tempo. Duas instancias compartilham o MESMO diretorio de
    # uploads (`src/uploads/`), entao gravam e leem os mesmos arquivos, e
    # requisicoes do mesmo operador caem em instancias diferentes. A exclusividade
    # e, portanto, responsabilidade daqui.
    #
    # Ate a feature 005 havia um motivo a mais — o estado global da arvore, que
    # fazia as duas instancias divergirem em memoria. O estado saiu, e o motivo que
    # fica e o armazenamento em disco.
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
