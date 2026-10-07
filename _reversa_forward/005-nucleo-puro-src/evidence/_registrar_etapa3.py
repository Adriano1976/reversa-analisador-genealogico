"""Anexa ao progress.jsonl os estagios finais (T024 a T029) da feature 005."""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
PROGRESS = os.path.join(RAIZ, "_reversa_forward", "005-nucleo-puro-src", "progress.jsonl")

EVENTOS = [
    {
        "ts": "2026-10-07T16:00:00Z",
        "action": "T024",
        "status": "done",
        "files": ["tests/test_dependencias_nucleo.py"],
        "nota": (
            "Caminho negativo das guardas, executado com SONDA REAL em src/core/ e nao com "
            "string sintetica. A diferenca importa: a string prova que o predicado funciona, "
            "mas nao prova que a guarda o aplica aos arquivos certos. Criado "
            "src/core/_sonda_t024.py com tres violacoes ao mesmo tempo (import flask, open(), "
            "people={} e versao=0 em nivel de modulo). As TRES guardas reprovaram apontando o "
            "achado exato: '_sonda_t024.py:16 people' e '_sonda_t024.py:17 versao'. Sonda "
            "removida; guardas de volta ao verde, 10 passed. Evidencia em "
            "evidence/T024-caminho-negativo.md. T025 ja estava ABSORVIDO pelo T023 (o modulo "
            "de estado foi apagado la, e registro.py ja era o destino dos consumidores) — nao "
            "havia trabalho remanescente. T026 medido e registrado: suite 178 passed, 0 xfailed, "
            "15 errors; paridade 100 por cento; linha de base era 164 passed, 15 errors; a conta "
            "fecha (14 testes novos menos 1 de transicao removido = +13, e o xfail que virou "
            "aprovado = +1). Evidencia em evidence/T026-medicao-final.md."
        ),
    },
    {
        "ts": "2026-10-07T16:40:00Z",
        "action": "T027",
        "status": "done",
        "files": ["README.md", "src/app.py"],
        "nota": (
            "Quatro passagens, e nao tres. As tres do README (linhas 63, 147 e 251) afirmavam "
            "que o estado do GEDCOM vive em globais compartilhadas entre threads; agora dizem "
            "que a arvore existe por requisicao e e passada por parametro. A QUARTA foi achada "
            "por varredura e nao estava no plano: o comentario da guarda de exclusividade em "
            "app.py justificava a RN-05 pelo estado global ('duas instancias divergem em "
            "memoria'). O estado saiu, mas a guarda FICA — o motivo que resta e o "
            "armazenamento em disco compartilhado (src/uploads/), que duas instancias gravam e "
            "leem. Reescrever o motivo em vez de apagar a guarda."
        ),
    },
    {
        "ts": "2026-10-07T17:10:00Z",
        "action": "T028",
        "status": "done",
        "files": [
            "src/core/family_navigation.py",
            "src/core/path_finding.py",
            "src/core/diagram_domain.py",
            "src/core/documentary_relationship.py",
            "src/utils/text_cleaning.py",
            "src/core/registro.py",
        ],
        "nota": (
            "Docstrings que documentavam o mecanismo extinto. Alem dos tres arquivos do escopo "
            "nominal, dois achados por varredura: (1) text_cleaning.py dizia 'dicionarios "
            "globais de gedcom_state.py' em dois lugares; (2) registro.py citava "
            "gedcom_state.py sem dizer que foi apagado. O ACHADO GRAVE foi em "
            "documentary_relationship.py: um bloco de comentario afirmava que 'quando T023 "
            "remover o estado, a identidade volta a ser chave valida' — ou seja, RECOMENDAVA "
            "voltar a usar id() como chave do cache. Isso seria um BUG: id() e reciclado, o "
            "dicionario da arvore anterior deixa de ser referenciado quando o parse devolve o "
            "novo, o CPython pode reusar o endereco, e o cache devolveria o mapa de um GEDCOM "
            "diferente — falha que so apareceria sob carga. O bloco foi substituido por uma "
            "explicacao de por que NAO voltar a usar id(). A docstring de _chave_de tambem "
            "dizia 'o parse muta people in place', que deixou de ser verdade."
        ),
    },
    {
        "ts": "2026-10-07T17:50:00Z",
        "action": "T029",
        "status": "done",
        "files": [
            "_reversa_forward/005-nucleo-puro-src/evidence/_verificar_t029.py",
            "_reversa_forward/005-nucleo-puro-src/evidence/T029-verificacao-manual.md",
        ],
        "nota": (
            "Verificacao manual de ponta a ponta, automatizada por HTTP contra o servidor de "
            "PRODUCAO (waitress) numa porta livre. Feito com script, e nao a mao, porque a "
            "verificacao precisa ser REPETIVEL e o roteiro do onboarding.md tem 9 passos. "
            "APROVADO: raiz HTTP 200 com cabecalho Server: waitress e formulario presente; "
            "upload de basic.ged devolveu gedcom_filename e 7 nomes no campo de sugestao; "
            "analise de DNA com cm_boundaries.csv OK; fronteira de cM confirmada (0 e -5 "
            "devolvem lista VAZIA, e 99999 devolve o literal, AMB-023); busca de caminho nos "
            "dois modos, com a marcacao de afinidade presente so no caso indireto; passos 7 e 8 "
            "sem nenhum achado. Duas armadilhas do proprio instrumento, registradas: o console "
            "padrao do Windows e cp1252 e as fixtures tem nomes com caracteres que nao cabem "
            "nele (o script morria ao IMPRIMIR um nome valido — mesmo genero de aviso do "
            "ORACLE_MANIFEST), e multipart() precisa de arquivos opcionais para a busca de "
            "caminho. ATENCAO: a verificacao grava em src/uploads/ e o _clean_residue.py NAO "
            "remove isso — conferir git status antes de commitar (Principio I). Evidencia em "
            "evidence/T029-verificacao-manual.md."
        ),
    },
]

with open(PROGRESS, "a", encoding="utf-8", newline="\n") as fh:
    for evento in EVENTOS:
        fh.write(json.dumps(evento, ensure_ascii=False) + "\n")

with open(PROGRESS, encoding="utf-8") as fh:
    linhas = fh.readlines()
print("progress.jsonl: %d linhas (4 anexadas)" % len(linhas))
for linha in linhas[-4:]:
    dado = json.loads(linha)
    print("  %s  %s  %s" % (dado["ts"], dado["action"], dado["status"]))
