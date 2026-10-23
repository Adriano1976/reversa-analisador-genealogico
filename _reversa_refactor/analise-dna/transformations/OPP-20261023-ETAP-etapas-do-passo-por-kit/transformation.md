---
schema_version: 1
id: OPP-20261023-ETAP
verb: restructure
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - safety-net/equivalencia-no-projeto.txt
    - safety-net/suite-antes.txt
    - safety-net/suite-depois.txt
    - ../OPP-20261023-ORQA-fluxo-de-553-linhas-sem-fronteira/safety-net/equivalencia.py
measurement:
  before: >
    `_cartao_do_kit` com 368 linhas e 8 condicionais; catorze etapas encadeadas
    sem fronteira interna; módulo com 1.181 linhas
  after: >
    `_cartao_do_kit` com 224 linhas e 5 condicionais, mais seis etapas nomeadas de
    17 a 66 linhas; módulo com 1.258 linhas
change_set:
  - chg: CHG-001
    file: src/core/dna_analysis.py
    purpose: >
      extrai seis etapas de `_cartao_do_kit`: `_recusa_do_kit`, `_parentesco_do_kit`,
      `_endogamia_estrutural`, `_confronto_do_kit`, `_profundidade_do_caminho` e
      `_rotulo_do_confronto`
approval:
  by: user
  at: 2026-10-23T15:10:10-03:00
  plan_at: 2026-10-23T14:59:41-03:00
reversible_via: [CHG-001-seis-etapas-do-passo-por-kit.diff]
---

## O que foi extraído

Seis etapas do corpo de `_cartao_do_kit`, cada uma com nome, assinatura e um único
motivo de existir.

| # | Função | Parâmetros | Devolve | Linhas |
|---|---|---|---|---|
| E1 | `_recusa_do_kit` | contexto, kit, reason, proximos, evidencia_mitigada | descarte | 37 |
| E2 | `_parentesco_do_kit` | contexto, kit, candidate_pids | pid, documentary, homonimos | 23 |
| E3 | `_endogamia_estrutural` | contexto, pid, documentary, evidencia_mitigada | arvore, selo, tem_caminho, observações | 66 |
| E4 | `_confronto_do_kit` | por_kit, chave_kit, avisos, documentary | evidence, hypotheses, comparison, nomes | 17 |
| E5 | `_profundidade_do_caminho` | documentary, evidence | 5 valores | 42 |
| E6 | `_rotulo_do_confronto` | comparison, janela | efetiva, rótulo | 24 |

Os blocos foram movidos **verbatim**: mesmo código, mesmos comentários, mesma
indentação. O único ajuste de recuo foi no E1, que morava dentro de um `if` a 8
espaços. Os nomes locais viraram parâmetros de mesmo nome, então nenhuma expressão
foi reescrita e nenhuma ordem de efeito mudou.

## Efeito medido

| Medida | Antes | Depois |
|---|---|---|
| `_cartao_do_kit` | 368 linhas, 8 condicionais | **224 linhas, 5 condicionais** |
| etapas nomeadas | 0 | 6 |
| módulo | 1.181 | 1.258 |

O módulo cresceu 77 linhas, e isso é esperado: seis funções com docstring custam
mais linhas que o bloco que saiu de uma só. O ganho é estrutural, não de contagem.

## Correção de estimativa

A oportunidade prometia `_cartao_do_kit` com cerca de 150 linhas. O número real é
**224**, e o piso é o dicionário de 40 chaves: 96 linhas de dado, não de lógica.
Tirá-lo do corpo exigiria uma função de 25 parâmetros, que seria pior que o
problema. O dicionário só sai quando o cartão ganhar um construtor único, e isso é
a `OPP-20261023-CTAO`.

## Prova

| Verificação | Resultado |
|---|---|
| digest de equivalência, 3 cenários | `b8d186c8…b570b5dd`, idêntico ao de antes |
| `git apply --check` antes de aplicar | exit 0 |
| arquivo aplicado x `depois.py` revisado | sha256 idêntico |
| suíte antes | **1625 passed, 9 skipped** em 108,78 s |
| suíte depois | **1625 passed, 9 skipped** em 95,87 s |

## O que sobra no corpo

Depois das seis extrações, `_cartao_do_kit` ainda tem as etapas que dependem de
muitos valores ao mesmo tempo: identidade, janela de vida e a regra do operador
(oito resultados), e a validação com a árvore sugerida (nove parâmetros). Elas
ficaram de propósito: extrair com essa assinatura trocaria um corpo longo por um
invólucro de parâmetros, sem ganho de leitura.

## Reversão

`git apply -R CHG-001-seis-etapas-do-passo-por-kit.diff`.

---
*Aplicado em 2026-10-23 pelo Reversa-Refactor, sob gate de plano e de diff aprovados pelo usuário.*
