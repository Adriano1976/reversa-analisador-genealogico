# Adendo: a árvore e os índices deixaram de ser reconstruídos a cada `POST`

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md#1` e `_reversa_sdd/analise-dna/design.md`)

## Vigência

Vigente desde 2026-10-24.

## Resumo da entrega

O `POST` de análise de DNA media **67,29 s** num caso real (19.403 pessoas, CSV de 492 linhas), e
**88 % disso era custo fixo reexecutado para o mesmo arquivo**: 50,53 s de parse e 8,72 s de
índices. A feature faz os dois derivados nascerem uma vez e serem reusados enquanto o arquivo não
mudar.

Duas peças, um dono cada: o adaptador `CarregadorDeArvoresGedcom` guarda a última árvore,
chaveada por `(caminho, mtime_ns, tamanho)`, com teto 1 e *single-flight*; `build_ged_indexes`
prende o trio de índices ao grafo da própria árvore, como `fichas_da_pessoa._indice_de_filhos` já
fazia com o índice de filhos.

**17 de 17 ações concluídas.** Suíte: **1655 passed, 9 skipped** (baseline 1635/9). Medição
pareada, na mesma sessão:

| Ação | Sem cache | Com cache |
|---|---:|---:|
| Selecionar a árvore | 54,81 s | **0,92 s** |
| Análise nº 1 (constrói os índices) | 70,70 s | **17,79 s** |
| Análise nº 2 (índices prontos) | 62,17 s | **4,74 s** |

O `sha256` do HTML foi idêntico nas quatro execuções (duas com, duas sem cache): nenhum cartão,
veredito, ordem ou descarte mudou. Memória: 381 MB depois do parse e 412 MB depois dos índices,
com teto 1.

**Nota de retenção (privacidade).** A árvore, que antes vivia apenas durante a requisição, passa
a ficar residente enquanto `ANALISADOR_CACHE_DE_ARVORE` estiver ligada. Ela continua sem ser
escrita em disco, logada ou serializada, e morre com o processo; o que muda é o tempo de vida em
memória. Nenhuma política de retenção nova foi criada — a dívida `L-29` (dado pessoal no
PostgreSQL) segue intocada.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (Visão geral) | `regra-alterada` | "Não há cache entre requisições" passa a ser **condicional**: com a variável de ambiente, a árvore e seus derivados sobrevivem à requisição, invalidados pelo arquivo e limitados a uma árvore |
| `_reversa_sdd/architecture.md` | §4 (Modelo de dados) | `delta-de-dados` | A memória de módulo passa de **1** para **2** estruturas: `CACHE_DE_NOMES` e `CACHE_DE_ARVORES` (~337 MB por árvore, ~31 MB de índices) |
| `_reversa_sdd/erd-complete.md` | §7 (inventário das 42 estruturas) | `componente-novo` | Entra `CACHE_DE_ARVORES`, chaveada pelo arquivo; o inventário passa a **43** estruturas |
| `_reversa_sdd/data-dictionary.md` | entradas de memória de módulo | `delta-de-dados` | `CACHE_DE_ARVORES`: chave `(caminho, mtime_ns, tamanho)`, teto 1, LRU, sem persistência |
| `_reversa_sdd/analise-dna/design.md` | §Fluxo Principal | `regra-alterada` | `build_ged_indexes` constrói **uma vez por árvore** e prende o trio ao grafo; a segunda chamada não percorre as pessoas |
| `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md` | "O que NÃO muda" | `regra-alterada` | O item que afirmava "não há cache entre requisições" **deixa de valer**; a regra 2 do mesmo adendo (índice derivado, sem chave que possa colidir) permanece e foi seguida |

## Regras sob vigilância

`W001`, `W002`, `W003`, `W004`, `W005` — em
`_reversa_forward/047-cache-dos-indices-da-arvore/regression-watch.md`.

## Fontes

- `_reversa_forward/047-cache-dos-indices-da-arvore/requirements.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/roadmap.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/legacy-impact.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/regression-watch.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/progress.jsonl`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/depois.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/paridade.md`
- `_reversa_forward/047-cache-dos-indices-da-arvore/evidence/memoria.md`
