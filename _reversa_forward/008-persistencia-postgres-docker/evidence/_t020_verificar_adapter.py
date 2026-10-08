"""Verificacao do adaptador DENTRO do conteiner (a substancia do `T014`).

Este script existe porque o `T014` nao pode rodar no host: o `.venv/` nao tem o
driver `psycopg2` e nao consegue ter (o `pip install` falha com `0o700` — `OBS-15`).
Aqui o driver existe, porque a imagem o instala a partir do `requirements.txt`.

Ele NAO substitui o `tests/test_registro_de_analises.py`: aquele arquivo continua
sendo o teste do repositorio, e continua pulado sem `DATABASE_URL`. O que este
script faz e executar os mesmos caminhos **uma vez**, com o banco no ar, e deixar a
saida registrada como evidencia do `T020`.

Rodado como:  docker compose exec -T app python /tmp/verificar.py
"""
import os
import sys

sys.path.insert(0, "/app/src")

from application.dna_analysis import projetar_analise  # noqa: E402
from ports.adaptadores import RegistroDeAnalisesPostgres  # noqa: E402

URL = os.environ["DATABASE_URL"]
MARCA = "verificacao-t020__arvore.ged"
FALHAS = []


def checar(nome, ok, detalhe=""):
    print(("PASS  " if ok else "FAIL  ") + nome + (("  |  " + str(detalhe)) if detalhe else ""))
    if not ok:
        FALHAS.append(nome)


def conexao_de(kit, cm, status, nome_csv="Ana Silva Souza"):
    """Uma conexao no formato que o nucleo produz: UM kit por conexao."""
    resultado = {
        "match_name": "Ana Silva Souza",
        "csv_name": nome_csv,
        "cm": cm,
        "kit": kit,
        "documentary": {
            "status": "found", "label": "Irmãos", "relationship_key": "SIBLINGS",
            "meioses": 2,
            "person_a": {"id": "I12", "name": "Carlos", "sex": "M", "birth": "1980",
                         "birth_place": "Recife", "death": None},
            "person_b": {"id": "I13", "name": "Ana", "sex": "F", "birth": None,
                         "birth_place": None, "death": None},
            "common_ancestor": {"id": "I10", "name": "Joaquim", "birth": "1950"},
            "path": {"ids": ["I12", "I10", "I13"], "names": ["Carlos", "Joaquim", "Ana"]},
            "warnings": [],
        },
        "genetic_evidence": {
            "available": True, "source": "GEDmatch",
            "kits": [{"kit": kit, "source": "GEDmatch", "total_cm": cm,
                      "segment_count": 3, "largest_segment_cm": cm}],
            "totals": {"cm": None},
        },
        "hypotheses": [],
        "comparison": {
            "status": status, "label": status.capitalize(), "message": "m",
            "causes": ["endogamia"],
            "per_kit": [{"kit": kit, "status": status, "cm": cm, "note": "nota"}],
            "method": "scp40:Siblings",
            "expected_range": {"low": 1613, "high": 3488, "average": 2613},
            "detail": "Parentesco documental: Irmãos (2 meioses).",
            "observations": ["aviso"],
        },
        "observations": ["aviso"],
        "warnings": [],
    }
    return resultado


def analise(*conexoes, descartados=(), message="2 conexões encontradas. 1 descartada."):
    return projetar_analise(list(conexoes), list(descartados), message,
                            MARCA, "verificacao-t020__matches.csv", "Carlos Silva Souza")


def limpar():
    import psycopg2
    con = psycopg2.connect(URL)
    try:
        with con:
            with con.cursor() as cur:
                cur.execute("DELETE FROM dna_analysis WHERE tree_ref = %s", (MARCA,))
    finally:
        con.close()


def consultar(sql, params=None):
    import psycopg2
    con = psycopg2.connect(URL)
    try:
        with con.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        con.close()


