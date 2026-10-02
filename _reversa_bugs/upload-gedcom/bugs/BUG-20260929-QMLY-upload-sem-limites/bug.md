---
schema_version: 1
id: BUG-20260929-QMLY
display_number: 2
title: Upload sem limite de tamanho, sem validação de extensão ou conteúdo e sem sanitização de nome
status: resolved
phase: delivering
severity: high
priority: P1
created: 2026-09-29
updated: 2026-10-02

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

relationships:
  - bug: BUG-20260929-BJJH
    type: related-to
    state: confirmed
    evidence:
      - ref: .pytest-tmp/probe-qmly-saida.txt#E
        observation: Medido em 2026-10-02. POST de path_search com gedcom_filename
          arbitrario responde 200 e carrega o arquivo correspondente de uploads/ sem
          verificacao de propriedade. O nome de arquivo controlado pelo cliente funciona
          como identificador de sessao, que e o mecanismo compartilhado com o BJJH.

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
  root_cause:
    state: confirmed
    hypothesis: >-
      O caminho de upload sempre tratou o nome de arquivo escolhido pelo cliente como chave de
      armazenamento. Ele e concatenado a UPLOAD_FOLDER com os.path.join e gravado antes de qualquer
      verificacao, e devolvido ao cliente como gedcom_filename para ser reenviado como identificador
      nas requisicoes seguintes. Nenhuma das quatro defesas existe no projeto, e nenhuma existia no
      legado, de modo que a reconstrucao preservou a limitacao por fidelidade, como seu docstring
      declara.
    causal_path:
      - "o legado escrevia com os.path.join(UPLOAD_FOLDER, gedcom_file.filename) em app_legacy_e43ca22.py:569-570, sem sanitizacao"
      - "a reconstrucao reproduziu a mesma construcao em app.py:31-32 e :49-50, tambem para o CSV de DNA"
      - "nenhum MAX_CONTENT_LENGTH foi definido, medido como app.config['MAX_CONTENT_LENGTH'] is None"
      - "nenhuma validacao de extensao ou de conteudo precede o save; o save vem antes do parse"
      - "o nome do cliente entra em os.path.join, e '../ESCAPIU.ged' grava fora de uploads/, provado por gravacao real"
      - "o mesmo nome atravessa a requisicao como campo oculto gedcom_filename e volta como chave de recuperacao"
      - "dois envios com o mesmo nome se sobrescrevem sem aviso, e o primeiro e perdido em silencio"
    evidence:
      - ref: evidence/reproduction.md
        observation: capsula de reproducao medida, deterministica, sonda com exit code 0
      - ref: evidence/verificacao-medida.md
        observation: seis grupos de medicao, incluindo escape provado por gravacao real e perda silenciosa na colisao
      - ref: evidence/causacao-medida.txt
        observation: as linhas do oraculo congelado lado a lado com as atuais, e 0 ocorrencias de MAX_CONTENT_LENGTH e secure_filename no oraculo
    code_refs:
      - file: analisador-genealogico/app.py
        symbol: index
        commit: 95d87fc
      - file: analisador-genealogico/reconstructed/upload.py
        symbol: load_gedcom_and_build_graph
        commit: 95d87fc
  reproduction_tests:
    - tests/test_upload_seguranca.py::TestReproducao::test_existe_teto_de_tamanho_de_requisicao
    - tests/test_upload_seguranca.py::TestReproducao::test_requisicao_acima_do_teto_e_rejeitada
    - tests/test_upload_seguranca.py::TestReproducao::test_nome_com_aspas_e_barra_nao_escapa_da_pasta
    - tests/test_upload_seguranca.py::TestReproducao::test_nome_com_barra_invertida_nao_escapa_da_pasta
    - tests/test_upload_seguranca.py::TestReproducao::test_chave_de_armazenamento_e_gerada_pelo_servidor
    - tests/test_upload_seguranca.py::TestReproducao::test_conteudo_invalido_e_recusado_antes_do_parse
    - tests/test_upload_seguranca.py::TestReproducao::test_conteudo_invalido_nao_fica_em_disco
    - tests/test_upload_seguranca.py::TestReproducao::test_arquivo_vazio_e_recusado_e_nao_fica_em_disco
    - tests/test_upload_seguranca.py::TestReproducao::test_dois_envios_de_mesmo_nome_nao_se_perdem
    - tests/test_upload_seguranca.py::TestModuloDeValidacao
  regression_tests:
    - tests/test_upload_seguranca.py::TestRegressao::test_gedcom_valido_continua_aceito_e_parseado
    - tests/test_upload_seguranca.py::TestRegressao::test_gedcom_valido_sem_extensao_ged_continua_aceito
    - tests/test_upload_seguranca.py::TestRegressao::test_arvore_continua_encontravel_na_requisicao_seguinte
    - tests/test_upload_seguranca.py::TestRegressao::test_uploads_vazio_antes_do_upload
    - tests/test_upload_seguranca.py::TestRegressao::test_fixtures_de_paridade_continuam_validas
    - tests/test_upload.py
    - tests/test_path_search.py
    - tests/test_dna_analysis.py
    - tests/test_characterization_matching.py
    - tests/test_characterization_mermaid.py
    - tests/test_mermaid_escape.py
    - tests/test_domain.py

