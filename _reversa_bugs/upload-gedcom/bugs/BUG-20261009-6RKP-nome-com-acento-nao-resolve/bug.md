---
schema_version: 1
id: BUG-20261009-6RKP
display_number: 6
title: Nome armazenado com acento ou espaço não pode ser resolvido
status: resolved
phase: delivering
severity: high
priority: P2
created: 2026-10-09
updated: 2026-10-10

origin:
  type: inspection
  external_ref: {provider: reversa-audit, id: A007}

area: analisador-genealogico
module: upload
feature: upload-gedcom
labels: []

visibility: normal
security_suspected: false

reproduction:
  classification: deterministic
  rate: "7/7"
  suspected_triggers: []

blocking: []

mitigation:
  kind: data-repair
  applied_at: 2026-10-09
  temporary: true
  what: >-
    Renomeados no disco os 4 arquivos com chave cujo nome visivel tinha acento ou espaco, tirando
    o acento e trocando o espaco por underscore. A CHAVE foi preservada, e ela vem do conteudo, de
    modo que a referencia continua valida. Os 3 arquivos SEM chave ficaram de fora: sao duplicatas
    byte a byte de arquivos com chave, e renomear para a chave do gemeo colidiria com ele.
  approved_by: Adriano
  approved_at: 2026-10-09
  gate: reparo de dados, aprovado na forma "renomear com MANIFESTO em vez de copia fisica"
  evidence: fix/manifesto-renomeacao.md
  effect: >-
    Alcancaveis por referencia passaram de 12 para 16, de 19 arquivos. Prova 1 do manifesto: o
    multiconjunto de sha256+bytes da pasta e IDENTICO antes e depois, ou seja, so os nomes mudaram.
  NOT_fixed: >-
    MITIGADO NAO E CORRIGIDO. O gravador continua preservando acento, e todo arquivo novo enviado
    com acento no nome nasce inalcancavel. E a mitigacao e temporary: se o fix decidir aceitar
    acento na leitura, as renomeacoes se tornam desnecessarias. Reversao: renomear de volta, pelo
    mapeamento do manifesto.

relationships:
  - bug: BUG-20260929-QMLY
    type: related-to
    state: confirmed
    evidence:
      - ref: _reversa_sdd/upload-gedcom/contracts.md#2.1
        observation: >-
          O `QMLY` introduziu a forma `<16 hex>__<nome visivel>` com o alfabeto fechado como
          defesa contra escape. O `root_cause` CONFIRMADO deste bug e essa mesma forma, lida
          contra a metade que preserva acento e espaco. A hipotese virou fato no fix.

traceability:
  specs:
    - "_reversa_sdd/upload-gedcom/contracts.md#2.1"
    - "_reversa_sdd/domain.md#3.5"
  affected_code:
    - "src/utils/validate.py"
    - "src/ports/adaptadores.py"
  root_cause:
    state: confirmed
    hypothesis: >-
      A defesa contra escape de caminho foi escrita como um ALFABETO FECHADO
      (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) no MESMO arquivo em que o gravador PRESERVA
      acento e espaço no nome visível. As duas regras nunca foram confrontadas, e o
      resolvedor passou a recusar exatamente o que o gravador produz.
    causal_path:
      - "`nome_visivel_seguro` preserva acento e espaço (`RF-06`, requisito Must)"
      - "`_FORMATO_CHAVE` exige `[A-Za-z0-9._-]+` na parte visível"
      - "`chave_recebida_e_valida` devolve `False` para o nome que a aplicação gravou"
      - "`ArmazenamentoEmDisco.resolver` devolve `None`"
      - "a tela responde `Erro: Arquivo '...' não existe mais.` — que é FALSO"
    evidence:
      - ref: evidence/_sonda_forma_do_nome.py
        observation: >-
          varredura dos nomes da pasta real: 7 de 19 recusados — 3 por acento, 3 por não
          terem chave e 1 por espaço.
      - ref: ../evidence/_sonda_forma_do_nome.py
        observation: >-
          depois do conserto, a MESMA sonda mede 13 de 13 aceitos e 0 recusados pelo
          validador de forma.
      - ref: ../../../../_reversa_forward/011-escolher-arquivo-da-lista/audit/cross-check.md
        observation: >-
          `A007` (CRITICAL) mediu o mesmo defeito pelo lado da lista, e é a origem deste
          registro.
    code_refs:
      - {file: src/utils/validate.py, symbol: chave_recebida_e_valida, commit: null}
      - {file: src/utils/validate.py, symbol: _FORMATO_CHAVE, commit: null}
  reproduction_tests:
    - tests/test_forma_da_referencia.py
  regression_tests:
    - tests/test_forma_da_referencia.py
    - tests/test_upload_seguranca.py
    - tests/test_lista_de_arquivos.py
    - tests/test_path_search.py

