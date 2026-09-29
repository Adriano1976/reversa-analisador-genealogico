---
schema_version: 1
id: OPP-20260929-SEQO
verb: prune
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: death-proof
  evidence:
    - before-after/death-proof.txt
    - safety-net/smoke-after-apply.txt
    - safety-net/pytest-after-apply.txt
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/app.py
    purpose: Remove STATIC_FOLDER e o makedirs correspondente: residuo da pasta do pyvis, sem nenhum consumidor
    diff: CHG-001.diff
  - chg: CHG-002
    kind: configuration
    artifact: analisador-genealogico/requirements.txt
    purpose: Remove matplotlib e pyvis, declarados e nunca importados em nenhum arquivo do repositorio
    diff: CHG-002.diff
approval:
  by: user
  at: 2026-09-29T03:02:56-03:00
reversible_via: [CHG-001.diff, CHG-002.diff]
---

## O que foi feito

Varredura de morte em 406 arquivos do repositorio inteiro, nao so no app, porque
`requirements.txt` e um manifesto que scripts de diagnostico podem consumir. Resultado: **zero**
imports de `matplotlib` e `pyvis` em qualquer arquivo.

Nuance provada, nao argumentada: `app = Flask(__name__)` usa o padrao do framework e portanto
**continua registrando a rota `/static/<path:filename>`** depois da remocao. A equivalencia de rotas
carrega as duas versoes do app como modulos distintos e compara `url_map`, `static_folder` relativo,
`static_url_path` e views: tudo identico.

Orfao suspeito registrado e **nao** removido: `ensure_dirs` (`upload.py:24`), chamado apenas pelo
proprio teste.

Divergencias de documentacao deixadas registradas para decisao: `README.md:25` ainda anuncia o grafo
`pyvis`, e `ORACLE_MANIFEST.md` lista as duas dependencias no ambiente do oraculo.

## Estado dos arquivos

`86 e 9` linhas antes, `84 e 7` depois.
