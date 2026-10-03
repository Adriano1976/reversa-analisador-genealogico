"""Atualiza as referencias de caminho da raiz de codigo: analisador-genealogico -> src.

Executado por /reversa-coding na feature 003-renomear-pasta-app-para-src.
Fica arquivado como evidencia: registra exatamente o que foi transformado.

Cobre as acoes:
  T009  os 8 arquivos de teste (9 pontos de caminho, incluindo a definicao da
        pasta do aplicativo que alimenta o root_path e o caminho do app.py)
  T010  pyrefly.toml
  T011  .vscode/settings.json
  T012  harness.py, _check_split_types.py, _golden_capture.py
  T013  _verify_fix_gives_parity.py (inclui a string de busca que ele guarda)
  T014  _profile_big.py, _profile_collector_costs.py, _scr005_find_trio.py,
        oracle/run_oracle.py

EXCECAO DELIBERADA em run_oracle.py: a linha que contem `git show e43ca22` cita o
caminho COMO ELE ERA no commit congelado. Reescreve-la produziria um comando que
falha, porque aquele commit nao tem `src/`. A ocorrencia remanescente e esperada
e esta declarada na evidencia da varredura residual (T018).

Nenhum arquivo de _reversa_bugs/, _reversa_refactor/ ou _reversa_forward/ e
tocado, e nenhuma spec de _reversa_sdd/ e reescrita (RN-03).
"""
import pathlib
import sys

ANTIGO = "analisador-genealogico"
NOVO = "src"
NL = chr(10)


def ler(caminho):
    return pathlib.Path(caminho).read_text(encoding="utf-8")


def gravar(caminho, texto):
    # newline="" preserva LF, sem traducao de fim de linha
    pathlib.Path(caminho).write_text(texto, encoding="utf-8", newline="")


def trocar(caminho):
    p = pathlib.Path(caminho)
    if not p.exists():
        return None
    t = ler(p)
    n = t.count(ANTIGO)
    if n == 0:
        return None
    gravar(p, t.replace(ANTIGO, NOVO))
    return n


def trocar_exceto(caminho, marcador):
    """Troca todas as ocorrencias, exceto nas linhas que contem o marcador."""
    p = pathlib.Path(caminho)
    if not p.exists():
        return None
    linhas = ler(p).split(NL)
    n = 0
    for i, linha in enumerate(linhas):
        if ANTIGO in linha and marcador not in linha:
            linhas[i] = linha.replace(ANTIGO, NOVO)
            n += 1
    if n == 0:
        return None
    gravar(p, NL.join(linhas))
    return n


def main():
    relatorio = []

    # T009 - arquivos de teste
    for p in sorted(pathlib.Path("tests").glob("*.py")):
        n = trocar(p)
        if n:
            relatorio.append(("T009", str(p), n))

    # T010 e T011 - configuracao
    for rotulo, alvo in (("T010", "pyrefly.toml"), ("T011", ".vscode/settings.json")):
        n = trocar(alvo)
        if n:
            relatorio.append((rotulo, alvo, n))

    # T012 - instrumentacao que resolve a raiz de codigo
    for alvo in ("harness.py", "_check_split_types.py", "_golden_capture.py"):
        n = trocar(pathlib.Path("_reversa_sdd") / "parity" / alvo)
        if n:
            relatorio.append(("T012", "_reversa_sdd/parity/" + alvo, n))

    # T013 - contraprova, incluindo a string de busca
    n = trocar(pathlib.Path("_reversa_sdd") / "parity" / "_verify_fix_gives_parity.py")
    if n:
        relatorio.append(("T013", "_reversa_sdd/parity/_verify_fix_gives_parity.py", n))

    # T014 - instrumentacao que aponta para a pasta de upload + runner do oraculo
    for alvo in ("_profile_big.py", "_profile_collector_costs.py", "_scr005_find_trio.py"):
        n = trocar(pathlib.Path("_reversa_sdd") / "parity" / alvo)
        if n:
            relatorio.append(("T014", "_reversa_sdd/parity/" + alvo, n))
    n = trocar_exceto(pathlib.Path("_reversa_sdd") / "oracle" / "run_oracle.py", "e43ca22")
    if n:
        relatorio.append(("T014", "_reversa_sdd/oracle/run_oracle.py (exceto a linha do git show e43ca22)", n))

    if not relatorio:
        print("NADA A FAZER: nenhuma ocorrencia encontrada")
        return 0

    for rotulo, caminho, n in relatorio:
        print("%-6s %-62s %d ocorrencia(s)" % (rotulo, caminho, n))
    print()
    print("arquivos alterados = %d" % len(relatorio))
    print("ocorrencias trocadas = %d" % sum(r[2] for r in relatorio))
    return 0


if __name__ == "__main__":
    sys.exit(main())