spec_verdict: spec-correta

approval:
  spec_verdict:
    decided_by: Adriano
    decided_at: 2026-10-10
    document: _reversa_sdd/addenda/011-escolher-arquivo-da-lista.md

change_set:
  - id: CHG-001
    kind: code
    artifact: src/utils/validate.py
    purpose: >-
      `chave_recebida_e_valida` deixa de exigir o alfabeto fechado e passa a exigir que a
      referência seja um NOME: prefixo de 16 hexadecimais, e a parte visível validada por
      `referencia_de_arquivo_da_pasta` — sem barra, sem barra invertida, sem byte nulo,
      sem `.` nem `..`. A defesa contra escape NÃO era o alfabeto, e sim a exigência de
      ser um nome.
  - id: CHG-002
    kind: test
    artifact: tests/test_forma_da_referencia.py
    purpose: >-
      Prova as DUAS metades: as formas que o gravador produz são aceitas (acento, espaço,
      apóstrofo, parênteses, chave dupla), e o escape continua recusado — os cinco casos
      do `BUG-20260929-QMLY` mais dez tentativas de escapar COM o prefixo da chave.
  - id: CHG-003
    kind: code
    artifact: src/app.py
    purpose: >-
      Conserto do SEGUNDO defeito, que este registro deixou em aberto na seção de Agent
      Notes e que foi tratado como `T042` da feature 011: `_arvore_do_formulario` ganha
      guarda em volta do parse, o traceback vai para o LOG, e as mensagens de erro passam
      a mostrar o rótulo em vez da referência com a chave dentro (`D-09`).

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Nome armazenado com acento ou espaço não pode ser resolvido

## Summary

O gravador de arquivos compõe o nome armazenado preservando **acentos e espaços** no nome visível, e o
resolvedor recusa toda referência que não case a forma fechada `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`, que não
admite nem acento nem espaço. As duas regras vivem no **mesmo arquivo** (`src/utils/validate.py`), de modo
que todo arquivo cujo nome visível tenha acento ou espaço fica **gravado sob um nome que o próprio sistema
não consegue ler de volta**.

Medido nos 19 arquivos da pasta canônica: **7 são inalcançáveis por referência**, e a resposta ao operador
é `Erro: Arquivo '...' não existe mais.`, que é **falsa**.

## Expected Behavior

A spec efetiva é `_reversa_sdd/upload-gedcom/contracts.md#2.1`, e ela declara **as duas coisas**, em linhas
vizinhas:

- `contracts.md:51` (🟢): o nome visível preserva "**acentos, espaços** e a extensão original";
- `contracts.md:53` (🟢): "**Forma fechada, verificada em toda leitura:** `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`".

O comportamento esperado é que as duas sejam satisfeitas ao mesmo tempo, o que é impossível para um nome
visível com acento ou espaço. Este bug existe porque **a spec se contradiz**, e o código implementa
fielmente as duas metades. `_reversa_sdd/domain.md#3.5` repete a mesma tensão: a linha `domain.md:140`
manda preservar a extensão e a `:139` declara a forma fechada como a defesa contra escape da pasta.

**Não é `spec-gap`.** A spec cobre o assunto, de forma inconsistente. A decisão de qual lado cede é humana,
e deve virar adendo versionado conforme o protocolo do registro.

## Actual Behavior

1. `nome_visivel_seguro` (`src/utils/validate.py:40-65`) preserva acentos e espaços, deliberadamente, para
   que o rótulo seja o que o operador reconhece.
2. `ArmazenamentoEmDisco.resolver` (`src/ports/adaptadores.py:93`) chama `chave_recebida_e_valida`
   (`src/utils/validate.py:78-87`), que aplica `_FORMATO_CHAVE` (`:32`) e devolve `False` para qualquer
   acento ou espaço.
3. `resolver` devolve `None`, `_arvore_do_formulario` (`src/app.py:186-188`) traduz o `None` em
   `Erro: Arquivo '{referencia}' não existe mais.`, e a mensagem é **falsa**: o arquivo está na pasta.
