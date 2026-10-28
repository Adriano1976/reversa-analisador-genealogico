# Auditoria — Analisador de Conexões Genealógicas

**Data:** 2026-10-28
**Escopo:** leitura de código, execução da suíte de testes e verificação do estado do repositório.
**O que NÃO foi feito:** nenhum arquivo do projeto foi alterado, nenhuma migração foi aplicada, nada foi instalado. O único arquivo criado é este relatório.
**Base auditada:** `HEAD` = `5aa080f` (árvore limpa, exceto `tests/test_tela_de_entrada.py`, não rastreado e pré-existente).

## O que este sistema é (e o que ele não é)

É um app Flask monousuário-por-conta que recebe GEDCOM + CSV de DNA, cruza os dois e grava o histórico em PostgreSQL. Não há e-commerce, não há cobrança, não há gateway de pagamento e não há webhook. Então os fluxos que o roteiro pede por padrão — cadastro, checkout, assinatura, webhook — **não existem** neste projeto; onde isso acontece eu escrevo "não aplicável" em vez de inventar equivalente. Os fluxos críticos reais são: entrada (OAuth Google), upload de GEDCOM, análise de DNA, busca de caminho, aposentadoria de arquivo e persistência do histórico — e são esses que a Etapa 1 cobre.

---

## Os 5 achados de maior risco, em ordem

| # | Achado | Risco | Onde | Por que está nesta posição |
|---|---|---|---|---|
| **P1** | A autenticação é **condicional ao entrypoint**: `create_app()` monta a app sem guarda quando as 5 variáveis faltam, e `_dono()` cai no literal `"unico"`, que aponta para a **raiz** da pasta de upload — onde estão todos os arquivos herdados. Só `python src/app.py` recusa subir. | **Alto** | `src/app.py:79`, `src/app.py:82-88`, `src/app.py:867-870`, `src/app.py:893-898` | É o único achado que expõe dado **hoje**: qualquer runner que não seja `python src/app.py` (`flask run`, `waitress-serve`, `gunicorn`) sobe a aplicação aberta, sem login, com acesso a todas as árvores e relatórios. |
| **P2** | O isolamento por dono **não existe no banco**: `owner_id` é gravado e nunca lido. Não há RLS, não há policy, não há índice de escopo, e nenhuma consulta filtra por dono. | **Alto (latente)** | `init.sql:26`, `init.sql:182-184`, `src/ports/adaptadores.py:583` | Hoje não vaza só porque o histórico é *write-only* (não há tela que leia `dna_analysis`). No dia em que a primeira consulta de histórico nascer, ela devolve o acervo de todos os donos — e o banco não tem nada que a impeça. |
| **P3** | O armazenamento em disco faz **ler → decidir → gravar** sem nenhuma operação atômica: `exists()` antes de `open("wb")` no caminho final, snapshot da pasta antes de gravar, e `os.replace` no fim de um `_destino_livre` que decide por `exists()`. | **Alto** | `src/ports/adaptadores.py:119-121`, `src/ports/adaptadores.py:262-268`, `src/ports/adaptadores.py:280-285`, `src/application/reenvio.py:62-77` | É o achado mais provável de acontecer na operação real: 4 threads no waitress e o operador clicando duas vezes. Quebra a `RN-17` ("a lista fica com UMA versão") e devolve `500` em vez da mensagem de contrato. |
| **P4** | **Não existe banco de teste.** O teste de banco roda contra o mesmo banco de produção e apaga linhas por `tree_ref`; e não há runner de migração (mudança de esquema exige `down -v`, que apaga o histórico). | **Alto** | `tests/test_registro_de_analises.py:45-51`, `tests/test_registro_de_analises.py:107-117`, `init.sql:186-189` | Habilitar os testes de banco (definir `DATABASE_URL` + instalar `psycopg2`) aponta a suíte para o acervo real. O `_limpar` filtra por `tree_ref = 'chave__arvore.ged'` — que é um nome plausível de arquivo real. |
| **P5** | Suíte **vermelha** em `HEAD` (5 falhas de caracterização) e CI que **não roda teste**; o POST de análise não tem idempotência, então duplo clique grava duas análises e paga dois parses. | **Médio** | `tests/test_characterization_mermaid.py:174`, `tests/test_tres_fases_da_tela.py:258`, `.github/workflows/tipos.yml:18-45`, `src/app.py:552-561` | Sem suíte verde não há como provar que P1–P4 não regrediram. A falha de idempotência é o único efeito colateral barato de corrigir em conjunto. |

Os cinco prompts de correção correspondentes estão nomeados **P1…P5** e a recomendação de ordem está no fim deste documento.

---

## Como verifiquei

