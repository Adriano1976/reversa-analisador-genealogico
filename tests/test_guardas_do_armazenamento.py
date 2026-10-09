"""Guarda do armazenamento: as duas linhas que sustentam o Principio I.

O Principio I de `.reversa/principles.md` manda que dado real de DNA/GEDCOM nunca entre no
versionamento. Com a pasta canonica de volta **dentro** do repositorio (feature 012), duas
linhas de configuracao passam a ser tudo o que separa o dado real de uma exposicao:

1. `.gitignore` -> `uploads/`
2. `.dockerignore` -> `src/uploads/`, **depois** de `!src/**`

Nenhuma das duas tinha teste. Este arquivo prende as duas, e prende tambem a **ordem** no
`.dockerignore`: o `.dockerignore` do projeto e lista de permissao, e no Docker a **ultima
linha que casa vence** (documentacao oficial, `Build context` -> `Negating matches`). Com
`src/uploads/` antes de `!src/**`, o dado real volta a ser enviado ao daemon **sem que
nenhuma linha tenha sido removida** -- e nenhum teste de presenca pegaria isso.

Por que assercao **de efeito** alem da literal: a linha existir nao prova que ela produz o
efeito, porque outra regra poderia estar cobrindo o caminho. `git check-ignore -v` responde
qual regra, de qual arquivo e em qual linha, decidiu -- e o teste exige que seja o
`.gitignore`. O controle negativo (`README.md` nao pode ser ignorado) prova que a assercao
de efeito discrimina em vez de responder "sim" para tudo.

Por que a mutacao: uma assercao que nunca foi vista falhar nao e prova (Principio III). Os
testes de mutacao rodam sobre **copias temporarias** dos arquivos -- nunca sobre o original,
porque um teste que muta o `.gitignore` real deixaria o repositorio exposto se abortasse no
meio.
"""
from __future__ import annotations

import os
import shutil
import subprocess

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITIGNORE = os.path.join(RAIZ, ".gitignore")
DOCKERIGNORE = os.path.join(RAIZ, ".dockerignore")

# As regras que este arquivo vigia, pelo texto exato da linha.
REGRA_GIT = "uploads/"
REGRA_DOCKER = "src/uploads/"
PERMISSAO_DOCKER = "!src/**"

# Um caminho representativo do dado real, e um que nunca pode ser ignorado.
CAMINHO_DO_DADO = "src/uploads/080e7943572d2652__arvore.ged"
CAMINHO_NEUTRO = "README.md"


def _linhas(caminho: str) -> list:
    with open(caminho, encoding="utf-8") as fh:
        return fh.read().splitlines()


def _tem_regra(caminho: str, alvo: str) -> bool:
    """A linha existe e nao e comentario."""
    return any(linha.strip() == alvo and not linha.lstrip().startswith("#")
               for linha in _linhas(caminho))


def _indice_da_regra(caminho: str, alvo: str) -> int:
    """Indice da linha da regra no arquivo, ou -1."""
    for indice, linha in enumerate(_linhas(caminho)):
        if linha.strip() == alvo and not linha.lstrip().startswith("#"):
            return indice
    return -1


def _ordem_do_dockerignore(caminho: str) -> bool:
    """A reexclusao de `src/uploads/` vem DEPOIS da permissao de `src/`."""
    permissao = _indice_da_regra(caminho, PERMISSAO_DOCKER)
    reexclusao = _indice_da_regra(caminho, REGRA_DOCKER)
    return permissao >= 0 and reexclusao >= 0 and reexclusao > permissao


def _git_diz_quem_ignora(caminho: str) -> str:
    """Saida de `git check-ignore -v`, ou string vazia quando o git nao ignora."""
    if shutil.which("git") is None:
        pytest.skip("git nao esta no PATH")
    resultado = subprocess.run(
        ["git", "check-ignore", "-v", caminho],
        cwd=RAIZ, capture_output=True, text=True,
    )
    return resultado.stdout.strip()


# ---------------------------------------------------------------------------
# Guarda 1: `.gitignore`
# ---------------------------------------------------------------------------

def test_gitignore_tem_a_regra_de_uploads():
    assert _tem_regra(GITIGNORE, REGRA_GIT), (
        "a linha `%s` saiu do .gitignore: sem ela o git passa a rastrear o dado real do "
        "operador, e o Principio I deixa de valer" % REGRA_GIT
    )


def test_gitignore_surte_efeito_e_o_git_nomeia_a_regra():
    saida = _git_diz_quem_ignora(CAMINHO_DO_DADO)

    assert saida, "o git deixou de ignorar `%s`" % CAMINHO_DO_DADO
    assert ".gitignore" in saida, (
        "quem ignora `%s` nao e o .gitignore, e sim outra regra: %r. A guarda nao esta "
        "onde este teste a procura" % (CAMINHO_DO_DADO, saida)
    )


