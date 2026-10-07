# Investigation: núcleo puro em `src/core/`

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Requirements: `_reversa_forward/005-nucleo-puro-src/requirements.md`

## 1. Pergunta investigada

O `src/core/` já contém toda a decisão de domínio, não conhece HTTP e não faz I/O de arquivo. **Por que ele ainda não é um núcleo puro, e o que exatamente falta?**

A investigação partiu de uma suspeita registrada em `_reversa_sdd/architecture.md#1` — "o mecanismo de integração entre as camadas é estado global mutável, e não injeção de dependência" — e foi verificar cada ponto de acoplamento no código atual, não nos artefatos.

## 2. Achados, medidos no código

### 2.1 Onde o estado global vive, e quem o lê

`src/core/gedcom_state.py` tem **39 linhas** e declara cinco nomes mutáveis: `people`, `families`, `graph`, `child_to_family` e `versao`. Nenhum dos cinco é constante: o parse os substitui a cada carga.

Consumidores, por arquivo de origem:

| Módulo | Nomes que consome | Como |
|---|---|---|
| `src/parsers/gedcom_parser.py` | os quatro + `versao` | **Escreve**: `clear()` + `update()` nos três dicionários, reatribui `graph`, incrementa `versao` (linhas 62-67) |
| `src/core/documentary_relationship.py` | `child_to_family`, `families`, `get_name`, `people`, `ref_id`, `gedcom_state.versao` | O maior consumidor: 13 usos, incluindo o cache `_INDICE_DE_NOMES` |
| `src/core/family_navigation.py` | `child_to_family`, `families`, `get_name`, `people`, `ref_id` | Import no topo |
| `src/core/path_finding.py` | `people` (topo) e `graph` (**dentro da função**) | Import tardio documentado como contrato |
| `src/core/matching.py` | `get_name`, `people` | Import no topo |
| `src/core/dna_analysis.py` | `get_name`, `people` | Import no topo |
| `src/core/path_search.py` | `get_name`, `people` | Import no topo |
| `src/core/diagram_domain.py` | `get_name`, `people` | Import **dentro** do resolvedor |
| `src/parsers/csv_ingest.py` | nenhum de estado | Já é folha em relação ao estado |

### 2.2 A assimetria que explica o resto

`people`, `families` e `child_to_family` são **mutados in place**, então um `import` no topo continua apontando para o objeto vivo. `graph` é **reatribuído**, então um import no topo ficaria preso ao grafo antigo — e é por isso que `path_finding.py:38` importa dentro da função.

Essa assimetria é a origem de três artefatos estranhos que o código carrega hoje, todos documentados em docstring como se fossem contrato:

1. **O import dentro da função** em `path_finding.py:38`, que existe só para não ficar preso ao grafo velho.
2. **O contador `versao`**, que existe porque `id()` não muda com mutação in-place e alguém precisa sinalizar que a árvore mudou (`gedcom_state.py:25-30`).
3. **O resolvedor de diagrama** em `diagram_domain.py:25`, que devolve um `dict` com `people` **capturado naquele instante** — e não uma consulta. Ver 2.3.

Nenhum dos três é regra de negócio. Os três são consequência do mecanismo de estado, e os três desaparecem quando a árvore vira parâmetro.

### 2.3 O resolvedor captura o dicionário, e isso é um risco latente

`diagram_domain.resolvedor_de_diagrama()` devolve `{"people": people, ...}` — o **objeto** do dicionário, não uma função que o consulta. Em `dna_analysis.py:169` e `path_search.py:173` o resolvedor é montado **depois** do parse, então hoje funciona.

O risco aparece porque `load_gedcom_and_build_graph` muta o dicionário existente em vez de substituí-lo: quem montar o resolvedor **antes** de um segundo parse recebe um mapeamento que aponta para o dicionário **certo** (mutado in place) mas com o `graph` da **mesma** chamada — e o `graph` é justamente o que é reatribuído. A combinação "captura no momento" + "duas políticas de substituição diferentes" é frágil por construção.

Isto **não** é um defeito observado em produção: é a razão de a `RN-02` e a `RF-01` tratarem o resolvedor como componente próprio do delta, e não como detalhe.

### 2.4 A remoção do global alcança os testes

Sete arquivos de teste leem `gedcom_state` diretamente:

| Arquivo | O que lê |
|---|---|
| `tests/test_upload.py` | `people`, `families`, `child_to_family`, `graph`, `get_name`, `ref_id` |
| `tests/test_dna_analysis.py` | o módulo inteiro, via fixture `dna_loaded` |
| `tests/test_path_search.py` | o módulo inteiro, via fixture |
| `tests/test_characterization_matching.py` | o módulo inteiro, via fixture |
| `tests/test_characterization_mermaid.py` | o módulo inteiro, via fixture |
| `tests/test_formatacao_cm.py` | indiretamente, via `load_gedcom_and_build_graph` |
| `tests/test_mermaid_escape.py` | indiretamente, via `load_gedcom_and_build_graph` |
| `tests/test_confrontacao_gedcom_dna.py` | indiretamente, via `load_gedcom_and_build_graph` (linha 384) |

