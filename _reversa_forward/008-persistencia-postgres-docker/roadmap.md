# Roadmap: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Requirements: `_reversa_forward/008-persistencia-postgres-docker/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 0. Linha de base medida, antes do plano

O plano não herda número de outra feature: ele mede. Os quatro valores abaixo foram
produzidos nesta sessão, no interpretador oficial, **antes** de qualquer linha ser escrita.

| Medição | Comando | Resultado |
|---|---|---|
| Suíte completa | `.venv\Scripts\python.exe -m pytest -q` | **`261 passed`** — 0 falhas, 0 erros, 27,1 s |
| Paridade diferencial | `.venv\Scripts\python.exe _reversa_sdd\parity\harness.py` | **`PARIDADE 100%`**, zero divergência, **exit 0** |
| Interpretador | `.venv\Scripts\python.exe -c "import sys; print(sys.version)"` | `3.14.6 (tags/v3.14.6:c63aec6, Jun 10 2026)` |
| Docker no host | `docker --version` / `docker compose version` | `29.6.1` / `v5.2.0` — **instalados** |

Duas medições adicionais desta investigação, e as duas **aposentam risco**:

| Medição | Método | Resultado |
|---|---|---|
| Wheel do driver para `cp314`/Windows | API JSON do PyPI | `psycopg2_binary-2.9.13-cp314-cp314-win_amd64.whl` **existe**; `psycopg_binary-3.3.6-cp314-cp314-win_amd64.whl` e `sqlalchemy-2.1.4-cp314-cp314-win_amd64.whl` também |
| Imagens base | API de tags do Docker Hub | `python:3.14-slim` **existe**; `postgres:16-alpine` **existe** |

⚠️ **O `pip download` e o `pip install --dry-run` falham nesta máquina**, e não é
defeito do plano: o pip cria o diretório de trabalho por `tempfile.mkdtemp`, que usa
`mode=0o700` — o mesmo defeito já medido e documentado em `tests/conftest.py` §1 e no
adendo da feature 007. A medição dos wheels foi feita **sem diretório temporário**,
consultando a API do PyPI. Registrado para que o próximo leitor não repita a tentativa.

## 1. Resumo da abordagem

A persistência entra como **quarta porta** da fronteira, ao lado das três que a Onda 2
declarou, e é consumida pelo **caso de uso** `application/dna_analysis.py` — o mesmo
padrão de `upload_gedcom`, que já recebe duas portas e orquestra I/O. O núcleo continua
sem saber que existe banco: `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/`
não são tocados, e nenhum deles importa acesso a dados.

A decisão que governa todo o resto é a **regra dos três estados**, que nasce do `Q-03`:
sem `DATABASE_URL` a persistência fica **desabilitada** e a tela fica byte a byte como
é hoje (é isso que protege a paridade das 6 fixtures e os `261` testes); com a variável
presente e o banco respondendo, grava; com a variável presente e a gravação falhando, a
análise **conclui e é exibida** com um aviso não bloqueante. O import de `src/app.py`
**nunca** toca a rede — e isso não é estilo, é requisito: `tests/conftest.py:166-171` e
`_reversa_sdd/parity/harness.py:356` **importam `app.py`**, então uma conexão no import
quebraria a suíte e a paridade por ambiente.

A infraestrutura vem em bloco separado e antes do código, para que o risco de contêiner
e de esquema não se misture com o risco de costura. Nenhuma linha de Python de produção
muda no bloco 0.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | **É o princípio mais tensionado por esta feature, e o conflito é real.** O volume do banco passa a conter nome, kit, cM e veredito de pessoas reais, **sem criptografia em repouso**, por aceite de risco explícito de 2026-10-08 (`Q-04`). O aceite é o mesmo regime do `BUG-20260929-BJJH` e tem a mesma condição de reabertura nomeada. Fora disso: nenhum dado real entra em teste, fixture ou evidência, e o `.dockerignore` existe em parte para impedir que `src/uploads/` — que hoje contém o GEDCOM real de 5,3 MB do operador — seja enviado ao contexto de build | conflita (**aceito e declarado**, não escondido) |
| II. Comportamento observável é preservado em refatoração | **É o princípio que governa esta feature.** A `RN-02` exige os mesmos matches, a mesma ordem, os mesmos cM e os mesmos vereditos. A regra dos três estados existe para que a persistência desabilitada produza saída **idêntica**: `261` aprovados e `PARIDADE 100%` são medidos **sem** `DATABASE_URL`, e o `RF-13` é o portão | respeita |
| III. Nenhuma mudança sem teste que a cubra | Respeita. Cada um dos três estados da persistência ganha teste: desabilitada (página idêntica), gravando (linha no banco pela consulta do `RF-14`) e falhando (aviso não bloqueante com o banco derrubado). A idempotência do `init.sql` ganha teste de reexecução | respeita |
| IV. Arestas do grafo são tipadas | **Não é tocada, e o conflito permanece herdado.** Nenhuma travessia, peso ou constante de parentesco é tocada — o delta arquitetural do §5 lista `src/core/` como *presença*, sem alteração. O conflito é anterior e está declarado desde a feature 005 | conflita (herdado, declarado) |
| V. Toda suposição de genealogia genética cita a fonte | Respeita, e é o motivo do `RN-05`. O cM é **transportado** do núcleo para o banco, nunca reagregado: o `RISK-004` registra que um `SUM` do PostgreSQL pode alterar o último dígito e **cruzar um limite de faixa**. Nenhuma faixa, média ou heurística é criada, alterada ou reinterpretada pela persistência | respeita |

