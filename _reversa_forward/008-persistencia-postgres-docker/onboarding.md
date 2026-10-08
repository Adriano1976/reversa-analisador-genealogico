# Onboarding: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Requirements: `_reversa_forward/008-persistencia-postgres-docker/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Para quem é este documento

Para quem vai **testar esta feature pela primeira vez**, sem ter acompanhado o
desenvolvimento. Ele é executável de ponta a ponta: cada passo traz o comando e o resultado
esperado, e o resultado esperado é um **número** ou uma linha de banco, não uma impressão.

O que ele prova, em quatro frases: o resultado da análise de DNA passa a **existir depois
da requisição**, com as pessoas usadas, os kits e o veredito de quatro estados; a aplicação
e o banco **sobem juntos** com um comando e **sobrevivem** a `down` + `up`; a suíte e a
paridade continuam **idênticas** quando a persistência está desligada; e com o banco
**derrubado** a análise continua saindo na tela, com aviso e sem perder o resultado.

## 2. Pré-requisitos

| Item | Valor |
|---|---|
| Sistema | Windows com Docker Desktop — medido nesta máquina: `docker 29.6.1`, `docker compose v5.2.0` |
| Interpretador **oficial** | `.venv\Scripts\python.exe` (`3.14.6`) — decisão de 2026-10-05, registrada em `requirements.txt` |
| Pacotes | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| Raiz de trabalho | `D:\Projetos\reversa_analisador_gelealogico` |
| Estado de partida | **Nenhum.** Não há dado a migrar, não há schema anterior, não há passo manual de banco |
| Porta do host | `5080` — escolhida para não colidir com a `5000` padrão nem com a `5057` da verificação da feature 007 |

⚠️ **Não use o `python` global para aferir esta feature.** Ele carrega `ged4py 0.5.2`,
`networkx 3.6.1` e `pandas 3.0.3`, que são as versões do manifesto do oráculo, e não as do
pin do projeto. O instrumento oficial é o `.venv/`.

⚠️ **`pip download` e `pip install --dry-run` não funcionam nesta máquina** — o pip cria o
diretório de trabalho por `tempfile.mkdtemp`, e `0o700` aqui não é listável, gravável nem
removível (`tests/conftest.py` §1). Se você precisar conferir disponibilidade de pacote,
consulte a API do PyPI em vez de usar o pip. Registrado porque o defeito já foi atribuído à
máquina duas vezes.

## 3. Números esperados

| Medição | Antes desta feature | **Depois, esperado** |
|---|---|---|
| Suíte completa **sem** `DATABASE_URL` | `261 passed` | **`261 passed` + os testes novos**, 0 falhas e 0 erros |
| `tests/test_upload_seguranca.py` | `36 passed` | **`36 passed`** — intocado |
| Paridade diferencial | `100 %`, exit 0 | **`100 %`, exit 0** |
| Tabelas no banco | *(não existia banco)* | **6** — e 6 depois de rodar o `init.sql` **duas vezes** |
| Serviços do compose | *(não existia)* | **2** — `db` e `app` |

⚠️ **O total de aprovados vai crescer, e isso não é regressão.** A conta é
`261 + testes novos`. **A regra de comparação é por conjunto, não por total:** nenhum teste
que passava pode passar a falhar, e nenhum teste pode ser removido, desabilitado ou
renomeado. `261` fica como leitura **histórica**, medida em 2026-10-08 antes do plano.

## 4. Passo 1 — a linha de base, e o passo que prova que o núcleo não foi tocado

```powershell
cd D:\Projetos\reversa_analisador_gelealogico

# 1a. os 261 continuam passando SEM banco nenhum configurado
.venv\Scripts\python.exe -m pytest -q

# 1b. a paridade continua em 100 %, tambem sem banco
.venv\Scripts\python.exe _reversa_sdd\parity\harness.py

# 1c. e a confianca de que a variavel nao esta definida nesta janela
Test-Path env:DATABASE_URL        # esperado: False
```

Esperado: `0 errors` e nenhuma falha no 1a; `PARIDADE 100%` com **exit 0** no 1b.

