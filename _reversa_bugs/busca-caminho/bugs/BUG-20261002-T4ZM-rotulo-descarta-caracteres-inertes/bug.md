---
schema_version: 1
id: BUG-20261002-T4ZM
display_number: 4
title: Rotulo Mermaid descarta 14 caracteres inertes que o legado preservava
status: resolved
phase: patching
severity: low
priority: P3
created: 2026-10-02
updated: 2026-10-02

origin:
  type: inspection
  external_ref: null

area: analisador-genealogico
module: path-search
feature: busca-caminho
labels: [escape, mermaid, regressao-de-correcao, spec-gap]

visibility: normal
security_suspected: false

reproduction:
  classification: deterministic
  rate: "15/15 caracteres divergentes, 1 execucao por caractere em cada lado"
  suspected_triggers:
    - nome de pessoa contendo # $ % * + = @ \ ^ _ ` { | } ~

blocking: []

relationships:
  - bug: BUG-20260929-J6PQ
    type: caused-by
    state: confirmed
    evidence:
      - ref: evidence/causacao-medida.txt
        observation: a versao anterior ao CHG-001 daquele bug era identica ao oraculo nos 95 caracteres, com 0 divergencias, e a versao atual diverge em 15
      - ref: evidence/varredura-divergencias.txt
        observation: o CHG-001 trocou a lista negra por `_LABEL_SEGURO`, e a amplitude escolhida descarta 14 caracteres alem da crase

traceability:
  specs:
    - _reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md
    - _reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md
    - _reversa_sdd/busca-caminho/design.md#interface
  affected_code:
    - analisador-genealogico/reconstructed/mermaid_render.py
  root_cause:
    state: confirmed
    hypothesis: >-
      A lista branca `_LABEL_SEGURO` foi enumerada pelo criterio de "comprovadamente seguro", que e
      mais estreito que "comprovadamente inerte". Tudo que ficou fora da enumeracao passou a ser
      descartado, incluindo 14 caracteres que o legado preservava e que a gramatica do Mermaid
      tolera.
    causal_path:
      - o BUG-20260929-J6PQ exigia que a crase deixasse de sair do rotulo
      - a correcao daquele bug trocou a lista negra por lista branca, conforme o plano aprovado
      - a lista foi enumerada pelo criterio de "comprovadamente seguro", nao pelo de "comprovadamente inerte"
      - 14 caracteres ASCII imprimiveis ficaram fora da enumeracao
      - _mermaid_label descarta todo caractere fora da lista, em mermaid_render.py:54
      - o nome aparece no diagrama sem esses caracteres, de forma silenciosa
    evidence:
      - ref: evidence/causacao-medida.txt
        observation: versao anterior ao CHG-001 identica ao oraculo nos 95 caracteres; versao atual diverge em 15
      - ref: evidence/varredura-divergencias.txt
        observation: 15 dos 95 caracteres divergem, e apenas a crase era o descarte pretendido
    code_refs:
      - file: analisador-genealogico/reconstructed/mermaid_render.py
        symbol: _LABEL_SEGURO
        commit: c709ea0
  reproduction_tests:
    - tests/test_mermaid_escape.py::test_caractere_inerte_sobrevive_ao_rotulo
    - tests/test_mermaid_escape.py::test_lista_branca_preserva_todo_ascii_imprimivel_menos_a_crase
  regression_tests:
    - tests/test_mermaid_escape.py::test_rotulo_neutraliza_crase
    - tests/test_mermaid_escape.py::test_diagrama_nao_carrega_caractere_que_quebra_a_gramatica
    - tests/test_mermaid_escape.py::test_entidades_html_preservadas
    - tests/test_mermaid_escape.py::test_neutralizacoes_que_ja_existiam
    - tests/test_characterization_mermaid.py::test_saida_mermaid_caracterizada
    - tests/test_characterization_mermaid.py::test_rotulo_com_caracteres_de_escape

spec_verdict: spec-gap

change_set:
  - id: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/mermaid_render.py
    purpose: Acrescenta os 14 caracteres inertes a lista branca _LABEL_SEGURO e documenta o criterio de amplitude
    diff: fix/CHG-001.diff
  - id: CHG-002
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md
    purpose: Enumera a lista branca e declara que o criterio e inerte, nao seguro
    diff: null

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Rotulo Mermaid descarta 14 caracteres inertes que o legado preservava

