"""Estado do GEDCOM carregado e acesso aos registros.

Responsabilidade unica: ser o registro do estado do processo (singleton, nao
persistente) e dar acesso aos registros de pessoa e de familia.

## Contrato de estado

`load_gedcom_and_build_graph`, em `gedcom_parser`, muta `people`, `families` e
`child_to_family` in place (`clear()` mais `update()`) para que o binding
importado no topo pelos outros modulos continue apontando para o objeto vivo.
`graph` e a excecao: e reatribuido, e por isso quem o consome o importa dentro da
funcao (ver `path_finding.py`).

Extraido de `upload.py` pela OPP-20261003-TWNT. As globais e as funcoes sao as
mesmas; o que mudou foi o endereco.

## Transicao para o modulo puro (feature 005, T008)

`ref_id` e `get_name` NAO sao estado: sao leitura de registro, e agora vivem em
`core/registro.py`. Eles continuam sendo reexportados aqui **apenas** enquanto
houver consumidor importando deste modulo; a migracao de cada consumidor e a
remocao final do estado estao em `_reversa_forward/005-nucleo-puro-src/actions.md`
(`T011` a `T014`, `T023`).
"""
from __future__ import annotations

from .registro import get_name, ref_id  # noqa: F401  reexport de transicao

# Estado global em memória (singleton por processo) — não persistente.
people = {}
families = {}
graph = None
child_to_family: dict[str, list[str]] = {}

# Contador de carregamentos. `people`/`families` sao mutados in place, entao o
# `id()` deles nao muda quando outro GEDCOM entra; quem guarda indice derivado
# (ex.: nome normalizado -> ids, em `documentary_relationship`) precisa de um
# sinal de invalidacao que o rebind nao da. Este contador e esse sinal, e e
# incrementado por `load_gedcom_and_build_graph`.
versao = 0

