---
schema_version: 1
id: BUG-20261021-7O7V
display_number: 13
title: Análise de DNA com 19.403 pessoas e 308 linhas de CSV leva cerca de 6 minutos
status: active
phase: awaiting-human
severity: high
priority: P1
created: 2026-10-21
updated: 2026-10-21

origin:
  type: manual-report
  external_ref: null

area: analisador-genealogico
module: dna-analysis
feature: analise-dna
labels: [desempenho, lentidao, spec-gap]

visibility: normal
security_suspected: false

reproduction:
  classification: deterministic
  rate: null
  suspected_triggers:
    - árvore grande (19.403 pessoas)
    - CSV com muitas linhas (308)

blocking: []

relationships:
  - bug: BUG-20260929-QMLY
    type: related-to
    state: proposed
    evidence:
      - ref: _reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-upload-sem-limites/bug.md
        observation: >-
          O QMLY tratou o tamanho e o conteúdo do arquivo aceito. Este defeito é o custo de
          PROCESSAR a entrada que o QMLY passou a aceitar: nenhuma das duas correções cobre a
          outra, e o sistema continua sem teto de tempo.

traceability:
  specs:
    - _reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais
    - _reversa_sdd/analise-dna/requirements.md#matching-difuso
    - _reversa_sdd/architecture.md#1
    - _reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais
    - _reversa_sdd/domain.md#4
    - _reversa_sdd/addenda/025-desempenho-carga-arvore.md
    - _reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md
  affected_code:
    - src/app.py
    - src/application/dna_analysis.py
    - src/parsers/gedcom_parser.py
    - src/core/matching.py
    - src/core/dna_analysis.py
    - src/core/documentary_relationship.py
    - src/reporting/mermaid_render.py
    - src/ports/adaptadores.py
    - src/templates/index.html
  root_cause:
    state: supported
    hypothesis: >-
      O custo por cartão é dominado por duas ineficiências medidas no mesmo caminho: (1)
      `person_summary` chama `get_children`, que varre TODAS as famílias para cada ficha, e a
      análise de 101 cartões chamou `person_summary` 1.024 vezes; (2) `homonym_dossier` monta as
      mesmas fichas duas vezes, porque `_diferencas` é chamado uma vez para `differences` e outra
      dentro de `identical_data`. O pool de sobrenomes em `avaliar_candidatos` é o terceiro custo.
    causal_path:
      - "`person_summary` (documentary_relationship.py:198) inclui `children: get_children(arvore, person_id)`."
      - "`get_children` (:182) percorre `families.values()` inteiro, com dois `next(...)` por família, para achar as famílias em que a pessoa é HUSB ou WIFE."
      - "O laço por cartão chama `homonym_dossier` e `documental_nao_encontrado`/`documentary_relationship`, e cada um monta fichas de novo."
      - "`homonym_dossier` (:301) monta `fichas` e chama `_diferencas` duas vezes (:320-321); cada `_diferencas` remonta as fichas."
    evidence:
      - ref: evidence/reproduction.md
        observation: "Perfil sintético de 19.405 pessoas e 309 linhas: `get_children` com 66,7 s cumulativos em 1.024 chamadas e `_diferencas` com 24,2 s em 120 chamadas, sob `cProfile`."
      - ref: evidence/reproduction.md
        observation: "Sem perfil: parse 10,41 s e análise 42,68 s, 101 cartões e 208 descartes, determinístico em 2 execuções."
    code_refs:
      - file: src/core/documentary_relationship.py
        symbol: get_children
        commit: 1befc8d
      - file: src/core/documentary_relationship.py
        symbol: person_summary
        commit: 1befc8d
      - file: src/core/documentary_relationship.py
        symbol: homonym_dossier
        commit: 1befc8d
      - file: src/core/documentary_relationship.py
        symbol: _diferencas
        commit: 1befc8d
  reproduction_tests:
    - tests/test_desempenho_das_fichas.py::test_person_summary_nao_varre_as_familias_por_ficha
    - tests/test_desempenho_das_fichas.py::test_dossie_calcula_as_diferencas_uma_vez
  regression_tests:
    - tests/test_desempenho_das_fichas.py::test_get_children_mesma_ordem_e_deduplicacao
    - tests/test_desempenho_das_fichas.py::test_dossie_preserva_os_campos

spec_verdict: spec-gap