## Summary

O rótulo de nó Mermaid passou a descartar 14 caracteres ASCII imprimíveis que o legado preservava:
`#`, `$`, `%`, `*`, `+`, `=`, `@`, `\`, `^`, `_`, `{`, `|`, `}` e `~`. Um nome como `Ana_Silva`
aparece no diagrama como `AnaSilva`.

A causa é o efeito colateral da correção do `BUG-20260929-J6PQ`. Aquele bug trocou a neutralização
por lista negra por uma lista branca, e a lista escolhida foi conservadora demais: excluiu tudo que
não era comprovadamente seguro, em vez de excluir apenas o que a gramática do Mermaid prova ser
perigoso. O único descarte pretendido era a **crase**, e ele continua correto.

O defeito foi encontrado por medição comparando o oráculo congelado com o candidato, durante uma
auditoria de estimativas. Não veio de relato de usuário, e a suíte de testes não o detecta.

## Expected Behavior

O comportamento esperado está na spec efetiva:

- `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md` especifica o contrato de escape: o rótulo é
  emitido entre aspas duplas, a aspa dupla vira apóstrofo, a crase é descartada, `&`, `<` e `>`
  viram entidades HTML, e **o escape é por lista branca**, com caracteres fora dela descartados.
- `_reversa_sdd/busca-caminho/design.md#interface` especifica `generate_mermaid_graph` e
  `generate_mermaid_graph_indirect_bridge` como as funções que produzem o diagrama, e o texto do
  rótulo vem de `get_name(...)`, do GEDCOM do usuário.

**A amplitude da lista branca nunca foi especificada.** O adendo do `J6PQ` fixa o mecanismo mas não
enumera o conjunto de caracteres que devem sobreviver, e é exatamente aí que este defeito nasce. Por
isso o bug carrega o label `spec-gap`: a decisão de quais caracteres preservar fica em aberto para o
fix, e provavelmente exige um adendo que enumere o conjunto.

O critério que a medição sustenta: dos 15 caracteres que divergem, **um** é pretendido, a crase, e
os outros **14** são inertes dentro das aspas, conforme a gramática do `flowchart` do Mermaid, que
consome tudo com `<string>[^"]+` no estado `string`. O legado os preservava.

## Actual Behavior

1. `analisador-genealogico/reconstructed/mermaid_render.py:42` define
   `_LABEL_SEGURO = re.compile(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ .,'()&<>:;/\[\]!?-]")`.
2. `_mermaid_label` (`:45-55`) aplica essa lista branca em `:54`, descartando todo caractere fora
   dela, e só depois converte `&`, `<` e `>` em entidade (`:55`).
3. Nenhum dos 14 caracteres descartados é perigoso para a gramática. A lista inclui `_`, que é comum
   em identificador; `@`, que é o delimitador de xref de GEDCOM; e `#`, `$`, `%`, `*`, `+`, `=`, `\`,
   `^`, `{`, `|`, `}`, `~`, todos inertes dentro de um rótulo entre aspas.
4. O efeito é visual: o nome sai sem o caractere. A estrutura do diagrama não muda e a conexão
   exibida continua correta.

## Steps to Reproduce

1. Execute a sonda, que compara oráculo e candidato caractere a caractere:

   ```
   py -3.14 evidence/probe_escape_sweep.py --oracle
   py -3.14 evidence/probe_escape_sweep.py --cand
   ```

2. Compare as duas saídas. Das 95 linhas, 15 divergem.
3. Alternativamente, monte um GEDCOM cujo nome contenha `_` e observe o rótulo no diagrama: o
   caractere não aparece.

## Evidence

- `evidence/causacao-medida.txt`: a tabela de três colunas que fecha a causação, com 0 divergências
  antes do `CHG-001` do `J6PQ` e 15 depois.
- `evidence/varredura-divergencias.txt`: oráculo contra o candidato atual, 15 de 95 caracteres.
- `evidence/varredura-oraculo.txt`: saída crua do oráculo congelado, 95 linhas.
- `evidence/varredura-candidato.txt`: saída crua do candidato, 95 linhas.
- `evidence/varredura-antes-da-correcao.txt`: saída crua da versão anterior ao `CHG-001`.
- `evidence/reproduction.md`: cápsula de reprodução, com o ambiente e o que a medição prova e não
  prova.
- `evidence/probe_escape_sweep.py`: a sonda que compara oráculo e candidato, rodando cada lado em
  processo separado porque o oráculo mantém estado global mutável.
- `evidence/probe_varredura_antes.py`: a sonda que mede a versão pré-correção, com o corpo extraído
  verbatim de `c709ea0^`.
- Relato de origem e observações do escrivão: `../../intake/relato-20261002-1613.md`.

## Suspected Area

`_mermaid_label` e a lista branca `_LABEL_SEGURO` em
`analisador-genealogico/reconstructed/mermaid_render.py`. O módulo nasceu na divisão feita pela
`OPP-20260929-UXEF` e trouxe a lista intacta de `path_search.py`.

## Acceptance Criteria

- [x] Um nome contendo `_`, `@`, `#`, `*` ou `+` aparece no diagrama com o caractere preservado.
      **Satisfeito** pelos 14 casos de `test_caractere_inerte_sobrevive_ao_rotulo`.
