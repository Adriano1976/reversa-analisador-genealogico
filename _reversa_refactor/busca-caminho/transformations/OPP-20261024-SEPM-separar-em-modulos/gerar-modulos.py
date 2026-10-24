"""Gera os quatro modulos novos e a fachada, por recorte de linhas do arquivo atual.

Mecanico de proposito: cada trecho e copiado VERBATIM, sem redigitacao, e o script confere
que cada fatia comeca e termina no token esperado antes de escrever. As unicas mudancas de
texto sao as tres renomeacoes declaradas no plano (`_ids` e `_local_de` viram nomes publicos,
porque atravessam a fronteira de modulo) e os cabecalhos de cada modulo.

Uso:
  --conferir   so mostra o que faria, sem escrever
  (sem flag)   escreve os arquivos
"""
from __future__ import annotations

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[4]
CORE = RAIZ / "src" / "core"
ALVO = CORE / "documentary_relationship.py"

LINHAS = ALVO.read_text(encoding="utf-8").splitlines()


def fatia(inicio: int, fim: int, comeco: str, termino: str) -> str:
    """As linhas `inicio` a `fim`, 1-based e inclusivas, conferidas nas duas pontas."""
    trecho = "\n".join(LINHAS[inicio - 1:fim])
    primeira = LINHAS[inicio - 1]
    ultima = LINHAS[fim - 1]
    assert primeira.startswith(comeco), f"linha {inicio} comeca com {primeira!r}, esperado {comeco!r}"
    assert ultima.startswith(termino), f"linha {fim} termina com {ultima!r}, esperado {termino!r}"
    return trecho


# --- datas_do_gedcom ------------------------------------------------------
CONSTANTES = fatia(40, 43, "# Idade minima", "IDADE_MAXIMA_GENITOR")
DATAS = fatia(72, 173, "# Datas", "    return float(median(intervalos))")
DATAS = DATAS.replace("# Datas\n", "# Data e local\n", 1)
LOCAL = '''
def birth_place(people, pid):
    """Local de nascimento, ou None. Espelha `birth_date` na forma."""
    return _sub_valor(people, pid, "BIRT", "PLAC")
'''

datas_modulo = f'''"""Data e local do registro GEDCOM, sem nenhum parentesco.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele responde uma coisa so: o
que o registro diz sobre data e local. Nao sabe de arvore, de caminho nem de cartao.

Mora separado porque tres consumidores diferentes precisam da mesma leitura: a ficha da
pessoa, o dossie de homonimos e o proprio cartao documental.
"""
from __future__ import annotations

import re
from statistics import median

from .registro import ref_id

{CONSTANTES}

{DATAS}
{LOCAL}

__all__ = [
    "IDADE_MINIMA_GENITOR", "IDADE_MAXIMA_GENITOR",
    "parse_year", "birth_date", "death_date", "birth_place",
    "intervalo_de_geracao_mediano",
]
'''

# --- fichas_da_pessoa -----------------------------------------------------
FICHAS = fatia(176, 257, "# ----", "    }")
FICHAS = FICHAS.replace("# Fichas de pessoa\n", "# Ficha comparavel da pessoa\n", 1)
FICHAS = FICHAS.replace("def _ids(", "def ids_com_tag(")
FICHAS = FICHAS.replace("_ids(people,", "ids_com_tag(people,")
FICHAS = FICHAS.replace('_local_de(people, person_id, "BIRT")', "birth_place(people, person_id)")

fichas_modulo = f'''"""A ficha comparavel de uma pessoa da arvore, e o indice pai para filhos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). A ficha serve para
desambiguar homonimos; o indice pai para filhos evita varrer todas as familias a cada ficha.
Nenhuma das duas sabe o que e parentesco documental.
"""
from __future__ import annotations

from .datas_do_gedcom import birth_date, birth_place, death_date, parse_year
from .family_navigation import get_parents
from .registro import get_name, ref_id

{FICHAS}

__all__ = ["get_children", "person_summary", "ids_com_tag"]
'''

# --- homonimos ------------------------------------------------------------
CACHE = fatia(52, 71, "# ----", "# ----")
HOMONIMOS = fatia(260, 375, "# ----", "    }")
HOMONIMOS = HOMONIMOS.replace("# Homonimos\n", "# Homonimos e o indice de nomes\n", 1)

homonimos_modulo = f'''"""Reconhecer o mesmo nome e montar o dossie de homonimos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele e o dono do unico estado
de modulo do nucleo, o CACHE_DE_NOMES, e o unico lugar que compara nomes ignorando acento.
"""
from __future__ import annotations

import unicodedata

from .fichas_da_pessoa import person_summary
from .registro import get_name
from utils.text_cleaning import demojibake

{CACHE}

{HOMONIMOS}

__all__ = ["normalizar", "homonym_dossier"]
'''

