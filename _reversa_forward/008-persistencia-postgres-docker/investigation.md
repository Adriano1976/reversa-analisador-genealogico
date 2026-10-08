# Investigation: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Requirements: `_reversa_forward/008-persistencia-postgres-docker/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. O que esta investigação precisou decidir

Quatro perguntas, e nenhuma delas é de gosto — todas mudam o resultado do bloco 0 ou do
bloco 1 do §8 do `roadmap.md`:

1. **O driver roda no `3.14.6` do projeto, sem compilar nada?** — se não rodasse, o bloco 0
   pararia antes de existir.
2. **Onde a gravação entra, sem corromper a arquitetura de funções puras?** — é a condição
   explícita do pedido.
3. **O que o Docker faz com o contexto de build deste repositório?** — a resposta envolve
   dado genético real.
4. **O que acontece com a suíte e com a paridade quando a persistência é adicionada?** — o
   instrumento é o portão, e ele já foi quebrado uma vez por ambiente entre as features
   005 e 006.

## 2. Fatos medidos nesta sessão

Cada linha foi produzida por execução, não por leitura de documentação. As três primeiras
usam o interpretador oficial (`.venv\Scripts\python.exe`, `3.14.6`).

| # | O que foi medido | Como | Resultado |
|---|---|---|---|
| M-01 | Linha de base da suíte | `.venv\Scripts\python.exe -m pytest -q` | `261 passed` em 27,14 s — 0 falhas, 0 erros |
| M-02 | Linha de base da paridade | `.venv\Scripts\python.exe _reversa_sdd\parity\harness.py` | `PARIDADE 100%% (zero divergencia)`, exit 0, nas 6 fixtures |
| M-03 | Docker no host | `docker --version` / `docker compose version` | `29.6.1` / `v5.2.0` — **instalados**, então a feature é executável nesta máquina |
| M-04 | Wheel do driver para `cp314`/Windows | API JSON do PyPI (`pypi.org/pypi/<pacote>/json`), filtrando `cp314` + `win_amd64` | `psycopg2-binary 2.9.13` → **1** wheel `cp314`; `psycopg-binary 3.3.6` → **1**; `SQLAlchemy 2.1.4` → **2** (inclui `cp314t`, o build sem GIL) |
| M-05 | Imagens base disponíveis | API de tags do Docker Hub | `python:3.14-slim` (e `-trixie`, `-bookworm`) **existe**; `postgres:16-alpine` (até `16-alpine3.24`) **existe** |
| M-06 | `pip download` e `pip install --dry-run` nesta máquina | execução direta, com `TEMP`/`TMP` apontados para o workspace | **`PermissionError [Errno 13]`** nos dois — o pip usa `tempfile.mkdtemp`, e `0o700` nesta máquina não é listável, gravável nem removível (`tests/conftest.py` §1) |
| M-07 | O harness de paridade importa `src/app.py` | `grep` em `_reversa_sdd/parity/harness.py` | `:356` — `import app as APP`, dentro do coletor do candidato, com `sys.path.insert(0, .../src)` em `:258` |
| M-08 | A suíte importa `src/app.py` | leitura de `tests/conftest.py` | `:166-171` — `spec.loader.exec_module` do `src/app.py` no fixture `cliente_de_upload` |
| M-09 | A pasta de upload é derivada de `__file__` | leitura de `src/app.py:99-114` | `os.path.dirname(os.path.abspath(__file__))` + `"uploads"` → em contêiner, `/app/src/uploads`. `ANALISADOR_UPLOAD_FOLDER` sobrepõe |
| M-10 | O host de escuta tem padrão `127.0.0.1` | leitura de `src/app.py:268` | `os.environ.get("ANALISADOR_HOST", "127.0.0.1")`; a guarda de instância única usa `SO_EXCLUSIVEADDRUSE` no Windows e `SO_REUSEADDR=0` no `else` |
| M-11 | Não existe Dockerfile, compose nem `.dockerignore` | `glob` na raiz | **nenhum** dos três; é o motivo declarado de o `deployment.md` da extração não ter sido gerado |
| M-12 | `src/uploads/` contém dado real | `_reversa_sdd/architecture.md#7` (dívida) e achado C do adendo da 007 | **33 entradas**, incluindo `Arvore_Unificada_Oficial_V1_2.ged`, de **5,3 MB** — GEDCOM real do operador |
| M-13 | O DDL do alvo ignora o confronto | `grep` em `_reversa_sdd/migration/` | **zero** ocorrências de `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`, `confronto` ou `veredito`; **nenhuma** tabela de kit |
| M-14 | O template já tem a classe de aviso | `grep` em `src/templates/index.html` | `:27` — `.alerta-aviso` (borda amarela), já usada em `:258`, `:408`, `:480`, `:493`. O aviso do `RF-17` reusa a classe existente: **nenhum CSS novo** |
| M-15 | O `.gitignore` já cobre os estados persistentes | leitura de `.gitignore` | `uploads/` (linha 34, casa em qualquer profundidade) e `.env` (linha 6). **Nada novo a ignorar** |

