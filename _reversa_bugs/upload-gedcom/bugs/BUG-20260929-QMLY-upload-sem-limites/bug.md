---
schema_version: 1
id: BUG-20260929-QMLY
display_number: 2
title: Upload sem limite de tamanho, sem validação de extensão ou conteúdo e sem sanitização de nome
status: open
phase: triaging
severity: high
priority: P1
created: 2026-09-29
updated: 2026-09-29

origin:
  type: manual-report
  external_ref: null

area: analisador-genealogico
module: upload
feature: upload-gedcom
labels: [seguranca, upload, lgpd, spec-reaberta]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: null
  suspected_triggers: []

blocking: []

relationships: []

traceability:
  specs:
    - _reversa_sdd/migration/risk_register.md#risk-007
    - _reversa_sdd/migration/target_business_rules.md#br-humana-001
    - _reversa_sdd/migration/discard_log.md#br-descartar-003
    - _reversa_sdd/migration/discard_log.md#br-descartar-006
    - _reversa_sdd/migration/ambiguity_log.md#amb-006
    - _reversa_sdd/questions.md#pergunta-3
    - _reversa_sdd/analise-dna/requirements.md#rastreabilidade-de-código
    - _reversa_sdd/upload-gedcom/design.md#riscos-e-lacunas
    - _reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais
    - _reversa_sdd/confidence-report.md#lacunas-pendentes-
  affected_code:
    - analisador-genealogico/app.py
    - analisador-genealogico/reconstructed/upload.py
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

# Upload sem limite de tamanho, sem validação de extensão ou conteúdo e sem sanitização de nome

## Summary

O endpoint de upload aceita qualquer arquivo, de qualquer tamanho, com qualquer nome, e usa esse
nome controlado pelo cliente como caminho de escrita e como chave de recuperação nas requisições
seguintes. Não há `MAX_CONTENT_LENGTH`, não há lista de extensões permitidas, não há verificação de
que o conteúdo é GEDCOM antes do parse e não há `secure_filename`. O nome enviado também é usado em
`os.path.join`, o que abre caminho para escrita fora da pasta de upload. Este é o item BR-DESCARTAR-006
do log de descartes: uma limitação aceita no contexto de uso local single-user e reaberta quando o
alvo passou a ser multiusuário público com dado genético sensível.

## Expected Behavior

O esperado está registrado na spec efetiva, e o usuário confirmou nesta sessão que o projeto deve ser
tratado como multiusuário desde já:

- `_reversa_sdd/migration/risk_register.md#risk-007` define gatilho ("upload aceito sem verificação
  de tipo declarado vs conteúdo; ausência de limite de tamanho; nomes de arquivo do cliente usados em
  caminho") e mitigação: chave de armazenamento gerada pelo servidor (UUID), nome original apenas como
  metadado, limite de tamanho explícito, validação de extensão e de conteúdo antes do parse,
  isolamento por `owner_id`.
- `_reversa_sdd/migration/target_business_rules.md#br-humana-001` registra a decisão humana de
  descartar a limitação aceita.
- `_reversa_sdd/migration/discard_log.md#br-descartar-003` e `#br-descartar-006` registram o descarte
  do armazenamento por nome do cliente e da ausência de política de upload.
- `_reversa_sdd/migration/ambiguity_log.md#amb-006` registra a reabertura da decisão.
- `_reversa_sdd/migration/risk_register.md#risk-007` também define o plano de contingência: se a
  validação estrita rejeitar GEDCOM válido de algum exportador, relaxar apenas a validação de
  extensão e manter limite de tamanho e chave gerada.

O comportamento oposto está documentado como decisão antiga e superada:
`_reversa_sdd/questions.md#pergunta-3` ("Limitação aceita para uso local. Manter sem política de
segurança") e `_reversa_sdd/reconstruction-plan.md#alertas-de-pré-voo`. Essa resposta pressupunha uso
local, contexto que o `_reversa_sdd/migration/migration_brief.md` alterou explicitamente.

## Actual Behavior

1. `analisador-genealogico/app.py:10-16` cria o app e as pastas, e nunca define
   `MAX_CONTENT_LENGTH`. Não há limite de tamanho de requisição em nenhum ponto do projeto.
2. `app.py:31-32` grava o GEDCOM em `os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`, com o nome
   enviado pelo cliente, sem sanitização nem validação de extensão.
3. `app.py:51-52` faz o mesmo com o CSV de DNA.
4. Não há verificação de tipo de conteúdo: `load_gedcom_and_build_graph`
   (`reconstructed/upload.py:82-100`) apenas abre o arquivo com `GedcomReader`.
5. Dois arquivos de mesmo nome se sobrescrevem sem aviso.
6. O nome do arquivo funciona como identificador de sessão: é devolvido ao cliente como
   `gedcom_filename` e volta no próximo `POST` (`app.py:34`, `:38-44`).

## Steps to Reproduce

1. Suba a aplicação com `py -3.14 analisador-genealogico/app.py`.
2. Envie um arquivo de tamanho arbitrário no campo do GEDCOM e observe que a requisição é aceita e
   gravada em `uploads/`.
3. Envie um arquivo com extensão diferente de `.ged` e observe que o parse é tentado do mesmo modo.
4. Envie dois arquivos com o mesmo nome em sequência e observe que o segundo sobrescreve o primeiro.
5. Envie um nome de arquivo contendo separadores de caminho e observe o destino da escrita.

Nenhuma reprodução end-to-end foi executada nesta sessão: a classificação `deterministic` decorre da
leitura do código, onde nenhum desses passos encontra verificação.

## Evidence

- `evidence/verificacao-codigo.md` com os trechos exatos verificados e o locator de cada um.
- Relato bruto e observações do escrivão: `../intake/relato-20260929-0139.md`.
- Decisão humana anterior e sua reabertura: `_reversa_sdd/questions.md#pergunta-3` e
  `_reversa_sdd/migration/discard_log.md#br-descartar-006`.

## Suspected Area

Rota de upload em `analisador-genealogico/app.py` e a fronteira de parsing em
`analisador-genealogico/reconstructed/upload.py`. O projeto não tem camada de validação de entrada.

## Acceptance Criteria

- [ ] Existe limite explícito de tamanho de requisição, e requisição acima do limite é rejeitada com
      mensagem própria.
- [ ] Extensão e conteúdo são validados antes do parse, conforme
      `_reversa_sdd/migration/risk_register.md#risk-007`.
- [ ] A chave de armazenamento é gerada pelo servidor; o nome original é apenas metadado.
- [ ] Dois envios com o mesmo nome não se sobrescrevem, e o comportamento é coberto por teste.
- [ ] Nome controlado pelo cliente não participa da composição de caminho no sistema de arquivos.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/migration/risk_register.md#risk-007`, `_reversa_sdd/migration/target_business_rules.md#br-humana-001`, `_reversa_sdd/migration/discard_log.md#br-descartar-003`, `_reversa_sdd/migration/discard_log.md#br-descartar-006`, `_reversa_sdd/migration/ambiguity_log.md#amb-006`, `_reversa_sdd/questions.md#pergunta-3`, `_reversa_sdd/analise-dna/requirements.md#rastreabilidade-de-código`, `_reversa_sdd/upload-gedcom/design.md#riscos-e-lacunas`, `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais`, `_reversa_sdd/confidence-report.md#lacunas-pendentes-` |
| Código afetado | `analisador-genealogico/app.py`, `analisador-genealogico/reconstructed/upload.py` |
| Causa raiz | a preencher pelo `/reversa-debugger-fix` |
| Testes de reprodução | nenhum ainda |
| Testes de regressão | nenhum ainda |
| Veredito de spec | a decidir por humano (`spec_verdict` nulo) |

## Resolution

Não preenchida. Corrigir é trabalho do `/reversa-debugger-fix`, em dois gates de aprovação.

## Agent Notes

- **Conflito de spec declarado, não resolvido aqui.** Existem duas respostas humanas em sentidos
  opostos para o mesmo comportamento: `_reversa_sdd/questions.md#pergunta-3` aceita a limitação para
  uso local, e `_reversa_sdd/migration/target_business_rules.md#br-humana-001` a descarta para o alvo
  multiusuário. O usuário confirmou nesta sessão o enquadramento multiusuário, o que alinha o bug com
  a segunda resposta. O `spec_verdict` continua nulo: é decisão humana registrada, e o caminho
  provável é um adendo em `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-vNNN.md`, nunca a edição da
  spec original.
- **Atenção à paridade.** `reconstructed/upload.py:1-7` declara explicitamente que preserva a
  limitação por fidelidade ao legado. Validação estrita pode rejeitar GEDCOM válido e quebrar
  paridade de parsing, que é o risco número um declarado do projeto. O plano de contingência já está
  escrito em `risk_register.md#risk-007`: relaxar apenas a extensão.
- **`visibility: restricted` por decisão do usuário.** Este bug não entra nas views; `generated/index.md`
  o mostra apenas como ID e "restrito".
- **Relação proposta.** Aresta `related-to` gravada em `BUG-20260929-BJJH`, apontando para este bug,
  porque ambos dependem da mesma pasta compartilhada e do mesmo nome de arquivo como chave.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.