**Consequência para o plano:** a atualização do encanamento dos testes **não é opcional nem acidental** — é parte da entrega. Isso foi registrado como `D-09` no `roadmap.md`, com a proibição explícita de afrouxar asserção para a suíte passar. O precedente é conhecido e está documentado: `parity_harness.md` §DIV-001a registra que a asserção `in ("Sem Nome", "")` não podia falhar por construção, e que foi justamente ela que deixou a divergência passar por 47 testes.

> ⚠️ **Correção de 2026-10-06.** Esta tabela listava **sete** arquivos e omitia `test_confrontacao_gedcom_dna.py`, que tem 922 linhas e cobre o confronto GEDCOM × DNA. O achado foi `A012` de `audit/cross-check.md`, e a contagem correta é **oito**.

### 2.5 O que NÃO está acoplado a estado

Vale registrar o que a investigação **não** encontrou, porque reduz o escopo:

- **Nenhum framework no núcleo.** `flask` aparece só em `src/app.py`. Não há `fastapi`, `sqlalchemy`, `pydantic` nem `waitress` em `src/`.
- **Nenhum I/O no núcleo.** `open()`, `os.makedirs` e `os.environ` aparecem apenas em `src/app.py` e `src/utils/validate.py`.
- **`utils/` é folha real.** Nenhum módulo de `utils/` importa outro módulo do projeto — confirmado por varredura de imports.
- **`csv_ingest` já é funcionalmente puro** em relação ao estado: recebe e devolve valores.

### 2.6 Números medidos em 2026-10-06

| Pacote | Linhas |
|---|---:|
| `src/core/` (13 módulos, sem `__init__`) | 1.982 |
| `src/parsers/` (2 módulos) | 252 |
| `src/reporting/` (1 módulo) | 252 |
| `src/utils/` (4 módulos) | 225 |
| `src/app.py` | 258 |
| **Total** | **~2.969** |

O `architecture.md#3` de 2026-10-05 registra **3.489** linhas. A diferença (~500) **não foi reconciliada** nesta investigação; os três refactors de 2026-10-06 (`2443273`, `87bcea5`, `d062c20`) removeram superfície e código morto, e é a explicação mais provável, mas não foi medida. Registrado como lacuna.

## 3. Alternativas avaliadas

### A. Árvore por parâmetro explícito (escolhida)

As quatro estruturas entram como parâmetro em cada função de núcleo. `parsers/` devolve o valor; `app.py` monta e repassa.

- **A favor:** é a única opção que satisfaz a `RF-01` sem criar um novo mecanismo de escopo. Não introduz classe com estado, respeitando a proibição do `paradigm_decision.md` sobre objetos com estado no cálculo.
- **Contra:** é a maior mudança de assinatura, e alcança **8 arquivos de teste** (4 pelo módulo direto e 4 pelo retorno do parse) e o harness.

### B. Objeto de contexto (`dict` ou dataclass) passado adiante

Um único parâmetro `arvore` em vez de quatro.

- **A favor:** menos parâmetros por assinatura; legível.
- **Contra:** um `dict` mutável compartilhado é o estado global **com outro nome** — o mesmo modo de falha que a feature existe para eliminar, apenas com escopo menor. Uma `dataclass` congelada evitaria isso, mas é decisão de forma que o `paradigm_decision.md` manda não introduzir no núcleo de cálculo, e o ganho sobre quatro parâmetros é cosmético. **Descartada.**
- **Nota:** em dois pontos o núcleo já usa `dict` como contrato — `resolvedor_de_diagrama()` devolve um `dict` de funções. O padrão existe no projeto, mas ali ele carrega **funções**, não dados mutáveis, e é justamente o que a investigação 2.3 mostra como frágil. Não é precedente a favor da opção B.

### C. Injeção de dependência com contêiner

Um resolvedor de dependências monta o núcleo com a árvore injetada.

- **A favor:** familiar para quem vem de FastAPI.
- **Contra:** resolve um problema de **borda** (ciclo de vida, escopo, tenant) que esta feature não tem, e não resolve o problema de **pureza** — a função continua dependendo de algo externo ao seu escopo. O `paradigm_decision.md` reserva DI para a fronteira, e o núcleo é declaradamente funções puras. **Descartada.**

### D. Manter o global e provar paridade assim mesmo

- **Contra:** o `cutover_plan.md` exige o núcleo isolável para a Onda 1, e o `topology_decision.md` proíbe `core/` de carregar estado. Manter o global tornaria a Onda 2 (multiusuário) impossível sem refazer o trabalho. **Descartada** — já excluída por decisão de 2026-09-28.

### E. Reescrever tudo de uma vez, sem passos intermediários

- **Contra:** durante a reescrita não haveria ponto de medição. O plano escolhido migra **módulo a módulo**, rodando o harness a cada passo, para que uma divergência seja atribuível a um módulo e não ao conjunto. **Descartada.**

## 4. Padrões aplicáveis — apenas os já previstos nas specs

