---
schema_version: 1
id: BUG-20260929-BJJH
display_number: 1
title: Estado global e pasta de upload compartilhada expõem a árvore de um usuário a outro
status: open
phase: triaging
severity: critical
priority: P0
created: 2026-09-29
updated: 2026-09-29

origin:
  type: manual-report
  external_ref: null

area: analisador-genealogico
module: upload
feature: busca-caminho
labels: [seguranca, isolamento, regulatorio, lgpd]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: null
  suspected_triggers: []

blocking: []

relationships:
  - bug: BUG-20260929-QMLY
    type: related-to
    state: proposed
    evidence:
      - ref: analisador-genealogico/app.py:13-14,29-31,49-50
        observation: As duas falhas compartilham a mesma pasta fixa uploads/ e o mesmo nome de arquivo controlado pelo cliente atuando como chave de sessão.

traceability:
  specs:
    - _reversa_sdd/migration/risk_register.md#risk-005
    - _reversa_sdd/migration/ambiguity_log.md#amb-009
    - _reversa_sdd/migration/target_business_rules.md#br-humana-004
    - _reversa_sdd/migration/parity_specs.md#2-isolamento-por-tenant
    - _reversa_sdd/migration/cutover_plan.md#criterios-de-go-no-go
    - _reversa_sdd/domain.md#4-lacunas-requerem-validação-humana
    - _reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas
    - _reversa_sdd/migration/migration_brief.md#métricas-de-sucesso
  affected_code:
    - analisador-genealogico/reconstructed/upload.py
    - analisador-genealogico/app.py
    - analisador-genealogico/templates/index.html
  root_cause: null
  reproduction_tests: []
  regression_tests: []

spec_verdict: null

change_set: []

closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# Estado global e pasta de upload compartilhada expõem a árvore de um usuário a outro

## Summary

A árvore genealógica carregada não pertence a ninguém. Ela vive em variáveis globais de processo,
mutadas in-place a cada upload (`reconstructed/upload.py:15-19` e `:95-98`), enquanto o arquivo de
origem fica numa pasta única e compartilhada (`uploads/`) endereçável pelo nome que o próprio
cliente escolheu (`app.py:13`, `:31`, `:38-44`). O efeito prático é que uma sessão passa a operar
sobre a árvore carregada por outra, e a lista completa de nomes dessa árvore é embutida no HTML
devolvido (`templates/index.html:102-106`). Em contexto multiusuário, é vazamento de dado
genealógico entre contas.

## Expected Behavior

O comportamento esperado está definido na spec efetiva, não no código atual:

- `_reversa_sdd/migration/risk_register.md#risk-005` exige que a propriedade do dado seja
  invariante do aggregate, com repositório sempre escopado, e define teste negativo obrigatório:
  usuário A acessando recurso de B recebe `404`, não `403`.
- `_reversa_sdd/migration/ambiguity_log.md#amb-009` e
  `_reversa_sdd/migration/target_business_rules.md#br-humana-004` registram a decisão humana de
  eliminar o conceito de "GEDCOM carregado" global, com `owner_id` como identidade do aggregate.
- `_reversa_sdd/migration/parity_specs.md#2-isolamento-por-tenant` trata isolamento por tenant como
  dimensão nova da matriz de paridade.
- `_reversa_sdd/migration/cutover_plan.md#criterios-de-go-no-go` condiciona o go-live a esse teste
  negativo passar.
- `_reversa_sdd/migration/migration_brief.md#métricas-de-sucesso` define "nenhum cruzamento de
  árvores ou matches entre contas" como métrica de sucesso.

O legado nunca especificou o contrário: `_reversa_sdd/domain.md#4-lacunas-requerem-validação-humana`
registra a ausência de autenticação e autorização como lacuna, não como requisito.

## Actual Behavior

1. `reconstructed/upload.py:15-19` declara `people`, `families`, `graph` e `child_to_family` como
   globais de módulo, descritos no próprio código como "singleton por processo".
2. `reconstructed/upload.py:95-98` sobrescreve as quatro estruturas a cada parse, por `clear()` mais
   `update()`.
3. `app.py:13` fixa `UPLOAD_FOLDER = "uploads"`, uma pasta única para todos.
4. `app.py:38-44` reconstrói o caminho do GEDCOM a partir do campo `gedcom_filename` enviado pelo
   formulário, sem verificar qualquer propriedade.
5. `templates/index.html:102-106` embute `all_names`, a lista completa de nomes da árvore carregada,
   no HTML de resposta.
6. Não há autenticação, sessão de usuário nem `owner_id` em nenhum ponto do projeto.

