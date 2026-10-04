---
schema_version: 1
id: BUG-20261004-EWSJ
display_number: 5
title: Badge de cM exibe o valor com ruído de ponto flutuante
status: resolved
phase: patching
severity: low
priority: P3
created: 2026-10-04
updated: 2026-10-04

origin:
  type: manual-report
  external_ref: null

area: analisador-genealogico
module: dna-analysis
feature: analise-dna
labels: [apresentacao, ponto-flutuante, spec-gap]

visibility: normal
security_suspected: false

reproduction:
  classification: deterministic
  rate: "3/3"
  suspected_triggers:
    - total de cM sem representacao binaria exata, como 19,2

blocking: []

relationships:
  - bug: BUG-20261002-T4ZM
    type: related-to
    state: proposed
    evidence:
      - ref: _reversa_bugs/busca-caminho/bugs/BUG-20261002-T4ZM-rotulo-descarta-caracteres-inertes/bug.md
        observation: >-
          Aproximacao conceitual, nao causal. As Agent Notes daquele bug registram a intencao de
          contrato "nao deixar texto do usuario degradar a apresentacao". Aqui o dado do usuario
          degrada a apresentacao por outra via, o residuo da soma em ponto flutuante. A investigacao
          de 2026-10-04 nao produziu evidencia causal entre os dois, entao a aresta permanece
          proposed.

traceability:
  specs:
    - _reversa_sdd/analise-dna/requirements.md#agregação
    - _reversa_sdd/analise-dna/requirements.md#saída
    - _reversa_sdd/analise-dna/requirements.md#matching
    - _reversa_sdd/analise-dna/requirements.md#critérios-de-aceitação
    - _reversa_sdd/analise-dna/design.md#interface
    - _reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md
  affected_code:
    - src/templates/index.html
    - src/core/dna_analysis.py
  root_cause:
    state: confirmed
    hypothesis: >-
      O total de cM e somado em ponto flutuante e entregue ao template como float, sem nenhuma etapa
      de formatacao entre o nucleo e o HTML. O Jinja interpola o float cru, e o `str` do Python
      devolve a menor representacao decimal capaz de reconstruir o mesmo valor binario, que no caso
      de 19,2 e 19.200000000000003. Nao ha erro de calculo: o defeito nasce da ausencia de formatacao
      na fronteira de apresentacao.
    causal_path:
      - tres segmentos de 6,4 cM do mesmo match sao agregados por soma, em csv_ingest
      - a soma em ponto flutuante de 6,4 + 6,4 + 6,4 vale 19.200000000000003, e nao 19,2
      - core/dna_analysis.py:95 publica o valor cru em result['cm'], sem arredondar, o que preserva o contrato de paridade exata
      - src/templates/index.html:121 interpolava {{ result.cm }} sem filtro de formatacao
      - o operador le o residuo da soma como se fosse o valor
    evidence:
      - ref: evidence/reproduction.txt
        observation: >-
          O HTML real renderizado pelo template trazia
          <span class="badge bg-success">19.200000000000003 cM</span>, e a soma bruta 6,4 + 6,4 + 6,4
          vale 19.200000000000003. 3 de 3 execucoes reproduzem.
      - ref: evidence/probe_reproducao.py
        observation: >-
          Sonda determinista que carrega o GEDCOM dos fixtures, roda o fluxo real e renderiza o
          template real em contexto de requisicao do Flask, sem abrir porta.
    code_refs:
      - file: src/templates/index.html
        symbol: 'span class="badge bg-success"'
        commit: aba650d
      - file: src/core/dna_analysis.py
        symbol: '"cm": cm_value'
        commit: aba650d
  reproduction_tests:
    - tests/test_formatacao_cm.py::test_badge_nao_exibe_ruido_de_ponto_flutuante
    - tests/test_formatacao_cm.py::test_badge_nunca_carrega_cauda_de_ponto_flutuante
  regression_tests:
    - tests/test_formatacao_cm.py::test_cm_com_duas_casas_preserva_as_duas
    - tests/test_formatacao_cm.py::test_cm_inteiro_nao_ganha_casa_decimal
    - tests/test_formatacao_cm.py::test_formatador_aceita_bordas_numericas
    - tests/test_formatacao_cm.py::test_valor_armazenado_permanece_exato

spec_verdict: spec-gap

