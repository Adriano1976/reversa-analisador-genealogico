# Auditoria — Analisador de Conexões Genealógicas

**Data:** 2026-10-30
**Base auditada:** `HEAD` = `619395c` (`test(auth): cobre o contrato da tela de entrada da 053`), árvore limpa.
**Escopo desta rodada:** releitura completa depois das features 052 (busca por nome) e 053 (conta com senha, confirmação e recuperação), **com o objetivo novo de distribuir o app por instalador no computador do usuário**.
**O que NÃO foi feito:** nenhum arquivo do projeto foi alterado, nenhuma migração foi aplicada, nada foi instalado. O único arquivo escrito é este relatório. As duas sondas de execução rodaram com pastas temporárias em `.parity-tmp/` (ignorado pelo git) e foram removidas no mesmo comando; `git status --porcelain` terminou vazio depois de cada uma, e ao fim da auditoria o único caminho alterado é o deste relatório.

---

## O que mudou desde a auditoria de 2026-10-28

| Mudança | Efeito na auditoria |
|---|---|
| Feature 053 entrou: `/cadastro`, `/login` com senha, `/confirmar`, `/recuperar-senha`, `/redefinir-senha`, `/definir-senha`, tokens de uso único, transporte SMTP, `ContasEmArquivo` | Nasceu uma superfície de autenticação **própria** — e com ela a pergunta "onde ficam as contas?". A resposta cria o P2 de hoje. |
| `src/dados/contas.json` passou a existir, com **duas contas reais** (uma Google, uma local), ambas com credencial scrypt | O maior achado novo: esse arquivo está dentro de `src/`, que é exatamente o que a imagem Docker copia. |
| Feature 052 entrou: `POST /busca`, fontes de nomes, isolamento por dono na busca | Não há achado novo de isolamento: a busca resolve por dono e o teste de isolamento existe. |
| Suíte cresceu de 1752 para **1939 testes passando** (1953 casos coletados) | As **mesmas 5 falhas** de 28/10 continuam. |
| Objetivo declarado: distribuir por instalador | Não existe uma linha de empacotamento no repositório. A Etapa 6 mede o que **impede** esse instalador de funcionar. |

**Mapa em relação à auditoria de 28/10:** o antigo P1 (autenticação condicional) continua **P1**; o antigo P3 (corridas de disco) virou **P5**; o antigo P2 (isolamento no banco) caiu para a Etapa 2 porque segue latente; o antigo P4 (banco de teste) e o antigo P5 (suíte vermelha) saíram do top 5 — com o instalador no horizonte, dois bloqueios de empacotamento passam na frente deles.

---

## Os 5 achados de maior risco, em ordem

| # | Achado | Risco | Onde | Por que está nesta posição |
|---|---|---|---|---|
| **P1** | A autenticação continua **condicional ao entrypoint**. Só `python src/app.py` recusa subir sem as cinco variáveis; `create_app()` monta a aplicação **sem guarda nenhuma** e `_dono()` cai no literal `"unico"`, que aponta para a raiz da pasta de upload. Medido nesta rodada: sem credencial, `GET /` responde **200**, `GET /login` responde **404** e `POST /` com `action=upload_gedcom` **executa o handler**. | **Alto** | `src/app.py:243`, `src/app.py:1005-1013`, `src/app.py:1022-1041`, `src/app.py:101` | É o único achado que expõe dado **hoje**, e o instalador vai escolher o entrypoint por você. Qualquer atalho que não chame `app.py` (`waitress-serve` na linha de comando, um serviço do Windows, um `.bat` com `flask run`) sobe o app aberto, com todas as árvores e relatórios. |
| **P2** | As contas reais moram **dentro de `src/`** (`src/dados/contas.json`) e entram no artefato: o `.dockerignore` é lista de permissão e libera `src/**`, reexcluindo **só** `src/uploads/`; o `Dockerfile` faz `COPY src/`. Hoje o arquivo tem duas contas com e-mail, hash scrypt e (se houver) tokens pendentes. | **Alto** | `src/app.py:251-262`, `.dockerignore:15`, `.dockerignore:21`, `docker/Dockerfile:46` | Vaza material de credencial para quem receber a imagem ou o instalador — e faz o cliente herdar a conta do desenvolvedor. Acontece **na primeira vez** que alguém empacotar o app. |
| **P3** | **Não existe modo "instalação local"**: toda a identidade da 053 (cadastro, senha, recuperação) só é montada se as **cinco** variáveis do Google existirem. Sem elas, `/cadastro` e `/login` nem são registradas. Medido: com as cinco preenchidas com valor inventado, tudo monta e `GET /` passa a redirecionar para `/login`. | **Alto** | `src/app.py:243`, `src/app.py:908-928`, `src/app.py:1005-1013`, `src/web/autenticacao.py:38-44` | É o que decide o instalador: ou ele embarca o **client secret do Google do desenvolvedor** em cada máquina (o mesmo cliente OAuth para todos os clientes), ou inventa cinco valores, ou entrega o app aberto (P1). Não há quarta opção hoje. |
| **P4** | Tudo o que a aplicação **escreve** está ancorado no diretório da instalação: uploads (`__file__`), logs (raiz do projeto) e contas (`src/dados`). E a criação da pasta de upload roda **no import, sem guarda**. Medido: com a pasta não gravável, `import app` levanta `PermissionError` e o app **não sobe** — sem mensagem de contrato, com traceback. | **Alto** | `src/app.py:191-211`, `src/app.py:251-262`, `src/utils/logs.py:198-208` | Instalador padrão no Windows escreve em `C:\Program Files\...`, que não é gravável por usuário comum. Sem mover os dados para `%LOCALAPPDATA%`, o produto não abre na máquina do cliente. |
| **P5** | O armazenamento em disco continua fazendo **ler → decidir → gravar** sem operação atômica: `exists()` antes de `open("wb")`, `_destino_livre` decidindo por `exists()` e `os.replace` executando depois, e a foto → grava → aposenta do reenvio sem serialização. | **Alto** | `src/ports/adaptadores.py:119-121`, `src/ports/adaptadores.py:263-267`, `src/ports/adaptadores.py:270-286`, `src/application/reenvio.py:62-77` | É o defeito mais provável de acontecer no uso real (4 threads no waitress + duplo clique): grava dois arquivos no mesmo caminho, aposenta a versão recém-gravada e devolve `500` no lugar da mensagem de contrato. |