**O que este passo prova.** É o `RF-13`, e é o passo mais importante do documento: se a
suíte ou a paridade mudarem **sem** o banco, a persistência deixou de ser camada de saída e
entrou no caminho crítico. `src/app.py` é importado pela suíte
(`tests/conftest.py:166-171`) e pelo harness (`_reversa_sdd/parity/harness.py:356`), então
qualquer efeito colateral no import aparece **aqui**, e não em produção.

**O que este passo NÃO deve mostrar.** Nenhum `ERROR ... at setup`: isso é erro de
**ambiente**, não de produto, e a causa medida está em `tests/conftest.py` §1.

## 5. Passo 2 — a credencial, e por que ela não está no repositório

Crie um arquivo `.env` **na raiz** (ele já está no `.gitignore`, linha 6 — não é versionado):

```powershell
@"
POSTGRES_USER=genealogia
POSTGRES_PASSWORD=escolha-uma-senha
POSTGRES_DB=genealogia
DATABASE_URL=postgresql://genealogia:escolha-uma-senha@db:5432/genealogia
"@ | Set-Content -Path .env -Encoding ascii
```

⚠️ **O `docker-compose.yml` não tem senha padrão.** Ele exige as variáveis. É de propósito
(`RF-11`): credencial com valor padrão dentro de arquivo versionado é credencial
versionada, ainda que disfarçada.

```powershell
git check-ignore -v .env      # esperado: .gitignore:6:.env
```

**O que este passo prova.** A string de conexão existe **só** no ambiente. Ela não está no
compose, no código, no template, no log nem em camada de imagem — e o passo 9 confere isso.

## 6. Passo 3 — o stack sobe com um comando, e os dois estados persistem

```powershell
docker compose up -d --build
docker compose ps
```

Esperado: **dois** serviços. O `db` aparece `healthy` (o `healthcheck` existe para você e
para o `compose ps`); o `app` aparece `Up` — **e o `app` não espera o `db` ficar saudável**,
por decisão (`D-09`): se esperasse, o banco fora do ar esconderia até a análise, que é o
que o `RF-17` proíbe.

```powershell
curl.exe -s -o NUL -w "%{http_code}`n" http://127.0.0.1:5080/
```

Esperado: **`200`**.

Agora o teste da persistência dos dois estados (`RF-02`):

```powershell
# grave o estado atual
docker compose down
docker compose up -d
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM dna_analysis;"
Test-Path src\uploads        # esperado: True
```

Esperado: a contagem é a **mesma** de antes do `down`, e a pasta de uploads continua no
lugar. O volume do banco é **nomeado** e o de uploads é **bind mount** (`D-08`) — e é por
isso que os dois regimes são diferentes.

## 7. Passo 4 — o `init.sql` roda duas vezes sem quebrar (`RF-12`)

```powershell
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
docker compose exec -T db psql -U genealogia -d genealogia -f /docker-entrypoint-initdb.d/init.sql
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
```

Esperado: **`6`** nas duas contagens, e **nenhum** erro na execução do meio.

**O que este passo prova.** O entrypoint do PostgreSQL só roda os scripts com o diretório
de dados **vazio** — isso cobre a primeira subida, mas **não** uma reexecução manual, que é
o que a `RF-12` quer proteger. Por isso o script usa `IF NOT EXISTS` em tudo e **não** tem
`DROP`: um `DROP` no topo apagaria o histórico, que é o propósito da feature.

## 8. Passo 5 — uma análise grava, e a consulta do `RF-14` devolve o veredito

Prepare o dado **sintético** (Princípio I: nunca use dado real nesta verificação):

```powershell
$pasta = "$PWD\_reversa_forward\008-persistencia-postgres-docker\evidence\_tmp_e2e"
New-Item -ItemType Directory -Force -Path $pasta | Out-Null
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'tests'); from fixtures.sample_gedcom import SAMPLE_GED; open(r'$pasta\arvore.ged', 'w', encoding='utf-8').write(SAMPLE_GED)"
Set-Content -Path "$pasta\matches.csv" -Value "Name,cM,Kit`nCarlos Silva,150,KIT-A" -Encoding ascii
```

Os três fluxos:

```powershell
# 5a. upload do GEDCOM
curl.exe -s -X POST http://127.0.0.1:5080/ -F "action=upload_gedcom" -F "gedcom=@$pasta\arvore.ged" -o "$pasta\1_upload.html"
Select-String -Path "$pasta\1_upload.html" -Pattern 'gedcom_filename" value="([^"]+)"'

