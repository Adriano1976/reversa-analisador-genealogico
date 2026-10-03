---
schema_version: 1
id: OPP-20261003-LMAY
verb: standardize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: pattern-only
  evidence:
    - safety-net/padronizacao.txt
    - safety-net/suite-depois.txt
    - safety-net/paridade-depois.txt
measurement:
  before: "12 referencias vivas ao nome antigo do modulo, em 6 arquivos"
  after: "0 referencias vivas ao nome antigo do modulo"
change_set:
  - chg: CHG-001
    file: src/reconstructed/domain.py
    purpose: renomeado para `src/reconstructed/text_cleaning.py`, que e o que o modulo faz; o docstring passa a nomear os consumidores reais
  - chg: CHG-002
    file: src/reconstructed/csv_ingest.py, src/reconstructed/name_normalization.py, src/reconstructed/dna_analysis.py, tests/test_domain.py
    purpose: os quatro importadores e as duas citacoes em docstring passam a apontar para o nome novo
  - chg: CHG-003
    file: _reversa_sdd/parity/harness.py
    purpose: o import que vive DENTRO da string do coletor passa ao nome novo, e o comentario que descrevia duas implementacoes divergentes vira registro historico com a medicao que o refuta
  - chg: CHG-004
    file: README.md
    purpose: a arvore de `src/` passa a bater com o disco e a prosa cita o modulo pelo nome novo
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-renomear-modulo.diff
  - CHG-002-importadores.diff
  - CHG-003-harness-comentario.diff
  - CHG-004-readme.diff
---

## O padrao detectado, e a convencao aplicada

Dos treze modulos do pacote, doze nomeiam a acao que executam, em `snake_case` e sem prefixo de camada: `csv_ingest`, `gedcom_state`, `gedcom_parser`, `name_normalization`, `matching`, `path_finding`, `family_navigation`, `mermaid_render`, `path_search`, `dna_analysis`, `validate`, `core/cm_estimator`. O decimo terceiro era `domain.py`, que nomeava uma camada e cujo conteudo era limpeza de texto corrompido.

A convencao aplicada e a que o projeto ja pratica: **o nome do modulo diz o que ele faz**. Nenhuma convencao nova foi introduzida, nenhum estilo foi imposto de fora, e nenhum outro modulo foi tocado por nao seguir o padrao.

## O que mudou, e a prova de que nada semantico mudou

| Verificacao | Resultado |
|---|---|
| Codigo do modulo, comparado por AST e sem os docstrings | **identico**: nenhum comando, chamada, literal ou expressao mudou |
| Linhas trocadas fora do codigo, dentro do docstring do modulo | 6 |
| Linhas trocadas fora do codigo, em comentario | 4, que sao duas trocas de duas linhas |
| Linhas trocadas de qualquer outro tipo | **0** |
| Linhas do modulo | 84 para 86, pelas duas linhas que o docstring ganhou |

A comparacao por AST e a prova principal, e ela e o que sustenta `preservation.method: pattern-only`: uma renomeacao que tivesse arrastado qualquer comando apareceria como AST diferente, mesmo que o texto continuasse parecido.

As duas trocas de comentario sao as citacoes de `upload.families` e `upload.graph`, que passaram a `gedcom_state.families` e `gedcom_state.graph`. Elas **nao** entram na medicao de 12 referencias, porque o medidor conta referencias ao nome `domain`, e estas sao referencias a um modulo que deixou de existir na `OPP-20261003-TWNT`. Foram corrigidas no mesmo lote porque o plano determina que o docstring deste modulo pare de citar modulo inexistente, e deixar duas de tres seria pior do que nao mexer.

## A oportunidade encolheu antes de ser executada

A `LMAY` foi registrada com dois nomes a corrigir. O primeiro ja nao existia: `upload.py` virou `gedcom_state.py` mais `gedcom_parser.py` na `OPP-20261003-TWNT`, com nomes que descrevem o que os modulos fazem. O registro da oportunidade foi atualizado nesta transformacao justamente para nao continuar cobrando um alvo que deixou de existir.

## A armadilha que quase invalidou a prova

O harness de paridade importa o modulo **dentro de uma string**, porque o coletor do candidato e um script embutido em `harness.py`. A linha 163 nao aparece em nenhuma leitura de AST, e um `grep` por `import domain` tambem nao a encontra. Se ela ficasse para tras, o coletor do candidato morreria com `ImportError`, a paridade nao teria medicao, e a transformacao poderia ser declarada verde sem prova nenhuma.

