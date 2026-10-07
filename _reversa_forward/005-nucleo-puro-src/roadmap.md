# Roadmap: núcleo puro em `src/core/` (Onda 1 do cutover)

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Requirements: `_reversa_forward/005-nucleo-puro-src/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

O núcleo de decisão já está separado da rota: `src/app.py` tem 258 linhas e nenhuma regra de negócio. O que falta para a Onda 1 é remover o **mecanismo** de ligação entre os módulos, que hoje é estado global mutável em `src/core/gedcom_state.py` (`people`, `families`, `graph`, `child_to_family` e o contador `versao`). A mudança é estrutural e não toca nenhuma decisão de domínio: `parsers/gedcom_parser.py` passa a **devolver** a árvore como valor em vez de substituir as globais in place, as funções do núcleo passam a **receber** a árvore, e `src/app.py` monta e repassa esse valor. A ordem de execução é fixada por um critério de risco, não por conveniência: **instrumentar o probe de aceitação primeiro**, porque as regras A/B/C/D e o Jaccard não têm cobertura diferencial hoje e é exatamente nelas que a mudança de assinatura mexe. A remoção do global alcança **8 arquivos de teste** que leem `gedcom_state` — 4 pelo módulo direto e 4 pelo retorno do parse — e nesses só o encanamento muda; nenhuma asserção é afrouxada.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | O corpus de paridade continua sintético; a verificação manual usa `_reversa_sdd/parity/fixtures/gedcom/basic.ged`, nunca `src/uploads/` | respeita |
| II. Comportamento observável é preservado em refatoração | É o princípio que governa a feature inteira: mesma entrada, mesma saída. A mudança é de estrutura, e a prova é o harness diferencial com igualdade exata | respeita |
| III. Nenhuma mudança sem teste que a cubra | O probe de aceitação é **pré-requisito**, não consequência (`RF-10`): sem ele a mudança de assinatura de `match_candidates` passa sem rede | respeita |
| IV. Arestas do grafo são tipadas | **Conflita**, e o conflito é declarado na `RN-01` e no `requirements.md#4`: `find_indirect_path` trata filiação e casamento como o mesmo salto. A feature **preserva** esse comportamento de propósito, porque corrigi-lo quebraria a paridade e mudaria a natureza da entrega | conflita (declarado) |
| V. Toda suposição de genealogia genética cita a fonte | A tabela de cM e a janela por meioses não são tocadas; a feature move o parâmetro, não o número | respeita |

