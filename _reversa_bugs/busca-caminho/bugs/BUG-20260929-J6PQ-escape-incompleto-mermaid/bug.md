---
schema_version: 1
id: BUG-20260929-J6PQ
display_number: 3
title: Escape incompleto de nomes no rótulo Mermaid permite falsificar o grafo exibido
status: resolved
phase: patching
severity: medium
priority: P1
created: 2026-09-29
updated: 2026-09-29

origin:
  type: manual-report
  external_ref: null

area: analisador-genealogico
module: path-search
feature: busca-caminho
labels: [seguranca, injecao, mermaid, paridade, spec-gap]

visibility: restricted
security_suspected: true

reproduction:
  classification: deterministic
  rate: 1/1
  suspected_triggers:
    - nome de pessoa no GEDCOM que comeca com crase, produzindo a sequencia aspa mais crase no rotulo emitido
    - nome de pessoa no GEDCOM contendo colchete (medido como inerte: fica dentro das aspas)
    - nome de pessoa no GEDCOM contendo palavra-chave do Mermaid (medida como inerte)

blocking: []

relationships: []

traceability:
  specs:
    - _reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega
    - _reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#impacto-por-artefato-da-extração
    - _reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas
    - _reversa_forward/001-reconstrua-o-conteudo-da-index/investigation.md#segurança-do-mermaid
    - _reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9-esclarecimentos
    - _reversa_sdd/busca-caminho/design.md#interface
    - _reversa_sdd/busca-caminho/design.md#riscos-e-lacunas
    - _reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md
  affected_code:
    - analisador-genealogico/reconstructed/path_search.py
    - analisador-genealogico/templates/index.html
  root_cause:
    state: confirmed
    hypothesis: >-
      A sequencia aspa mais crase no rotulo, produzida por nome que comeca com crase, desvia o lexer
      do Mermaid para o modo md_string, e ali o fecha-colchete nunca vira o token SQE que a regra
      vertex exige, o que impede o diagrama de renderizar.
    causal_path:
      - o nome vindo do GEDCOM tem crase na primeira posicao
      - _mermaid_label emite o rotulo entre aspas duplas sem neutralizar a crase
      - o lexer do flowchart casa a regra de aspa seguida de crase e entra em md_string
      - o fecha-colchete e consumido como texto e o token SQE nunca e emitido
      - a regra vertex fica sem fechamento e o Mermaid reporta Syntax error in text
    evidence:
      - ref: evidence/reproduction.md
        observation: navegador real com Mermaid 10.9.8 exibiu Syntax error in text no lugar do diagrama
      - ref: evidence/analise-gramatica-mermaid-20260929.md
        observation: a regra de lexer que dispara o desvio, citada literalmente do flow.jison
      - ref: tests/test_mermaid_escape.py
        observation: os 2 casos de reproducao falham antes da correcao e passam depois, e os 4 payloads sem crase passam nos dois estados
    code_refs:
      - file: analisador-genealogico/reconstructed/path_search.py
        symbol: _mermaid_label
        commit: null
  reproduction_tests:
    - tests/test_mermaid_escape.py::test_rotulo_neutraliza_crase
    - tests/test_mermaid_escape.py::test_diagrama_nao_carrega_caractere_que_quebra_a_gramatica
  regression_tests:
    - tests/test_mermaid_escape.py::test_entidades_html_preservadas
    - tests/test_mermaid_escape.py::test_caracteres_legitimos_sobrevivem
    - tests/test_mermaid_escape.py::test_neutralizacoes_que_ja_existiam
    - tests/test_mermaid_escape.py::test_rotulo_vazio_continua_vazio
    - tests/test_characterization_mermaid.py::test_saida_mermaid_caracterizada
    - tests/test_characterization_mermaid.py::test_rotulo_com_caracteres_de_escape

spec_verdict: spec-gap