def test_gitignore_nao_ignora_o_que_nao_e_dado():
    """Controle negativo: a assercao de efeito acima tem de discriminar."""
    saida = _git_diz_quem_ignora(CAMINHO_NEUTRO)

    assert not saida, (
        "`%s` aparece como ignorado (%r). A assercao de efeito responderia 'sim' para "
        "qualquer caminho, e nao provaria nada" % (CAMINHO_NEUTRO, saida)
    )


# ---------------------------------------------------------------------------
# Guarda 2: `.dockerignore`
# ---------------------------------------------------------------------------

def test_dockerignore_tem_a_reexclusao_de_src_uploads():
    assert _tem_regra(DOCKERIGNORE, REGRA_DOCKER), (
        "a linha `%s` saiu do .dockerignore: o contexto de build passa a levar o dado "
        "real do operador para o daemon do Docker" % REGRA_DOCKER
    )


def test_dockerignore_reexclui_depois_de_permitir():
    assert _tem_regra(DOCKERIGNORE, PERMISSAO_DOCKER), (
        "a permissao `%s` saiu do .dockerignore; o arquivo nao e mais lista de permissao, "
        "e toda esta guarda precisa ser relida" % PERMISSAO_DOCKER
    )
    assert _ordem_do_dockerignore(DOCKERIGNORE), (
        "em `.dockerignore` a ULTIMA regra que casa vence: com `%s` antes de `%s`, a "
        "reexclusao perde e o dado real volta ao contexto de build"
        % (REGRA_DOCKER, PERMISSAO_DOCKER)
    )


# ---------------------------------------------------------------------------
# Mutacao: a assercao tem de ser vista falhando
#
# Tudo aqui roda sobre COPIAS em pasta temporaria. Mutar o `.gitignore` ou o
# `.dockerignore` reais deixaria o repositorio exposto se o teste abortasse entre
# a mutacao e a restauracao.
# ---------------------------------------------------------------------------

def _copia_sem_a_regra(origem: str, destino: str, alvo: str) -> str:
    """Copia `origem` para `destino` sem a linha da regra `alvo`."""
    todas = _linhas(origem)
    restantes = [linha for linha in todas
                 if not (linha.strip() == alvo and not linha.lstrip().startswith("#"))]
    assert len(restantes) < len(todas), "a regra `%s` nao estava em %s" % (alvo, origem)
    with open(destino, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(restantes) + "\n")
    return destino


def _copia_com_as_duas_regras_trocadas(origem: str, destino: str) -> str:
    """Copia `origem` para `destino` com a permissao e a reexclusao invertidas."""
    linhas = _linhas(origem)
    permissao = _indice_da_regra(origem, PERMISSAO_DOCKER)
    reexclusao = _indice_da_regra(origem, REGRA_DOCKER)
    assert permissao >= 0 and reexclusao >= 0, "as duas regras tem de estar em %s" % origem
    linhas[permissao], linhas[reexclusao] = linhas[reexclusao], linhas[permissao]
    with open(destino, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")
    return destino


def test_mutacao_a_guarda_do_gitignore_falha_quando_a_linha_sai(tmp_path):
    copia = _copia_sem_a_regra(GITIGNORE, str(tmp_path / ".gitignore"), REGRA_GIT)

    assert not _tem_regra(copia, REGRA_GIT), (
        "a assercao literal passou com a linha removida: ela nao prende nada"
    )


def test_mutacao_a_guarda_do_dockerignore_falha_quando_a_reexclusao_sai(tmp_path):
    copia = _copia_sem_a_regra(DOCKERIGNORE, str(tmp_path / ".dockerignore"), REGRA_DOCKER)

    assert not _tem_regra(copia, REGRA_DOCKER)
    assert not _ordem_do_dockerignore(copia), (
        "a assercao de ordem passou sem a reexclusao: ela nao prende nada"
    )


def test_mutacao_a_guarda_de_ordem_falha_quando_as_linhas_invertem(tmp_path):
    """O caso que um teste de presenca jamais pegaria.

    As duas linhas continuam no arquivo; o que muda e a posicao. Se a assercao de
    ordem nao falhar aqui, ela esta presa a presenca e nao a ordem -- e a regra que
    o Docker de fato aplica e a ordem.
    """
    copia = _copia_com_as_duas_regras_trocadas(DOCKERIGNORE, str(tmp_path / ".dockerignore"))

    assert _tem_regra(copia, REGRA_DOCKER), "a reexclusao tem de continuar presente"
    assert _tem_regra(copia, PERMISSAO_DOCKER), "a permissao tem de continuar presente"
    assert not _ordem_do_dockerignore(copia), (
        "com as duas linhas presentes e invertidas, a assercao de ordem passou: ela estaria "
        "presa a presenca, e nao a ordem -- que e a regra real do .dockerignore"
    )