> **Sobre o Princípio I, e por que ele está marcado como conflito.** O `Q-04` decidiu gravar
> dado genético real sem criptografia. Este roadmap **não** atenua o princípio nem o
> reescreve — isso é trabalho do `/reversa-principles`. Ele registra o conflito e a decisão
> que o aceita, para que a próxima leitura da extração não encontre "o Princípio I vale" e
> "o banco tem dado real em claro" no mesmo repositório sem explicação.
>
> **Sobre o Princípio IV.** Ele não é violado *por esta feature*: a violação é anterior. O
> registro existe para que ninguém leia esta entrega como "a persistência aproximou a
> tipagem de aresta". Não aproximou.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A persistência entra como **porta nova** — `RegistroDeAnalises` (`Protocol` em `src/ports/__init__.py`) com adaptador `RegistroDeAnalisesPostgres` (`src/ports/adaptadores.py`) —, consumida pelo **caso de uso** `application/dna_analysis.py`, montada na borda (`src/app.py`) | É o padrão que a própria fronteira já fixou: `upload_gedcom` recebe duas portas e orquestra I/O, e o caso de uso é o lugar da orquestração desde a Onda 2. A porta nova é a quarta, e ela **não** é o `RepositorioDeArvores`: aquele é sobre a **árvore**, e a `RN-04` diz que a árvore não vai para o banco | (a) gravar direto em `src/app.py` — devolve orquestração de I/O para a rota, que é o que a Onda 2 tirou de lá (`RF-01` da 006); (b) implementar `RepositorioDeArvores` — a 007 o declarou sem consumidor, e ele persistiria a árvore, não a análise; (c) gravar dentro de `core/dna_analysis.py` — proibido pela `RN-01`, e destruiria a pureza do núcleo que as features 005 e 006 construíram | 🟢 |
| D-02 | **Regra dos três estados, e conexão nunca no import.** (1) `DATABASE_URL` ausente → **registrador nulo**, sem aviso, tela idêntica; (2) presente e o banco responde → grava; (3) presente e a gravação falha → análise conclui e é exibida, com **aviso não bloqueante** | **Medido no código:** `tests/conftest.py:166-171` faz `spec.loader.exec_module` de `src/app.py` e `_reversa_sdd/parity/harness.py:356` faz `import app as APP`. Uma conexão aberta no import quebraria a suíte e a paridade **por ambiente** — exatamente o defeito que a feature 007 acabou de corrigir. E o estado (1) sem aviso é o que mantém a paridade: avisar quando a persistência está desligada por configuração mudaria o contrato congelado de tela das 6 fixtures | (a) conectar no import — quebra suíte e paridade por ambiente; (b) tratar "sem URL" como falha e avisar — derruba a paridade e inventa um erro que o operador não cometeu; (c) levantar exceção quando o banco falha — viola a `RN-13` e o `Q-03` | 🟢 medido |
| D-03 | Driver **`psycopg2-binary`**, versão pinada, com **SQL escrito à mão**; sem ORM | O nome foi dado pelo solicitante, e é **uma** dependência. **Medido:** existe wheel `psycopg2_binary-2.9.13-cp314-cp314-win_amd64.whl`, então o `3.14.6` do projeto está coberto e não há compilação local. O ORM é descartado por duas razões convergentes: o DDL do alvo é **SQL literal** (`migration/target_data_model.md#Schema (DDL)`), e o projeto registra "não há ORM" (`architecture.md#4`) — e um ORM convidaria a mover decisão de domínio para a camada de persistência, o que a `RN-01` e a `RN-12` proíbem | (a) `psycopg` 3 — moderno e também com wheel `cp314` medido (`psycopg_binary-3.3.6-cp314-cp314-win_amd64.whl`), mas troca o nome pedido sem ganho medido para "uma conexão e uma transação por análise"; (b) SQLAlchemy — peso e risco de vazamento de domínio para a persistência; (c) `asyncpg` — a aplicação é WSGI síncrona (Flask + waitress) e não há laço de eventos onde a assincronia rodar | 🟢 medido |
| D-04 | **Uma conexão por análise**, aberta e fechada dentro da própria chamada; **sem pool** | 4 threads (`ANALISADOR_THREADS = 4`), um usuário e uma gravação por requisição. Conexão por chamada é thread-safe por construção, e um pool seria otimização sem necessidade medida que acrescenta **estado por processo** — justamente o que a feature 005 removeu e o que a dívida #3 condena | (a) `ThreadedConnectionPool` — mais uma estrutura de estado global de processo para gerenciar e para vazar; (b) conexão global única — não é thread-safe e reintroduz o estado de processo que a 005 removeu | 🟢 |
| D-05 | **Uma transação por análise**, com o contexto e todos os resultados dentro; falha não deixa análise parcial | É o `RF-10`, e o motivo é de negócio, não de pureza técnica: uma análise pela metade deixaria o veredito de um par gravado com os dados de outro, e o histórico passaria a mentir de um jeito que ninguém detecta lendo a tela | (a) autocommit por linha — deixa análise pela metade; (b) duas transações, contexto e depois resultados — o mesmo defeito em escala menor, e a segunda pode falhar sozinha | 🟢 |
| D-06 | O esquema **reusa os nomes do DDL do alvo** (`dna_analysis`, `match_result`, `skipped_match`) e **estende** o que ele não alcança, nomeando a extensão: bloco do veredito em `match_result`, mais as tabelas `match_kit` e `analysis_person` | **Achado medido:** o DDL do alvo foi escrito em **2026-09-28** e é **anterior** ao nascimento do confronto (2026-10-05). Varredura em `_reversa_sdd/migration/`: **zero** ocorrências de `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`, `confronto` ou `veredito`, e **nenhuma** tabela de metadados de kit — só `match_result.total_cm`. Sem a extensão, o veredito não teria onde morar. Nomear a extensão é o que permite a onda seguinte **reconciliar** em vez de descobrir | (a) copiar o DDL do alvo inteiro, incluindo `app_user`, `consent_record`, `data_retention_policy` — constrói no `src/` o que é das Ondas 3 e 5, sem consumidor; (b) inventar nomes novos para tudo — joga fora a herança que é o ponto do `RN-09` | 🟢 medido |
| D-07 | `init.sql` **idempotente** (`CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`, sem `DROP`), executado pelo `docker-entrypoint-initdb.d`; `gen_random_uuid()` sem extensão | O entrypoint do PostgreSQL só executa os scripts quando o diretório de dados está **vazio** — isso resolve a primeira subida, mas **não** a reexecução manual, e é a reexecução que a `RF-12` quer proteger. `gen_random_uuid()` é **nativo desde o PostgreSQL 13**, então o PG 16 não precisa de `pgcrypto`; o DDL do alvo já o usa literalmente. Adotar o mesmo gerador mantém a herança do `D-06` | (a) confiar só no comportamento de primeira subida — uma reexecução manual duplicaria ou falharia no meio; (b) `DROP TABLE` no topo do script — destrói o histórico, que é o propósito da feature e o `RF-02` | 🟢 |
| D-08 | Uploads em **bind mount** (`./src/uploads:/app/src/uploads`); dados do banco em **volume nomeado** | O pedido manda persistir os dois, e os dois têm regimes diferentes. O bind mount deixa o arquivo que o operador enviou visível no host, e a pasta **já está coberta** pelo `.gitignore` (`uploads/`, linha 34, casa em qualquer profundidade) — **nada novo a ignorar**. O diretório de dados do PostgreSQL sobre bind mount em Windows/Docker Desktop é fonte conhecida de erro de permissão, e o operador não ganha nada enxergando os arquivos internos do SGBD | (a) bind mount para os dois — expõe o diretório de dados do PG ao Windows; (b) volume nomeado para os dois — o operador perde a visibilidade do upload que ele mesmo fez, e a `RF-02` pede que o arquivo continue em `src/uploads/` | 🟢 |
| D-09 | O serviço da aplicação **não** espera o banco ficar saudável: `depends_on` na forma curta (ordem), **sem** `condition: service_healthy` | Consequência direta do `Q-03`/`RN-13`. Se a aplicação só subisse depois do banco saudável, com o banco fora do ar o operador **não teria nem a análise** — que é exatamente o desfecho que a `RN-13` existe para impedir, e o `RF-17` existe para proibir. O `healthcheck` do serviço de banco **existe** (serve ao operador e ao `docker compose ps`), mas **ninguém o consome como portão** | (a) `condition: service_healthy` — transforma o histórico em dependência de subida, contra a `RN-13` e o `RF-17`; (b) sem `depends_on` nenhum — o banco pode ainda não estar escutando na primeira análise e o aviso aparece à toa numa execução sadia | 🟢 |
| D-10 | A aplicação escuta `0.0.0.0` **dentro** do contêiner, e a publicação no host fica em `127.0.0.1` | **Medido no código:** `src/app.py:268` lê `ANALISADOR_HOST` com padrão `127.0.0.1`, e a decisão da feature 004 é que "atender a rede passa a ser ato explícito de quem opera". Dentro do contêiner, `127.0.0.1` é **inalcançável** pela publicação de porta: o encaminhamento chega pelo IP do contêiner. Com `ANALISADOR_HOST=0.0.0.0` no contêiner e `127.0.0.1:<porta>:<porta>` no host, o ato explícito passa a ser a linha de publicação — que é onde ele é **verificável**. A guarda de instância única continua valendo: no Linux o `else` de `src/app.py:310-314` roda (`SO_REUSEADDR=0`) | (a) `network_mode: host` — fura o isolamento e não tem o mesmo comportamento no Docker Desktop; (b) manter `127.0.0.1` no contêiner — a aplicação sobe e **não responde**, que é pior que não subir | 🟢 medido |
| D-11 | `Dockerfile` em `docker/`, `docker-compose.yml` e `init.sql` na raiz, e o **`.dockerignore` na raiz** — desvio declarado do `Q-05` | O `Q-05` respondeu "`docker/**` mais os dois arquivos da raiz", e o RNF de Operação registrou `Dockerfile`/`.dockerignore` em `docker/`. **A medição desta investigação corrige um dos dois:** o contexto de build precisa ser a **raiz** (é de lá que vêm `src/` e `requirements.txt`), e o Docker lê o `.dockerignore` **apenas no topo do contexto** — em `docker/` ele é ignorado. A consequência não é cosmética: sem ele, o contexto enviado ao daemon carrega `.venv/`, `docs/`, `plugins/`, `_reversa_sdd/`, `_reversa_forward/` e **`src/uploads/` com o GEDCOM real de 5,3 MB do operador** (`architecture.md#7`, achado C da 007), o que atrita com a intenção do Princípio I. O `COPY` do Dockerfile também é **estreito** (só `src/` e `requirements.txt`), para que o `.dockerignore` seja defesa em profundidade e não a única barreira | (a) `.dockerignore` em `docker/` — o Docker o ignora e o dado real vai para o contexto; (b) contexto = `docker/` — `src/` e `requirements.txt` ficam de fora e o `COPY` falha; (c) dispensar o `.dockerignore` — o contexto carrega o dado real; (d) `Dockerfile` na raiz também — mais simples, mas contraria o `Q-05` sem necessidade, já que `docker/**` está liberado | 🟢 medido |
| D-12 | O `RF-14` é atendido por **consulta SQL documentada**, sem código novo | O critério de aceite do `RF-14` é "uma consulta direta ao banco devolve o veredito e os kits da análise mais recente". Criar CLI ou rota seria **interface nova**, que o próprio requisito nega. A consulta entra no `onboarding.md` e roda por `docker compose exec db psql` | (a) script `consultar.py` — um segundo ponto de entrada para ler o que o `psql` já lê; (b) rota `/historico` — é a tela que o §12 do `requirements.md` declara fora de escopo | 🟢 |
| D-13 | **Nenhum arquivo novo de configuração além dos de infraestrutura**: sem `.gitignore` novo, sem `.env.example`, sem rota, sem CLI | `.gitignore` e um `.env.example` estariam **fora de `allowedPaths`**, e o `README.md` está dentro. **Medido:** o bind mount de uploads cai em `uploads/`, que o `.gitignore` **já** cobre; o volume do banco vive fora do repositório; `.env` já está ignorado (linha 6). Então não há linha de ignore a acrescentar — e criar `.env.example` seria ato do usuário para cobrir uma necessidade que não foi medida | (a) criar `.env.example` — arquivo novo na raiz, fora de `allowedPaths`, sem necessidade; (b) acrescentar linhas ao `.gitignore` — exigiria ato do usuário para cobrir caminhos já cobertos | 🟢 medido |
| D-14 | Os dois portões — suíte e paridade — rodam **sem** `DATABASE_URL`, e a persistência real é provada em dois passos separados no `onboarding.md` | É o que torna o `RF-13` verificável em vez de retórico: a suíte (`261`) e a paridade (`100 %`) são medidas **sem** o banco, e o onboarding fecha com um passo que sobe o stack, grava e lê uma análise, e outro que **derruba o banco** e prova que a análise continua saindo com aviso | (a) rodar a suíte contra o banco — a suíte passaria a depender de ambiente, que é o defeito que a 007 acabou de eliminar; (b) aceitar a garantia por leitura de código — a `RN-13` é comportamental e só medição a sustenta | 🟢 |
| D-15 | A persistência é **projeção pura do resultado**: nenhum campo é recalculado e o caminho de gravação não chama nenhuma função do núcleo | É a forma mais forte de garantir a `RN-02` e a `RN-05`: se o gravado é o que o núcleo produziu e nada mais, não existe segunda autoridade para divergir. A consequência é **declarada e tem dois itens**, os dois medidos por leitura: o **`root_was_ambiguous` estruturado** do `RF-03` e o **sexo/datas dos nós do caminho** do `RF-04` **não existem** na saída do núcleo — a ambiguidade da raiz chega só como **texto** em `observations` (`core/dna_analysis.py:182-189`), e os nós intermediários chegam com `id` e `nome` apenas (`:243-249`). Persiste-se o que existe, e `analysis_person.completa` distingue ficha completa de mera identificação | (a) mudar a saída do núcleo para expor o booleano e as fichas dos nós — quebra o `W016` (assinatura de retorno congelada, com asserções que a desempacotam) e a paridade, que compara o resultado coletado; (b) chamar `person_summary` no caminho de gravação — recalcula o que o núcleo já decidiu e acopla a persistência ao domínio; (c) derivar o booleano do texto de `observations` — inferência a partir de mensagem de contrato, que é exatamente o que a feature 006 abandonou ao criar o campo de desfecho | 🟢 medido |
| D-16 | `observations`, `causes` e `detail` são persistidos como **texto, ao caractere**; o **código** dos avisos **não** é persistido | O núcleo entrega `warnings` com `code` e `message`, mas a análise já produz a lista **deduplicada de textos** por resultado (`_observacoes`, `core/dna_analysis.py:100-115`), e o `code` não é correlacionável a resultado nenhum sem reabrir o núcleo. O que se preserva é o que o operador **leu** — que é o insumo da auditoria —, e o código fica como lacuna declarada (`DD-01` do `data-delta.md`) | (a) persistir o `code` — exigiria mudar o núcleo para carregá-lo junto ao resultado; (b) remapear o código a partir do texto — parsing de mensagem de contrato | 🟢 |
| D-17 | Os testes que **exigem banco** são marcados e **pulados** quando `DATABASE_URL` está ausente; a prova de ponta a ponta com o stack no ar vive no `onboarding.md` e em `evidence/` | Consequência direta do `RF-13` e da `D-14`: a suíte tem de passar **sem** banco, e um teste de gravação sem banco ou falha ou precisa de ambiente — as duas coisas reintroduzem a dependência que esta feature existe para não criar. O pulo é **declarado** e justificado, nunca um teste que passa por não rodar em silêncio: o `onboarding.md` §8 e §9 executam os mesmos caminhos com o stack no ar, e o `T022` registra os **dois** números da suíte, com e sem banco | (a) deixar os testes de banco na suíte padrão — quebra o `RF-13` na primeira execução sem Docker; (b) fingir o banco com um duplo em memória — testaria o duplo, e não o `init.sql`, a transação nem o esquema, deixando o `RF-10` sem prova real; (c) não escrever teste de gravação e confiar só no onboarding — deixa a projeção e a ida e volta do cM sem cobertura automatizada | 🟢 |
| D-18 | O `.dockerignore` é **lista de permissão**, e não de negação: `*` na primeira linha, depois `!requirements.txt`, `!src/`, `!src/**`, e por último `src/uploads/` e `src/**/__pycache__/` para reexcluir | **Medido pela auditoria de 2026-10-08** (`A002` do `audit/cross-check.md`): a raiz do projeto tem **22** diretórios que recusam `os.scandir`, e a lista de negação do `D-11` cobria **12** — **10 ficavam dentro do contexto de build**: sete em `.pytest-tmp/`, dois em `_probe_acl/` e um em `_probe_acl2/`. `docker build` percorre o contexto e **aborta** neles, exatamente como abortou com o `.probe/` desta sessão: o `T008` não subiria o stack e o Bloco 0 não fecharia, por um defeito que **não é do produto**. A lista de permissão é imune ao resíduo de hoje e ao de amanhã porque inverte a regra: o que não está nomeado não entra | (a) acrescentar `.pytest-tmp/`, `_probe_acl*/`, `.parity-run-*/`, `.pytest_cache/`, `.reversa/`, `.obsidian/`, `.agents/`, `.github/` e `.vscode/` à lista de negação — resolve os 22 de hoje e **quebra no próximo resíduo preso**, porque a lista enumera só o que se conhece; (b) usar um subdiretório como contexto de build — `src/` e `requirements.txt` ficariam de fora e o `COPY` do `T003` falharia; (c) limpar os diretórios presos antes de construir — exige shell elevado que a sessão não tem, e a feature não pode depender de um ato de terceiro | 🟢 medido |