- [x] A crase continua descartada, e a aspa dupla continua virando apóstrofo. **Satisfeito** pelos
      testes herdados do `BUG-20260929-J6PQ`, que seguem verdes.
- [x] `&`, `<` e `>` continuam saindo como entidade HTML. **Satisfeito** por
      `test_entidades_html_preservadas`.
- [x] A varredura contra o oráculo passa a divergir em **exatamente um** caractere, a crase.
      **Satisfeito e medido**: 15 divergências antes, **1** depois.
- [x] Existe teste que falha antes da correção, cobrindo ao menos `_` e um dos símbolos.
      **Satisfeito**: 15 falhas antes, 0 depois.
- [ ] O diagrama continua renderizando no navegador para nome que contenha os caracteres
      preservados. **NÃO VERIFICADO.** Não houve conferência em navegador nesta correção. A prova
      que tenho é a da gramática, que mostra o lexer consumindo esses caracteres como texto no
      estado `string`, e a paridade com o legado, que os preservava. É prova forte e não é a mesma
      coisa que execução do parser. O `BUG-20260929-J6PQ` ensinou que essa diferença importa.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md`, `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md`, `_reversa_sdd/busca-caminho/design.md#interface` |
| Código afetado | `analisador-genealogico/reconstructed/mermaid_render.py` |
| Causa raiz | a preencher pelo `/reversa-debugger-fix` |
| Testes de reprodução | `tests/test_mermaid_escape.py::test_caractere_inerte_sobrevive_ao_rotulo`, `tests/test_mermaid_escape.py::test_lista_branca_preserva_todo_ascii_imprimivel_menos_a_crase` |
| Testes de regressão | os casos do `BUG-20260929-J6PQ` em `tests/test_mermaid_escape.py`, mais `tests/test_characterization_mermaid.py::test_saida_mermaid_caracterizada` |
| Veredito de spec | `spec-gap`, com adendo aditivo `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md` |

## Resolution

**Causa raiz.** `confirmed`. A lista branca `_LABEL_SEGURO` foi enumerada pelo critério de
"comprovadamente seguro", que é mais estreito que o de "comprovadamente inerte". Os 14 caracteres
imprimíveis que ficaram fora passaram a ser descartados do nome exibido. A causação foi medida, não
deduzida: a versão anterior ao `CHG-001` do `J6PQ` é idêntica ao oráculo nos 95 caracteres, com 0
divergências, e a versão atual divergia em 15.

**Veredito de spec.** `spec-gap`, aprovado pelo usuário na etapa 7. O adendo v001 especifica o
mecanismo do escape com precisão e é silencioso quanto à amplitude: não enumera o conjunto que deve
sobreviver. Foi essa liberdade que permitiu escolher uma lista estreita sem que nada apontasse o
erro. O adendo v002 enumera o conjunto e declara que o critério é **inerte**, corrigindo a leitura
que a palavra "seguros" do v001 convidava.

**`resolution_kind`.** `fixed`.

### Change set