change_set:
  - id: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/path_search.py
    purpose: Troca a neutralizacao por lista negra por lista branca de caracteres no rotulo Mermaid
    diff: fix/CHG-001.diff
  - id: CHG-002
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md
    purpose: Especifica pela primeira vez o contrato de escape do rotulo Mermaid
    diff: null

closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Escape incompleto de nomes no rótulo Mermaid permite falsificar o grafo exibido

## Summary

Os nomes de pessoas entram no diagrama Mermaid como conteúdo de rótulo de nó, e o escape aplicado é
parcial. `_mermaid_label` em `reconstructed/path_search.py` neutraliza `&`, `<`, `>`, aspas duplas
e quebras de linha, mas deixa passar colchetes, crase e palavras-chave da própria linguagem Mermaid.
O resultado é injetado com autoescape desligado em `templates/index.html`. A defesa adicional do
renderizador é `securityLevel: 'strict'`, que bloqueia execução de HTML e script, mas não impede que
o texto do usuário altere a sintaxe do diagrama. O sintoma plausível é falsificação do parentesco
exibido, não execução de código.

## Expected Behavior

O comportamento esperado está na spec efetiva:

- `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega` registra a única
  mudança funcional autorizada na reconstrução da interface: inicializar o Mermaid com
  `securityLevel: 'strict'`, "fecha vetor de XSS vindo dos arquivos do usuário (GEDCOM/CSV)".
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas` repete o
  objetivo: o modo estrito impede a renderização de tags HTML não seguras nos rótulos dos grafos.
- `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9-esclarecimentos` registra a
  resposta humana que originou a decisão: "Mudar para o padrão strict (maior segurança)".
- `_reversa_sdd/busca-caminho/design.md#interface` especifica `generate_mermaid_graph` e
  `generate_mermaid_graph_indirect_bridge` como as funções que produzem o diagrama.

A intenção declarada da spec é que conteúdo vindo de arquivo do usuário não consiga alterar o que o
diagrama expressa. O escape parcial não cumpre essa intenção, mesmo com o modo estrito ativo.

**Lacuna declarada (`spec-gap`).** A spec efetiva trata do vetor de HTML e script, fechado pela
decisão D-02, e nunca tratou do vetor de integridade do diagrama: `design.md#riscos-e-lacunas` não
menciona escape nem caracteres de rótulo. O contrato existia apenas como detalhe de implementação. Foi
especificado pela primeira vez em `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md`, aprovado pelo
usuário em 2026-09-29, na etapa 7 do fluxo de correção.

## Actual Behavior

Re-verificado em 2026-09-29, depois da `OPP-20260929-TPSH`. A duplicação que o registro original
descrevia não existe mais: o escape é definido uma única vez, em
`reconstructed/path_search.py:193` (`_mermaid_label`), e as duas funções de renderização o alcançam
por alias, em `:206` e `:255`. Com a duplicação, saiu também a divergência entre cópias.

1. `_mermaid_label` (`:193-202`) normaliza para NFC, troca espaços não separáveis e travessões,
   converte `&`, `<` e `>` nas entidades HTML correspondentes (`:200`), substitui `"` por `'`
   (`:201`) e colapsa `\r` e `\n` em espaço (`:202`).
2. A função não trata `[`, `]`, crase nem palavras-chave do Mermaid. Isso permanece verdadeiro.
3. O rótulo é emitido **entre aspas duplas**, no formato `N_id["texto"]`, em `:227`, `:235` e
   `:305`. O texto vem de `get_name(...)`, ou seja, do GEDCOM enviado pelo usuário (`:225-226`,
   `:234`, `:296`, `:305`, `:373`).
4. `templates/index.html:125` e `:170` injetam a string resultante com `| safe`, desligando o
   autoescape do Jinja2 nesses dois pontos.
5. `templates/index.html:182` inicializa o renderizador com `securityLevel: 'strict'`, o que contém o
   dano em HTML e script, mas não torna o texto inerte para a gramática do Mermaid.