4. Varredura dos 19 arquivos, com a função do próprio repositório:

   | Grupo | Arquivos | Alcançável |
   |---|---:|---|
   | Chave + nome visível em ASCII | 12 | sim |
   | Nome visível com acento | 3 | **não** |
   | Sem chave no nome | 3 | **não** |
   | Chave + espaço no nome visível | 1 | **não** |

   Os arquivos com acento são `50a3dd36fea8f8bb__Famílias_Sergipanas.csv`,
   `94e2402671702cac__Famílias_Sergipanas.csv` e `94e2402671702cac__Famílias_Sergipanas.csv.ged`. O com
   espaço é `b70889273a505a5d__Familias Sergipanas.xlsx`. Os três sem chave são anteriores à chave por
   conteúdo: `Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged` e `Famílias_Sergipanas.csv`.

## Steps to Reproduce

1. Aponte a aplicação para uma pasta com um arquivo cujo nome visível tenha acento:

   ```powershell
   $env:PYTHONIOENCODING = "utf-8"
   .\.venv\Scripts\python.exe _reversa_bugs\upload-gedcom\bugs\BUG-20261009-6RKP-nome-com-acento-nao-resolve\evidence\_sonda_forma_do_nome.py
   ```

   Saída esperada: `RECUSA` nas 7 linhas apontadas acima.

2. Rode a rota contra a pasta real, em modo somente leitura:

   ```powershell
   .\.venv\Scripts\python.exe _reversa_bugs\upload-gedcom\bugs\BUG-20261009-6RKP-nome-com-acento-nao-resolve\evidence\_sonda_caso_negativo_real.py
   ```

   Saída esperada: `200` com `mensagem contem: "não existe mais"` para o CSV com nome `.ged`, e
   `VEREDITO: pasta IDENTICA` no fim.

3. Para o caso geral, envie pela tela um arquivo cujo nome tenha acento, e tente usá-lo na requisição
   seguinte: a referência devolvida pelo formulário jamais resolve.

## Evidence

- `evidence/_sonda_forma_do_nome.py`: varredura dos 19 nomes com `chave_recebida_e_valida`.
- `evidence/_sonda_caso_negativo_real.py`: execução da rota contra a pasta real, com inventário por
  `sha256` antes e depois.
- `evidence/_sonda_caso_negativo.py`: a mesma rota com arquivo sintético, que expõe um **segundo** defeito
  (ver Agent Notes).
- `evidence/cross-check-A007.md`: o recorte da auditoria da feature 011 que mediu o caso.

## Suspected Area

- `src/utils/validate.py`: `_FORMATO_CHAVE` (`:32`), `nome_visivel_seguro` (`:40-65`) e
  `chave_recebida_e_valida` (`:78-87`). A contradição está contida neste arquivo.
- `src/ports/adaptadores.py:93`: quem aplica a forma na leitura.
- `src/app.py:186-188`: quem transforma o `None` na mensagem falsa.

## Acceptance Criteria

1. Um arquivo cujo nome visível tenha acento **e** um cujo nome visível tenha espaço, uma vez gravados,
   podem ser resolvidos e usados pela aplicação, **ou** deixam de ser gravados com esses caracteres. Qual
   dos dois lados cede é decisão humana registrada em `spec_verdict` e em adendo.