spec_verdict: spec-desatualizada

approval:
  spec_verdict:
    decided_by: Adriano
    decided_at: 2026-10-02
    document: _reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md

change_set:
  - id: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/validate.py
    diff: fix/CHG-001.diff
    purpose: >-
      Modulo puro de validacao do upload. Nome visivel seguro, chave de
      armazenamento derivada do conteudo (sha256 truncado) e validacao de
      conteudo GEDCOM pela declaracao 0 HEAD. Nao importa Flask e nao toca o
      disco, para ser testavel isoladamente.
  - id: CHG-002
    kind: code
    artifact: analisador-genealogico/app.py
    diff: fix/CHG-002.diff
    purpose: >-
      Teto de MAX_CONTENT_LENGTH com resposta 413 e mensagem propria; gravacao
      sob chave gerada pelo servidor em vez do nome do cliente; validacao antes
      da gravacao, de modo que arquivo recusado nao fica em disco; resolucao da
      chave recebida validada por formato. Cobre tambem o CSV de DNA, que tinha
      a mesma fragilidade.
  - id: CHG-003
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md
    diff: null
    purpose: >-
      Adendo versionado do veredito spec-desatualizada. Registra a divergencia
      deliberada do legado, define a validacao por conteudo em vez de extensao,
      e declara o delta de leitura de cada secao alvo. A spec original nao e
      editada.

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
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

1. `analisador-genealogico/app.py:10-14` cria o app e as pastas, e nunca define
   `MAX_CONTENT_LENGTH`. Não há limite de tamanho de requisição em nenhum ponto do projeto.
2. `app.py:29-30` grava o GEDCOM em `os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`, com o nome
   enviado pelo cliente, sem sanitização nem validação de extensão.
3. `app.py:49-50` faz o mesmo com o CSV de DNA.
4. Não há verificação de tipo de conteúdo: `load_gedcom_and_build_graph`
   (`reconstructed/upload.py:82-100`) apenas abre o arquivo com `GedcomReader`.
5. Dois arquivos de mesmo nome se sobrescrevem sem aviso.
6. O nome do arquivo funciona como identificador de sessão: é devolvido ao cliente como
   `gedcom_filename` e volta no próximo `POST` (`app.py:36`, `:39-42`).

