# Adendo: núcleo puro em `src/core/` (Onda 1 do cutover)

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-07`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-07.

## Resumo da entrega

A Onda 1 do `cutover_plan.md` exigia um núcleo de funções puras, sem estado global,
para que a paridade do matching fosse isolável e provada. A entrega **removeu o
estado global do sistema**: `src/core/gedcom_state.py` foi apagado, `carregar_arvore`
passou a **devolver** a árvore como valor em vez de escrever as globais, e todas as
funções do núcleo que precisavam da árvore passaram a recebê-la como primeiro
parâmetro. `get_name` e `ref_id`, que nunca foram estado, sobrevivem em
`src/core/registro.py`. O `src/core/` deixou de importar `parsers/` e `reporting/`,
o `app.py` monta as dependências de borda e as injeta, e a superfície de
compatibilidade reexportada por `dna_analysis` e `path_search` foi removida.

**Nenhum resultado de domínio mudou.** Nenhum limiar, peso, ordem de avaliação ou
critério do matching e do caminho foi alterado (`RN-01`), e isso foi verificado por
medição, não por inspeção.

**Progresso: 30 de 30 ações concluídas**, nenhuma aberta em `actions.md`.

| Prova | Resultado |
|---|---|
| Paridade diferencial contra o oráculo congelado | **100 %** nas 6 fixtures, exit 0 |
| Suíte | **178 aprovados, 0 falhas esperadas, 15 erros de ambiente** |
| Linha de base (`T004`) | 164 aprovados e os mesmos 15 erros |
| Verificação manual de ponta a ponta | **APROVADO** — `waitress`, `HTTP 200`, upload, DNA e busca de caminho |
| Guardas estruturais do núcleo | 4 de 4 verdes, e provadas **nos dois sentidos** |

A diferença de 14 aprovados é integralmente verificações novas — 8 em
`test_dependencias_nucleo.py` e 5 em `test_arvore_devolvida.py`, mais a mudança de
estado da guarda de `xfail` para aprovado — e **nenhum teste de produto foi
removido**. O único teste retirado foi
`test_transicao_ainda_atualiza_o_estado_global`, cujo próprio docstring mandava
removê-lo, e não consertá-lo, quando a condição que ele media deixasse de valer.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#1` (Visão Geral da Arquitetura) | `regra-removida` | O §1 afirma que "o mecanismo de integração entre as camadas é estado global mutável, e não injeção de dependência". **Deixou de ser verdade.** Leia como: o mecanismo é a **árvore passada por parâmetro**, e a borda injeta as dependências de I/O. A tabela das duas assimetrias deliberadas (`clear()`+`update()` nos dicionários, reatribuição do `graph`, contador `versao`) descreve um mecanismo que não existe mais |
| `_reversa_sdd/architecture.md` | `#1` (tabela de camadas) | `componente-extinto` | `core/gedcom_state.py` **não existe mais**; o núcleo perdeu um módulo e a contagem de `core/` caiu de 12 para 11. A contagem de linhas do `src/` também caiu — mas **este adendo não reconcilia os números do §1**, que já estavam defasados antes desta feature (ver "Lacunas declaradas") |
| `_reversa_sdd/architecture.md` | `#2` (Containers), concorrência | `regra-alterada` | A nota de concorrência diz que "o estado do GEDCOM é global de processo". Não é mais. A exclusividade de instância continua sendo de **processo, não de thread**, mas o vetor de contaminação por estado de domínio compartilhado **deixou de existir** — cada requisição monta a própria árvore |
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `delta-de-contrato-externo` | O contrato de assinatura do núcleo mudou: toda função pública que precisa da árvore a recebe como **primeiro parâmetro**. As exceções são as que operam sobre lista de ids e não a usam (`split_path_by_marriage`, `exclude_tail`) — a assinatura é explícita, não uniforme |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas Técnicas), dívida #17 | `regra-removida` | ✅ **FECHADA.** As superfícies de compatibilidade de `path_search.__all__` e `dna_analysis.__all__` não existem mais |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas Técnicas), dívida #18 | `regra-alterada` | ⚠️ **PARCIAL.** `cm_estimator.py` **permanece em disco** por decisão explícita da ação, mas **deixou de ser reexportado** por `dna_analysis` e nenhum teste o alcança pela fachada. Não leia como "foi removido" |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas Técnicas), dívida #3 | `regra-alterada` | ⚠️ **A DÍVIDA NÃO ESTÁ FECHADA.** O vetor "estado global reescrito por requisição + 4 threads" deixou de existir, mas a guarda de instância única continua sendo de processo, não de thread. O que saiu foi o estado de domínio compartilhado; thread-safety geral segue aberta (lacuna `L-16` / `M-03`) |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas Técnicas), dívida #5 | `presença` | ❌ **INALTERADA.** Os ciclos `core/` ↔ `reporting/` e `core/` ↔ `parsers/` continuam idênticos. Esta feature removeu o **estado**, não o ciclo |
| `_reversa_sdd/erd-complete.md` | diagrama de memória do processo e tabela de entidades | `componente-extinto` | A entidade `ESTADO_VERSAO` (a **quinta** do inventário) **não existe mais**, e a razão que a justificava também não. Leia as entidades 1 a 4 (`PESSOA`, `FAMILIA`, `GRAFO_BIPARTIDO`, `CHILD_TO_FAMILY`) como **inalteradas na forma**, mudando apenas o local: do módulo `gedcom_state` para o valor devolvido pelo parse |
| `_reversa_sdd/erd-complete.md` | relação `ESTADO_VERSAO` → índices derivados | `regra-alterada` | O §5 do `data-delta.md` da feature e o `documentary_relationship.py` passam a invalidar o índice de nomes pelo **conteúdo** de `people`, nunca por identidade. **`id()` é explicitamente rejeitado como chave** — ele é reciclado, e o defeito apareceria só sob carga |
| `_reversa_sdd/domain.md` | `#5.2` (Contrato de Mensagens, Núcleo) | `regra-alterada` | A linha do literal `"Sem Nome"` aponta `gedcom_state.py:43`, `:52`. O literal **não mudou** e continua sendo contrato (só aparece quando não há `name`; formato vazio devolve `''`, DIV-001). Mudou o **arquivo**: agora é `src/core/registro.py` |
| `_reversa_sdd/domain.md` | `#3` e `#4` (Regras de Domínio) | `presença` | **Nenhuma regra de negócio foi criada, alterada ou removida.** É a `RN-01` da feature, e a paridade em 100 % nas 6 fixtures a sustenta. Esta é a linha mais importante desta tabela: o delta desta entrega é **mecanismo**, não comportamento |
| `_reversa_sdd/c4-components.md` | `core/`, entradas que citam `gedcom_state` | `componente-extinto` | O componente `gedcom_state.py` sai do inventário; `get_name` e `ref_id` passam a pertencer a `core/registro.py`, que é **módulo puro** — não lê nem escreve estado, não faz I/O e não importa framework |
| `_reversa_sdd/architecture.md` | `#1` (mecanismo de integração), leitura de operação | `delta-de-contrato-externo` | `README.md` e o comentário da guarda de exclusividade em `app.py` foram corrigidos: a árvore existe **por requisição**, e a guarda de instância única passou a ser justificada pelo diretório `src/uploads/` compartilhado e pelo roteamento entre instâncias — **não** por divergência de estado em memória |

