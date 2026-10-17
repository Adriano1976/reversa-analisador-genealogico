"""T008 (feature `025-desempenho-carga-arvore`): uma materializacao por registro.

## O que este arquivo vigia (`RN-02`)

Cada registro de nivel 0 do GEDCOM e materializado **uma unica vez** por carga. O
codigo anterior a esta feature percorria `records0("FAM")` duas vezes: uma para
montar `families` e outra dentro de `build_graph_from_parser`. O sintoma medido na
arvore real era `read_record` = 49.321, isto e, 1 `HEAD` + 35.460 `INDI` +
2 x 6.930 `FAM`.

## Por que a contagem, e nao o tempo

Tempo nao serve como assercao: a mesma carga variou 83 % entre execucoes nesta
maquina (medido em 2026-10-17). A contagem de chamadas e deterministica e falha
exatamente quando o desperdicio volta — inclusive se alguem reintroduzir a
segunda leitura por outro caminho.

## Contra o codigo anterior, este teste FALHA com `FAM` = 2

Era o proposito da `T008`: um teste de contagem que nunca foi visto falhar nao
prova nada (`Principio III`).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_gedcom import SAMPLE_GED

from parsers.gedcom_parser import carregar_arvore


def _escrever(conteudo=SAMPLE_GED):
    """GEDCOM sintetico em arquivo temporario — nunca dado real (Principio I)."""
    descritor, caminho = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return caminho
    except Exception:
        os.remove(caminho)
        raise


def _instalar_contadores(monkeypatch):
    """Conta as chamadas ao `ged4py` sem tocar no codigo de producao."""
    from ged4py.parser import GedcomReader

    contagem = {"records0": {}, "index0": 0, "init_index": 0, "read_record": 0}

    leitura_index0 = GedcomReader.index0.fget

    def index0(self):
        contagem["index0"] += 1
        return leitura_index0(self)

    monkeypatch.setattr(GedcomReader, "index0", property(index0))

    init_index = GedcomReader._init_index

    def _init_index(self):
        contagem["init_index"] += 1
        return init_index(self)

    monkeypatch.setattr(GedcomReader, "_init_index", _init_index)

    records0 = GedcomReader.records0

    def records0_contando(self, tag=None):
        contagem["records0"][tag] = contagem["records0"].get(tag, 0) + 1
        return records0(self, tag)

    monkeypatch.setattr(GedcomReader, "records0", records0_contando)

    read_record = GedcomReader.read_record

    def read_record_contando(self, *args, **kwargs):
        contagem["read_record"] += 1
        return read_record(self, *args, **kwargs)

    monkeypatch.setattr(GedcomReader, "read_record", read_record_contando)
    return contagem


def _contar_no_arquivo(caminho):
    """Quantos registros `INDI` e `FAM` o arquivo tem, por leitura independente."""
    from ged4py.parser import GedcomReader

    with GedcomReader(caminho) as leitor:
        total_indi = sum(1 for _ in leitor.records0("INDI"))
        total_fam = sum(1 for _ in leitor.records0("FAM"))
    return total_indi, total_fam


def test_carga_materializa_cada_registro_de_nivel_0_uma_vez(monkeypatch):
    caminho = _escrever()
    try:
        total_indi, total_fam = _contar_no_arquivo(caminho)
        contagem = _instalar_contadores(monkeypatch)
        people, families, _graph, _child_to_family = carregar_arvore(caminho)
    finally:
        os.remove(caminho)

    assert contagem["records0"].get("INDI") == 1
    assert contagem["records0"].get("FAM") == 1, (
        "os registros de familia foram materializados %s vezes; a carga deve ler "
        "o arquivo uma unica vez (RN-02)"
        % contagem["records0"].get("FAM"))
    assert contagem["init_index"] == 1, (
        "o indice de nivel 0 foi construido %s vezes; ele e cacheado por leitor "
        "e deveria ser construido uma unica vez"
        % contagem["init_index"])
    assert contagem["read_record"] == 1 + total_indi + total_fam, (
        "read_record=%s, esperado 1 (HEAD) + %s (INDI) + %s (FAM)"
        % (contagem["read_record"], total_indi, total_fam))
    assert len(people) == total_indi
    assert families


def test_a_arvore_devolvida_nao_depende_do_arquivo_aberto(monkeypatch):
    """A arvore sai pronta do `with`: nada e lido depois que o leitor fecha."""
    caminho = _escrever()
    try:
        people, families, graph, child_to_family = carregar_arvore(caminho)
    finally:
        os.remove(caminho)

    assert people
    assert families
    assert graph.number_of_nodes() == len(people) + len(families)
    filhos = {filho for filhos in child_to_family.values() for filho in filhos}
    assert filhos <= set(families)
