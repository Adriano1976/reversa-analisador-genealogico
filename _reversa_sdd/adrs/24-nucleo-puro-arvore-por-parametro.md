# ADR-24 — Núcleo puro: a árvore entra por parâmetro e o estado de processo sai

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-07
- **Commit(s):** `ffc494c` (abre o ciclo `005-nucleo-puro-src`), `3d109b0`, `c6ae2d7`, `9657fd7`, `ccd4bba`, `1ecf8dc`, `cdcccb8`, `fd60f22`, `c6a7e72`, `2c6bd01`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Até esta decisão, `src/core/gedcom_state.py` mantinha `people`, `families`, `graph`, `child_to_family` e um contador `versao` como **estado global de processo**, mutado *in place* pelo parse. Três consequências já documentadas: (a) dois fluxos não podiam coexistir sem trocar de árvore; (b) o **`graph` era reatribuído**, e não mutado, o que obrigava quem o consumia a importá-lo **dentro da função**; (c) dois GEDCOMs carregados no mesmo processo eram indistinguíveis por identidade, o que forçou o cache de nomes a inventar uma chave de invalidação.

O `ADR-02` já havia reduzido a rota a uma camada fina, e o `ADR-08` decidiu **não** implementar determinadas heurísticas por falta de medição. O que faltava era o passo estrutural: o núcleo continuava a depender de um módulo de estado, e portanto **nenhum caso de uso podia ser exercitado sem um processo que já tivesse parseado algo**.

## Decisão

**A árvore passa a ser um valor.** O parse devolve `(people, families, graph, child_to_family)`; todas as funções do núcleo recebem `arvore` como **primeiro parâmetro**; e o módulo de estado é **apagado**.

Consequências diretas da decisão, todas implementadas no ciclo:

1. `parsers.gedcom_parser.carregar_arvore` devolve a árvore (transição feita em `c6ae2d7`).
2. `get_name` e `ref_id` saem do módulo de estado para `core/registro.py`, porque **não eram estado** — eram leitura de registro (`3d109b0`).
3. As dependências de borda (leitura de CSV e emissão de diagrama) passam a ser **injetadas** por parâmetro, e não importadas pelo núcleo (`ccd4bba`).
4. `core/gedcom_state.py` é **removido** no `fd60f22`, junto com o `xfail` da guarda estrutural que o vigiava.

## Evidência

- `src/core/gedcom_state.py` **não existe**. Confirmado por listagem do diretório: os arquivos de `src/core/` são `cm_estimator`, `diagram_domain`, `dna_analysis`, `documentary_relationship`, `erros`, `evidence_comparison`, `family_navigation`, `genetic_evidence`, `matching`, `name_normalization`, `path_finding`, `path_search`, `registro`, `relationship_hypotheses`.
- Todas as assinaturas do núcleo recebem `arvore` primeiro: `dna_analysis(…, arvore)`, `path_search(…, arvore)`, `build_ged_indexes(arvore)`, `match_candidates(arvore, …)`, `documentary_relationship(arvore, …)`, `find_ancestral_path(arvore, …)`, `find_indirect_path(arvore, …)`, `get_parents(arvore, …)`, `get_spouses(arvore, …)`, `resolvedor_de_diagrama(arvore)`.
- `core/registro.py` existe com 33 linhas úteis e **dois** símbolos: `ref_id` e `get_name`.
- **Não há nenhuma variável de módulo mutável no núcleo.** O único cache de módulo que sobrou é `_INDICE_DE_NOMES`, em `documentary_relationship.py` — e ele é **derivado** do conteúdo recebido, não escrito pelo parse.

## Justificativa

Dependência explícita em vez de ambiente implícito. A motivação operacional está registrada no commit `405f5a1`: **a árvore por requisição** passou a ser o motivo que resta para a guarda de instância única, porque a árvore já não é compartilhada entre requisições. Um núcleo que recebe o que consome pode ser exercitado por qualquer chamador — inclusive um teste, sem servidor.

## Consequências

- 🟢 **A contaminação entre requisições concorrentes deixou de existir estruturalmente** (`L-16` do `domain.md`, `M-03` do `state-machines.md`). A guarda de instância única **permanece**, mas por outro motivo: o armazenamento em disco continua único por processo.
- 🟢 **O cache de nomes teve de inventar outra chave de invalidação.** Como não há mais contador `versao`, `_chave_de` passou a derivar de `(len(people), primeira chave, última chave)`. **É dessa necessidade que nasce a lacuna `L-24`** — a chave pode colidir entre duas árvores de mesmo tamanho. A decisão de remover o estado **criou** essa lacuna, e ela está aberta.
- 🟡 **O `dono` deixou de ter onde ancorar naturalmente**, o que motivou o `ADR-26`.
- 🟢 **O import tardio do grafo desapareceu.** O `path_finding` lia `graph` de dentro da função porque ele era reatribuído; hoje ele vem da árvore recebida.
- 🟢 **O reexport do `cm_estimator` foi removido no mesmo ciclo** (`c6a7e72`), com os consumidores migrados para o módulo canônico — a primeira das remoções de superfície de compatibilidade que o `ADR-34` consolida.
