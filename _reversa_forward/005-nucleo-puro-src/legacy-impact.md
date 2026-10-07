# Legacy Impact: núcleo puro em `src/core/`

> Identificador da feature: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Rodada: **parcial** — Fase 1 (Preparação), ações `T001` a `T004`
>
> ⚠️ **Este arquivo tem DUAS rodadas.** A rodada 1 foi escrita por
> `/reversa-coding` ao fim de `T001`–`T004` e descreve **apenas o instrumento de
> paridade**. A **rodada 2**, ao final do arquivo, registra a execução de `T009` a
> `T029` — que é a entrega propriamente dita e **muda o mecanismo de integração do
> sistema**. Quem lê o delta desta feature precisa ler as duas: a rodada 1 sozinha
> afirma que "nenhuma regra de negócio foi modificada", o que era verdade para ela e
> **deixou de ser** para a feature.

## Rodada 1 — Fase 1 (Preparação), `T001` a `T004`

### Escopo da rodada 1

Esta rodada **não tocou código de produto**. Ela instrumentou o harness diferencial (dois probes novos) e registrou a linha de base. `src/` está exatamente como estava: nenhuma regra de negócio foi criada, alterada ou removida.

## Arquivo afetado | Componente | Tipo | Severidade | Justificativa

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `_reversa_sdd/parity/harness.py` | instrumento de paridade (`_reversa_sdd/migration/parity_harness.md`) | contrato-alterado | MEDIUM | Os dois coletores passam a receber o diretório de CSVs de DNA como argumento posicional, e o harness ganha `--dna`. O probe de aceitação só é possível por essa porta. Também corrigido o caminho do `--gedcom` para absoluto, porque o coletor faz `chdir` antes de usar o caminho |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | componente-alterado | MEDIUM | Dois probes novos: `dna` (análise pela rota, nas 7 fixtures de CSV) e `decomposicao` (`are_spouses` para todos os pares + `split_path_by_marriage` para todo par com caminho indireto) |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | regra-nova | HIGH | Classificação do desfecho por **modo** (`ok`, `erro`, `raiz_ausente`, `arquivo_ausente`, `sem_arquivo`, `outro`) em vez de comparação de texto de mensagem. Sem isso, todo caso de erro acusaria divergência de redação |
| `_reversa_forward/005-nucleo-puro-src/evidence/` | — | componente-novo | LOW | Evidência da linha de base: suíte, paridade e procedência do oráculo |

## Diff conceitual por componente

### `harness.py` — o probe de aceitação não podia ser o que a `T001` descrevia

A ação pedia comparar `build_ged_indexes` e `match_candidates` nos dois lados. **No oráculo essas funções não existem.** Verificado por varredura das definições: as 16 funções do oráculo são `get_name`, `strip_bad_utf`, `norm_name`, `drop_short_tokens`, `surname_core_tokens`, `split_name_pt`, `surnames_set`, `top_given_tokens`, `token_prefixes`, `demojibake`, `get_relationships_by_cm`, `load_gedcom_and_build_graph`, `are_spouses`, `split_path_by_marriage`, `find_indirect_path` e `find_ancestral_path`.

A decisão de aceitação do legado está **inline** dentro da rota `POST /`, entre `app_legacy_e43ca22.py:695` (`best_score = best_g = -1`) e `:796` (a mensagem com `given`, `final`, `inter`, `jacc`). Transcrever aquele bloco para o coletor criaria uma segunda implementação para comparar com a primeira — exatamente a validação circular que o RISK-002 existe para prevenir.

**Solução implementada, por decisão explícita do usuário em 2026-10-06:** os dois lados executam a análise de DNA **pela rota**, com o mesmo GEDCOM e o mesmo CSV, e o probe intercepta `render_template` para capturar o contexto de domínio — `dna_results`, `skipped_matches` e a mensagem — **sem renderizar HTML**. É compatível com a regra do `parity_specs.md` ("asserir sobre comportamento de domínio, nunca sobre HTML") e não depende de `src/templates/index.html` nem do template legado, cuja deriva está registrada como não reconciliada.

