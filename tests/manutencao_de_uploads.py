"""Manutencao da pasta de upload: migrar, manifesto, expurgo, duplicatas.

Ferramenta de operador da feature `010-uploads-fora-do-repositorio`. Ela existe para
duas tarefas que a aplicacao, de proposito, **nao** faz: tirar os arquivos ja enviados
de dentro do repositorio (`migrar`) e remover residuo de instrumento sob revisao
humana (`manifesto` + `expurgo`).

## Por que ela mora em `tests/` (D-03)

`.reversa/reversa-config.json` libera `tests/**` e nao libera pasta nova como
`scripts/**`. `src/tools/**` seria alternativa, mas o `docker/Dockerfile` copia `src/`
inteiro, entao a ferramenta viajaria na imagem de producao — lugar errado para uma
ferramenta de manutencao local. O padrao seguido e o de `tests/icone_de_atalho.py`
(feature 009): um modulo utilitario em `tests/`, com teste que o exercita. O
compromisso esta declarado no roadmap (`D-03`).

## Regras que a ferramenta nao quebra

1. **Nunca remove a origem.** `migrar` copia; quem apaga a pasta antiga e o operador
   (`onboarding.md` secao 12).
2. **Nunca remove o que nao esta no manifesto.** O expurgo le a lista revisavel e
   recusa qualquer coisa fora dela (`RN-06`).
3. **Nunca remove duplicata.** Copias byte a byte identicas de arquivo do operador sao
   **relatadas** (`D-06`): tres arquivos da mesma arvore convivem com um quarto de
   mesmo tamanho e conteudo distinto, e tamanho nao serve de criterio.
4. **Recusa link simbolico e caminho fora da pasta alvo.** A forma fechada do nome
   (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) e o contrato de seguranca do armazenamento
   (`_reversa_sdd/upload-gedcom/contracts.md#2.1`) e e reaproveitada aqui.

## Uso

    python tests/manutencao_de_uploads.py migrar --origem DIR --destino DIR [--relatorio ARQ]
    python tests/manutencao_de_uploads.py manifesto --pasta DIR --saida ARQ
    python tests/manutencao_de_uploads.py expurgo --manifesto ARQ [--pasta DIR] (--dry-run|--aplicar) [--relatorio ARQ]
    python tests/manutencao_de_uploads.py duplicatas --pasta DIR [--relatorio ARQ]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

# A mesma forma fechada do armazenamento: 16 hexadecimais, separador de dois
# underscores e o nome visivel. Nao ha lista negra a manter — e validacao por forma.
FORMA_DO_NOME = re.compile(r"^[0-9a-f]{16}__[A-Za-z0-9._-]+$")

SEPARADOR = "__"

# Nomes que os instrumentos de verificacao enviam pela aplicacao. E o criterio do
# manifesto: o nome visivel do arquivo armazenado pertence a este conjunto fechado.
# Cada um deles foi medido na pasta real em 2026-10-09 (18 arquivos, 6.631 bytes).
NOMES_DE_INSTRUMENTO = frozenset({
    # sondas de GEDCOM do harness de paridade
    "probe.ged",
    "arvore.ged",
    "basic.ged",
    "nomes-inertes.ged",
    # fixtures de DNA do harness de paridade
    "matches_dois_kits.csv",
    "utf8.csv",
    "duplicated.csv",
    "no_intersection.csv",
    "generic.csv",
    "cm_boundaries.csv",
    "latin1.csv",
    "missing_col.csv",
})

MOTIVO_INSTRUMENTO = "nome de sonda/fixture de instrumento (paridade/evidencia)"

CABECALHO_DO_MANIFESTO = "# Manifesto de residuo de instrumento - feature 010"


def _agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_de(caminho: str) -> str:
    """Impressao digital do conteudo, em blocos (arquivos de 5 MB existem aqui)."""
    resumo = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def nome_visivel(nome_armazenado: str) -> str:
    """A parte depois do separador, ou o proprio nome quando nao ha separador."""
    _, _, visivel = nome_armazenado.partition(SEPARADOR)
    return visivel or nome_armazenado


def inventariar(pasta: str) -> dict:
    """`{nome: (bytes, sha256)}` dos arquivos regulares da pasta, em ordem de nome."""
    inventario = {}
    for nome in sorted(os.listdir(pasta)):
        caminho = os.path.join(pasta, nome)
        if os.path.isfile(caminho) and not os.path.islink(caminho):
            inventario[nome] = (os.path.getsize(caminho), sha256_de(caminho))
    return inventario


def _dentro_da_pasta(pasta: str, nome: str) -> bool:
    """Defesa em profundidade contra escape de caminho, alem da forma fechada."""
    alvo = os.path.abspath(os.path.join(pasta, nome))
    raiz = os.path.abspath(pasta)
    return os.path.dirname(alvo) == raiz


# ---------------------------------------------------------------------------
# migrar
# ---------------------------------------------------------------------------

@dataclass
class ResultadoDaMigracao:
    copiados: list = field(default_factory=list)
    ja_conferidos: list = field(default_factory=list)
    divergentes: list = field(default_factory=list)
    origem_bytes: int = 0
    destino_bytes: int = 0

    @property
    def ok(self) -> bool:
        return not self.divergentes and len(self.copiados) + len(self.ja_conferidos) > 0

    def texto(self) -> str:
        linhas = [
            "# Migracao - feature 010",
            "# Gerado em: " + _agora(),
            "# copiados: %d" % len(self.copiados),
            "# ja conferidos (mesmo sha256 no destino): %d" % len(self.ja_conferidos),
            "# divergentes (NAO sobrescritos, origem intacta): %d" % len(self.divergentes),
            "# bytes na origem: %d" % self.origem_bytes,
            "# bytes no destino: %d" % self.destino_bytes,
            "",
        ]
        for nome in self.copiados:
            linhas.append("copiado\t" + nome)
        for nome in self.ja_conferidos:
            linhas.append("ja_conferido\t" + nome)
        for nome in self.divergentes:
            linhas.append("DIVERGENTE\t" + nome)
        return "\n".join(linhas) + "\n"


def migrar(origem: str, destino: str) -> ResultadoDaMigracao:
    """Copia `origem` para `destino` conferindo `sha256` arquivo a arquivo.

    Idempotente: arquivo que ja existe no destino com o **mesmo** hash nao e regravado.
    Arquivo com hash **diferente** nao e sobrescrito e nao remove a origem — ele entra
    no relatorio como divergente. Interromper no meio e inofensivo: repetir continua.
    """
    if not os.path.isdir(origem):
        raise SystemExit("origem inexistente: %s" % origem)
    os.makedirs(destino, exist_ok=True)

    resultado = ResultadoDaMigracao()
    for nome, (tamanho, hash_origem) in inventariar(origem).items():
        resultado.origem_bytes += tamanho
        origem_arquivo = os.path.join(origem, nome)
        destino_arquivo = os.path.join(destino, nome)
        if os.path.exists(destino_arquivo):
            if sha256_de(destino_arquivo) == hash_origem:
                resultado.ja_conferidos.append(nome)
                resultado.destino_bytes += os.path.getsize(destino_arquivo)
                continue
            resultado.divergentes.append(nome)
            resultado.destino_bytes += os.path.getsize(destino_arquivo)
            continue
        shutil.copy2(origem_arquivo, destino_arquivo)
        if sha256_de(destino_arquivo) != hash_origem:
            resultado.divergentes.append(nome)
        else:
            resultado.copiados.append(nome)
        resultado.destino_bytes += os.path.getsize(destino_arquivo)
    return resultado


# ---------------------------------------------------------------------------
# manifesto
# ---------------------------------------------------------------------------

@dataclass
class Entrada:
    nome: str
    sha256: str
    motivo: str


def gerar_manifesto(pasta: str, saida: str) -> list:
    """Escreve a lista revisavel do residuo de instrumento e devolve as entradas.

    O criterio e o **nome visivel** pertencer ao conjunto fechado dos instrumentos.
    A lista e regeneravel por comando: rodar de novo depois de uma verificacao nova
    produz a lista atualizada. Ela carrega a pasta de origem no cabecalho, para o
    expurgo nao depender de o operador repetir o caminho.
    """
    entradas = [
        Entrada(nome, hash_do_arquivo, MOTIVO_INSTRUMENTO)
        for nome, (_tamanho, hash_do_arquivo) in inventariar(pasta).items()
        if nome_visivel(nome) in NOMES_DE_INSTRUMENTO
    ]
    linhas = [
        CABECALHO_DO_MANIFESTO,
        "# Gerado em: " + _agora(),
        "# Pasta: " + os.path.abspath(pasta),
        "# Arquivos listados: %d" % len(entradas),
        "# REGRA: o expurgo remove APENAS as linhas abaixo.",
        "# Revise esta lista e apague as linhas que voce NAO quer remover.",
        "# Formato: nome<TAB>sha256<TAB>motivo",
        "",
    ]
    for entrada in entradas:
        linhas.append("\t".join((entrada.nome, entrada.sha256, entrada.motivo)))
    with open(saida, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(linhas) + "\n")
    return entradas


def ler_manifesto(caminho: str) -> tuple:
    """Devolve `(pasta, entradas)`. A pasta vem do cabecalho do manifesto."""
    pasta = None
    entradas = []
    with open(caminho, encoding="utf-8") as fh:
        for linha in fh:
            linha = linha.rstrip("\n")
            if linha.startswith("# Pasta:"):
                pasta = linha.split(":", 1)[1].strip()
                continue
            if not linha.strip() or linha.startswith("#"):
                continue
            partes = linha.split("\t")
            if len(partes) != 3:
                raise SystemExit("linha de manifesto invalida: %r" % linha)
            entradas.append(Entrada(partes[0], partes[1], partes[2]))
    return pasta, entradas


# ---------------------------------------------------------------------------
# expurgo
# ---------------------------------------------------------------------------

@dataclass
class ResultadoDoExpurgo:
    removidos: list = field(default_factory=list)
    recusados: list = field(default_factory=list)   # (nome, motivo)
    ausentes: list = field(default_factory=list)
    duplicatas: list = field(default_factory=list)
    simulado: bool = True

    def texto(self) -> str:
        modo = "SIMULACAO (nada foi removido)" if self.simulado else "APLICADO"
        linhas = [
            "# Expurgo de residuo - feature 010",
            "# Gerado em: " + _agora(),
            "# Modo: " + modo,
            "# removidos: %d" % len(self.removidos),
            "# recusados: %d" % len(self.recusados),
            "# ausentes: %d" % len(self.ausentes),
            "# duplicatas relatadas (preservadas): %d grupo(s)" % len(self.duplicatas),
            "",
        ]
        for nome in self.removidos:
            linhas.append(("seria removido\t" if self.simulado else "removido\t") + nome)
        for nome in self.ausentes:
            linhas.append("ausente\t" + nome)
        for nome, motivo in self.recusados:
            linhas.append("RECUSADO\t%s\t%s" % (nome, motivo))
        if self.duplicatas:
            linhas.append("")
            linhas.append("# Duplicatas byte a byte identicas - RELATADAS, nao removidas (D-06)")
            for grupo in self.duplicatas:
                linhas.append("duplicata\t%d copias\tsha256=%s" % (len(grupo[1]), grupo[0]))
                for nome in grupo[1]:
                    linhas.append("    " + nome)
        return "\n".join(linhas) + "\n"


def duplicatas(pasta: str) -> list:
    """Grupos `(sha256, [nomes])` de arquivos byte a byte identicos. Nunca remove."""
    por_hash = {}
    for nome, (_tamanho, hash_do_arquivo) in inventariar(pasta).items():
        por_hash.setdefault(hash_do_arquivo, []).append(nome)
    return sorted(
        ((h, sorted(nomes)) for h, nomes in por_hash.items() if len(nomes) > 1),
        key=lambda grupo: grupo[1][0],
    )


def expurgar(pasta: str, entradas: list, aplicar: bool = False) -> ResultadoDoExpurgo:
    """Remove **apenas** o que esta no manifesto, conferindo o hash antes de remover.

    Recusa, sem remover e com motivo no relatorio: nome fora da forma fechada,
    caminho que sairia da pasta, link simbolico, e arquivo cujo conteudo mudou desde
    a geracao do manifesto (nesse caso o manifesto esta velho — regenere).
    `aplicar=False` e simulacao: tudo e classificado e nada e removido.
    """
    resultado = ResultadoDoExpurgo(simulado=not aplicar)
    for entrada in entradas:
        nome = entrada.nome
        caminho = os.path.join(pasta, nome)
        if not FORMA_DO_NOME.match(nome):
            resultado.recusados.append((nome, "nome fora da forma fechada"))
            continue
        if not _dentro_da_pasta(pasta, nome):
            resultado.recusados.append((nome, "caminho sairia da pasta alvo"))
            continue
        if os.path.islink(caminho):
            resultado.recusados.append((nome, "link simbolico"))
            continue
        if not os.path.isfile(caminho):
            resultado.ausentes.append(nome)
            continue
        if sha256_de(caminho) != entrada.sha256:
            resultado.recusados.append((nome, "hash diferente do manifesto (regenere)"))
            continue
        if aplicar:
            os.remove(caminho)
        resultado.removidos.append(nome)
    resultado.duplicatas = duplicatas(pasta)
    return resultado


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _escrever(caminho: str | None, texto: str) -> None:
    if caminho:
        with open(caminho, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manutencao da pasta de upload (feature 010).")
    sub = parser.add_subparsers(dest="verbo", required=True)

    p_migrar = sub.add_parser("migrar", help="copia a origem para o destino com conferencia de sha256")
    p_migrar.add_argument("--origem", required=True)
    p_migrar.add_argument("--destino", required=True)
    p_migrar.add_argument("--relatorio")

    p_man = sub.add_parser("manifesto", help="gera a lista revisavel de residuo de instrumento")
    p_man.add_argument("--pasta", required=True)
    p_man.add_argument("--saida", required=True)

    p_exp = sub.add_parser("expurgo", help="remove apenas o que esta no manifesto")
    p_exp.add_argument("--manifesto", required=True)
    p_exp.add_argument("--pasta", help="sobrepoe a pasta registrada no cabecalho do manifesto")
    p_exp.add_argument("--relatorio")
    grupo = p_exp.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--dry-run", action="store_true", help="lista e nao remove")
    grupo.add_argument("--aplicar", action="store_true", help="remove de fato")

    p_dup = sub.add_parser("duplicatas", help="relata copias identicas sem remove-las")
    p_dup.add_argument("--pasta", required=True)
    p_dup.add_argument("--relatorio")

    args = parser.parse_args(argv)

    if args.verbo == "migrar":
        resultado = migrar(args.origem, args.destino)
        texto = resultado.texto()
        print(texto, end="")
        _escrever(args.relatorio, texto)
        return 0 if resultado.ok or resultado.ja_conferidos else 2

    if args.verbo == "manifesto":
        entradas = gerar_manifesto(args.pasta, args.saida)
        print("manifesto com %d arquivo(s): %s" % (len(entradas), args.saida))
        return 0

    if args.verbo == "expurgo":
        pasta_do_manifesto, entradas = ler_manifesto(args.manifesto)
        pasta = args.pasta or pasta_do_manifesto
        if not pasta:
            raise SystemExit("pasta nao informada e ausente no cabecalho do manifesto")
        resultado = expurgar(pasta, entradas, aplicar=args.aplicar)
        texto = resultado.texto()
        print(texto, end="")
        _escrever(args.relatorio, texto)
        return 0 if not resultado.recusados else 1

    if args.verbo == "duplicatas":
        grupos = duplicatas(args.pasta)
        linhas = ["# Duplicatas relatadas - nenhuma foi removida", "# Grupos: %d" % len(grupos), ""]
        for hash_do_grupo, nomes in grupos:
            linhas.append("sha256=%s\t%d copias" % (hash_do_grupo, len(nomes)))
            for nome in nomes:
                linhas.append("    " + nome)
        texto = "\n".join(linhas) + "\n"
        print(texto, end="")
        _escrever(args.relatorio, texto)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