> **Nota sobre o Princípio IV:** o roadmap não propõe mudança no princípio nem o atenua. A resolução do conflito é mudança de comportamento e, pelo Princípio II, exige feature própria com passagem por `/reversa-requirements`. Esta feature mantém o conflito aberto e visível.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A árvore entra por **parâmetro explícito** em cada função do núcleo (os quatro valores: `people`, `families`, `graph`, `child_to_family`) | É a única forma de pureza que não reintroduz um mecanismo de escopo compartilhado; o `paradigm_decision.md` proíbe transportar o estado global e a mutação in-place | (a) objeto de contexto mutável passado adiante, que reconstrói o global com outro nome; (b) adaptador de compatibilidade, que precisaria carregar o estado | 🟢 |
| D-02 | `load_gedcom_and_build_graph` **devolve** a árvore. **Ao final da migração** deixa de mutar as globais; durante ela, a mutação continua pela `D-11` | O parse é a origem do estado global; a pureza não fecha enquanto ele escrever em vez de devolver. A mutação sobrevive **apenas** enquanto houver consumidor não migrado, e a última ação da migração a remove | (a) manter a mutação e sincronizar um retorno, que duplica a verdade; (b) o núcleo importar `ged4py` e ler o arquivo, que viola a `RN-04` | 🟢 |
| D-03 | A invalidação do índice de nomes passa a ser derivada do **valor recebido**. **Durante a migração**, o contador `versao` é mantido como sinal interno para os módulos ainda não migrados, e some com o estado global | O contador existe só porque `id()` não muda com mutação in-place; sem mutação in-place o problema desaparece na raiz. Mantê-lo durante a migração é o que permite migrar módulo a módulo sem uma janela em que o índice fique velho | (a) remover `versao` no passo 4, junto com a mudança do parse, o que exigiria migrar todos os consumidores de uma vez; (b) manter `versao` como parâmetro permanente, que perpetua o sinal para um problema que deixa de existir | 🟢 |
| D-04 | O núcleo pode importar a biblioteca padrão e terceiros **sem I/O** (`networkx`, `thefuzz`, `pandas`) | Decisão do usuário em 2026-10-06. `find_indirect_path` depende da ordem de inserção das arestas no `networkx` para escolher entre caminhos de mesmo comprimento — o harness compara exatamente essa ordem | (a) só biblioteca padrão, que exigiria BFS e score reescritos à mão | 🟢 |
| D-05 | A superfície de compatibilidade de `path_search.py` e `dna_analysis.py` é **removida** | Decisão do usuário em 2026-10-06. Dívida #17: são nomes históricos sem consumidor de produção; preservá-los esconderia a mudança de assinatura | (a) manter o que os testes usam; (b) manter integralmente | 🟢 |
| D-06 | `gedcom_state.py` deixa de guardar estado. `get_name` e `ref_id` **migram** para `src/core/registro.py`, um módulo puro de acesso a registro | São funções de registro, não de estado: `get_name` é a cópia fiel do oráculo, e é referenciada por 5 dos 7 arquivos de teste. Enterrá-las no `dna_analysis.py` tornaria a fonte da paridade invisível | (a) inlinar cada uma no consumidor, que duplicaria a cópia fiel; (b) manter um `gedcom_state` só com as duas, que preserva um nome que já não descreve o conteúdo | 🟢 |
| D-07 | **Sequenciamento por risco:** o probe de aceitação no harness vem **antes** de qualquer mudança de assinatura | `match_candidates` e `build_ged_indexes` não têm probe hoje (`_reversa_sdd/parity/harness.py:111-144`). Mudar a assinatura antes de instrumentar deixaria a decisão mais sensível do sistema sem rede diferencial justamente durante a mudança | (a) trocar só `people`/`families`, deixando `matching` para depois, que não elimina o global e não fecha a Onda 1 | 🟡 |
| D-08 | **Não** se cria `analisador/core/` nem árvore de projeto novo | Decisão do usuário em 2026-10-06 (Branch by Abstraction). `src/core/` já contém o núcleo e já está em 100% de paridade; duplicá-lo criaria duas verdades | (a) herdar literalmente o `topology_decision.md`, criando `analisador/` e re-portando o núcleo | 🟢 |
| D-09 | Os **8 arquivos de teste** que dependem de `gedcom_state` são atualizados no encanamento, com as asserções intactas | O `RF-11` mede a contagem de aprovados: 164. Afrouxar asserção para a suíte passar é exatamente o defeito que o `parity_harness.md` registrou (a asserção nula `in ("Sem Nome", "")` que não podia falhar) | (a) manter `gedcom_state` só para os testes, que deixaria os testes validando um mundo que a produção não usa | 🟢 |
| D-10 | O `harness.py` passa a apontar o coletor do candidato para a assinatura nova no **mesmo commit** da mudança | A regra de sequenciamento do `cutover_plan.md` e do `handoff.md` é rígida: nenhuma onda avança com paridade pendente, e um harness desatualizado produz INCONCLUSIVO, não paridade | (a) deixar o harness quebrado e remedir no fim, aceitando uma janela sem medição | 🟢 |
| D-11 | **Durante a migração**, o parse devolve a árvore **e** continua atualizando as globais, até que o último consumidor tenha migrado | É a técnica que permite migrar módulo a módulo sem quebrar o sistema no meio: os módulos ainda não migrados seguem lendo o global, e os já migrados leem o parâmetro. Sem isso a migração teria de ser um passo indivisível, contra a `D-07` e o passo 1 do plano | (a) migrar tudo de uma vez, que elimina os pontos de medição intermediários | 🟢 |

## 4. Premissas

