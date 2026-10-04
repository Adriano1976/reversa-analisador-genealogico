---
schema_version: 1
id: BUG-20260929-BJJH
display_number: 1
title: Estado global e pasta de upload compartilhada expõem a árvore de um usuário a outro
status: active
phase: mitigating
severity: critical
priority: P0
created: 2026-09-29
updated: 2026-10-04

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

blocking:
  - kind: external
    reason: >-
      O tratamento decidido e a Rota 3 do `fix/plano-de-tratamento.md`: resolver na Onda 3 da
      migracao, onde a spec manda, com `api/auth` resolvendo `owner_id`, repositorio com escopo
      obrigatorio na assinatura e o teste negativo de 404 que o cutover exige como portao de go-live.
      Nao ha trabalho de codigo deste bug a executar no legado.
    since: 2026-10-02

mitigation:
  kind: risk-acceptance
  applied_at: 2026-10-04
  temporary: true
  reason: >-
    Registro do estado provisorio que o plano de tratamento ja recomendava: o legado permanece
    single-tenant por contingencia prevista no RISK-005, e nao por descuido. Sem tocar em codigo.
    Condicao que reabre: alguem alem do owner passar a ter acesso antes da Onda 3.

relationships:
  - bug: BUG-20260929-QMLY
    type: related-to
    state: confirmed
    evidence:
      - ref: _reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-upload-sem-limites/fix/gate2-sonda-antes.txt
        observation: >-
          Medido em 2026-10-02. POST de path_search com gedcom_filename arbitrario responde 200 e
          carrega o arquivo correspondente de uploads/ sem verificacao de propriedade. O nome de
          arquivo controlado pelo cliente funcionava como identificador de sessao, que e o mecanismo
          compartilhado com este bug.
      - ref: analisador-genealogico/app.py:31-33,42
        observation: >-
          As duas falhas compartilham a mesma pasta fixa uploads/ e o mesmo nome de arquivo
          controlado pelo cliente. A aresta foi promovida de proposed a confirmed em 2026-10-02,
          quando a medicao do QMLY fechou o caminho causal.

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

> **Atualização de 2026-10-02.** O `app.py` mudou de novo: o `BUG-20260929-QMLY` aplicou o `CHG-002`,
> e as linhas de upload passaram a ser `:31-33` (gravação sob chave gerada) e `:42` (resolução da
> chave recebida), com a validação em `reconstructed/validate.py`. O `CHG-002` **não corrige este
> bug**: o estado global em memória e a ausência de `owner_id` permanecem intactos, e o
> `gedcom_filename` continua servindo de identificador sem verificação de propriedade. A pasta
> `uploads/` segue única, agora com nomes de arquivo derivados do conteúdo.

O vetor de "artefato HTML de grafo em caminho fixo", levantado no intake como Problema 1, **não existe
mais**: a `SEQO` removeu o `STATIC_FOLDER` e a pasta `static/` não está na árvore. O que resta, e
sustenta este bug, é o estado global em memória mais a pasta `uploads/` compartilhada.

> **Atualização de 2026-10-04: mitigado, e não corrigido.** O bug passa a `active`/`mitigating` pela
> decisão do usuário no menu de mitigação do `/reversa-debugger-fix`. O estado provisório é o que o
> `fix/plano-de-tratamento.md` já recomendava (Rota 3, com o registro da Rota 1): o legado permanece
> **single-tenant por contingência prevista no `RISK-005`**, e não por descuido. Nenhuma linha de
> código foi alterada nesta mitigação, e o bug **continua aberto**.

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

> **Estes critérios pertencem à Onda 3, não ao legado.** A verificação de 2026-10-02 estabeleceu
> que o segundo critério é **inaplicável ao legado**: sem autenticação, sem sessão e sem `owner_id`,
> não existem "dono A" e "dono B" para que a resposta difira entre `404` e `403`. Ver
> `fix/plano-de-tratamento.md` § 2. Nenhum deles pode ser marcado por trabalho feito no aplicativo
> atual.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/migration/risk_register.md#risk-005`, `_reversa_sdd/migration/ambiguity_log.md#amb-009`, `_reversa_sdd/migration/target_business_rules.md#br-humana-004`, `_reversa_sdd/migration/parity_specs.md#2-isolamento-por-tenant`, `_reversa_sdd/migration/cutover_plan.md#criterios-de-go-no-go`, `_reversa_sdd/domain.md#4-lacunas-requerem-validação-humana`, `_reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas`, `_reversa_sdd/migration/migration_brief.md#métricas-de-sucesso` |
| Código afetado | `analisador-genealogico/reconstructed/upload.py`, `analisador-genealogico/app.py`, `analisador-genealogico/templates/index.html` |
| Causa raiz | a preencher pelo `/reversa-debugger-fix`, e só na Onda 3 |
| Testes de reprodução | nenhum ainda |
| Testes de regressão | nenhum ainda |
| Veredito de spec | a decidir por humano (`spec_verdict` nulo) |
| Tratamento decidido | Onda 3, conforme `fix/plano-de-tratamento.md`; legado permanece single-tenant. **Mitigado em 2026-10-04** por aceite de risco registrado, sem código alterado |