2. A mensagem `Erro: Arquivo '...' não existe mais.` deixa de ser usada para um arquivo que existe.
3. Testes de regressão cobrem os dois caracteres, e a defesa contra escape de caminho continua provada
   (nenhum nome com `/`, `\`, `..` ou NUL pode ser resolvido).
4. Os 19 arquivos da pasta canônica são reclassificados: cada um ou é alcançável, ou tem motivo declarado.

## Traceability

- Spec efetiva: `_reversa_sdd/upload-gedcom/contracts.md#2.1` (linhas 51 e 53) e
  `_reversa_sdd/domain.md#3.5` (linhas 139 e 140).
- Código afetado: `src/utils/validate.py`, `src/ports/adaptadores.py`, `src/app.py`.
- Testes existentes relacionados: `tests/test_upload_seguranca.py` (forma do nome e escape de caminho),
  `tests/test_porta_de_armazenamento.py` (adaptador e contrato das portas).
- Causa raiz e veredito de spec: **preenchidos pelo `/reversa-debugger-fix`**, não aqui.

## Resolution

**Corrigido em 2026-10-10.** `resolution_kind: fixed`, `closure.satisfied: true`.

### Causa raiz, confirmada

A defesa contra escape de caminho foi escrita como um **alfabeto fechado**
(`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) no mesmo arquivo em que o gravador **preserva acento e
espaço** no nome visível. As duas regras vivem em `src/utils/validate.py` e nunca foram
confrontadas: o gravador produz `94e2402671702cac__Famílias_Sergipanas.csv` e o resolvedor
recusa esse mesmo nome. Medido: **7 dos 19 arquivos** da pasta ficavam inalcançáveis, e a tela
dizia "não existe mais" sobre arquivos que existiam.

### Veredito de spec: `spec-correta`

A spec **estava certa**. O `RF-06` exige preservar acentos e espaços no nome visível, e é o
gravador que cumpre esse requisito; quem divergia era o resolvedor. Por isso o lado que cedeu
foi o **código** — decisão do operador, registrada em `approval.spec_verdict` e declarada como
`RN-20` no adendo da feature 011.

### O argumento de segurança, e por que ele não se sustenta

Este registro proibia enfraquecer a forma fechada, porque ela era tida como a defesa contra
escape. **A defesa nunca foi o alfabeto** — era a exigência de a referência ser um **NOME**, e
não um caminho. A prova é que os cinco casos do `BUG-20260929-QMLY` continuam recusados por
construção, e não por acaso:

| caso | por que continua recusado |
|---|---|
| `../etc/passwd` | não tem o prefixo de 16 hexadecimais |
| `uploads\..\x.ged` | idem |
| `nome_do_cliente.ged` | idem |
| `""` | sai na primeira linha |
| `None` | idem |
| `<chave>__../fora.ged` | tem o prefixo, e o separador barra na parte visível |
| `<chave>__a\b.ged` | idem |
| `<chave>__a\x00b.ged` | byte nulo |
| `<chave>__..` e `<chave>__` | `..` e vazio |

### Change set

| id | tipo | artefato | o que faz |
|---|---|---|---|
| `CHG-001` | code | `src/utils/validate.py` | `chave_recebida_e_valida` passa a exigir um NOME, com a parte visível validada por `referencia_de_arquivo_da_pasta` |
| `CHG-002` | test | `tests/test_forma_da_referencia.py` | 32 testes: 9 formas aceitas, o cruzamento gravador × resolvedor, os 5 casos originais de escape, 10 tentativas **com** o prefixo, 6 fora da forma da chave, e o contrapeso contra `return False` fixo |
| `CHG-003` | code | `src/app.py` | o **segundo defeito** desta pasta, que o registro deixou em aberto: parse sem guarda (§ Agent Notes). Tratado como `T042` da feature 011 |

### Testes

- **Reprodução** (`reproduction_tests`): `tests/test_forma_da_referencia.py`. Antes do conserto,
  `TestFormasAceitas` falhava para acento e espaço. Depois dele, o mesmo arquivo mede o
  comportamento correto — e é por isso que ele aparece também como regressão.
- **Regressão** (`regression_tests`): o mesmo arquivo (escape), mais `tests/test_upload_seguranca.py`
  (os cinco casos originais), `tests/test_lista_de_arquivos.py` (o item indisponível que resta é o
  arquivo **sem chave**) e `tests/test_path_search.py` (recusa sem `500`).

### Prova no conteúdo real

A sonda `evidence/_sonda_forma_do_nome.py`, rodada contra a pasta do operador **depois** do
conserto: **13 de 13 aceitos, 0 recusados** pelo validador de forma. A suíte fecha em
**517 passed, 9 skipped, zero falhas**.

### O que este conserto NÃO faz

- **Não repara o passado.** Os arquivos que a mitigação de 2026-10-09 renomeou continuam com os
  nomes ASCII; nada é renomeado de volta.
- **Não torna alcançável o arquivo sem chave.** Ele continua indisponível, e agora é o **único**
  caso de indisponibilidade — a `RN-11` ficou sem objeto para acento e espaço.
- **Não fecha o `A008` como parte deste bug.** Ele foi corrigido, e está em `CHG-003`, mas o
  crédito é da `T042` da feature 011, que o encontrou pela rota e o reproduziu.

## Agent Notes

- **Restrição de ouro: a defesa contra escape de caminho não pode enfraquecer.** A forma fechada é o que
  impede um `gedcom_filename` manipulado de apontar para fora da pasta, e ela não usa lista negra
  (`contracts.md#2.1`, `domain.md:139`). Se a decisão for aceitar acento e espaço, a forma nova precisa
  manter proibidos `/`, `\`, NUL e qualquer sequência que produza `..`, e isso tem de estar **provado por
  teste**, não argumentado.
- **Não há contorno pela aplicação.** Reenviar o mesmo arquivo reproduz o nome acentuado, pela chave de
  conteúdo e pela preservação do nome. O contorno é renomear o arquivo antes de enviar.
- **Segundo defeito, medido no caminho, e não corrigido aqui:** um arquivo cujo **nome passa** na forma
  fechada e cujo **conteúdo** o `ged4py` não lê derruba a requisição com `500` e traceback, porque
  `_arvore_do_formulario` chama `carregar_arvore` fora de qualquer `try` (`src/app.py:186` e `:263`, contra
  os ramos que capturam exceção em `:299` e `:322`). Não é alcançável com os 19 arquivos de hoje, mas é
  alcançável por arquivo colocado na pasta fora da aplicação. Está registrado em
  `_reversa_forward/011-escolher-arquivo-da-lista/audit/cross-check.md` como `A008`. **Decidir se entra
  neste bug ou vira um segundo.**
  - **DECIDIDO E CORRIGIDO em 2026-10-10:** virou a `T042` da feature 011, que o reproduziu pela rota
    (`POST` com `gedcom_filename` apontando para um `.csv`) e mediu que **10 dos 13 arquivos da pasta
    real** derrubavam o parser. Está em `CHG-003` e na `## Resolution`. Fica registrado aqui porque a
    instrução de decidir nasceu nesta linha.
- **Prioridade.** Mantida em P2 porque os outros 12 arquivos funcionam. Se `Famílias_Sergipanas.csv` for o
  dado de trabalho do operador, sobe para P1: são 3 dos 10 arquivos de DNA, e um deles aparece duas vezes
  na lista da feature 011.
- **Relação `related-to` com BUG-20260929-QMLY** (mesmo `module: upload`, mesma `feature`, mesma região de
  código: composição do nome armazenado). Estado `proposed`: é hipótese de leitura, não fato apurado.
- **Relação com a feature 011.** A `011` **marca** o item indisponível e não conserta o contrato. Se este
  bug for corrigido antes de a 011 entrar, a marca fica sem objeto para os arquivos acentuados, e a `011`
  precisa ser reavaliada (`RN-11`, `RF-09`, `D-11`).
- **Taxonomia.** `module: upload` e `feature: upload-gedcom` são valores existentes de `taxonomy.yaml`. Não
  foi necessário propor termo novo.
- **Convenção não documentada, que o fix vai precisar:** o bloco de topo `approval` (com `spec_verdict`,
  `decided_by`, `decided_at` e `document`) **não está no `bug-schema.md`**, mas existe em
  `BUG-20260929-QMLY` e é o que registra a decisão humana que aprovou o veredito de spec. Este registro
  nasceu com `spec_verdict: null` e **sem** esse bloco; no instante em que o veredito for decidido, o bloco
  tem de ser acrescentado junto, apontando o adendo. Fica registrado aqui para não se perder.
- **A MITIGAÇÃO JÁ FOI APLICADA, e ela mexe no que o fix vai encontrar.** Em 2026-10-09 o operador aprovou
  o reparo de dados que renomeou os 4 arquivos com chave (manifesto e prova em
  `fix/manifesto-renomeacao.md`). Consequências para quem for corrigir: (a) os nomes com acento **não
  existem mais no disco**, e sim os ASCII, então os passos de reprodução que citam os nomes antigos
  precisam do manifesto; (b) a mitigação é `temporary: true` e reversível, e **pode se tornar
  desnecessária** se o veredito for aceitar acento na leitura; (c) o defeito de raiz **continua** — basta
  enviar um arquivo novo com acento no nome.
- **Um teste prende o lado "gravar" da contradição, e o fix tem de saber disso.**
  `tests/test_upload_seguranca.py:387-388` compõe o nome com `nome_do_arquivo_armazenado` e assere
  `endswith("__Famílias_Sergipanas.csv")`, ou seja, **exige que o gravador preserve o acento**. Se o
  veredito de spec for "parar de preservar acento", esse teste muda junto e o adendo tem de dizer por quê.
  Se o veredito for "aceitar acento na leitura", o teste fica como está.
- **Referências históricas não serão reescritas.** Cerca de cem documentos de `_reversa_forward/`,
  `_reversa_sdd/` e `_reversa_bugs/` citam os nomes antigos. O manifesto é o mapa antigo -> novo; reescrever
  registro histórico está fora do protocolo.
- **Não medido:** as linhas históricas da tabela `dna_analysis` podem guardar o *nome* dos arquivos
  renomeados. `DATABASE_URL` está ausente do ambiente e nenhum código de `src/` faz `SELECT`, então não há
  efeito funcional — mas o banco **não foi consultado**, e o registro não afirma que ele está limpo.