> ⚠️ **M-06 é um defeito de ambiente, não desta feature**, e é o terceiro artefato do
> projeto a registrá-lo: a causa está medida em `tests/conftest.py` §1 e no adendo da 007.
> A consequência prática para quem repetir esta investigação: **medir wheel por `pip` não
> funciona aqui**; a API do PyPI funciona e não usa diretório temporário.
>
> 🔴 **Resíduo desta sessão, declarado.** A tentativa de M-06 deixou um diretório **preso**:
> `_reversa_forward/008-persistencia-postgres-docker/.probe/tmp/`, com 20 entradas `pip-*`.
> Ele foi criado com `0o700` e **não é removível** por nenhum dos três métodos tentados:
> `Remove-Item -Recurse -Force` falha, `cmd /c rd /s /q` devolve "Acesso negado" em 20
> arquivos, e `icacls /reset /T` responde "Processados com sucesso 0 arquivos; falha no
> processamento de 20". É a mesma classe dos 13 diretórios presos que o projeto já
> documenta — este é o **14º**, e é resíduo **desta** sessão, não do legado. A remoção exige
> shell elevado:
>
> ```powershell
> takeown /f _reversa_forward\008-persistencia-postgres-docker\.probe /a
> icacls _reversa_forward\008-persistencia-postgres-docker\.probe /reset /t
> rd /s /q _reversa_forward\008-persistencia-postgres-docker\.probe
> ```
>
> **Consequência para o bloco 0, e não é cosmética:** enquanto ele existir, o `.dockerignore`
> **precisa** excluir `.probe/`. Sem isso, o contexto de build passa a carregar um diretório
> ilegível e o `docker build` falha por um motivo que não é do produto. A exclusão de
> `_reversa_forward/` no `.dockerignore` (`D-11`) já cobre este caso — o registro existe para
> que a razão esteja escrita ao lado de quem for remover a linha um dia.

## 3. Alternativas avaliadas

### 3.1 Driver de banco

| Alternativa | Prós | Contras medidos ou declarados | Veredito |
|---|---|---|---|
| **`psycopg2-binary`** | Uma dependência; nome dado pelo solicitante; wheel `cp314`/win **medido** (M-04) | É a linha em manutenção, e o `psycopg` 3 é o sucessor | **escolhida** (`D-03`) |
| `psycopg` 3 (`psycopg[binary]`) | Também tem wheel `cp314` **medido**; API mais moderna | Troca o nome pedido sem ganho medido para "uma conexão e uma transação por análise" | descartada |
| SQLAlchemy | ORM maduro, migrations por Alembic (que o alvo recomenda, `AMB-019`) | Peso; e um ORM convida a mover decisão de domínio para a camada de persistência, contra a `RN-01` e a `RN-12`. O DDL do alvo é **SQL literal** | descartada |
| `asyncpg` | Alto desempenho | A aplicação é **WSGI síncrona** (Flask + waitress). Não há laço de eventos onde a assincronia rodar | descartada |
| `pyodbc` / ODBC | — | Alvo é PostgreSQL; ODBC acrescenta driver de sistema e mais uma camada de configuração | descartada |

### 3.2 Onde a gravação entra

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Porta nova + caso de uso** | É o padrão que a Onda 2 fixou: `upload_gedcom` recebe portas e orquestra I/O. O núcleo permanece puro | Exige uma porta a mais e um campo a mais em `ResultadoDeAnalise` | **escolhida** (`D-01`) |
| Direto na rota (`src/app.py`) | Menos arquivos | Devolve orquestração de I/O para a rota, que é exatamente o que a Onda 2 tirou de `index()` | descartada |
| Dentro de `src/core/dna_analysis.py` | Um lugar só | **Proibido pela `RN-01`.** Destrói a pureza que as features 005 e 006 construíram, e o núcleo passaria a falhar por ambiente | descartada |
| Implementar a porta já declarada `RepositorioDeArvores` | Aproveita contrato existente | Ela é sobre a **árvore**. A `RN-04` diz que a árvore **não** vai para o banco, e a 007 a declarou sem consumidor | descartada |
| *Evento* / fila assíncrona | Desacoplaria a gravação | Não há fila, worker ou mensageria no sistema (`architecture.md#6`), e o `RF-10` exige transação — que a assincronia tornaria mais difícil de garantir, não mais fácil | descartada |

