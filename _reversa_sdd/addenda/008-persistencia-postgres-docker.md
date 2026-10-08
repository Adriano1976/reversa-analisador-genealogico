# Adendo: persistência histórica das análises em banco relacional

> Identificador da feature: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

## Vigência

Vigente desde 2026-10-08.

## Resumo da entrega

Entrega o **histórico das análises de DNA**: o que morria ao fim da requisição passa a ser
gravado — os dados das pessoas da árvore que a análise usou, os metadados dos kits e o
**veredito do confronto** (`COMPATIVEL` / `POSSIVEL` / `CONFLITANTE` / `INCONCLUSIVO`), com o
porquê de cada um. Entrega também a aplicação e o banco subindo juntos, com os dois estados
persistentes em volume: a pasta de uploads e os dados do banco.

A persistência entrou como **porta na fronteira** e como **projeção pura no caso de uso**,
com a borda montando o registrador. Nenhuma regra de domínio foi reescrita e nenhuma
constante numérica mudou — `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` não
têm **uma linha alterada** em toda a feature, o que torna o `RN-01` verificável por `diff`
em vez de por afirmação.

| Prova | Resultado |
|---|---|
| Suíte sem `DATABASE_URL` | **282 aprovados, 8 pulados** (linha de base: `261 aprovados`) |
| Suíte com o stack no ar | `2 falhas, 280 aprovados, 8 pulados` — as duas falhas são **guardas deliberadas** de `test_persistencia_desabilitada.py` |
| Paridade diferencial | **100 %**, exit 0, medida várias vezes |
| Núcleo intocado | **`diff` vazio** em `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` em todos os commits da feature |
| Contrato de tela | `src/templates/index.html` **+3 linhas, zero remoções** — nenhuma tela existente mudou de texto |
| RNF de Desempenho | **ATENDIDO**: `1,08×` em 19.682 pessoas / 71 matches (`5.088 ms` → `5.501 ms`, **+413 ms**) e `1,58×` em 728 pessoas / 21 matches, contra o teto de `2,00×` |
| Verificação de ponta a ponta | **APROVADA** (`T020`) e na verificação manual (`T021`) |

**Progresso: 26 de 26 ações concluídas**, nenhuma aberta em `actions.md`.

⚠️ **O adendo declara uma retratação.** O `T026` mediu `8,14×` com um fixture de **5 pessoas**
e a rodada registrou a falha **do critério**; a medição refeita em escala representativa dá
`1,08×`. O defeito era **do instrumento** — um fixture pequeno mede o próprio tamanho, não o
custo da gravação. O critério **não** foi afrouxado: o medidor é que foi consertado. É o
segundo defeito de instrumento desta feature, e o `OBS-22` registra o primeiro.