| Verificação | Comando | Resultado |
|---|---|---|
| Suíte completa | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | **5 failed, 1752 passed, 9 skipped** em 601 s |
| Skips | `pytest tests/test_registro_de_analises.py -q -rs` e `pytest tests/test_manutencao_de_uploads.py -q -rs` | 8 = banco (`DATABASE_URL` + `psycopg2` ausentes); 1 = link simbólico no Windows |
| Segredos no histórico | `git log --all -S "<valor>"` para senha do banco, client secret, chave de sessão e client id | **nenhum** dos quatro valores aparece no histórico do git |
| RLS / policies | busca por `ROW LEVEL SECURITY`, `CREATE POLICY`, `auth.uid`, `USING (true)` em todo o repositório | **zero ocorrências** |
| Webhook / gateway | busca por `webhook`, `stripe`, `pagseguro`, `mercadopago`, `asaas`, `idempotency` em `src`, `tests`, `docs`, `docker` | **zero ocorrências** |
| Locks / atomicidade | busca por `lock`, `FOR UPDATE`, `ON CONFLICT`, `flock`, `advisory` em `src` | **1 ocorrência**: `threading.Lock` no cache (`src/ports/adaptadores.py:369`) |
| Segredos no front | busca por `secret`, `api_key`, `client_id`, `Bearer` em `src/templates/*.html`; busca por `NEXT_PUBLIC`, `VITE_`, `EXPO_PUBLIC` | **zero ocorrências** |

**Nota de ambiente (não é achado do projeto):** o sandbox do meu harness bloqueia escrita no temporário do sistema, e o pytest não inicia sem ele. Rodei apontando `TEMP`/`TMP` para um diretório de rascunho e removi o diretório no mesmo comando (`git status` depois da execução segue limpo, exceto o arquivo não rastreado que já existia). A suíte em si isola uploads e logs em temporário por `tests/conftest.py:109-119`, então **nenhum teste escreveu no projeto**.

---

## Etapa 1 — Testes de integração

### 1.1 Ferramenta, banco de teste e comando

| Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|
| Ferramenta de teste configurada: **pytest 9.1.1** no `.venv`, com `pytest.ini` apontando `testpaths = tests`. Existe e funciona. | — | `pytest.ini:1-2` | Nada a corrigir. |
| **Não existe banco de teste separado.** Um único serviço `db` no compose, uma única `DATABASE_URL`, e os testes de banco usam essa mesma URL. | **Alto** | `docker-compose.yml:20-46`, `docker-compose.yml:66` | Criar serviço `db_teste` (ou banco `genealogia_teste` no mesmo serviço) e uma `DATABASE_URL_DE_TESTE` lida só pela suíte; recusar rodar o arquivo de teste se a URL não contiver `teste`. |
| Quando habilitado, o teste de banco **apaga linhas** do banco apontado pela `DATABASE_URL`, filtrando por `tree_ref = 'chave__arvore.ged'` — um nome plausível de arquivo real. | **Alto** | `tests/test_registro_de_analises.py:107-117` | Além do banco separado, trocar o filtro por um `owner_id` exclusivo de teste (`owner_id = 'suite-de-teste'`) e apagar só por ele. |
| `pytest` **não está declarado** em `requirements.txt`, e não existe `requirements-dev.txt`. Uma instalação limpa não reproduz a suíte. | **Médio** | `requirements.txt:20-52` | Criar `requirements-dev.txt` com `pytest`, `pytest-cov` e `pyrefly`, e documentar o comando no README/onboarding. |
| O CI roda **somente checagem de tipos** (`pyrefly check src`); nenhum workflow executa o pytest. | **Médio** | `.github/workflows/tipos.yml:18-45` | Acrescentar job `pytest` com serviço Postgres de teste, e torná-lo obrigatório. |
| **Comando para rodar tudo:** `.\.venv\Scripts\python.exe -m pytest` — resultado medido: **1752 passam, 5 falham, 9 são pulados**, em 601 s. | **Médio** | — | Ver as duas linhas seguintes: as 5 falhas e os 9 pulos. |
| **5 falhas, todas de teste de caracterização desatualizado** (contrato congelado que a UI já mudou): `width:190px` no Mermaid virou `230px`, e o literal `1. Lista de Matches (CSV)` sumiu da tela. Reproduzidas isoladamente em `HEAD` limpo. | **Médio** | `tests/test_characterization_mermaid.py:174` (e 3 parametrizações), `tests/test_tres_fases_da_tela.py:258` | Atualizar os congelados **com registro da decisão** (não só reescrever o número): ou o layout voltou a 190 px sem intenção, ou o teste é que estava velho. Enquanto isso, a suíte não serve de sinal. |
| **9 pulos**, todos justificados por ambiente: 8 de banco (`DATABASE_URL` + `psycopg2` ausentes no `.venv` do host) e 1 de link simbólico no Windows. **Um teste pulado não é um teste que passou** — a persistência em Postgres não é verificada nesta máquina. | **Alto** | `tests/test_registro_de_analises.py:45-51`, `tests/test_manutencao_de_uploads.py:252` | Instalar `psycopg2` no `.venv` (ou rodar a suíte dentro do container, como o `tests/verificacao_no_conteiner.py` já prevê) com banco de teste. |

### 1.2 Fluxos críticos × cobertura real

Legenda: **rota** = teste chama `POST /` ou a rota real via `test_client` (com dublê só na borda externa); **unitário** = testa a função pura, sem HTTP; **nada** = sem teste.