Re-verificado em 2026-09-29: nenhuma referência deste item mudou de sentido, apenas de linha, porque
a `OPP-20260929-SEQO` removeu o `STATIC_FOLDER` de `app.py` e encurtou o arquivo. A varredura
confirma que não existe `MAX_CONTENT_LENGTH` nem `secure_filename` em nenhum arquivo do projeto, e
que `load_gedcom_and_build_graph` continua em `reconstructed/upload.py:82-100`.

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

- `evidence/reproduction.md` com a cápsula de reprodução medida em 2026-10-02 (commit, ambiente,
  comando, exit code, determinismo).
- `evidence/verificacao-medida.md` com os seis grupos de medição executada, substituindo a leitura
  de código do registro original.
- `evidence/causacao-medida.txt` com a causa raiz medida, linha a linha, contra o oráculo congelado.
- `evidence/verificacao-codigo.md`, a verificação por leitura de 2026-09-29, mantida como registro
  histórico.
- Relato bruto e observações do escrivão: `../intake/relato-20260929-0139.md`.
- Decisão humana anterior e sua reabertura: `_reversa_sdd/questions.md#pergunta-3` e
  `_reversa_sdd/migration/discard_log.md#br-descartar-006`.

## Reprodução medida em 2026-10-02

O registro original classificava a reprodução como `deterministic` por leitura de código e declarava
que nenhuma reprodução end-to-end havia sido executada. Ela foi executada agora, e a classificação
se confirmou por medição.

Cinco efeitos foram medidos, e dois deles o registro não tinha:

| Efeito | Medida |
|---|---|
| Sem teto de tamanho | `app.config["MAX_CONTENT_LENGTH"] is None` |
| **Escrita fora de `uploads/`** | nome `../ESCAPIU.ged` grava em `qmly-run/ESCAPIU.ged`; `uploads/` fica vazia |
| **Gravação antes da validação** | `lixo.bin` e `vazio.ged` falham no parse e ficam em disco |
| Colisão silenciosa | o primeiro envio é perdido, sem erro e com mensagem de sucesso |
| Nome como chave de sessão | `gedcom_filename` arbitrário responde `200` e carrega o arquivo |

O escape por caminho deixou de ser hipótese: o arquivo nasce fisicamente fora da pasta de upload.

A causa raiz é **herdada do legado**. O oráculo congelado
`_reversa_sdd/oracle/app_legacy_e43ca22.py` (sha256 conferido nesta sessão) tem as mesmas quatro
construções em `:569-570`, `:579` e `:589-590`, e zero ocorrências de `MAX_CONTENT_LENGTH` e
`secure_filename`. Corrigir aqui é divergir do legado de forma deliberada, e é por isso que o
veredito de spec é obrigatório.

## Suspected Area

Rota de upload em `analisador-genealogico/app.py` e a fronteira de parsing em
`analisador-genealogico/reconstructed/upload.py`. O projeto não tem camada de validação de entrada.

## Acceptance Criteria

- [x] Existe limite explícito de tamanho de requisição, e requisição acima do limite é rejeitada com
      mensagem própria. **Medido:** `MAX_CONTENT_LENGTH = 16 MB`, requisição acima recebe `413` e
      nada é gravado.
- [x] Extensão e conteúdo são validados antes do parse, conforme
      `_reversa_sdd/migration/risk_register.md#risk-007`. **Atendido com uma divergência declarada:**
      a validação é **de conteúdo**, não de extensão. A extensão rígida rejeitaria GEDCOM legítimo e
      quebraria a paridade, e o próprio `RISK-007` autoriza relaxá-la. Ver o
      `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` § 1.
- [x] A chave de armazenamento é gerada pelo servidor; o nome original é apenas metadado.
      **Medido:** `uploads/28a3f5fc1baa56a5__colisao.ged`.
- [x] Dois envios com o mesmo nome não se sobrescrevem, e o comportamento é coberto por teste.
      **Medido:** os dois conteúdos coexistem em disco.