⚠️ **A Onda 3 do `cutover_plan.md` continua NÃO satisfeita.** A condição de go-live é um
**teste negativo de isolamento** — *"usuário A recebe `404` ao tentar acessar recurso de
usuário B"* —, e ele continua inexistente. `owner_id` **é coluna** e **nada filtra por ele**:
ele aparece em exatamente três lugares, e nenhum é `CREATE INDEX`, `CHECK` ou `WHERE`. As
dívidas **#3** (contaminação entre requisições concorrentes) e **#4** (ausência de
isolamento) seguem **abertas** (`RN-10`).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | `#1` (Visão Geral da Arquitetura) | `regra-alterada` | 🟡 Deixa de valer "sem banco de dados, sem persistência de resultados". `index()` passa a montar o registrador pela **regra dos três estados** e a repassar o aviso ao template. **Nenhum passo de domínio voltou para a rota** — persistir é I/O de borda |
| `_reversa_sdd/architecture.md` | `#2` (Containers) | `componente-novo` | O contêiner de aplicação que a extração registrava como inexistente existe (`docker/Dockerfile`), e o **primeiro contêiner de banco** existe (`docker-compose.yml`, `postgres:16-alpine`). Leia a topologia como **dois serviços em uma composição nomeada**, com volume nomeado para o banco e *bind mount* para `src/uploads/` |
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `contrato-novo` | A fronteira passa de **três para quatro portas**: `RegistroDeAnalises`, com cinco tipos de payload **plano**, para que o adaptador não conheça o formato do resultado do núcleo. ⚠️ A porta nova guarda o **resultado** da análise, não a árvore — o `RepositorioDeArvores` continua **declarado, sem implementação e sem consumidor** |
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `componente-novo` | `RegistroDeAnalisesPostgres` em `src/ports/adaptadores.py`. O `import psycopg2` é **preguiçoso**, e a razão é medida: o driver não está no `.venv/` do host, que é o interpretador da suíte e da paridade |
| `_reversa_sdd/architecture.md` | `#4` (Modelo de Dados) | `delta-de-dados` | 🟡 "**Sem banco de dados.** Não há DDL, migration, schema, ORM nem arquivo de configuração de persistência" deixa de ser verdade: há `init.sql` com **seis tabelas**. Leia o ERD lógico como agora tendo uma contraparte física **parcial** |
| `_reversa_sdd/architecture.md` | `#6` (Mapa de Integrações Externas) | `delta-de-contrato-externo` | 🟡 "**Zero integrações de rede**" deixa de ser verdade: o PostgreSQL é a **primeira** dependência externa de runtime. As portas publicadas ficam em `127.0.0.1` (`5080` e `5432`) |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #3 e #4 | `presença` | ❌ **INALTERADAS.** Nenhum comportamento de isolamento foi implementado e a guarda de exclusividade continua de **processo**, não de thread. `owner_id` é coluna sem filtro e sem índice |
| `_reversa_sdd/architecture.md` | `#7` (Dívidas), #8 ("nada é persistido entre requisições") | `regra-alterada` | A dívida **deixa de ser verdadeira**: o resultado da análise é gravado. A decisão de negócio que ela dizia faltar foi tomada em 2026-10-08 (`Q-01`). ⚠️ A leitura **não** é "a dívida fechou por completo": nada é **lido** do banco para decidir nada (`RN-12`) |
| `_reversa_sdd/domain.md` | `#3` (Regras de Negócio Principais) | `presença` | ❌ **NENHUMA regra criada, alterada ou removida.** A paridade em 100 % nas 6 fixtures é a prova, e ela é o instrumento que compara o núcleo contra o oráculo congelado |
| `_reversa_sdd/domain.md` | `#5` (Contrato de Mensagens ao Usuário) | `regra-nova` | ⚠️ **Texto NOVO visível ao operador**, e o único desta entrega: o aviso não bloqueante de que o histórico não foi registrado (`RF-17`, `RN-13`). Ele **só aparece no caminho de falha** e **não renderiza nada** quando é nulo. Não é mensagem do núcleo e não toca no `W016` |
| `_reversa_sdd/domain.md` | `#6` (Decisões Humanas Vigentes) | `presença` | ❌ O **single-tenant por aceite de risco** continua vigente (`adrs/18`), e o `BUG-20260929-BJJH` continua `active`/`mitigating`. ⚠️ **`owner_id` não é credencial:** nasce da constante `DONO_DO_PROCESSO = "unico"` |
| `_reversa_sdd/erd-complete.md` | `#6` (Inventário das 27 estruturas) | `delta-de-dados` | Seis tabelas reais onde o modelo extraído tinha **27 estruturas e nenhuma tabela**: `dna_analysis`, `analysis_person`, `match_result`, `match_kit`, `match_path_node`, `skipped_match`. Os nomes e as colunas vêm do DDL do alvo; duas extensões são **desta feature** (abaixo) |
| `_reversa_sdd/erd-complete.md` | `#7` (O que o ERD não tem) e `#8` (Lacunas) | `delta-de-dados` | Duas lacunas do alvo ficam **nomeadas** e resolvidas no físico: o **veredito** do confronto nos quatro estados e os **metadados de kit**. O artefato de migração **não** foi corrigido — a divergência está declarada no `RN-09` |
| `_reversa_sdd/dependencies.md` | `#2` (Dependências Diretas) | `regra-alterada` | As diretas passam de **oito para nove** (`psycopg2-binary==2.9.13`). **Nenhuma versão existente muda** |
| `_reversa_sdd/dependencies.md` | `#4` (Divergência entre o `.venv` e o `requirements.txt`) | `presença` | ⚠️ A divergência **piora de propósito**: `psycopg2-binary` está no arquivo e **não** está no `.venv` do host. Não é esquecimento — é o que mantém a suíte e a paridade independentes do banco (`RF-13`) |
| `_reversa_sdd/gaps.md` | `#6`, requisito 1 ("Persistir resultados e histórico de análises") | `regra-alterada` | 🔴 **Divergência declarada.** O `gaps.md#6` encaminhava a persistência ao **alvo** e dizia que criá-la no legado era "construir o que a Onda 3 substitui". Por decisão de 2026-10-08 (`Q-01`) a feature **reverte o adiamento** e grava no `src/`. Leia o requisito 1 como **atendido no legado**, e a divergência como deliberada. Os requisitos 2, 3 e 4 de `#6` seguem no alvo |
| `_reversa_sdd/permissions.md` | `P-01` a `P-05` | `presença` | ❌ Continua **zero** papel, **zero** sessão e **zero** autenticação. `P-01` segue decidida: a ausência de autenticação é **omissão**, e a correção pertence à Onda 3 |
| `_reversa_sdd/migration/target_data_model.md` | "Entidades de dados" e "Schema (DDL)" | `delta-de-dados` | ⚠️ **Conflito de forma no mesmo campo.** O alvo especifica `owner_id UUID NOT NULL REFERENCES app_user(user_id)` com índice de escopo; o físico desta feature tem `owner_id` **TEXT, sem FK e sem índice**. O `init.sql` **antecipa o nome e adia a forma** — a Onda 3 reconcilia |
| `_reversa_sdd/migration/cutover_plan.md` | "Onda 3 — Isolamento por usuário provado" | `presença` | ❌ **Continua NÃO satisfeita.** O teste negativo de `404` não existe, e o `RISK-005` continua sendo a condição de não-liberação da Onda 4 |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | `D-01`, `D-03`, `RF-08`, `RN-06` | `regra-alterada` | O adendo da 006 continua **vigente** e descreve **três** portas. Leia os dois juntos: este acrescenta a quarta e mantém a decisão de **nenhum ORM** (`D-03`) — o acesso é SQL escrito à mão |
| `_reversa_sdd/addenda/007-dono-no-port-e-baseline.md` | `W020`, `W022` e o "não implementa isolamento" | `presença` | ❌ **Nada a reescrever.** A 007 preparou a costura do dono; esta feature **usa** a costura e não lhe dá comportamento. O `W020` (o dono não entra na chave nem no caminho do armazenamento) continua verdadeiro |