| Fluxo | Existe no produto? | Nível do teste | Onde | Veredito |
|---|---|---|---|---|
| **Cadastro** | **Não** (a conta nasce no Google no primeiro acesso) | — | `src/templates/login.html:15-17` | Não aplicável. |
| **Login / entrada** | Sim (OAuth 2.0 authorization code) | **Rota**, com provedor falso em memória | `tests/test_autenticacao.py:99-141`, `tests/test_sessao_e_guarda.py`, `tests/test_tela_de_entrada.py`, `tests/fixtures/autenticacao.py` | Coberto na rota: `state` divergente, `state` de uso único, cancelamento, falha na troca, guarda de sessão, logout. **Não cobre** o provedor real (nenhum teste fala com o Google — correto) nem a troca de código de verdade. |
| **Isolamento entre donos** | Sim (feature 051) | **Rota** | `tests/test_isolamento_por_dono.py` (5 testes) | Bom: A não vê B, 404 em vez de 403, aposentar de outro dono não move nada, mesmo conteúdo em dois donos = dois arquivos. |
| **Upload de GEDCOM** | Sim | **Rota** + unitário | `tests/test_upload.py`, `tests/test_upload_seguranca.py` (5 casos de escape), `tests/test_formatos_do_envio.py`, `tests/test_reenvio_do_arquivo.py` | Coberto, inclusive os 5 casos de path traversal e o teto de 16 MB. |
| **Análise de DNA** | Sim | **Rota** | `tests/test_dna_analysis.py:373-431`, `tests/test_confrontacao_gedcom_dna.py` (901 linhas), `tests/test_promocao_de_descarte.py:201` | Coberto na rota. |
| **Busca de caminho** | Sim | **Rota** + unitário | `tests/test_path_search.py:161-215` (rota) e o resto unitário | Coberto. |
| **Aposentar arquivo** (destrutivo) | Sim | **Rota** | `tests/test_aposentar_arquivo.py:260-312`, `tests/test_registro_de_auditoria.py:68-81` | Coberto, incluindo a auditoria das duas tentativas. |
| **Persistência do histórico (Postgres)** | Sim | **Nada na prática** — 8 testes escritos, **todos pulados** nesta máquina | `tests/test_registro_de_analises.py` | **Não verificado em host.** Só é exercitado dentro do container (`tests/verificacao_no_conteiner.py`) e em verificação manual (T020/T021). |
| **Checkout / assinatura / webhook de pagamento** | **Não existem** | — | — | Não aplicável. Não há gateway, não há cobrança, não há webhook (busca com zero ocorrências). |
| **Recuperação de senha** | **Não existe** (não há senha) | — | — | Não aplicável. |

---

## Etapa 2 — Confiança no cliente

### 2.1 Regras de negócio que o cliente decide

| Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|
| O campo oculto **`promover`** chega do formulário e **substitui a decisão de matching**: `candidate_pids = [promovido[0]]` com `reason = None`, sem revalidar que aquele `xref` pertence ao conjunto de candidatos que o servidor havia calculado. | **Baixo** | `src/app.py:492-498`, `src/core/passo_por_kit.py:286-290`, `src/templates/index.html:1915-1918` | Já é intenção de produto (o operador escolhe o nó). O que falta é **servidor revalidar**: aceitar a promoção só se o `xref` estiver entre os candidatos devolvidos por `avaliar_candidatos` para aquele kit; hoje um `xref` arbitrário da árvore é aceito e o cartão nasce com `reason = None`. |
| O campo oculto **`dados`** leva o JSON dos descartes de volta ao servidor, que o converte em CSV sem confrontar com o que ele mesmo produziu. | **Baixo** | `src/web/rotas_assets.py:57-74` | Aceitável (o dado é do próprio dono e `csv_de_descartes` já desarma fórmula de planilha). Se um dia esse CSV virar documento com valor probatório, gerar no servidor a partir do resultado da análise, não do que o navegador devolve. |
| **Não existem** regras de preço, desconto, papel de admin, permissão ou limite de plano em lugar nenhum — nem no front, nem no back. O único limite é o teto de 16 MB, e ele está **no servidor** (Flask `MAX_CONTENT_LENGTH` **e** `waitress.max_request_body_size`). | — | `src/app.py:106-127`, `src/app.py:821`, `src/app.py:987-988` | Nada a corrigir. Registro o contraexemplo: o teto é o caso em que a regra está só no servidor, como deve ser. |
| O `gedcom_filename` e o `matches_csv_filename` vêm do formulário, mas são **validados no servidor** por forma (nome simples, prefixo de 16 hex) e escopados pela pasta do dono antes de qualquer `exists()`. | — | `src/app.py:328-346`, `src/utils/validate.py:170-229`, `src/ports/adaptadores.py:124-146` | Nada a corrigir. É o outro contraexemplo correto: o cliente manda a referência, o servidor decide o alcance. |

### 2.2 Chaves e tokens (público por design × secreto)

