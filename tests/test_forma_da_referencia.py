"""`RN-20` (`BUG-20261009-6RKP`): a forma da referencia aceita, e a defesa contra escape.

## O que mudou, e por que isto e um teste de SEGURANCA

A forma fechada antiga era `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`. Ela recusava **acento e espaco** —
que o gravador produz de proposito, porque preserva-los e requisito (`RF-06`). Os dois lados se
contradiziam, e o resultado medido na pasta do operador foi: 3 arquivos com acento e 1 com espaco
inalcancaveis, com a tela dizendo "nao existe mais" sobre arquivos que existiam.

O `_spec-impact-matrix.md` marca aquela forma como **defesa de seguranca** e avisa que afrouxa-la
reabre o escape de caminho do `BUG-20260929-QMLY`. Por isso este arquivo existe, e por isso ele
tem as DUAS metades:

- `TestFormasAceitas` — o que passou a ser aceito, com acento, espaco e nome visivel estranho;
- `TestEscapeContinuaRecusado` — **os cinco casos originais do bug de escape**, mais os que
  tentam escapar COM o prefixo da chave. Se qualquer um destes passar a ser aceito, o escape
  voltou, e este teste e a barreira.

A defesa nunca foi o alfabeto: e a exigencia de a referencia ser um NOME, e nao um caminho.
"""
from __future__ import annotations

import os
import sys

import pytest

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _caminho in (_RAIZ, os.path.join(_RAIZ, "src")):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from utils.validate import chave_recebida_e_valida, nome_visivel_seguro  # noqa: E402

CHAVE = "94e2402671702cac"
# Nome visivel escolhido pelo cliente, que NAO pode virar caminho. E o valor que o
# `BUG-20260929-QMLY` usava para provar o escape.
FORA = "../../etc/passwd"


class TestFormasAceitas:
    """O que o gravador produz tem de ser aceito pelo resolvedor. E a `RN-20`."""

    @pytest.mark.parametrize("visivel", [
        "arvore.ged",
        "Famílias_Sergipanas.csv",
        "planilha de dna.xlsx",
        "Backup-Arvore-Sandro-12-11-2024.ged",
        "Adriano_Santos.ged",
        "080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged",
        "d'Agua.ged",
        "relatório(final).csv",
        "árvore da família.ged",
    ])
    def test_o_nome_que_o_gravador_produz_e_aceito(self, visivel):
        armazenado = f"{CHAVE}__{visivel}"

        assert chave_recebida_e_valida(armazenado) is True, (
            f"{armazenado!r} e um nome que `nome_do_arquivo_armazenado` produz e o resolvedor "
            "recusa: o arquivo fica inalcancavel e a tela diz que ele nao existe"
        )

    def test_aceitar_o_nome_do_gravador_e_o_que_fecha_a_contradicao(self):
        """A prova direta: para QUALQUER nome que o gravador aceite, o resolvedor aceita.

        Este e o teste que teria pegado o `BUG-20261009-6RKP` no dia em que ele nasceu: ele nao
        lista casos, ele cruza as duas funcoes.
        """
        for original in ["Famílias.csv", "planilha de dna.xlsx", "árvore.ged",
                         "Backup-Arvore-12-11-2024.ged", "../../etc/passwd", "",
                         "nome.com.muitos.pontos.ged", "a" * 80]:
            armazenado = f"{CHAVE}__{nome_visivel_seguro(original)}"

            assert chave_recebida_e_valida(armazenado) is True, (
                f"o gravador aceita {original!r} e produz {armazenado!r}, que o resolvedor recusa"
            )


class TestEscapeContinuaRecusado:
    """Os cinco casos do `BUG-20260929-QMLY`, mais os que tentam escapar COM o prefixo."""

    @pytest.mark.parametrize("referencia", [
        FORA,
        "uploads\\..\\x.ged",
        "nome_do_cliente.ged",
        "",
        None,
    ])
    def test_os_cinco_casos_originais_continuam_recusados(self, referencia):
        """Sem o prefixo da chave, a referencia nao alcanca nada. Era e continua sendo assim."""
        assert chave_recebida_e_valida(referencia) is False

    @pytest.mark.parametrize("visivel", [
        "../fora.ged",
        "..\\fora.ged",
        "sub/pasta.ged",
        "sub\\pasta.ged",
        "/etc/passwd",
        "C:\\Windows\\system.ini",
        "..",
        ".",
        "a\x00b.ged",
        "",
    ])
    def test_escapar_COM_o_prefixo_da_chave_tambem_e_recusado(self, visivel):
        """O ataque que importa: ter o prefixo valido e tentar sair da pasta pelo nome visivel."""
        referencia = f"{CHAVE}__{visivel}"

        assert chave_recebida_e_valida(referencia) is False, (
            f"{referencia!r} foi ACEITO: a referencia deixou de exigir um NOME e voltou a aceitar "
            "caminho. E o escape do BUG-20260929-QMLY de volta"
        )

    @pytest.mark.parametrize("referencia", [
        "94e2402671702ca__curta.ged",
        "94E2402671702CAC__maiuscula.ged",
        "zzzzzzzzzzzzzzzz__nao_hex.ged",
        "94e2402671702cac_um_separador.ged",
        # `<chave>__` — sem NENHUM nome visivel. A primeira versao deste caso era
        # `94e2402671702cac________`, e ela estava ERRADA: as seis sublinhados que sobram sao um
        # nome visivel valido, e `nome_visivel_seguro` pode produzir exatamente isso a partir de
        # um nome so de barras. O caso que nao tem nome visivel e este.
        "94e2402671702cac__",
        "__sem_chave.ged",
    ])
    def test_referencia_sem_a_forma_da_chave_e_recusada(self, referencia):
        assert chave_recebida_e_valida(referencia) is False

    def test_a_recusa_nao_virou_um_false_constante(self):
        """O contrapeso: sem isto, um `return False` fixo passaria em tudo acima."""
        assert chave_recebida_e_valida(f"{CHAVE}__Famílias_Sergipanas.csv") is True