change_set:
  - id: CHG-001
    kind: code
    artifact: src/core/documentary_relationship.py
    purpose: >-
      `get_children` passa a consultar um índice pai -> filhos montado uma vez e preso ao
      grafo da árvore, em vez de varrer todas as famílias por ficha.
    diff: fix/change-set.diff
  - id: CHG-002
    kind: code
    artifact: src/core/documentary_relationship.py
    purpose: >-
      `_diferencas_de_fichas` recebe as fichas já montadas; `homonym_dossier` calcula
      `differences` uma vez e deriva `identical_data` da mesma lista.
    diff: fix/change-set.diff
  - id: CHG-003
    kind: code
    artifact: src/core/documentary_relationship.py
    purpose: >-
      `person_summary` calcula nascimento, falecimento e pais uma vez e reusa os valores.
    diff: fix/change-set.diff
  - id: CHG-004
    kind: test
    artifact: tests/test_desempenho_das_fichas.py
    purpose: >-
      Reprodução por contagem (varreduras de família e fichas do dossiê) e regressão de
      paridade de `get_children` e dos campos do dossiê.
    diff: tests/test_desempenho_das_fichas.py
  - id: CHG-005
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md
    purpose: >-
      Adendo aditivo do veredito `spec-gap`: fixa o critério de custo por ficha, autoriza
      índices derivados por requisição e deixa o alvo numérico pendente de medição.
    diff: _reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md

closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# Análise de DNA com 19.403 pessoas e 308 linhas de CSV leva cerca de 6 minutos

## Summary

Em 2026-10-21 o operador relatou que o fluxo do Analisador de DNA leva cerca de **6 minutos**
com uma árvore de **19.403 pessoas** e um CSV de **308 linhas**. Acontece sempre com esses dois
arquivos, no Windows com o `.venv` e também no Docker.

Durante a espera a tela mostra "Analisando... Isso pode levar alguns segundos.", que é o estado
de envio do formulário: a página de resultados ainda não chegou. Isso localiza a maior parte da
espera no **processamento do servidor**, antes de qualquer desenho da tela.

O relato original também fala em "visualização dos resultados". O operador não conseguiu separar
as duas fases, e nenhuma evidência foi recebida sobre o que acontece depois que a página aparece.
O que este registro documenta é o processamento; a visualização fica como verificação pendente
(ver Agent Notes).

## Expected Behavior

A spec efetiva descreve o custo do fluxo, e não fixa um teto:

- `_reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais` declara "Sem cache entre
  requisições: os índices do GEDCOM inteiro são reconstruídos a cada `POST`".
- `_reversa_sdd/architecture.md#1` repete: a cada `POST` o GEDCOM é re-parseado integralmente e
  não há cache entre requisições.
- `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais` diz o mesmo para a carga
  da árvore.

O que o operador espera é que uma execução real (19.403 pessoas, 308 linhas) termine em tempo
útil de trabalho, e não em minutos. **A spec nunca definiu esse tempo**: não há orçamento de
latência, nem teto de linhas, nem tempo máximo por requisição. Por isso o bug carrega o label
`spec-gap`: a pergunta "é defeito ou nunca foi especificado?" está aberta, e a resposta é decisão
humana antes da correção.

## Actual Behavior

- Com árvore de 19.403 pessoas e CSV de 308 linhas, o envio leva cerca de 6 minutos até a página
  aparecer (relato do operador em 2026-10-21).
- Acontece sempre com esses dois arquivos, no `.venv` local e no Docker.
- O indicador "Analisando... Isso pode levar alguns segundos." fica visível durante a espera.
- Não existe medição do time para esse volume. Os números disponíveis são de entradas menores e
  estão em `evidence/medicoes-anteriores.md`.

## Steps to Reproduce

Com os arquivos reais do operador (não anexados a este registro):

1. Subir a aplicação (`.venv` local ou `docker-compose`).
2. Selecionar a árvore de 19.403 pessoas na fase Árvores GEDCOM.
3. Enviar o CSV de 308 linhas na fase Analisador de DNA.
4. Disparar a análise e medir o tempo até a página de resultados aparecer. Observado: cerca de
   6 minutos.

Receita sintética para a triagem, sem dado pessoal (não reproduz a distribuição real de
sobrenomes, então serve para localizar a fase, não para provar o número):

- `_reversa_bugs/_sondas-seguranca/gerar_fixtures.py` tem `arvore_grande(19403)` e
  `matches(307)`. Gerar os dois, subir o app com a pasta de upload desviada e rodar a fase de DNA.

## Evidence