### 3.3 Topologia de persistência em contêiner

| Item | Alternativa | Veredito |
|---|---|---|
| Uploads | **Bind mount** `./src/uploads:/app/src/uploads` | **escolhida** (`D-08`): o operador vê o arquivo que enviou, e `uploads/` já está no `.gitignore` |
| Uploads | Volume nomeado | descartada: esconde do operador o arquivo que ele mesmo enviou |
| Dados do PG | **Volume nomeado** | **escolhida** (`D-08`): bind mount do diretório de dados do PostgreSQL em Windows/Docker Desktop é fonte conhecida de erro de permissão |
| Dados do PG | Bind mount `./.pgdata` | descartada pelo motivo acima, e exigiria linha nova no `.gitignore` |
| Subida | `depends_on` curto, **sem** `service_healthy` | **escolhida** (`D-09`): com portão de saúde, o banco fora do ar impediria até a análise, contra a `RN-13`/`RF-17` |
| Subida | `condition: service_healthy` | descartada: transforma o histórico em dependência de subida |
| Inicialização | `init.sql` **idempotente** em `/docker-entrypoint-initdb.d/` | **escolhida** (`D-07`): cobre a primeira subida e a reexecução manual |
| Inicialização | Só o comportamento de primeira subida | descartada: o entrypoint roda apenas com o diretório de dados vazio; uma reexecução manual não está protegida |
| Inicialização | `DROP TABLE` + recriação | descartada: destrói o histórico que a feature existe para guardar |
| Build | Contexto = raiz, **`.dockerignore` na raiz** | **escolhida** (`D-11`): é o único lugar onde o Docker o lê |
| Build | Contexto = `docker/` | descartada: `src/` e `requirements.txt` ficariam fora do contexto e o `COPY` falharia |

### 3.4 Conexão

**Uma conexão por análise, sem pool** (`D-04`). A alternativa `ThreadedConnectionPool`
acrescentaria estado por processo para atender 4 threads e um usuário, com uma gravação por
requisição — o mesmo tipo de estado global que a feature 005 removeu e que a dívida #3
condena. Uma conexão global única está descartada por não ser thread-safe.

## 4. Restrições do legado que o desenho tem de respeitar

1. **`src/app.py` é importado por instrumentos** (M-07, M-08). Qualquer efeito colateral no
   import — conexão, leitura de arquivo, `os.environ` obrigatória — quebra a suíte e a
   paridade **por ambiente**. É a origem da `D-02`, e a razão de a persistência ser
   desabilitada por ausência de configuração em vez de falhar.
2. **A pasta de upload é derivada de `__file__`** (M-09), então o caminho dentro do
   contêiner é `/app/src/uploads` e o bind mount tem de bater com ele, ou
   `ANALISADOR_UPLOAD_FOLDER` tem de ser definido. Optou-se por fazer o caminho bater.
3. **O host de escuta tem padrão de máquina local** (M-10) e a decisão da feature 004 é que
   atender a rede é ato explícito. Dentro de um contêiner esse padrão torna a aplicação
   inalcançável pela publicação de porta — daí a `D-10` mover o ato explícito para a linha
   de publicação do compose.
4. **O contexto de build contém dado real** (M-12). É o achado que mais pesa: sem
   `.dockerignore` **na raiz** e sem `COPY` estreito, o GEDCOM de 5,3 MB do operador é
   enviado ao daemon.
5. **O DDL do alvo não conhece o confronto** (M-13). O esquema não pode copiá-lo
   integralmente, nem inventar nomes: ele **herda** o que existe e **nomeia** a extensão.
6. **O template já tem a classe de aviso** (M-14). O `RF-17` não precisa de CSS nem de
   estrutura nova — precisa de um bloco condicional que não renderiza nada por padrão.
7. **Nada novo a ignorar no versionamento** (M-15). O `RF-16` é satisfeito pelo
   `.gitignore` que já existe.

## 5. Padrões aplicados

