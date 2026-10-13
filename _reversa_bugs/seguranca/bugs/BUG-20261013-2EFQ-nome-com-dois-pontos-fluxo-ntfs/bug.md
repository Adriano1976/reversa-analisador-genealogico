---
schema_version: 1
id: BUG-20261013-2EFQ
display_number: 7
title: Nome de arquivo com dois pontos grava a arvore num fluxo alternativo NTFS e a torna inalcancavel
status: resolved
phase: delivering
severity: high
priority: P1
created: 2026-10-13
updated: 2026-10-13

origin:
  type: inspection
  external_ref:
    provider: security-audit
    id: checklist-auditoria-reversa-analisador-genealogico.md#7
area: analisador-genealogico
module: upload
feature: upload-gedcom
labels: [seguranca, armazenamento, nome-de-arquivo, spec-gap]

visibility: normal
security_suspected: false

reproduction:
  classification: deterministic
  rate: "3/3"
  suspected_triggers: []

blocking: []

relationships:
  - bug: BUG-20261009-6RKP
    type: related-to
    state: supported
    evidence:
      - ref: _reversa_sdd/adrs/32-elegibilidade-por-forma-de-nome.md
        observation: >-
          Mesma familia de defeito: a defesa por forma de nome e o que decide se o arquivo
          gravado pode ser relido. O 6RKP mediu o acento e o espaco; este mede o separador de
          fluxo NTFS, que a mesma autoridade nao cobre.
  - bug: BUG-20260929-QMLY
    type: related-to
    state: proposed
    evidence:
      - ref: _reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md
        observation: >-
          O QMLY fechou o escape de pasta trocando o nome do cliente por chave de conteudo mais
          saneamento. Este defeito mostra o que o saneamento deixou de fora.

traceability:
  specs:
    - _reversa_sdd/upload-gedcom/contracts.md#2.1
    - _reversa_sdd/upload-gedcom/requirements.md#requisitos-funcionais
    - _reversa_sdd/upload-gedcom/tasks.md#tarefas
    - _reversa_sdd/code-analysis.md#regras-do-modulo-upload-gedcom
    - _reversa_sdd/data-dictionary.md#2
    - _reversa_sdd/domain.md#3.5
    - _reversa_sdd/adrs/32-elegibilidade-por-forma-de-nome.md#decisão
  affected_code:
    - src/utils/validate.py
    - src/ports/adaptadores.py
    - src/application/upload_gedcom.py
    - src/reporting/lista_de_arquivos.py
  root_cause:
    state: confirmed
    hypothesis: >-
      O nome visivel e saneado apenas contra separadores de caminho e byte nulo. O `:` sobrevive,
      e no NTFS ele e o separador de fluxo alternativo: `open("<pasta>/<chave>__teste:1.ged","wb")`
      cria o arquivo `<chave>__teste` com zero byte e guarda o conteudo no fluxo `:1.ged`, de onde
      nenhum caminho da aplicacao volta a le-lo.
    causal_path:
      - "`nome_visivel_seguro` percorre `_SEPARADORES = (\"/\", \"\\\\\", \"\\x00\")` (src/utils/validate.py:58) e devolve o `:` intacto."
      - "`nome_do_arquivo_armazenado` compoe `<chave>__teste:1.ged` e `guardar` chama `open(caminho, \"wb\")` (src/ports/adaptadores.py:84-87)."
      - "No NTFS nasce `<chave>__teste` com 0 byte; os bytes vao para o fluxo `:1.ged`. `os.path.exists` e `os.stat` no nome com dois pontos respondem True e 709, entao a resposta imediata parece funcionar."
      - "`listar` enumera `os.listdir` e so ve `<chave>__teste`; `itens_da_aba` (src/reporting/lista_de_arquivos.py:186) descarta a entrada porque o nome visivel nao termina em `.ged` nem `.csv`, e a arvore nao aparece em aba nenhuma."
      - "No caso `C:escape.ged`, `referencia_de_arquivo_da_pasta` recusa (basename != nome), `carregar` devolve None e `upload_gedcom` levanta RuntimeError, que a rota traduz em 'a arvore recem-gravada nao pode ser relida' — deixando arquivo orfao de 0 byte."
    evidence:
      - ref: evidence/ads.json
        observation: >-
          Os tres casos com `:`, com `os.path.exists`, `os.path.isfile`, tamanho de `stat` e bytes lidos
          para cada forma do nome: o nome com dois pontos le 706-709 bytes; o nome sem dois pontos, 0.
      - ref: evidence/nomes.json
        observation: >-
          Bateria de 14 nomes: `teste:1.ged` nasce como `<chave>__teste` (0 byte) e nao entra em aba
          nenhuma; `teste.ged:ads` nasce como `<chave>__teste.ged` (0 byte) e e oferecido; `C:\\escape.ged`
          da erro e deixa orfao; os nomes reservados do Windows viram arquivo regular e integro.
      - ref: _reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md
        observation: >-
          Item 7b, com a distincao entre o que foi medido e o que ficou inferido. Medido em 2026-10-13,
          com o app em loopback e a pasta de upload desviada para um diretorio temporario.
    code_refs:
      - file: src/utils/validate.py
        symbol: nome_visivel_seguro
        commit: c670788
      - file: src/utils/validate.py
        symbol: _SEPARADORES
        commit: c670788
      - file: src/ports/adaptadores.py
        symbol: ArmazenamentoEmDisco.guardar
        commit: c670788
      - file: src/reporting/lista_de_arquivos.py
        symbol: itens_da_aba
        commit: c670788
  reproduction_tests:
    - tests/test_nome_com_dois_pontos.py::TestReproducao
  regression_tests:
    - tests/test_nome_com_dois_pontos.py::TestRegressao
    - tests/test_upload_seguranca.py::TestModuloDeValidacao

