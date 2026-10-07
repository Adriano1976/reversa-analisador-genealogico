"""Acrescenta o registro de reversao do T023(a) ao progress.jsonl."""
import io
import json

A = r"_reversa_forward/005-nucleo-puro-src/progress.jsonl"

REG = {
    "ts": "2026-10-07T12:30:00Z",
    "action": "T023(a)",
    "status": "reverted",
    "files": [
        "src/parsers/gedcom_parser.py",
        "tests/fixtures/arvore_atual.py",
        "tests/test_upload.py",
        "tests/test_confrontacao_gedcom_dna.py",
        "tests/test_characterization_matching.py",
        "tests/test_path_search.py",
    ],
    "nota": (
        "REVERTIDO por decisao do usuario, depois de a suite ficar VERMELHA com 49 falhas. "
        "Causa: ataquei (a) antes de (b); tornar o parse puro quebrou 70 testes de uma vez, porque "
        "todo fixture que carregava via parse e lia as globais passou a ler dicionario vazio. "
        "A ORDEM CORRETA E A INVERSA: primeiro os fixtures devolvem a arvore do parse COM o parser "
        "ainda mutando (suite verde o tempo todo, porque as duas leituras sao equivalentes), e so "
        "depois a mutacao sai. O git checkout do parser levou junto o carregar_arvore, que era "
        "trabalho nao commitado, e ele foi RESTAURADO com semantica de transicao (devolve a arvore "
        "E muta as globais). TRES ERROS MEUS, registrados para nao repetir: (1) a ordem de (a) e (b); "
        "(2) substituicao global de texto criou recursao infinita em dois helpers e 9 RecursionError; "
        "(3) o recurso do helper atual() de ler as globais MISTURA a arvore de outro arquivo de teste "
        "— o test_path_search passava isolado e falhava na suite. "
        "MEDIDO APOS A REVERSAO: suite 178 passed / 1 xfailed / 15 errors e paridade 100 por cento "
        "nas 6 fixtures, exit 0. Detalhe em evidence/T023-estado-apos-reversao.md"
    ),
}


def main() -> int:
    linhas = [l for l in io.open(A, encoding="utf-8").read().splitlines() if l.strip()]
    linhas.append(json.dumps(REG, ensure_ascii=False))
    io.open(A, "w", encoding="utf-8", newline="").write("\n".join(linhas) + "\n")
    validadas = [json.loads(l) for l in io.open(A, encoding="utf-8") if l.strip()]
    print("JSONL OK - %d linhas; ultima: %s %s"
          % (len(validadas), validadas[-1]["action"], validadas[-1]["status"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
