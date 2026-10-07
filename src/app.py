import errno
import os
import socket
import sys

from flask import Flask, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from application import Desfecho, nomes_de_exibicao
from application.dna_analysis import dna_analysis as caso_de_uso_dna
from application.path_search import path_search as caso_de_uso_de_busca
from application.traducao import traduzir
from application.upload_gedcom import upload_gedcom as caso_de_uso_de_upload
from core.dna_analysis import Dependencias
from core.erros import ErroDeDominio
from parsers.csv_ingest import (
    aggregate_matches,
    detect_columns as detectar_colunas,
    read_csv_with_fallback,
)
from reporting.mermaid_render import (
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from ports.adaptadores import ArmazenamentoEmDisco, CarregadorDeArvoresGedcom
from utils.number_format import formatar_cm, formatar_inteiro

# As dependencias de borda que o nucleo consome (RF-09): leitura de CSV e
# emissao de diagrama. Montadas UMA vez, aqui na borda, e injetadas nos fluxos
# pelo caso de uso (D-05). Ate a extracao havia uma segunda montagem identica
# dentro do ramo de DNA, a cada requisicao; ela saiu em `T018`.
_DEPENDENCIAS = Dependencias(
    read_csv_with_fallback,
    detectar_colunas,
    aggregate_matches,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

# RN-06: NAO ha identidade de usuario nesta onda. O dono e um marcador unico do
# processo, e existe porque a costura precisa estar na assinatura ANTES de a Onda
# 3 chegar — adiar reabriria toda assinatura de porta (RF-08). Nenhum
# comportamento de isolamento depende deste valor, e nenhuma entrega desta feature
# pode ser citada como tendo implementado isolamento.
DONO_DO_PROCESSO = "unico"

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
#
# O valor passa a ter nome (`T004`, `D-10`). A `RN-01` permite nomear constantes e
# proibe alterar valores: o numero e o MESMO, e o que muda e existir um ponto unico
# de mudanca — e o teste poder citar a constante em vez de repetir o literal.
TETO_DE_UPLOAD_EM_BYTES = 16 * 1024 * 1024

# Derivado do mesmo teto para a mensagem de `413`, que fala em MB e nao em bytes.
# A divisao fica aqui, ao lado da origem, para as duas formas do MESMO teto
# mudarem juntas se o valor mudar um dia.
TETO_DE_UPLOAD_EM_MB = TETO_DE_UPLOAD_EM_BYTES // (1024 * 1024)

app.config["MAX_CONTENT_LENGTH"] = TETO_DE_UPLOAD_EM_BYTES

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

# Os adaptadores concretos das portas, montados na borda (RF-02, D-07). Nenhum
# caso de uso instancia estes: ele recebe a porta por parametro. A pasta e
# resolvida UMA vez, aqui, e nao a cada requisicao — a funcao acima le o
# ambiente, e o ambiente nao muda no meio do processo.
_ARMAZENAMENTO = ArmazenamentoEmDisco(_pasta_uploads())
_CARREGADOR = CarregadorDeArvoresGedcom(_ARMAZENAMENTO)


@app.errorhandler(RequestEntityTooLarge)
def _requisicao_grande(_erro):
    return render_template(
        "index.html",
        message=f"Arquivo maior que o limite de {TETO_DE_UPLOAD_EM_MB} MB.",
        success=False,
    ), 413


def _arvore_do_formulario() -> tuple[str | None, object | None, str | None]:
    """Arvore pedida pelo formulario: devolve `(referencia, arvore, mensagem)`.

    Fonte unica das duas guardas de entrada dos fluxos pos-upload (analise de
    DNA e busca de caminho). Antes da OPP-20261006-4KMB o mesmo par de guardas
    estava escrito em `index()` com as duas mensagens duplicadas.

    A `referencia` volta junto porque e ela que o template devolve no campo oculto
    `gedcom_filename`, para a requisicao seguinte. E o valor RECEBIDO do
    formulario, e nao uma forma derivada do caminho: e assim que o contrato de
    continuidade entre requisicoes sempre funcionou.

    Ate `T016` da feature 006 esta funcao resolvia o caminho por
    `_resolver_caminho_armazenado` e chamava `carregar_arvore` direto — as duas
    coisas que a `RF-01` tira do adaptador de entrada. Agora quem resolve e quem
    parseia sao as portas: `CarregadorDeArvores` resolve a referencia e devolve a
    arvore, e `None` significa que a referencia nao aponta para arquivo existente.

    A uniao e explicita de proposito, e o chamador repete a guarda de `None`. O
    checador nao estreita o segundo elemento da tupla por `erro is not None`,
    entao sem as duas a chamada do carregador recebe `str | None`.
    """
    referencia = request.form.get("gedcom_filename")
    if not referencia:
        return None, None, "Erro: Arquivo GEDCOM não encontrado."
    arvore = _CARREGADOR.carregar(referencia)
    if arvore is None:
        return None, None, f"Erro: Arquivo '{referencia}' não existe mais."
    return referencia, arvore, None


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
                resultado = caso_de_uso_de_upload(
                    gedcom_file.read(), gedcom_file.filename, DONO_DO_PROCESSO,
                    _ARMAZENAMENTO, _CARREGADOR)
                return render_template("index.html", gedcom_filename=resultado.referencia, all_names=resultado.nomes, message=resultado.mensagem, success=True)
            except ErroDeDominio as erro_de_dominio:
                # A recusa de conteudo passa por aqui. O texto e o MESMO de antes
                # da extracao (`Arquivo nao reconhecido como GEDCOM: ...`), e a
                # unica diferenca e que agora a condicao chega TIPADA: a moldura
                # e da tabela de traducao, e o motivo veio dentro da excecao.
                return render_template("index.html", message=traduzir(erro_de_dominio).mensagem, success=False)
            except Exception as e:
                return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)

        gedcom_filename, arvore, erro = _arvore_do_formulario()
        if erro is not None:
            return render_template("index.html", message=erro, success=False)
        if arvore is None:
            # Inalcancavel em execucao: `erro` e `arvore` sao preenchidos juntos.
            # Existe para o checador de tipos estreitar a uniao do retorno.
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        all_names = nomes_de_exibicao(arvore)

        if action == "dna_analysis":
            try:
                if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                matches_file, root_name = request.files["matches_csv"], request.form["root_name"]

                # A gravação do CSV passa pela MESMA porta do GEDCOM. O tipo
                # `"csv"` nao valida conteudo — a assimetria com o GEDCOM e a
                # divida #10, preservada de proposito (`RF-10`, `RN-01`).
                caminho_do_csv, motivo = _ARMAZENAMENTO.guardar(
                    matches_file.read(), matches_file.filename, "csv")
                if motivo is not None:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=motivo, success=False)

                resultado = caso_de_uso_dna(
                    caminho_do_csv, root_name, arvore, _DEPENDENCIAS, DONO_DO_PROCESSO)
                return render_template(
                    "index.html",
                    gedcom_filename=gedcom_filename,
                    all_names=all_names,
                    dna_results=resultado.resultados,
                    skipped_matches=resultado.descartados,
                    message=resultado.mensagem,
                    success=True
                )
            except ErroDeDominio as erro_de_dominio:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=traduzir(erro_de_dominio).mensagem, success=False)
            except Exception as e:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message=f"Ocorreu um erro: {e}", success=False)

        if action == "path_search":
            try:
                person1_name = request.form["person1_name"].strip()
                person2_name = request.form["person2_name"].strip()

                resultado = caso_de_uso_de_busca(
                    person1_name, person2_name, arvore, _DEPENDENCIAS, DONO_DO_PROCESSO)

                # O modo de renderizacao vem do DESFECHO, nunca do texto: sao dois
                # casos que o operador ve de formas diferentes e que hoje so se
                # distinguem por uma linha de codigo — "pessoa nao encontrada"
                # (alerta de erro) e "nenhuma conexao encontrada" (cartao, com
                # sucesso). `D-11`.
                if resultado.desfecho is Desfecho.ERRO_DE_ENTRADA:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                           message=resultado.mensagem, success=False)
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       path_result=resultado.dados, message=resultado.mensagem, success=True)
            except ErroDeDominio as erro_de_dominio:
                return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names,
                                       message=traduzir(erro_de_dominio).mensagem, success=False)
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