Os cinco prompts de correção correspondentes estão nomeados **P1…P5**, e a ordem recomendada de execução está no fim do documento.

---

## Como verifiquei

| Verificação | Comando | Resultado |
|---|---|---|
| Suíte completa | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` | **5 failed, 1939 passed, 9 skipped** em 350,37 s (1953 casos coletados) |
| Motivo dos 9 skips | `pytest tests/test_registro_de_analises.py tests/test_manutencao_de_uploads.py -q -rs` | 8 = banco (`DATABASE_URL` **e** `psycopg2` ausentes, os dois medidos); 1 = link simbólico sem privilégio |
| Driver do banco | `python -c "import importlib.util; print(find_spec('psycopg2'))"` | `None` — o `.venv` **não tem** o driver; `DATABASE_URL` também não está no ambiente |
| App sobe aberto? | sonda com `create_app()` + `test_client`, sem as cinco variáveis | `GET /` → **200**; `GET /login` → **404**; `POST /` (`upload_gedcom`) → **200** |
| Modo local existe? | mesma sonda com as cinco variáveis preenchidas com valor inventado | 17 regras de rota (a `/busca` aparece duas vezes, `GET` e `POST`), `/cadastro` → **200**, `GET /` → **302 /login** |
| Pasta de upload não gravável | mesma sonda apontando para local sem permissão | `PermissionError` em `src/app.py:211`, traceback cru, app não importa |
| Contas reais no diretório do código | leitura de `src/dados/contas.json` (só metadados, sem valores) | `contas: 2`, ambas com credencial e confirmadas, `tokens: 0`; `git check-ignore` confirma que o git as ignora (`.gitignore:42`) |
| O que entra na imagem | leitura de `.dockerignore` e `docker/Dockerfile` | `!src/**` (linha 15) inclui `src/dados/`; só `src/uploads/` é reexcluído (linha 21) |
| RLS / policies | busca por `ROW LEVEL SECURITY`, `CREATE POLICY`, `auth.uid`, `USING (true)`, `WITH CHECK` em todo o repositório | **zero ocorrências** |
| Webhook / gateway | busca por `webhook`, `stripe`, `pagseguro`, `mercadopago`, `asaas`, `idempoten` em `src`, `tests`, `docker` | 18 ocorrências, **todas** de "idempotente" em prosa ou de `UPDATE` idempotente; nenhum webhook, nenhum gateway |
| Preço / plano / admin | busca por `preço`, `desconto`, `plano`, `admin`, `assinatura`, `cobrança`, `checkout` | 82 ocorrências, **todas** falsos positivos: em português `assinatura` é assinatura de função/parâmetro. Não há cobrança no produto |
| Segredo no front | busca por `NEXT_PUBLIC`, `VITE_`, `EXPO_PUBLIC`, `secret`, `api_key`, `client_id`, `Bearer` em `src/templates` e `src/assets` | **zero** variáveis públicas; nenhum segredo em HTML/CSS |
| Locks / atomicidade | busca por `FOR UPDATE`, `ON CONFLICT`, `flock`, `advisory`, `threading.Lock`, `RLock` em `src` | 2 travas em memória (`adaptadores.py:369`, `contas_em_arquivo.py:62`) + `SO_EXCLUSIVEADDRUSE`; **nenhum** lock de linha no banco |
| Instalador | busca por `pyinstaller`, `inno setup`, `nsis`, `msix`, `wix`, `squirrel`, `nuitka`, `instalador` | **zero** arquivos e zero menção; não existe empacotamento no repositório |
| Versão do produto | busca por `__version__`, `VERSION` em `src` | **zero** ocorrências |

**Nota de ambiente (não é achado do projeto):** a política de escrita do meu harness mudou no meio da execução e passou a negar criação de diretório no temporário do sistema; a suíte não depende disso (o `tests/conftest.py` isola uploads e logs), mas a sonda da pasta não gravável reproduziu, por acidente, exatamente o defeito de `src/app.py:211`. O achado P4 é do código, não do meu sandbox: a linha não tem guarda.

---

## Etapa 1 — Testes de integração

### Ferramenta, banco e comando

- **Ferramenta:** pytest 9.1.1, configurado por `pytest.ini` (só `testpaths = tests`). Não há marcador de integração, não há `pytest-cov` declarado no `requirements.txt` (o `.coverage` da raiz é artefato de execução manual), e não há plugin de banco.
- **Banco de teste:** **não existe.** O único teste que fala com PostgreSQL usa o `DATABASE_URL` do ambiente — o mesmo nome de variável do banco de produção — e apaga linhas por `tree_ref = 'chave__arvore.ged'`, que é um nome plausível de arquivo real.
- **Comando para rodar tudo:** `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
- **Toca produção?** Não, do jeito que está: sem `DATABASE_URL` e sem driver, os 8 testes de banco são pulados e os demais isolam uploads e logs em temporário. **Mas** o caminho que habilita esses 8 aponta para o banco de produção.

### Resultado da execução

| Número | Valor |
|---|---|
| Passam | **1939** |
| Falham | **5** |
| Pulados | **9** |
| Total | 1953 |
| Tempo | 350,37 s |

As 5 falhas são as **mesmas** de 28/10 — nenhuma regressão nova da 052/053:

| Teste | O que ele espera | O que o código entrega |
|---|---|---|
| `test_characterization_mermaid.py::test_saida_mermaid_caracterizada[direto]` | `width:190px` | `width:230px` |
| `test_characterization_mermaid.py::…[indireto]` | `width:190px` | `width:230px` |
| `test_characterization_mermaid.py::…[trivial]` | `width:190px` | `width:230px` |
| `test_characterization_mermaid.py::test_o_no_carrega_a_caixa_de_tamanho_fixo` | `width:190px` | `width:230px` |
| `test_tres_fases_da_tela.py::TestLiteraisPreservados::test_os_rotulos_congelados_continuam` | literal `1. Lista de Matches (CSV)` na tela | o literal sumiu |

São testes de **caracterização**: eles congelam um desenho que foi alterado sem atualizar o teste. Não indicam bug de produto — indicam contrato desatualizado.

### Fluxos críticos × cobertura

O produto **não é e-commerce**: não há cadastro de cliente pagante, checkout, assinatura, gateway ou webhook. Os fluxos críticos reais são os de identidade e os de arquivo/análise.

| Fluxo | Tipo de teste | Onde |
|---|---|---|
| Cadastro (e-mail + senha) | **rota de verdade** (`POST /cadastro`, arquivo de contas em memória, e-mail em memória) | `tests/test_cadastro_e_confirmacao.py`, `tests/test_rotas_de_identidade.py` |
| Login com senha | **rota de verdade** (`POST /login` pelo helper `entrar_com_senha`) | `tests/fixtures/identidade.py`, `tests/test_rotas_de_identidade.py` |
| Login Google / `/callback` | **rota de verdade com provedor falso**; a troca real com o Google **não** é exercitada (por desenho: `ProvedorFalso`) | `tests/test_autenticacao.py`, `tests/test_tela_de_entrada.py` |
| Confirmação de e-mail | **rota de verdade** (`GET /confirmar?token=`) | `tests/test_cadastro_e_confirmacao.py` |
| Recuperação / redefinição | **rota de verdade** (`POST /recuperar-senha`, `GET`+`POST /redefinir-senha`), SMTP dublê | `tests/test_recuperacao_de_senha.py`, `tests/test_alternar_senha.py` |
| Definir senha (conta Google) | **rota de verdade** (`/definir-senha`) | `tests/test_definir_senha.py` |
| Logout | **rota de verdade** (`POST /logout`) | `tests/test_sessao_e_guarda.py` |
| Guarda de sessão (302/303, `no-store`, cookie) | **rota de verdade** | `tests/test_sessao_e_guarda.py` |
| Upload de GEDCOM | **rota de verdade** (`POST /` `action=upload_gedcom`) | `tests/test_upload.py`, `tests/test_upload_seguranca.py` |
| Análise de DNA | **rota de verdade** (`action=dna_analysis`) | `tests/test_dna_analysis.py` |
| Busca de caminho | **rota de verdade** (`action=path_search`) | `tests/test_path_search.py` |
| Busca por nome | **rota de verdade** (`POST /busca`) | `tests/test_rota_de_busca.py`, `tests/test_isolamento_da_busca.py` |
| Aposentar arquivo | **rota de verdade** (`action=aposentar_arquivo`) | `tests/test_aposentar_arquivo.py` |
| **Persistência no PostgreSQL** | **nenhum** — 8 testes pulados | `tests/test_registro_de_analises.py` |
| Envio SMTP real (`smtplib`) | **nenhum** — o dublê substitui o transporte | `tests/fixtures/identidade.py` (`EmailQueGrava`) |
| Checkout / assinatura / webhook | **não aplicável** — o produto não cobra | busca sem ocorrência |

### Achados da Etapa 1

| # | Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|---|
| 1.1 | **Não há banco de teste.** O teste de banco usa a mesma variável do banco de produção (`DATABASE_URL`), e habilita-lo aponta a suíte para o acervo real. | **Alto** | `tests/test_registro_de_analises.py:45-51` | Criar `ANALISADOR_DATABASE_URL_DE_TESTE` (ou schema dedicado) e **recusar** rodar se a URL não contiver um marcador de teste; nunca cair no `DATABASE_URL`. |
| 1.2 | A limpeza apaga por `tree_ref = 'chave__arvore.ged'` sem escopo de dono nem de execução. | **Alto** | `tests/test_registro_de_analises.py:107-117` | `DELETE ... WHERE tree_ref = %s AND owner_id = %s AND created_at > %s`, com o dono e o instante da execução. |
| 1.3 | **O CI não roda teste nenhum** — só `pyrefly check src`. Um PR pode quebrar 1939 testes verdes e o check fica verde. | **Alto** | `.github/workflows/tipos.yml:38-42` | Job `pytest` sem banco (o caminho padrão já é "sem `DATABASE_URL`"), com `-q` e falha em skip inesperado. |
| 1.4 | O driver `psycopg2` **não está no `.venv`** e o `DATABASE_URL` não está definido: os 8 testes de banco nunca rodaram nesta máquina. | **Alto** | `tests/test_registro_de_analises.py:1-22`, `:45-51` | Instalar o driver no ambiente oficial e subir o `db` do compose apontando para banco de teste (depende de 1.1). |
| 1.5 | **Suíte vermelha em `HEAD`**: 5 falhas de caracterização. | **Médio** | `tests/test_characterization_mermaid.py:174`, `tests/test_tres_fases_da_tela.py:258` | Atualizar a caracterização para `230px` e o literal da tela (ou reverter o desenho), e só então ligar o CI da 1.3 — senão o job nasce vermelho. |
| 1.6 | Um teste **congela o modo aberto** como contrato: sem autenticação, a tela tem de responder 200 e `/login` tem de ser 404. | **Alto** (é a causa do P1) | `tests/test_sessao_e_guarda.py:80-88` | Substituir por um teste que exija **recusa**, com escape explícito de teste (`ANALISADOR_MODO_TESTE=1` fixado no `tests/conftest.py`), em vez de "sem credencial = aberto". |
| 1.7 | Não há marcador de teste de integração: os 1939 verdes e os 8 pulados aparecem no mesmo número, e "1939 passed" sugere cobertura de banco que não existe. | **Baixo** | `pytest.ini:1-2` | `markers = integracao` e um alvo `-m "not integracao"` no CI, com o total de integração reportado à parte. |

---

## Etapa 2 — Confiança no cliente

### Regras que existem só no front

**Nenhuma.** O produto não tem preço, desconto, papel de admin nem limite de plano (busca com 82 ocorrências e **todas** falsos positivos: em português, `assinatura` é assinatura de função). As regras que existem são de servidor:

- teto de upload de 16 MB em duas camadas (Flask e waitress) — `src/app.py:128`, `:149`, `:957`;
- teto do termo de busca em 120 caracteres, aplicado na rota e não só no `maxlength` — `src/web/rotas_busca.py:36`, `:71`;
- política de senha no núcleo, uma única autoridade, com a tela apenas exibindo a mesma frase — `src/core/conta.py:111-136`;
- limite de tentativas por escopo — `src/application/limite.py:42-47`.

O `maxlength` do HTML existe como conforto, e o servidor repete o limite. Não encontrei nenhuma decisão de negócio que dependa do navegador.

### Chaves e tokens que vão para o navegador

| Item | Classificação | Onde |
|---|---|---|
| Variáveis `NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_` ou equivalentes | **nenhuma** (0 ocorrências) | — |
| Cookie de sessão `analisador_sessao` | **pública por design** — assinada, `HttpOnly`, `SameSite=Lax`, `Secure` só em HTTPS | `src/app.py:838-846`, `src/web/sessao.py:88-101` |
| Token de redefinição/confirmação na URL e no campo oculto | **secreta, mas por design** — é o portador do link; a página sai com `no-store` e `Referrer-Policy: no-referrer` | `src/web/rotas_conta.py:112-117`, `:308`, `:314` |
| Segredos em HTML/CSS (`secret`, `api_key`, `client_id`, `Bearer`) | **nenhum** (0 ocorrências) | — |
| `contas.json` (e-mail + hash scrypt + tokens) | **secreta — e hoje sai no artefato** (ver 2.1) | `src/app.py:251-262` |
| Senha de SMTP e client secret do Google | **secretas — em arquivo ao lado do app** (ver 2.2) | `.env.local:11`, `.env.local:20` |

### Banco exposto por API

Não há Supabase, não há PostgREST, não há API de dados. Há um **PostgreSQL 16 publicado em `127.0.0.1:5432`** (só loopback, o que é correto) e **zero RLS, zero policy, zero `auth.uid`**.

Em português, o que isso significa: **não existe uma única regra de banco dizendo quem pode ler o quê.** O banco aceita qualquer conexão que apresente a senha do `.env`, e devolve todas as linhas. O controle de acesso que existe é o `WHERE` escrito na aplicação — e a tabela `dna_analysis` **não tem `WHERE owner_id` em lugar nenhum**: o campo é gravado em toda análise (`src/ports/adaptadores.py:604-613`) e nunca lido por filtro, porque não há tela de histórico ainda. `init.sql:26` declara a dívida com todas as letras ("SEM FK e SEM indice de escopo") e `init.sql:182-184` repete que nenhum índice começa por `owner_id`.

Consequência prática para o instalador: se o banco for embarcado na máquina do cliente, qualquer processo local que leia o `.env` (ou o arquivo de configuração do serviço) lê o histórico inteiro de todas as contas — o app não tem como impedir, porque a barreira não está no banco.

### Achados da Etapa 2

| # | Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|---|
| 2.1 | **`src/dados/contas.json` está dentro da árvore de código e entra no artefato.** O `.dockerignore` libera `src/**` e reexclui apenas `src/uploads/`; o `Dockerfile` copia `src/` inteiro. O arquivo existe, com duas contas reais. | **Alto** | `src/app.py:251-262`; `.dockerignore:15`; `.dockerignore:21`; `docker/Dockerfile:46` | Mover o dado de runtime para fora de `src/` (ex.: `%PROGRAMDATA%`/`%LOCALAPPDATA%` no host, `/dados` no container) **e** excluir `src/dados/` no `.dockerignore` como já se faz com `src/uploads/`. |
| 2.2 | `.env.local` guarda **credencial SMTP real** e o **client secret do Google** no diretório do app; qualquer pacote feito "copiando a pasta" os leva. Há ainda `ANALISADOR_SECRET_KEY` duplicada (uma vazia, uma preenchida). | **Alto** | `.env.local:11`, `.env.local:15`, `.env.local:20`; `iniciar.ps1:23` | Instalador deve gerar os segredos **por instalação** e nunca copiar `.env*`; validar a duplicata no carregamento (a última vence hoje, em silêncio). |
| 2.3 | O isolamento por dono **não existe no banco**: `owner_id` é gravado e nunca filtrado; sem RLS, sem policy, sem índice de escopo. | **Alto (latente)** | `init.sql:26`, `init.sql:182-189`, `src/ports/adaptadores.py:583` | Índice `(owner_id, created_at DESC)`, um caminho único de leitura já escopado, e o teste que prova que nenhuma consulta sai sem `WHERE owner_id`. RLS é opcional enquanto o banco não for multiusuário; o índice não é. |
| 2.4 | PostgreSQL publicado em loopback, **sem RLS**, com a senha em arquivo texto. | **Médio** | `docker-compose.yml:37`, `.env:14` | Se o banco for embarcado, gerar a senha por instalação e restringir a leitura do arquivo à conta do serviço. |
| 2.5 | A senha de SMTP fica em claro em arquivo de configuração e é lida por `os.environ`; não há cofre nem variável de serviço. | **Médio** | `src/ports/email_smtp.py:33-40`, `:131-138` | No instalador, guardar em Credential Manager/DPAPI, ou pedir ao usuário na primeira execução e não persistir. |
| 2.6 | A conta "dona inicial" (`ANALISADOR_DONO_INICIAL`) **herda todos os arquivos da raiz** no primeiro login, copiando o acervo inteiro para a pasta dela. | **Médio** | `src/application/dono_inicial.py:42-63`, `src/web/rotas_auth.py:228-240` | Em instalação nova, a pasta nasce vazia e o fluxo nunca roda; garantir que o instalador **não** embale `src/uploads/` (hoje o `.dockerignore` já protege a imagem, mas não um zip/instalador). |
| 2.7 | O token de redefinição fica no histórico do navegador (está na URL do link do e-mail). | **Baixo** | `src/web/rotas_conta.py:286-308` | Já mitigado com `no-store` + `no-referrer`; se quiser fechar, trocar o `GET` por um `POST` de confirmação com o token em campo oculto. |

---

## Etapa 3 — Race condition

Não há estoque, cupom, saldo, crédito, vaga nem convite. O recurso limitado deste produto é **o disco** (nome de arquivo é a chave de conteúdo) e **o arquivo de contas**. O banco não participa de nenhuma decisão ler-depois-gravar: só recebe `INSERT` com PK UUID em uma transação por análise.

### O que acontece se duas requisições iguais chegarem juntas

| # | Trecho (lê → decide → grava) | Duas requisições juntas | Proteção existente | Risco | Arquivo e linha |
|---|---|---|---|---|---|
| 3.1 | `guardar`: `if not os.path.exists(caminho)` → `open(caminho, "wb")` | As duas veem "não existe", as duas abrem o mesmo caminho em `wb` e escrevem concorrentes: **arquivo truncado ou intercalado**, e a análise depois lê lixo | **nenhuma** (não há `xb`, não há trava) | **Alto** | `src/ports/adaptadores.py:119-121` |
| 3.2 | `aposentar`: `_destino_livre` decide por `exists()` → `os.replace` executa depois | A segunda escolhe o **mesmo destino** (sobrescreve o aposentado) ou corre com a origem já movida e levanta `FileNotFoundError` → **500** | **nenhuma**; `os.replace` está fora de `try` | **Alto** | `src/ports/adaptadores.py:263-267`, `:270-286` |
| 3.3 | `guardar_com_substituicao`: foto da pasta → `guardar` → `aposentar` as versões anteriores | Dois envios do mesmo nome visível: cada um aposenta o arquivo do outro, e a lista pode terminar com a **versão antiga** e a nova aposentada — quebra a `RN-17` ("a lista fica com UMA versão") | **nenhuma** | **Alto** | `src/application/reenvio.py:62-77` |
| 3.4 | `garantir_dados_do_dono`: `exists(marcador)` → copia → grava marcador | Duas entradas simultâneas copiam duas vezes e gravam o marcador duas vezes; se o processo cair no meio, a pasta do dono fica com **arquivo pela metade** (`copy2` não é atômico) | Marcador atômico (`os.replace`) **só no fim** | **Médio** | `src/application/dono_inicial.py:52-53`, `:98`, `:107-119`, `:122-128` |
| 3.5 | `Limitador.exigir` + `registrar` (dois passos) | N threads passam na verificação antes de qualquer uma registrar: o limite de 5 vira ~5+N | `Lock` por operação, **não** por par verificar+registrar | **Médio** | `src/application/limite.py:67-86`, `src/application/cadastro.py:91-92`, `src/application/entrada_com_senha.py:66-77` |
| 3.6 | `ContasEmArquivo.criar`: `por_email` → `criar` | Cadastro concorrente do mesmo e-mail: serializado pelo `RLock`; a segunda chamada levanta `ContaDuplicada` **dentro** do repositório, e a rota traduz | `RLock` + escrita atômica (`mkstemp` → `fsync` → `os.replace`) | **Baixo** | `src/ports/contas_em_arquivo.py:62`, `:108-133`, `:136-145` |
| 3.7 | `ContasEmArquivo.consumir_token` | Duplo clique no link de confirmação: o `pop` + `_gravar` dentro da trava garante **um** consumo | `RLock` | **Baixo** | `src/ports/contas_em_arquivo.py:181-199` |
| 3.8 | `CacheDeArvores` (single-flight) | Quatro requisições na mesma árvore: uma parseia, as outras esperam o evento | `threading.Lock` + `Event` | **Baixo** | `src/ports/adaptadores.py:369`, `:409-459` |
| 3.9 | Exclusividade de instância | Duas instâncias na mesma porta: a segunda falha o `bind` | `SO_EXCLUSIVEADDRUSE` (Windows) / `SO_REUSEADDR=0` | **Baixo** (proteção boa) | `src/app.py:1077-1092` |

### Proteção que depende de lock em memória, e se o banco sozinho resolveria

| Proteção | Depende de | Sobrevive a reinício? | Vale entre processos? | O banco sozinho resolveria? |
|---|---|---|---|---|
| `Limitador` (tentativas) | `dict` + `Lock` no processo | **Não** — reiniciar zera, e o instalador reinicia a cada boot | **Não** | Sim: tabela `tentativa(escopo, chave, instante)` com índice e `INSERT`; ou um `UPDATE ... SET contador = contador + 1` atômico |
| `CacheDeArvores` | `dict` + `Lock` | Não (é cache, tudo bem) | Não | Não se aplica — é cache de CPU, não invariante |
| `ContasEmArquivo` | `RLock` + `os.replace` | Sim (o dado está no disco) | **Não** | Sim: `UNIQUE (email_normalizado)` no banco faria o trabalho que o `RLock` faz hoje |
| Exclusividade de instância | socket do SO | Não (mas o efeito é imediato) | **Sim** | Não precisa |
| Corridas de disco (3.1–3.4) | nada | — | — | **Não** — o problema é o sistema de arquivos, e a correção é `open(..., "xb")` / `os.rename` / trava por nome |

**Resposta curta:** o banco resolveria 3.5 e 3.6; **não** resolve 3.1–3.4, que são o risco alto desta etapa. O que resolve 3.1–3.4 é exclusividade de criação no próprio sistema de arquivos (`"xb"`, `os.replace`, `os.link`) mais uma trava por `(dono, nome visível)`.

---

## Etapa 4 — Idempotência

### Webhooks

**Não existem.** Zero ocorrências de `webhook` no repositório. Não há assinatura de corpo bruto a verificar, não há tabela de eventos processados, não há evento duplicado a tratar. Item **não aplicável** — e, se um dia entrar cobrança, o desenho terá de nascer com corpo bruto + `HMAC` + tabela `evento_processado(evento_id UNIQUE)`.

### Gateway de pagamento

**Não existe.** Sem Stripe, PagSeguro, Mercado Pago, Asaas. Não há `idempotency key` porque não há chamada de cobrança. Item **não aplicável**.

### O que existe de idempotência de verdade (e o que falta)

| # | Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|---|
| 4.1 | O `POST` de análise de DNA **não tem chave de idempotência**: duplo clique grava **duas** análises no banco e paga dois parses de ~50 s. | **Médio** | `src/app.py:541-654`, `src/application/dna_analysis.py:102`, `src/ports/adaptadores.py:601-614` | Token de formulário de uso único (nonce em `g`/sessão) e/ou `UNIQUE (owner_id, tree_ref, match_file_ref, root_name_input, created_at::date)` com `ON CONFLICT DO NOTHING`. |
| 4.2 | A confirmação de e-mail é idempotente **por consumo**: o segundo `GET` com o mesmo token devolve "link inválido". | Baixo (bom) | `src/ports/contas_em_arquivo.py:181-199` | — |
| 4.3 | `adotar()` é idempotente por construção (`UPDATE` condicionado ao dono anterior, segunda chamada devolve 0). | Baixo (bom) | `src/ports/adaptadores.py:566-591` | — |
| 4.4 | O upload é idempotente por conteúdo: mesma chave, não regrava. | Baixo (bom) | `src/ports/adaptadores.py:116-122` | — |
| 4.5 | O `GET /confirmar` **consome** o token: um scanner de e-mail que abra o link confirma a conta antes do dono. | Baixo (decisão declarada) | `src/core/token_de_uso_unico.py:11-17` | Se quiser blindar, espelhar o desenho da redefinição: `GET` só valida, `POST` consome. |
| 4.6 | `_acao_dna_analysis` audita e grava sem deduplicar; a auditoria registra as duas tentativas, mas o banco fica com duas análises. | **Médio** | `src/app.py:628-639` | Resolver junto com 4.1. |

---

## Etapa 5 — Separação de responsabilidades

### Arquivos mais longos (contagem medida)

| # | Arquivo | Linhas | O que ele mistura |
|---|---|---|---|
| 1 | `src/app.py` | **1131** | HTTP (21 `render_template`), despacho de ação, montagem de **todos** os adaptadores, configuração de sessão, boot, guarda de socket, fail-closed e servidor waitress |
| 2 | `src/core/cirurgia_do_grafo.py` | 838 | domínio puro — sem I/O, sem Flask, sem banco |
| 3 | `src/core/endogamia.py` | 800 | domínio puro |
| 4 | `src/ports/adaptadores.py` | **689** | três adaptadores no mesmo módulo: disco (arquivos), cache em memória e PostgreSQL |
| 5 | `src/ports/__init__.py` | 612 | 7 `Protocol` + 6 dataclasses de contrato num arquivo só |
| 6 | `src/core/relationship_hypotheses.py` | 566 | domínio puro |
| 7 | `src/reporting/mermaid_render.py` | 576 | formatação de diagrama |
| 8 | `src/core/validator.py` | 528 | domínio puro |
| 9 | `src/core/passo_por_kit.py` | 474 | domínio puro |
| 10 | `src/web/rotas_conta.py` | **419** | só HTTP, mas 6 rotas e ~25 literais de tela importados de uma vez |
| 11 | `src/core/genetic_evidence.py` | 406 | domínio puro |
| 12 | `src/core/evidence_comparison.py` | 393 | domínio puro |
| 13 | `src/reporting/visualizer.py` | 381 | DOT + Graphviz + `shutil.which` (borda de processo dentro de `reporting`) |

### Diagnóstico

Os cinco maiores arquivos de **domínio** são grandes, mas limpos: nenhum importa Flask, banco, SMTP ou disco. Tamanho ali é dívida de leitura, não mistura de responsabilidades.

O único arquivo que mistura **tela, regra e acesso a serviço externo** é `src/app.py`:

| Camada | O que está lá | Linha |
|---|---|---|
| Rota e despacho | `index()`, `_ACOES_PRE_ARVORE`, `_ACOES_COM_ARVORE` | `780-809` |
| Regra de apresentação | 21 `render_template`, mensagens de contrato no literal | `278`, `450`…`809` |
| Regra de negócio vazando | parsing de `promover` (`split("|", 2)`), decisão de 404 por dono, mensagem de substituição | `554-557`, `562-570`, `608-611` |
| Montagem de infraestrutura | `ArmazenamentoEmDisco`, `CarregadorDeArvoresGedcom`, `RegistroDeAnalisesPostgres`, `ContasEmArquivo`, `EmailPorSmtp`, `CacheDeArvores` | `217-274` |
| Boot e servidor | fail-closed, import tardio do waitress, socket exclusivo, `serve(...)` | `1022-1131` |

**Candidato nº 1: `src/app.py`.** Ele é, ao mesmo tempo, a borda HTTP, o *composition root*, o bootstrap do processo e o servidor. Por isso o P1 existe: o fail-closed mora no `__main__` de um arquivo que também é importado como biblioteca pela suíte e pelo harness de paridade, e a única saída encontrada foi "não recusar no `create_app`". Separar em três — `web/rotas_principais.py` (rotas e handlers), `borda.py` (montagem) e `__main__.py`/`servidor.py` (boot, socket, waitress) — resolve P1 e P4 de uma vez, porque o boot passa a ser o único lugar que decide "subo ou recuso", e a montagem passa a poder receber caminhos de dados em vez de derivá-los de `__file__`.

**Candidato nº 2: `src/ports/__init__.py`** (612 linhas, 7 Protocol + 6 dataclasses). Não é mistura de camadas, é um módulo-deus de contratos: toda mudança de porta toca o mesmo arquivo, e o `TYPE_CHECKING` de todo mundo aponta para cá.

**Candidato nº 3: `src/ports/adaptadores.py`** (689). Disco + cache + Postgres no mesmo módulo significa que uma mudança no adaptador de banco reconstrói o módulo que a suíte inteira importa para testar upload. Separar em `adaptadores_de_disco.py`, `cache_de_arvores.py` e `registro_postgres.py` é mecânico e reduz o blast radius.

### Achados da Etapa 5

| # | Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|---|
| 5.1 | `src/app.py` concentra borda HTTP + composição + boot + servidor, e é a razão de o fail-closed não poder morar em `create_app`. | **Médio** | `src/app.py:1-1131` (ver tabela acima) | Extrair `servidor.py` (boot/socket/waitress) e `borda.py` (montagem); a rota fica em `web/`. |
| 5.2 | `src/ports/__init__.py` é um módulo-deus de contratos. | **Baixo** | `src/ports/__init__.py:84-612` | Quebrar por área: `portas_de_arquivo.py`, `portas_de_identidade.py`, `portas_de_registro.py`. |
| 5.3 | `src/ports/adaptadores.py` mistura três adaptadores com dependências diferentes. | **Baixo** | `src/ports/adaptadores.py:65-689` | Separar em três módulos; nenhum ganho de comportamento, ganho de leitura e de cache de import. |
| 5.4 | Docstrings **desatualizadas** que afirmam o contrário do código: "`dono` não é usado para comportamento" e "nenhum isolamento entre donos é implementado". Hoje o dono escopa pasta, listagem, resolução e histórico. | **Baixo** | `src/application/upload_gedcom.py:75-79`, `src/application/path_search.py:51-52` | Corrigir os dois parágrafos — é a documentação que um agente vai ler antes de mexer no isolamento. |

---

## Etapa 6 — Distribuição por instalador (escopo novo desta rodada)

Não existe instalador no repositório: zero `.iss`, `.nsi`, `.wxs`, `.spec`; zero menção a "instalador" no README; zero `__version__` no código. O que dá para auditar é a **prontidão** — e ela tem quatro bloqueios duros.

| # | Achado | Risco | Arquivo e linha | Correção sugerida |
|---|---|---|---|---|
| 6.1 | **Não há modo "instalação local".** A identidade da 053 só monta com as cinco variáveis do Google. Sem elas: `/cadastro` e `/login` não existem (medido: 404) e o app sobe aberto. Com elas preenchidas por valor inventado: tudo monta (medido). | **Alto** | `src/app.py:243`, `:1005-1013`, `src/web/autenticacao.py:38-44` | Criar um modo explícito (`ANALISADOR_MODO=local`) que monte identidade local **sem** Google, com guarda ligada e sem rota `/callback`. |
| 6.2 | **Dados no diretório da instalação.** Uploads ancorados em `__file__`, logs na raiz do projeto, contas em `src/dados`. | **Alto** | `src/app.py:191-206`, `:251-262`, `src/utils/logs.py:198-208` | Resolver os três por variável de ambiente com padrão em `%LOCALAPPDATA%\<app>` (e `/dados` no container), mantendo as variáveis atuais como override. |
| 6.3 | **`os.makedirs` da pasta de upload no import, sem guarda.** Pasta não gravável → `PermissionError`, traceback, app não sobe. Reproduzido nesta rodada. | **Alto** | `src/app.py:209-211` | Envolver em `try/except OSError` com `SystemExit` de mensagem clara — ou, melhor, só criar a pasta na primeira escrita, depois de resolver o caminho gravável. |
| 6.4 | **Segredos por instalação inexistentes.** Só `ANALISADOR_SECRET_KEY` é gerada (`iniciar.ps1`). A senha do banco, a de SMTP e o client secret vêm prontos do `.env`/`.env.local` do desenvolvedor. | **Alto** | `iniciar.ps1:84-90`, `.env:14`, `.env.local:11`, `.env.local:20` | Gerar no instalador: `ANALISADOR_SECRET_KEY`, senha do Postgres (se embarcado) e um `sub` de dono inicial; nunca copiar `.env*`. |
| 6.5 | Não há versão do produto: "Adicionar ou remover programas" não tem o que mostrar, e não há como responder "que versão está instalada?". | **Médio** | busca por `__version__` em `src`: zero | `src/versao.py` (ou `importlib.metadata`) + carimbo no instalador + `GET /versao` para suporte. |
| 6.6 | O único caminho de atualização é `atualizar.ps1`, que exige **Docker** e `git` no PATH. | **Médio** | `atualizar.ps1:99-101`, `:105-111`, `:140` | Definir o canal de atualização do instalador (download de pacote assinado ou "baixe e rode de novo") antes de publicar; documentar o que acontece com uploads e contas. |
| 6.7 | Sem assinatura de código, o SmartScreen vai tratar o `.exe` como desconhecido. | **Médio** | não existe artefato para verificar | Certificado de assinatura (EV ou OV) e `signtool` no pipeline do instalador. |
| 6.8 | Não há desinstalação nem retenção declarada: uploads, `contas.json` e a trilha de auditoria (que por decisão **não** rotaciona, `src/utils/logs.py:8-15`) ficam na máquina para sempre. | **Médio** | `src/utils/logs.py:8-15`, `src/dados/contas.json` | Definir no instalador o que é removido, o que é preservado e por quanto tempo; a trilha de 90 dias é expurgo manual hoje. |
| 6.9 | Se o banco for embarcado, o modelo de dados atual não sustenta várias contas com privacidade real (ver 2.3): a separação existe na pasta, não no banco nem na ACL do Windows. | **Alto** | `init.sql:26`, `src/ports/adaptadores.py:77-91` | Para desktop de um usuário, declarar "um dono por máquina" e simplificar; para multiusuário, RLS + ACL por conta do Windows. |

### O que o instalador precisa decidir antes da primeira linha de código

1. **Um usuário por máquina ou vários?** Se for um, o P2/P3/6.1 encolhem (some a necessidade de login) e o produto fica mais simples. Se forem vários, o banco precisa do P2 da Etapa 2 **antes**.
2. **Postgres embarcado ou opcional?** Hoje o histórico é opcional por desenho (`RN-13`): sem banco a análise funciona. Um instalador que embarca Postgres cria uma dependência de serviço, backup e senha que o produto não tem hoje.
3. **Onde ficam os dados do usuário?** `%LOCALAPPDATA%` é o único caminho que funciona sob `Program Files` sem elevação (P4).
4. **Como atualiza?** Sem canal definido, cada versão é uma reinstalação manual e os dados ficam na máquina sem dono declarado.

---

## Não verificado (e por quê)

| Item | Por que não foi verificado |
|---|---|
| Instalador real (Inno Setup, NSIS, MSIX, PyInstaller) | Não existe no repositório. Não há artefato para auditar; auditei a **prontidão** do código (Etapa 6). |
| Assinatura de código e integridade do download | Não existe artefato publicado. |
| Comportamento sob `C:\Program Files\...` | Não executei um instalador. O que medi foi o efeito da pasta não gravável (P4) e li a ausência de guarda em `src/app.py:211`. |
| Postgres ao vivo (schema, índices, tempo de consulta) | `psycopg2` não está no `.venv` e `DATABASE_URL` não está definido; subir o banco seria "rodar migration", proibido nesta tarefa. |
| Envio SMTP real | Não há servidor SMTP de teste. O dublê substitui o transporte em todos os testes; a credencial real existe em `.env.local` e não foi usada. |
| Custo do scrypt `n=2^14` num PC modesto | Não medido nesta máquina. Importa para o instalador (login pode ficar lento), mas medir exigiria um alvo de referência que eu não tenho. |
| Política de retenção/expurgo da trilha de auditoria | É decisão de operação declarada (`src/utils/logs.py:13-15`), não há código de expurgo para auditar. |
| RLS/policies permissivas | Não existem policies — não há o que explicar além da ausência (Etapa 2). |

---

## Qual correção rodar primeiro, e por quê

**Rode o P1 primeiro — mas o P1 tem de incluir o P3.**

O P1 é o único achado que expõe dado **hoje**, e eu o medi nesta rodada em vez de deduzi-lo: sem as cinco variáveis, a aplicação responde `200` na tela principal, `404` em `/login` e executa o handler de upload sem sessão. Com o instalador, o entrypoint deixa de ser escolha de quem opera e passa a ser detalhe de empacotamento — e é justamente aí que o fail-closed do `__main__` deixa de valer.

Só que fechar o P1 sozinho troca "app aberto" por "app que não abre": a identidade local da 053 depende das cinco variáveis do Google (P3), então um `create_app` que recuse sem credencial recusaria **também** a instalação local que você quer distribuir. Por isso o primeiro prompt precisa ser um só, com dois critérios de pronto:

1. `create_app` (e não só o `__main__`) recusa subir sem um modo declarado — `ANALISADOR_MODO=local` ou `=google` —, com mensagem que diga o que falta;
2. `ANALISADOR_MODO=local` monta a identidade da 053 **sem** Google, liga a guarda e não registra `/callback`.

O que ele vai quebrar, e por isso precisa entrar no mesmo commit: `tests/test_sessao_e_guarda.py:80-88` **exige** hoje que sem autenticação a tela responda 200 — esse teste é a materialização do P1 e tem de ser reescrito junto, com um escape explícito de teste (`ANALISADOR_MODO_TESTE=1` no `tests/conftest.py`) para os 1939 testes que importam `src/app.py` sem credencial e sem banco.

**Na mesma passada, faça o P2** (tirar `src/dados/` do artefato + uma linha no `.dockerignore`): é a correção mais barata do relatório, e é a única cujo dano é irreversível — hash de senha e e-mail que saem num pacote não voltam.

**Depois:** P4 (caminhos graváveis — é o que faz o instalador abrir no cliente) → P5 (corridas de disco) → item 1.1 da Etapa 1 (banco de teste) → e só então a suíte vermelha e o CI (itens 1.3 e 1.5), que hoje são ruído de contrato e não risco de produto.
