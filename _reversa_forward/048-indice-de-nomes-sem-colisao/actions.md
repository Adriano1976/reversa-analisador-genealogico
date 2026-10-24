# Actions: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`
> Roadmap: `_reversa_forward/048-indice-de-nomes-sem-colisao/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 10 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 8 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Registrar a linha de base: suíte (`1655 passed, 9 skipped`) e o dossiê de referência de uma árvore sintética com homônimos — ids, ordem, `exact_count` e fichas — para comparação depois | - | `[//]` | `_reversa_forward/048-indice-de-nomes-sem-colisao/evidence/linha-de-base.md` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Reescrever `tests/test_indice_de_nomes_do_documental.py`: remover as guardas de AST da tupla `_INDICE_DE_NOMES` e a prova de corrida; manter o helper de árvore, agora com grafo real; escrever o teste de **não-contaminação** (`TT-20`) — duas árvores de 3 pessoas com xrefs `@I1@`/`@I9@` e um `xref` interior diferente não podem compartilhar o mapa | - | `[//]` | `tests/test_indice_de_nomes_do_documental.py` | 🟢 | `[X]` |
| T003 | Acrescentar o teste do memo por árvore: duas chamadas devolvem o **mesmo objeto** e a segunda não percorre as pessoas (contando `get_name`); árvore sem grafo (`arvore[2] is None`) constrói sem estourar | T002 | - | `tests/test_indice_de_nomes_do_documental.py` | 🟢 | `[X]` |
| T004 | Acrescentar o teste estrutural: o módulo não declara `_INDICE_DE_NOMES` nem `_chave_de`, e `_indice_por_nome` não escreve em `global` | T003 | - | `tests/test_indice_de_nomes_do_documental.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Em `src/core/homonimos.py`, trocar o cache de módulo pelo mapa preso ao grafo da árvore, com guarda para grafo ausente, e **remover** `_INDICE_DE_NOMES` e `_chave_de` | T002, T003, T004 | - | `src/core/homonimos.py` | 🟢 | `[X]` |
| T006 | Reescrever o bloco de comentário e a docstring que justificam a chave antiga e proíbem `id()`, registrando o desenho novo: chave zero, vida do mapa = vida da árvore | T005 | - | `src/core/homonimos.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Rodar a suíte completa e corrigir regressões; registrar o número final | T005, T006 | - | `tests/` | 🟢 | `[X]` |
| T008 | Conferir a paridade do dossiê contra a linha de base: mesmos ids, mesma ordem, mesmo `exact_count` e mesmas fichas | T007 | `[//]` | `_reversa_forward/048-indice-de-nomes-sem-colisao/evidence/depois.md` | 🟢 | `[X]` |
| T009 | Conferir a ausência de estado de módulo por varredura do fonte e o custo por contagem (uma construção por árvore), registrando os dois resultados | T007 | `[//]` | `_reversa_forward/048-indice-de-nomes-sem-colisao/evidence/verificacoes.md` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Atualizar o `onboarding.md` com a contagem final de testes e o resultado das verificações, substituindo o texto de expectativa | T008, T009 | - | `_reversa_forward/048-indice-de-nomes-sem-colisao/onboarding.md` | 🟢 | `[X]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-to-do` | reversa |