change_set:
  - id: CHG-001
    kind: code
    artifact: src/utils/number_format.py
    purpose: Modulo novo com `formatar_cm`, a autoridade unica do formato do total de cM exibido
    diff: fix/CHG-001.diff
  - id: CHG-002
    kind: code
    artifact: src/app.py
    purpose: Registra o filtro Jinja `cm_br` apontando para `formatar_cm`
    diff: fix/CHG-002.diff
  - id: CHG-003
    kind: code
    artifact: src/templates/index.html
    purpose: A linha 121 passa a usar `{{ result.cm | cm_br }}`, e o valor cru deixa de ir ao HTML
    diff: fix/CHG-003.diff
  - id: CHG-004
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md
    purpose: Adendo aditivo que especifica pela primeira vez o formato exibido do total de cM
    diff: null

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Badge de cM exibe o valor com ruído de ponto flutuante

## Summary

O cartão de resultado da análise de DNA exibia o total de cM do match como `19.200000000000003 cM`,
em vez de `19,2 cM`. O valor é a soma dos segmentos do mesmo match em ponto flutuante de dupla
precisão, e a cauda de dígitos era resíduo da soma, não informação sobre o parentesco.

O que chegava à tela era o `str` do `float` do Python, idêntico ao `repr` desde a versão 3.1, que
devolve a forma mais curta capaz de reconstruir o mesmo valor binário. Comportamento correto da
linguagem, e errado para quem lê.

**O defeito era de apresentação, não de cálculo.** `19.200000000000003` é o `float` mais próximo de
19,2 depois da soma, e a ordenação dos resultados sempre esteve correta. O dano era de confiança: o
operador via um número que parecia errado num relatório de parentesco, e passava a duvidar dos outros.

## Expected Behavior

A spec efetiva não definia o formato do valor exibido, e passou a definir com o adendo
`_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md`:

- o total de cM é exibido com **até duas casas decimais**, **vírgula** decimal, **sem zeros à
  direita** e **sem separador de milhar**;
- o valor **armazenado** em `result["cm"]` continua o `float` exato, porque a paridade contra o
  oráculo congelado exige igualdade exata (`_reversa_sdd/migration/parity_specs.md:113`);
- a regra mora em um lugar só, `src/utils/number_format.py`, exposta ao template como o filtro
  `cm_br`.

O que a spec já definia, e este bug nunca contestou: o cM do match é a soma dos segmentos do grupo
(`_reversa_sdd/analise-dna/requirements.md#agregação`); os resultados são ordenados por cM decrescente
(`#saída`); o cM não decide aceitação por si só (`#matching`).

## Actual Behavior

1. `src/core/dna_analysis.py:95` montava cada resultado com `"cm": cm_value`, o valor somado dos
   segmentos, sem arredondamento.
2. `src/core/dna_analysis.py:106` ordena a lista por esse mesmo valor.
3. `src/templates/index.html:121` interpolava o valor cru no HTML:
   `<span class="badge bg-success">{{ result.cm }} cM</span>`.
4. Não existia filtro de formatação, helper de apresentação nem arredondamento em nenhum ponto entre a
   soma e o HTML. O único `round` do núcleo é o do score de matching, em `src/core/matching.py:101`.
5. Efeito observado: o badge mostrava `19.200000000000003 cM`.

## Steps to Reproduce

1. Suba a aplicação e carregue um GEDCOM.
2. Envie um CSV de matches com `root_name` válido e ao menos um match cujo total de cM não tenha
   representação binária exata, como 19,2.
3. A tela exibe o cartão "Conexão com: <nome>", com o total no badge verde do cabeçalho.
4. Observado: `19.200000000000003 cM`.

**Reproduzido em 2026-10-04**, no commit `aba650d`, com **3 de 3** execuções. A reprodução usa a sonda
`evidence/probe_reproducao.py`, que roda o fluxo real e o template real sem abrir porta, e a cápsula
completa está em `evidence/reproduction.md`. O caso mínimo medido é a soma de três segmentos de
6,4 cM do mesmo match.

## Evidence

- `evidence/reproduction.md`: cápsula de reprodução, com commit, ambiente, comando, taxa e a distinção
  entre o que a medição prova e o que não prova.
- `evidence/reproduction.txt`: saída literal das 3 execuções da sonda.
- `evidence/probe_reproducao.py`: a sonda, determinista e isolada.
- `evidence/badge-cm-com-artefato-de-ponto-flutuante.png`: print do relator, com o badge circulado em
  vermelho.
