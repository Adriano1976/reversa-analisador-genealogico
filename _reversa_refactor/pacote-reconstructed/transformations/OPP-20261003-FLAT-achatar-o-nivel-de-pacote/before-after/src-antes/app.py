import os

from flask import Flask, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from reconstructed.core.dna_analysis import dna_analysis as dna_analysis_flow
from reconstructed.core.path_search import path_search as path_search_flow
from reconstructed.parsers.gedcom_parser import load_gedcom_and_build_graph
from reconstructed.utils.validate import (
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
    app.run(debug=True)