- `evidence/relato-do-operador.md` - as respostas do operador na sessão de registro.
- `../../intake/relato-20261021-1516.md` - o relato bruto, na pasta do contexto.
- `evidence/medicoes-anteriores.md` - números já medidos no projeto, com fonte, e o que falta
  medir.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md`, itens 3 e
  4 - parse por requisição, colapso de concorrência e custo do DNA por linhas x pool.
- `_reversa_sdd/addenda/025-desempenho-carga-arvore.md` - a otimização anterior e o ganho
  declarado de cerca de 1,5 s.

Nenhuma imagem, log ou captura de tela foi recebida até agora.

## Suspected Area

O caminho inteiro do `POST`, sem cache entre requisições:

| Ponto | O que faz | Custo conhecido |
|---|---|---|
| `src/app.py:344` | `_CARREGADOR.carregar` a cada requisição | parse de 35.460 pessoas = 20,9 s; 19.403 deve ser da mesma ordem |
| `src/parsers/gedcom_parser.py` | monta `people`, `families`, `graph` e `child_to_family` | idem |
| `src/core/matching.py:175-197` | para cada linha do CSV, percorre o pool de sobrenomes e roda três razões difusas por candidato | cresce com linhas x pool, sem teto |
| `src/core/dna_analysis.py:524-528` | `_dossie` guarda um dossiê por nome distinto do CSV | `homonym_dossier` medido em 1,73 s por chamada |
| `src/core/dna_analysis.py:547` | laço por kit e pipeline completo por cartão aceito | não medido por cartão |
| `src/core/documentary_relationship.py:301` | dossiê e parentesco documental por cartão | BFS no grafo de 19.403 pessoas por cartão |
| `src/core/dna_analysis.py:780-844` | resumo e Mermaid da árvore sugerida por cartão | não medido |
| `src/reporting/mermaid_render.py` | monta o texto Mermaid de cada cartão | não medido |
| `src/templates/index.html` | página com um cartão por resultado, 174 KB de template | não medido |

**Medido em 2026-10-21, com dado sintético** (19.405 pessoas, 309 linhas, 101 cartões):
`get_children` acumula 66,7 s em 1.024 chamadas de `person_summary`, porque varre todas as
3.881 famílias por ficha; `_diferencas` acumula 24,2 s em 120 chamadas, porque o dossiê o chama
duas vezes; `avaliar_candidatos` acumula 34,6 s com 1,4 milhão de chamadas ao rapidfuzz. O parse
custou 10,4 s e a análise inteira 42,7 s, sem perfil.

O caso do operador tem 6 minutos e este reproduz 53 s, então **a atribuição do tempo real a
essas funções ainda é hipótese**: a árvore sintética é uma floresta de famílias isoladas e quase
não produz caminho, enquanto a real é conectada. O que está confirmado é o custo relativo no
mesmo caminho de código (`evidence/reproduction.md`).

## Acceptance Criteria

1. A execução com a mesma árvore (19.403 pessoas) e o mesmo CSV (308 linhas) termina abaixo de um
   alvo numérico acordado com o operador antes da correção. Proposta para discussão: até 60 s no
   ambiente local.
2. O resultado é idêntico ao de hoje: mesmos cartões, mesmos vereditos, mesma ordem, mesmos
   descartes e mesmos motivos (paridade com o comportamento atual).
3. Nenhuma linha do CSV deixa de ser avaliada sem decisão humana registrada.
4. A diferença entre `.venv` local e Docker é medida e explicada, ou não existe.
5. Fica registrada uma medição antes/depois com o número, e uma proteção de regressão que não
   dependa de tempo absoluto. O precedente é `tests/test_carga_da_arvore.py`, que conta
   materializações em vez de cronometrar.

## Traceability

| Campo | Valor |
|---|---|
| Specs | `_reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais`, `#matching-difuso`, `_reversa_sdd/architecture.md#1`, `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais`, `_reversa_sdd/domain.md#4`, `_reversa_sdd/addenda/025-desempenho-carga-arvore.md` |
| Código afetado | `src/app.py`, `src/application/dna_analysis.py`, `src/parsers/gedcom_parser.py`, `src/core/matching.py`, `src/core/dna_analysis.py`, `src/core/documentary_relationship.py`, `src/reporting/mermaid_render.py`, `src/ports/adaptadores.py`, `src/templates/index.html` |
| Causa raiz | não determinada (o `/reversa-debugger` não corrige) |
| Testes de reprodução | nenhum |
| Testes de regressão | nenhum |
| Veredito de spec | `spec-gap` (CHG-005, adendo `bug-BUG-20261021-7O7V-v001`) |

## Resolution

Correção aplicada em 2026-10-21, com os dois gates aprovados. **O bug NÃO está fechado**: falta a
medição do operador com os arquivos reais, que é o único dado capaz de confirmar o alvo de tempo.

### Causa raiz

Estado `supported`. No perfil sintético, `person_summary` chamava `get_children` uma vez por ficha,
e `get_children` varria todas as famílias; `homonym_dossier` montava as mesmas fichas três vezes
(uma para `exact_matches`, duas para `_diferencas`). Medido: 1.024 chamadas de `person_summary` e
66,7 s em `get_children` para 101 cartões.

### Change set