Medição de re-verificação, em `evidence/reverificacao-emissao-20260929.txt`: o payload
`Joao"] --> N_evil["x`, o mais hostil do conjunto, produz
`N_I1["Joao'] --&gt; N_evil['x"]`. A aspa dupla, único caractere capaz de encerrar o rótulo antes do
fim, é substituída por apóstrofo, e a sequência de seta perde o `>`. Colchete, crase e palavra-chave
permanecem dentro das aspas.

Consequência para a classificação: o texto do usuário **não altera a estrutura do diagrama** pelos
caminhos medidos. O defeito que sobra é de contrato de escape e de robustez, não de falsificação
alcançável. A reavaliação de severidade depende da confirmação em navegador descrita nas Agent Notes,
que ainda não foi feita.

## Steps to Reproduce

1. Suba a aplicação e carregue um GEDCOM que contenha, no nome de uma pessoa presente no caminho,
   um dos caracteres que o escape não cobre: colchete, crase ou palavra-chave do Mermaid.
2. Execute uma busca de caminho que inclua essa pessoa.
3. Observe no diagrama se o texto do nome encerra o rótulo antes das aspas de fechamento e se o
   restante passa a ser interpretado como sintaxe, acrescentando nós ou arestas que não existem na
   árvore.

**Reproduzido em 2026-09-29, em navegador**, com a cápsula completa em `evidence/reproduction.md`.
O diagrama não renderiza: a página exibe `Syntax error in text` com `mermaid version 10.9.8`.

O sintoma observado **não** é o que o título deste bug afirma. Nenhum payload falsificou o
parentesco exibido. O que acontece é a renderização falhar por completo, e o gatilho é a sequência
de aspa seguida de crase, produzida por um nome que começa com crase. Essa sequência casa a regra
`<*>["][`]` do lexer do `flowchart`, que desvia o modo para `md_string`; ali o `]` de fechamento é
engolido como texto e nunca vira o token `SQE` que a regra `vertex` exige.

## Evidence

- `evidence/sonda-escape-mermaid-20260929.txt`: transcrição da sonda com oito nomes hostis e a saída
  Mermaid gerada para cada um.
- `evidence/probe_mermaid.py`: script da sonda. Ele substitui o dicionário `people` do módulo apenas
  em memória e não altera nenhum arquivo do projeto.
- `evidence/verificacao-codigo.md`: os trechos exatos do código e o locator de cada um.
- `evidence/reverificacao-pos-refactor-20260929.txt`: re-verificação do escape depois da
  `OPP-20260929-TPSH`, com o veredito por caractere.
- `evidence/reverificacao-emissao-20260929.txt`: re-verificação do **formato de emissão**, medindo se
  cada payload consegue encerrar o rótulo antes das aspas de fechamento.
- `evidence/probe_reverificacao_j6pq.py` e `evidence/probe_emissao_rotulo.py`: sondas da
  re-verificação, ambas somente leitura.
- Relato bruto e observações do escrivão: `../intake/relato-20260929-0139.md`.

## Suspected Area

`_mermaid_label` em `analisador-genealogico/reconstructed/path_search.py:193`, alcançada por alias em
`:206` e `:255`, e os dois pontos de injeção com `| safe` em
`analisador-genealogico/templates/index.html`.

## Acceptance Criteria

- [x] Nome de pessoa proveniente do GEDCOM não altera a estrutura do diagrama, qualquer que seja o
      conjunto de caracteres que ele contenha. **Satisfeito** pela lista branca do `CHG-001` e
      coberto por `tests/test_mermaid_escape.py`.
- [x] Existe teste que alimenta a geração do Mermaid com nomes hostis e falha antes da correção.
      **Satisfeito**: 2 casos falhavam antes, ver `fix/gate1-testes-falham.txt`.
- [x] O escape é definido em um único lugar, e não em duas cópias que podem divergir. **Satisfeito
      pela `OPP-20260929-TPSH`**, antes desta correção: `_mermaid_label` existe uma única vez, em
      `path_search.py:193`, e as duas funções o alcançam por alias.
- [x] O modo `securityLevel: 'strict'` permanece ativo, conforme
      `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega`. **Satisfeito**:
      o `CHG-001` não tocou `templates/index.html`.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega`, `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#impacto-por-artefato-da-extração`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/investigation.md#segurança-do-mermaid`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9-esclarecimentos`, `_reversa_sdd/busca-caminho/design.md#interface`, `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` |