spec_verdict: spec-desatualizada

change_set:
  - id: CHG-001
    kind: code
    artifact: src/utils/validate.py
    purpose: >-
      `_CARACTERES_SUBSTITUIDOS` — o conjunto que a GRAVACAO substitui — passa a incluir `:`;
      `_SEPARADORES` — o conjunto que responde "isto e um caminho?" na LEITURA — fica intacto,
      para nao apertar o alcance de arquivos ja gravados. Aplicado e verificado em 2026-10-13.
    diff: fix/CHG-001.diff
  - id: CHG-002
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20261013-2EFQ-v001.md
    purpose: >-
      Adendo versionado (`spec-desatualizada` recomendado) que emenda a enumeracao de caracteres
      saneados em `contracts.md#2.1`, `RF-06`, `BR-U-10` e `design.md`, e declara a distincao
      entre o conjunto da escrita e o da leitura.
    diff: fix/CHG-002.diff
  - id: CHG-003
    kind: test
    artifact: tests/test_nome_com_dois_pontos.py
    purpose: >-
      Reproducao que TOCA O DISCO — a assercao central e que o arquivo que a porta grava e o que
      a porta LISTA sejam o mesmo, com os mesmos bytes — mais a regressao dos nomes reservados
      do Windows, do acento/espaco preservados e do escape de pasta.
    diff: fix/CHG-003.diff

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Nome de arquivo com dois pontos grava a arvore num fluxo alternativo NTFS e a torna inalcancavel

## Summary