| CHG | Tipo | Artefato | O que faz |
|---|---|---|---|
| CHG-001 | code | `src/core/documentary_relationship.py` | índice pai -> filhos preso ao grafo da árvore; `get_children` vira consulta |
| CHG-002 | code | `src/core/documentary_relationship.py` | dossiê calcula `differences` uma vez e deriva `identical_data` |
| CHG-003 | code | `src/core/documentary_relationship.py` | `person_summary` calcula nascimento, falecimento e pais uma vez |
| CHG-004 | test | `tests/test_desempenho_das_fichas.py` | reprodução por contagem e regressão de paridade |
| CHG-005 | specification | `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md` | adendo aditivo do veredito `spec-gap` |

Diff completo: `fix/change-set.diff`.

### Testes, vermelho para verde

Antes do change set:

```text
FF.F
FAILED test_person_summary_nao_varre_as_familias_por_ficha (50 varreduras para 50 fichas)
FAILED test_dossie_calcula_as_diferencas_uma_vez (6 fichas para 2 homônimos)
2 failed, 2 passed
```

Depois:

```text
....
4 passed in 6.34s
```

Suíte inteira: **1385 passed, 9 skipped** em 386,90 s.

### Medição antes e depois

Probe `_reversa_bugs/desempenho/probes/medir_fases.py --pessoas 19403 --exatas 100 --pool 208`:

| Fase | Antes | Depois |
|---|---:|---:|
| Parse | 10,41 s | 9,41 s |
| Análise | 42,68 s | **18,71 s** |
| Total | 53,08 s | **28,13 s** |

Análise **2,28x** mais rápida, total 1,89x, com resultado idêntico (101 cartões, 208 descartes).
A árvore sintética tem 19.405 pessoas, próxima das 19.403 do relato.

### Paridade

`tests/rodar_paridade.py` termina com **25 divergências pré-existentes**, nenhuma atribuível a este
change set: as chaves `ancestral[...]` vêm de `find_ancestral_path` (alterado em `b39d148`,
2026-10-14, depois do checkpoint de paridade de 2026-10-13) e as de `dna[...].descartados` são o
texto humanizado do motivo (feature 038). Nenhum dos dois probes consome `get_children` nem
`person_summary`. Detalhe em `evidence/gate2-verde.txt`.

### Veredito de spec

**`spec-gap`**, decidido por Adriano em 2026-10-21. A spec nunca definiu custo nem alvo de tempo.
Adendo aditivo gerado em `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md` (CHG-005): fixa o
critério de custo por ficha, autoriza índices derivados por requisição e deixa o alvo numérico
pendente da medição do operador.

### O que falta para fechar

1. O operador rodar a mesma árvore e o mesmo CSV e informar o tempo até a página aparecer.
2. Confirmar se o tempo caiu de forma proporcional e se a visualização ainda incomoda.
3. Veredito de spec (decisão humana), pendente.


## Agent Notes

- **Dedupe**: procurei "lentidão", "desempenho", "performance" e "demora" nos quatro contextos
  existentes e nos `catalog.jsonl`. O único registro próximo é a inspeção de segurança de
  2026-10-13 (itens 3 e 4), que mediu o problema e não virou bug. `BUG-20260929-QMLY` está
  fechado e entra como `related-to`, não como duplicata.
- **Não ler `src/uploads/`**: o registro e a medição devem usar dados sintéticos, como fez a
  inspeção de segurança. O `.env` e os arquivos do operador não entram em evidência.
- **Medir antes de otimizar**: a feature 025 já removeu trabalho redundante do parse e o ganho
  declarado foi de cerca de 1,5 s, "não perceptível". Repetir micro-otimização sem medir o todo
  não resolve 6 minutos.
- **Cuidado com cache**: um cache de árvore entre requisições reintroduz estado de processo, que
  a ADR-24 removeu. O cache de nomes (`_INDICE_DE_NOMES`) já tem a colisão conhecida
  (`L-24`/`E-05`) e não pode ser ampliado sem endereçar isso.
- **Visualização**: o relato inicial citava "visualização dos resultados". Depois que o servidor
  responder rápido, confirmar com o operador se a página ainda demora a desenhar. Se demorar,
  registrar bug próprio: o botão "Expandir todas as análises" (`src/templates/index.html:1847`)
  abre todos os cartões e dispara `mermaid.run` por cartão (`:1808-1818`), o que pode travar o
  navegador.
- **Taxonomia**: `area: analisador-genealogico`, `module: dna-analysis` e `feature: analise-dna`
  existem em `taxonomy.yaml`. Nenhum termo novo foi proposto.
- **Contexto novo**: `desempenho` foi criado por escolha do operador, porque ele não conseguiu
  separar processamento de visualização. Se a triagem separar, os bugs podem nascer nos contextos
  `analise-dna` e `busca-caminho`.