**Contagem por tipo:** `presença` 7 · `regra-alterada` 5 · `delta-de-dados` 4 ·
`componente-novo` 2 · `contrato-novo` 1 · `delta-de-contrato-externo` 1 · `regra-nova` 1 —
**21 impactos**.

> **Nota sobre a taxonomia.** O `legacy-impact.md` desta feature usou dois rótulos que a lista
> genérica do `/reversa-sync` não prevê — `contrato-novo` e `contrato-alterado`, herdados da
> rodada de coding. Eles foram **preservados aqui** por serem mais precisos que `componente-novo`
> para a quarta porta. Não há, nesta entrega, impacto classificado como `regra-removida` nem
> como `componente-extinto`: **nada foi removido**.

## Regras sob vigilância

**O watch principal desta feature está vazio, e o adendo declara isso com a ressalva devida.**
`_reversa_forward/008-persistencia-postgres-docker/regression-watch.md` traz `(nenhum)` na
tabela do watch principal, mais as observações `OBS-01` a `OBS-24`. **Nenhum item `W0xx` foi
criado** — os últimos do projeto são `W020` a `W025`, da feature 007.

⚠️ **Duas ressalvas, porque a ausência de watch item é ambígua aqui:**

1. **A justificativa registrada no arquivo está obsoleta.** Ela diz que o watch está vazio
   "porque a execução parou no `T001` antes de escrever qualquer arquivo" — o que era verdade
   na **primeira** rodada e deixou de ser nas seguintes. A **conclusão** (nenhuma regra 🟢
   modificada) continua correta; o **motivo** não. A tabela deveria dizer que o watch deriva
   das regras marcadas como *Modificadas* no `legacy-impact.md`, e que ali não há nenhuma.
