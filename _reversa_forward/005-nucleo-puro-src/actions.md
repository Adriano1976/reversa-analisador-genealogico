# Actions: núcleo puro em `src/core/` (Onda 1 do cutover)

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Roadmap: `_reversa_forward/005-nucleo-puro-src/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **30** |
| Paralelizáveis (`[//]`) | **7** (`T003`, `T008`, `T015`, `T019`, `T026`, `T027`, `T028`) |
| Maior cadeia de dependência | **17 ações** (16 elos): `T002` → `T004` → `T009` → `T011` → `T012` → `T013` → `T014` → `T016` → `T018` → `T020` → `T021` → `T022` → `T023` → `T025` → `T027` → `T029` |

**Composição:** 4 ações de preparação, **4** de teste, 12 de núcleo, 7 de integração e 3 de polimento.

> ⚠️ **A ordem não é preferência, é o plano.** As duas primeiras ações instrumentam o harness **antes** de qualquer mudança de assinatura (`D-07`). O `harness.py` hoje **não tem probe** para `match_candidates` nem para `build_ged_indexes` (`harness.py:111-144`), e são exatamente as funções que esta feature altera. Um probe escrito depois da mudança seria escrito contra o código novo, sem linha de base.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar ao coletor do candidato e ao do oráculo o probe de aceitação do matching: para cada par (nome do CSV, cM) das fixtures de DNA, registrar a lista de candidatos aceitos com o **motivo** e a lista de descartados com o motivo, usando `build_ged_indexes` e `match_candidates` na assinatura atual | - | - | `_reversa_sdd/parity/harness.py` | 🟢 | `[X]` |
| T002 | Acrescentar aos dois coletores o probe de decomposição do caminho: para cada par de `affinity.ged`, registrar `split_path_by_marriage`, `are_spouses` e o par de cônjuges de afinidade, preservando a ordem dos ramos | T001 | - | `_reversa_sdd/parity/harness.py` | 🟢 | `[X]` |
| T003 | Limpar o resíduo de execuções anteriores do harness e conferir que a árvore de trabalho não tem arquivo de instrumento não rastreado | - | `[//]` | `_reversa_sdd/parity/_clean_residue.py` | 🟢 | `[X]` |
| T004 | Medir e registrar a linha de base com a assinatura atual: suíte completa e paridade nas 6 fixtures, guardando a saída como evidência | T001, T002, T003 | - | `_reversa_forward/005-nucleo-puro-src/evidence/` | 🟢 | `[X]` |

> ✅ **`T001` NÃO foi executado como escrito, e a diferença está registrada.** O oráculo congelado **não expõe** `match_candidates` nem `build_ged_indexes`: a decisão de aceitação vive `inline` dentro da rota `POST /` (`app_legacy_e43ca22.py:695-796`). Transcrever aquele bloco para o coletor seria circular. O que foi implementado, com decisão explícita do usuário em 2026-10-06, é um **probe de rota**: os dois lados executam a análise de DNA pela mesma porta de entrada, e o probe intercepta `render_template` para capturar o contexto de domínio — `dna_results`, `skipped_matches` e a mensagem — sem renderizar HTML.
>
> **Limitação declarada:** o campo `motivo` do legado funde "recusado pelas regras de aceitação" com "aceito mas sem caminho", então o probe **não isola** as regras A/B/C/D da busca de caminho. Detalhe em `evidence/T004-linha-de-base.md`.
>
> **Achado secundário do `T001`:** o harness nunca conseguia passar um CSV aos coletores — só recebia GEDCOM. O probe exigiu estender o contrato dos dois coletores para receber a fixture de DNA (novo argumento posicional) e uma opção `--dna` no harness.

> **Por que T001 e T002 são sequenciais, e não paralelas:** as duas editam o **mesmo arquivo** (`harness.py`), e o critério de paralelismo do Reversa exige arquivos alvo diferentes. Elas foram separadas mesmo assim porque são dois probes distintos, com resultados verificáveis separadamente — e porque escrever os dois de uma vez tornaria impossível saber qual deles quebrou se a coleta falhasse.
>
> **T004 é o portão da fase:** sem a linha de base registrada **antes** da mudança, nenhuma divergência posterior é atribuível. A suíte esperada é `164 passed, 15 errors`; a paridade esperada é `100% nas 6 fixtures`.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Escrever o teste por inspeção de AST que falha se qualquer módulo de `src/core/` importar `flask`, `fastapi`, `sqlalchemy`, `pydantic` ou `waitress`, confirmando que ele **falha** se um import proibido for introduzido de propósito | T004 | - | `tests/test_dependencias_nucleo.py` | 🟢 | `[X]` |
| T006 | Estender o mesmo arquivo com a afirmação de que nenhum módulo de `src/core/` faz I/O nem depende de plataforma: sem `open`, `os.makedirs`, `os.environ`, `requests`, leitura de socket, `errno` e `SO_EXCLUSIVEADDRUSE` | T005 | - | `tests/test_dependencias_nucleo.py` | 🟢 | `[X]` |
| T007 | Estender o mesmo arquivo com a afirmação de que nenhum módulo de `src/core/` declara estado mutável de módulo (`people`, `families`, `graph`, `child_to_family`, `versao`), escrevendo a asserção de forma que ela **falhe hoje** e passe só ao final | T006 | - | `tests/test_dependencias_nucleo.py` | 🟢 | `[X]` |
| T030 | Escrever o teste que prova o bloqueio por divergência: alimentar o comparador do harness com duas observações que diferem em um único valor e confirmar que o resultado é divergência reportada com fixture e chave, e não paridade | T004 | - | `_reversa_sdd/parity/harness.py` | 🟢 | `[X]` |

> ✅ **Fase 2 executada. Medições da rodada:**
>
> | Medição | Antes | Depois |
> |---|---|---|
> | Suíte | 164 passed, 15 errors | **172 passed, 2 xfailed, 15 errors** |
> | Arquivo novo | — | 10 verificações: 8 aprovadas e 2 declaradamente falhando |
>
> Os **15 erros de ambiente são os mesmos**, e os 8 aprovados a mais são exatamente as verificações novas. **Nenhum teste foi removido, desabilitado ou afrouxado** (`RF-11`).
>
> ⚠️ **DESVIO DECLARADO DO `T007` COMO ESCRITO.** A ação pedia uma asserção que **falhe hoje** e passe ao final. Duas afirmações satisfazem essa descrição — a de estado global e a de `parsers/`/`reporting/` (`RF-09`, que a execução mediu em `dna_analysis.py` e `path_search.py`) — e uma falha vermelha e permanente deixaria a suíte cega entre `T007` e `T023`: a próxima ação que rodasse a suíte não distinguiria a falha esperada de uma regressão real.
>
> As duas foram escritas com **`@pytest.mark.xfail(strict=True)`**. O `strict` é o que preserva a exigência da ação: se a asserção for escrita frouxa e passar por engano, o XPASS vira **falha**. Ao final da migração (`T023`), o marcador é removido e o teste passa por mérito próprio.
>
> O desvio é de **mecanismo**, não de intenção: a asserção continua discriminante e continua falhando hoje. O que muda é que ela falha de forma **declarada**, e não contamina o resto da suíte.
>
> **Controles negativos escritos junto:** cada guarda tem um teste que prova que ela **consegue** falhar (`T005` e `T007`). Sem isso, uma asserção que olhasse para o lugar errado passaria por vacuidade — o defeito que o `parity_harness.md` §DIV-001a registrou na suíte antiga.

> **T007 é escrita para falhar de propósito.** É o critério da `RF-01`, e é o teste que fecha a conta de que nenhum leitor do estado sobrou. A tentação de escrevê-la frouxa — aceitando qualquer coisa que se pareça com dicionário — é o defeito que o `parity_harness.md` §DIV-001a documentou. Escreva-a discriminante.
>
> ⚠️ **Estado esperado da suíte entre `T007` e `T025`.** Enquanto a asserção de `T007` estiver no lugar e o estado global ainda existir, a suíte tem **1 falha intencional**: ela reporta **163 aprovados + 1 falha**, e não 164. **Isso não é regressão** — é o comportamento declarado de um teste escrito para falhar até que a condição que ele mede passe a valer. Quem medir a suíte nessa janela deve ler o número assim, e a evidência de `T026` deve declarar a diferença. Ao final, com `T025` executada, a suíte volta a **164 aprovados**.
>
> **A nova ação é `T030`, e não `T024` estendida.** São dois caminhos negativos distintos: `T024` prova que o teste de dependências falha quando um import proibido entra; `T030` prova que o **harness** recusa paridade quando há divergência. Misturar os dois na mesma ação tornaria impossível saber qual dos dois quebrou.

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Criar `src/core/registro.py` com `get_name` e `ref_id` copiados **literalmente** de `gedcom_state.py`, preservando a docstring que explica por que o formato vazio devolve `''` e não "Sem Nome" (DIV-001) | T004 | `[//]` | `src/core/registro.py` | 🟢 | `[X]` |
| T009 | Fazer `load_gedcom_and_build_graph` **devolver** a árvore como valor (pessoas, famílias, grafo, filho→família) sem deixar de atualizar as globais durante a migração, e sem alterar a ordem de inserção de nenhuma estrutura | T008 | - | `src/parsers/gedcom_parser.py` | 🟢 | `[X]` |
| T010 | Apontar o coletor do candidato no harness para a assinatura nova, de forma que ele consuma a árvore devolvida pelo parse em vez de ler o global | T009 | - | `_reversa_sdd/parity/harness.py` | 🟢 | `[ ]` |
| T011 | Migrar `family_navigation` para receber a árvore por parâmetro em `get_parents`, `get_spouses`, `find_person_by_name` e no índice filho→família, atualizando os chamadores no mesmo passo | T009 | - | `src/core/family_navigation.py` | 🟢 | `[X]` |
| T012 | Migrar `path_finding` para receber a árvore e o grafo por parâmetro, removendo o import dentro de `find_indirect_path`, sem tocar em `MAX_DEPTH` nem em `MAX_HOPS` | T011 | - | `src/core/path_finding.py` | 🟢 | `[X]` |
| T013 | Migrar `matching` para receber a árvore por parâmetro em `build_ged_indexes` e `match_candidates`, **sem tocar em nenhum limiar, peso ou ramo de aceitação** | T012 | - | `src/core/matching.py` | 🟢 | `[X]` |
| T014 | Migrar `documentary_relationship` para receber a árvore por parâmetro, trocando a invalidação do índice de nomes por chave derivada do valor recebido em vez de `gedcom_state.versao` | T013 | - | `src/core/documentary_relationship.py` | 🟢 | `[X]` |
| T015 | Migrar `genetic_evidence` e `evidence_comparison` para receber o que consomem por parâmetro, sem alterar a chave de evidência (nome, kit) nem a ordem de acumulação de cM | T013 | `[//]` | `src/core/genetic_evidence.py`, `src/core/evidence_comparison.py` | 🟢 | `[X]` |

> ✅ **`T015` verificada em 2026-10-06: os dois módulos JÁ ERAM puros.** Varredura de imports e de leitura de estado: `genetic_evidence` importa `re`, `name_normalization` e `utils.text_cleaning`; `evidence_comparison` importa `relationship_hypotheses`. **Nenhum dos dois toca `gedcom_state`, `parsers/` ou `reporting/`**, e o docstring do `genetic_evidence` já declarava "modulo nao conhece `people`, nao conhece arvore". Não houve migração a fazer — a ação fechou por verificação, e isso está registrado para que a leitura futura não procure um diff que não existe.
| T016 | Migrar o fluxo `dna_analysis` para receber a árvore, deixando de importar `parsers/csv_ingest` e `reporting/mermaid_render`: a leitura do CSV e o diagrama passam a ser entregues pelo chamador | T014, T015 | - | `src/core/dna_analysis.py` | 🟢 | `[X]` |
| T017 | Migrar o fluxo `path_search` para receber a árvore, deixando de importar `reporting/mermaid_render` e consumindo o resolvedor de diagrama pelo parâmetro | T014 | - | `src/core/path_search.py` | 🟢 | `[X]` |
| T018 | Reescrever `diagram_domain` para receber a árvore e devolver as consultas sobre **ela**, eliminando o import tardio de `gedcom_state` e a captura do dicionário no momento da montagem | T011, T012 | - | `src/core/diagram_domain.py` | 🟢 | `[X]` |
| T019 | Migrar `csv_ingest` para devolver os valores que o fluxo de DNA consome, sem escrever estado de domínio, preservando o fallback de encoding e a detecção de colunas | T009 | `[//]` | `src/parsers/csv_ingest.py` | 🟢 | `[X]` |

> ✅ **`T018` e `T019` fechadas — e a Fase 3 (Núcleo) está completa. Medições: suíte `178 passed, 1 xfailed, 15 errors` e paridade `100%` nas 6 fixtures, exit 0.**
>
> **`T018` era, na prática, consolidação.** O `diagram_domain` já recebia a árvore desde o `T011` — o que faltava era o **import tardio de `gedcom_state`** que restava no corpo do resolvedor, e que a ação pedia para eliminar. Aproveitei para atacar um problema que a migração criou: havia **três cópias** da função `_arvore_global()`, uma em cada fluxo de entrada. Três funções de transição são pior do que uma: são três pontos para esquecer quando a transição acabar. Agora existe **uma só**, em `documentary_relationship`, e os outros dois módulos a importam. Verificado: `grep '^def _arvore_global'` devolve **1**.
>
> ✅ **`T019` fechada por verificação, sem diff.** O `csv_ingest` **já era uma folha pura**: importa apenas `csv`, `io`, `Counter`, `pandas`, `utils.name_keys` e `utils.text_cleaning`. Nenhum acesso a `gedcom_state`, e todas as suas funções já devolvem valores (`read_csv_with_fallback` devolve um DataFrame, `detect_columns` um dict, `aggregate_matches` uma lista). Não havia estado a remover — a ação fechou por medição, e isso está registrado para que uma leitura futura não procure um diff que não existe.
>
> **Resumo da Fase 3:** 12 de 12 ações fechadas. O `src/core/` **não declara estado mutável**, **não importa framework** e **não importa `parsers/` nem `reporting/`** — as três guardas de `test_dependencias_nucleo.py` refletem isso, e a de `RF-09` já passou de `xfail` a verde. Falta o `T023` remover o módulo de estado, e com ele o último `xfail`.

> **T011 a T014 são sequenciais de propósito, e cada uma termina com a mesma verificação:** rodar o harness e confirmar paridade 100% antes de seguir. Migrar dois módulos de uma vez torna uma divergência não atribuível, e a `D-07` existe exatamente para preservar a atribuibilidade.
>
> **T015 é `[//]` com relação a T014** por tocar arquivos diferentes, mas depende de T013 — e só deve rodar depois que a paridade de T014 estiver confirmada.
>
> **T013 é a ação de maior risco do documento.** É onde vivem as regras A/B/C/D, o filtro anti-falso-positivo e o Jaccard. A ação muda **assinatura**, e nada mais: nenhum literal de `matching.py:99-166` pode mudar de valor.

### Execução de 2026-10-06 — `T008` e `T009`

**Medições:** suíte `177 passed, 2 xfailed, 15 errors` (linha de base era `164 passed, 15 errors`; as 13 a mais são as verificações novas de `test_dependencias_nucleo.py` e `test_arvore_devolvida.py`) e paridade **100% nas 6 fixtures**, exit 0. **Ordem:** `T010` foi adiado e absorvido por `T023`; a execução segue por `T011`.

**`T008` foi além do texto da ação, por necessidade.** `gedcom_state.py` **também** era a origem de `get_name` e `ref_id` para oito pontos do núcleo e do parser. Remover as duas de lá sem mais nada quebraria todos os imports no mesmo passo. O arquivo ficou **reexportando** as duas de `core/registro.py`, com `noqa` e nota de transição no docstring. A migração de cada consumidor acontece em `T011`–`T014`, junto com a migração do módulo que o consome — uma passada por arquivo, não duas.

⚠️ **DESVIO DECLARADO no `T009`: o parse foi DIVIDIDO, e não teve o retorno trocado.** A ação pedia "fazer `load_gedcom_and_build_graph` devolver a árvore", mas isso **é** mudança de contrato dos dois consumidores: `src/app.py` usa a lista de nomes para o campo de sugestão, e o probe `names` do harness compara a lista com a do oráculo. Trocá-la agora quebraria os dois no mesmo passo em que o parse muda — contra a própria `D-11`.

O que foi feito: `carregar_arvore()` é a função nova, que devolve `(people, families, graph, child_to_family)` e continua atualizando as globais numa transição explícita; `load_gedcom_and_build_graph()` virou casca fina sobre ela, com o retorno antigo intacto. **Um único lugar do projeto ainda escreve as globais**, o que torna a remoção de `T023` mecânica.

⚠️ **DESVIO DECLARADO no `T010`: adiado para `T023`.** A ação manda apontar o coletor do harness para a assinatura nova. Mas o coletor é o **instrumento de medição**: se ele passar a ler a árvore de `carregar_arvore` enquanto o sistema ainda depende das globais, o harness deixa de medir o caminho de produção. Ele só deve migrar quando as globais saírem — e nesse momento é obrigatório, senão o coletor quebra junto com a casca. `T010` fica `[ ]` e passa a depender de `T023`.

**Testes novos:** `tests/test_arvore_devolvida.py`, 5 verificações — os quatro componentes preenchidos, a forma preservada (`dict`/`dict`/`nx.Graph`/`dict` de listas), o grafo bidirecional com o nó de família, o estado global ainda atualizado na transição, e o contrato antigo devolvendo a lista ordenada de nomes.

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T020 | Atualizar a camada de rota para montar a árvore a partir do retorno do parse e repassá-la aos dois fluxos, sem introduzir regra de negócio no `app.py` | T016, T017, T019 | - | `src/app.py` | 🟢 | `[X]` |
| T021 | Atualizar o encanamento dos oito arquivos de teste que dependem de `gedcom_state`, **preservando todas as asserções** e sem remover nem desabilitar teste | T020 | - | `tests/test_upload.py`, `tests/test_dna_analysis.py`, `tests/test_path_search.py`, `tests/test_characterization_matching.py`, `tests/test_characterization_mermaid.py`, `tests/test_formatacao_cm.py`, `tests/test_mermaid_escape.py`, `tests/test_confrontacao_gedcom_dna.py` | 🟢 | `[X]` |
| T022 | Remover a superfície de compatibilidade reexportada por `path_search` e `dna_analysis`, atualizando quem a consumia; manter `cm_estimator` em disco, removendo apenas o reexport | T021 | - | `src/core/path_search.py`, `src/core/dna_analysis.py` | 🟢 | `[ ]` |
| T023 | Remover o estado global: tirar `people`/`families`/`graph`/`child_to_family`/`versao` e o reexport de `get_name`/`ref_id` de `gedcom_state.py`, apontar os últimos consumidores para `src/core/registro.py`, tirar a escrita das globais de `carregar_arvore` — e **absorver o `T010`**: apontar o coletor do harness para a árvore devolvida, já que a casca `load_gedcom_and_build_graph` deixa de existir aqui | T022, T010 | - | `src/core/gedcom_state.py`, `src/parsers/gedcom_parser.py`, `_reversa_sdd/parity/harness.py` | 🟢 | `[ ]` |
| T024 | Verificar o caminho negativo do teste de dependências: introduzir de propósito um import proibido em `src/core/` e confirmar que `T005` falha; depois revertê-lo | T023 | - | `tests/test_dependencias_nucleo.py` | 🟢 | `[ ]` |
| T025 | Remover o módulo de estado e apontar os últimos consumidores para `src/core/registro.py` | T023 | - | `src/core/` | 🟢 | `[ ]` |
| T026 | Medir o resultado final e registrar a evidência: suíte e paridade com a assinatura nova, comparando com a linha de base de `T004` | T025 | `[//]` | `_reversa_forward/005-nucleo-puro-src/evidence/` | 🟢 | `[ ]` |

> **T024 e T025 trocam de ordem em relação ao plano do roadmap**, que punha a remoção antes da verificação do caminho negativo. A razão é prática: o caminho negativo precisa de um estado em que o import proibido **seja** proibido, e não de um estado intermediário.

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Atualizar as três passagens do README que afirmam que o estado do GEDCOM vive em estruturas globais em memória compartilhadas entre threads, agora que a afirmação é falsa | T025 | `[//]` | `README.md` | 🟢 | `[ ]` |
| T028 | Remover as docstrings que documentam como contrato os artefatos do estado global: o contrato de import com `gedcom_state` em `family_navigation` e `path_finding`, o contador `versao` e a nota de captura do resolvedor | T025 | `[//]` | `src/core/family_navigation.py`, `src/core/path_finding.py`, `src/core/diagram_domain.py` | 🟡 | `[ ]` |
| T029 | Executar a verificação manual do `onboarding.md`: subir por `waitress`, confirmar `HTTP 200`, formulário presente, upload do GEDCOM sintético, análise com o CSV de fronteiras de cM e busca de caminho, registrando a saída em `evidence/` | T026, T027, T028 | - | `_reversa_forward/005-nucleo-puro-src/evidence/` | 🟢 | `[ ]` |

> **Nota sobre `T026` e `T029` no mesmo alvo.** As duas escrevem em `evidence/`, e `T026` está marcada `[//]`. Isso **não** é violação do critério de paralelismo: a regra proíbe tarefas `[//]` **entre si** de compartilhar alvo, e `T029` não é `[//]`. Além disso `T029` depende de `T026`, então as duas são sequenciais por construção.

> **T028 não é cosmético.** As docstrings de `path_finding.py:8-13` e `diagram_domain.py:1-6` documentam o import tardio e a captura do dicionário como se fossem contrato deliberado. Depois desta feature elas descrevem um mecanismo que não existe mais, e uma docstring que mente sobre o mecanismo é pior do que docstring nenhuma — foi assim que a `D-06` precisou de justificativa explícita.

## Notas de execução

Reservado para `/reversa-coding`.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-06 | Correções após auditoria (`audit/cross-check.md`): maior cadeia de dependência corrigida de 15 para 17 ações, com o caminho real; `T028` acrescentado às dependências de `T029`; `T029` passa a registrar evidência em `evidence/`; `T021` cobria 7 arquivos e passou a cobrir os 8 que dependem de `gedcom_state` | reversa |
| 2026-10-06 | Decisões do usuário sobre os findings abertos: `T030` criada para verificar o bloqueio por divergência (`A004`); `are_spouses` incluído no probe de `T002` (`A007`); portabilidade incorporada ao teste de dependências de `T006` (`A009`); estado esperado da suíte entre `T007` e `T025` registrado como 163 aprovados + 1 falha intencional (`A008`) | reversa |