### `harness.py` — a limitação que o probe carrega

O campo `motivo` do legado funde **duas causas distintas**:

| Causa | Mensagem |
|---|---|
| Recusado pelas regras de aceitação | `score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…, jacc=…)` |
| **Aceito** mas sem caminho | `sem caminho subindo por pais (pais ausentes no GED?)` |

O candidato mantém a mesma fusão. Portanto o probe **não isola** as regras A/B/C/D da busca de caminho. O que ele prova é o **resultado observável da análise inteira**, o que fecha a lacuna nº 1 do `parity_harness.md` — mas **não** é o probe cirúrgico que a `RF-10` descrevia, e isso está declarado no artefato de evidência.

### Correções necessárias ao próprio probe

Cinco defeitos do probe foram encontrados e corrigidos **antes** da medição final. Registrados porque três deles são armadilhas que voltariam a morder:

1. **Caminho relativo do `--gedcom`** quebrava, porque o coletor faz `chdir` antes de usar o caminho. Corrigido com `os.path.abspath`.
2. **O candidato deriva o nome do arquivo GEDCOM do conteúdo** (`chave_de_armazenamento`, BUG-QMLY), e o formulário devolve esse nome no POST seguinte. Reenviar o nome original fazia o candidato responder `Arquivo 'probe.ged' não existe mais` — erro de encanamento do probe, não divergência de domínio. Corrigido fazendo o que o navegador faz: sobe, lê o nome devolvido e usa o nome devolvido.
3. **`relacoes` não existe no resultado do candidato.** O oráculo passa `relationships` como string pronta; o candidato passa `hypotheses` em estrutura. Comparar produziria divergência de forma, não de conteúdo. Campo removido da comparação.
4. **cM agregado diverge por desenho.** Medido em `cm_boundaries.csv` sobre `basic.ged`: o legado soma os 6 segmentos de `Ana Silva` (3.760); o candidato agrupa por kit. Comparar esses números acusaria divergência onde não há. O cM **não** é comparado; caminho, nome e contagens são.
5. **`"não encontrada"` é substring de `"não encontradas"`.** O erro de colunas do CSV (`Colunas de Nome e cM não encontradas`) era classificado como raiz ausente. Corrigido com padrão específico (`seu nome.*não foi encontrad`), e não por substring.

## Preservadas

Todas as regras 🟢 de `_reversa_sdd/domain.md` continuam intactas. As que importam para esta feature, e que a linha de base confirma:

| Regra | Situação |
|---|---|
| BR-D-44 a BR-D-53 — matching exato, score difuso, filtro anti-falso-positivo, Jaccard adaptativo e os cinco ramos de aceitação | **Intactas.** O probe novo exercita a cadeia inteira e não achou divergência |
| BR-D-15 — o cM acumulado não é arredondado | **Intacta.** Nenhum código de produto foi tocado |
| BR-C-04 a BR-C-08 — BFS bidirecional com teto de 20, caminho indireto com teto de 40, import do grafo dentro da função | **Intactas.** Os 1.600 pares por fixture seguem em paridade |
| BR-C-22 — o índice nome→ids é reconstruído quando `versao` muda | **Intacta.** Nenhum código de produto foi tocado |
| BR-MIGRAR-020/021 — as 9 faixas de cM se sobrepõem; cM ≤ 0 devolve lista vazia | **Intactas.** Os 40 valores de cM seguem em paridade |
| `are_spouses` / `split_path_by_marriage` — decomposição do caminho (RISK-011) | **Intactas e agora medidas.** Passaram a ter probe dedicado, o que não tinham |

## Modificadas

**Nenhuma regra de negócio foi modificada, removida ou criada nesta rodada.** A alteração é toda em instrumento de verificação (`harness.py`), que não é runtime do sistema — o `architecture.md` já declara `_reversa_sdd/oracle/`, `parity/`, `screens/` e `migration/` como instrumentação **fora do escopo do sistema em runtime**.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |

---
---