def main():
    import importlib.util
    checar("driver psycopg2 importavel no conteiner",
           importlib.util.find_spec("psycopg2") is not None)

    registro = RegistroDeAnalisesPostgres(URL)
    limpar()

    # ---- 1. Dois kits do mesmo nome: DUAS conexoes, um kit cada (RF-05) ----
    referencia, aviso = registro.registrar(
        analise(conexao_de("KIT-A", 200.0, "COMPATIVEL"),
                conexao_de("KIT-B", 60.0, "CONFLITANTE"),
                descartados=[{"csv_name": "Zzz Ninguem", "kit": None, "cm": 150.0,
                              "motivo": "não encontrado"}]),
        "unico")
    checar("gravou e devolveu referencia", aviso is None and bool(referencia), aviso)
    if not referencia:
        return

    linhas = consultar(
        "SELECT result_ordinal, csv_name, total_cm, comparison_status FROM match_result "
        "WHERE analysis_id = %s ORDER BY result_ordinal", (referencia,))
    checar("duas conexoes gravadas", len(linhas) == 2, linhas)
    checar("ordem preservada", [linha[0] for linha in linhas] == [0, 1], linhas)
    checar("estados individuais preservados",
           [linha[3] for linha in linhas] == ["COMPATIVEL", "CONFLITANTE"], linhas)

    cms = [float(linha[0]) for linha in consultar(
        "SELECT k.total_cm FROM match_kit k JOIN match_result m USING (match_id) "
        "WHERE m.analysis_id = %s ORDER BY m.result_ordinal", (referencia,))]
    checar("cM por kit, sem soma", cms == [200.0, 60.0], cms)
    checar("a soma nao existe em lugar nenhum", 260.0 not in cms, cms)

    papeis = [linha[0] for linha in consultar(
        "SELECT role FROM match_path_node n JOIN match_result m USING (match_id) "
        "WHERE m.analysis_id = %s ORDER BY m.result_ordinal, n.ordinal", (referencia,))]
    checar("papeis do caminho derivados do ancestral comum",
           papeis[:3] == ["ascendente", "ascendente", "descendente"], papeis)

    completas = dict(consultar(
        "SELECT xref, completa FROM analysis_person WHERE analysis_id = %s", (referencia,)))
    checar("a raiz e o match tem ficha completa",
           completas.get("I12") is True and completas.get("I13") is True, completas)
    checar("o no do caminho fica so identificado", completas.get("I10") is False, completas)

    descartes = consultar(
        "SELECT csv_name, reason FROM skipped_match WHERE analysis_id = %s", (referencia,))
    checar("descarte gravado com o motivo em texto",
           descartes == [("Zzz Ninguem", "não encontrado")], descartes)

    # ---- 2. Ida e volta do cM nas fronteiras de faixa (RISK-004) ----
    for cm in (46.0, 200.0, 553.0, 1317.0, 2200.0, 3300.0):
        ref, aviso = registro.registrar(
            analise(conexao_de("KIT-F", cm, "INCONCLUSIVO")), "unico")
        lido = (consultar("SELECT total_cm FROM match_result WHERE analysis_id = %s",
                          (ref,)) or [[None]])[0][0]
        checar("cM de fronteira %g sobrevive a ida e volta" % cm,
               aviso is None and lido is not None and float(lido) == cm, lido)
        limpar()

    # ---- 3. Ausente e NULL, nunca zero (RN-11) ----
    vazia = conexao_de("KIT-N", None, "INCONCLUSIVO")
    vazia["comparison"] = dict(vazia["comparison"], method=None, expected_range=None,
                               causes=None)
    vazia["observations"] = None
    ref, aviso = registro.registrar(analise(vazia), "unico")
    linha = consultar(
        "SELECT total_cm, comparison_method, expected_low, causes FROM match_result "
        "WHERE analysis_id = %s", (ref,))[0]
    checar("cM ausente e NULL e nao zero", linha[0] is None, linha)
    checar("metodo ausente e NULL", linha[1] is None, linha)
    checar("faixa ausente e NULL", linha[2] is None, linha)
    checar("causes ausente nao virou lista com valor",
           linha[3] is None or list(linha[3]) == [], linha)

    # ---- 4. Falha nao levanta, e nao deixa nada pela metade (RN-13, RF-10) ----
    quebrado = RegistroDeAnalisesPostgres(
        "postgresql://ninguem:ninguem@127.0.0.1:1/inexistente")
    referencia_ruim, aviso_ruim = quebrado.registrar(
        analise(conexao_de("KIT-X", 100.0, "POSSIVEL")), "unico")
    checar("falha devolve aviso em vez de excecao",
           referencia_ruim is None and bool(aviso_ruim)
           and "Histórico não registrado" in (aviso_ruim or ""), aviso_ruim)

    # A analise inteira e recusada pelo `CHECK` de estado: a conexao viola o dominio
    # fechado, o INSERT levanta, e a transacao tem de voltar INTEIRA — nem a linha de
    # `dna_analysis` pode sobrar. E a prova do `RF-10`.
    from dataclasses import replace
    antes = consultar("SELECT count(*) FROM dna_analysis")[0][0]
    boa = analise(conexao_de("KIT-Y", 100.0, "POSSIVEL"))
    invalida = replace(boa, conexoes=(
        replace(boa.conexoes[0], comparison_status="NAO_EXISTE"),))
    referencia_check, aviso_check = registro.registrar(invalida, "unico")
    depois = consultar("SELECT count(*) FROM dna_analysis")[0][0]

    checar("o CHECK recusa estado fora dos quatro, e devolve aviso",
           referencia_check is None and bool(aviso_check), aviso_check)
    checar("transacao unica: a analise recusada nao deixou NENHUMA linha",
           depois == antes, (antes, depois))

    limpar()
    print()
    print("RESULTADO: %d falha(s)" % len(FALHAS))
    for nome in FALHAS:
        print("  - " + nome)


main()
