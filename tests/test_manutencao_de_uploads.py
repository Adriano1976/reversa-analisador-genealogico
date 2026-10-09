"""Testes da ferramenta de manutencao da pasta de upload (feature 010).

Cobrem os dois verbos que mexem em dado do operador — `migrar` e `expurgo` — e o
criterio do `manifesto`. Todos usam **arquivos sinteticos** em pasta temporaria, nunca
dado real: e o que o Principio I de `.reversa/principles.md` exige, e e a razao de o
`tmp_path` da suite existir (`.reversa`/`tests/conftest.py`).

O que cada grupo protege:

- migracao: copia conferida por `sha256`, origem intacta, idempotencia e recusa de
  sobrescrever destino divergente (`RF-07`, `D-04`);
- manifesto: o criterio e o nome visivel pertencer ao conjunto fechado dos instrumentos
  (`RN-06`, `4a`);
- expurgo: simulacao nao remove; a aplicacao remove **apenas** o manifesto; duplicatas
  sao relatadas e preservadas (`RF-05`, `RF-06`, `D-05`, `D-06`);
- seguranca: nome fora da forma fechada e link simbolico sao recusados.
"""
from __future__ import annotations

import hashlib
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import manutencao_de_uploads as MU  # noqa: E402


# ---------------------------------------------------------------------------
# Apoio
# ---------------------------------------------------------------------------

