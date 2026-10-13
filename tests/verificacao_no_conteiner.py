"""Verificacao que roda DENTRO da imagem: a arte servida e a gravacao no banco.

## Por que este arquivo existe

Duas dividas declaradas so podem ser fechadas com a aplicacao rodando **na imagem**:

- **`L-33`** — nao havia verificacao de que a arte servida e a arte que existe **dentro
  do container**. Os testes rodam no host, onde `docs/` existe; se a arte faltasse na
  imagem, a degradacao seria `404`, silenciosa, sem log e sem teste. E exatamente o caso
  que a escolha de `src/assets/` (permitida pelo `.dockerignore` de permissao) existe
  para evitar.
- **`L-28` / `X-05`** — nao havia teste do **caminho feliz de gravacao** no banco. Ele
  existe em `tests/test_registro_de_analises.py`, mas se **pula** no `.venv/` do host por
  dois motivos medidos: o driver `psycopg2` nao esta instalado la (e o `pip install`
  falha com `PermissionError` por causa do `0o700` que ele cria) e a suite roda **sem**
  `DATABASE_URL` por decisao (`D-17`). Dentro da imagem o driver existe, porque a imagem o
  instala a partir do `requirements.txt`.

## Por que nao e um teste do pytest

O `requirements.txt` e lista de **runtime**: o pytest nao esta na imagem, e instala-lo ali
seria mudar a imagem para caber no instrumento. Este arquivo usa **somente dependencias de
producao** e roda como script.

## Como rodar

```powershell
docker compose up -d db
docker compose run --rm `
    -v ./tests:/app/tests `
    -v ./src/uploads:/app/src/uploads:ro `
    -e ANALISADOR_UPLOAD_FOLDER=/tmp/uploads-verificacao `
    app python tests/verificacao_no_conteiner.py
```

Tres detalhes do comando, e o motivo de cada um:

1. `-v ./tests:/app/tests` — a imagem **nao** tem `tests/`: o `.dockerignore` e lista de
   permissao (so `requirements.txt` e `src/` entram). O instrumento vem do host.
2. `-v ./src/uploads:/app/src/uploads:ro` — o servico monta a pasta real do operador; aqui
   ela entra **somente leitura**, e `ANALISADOR_UPLOAD_FOLDER` aponta para `/tmp` antes do
   `import app`. Nenhum byte do operador e lido pelo fluxo da verificacao nem escrito.
3. `-e ANALISADOR_UPLOAD_FOLDER=...` — a tela de entrada lista a pasta, e a lista nao pode
   depender do dado real para o resultado ser reproduzivel.

Rodar o mesmo arquivo no host tambem e valido: a parte da arte passa, e a do banco se
**pula** com a mensagem explicita (e nao como "passou").

⚠️ **Um pulo nao e um sucesso.** O veredito imprime `PULADO` nesse caso, e a contagem de
verificacoes executadas aparece ao lado do total.
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

DENTRO_DO_CONTEINER = os.path.exists("/.dockerenv")

# A pasta de upload e desviada ANTES do import do app, que cria a pasta no import.
PADRAO_ISOLADO = ("/tmp/uploads-verificacao" if DENTRO_DO_CONTEINER
                  else os.path.join(tempfile.gettempdir(), "uploads-verificacao"))
PASTA_ISOLADA = os.environ.setdefault("ANALISADOR_UPLOAD_FOLDER", PADRAO_ISOLADO)

resultados: list[tuple[str, str, str]] = []


def registrar(nome: str, situacao: str, detalhe: str) -> None:
    resultados.append((nome, situacao, detalhe))
    marca = {"OK": "ok   ", "FALHA": "FALHA", "PULADO": "pulado"}[situacao]
    print(f"  {marca}  {nome}: {detalhe}")


def sha256_de(caminho: str) -> str:
    with open(caminho, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------------------
# L-33: a arte servida dentro da imagem
# ---------------------------------------------------------------------------

ROTAS_DE_ARTE = (
    ("/apple-touch-icon.png", "image/png", "ARTE_DO_ICONE"),
    ("/banner.png", "image/png", "ARTE_DO_TOPO"),
    ("/app.css", "text/css", "ESTILO_DA_TELA"),
)


def verificar_arte() -> None:
    import app as modulo_do_app

    print("\n[L-33] arte servida dentro da imagem")
    cliente = modulo_do_app.app.test_client()

    for rota, tipo_esperado, chave in ROTAS_DE_ARTE:
        caminho = modulo_do_app.app.config[chave]
        if not os.path.isfile(caminho):
            registrar(rota, "FALHA", f"o arquivo nao existe na imagem: {caminho}")
            continue
        resposta = cliente.get(rota)
        tipo = (resposta.headers.get("Content-Type") or "").split(";")[0].strip()
        if resposta.status_code != 200:
            registrar(rota, "FALHA", f"status {resposta.status_code}, esperado 200")
            continue
        if tipo != tipo_esperado:
            registrar(rota, "FALHA", f"Content-Type {tipo!r}, esperado {tipo_esperado!r}")
            continue
        if not resposta.data:
            registrar(rota, "FALHA", "corpo vazio")
            continue
        registrar(rota, "OK",
                  f"200, {tipo}, {len(resposta.data)} bytes servidos de "
                  f"{caminho} (sha256 {sha256_de(caminho)[:16]}…)")

    tela = cliente.get("/")
    tipo_tela = (tela.headers.get("Content-Type") or "").split(";")[0].strip()
    if tela.status_code == 200 and tipo_tela == "text/html":
        registrar("GET /", "OK", f"200, {tipo_tela}, {len(tela.data)} bytes")
    else:
        registrar("GET /", "FALHA", f"status {tela.status_code}, Content-Type {tipo_tela!r}")


# ---------------------------------------------------------------------------
# L-28 / X-05: o caminho feliz de gravacao no banco
# ---------------------------------------------------------------------------

def _analise_sintetica(cm_kit_a: float, cm_kit_b: float):
    """Analise de um par, ja no formato que a projecao entrega a porta.

    Mesma forma usada por `tests/test_registro_de_analises.py`, para que a verificacao
    exercite a projecao **e** o adaptador, e nao um payload montado a mao.
    """
    from application.dna_analysis import projetar_analise

    resultado = {
        "match_name": "Ana Silva Souza",
        "csv_name": "Ana Silva Souza",
        "cm": cm_kit_a,
        "kit": "KIT-A",
        "documentary": {
            "status": "found", "label": "Irmãos", "relationship_key": "SIBLINGS", "meioses": 2,
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
            "kits": [
                {"kit": "KIT-A", "source": "GEDmatch", "total_cm": cm_kit_a,
                 "segment_count": 3, "largest_segment_cm": cm_kit_a},
                {"kit": "KIT-B", "source": "MyHeritage", "total_cm": cm_kit_b,
                 "segment_count": 1, "largest_segment_cm": cm_kit_b},
            ],
            "totals": {"cm": None},
        },
        "hypotheses": [],
        "comparison": {
            "status": "CONFLITANTE", "label": "Conflitante", "message": "m",
            "causes": ["endogamia"], "per_kit": [
                {"kit": "KIT-A", "status": "COMPATIVEL", "cm": cm_kit_a, "note": "dentro"},
                {"kit": "KIT-B", "status": "CONFLITANTE", "cm": cm_kit_b, "note": "fora"},
            ],
            "method": "scp40:Siblings",
            "expected_range": {"low": 1613, "high": 3488, "average": 2613},
            "detail": "Parentesco documental: Irmãos (2 meioses).",
            "observations": ["aviso"],
        },
        "observations": ["aviso"],
        "warnings": [],
    }
    return projetar_analise([resultado], [], "1 conexões encontradas. 0 descartadas.",
                            "verificacao__arvore.ged", "verificacao__matches.csv", "Carlos")


def verificar_banco() -> None:
    print("\n[L-28 / X-05] gravacao no banco pelo caminho feliz da porta")
    url = os.environ.get("DATABASE_URL")
    try:
        import psycopg2
    except ImportError as erro:
        if DENTRO_DO_CONTEINER:
            registrar("driver psycopg2", "FALHA",
                      f"ausente DENTRO do conteiner, onde ele deveria existir ({erro})")
        else:
            registrar("driver psycopg2", "PULADO",
                      "ausente no interpretador do host por defeito de ambiente conhecido "
                      "(OBS-02/OBS-15); rode este arquivo dentro do conteiner")
        return

    if not url:
        registrar("DATABASE_URL", "PULADO", "nao definida; a suite roda sem ela por decisao (D-17)")
        return

    from ports.adaptadores import RegistroDeAnalisesPostgres

    registro = RegistroDeAnalisesPostgres(url)
    referencia, aviso = registro.registrar(_analise_sintetica(200.0, 60.0), "unico")
    if aviso is not None or not referencia:
        registrar("registrar()", "FALHA", f"nao gravou: {aviso}")
        return
    registrar("registrar()", "OK", f"gravou e devolveu a referencia {referencia}")

    conexao = psycopg2.connect(url)
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT accepted_count, skipped_count FROM dna_analysis WHERE analysis_id = %s",
                (referencia,))
            linha = cursor.fetchone()
            if linha and linha[0] == 1 and linha[1] == 0:
                registrar("dna_analysis", "OK", f"accepted={linha[0]}, skipped={linha[1]}")
            else:
                registrar("dna_analysis", "FALHA", f"contadores inesperados: {linha}")

            cursor.execute("SELECT count(*) FROM analysis_person WHERE analysis_id = %s",
                           (referencia,))
            pessoas = cursor.fetchone()[0]
            registrar("analysis_person", "OK" if pessoas >= 2 else "FALHA",
                      f"{pessoas} pessoa(s) — a raiz, o match e os nos do caminho")

            cursor.execute(
                "SELECT matched_person_xref FROM match_result WHERE analysis_id = %s",
                (referencia,))
            resultado = cursor.fetchone()
            registrar("match_result", "OK" if resultado and resultado[0] else "FALHA",
                      f"matched_person_xref={resultado[0] if resultado else None} "
                      "(a FK composta exige a pessoa gravada)")

            cursor.execute(
                """
                SELECT k.total_cm FROM match_kit k
                  JOIN match_result m USING (match_id)
                 WHERE m.analysis_id = %s ORDER BY k.ordinal
                """, (referencia,))
            cms = [float(valor[0]) for valor in cursor.fetchall()]
            if cms == [200.0, 60.0]:
                registrar("match_kit", "OK", f"cM por kit preservados: {cms} (nunca somados)")
            else:
                registrar("match_kit", "FALHA", f"os cM dos kits foram somados ou trocados: {cms}")

            cursor.execute(
                "SELECT role FROM match_path_node WHERE analysis_id = %s ORDER BY ordinal",
                (referencia,))
            papeis = [valor[0] for valor in cursor.fetchall()]
            dominio = {"ascendente", "descendente", "afinidade"}
            if len(papeis) >= 2 and set(papeis) <= dominio:
                registrar("match_path_node", "OK", f"{len(papeis)} nos, papeis {papeis}")
            else:
                registrar("match_path_node", "FALHA", f"papeis fora do dominio fechado: {papeis}")

            cursor.execute("SELECT count(*) FROM skipped_match WHERE analysis_id = %s",
                           (referencia,))
            descartados = cursor.fetchone()[0]
            registrar("skipped_match", "OK" if descartados == 0 else "FALHA",
                      f"{descartados} descartado(s), esperado 0")
    finally:
        conexao.close()

    limpeza = psycopg2.connect(url)
    try:
        with limpeza:
            with limpeza.cursor() as cursor:
                cursor.execute("DELETE FROM dna_analysis WHERE tree_ref = %s",
                               ("verificacao__arvore.ged",))
        with limpeza.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM dna_analysis WHERE tree_ref = %s",
                           ("verificacao__arvore.ged",))
            restantes = cursor.fetchone()[0]
        registrar("limpeza", "OK" if restantes == 0 else "FALHA",
                  f"{restantes} linha(s) do teste restantes no historico")
    finally:
        limpeza.close()


def main() -> int:
    print("=" * 78)
    print("verificacao no conteiner — arte servida e gravacao no banco")
    print(f"pasta de upload isolada em: {PASTA_ISOLADA}")
    print(f"rodando dentro de conteiner: {'sim' if DENTRO_DO_CONTEINER else 'nao (host)'}")
    print("=" * 78)

    verificar_arte()
    verificar_banco()

    falhas = [nome for nome, situacao, _ in resultados if situacao == "FALHA"]
    pulados = [nome for nome, situacao, _ in resultados if situacao == "PULADO"]
    print("\n" + "=" * 78)
    print(f"verificacoes: {len(resultados)} | "
          f"executadas: {len(resultados) - len(pulados)} | "
          f"falhas: {len(falhas)} | puladas: {len(pulados)}")
    if pulados:
        print(f"puladas: {', '.join(pulados)} — um pulo NAO e um sucesso")
    if falhas:
        print(f"RESULTADO: FALHA em {', '.join(falhas)}")
        return 1
    print("RESULTADO: todas as verificacoes executadas passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
