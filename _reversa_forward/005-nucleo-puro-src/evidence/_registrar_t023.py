"""Anexa ao progress.jsonl os dois estagios finais do T023 (feature 005).

Script, e nao edicao direta, por dois motivos: o JSONL tem uma linha por evento e
nao tolera quebra de linha no meio, e o PowerShell aqui destroi acentos em
here-string. Rodar da raiz do projeto:

    python _reversa_forward/005-nucleo-puro-src/evidence/_registrar_t023.py
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
PROGRESS = os.path.join(RAIZ, "_reversa_forward", "005-nucleo-puro-src", "progress.jsonl")

EVENTOS = [
    {
        "ts": "2026-10-07T14:00:00Z",
        "action": "T023(b)",
        "status": "done",
        "files": [
            "tests/fixtures/arvore_atual.py",
            "tests/fixtures/helpers.py",
            "tests/test_characterization_matching.py",
            "tests/test_characterization_mermaid.py",
            "tests/test_mermaid_escape.py",
            "tests/test_dna_analysis.py",
            "tests/test_path_search.py",
            "tests/test_confrontacao_gedcom_dna.py",
            "tests/test_formatacao_cm.py",
            "tests/test_upload.py",
            "tests/test_arvore_devolvida.py",
        ],
        "nota": (
            "(b) executado ANTES de (a), que foi a licao da reversao. Os fixtures e testes "
            "passaram a ler a arvore pelo RETORNO do parse, com o parser ainda mutando as "
            "globais; suite verde o tempo todo, porque as duas leituras eram equivalentes. "
            "Quatro leitores do global foram encontrados e corrigidos: o fixture `carregado` "
            "de test_characterization_mermaid devolvia o modulo de estado (virou atual()); "
            "`_carregar` de test_mermaid_escape chamava load_gedcom_and_build_graph e "
            "descartava o valor, e o teste recorria a _gs (virou carregar_arvore + a arvore "
            "passada adiante); os fixtures dna_loaded e tree devolviam/reconstruiam estado. "
            "ACHADO: o fixture `tree` de test_characterization_matching e scope=module e NUNCA "
            "chamou guardar(), mas o corpo de test_pipeline_caracterizado usa atual() — ele so "
            "funcionava pelo recurso de transicao, e teria lido a arvore de OUTRO arquivo de "
            "teste. Corrigido com guardar(). Tambem removidos quatro imports mortos de "
            "gedcom_state e um import duplicado em test_confrontacao_gedcom_dna. Em seguida o "
            "recurso de transicao de atual() foi REMOVIDO e atual() passou a falhar alto: "
            "nenhum teste quebrou, o que prova que ninguem dependia do global. MEDIDO apos "
            "(b): suite 177 passed / 1 xfailed / 15 errors — uma a menos que a linha de base "
            "porque o teste de transicao test_transicao_ainda_atualiza_o_estado_global foi "
            "removido, como o proprio docstring dele mandava."
        ),
    },
    {
        "ts": "2026-10-07T14:40:00Z",
        "action": "T023(a,c,d)",
        "status": "done",
        "files": [
            "src/parsers/gedcom_parser.py",
            "src/core/gedcom_state.py",
            "tests/test_dependencias_nucleo.py",
            "_reversa_sdd/parity/harness.py",
            "_reversa_sdd/parity/_collect_cand.py",
            "tests/test_arvore_devolvida.py",
        ],
        "nota": (
            "(a) carregar_arvore deixou de mutar as globais e o import de gedcom_state saiu do "
            "parser; get_name/ref_id passaram a vir de core.registro. O coletor do harness lia "
            "GS (T010 absorvido): passou a desempacotar a arvore devolvida. ATENCAO — o coletor "
            "do candidato esta EMBUTIDO COMO STRING em harness.py, e o arquivo "
            "_collect_cand.py e apenas uma copia de referencia: editar so o .py nao tem efeito, "
            "e o harness continua quebrando. (c) src/core/gedcom_state.py REMOVIDO; nenhum "
            "modulo de src o importava mais, so restam 12 mencoes em TEXTO, que sao alvo de "
            "T027/T028. (d) o xfail(strict=True) da guarda de estado saiu e o teste passa por "
            "merito proprio. MEDIDO: suite 178 passed / 0 xfailed / 15 errors e paridade 100 "
            "por cento nas 6 fixtures, exit 0. O xfailed caiu a zero porque o marcador saiu; o "
            "total subiu de 177 para 178 porque o teste de estado agora CONTA como aprovado em "
            "vez de xfail."
        ),
    },
    {
        "ts": "2026-10-07T15:20:00Z",
        "action": "T022",
        "status": "done",
        "files": [
            "src/core/dna_analysis.py",
            "src/core/path_search.py",
            "tests/test_dna_analysis.py",
            "_reversa_sdd/parity/harness.py",
            "_reversa_sdd/parity/_collect_cand.py",
        ],
        "nota": (
            "A superficie de compatibilidade de dna_analysis SAIU. Medi-la antes de mexer "
            "evitou duas suposicoes erradas: (1) eu supus que o modulo usava SHARED_CM_DATA na "
            "evidencia genetica — medido, o corpo NAO referenciava nenhum dos dois nomes, so o "
            "import os trazia; (2) a restricao registrada na OPP-20261006-ESKO (transformation.md "
            "secao 'Efeito colateral registrado') dizia que reduzir dna_analysis exigia verificar "
            "o contrato do harness, que a alcanca por D.get_relationships_by_cm. Como o coletor "
            "ja estava sendo alterado pelo T023, o contrato foi verificado e cumprido: o coletor "
            "passou a importar get_relationships_by_cm de core.cm_estimator, e o teste de "
            "test_dna_analysis idem. Saíram: o import de cm_estimator, e "
            "'get_relationships_by_cm'/'SHARED_CM_DATA' de __all__. cm_estimator PERMANECE em "
            "disco, como a acao manda. Tambem removido o bloco-comentario morto 'Ponto unico de "
            "transicao' de path_search, que descrevia mecanismo extinto. MEDIDO: suite 178 "
            "passed / 15 errors e paridade 100 por cento, exit 0."
        ),
    },
]

with open(PROGRESS, "a", encoding="utf-8", newline="\n") as fh:
    for evento in EVENTOS:
        fh.write(json.dumps(evento, ensure_ascii=False) + "\n")

with open(PROGRESS, encoding="utf-8") as fh:
    linhas = fh.readlines()
print("progress.jsonl: %d linhas (3 anexadas)" % len(linhas))
for linha in linhas[-3:]:
    dado = json.loads(linha)
    print("  %s  %s  %s" % (dado["ts"], dado["action"], dado["status"]))