> **Nota sobre `erd-complete.md` e `c4-components.md`.** Nenhum dos dois é citado no
> `requirements.md` da feature, e ambos foram incluídos aqui por varredura: os dois
> afirmam o módulo de estado e a entidade `versao` como estado atual do sistema.
> Um adendo que os omitisse deixaria a extração mentindo nesses dois pontos.

## O que a extração **não** precisa mudar

Esta é a parte que costuma ser esquecida num adendo, e aqui ela é grande — porque a
feature foi desenhada para não mudar comportamento:

- **As regras de negócio.** `BR-D-44` a `BR-D-53` (matching, score difuso,
  anti-falso-positivo, Jaccard adaptativo e os cinco ramos de aceitação),
  `BR-D-15` (o cM acumulado não é arredondado), `BR-C-04` a `BR-C-08` (BFS
  bidirecional com teto de 20, caminho indireto com teto de 40) e
  `BR-MIGRAR-020/021` (as 9 faixas de cM se sobrepõem; cM ≤ 0 devolve lista vazia)
  estão **intactas**.
- **A ordem de inserção** de `people` e das arestas do grafo (tag `@ordem`) segue
  sendo contrato de paridade. A estrutura não foi trocada por nenhuma cujo percurso
  não preserve a ordem.
- **A forma dos dados** não mudou: nenhum campo acrescentado, removido, renomeado ou
  retipado. O grafo continua `nx.Graph` não direcionado e **sem tipo de aresta** —
  filiação e casamento continuam sendo a mesma aresta.
