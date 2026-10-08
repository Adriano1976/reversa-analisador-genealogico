"""Adaptador `RegistroDeAnalisesPostgres` contra o banco de verdade (`T014`).

## Por que este arquivo se pula, e o que o pulo significa

O `T014` exige **duas** coisas ao mesmo tempo: `DATABASE_URL` apontando para um
banco alcancavel, **e** o driver `psycopg2` instalado no interpretador que roda o
teste. Nenhuma das duas esta garantida na suite:

- a suite roda **sem** `DATABASE_URL` por decisao (`D-17`, `RF-13`) — a persistencia
  desabilitada e o estado que precisa ser o padrao;
- o `.venv/` do host **nao tem** o driver, e nao consegue ter: o `pip install` falha
  com `Errno 13 Permission denied` no diretorio que ele cria com `0o700`
  (`OBS-02`/`OBS-15`). Dentro do conteiner o driver existe, porque a imagem o
  instala a partir do `requirements.txt`.

Por isso o pulo e **explicito e justificado**, e nunca um teste que passa por nao
rodar. Quem exercita estes caminhos com o banco no ar e o `T020` (ponta a ponta,
pelos tres fluxos da rota) e o `T021` (a verificacao manual do `onboarding.md`).

⚠️ **Um teste pulado nao e um teste que passou.** O `T022` registra os dois numeros
da suite lado a lado, com e sem `DATABASE_URL`, e nao os apresenta como um so.
"""
from __future__ import annotations

import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)
sys.path.insert(0, os.path.join(_RAIZ, "src"))

from application.dna_analysis import projetar_analise  # noqa: E402


def _tem_driver() -> bool:
    try:
        import psycopg2  # noqa: F401
        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not (os.environ.get("DATABASE_URL") and _tem_driver()),
    reason=("T014 exige DATABASE_URL E o driver psycopg2 no interpretador do host. "
            "O .venv do host nao tem o driver por um defeito de ambiente conhecido "
            "(pip + 0o700, OBS-02/OBS-15), e a suite roda sem DATABASE_URL por "
            "decisao (D-17). Os mesmos caminhos sao exercitados no T020/T021."),
)


def _analise(*, kit_a_cm: float, kit_b_cm: float, status_final: str = "CONFLITANTE"):
    """Analise sintetica, ja no formato que a projecao entrega a porta."""
    resultado = {
        "match_name": "Ana Silva Souza",
        "csv_name": "Ana Silva Souza",
        "cm": kit_a_cm,
        "kit": "KIT-A",
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
            "kits": [
                {"kit": "KIT-A", "source": "GEDmatch", "total_cm": kit_a_cm,
                 "segment_count": 3, "largest_segment_cm": kit_a_cm},
                {"kit": "KIT-B", "source": "MyHeritage", "total_cm": kit_b_cm,
                 "segment_count": 1, "largest_segment_cm": kit_b_cm},
            ],
            "totals": {"cm": None},
        },
        "hypotheses": [],
        "comparison": {
            "status": status_final, "label": "Conflitante", "message": "m",
            "causes": ["endogamia"], "per_kit": [
                {"kit": "KIT-A", "status": "COMPATIVEL", "cm": kit_a_cm, "note": "dentro"},
                {"kit": "KIT-B", "status": status_final, "cm": kit_b_cm, "note": "fora"},
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
                            "chave__arvore.ged", "chave2__matches.csv", "Carlos")


@pytest.fixture
def registro():
    from ports.adaptadores import RegistroDeAnalisesPostgres
    return RegistroDeAnalisesPostgres(os.environ["DATABASE_URL"])


def _limpar(url: str) -> None:
    """Apaga as analises gravadas pelo teste, para nao poluir o historico do operador."""
    import psycopg2
    conexao = psycopg2.connect(url)
    try:
        with conexao:
            with conexao.cursor() as cursor:
                cursor.execute("DELETE FROM dna_analysis WHERE tree_ref = %s",
                               ("chave__arvore.ged",))
    finally:
        conexao.close()


def test_grava_e_devolve_referencia(registro):
    referencia, aviso = registro.registrar(_analise(kit_a_cm=200.0, kit_b_cm=60.0), "unico")
    try:
        assert aviso is None, f"a gravacao falhou: {aviso}"
        assert referencia, "a gravacao nao devolveu referencia"
    finally:
        _limpar(os.environ["DATABASE_URL"])


def test_dois_kits_gravam_dois_registros_e_nenhuma_soma(registro):
    import psycopg2
    url = os.environ["DATABASE_URL"]
    referencia, aviso = registro.registrar(_analise(kit_a_cm=200.0, kit_b_cm=60.0), "unico")
    assert aviso is None, aviso
    conexao = psycopg2.connect(url)
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT k.total_cm FROM match_kit k
                  JOIN match_result m USING (match_id)
                 WHERE m.analysis_id = %s ORDER BY k.ordinal
                """, (referencia,))
            cms = [float(linha[0]) for linha in cursor.fetchall()]
    finally:
        conexao.close()
        _limpar(url)
    assert cms == [200.0, 60.0], f"os cM dos kits foram somados ou trocados: {cms}"


@pytest.mark.parametrize("cm", [46.0, 200.0, 553.0, 1317.0, 2200.0, 3300.0])
def test_ida_e_volta_do_cm_nos_valores_de_fronteira(registro, cm):
    """`RISK-004`: gravar e reler NAO pode mudar o valor — sao fronteiras de faixa."""
    import psycopg2
    url = os.environ["DATABASE_URL"]
    referencia, aviso = registro.registrar(_analise(kit_a_cm=cm, kit_b_cm=cm), "unico")
    assert aviso is None, aviso
    conexao = psycopg2.connect(url)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT total_cm FROM match_result WHERE analysis_id = %s",
                           (referencia,))
            lido = float(cursor.fetchone()[0])
    finally:
        conexao.close()
        _limpar(url)
    assert lido == cm, f"o cM mudou na ida e volta: {cm} -> {lido}"
