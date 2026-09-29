---
schema_version: 1
id: BUG-20260929-J6PQ
display_number: 3
title: Escape incompleto de nomes no rótulo Mermaid permite falsificar o grafo exibido
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
module: path-search
feature: busca-caminho
labels: [seguranca, injecao, mermaid, paridade]

visibility: restricted
security_suspected: true

reproduction:
  classification: not-reproduced
  rate: null
  suspected_triggers:
    - nome de pessoa no GEDCOM contendo colchetes
    - nome de pessoa no GEDCOM contendo crase
    - nome de pessoa no GEDCOM contendo palavra-chave do Mermaid

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
  affected_code:
    - analisador-genealogico/reconstructed/path_search.py
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

# Escape incompleto de nomes no rótulo Mermaid permite falsificar o grafo exibido

## Summary

Os nomes de pessoas entram no diagrama Mermaid como conteúdo de rótulo de nó, e o escape aplicado é
parcial. As funções `lab()` de `reconstructed/path_search.py` neutralizam `&`, `<`, `>`, aspas duplas
e quebras de linha, mas deixam passar colchetes, crase e palavras-chave da própria linguagem Mermaid.
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

## Actual Behavior

1. `reconstructed/path_search.py:190-199` e `:254-262` definem duas cópias textuais da função interna
   `lab(txt)`. Ela normaliza para NFC, troca espaços não separáveis e travessões, converte `&`, `<` e
   `>` nas entidades HTML correspondentes, substitui `"` por `'` e colapsa `\r` e `\n` em espaço.
2. Nenhuma das duas cópias trata `[`, `]`, crase ou palavras-chave do Mermaid.
3. Os rótulos são emitidos no formato de nó com texto entre aspas duplas, e o texto vem de
   `get_name(...)`, ou seja, do GEDCOM enviado pelo usuário (`path_search.py:227`, `:312`, `:220`,
   `:303`, `:380`).
4. `templates/index.html:125` e `:170` injetam a string resultante com `| safe`, desligando o
   autoescape do Jinja2 nesses dois pontos.
5. `templates/index.html:182` inicializa o renderizador com `securityLevel: 'strict'`, o que contém o
   dano em HTML e script, mas não torna o texto inerte para a gramática do Mermaid.

## Steps to Reproduce

1. Suba a aplicação e carregue um GEDCOM que contenha, no nome de uma pessoa presente no caminho,
   um dos caracteres que o escape não cobre: colchete, crase ou palavra-chave do Mermaid.
2. Execute uma busca de caminho que inclua essa pessoa.
3. Observe no diagrama se o texto do nome encerra o rótulo antes das aspas de fechamento e se o
   restante passa a ser interpretado como sintaxe, acrescentando nós ou arestas que não existem na
   árvore.

Reprodução não obtida nesta sessão. A classificação é `not-reproduced`: a sonda executada prova que
o escape é incompleto, mas se o analisador do Mermaid encerra ou não o rótulo no primeiro colchete
depende do parser e precisa de execução em navegador. O veredito do `bug.md` registra a hipótese,
não o fato.

## Evidence

- `evidence/sonda-escape-mermaid-20260929.txt`: transcrição da sonda com oito nomes hostis e a saída
  Mermaid gerada para cada um.
- `evidence/probe_mermaid.py`: script da sonda. Ele substitui o dicionário `people` do módulo apenas
  em memória e não altera nenhum arquivo do projeto.
- `evidence/verificacao-codigo.md`: os trechos exatos do código e o locator de cada um.
- Relato bruto e observações do escrivão: `../intake/relato-20260929-0139.md`.

## Suspected Area

`lab()` em `analisador-genealogico/reconstructed/path_search.py`, duplicada em duas funções, e os dois
pontos de injeção com `| safe` em `analisador-genealogico/templates/index.html`.

## Acceptance Criteria

- [ ] Nome de pessoa proveniente do GEDCOM não altera a estrutura do diagrama, qualquer que seja o
      conjunto de caracteres que ele contenha.
- [ ] Existe teste que alimenta a geração do Mermaid com nomes hostis e falha antes da correção.
- [ ] O escape é definido em um único lugar, e não em duas cópias que podem divergir.
- [ ] O modo `securityLevel: 'strict'` permanece ativo, conforme
      `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega`.

## Traceability

| Item | Valor |
|------|-------|
| Specs | `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega`, `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#impacto-por-artefato-da-extração`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/investigation.md#segurança-do-mermaid`, `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9-esclarecimentos`, `_reversa_sdd/busca-caminho/design.md#interface`, `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` |
| Código afetado | `analisador-genealogico/reconstructed/path_search.py`, `analisador-genealogico/templates/index.html` |
| Causa raiz | a preencher pelo `/reversa-debugger-fix` |
| Testes de reprodução | nenhum ainda |
| Testes de regressão | nenhum ainda |
| Veredito de spec | a decidir por humano (`spec_verdict` nulo) |

## Resolution

Não preenchida. Corrigir é trabalho do `/reversa-debugger-fix`, em dois gates de aprovação.

## Agent Notes

- **Estado epistemológico.** A sonda é evidência de escape incompleto, não de exploração bem
  sucedida. Quem for corrigir deve começar confirmando em navegador se o rótulo é encerrado no
  primeiro colchete. Se não for, o defeito é de robustez e de contrato de escape, e a severidade
  deve ser reavaliada para baixo com registro da decisão.
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