- **A superfície HTTP** não mudou: mesmas rotas, mesmos campos de formulário,
  mesmas mensagens de contrato.
- **O contrato de mensagens do núcleo** (`domain.md` §5.2) permanece literal, com a
  única correção de **arquivo** anotada acima.

## Regras sob vigilância

`W001`, `W002`, `W003` e `W004`, definidos em
`_reversa_forward/005-nucleo-puro-src/regression-watch.md`.

| Item | Cobre | Origem |
|---|---|---|
| `W001` | O harness executa o oráculo **congelado** (`_reversa_sdd/oracle/app_legacy_e43ca22.py`) e o candidato `src/`; os coletores recebem o diretório de CSVs | Rodada 1 (`T001`–`T004`) |
| `W002` | **A árvore é valor, não estado**: nenhum módulo de `src/core/` declara `people`/`families`/`graph`/`child_to_family`/`versao`, e `carregar_arvore` não escreve globais | Rodada 2 (`T009`–`T029`) |
| `W003` | **A dívida #3 não está fechada** — a guarda de exclusividade é de processo, não de thread | Rodada 2 |
| `W004` | **`ESTADO_VERSAO` não existe** e `id()` nunca é chave de cache | Rodada 2 |

**Dois itens merecem leitura explícita.** O `W003` existe para impedir que esta
feature seja citada como tendo resolvido a contaminação entre requisições
concorrentes: ela removeu **um** dos vetores, não a dívida. O `W004` guarda um
defeito que **não aparece em teste isolado** — se o cache voltar a ser chaveado por
identidade, ele devolve o mapa de outro GEDCOM apenas sob carga.

## Alerta: a fonte principal indicada pelo skill estava defasada, e foi corrigida

O `/reversa-sync` designa `_reversa_forward/<feature>/legacy-impact.md` como **fonte
principal do delta**. Nesta feature essa fonte estava **congelada na Fase 1**: tinha
um único commit (o de abertura do ciclo), declarava-se `Rodada: parcial — ações
T001 a T004`, e afirmava que "nenhuma regra de negócio foi modificada, removida ou
criada nesta rodada" e que a rodada "não tocou código de produto".

Isso era verdade quando foi escrito, e **deixou de ser**: o `T023` apagou o módulo
de estado, o `T022` removeu a superfície de compatibilidade e os `T011` a `T021`
migraram cada consumidor. Nem o `legacy-impact.md` nem o `regression-watch.md`
foram atualizados quando o `/reversa-coding` fechou as ações, e o `data-delta.md`
registra uma correção de 2026-10-06 mas também é anterior à execução.

Se o adendo tivesse sido gerado só a partir daquele texto, ele sairia **verdadeiro e
inútil**: uma tabela de impacto sobre o instrumento de paridade, sem uma linha sobre
a mudança central da feature.

**Providência tomada, por decisão explícita do usuário em 2026-10-07.** Como o
`/reversa-sync` escreve apenas em `_reversa_sdd/addenda/` e trata os artefatos da
feature como somente leitura, o bloqueio foi levado ao usuário, que escolheu
corrigir a fonte. Foram acrescentadas, **sem alterar uma linha das rodadas
originais**:

| Arquivo | O que foi acrescentado |
|---|---|
| `_reversa_forward/005-nucleo-puro-src/legacy-impact.md` | Seção **"Rodada 2 — Integração e Polimento, `T009` a `T029`"**, com a tabela de impacto da entrega real, o diff conceitual, as regras preservadas e o efeito nas dívidas #17, #18 e #3 |
| `_reversa_forward/005-nucleo-puro-src/regression-watch.md` | `W002`, `W003` e `W004`, mais `OBS-07` a `OBS-10` |