> Nenhuma. O `requirements.md` está com **zero** marcadores `[DÚVIDA]`: as três lacunas iniciais e a quarta decisão foram resolvidas na sessão de esclarecimento de 2026-10-06 (`requirements.md#9`).

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| n/a | n/a | n/a |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `gedcom_state` | `_reversa_sdd/architecture.md#1` | componente-extinto ao final | Deixa de ser o registro do estado do processo. O nome não sobrevive: ao final da migração o módulo é **removido**, e o acesso a registro (`get_name`, `ref_id`) vive em `src/core/registro.py` (`D-06`, `T023`, `T025`). Durante a migração o arquivo existe, sem estado, apenas para não quebrar consumidores ainda não migrados |
| `load_gedcom_and_build_graph` | `_reversa_sdd/code-analysis.md#2.2` | contrato-alterado | Passa a devolver a árvore como valor. **Durante a migração** continua atualizando as globais, para não quebrar os consumidores ainda não migrados (`D-11`); a mutação some junto com o estado global |
| `family_navigation` | `_reversa_sdd/code-analysis.md#4.2` | contrato-alterado | `get_parents`, `get_spouses`, `get_children`, `find_person_by_name` recebem a árvore |
| `path_finding` | `_reversa_sdd/code-analysis.md#4.2` | contrato-alterado | `find_ancestral_path` e `find_indirect_path` recebem a árvore e o grafo; o import dentro da função (`path_finding.py:38`) desaparece |
| `matching` | `_reversa_sdd/code-analysis.md#3.2` | contrato-alterado | `build_ged_indexes` e `match_candidates` recebem a árvore; nenhum limiar muda (`RF-03`) |
| `documentary_relationship` | `_reversa_sdd/code-analysis.md#4.2` | contrato-alterado | O maior consumidor (13 usos de estado). O cache `_INDICE_DE_NOMES` deixa de depender de `gedcom_state.versao` |
| `dna_analysis` | `_reversa_sdd/code-analysis.md#3.1` | contrato-alterado | Passa a receber a árvore em vez de ler `people`; deixa de importar `parsers/` e `reporting/` (`RF-09`) |
| `diagram_domain` | `_reversa_sdd/architecture.md#3` | contrato-alterado | O resolvedor injetado (`resolvedor_de_diagrama`) e o import tardio de `gedcom_state` (`diagram_domain.py:38`) precisam sobreviver à remoção do global |
| `path_search` | `_reversa_sdd/code-analysis.md#4.1` | contrato-alterado | Recebe a árvore; a superfície de compatibilidade é removida (`D-05`) |
| `csv_ingest` | `_reversa_sdd/code-analysis.md#3.1` | contrato-alterado | Já é folha funcionalmente; a mudança é de contrato — quem o chama passa a ser a borda, e não o núcleo |
| `app.py` (camada de rota) | `_reversa_sdd/architecture.md#1` | contrato-alterado | Monta a árvore a partir do retorno do parse e a repassa aos fluxos; continua sem regra de negócio |
| `harness.py` (instrumento, não runtime) | `_reversa_sdd/migration/parity_harness.md` | componente-alterado | Ganha os probes de aceitação e de decomposição (`RF-10`) e passa a usar a assinatura nova |
| `README.md` | `README.md:63`, `:147`, `:251` | regra-alterada | **Obrigatório:** três passagens afirmam que "o estado do GEDCOM fica em estruturas globais em memória, compartilhadas entre as threads de um mesmo processo". Depois desta feature a afirmação fica **falsa**. O README é a única superfície de documentação sem defasagem do repositório, e deixá-lo contradizer o código seria criar a defasagem que a re-extração de 2026-10-05 registrou |
| `interfaces/` de contrato externo | — | n/a | Nenhum contrato externo muda nesta feature: não há rota nova, campo de formulário novo, mensagem nova nem formato de arquivo novo |

> **Fronteira que a feature NÃO cruza:** `src/templates/index.html`, as mensagens de contrato de `_reversa_sdd/domain.md#4`, o bloco de entrada do `src/app.py` (socket exclusivo, `waitress`, variáveis de ambiente) e o `requirements.txt` ficam intactos. A feature é interna ao processo Python.

## 6. Delta no modelo de dados