# Copie a chave que o comando acima imprime e use nas duas chamadas seguintes:
$chave = "<cole aqui a chave>"

# 5b. analise de DNA — e esta chamada que grava
curl.exe -s -X POST http://127.0.0.1:5080/ -F "action=dna_analysis" -F "gedcom_filename=$chave" -F "root_name=Carlos Silva" -F "matches_csv=@$pasta\matches.csv" -o "$pasta\2_dna.html"
Select-String -Path "$pasta\2_dna.html" -Pattern 'Compatível|Possível|Conflitante|Inconclusivo'
```

Esperado no `2_dna.html`: o resultado com o veredito exibido, **e nenhum aviso de
persistência** — porque o banco está no ar.

A consulta do `RF-14` — a última análise de um par `(raiz, match)`, com o veredito e os
kits:

```sql
-- salve como _reversa_forward\008-persistencia-postgres-docker\evidence\_consulta.sql
SELECT a.created_at, a.root_name_input, a.accepted_count, a.skipped_count,
       m.result_ordinal, m.csv_name, m.matched_name, m.total_cm,
       m.comparison_status, m.comparison_label, m.comparison_method,
       m.expected_low, m.expected_high, m.comparison_detail
  FROM dna_analysis a
  JOIN match_result m USING (analysis_id)
 WHERE a.root_name_input = 'Carlos Silva'
 ORDER BY a.created_at DESC, m.result_ordinal
 LIMIT 20;

SELECT m.result_ordinal, m.csv_name, k.kit, k.source, k.total_cm,
       k.segment_count, k.largest_segment_cm, k.status, k.status_note
  FROM match_result m
  JOIN match_kit k USING (match_id)
 ORDER BY m.result_ordinal, k.ordinal;
```

```powershell
# salve as duas consultas acima em $pasta\_consulta.sql e mande pelo stdin do container
Get-Content "$pasta\_consulta.sql" -Raw | docker compose exec -T db psql -U genealogia -d genealogia
```

Esperado: **uma linha por conexão**, com `comparison_status` preenchido com um dos quatro
valores, `comparison_method` e a faixa esperada — e uma linha por kit na segunda consulta.

**O que este passo prova.** As três coisas pedidas estão gravadas e são **legíveis**: os
dados das pessoas (`analysis_person`), os metadados dos kits (`match_kit`) e o status do
confronto (`match_result.comparison_status`), com o porquê. E a ordem relida é a ordem
exibida (`result_ordinal`), não uma reordenação por cM.

## 9. Passo 6 — o banco cai, e a análise continua (`RF-17`)

```powershell
docker compose stop db

# repita os tres fluxos do passo 5
curl.exe -s -X POST http://127.0.0.1:5080/ -F "action=upload_gedcom" -F "gedcom=@$pasta\arvore.ged" -o "$pasta\4_upload_sem_db.html"
# copie a chave nova e rode a analise
curl.exe -s -X POST http://127.0.0.1:5080/ -F "action=dna_analysis" -F "gedcom_filename=<chave>" -F "root_name=Carlos Silva" -F "matches_csv=@$pasta\matches.csv" -o "$pasta\5_dna_sem_db.html"

