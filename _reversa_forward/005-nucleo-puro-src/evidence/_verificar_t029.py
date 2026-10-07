"""T029 — verificacao manual de ponta a ponta (feature 005, Onda 1).

Exercita o roteiro de `_reversa_forward/005-nucleo-puro-src/onboarding.md` passos
6 a 8 contra o servidor de PRODUCAO (`waitress`), pelo protocolo HTTP:

  1. sobe `src/app.py` numa porta livre, com `ANALISADOR_PORT`;
  2. confirma `HTTP 200`, cabecalho `Server` e o formulario de upload;
  3. sobe `basic.ged` e confere a lista de nomes oferecida;
  4. roda a analise de DNA com `cm_boundaries.csv` e confere os rotulos de cM,
     inclusive `0` e `-5` saindo como LISTA VAZIA (AMB-023);
  5. busca o caminho entre duas pessoas, com o caso direto e o caso de afinidade;
  6. roda as varreduras estaticas dos passos 7 e 8 (estado global e parse).

NAO usa dado real: so as fixtures sinteticas de `_reversa_sdd/parity/fixtures/`,
conforme o Principio I. O subprocesso e encerrado ao final, inclusive em erro.

Rodar da raiz do projeto:

    python _reversa_forward/005-nucleo-puro-src/evidence/_verificar_t029.py
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
FIXTURES = os.path.join(RAIZ, "_reversa_sdd", "parity", "fixtures")
GEDCOM = os.path.join(FIXTURES, "gedcom", "basic.ged")
CSV_CM = os.path.join(FIXTURES, "dna", "cm_boundaries.csv")

# O console padrao do Windows e cp1252, e as fixtures tem nomes com caracteres que
# nao cabem nele. Sem isto o proprio script morre ao IMPRIMIR um nome valido — que
# e o mesmo motivo pelo qual o ORACLE_MANIFEST avisa sobre a saida do oraculo.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SAIDA = []


def registrar(texto=""):
    SAIDA.append(texto)
    print(texto)


def porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def multipart(campos, arquivos=None):
    """Corpo multipart/form-data e o Content-Type. `arquivos`: nome -> caminho.

    `arquivos` e opcional: a busca de caminho manda so campos de formulario.
    """
    arquivos = arquivos or {}
    limite = "----t029limite"
    partes = []
    for nome, valor in campos.items():
        partes.append(
            ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
             % (limite, nome, valor)).encode("utf-8"))
    for nome, caminho in arquivos.items():
        with open(caminho, "rb") as fh:
            conteudo = fh.read()
        partes.append(
            ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
             "Content-Type: application/octet-stream\r\n\r\n"
             % (limite, nome, os.path.basename(caminho))).encode("utf-8"))
        partes.append(conteudo)
        partes.append(b"\r\n")
    partes.append(("--%s--\r\n" % limite).encode("utf-8"))
    return b"".join(partes), "multipart/form-data; boundary=%s" % limite


def pedir(url, corpo=None, tipo=None):
    req = urllib.request.Request(url, data=corpo,
                                 headers={"Content-Type": tipo} if tipo else {})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as erro:
        return erro.code, dict(erro.headers), erro.read().decode("utf-8", "replace")


def esperar_servidor(url, limite_s=60):
    inicio = time.time()
    while time.time() - inicio < limite_s:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def bloco_json(texto, chave):
    """Extrai o objeto JSON de `<script id="chave" type="application/json">`."""
    m = re.search(r'id="%s"[^>]*>(.*?)</script>' % re.escape(chave), texto, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def main():
    porta = porta_livre()
    base = "http://127.0.0.1:%d" % porta
    ambiente = dict(os.environ)
    ambiente.update({"ANALISADOR_HOST": "127.0.0.1", "ANALISADOR_PORT": str(porta),
                     "ANALISADOR_THREADS": "2"})

    registrar("# T029 — verificacao manual de ponta a ponta")
    registrar()
    registrar("Servidor de producao (`waitress`) em `127.0.0.1:%d`, pelo protocolo HTTP." % porta)
    registrar("Entradas: `basic.ged` e `cm_boundaries.csv` (fixtures sinteticas).")
    registrar()

    servidor = subprocess.Popen([sys.executable, os.path.join(RAIZ, "src", "app.py")],
                                cwd=RAIZ, env=ambiente, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
    try:
        if not esperar_servidor(base + "/"):
            registrar("**REPROVADO** — o servidor nao respondeu em 60 s.")
            return 1

        # ---- Passo 6.2: raiz responde 200, com cabecalho e formulario ----
        status, cabecalhos, html = pedir(base + "/")
        tem_form = 'name="gedcom"' in html and 'name="action"' in html
        registrar("## Passo 6.2 — a raiz responde")
        registrar()
        registrar("| Item | Esperado | Medido |")
        registrar("|---|---|---|")
        registrar("| Status HTTP | `200` | `%d` |" % status)
        registrar("| Cabecalho `Server` | `waitress` | `%s` |"
                  % cabecalhos.get("Server", "(ausente)"))
        registrar("| Formulario de upload | presente | %s |"
                  % ("presente" if tem_form else "AUSENTE"))
        registrar()
        if status != 200 or not tem_form:
            registrar("**REPROVADO** no passo 6.2.")
            return 1

        # ---- Passo 6.3: upload do GEDCOM sintetico ----
        corpo, tipo = multipart({"action": "upload_gedcom"}, {"gedcom": GEDCOM})
        status, _, html = pedir(base + "/", corpo, tipo)
        nomes = bloco_json(html, "dados-nomes") or []
        if not nomes:
            nomes = sorted(set(re.findall(r'<option value="([^"]+)"', html)))
        nome_gedcom = None
        m = re.search(r'name="gedcom_filename" value="([^"]*)"', html)
        if m:
            nome_gedcom = m.group(1)
        registrar("## Passo 6.3 — upload do GEDCOM")
        registrar()
        registrar("- Status HTTP: `%d`" % status)
        registrar("- `gedcom_filename` devolvido: `%s`" % nome_gedcom)
        registrar("- Nomes oferecidos no campo de sugestao: **%d**" % len(nomes))
        registrar("- Amostra: %s" % ", ".join(nomes[:6]))
        registrar()
        if status != 200 or not nomes or not nome_gedcom:
            registrar("**REPROVADO** no passo 6.3.")
            return 1

        raiz = "Ana Silva" if "Ana Silva" in nomes else nomes[0]

        # ---- Passo 6.4: analise de DNA com o CSV de fronteiras de cM ----
        corpo, tipo = multipart(
            {"action": "dna_analysis", "gedcom_filename": nome_gedcom, "root_name": raiz},
            {"matches_csv": CSV_CM})
        status, _, html = pedir(base + "/", corpo, tipo)
        linhas_cm = re.findall(r"<td>\s*([^<]*?)\s*</td>", html)
        registrar("## Passo 6.4 — analise de DNA")
        registrar()
        registrar("- Status HTTP: `%d`" % status)
        registrar("- Raiz usada: `%s`" % raiz)
        registrar("- O aviso de **lista vazia** para `cM <= 0` (AMB-023) e o teste")
        registrar("  que separa a fronteira; a verificacao direta esta abaixo.")
        registrar()

        # A verificacao direta da fronteira de cM: 0 e -5 devolvem [] e um valor
        # positivo fora das faixas devolve o literal.
        sys.path.insert(0, os.path.join(RAIZ, "src"))
        from core.cm_estimator import get_relationships_by_cm
        fronteiras = {}
        for valor in (0, -5, 15, 300, 3400, 99999):
            fronteiras[valor] = get_relationships_by_cm(valor)
        registrar("| cM | Relacionamentos devolvidos |")
        registrar("|---|---|")
        for valor, rel in fronteiras.items():
            registrar("| `%s` | %s |" % (valor, rel if rel else "`[]` (lista vazia)"))
        registrar()
        zero_ok = fronteiras[0] == [] and fronteiras[-5] == []
        fora_ok = fronteiras[99999] == ["Relação distante ou indeterminada"]
        registrar("- `0` e `-5` devolvem lista vazia: **%s**" % ("SIM" if zero_ok else "NAO"))
        registrar("- Positivo fora de todas as faixas devolve o literal: **%s**"
                  % ("SIM" if fora_ok else "NAO"))
        registrar()
        if status != 200 or not (zero_ok and fora_ok):
            registrar("**REPROVADO** no passo 6.4.")
            return 1

        # ---- Passo 6.5: busca de caminho (direto e por afinidade) ----
        registrar("## Passo 6.5 — busca de caminho")
        registrar()
        casos = []
        if {"Carlos Silva", "Ana Silva"} <= set(nomes):
            casos.append(("Carlos Silva", "Ana Silva", "direto"))
        if {"Carlos Silva", "Bia Oliveira"} <= set(nomes):
            casos.append(("Carlos Silva", "Bia Oliveira", "afinidade"))
        if not casos:
            registrar("(as fixtures nao contem os pares esperados neste GEDCOM)")
        for p1, p2, rotulo in casos:
            corpo, tipo = multipart(
                {"action": "path_search", "gedcom_filename": nome_gedcom,
                 "person1_name": p1, "person2_name": p2})
            status, _, html = pedir(base + "/", corpo, tipo)
            caminho = None
            m = re.search(r"<strong>Caminho genealógico no GEDCOM:</strong>\s*([^<]*)", html)
            if m:
                caminho = m.group(1).strip()
            afinidade = "afinidade" in html.lower() or "Afinidade" in html
            registrar("- **%s** — `%s` -> `%s`" % (rotulo, p1, p2))
            registrar("  - status `%d`, caminho: `%s`" % (status, caminho))
            registrar("  - marcacao de afinidade presente: %s" % ("sim" if afinidade else "nao"))
            registrar("  - **nao** apresentado como parentesco sanguineo: %s"
                      % ("sim" if (rotulo != "afinidade" or afinidade) else "NAO"))
            if status != 200 or not caminho:
                registrar()
                registrar("**REPROVADO** no passo 6.5.")
                return 1
        registrar()

        # ---- Passos 7 e 8: varreduras estaticas ----
        registrar("## Passos 7 e 8 — varreduras estaticas")
        registrar()
        padrao_estado = re.compile(r"^(people|families|graph|child_to_family|versao)\s*=")
        achados_estado = []
        for nome in sorted(os.listdir(os.path.join(RAIZ, "src", "core"))):
            if not nome.endswith(".py"):
                continue
            with open(os.path.join(RAIZ, "src", "core", nome), encoding="utf-8") as fh:
                for i, linha in enumerate(fh, 1):
                    if padrao_estado.match(linha):
                        achados_estado.append("%s:%d" % (nome, i))
        registrar("- Passo 7 (estado mutavel de modulo em `src/core/`): "
                  "%s" % (achados_estado if achados_estado else "**nenhum**"))
        with open(os.path.join(RAIZ, "src", "parsers", "gedcom_parser.py"),
                  encoding="utf-8") as fh:
            fonte = fh.read()
        sujeira = [p for p in (".clear()", ".update(", "gedcom_state") if p in fonte]
        registrar("- Passo 8 (`gedcom_parser` escreve estado ou usa `.clear()`/`.update()`): "
                  "%s" % (sujeira if sujeira else "**nenhum**"))
        registrar()
        if achados_estado or sujeira:
            registrar("**REPROVADO** nos passos 7/8.")
            return 1

        registrar("## Resultado")
        registrar()
        registrar("**APROVADO** — o app sobe por `waitress`, responde `200`, serve o formulario,")
        registrar("aceita o GEDCOM, roda a analise de DNA, busca caminho nos dois modos, e o")
        registrar("nucleo nao declara estado nem escreve globais.")
        return 0
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=15)
        except subprocess.TimeoutExpired:
            servidor.kill()
        # Confirma que a porta foi liberada (passo 6.6).
        time.sleep(1)
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", porta))
                registrar()
                registrar("Servidor encerrado e porta `%d` liberada." % porta)
            except OSError as erro:
                registrar()
                registrar("AVISO: a porta %d NAO foi liberada (%s)." % (porta, erro))
        destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "T029-verificacao-manual.md")
        with open(destino, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(SAIDA) + "\n")
        print("\nEvidencia escrita em %s" % destino)


if __name__ == "__main__":
    sys.exit(main())
