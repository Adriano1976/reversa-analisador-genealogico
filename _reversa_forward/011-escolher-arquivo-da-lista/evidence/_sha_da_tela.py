"""Mede o sha256 do HTML de `GET /` do jeito que `test_icone_de_atalho.py` mede.

Mesmo fixture (`cliente_de_upload`) e mesmo estado: pasta de upload temporaria e VAZIA.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sys
import uuid
from pathlib import Path

RAIZ = None
for c in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
    if (c / "src" / "utils" / "validate.py").is_file():
        RAIZ = c
        break
PASTA_APP = RAIZ / "src"

tmp = RAIZ / "tests" / ".tmp" / uuid.uuid4().hex
tmp.mkdir(parents=True)
uploads = tmp / "uploads"
uploads.mkdir()
os.environ["ANALISADOR_UPLOAD_FOLDER"] = str(uploads)

for caminho in (str(RAIZ), str(PASTA_APP)):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

spec = importlib.util.spec_from_file_location("_app_sha_011", str(PASTA_APP / "app.py"))
modulo = importlib.util.module_from_spec(spec)
modulo.__file__ = str(PASTA_APP / "app.py")
spec.loader.exec_module(modulo)
modulo.app.root_path = str(PASTA_APP)

corpo = modulo.app.test_client().get("/").get_data()
print("bytes:", len(corpo))
print("sha256:", hashlib.sha256(corpo).hexdigest())

shutil.rmtree(tmp, ignore_errors=True)