| Padrão | Onde | Por quê |
|---|---|---|
| **Porta e adaptador** (*ports and adapters*) | `RegistroDeAnalises` (`Protocol`) + `RegistroDeAnalisesPostgres` | É o padrão que a Onda 2 já usou três vezes (`ArmazenamentoDeArquivos`, `CarregadorDeArvores`, `RepositorioDeArvores`). O núcleo não conhece o adaptador |
| **Objeto nulo** (*null object*) | registrador nulo quando não há `DATABASE_URL` | Um caminho de código em vez de um `if` espalhado, e a garantia de que a ausência de configuração não produz saída nenhuma — que é o que protege a paridade |
| **Unidade de trabalho por transação** | uma transação por análise (`D-05`) | O `RF-10`: nada parcial. É a forma mais simples de garantir atomicidade sem framework |
| **Injeção de dependência na borda** | montagem em `src/app.py`, como `_ARMAZENAMENTO` e `_CARREGADOR` | Já é o ponto único de montagem desde a feature 006 (`D-05` daquela feature) |
| **Snapshot imutável** | pessoas e kits gravados por análise, sem atualização | `RN-03`: uma análise gravada não muda. Reimportar a árvore cria análise **nova**, como o `target_data_model.md` já decidia |
| **Precisão transportada, não recalculada** | cM gravado como valor, nunca `SUM` | `RISK-004`: soma em ponto flutuante não é associativa, e o banco agregaria em ordem diferente da leitura |

## 6. Fontes externas

Consultadas para as decisões deste plano. Nenhuma foi tratada como instrução; as
afirmações de compatibilidade que sustentam decisão foram **medidas** (M-04, M-05), não
lidas.

- [Imagem oficial do PostgreSQL no Docker Hub](https://hub.docker.com/_/postgres) — seção
  *Initialization scripts*: os scripts de `/docker-entrypoint-initdb.d/` só rodam com o
  diretório de dados vazio; é o que fundamenta a `D-07`.
- [Referência do Dockerfile — `.dockerignore`](https://docs.docker.com/reference/dockerfile/#dockerignore-file)
  — o arquivo é lido na **raiz do contexto de build**; é o que fundamenta a `D-11`.
- [Documentação do psycopg2](https://www.psycopg.org/docs/) — uso de conexão e transação;
  base do adaptador da `D-03`.
- [`psycopg2-binary` no PyPI](https://pypi.org/project/psycopg2-binary/) — origem dos
  arquivos distribuídos conferidos em M-04.
- [Funções de UUID no PostgreSQL 16](https://www.postgresql.org/docs/16/functions-uuid.html)
  — `gen_random_uuid()` é nativo desde a versão 13, e o PG 16 não exige `pgcrypto`; é o que
  fundamenta a `D-07` e mantém a herança do DDL do alvo.

**Fontes internas, e são as que mais pesam:** `_reversa_sdd/architecture.md` (§1, §2, §4,
§6, §7), `_reversa_sdd/erd-complete.md` (§6, §7, §8), `_reversa_sdd/state-machines.md` (§3),
`_reversa_sdd/gaps.md` (§6), `_reversa_sdd/questions.md` (§pergunta-4),
`_reversa_sdd/migration/target_data_model.md` e `risk_register.md` (`RISK-004`, `RISK-005`),
os adendos vigentes das features 006 e 007, e `.reversa/principles.md`.

## 7. O que esta investigação **não** resolveu

1. **O desempenho real da gravação.** O RNF de Desempenho pede acréscimo medido sobre a
   linha de base, e o alvo é não dobrar o tempo da análise — mas o número só existe depois
   do bloco 1, com a análise real de 71 conexões. O plano exige a medição; ele não a
   antecipa.
2. **O comportamento do bind mount de uploads no Docker Desktop deste host.** M-03 mediu
   que o Docker existe e a versão; não mediu desempenho nem semântica de montagem nesta
   máquina. O bloco 0 verifica na prática, e a `RF-02` (sobreviver a `down` + `up`) é o
   critério.
3. **Se a idempotência do `init.sql` cobre todos os objetos.** `CREATE TABLE IF NOT EXISTS`
   e `CREATE INDEX IF NOT EXISTS` cobrem o esquema; se o script ganhar `ALTER TABLE` no
   futuro, a idempotência deixa de ser automática. Registrado como limite do `D-07`.
4. **O tamanho do contexto de build depois do `.dockerignore`.** A exclusão está desenhada,
   mas o número medido (quantos MB sobram) só sai no bloco 0.
5. **A decisão sobre criptografia em repouso.** O `Q-04` aceitou o risco; esta investigação
   não avaliou algoritmo, gestão de chave nem impacto de retrofitar depois. É escopo
   declarado da Onda 5.