2. **Há um candidato a watch item que não foi criado.** Esta entrega acrescenta **texto novo
   visível** ao operador (o aviso não bloqueante de `RF-17`), e o `W005` da feature 006 existe
   exatamente para vigiar *"literais de tela ao caractere, caso a caso"*. O aviso é texto novo,
   não alteração de literal existente — e por isso não viola o `W005` —, mas **não há item
   vigiando o literal que ele introduz**. Registrado como lacuna, não corrigido: o `/reversa-sync`
   escreve apenas em `addenda/`.

**Itens herdados que esta entrega tem de respeitar, e respeita** (definidos em
`_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` e
`_reversa_forward/007-dono-no-port-e-baseline/regression-watch.md`):

| Item | Cobre | Situação nesta entrega |
|---|---|---|
| `W005` | Literais de tela ao caractere, caso a caso | ✅ Nenhum literal existente mudou; o template ganhou **+3 linhas e nenhuma remoção** |
| `W012` | Chave por conteúdo, validação antes da gravação | ✅ O banco guarda a **referência**, não o arquivo (`RN-04`) |
| `W016` | Assinatura de retorno do núcleo congelada | ✅ `src/core/dna_analysis.py` devolve a tupla de três, sem uma linha alterada |
| `W017` | Nenhum teste removido ou desabilitado | ✅ **21 testes acrescentados**; a única alteração em teste existente reabre, por decisão declarada (`D-01`), a lista de `__all__` que a 007 prendia |
| `W018` | Paridade em 100 % | ✅ Medida, exit 0 |
| `W020` | O dono não entra na chave nem no caminho do armazenamento | ✅ Verdadeiro, e mais forte: o dono também **não** entra em nenhum `WHERE` |
| `W021` | O `tmp_path` da suíte é o do projeto | ✅ **Intocado** por esta feature |
| `W024` | Os 15 testes de rota executam, e nenhum foi reescrito | ✅ Executam; nenhum foi reescrito |

## Divergências declaradas contra a extração

Quatro divergências ficam registradas em vez de silenciadas, e **nenhuma é erro de execução**:
todas foram decididas antes do código, com o operador, na sessão de esclarecimento de
2026-10-08 (`_reversa_forward/008-persistencia-postgres-docker/requirements.md#9`).

| # | A extração dizia | A entrega fez | Decisão |
|---|---|---|---|
| 1 | `gaps.md#6`: persistir é requisito **do alvo**, e criá-lo no legado é construir o que a Onda 3 substitui | Persistência **no `src/`**, agora | `Q-01` — reversão deliberada do adiamento |
| 2 | `architecture.md#6`: "zero integrações de rede" | PostgreSQL como primeira dependência de runtime | `Q-05` — layout fixado na raiz e em `docker/` |
| 3 | `ambiguity_log.md` `AMB-017` e `risk_register.md` `RISK-005`: criptografia em repouso antes do go-live | **Sem** criptografia em repouso | `Q-04` — aceite de risco de 2026-10-08, mesmo regime do `BUG-BJJH`. **Cobre a ausência agora, não dispensa o requisito** |
| 4 | `target_data_model.md`: `owner_id` é invariante com FK e índice de escopo | `owner_id` TEXT, sem FK e sem índice | `RN-10` — a forma é da Onda 3; esta entrega **antecipa o nome** |

## O que a extração **não** precisa mudar

- **A forma dos dados do núcleo.** O `Tree` continua a tupla de quatro elementos, e
  `path_search` e `dna_analysis` continuam devolvendo a tupla de três com o indicador de
  sucesso. Nenhum campo de desfecho entrou no núcleo.