## 4. Premissas

Nenhuma. O `requirements.md` desta feature foi fechado com **zero** marcadores
`[DÚVIDA]`: as três dúvidas da versão inicial foram resolvidas na sessão de esclarecimento
de 2026-10-08, e as duas questões que não eram dúvida (`Q-02`, escopo dos dados de pessoa;
`Q-05`, layout da infraestrutura) também foram decididas na mesma sessão, registradas na §9
daquele documento. Nada aqui depende de premissa não decidida.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `RegistroDeAnalises` (novo `Protocol`) | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | contrato-novo | A **quarta** porta da fronteira: registrar a análise e devolver `(referencia, aviso)`. Não toca `RepositorioDeArvores`, que é da árvore (`D-01`) |
| `RegistroDeAnalisesPostgres` | `_reversa_sdd/architecture.md#3` | componente-novo | Adaptador concreto, `psycopg2`, SQL à mão, conexão por chamada e transação única (`D-03`, `D-04`, `D-05`) |
| `src/application/dna_analysis.py` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | contrato-alterado | O caso de uso passa a **receber a porta** e a chamá-la depois do fluxo do núcleo; `ResultadoDeAnalise` ganha `aviso_de_persistencia: str \| None = None`, campo novo com valor padrão, para não quebrar as construções existentes |
| `index()` em `src/app.py` | `_reversa_sdd/architecture.md#1` | regra-alterada | Monta o registrador (nulo quando não há `DATABASE_URL`) e repassa o aviso ao template. **Nenhum passo de domínio volta para a rota** — persistir é I/O de borda, e a `RF-01` da 006 continua verdadeira |
| `src/templates/index.html` | `_reversa_sdd/architecture.md#1` | regra-alterada | Bloco de aviso **não bloqueante** na seção de DNA, reusando a classe `.alerta-aviso` que já existe (`:27`), sob `{% if aviso_de_persistencia %}`. **Com a persistência desabilitada ou bem-sucedida, nada é renderizado** — é o que preserva o contrato congelado de tela |
| `src/core/` (todo o pacote) | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** Nem `dna_analysis.py`, nem `evidence_comparison.py`, nem `erros.py`. É a `RN-01`: o núcleo não conhece persistência |
| `src/parsers/`, `src/reporting/`, `src/utils/` | `_reversa_sdd/architecture.md#3` | presença | **Nenhuma alteração.** `utils/validate.py` continua a autoridade única da regra de upload, e `reporting/mermaid_render.py` continua intocado — o Mermaid não é persistido |
| `RepositorioDeArvores` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (`D-03`, `RF-08`) | presença | **INALTERADO.** Continua declarado, **sem implementação e sem consumidor**, como a 007 o deixou. Esta feature cria uma porta **diferente** e não o preenche |
| `requirements.txt` | `_reversa_sdd/dependencies.md#2` | regra-alterada | Ganha **uma** linha pinada (`psycopg2-binary==2.9.13`). As seis diretas e as duas transitivas promovidas não mudam de versão |
| Dívida #8 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | regra-alterada | **Parcialmente fechada, e o registro é preciso:** "nada é persistido entre requisições" deixa de ser verdade para o **histórico de resultados**. O que **permanece** é a análise sob demanda, sem cache entre requisições, que passa a ser decisão declarada (`RN-12`), não ausência de decisão |
| Dívidas #3 e #4 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADAS.** A guarda continua de processo, não de thread; o `dono` ganha **coluna**, sem filtro e sem isolamento. A `RN-10` proíbe declarar o contrário |
| Dívida #10 (`architecture.md#7`) | `_reversa_sdd/architecture.md#7` | presença | **INALTERADA.** O CSV de DNA continua sem validação de conteúdo |
| `docker-compose.yml` | `_reversa_sdd/architecture.md#2` | componente-novo | Dois serviços (`db`, `app`), um bind mount e um volume nomeado, `healthcheck` no banco e **sem** portão de saúde para a aplicação (`D-08`, `D-09`) |
| `init.sql` | `_reversa_sdd/migration/target_data_model.md#Schema (DDL)` | componente-novo | Esquema idempotente, alinhado ao alvo e com as duas extensões nomeadas (`D-06`, `D-07`) |
| `docker/Dockerfile` | *(infraestrutura, fora da extração)* | componente-novo | `python:3.14-slim`, `COPY` estreito, `waitress` por `src/app.py`, `ANALISADOR_HOST=0.0.0.0` (`D-10`, `D-11`) |
| `.dockerignore` (raiz) | *(infraestrutura, fora da extração)* | componente-novo | **Precisa estar na raiz para valer** (`D-11`) e é **lista de permissão** (`D-18`): `*`, `!requirements.txt`, `!src/`, `!src/**`, e `src/uploads/` com `src/**/__pycache__/` reexcluídos no fim |
| `_reversa_sdd/migration/target_data_model.md` | `_reversa_sdd/migration/target_data_model.md` | presença | **NÃO É REESCRITO** — os artefatos de migração estão preservados sem regeneração desde 2026-09-28. Esta feature **nomeia** a divergência (§3 `D-06`, §6); reconciliar o artefato é ato da onda seguinte |
| `tests/` | *(infraestrutura de teste)* | componente-novo | Três arquivos novos (ou classes novas): os três estados da persistência, a ida e volta do cM e a idempotência do esquema. **Nenhum teste existente é removido, desabilitado ou renomeado** |
| `README.md` | *(raiz do projeto)* | presença | **NÃO É TOCADO.** A documentação executável desta feature vive no `onboarding.md`. O arquivo está em `allowedPaths`, então atualizá-lo é ato do usuário, não desta feature |