- **Resumo das mudanças:** não há banco de dados, schema nem persistência neste sistema (`_reversa_sdd/architecture.md#4`). O "modelo" é a forma das estruturas em memória: as quatro estruturas globais (`people`, `families`, `graph`, `child_to_family`) e o contador `versao` deixam de ser estado de módulo e passam a ser **valor de retorno do parse** recebido por parâmetro. A **forma** dos dados não muda — mesmos dicionários, mesmas chaves, mesmo grafo `nx.Graph` sem tipo de aresta. Nenhum campo é acrescentado, removido ou renomeado.
- **Detalhe completo em:** `_reversa_forward/005-nucleo-puro-src/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a | n/a | Nenhum contrato externo é tocado. `interfaces/` não é criado |

> A superfície externa do sistema é o `POST /` com o campo `action` (`upload_gedcom`, `dna_analysis`, `path_search`), e ela não muda: mesmos campos, mesmas mensagens, mesmas quatro seções de resultado. A única mudança observável é interna ao processo. `interfaces/` é omitido conforme a regra do skill.

## 8. Plano de migração

Não há dados a migrar (`data_migration_plan.md`: volume zero em todas as entidades). O que existe é a **ordem de execução dentro do processo**, e ela é escolhida por risco:

1. **Instrumentar antes de mover.** Acrescentar ao `harness.py` os probes de aceitação (`build_ged_indexes`, `match_candidates` com veredito e motivo) e de decomposição do caminho. Rodar e confirmar 100% nas 6 fixtures **na assinatura atual**, para que o probe tenha linha de base.
2. **Medir a linha de base duas vezes.** Suíte (`164 aprovados / 15 erros`) e paridade, **antes de qualquer edição de produto** — a edição dos passos 1 e 3 é de instrumento e de módulo novo, e o portão é que nenhuma delas mova os números.
3. **Criar o módulo puro de acesso a registro** com `get_name` e `ref_id`, e apontar os consumidores para ele (`D-06`).
4. **Mudar o parse para devolver a árvore** (`D-02`), mantendo as globais sendo atualizadas **até o último consumidor migrar** (`D-11`). É o que permite migrar módulo a módulo sem quebrar o sistema entre um passo e o seguinte.
5. **Migrar o núcleo por módulo, de dentro para fora:** `family_navigation` → `path_finding` → `matching` → `documentary_relationship` → `genetic_evidence`/`evidence_comparison` → `dna_analysis`/`path_search`. A cada módulo, atualizar os chamadores e **rodar o harness** — a paridade por módulo é o portão.
6. **Atualizar `app.py`** para montar e repassar a árvore.
7. **Atualizar o encanamento dos 8 arquivos de teste** e o `harness.py` (`D-09`, `D-10`).
8. **Remover o estado global** e a superfície de compatibilidade (`D-05`), quando nada mais ler nenhum dos dois.
9. **Conferir o teste de dependências** do núcleo (`RF-08`, `RF-09`), criado no passo de testes e mantido **falhando de propósito** até o passo 8, e **remedir tudo** contra a linha de base do passo 2.

> ⚠️ **Ordem não negociável:** o passo 1 vem antes do 4. Um probe de aceitação escrito **depois** da mudança de assinatura seria escrito contra o código novo, e não haveria como saber se ele teria capturado uma divergência introduzida na mudança.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A mudança de assinatura passa sem rede nas regras A/B/C/D, porque `match_candidates` não tem probe | alto | alta | Passo 1 do plano de migração: instrumentar e **medir a linha de base antes** de mover (`RF-10`, `D-07`) |
| A ordem de iteração do `networkx` muda ao trocar o grafo de global para parâmetro, e o caminho escolhido entre iguais muda junto | alto | média | O grafo continua sendo o **mesmo objeto e a mesma ordem de inserção**; o harness compara caminho e MRCA por igualdade exata nos 1.600 pares (`RF-05`) |
| Divergência silenciosa na soma de cM ao mover a agregação | alto | baixa | `total_cm` comparado por igualdade exata, sem arredondamento, nos CSVs `duplicated` e `cm_boundaries` (`RF-07`) |
| Atualizar teste afrouxando asserção, para a suíte "passar" | alto | média | `RF-11` fixa a contagem em 164 aprovados; a `D-09` proíbe afrouxar asserção, e o precedente da asserção nula está documentado em `parity_harness.md` |
| A remoção do global deixa um leitor esquecido, e o sistema passa a ler um dicionário vazio | alto | média | O passo 8 só remove depois de nada ler; o teste de dependências (`RF-08`) e a suíte inteira fecham a conta |
| `diagram_domain.py` quebra ao remover `gedcom_state`, porque usa import tardio e injetado | médio | média | Tratado como componente próprio no delta (§5), com verificação dedicada antes do passo 8 |
| O `cm_estimator` (legado fora do fluxo, `adrs/19`) some junto com a limpeza de superfície sem decisão explícita | baixo | média | Removido apenas o **reexport**; o módulo permanece até decisão própria, registrada como observação no `investigation.md` |
| O harness produz INCONCLUSIVO durante a migração por módulo, e a leitura vira "paridade OK" | médio | média | O harness já reporta INCONCLUSIVO em vez de paridade quando estoura o tempo; a `D-10` exige atualizar o coletor no mesmo commit de cada módulo |
| O custo do processo cresce com os passos, e a onda não fecha | médio | baixa | Todos os passos são internos ao processo Python, sem infraestrutura nova; cada passo é verificável isoladamente |

## 10. Critério de pronto

- [ ] O harness reporta **paridade 100% nas 6 fixtures** com a assinatura nova, e passa a cobrir as funções de aceitação e a decomposição do caminho
- [ ] A suíte reporta **164 aprovados** (linha de base de 2026-10-06), com os mesmos 15 erros de ambiente, e nenhum teste removido ou desabilitado
- [ ] Nenhum módulo de `src/core/` lê ou escreve estado de módulo mutável
- [ ] Nenhum módulo de `src/core/` importa `parsers/`, `reporting/`, `flask`, `fastapi`, `sqlalchemy`, `pydantic` ou `waitress` — verificado por teste automatizado
- [ ] `parsers/gedcom_parser.py` devolve a árvore como valor e não atribui estrutura global
- [ ] A superfície de compatibilidade reexportada não existe mais, e todos os chamadores usam a assinatura nova
- [ ] Aplicação sobe por `waitress` e o caminho feliz responde `HTTP 200` com o formulário de upload presente
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-06 | Correções de redação após auditoria (`audit/cross-check.md`): `D-02` declara que descreve o estado final; contagem de arquivos de teste corrigida de 7 para 8; `gedcom_state` reclassificado como `componente-extinto ao final`; `csv_ingest` reclassificado como `contrato-alterado`; escopo de `T021` ampliado | reversa |