## Rodada 2 — Integração e Polimento, `T009` a `T029` ⚠️ **ESTA É A ENTREGA DA FEATURE**

> Data: `2026-10-07`
> A rodada 1 instrumentou o harness; esta rodada **removeu o estado global do
> sistema**. Escrita retroativamente pelo `/reversa-sync`, porque a rodada 1 não foi
> atualizada quando o `/reversa-coding` fechou as ações.

### Escopo da rodada 2

`src/` **mudou**. O `T023` apagou `src/core/gedcom_state.py` e tirou a escrita das
globais de `carregar_arvore`; o `T022` removeu a superfície de compatibilidade de
`dna_analysis`; os `T011` a `T021` migraram cada consumidor para a árvore por
parâmetro. **Nenhum resultado de domínio mudou** — a paridade continua 100% nas 6
fixtures e a suíte passou de `164 passed` para `178 passed` sem remover teste de
produto. O que mudou é **como as camadas se integram**.

### Arquivo afetado | Componente | Tipo | Severidade | Justificativa (rodada 2)

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/gedcom_state.py` | estado do GEDCOM (`architecture.md#1`) | **componente-extinto** | HIGH | O módulo foi **apagado**. Continha `people`, `families`, `graph`, `child_to_family` e o contador `versao`. `get_name` e `ref_id` sobrevivem em `src/core/registro.py` (`T008`), sem estado |
| `src/parsers/gedcom_parser.py` | leitura do GEDCOM (`architecture.md#1`) | **regra-alterada** | HIGH | `carregar_arvore` **devolve** a árvore como valor e **não escreve mais** as globais. A assimetria de substituição que o `architecture.md#1` documenta (dicionários mutados *in place*, grafo reatribuído) **deixa de existir**: não há mais nada a substituir |
| `src/core/` (12 módulos) | contrato de assinatura do núcleo (`architecture.md#3`) | **delta-de-contrato-externo** | HIGH | Toda função pública que precisava da árvore passa a recebê-la como **primeiro parâmetro** (`T011`–`T014`). As exceções são as que operam sobre lista de ids e não a usam (`split_path_by_marriage`, `exclude_tail`) |
| `src/core/documentary_relationship.py` | cache de índice de nomes (`erd-complete.md`, `ESTADO_VERSAO`) | **regra-alterada** | MEDIUM | `versao` não existe mais. A invalidação de `_INDICE_DE_NOMES` passa a ser derivada do **conteúdo** de `people` (`_chave_de`), e a identidade do dicionário é explicitamente rejeitada como chave — `id()` é reciclado e o defeito apareceria só sob carga |
| `src/core/dna_analysis.py` | superfície de compatibilidade (`architecture.md#7`, dívida #17 e #18) | **regra-removida** | LOW | Saíram o import e as entradas `get_relationships_by_cm` e `SHARED_CM_DATA` de `__all__`. Medido: o módulo **não referenciava** nenhum dos dois no corpo. `cm_estimator.py` **permanece em disco** |
| `src/core/path_search.py` | superfície de compatibilidade (dívida #17) | **regra-removida** | LOW | O bloco de reexportação de 17 nomes já havia saído na OPP-20261006-ESKO; esta rodada removeu o comentário morto que ainda descrevia o mecanismo |
| `src/app.py` | guarda de instância única (`RN-05`) | **regra-alterada** | LOW | A justificativa da guarda **muda de motivo**: era o estado global em memória, que faria duas instâncias divergirem; agora é o diretório `src/uploads/` compartilhado e o fato de requisições do mesmo operador caírem em instâncias diferentes. **A guarda permanece** — só o motivo foi reescrito |
| `README.md` | documentação de operação | **delta-de-contrato-externo** | MEDIUM | Quatro passagens afirmavam que o estado do GEDCOM vive em globais compartilhadas entre threads. Agora afirmam que a árvore existe **por requisição** e é passada por parâmetro |
| `tests/` (8 arquivos + 2 módulos novos) | encanamento dos testes | **regra-alterada** | MEDIUM | Os fixtures passaram a ler a árvore pelo **retorno** do parse. Isto **não** é detalhe de teste: é o que permitiu remover o estado sem quebrar a suíte, e o que revelou que a guarda `atual()` tinha de ser estrita |
| `_reversa_sdd/parity/harness.py` | instrumento de paridade | **contrato-alterado** | HIGH | O coletor do candidato lia `GS` (o módulo de estado) e passou a desempacar a árvore devolvida. **Absorve o `T010`**, que estava adiado justamente para este momento |

### Diff conceitual por componente (rodada 2)

### `gedcom_state.py` — o que saiu, e o que ficou no lugar

O módulo era o **hub de dependência** do sistema: o `architecture.md#3` o registra
com 8 dependentes diretos. Ele não foi substituído por outro módulo; foi
**substituído por um parâmetro**. A árvore é uma tupla de quatro estruturas —
`(people, families, graph, child_to_family)` — que o parse devolve e o chamador
repassa. A forma dos dados **não mudou** (ver `data-delta.md` §2): o que mudou é
quem as possui.

`get_name` e `ref_id` foram para `src/core/registro.py` no `T008`. Eles nunca
foram estado — são leitura de registro — e a `get_name` é cópia literal do
oráculo, o ativo de paridade mais delicado do núcleo.

### `architecture.md#1` — o mecanismo de integração deixou de ser estado global

O §1 afirma: *"O mecanismo de integração entre as camadas é estado global mutável,
e não injeção de dependência."* **Isso deixou de ser verdade.** A tabela das duas
assimetrias deliberadas (`clear()`+`update()` para os dicionários, reatribuição
para o `graph`, e o contador `versao`) descreve um mecanismo que não existe mais:
não há global a mutar nem a reatribuir, e o `versao` foi removido com o módulo.

### `architecture.md#7` — duas dívidas fecham, uma muda de mecanismo

| Dívida | Situação após esta feature |
|---|---|
| #17 — superfícies de compatibilidade | ✅ **FECHADA.** `path_search.__all__` já declarava só `path_search`; `dna_analysis.__all__` perdeu os dois nomes de `cm_estimator` |
| #18 — `cm_estimator` como legado reexportado | ⚠️ **PARCIAL.** O módulo permanece em disco (a ação manda mantê-lo), mas **deixou de ser reexportado** e nenhum teste de produção o alcança pela fachada |
| #3 — contaminação entre requisições concorrentes | ⚠️ **MECANISMO ALTERADO, DÍVIDA ABERTA.** O vetor "estado global reescrito por requisição + 4 threads" **deixa de existir**: cada requisição monta a própria árvore. A guarda de instância única continua sendo de processo, não de thread, e a dívida permanece como dívida de **thread-safety geral** — não mais de estado de domínio compartilhado |
| #5 — ciclos de pacote | ❌ **INALTERADA.** `core/` ↔ `reporting/` e `core/` ↔ `parsers/` continuam. Esta feature removeu o **estado**, não o ciclo: `reporting/mermaid_render.py` segue recebendo a árvore por parâmetro via resolvedor injetado |

> **Não inventamos dívida nova.** A remoção do estado não introduziu ciclo nem
> dependência nova; o `src/core/` inclusive **perdeu** duas dependências (o módulo
> de estado e o import de `cm_estimator`).

### `erd-complete.md` — `ESTADO_VERSAO` deixa de existir

O ERD documenta 21 estruturas em memória e lista `ESTADO_VERSAO` como a **quinta**
entidade, com a relação "`ESTADO_VERSAO` → índices derivados (1..N) ... existe
porque `id()` não muda com mutação *in place*". A entidade **não existe mais**, e
a razão que a justificava também não. As entidades 1 a 4 (`PESSOA`, `FAMILIA`,
`GRAFO_BIPARTIDO`, `CHILD_TO_FAMILY`) **permanecem**, com a mesma forma, mudando
apenas o local: de `gedcom_state.*` para o valor devolvido pelo parse.

### `domain.md` §5.2 — o local do fallback `"Sem Nome"` mudou

A tabela de mensagens de contrato do núcleo aponta `"Sem Nome"` para
`gedcom_state.py:43`, `:52`. O literal **não mudou** e continua sendo contrato
(DIV-001: formato vazio devolve `''`, e `"Sem Nome"` só aparece quando não há
`name`). Só o **arquivo** mudou: agora é `src/core/registro.py`.

### Modificadas — o que a rodada 2 mudou

**Nenhuma regra de negócio 🟢 foi alterada, removida ou criada.** O que mudou é o
**mecanismo de integração** e as **assinaturas**, exatamente como a `RN-02` e a
`RN-03` do `requirements.md` §4 previram e autorizaram. A `RN-01` — nenhum
limiar, peso, ordem de avaliação ou critério do matching e do caminho é alterado —
foi verificada por medição, não por inspeção:

| Verificação | Resultado |
|---|---|
| Paridade diferencial contra o oráculo congelado | `100%` nas 6 fixtures, exit 0 |
| Suíte | `178 passed, 0 xfailed, 15 errors` (linha de base: `164 passed, 15 errors`; os 15 erros são de ambiente e pré-existentes) |
| Verificação manual de ponta a ponta | `APROVADO` — `waitress`, `HTTP 200`, upload, DNA e caminho |
| Guardas estruturais do núcleo | 4 de 4 verdes, provadas **nos dois sentidos** (`T024`) |

### Preservadas — verificado por medição

| Regra | Situação |
|---|---|
| BR-D-44 a BR-D-53 — matching exato, score difuso, anti-falso-positivo, Jaccard e os cinco ramos de aceitação | **Intactas.** O probe `dna` exercita a cadeia inteira e não achou divergência |
| BR-C-04 a BR-C-08 — BFS bidirecional com teto de 20, caminho indireto com teto de 40 | **Intactas.** Os 1.600 pares por fixture seguem em paridade |
| BR-D-15 — o cM acumulado não é arredondado | **Intacta.** Nenhum código de produto foi tocado |
| BR-MIGRAR-020/021 — as 9 faixas de cM se sobrepõem; cM ≤ 0 devolve lista vazia | **Intactas.** Medido na verificação manual: `0` e `-5` devolvem `[]`, `99999` devolve o literal |
| BR-C-22 — o índice nome→ids é invalidado quando a árvore muda | **Preservada com mecanismo novo.** Antes por contador `versao`; agora por conteúdo recebido (`RN-03`) |
| `are_spouses` / `split_path_by_marriage` — decomposição do caminho (RISK-011) | **Intactas** e com probe dedicado desde a rodada 1 |
| Ordem de inserção de `people` e das arestas do grafo (tag `@ordem`) | **Intacta.** É contrato de paridade: a ordem decide qual ID o "primeiro ID" escolhe e qual caminho o `shortest_path` devolve |

## Arquivos de observação que esta rodada corrigiu em texto, não em código

`T027` e `T028` corrigiram **quatro** passagens que afirmavam o estado global
(três no `README.md`, uma no comentário da guarda de exclusividade em `app.py`) e
as docstrings de `family_navigation.py`, `path_finding.py`, `diagram_domain.py`,
`documentary_relationship.py`, `text_cleaning.py` e `registro.py`. Uma delas era
**perigosa e não cosmética**: um comentário em `documentary_relationship.py`
recomendava voltar a usar `id()` como chave do cache "quando o `T023` removesse o
estado". Seguir essa recomendação introduziria um defeito de produção — `id()` é
reciclado — e a nota foi substituída pela explicação de por que **não** fazer isso.

### Histórico de alterações (rodada 2)

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-coding` na execução de `T001` a `T004` (rodada parcial, Fase 1) | reversa |
| 2026-10-07 | **Rodada 2** acrescentada retroativamente pelo `/reversa-sync`: delta de `T009` a `T029`, com a remoção do estado global, o `componente-extinto` `gedcom_state.py`, as dívidas #17/#18/#3 e o efeito em `architecture.md`, `erd-complete.md` e `domain.md` | reversa |