## 6. Delta no modelo de dados

- **Resumo das mudanças:** o sistema sai de **27 estruturas e nenhuma tabela** para
  **27 estruturas e 6 tabelas**. Nada é removido, nada é renomeado e **nenhum dado é
  migrado** — não existe dado persistido a migrar, porque o sistema nunca persistiu
  resultado de análise. As seis tabelas são `dna_analysis`, `match_result`,
  `match_path_node` e `skipped_match` — **herdadas** do DDL do alvo, com o bloco do veredito
  acrescentado a `match_result` —, mais `match_kit` e `analysis_person`, que são
  **extensões declaradas** porque o DDL congelado não modela kit nem pessoa da análise
  (`D-06`). A tabela de versão de esquema foi considerada e **descartada**: sem runner de
  migração ela seria decoração, e o alvo também não a tem. O par `(nome do CSV, kit)` é a
  chave da evidência, como no núcleo — **nunca somada entre kits**. O cM é transportado,
  com precisão suficiente para não cruzar limite de faixa (`RN-05`, `RISK-004`).
- **O que deliberadamente NÃO entra no banco:** a árvore completa, os segmentos por
  linha do CSV, o texto do Mermaid e a lista de nomes da tela. Os três primeiros são
  dado bruto que já vive no arquivo imutável de `src/uploads/` sob chave de conteúdo
  (`RN-04`); o último é a exposição que o `gaps.md#6` já encaminhou à Onda 4.
