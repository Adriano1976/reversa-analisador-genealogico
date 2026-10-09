---
schema_version: 1
id: BUG-20261009-6RKP
display_number: 6
title: Nome armazenado com acento ou espaço não pode ser resolvido
status: active
phase: reproducing
severity: high
priority: P2
created: 2026-10-09
updated: 2026-10-09

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
    state: proposed
    evidence: []

traceability:
  specs:
    - "_reversa_sdd/upload-gedcom/contracts.md#2.1"
    - "_reversa_sdd/domain.md#3.5"
  affected_code:
    - "src/utils/validate.py"
    - "src/ports/adaptadores.py"
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

A preencher pelo `/reversa-debugger-fix`. Este registro nunca corrige.

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