| Item | Classificação | Onde | Situação |
|---|---|---|---|
| `POSTGRES_PASSWORD`, `DATABASE_URL` | **Secreta** | `.env:13-16` | No disco, em claro; **não versionada** (`git ls-files` não a lista; `.gitignore:6`) e **ausente de todo o histórico** (`git log --all -S` sem ocorrência do valor). O compose usa `${VAR:?}` e **para** se faltar — corretamente sem valor padrão (`docker-compose.yml:23-25`). |
| `GOOGLE_CLIENT_SECRET` | **Secreta** | `.env.local:11` | Mesma situação: fora do git, ausente do histórico. Usada **só no servidor** (`src/web/autenticacao.py:140-155`); nunca chega ao navegador. |
| `ANALISADOR_SECRET_KEY` (chave de assinatura do cookie de sessão) | **Secreta** | `.env.local:12` e `.env.local:14` | Fora do git, ausente do histórico. **Defeito de higiene:** a variável aparece **duas vezes** no mesmo arquivo — uma vazia (linha 12) e uma preenchida (linha 14). Quem lê só a primeira ocorrência (ou um parser "primeiro vence") recebe vazio e a app recusa subir. |
| `GOOGLE_CLIENT_ID` | **Pública por design** | `.env.local:10` | Correta: o `client_id` é público no protocolo OAuth. |
| Tokens de acesso do OAuth | **Secretos, e nunca persistidos** | `src/web/autenticacao.py:140-174` | O token é trocado e consumido no servidor, e não entra em log (o módulo declara e cumpre: motivo curto, nunca token/código/segredo). |
| Variáveis de front (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_`) | — | — | **Não existem**: é Jinja server-side. Nenhum segredo em `src/templates/*.html` (busca por `secret`, `api_key`, `client_id`, `Bearer`: zero). |
| `.dockerignore` | — | `.dockerignore:12-16` | Lista de **permissão** (`*` + `!src/**`): `.env` não entra na imagem. Correto. |
| Porta do Postgres publicada | **Médio** | `docker-compose.yml:33-37` | Publicada em `127.0.0.1:5432` (só loopback, correto), mas com a senha em claro no `.env` e sem TLS. Em máquina compartilhada, qualquer processo local lê o `.env`. Aceitável para uso local; registrar como dívida para qualquer deploy multiusuário. |

### 2.3 Banco exposto por API, RLS e policies

**Não há Supabase, não há PostgREST, não há API de banco.** O Postgres é alcançado apenas pelo servidor Flask via `psycopg2`, com a `DATABASE_URL` do processo. Portanto:

| Pergunta | Resposta |
|---|---|
| Tabelas expostas ao cliente? | **Não.** Nenhuma rota lê o banco, e o banco não é publicado para fora do host. |
| Existe RLS? | **Não.** `ROW LEVEL SECURITY` aparece **zero vezes** no repositório. |
| Existem policies (`USING (true)`, `WITH CHECK (true)`, `auth.uid()`)? | **Não existem.** Não há `CREATE POLICY` em lugar nenhum — e é exatamente por isso que a pergunta "explique cada policy" não tem o que explicar aqui. O controle de acesso não foi delegado ao banco; foi delegado ao `WHERE` da aplicação — **que não tem `WHERE` de dono em nenhuma consulta**. |
| O que existe no lugar do RLS? | Duas coisas, e nenhuma delas é do banco: (1) o **filtro por pasta** no disco (`<pasta>/<dono>/`, `src/ports/adaptadores.py:77-91`), que funciona e está testado; (2) a coluna `owner_id`, que é **gravada e nunca lida**. |

| Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|
| `owner_id` é `TEXT NOT NULL`, **sem FK e sem índice de escopo**, e o próprio esquema declara que nenhuma consulta filtra por dono. | **Alto (latente)** | `init.sql:26`, `init.sql:182-184` | Antes de existir qualquer leitura de histórico: índice `(owner_id, created_at DESC)` e **toda** consulta com `WHERE owner_id = %s`. Se o banco for exposto algum dia, RLS com `USING (owner_id = current_setting('app.dono'))` como segunda barreira. |
| `adotar()` faz `UPDATE dna_analysis SET owner_id = %s WHERE owner_id = 'unico'` — transfere **todas** as linhas não atribuídas para a conta que entrou. | **Médio** | `src/ports/adaptadores.py:566-591` | É a `RN-15` e é atômico (bom). O risco é de operação: quem entrar primeiro com o e-mail de `ANALISADOR_DONO_INICIAL` leva o acervo inteiro. Documentar como "primeiro login é irreversível" e logar a contagem transferida (hoje só o disco é logado). |
| A "adoção" do disco **copia** todos os arquivos da raiz para a pasta do dono inicial, sem apagar o original. | **Médio** | `src/application/dono_inicial.py:82-104` | Funciona e é conservador (nada é apagado). Falta um caminho de desfazer documentado: hoje o marcador `.dono-inicial` impede nova adoção, mas o original continua na raiz e continua sendo servido no modo sem autenticação (`"unico"`). |
| Nenhuma consulta de leitura de histórico existe no app (verificado: zero `SELECT` sobre `dna_analysis`/`match_result`). | — | — | Registro como o **motivo** de P2 ainda não ser explorável, e como a condição que o transforma em crítico. |

---

## Etapa 3 — Race conditions

O projeto não tem estoque, cupom, saldo, crédito, vaga nem convite. Os **recursos limitados reais** são: o arquivo no disco (nome único por conteúdo, versão única por nome visível), a pasta de aposentados (nome livre por colisão) e o cache de árvore (capacidade 1). A tabela cobre todos os trechos que leem, decidem e gravam.

| Achado (trecho que lê → decide → grava) | Risco | Arquivo e linha | O que acontece com 2 requisições iguais | Proteção existente / o banco sozinho resolveria? | Correção sugerida |
|---|---|---|---|---|---|
| `ArmazenamentoEmDisco.guardar`: `if not os.path.exists(caminho)` → `open(caminho, "wb").write(conteudo)` | **Alto** | `src/ports/adaptadores.py:119-121` | Mesmo conteúdo e mesmo dono produzem **o mesmo caminho**: as duas passam pelo `exists()`, as duas abrem o arquivo final para escrita. O conteúdo final fica correto (bytes idênticos), mas um leitor concorrente (`resolver` → `carregar_arvore`) pode abrir o arquivo **pela metade** e falhar o parse — o operador recebe o `500` genérico em vez da árvore. | **Nenhuma**: não há `O_EXCL`, não há escrita em temporário, não há rename atômico. **O banco não resolveria** — ele não participa do disco. | Escrever em `<caminho>.tmp-<uuid>` e `os.replace` no fim (atômico no mesmo volume), ou abrir com `O_CREAT\|O_EXCL` e tratar `FileExistsError` como "já gravado". |
| `reenvio.guardar_com_substituicao`: `listar` (foto) → `guardar` → `aposentar` as versões anteriores | **Médio** | `src/application/reenvio.py:62-77` | Dois uploads **diferentes com o mesmo nome visível**, simultâneos, e a pasta vazia: nenhum dos dois vê o outro na foto, nenhum aposenta nada, e a lista termina com **duas linhas do mesmo rótulo** — exatamente o defeito que a `RN-17` existe para impedir. Se já havia uma versão antiga, os dois tentam aposentá-la; o segundo recebe `False`, a mensagem sai como "novo" e a duplicata nasce do mesmo jeito. | **Nenhuma**: a foto é tirada antes, e nada serializa o par gravar/aposentar. **O banco não resolveria** (é disco); `ON CONFLICT` não tem onde atuar. | Serialização por dono: um `flock`/mutex sobre `<pasta>/<dono>` em volta do bloco inteiro, ou uma fila por dono. |
| `ArmazenamentoEmDisco.aposentar`: `os.path.isfile(origem)` → `_destino_livre` → `os.replace` | **Médio** | `src/ports/adaptadores.py:262-268` (o `os.replace` em `:267`) | Dois cliques em "aposentar" no mesmo arquivo: as duas passam pelo `isfile`, a primeira move, a segunda chama `os.replace` com a origem já inexistente → **`FileNotFoundError` não tratado** → `500`, e a linha de auditoria da segunda tentativa **não é escrita** (o `auditar` de `src/app.py:451` fica depois da chamada que levanta). | **Nenhuma**: o `os.replace` está fora de qualquer `try`. **O banco não resolveria.** | Capturar `FileNotFoundError`/`OSError` e devolver `False` (o contrato já existe: "não está mais na pasta", `404` com a mensagem congelada), garantindo que a auditoria rode nos dois desfechos. |
| `ArmazenamentoEmDisco._destino_livre`: `if not os.path.exists(destino): return destino` | **Médio** | `src/ports/adaptadores.py:280-285` | É **TOCTOU**: entre a checagem e o `os.replace`, o destino pode nascer (outro processo, ou um operador restaurando um aposentado à mão). Como `os.replace` **sobrescreve** no Windows e no POSIX, o aposentado que já estava lá é perdido em silêncio — violação direta da `RN-07` ("a aplicação nunca apaga arquivo enviado"). | **Nenhuma**: a checagem e a escrita não são a mesma operação. **O banco não resolveria.** | `os.link(origem, destino)` + `os.unlink(origem)` para falhar com `FileExistsError` em vez de sobrescrever, ou reabrir o laço de sufixo quando o `replace` acusar colisão. |
| `dono_inicial._copiar`: `exists(marcador)` → `copy2` arquivo a arquivo → grava marcador | **Baixo** | `src/application/dono_inicial.py:52-53`, `:82-104`, `:122-128` | Dois logins simultâneos da conta inicial copiam ao mesmo tempo. `copy2` **sobrescreve** o destino: não há perda (mesmo conteúdo), mas dois escritores no mesmo arquivo podem deixar um arquivo truncado no meio da cópia. O marcador em si é atômico (`.tmp` + `os.replace`). | **Parcial**: o marcador é atômico; a cópia não é. **No banco, `adotar` é um `UPDATE` único e atômico** — o contraexemplo positivo. | Serializar a cópia com o mesmo mutex por dono do `reenvio`, ou copiar para `.tmp` e renomear cada arquivo. |
| `CacheDeArvores.carregar`: `threading.Lock` + `threading.Event` (single-flight) | **Baixo** | `src/ports/adaptadores.py:398-459`, trava em `:369` | Quatro requisições na mesma árvore: uma parseia, três esperam o evento. Se o parse do primeiro falhar, quem esperou parseia por conta própria. | **`threading.Lock` em memória** (não há lock no Redis nem leitura de cache distribuído). **O banco não resolveria, e não precisa:** o cache é de *desempenho*, não de integridade. O limite real é que o lock **não vale entre processos**: com N workers, cada um parseia a própria cópia e a memória multiplica (~337 MB por árvore). Hoje contido porque `src/app.py:934-950` garante instância única e um processo. | Nada a corrigir enquanto o servidor for processo único; registrar no README que trocar waitress por gunicorn multiprocesso quebra a exclusividade **e** a estimativa de memória. |
| `RegistroDeAnalisesPostgres.adotar`: `UPDATE ... WHERE owner_id = 'unico'` | — (OK) | `src/ports/adaptadores.py:566-591` | Duas chamadas simultâneas: a primeira transfere N linhas, a segunda encontra zero e devolve `0`. | **Atomicidade do próprio `UPDATE`** — é o único trecho em que o banco, sozinho, resolve. | Nada. |
| Constraints que **já existem**: `uq_match_kit_ordinal (match_id, ordinal)`, `uq_skipped_ordinal (analysis_id, ordinal)`, PKs compostas, FKs com `ON DELETE CASCADE` | **Baixo** | `init.sql:97-130`, `init.sql:148`, `init.sql:166` | Duas gravações da mesma análise **não colidem**, porque `analysis_id` é UUID novo por chamada. Essas constraints impedem ordinal repetido *dentro* da mesma análise, e não o registro duplicado. | Constraints de banco (boas, mas não cobrem o caso) / **o banco resolveria** se existisse a chave de requisição. | Adicionar `UNIQUE (owner_id, request_id)` em `dna_analysis` — ver Etapa 4. |

---

## Etapa 4 — Idempotência

### 4.1 Webhooks recebidos

**Não existem.** Verifiquei em `src`, `tests`, `docs` e `docker`: zero ocorrências de `webhook`, `Stripe`, `PagSeguro`, `MercadoPago`, `Asaas`. Não há endpoint de recebimento, logo não há assinatura a verificar com corpo bruto, nem tabela de eventos processados, nem comportamento a descrever para "o mesmo evento chegando duas vezes".

> **Não verificado — e o motivo é que não há o que verificar.** Registro assim em vez de descrever um webhook hipotético.

### 4.2 Chamadas ao gateway de pagamento

**Não existem.** Não há gateway, não há cobrança, não há `Idempotency-Key`. O único serviço externo chamado é o Google (OAuth), e ele não é gateway de pagamento.

### 4.3 O que existe de fato, e como se comporta em duplicidade

| Operação | Se a mesma requisição chegar 2 vezes | Proteção | Risco |
|---|---|---|---|
| **Callback OAuth** (`GET /callback`) | O `state` é removido da sessão com `session.pop` e comparado com `hmac.compare_digest`; a segunda chegada não encontra `state` e recebe "A entrada expirou". O `code` é de uso único **no Google**, então um replay direto recebe `token_http_400`. | Uso único do `state` no cookie assinado + uso único do `code` no provedor. **Não há registro de evento processado** (nem tabela, nem cache). | **Médio** — a defesa contra replay é delegada 100% ao provedor; se ele mudar o contrato, nada do lado de cá segura. |
| **POST de análise** (`action=dna_analysis`) | Dois cliques criam **duas análises completas**: duas linhas em `dna_analysis`, com todas as filhas, e **dois parses de ~50 s** (o cache single-flight segura o parse simultâneo, mas o segundo POST chega depois e parseia de novo se a árvore já saiu do cache). Nada detecta que é a mesma intenção. | **Nenhuma.** Sem `Idempotency-Key`, sem chave única no banco, sem *debounce* no front que sobreviva a duplo clique real. | **Médio** |
| **Upload de GEDCOM / CSV** | É **idempotente por construção**: o nome vem do `sha256` do conteúdo, então o mesmo envio reencontra o mesmo caminho e a porta não regrava. A mensagem distingue "já estava armazenado" de "carregado". | Chave derivada do conteúdo (`src/utils/validate.py:104-106`, `src/ports/adaptadores.py:116-122`). | — (OK) |
| **Aposentar** | Segunda tentativa devolve `404` com "não está mais na pasta" — idempotente em efeito. Mas *concorrente* quebra (ver Etapa 3, linha do `os.replace`). | Nenhuma atômica. | **Médio** |
| **`/logout`** | Idempotente por desenho: sem sessão, também redireciona para a entrada (`src/web/rotas_auth.py:109-122`). | — | — (OK) |
| **Adoção do histórico** (`adotar`) | Idempotente por condição (`WHERE owner_id = 'unico'`); a segunda chamada devolve `0`. | `UPDATE` atômico. | — (OK) |

| Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|
| POST de análise sem chave de idempotência: duplo envio grava o histórico duas vezes e paga dois parses. | **Médio** | `src/app.py:552-561`, `src/ports/adaptadores.py:544-564`, `init.sql:24-35` | Gerar um `request_id` no servidor por renderização do formulário (campo oculto assinado) e gravá-lo em `dna_analysis` com `UNIQUE (owner_id, request_id)`; a segunda gravação vira *no-op* e a tela devolve o resultado já calculado. Alternativa mínima: desabilitar o botão no `submit` **e** aceitar a duplicata no banco (o custo caro é o parse, e o cache já o reduz). |
| O callback OAuth não registra eventos processados. | **Médio** | `src/web/rotas_auth.py:70-106` | Se o provedor um dia passar a reenviar, não há como detectar. Registrar o `jti`/`code` já consumido (tabela ou cache com TTL) e recusar antes da troca. Hoje é dívida, não bug. |

---

## Etapa 5 — Separação de responsabilidades

Contagem exata de linhas (`(Get-Content).Count`, incluindo brancas):

| Arquivo | Linhas | Tela | Regra de negócio | Banco / serviço externo | Diagnóstico |
|---|---|---|---|---|---|
| `src/templates/index.html` | **2407** | Sim (todo o HTML) | Sim (filtro, paginação, ordenação e o payload `dados` montados em **6 blocos de `<script>` inline**) | Não | Grande, mas de uma responsabilidade só (apresentação). O problema é o **JS de comportamento** convivendo com o Jinja no mesmo arquivo. |
| `src/assets/app.css` | **1732** | Sim | Não | Não | Só estilo. Fora do escopo do achado. |
| **`src/app.py`** | **988** | **Sim** (`render_template` em 21 pontos) | **Sim** (decide CSV vs upload, promoção, 404 vs 200, qual mensagem) | **Sim** (monta `RegistroDeAnalisesPostgres`, lê `os.environ`, chama a auditoria/log) **e** sobe o servidor de produção | **Candidato nº 1.** Cinco responsabilidades num módulo: fábrica da app, configuração, handlers HTTP com decisão de negócio, efeitos externos (auditoria/log) e **bootstrap do waitress** (socket exclusivo, `errno`, `SystemExit`) nas linhas 879-988. |
| `src/core/cirurgia_do_grafo.py` | 838 | Não | Sim | **Não** (só `math` e vizinhos de domínio) | Domínio puro. Correto. |
| `src/core/endogamia.py` | 800 | Não | Sim | Não | Domínio puro. Correto. |
| **`src/ports/adaptadores.py`** | **689** | Não | Não | **Sim, quatro vezes**: disco, cache em memória, carregador de árvore e Postgres | **Candidato nº 2.** Quatro adaptadores independentes no mesmo arquivo; o acesso ao banco mora junto com o cache e o sistema de arquivos. Separar em `armazenamento_em_disco.py`, `cache_de_arvores.py`, `carregador_de_arvores.py` e `registro_postgres.py`. |
| `src/reporting/mermaid_render.py` | 576 | Sim (gera o diagrama) | Parcial (geometria/largura) | Não | Aceitável: é o formatador de uma representação. |
| `src/core/relationship_hypotheses.py` | 566 | Não | Sim | Não | Domínio puro. |
| `src/core/validator.py` | 528 | Não | Sim | Não | Domínio puro. |
| `src/core/passo_por_kit.py` | 474 | Não | Sim | Não | Domínio puro. |
| `src/ports/__init__.py` | 468 | Não | Define contratos | Não | Fino, mas é onde o contrato de porta mora — está no lugar certo. |

| Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|
| `src/app.py` mistura fábrica, rotas com regra de negócio, efeitos externos e **bootstrap do servidor**. O caso mais caro é `_acao_dna_analysis` (147 linhas): lê formulário, decide substituição de CSV, monta promoção, chama o caso de uso **com o registrador do banco**, audita e renderiza. | **Médio** (manutenção/risco de regressão) | `src/app.py:480-626`; bootstrap em `src/app.py:879-988` | Extrair em três: (1) `web/routes/index.py` com os despachantes e **sem** decisão de negócio (a decisão de CSV já vive em `application/reenvio.py` — falta só parar de orquestrá-la na rota); (2) `server.py` com o bloco `__main__` (socket, waitress, `errno`); (3) `factory.py` com `create_app`. Alvo: nenhuma função de rota acima de ~40 linhas. |
| `index.html` concentra 6 blocos de JS inline (~500 linhas) que manipulam dados da análise (filtro, paginação, impressão). | **Baixo** | `src/templates/index.html:604-760`, `1996-2347`, `2353-2404` | Mover para `src/assets/app.js` servido por rota (como já se faz com `/app.css`) e remover o `mermaid` inline — é pré-requisito para a CSP que a `BUG-20261013-4PYJ` já registra como pendente. |
| `ports/adaptadores.py` reúne quatro adaptadores. | **Baixo** | `src/ports/adaptadores.py:65-286`, `336-459`, `469-507`, `510-686` | Dividir em quatro módulos, mantendo `ports/__init__.py` como fachada de import para não quebrar a borda. |
| Comentários de contrato desatualizados **contradizem o código atual**: `upload_gedcom` afirma que "`dono` não é usado para comportamento... nenhum isolamento entre donos é implementado aqui", mas a feature 051 fez o adaptador escopar por dono; `application/dna_analysis.py` repete a mesma frase sobre o banco. | **Baixo** (mas é o tipo de comentário que faz um revisor concluir o oposto do que o código faz) | `src/application/upload_gedcom.py:75-79`, `src/application/dna_analysis.py:72-75` | Atualizar os dois docstrings para o comportamento pós-051 (disco escopado; banco ainda não escopado em consulta). |

---

## Não verificado (e o motivo)

| Item | Por que não foi verificado |
|---|---|
| Execução real do fluxo OAuth contra o Google (troca de código, leitura de perfil, HTTPS) | Exigiria credencial real e rede. A suíte usa provedor falso de propósito; a troca de código real nunca é exercitada por teste. |
| Persistência em PostgreSQL contra banco vivo | `psycopg2` **não está instalado** no `.venv` do host (8 testes auto-pulados) e não há `DATABASE_URL` no ambiente. Não instalei nada, por instrução. Os mesmos caminhos são exercitados por `tests/verificacao_no_conteiner.py` (rodando dentro da imagem) e pela verificação manual T020/T021 — **não executei nenhum dos dois**. |
| Comportamento sob concorrência real (4 threads do waitress) | Auditei por leitura de código e por raciocínio sobre o intercalamento; não instrumentei nem disparei requisições simultâneas. As conclusões da Etapa 3 são análise estática, não medição. |
| Restauração de backup / integridade do volume `dados_do_banco` | Fora do escopo: não há rotina de backup no repositório para auditar (verifiquei `docker-compose.yml` e `atualizar.ps1`; nenhum dos dois faz *dump*). |
| Conteúdo real de `src/uploads/` (dados do operador) | Dado pessoal; não abri nenhum arquivo de árvore nem listei nomes. Só li o código que os manipula. |
| Superfície de rede além de `127.0.0.1` | O compose publica app em `127.0.0.1:5080` e banco em `127.0.0.1:5432`; se há proxy/túnel na frente em produção, não há nada no repositório que o descreva. |

---

## Qual dos 5 prompts de correção rodar primeiro

**Rode o P1 primeiro** — *tornar a autenticação fail-closed independentemente do entrypoint*.

Três razões, na ordem que importa:

1. **É o único achado que expõe dado hoje.** P2, P3 e P4 são latentes ou condicionais (P2 só morde quando o histórico for exibido, P3 precisa de concorrência, P4 precisa de alguém habilitar o banco). O P1 não: qualquer processo que monte a app sem as cinco variáveis — `flask run`, `waitress-serve`, `gunicorn`, um teste manual de import — serve a aplicação **sem login**, e `_dono()` cai em `"unico"`, que resolve para a **raiz** da pasta de upload, onde estão todos os arquivos herdados. É a diferença entre "há uma dívida" e "há uma porta aberta".
2. **É o menor esforço com o maior retorno.** Não mexe em esquema, não mexe em dados, não exige migração. É uma guarda incondicional na fábrica mais a recusa de subida fora do `__main__`.
3. **Ele condiciona a verificação dos outros quatro.** Com a app incapaz de subir aberta, os testes de P2/P3/P4 passam a ter um estado de referência confiável — hoje, metade da suíte roda no modo sem autenticação (`"unico"`), que é justamente o modo que o P1 vai eliminar. Sem resolver isso antes, cada correção seguinte precisa ser validada em dois modos.

**Restrição de projeto que o P1 precisa respeitar** (e que o prompt tem de dizer em voz alta): 1752 testes e o harness de paridade **importam `src/app.py` sem credencial** de propósito. Uma guarda incondicional ingênua derruba a suíte inteira. A forma segura é: `create_app()` recusa montar a app sem as cinco variáveis **a menos que** um modo de teste explícito esteja ligado (`ANALISADOR_MODO_TESTE=1`, ligado no `tests/conftest.py`), e `_dono()` deixa de ter o fallback silencioso para `"unico"` — passando a levantar se for chamado sem sessão fora do modo de teste. Assim o P1 fecha a porta sem apagar o caminho legado que os testes usam.

Depois do P1, a ordem que eu seguiria é **P2 → P4 → P3 → P5**: P2 porque é a próxima barreira que impede vazamento entre contas e é pré-requisito de qualquer tela de histórico; P4 porque sem banco de teste separado é arriscado exercitar P2 e P3 contra o acervo real; P3 porque as corridas de disco são reais mas produzem duplicata e `500`, não perda silenciosa na maioria dos casos; e P5 por último porque a suíte verde é o que **prova** que P1–P4 funcionaram — mas ela precisa entrar em algum momento, e a falha de caracterização do Mermaid é o item mais barato de toda a lista.
