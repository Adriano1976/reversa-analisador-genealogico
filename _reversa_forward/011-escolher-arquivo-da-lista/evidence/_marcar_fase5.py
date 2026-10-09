"""Marca as acoes da Fase 5 no actions.md e registra as linhas no progress.jsonl."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
FEATURE = RAIZ / "_reversa_forward" / "011-escolher-arquivo-da-lista"
ACTIONS = FEATURE / "actions.md"
PROGRESS = FEATURE / "progress.jsonl"

FECHAR = ("| T025 |", "| T026 |", "| T027 |", "| T029 |", "| T030 |", "| T031 |", "| T032 |")

LINHAS = [
    ("T025", "done", "Inventario DEPOIS: conjunto de sha256 IDENTICO ao de antes, nos 19 arquivos. RF-08 provado por medicao, nao por argumento."),
    ("T026", "done", "git diff -- src/core src/parsers src/application VAZIO: o nucleo nao foi tocado."),
    ("T027", "done", "Golden SCR-001 intacto: sha256 ec07f71b4084269a e git status do diretorio vazio. D-05 executado."),
    ("T029", "done", "legacy-impact.md escrito: tabela por componente, diff conceitual, regras preservadas e a unica modificada (domain.md secao 4), com as duas divergencias declaradas."),
    ("T030", "done", "regression-watch.md escrito: W001..W008 com origem, regra esperada, tipo de verificacao e sinal de violacao; OBS-01..OBS-05 na secao sem peso de regressao."),
    ("T031", "done", "onboarding.md com a tabela de resultados medidos preenchida, incluindo a ressalva declarada da linha 13."),
    ("T032", "done", "Adendo _reversa_sdd/addenda/011-escolher-arquivo-da-lista.md gravado e vigente. Estagio /reversa-sync."),
    ("T028", "failed",
     "PREMISSA FALSA, e nao execucao falha. A acao diz que a tela de entrada descrita deixa de existir, "
     "mas a varredura do README por tela, interface, fluxo e upload mostra que ele NUNCA descreveu a tela "
     "de entrada: descreve arquitetura, caminho do dado, pasta canonica, configuracao e arvore de arquivos. "
     "Nao ha o que corrigir. Falta ADICIONAR a descricao da tela nova, que e tarefa diferente e maior. "
     "Mantida aberta de proposito."),
]

agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

linhas = ACTIONS.read_text(encoding="utf-8").splitlines(True)
marcadas = []
for i, linha in enumerate(linhas):
    if linha.startswith(FECHAR) and linha.rstrip().endswith("| [ ] |"):
        linhas[i] = linha.replace("| [ ] |", "| [X] |")
        marcadas.append(linha.split("|")[1].strip())
ACTIONS.write_text("".join(linhas), encoding="utf-8")

with PROGRESS.open("a", encoding="utf-8", newline="\n") as fh:
    for acao, status, nota in LINHAS:
        fh.write(json.dumps({"ts": agora, "action": acao, "status": status, "nota": nota},
                            ensure_ascii=False) + "\n")

print("marcadas:", ", ".join(marcadas))
abertas = sum(1 for l in linhas if l.rstrip().endswith("| [ ] |"))
fechadas = sum(1 for l in linhas if l.rstrip().endswith("| [X] |"))
print(f"acoes: {fechadas} fechadas, {abertas} abertas, {fechadas + abertas} no total")
