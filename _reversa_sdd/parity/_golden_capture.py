"""Captura os golden files de tela do oraculo legado (Onda 0 / AMB-022).

## Por que este script existe

`_reversa_sdd/screens/golden/manifest.yaml` descreve o comando de captura de cada tela,
mas em v1 a captura automatizada e OQ-02 (nao implementada): o manifesto instrui o
usuario a rodar manualmente. Este script executa esses comandos de forma reprodutivel
e preenche o manifesto, eliminando a captura manual.

## Isolamento do legado (regra absoluta)

O oraculo cria `uploads/` e `static/` no DIRETORIO DE TRABALHO e grava os arquivos
enviados la. Para NAO escrever nada em `src/`:

1. copia o projeto legado para `.golden-capture/app/` (area descartavel);
2. copia o oraculo congelado para la como `legacy_oracle.py`;
3. faz chdir para essa copia ANTES de importar.

Assim o legado real permanece intocado e os uploads temporarios ficam na copia.

## Determinismo

O oraculo sobe com `use_reloader=False` (sem processo filho e sem restart no meio da
captura). Os fixtures sao fixos no manifesto. A captura NAO depende de relogio.

## Ordem de execucao obrigatoria

    1. python _golden_capture.py          # SCR-001, G02, 002, 003, 004, 005
    2. python _golden_extract_g01.py      # SCR-G01 (derivado do SCR-002)
    3. python _golden_manifest_patch.py   # preenche o manifest.yaml

O SCR-G01 **nao** tem requisicao propria: e um recorte do bloco de alerta de sucesso
dentro do SCR-002, por isso o passo 2 e separado. Rodar so o passo 1 deixa o G01 com
`present: false`.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEGACY = os.path.join(ROOT, "src")
ORACLE = os.path.join(ROOT, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py")
GOLDEN = os.path.join(ROOT, "_reversa_sdd", "screens", "golden")
WORK = os.path.join(ROOT, ".golden-capture")
APPDIR = os.path.join(WORK, "app")

# Trio deterministico do SCR-005, descoberto por MEDICAO em `_scr005_find_trio.py`:
# entre 6 GEDCOMs x 6 CSVs reais, este par e o que casa mais linhas (393) por nome
# exato, com o root_name resolvendo para UMA pessoa unica (@I804@).
# Ordem de preferencia: o primeiro que existir e casar e usado.
SCR005_FIXTURES = [
    ("sssazevedo_2025-10-07.ged", "DNA_Matches_Sandro.csv", "Luiz de Freitas Melro Neto"),
]


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def preparar_isolamento() -> None:
    # ATENCAO — apagar WORK inteiro destroi `capturas.json`, que e a proveniencia das
    # capturas anteriores. Isso ja aconteceu uma vez e obrigou a re-extrair o SCR-G01
    # (que e DERIVADO do SCR-002, nao capturado por requisicao propria). Por isso
    # apagamos apenas a copia do app.
    shutil.rmtree(APPDIR, ignore_errors=True)
    os.makedirs(WORK, exist_ok=True)
    # Copia o legado, mas NAO os uploads do usuario (dados reais, nao precisamos deles).
    shutil.copytree(LEGACY, APPDIR, ignore=shutil.ignore_patterns("uploads", "__pycache__", "*.pyc"))
    os.makedirs(os.path.join(APPDIR, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(APPDIR, "static"), exist_ok=True)
    shutil.copyfile(ORACLE, os.path.join(APPDIR, "legacy_oracle.py"))


LAUNCHER = r'''
import os, sys, threading, time
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import importlib.util
spec = importlib.util.spec_from_file_location("legacy_oracle", "legacy_oracle.py")
m = importlib.util.module_from_spec(spec); sys.modules["legacy_oracle"] = m
spec.loader.exec_module(m)
port = int(sys.argv[1])
# use_reloader=False: sem processo filho, sem restart no meio da captura.
m.app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
'''


def subir_oraculo(port: int) -> subprocess.Popen:
    runner = os.path.join(APPDIR, "_launcher.py")
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(LAUNCHER)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([sys.executable, runner, str(port)], cwd=APPDIR, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def esperar(port: int, timeout=60) -> bool:
    fim = time.time() + timeout
    while time.time() < fim:
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=3).read()
            return True
        except Exception:
            time.sleep(0.4)
    return False


def http(url: str, dados: bytes | None = None, content_type: str | None = None) -> tuple[int, str]:
    req = urllib.request.Request(url, data=dados)
    if content_type:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def multipart(campos: dict[str, str], arquivos: dict[str, tuple[str, bytes]]) -> tuple[bytes, str]:
    """Monta um corpo multipart/form-data sem depender de requests."""
    b = "----golden" + hashlib.md5(str(time.time()).encode()).hexdigest()
    out = bytearray()
    for k, v in campos.items():
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
    for k, (nome, conteudo) in arquivos.items():
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % (b, k, nome)).encode()
        out += conteudo + b"\r\n"
    out += ("--%s--\r\n" % b).encode()
    return bytes(out), "multipart/form-data; boundary=%s" % b


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else free_port()
    preparar_isolamento()
    os.makedirs(GOLDEN, exist_ok=True)
    print("=" * 74)
    print("CAPTURA DE GOLDEN FILES — oraculo isolado em %s" % os.path.relpath(APPDIR, ROOT))
    print("porta %d | legado real NAO e tocado" % port)
    print("=" * 74, flush=True)

    proc = subir_oraculo(port)
    try:
        if not esperar(port):
            print("ERRO: o oraculo nao respondeu em 60s")
            return 1
        base = "http://127.0.0.1:%d/" % port
        ged = open(os.path.join(ROOT, "_reversa_sdd", "upload-gedcom", "exemplo_familia.ged"), "rb").read()
        resultados = []

        def gravar(nome: str, status: int, corpo: str, como: str) -> None:
            p = os.path.join(GOLDEN, nome)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(corpo)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            resultados.append({"name": nome, "status": status, "sha256": h,
                               "bytes": len(corpo.encode("utf-8")), "capture": como})
            print("  %-34s HTTP %s  %7d bytes  sha256 %s" % (nome, status, len(corpo.encode("utf-8")), h[:16]))
            print("      via: %s" % como, flush=True)

        # SCR-001 — estado inicial, sem fixture.
        st, corpo = http(base)
        gravar("SCR-001-initial-upload.html.txt", st, corpo, "GET /")

        # SCR-G02 — submeter SEM arquivo (mensagem congelada BR-MIGRAR-028).
        body, ct = multipart({"action": "upload_gedcom"}, {})
        st, corpo = http(base, body, ct)
        gravar("SCR-G02-alert-error.html.txt", st, corpo, "POST / action=upload_gedcom (sem arquivo)")

        # SCR-002 — hub carregado (fixture GEDCOM).
        body, ct = multipart({"action": "upload_gedcom"}, {"gedcom": ("exemplo_familia.ged", ged)})
        st, corpo = http(base, body, ct)
        gravar("SCR-002-loaded-hub.html.txt", st, corpo, "POST / action=upload_gedcom (exemplo_familia.ged)")

        # SCR-003 / SCR-004 — mesmo documento do hub, secoes distintas do template.
        gravar("SCR-003-path-search-tab.html.txt", st, corpo, "idem SCR-002 (painel de aba)")
        gravar("SCR-004-dna-analysis-tab.html.txt", st, corpo, "idem SCR-002 (painel de aba)")

        # SCR-005 — regiao de resultados da analise de DNA.
        #
        # O oraculo NAO usa sessao: ele re-le o GEDCOM DO DISCO pelo nome enviado no
        # campo oculto `gedcom_filename` (L579). Entao a analise exige que o GEDCOM ja
        # esteja no uploads da copia — o upload de SCR-002 (feito acima, mesma fixture)
        # garante isso. Os fixtures vem dos DADOS REAIS em uploads/, lidos do path
        # original: nada e escrito no legado.
        for ged_nome, csv_nome, root in SCR005_FIXTURES:
            gp = os.path.join(LEGACY, "uploads", ged_nome)
            cp = os.path.join(LEGACY, "uploads", csv_nome)
            if not (os.path.exists(gp) and os.path.exists(cp)):
                print("  SCR-005 PULADO — fixture ausente: %s / %s" % (ged_nome, csv_nome), flush=True)
                continue
            # 1) Garante o GEDCOM no uploads da copia isolada (mesmo nome de arquivo).
            gbytes = open(gp, "rb").read()
            body, ct = multipart({"action": "upload_gedcom"}, {"gedcom": (ged_nome, gbytes)})
            http(base, body, ct)
            # 2) Roda a analise de DNA com o CSV de matches e o root_name.
            cbytes = open(cp, "rb").read()
            body, ct = multipart(
                {"action": "dna_analysis", "gedcom_filename": ged_nome, "root_name": root},
                {"matches_csv": (csv_nome, cbytes)},
            )
            st, corpo = http(base, body, ct)
            gravar("SCR-005-results-region.html.txt", st, corpo,
                   "POST / action=dna_analysis | gedcom=%s | csv=%s | root=%r" % (ged_nome, csv_nome, root))

        print()
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
        with open(os.path.join(WORK, "capturas.json"), "w", encoding="utf-8") as fh:
            json.dump(resultados, fh, ensure_ascii=False, indent=2)
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
