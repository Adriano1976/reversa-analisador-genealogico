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

A **terceira** guarda e da mesma familia, e nasceu de um defeito medido em 2026-10-11: o
container publicado na porta 5080 servia o codigo de **2026-10-08** enquanto a arvore de
trabalho ja tinha a feature 011 inteira. A imagem e um **retrato** do dia do build (`COPY
src/`), e nada dizia a idade dela -- nem para quem operava, nem para quem depurava. Esta
guarda prende as quatro pecas que fazem a defasagem ficar visivel: o rotulo
`org.opencontainers.image.revision`, o carimbo `/app/CONSTRUIDO_EM` (os dois no
`docker/Dockerfile`), a passagem da revisao pelo `docker-compose.yml`, e a secao do
`README.md` que manda reconstruir depois de mudar `src/`.

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
DOCKERFILE = os.path.join(RAIZ, "docker", "Dockerfile")
COMPOSE = os.path.join(RAIZ, "docker-compose.yml")
README = os.path.join(RAIZ, "README.md")
ATALHO = os.path.join(RAIZ, "atualizar.ps1")

# As regras que este arquivo vigia, pelo texto exato da linha.
REGRA_GIT = "uploads/"
REGRA_DOCKER = "src/uploads/"
PERMISSAO_DOCKER = "!src/**"

# Guarda 3: a identidade do build. As tres linhas vivem no `docker/Dockerfile`.
ARG_DA_REVISAO = "ARG REVISAO=desconhecida"
ROTULO_DA_REVISAO = "LABEL org.opencontainers.image.revision=$REVISAO"
COPIA_DO_CODIGO = "COPY src/ /app/src/"
CARIMBO_DO_BUILD = "RUN date -u +%Y-%m-%dT%H:%M:%SZ > /app/CONSTRUIDO_EM"
INSTALACAO_DE_DEPENDENCIAS = "RUN pip install --no-cache-dir -r requirements.txt"
# No compose, a linha que leva a revisao para dentro do build.
PASSAGEM_DA_REVISAO = "REVISAO:"
# O comando que o operador tem de rodar depois de mexer em `src/`, e o titulo da secao do
# README que o explica. Os dois sao LITERAIS de contrato de documentacao: mudar o texto exige
# mudar o teste, que e o mesmo regime dos literais de mensagem da tela.
COMANDO_DE_ATUALIZACAO = "docker compose up -d --build"
SECAO_DOCKER = "### Executar com Docker"
MOTIVO_NO_README = "não chega ao container"
# O atalho da raiz, que faz o rebuild com a revisao preenchida, e a leitura do carimbo que ele
# imprime — o operador ve o que subiu sem digitar `docker inspect` na mao.
LEITURA_DO_CARIMBO = "cat /app/CONSTRUIDO_EM"

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


# ---------------------------------------------------------------------------
# Guarda 3: a identidade do build, para a imagem defasada ser visivel
# ---------------------------------------------------------------------------

def _tem_linha_com(caminho: str, trecho: str) -> bool:
    """Alguma linha nao-comentario CONTEM o trecho."""
    return any(trecho in linha and not linha.lstrip().startswith("#")
               for linha in _linhas(caminho))


def _indice_da_linha_com(caminho: str, trecho: str) -> int:
    """Indice da primeira linha nao-comentario que contem o trecho, ou -1."""
    for indice, linha in enumerate(_linhas(caminho)):
        if trecho in linha and not linha.lstrip().startswith("#"):
            return indice
    return -1


def _secao(caminho: str, titulo: str) -> str:
    """Texto da secao `titulo`: do cabecalho ate o proximo de nivel igual ou maior.

    Devolve string vazia quando o cabecalho nao existe -- e o teste que a usa trata isso como
    falha, para o renome da secao nao virar um teste que passa medindo nada.
    """
    linhas = _linhas(caminho)
    if titulo not in linhas:
        return ""
    inicio = linhas.index(titulo)
    nivel = len(titulo) - len(titulo.lstrip("#"))
    corpo = []
    for linha in linhas[inicio + 1:]:
        if linha.startswith("#") and (len(linha) - len(linha.lstrip("#"))) <= nivel:
            break
        corpo.append(linha)
    return "\n".join(corpo)


def test_dockerfile_grava_a_identidade_do_build():
    """As tres linhas que tornam a idade da imagem conferivel sem abrir o container.

    Sem elas, a unica forma de saber o que a imagem carrega era entrar no container e ler os
    arquivos -- foi o que precisei fazer em 2026-10-11 para descobrir que a 5080 servia o
    codigo de 2026-10-08.
    """
    assert _tem_regra(DOCKERFILE, ARG_DA_REVISAO), (
        "o `ARG REVISAO` saiu do docker/Dockerfile: o commit deixa de poder entrar no rotulo"
    )
    assert _tem_regra(DOCKERFILE, ROTULO_DA_REVISAO), (
        "o rotulo `org.opencontainers.image.revision` saiu do docker/Dockerfile: "
        "`docker image inspect` deixa de dizer qual codigo esta na imagem"
    )
    assert _tem_regra(DOCKERFILE, CARIMBO_DO_BUILD), (
        "o carimbo `/app/CONSTRUIDO_EM` saiu do docker/Dockerfile: passa a nao haver marca "
        "nenhuma de QUANDO a imagem foi construida"
    )


