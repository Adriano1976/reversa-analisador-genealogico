import os

from flask import Flask, render_template, request

from reconstructed.dna_analysis import dna_analysis as dna_analysis_flow
from reconstructed.path_search import path_search as path_search_flow
from reconstructed.upload import load_gedcom_and_build_graph

# --- Configuração ---
app = Flask(__name__)
app.secret_key = 'f@milyse@rch_dna_edition_v16'

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)


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
                gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_file.filename)
                gedcom_file.save(gedcom_path)
                all_names = load_gedcom_and_build_graph(gedcom_path)
                return render_template("index.html", gedcom_filename=gedcom_file.filename, all_names=all_names, message=f"Arquivo '{gedcom_file.filename}' carregado!", success=True)
            except Exception as e:
                return render_template("index.html", message=f"Erro ao processar GEDCOM: {e}", success=False)

        gedcom_filename = request.form.get("gedcom_filename")
        if not gedcom_filename:
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_filename)
        if not os.path.exists(gedcom_path):
            return render_template("index.html", message=f"Erro: Arquivo '{gedcom_filename}' não existe mais.", success=False)
        all_names = load_gedcom_and_build_graph(gedcom_path)

        if action == "dna_analysis":
            try:
                if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                matches_file, root_name = request.files["matches_csv"], request.form["root_name"]
                matches_path = os.path.join(UPLOAD_FOLDER, matches_file.filename)
                matches_file.save(matches_path)

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