- Detalhe completo em: `_reversa_forward/008-persistencia-postgres-docker/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` (as três `action` do formulário) | HTTP | **não alterado.** Mesmas rotas, mesmos campos, mesmos status, mesmos literais. O **único** delta possível é o aviso não bloqueante do `RF-17`, e ele só aparece no terceiro estado (persistência habilitada **e** gravação falhando). O diretório `interfaces/` **não** é criado: não há contrato novo de HTTP, fila, gRPC ou GraphQL nesta feature |
| Layout de arquivos em `src/uploads/` | arquivo | **não alterado.** `<chave sha256 truncada>__<nome visível>`, um arquivo por conteúdo. O caminho **dentro do contêiner** passa a ser `/app/src/uploads`, porque é o que `_pasta_uploads()` (`src/app.py:99-114`) deriva de `__file__`; o bind mount preserva o caminho do host |
| Esquema do banco de dados | banco relacional | **contrato novo, e o único novo.** Ele é o objeto do `data-delta.md`, que é onde o detalhe vive — a lista de tabelas e colunas, os índices e a herança do DDL do alvo. Não é um contrato externo de rede: é a fronteira de persistência, atrás da porta `RegistroDeAnalises` (`D-01`) |

## 8. Plano de migração

> **Não há dado a migrar.** O sistema nunca persistiu resultado de análise, então não
> existe registro a converter, a reindexar ou a reescrever. A "migração" aqui é de
> **infraestrutura e de código**, em três blocos com medição entre eles — e o critério
> que separa os blocos é o mesmo da 007: o bloco 0 muda o **ambiente** e não toca Python
> de produção; o bloco 1 muda o **código**; o bloco 2 confere o **escopo**.