- [x] Nome controlado pelo cliente não participa da composição de caminho no sistema de arquivos.
      **Medido:** `../ESCAPIU.ged` não grava fora da pasta, e é recusado como chave de recuperação.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/migration/risk_register.md#risk-007`, `_reversa_sdd/migration/target_business_rules.md#br-humana-001`, `_reversa_sdd/migration/discard_log.md#br-descartar-003`, `_reversa_sdd/migration/discard_log.md#br-descartar-006`, `_reversa_sdd/migration/ambiguity_log.md#amb-006`, `_reversa_sdd/questions.md#pergunta-3`, `_reversa_sdd/analise-dna/requirements.md#rastreabilidade-de-código`, `_reversa_sdd/upload-gedcom/design.md#riscos-e-lacunas`, `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais`, `_reversa_sdd/confidence-report.md#lacunas-pendentes-` |
| Adendo vigente | `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` |
| Código afetado | `analisador-genealogico/app.py`, `analisador-genealogico/reconstructed/upload.py` |
| Causa raiz | `confirmed`, medida. O nome do cliente sempre foi tratado como chave de armazenamento: concatenado a `UPLOAD_FOLDER`, gravado antes de qualquer validação e devolvido como `gedcom_filename`. Herdada do legado, não introduzida pela reconstrução. Ver `evidence/causacao-medida.txt` |
| Testes de reprodução | `tests/test_upload_seguranca.py::TestReproducao` (9) e `::TestModuloDeValidacao` (14) |
| Testes de regressão | `tests/test_upload_seguranca.py::TestRegressao` (4), mais a suíte inteira (128 itens) e o harness de paridade |
| Veredito de spec | `spec-desatualizada`, aprovado pelo usuário em 2026-10-02 |

## Resolution

Fechado em 2026-10-02 pelo `/reversa-debugger-fix`, em dois gates aprovados.

### Causa raiz

Estado final: **`confirmed`**, por medição e não por leitura de código.

O caminho de upload sempre tratou o nome escolhido pelo cliente como chave de armazenamento. Ele era
concatenado a `UPLOAD_FOLDER` com `os.path.join`, gravado **antes** de qualquer verificação, e
devolvido ao cliente como `gedcom_filename` para voltar como identificador nas requisições seguintes.
Nenhuma das quatro defesas existia no projeto, e **nenhuma existia no legado**: o oráculo congelado
tem as mesmas construções em `:569-570`, `:579` e `:589-590`, com zero ocorrências de
`MAX_CONTENT_LENGTH` e `secure_filename`. A reconstrução preservou a limitação por fidelidade, como o
docstring de `reconstructed/upload.py:1-7` declara.

### O que a medição acrescentou ao registro original

O registro classificava a reprodução como determinística por leitura de código. A sonda executou
cinco efeitos, e dois eram desconhecidos:

| Efeito | Medido |
|---|---|
| Sem teto de tamanho | `app.config["MAX_CONTENT_LENGTH"] is None` |
| **Escrita fora de `uploads/`** | nome `../ESCAPIU.ged` grava fora da pasta; `uploads/` fica vazia |
| **Gravação antes da validação** | `lixo.bin` e `vazio.ged` falham no parse e **ficam** em disco |
| Colisão silenciosa | o primeiro envio é perdido, com mensagem de sucesso e sem erro no servidor |
| Nome como chave de sessão | `gedcom_filename` arbitrário responde `200` e carrega o arquivo |

### Estratégia

**Correção direta**, aprovada na etapa 4. Causa raiz confirmada por medição, alvo localizado e
mudança reversível: os cinco critérios nascem da mesma decisão, e um change set único os fecha
juntos. O debate multiagente foi oferecido e recusado, corretamente: não havia hipóteses concorrentes
de diagnóstico.

### Change set

| CHG | Tipo | Artefato | Diff |
|---|---|---|---|
| `CHG-001` | `code` | `analisador-genealogico/reconstructed/validate.py` (novo) | `fix/CHG-001.diff` |
| `CHG-002` | `code` | `analisador-genealogico/app.py` | `fix/CHG-002.diff` |
| `CHG-003` | `specification` | `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` (novo) | não é diff de código |

