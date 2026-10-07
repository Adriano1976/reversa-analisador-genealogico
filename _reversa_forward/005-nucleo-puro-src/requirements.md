# Requirements: núcleo puro em `src/core/` (Onda 1 do cutover)

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A Onda 1 do `cutover_plan.md` exige um núcleo de funções puras, sem estado global, para que a paridade do matching seja isolável e provada. O `src/core/` atual contém toda a decisão de domínio, mas se comunica por estado global mutável em `core/gedcom_state.py`, e por isso não é executável sobre fixtures sem um processo inteiro por trás. Esta feature retira esse estado sem alterar nenhum resultado: as estruturas passam a ser parâmetros, o núcleo deixa de depender de `parsers/` e `reporting/`, e o harness diferencial comprova 100% de paridade contra o oráculo congelado. Vale para quem mantém o analisador e para quem vai construir a fronteira multiusuário sobre ele.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1` | "O mecanismo de integração entre as camadas é estado global mutável, e não injeção de dependência." `people`, `families`, `child_to_family` por mutação in-place; `graph` por reatribuição, forçando import dentro da função | 🟢 |
| `_reversa_sdd/architecture.md#3` | Os quatro pacotes não formam camadas acíclicas: ciclo `core/ ↔ reporting/` e ciclo `core/ ↔ parsers/` | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida 3 (contaminação entre requisições concorrentes, Alta) e dívida 5 (ciclos de pacote, Média) | 🟢 |
| `_reversa_sdd/code-analysis.md#3.5` | BR-D-44 a BR-D-53: matching exato, score difuso, filtro anti-falso-positivo, Jaccard adaptativo e os cinco ramos de aceitação | 🟢 |
| `_reversa_sdd/code-analysis.md#4.5` | BR-C-04 a BR-C-08: BFS bidirecional com teto de 20 iterações, caminho indireto com teto de 40 arestas, e o import do grafo dentro da função | 🟢 |
| `_reversa_sdd/code-analysis.md#3.5` | BR-D-15: o cM acumulado não é arredondado em nenhum ponto | 🟢 |
| `_reversa_sdd/oracle/ORACLE_MANIFEST.md` | Oráculo congelado `app_legacy_e43ca22.py`, sha256 `44370b23…`, 888 linhas; importá-lo no processo do candidato contaminaria o candidato | 🟢 |
| `_reversa_sdd/migration/parity_harness.md#Resultado` | Paridade de 100% nas 6 fixtures sintéticas e nas árvores reais, com o candidato em `src/` | 🟢 |
| `_reversa_sdd/migration/topology_decision.md#Decisão do usuário` | "Restrição de dependência do núcleo: `core/` não pode importar `fastapi`, `sqlalchemy`, `pydantic` nem `flask`. Violação invalida a Onda 0 e deve ser detectada por teste automático." | 🟢 |
| `_reversa_sdd/migration/paradigm_decision.md#Implicações` | Implicação 1: o estado global vira dependência injetada; a mutação in-place da reconstrução não deve ser transportada | 🟢 |
| `_reversa_sdd/architecture.md#3` | `utils/` é o único pacote folha real; `norm_name` já foi movido para lá (commit `2443273`) e o resolvedor de diagrama já é injetado (commit `87bcea5`) | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Desenvolvedor do analisador | Alterar ou depurar uma regra de matching sem carregar um GEDCOM por um processo inteiro | Monta as estruturas em memória, chama a função de aceitação e vê o veredito e o motivo |
| Mantenedor da migração | Provar que o núcleo novo reproduz o legado | Roda o harness diferencial contra o oráculo congelado e obtém zero divergência |
| Responsável pelo cutover | Fechar o portão da Onda 1 antes de iniciar a Onda 2 | Confere o relatório de paridade e a guarda automática de dependências do núcleo |
| Genealogista (usuário final) | Continuar recebendo os mesmos parentescos, pontuações e relações por cM | Usa a aplicação após a mudança e não percebe diferença de resultado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Nenhum limiar, peso, ordem de avaliação ou critério do matching e do caminho é alterado por esta feature. Nomear constantes não altera valores. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#3.5` (BR-D-44 a BR-D-53) e `#4.5` (BR-C-04 a BR-C-08)
   - Tipo: nova, e é uma regra de preservação — não altera nenhuma regra existente