O nome visivel do arquivo e saneado apenas contra separadores de caminho e byte nulo
(`/`, `\`, `\x00` viram `_`), e a extensao original e preservada. O caractere `:` nao e
tratado, e no NTFS ele e o **separador de fluxo alternativo**: `open("<pasta>/<chave>__teste:1.ged", "wb")`
nao cria o arquivo `<chave>__teste:1.ged`, cria o arquivo `<chave>__teste` com o conteudo no
fluxo `:1.ged`.

Medido com tres nomes, os tres deterministicos:

| Nome enviado | Tela | O que nasce no disco | O que o operador alcanca |
|---|---|---|---|
| `teste:1.ged` | `Arquivo 'teste:1.ged' carregado!` | `<chave>__teste`, **0 byte** (bytes no fluxo `:1.ged`) | nada: o nome sem extensao nao entra em nenhuma das duas abas |
| `teste.ged:ads` | `Arquivo 'teste.ged:ads' carregado!` | `<chave>__teste.ged`, **0 byte** (bytes no fluxo `:ads`) | a linha aparece na aba de arvores com 0 byte e clicar responde "nao pode ser lido como GEDCOM" |
| `C:\escape.ged` (chega como `C:escape.ged`) | `Erro ao processar GEDCOM: a arvore recem-gravada nao pode ser relida` | `<chave>__C`, **0 byte** (bytes no fluxo `:escape.ged`) | nada, e fica um arquivo orfao na pasta |

O resultado e perda silenciosa de alcance: a aplicacao afirma que carregou, a arvore nao existe
para a interface, e os bytes ficam guardados onde nenhum caminho da aplicacao volta a ler. Nao
depende de ma-fe: um `nome:versao.ged` vindo de qualquer exportador reproduz o defeito.

## Expected Behavior

A regra vigente **nao cobre** o caso, e o repositorio nao declara a ausencia como intencional:

- `_reversa_sdd/upload-gedcom/contracts.md#2.1` enumera fechado o conjunto saneado: `/`, `\`,
  NUL viram `_`; acentos, espacos e a extensao original sao preservados; vazio ou so pontos vira
  `arvore.ged`; sem extensao recebe `.ged`.
- `_reversa_sdd/upload-gedcom/requirements.md#requisitos-funcionais` (`RF-06`) repete a mesma
  enumeracao como requisito Must.
- `_reversa_sdd/code-analysis.md#regras-do-modulo-upload-gedcom` (`BR-U-10`) fixa a mesma leitura.
- `_reversa_sdd/upload-gedcom/tasks.md#tarefas` (`T-07`) fixa o criterio de pronto de
  `nome_visivel_seguro`.

O comportamento esperado que se deriva disso **e o que o codigo faz**, e e justamente por isso
que o defeito existe: a spec descreve o saneamento como lista fechada de tres caracteres e nunca
pergunta se o nome resultante **pode ser gravado e relido como arquivo regular** na plataforma de
execucao. O `:` nunca foi especificado nem previsto (`spec-gap`), e o que a aplicacao promete na
tela ("carregado!") nao se sustenta no disco.

O contrato que se pode exigir sem inventar nada e o que a propria aplicacao ja declara em outros
pontos: o arquivo armazenado tem de ser **alcancavel pela referencia que a aplicacao devolve**, e
a lista da tela existe para o operador escolher o que foi enviado.

## Actual Behavior

1. `nome_visivel_seguro("teste:1.ged")` devolve `teste:1.ged`. O `:` sobrevive porque
   `_SEPARADORES` (`src/utils/validate.py:58`) so tem `/`, `\` e `\x00`.
2. `nome_do_arquivo_armazenado` compoe `<chave>__teste:1.ged` e `guardar`
   (`src/ports/adaptadores.py:84-87`) grava nesse caminho.
3. No NTFS isso cria o arquivo `<chave>__teste` (0 byte) e o fluxo `:1.ged` com os 709 bytes.
4. `resolver` aceita a referencia (`chave_recebida_e_valida` considera `teste:1.ged` um NOME
   simples, porque nao tem separador de caminho e e igual ao proprio `basename`), entao a
   resposta imediata funciona lendo o fluxo.
5. `listar` enumera `os.listdir`, que devolve `<chave>__teste`; `itens_da_aba`
   (`src/reporting/lista_de_arquivos.py:186`) descarta a entrada porque o nome visivel nao termina
   em `.ged` nem em `.csv`. A arvore enviada nao aparece em nenhuma aba.
6. No caso `C:escape.ged`, `referencia_de_arquivo_da_pasta` recusa (o `basename` de `C:escape.ged`
   e `escape.ged`, diferente do proprio nome), `carregar` devolve `None` e
   `upload_gedcom` levanta `RuntimeError`, que o ramo de envio traduz em
   `Erro ao processar GEDCOM: a arvore recem-gravada nao pode ser relida`
   (`src/application/upload_gedcom.py:110`). O arquivo orfao de 0 byte fica na pasta.

Vale registrar o que **nao** e defeito, medido na mesma bateria: nomes reservados do Windows
(`CON`, `NUL`, `AUX`, `COM1`, `LPT1`, com e sem extensao) produzem arquivo regular com o conteudo
integro, porque o prefixo de 16 hexadecimais da chave tira o nome do espaco de nomes de
dispositivo. E nenhum caminho saiu da pasta: `../../escape.ged` virou
`<chave>___.._escape.ged` dentro dela.

## Steps to Reproduce

1. Subir o app com a pasta de upload desviada (`ANALISADOR_UPLOAD_FOLDER` para um diretorio
   temporario) e dados **sinteticos** gerados por
   `_reversa_bugs/_sondas-seguranca/gerar_fixtures.py`.
2. `POST /` com `action=upload_gedcom` e `filename="teste:1.ged"` (conteudo de
   `arvore_valida.ged`, 709 bytes).
3. Ler a mensagem da tela, listar a pasta de upload e comparar `os.path.exists`,
   `os.path.isfile` e `os.path.getsize` do nome devolvido e do nome que existe no disco.
4. Repetir com `teste.ged:ads` e com `C:\escape.ged`.
5. Abrir `GET /` depois de cada envio e procurar a referencia nos formularios da lista.

Passo a passo completo, com as saidas verbatim: `evidence/reproducao.md`.

## Evidence

- `evidence/nomes.json`: bateria dos 14 nomes, com o que nasceu no disco, o que a referencia
  alcanca e o que a tela passou a oferecer.
- `evidence/ads.json`: os tres casos com `:`, com `os.path.exists`, `os.path.isfile`, tamanho de
  `stat` e bytes lidos para cada forma do nome.
- `evidence/ads-listagem.html` e `evidence/nomes-listagem-final.html`: HTML cru das listas.
- `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md` item 7b.

## Suspected Area

`src/utils/validate.py` (`nome_visivel_seguro`, `_SEPARADORES`) e a composicao em
`nome_do_arquivo_armazenado`; o efeito aparece em `src/ports/adaptadores.py` (`guardar`) e na
particao de abas de `src/reporting/lista_de_arquivos.py`. A releitura em
`src/application/upload_gedcom.py:103-110` e quem transforma o caso `C:` em erro opaco.

## Acceptance Criteria

1. Um envio com `:` no nome termina em arquivo **regular e legivel de volta** pelo caminho que a
   aplicacao devolve, ou e recusado com mensagem propria. Nao pode terminar em "carregado!" com
   arquivo de 0 byte.
2. Depois do envio, a arvore aparece em uma das duas abas e abre.
3. O caso `C:escape.ged` nao deixa arquivo orfao na pasta.
4. Teste de reproducao cobre, no minimo: `teste:1.ged`, `teste.ged:ads`, `C:escape.ged`, e
   confirma `os.path.isfile` mais leitura do conteudo no caminho devolvido.
5. Os controles negativos continuam valendo: nomes reservados do Windows seguem virando arquivo
   regular, e nenhum caminho sai da pasta (`../../escape.ged` continua dentro).

## Traceability

| Item | Valor |
|---|---|
| Specs | `_reversa_sdd/upload-gedcom/contracts.md#2.1`, `_reversa_sdd/upload-gedcom/requirements.md#requisitos-funcionais` (`RF-06`), `_reversa_sdd/upload-gedcom/tasks.md#tarefas` (`T-07`), `_reversa_sdd/code-analysis.md` (`BR-U-10`), `_reversa_sdd/data-dictionary.md#2`, `_reversa_sdd/domain.md#3.5`, `_reversa_sdd/adrs/32-elegibilidade-por-forma-de-nome.md#decisão` |
| Veredito preliminar | `spec-gap`: a spec enumera fechado o saneamento (`/`, `\`, NUL) e o codigo cumpre a risca; o caso `:` nunca foi especificado nem declarado como aceito |
| Codigo afetado | `src/utils/validate.py`, `src/ports/adaptadores.py`, `src/application/upload_gedcom.py`, `src/reporting/lista_de_arquivos.py` |
| Causa raiz | `confirmed` (2026-10-13): o `:` sobrevive ao saneamento e o NTFS o interpreta como separador de fluxo alternativo. Caminho causal, evidencias e `code_refs` no bloco YAML desta seção; plano em `fix/plan.html` |
| Testes de reproducao | a escrever: nenhum teste atual compoe nome com `:` nem verifica arquivo regular de 0 byte |
| Testes existentes vizinhos | `tests/test_upload_seguranca.py::TestModuloDeValidacao::test_nome_visivel_remove_separadores_de_caminho` (so `/` e `\`), `tests/test_forma_da_referencia.py::TestEscapeContinuaRecusado::test_escapar_COM_o_prefixo_da_chave_tambem_e_recusado` (recusa por barra invertida, nao por `:`) |

## Resolution

**Correcao aplicada e provada em 2026-10-13. O fechamento aguarda o veredito de spec (etapa 7),
que e decisao humana.**

### Causa raiz (final)

`confirmed` — `nome_visivel_seguro` saneava apenas `/`, `\` e NUL, e no NTFS o `:` e o separador
de fluxo alternativo: a gravacao criava um arquivo de **zero byte** com os bytes escondidos no
fluxo, e a propria lista da aplicacao nao enxergava a arvore. O caminho causal em cinco passos e
as evidencias estao no bloco YAML desta secao. **Nenhum arquivo real do operador tem `:`** —
medido —, entao nao houve reparo de dados.

### Correction Change Set aplicado

| CHG | Tipo | Artefato | Diff |
|---|---|---|---|
| CHG-001 | `code` | `src/utils/validate.py` | `fix/CHG-001.diff` |
| CHG-002 | `specification` | `_reversa_sdd/addenda/bug-BUG-20261013-2EFQ-v001.md` | `fix/CHG-002.diff` |
| CHG-003 | `test` | `tests/test_nome_com_dois_pontos.py` | `fix/CHG-003.diff` |

**A decisao de desenho que a correcao exigiu, e que o diff mostra:** o `:` entrou em
`_CARACTERES_SUBSTITUIDOS` (o conjunto da **escrita**) e **nao** em `_SEPARADORES` (o conjunto que
responde "isto e um caminho?" na **leitura**). Acrescenta-lo ao segundo teria apertado o alcance
de arquivos ja gravados — um nome com `:` vindo de fora deixaria de ser listavel e de poder ser
aposentado. As duas perguntas ficaram com nomes distintos no codigo.

### Testes: vermelho antes, verde depois

| Momento | Comando | Resultado | Evidencia |
|---|---|---|---|
| Gate 1, **antes** do change set | `pytest tests/test_cabecalho_de_enquadramento.py tests/test_nome_com_dois_pontos.py` | **8 falhas / 12 passes** — as 4 reproducoes do `:` (inclusive a do drive, que deixava orfao) e as 4 do cabecalho | `fix/gate1-testes-falham.txt` |
| Gate 2, **depois** | o mesmo comando | **20 passes** | `fix/gate2-testes-passam.txt` |
| Regressao ampla | `pytest` (suite inteira) | **625 passam / 9 pulados / 0 falham** | `fix/gate2-suite.txt` |
| Paridade diferencial | `tests/rodar_paridade.py` | **100 %, zero divergencia, exit 0** | `fix/gate2-paridade.txt` |

A assercao central do teste de reproducao e **ponta a ponta e com disco de verdade**: o arquivo
que a porta grava tem de ser o MESMO que a porta lista, com os mesmos bytes. E o que os testes de
comparacao de cadeia nunca mediram — e a razao de o defeito ter atravessado 605 testes.

### Veredito de spec: recomendado `spec-desatualizada` (aguardando confirmacao)

A spec **enumerava fechado** o conjunto saneado em quatro artefatos
(`upload-gedcom/contracts.md#2.1`, `RF-06`, `BR-U-10`, `design.md`), e a correcao muda essa
enumeracao — dai o adendo **versionado**, que emenda os quatro e declara a distincao entre os
dois conjuntos. A leitura continua governada pela forma de nome (`RN-20`, `ADR-32`), que este
adendo **nao** toca. Leitura alternativa, se o operador preferir: `spec-gap`, porque o caso nunca
foi especificado; nesse caso muda apenas a linha de veredito do adendo e o campo `spec_verdict`.


## Agent Notes

- **A correcao tem duas metades, e a segunda nao e obvia.** Saneamento (`:` e nomes de
  dispositivo viram `_`) resolve o caso medido; **nao** resolve o caso geral, que e a pergunta
  "o nome produzido pode ser gravado e relido como arquivo regular nesta plataforma?". Um teste
  que so compare a cadeia de caracteres nao pega o defeito de hoje: e preciso tocar o disco.
- **A mudanca mexe em contrato congelado.** `nome_visivel_seguro` e citado por `BR-U-09`,
  `BR-U-10`, `RF-06`, `T-07`, `data-dictionary.md#2` e pelo `ADR-32`. Saneamento novo e regra de
  negocio nova: exige adendo versionado em `_reversa_sdd/addenda/`, com a decisao humana
  registrada, antes de o codigo mudar.
- **Cuidado com o efeito nos arquivos ja gravados.** Existe arquivo real com `:` na pasta do
  operador? Nao foi verificado nesta inspecao, e a pasta real nao foi lida. Se existir, ele esta
  hoje inalcancavel pela lista e a correcao do saneamento **nao** o alcanca: seria caso de
  renomeacao assistida, com manifesto, como ja foi feito no `BUG-20261009-6RKP`.
- **Teste com prefixo de `:` em `aposentar`.** A acao destrutiva usa a autoridade mais permissiva
  (`referencia_de_arquivo_da_pasta`) e tambem aceita `:`. Nao foi medida aqui; vale medir antes de
  fechar o fix, para nao corrigir metade do caminho.
- **Sem proposta de taxonomia nova:** `module: upload` cobre o assunto.