Re-verificado em 2026-09-29, depois do refactor. `upload.py:15-19`, `:95-98`, `app.py:13`, `:38-44` e
`index.html:102-106` conferem com a árvore atual. A única referência defasada era a da aresta
`related-to` com o `QMLY`, que citava `app.py:13-16,31,51`: o `:51` designava a gravação do CSV, hoje
em `:49-50`, e o arquivo encolheu porque a `OPP-20260929-SEQO` removeu o `STATIC_FOLDER`.

O vetor de "artefato HTML de grafo em caminho fixo", levantado no intake como Problema 1, **não existe
mais**: a `SEQO` removeu o `STATIC_FOLDER` e a pasta `static/` não está na árvore. O que resta, e
sustenta este bug, é o estado global em memória mais a pasta `uploads/` compartilhada.

## Steps to Reproduce

1. Suba a aplicação com `py -3.14 analisador-genealogico/app.py`.
2. Na sessão A, carregue um GEDCOM e confirme que a árvore responde a uma busca de caminho.
3. Em outra sessão, carregue um GEDCOM diferente. O parse substitui o estado global do processo.
4. Volte à sessão A e repita a busca: o resultado é calculado sobre a árvore da segunda sessão.
5. Variante sem segunda sessão: enviar no campo `gedcom_filename` o nome de um arquivo já presente
   em `uploads/` faz a aplicação carregar a árvore de outro remetente.

Nenhuma reprodução end-to-end foi executada nesta sessão: a classificação `deterministic` decorre da
leitura do código, onde não há ramo condicional, aleatoriedade nem dependência de ambiente.

## Evidence

- `evidence/verificacao-codigo.md` com os trechos exatos verificados e o locator de cada um.
- Relato bruto e observações do escrivão: `../intake/relato-20260929-0139.md`.
- Specs citadas em `## Traceability`, lidas diretamente dos arquivos.

## Suspected Area

Estado compartilhado no módulo `reconstructed/upload.py`, combinado com o roteamento de `app.py` que
aceita o nome do arquivo como identificador, e com a renderização de `all_names` em
`templates/index.html`.

## Acceptance Criteria

- [ ] Duas sessões com GEDCOM distintos nunca compartilham árvore: cada requisição resolve a árvore
      do seu próprio contexto.
- [ ] Requisição que referencie árvore de outro dono responde `404` (não `403`), conforme
      `_reversa_sdd/migration/risk_register.md#risk-005`.
- [ ] Existe teste negativo de isolamento no repositório, e ele falha antes da correção.
- [ ] A lista de nomes exposta ao cliente contém apenas nomes da árvore do próprio usuário.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/migration/risk_register.md#risk-005`, `_reversa_sdd/migration/ambiguity_log.md#amb-009`, `_reversa_sdd/migration/target_business_rules.md#br-humana-004`, `_reversa_sdd/migration/parity_specs.md#2-isolamento-por-tenant`, `_reversa_sdd/migration/cutover_plan.md#criterios-de-go-no-go`, `_reversa_sdd/domain.md#4-lacunas-requerem-validação-humana`, `_reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas`, `_reversa_sdd/migration/migration_brief.md#métricas-de-sucesso` |
| Código afetado | `analisador-genealogico/reconstructed/upload.py`, `analisador-genealogico/app.py`, `analisador-genealogico/templates/index.html` |
| Causa raiz | a preencher pelo `/reversa-debugger-fix` |
| Testes de reprodução | nenhum ainda |
| Testes de regressão | nenhum ainda |
| Veredito de spec | a decidir por humano (`spec_verdict` nulo) |

## Resolution

Não preenchida. Corrigir é trabalho do `/reversa-debugger-fix`, em dois gates de aprovação.

## Agent Notes

- **Contexto fixado em `busca-caminho` por decisão do usuário.** O sintoma relatado ("um usuário ver
  a árvore de outro") foi enquadrado na área do grafo. O mecanismo, porém, vive em
  `reconstructed/upload.py` e `app.py`, e é por isso que `module: upload`. Se o time preferir tratar
  este defeito sob `upload-gedcom`, a mudança de contexto é decisão humana: a pasta do bug nunca se
  move.
- **`visibility: restricted` por decisão do usuário.** Este bug não entra nas views
  (`generated/index.md` o mostra apenas como ID e "restrito"). Nada de payload ou passo a passo
  explorável foi escrito neste arquivo; o relato bruto com os detalhes de mecanismo fica em
  `../intake/relato-20260929-0139.md`, fora de `generated/`.
- **Correlação proposta.** Aresta `related-to` com `BUG-20260929-QMLY`, gravada aqui porque o
  endereço de arquivo compartilhado é comum aos dois. Estado `proposed`: é hipótese, não fato
  promovido.
- **Relação com a correção.** `risk_register.md#risk-005` já nomeia o plano de contingência: se o
  isolamento não puder ser garantido de forma estrutural, não liberar a onda seguinte. Corrigir este
  bug é pré-requisito de go-live, não melhoria.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.