| CHG | Tipo | Artefato | Propósito | Diff |
|-----|------|----------|-----------|------|
| `CHG-001` | code | `analisador-genealogico/reconstructed/mermaid_render.py` | Acrescenta os 14 caracteres inertes à lista branca e documenta o critério de amplitude | `fix/CHG-001.diff` |
| `CHG-002` | specification | `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v002.md` | Enumera a lista e declara o critério inerte | arquivo novo, sem diff |

O diff de código e o adendo de spec ficam registrados **juntos**, como exige o protocolo do registro.

### Testes

Vermelho para verde, medido no mesmo commit:

| Estado | `tests/test_mermaid_escape.py` | Suíte completa | Varredura contra o oráculo |
|--------|-------------------------------|----------------|----------------------------|
| Antes do `CHG-001` | 15 falhas, 19 passam | 15 failed, 86 passed | 15 divergências |
| Depois do `CHG-001` | **34 passam** | **101 passed** | **1 divergência**, a crase |

- Evidência do vermelho: `fix/gate1-testes-falham.txt`
- Evidência do verde: `fix/gate2-testes-passam.txt`
- O diff aplicado é idêntico por hash ao aprovado no Gate 2.

### Aprovações

Plano, Gate 1 e Gate 2 aprovados pelo usuário em 2026-10-02, na mesma sessão. Severidade `low` e
prioridade `P3` confirmadas pelo usuário.

### Ressalva declarada

A última critério de aceite, o de renderização em navegador, **não foi verificado**. A prova
disponível é a da gramática do Mermaid e a paridade com o legado. Para um defeito `low` cujos
caracteres a gramática consome como texto, considerei suficiente e registro a diferença em vez de
marcar como cumprido.

### Incidente desta sessão

Durante a correção, o estado de trabalho não commitado da `OPP-20260929-H2YY` foi destruído por um
`git checkout --` meu e recuperado em seguida pelo `CHG-001.diff` daquela transformação. Registro em
`_reversa_refactor/busca-caminho/transformations/OPP-20260929-H2YY-encurtar-a-ponte/incidente-20261002-estado-de-trabalho.md`.

### Reversão

Por `git apply --reverse` de `fix/CHG-001.diff` sobre `mermaid_render.py`, e remoção do adendo v002.
**Não usar `git checkout` neste arquivo** enquanto o `H2YY` não estiver commitado: a lição está no
registro do incidente acima.

## Agent Notes

- **A relação é `caused-by`, não `regression-of`.** O defeito do `J6PQ` não voltou: o escape
  incompleto continua corrigido. O que houve foi um defeito **novo**, introduzido pelo `CHG-001`
  daquele bug. A pasta do `J6PQ` tem `DONE.md` e é somente leitura, e nada aqui a reabre.
- **A suíte não pegava, e isso não é falha da suíte.** Os testes do `J6PQ` cobrem o comportamento do
  rótulo para os payloads que motivaram aquele bug. Nenhum deles exercita `_`, `@`, `#` ou os demais,
  porque ninguém sabia que estavam em risco. Quem revelou foi o oráculo congelado. Este é um caso
  concreto onde a paridade acha o que o teste de unidade não acha.
- **Severidade e prioridade aguardam confirmação humana.** Registrei `low` e `P3` por proposta:
  caractere raro em nome de pessoa, efeito cosmético, sem perda de dado e sem alteração de estrutura
  do diagrama. O escrivão não decide isso sozinho.
- **Há decisão de produto embutida.** A pergunta não é só "quais caracteres a gramática permite", é
  "quais o produto quer exibir". O critério medido dá o limite superior: tudo que o legado preservava
  e a gramática tolera. Se o produto quiser ser mais restritivo que isso, é decisão declarada, e o
  adendo precisa dizer.
- **Consequência para a migração.** Este defeito não bloqueia a Onda 1, porque a string Mermaid é
  superfície declarada fora da paridade pela exceção `DEV-004` de `parity_specs.md`. Mas a intenção
  do contrato, isto é, não deixar texto do usuário degradar a apresentação, viaja para o
  `KinshipPath` do alvo.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.
  Proposta de melhoria: a entrada `module: path-search` descreve `reconstructed/path_search.py`, mas o
  render e o escape agora vivem em `reconstructed/mermaid_render.py`. O valor continua adequado em
  significado, e o comentário do arquivo é que ficou defasado depois da divisão.