2. **RN-02:** As estruturas da árvore (`people`, `families`, `graph`, `child_to_family`) deixam de ser variáveis de módulo e passam a ser parâmetros explícitos ou valor de retorno do parse. Toda função do núcleo que hoje lê essas estruturas passa a recebê-las declaradas. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#1`
   - Tipo: alterada — o comportamento observável não muda, o mecanismo de acesso muda
   - **Decisão de 2026-10-06:** a assinatura muda de verdade, e `src/app.py` e os demais chamadores são atualizados junto. A superfície antiga **não** sobrevive como adaptador.
3. **RN-03:** A invalidação de índices derivados deixa de depender do contador de módulo `versao` e passa a ser derivada do valor recebido. 🟡
   - Origem no legado: `_reversa_sdd/code-analysis.md#4.5` (BR-C-22)
   - Tipo: alterada — o efeito (reconstruir o índice quando a árvore muda) é preservado
4. **RN-04:** O núcleo não faz I/O e não lê configuração de ambiente. 🟢
   - Origem no legado: `_reversa_sdd/migration/topology_decision.md#Decisão do usuário`
   - Tipo: nova, restrição de dependência
   - **Decisão de 2026-10-06:** pode importar a biblioteca padrão **e** bibliotecas de terceiros que não fazem I/O — hoje `networkx`, `thefuzz` e `pandas`. O que está proibido é importar framework web, ORM, biblioteca de validação, `parsers/` e `reporting/`.

> **Decisão de 2026-10-06 sobre o parse.** `parsers/gedcom_parser.py` deixa de **escrever** o estado do domínio e passa a **devolver** a árvore como valor. O núcleo recebe esse valor; ele **não** importa o `ged4py` e **não** lê arquivo. A leitura do arquivo permanece na borda.