- `fix/gate1-testes-falham.txt`: o vermelho, com as duas falhas de reprodução nomeadas.
- `fix/gate2-testes-passam.txt`, `fix/gate2-suite.txt` e `fix/gate2-paridade.txt`: o verde medido.
- `fix/CHG-001.diff`, `fix/CHG-002.diff` e `fix/CHG-003.diff`: a correção aplicada.
- Relato bruto e observações do escrivão: `../../intake/relato-20261004-1325.md`.

## Suspected Area

`src/templates/index.html:121` é onde o defeito **aparecia**. A causa raiz confirmada foi a ausência de
uma etapa de formatação na fronteira entre o núcleo e o template, e não um erro de cálculo em
`src/core/dna_analysis.py`, cujo valor sempre esteve correto.

## Acceptance Criteria

- [x] O badge exibe `19,2 cM` para o caso do print, com vírgula decimal, até 2 casas e sem zeros à
      direita. **Satisfeito** por `test_badge_nao_exibe_ruido_de_ponto_flutuante`.
- [x] Um total com duas casas reais, como `19,25`, continua exibindo as duas casas. **Satisfeito** por
      `test_cm_com_duas_casas_preserva_as_duas`.
- [x] O valor **armazenado** em `result["cm"]` permanece o `float` exato, sem arredondamento.
      **Satisfeito** por `test_valor_armazenado_permanece_exato`, que roda o fluxo real.
- [x] Existe teste que falha antes da correção e cobre a formatação, e a suíte mantém o resultado da
      linha de base. **Satisfeito e medido**: 5 falhas antes, 6 aprovações depois, e a suíte em 131
      aprovados e 15 erros de ambiente, contra 125 e os mesmos 15 na base.
- [x] A paridade diferencial permanece em 100 por cento nas 6 fixtures. **Satisfeito e medido**:
      `PARIDADE 100% (zero divergencia)`.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/analise-dna/requirements.md#agregação`, `#saída`, `#matching`, `#critérios-de-aceitação`, `_reversa_sdd/analise-dna/design.md#interface`, `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md` |
| Código afetado | `src/templates/index.html` (onde aparecia), `src/core/dna_analysis.py` (onde o valor nasce) |
| Causa raiz | `confirmed`: ausência de formatação entre a soma e o HTML, em `src/templates/index.html:121` |
| Testes de reprodução | `tests/test_formatacao_cm.py::test_badge_nao_exibe_ruido_de_ponto_flutuante`, `tests/test_formatacao_cm.py::test_badge_nunca_carrega_cauda_de_ponto_flutuante` |
| Testes de regressão | `tests/test_formatacao_cm.py::test_cm_com_duas_casas_preserva_as_duas`, `::test_cm_inteiro_nao_ganha_casa_decimal`, `::test_formatador_aceita_bordas_numericas`, `::test_valor_armazenado_permanece_exato` |
| Veredito de spec | `spec-gap`, com adendo aditivo `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md` |
| Formato decidido | `19,2 cM`, vírgula decimal, até 2 casas, sem zeros à direita (relator, 2026-10-04) |

## Resolution

**Causa raiz.** `confirmed`. Não havia etapa de formatação entre a soma do cM e o HTML. O valor
armazenado sempre foi o `float` exato da soma, e o template o interpolava cru, fazendo o `str` do
Python exibir a menor representação decimal que reconstrói o mesmo valor binário. A causação foi
medida, e não deduzida: a sonda reproduziu o HTML exato com o valor do relato em 3 de 3 execuções.

**Veredito de spec.** `spec-gap`, aprovado pelo usuário na etapa 7. O formato do número exibido nunca
foi especificado, e a única decisão de arredondamento da extração é de outro valor, o score de
matching. O adendo `v001` especifica o formato pela primeira vez, sem alterar nenhuma seção existente.

**`resolution_kind`.** `fixed`.

### Change set

| CHG | Tipo | Artefato | Propósito | Diff |
|-----|------|----------|-----------|------|
| `CHG-001` | code | `src/utils/number_format.py` | Módulo novo com `formatar_cm` | `fix/CHG-001.diff` |
| `CHG-002` | code | `src/app.py` | Registra o filtro Jinja `cm_br` | `fix/CHG-002.diff` |
| `CHG-003` | code | `src/templates/index.html` | Linha 121 passa a usar o filtro | `fix/CHG-003.diff` |
| `CHG-004` | specification | `_reversa_sdd/addenda/bug-BUG-20261004-EWSJ-v001.md` | Especifica o formato exibido | arquivo novo, sem diff |