- **A superfície HTTP.** Mesmas rotas, mesmos campos de formulário, mesmos status, mesmos
  redirecionamentos, mesmo template. `DATABASE_URL` é variável de **processo**: não é campo de
  formulário nem cabeçalho.
- **A decisão da análise.** Nada é lido do banco para decidir o que a tela mostra (`RN-12`).
  O banco é **histórico**, e é essa propriedade que preserva a arquitetura de funções puras.
- **O leiaute de `src/uploads/`.** Nenhum arquivo precisa ser renomeado ou movido, e nenhum
  foi. O *bind mount* do compose preserva os 35 arquivos existentes através de `down` + `up`.
- **Os artefatos de `migration/`.** Continuam válidos como plano de ondas futuras e **não**
  foram reescritos. A Onda 3 continua **No-go**, com uma condição a menos: o esquema físico já
  existe.

## Lacunas declaradas

Nem tudo neste adendo é afirmação verificada. O que segue é limite de conhecimento, e não
omissão:

1. **Oito testes do adaptador nunca executaram no host — os oito pulos da suíte são deles.**
   `tests/test_registro_de_analises.py` está escrito e marcado com `skipif`: dois testes
   independentes e seis parametrizações. Os oito são pulados porque o host não tem o driver e a
   suíte roda **sem** `DATABASE_URL` (política `D-17`). **Um teste pulado não é um teste que
   passou.** A prova dos mesmos caminhos com o banco no ar é do `T020` — 24 conferências,
   0 falhas, executadas **dentro do contêiner**.
2. **Dois números da suíte convivem, e é de propósito.** Sem a variável: `282 aprovados,
   8 pulados`. Com o stack no ar e a variável definida: `2 falhas, 280 aprovados, 8 pulados`,
   e as falhas são **guardas deliberadas** que prendem o estado desabilitado. O estado
   **suportado** da suíte é o **sem** `DATABASE_URL`.
3. **O `T026` foi medido com fixture sintética, não com o GEDCOM real.** O caso real tem 71
   conexões; o fixture de 19.682 pessoas foi construído para reproduzir essa ordem de grandeza.
   A medição é **representativa**, não **a** medição do arquivo de 5,3 MB.
4. **A remoção do `detail` exigiu recriar o volume.** `CREATE TABLE IF NOT EXISTS` não altera
   tabela existente. Quem for reconstruir o ambiente do zero precisa de `docker compose down -v`
   se o volume for anterior a essa correção.
5. **Dois achados da auditoria continuam abertos.** O `B001` (citação parcialmente corrigida no
   `roadmap.md`) e o `B002` (o `T026` cita o §0 como linha de base que não existe lá) não foram
   tocados. O `B003` foi **fechado** por `tests/test_projecao_da_analise.py`.

## Fontes

- `_reversa_forward/008-persistencia-postgres-docker/legacy-impact.md` (fonte principal do delta)
- `_reversa_forward/008-persistencia-postgres-docker/regression-watch.md` (`OBS-01` a `OBS-24`)
- `_reversa_forward/008-persistencia-postgres-docker/requirements.md` (objetivo, `RN-01` a
  `RN-13`, `RF-13`, `RF-14`, `RF-17`, §9 `Q-01` a `Q-05`, §12 fora de escopo)
- `_reversa_forward/008-persistencia-postgres-docker/actions.md` e `roadmap.md` (26 de 26)
- `_reversa_forward/008-persistencia-postgres-docker/progress.jsonl` (26 `done`, 1 `blocked`,
  2 `failed`, 5 `corrected` — o `blocked` e os `failed` são **históricos**, e a última
  `corrected` retrata a leitura errada do `T026`)
- `_reversa_forward/008-persistencia-postgres-docker/evidence/` — `T020-ponta-a-ponta.md`,
  `T021-verificacao-manual.md`, `T022-linha-de-base-bloco1.md`, `T025-varredura-de-credencial.md`,
  `T026-custo-da-gravacao.md`, `T023-conferencia-de-escopo.md`
- `_reversa_forward/008-persistencia-postgres-docker/audit/cross-check.md` (`B001`, `B002`, `B003`)