> **Decisão de 2026-10-06 sobre a superfície de compatibilidade.** Os nomes históricos reexportados por `src/core/path_search.py` e `src/core/dna_analysis.py` (dívida #17 de `_reversa_sdd/architecture.md#7`) são **removidos**, com todos os chamadores atualizados. É consequência direta da decisão da RN-02: superfície morta preservada esconderia justamente a mudança de assinatura que a feature precisa tornar visível.

> ⚠️ **Conflito com princípio ativo, registrado explicitamente.** O **Princípio IV** de `.reversa/principles.md` diz que "*parentesco biológico e vínculo por casamento nunca são tratados como o mesmo tipo de aresta em cálculo de parentesco, de distância ou de cM esperado*". A `RN-01` desta feature **preserva** o comportamento atual, e o comportamento atual viola esse princípio: `find_indirect_path` percorre o grafo com o caminho mais curto e comprime os nós de família **sem distinguir filiação de casamento**, contando os dois como o mesmo salto. A preservação é deliberada e tem duas razões: (a) é o portão da Onda 1, cuja métrica é paridade exata — corrigir aqui quebraria a paridade e transformaria a entrega em mudança de comportamento; (b) o `paradigm_decision.md` classifica o algoritmo de caminho como **núcleo congelado**, que não pode ser reinterpretado. **Consequência a decidir fora desta feature:** a tipagem das arestas é mudança de comportamento e, pelo Princípio II, percorre o fluxo de requisito como feature própria — não se disfarça de refactor. Esta feature **não** fecha esse conflito; ela o mantém aberto e visível.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O núcleo de matching e de caminho expõe funções puras: recebem a árvore como parâmetro e não leem nem escrevem variável de módulo | Must | Duas chamadas com a mesma entrada, em qualquer ordem, produzem saída idêntica; `src/core/gedcom_state.py` deixa de conter estado mutável. A assinatura nova é aplicada a todos os chamadores, incluindo `src/app.py`, sem adaptador de compatibilidade | 🟢 |
| RF-02 | O grafo é recebido como parâmetro, eliminando o import dentro da função e o acoplamento ao rebind | Must | Nenhum `import` de grafo dentro de corpo de função em `src/core/`; o teste de dependências não encontra o padrão | 🟢 |
| RF-03 | As regras A/B/C/D, o filtro anti-falso-positivo e o Jaccard adaptativo produzem decisão e motivo idênticos aos atuais | Must | Os 16 valores de cM de fronteira e os pares nome/prenome mantêm veredito e motivo, comparados por igualdade exata | 🟢 |
| RF-04 | O caminho ancestral mantém BFS bidirecional, teto de 20 iterações, MRCA e ordem de expansão | Must | Caminho e ancestral idênticos nos pares medidos, inclusive `deep25.ged` | 🟢 |
| RF-05 | O caminho indireto mantém o teto de 40 arestas, a compressão dos nós de família e a ordem das arestas | Must | Caminho idêntico nos pares de `affinity.ged`, com múltiplas afinidades | 🟢 |
| RF-06 | A tabela de cM mantém as 9 faixas sobrepostas, a ordem de avaliação e a lista vazia para cM ≤ 0 | Must | Os 40 valores de cM do harness, incluindo as fronteiras, retornam listas idênticas | 🟢 |
| RF-07 | A agregação do CSV de DNA mantém a chave (nome, kit), a ordem de soma e a ausência de arredondamento | Must | `total_cm` idêntico ao último bit nos CSVs `duplicated` e `cm_boundaries` | 🟢 |
| RF-08 | O núcleo não importa nenhum framework web, ORM ou biblioteca de validação | Must | Teste automático falha se qualquer módulo de `src/core/` importar `flask`, `fastapi`, `sqlalchemy`, `pydantic` ou `waitress` | 🟢 |
| RF-09 | O núcleo deixa de importar `parsers/` e `reporting/` | Should | Nenhum `from parsers` nem `from reporting` dentro de `src/core/`; a leitura de CSV e a emissão de diagrama passam a ser chamadas pela borda. Importar a biblioteca padrão, `networkx`, `thefuzz` e `pandas` é permitido, porque nenhum deles faz I/O | 🟢 |
| RF-10 | A suíte de paridade cobre também as funções de aceitação e a decomposição do caminho | Must | O harness reporta probes de aceitação e de decomposição, e a paridade segue em 100% nas 6 fixtures | 🟡 |
| RF-11 | A suíte de testes existente continua passando, sem teste removido ou desabilitado | Must | Linha de base medida em 2026-10-06: **164 aprovados e 15 erros de ambiente**, que são os **179 itens** do `inventory.md#6`. Os 15 erros são todos de `test_upload_seguranca.py`, em `setup`, por `PermissionError` do sandbox no diretório temporário — nenhum deles é regressão de código | 🟢 |
| RF-12 | A superfície de compatibilidade reexportada por `path_search.py` e `dna_analysis.py` é removida, com os chamadores atualizados | Should | Nenhum nome histórico sem consumidor permanece reexportado; nenhum chamador usa os nomes removidos. Dívida #17 de `_reversa_sdd/architecture.md#7` | 🟢 |
| RF-13 | O parse devolve a árvore como valor, sem escrever estado de domínio | Must | **Ao final da migração**, `parsers/gedcom_parser.py` não muta nem atribui estrutura global; a árvore é o valor de retorno, consumido pelo núcleo como entrada. **Durante a migração a mutação continua de propósito**, pela ordem de execução do `roadmap.md#8` — o critério só é exigível no estado final | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Reprodutibilidade | O núcleo produz a mesma saída sob diferentes sementes de hash do interpretador (`PYTHONHASHSEED`) | `_reversa_sdd/oracle/ORACLE_MANIFEST.md` registra que a ordem de iteração de `set` muda por semente; o desempate do matching precisa ser determinístico | 🟢 |
| Exatidão | A comparação de paridade é por igualdade exata, sem tolerância e sem arredondamento | `_reversa_sdd/migration/parity_specs.md#Critérios` e `#3`, RISK-004 | 🟢 |
| Manutenibilidade | O núcleo é o único lugar com decisão de domínio; `parsers/`, `reporting/` e `utils/` não decidem regra de negócio | `_reversa_sdd/architecture.md#3` | 🟢 |
| Testabilidade | O núcleo é executável sobre estruturas em memória, sem HTTP, sem processo do servidor e sem arquivo em disco | `_reversa_sdd/migration/topology_decision.md#Ganhos concretos esperados` | 🟢 |
| Portabilidade | Nenhuma dependência do núcleo é específica de plataforma; sem uso de `socket`, `errno` ou API exclusiva do Windows | `src/app.py` concentra o `SO_EXCLUSIVEADDRUSE` no bloco de entrada | 🟡 |
| Desempenho | O custo por chamada não cresce de ordem de grandeza; a amostra de 40×40 pares por fixture continua concluindo dentro do tempo limite do harness | `_reversa_sdd/migration/parity_harness.md#O que ainda NÃO está coberto`, item 5 | 🟡 |
| Observabilidade | O motivo de descarte de um candidato continua disponível para auditoria | `_reversa_sdd/parity_tests/10-descartados-auditoria.feature` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: O núcleo responde sem estado global
  Dado que as estruturas da árvore são construídas em memória para uma fixture
  Quando a função de aceitação é chamada duas vezes com a mesma entrada
  Então o segundo resultado é idêntico ao primeiro
  E nenhuma variável de módulo foi lida ou escrita

Cenário: A decisão do matching é preservada
  Dado um nome de correspondente com cM e prenome conhecidos
  Quando a decisão de aceitação é tomada sobre os mesmos índices do GEDCOM
  Então o veredito é idêntico ao do oráculo congelado
  E o motivo do descarte, quando houver, é idêntico

Cenário: O caminho ancestral é preservado
  Dado um par de pessoas ligadas por uma cadeia de pais dentro do teto
  Quando a busca ancestral é executada
  Então o caminho e o ancestral comum são idênticos aos do oráculo
  E a ordem dos ramos é a mesma

Cenário: O caminho indireto com múltiplas afinidades é decomposto igual
  Dado um par de pessoas ligado por mais de um casamento no trajeto
  Quando o caminho indireto é buscado e decomposto
  Então o par de cônjuges de afinidade é o mesmo do oráculo
  E os ramos antes e depois do casamento são os mesmos

Cenário: A tabela de cM devolve a lista completa de faixas
  Dado um valor de cM que cai em mais de uma faixa publicada
  Quando a relação provável é consultada
  Então a lista devolvida contém todas as faixas na ordem de avaliação
  E um valor menor ou igual a zero devolve lista vazia

Cenário: A agregação do CSV preserva a soma exata
  Dado um CSV com mais de um segmento para o mesmo par de nome e kit
  Quando os segmentos são agregados
  Então o cM total é idêntico ao do oráculo, sem arredondamento

Cenário: O núcleo recusa dependência de framework
  Dado um módulo qualquer dentro de src/core
  Quando o teste de dependências varre os imports do pacote
  Então nenhum framework web, ORM ou biblioteca de validação é encontrado

Cenário: O núcleo não alcança o mundo de fora
  Dado um módulo qualquer dentro de src/core
  Quando o teste de dependências varre os imports do pacote
  Então nenhuma leitura de arquivo, de rede ou de variável de ambiente é encontrada

Cenário: O parse devolve a árvore sem escrever estado
  Dado um arquivo GEDCOM válido
  Quando o parse é executado
  Então a árvore é devolvida como valor de retorno
  E nenhuma estrutura global de domínio foi atribuída ou mutada

Cenário: A superfície de compatibilidade não sobrevive
  Dado o núcleo depois da mudança de assinatura
  Quando os nomes reexportados por path_search e dna_analysis são procurados
  Então nenhum nome histórico sem consumidor permanece exportado
  E todos os chamadores usam a assinatura nova

Cenário negativo: Divergência bloqueia a Onda 1
  Dado um candidato que produza um único valor diferente do oráculo
  Quando o harness diferencial é executado
  Então o relatório aponta a divergência com a fixture e a chave
  E a Onda 1 não é declarada fechada

Cenário negativo: A suíte existente não pode ser reduzida
  Dado que um teste foi removido ou desabilitado durante a mudança
  Quando a suíte completa é executada
  Então a contagem de aprovados é menor que a linha de base
  E a entrega é recusada
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a definição da Onda 1: sem núcleo puro a paridade não é isolável |
| RF-03 | Must | É o risco #1 declarado no brief, a fidelidade do matching |
| RF-04 | Must | O caminho ancestral é consumido por dois casos de uso |
| RF-05 | Must | É o RISK-011: a decomposição pode desaparecer sem que o matching falhe |
| RF-06 | Must | As faixas se sobrepõem até quatro vezes; a lista é o contrato |
| RF-07 | Must | A ordem de soma de ponto flutuante é não associativa |
| RF-08 | Must | Violação invalida a Onda 0, conforme a decisão de topologia |
| RF-13 | Must | Sem isso o parse continua sendo a origem do estado global que a feature remove |
| RF-11 | Must | Princípio III: nenhuma mudança sem teste que a cubra |
| RF-02 | Must | Sem isso a função não é pura |
| RF-09 | Should | Quebra os ciclos de pacote; pode entrar depois sem quebrar paridade |
| RF-10 | Should | Amplia a cobertura do harness para os pontos hoje descobertos |
| RF-12 | Should | Dívida #17: é limpeza de superfície, não condição de pureza |
| RNF de desempenho | Should | O parse domina o custo; a pureza não deve piorar a ordem de grandeza |
| RNF de portabilidade | Could | Nada no núcleo é específico de plataforma hoje |

> **Nota sobre a distribuição das prioridades.** `RF-01` e `RF-02` são as duas metades da pureza — uma trata do estado, a outra do parâmetro que o substitui — e por isso as duas estão em `Must`; tratá-las em prioridades diferentes deixaria a entrega num estado em que o núcleo não é puro nem preserva a assinatura. `RF-09`, que remove a dependência do núcleo sobre `parsers/` e `reporting/`, é a **consequência** da pureza e não a sua condição: pode ficar para depois da Onda 1 sem que a paridade ou a testabilidade sejam afetadas, desde que nenhuma dependência nova seja criada na direção contrária.

## 9. Esclarecimentos

### Sessão 2026-10-06

- **Q:** O núcleo puro pode importar bibliotecas de terceiros que não fazem I/O?
  **R:** Sim. `core/` pode importar a biblioteca padrão **e** terceiros que não fazem I/O — hoje `networkx` (caminho), `thefuzz` (score difuso) e `pandas` (leitura já entregue como valor). O que permanece proibido é framework web, ORM, biblioteca de validação, `parsers/` e `reporting/`. Justificativa: a ordem de iteração do `networkx` decide qual caminho de mesmo comprimento é devolvido; reescrever o algoritmo à mão trocaria uma garantia de paridade por uma reimplementação.
- **Q:** Como o núcleo recebe a árvore — a assinatura muda e os chamadores são atualizados, ou a superfície antiga sobrevive como adaptador?
  **R:** A assinatura muda e `src/app.py` e os demais chamadores são atualizados junto. A superfície antiga **não** sobrevive como adaptador: manter um adaptador exigiria carregar o estado que a feature remove.
- **Q:** Quem produz a árvore depois da mudança?
  **R:** `parsers/gedcom_parser.py` deixa de escrever o estado do domínio e passa a **devolver** a árvore como valor. O núcleo recebe esse valor e **não** importa o `ged4py` nem lê arquivo. A leitura do arquivo fica na borda.
- **Q:** O que fazer com a superfície de compatibilidade reexportada (dívida #17)?
  **R:** Remover, atualizando todos os chamadores. É consequência da decisão anterior: superfície morta esconderia a mudança de assinatura que a feature precisa tornar visível.

## 10. Lacunas

> Nenhuma lacuna aberta nesta data. As três lacunas da versão inicial foram resolvidas na sessão de esclarecimento de 2026-10-06 e estão registradas na seção 9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-06 | Sessão de esclarecimento: 4 decisões integradas, 3 `[DÚVIDA]` removidas, `RF-12` e `RF-13` acrescentadas, cenários de parse e de superfície acrescentados | reversa |
| 2026-10-06 | Critério de aceite da `RF-13` qualificado como estado final, após achado `A005` de `audit/cross-check.md` (durante a migração a mutação continua, pela ordem do `roadmap.md#8`) | reversa |