1. **Bloco 0 — infraestrutura e esquema.** Escrever `docker-compose.yml`, `init.sql`,
   `docker/Dockerfile` e o `.dockerignore` da raiz (`D-07`, `D-08`, `D-09`, `D-10`,
   `D-11`), e acrescentar o pin do driver ao `requirements.txt` (`D-03`).
   **Medir:** `docker compose config` válido; os dois serviços sobem; `init.sql` executado
   **duas vezes** não quebra nem duplica (`RF-12`); a aplicação responde em
   `127.0.0.1:<porta>` com `ANALISADOR_HOST=0.0.0.0` no contêiner (`D-10`); e as
   varreduras de portão seguem **iguais** — `261 passed` e `PARIDADE 100%` —, porque
   nenhuma linha de Python de produção mudou ainda.
   ⚠️ **Pré-requisito de permissão:** `.dockerignore` **não** está em `allowedPaths`
   (ver §9). Sem o ato do usuário, o bloco 0 para no primeiro arquivo.
2. **Bloco 1 — a costura da persistência.** Criar a porta `RegistroDeAnalises` e o
   adaptador `RegistroDeAnalisesPostgres` (`D-01`, `D-03`, `D-04`, `D-05`); fazer o caso
   de uso recebê-lo e devolver o aviso (`D-02`); montar o registrador na borda com a
   regra dos três estados e repassar o aviso ao template (`D-02`); acrescentar o bloco de
   aviso ao `index.html`.
   **Medir, nesta ordem:** (a) suíte e paridade **sem** `DATABASE_URL` — `261 passed` e
   `PARIDADE 100%`, byte a byte iguais ao bloco 0 (`RF-13`, `D-14`); (b) com o stack no
   ar e a variável presente, uma análise grava, e a consulta do `RF-14` devolve o
   veredito e os kits (`D-12`); (c) com o banco **derrubado**, a análise conclui, a tela
   mostra o mesmo veredito e o aviso não bloqueante aparece (`RF-17`); (d) nenhuma
   análise parcial em (c) (`RF-10`).
3. **Bloco 2 — fechamento e escopo.** Conferir por diff que `src/core/`, `src/parsers/`,
   `src/reporting/` e `src/utils/` **não têm alteração nenhuma** (`RN-01`); conferir que
   `pytest.ini`, `.gitignore` e os artefatos de `_reversa_sdd/migration/` estão
   intocados; conferir `git status` contra `src/uploads/`, `uploads/` e contra o
   contexto de build; registrar o **novo** número da suíte (que cresce com os testes
   novos) mantendo `261` como leitura histórica; rodar a verificação manual do
   `onboarding.md`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O contexto de build levar **dado genético real** ao daemon do Docker — `src/uploads/` contém o GEDCOM real de 5,3 MB do operador (Achado C do `actions.md` da feature 007) | **alto** | **alta** | Duas barreiras independentes (`D-11`): `.dockerignore` **na raiz** (em `docker/` o Docker o ignora) e `COPY` **estreito**, que copia só `src/` e `requirements.txt`. O `T010` mede o contexto antes de construir, e o critério de pronto confere que `src/uploads/` fica fora |