O diff de código e o adendo de spec ficam registrados **juntos**, como exige o protocolo do registro.

### Testes

Vermelho para verde, medido na mesma sessão:

| Estado | `tests/test_formatacao_cm.py` | Suíte completa | Paridade |
|--------|-------------------------------|----------------|----------|
| Antes do change set | 5 falhas, 1 passa | 125 aprovados, 15 erros | 100 por cento |
| Depois do change set | **6 passam** | **131 aprovados, 15 erros** | **100 por cento** |

- Evidência do vermelho: `fix/gate1-testes-falham.txt`
- Evidência do verde: `fix/gate2-testes-passam.txt`, `fix/gate2-suite.txt`, `fix/gate2-paridade.txt`

Os 15 erros são os mesmos da linha de base, todos em `test_upload_seguranca.py`, por permissão de
diretório temporário no sandbox, e não regressão.

### Aprovações

Plano de correção e os dois gates aprovados pelo usuário em 2026-10-04, na mesma sessão. Severidade
`low` e prioridade `P3` confirmadas pelo relator no registro.

### Ressalva declarada

**A exibição em navegador não foi conferida.** A prova é sobre o HTML emitido pelo template real, e
não sobre a renderização visual. Para um defeito cuja causa é o texto dentro do HTML, e não a
interpretação dele pelo navegador, considerei suficiente, e registro a diferença em vez de marcar como
cumprido. O mesmo tipo de ressalva está no `BUG-20261002-T4ZM`.

A instância que estava no ar durante a correção é anterior a ela. O operador precisa reiniciar a
aplicação para ver o formato novo na tela.

### Reversão

Por `git apply --reverse` dos três diffs de código, e remoção do adendo `v001`.

## Agent Notes

- **Restrição que decidiu o lugar do fix, e que continua valendo.** Arredondar no núcleo mudaria o
  valor contratual de `result["cm"]`, e a spec de migração exige comparação **exata** contra o oráculo
  congelado: `_reversa_sdd/migration/parity_specs.md:113` diz "Sem `pytest.approx`, sem tolerância,
  sem arredondamento". O fix formatou na apresentação, e não tocou no contrato.
- **O valor armazenado é contrato, e a correção não encostou nele.** O critério de aceite que exige o
  `float` exato não era formalidade: a ordenação por cM decrescente (`#saída`) e a paridade dependem
  dele. Formatar é transformar na saída, nunca no estado.
- **Renome de teste declarado.** O rascunho aprovado no Gate 1 trazia `test_formatador_e_total`. O
  helper não é total para entrada não numérica, por decisão, então o nome passou a
  `test_formatador_aceita_bordas_numericas`, que é o que ele prova. As asserções não mudaram, e a
  cobertura não mudou.
- **A suíte não pegava este defeito, e isso não é falha dela.** Nenhum teste renderiza a tela. Os
  testes de caracterização existentes congelam a saída do Mermaid e a decisão de matching. Quem pegou
  foi o olho do operador. O que o fix deixa atrás é a cobertura que faltava: o template real agora é
  exercitado por teste.
- **Separador decimal é decisão de produto, e foi tomada pelo relator.** `19,2` com vírgula foi
  escolha explícita. O ponto decimal evitaria ambiguidade ao copiar o valor para uma planilha, e foi
  descartado.
- **Relação `related-to` com `BUG-20261002-T4ZM` permanece `proposed`.** A investigação não produziu
  evidência causal entre os dois defeitos, e aresta sem evidência não é promovida.
- **Taxonomia.** `area`, `module` e `feature` reaproveitam o vocabulário dos bugs vizinhos.
  **`_reversa_bugs/taxonomy.yaml` não existe no repositório**, embora o `README.md` do registro o
  declare como fonte do vocabulário e três bugs o citem nas Agent Notes. Registro a inconsistência: o
  arquivo precisa ser criado, e `module: dna-analysis` é a proposta de entrada nova.
- **`area` está defasado em todos os bugs.** `analisador-genealogico` era o nome da pasta de código
  antes da feature 003, e hoje a raiz é `src/`. Não corrigi, por ser valor de vocabulário
  compartilhado, e a correção é decisão humana.

---
*Gerado pelo Reversa-Debugger em 2026-10-04. Encerrado pelo Reversa-Debugger-Fix em 2026-10-04.*