O que garante que ela foi alcancada nao e a varredura: e a paridade ter rodado e dado **100 por cento**. Um import quebrado nao produz paridade, produz erro de coleta.

## Medicao: 12 referencias vivas para 0

Varredura medida, com o medidor arquivado nesta pasta. Ele cobre `src/`, `tests/`, `_reversa_sdd/parity/*.py` e `README.md`, e ignora de proposito `_reversa_sdd/domain.md` (que e uma spec, nao o modulo), o residuo gerado pelo harness e `_reversa_refactor/**` (que e evidencia historica e nao deve ser reescrita).

| Tipo de referencia | Antes | Depois |
|---|---|---|
| Import relativo dentro do pacote | 3 | 0 |
| Import do pacote no teste | 1 | 0 |
| Import do pacote dentro da string do harness | 1 | 0 |
| Citacao de arquivo em docstring ou prosa | 4 | 0 |
| Citacao de simbolo em comentario | 3 | 0 |
| **Total** | **12** | **0** |

Os retratos completos estao em `before-after/referencias-antes.txt` e `before-after/referencias-depois.txt`.

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento em 6 fixtures | **100 por cento, zero divergencia em 6 fixtures** |
| Verificacao da padronizacao | nao se aplica | **codigo intacto por AST, arvore do README coerente, consumidores no nome novo** |
| Import do coletor embutido | nao se aplica | **vivo, provado pela paridade ter medido** |

Nenhum teste foi renomeado, removido, desabilitado ou afrouxado.

## Exclusoes declaradas

Tres coisas ficaram de fora, e nenhuma delas e esquecimento:

| Item | Por que nao entrou |
|---|---|
| Renomear `tests/test_domain.py` | O registro da oportunidade preve atualizar o import dele, nao o nome. Renomear acrescentaria referencias desatualizadas em `_reversa_docs/`, que e gerado |
| Remover o import morto `DM` do harness | Ele e importado e nunca usado, mas remover e `prune`, nao `standardize`, e mudaria o conjunto de modulos que o coletor importa. Renomear preserva o comportamento exatamente. Vira oportunidade propria |
| Atualizar `_reversa_sdd/`, `_reversa_docs/` e a alma | Sao artefatos de outros donos. A arvore do README e do projeto e esta no `allowedPaths`; as specs nao |

## Nota de metodo: os diffs saem contra o estado real do Git

As tres transformacoes anteriores (`TWNT`, `DWJC`, `RGKA`) foram **commitadas em `60ad797`** durante esta sessao, antes desta transformacao comecar. Isso tem uma consequencia boa e uma obrigacao:

- consequencia boa: o `HEAD` **e** o estado anterior da LMAY, arquivo por arquivo, entao os quatro diffs saem contra o Git, sem reconstrucao de nada;
- obrigacao: provar isso, em vez de supor.

A prova e uma conferencia inversa, feita pelo proprio gerador de diffs: aplicando o inverso exato de cada edicao desta transformacao ao arquivo atual, o resultado tem de ser igual ao `HEAD`. Os **cinco** arquivos com par inverso batem byte a byte. O `README.md` foi comparado direto contra o `HEAD`, sem par inverso.

O conteudo de `HEAD` de cada arquivo foi congelado em `before-after/head/` no momento da aplicacao. Os diffs continuam reproduziveis mesmo que o `HEAD` ande depois, porque sao gerados contra as copias congeladas, e nao contra o Git em tempo de execucao.

## Efeito colateral declarado

`name_normalization.py` foi de 121 para 122 linhas. Nao houve mudanca de conteudo: o nome novo do modulo e quatro caracteres mais longo que o antigo, e a quebra de linha do docstring acompanhou.

## Pendencias, e nao sao desta transformacao

- `OPP-20261003-GUE7` continua com inventario desatualizado: o registro diz 12 arquivos e 1363 linhas, e o pacote tem **15 arquivos e 1422 linhas**.
- `README.md` deste registro de refactor continua dizendo que o harness de paridade "nao pode mais rodar". Ele roda, e deu 100 por cento nas tres ultimas transformacoes.
- `_reversa_sdd/` e `_reversa_docs/` ainda citam `domain.py`, `tests/test_domain.py` e `analisador-genealogico/`. Sao artefatos de extracao e de documentacao publicada, de outros donos.