| O contexto de build ser **ilegível** e derrubar o `docker build` — medido pela auditoria em 2026-10-08: **22** diretórios da raiz recusam `os.scandir`, e **10** deles ficavam fora da lista de exclusão original | **alto** | **alta** (medida) | `D-18`: o `.dockerignore` passa a ser **lista de permissão**, e nenhum diretório não nomeado entra no contexto. O `T002` escreve essa lista, o `T010` mede o contexto depois, e o `T008` é quem acusaria a falha |
| Alguma forma de conexão acabar no **import** de `src/app.py`, quebrando a suíte e a paridade por ambiente | **alto** | média | **Medido:** `tests/conftest.py:166-171` e `_reversa_sdd/parity/harness.py:356` importam `app.py`. A `D-02` proíbe conexão no import, o registrador é nulo sem `DATABASE_URL`, e um teste **importa `app.py` sem a variável** e afirma que a página é idêntica — o modo de falha é reconhecível, e não "erro de ambiente na máquina" |
| O aviso do `RF-17` mudar o contrato congelado de tela e derrubar a paridade das 6 fixtures | alto | baixa | A regra dos três estados (`D-02`): **sem** `DATABASE_URL` não há aviso e a página é idêntica; o aviso só existe no terceiro estado. A paridade roda sem a variável, e o teste do estado desabilitado compara a página com e sem a persistência configurada |
| `init.sql` não idempotente apagar ou duplicar o histórico numa reexecução | alto | baixa | `D-07`: `IF NOT EXISTS` em tudo e **nenhum** `DROP`; passo dedicado no onboarding que executa o script duas vezes e confere a contagem de tabelas e de linhas |
| Precisão do cM: gravar e reler altera o último dígito e **cruza um limite de faixa** | alto | média | `RISK-004` é mitigado por desenho (`RN-05`): o cM é **transportado** do núcleo e persistido como valor; **nunca** se usa `SUM` do banco no lugar do total do núcleo; teste de ida e volta do cM com valor de fronteira (46, 200, 553, 1317, 2200, 3300) |
| Alguém reintroduzir `condition: service_healthy` "para garantir a ordem de subida" | **alto** | média | `D-09` declara o motivo, e o passo (c) do bloco 1 **mede** o comportamento com o banco derrubado: se a aplicação deixar de subir ou de responder, o `RF-17` está violado e o sintoma é imediato |
| Bind mount do diretório de dados do PostgreSQL em Windows/Docker Desktop | médio | média | `D-08`: o dado do banco vai para **volume nomeado**. O bind mount fica só para os uploads, onde o acesso é do operador e o formato é arquivo, não B-tree |
| Dado real do operador aparecer em fixture, evidência ou captura de tela | médio | alta | Princípio I: os testes usam as fixtures sintéticas que já existem (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`), a verificação manual usa `SAMPLE_GED`, e o critério de pronto confere `git status` e a pasta `evidence/` |
| A entrega ser lida como fechamento das dívidas **#3** (corrida entre threads) ou **#4** (isolamento) | médio | **alta** | `RN-10` proíbe a afirmação em qualquer artefato desta feature; a coluna de `owner_id` **não** filtra nada e **não** tem índice de escopo; o `onboarding.md` tem uma seção "o que esta feature **não** fez", no padrão da 007 |
| A dívida **#8** ser declarada integralmente fechada | médio | média | O §5 registra o delta com precisão: fecha o **histórico de resultados**, e **não** a análise sob demanda — que passa a ser decisão declarada (`RN-12`), não ausência de decisão |
| `.dockerignore` e `docker/**` fora de `allowedPaths`, e o bloco 0 parar no primeiro arquivo | **alto** | **alta** | Declarado no §8 e no §10; a liberação é **ato do usuário** e precisa acontecer antes do `/reversa-coding`. O Reversa não edita `reversa.config.json` por iniciativa própria |
| A persistência mudar o resultado por efeito colateral da leitura do CSV, do matching ou da ordem | alto | baixa | `RN-01` mantém o núcleo intocado e o bloco 2 confere por diff; a paridade nas 6 fixtures é medida **nos dois blocos**, e a regra de comparação da suíte é por **conjunto**, não por total |
| O índice de cM do alvo ser herdado por hábito, e a releitura do histórico devolver ordem diferente da que a tela exibiu | médio | média | **Achado medido** e registrado no `data-delta.md` §4: a ordem do núcleo é `(tem_caminho primeiro, −cM depois)` — `core/dna_analysis.py:266-270` —, e **não** cM decrescente puro. Logo o `ix_match_analysis_cm` do alvo **não** reproduz a ordem exibida, e o índice criado é `(analysis_id, result_ordinal)`. O teste do `RF-09` compara a ordem relida com a ordem exibida |
| `RF-03` e `RF-04` entregues com desvio: ambiguidade da raiz só como texto, e nós do caminho sem sexo nem datas | médio | **alta** | `D-15` declara o desvio, e o `data-delta.md` §6 mede a causa na saída do núcleo (`dna_analysis.py:182-189`, `:243-249`). O `/reversa-audit` é o lugar de recusá-lo. Nenhum dos dois é resolvido mudando o núcleo: o `W016` congela a assinatura de retorno, e a paridade compara o resultado coletado |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado, incluindo o aviso de que `RepositorioDeArvores` segue
      sem implementação e sem consumidor
- [ ] Suíte completa medida com `.venv\Scripts\python.exe`, com o comando ao lado do número,
      e **`261` preservado como leitura histórica** (`RF-13`, `D-14`)
- [ ] Paridade diferencial em **100 %**, exit 0, medida **sem** `DATABASE_URL` (`RF-13`)
- [ ] Nenhum teste existente removido, desabilitado, renomeado ou com asserção reescrita
- [ ] `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` sem nenhuma alteração;
      nenhum deles importa acesso a dados (`RN-01`)
- [ ] `docker compose` sobe os dois serviços com **um** comando, e `down` + `up` preserva
      `src/uploads/` **e** os dados do banco (`RF-01`, `RF-02`)
- [ ] O banco **não** é publicado fora de `127.0.0.1` (`RF-01`)
- [ ] `init.sql` executado **duas vezes** não quebra nem duplica (`RF-12`)
- [ ] Uma análise gravada tem contexto, pessoas usadas, kits, veredito com porquê e ordem,
      e a leitura devolve a **mesma** ordem (`RF-03` a `RF-09`)
- [ ] Os **quatro** estados do confronto são graváveis e o gravado é igual ao exibido (`RF-06`)
- [ ] Dois kits do mesmo nome geram **dois** registros e **nenhum** total somado (`RF-05`)
- [ ] Campo desconhecido entra `null`, nunca zero — incluindo cM não utilizável (`RN-11`)
- [ ] Falha no meio da gravação não deixa análise parcial (`RF-10`)
- [ ] Com o banco **derrubado**, a análise conclui, o veredito é o mesmo e o aviso não bloqueante aparece (`RF-17`)
- [ ] Com a persistência **desabilitada**, a página é idêntica à de antes da feature (`D-02`)
- [ ] Nenhuma credencial em código, arquivo versionado, template, log ou camada da imagem;
      `DATABASE_URL` só do ambiente (`RF-11`)
- [ ] A consulta do `RF-14` está documentada no `onboarding.md` e devolve o veredito e os kits
- [ ] A dependência nova está **pinada** no `requirements.txt` e instalada no `.venv/` (`RF-15`)
- [ ] `git status` não lista arquivo de upload nem dado de banco (`RF-16`)
- [ ] `.dockerignore` **na raiz** e como **lista de permissão**, e o contexto de build
      comprovadamente **não** inclui `src/uploads/` nem os diretórios presos (`D-11`, `D-18`)
- [ ] ✅ **ATENDIDO** — o `T026` mediu **`1,08×`** contra o limite de "abaixo do dobro", na
      escala que corresponde ao caso real (**19.682 pessoas sintéticas, 71 matches**): 5.088 ms
      sem persistência contra 5.501 ms com ela, acréscimo absoluto de **413 ms**. ⚠️ Na escala
      pequena (5 pessoas) a razão é `8,16×` e **não** significa nada — o instrumento é que era
      pequeno demais. Ver `evidence/T026-custo-da-gravacao.md` e `evidence/_gerar_fixture.py`
- [ ] `pytest.ini`, `.gitignore` e os artefatos de `_reversa_sdd/migration/` intocados
- [ ] Nenhuma afirmação, em nenhum artefato da feature, de que as dívidas #3 ou #4 foram fechadas (`RN-10`)
- [ ] `RF-03` e `RF-04` entregues com o desvio de `D-15` **declarado**: a ambiguidade da raiz
      preservada **como texto** em `observations`, e `analysis_person.completa` distinguindo
      ficha completa de mera identificação
- [ ] Nenhum índice começa por `owner_id`, e o `ix_match_analysis_cm` do alvo **não** é
      criado (`RN-10`, `data-delta.md` §4)
- [ ] O `reason` dos descartes é **texto do núcleo**, sem mapa de código inventado (`data-delta.md` §3.5)
- [ ] Verificação manual do `onboarding.md` executada e registrada em `evidence/`, com dado **sintético**

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-08 | Medição da linha de base antes do plano: suíte `261 passed`, paridade `100 %` exit 0, Docker `29.6.1`/`v5.2.0` no host. Medição de wheels `cp314` e de imagens base pela API do PyPI e do Docker Hub, porque `pip download` e `pip install --dry-run` falham nesta máquina pelo defeito de `0o700` já documentado | reversa |
| 2026-10-08 | `D-11` corrige o `Q-05` num ponto: o `.dockerignore` precisa ficar na **raiz** para o Docker lê-lo, e o `Q-05` o havia registrado em `docker/`. Registrado como desvio declarado, com a consequência medida (o contexto levaria `src/uploads/` com dado real) | reversa |
| 2026-10-08 | A leitura da saída do núcleo, feita antes de fechar o esquema, encontrou **dois limites** da assinatura congelada pelo `W016`: a ambiguidade da raiz só existe como texto, e os nós do caminho só carregam `id` e `nome`. Registrado em `D-15` e no `data-delta.md` §6 em vez de silenciado; o esquema passa a distinguir ficha completa de identificação (`analysis_person.completa`) | reversa |
| 2026-10-08 | `D-06` refinado por medição: o índice de cM do alvo (`ix_match_analysis_cm`) **não** reproduz a ordem do núcleo, que é `(tem_caminho, −cM)` e não cM decrescente puro. O índice criado passa a ser `(analysis_id, result_ordinal)`, e a divergência fica declarada no `data-delta.md` §4 | reversa |
| 2026-10-08 | `D-17` acrescentada na decomposição: os testes que exigem banco são **pulados** sem `DATABASE_URL`, para que a suíte continue passando sem Docker — que é o `RF-13`. Sem esta decisão, o `T014` do `actions.md` quebraria a suíte na primeira execução sem banco | reversa |
| 2026-10-08 | `D-18` acrescentada no fechamento da auditoria: o `.dockerignore` vira **lista de permissão**. A auditoria mediu a raiz e encontrou **22** diretórios que recusam `os.scandir`, com **10** fora da lista de negação do `D-11` — `docker build` abortaria neles. O critério de pronto ganha o custo da gravação (`A003`), e a citação "achado C da 007" passa a apontar o arquivo (`A009`). Os dez achados de `audit/cross-check.md` foram fechados por edição nos dois artefatos; **o relatório de auditoria não foi alterado** | reversa |
