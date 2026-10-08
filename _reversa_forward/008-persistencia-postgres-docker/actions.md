# Actions: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Roadmap: `_reversa_forward/008-persistencia-postgres-docker/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | **26** |
| Concluídas nesta rodada | **25** de 26 — `T001` a `T025` |
| **Falhou** | **1** — `T026`, que **não atendeu o critério**: mediu `8,14×` contra o limite de `2,00×`. A falha é **do critério**, e não da implementação — ver `evidence/T026-custo-da-gravacao.md` |
| Paralelizáveis (`[//]`) | **11** (`T002`, `T003`, `T004`, `T007`, `T009`, `T010`, `T013`, `T015`, `T018`, `T019`, `T024`) |
| Maior cadeia de dependência | **14 ações** (13 elos): `T001` → `T004` → `T005` → `T006` → `T008` → `T009` → `T011` → `T012` → `T013` → `T016` → `T017` → `T020` → `T021` → `T022` |
| Linha de base herdada | `261 passed`, `0 errors` e paridade `100 %` — medidos em 2026-10-08, **antes** do plano, com o comando em `roadmap.md` §0 |
| Linha de base a **produzir** | Dois números, lado a lado: a suíte **sem** `DATABASE_URL` e a suíte **com** o stack no ar. Nenhum deles é prometido aqui — o `T022` mede os dois |

**Composição:** 7 ações de preparação, 4 de teste, 6 de núcleo, 4 de integração e 5 de polimento.

> ⚠️ **A ordem é o plano, e ela tem uma razão só — a mesma da feature 007.** O **Bloco 0**
> (`T001` a `T011`) devolve **infraestrutura e esquema** e **não toca uma linha de Python de
> produção**; o **Bloco 1** (`T012` a `T021`) faz a **costura**; o **Bloco 2** (`T022` a
> `T026`) confere o **escopo**, as **credenciais** e o **custo**. A costura não começa antes
> de o Bloco 0 estar medido, porque
> o risco de contêiner e de esquema é de outra natureza que o risco de costura — e misturar
> os dois deixa uma falha sem ponto de atribuição. O `T011` é o portão: se a suíte ou a
> paridade se moverem ali, o problema é **infraestrutura**, e não persistência.

> ⚠️ **`T001` pode parar o Bloco 0 inteiro, e isso é o desenho.** A política de edição do
> legado precisa liberar `docker/**`, `docker-compose.yml`, `init.sql` e `.dockerignore`
> antes de qualquer escrita na raiz. O Reversa **não** edita `.reversa/reversa-config.json`
> por iniciativa própria: a liberação é ato do usuário, e o `T001` existe para que a parada
> aconteça no primeiro passo, nomeada, em vez de no meio do bloco.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Verificar o **pré-requisito de permissão**: ler `.reversa/reversa-config.json` e conferir que `allowedPaths` cobre `docker/**`, `docker-compose.yml`, `init.sql` e `.dockerignore`. Registrar o array bruto lido. Se faltar qualquer um dos quatro, **parar** e reportar ao usuário — a liberação é ato dele | - | - | `_reversa_forward/008-persistencia-postgres-docker/evidence/` | 🟢 | `[X]` |
| T002 | Escrever o `.dockerignore` **na raiz do projeto** como **lista de permissão**, e não de negação: `*` na primeira linha, depois `!requirements.txt`, `!src/` e `!src/**`, e por último `src/uploads/` e `src/**/__pycache__/` para reexcluir — a última regra que casa vence. A raiz é obrigatória, porque o Docker só lê este arquivo no **topo do contexto de build**, e a lista de permissão é imune a resíduo novo na raiz, preso ou não (`D-11`, `D-18`) | T001 | `[//]` | `.dockerignore` | 🟢 | `[X]` |
| T003 | Escrever `docker/Dockerfile`: base `python:3.14-slim`, `WORKDIR /app`, `COPY requirements.txt` seguido de `pip install --no-cache-dir -r requirements.txt`, `COPY src/ /app/src/`, `ENV ANALISADOR_HOST=0.0.0.0`, `ENV ANALISADOR_PORT=5000`, `EXPOSE 5000` e `CMD ["python", "src/app.py"]`. O `COPY` é **estreito** — duas origens nomeadas, e a raiz nunca é copiada (`D-10`, `D-11`) | T001 | `[//]` | `docker/Dockerfile` | 🟢 | `[X]` |
| T004 | Escrever `init.sql` com as **quatro tabelas herdadas** do DDL do alvo — `dna_analysis`, `match_result`, `match_path_node` e `skipped_match` —, com `gen_random_uuid()` nas chaves e as chaves estrangeiras entre elas. **Toda criação com `IF NOT EXISTS` e nenhum `DROP`**, porque a idempotência é requisito e não consequência (`D-06`, `D-07`, `RF-12`) | T001 | `[//]` | `init.sql` | 🟢 | `[X]` |
| T005 | Acrescentar a `init.sql` as **extensões** do `D-06`: o bloco do veredito em `match_result` (`comparison_status`, `comparison_label`, `comparison_method`, `expected_low`, `expected_high`, `expected_average`, `comparison_detail`, `causes`, `observations`, `detail`, `documentary_status`, `csv_name`, `relationship_key`, `meioses`, `mrca_xref`), as tabelas `match_kit` e `analysis_person`, os `CHECK` de quatro estados e os índices do `data-delta.md` §4. **`IF NOT EXISTS` em tudo, sem `DROP`**, e nenhum índice pode começar por `owner_id` (`RN-10`, `D-07`) | T004 | - | `init.sql` | 🟢 | `[X]` |
| T006 | Escrever `docker-compose.yml` com **dois** serviços. `db`: `postgres:16-alpine`, volume **nomeado** em `/var/lib/postgresql/data`, **bind mount somente-leitura de `./init.sql` em `/docker-entrypoint-initdb.d/init.sql`** (sem ele o `T009` não tem o que executar), `healthcheck` com `pg_isready` e publicação apenas em `127.0.0.1`. `app`: build com `dockerfile: docker/Dockerfile`, bind mount `./src/uploads:/app/src/uploads`, `ANALISADOR_HOST=0.0.0.0`, `DATABASE_URL` vinda do ambiente **sem valor padrão**, e `depends_on` na forma curta — **sem** `condition: service_healthy` (`D-07`, `D-08`, `D-09`, `D-10`) | T003, T005 | - | `docker-compose.yml` | 🟢 | `[X]` |
| T007 | Acrescentar `psycopg2-binary==2.9.13` ao `requirements.txt`, junto das diretas, com uma linha dizendo que a versão está fixada pelo mesmo motivo das outras e que o pacote é usado **só** pela porta de registro (`D-03`, `RF-15`) | T001 | `[//]` | `requirements.txt` | 🟢 | `[X]` |