def test_o_carimbo_do_build_vem_depois_do_codigo():
    """Ordem, e nao presenca: e a ordem que preserva o cache do `pip install`.

    O carimbo muda a cada build. Tudo o que viesse DEPOIS dele seria refeito junto, entao
    mante-lo no fim e o que faz o rebuild do dia a dia (mudar `src/` e reconstruir) aproveitar
    a camada de dependencias. As duas linhas continuam no arquivo se a ordem inverter -- por
    isso a assercao e de posicao.
    """
    codigo = _indice_da_regra(DOCKERFILE, COPIA_DO_CODIGO)
    carimbo = _indice_da_regra(DOCKERFILE, CARIMBO_DO_BUILD)

    assert codigo >= 0, "o `COPY src/ /app/src/` saiu do docker/Dockerfile"
    assert carimbo >= 0, "o carimbo do build saiu do docker/Dockerfile"
    assert carimbo > codigo, (
        "o carimbo do build ficou ANTES do `COPY` do codigo: como ele muda a cada build, o "
        "codigo e o `pip install` perdem o cache em todo rebuild"
    )


def test_a_revisao_fica_depois_das_camadas_caras():
    """Um `ARG` invalida o cache do que vem DEPOIS dele -- e isso foi MEDIDO, nao deduzido.

    A primeira versao desta mudanca declarava `ARG REVISAO` no topo do arquivo, junto do
    comentario que explica a identidade do build. O build seguinte refez
    `RUN pip install --no-cache-dir -r requirements.txt` -- medido na saida:
    `#10 13.71 Installing build dependencies: started` -- apenas porque o valor da revisao
    tinha mudado. Um `ARG` entra na chave de cache das instrucoes seguintes mesmo sem ser
    citado por nenhuma delas, e a camada das dependencias e justamente a que o rebuild do dia
    a dia (mexer em `src/` e reconstruir) precisa manter.

    A assercao e de POSICAO: as duas linhas continuam no arquivo se a ordem inverter.
    """
    dependencias = _indice_da_regra(DOCKERFILE, INSTALACAO_DE_DEPENDENCIAS)
    revisao = _indice_da_regra(DOCKERFILE, ARG_DA_REVISAO)

    assert dependencias >= 0, "o `RUN pip install` saiu do docker/Dockerfile"
    assert revisao >= 0, "o `ARG REVISAO` saiu do docker/Dockerfile"
    assert revisao > dependencias, (
        "o `ARG REVISAO` ficou ANTES da instalacao das dependencias: mudar a revisao passa a "
        "reinstalar todas as dependencias em todo rebuild, porque um ARG entra na chave de "
        "cache do que vem depois dele -- medido em 2026-10-11"
    )


def test_o_compose_passa_a_revisao_para_o_build():
    """O Dockerfile sozinho nao basta: sem o `args`, o rotulo fica sempre `desconhecida`."""
    assert _tem_linha_com(COMPOSE, PASSAGEM_DA_REVISAO), (
        "o `docker-compose.yml` deixou de passar `REVISAO` para o build: o rotulo da imagem "
        "fica preso no valor padrao e nao diz mais qual codigo foi construido"
    )


def test_o_readme_manda_reconstruir_depois_de_mudar_o_codigo():
    """A guarda de documentacao: o comando E o motivo, na mesma secao.

    As duas assercoes sao necessarias. So o comando nao ensina nada (ele ja aparecia no README
    como parte da subida inicial do stack), e so o motivo nao da o que executar. O defeito de
    2026-10-11 foi exatamente essa combinacao ausente: o comando existia, e nada dizia que ele
    e obrigatorio depois de mexer em `src/`.
    """
    secao = _secao(README, SECAO_DOCKER)

    assert secao, (
        "a secao `%s` saiu do README: o operador volta a nao ter onde ler que a mudanca em "
        "`src/` precisa de rebuild" % SECAO_DOCKER
    )
    assert COMANDO_DE_ATUALIZACAO in secao, (
        "a secao `%s` do README nao traz o comando `%s`" % (SECAO_DOCKER, COMANDO_DE_ATUALIZACAO)
    )
    assert MOTIVO_NO_README in secao, (
        "a secao `%s` do README traz o comando mas nao explica POR QUE ele e obrigatorio "
        "(`%s`)" % (SECAO_DOCKER, MOTIVO_NO_README)
    )


