"""Varredura por referencia residual ao nome antigo, no conjunto VIVO.

Executado por /reversa-coding na feature 003-renomear-pasta-app-para-src (T018).
Gera o relatorio em evidence/varredura-residual.txt.

Conjunto varrido (o "vivo"): codigo da aplicacao, testes, configuracao e os
scripts executaveis de instrumentacao. NAO entram:
  - _reversa_bugs/, _reversa_refactor/, _reversa_forward/  (registro historico)
  - _reversa_sdd/*.md e _reversa_sdd/addenda/              (documentacao de extracao)
  - _reversa_docs/                                          (site derivado)
Esses sao preservados por decisao (RN-03) e corrigidos por adendo, nao por edicao.
"""
import pathlib

ALVO = "analisador-genealogico"
# Conjunto vivo, em dois grupos com escopos diferentes:
#   codigo, testes e configuracao -> varredura ampla de extensoes;
#   instrumentacao executavel      -> APENAS .py.
# Os .md dentro de _reversa_sdd/parity e _reversa_sdd/oracle sao registro e
# documentacao da extracao: preservados por decisao (RN-03), corrigidos por
# adendo, nunca por reescrita.
RAIZES_CODIGO = ["src", "tests", ".vscode"]
RAIZES_EXECUTAVEIS = ["_reversa_sdd/parity", "_reversa_sdd/oracle"]
ARQUIVOS_SOLTOS = ["pyrefly.toml"]
EXT = (".py", ".toml", ".json", ".md", ".html", ".txt", ".jsonl", ".yml", ".yaml")
EXT_EXECUTAVEL = (".py",)
NL = chr(10)

# Excecoes aceitas, declaradas explicitamente. Cada uma tem motivo.
EXCECOES = {
    "src/reconstructed/__init__.py": (
        "Nome do PROJETO em docstring, nao caminho. O pacote foi reconstruido a partir do "
        "projeto analisador-genealogico, e o projeto nao foi renomeado -- apenas a raiz de "
        "codigo. Manter e correto."
    ),
    "_reversa_sdd/oracle/run_oracle.py": (
        "Comando contra o commit congelado e43ca22, onde o caminho ERA analisador-genealogico/"
        "app.py. Reescrever produziria um comando que falha, porque aquele commit nao tem src/. "
        "Excecao deliberada, registrada no transformador apply-path-updates.py."
    ),
}


def varrer():
    achados = []
    grupos = [(RAIZES_CODIGO, EXT), (RAIZES_EXECUTAVEIS, EXT_EXECUTAVEL)]
    for raizes, extensoes in grupos:
        for raiz in raizes:
            base = pathlib.Path(raiz)
            if not base.exists():
                continue
            for p in sorted(base.rglob("*")):
                if not p.is_file() or p.suffix.lower() not in extensoes:
                    continue
                try:
                    t = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                for i, linha in enumerate(t.split(NL), 1):
                    if ALVO in linha:
                        achados.append((str(p).replace("\\", "/"), i, linha.strip()))
    for nome in ARQUIVOS_SOLTOS:
        p = pathlib.Path(nome)
        if not p.exists():
            continue
        for i, linha in enumerate(p.read_text(encoding="utf-8").split(NL), 1):
            if ALVO in linha:
                achados.append((nome, i, linha.strip()))
    return achados


def main():
    achados = varrer()
    linhas = []
    linhas.append("Varredura por referencia residual ao nome antigo -- conjunto vivo")
    linhas.append("Feature: 003-renomear-pasta-app-para-src | Acao: T018")
    linhas.append("Conjunto varrido (codigo, testes, configuracao): " + ", ".join(RAIZES_CODIGO + ARQUIVOS_SOLTOS))
    linhas.append("Conjunto varrido (instrumentacao executavel, apenas .py): " + ", ".join(RAIZES_EXECUTAVEIS))
    linhas.append("Fora do conjunto, por decisao (RN-03): registro historico e documentacao de extracao.")
    linhas.append("")
    linhas.append("ocorrencias encontradas = %d" % len(achados))
    linhas.append("")

    esperadas = 0
    inesperadas = 0
    for caminho, numero, texto in achados:
        chave = caminho.replace("\\", "/")
        motivo = EXCECOES.get(chave)
        if motivo:
            esperadas += 1
            linhas.append("[ESPERADA] %s:%d" % (chave, numero))
            linhas.append("           %s" % texto)
            linhas.append("           motivo: %s" % motivo)
        else:
            inesperadas += 1
            linhas.append("[INESPERADA] %s:%d" % (chave, numero))
            linhas.append("           %s" % texto)
        linhas.append("")

    linhas.append("excecoes aceitas e declaradas = %d" % esperadas)
    linhas.append("ocorrencias inesperadas     = %d" % inesperadas)
    linhas.append("")
    if inesperadas == 0:
        linhas.append("VEREDITO: nenhuma referencia residual inesperada. RF-02 satisfeito.")
    else:
        linhas.append("VEREDITO: ha referencia residual inesperada. RF-02 NAO satisfeito.")

    destino = pathlib.Path("_reversa_forward/003-renomear-pasta-app-para-src/evidence/varredura-residual.txt")
    destino.write_text(NL.join(linhas) + NL, encoding="utf-8", newline="")
    # Resumo na console. O detalhe fica no arquivo: a console deste ambiente e cp1252
    # e nao representa todos os caracteres do relatorio.
    print("conjunto vivo varrido; relatorio em " + str(destino).replace("\\", "/"))
    print("ocorrencias encontradas      = %d" % len(achados))
    print("excecoes aceitas declaradas  = %d" % esperadas)
    print("ocorrencias inesperadas      = %d" % inesperadas)
    print("VEREDITO: " + ("nenhuma referencia residual inesperada; RF-02 satisfeito."
                          if inesperadas == 0 else
                          "ha referencia residual inesperada; RF-02 NAO satisfeito."))
    return 0 if inesperadas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