> **Sobre `T002`, `T003`, `T004` e `T007`.** As quatro dependem apenas do `T001` e tocam
> arquivos alvo **distintos** — `.dockerignore`, `docker/Dockerfile`, `init.sql` e
> `requirements.txt`. Podem rodar em qualquer ordem, e é por isso que as quatro levam `[//]`.
> O `T003` **escreve** o Dockerfile; ele não constrói a imagem, porque a construção precisa do
> pin do `T007` e da verificação do `T010`.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Subir o stack com `docker compose up -d --build`, conferir **dois** serviços em `docker compose ps` (com o `db` em `healthy`) e provar que a aplicação responde `200` em `http://127.0.0.1:5080/`. Registrar os três comandos e as três saídas (`RF-01`) | T006, T007 | - | `evidence/T008-stack-no-ar.md` | 🟢 | `[X]` |
| T009 | Provar a **idempotência** do `init.sql`: contar as tabelas, executar o script outra vez por `docker compose exec`, e contar de novo, esperando **6** nas duas contagens e nenhum erro na execução do meio. Registrar as duas saídas (`RF-12`, `D-07`) | T008 | `[//]` | `evidence/T009-idempotencia-init-sql.md` | 🟢 | `[X]` |
| T010 | Provar que o **contexto de build não leva dado real**: medir o tamanho do contexto em `docker build` e provar por `docker run` que `src/uploads/` **não** existe na imagem. Registrar as duas saídas. É o portão do Princípio I e o teste do `D-11` | T003, T007 | `[//]` | `evidence/T010-contexto-de-build.md` | 🟢 | `[X]` |
| T011 | Medir e registrar a **linha de base do Bloco 0**: suíte completa e paridade diferencial, com o comando ao lado de cada número, confirmando `261 passed` e `PARIDADE 100 %` — porque nenhuma linha de Python de produção mudou ainda. É o **portão do Bloco 0** (`RF-13`, `D-14`) | T008, T009, T010 | - | `evidence/T011-linha-de-base-bloco0.md` | 🟢 | `[X]` |

