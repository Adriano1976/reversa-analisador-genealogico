"""Sonda diferencial das mensagens que a tela exibe, caso a caso.

## Por que ela existe

A tabela de traducao (`T014`) e as cinco acoes de integracao (`T016` a `T019`)
tem de reproduzir o texto observavel ao caractere. Duas condicoes parecidas podem
ser apresentadas de formas diferentes — a excecao do nucleo de DNA e envolvida por
`f"Ocorreu um erro: {e}"`, e o motivo de GEDCOM recusado NAO e. Escrever a tabela
de cabeca erraria; esta sonda MEDE cada caso.

## Como ela mede os dois lados

A mesma sonda roda antes e depois da extracao, e as duas saidas sao comparadas
caso a caso. O `ROTULO` vem do argumento:

    python probe_mensagens.py antes
    python probe_mensagens.py depois

Saida: `mensagens_<ROTULO>.json`, ao lado deste arquivo. O comparador e
`_comparar.py` no mesmo diretorio.

Ela cobre os **nove** literais congelados de `12-paridade-telas.feature`, os dois
literais negativos de upload sem cobertura de teste, o teto de `413` e os tres
caminhos de resultado da busca — um deles, o de afinidade, e o unico jeito de
alcancar a nona mensagem.

Nao escreve em `src/uploads/`: aponta `ANALISADOR_UPLOAD_FOLDER` para um
diretorio proprio ANTES de importar o `app.py`, que cria a pasta no import. A
pasta fica dentro do workspace de proposito: o sandbox desta sessao permite criar
um diretorio temporario do sistema (`tempfile.mkdtemp`) mas NEGA escrita dentro
dele, e o `tmp_path` do pytest tem o mesmo defeito por outro caminho (`0o700`).
Ver `README-evidencias.md` neste diretorio.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
PASTA_APP = os.path.join(RAIZ, "src")

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA_TEMP = os.path.join(AQUI, "_tmp_probe")
os.environ["ANALISADOR_UPLOAD_FOLDER"] = os.path.join(PASTA_TEMP, "uploads")
sys.path.insert(0, RAIZ)
sys.path.insert(0, PASTA_APP)

# Joao + Maria casados, Ana filha dos dois, Zeca casado com Ana, Solo sem familia.
# - Ana x Maria / Ana x Joao  -> conexao DIRETA (ancestral comum)
# - Maria x Zeca              -> conexao INDIRETA (so casamento: Maria chega a
#                                Zeca por Ana, e nao ha ancestral comum)
# - Joao x Solo               -> conexao NENHUMA (Solo nao tem familia)
GEDCOM = (
    "0 HEAD\n"
    "1 SOUR TESTE\n"
    "1 GEDC\n"
    "2 VERS 5.5.1\n"
    "2 FORM LINEAGE-LINKED\n"
    "0 @I1@ INDI\n"
    "1 NAME Joao /Silva/\n"
    "1 SEX M\n"
    "1 FAMS @F1@\n"
    "0 @I2@ INDI\n"
    "1 NAME Maria /Souza/\n"
    "1 SEX F\n"
    "1 FAMS @F1@\n"
    "0 @I3@ INDI\n"
    "1 NAME Ana /Silva/\n"
    "1 SEX F\n"
    "1 FAMC @F1@\n"
    "1 FAMS @F2@\n"
    "0 @I4@ INDI\n"
    "1 NAME Zeca /Pereira/\n"
    "1 SEX M\n"
    "1 FAMS @F2@\n"
    "0 @I5@ INDI\n"
    "1 NAME Solo /Ninguem/\n"
    "1 SEX M\n"
    "0 @F1@ FAM\n"
    "1 HUSB @I1@\n"
    "1 WIFE @I2@\n"
    "1 CHIL @I3@\n"
    "0 @F2@ FAM\n"
    "1 HUSB @I4@\n"
    "1 WIFE @I3@\n"
    "0 TRLR\n"
)

CSV_OK = b"Name,cM\nJoao Silva,150\n"
CSV_SEM_COLUNAS = b"alfa,beta\n1,2\n"

_ALERTA = re.compile(
    r'class="alert alert-(success|danger)[^"]*"[^>]*role="alert">\s*(.*?)\s*<button',
    re.DOTALL,
)


def _app():
    # `PROBE_APP` permite apontar a sonda para uma copia do `app.py` ANTERIOR a
    # extracao, guardada em `_antes/`. E assim que o lado "antes" e medido com a
    # lista de casos ATUAL: rodar a sonda nova contra o codigo velho, e nao
    # comparar duas listas diferentes.
    caminho = os.environ.get("PROBE_APP") or os.path.join(PASTA_APP, "app.py")
    spec = importlib.util.spec_from_file_location("_app_probe006", caminho)
    modulo = importlib.util.module_from_spec(spec)
    modulo.__file__ = caminho
    spec.loader.exec_module(modulo)
    modulo.app.root_path = PASTA_APP
    return modulo.app


def _mensagem(resposta):
    """(status, classe do alerta, texto) — o que o operador realmente ve."""
    texto = resposta.get_data(as_text=True)
    achado = _ALERTA.search(texto)
    if not achado:
        return resposta.status_code, None, None
    classe = achado.group(1)
    corpo = re.sub(r"\s+", " ", achado.group(2)).strip()
    return resposta.status_code, classe, corpo


def _upload(client, nome, conteudo):
    return client.post(
        "/",
        data={"action": "upload_gedcom", "gedcom": (io.BytesIO(conteudo), nome)},
        content_type="multipart/form-data",
    )


def _chave(client):
    pagina = _upload(client, "arvore.ged", GEDCOM.encode()).get_data(as_text=True)
    return re.search(r'name="gedcom_filename" value="([^"]+)"', pagina).group(1)


def _post(client, dados):
    return client.post("/", data=dados, content_type="multipart/form-data")


def coletar():
    app = _app()
    client = app.test_client()
    casos = []

    def registra(nome, resposta, obs=""):
        status, classe, mensagem = _mensagem(resposta)
        casos.append({"caso": nome, "status": status, "alerta": classe,
                      "mensagem": mensagem, "obs": obs})

    registra("upload_sem_arquivo", _post(client, {"action": "upload_gedcom"}))
    registra("upload_nome_vazio", _upload(client, "", GEDCOM.encode()))
    registra("upload_conteudo_invalido", _upload(client, "x.ged", b"nao e gedcom\n"))
    registra("upload_conteudo_vazio", _upload(client, "x.ged", b""))
    registra("upload_ok", _upload(client, "arvore.ged", GEDCOM.encode()))

    teto = app.config["MAX_CONTENT_LENGTH"]
    registra("upload_acima_do_teto", _upload(client, "grande.ged", b"x" * (teto + 1024)))

    chave = _chave(client)

    registra("ref_ausente", _post(client, {"action": "path_search"}))
    registra("ref_inexistente", _post(client, {
        "action": "path_search",
        "gedcom_filename": "0" * 16 + "__nao_existe.ged",
        "person1_name": "Joao Silva", "person2_name": "Ana Silva"}))
    registra("ref_forma_invalida", _post(client, {
        "action": "path_search", "gedcom_filename": "../app.py",
        "person1_name": "Joao Silva", "person2_name": "Ana Silva"}))

    registra("dna_sem_csv", _post(client, {
        "action": "dna_analysis", "gedcom_filename": chave, "root_name": "Joao Silva"}))
    registra("dna_csv_nome_vazio", _post(client, {
        "action": "dna_analysis", "gedcom_filename": chave, "root_name": "Joao Silva",
        "matches_csv": (io.BytesIO(CSV_OK), "")}))
    registra("dna_raiz_ausente", _post(client, {
        "action": "dna_analysis", "gedcom_filename": chave, "root_name": "Zzz Ninguem",
        "matches_csv": (io.BytesIO(CSV_OK), "matches.csv")}))
    registra("dna_csv_sem_colunas", _post(client, {
        "action": "dna_analysis", "gedcom_filename": chave, "root_name": "Joao Silva",
        "matches_csv": (io.BytesIO(CSV_SEM_COLUNAS), "matches.csv")}))
    registra("dna_ok", _post(client, {
        "action": "dna_analysis", "gedcom_filename": chave, "root_name": "Joao Silva",
        "matches_csv": (io.BytesIO(CSV_OK), "matches.csv")}))

    registra("path_pessoa1_ausente", _post(client, {
        "action": "path_search", "gedcom_filename": chave,
        "person1_name": "Zzz Ninguem", "person2_name": "Joao Silva"}))
    registra("path_pessoa2_ausente", _post(client, {
        "action": "path_search", "gedcom_filename": chave,
        "person1_name": "Joao Silva", "person2_name": "Zzz Ninguem"}))
    registra("path_direto", _post(client, {
        "action": "path_search", "gedcom_filename": chave,
        "person1_name": "Ana Silva", "person2_name": "Maria Souza"}))
    registra("path_indireto", _post(client, {
        "action": "path_search", "gedcom_filename": chave,
        "person1_name": "Maria Souza", "person2_name": "Zeca Pereira"}))
    registra("path_sem_conexao", _post(client, {
        "action": "path_search", "gedcom_filename": chave,
        "person1_name": "Joao Silva", "person2_name": "Solo Ninguem"}))

    return casos


if __name__ == "__main__":
    rotulo = sys.argv[1] if len(sys.argv) > 1 else "antes"
    casos = coletar()
    saida = os.path.join(AQUI, "mensagens_%s.json" % rotulo)
    with open(saida, "w", encoding="utf-8") as destino:
        json.dump(casos, destino, ensure_ascii=False, indent=2)
    for caso in casos:
        print("[%s] status=%s alerta=%s" % (
            caso["caso"], caso["status"], caso["alerta"]))
        print("    " + ascii(caso["mensagem"]))
    print("gravado em " + saida)