| Padrão | Onde entra | Autorizado por |
|---|---|---|
| **Branch by Abstraction** | É o padrão da entrega: a assinatura nova é introduzida e os consumidores migram atrás dela, no mesmo módulo, sem troca de sistema | `migration_strategy.md#Decisão humana` (estratégia C usa D como padrão interno) |
| **Ports & Adapters** | Não é exercido aqui na fronteira HTTP; a feature para na borda do processo. O que a feature faz é preparar o núcleo para que os ports existam depois | `topology_decision.md#Decisão do usuário` |
| **Repository** | **Não** entra nesta onda. Persistência é Onda 3 | `migration_strategy.md` § sequenciamento |
| **DI** | **Não** entra nesta onda, e não entra no núcleo. É plumbing de borda | `paradigm_decision.md#Implicações` |

> Nenhum padrão novo é introduzido. O `paradigm_decision.md` proíbe acrescentar padrão sem justificar e sem consultar, e esta feature não precisou de nenhum.

## 5. Instrumentos existentes que a feature reusa

| Instrumento | Caminho | Estado |
|---|---|---|
| Oráculo congelado | `_reversa_sdd/oracle/app_legacy_e43ca22.py` | Íntegro, sha256 `44370b23…`, somente leitura |
| Runner do oráculo | `_reversa_sdd/oracle/run_oracle.py` | Funcional |
| Harness diferencial | `_reversa_sdd/parity/harness.py` | Funcional, com o candidato apontado para `src/` (`harness.py:41`) |
| Fixtures | `_reversa_sdd/parity/fixtures/` | 13 arquivos (6 GEDCOM, 7 CSV) |
| Gerador de fixtures | `_reversa_sdd/parity/make_fixtures.py` | Funcional |
| Limpador de resíduo | `_reversa_sdd/parity/_clean_residue.py` | Funcional |
| Verificador de hashes | `_reversa_sdd/parity/_verify_hashes.py` | Funcional |
| Contraprova de regressão | `_reversa_sdd/parity/_verify_fix_gives_parity.py` | Mantida para o caso DIV-001 |
| Cenários Gherkin | `_reversa_sdd/migration/parity_tests/` | 12 arquivos, 102 cenários, **sem runner** |

## 6. Lacunas e observações

1. 🔴 **A diferença de ~500 linhas** entre a contagem medida (2.969) e o `architecture.md#3` (3.489) não foi reconciliada. Vale reconciliar antes do `/reversa-sync`, porque o `inventory.md` carrega os números antigos.
2. 🔴 **O `parity_harness.md#Cobertura dos probes` promete mais do que o `harness.py` entrega.** O artefato afirma cobertura "exaustiva" do núcleo; os probes reais (`harness.py:111-144`) cobrem 14 famílias e **não incluem `match_candidates` nem `build_ged_indexes`**. A correção do artefato é da Onda 1, junto com a instrumentação (`RF-10`).
3. 🔴 **A contagem de cenários Gherkin é 102, não 99.** O `parity_harness.md:13` diz "102 cenários" e o `handoff.md` e o `parity_specs.md` dizem 99. Medido: 102. Divergência de registro, sem efeito prático.
4. 🟡 **`cm_estimator` é legado fora do fluxo** (`adrs/19`) e é reexportado por `dna_analysis`. A limpeza de superfície (`D-05`) remove o **reexport**; a remoção do módulo é decisão própria e **não** faz parte desta feature.
5. 🟡 **`ANALISADOR_THREADS = 4`** com estado global é a dívida #3 do `architecture.md#7` (contaminação entre requisições concorrentes). Esta feature **reduz a superfície** do problema, porque remove o global que as threads compartilham, mas **não** fecha a dívida: a concorrência de thread e o escopo por usuário são da Onda 3.
6. 🟡 **O ambiente de teste tem restrição de diretório temporário.** A suíte só completa com `TEMP` apontando para um caminho gravável; sem isso o `pytest` falha na criação do diretório, antes de coletar. Registrado para não ser confundido com regressão.
7. 🟡 **O `harness.py` deixa resíduo não rastreado** (`_collect_oracle.py`, `_collect_cand.py`, `_obs_oracle.json`, `_obs_cand.json`, `.parity-run-*/`). O `parity_harness.md` §7 manda limpar com `_clean_residue.py`. Na verificação de 2026-10-06 havia resíduo na árvore de trabalho.

## 7. Fontes consultadas

- `_reversa_sdd/architecture.md` §1, §3, §7 (mecanismo de estado, ciclos de pacote, dívidas)
- `_reversa_sdd/code-analysis.md` §2.2, §3.1, §3.2, §4.2, §4.5 (funções e regras por unidade)
- `_reversa_sdd/migration/paradigm_decision.md` §Implicações
- `_reversa_sdd/migration/topology_decision.md` §Decisão do usuário
- `_reversa_sdd/migration/migration_strategy.md` §Decisão humana
- `_reversa_sdd/migration/parity_harness.md` (inteiro)
- `_reversa_sdd/oracle/ORACLE_MANIFEST.md` §Dependências congeladas, §Restrições de uso
- `.reversa/principles.md` (Princípios I a V)
- Código de `src/` e de `tests/`, medido em 2026-10-06

## 8. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-plan` | reversa |