> **`T011` é o portão do Bloco 0.** Ele é a única ação que pode dizer "a infraestrutura não
> tocou o produto". Se a suíte ou a paridade se moverem aqui, a causa é de **infraestrutura**
> — um `pip install` que trocou uma versão, um arquivo de produção tocado por engano —, e o
> Bloco 1 não começa antes disso estar nomeado. Um Bloco 0 que fecha sem este número
> registrado não fecha.

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Declarar a porta `RegistroDeAnalises` (`Protocol`) em `src/ports/__init__.py`, com **um** método que recebe a análise já projetada e o `dono`, e devolve `(referencia, aviso)`. As docstrings registram que o `dono` **não** filtra nada (`RN-10`), que o `aviso` existe no lugar da exceção (`RN-13`) e que esta porta **não** é o `RepositorioDeArvores`, que segue sem implementação (`D-01`) | T011 | - | `src/ports/__init__.py` | 🟢 | `[X]` |
| T013 | Implementar `RegistroDeAnalisesPostgres` em `src/ports/adaptadores.py`: o construtor **só** guarda a string de conexão, a conexão é aberta e fechada **dentro** da chamada, a análise inteira vai em **uma** transação, o motivo da falha volta como **texto** em vez de exceção, e os textos (`observations`, `causes`, `detail`) são gravados **ao caractere**, sem persistir o código do aviso (`D-02`, `D-03`, `D-04`, `D-05`, `D-16`) | T012 | `[//]` | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T014 | Escrever o teste do adaptador contra o banco do compose, **marcado para pular** quando `DATABASE_URL` está ausente (`D-17`): os quatro estados gravados e relidos, dois kits do mesmo nome **sem soma entre eles e com o estado final gravado sendo o mais conservador dos dois**, campo desconhecido entrando `null` em vez de zero, e a **ida e volta do cM** nos valores de fronteira 46, 200, 553, 1317, 2200 e 3300 (`RF-05`, `RF-06`, `RF-09`, `RN-05`, `RN-11`, `RISK-004`) | T013 | - | `tests/test_registro_de_analises.py` | 🟢 | `[X]` |
| T015 | Fazer o caso de uso `src/application/dna_analysis.py` receber a porta **com padrão `None`** — ausente significa **não registrar**, que é o estado desabilitado do `D-02` —, montar o payload por **projeção pura** do resultado, sem chamar nenhuma função do núcleo e sem recalcular nada (`D-15`), e devolver o aviso em `ResultadoDeAnalise.aviso_de_persistencia`, campo novo com valor padrão | T012 | `[//]` | `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T016 | Implementar a **regra dos três estados** em `src/app.py`: montar o registrador **uma única vez** na borda (nulo quando não há `DATABASE_URL`, concreto quando há), repassá-lo à chamada do caso de uso e entregar o aviso ao template. Nenhuma conexão pode acontecer no import (`D-02`) | T013, T015 | - | `src/app.py` | 🟢 | `[X]` |
| T017 | Renderizar o aviso de persistência em `src/templates/index.html`, reusando a classe `.alerta-aviso` que já existe na linha 27, sob uma condição que **não renderiza nada** quando o aviso é nulo. Nenhum CSS novo, nenhum bloco novo quando a persistência está desabilitada ou bem-sucedida (`RF-17`, `D-02`) | T016 | - | `src/templates/index.html` | 🟢 | `[X]` |

> **Sobre `T013` e `T015` serem paralelas.** Tocam arquivos alvo diferentes
> (`src/ports/adaptadores.py` e `src/application/dna_analysis.py`), nenhuma lê o que a outra
> escreve, e as duas dependem apenas do `T012`. É o mesmo critério que a feature 007 aplicou
> ao `T006`/`T007` dela.

> **Por que `T015` usa padrão `None`, e o `dono` da feature 007 não usou.** São decisões
> opostas porque os problemas são opostos. Lá, o padrão esconderia a costura e adiaria a Onda
> 3; aqui, `None` **é** o estado desabilitado, e ele é semanticamente verdadeiro: sem
> `DATABASE_URL` não há o que registrar. Com padrão, as chamadas existentes do caso de uso
> continuam válidas **sem alteração** — que é exatamente o que o `RF-13` quer dizer.

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Escrever o teste do estado **desabilitado**: importar `src/app.py` **sem** `DATABASE_URL` e afirmar que a página de DNA é idêntica à de antes da feature, com o registro desligado e **nenhum** aviso. É o teste que prende a `D-02` e o `RF-13` | T016, T017 | `[//]` | `tests/test_persistencia_desabilitada.py` | 🟢 | `[X]` |
| T019 | Escrever o teste do estado de **falha**: com a persistência habilitada e a gravação **recusada por alvo inválido** — `DATABASE_URL` apontando para uma porta fechada —, a análise conclui, o veredito é o mesmo e o aviso não bloqueante aparece, e **nenhum** registro parcial permanece. É o teste do `RF-10` e do `RF-17` | T016, T017 | `[//]` | `tests/test_persistencia_indisponivel.py` | 🟢 | `[X]` |
| T020 | Executar a persistência **ponta a ponta** pelos três fluxos da rota, com o stack no ar e `DATABASE_URL` presente, e conferir por consulta SQL que a análise, as pessoas usadas, os kits e o veredito com o porquê estão gravados, na ordem exibida. Registrar as saídas e as consultas (`RF-03` a `RF-09`, `RF-14`, `D-12`) | T016, T017 | - | `evidence/T020-ponta-a-ponta.md` | 🟢 | `[X]` |
| T021 | Executar a verificação manual do `onboarding.md` — os passos §6 (`down` + `up`, com `src/uploads/` e a contagem de análises preservadas, `RF-02`) e §9 (banco **derrubado**) —, usando só dado **sintético**, e limpar o que sobrar conferindo `git status` contra `src/uploads/` e `uploads/`, esperando que nenhum dos dois apareça (`RF-16`, `RF-17`, Princípio I) | T020 | - | `evidence/T021-verificacao-manual.md` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T022 | Medir e registrar a **linha de base vigente do Bloco 1**: a suíte completa **sem** `DATABASE_URL` e **com** o stack no ar, os dois números lado a lado com o comando de cada um, mantendo `261` como leitura **histórica** e a comparação por **conjunto** (`RF-13`, `D-14`, `D-17`) | T021 | - | `evidence/T022-linha-de-base-bloco1.md` | 🟢 | `[X]` |
| T023 | Conferir o **escopo** por `diff`: `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` sem nenhuma alteração (`RN-01`); `pytest.ini`, `.gitignore` e os artefatos de `_reversa_sdd/migration/` intocados; e nenhuma consulta, `CHECK` ou índice que filtre ou comece por `owner_id` (`RN-10`) | T021 | - | `evidence/T023-conferencia-de-escopo.md` | 🟢 | `[X]` |
| T024 | Documentar em `evidence/README-evidencias.md` os instrumentos desta rodada e o diretório **preso** `.probe/`, criado pela sonda de `pip` que falhou durante a investigação, com o comando de remoção que exige shell elevado (`D-11`, `investigation.md` §2) | T001 | `[//]` | `evidence/README-evidencias.md` | 🟢 | `[X]` |
| T025 | Varrer **credencial**: procurar por qualquer valor de `POSTGRES_PASSWORD` e por `DATABASE_URL` no que é versionado, no template, no `.env.example` inexistente, na saída de `docker compose config` e nas camadas da imagem, e confirmar por `git check-ignore -v .env` que o arquivo do operador está ignorado. Registrar os comandos e a ausência de ocorrência (`RF-11`) | T021 | - | `evidence/T025-varredura-de-credencial.md` | 🟢 | `[X]` |
| T026 | Medir e registrar o **custo da gravação**: tempo da análise no mesmo GEDCOM e CSV **sintéticos**, com a persistência desabilitada e habilitada, com o comando e os dois números lado a lado e o acréscimo em porcentagem. **Critério:** o tempo com a persistência tem de ficar **abaixo do dobro** do tempo sem ela — é o RNF de Desempenho, e o `roadmap.md` §0 registra a linha de base de onde ele parte | T021 | - | `evidence/T026-custo-da-gravacao.md` | 🟢 | `[ ]` |

## Notas sobre a decomposição

### Os três blocos, e o que cada um mede

| Bloco | Ações | O que muda | O que mede |
|---|---|---|---|
| **Bloco 0** | `T001`–`T011` | Infraestrutura e esquema. **Zero linha de Python de produção** | `T008` (stack no ar), `T009` (idempotência), `T010` (contexto de build), `T011` (**o portão**: `261` e `100 %`) |
| **Bloco 1** | `T012`–`T021` | A costura: porta, adaptador, caso de uso, borda, template, testes | `T014` (adaptador), `T018`/`T019` (os dois estados), `T020` (ponta a ponta), `T021` (manual) |
| **Bloco 2** | `T022`–`T026` | Nada. Confere e mede | `T022` (linha de base vigente), `T023` (escopo por diff), `T025` (credencial), `T026` (custo da gravação) |

### Paralelismo: nenhuma ação `[//]` compartilha arquivo alvo

As onze marcações foram conferidas par a par: `.dockerignore` (`T002`), `docker/Dockerfile`
(`T003`), `init.sql` (`T004`), `requirements.txt` (`T007`), `src/ports/adaptadores.py`
(`T013`), `src/application/dna_analysis.py` (`T015`),
`tests/test_persistencia_desabilitada.py` (`T018`),
`tests/test_persistencia_indisponivel.py` (`T019`), e três **arquivos distintos** dentro de
`evidence/` (`T009`, `T010`, `T024`).

⚠️ **A única ressalva é a de `T009`, `T010` e `T024`**, que compartilham a **pasta**
`evidence/` e não o arquivo: cada uma escreve um arquivo próprio e nenhuma lê o que a outra
escreve. É a mesma ressalva declarada que a feature 007 registrou para o `T011`/`T012` dela.
Quem ler a coluna "Arquivo alvo" dessas três precisa lê-la com esse cuidado.

### A `D-17` na prática: dois números de suíte, não um

`T014` depende de banco e é **pulado** sem `DATABASE_URL`. Consequência aritmética que o
`T022` tem de registrar com honestidade:

| Execução | Esperado |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q`, **sem** `DATABASE_URL` | `261 passed` + os testes novos de `T018`/`T019` + os pulos de `T014` declarados |
| Com o stack no ar e `DATABASE_URL` presente | O mesmo conjunto, com `T014` **executando** em vez de pular |

Um teste pulado **não** é um teste que passou, e o `T022` não pode apresentar os dois números
como se fossem um. É o mesmo cuidado que a feature 007 teve ao separar `231/15` de `246/0`.

### O que este documento **não** tem, e por quê

- Nenhuma ação de "configurar IDE", "rodar lint", "abrir PR" ou "atualizar README" — não é
  responsabilidade do Reversa, e o `README.md` está liberado mas é ato do usuário (`D-13`).
- Nenhuma ação para `.gitignore` nem para `.env.example`. **Medido:** `uploads/` (linha 34) e
  `.env` (linha 6) já cobrem os dois estados persistentes, e um `.env.example` seria um
  arquivo novo na raiz sem necessidade medida (`D-13`).
- Nenhuma ação para implementar `RepositorioDeArvores`. Ele continua declarado, **sem
  implementação e sem consumidor** — esta feature cria uma porta **diferente**, e a `D-01`
  registra a distinção.
- Nenhuma ação para a **tela de histórico**. O `RF-14` é atendido por consulta SQL
  documentada (`D-12`), e a tela está declarada fora de escopo no §12 do `requirements.md`.
- Nenhuma ação para criptografia em repouso, retenção ou expurgo — são da Onda 5, e o aceite
  de risco de 2026-10-08 cobre a ausência deles **agora**, não a dispensa (`Q-04`).
- Nenhum arquivo em `interfaces/`. O único contrato novo é o esquema do banco, e o detalhe
  dele vive no `data-delta.md` (`roadmap.md` §7).
- Nenhuma ação para tocar `_reversa_sdd/migration/target_data_model.md`. Ele está preservado
  sem regeneração desde 2026-09-28; esta feature **nomeia** a divergência, e reconciliar o
  artefato é ato da onda seguinte (`T023` confere que ele segue intocado).

### Sobre o template `init.sql` em duas ações

`T004` e `T005` editam o **mesmo** arquivo, e por isso nenhuma leva `[//]`: a segunda
depende da primeira. A divisão existe porque seis tabelas, os `CHECK` de estado e os índices
passariam de cinco subpontos lógicos numa ação só — e a metade herdada do alvo é uma decisão
diferente da metade que **estende** o alvo, com confidência e justificativa próprias
(`D-06`).

### Uma lacuna encontrada **na decomposição**, e fechada aqui

O critério de pronto do `roadmap.md` §10 tem um item — "nenhuma credencial em código,
arquivo versionado, template, log ou camada da imagem" (`RF-11`) — que **não tinha ação
nenhuma** nas 24 primeiras. A conferência de escopo (`T023`) cobre arquivos e índices, não
segredos; e o `T010` mede o contexto de build, não o conteúdo versionado. O `T025` foi
acrescentado por isso.

O registro existe porque a alternativa era aceitar um item de critério de pronto sem
evidência — que é a forma mais silenciosa de uma feature "fechar" sem atender o próprio
critério. **Nenhum ID foi reciclado:** o `T025` é novo, e os anteriores mantêm o número.

### Correções aplicadas depois da auditoria de 2026-10-08

O `/reversa-audit` produziu dez achados em `audit/cross-check.md` — **zero CRITICAL**, três
HIGH, três MEDIUM e quatro LOW. Este documento foi corrigido para fechar **todos os dez**;
o relatório de auditoria **não** foi alterado, porque ele é o registro do que foi encontrado
naquela data. A tabela abaixo é a ponte entre os dois.

| Achado | Severidade | O que mudou aqui |
|---|---|---|
| `A001` | HIGH | `T004`, `T005` e `T006` passam a declarar o `IF NOT EXISTS`, a ausência de `DROP` e a **montagem do `init.sql` em `/docker-entrypoint-initdb.d/`** — sem a montagem, o `T009` não tinha o que executar |
| `A002` | HIGH | O `T002` deixa de ser lista de **negação** e passa a **lista de permissão** (`D-18`). Medição da auditoria: a raiz tem **22** diretórios ilegíveis, **12 cobertos** e **10 fora** — sete em `.pytest-tmp/`, dois em `_probe_acl/` e um em `_probe_acl2/`. Com a lista de permissão, nenhum deles entra no contexto, e o `docker build` deixa de abortar |
| `A003` | HIGH | **`T026`** é novo: mede o custo da gravação com a persistência desabilitada e habilitada, com o critério "abaixo do dobro" |
| `A004` | MEDIUM | O `T021` passa a citar o passo §6 (`down` + `up`) do `onboarding.md`, e não só o §9 |
| `A005` | MEDIUM | O `T014` passa a afirmar que o **estado final gravado é o mais conservador** dos dois kits |
| `A006` | MEDIUM | O `T019` passa a dizer **como** provocar a recusa: `DATABASE_URL` apontando para uma porta fechada |
| `A007` | LOW | O `T021` passa a nomear o resultado esperado do `git status` contra `src/uploads/` e `uploads/` |
| `A008` | LOW | O `T013` passa a citar o `D-16`, o texto ao caractere e a ausência do código do aviso |
| `A009` | LOW | Corrigido no `roadmap.md`: "achado C da 007" passa a apontar o arquivo (`actions.md` da 007) |
| `A010` | LOW | Resolvido por consequência: a linha `.probe/` sai junto com a lista de negação do `T002` |

⚠️ **A auditoria não foi reexecutada.** Os dez achados foram fechados por edição, e a
verificação de que fecharam é uma **nova** passagem por `/reversa-audit` — não uma
afirmação deste documento.

## Notas de execução

> Reservado para `/reversa-coding` registrar avisos ou observações que surgiram durante a execução.
> Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.

> **Execução de 2026-10-08: 11 de 26 ações concluídas, 15 pendentes, 0 falhas em aberto.**
> Três paradas, todas do ambiente e nenhuma da feature: o `T001` (permissão de edição), o
> `T008` (motor do Docker desligado) e o named pipe que o modo confinado bloqueia. As três
> foram resolvidas, e **o Bloco 0 fechou com o portão verde**.

### Primeira parada: o `T001` e o veredito NÃO ATENDIDO

`.reversa/reversa-config.json` tinha `allowLegacyEdits: true` com `allowedPaths` **não vazio**,
e a lista não cobria `docker/**`, `docker-compose.yml`, `init.sql` nem `.dockerignore` — quatro
dos sete caminhos que a feature precisa escrever.

O `T002` **não foi tentado**, e a escolha foi deliberada: escrever o `.dockerignore` "por fora"
seria contornar a regra exatamente na feature que a regra restringe. O `progress.jsonl`
registrou `T002` com `status: blocked` e `attempted: false` — **não** `failed`, porque não
houve tentativa que tenha quebrado.

**O usuário liberou os quatro caminhos**, e a reexecução do `T001` deu **ATENDIDO**. O Bloco 0
começou. Nenhum contorno foi usado, e a liberação foi ato dele — que era o ponto do `T001`.

### Segunda parada: o `T008`, com o motor do Docker desligado

O Bloco 0 foi executado até onde não dependia do motor. `T002` a `T007` **concluídas**, seis
arquivos escritos, e um deles é o único arquivo do legado tocado nesta rodada:
`requirements.txt`, com uma linha.

O `T008` falhou por ambiente:

```
unable to get image 'genealogia-app': permission denied while trying to connect to the
docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

O CLI do Docker está instalado; o **motor não está em execução**. Nada do produto foi
exercitado, e por isso `T009` (idempotência), `T010` (contexto de build) e `T011` (**o portão
do Bloco 0**) ficaram pendentes. A fase para aqui, como o skill manda.

Duas verificações que **não** precisam do motor passaram, e valem registro:

1. **`docker compose config --quiet` devolveu exit 0**, com dois serviços (`db`, `app`), um
   volume nomeado (`dados_do_banco`) e as portas publicadas em `127.0.0.1` — `5080` para a
   aplicação e `5432` para o banco. O arquivo está sintaticamente correto e interpolável.
2. **O guarda do `RF-11` funciona em execução.** Sem `.env`, o `docker compose up` para com
   `required variable POSTGRES_USER is missing a value`. É o `${VAR:?}` fazendo o trabalho, e
   é prova de que não há credencial com valor padrão em arquivo versionado.

O `T008` precisava de **duas** coisas do operador, e as duas foram resolvidas: o Docker Desktop
foi iniciado por esta sessão **a pedido do usuário**, e o `.env` **foi criado por esta sessão**,
também a pedido dele, com senha gerada por `secrets.token_urlsafe(24)`.

⚠️ **Correção de um registro anterior desta rodada.** Este documento chegou a dizer que o
`.env` não seria criado, "porque a senha é escolha do operador". O usuário pediu explicitamente
o contrário, e o pedido foi atendido — a senha é dele para trocar. **Mas a troca tem de ser
agora:** `POSTGRES_PASSWORD` só tem efeito na **primeira** inicialização do volume, e mudá-la
depois exige `docker compose down -v`, que **apaga o histórico**. O `.env` está no `.gitignore`
(linha 6) e o `git check-ignore -v .env` confirma.

### Terceira parada — e a resolução: o named pipe

O motor não subia, e o motivo real **não era o motor**: o modo confinado do harness **bloqueia
named pipe**, e o CLI do Docker fala com o motor por
`npipe:////./pipe/dockerDesktopLinuxEngine`. Cada comando Docker falha com `permission denied
... npipe` e exige autorização explícita do usuário — uma **por comando**.

A saída foi **empacotar todo o Bloco 0 dependente do motor num único comando autorizado**, em
vez de pedir dezenas de autorizações. Ele executou `T008`, `T009` e `T010` de uma vez, com o log
bruto preservado em `evidence/_bloco0-build.log`. O `T011` não precisou de autorização: roda no
`.venv` do host.

### O Bloco 0 fechou, e o portão está verde

| Ação | Resultado |
|---|---|
| `T008` | build **exit 0**; os dois contêineres no ar; `db` **healthy**; `app` em `127.0.0.1:5080`; **HTTP 200 em 4 s** |
| `T009` | tabelas **6 → 6**, com apenas `NOTICE ... already exists, skipping` — `RF-12` provado por execução |
| `T010` | contexto de **250,70 kB** e `src/uploads/` **AUSENTE** na imagem — Princípio I provado por medição |
| `T011` | **`261 passed`** e **`PARIDADE 100 %`**, exit 0, os dois **sem** `DATABASE_URL` |

**O Bloco 1 pode começar.** O `T012` deixa de ter dependência aberta. Duas observações de
ambiente ficam para o `T022` e o `T014`: a suíte mais lenta com os contêineres no ar (`OBS-14`),
e o `pip install` do host ainda inviável (`OBS-15`).

### Bloco 1 — a costura: `T012` a `T019` concluídas

Oito ações, seis arquivos escritos em `src/` e quatro em `tests/`. **Nenhum arquivo do núcleo
foi tocado**: `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` seguem sem uma
linha alterada, e é isso que faz a `RN-01` ser verificável por `diff` em vez de por afirmação.

A suíte fechou em **`281 passed, 8 skipped`**, contra `261 passed` da linha de base. Os 20
aprovados novos são os testes desta feature, e os 8 pulos são o `T014` e as seis
parametrizações dele.

### Quatro desvios do plano, encontrados ao executar

1. **O caso de uso precisava da referência da árvore, e o plano não a previa.** O `RF-03`
   exige a chave de conteúdo do GEDCOM, e ela **não estava** na assinatura de
   `application/dna_analysis.py` — só a borda a tinha. `referencia_da_arvore` entrou como
   parâmetro com padrão `None`, e `None` significa **não registrar**: sem a referência não há
   o que gravar, e inventá-la aqui seria criar um identificador que não existe.
2. **O `import psycopg2` teve de ser preguiçoso.** O driver **não está no `.venv/` do host**,
   que é o interpretador da suíte e da paridade. Um import no topo de `adaptadores.py`
   derrubaria `import app` nos dois, por ambiente — a mesma classe de defeito que a feature
   007 corrigiu no `tmp_path`, só que na importação em vez do diretório temporário. O import
   vive **dentro** de `registrar`, e a ausência do driver vira **aviso**.
3. **A coluna `detail` do `init.sql` foi removida.** Ela era redundante com
   `comparison_detail`: o núcleo não entrega um "detalhe documental" separado, e eu havia
   criado duas colunas para o mesmo texto. Corrigido antes de existir dado — o volume precisa
   ser recriado no `T020`, e não há nada a perder.
4. **A asserção do "recuo" do caminho estava errada, e o teste pegou.** O corte caía no
   **último** nó em vez do penúltimo quando o ancestral comum não está no caminho, e o nó
   final saía `ascendente`. O teste foi escrito antes da correção e acusou; quem mudou foi a
   implementação.

### Uma armadilha de teste, medida

A fixture do estado de falha precisa que `src/app.py` seja carregado **com** a `DATABASE_URL`
já definida. A primeira versão definia a variável no corpo da fixture e devolvia
`cliente_de_upload` — e **não funcionava**: uma fixture tem o corpo executado **depois** do
corpo das suas dependências, então `app.py` já havia sido carregado com a variável ausente, e
o teste media o estado **desabilitado** achando que media o de falha. O app passou a ser
recarregado depois do `setenv`, e a armadilha está registrada no docstring da fixture.

### Um arame de tropeço da feature 007 disparou, e estava certo

`tests/test_porta_de_armazenamento.py` prende `adaptadores.__all__` numa lista literal e diz,
na mensagem da asserção: *"a superfície pública dos adaptadores mudou: reabra a D-03 antes"*.
Ele disparou porque a feature 008 acrescenta um adaptador, e a decisão foi **reaberta**: o
`D-01` desta feature a declara, e o `roadmap.md` §5 a registra como `componente-novo`. A lista
ganhou o terceiro nome com o motivo escrito ao lado, e a **outra metade** do teste — a que
prova que nenhum adaptador implementa o `RepositorioDeArvores` — segue intacta e passando.
**Nenhum teste foi removido, desabilitado ou enfraquecido.**

### O `B003` da auditoria foi fechado; o `T014` nunca executou

O `B003` dizia que a projeção era a única parte central da feature sem teste que rodasse sem
banco. Ela é **pura**, e `tests/test_projecao_da_analise.py` a exercita sem `DATABASE_URL`.

⚠️ **O `T014` é outra história, e ela não pode ser maquiada.** O arquivo está escrito e
marcado, e a ação pedia **escrever** o teste — o que está feito. Mas ele **nunca rodou**: o
host não tem `psycopg2` (`OBS-15`) e a suíte roda sem `DATABASE_URL` (`D-17`). **Um teste
pulado não é um teste que passou.** A prova dos mesmos caminhos com o banco no ar é do
`T020`, e o `T022` tem de registrar os dois números da suíte lado a lado.

### `T020` — a ponta a ponta, e dois achados que não são do produto

O stack foi recriado (`down -v`, porque o `init.sql` mudou depois da primeira subida) e
subiu com a imagem reconstruída. A rota, com **dois kits do mesmo nome**, gravou **duas
conexões** com o cM do seu próprio kit — 200 e 60, nenhuma soma —, **duas** linhas de
`match_kit`, **três** pessoas (raiz e match com ficha completa, nó do caminho só identificado)
e seis nós de caminho com os papéis derivados. **Sem aviso**, porque o banco estava no ar.

O adaptador foi verificado **dentro do contêiner** — onde o driver existe, ao contrário do
`.venv/` do host — e as **24** verificações passaram, incluindo a ida e volta do cM nos seis
valores de fronteira, `NULL` em vez de zero, aviso em vez de exceção e **transação única** com
a análise recusada não deixando nenhuma linha. É a substância do `T014`.

**Achado 1 — defeito de ESQUEMA, corrigido.** O script de verificação limpa o que grava, e o
`DELETE` **falhou**: as duas FKs de pessoa estavam com `ON DELETE RESTRICT`, e `analysis_person`
cascateia de `dna_analysis` — então **apagar uma análise era impossível**. O `RESTRICT` não
protegia nada: a garantia que interessa (não gravar referência a pessoa inexistente) o próprio
FK já dá no `INSERT`. Passaram a `CASCADE`, com a razão escrita no `init.sql`, e a correção foi
provada (`DELETE FROM dna_analysis` → `DELETE 1`; `match_result` → `0`).

**Achado 2 — defeito de INSTRUMENTO.** A primeira execução gravou **uma** conexão com
`total_cm = 260` e kit vazio. Não era a persistência: era o **meu CSV**. O núcleo só reconhece
a coluna de kit quando o **valor** casa `[A-Z]{1,3}\d{4,8}`, e `KIT-A` não casa — sem kit
detectado, as duas linhas viram o mesmo match `SEM-KIT` e o cM é **somado**, que é o
comportamento documentado. Medido com três CSVs, e o terceiro (sem coluna de kit) deu
resultado **idêntico** ao meu. ⚠️ O sintoma era convincente: "duas linhas somadas em 260"
parece defeito de agregação da persistência, e não é.

### O que continua pendente, e por quê

`T021` a `T026`: a verificação manual do `onboarding.md` (incluindo o `down`/`up` do `RF-02` e
o banco derrubado do §9), a linha de base vigente do `T022`, a conferência de escopo, o
registro das evidências, a varredura de credencial e o custo da gravação. Todos exigem o motor
do Docker, e todos exigem autorização explícita por causa do named pipe.

### `T025` passou; `T026` **falhou o critério**, e a fase para aqui

**`T025` — a varredura de credencial está limpa.** O **valor** da senha aparece em **dois**
lugares, e os dois são o `.env` — que o `.gitignore` exclui (linha 6) e que não é versionado.
Nos demais arquivos aparece só o **nome** da variável, nunca o valor. O template tem **zero**
ocorrências; as **camadas** da imagem, zero; o **ambiente** dentro dela, zero; e não existe
`.env` nenhum dentro da imagem. O que ela contém em `/app` é exatamente o `COPY` estreito:
`requirements.txt` e `src/` — e **`/app/src/uploads` ausente**, que é o Princípio I confirmado
de novo, agora por dentro.

⚠️ **Uma ressalva declarada, e ela não é desta feature:** `docker compose config` **imprime o
valor** da senha na saída — é o comportamento do Compose, que resolve as variáveis do `.env`.
Quem rodar esse comando num terminal expõe a senha na tela, e quem redirecionar a saída para um
arquivo a expõe no arquivo. Registrado porque vale para qualquer projeto com Compose.

**`T026` — e aqui a execução encontrou um defeito de REQUISITO, não de código.**

| | Menor de 5 |
|---|---|
| Análise sem persistência | **5,1 ms** |
| Análise com persistência | **41,5 ms** |
| Razão | **8,14×** — contra o limite de `2,00×`: **FAIL** |

O `RNF de Desempenho` diz que "a gravação não pode dobrar o tempo da análise", e a medição
mostra por que a frase está errada: **o fixture é trivial** (cinco pessoas, dois matches,
5,1 ms) porque o Princípio I **proíbe** medir com o GEDCOM real do operador. Qualquer trabalho
de banco maior que 5 ms "dobra" uma análise de 5 ms — o critério transforma o tamanho do
fixture em veredito sobre a feature.

O número útil é o **absoluto: 36,4 ms**. Ele não depende do tamanho da árvore, e sim do número
de conexões; sob a análise real de **71 conexões** a razão seria uma fração disso. Mas **essa
medição não pode ser feita**, e a razão é o próprio Princípio I.

**O que eu NÃO fiz, e não vou fazer: ajustar o critério para bater com o resultado.** O
`risk_register.md` nomeia esse movimento como o antipadrão a evitar — *"Nunca 'ajustar o alvo
para bater com a nova implementação'"*. Trocar "abaixo do dobro" por "abaixo de 10×" fecharia
o `T026` e destruiria a única informação que ele produziu.

**O `T026` fica aberto, e a fase para aqui**, como o skill manda quando uma ação falha. O que
precisa acontecer é uma decisão **de requisito**: trocar a razão por um **orçamento absoluto**
(por exemplo, "não acrescenta mais de 100 ms"), ou declarar o `n` do fixture em que a razão
passa a ter significado.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-08 | Correção dos dez achados de `audit/cross-check.md`: `T026` criado (`A003`), `T002`/`T004`/`T005`/`T006`/`T013`/`T014`/`T019`/`T021` reescritos. Total de 25 para **26** ações; nenhum ID reciclado | reversa |
| 2026-10-08 | Execução de `/reversa-coding`: **`T001` concluído** (pré-requisito verificado e **não atendido**), `T002` **bloqueado** por política de edição do legado, Bloco 0 parado. 1 de 26 ações concluídas, 0 falhas. Evidência em `evidence/T001-pre-requisito-de-permissao.md` | reversa |
| 2026-10-08 | Reexecução do `T001` após a liberação dos quatro caminhos pelo usuário: veredito **ATENDIDO**. Bloco 0 executado até o `T008` — `T002` a `T007` **concluídas** (`.dockerignore`, `docker/Dockerfile`, `init.sql`, `docker-compose.yml`, `requirements.txt`), 7 de 26 ações concluídas. `T008` **falhou**: motor do Docker não está em execução. `docker compose config` validado (exit 0) e o guarda do `RF-11` verificado em execução | reversa |
| 2026-10-08 | **Bloco 0 fechado com o portão verde.** O Docker Desktop foi iniciado e o `.env` criado por esta sessão, a pedido do usuário. A causa da falha do `T008` não era o motor, e sim o **bloqueio de named pipe** do modo confinado; a saída foi empacotar `T008`–`T010` num único comando autorizado. `T008`–`T011` **concluídas**: HTTP 200, `init.sql` idempotente (6→6), contexto de 250,70 kB com `src/uploads/` ausente da imagem, **`261 passed`** e **`PARIDADE 100 %`** sem `DATABASE_URL`. 11 de 26 ações concluídas | reversa |
| 2026-10-08 | **Bloco 1 executado: `T012` a `T019` concluídas**, 19 de 26 ações. Porta `RegistroDeAnalises` + payload, adaptador `RegistroDeAnalisesPostgres`, projeção pura no caso de uso, regra dos três estados na borda, bloco de aviso no template, e quatro arquivos de teste. Suíte em **`281 passed, 8 skipped`**. Quatro desvios declarados (referência da árvore no caso de uso, `import` preguiçoso do driver, coluna `detail` removida, recuo do caminho corrigido) e o `B003` da auditoria fechado. O `T014` **nunca executou** | reversa |
| 2026-10-08 | **`T020` concluído**: 20 de 26 ações. Rota com dois kits do mesmo nome gravou 2 conexões, 2 kits (200 e 60, sem soma), 3 pessoas e 6 nós de caminho; aviso ausente com o banco no ar. O adaptador verificado **dentro do contêiner**: 24 verificações, 0 falhas. **Dois achados:** `ON DELETE RESTRICT` tornava `DELETE FROM dna_analysis` impossível (corrigido para `CASCADE`, provado), e o CSV sintético não exercitava o caso porque o núcleo exige valor de kit no padrão `[A-Z]{1,3}\d{4,8}` — defeito de instrumento, não de produto | reversa |
| 2026-10-08 | **`T021` concluído**: 21 de 26 ações. Verificação manual do `onboarding.md` com dado sintético. `down` + `up` **sem** `-v` preservou os 35 arquivos de `src/uploads/` **e** a análise (1 → 1, com as 2 conexões e os 2 kits consultáveis) — `RF-02` provado. Banco **derrubado**: HTTP 200, as mesmas 2 conexões e o aviso não bloqueante, com o `OperationalError` de produção. Depois de religar, a análise continuava **1** — nada parcial, `RF-10` no caminho de falha real | reversa |
| 2026-10-08 | **`T022`, `T023` e `T024` concluídos**: 24 de 26 ações. `T022` mediu os dois números da suíte — **`282 passed, 8 skipped`** sem `DATABASE_URL`, e **`2 failed, 280 passed, 8 skipped`** com ela, sendo as duas falhas o **guarda do estado desabilitado** protestando de propósito. `T023` confirmou por `diff` que os quatro pacotes do núcleo e os arquivos de configuração estão intocados, e que nenhum índice, `CHECK` ou consulta começa por `owner_id`. `T024` documentou os instrumentos, o resíduo `.probe/` e os quatro defeitos de ambiente | reversa |
| 2026-10-08 | **`T025` concluído e `T026` FALHOU o critério**: 25 de 26 ações. `T025`: o valor da senha só existe no `.env` (gitignored), o template tem zero ocorrências, as camadas e o ambiente da imagem também, e `/app/src/uploads` está ausente. `T026` mediu **8,14×** contra o limite de `2,00×` — a falha é **do critério**, que compara uma razão sobre um fixture de 5,1 ms que o Princípio I obriga a ser sintético. **Não ajustei o critério para bater com o resultado.** A ação fica aberta e a fase para aqui | reversa |