def codigo_do_atalho() -> list:
    """Linhas de CODIGO do `atualizar.ps1`, sem os comentarios.

    As guardas do atalho medem o que ele **faz**. O proprio script cita, em comentario, as duas
    formas que falharam — o formato com aspas no `docker inspect` e o
    `$ErrorActionPreference = "Stop"` —, porque a explicacao do defeito mora ao lado do
    conserto. Medir o texto inteiro faria a guarda acusar a documentacao do problema; foi o que
    aconteceu na primeira versao de uma delas, e a falha e a prova de que ela discrimina.
    """
    return [linha for linha in _linhas(ATALHO) if not linha.lstrip().startswith("#")]


def test_o_atalho_de_atualizacao_faz_o_build_e_mostra_a_identidade():
    """Guarda de TEXTO, e o limite e declarado: a suite NAO tem Docker.

    O que ela prende e o que o atalho precisa TER para servir: o mesmo comando que o README
    manda, a revisao do git entregue ao build (sem ela o rotulo fica em `desconhecida`), a
    leitura das duas marcas — para o operador ver o que subiu sem digitar `docker inspect` — e
    a ancora na propria pasta, que e o que faz o atalho funcionar de qualquer diretorio.
    """
    assert os.path.isfile(ATALHO), (
        "o `atualizar.ps1` saiu da raiz: o operador volta a ter de montar o rebuild a mao"
    )
    assert _tem_linha_com(ATALHO, COMANDO_DE_ATUALIZACAO), (
        "o atalho nao roda `%s`" % COMANDO_DE_ATUALIZACAO
    )
    assert _tem_linha_com(ATALHO, "REVISAO"), (
        "o atalho nao entrega a revisao ao build: o rotulo da imagem fica em `desconhecida`"
    )
    assert _tem_linha_com(ATALHO, LEITURA_DO_CARIMBO), (
        "o atalho nao le o carimbo do build: ele reconstroi sem dizer o que ficou no ar"
    )
    assert _tem_linha_com(ATALHO, "$PSScriptRoot"), (
        "o atalho deixou de se ancorar na propria pasta: so funcionaria com o operador ja "
        "dentro da raiz do projeto"
    )
    assert not any('$ErrorActionPreference = "Stop"' in linha for linha in codigo_do_atalho()), (
        "o atalho voltou a usar `$ErrorActionPreference = \"Stop\"`: o `docker compose` escreve "
        "o progresso do build em stderr, e sob `Stop` cada linha dessas aborta o script — "
        "inclusive com a saida apenas redirecionada. Medido em 2026-10-11 nas duas formas"
    )


def test_o_atalho_le_o_rotulo_com_json_e_nao_com_aspas_no_formato():
    """A leitura do rotulo, no formato que sobrevive ao PowerShell.

    Medido em 2026-10-11, na primeira execucao do atalho: com
    `--format '{{index .Config.Labels "org.opencontainers.image.revision"}}'`, as aspas
    DENTRO do argumento sao comidas pelo PowerShell ao montar a linha de comando do docker, e
    o `inspect` responde `template parsing error: function "org" not defined` — o atalho
    imprimia `revisao :` VAZIO e nao avisava. A forma `{{json .Config.Labels}}` nao tem aspas
    internas, e quem separa a chave e o `ConvertFrom-Json`.

    As duas metades da assercao sao necessarias: a presenca da forma boa nao impede alguem de
    reintroduzir a ruim, que foi a que falhou.

    As duas olham as linhas de CODIGO, e nao o texto inteiro: o proprio comentario do atalho
    cita a forma ruim para registrar o defeito, e medir comentario faria a guarda acusar a
    documentacao que explica o problema. (A primeira versao desta guarda fez exatamente isso,
    e falhou — o que e a prova de que ela discrimina.)
    """
    codigo = codigo_do_atalho()

    assert any("{{json .Config.Labels}}" in linha for linha in codigo), (
        "o atalho deixou de ler o rotulo por JSON: o formato com aspas internas volta a ser o "
        "caminho, e ele imprime a revisao VAZIA"
    )
    assert not any("{{index .Config.Labels" in linha for linha in codigo), (
        "o atalho voltou a usar `{{index .Config.Labels \"chave\"}}`: o PowerShell come as "
        "aspas internas e o `docker inspect` falha com `function \"org\" not defined`"
    )


def test_mutacao_a_guarda_da_identidade_falha_sem_o_rotulo(tmp_path):
    copia = _copia_sem_a_regra(DOCKERFILE, str(tmp_path / "Dockerfile"), ROTULO_DA_REVISAO)

    assert not _tem_regra(copia, ROTULO_DA_REVISAO), (
        "a assercao passou com o rotulo removido: ela nao prende nada"
    )
    assert _tem_regra(copia, CARIMBO_DO_BUILD), (
        "o controle: tirar o rotulo nao pode levar o carimbo junto, senao a mutacao mede "
        "outra coisa"
    )
