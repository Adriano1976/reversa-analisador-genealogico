"""Smoke test do comando documentado `python src/app.py`, pela via HTTP real.

Fecha por medicao dois achados da auditoria cruzada:

  A001  nenhuma acao do plano verificava a execucao do aplicativo COMO SCRIPT.
        A suite cobre o aplicativo importado como modulo, com o caminho de busca
        manipulado pelo proprio teste -- modo de execucao diferente do comando
        publicado no README.

  A003  o cenario de aceite do upload e verificado apenas por um teste que nao
        roda neste ambiente (erro de permissao de diretorio temporario). Aqui o
        ciclo upload -> parse -> tela carregada e exercitado de verdade.

Cuidados:
  - A primeira requisicao usa a configuracao PADRAO do aplicativo. Como e um GET,
    nada e gravado: a pasta de dados reais nao e tocada.
  - A segunda requisicao faz POST de um GEDCOM SINTETICO, com a pasta de upload
    apontada para um diretorio de trabalho proprio. Nenhum dado real e lido e
    nada é gravado em src/uploads/.
"""
import http.client
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

NL = chr(10)
PORTA = 5000
BASE = "http://127.0.0.1:%d/" % PORTA
EVIDENCIA = pathlib.Path("_reversa_forward/003-renomear-pasta-app-para-src/evidence/smoke-src-app.txt")

sys.path.insert(0, os.getcwd())
from tests.fixtures.sample_gedcom import SAMPLE_GED  # noqa: E402


def porta_ocupada():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORTA)) == 0


def requisitar(metodo, corpo=None, cabecalhos=None):
    req = urllib.request.Request(BASE, data=corpo, headers=cabecalhos or {}, method=metodo)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def corpo_multipart(gedcom):
    # Multipart exige CRLF como separador de linha; LF sozinho faz o parser nao
    # encontrar a parte do arquivo e o upload chega vazio.
    crlf = chr(13) + chr(10)
    b = "----reversa003"
    partes = []
    partes.append("--" + b + crlf + 'Content-Disposition: form-data; name="action"' + crlf + crlf + "upload_gedcom" + crlf)
    partes.append("--" + b + crlf +
                  'Content-Disposition: form-data; name="gedcom"; filename="sintetico.ged"' + crlf +
                  "Content-Type: application/octet-stream" + crlf + crlf)
    corpo = "".join(partes).encode("utf-8") + gedcom.encode("utf-8") + (crlf + "--" + b + "--" + crlf).encode("utf-8")
    return corpo, "multipart/form-data; boundary=" + b