Ambos os arquivos receberam, no topo, um aviso de que **têm duas rodadas** e que a
rodada 1 sozinha afirma algo que deixou de valer para a feature. Esta é a diferença
em relação ao adendo da feature `004`, onde o sync apenas registrou a defasagem e
não a corrigiu.

**Distinção que importa para quem reimplementar:** o `legacy-impact.md` vale, sim,
como leitura — mas a leitura correta é `requirements.md` §4 (as `RN-01` a `RN-04` e
as decisões de 2026-10-06), depois `actions.md` e o `progress.jsonl`, e só então o
`legacy-impact.md`. O `legacy-impact.md` registra o que cada rodada entregou; ele
**não** é mais a fonte única do delta.

## Lacunas declaradas

Nem tudo neste adendo é uma afirmação verificada. O que segue é limite de
conhecimento, e não omissão:

1. **As contagens de linha do `architecture.md#1` já estavam defasadas antes desta
   feature.** O §1 diz `app.py` com 267 linhas e o núcleo com 3.489; as medições da
   extração de 2026-10-05 registram 262 e 3.473 para `src/`. Esta feature **reduziu**
   as duas contagens (um módulo apagado, imports removidos), mas o valor exato não
   foi reconciliado aqui, porque reconciliar número defasado de origem alheia à
   feature misturaria duas causas num mesmo delta.
2. **O probe `dna` do harness não isola as regras A/B/C/D da busca de caminho.**
   O campo `motivo` do legado funde "recusado pelas regras de aceitação" com "aceito
   mas sem caminho". A paridade em 100 % prova o **resultado observável da análise
   inteira**; ela **não** prova as cinco ramificações de aceitação isoladamente. Se
   isso virar exigência, exige instrumentar a rota do oráculo — trabalho novo, fora
   do escopo desta feature (`OBS-01`).
3. **Uma inconsistência em `documentary_relationship.py` não foi resolvida.**
   Comparando código e documentação, o método de atualização do cache mantém uma
   variável de nível de módulo — o que é estado mutável de módulo, embora não use
   nenhum dos cinco nomes que a guarda de `RF-01` procura. O `requirements.md` não
   pediu a remoção desse cache, e ele foi preservado de propósito por ser
   conteúdo-derivado e não apresentar o defeito que `id()` apresentaria. Registrado
   para que ninguém leia "a guarda passa" como "não há estado algum no núcleo".
4. **A verificação manual deixa resíduo.** Subir o app grava o GEDCOM enviado em
   `src/uploads/`, e o `_clean_residue.py` limpa apenas instrumento de paridade —
   ele **não** remove isso (`OBS-10`).

## Fontes

- `_reversa_forward/005-nucleo-puro-src/legacy-impact.md` (fonte principal do delta, **rodadas 1 e 2**)
- `_reversa_forward/005-nucleo-puro-src/regression-watch.md` (`W001` a `W004`, `OBS-01` a `OBS-10`)
- `_reversa_forward/005-nucleo-puro-src/requirements.md` (objetivo e as `RN-01` a `RN-04`)
- `_reversa_forward/005-nucleo-puro-src/actions.md` (30 de 30 ações concluídas)
- `_reversa_forward/005-nucleo-puro-src/progress.jsonl` (35 eventos)
- `_reversa_forward/005-nucleo-puro-src/data-delta.md` (delta do modelo em memória)
- `_reversa_forward/005-nucleo-puro-src/evidence/T026-medicao-final.md` (suíte e paridade finais)
- `_reversa_forward/005-nucleo-puro-src/evidence/T024-caminho-negativo.md` (guardas provadas nos dois sentidos)
- `_reversa_forward/005-nucleo-puro-src/evidence/T029-verificacao-manual.md` (aceite de ponta a ponta)
- `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`, `_reversa_sdd/erd-complete.md`, `_reversa_sdd/c4-components.md` (conferência de nomes de seção)