docker compose start db
```

Esperado no `5_dna_sem_db.html`: **os mesmos resultados e o mesmo veredito** do passo 5,
**mais** o aviso não bloqueante de que o histórico não foi registrado. Nenhuma tela de erro,
nenhum `500`, nenhuma exceção crua.

```powershell
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM dna_analysis;"
```

Esperado: a contagem **não** mudou — a análise do passo 6 não deixou nada, nem pela metade
(`RF-10`).

**O que este passo prova.** É o `Q-03` medido. Se a aplicação tivesse recusado a
requisição, ou se tivesse gravado metade, este passo falha. E é ele que dá sentido forte ao
`RF-13`: a análise não depende do banco **nem para decidir, nem para ser exibida**.

**O que este passo NÃO prova.** Nada de isolamento e nada de criptografia. Ver o §11.

## 10. Passo 7 — o contexto de build não leva dado real (Princípio I)

`src/uploads/` contém o **GEDCOM real** do operador — `Arvore_Unificada_Oficial_V1_2.ged`,
de **5,3 MB**, entre 33 entradas. Ele **não** pode entrar no contexto de build nem na
imagem.

```powershell
# 10a. o contexto deve ficar pequeno; se aparecer dezenas de MB, o .dockerignore nao esta sendo lido
docker build -f docker/Dockerfile -t genealogia-app:probe . 2>&1 | Select-String -Pattern "transferring context|DONE|ERROR"

# 10b. o arquivo real NAO pode existir na imagem
docker run --rm genealogia-app:probe sh -c "ls /app/src/uploads 2>/dev/null && echo PRESENTE || echo 'ausente na imagem (esperado)'"
```

Esperado: no 10a, contexto na casa de **poucos MB**; no 10b, **`ausente na imagem`**.

⚠️ **O `.dockerignore` precisa estar na raiz do projeto.** Em `docker/` o Docker **não** o
lê, porque ele só é considerado no topo do contexto de build — e o contexto tem de ser a
raiz, que é de onde vêm `src/` e `requirements.txt`. Esta é a razão de um dos desvios
declarados do plano (`D-11`).

```powershell
docker rmi genealogia-app:probe
```

## 11. Passo 8 — o que esta feature **não** fez

Leia esta seção antes de escrever qualquer conclusão. Ela existe para impedir a leitura
errada mais provável desta entrega.

| Afirmação | Veredito |
|---|---|
| "O `owner_id` isola os dados de cada usuário" | ❌ **FALSO.** Não há sessão, login nem papel no sistema (`_reversa_sdd/permissions.md`, `P-01` a `P-05`). A coluna existe e **nenhuma consulta filtra por ela**; não há sequer índice que comece por ela, para não insinuar escopo (`RN-10`) |
| "A dívida #4 (ausência de identidade e isolamento) foi fechada" | ❌ **FALSO.** Segue aberta. A `RN-10` proíbe esta afirmação em qualquer artefato da feature |
| "A dívida #3 (corrida entre requisições concorrentes) foi fechada" | ❌ **FALSO.** A guarda continua de **processo**, não de thread; o banco não tem relação com essa corrida |
| "A dívida #8 foi integralmente fechada" | ⚠️ **Parcial.** Fecha o **histórico de resultados**. A análise continua sendo sob demanda, sem cache entre requisições — e isso passa a ser **decisão declarada** (`RN-12`), não ausência de decisão |
| "A árvore foi para o banco" | ❌ **FALSO.** A árvore continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`. O banco guarda o **resultado**, e apenas as pessoas que a análise usou (`RN-04`) |
| "O `RepositorioDeArvores` ganhou implementação" | ❌ **FALSO.** Continua declarado, sem implementação e **sem consumidor**, como a feature 007 o deixou. Esta feature criou uma porta **diferente** |
| "A tela de histórico existe" | ❌ **FALSO.** O `RF-14` é atendido por consulta SQL documentada (§8). A tela é escopo da onda de apresentação, declarada fora de escopo no §12 do `requirements.md` |
| "O banco é a fonte do resultado exibido" | ❌ **FALSO.** A tela calcula do zero a cada requisição, a partir do arquivo de upload (`RN-12`). O banco é histórico, não cache |
| "O dado genético está criptografado em repouso" | ❌ **FALSO.** Está **em claro**, por aceite de risco de 2026-10-08 (`Q-04`), com a mesma condição de reabertura do aceite do `BUG-20260929-BJJH`. Criptografia, retenção e expurgo são da Onda 5 |
| "A ambiguidade da raiz foi gravada como campo" | ⚠️ **Não como campo estruturado.** O núcleo entrega esse sinal apenas como **texto**; ele está preservado em `match_result.observations` (`D-15`) |
| "Os nós do caminho têm sexo e datas no banco" | ⚠️ **Não.** O resultado do núcleo carrega apenas `id` e `nome` para os nós intermediários; a ficha completa existe para a raiz e para o match, e `analysis_person.completa` distingue os dois casos (`D-15`) |