def main():
    linhas = []
    linhas.append("Smoke test do comando documentado: python src/app.py")
    linhas.append("Feature: 003-renomear-pasta-app-para-src | verificacao adicional do executor")
    linhas.append("Fecha por medicao os achados A001 (execucao como script) e A003 (ciclo de upload) da auditoria.")
    linhas.append("Data: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    linhas.append("Comando: python src/app.py, a partir da raiz do repositorio")
    linhas.append("")

    if porta_ocupada():
        linhas.append("ABORTADO: a porta %d ja esta em uso; o teste nao pode isolar o resultado." % PORTA)
        EVIDENCIA.write_text(NL.join(linhas) + NL, encoding="utf-8", newline="")
        print("ABORTADO: porta em uso")
        return 1

    # Pasta de trabalho propria para o upload sintetico: nao toca em src/uploads/.
    # Fica DENTRO do workspace de proposito: o ambiente nega escrita no diretorio
    # temporario do sistema (mesma restricao que faz 15 testes da suite falharem).
    trabalho = pathlib.Path("_reversa_forward/003-renomear-pasta-app-para-src/evidence/smoke-uploads")
    if trabalho.exists():
        for velho in trabalho.glob("*"):
            velho.unlink()
    trabalho.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ANALISADOR_UPLOAD_FOLDER=str(trabalho))
    log = EVIDENCIA.parent / "smoke-src-app-saida.txt"
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen([sys.executable, "src/app.py"], stdout=fh, stderr=subprocess.STDOUT, env=env)

    linhas.append("processo iniciado; pid = %d" % proc.pid)
    linhas.append("pasta de upload apontada para diretorio de trabalho (sem tocar em src/uploads/): " + str(trabalho))
    linhas.append("")

    resultados = {}

    # --- requisicao 1: pagina inicial, configuracao padrao do aplicativo ---
    status = None
    corpo = ""
    inicio = time.time()
    while time.time() - inicio < 25:
        if proc.poll() is not None:
            linhas.append("O PROCESSO MORREU antes de responder (codigo %s)" % proc.returncode)
            break
        try:
            status, corpo = requisitar("GET")
            break
        except urllib.error.URLError:
            time.sleep(0.5)
        except Exception as e:
            linhas.append("erro ao requisitar: %r" % (e,))
            time.sleep(0.5)

    linhas.append("[1] GET / (pagina inicial, sem arvore carregada)")
    linhas.append("    resposta HTTP: %s   bytes: %d" % (status, len(corpo)))
    resultados["http_200"] = status == 200
    resultados["formulario_upload"] = 'value="upload_gedcom"' in corpo
    resultados["biblioteca_diagrama"] = "mermaid" in corpo.lower()
    linhas.append('    formulario de upload presente (value="upload_gedcom"): %s' % resultados["formulario_upload"])
    linhas.append("    biblioteca de diagrama presente (mermaid): %s" % resultados["biblioteca_diagrama"])
    linhas.append('    abas condicionais ausentes, como esperado: value="path_search" = %s, value="dna_analysis" = %s'
                  % ('value="path_search"' in corpo, 'value="dna_analysis"' in corpo))
    linhas.append("    causa: o template renderiza as duas abas apenas quando ha arvore carregada")
    linhas.append("")

    # --- requisicao 2: upload sintetico, exercitando o ciclo completo ---
    corpo2 = ""
    status2 = None
    if proc.poll() is None:
        try:
            dados, tipo = corpo_multipart(SAMPLE_GED)
            status2, corpo2 = requisitar("POST", dados, {"Content-Type": tipo})
        except Exception as e:
            linhas.append("erro no POST de upload: %r" % (e,))

    linhas.append("[2] POST / com action=upload_gedcom (GEDCOM sintetico das fixtures)")
    linhas.append("    resposta HTTP: %s   bytes: %d" % (status2, len(corpo2)))
    resultados["upload_confirmado"] = "carregado" in corpo2
    resultados["aba_busca"] = 'value="path_search"' in corpo2
    resultados["aba_dna"] = 'value="dna_analysis"' in corpo2
    linhas.append("    confirmacao de carga na tela: %s" % resultados["upload_confirmado"])
    linhas.append('    aba de busca de caminho presente (value="path_search"): %s' % resultados["aba_busca"])
    linhas.append('    aba de analise de DNA presente (value="dna_analysis"): %s' % resultados["aba_dna"])
    import re as _re
    _texto = " ".join(_re.sub("<[^>]+>", " ", corpo2).split())
    linhas.append("    texto visivel da resposta: " + _texto[:500])
    linhas.append("")

    # --- encerramento ---
    try:
        import psutil
        pai = psutil.Process(proc.pid)
        filhos = pai.children(recursive=True)
        for c in filhos:
            c.terminate()
        pai.terminate()
        psutil.wait_procs(filhos + [pai], timeout=10)
        sobraram = [p.pid for p in filhos + [pai] if p.is_running()]
        linhas.append("encerramento: pids remanescentes = %s" % (sobraram or "nenhum"))
    except Exception as e:
        proc.kill()
        linhas.append("encerramento por psutil falhou (%r); kill direto aplicado" % (e,))

    time.sleep(1.0)
    linhas.append("porta %d livre apos o encerramento: %s" % (PORTA, not porta_ocupada()))
    linhas.append("pasta de dados reais intocada: src/uploads/ com %d arquivos"
                  % len(list(pathlib.Path("src/uploads").glob("*"))))

    # prova de que o ciclo de gravacao completou, sem sujar o repositorio
    gravados = sorted(p.name for p in trabalho.glob("*"))
    linhas.append("arquivos gravados na pasta de trabalho do teste: %s" % (gravados or "nenhum"))
    for p in trabalho.glob("*"):
        p.unlink()
    trabalho.rmdir()
    linhas.append("pasta de trabalho do teste removida: %s" % (not trabalho.exists()))
    linhas.append("")
    linhas.append("")

    ok = all(resultados.values())
    linhas.append("VEREDITO: " + ("o comando documentado sobe a aplicacao, serve a tela e completa o ciclo de carga."
                                   if ok else
                                   "algum marcador esperado nao apareceu; ver detalhe acima."))

    EVIDENCIA.write_text(NL.join(linhas) + NL, encoding="utf-8", newline="")
    for l in linhas:
        print(l)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