def _hash(caminho: str) -> str:
    with open(caminho, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _chave(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()[:16]


def _criar(pasta, nome: str, conteudo: bytes = b"conteudo\n") -> str:
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as fh:
        fh.write(conteudo)
    return caminho


def _armazenado(pasta, visivel: str, conteudo: bytes = b"conteudo\n") -> str:
    """Cria um arquivo com a forma real do armazenamento: `<16 hex>__<nome visivel>`."""
    return _criar(pasta, _chave(conteudo) + "__" + visivel, conteudo)


# ===========================================================================
# migrar
# ===========================================================================

class TestMigrar:
    def test_copia_e_confere_hash_com_origem_intacta(self, tmp_path):
        origem, destino = str(tmp_path / "origem"), str(tmp_path / "destino")
        a = _criar(origem, "um.ged", b"AAA")
        b = _criar(origem, "dois.csv", b"BBB")
        hash_a, hash_b = _hash(a), _hash(b)

        resultado = MU.migrar(origem, destino)

        assert sorted(resultado.copiados) == ["dois.csv", "um.ged"]
        assert resultado.divergentes == []
        assert _hash(os.path.join(destino, "um.ged")) == hash_a
        assert _hash(os.path.join(destino, "dois.csv")) == hash_b
        # a origem continua existindo, com o mesmo conteudo
        assert _hash(a) == hash_a and _hash(b) == hash_b

    def test_e_idempotente(self, tmp_path):
        origem, destino = str(tmp_path / "origem"), str(tmp_path / "destino")
        _criar(origem, "um.ged", b"AAA")
        MU.migrar(origem, destino)
        antes = os.path.getmtime(os.path.join(destino, "um.ged"))

        segunda = MU.migrar(origem, destino)

        assert segunda.copiados == []
        assert segunda.ja_conferidos == ["um.ged"]
        assert segunda.divergentes == []
        # nao regravou: a data de modificacao do destino nao mudou
        assert os.path.getmtime(os.path.join(destino, "um.ged")) == antes

    def test_nao_sobrescreve_destino_divergente(self, tmp_path):
        origem, destino = str(tmp_path / "origem"), str(tmp_path / "destino")
        _criar(origem, "um.ged", b"ORIGEM")
        _criar(destino, "um.ged", b"DESTINO DIFERENTE")

        resultado = MU.migrar(origem, destino)

        assert resultado.divergentes == ["um.ged"]
        assert resultado.copiados == []
        # o destino ficou como estava e a origem continua intacta
        with open(os.path.join(destino, "um.ged"), "rb") as fh:
            assert fh.read() == b"DESTINO DIFERENTE"
        with open(os.path.join(origem, "um.ged"), "rb") as fh:
            assert fh.read() == b"ORIGEM"

    def test_origem_inexistente_aborta(self, tmp_path):
        with pytest.raises(SystemExit):
            MU.migrar(str(tmp_path / "nao_existe"), str(tmp_path / "destino"))


# ===========================================================================
# manifesto
# ===========================================================================

class TestManifesto:
    def test_lista_apenas_nomes_de_instrumento(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        sonda = _armazenado(pasta, "probe.ged", b"GEDCOM SINTETICO")
        fixture = _armazenado(pasta, "utf8.csv", b"a,b\n")
        real = _armazenado(pasta, "Arvore_Unificada_Oficial.ged", b"ARVORE DO OPERADOR")
        saida = str(tmp_path / "manifesto.txt")

        entradas = MU.gerar_manifesto(pasta, saida)

        nomes = sorted(e.nome for e in entradas)
        assert nomes == sorted([os.path.basename(sonda), os.path.basename(fixture)])
        assert os.path.basename(real) not in nomes
        # cada entrada carrega hash e motivo
        for entrada in entradas:
            assert entrada.sha256 == _hash(os.path.join(pasta, entrada.nome))
            assert entrada.motivo == MU.MOTIVO_INSTRUMENTO
        # o manifesto registra a pasta, para o expurgo nao depender de repetir o caminho
        with open(saida, encoding="utf-8") as fh:
            conteudo = fh.read()
        assert "# Pasta: " + os.path.abspath(pasta) in conteudo

    def test_pasta_sem_residuo_gera_manifesto_vazio(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        _armazenado(pasta, "Arvore_Real.ged", b"ARVORE")
        saida = str(tmp_path / "manifesto.txt")

        entradas = MU.gerar_manifesto(pasta, saida)

        assert entradas == []
        with open(saida, encoding="utf-8") as fh:
            assert "# Arquivos listados: 0" in fh.read()

    def test_e_regeneravel(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        _armazenado(pasta, "probe.ged", b"UMA SONDA")
        saida = str(tmp_path / "manifesto.txt")
        assert len(MU.gerar_manifesto(pasta, saida)) == 1

        _armazenado(pasta, "generic.csv", b"OUTRA FIXTURE")

        assert len(MU.gerar_manifesto(pasta, saida)) == 2

    def test_le_de_volta_o_que_escreveu(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        _armazenado(pasta, "probe.ged", b"SONDA")
        saida = str(tmp_path / "manifesto.txt")
        geradas = MU.gerar_manifesto(pasta, saida)

        pasta_lida, lidas = MU.ler_manifesto(saida)

        assert pasta_lida == os.path.abspath(pasta)
        assert [e.nome for e in lidas] == [e.nome for e in geradas]
        assert [e.sha256 for e in lidas] == [e.sha256 for e in geradas]


# ===========================================================================
# expurgo
# ===========================================================================

class TestExpurgo:
    def _preparar(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        sonda = _armazenado(pasta, "probe.ged", b"SONDA")
        fixture = _armazenado(pasta, "utf8.csv", b"FIXTURE")
        real = _armazenado(pasta, "Arvore_Real.ged", b"ARVORE DO OPERADOR")
        manifesto = str(tmp_path / "manifesto.txt")
        MU.gerar_manifesto(pasta, manifesto)
        return pasta, manifesto, sonda, fixture, real

    def test_simulacao_nao_remove_nada(self, tmp_path):
        pasta, manifesto, sonda, fixture, real = self._preparar(tmp_path)
        _, entradas = MU.ler_manifesto(manifesto)

        resultado = MU.expurgar(pasta, entradas, aplicar=False)

        assert sorted(resultado.removidos) == sorted([os.path.basename(sonda), os.path.basename(fixture)])
        assert resultado.simulado is True
        # tudo continua no disco
        assert os.path.exists(sonda) and os.path.exists(fixture) and os.path.exists(real)

    def test_aplicacao_remove_apenas_o_manifesto(self, tmp_path):
        pasta, manifesto, sonda, fixture, real = self._preparar(tmp_path)
        hash_real = _hash(real)
        _, entradas = MU.ler_manifesto(manifesto)

        resultado = MU.expurgar(pasta, entradas, aplicar=True)

        assert not os.path.exists(sonda) and not os.path.exists(fixture)
        assert resultado.simulado is False
        # o arquivo do operador continua la, com o mesmo conteudo
        assert os.path.exists(real) and _hash(real) == hash_real
        assert resultado.recusados == []

    def test_recusa_manifesto_velho(self, tmp_path):
        pasta, manifesto, sonda, fixture, real = self._preparar(tmp_path)
        _, entradas = MU.ler_manifesto(manifesto)
        # o conteudo muda depois de o manifesto ser gerado
        with open(sonda, "wb") as fh:
            fh.write(b"CONTEUDO NOVO")

        resultado = MU.expurgar(pasta, entradas, aplicar=True)

        recusados = [nome for nome, _motivo in resultado.recusados]
        assert os.path.basename(sonda) in recusados
        assert os.path.exists(sonda)
        # o outro continua elegivel
        assert os.path.basename(fixture) in resultado.removidos

    def test_recusa_nome_fora_da_forma_fechada(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        intruso = _criar(pasta, "probe.ged", b"SEM CHAVE")
        entradas = [MU.Entrada("probe.ged", _hash(intruso), MU.MOTIVO_INSTRUMENTO)]

        resultado = MU.expurgar(pasta, entradas, aplicar=True)

        assert resultado.removidos == []
        assert resultado.recusados[0][1] == "nome fora da forma fechada"
        assert os.path.exists(intruso)

    def test_recusa_escape_de_caminho_pela_defesa_em_profundidade(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        os.makedirs(pasta, exist_ok=True)
        assert MU._dentro_da_pasta(pasta, "..\\x.ged") is False
        assert MU._dentro_da_pasta(pasta, "../x.ged") is False
        assert MU._dentro_da_pasta(pasta, "a" * 16 + "__x.ged") is True

    def test_recusa_link_simbolico(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        alvo = _criar(str(tmp_path), "fora.ged", b"FORA DA PASTA")
        nome = _chave(b"FORA DA PASTA") + "__probe.ged"
        link = os.path.join(pasta, nome)
        os.makedirs(pasta, exist_ok=True)
        try:
            os.symlink(alvo, link)
        except (OSError, NotImplementedError):
            pytest.skip("este ambiente nao cria link simbolico sem privilegio")

        entradas = [MU.Entrada(nome, _hash(alvo), MU.MOTIVO_INSTRUMENTO)]
        resultado = MU.expurgar(pasta, entradas, aplicar=True)

        assert resultado.removidos == []
        assert resultado.recusados[0][1] == "link simbolico"
        assert os.path.exists(alvo)

    def test_manifesto_vazio_nao_remove_e_nao_erra(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        real = _armazenado(pasta, "Arvore_Real.ged", b"ARVORE")

        resultado = MU.expurgar(pasta, [], aplicar=True)

        assert resultado.removidos == [] and resultado.recusados == []
        assert os.path.exists(real)

    def test_duplicatas_sao_relatadas_e_preservadas(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        # tres copias byte a byte identicas e uma quarta de MESMO tamanho e conteudo
        # diferente — o caso real medido em 2026-10-09
        iguais = [_armazenado(pasta, "Arvore_Copia%d.ged" % i, b"X" * 64) for i in range(3)]
        distinta = _armazenado(pasta, "Arvore_Quarta.ged", b"Y" * 64)

        grupos = MU.duplicatas(pasta)

        assert len(grupos) == 1
        assert sorted(grupos[0][1]) == sorted(os.path.basename(p) for p in iguais)
        assert os.path.basename(distinta) not in grupos[0][1]
        # o expurgo relata e NAO remove duplicata
        resultado = MU.expurgar(pasta, [], aplicar=True)
        assert len(resultado.duplicatas) == 1
        for caminho in iguais + [distinta]:
            assert os.path.exists(caminho)

    def test_relatorio_conta_os_arquivos_do_grupo_e_nao_o_par(self, tmp_path):
        """Regressao: o cabecalho do grupo dizia "2 copias" para qualquer grupo.

        A causa era `len(grupo)` — o par `(sha256, nomes)` tem sempre dois elementos —
        em vez de `len(grupo[1])`. O defeito foi medido na pasta real em 2026-10-09, num
        grupo de TRES arquivos que apareceu como "2 copias".
        """
        pasta = str(tmp_path / "uploads")
        for indice in range(3):
            _armazenado(pasta, "Arvore_Copia%d.ged" % indice, b"X" * 64)

        resultado = MU.expurgar(pasta, [], aplicar=True)

        assert "duplicata\t3 copias" in resultado.texto(), (
            "o relatorio tem de contar os ARQUIVOS do grupo: " + resultado.texto()
        )


# ===========================================================================
# linha de comando
# ===========================================================================

class TestLinhaDeComando:
    def test_manifesto_e_expurgo_simulado(self, tmp_path, capsys):
        pasta = str(tmp_path / "uploads")
        sonda = _armazenado(pasta, "probe.ged", b"SONDA")
        saida = str(tmp_path / "manifesto.txt")
        relatorio = str(tmp_path / "expurgo.txt")

        assert MU.main(["manifesto", "--pasta", pasta, "--saida", saida]) == 0
        # a simulacao le a pasta do cabecalho do manifesto, sem repetir --pasta
        assert MU.main(["expurgo", "--manifesto", saida, "--dry-run",
                        "--relatorio", relatorio]) == 0

        saida_capturada = capsys.readouterr().out
        assert "SIMULACAO" in saida_capturada
        assert os.path.exists(sonda)
        with open(relatorio, encoding="utf-8") as fh:
            assert "seria removido" in fh.read()

    def test_duplicatas_pela_linha_de_comando(self, tmp_path):
        pasta = str(tmp_path / "uploads")
        _armazenado(pasta, "Arvore_A.ged", b"IGUAL")
        _armazenado(pasta, "Arvore_B.ged", b"IGUAL")
        assert MU.main(["duplicatas", "--pasta", pasta]) == 0