| Código afetado | `analisador-genealogico/reconstructed/path_search.py`, `analisador-genealogico/templates/index.html` |
| Causa raiz | `confirmed`: a sequência aspa mais crase no rótulo desvia o lexer do Mermaid para `md_string`, o `]` de fechamento nunca vira `SQE` e o diagrama não renderiza. Reproduzido em navegador com Mermaid 10.9.8 em 2026-09-29. O vetor de falsificação não se sustenta |
| Testes de reprodução | `tests/test_mermaid_escape.py::test_rotulo_neutraliza_crase`, `tests/test_mermaid_escape.py::test_diagrama_nao_carrega_caractere_que_quebra_a_gramatica` |
| Testes de regressão | `tests/test_mermaid_escape.py::test_entidades_html_preservadas`, `::test_caracteres_legitimos_sobrevivem`, `::test_neutralizacoes_que_ja_existiam`, `::test_rotulo_vazio_continua_vazio`, `tests/test_characterization_mermaid.py::test_saida_mermaid_caracterizada`, `tests/test_characterization_mermaid.py::test_rotulo_com_caracteres_de_escape` |
| Veredito de spec | `spec-gap`, com adendo aditivo `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md` |

## Resolution

**Causa raiz.** `confirmed`. A sequência aspa mais crase no rótulo, produzida por nome que começa com
crase, casa a regra de lexer que desvia o modo para `md_string`; ali o fecha-colchete nunca vira o
token `SQE` que a regra `vertex` exige, e o diagrama não renderiza. O caminho causal está no front
matter, com evidência por elo.

**O que o bug registrava, e o que era de fato.** O título afirmava falsificação do parentesco
exibido. A medição refutou esse vetor: a aspa dupla, único caractere que sairia do estado `string`, é
trocada por apóstrofo, e nenhum dos dez payloads encerrou o rótulo. O defeito confirmado é outro,
falha determinística de renderização. É por isso que a severidade caiu de `high` para `medium`, por
decisão do usuário registrada nas Agent Notes.

**Veredito de spec.** `spec-gap`, aprovado pelo usuário na etapa 7. A spec efetiva trata do vetor de
HTML e script, fechado pela decisão D-02 com `securityLevel: 'strict'`, e nunca tratou do vetor de
integridade do diagrama: `design.md#riscos-e-lacunas` não menciona escape nem caracteres de rótulo. O
contrato foi especificado pela primeira vez no adendo aditivo.

**`resolution_kind`.** `fixed`.

### Change set

| CHG | Tipo | Artefato | Propósito | Diff |
|-----|------|----------|-----------|------|
| `CHG-001` | code | `analisador-genealogico/reconstructed/path_search.py` | Lista negra vira lista branca em `_mermaid_label` | `fix/CHG-001.diff` |
| `CHG-002` | specification | `_reversa_sdd/addenda/bug-BUG-20260929-J6PQ-v001.md` | Especifica o contrato de escape pela primeira vez | arquivo novo, sem diff |

O diff de código e o adendo de spec ficam registrados **juntos**, como exige o protocolo do registro.

### Testes

Vermelho para verde, medido no mesmo commit:

| Estado | `tests/test_mermaid_escape.py` | Suíte completa |
|--------|-------------------------------|----------------|
| Antes do `CHG-001` | 2 falhas, 17 passam | 2 falhas, 93 passam |
| Depois do `CHG-001` | **19 passam** | **95 passam** |

- Evidência do vermelho: `fix/gate1-testes-falham.txt`
- Evidência do verde: `fix/gate2-testes-passam.txt`
- O diff aplicado foi conferido por hash contra o aprovado no Gate 2, e é idêntico.

### Aprovações

Plano, Gate 1 e Gate 2 aprovados pelo usuário em 2026-09-29, na mesma sessão.

### Reversão

`git checkout -- analisador-genealogico/reconstructed/path_search.py` e remoção do adendo. O arquivo de
teste pode permanecer: ele passaria a falhar, que é exatamente o comportamento desejado de um teste
de regressão.

## Agent Notes

- **Estado epistemológico.** A sonda é evidência de escape incompleto, não de exploração bem
  sucedida. Quem for corrigir deve começar confirmando em navegador se o rótulo é encerrado no
  primeiro colchete. Se não for, o defeito é de robustez e de contrato de escape, e a severidade
  deve ser reavaliada para baixo com registro da decisão.
- **Re-verificação de 2026-09-29, depois da `OPP-20260929-TPSH`.** O formato de emissão foi medido:
  `path_search.py:227`, `:235` e `:305` emitem o rótulo entre aspas duplas, e `:201` troca `"` por
  `'`. Em dez payloads hostis medidos, nenhum encerrou o rótulo. Isso responde à pergunta que o item
  anterior pedia para responder em navegador, mas por leitura do texto emitido, e não por execução do
  parser do Mermaid. **Falta a confirmação em navegador**, e é ela que decide a reavaliação de
  severidade. Enquanto não vier, a causa raiz fica em `supported`, nunca em `confirmed`.
- **A duplicação do escape já não existe.** A `TPSH` unificou as duas cópias de `lab()` em
  `_mermaid_label` (`path_search.py:193`), alcançada por alias em `:206` e `:255`. O critério de
  aceitação que exigia um único lugar para o escape está satisfeito desde então, antes de qualquer
  correção deste bug.
- **Severidade rebaixada de `high` para `medium` em 2026-09-29, por decisão do usuário**, cumprindo o
  que esta Agent Note pedia. Motivo: o vetor de falsificação do parentesco foi **refutado por
  medição** (a aspa dupla é neutralizada, e nenhum dos dez payloads encerrou o rótulo), e o defeito
  que sobrou é falha determinística de renderização, disparada por uma classe de caractere incomum.
  A prioridade segue `P1`: o defeito é total quando dispara, mesmo com gatilho raro.
- **Vocabulário pendente de revisão.** Com o vetor de injeção refutado, os labels `seguranca` e
  `injecao` ficaram imprecisos. A revisão deles é decisão humana e não foi feita aqui.
- **Duplicação relevante.** `lab()` existe duas vezes, em `generate_mermaid_graph` e em
  `generate_mermaid_graph_indirect_bridge`. Uma correção em apenas uma das cópias deixa metade dos
  caminhos desprotegida. `sid()` também está duplicada, com pequena diferença de tratamento de
  sequências, o que indica divergência já em curso.
- **O modo estrito não é a correção.** `securityLevel: 'strict'` foi a decisão D-02 da feature 001 e
  resolve XSS, não integridade do diagrama. Removê-lo ou rebaixá-lo contraria spec vigente.
- **`visibility: restricted` por decisão do usuário.** Este bug não entra nas views;
  `generated/index.md` o mostra apenas como ID e "restrito". Os nomes hostis usados na sonda ficam
  apenas em `evidence/`, e os passos de reprodução acima foram escritos sem payload pronto.
- **Taxonomia.** `area`, `module` e `feature` usam valores existentes em `_reversa_bugs/taxonomy.yaml`.