## Resolution

Não preenchida. Corrigir é trabalho do `/reversa-debugger-fix`, em dois gates de aprovação, e a
decisão vigente é que não há correção a fazer no legado. A mitigação de 2026-10-04 está registrada no
bloco `mitigation` e nas Agent Notes, e **não substitui a Resolution**.

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
- **Correlação CONFIRMADA em 2026-10-02.** A aresta `related-to` com `BUG-20260929-QMLY` foi
  promovida de `proposed` a `confirmed`. A medição daquele bug fechou o caminho causal: um
  `gedcom_filename` arbitrário era aceito no `POST` e carregava o arquivo correspondente de
  `uploads/` sem verificação de propriedade. É exatamente o mecanismo que sustenta este bug, o nome
  de arquivo controlado pelo cliente atuando como identificador de sessão. Ver
  `_reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-upload-sem-limites/evidence/causacao-medida.txt`
  § 8.
- **Relação com a correção.** `risk_register.md#risk-005` já nomeia o plano de contingência: se o
  isolamento não puder ser garantido de forma estrutural, não liberar a onda seguinte. Corrigir este
  bug é pré-requisito de go-live, não melhoria.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.
  **O arquivo `taxonomy.yaml` não existe no repositório**, embora o `README.md` do registro o declare
  como fonte do vocabulário. Registro a inconsistência aqui em vez de deixá-la implícita.
- **Decisão de tratamento (2026-10-02, Adriano).** Perguntado se alguém além dele precisa usar a
  aplicação antes da Onda 3, respondeu: **"Só eu mesmo"**. Com o uso restrito a uma pessoa, a
  aplicação permanece **single-tenant**, que é exatamente a contingência que o
  `_reversa_sdd/migration/risk_register.md#risk-005` já autoriza ("manter a aplicação single-tenant
  até o isolamento ser provado"). O tratamento é a **Rota 3** do `fix/plano-de-tratamento.md`:
  resolver na Onda 3, onde a spec manda, com `api/auth`, `owner_id` como invariante e repositório
  escopado. **Consequência: não há trabalho de código deste bug a executar no legado.** A Rota 2
  (escopo por sessão em memória) foi descartada por decisão humana, e não por impedimento técnico.
- **Por que o legado não é corrigido.** Não é adiamento por dificuldade. A correção no legado seria
  código descartado pela Onda 3 e, ainda assim, **não fecharia o segundo critério de aceite**, por
  não existir identidade. Detalhamento e comparação das três rotas no plano citado.
- **Mitigação aplicada em 2026-10-04, por decisão do usuário, e ela NÃO é correção.** No menu de
  mitigação que o `/reversa-debugger-fix` exige antes de investigar, o usuário escolheu registrar o
  estado provisório que o plano de tratamento já recomendava. O bug passou a `active`/`mitigating`,
  ganhou o bloco `mitigation` com `kind: risk-acceptance` e `temporary: true`, e ganhou uma condição
  `blocking` de tipo `external` nomeando a dependência da Onda 3. **Nenhuma linha de código ou de
  spec foi tocada**, o `spec_verdict` segue nulo e o `change_set` segue vazio. O bug continua aberto.
- **Fato novo que fortalece o pré-requisito da mitigação.** O plano de tratamento exigia que a
  aplicação não fosse exposta a mais de uma pessoa. Em 2026-10-02 isso dependia de disciplina, porque
  a aplicação nascia escutando em `0.0.0.0` e atendia a rede inteira por omissão. A feature
  `004-servidor-waitress`, entregue em **2026-10-04**, mudou o padrão para `127.0.0.1`, fez da
  exposição um ato explícito de quem opera e passou a recusar uma segunda instância na mesma porta.
  Medido na mitigação: a instância no ar escutava em `127.0.0.1:5000`. O pré-requisito deixou de ser
  promessa de disciplina e ganhou garantia técnica no padrão.
- **Condição que reabre esta mitigação.** Se qualquer pessoa além de Adriano passar a ter acesso à
  aplicação antes da Onda 3, o pré-requisito cai, esta decisão perde validade e a Rota 2 volta à
  mesa. O portão de go-live continua sendo o teste negativo de `404` do `cutover_plan.md`.
- **Divergências de rastreabilidade declaradas, não corrigidas.** `evidence/verificacao-codigo.md`
  descreve um `STATIC_FOLDER` que a `OPP-20260929-SEQO` removeu, e o
  `risk_register.md#risk-005` localiza o estado global em `app.py:20-23`, quando ele vive em
  `reconstructed/upload.py:15-19` e `:95-98`. Ambos são anteriores ao refactor. Não corrigidos
  porque alterar spec é ato humano; registrados para não se trabalhar sobre premissa morta.

---
*Gerado pelo Reversa-Debugger em 2026-09-29. Mitigado pelo Reversa-Debugger-Fix em 2026-10-04.*