## 12. Se algo divergir

| Sintoma | O que significa | O que fazer |
|---|---|---|
| `ERROR ... at setup` com `PermissionError [WinError 5]` na suíte | O fixture `tmp_path` de `tests/conftest.py` saiu de vigor — **não** é esta feature | Restaure a substituição; a causa está em `tests/conftest.py` §1 |
| A suíte passa a falhar **sem** `DATABASE_URL` | Algo passou a tocar o banco no import, ou a exigir configuração | **Pare.** É a `D-02` violada: o `RF-13` proíbe. Procure conexão fora do caminho de gravação |
| `PARIDADE` abaixo de 100 % | Ou uma constante de domínio mudou, ou o aviso de persistência está sendo renderizado com a persistência desabilitada | Reverta. Com `DATABASE_URL` ausente, a página tem de ser **byte a byte** a de antes |
| A página de DNA ganha um aviso com o banco **no ar** e a análise gravando | O aviso está sendo emitido no caminho de sucesso | Reverta: o aviso é do terceiro estado, e só dele |
| `docker compose up` falha reclamando de variável não definida | O `.env` não existe ou não está na raiz | Volte ao passo 2 |
| A aplicação sobe mas `curl` na `5080` não responde | `ANALISADOR_HOST` ficou `127.0.0.1` **dentro** do contêiner, e a publicação de porta não alcança o loopback do contêiner | Confira a variável no serviço `app`: tem de ser `0.0.0.0` no contêiner, com a publicação em `127.0.0.1` no host (`D-10`) |
| O contexto de build com dezenas de MB, ou o GEDCOM real presente na imagem | O `.dockerignore` não está na raiz, ou o `COPY` não é estreito | **Pare e corrija antes de qualquer imagem ir para um registro.** Ver o passo 7 |
| `init.sql` falha na segunda execução | A idempotência regrediu (`D-07`) | Confira se alguém trocou um `IF NOT EXISTS` por `CREATE` puro, ou introduziu `DROP` |
| Gravar e reler um cM de fronteira muda o valor (46, 200, 553, 1317, 2200, 3300) | Alguém passou a agregar no banco em vez de transportar o valor do núcleo | Reverta. É o `RISK-004`, e o `RN-05` exige transporte |
| A contagem de `dna_analysis` muda depois do passo 6 (banco parado) | Foi gravada análise parcial, ou o aviso não bloqueou a gravação | Reverta: o `RF-10` exige transação única, e o `RF-17` exige concluir **sem** gravar |
| O total de aprovados caiu em relação aos `261` | Regressão real — a regra é por conjunto | Investigue antes de prosseguir |

## 13. Roteiro mínimo, em uma tela

```powershell
cd D:\Projetos\reversa_analisador_gelealogico

# 1. sem banco nenhum: a suíte e a paridade continuam iguais
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe _reversa_sdd\parity\harness.py

# 2. sobe o stack e confere que a aplicacao responde
docker compose up -d --build
curl.exe -s -o NUL -w "%{http_code}`n" http://127.0.0.1:5080/

# 3. o init.sql e idempotente — 6 e 6
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
docker compose exec -T db psql -U genealogia -d genealogia -f /docker-entrypoint-initdb.d/init.sql
docker compose exec -T db psql -U genealogia -d genealogia -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# 4. uma analise grava (passo 5) e a consulta devolve o veredito (passo 5)

# 5. o banco cai e a analise continua, com aviso e sem gravar (passo 6)

# 6. o contexto de build nao leva dado real (passo 7)

# 7. nada de residuo
git status --short
```

Se os sete passos derem o resultado esperado, a feature está aceita.
