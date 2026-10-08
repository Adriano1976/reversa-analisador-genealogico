# Regression watch: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Âncora: **legado** — `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`

## Watch principal

**Vazio, e corretamente vazio.** O watch principal deriva das regras marcadas como
*Modificadas* no `legacy-impact.md`; nesta rodada **nenhuma regra foi modificada**, porque a
execução parou no `T001` antes de escrever qualquer arquivo. Não há regra 🟢 nova a vigiar.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| *(nenhum)* | — | — | — | — |

## Observações

Sem peso de regressão. Registradas para que a próxima rodada — e a próxima re-extração — não
atribuam à feature o que é do ambiente.

| ID | Observação |
|---|---|
| `OBS-01` | **Bloco 0 bloqueado por permissão.** `.reversa/reversa-config.json` tem `allowLegacyEdits: true` com `allowedPaths` não vazio, e nenhum dos quatro caminhos exigidos pela feature (`docker/**`, `docker-compose.yml`, `init.sql`, `.dockerignore`) casa com a lista. O `T001` recusou a escrita e parou o Bloco 0, como o plano previa. A liberação é **ato do usuário**, e o conteúdo exato a acrescentar está na §4 de `evidence/T001-pre-requisito-de-permissao.md` |
| `OBS-02` | **`pip install` não funciona no `.venv` do host.** Medido nesta rodada: `Errno 13 Permission denied` no diretório de unpack do `pip`, criado por `tempfile.mkdtemp` com `0o700`. É o mesmo defeito documentado em `tests/conftest.py` §1, no adendo da 007 e em `investigation.md` `M-06`. Apontar `TEMP`/`TMP` para dentro do workspace não resolve. Dentro do contêiner o `pip` funciona, porque o `build` roda no sistema de arquivos Linux |
| `OBS-03` | **Consequência do `OBS-02` no plano:** o `T007` fica bloqueado na metade local, e o `T014` depende dela, porque roda no `.venv` do host. Instalar em shell elevado ou executar o `T014` dentro do contêiner são as duas saídas — **a escolha é do usuário**, e nenhum artefato do plano a previu |
| `OBS-04` | **`.probe/` continua preso** em `_reversa_forward/008-persistencia-postgres-docker/.probe/` — 20 entradas ilegíveis, criadas pela sonda de `pip` desta sessão. Não é removível sem shell elevado. Está documentado em `investigation.md` §2 e é o `T024` que o registra formalmente. Enquanto existir, o `.dockerignore` do `T002` tem de mantê-lo fora do contexto de build, e a lista de permissão da `D-18` já faz isso |
| `OBS-05` | **A medição do `T001` não alterou nenhum artefato de auditoria.** `audit/cross-check.md` segue com as duas passagens registradas, e os achados `B001`, `B002` e `B003` continuam abertos: esta rodada não chegou ao ponto de tocá-los |
| `OBS-06` | **SUPLANTA o `OBS-01`.** O usuário liberou os quatro caminhos em `allowedPaths` (`docker/**`, `docker-compose.yml`, `init.sql`, `.dockerignore`), e a reexecução do `T001` deu **ATENDIDO**. O bloqueio de permissão está **encerrado**, e `T002` a `T007` foram executadas. O `OBS-01` fica como registro do que era verdade antes da liberação — não o apague, ele é o histórico da parada que o `T001` existia para produzir |
| `OBS-07` | **SUPLANTA o `OBS-03`, que estava ERRADO.** O `T007` como escrito no `actions.md` manda apenas acrescentar o pin ao `requirements.txt` — ele **não tem passo de instalação**, e foi concluído sem obstáculo. Quem depende do `pip install` no `.venv` do host é o **`T014`** (o teste do adaptador roda ali, contra o banco do compose) e o pré-requisito §2 do `onboarding.md`. A atribuição equivocada foi corrigida também em `evidence/T001-pre-requisito-de-permissao.md` §5 |
| `OBS-08` | **Motor do Docker não está em execução.** `docker compose up -d --build` falha com `unable to get image 'genealogia-app': permission denied while trying to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. O **CLI** está instalado (`29.6.1`, Compose `v5.2.0`); o **motor** não. Bloqueia `T008`, `T009`, `T010` e o portão `T011`. É ato do operador: subir o Docker Desktop |
| `OBS-09` | **O que passou sem o motor, e vale como verificação.** `docker compose config --quiet` devolveu **exit 0**, com dois serviços (`db`, `app`), um volume nomeado (`dados_do_banco`) e as portas publicadas só em `127.0.0.1` — `5080` e `5432`. E o guarda do `RF-11` foi verificado **em execução**: sem `.env`, o `up` para com `required variable POSTGRES_USER is missing a value`, que é o `${VAR:?}` funcionando — prova de que não existe credencial com valor padrão em arquivo versionado |
| `OBS-10` | **O Bloco 0 não fechou.** Sete ações concluídas e o portão `T011` **não medido**. O Bloco 1 não pode começar antes dele: o `T012` declara dependência do `T011`, e a costura começaria sem instrumento. Nenhuma linha de `src/` ou `tests/` foi escrita nesta rodada |
| `OBS-11` | **SUPLANTA o `OBS-08`.** O Docker Desktop foi iniciado e o **motor subiu**. O `OBS-08` fica como registro do estado anterior — o CLI estava instalado, o motor não |
| `OBS-12` | **O CLI do Docker exige autorização explícita nesta sessão.** O modo confinado do harness bloqueia acesso a **named pipe**, e o Docker fala com o motor por `npipe:////./pipe/dockerDesktopLinuxEngine`: cada comando falha com `permission denied ... npipe` e a execução só prossegue com autorização do usuário. **Não é defeito do produto nem da feature**, e não é contornável por outro caminho — a saída foi empacotar todo o Bloco 0 dependente do motor num **único** comando autorizado, em vez de uma autorização por comando |
| `OBS-13` | **Hipótese do `M-04` aposentada por medição.** Existiam wheels `manylinux` para `cp314` de **todos os nove** pacotes, incluindo `pandas 3.0.6` e `networkx 3.7`: o `RUN pip install` do build **não compilou nada**. O `M-04` havia medido só **Windows**, e era essa a lacuna que o `T010` deixou aberta |
| `OBS-14` | **A suíte ficou mais lenta com os contêineres no ar** — **62,2 s** contra os **27,1 s** da linha de base —, com o **mesmo** conjunto (`261 passed`) e sem nenhuma alteração em `src/` ou `tests/`. **Não atribuído à feature.** O `T022` mede a suíte outra vez com e sem o stack; se a diferença se reproduzir com os contêineres parados, deixa de ser observação e vira achado |
| `OBS-15` | **O `pip install` continua inviável no `.venv` do host**, e isso vale para o `T014`: o `OBS-02` e o `OBS-07` seguem de pé. O `T014` precisa de `psycopg2-binary` instalado no host **ou** de rodar dentro do contêiner. Os contêineres estão **no ar** (`docker compose up -d`), com o banco publicado em `127.0.0.1:5432` — o que torna a segunda saída viável |
| `OBS-16` | **A superfície pública de `adaptadores.py` mudou, e o arame de tropeço da feature 007 disparou** — corretamente. `tests/test_porta_de_armazenamento.py` prendia `__all__` numa lista literal e mandava reabrir a `D-03`; a decisão foi reaberta (`D-01` da 008, registrada como `componente-novo` no `roadmap.md` §5) e a lista ganhou `RegistroDeAnalisesPostgres`. **Nenhum teste foi removido, desabilitado ou enfraquecido**, e a metade que prova que nenhum adaptador implementa o `RepositorioDeArvores` segue passando |
| `OBS-17` | **O `T014` nunca executou.** O arquivo `tests/test_registro_de_analises.py` está escrito e marcado com `skipif`, e é pulado porque o host não tem `psycopg2` (`OBS-15`) e a suíte roda sem `DATABASE_URL` (`D-17`). **Um teste pulado não é um teste que passou.** O `T022` tem de registrar os **dois** números da suíte lado a lado, e a prova dos mesmos caminhos com o banco no ar é do `T020` |
| `OBS-18` | **A coluna `detail` do `init.sql` foi removida depois de o banco já existir.** Ela era redundante com `comparison_detail`, e a correção veio na execução, não no plano. `CREATE TABLE IF NOT EXISTS` **não altera tabela existente**, então o volume precisa de `docker compose down -v` antes do `T020`. Não há dado a perder: nenhuma análise foi gravada ainda |
| `OBS-19` | **Armadilha de fixture, medida.** Uma fixture tem o corpo executado **depois** do corpo das suas dependências. Definir `DATABASE_URL` no corpo de uma fixture que depende de `cliente_de_upload` chega **tarde** — o `src/app.py` já foi carregado, e o teste mede o estado desabilitado achando que mede o de falha. A saída é recarregar o módulo após o `setenv`, e a armadilha está no docstring da fixture |
| `OBS-20` | **O `B003` da auditoria de 2026-10-08 está FECHADO** por `tests/test_projecao_da_analise.py` — treze testes que exercitam a projeção **sem banco**, porque ela é pura. Os achados `B001` (citação parcialmente corrigida no `roadmap.md`) e `B002` (o `T026` cita o §0 como linha de base que não existe lá) continuam **abertos** |
| `OBS-21` | **`ON DELETE RESTRICT` nas FKs de pessoa tornava `DELETE FROM dna_analysis` impossível**, e o defeito era do `init.sql`, não do produto. `analysis_person` cascateia de `dna_analysis`, e os filhos (`match_result`, `match_path_node`) ainda a referenciavam — `ForeignKeyViolation: fk_path_person`. Corrigido para `CASCADE`, com a razão no próprio `init.sql`. **A lição:** a garantia que interessa (não gravar referência a pessoa inexistente) o `FK` já dá no `INSERT`; o `RESTRICT` só agia na hora de apagar, e ali ele impedia expurgo e limpeza de teste |
| `OBS-22` | **O núcleo só reconhece a coluna de kit quando o VALOR casa `[A-Z]{1,3}\d{4,8}`** (`core/genetic_evidence.py:42-44`). Um CSV com `KIT-A`/`KIT-B` **não tem kit detectado**: as duas linhas viram o mesmo match `SEM-KIT` e o cM é **somado** — comportamento documentado do núcleo para segmentos de um mesmo match. ⚠️ **O sintoma engana:** "duas linhas de kits diferentes somadas" parece defeito de agregação da persistência, e é o núcleo fazendo o que sempre fez. Quem for montar fixture sintética para o caso de dois kits tem de usar valores no padrão, ou o teste mede outro caso sem avisar |

## Histórico de re-extrações

*(Preenchido pelo agente reverso quando `/reversa` rodar de novo.)*

| Data | Extração | Veredito | Observação |
|---|---|---|---|
| — | — | — | — |

## Arquivadas

*(Vazio. Itens saem do watch principal para cá quando deixam de ser verdadeiros por decisão.)*

| ID | Regra | Motivo do arquivamento | Data |
|---|---|---|---|
| — | — | — | — |