`CHG-001` é um módulo puro: não importa Flask e não toca o disco. `CHG-002` liga a validação à rota,
define o teto de tamanho, grava sob a chave gerada e passa a validar o `gedcom_filename` recebido.
A mesma proteção foi aplicada ao upload do CSV de DNA, que tinha a fragilidade idêntica em
`app.py:49-50` e ficaria pela metade.

### Prova vermelho para verde

| Medida | Antes do change set | Depois |
|---|---|---|
| Testes do bug | 9 failed, 4 passed, 14 errors | **27 passed** |
| Suíte completa | 101 passed | **128 passed** |
| Paridade com o oráculo | 100% | **100%, zero divergência** |
| Requisição acima do teto | aceita e gravada | `413`, nada gravado |
| `../ESCAPIU.ged` | grava **fora** de `uploads/` | não grava fora |
| `lixo.bin`, `vazio.ged` | recusados, mas **ficam** em disco | recusados, não ficam |
| Dois envios de mesmo nome | o primeiro é perdido | **os dois** sobrevivem |
| `../ESCAPIU.ged` como chave | aceito | recusado |

A prova está em `fix/gate1-testes-falham.txt`, `fix/gate2-testes-passam.txt`, `fix/gate2-paridade.txt`
e na mesma sonda rodada nos dois estados (`fix/gate2-sonda-antes.txt`, `fix/gate2-sonda-depois.txt`).

### Risco assumido e declarado

A validação **não** filtra por extensão. Recusar por extensão rejeitaria GEDCOM legítimo e quebraria
a paridade de parsing, que é o risco número um do projeto. Medição de apoio: todos os 12 GEDCOM do
repositório usam `.ged`, incluindo as duas árvores reais e as 6 fixtures de paridade. A contingência
do `RISK-007` foi adotada na direção inversa: validar conteúdo e relaxar a extensão. Se algum
exportador legítimo for recusado, a cláusula permite relaxar mais, mantendo teto e chave gerada.

### Fechamento

`closure_policy: local-software` satisfeita: regressão passando (128 itens) e veredito de spec
registrado. `resolution_kind: fixed`, com causa raiz `confirmed` e testes de regressão não vazios.

## Agent Notes

- **Conflito de spec RESOLVIDO em 2026-10-02.** Existiam duas respostas humanas em sentidos opostos
  para o mesmo comportamento: `_reversa_sdd/questions.md#pergunta-3` aceitava a limitação para uso
  local, e `_reversa_sdd/migration/target_business_rules.md#br-humana-001` a descartava para o alvo
  multiusuário. O veredito aprovado foi **`spec-desatualizada`**, com adendo em
  `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md`. A spec original não foi editada, conforme a
  regra do registro.
- **Atenção à paridade, e como ela foi tratada.** `reconstructed/upload.py:1-7` declara que preserva a
  limitação por fidelidade ao legado, e validação estrita de extensão poderia rejeitar GEDCOM válido e
  quebrar a paridade de parsing, que é o risco número um do projeto. A correção **não filtra por
  extensão**: valida conteúdo e relaxa a extensão, que é a direção que o plano de contingência do
  `risk_register.md#risk-007` autoriza. Paridade medida em 100%, zero divergência, com o change set
  aplicado.
- **`visibility: restricted` por decisão do usuário.** Este bug não entra nas views; `generated/index.md`
  o mostra apenas como ID e "restrito".
- **Relação proposta.** Aresta `related-to` gravada em `BUG-20260929-BJJH`, apontando para este bug,
  porque ambos dependem da mesma pasta compartilhada e do mesmo nome de arquivo como chave.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.

---
*Gerado pelo Reversa-Debugger em 2026-09-29.*