# --- caminhos_alternativos ------------------------------------------------
LIMITES_CAMINHOS = fatia(45, 49, "# Teto de expansao", "LIMITE_DE_CADEIAS")
CAMINHOS = fatia(512, 602, "def _ancestor_depths", '    return {"ids": ids,')

caminhos_modulo = f'''"""Ancestrais comuns, cadeias ate eles e caminhos alternativos.

## Por que este modulo existe

Nasceu em `core/documentary_relationship` (OPP-20261024-SEPM). Ele responde pela enumeracao
que existe alem do caminho principal: quantos ancestrais comuns ha, quantas cadeias levam a
cada um e por onde passa o caminho alternativo.
"""
from __future__ import annotations

from collections import deque

from .datas_do_gedcom import birth_date
from .family_navigation import get_parents
from .registro import get_name

{LIMITES_CAMINHOS}


{CAMINHOS}

__all__ = ["find_all_common_ancestors"]
'''

# --- fachada --------------------------------------------------------------
EVIDENCIA = fatia(378, 432, "# ----", "    }")
ROTULO = fatia(435, 509, "# ----", '            "degrees": {"a_up": deg_a, "b_up": deg_b, "cousin_degree": grau, "removed": removidos}}')
CARTao = fatia(605, 821, "def _aviso_de_homonimo", "]")
CARTao = CARTao.replace("_ids(people,", "ids_com_tag(people,")
EVIDENCIA = EVIDENCIA.replace("_ids(people,", "ids_com_tag(people,")

fachada_modulo = f'''"""Parentesco DOCUMENTAL: a fachada publica e a montagem do cartao.

## Por que este arquivo continua sendo o endereco

Ele era o modulo inteiro ate 2026-10-24, quando a `OPP-20261024-SEPM` separou o que ele faz
em quatro modulos de responsabilidade unica:

- `core.datas_do_gedcom` le data e local do registro;
- `core.fichas_da_pessoa` monta a ficha comparavel e o indice pai para filhos;
- `core.homonimos` reconhece o mesmo nome e monta o dossie;
- `core.caminhos_alternativos` enumera ancestrais comuns, cadeias e caminhos alternativos.

O que sobrou aqui e o cartao: a decisao de qual caminho apresentar, a evidencia de cada
salto, os avisos e o dicionario final. A fachada reexporta os dezoito nomes de `__all__`
para que os quinze consumidores nao mudem de endereco.

## Regra do projeto

O GEDCOM determina o parentesco documental. O DNA **nao** altera nada do que este modulo
devolve: nenhuma funcao daqui aceita cM nem le o CSV. Quem confronta as duas evidencias e
`core.evidence_comparison`, depois e separadamente.

## Por que datas entram aqui

`_reversa_sdd/busca-caminho` documenta que o legado nunca olhou data: o BFS sobe por pais e
aceita qualquer salto. Medido em 2026-10 no GEDCOM real `Arvore_Unificada_Oficial_V1_2.ged`,
isso produz caminho com mae nascida 11 anos DEPOIS do filho (`@F6@`: Celso Gomes Gama, n. 1961,
filho de Maria Auxiliadora, n. 1972) apresentado como "conexao direta por ancestral comum".

Uma data impossivel **nao** invalida o vinculo nem muda o parentesco: o dado e do documento, e
cabe ao operador julgar. O que o cartao faz e **registrar a evidencia**
(`evidence[].age_at_birth`, `plausible`) e **avisar** (`warnings[].code == "data_impossivel"`).
"""
from __future__ import annotations

from .caminhos_alternativos import (
    MAX_DEPTH_ALTERNATIVOS,
    _cadeias_ate,
    _caminho_alternativo,
    find_all_common_ancestors,
)
from .datas_do_gedcom import (
    IDADE_MAXIMA_GENITOR,
    IDADE_MINIMA_GENITOR,
    birth_date,
    death_date,
    intervalo_de_geracao_mediano,
    parse_year,
)
from .fichas_da_pessoa import get_children, ids_com_tag, person_summary
from .graus_de_parentesco import ROMANO, nome_do_grau, nome_do_primo  # reexportados
from .homonimos import homonym_dossier, normalizar
from .path_finding import MAX_DEPTH, find_ancestral_path
from .registro import get_name, ref_id

{EVIDENCIA}


{ROTULO}


{CARTao}
'''

MODULOS = {
    "datas_do_gedcom.py": datas_modulo,
    "fichas_da_pessoa.py": fichas_modulo,
    "homonimos.py": homonimos_modulo,
    "caminhos_alternativos.py": caminhos_modulo,
    "documentary_relationship.py": fachada_modulo,
}

conferir = "--conferir" in sys.argv
for nome, texto in MODULOS.items():
    linhas = texto.splitlines()
    print(f"{nome:32} {len(linhas):4} linhas  |  {linhas[0][:50]!r}")
    if not conferir:
        destino = CORE / nome
        destino.write_text(texto, encoding="utf-8", newline="\n")

print()
print("gravados" if not conferir else "nada gravado (--conferir)")






