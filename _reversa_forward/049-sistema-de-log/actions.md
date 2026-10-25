# Actions: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Roadmap: `_reversa_forward/049-sistema-de-log/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 24 |
| Paralelizáveis (`[//]`) | 11 |
| Maior cadeia de dependência | 7 (T001 → T003 → T016 → T018 → T020 → T023 → T024) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar os módulos da feature com as constantes de ambiente e nome de arquivo, e resolver a pasta de log ancorada na raiz do projeto com `ANALISADOR_LOG_DIR` de sobrescrita: `logs/` na raiz, o mesmo caminho que o volume do compose publica | - | - | `src/utils/logs.py` | 🟢 | `[X]` |
| T002 | Implementar `configurar()` idempotente: console, arquivo geral rotativo (5 × 5 MB) e logger `auditoria` com `propagate=False`; nível por `ANALISADOR_LOG_LEVEL` e ajuste por módulo; linha de acesso do `waitress` sobe para `WARNING`; pasta inescrevível degrada para console com um aviso | T001 | - | `src/utils/logs.py` | 🟡 | `[X]` |
| T003 | Implementar o identificador de requisição: `novo_identificador()`, `identificador_atual()` e o filtro que injeta o valor em cada registro | T001 | - | `src/utils/logs.py` | 🟡 | `[X]` |
| T004 | Implementar a máscara de privacidade para texto de mensagem e argumentos: identificador de kit (`[A-Z]{2}\d{7}`) e endereço de e-mail | T001 | - | `src/utils/logs.py` | 🟡 | `[X]` |
| T005 | Estender a máscara ao **traceback**: materializar `exc_text` já mascarado e zerar `exc_info` para o formatador não reformatar a exceção crua | T004 | - | `src/utils/logs.py` | 🟡 | `[X]` |
| T006 | Implementar o medidor nomeado `medir(nome)`, que registra a duração em milissegundos ao sair do bloco | T001 | - | `src/utils/logs.py` | 🟢 | `[X]` |
| T007 | Isolar a pasta de log na suíte: fixture autouse de sessão apontando `ANALISADOR_LOG_DIR` para a pasta temporária, mais teste que falha se `logs/` nascer na raiz do repositório | T001 | - | `tests/conftest.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Testar a configuração: chamar `configurar()` duas vezes não duplica handler; a linha de auditoria não aparece no arquivo geral; nível por módulo muda só aquele módulo | T002 | `[//]` | `tests/test_configuracao_de_log.py` | 🟡 | `[X]` |
| T009 | Testar o identificador: toda resposta traz `X-Request-ID`; duas requisições têm valores diferentes; valor enviado pelo cliente é ignorado; a linha de acesso traz o mesmo valor | T003 | `[//]` | `tests/test_identificador_de_requisicao.py` | 🟡 | `[X]` |
| T010 | Testar a privacidade: máscara em mensagem **e** em traceback, e a análise com fixture sintética sem nenhum nome no log capturado | T005 | `[//]` | `tests/test_privacidade_do_log.py` | 🟢 | `[X]` |
| T011 | Testar a auditoria: aposentar com sucesso e com falha (duas linhas, desfechos distintos); envio novo, idêntico e substituído (três desfechos); análise com contagens; e a linha sem o rótulo visível do arquivo | T013 | `[//]` | `tests/test_registro_de_auditoria.py` | 🟢 | `[X]` |
| T012 | Testar a medição: a linha nomeia a etapa, traz duração em milissegundos e não carrega dado pessoal | T006 | `[//]` | `tests/test_medicao_da_carga.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Criar o módulo de auditoria: conjunto fechado de ações, montagem da linha com desfecho, chave de conteúdo mais extensão (via `decompor_nome_armazenado`), contagens numéricas, IP e identificador, e a emissão no logger `auditoria` | T001, T003 | `[//]` | `src/utils/auditoria.py` | 🟢 | `[X]` |
| T014 | Acrescentar o campo `desfecho` a `ResultadoDeUpload` e devolvê-lo no retorno do caso de uso, sem tocar nas três mensagens | - | `[//]` | `src/application/upload_gedcom.py` | 🟢 | `[X]` |
| T015 | Instrumentar o parse com `with medir("carregar_arvore")` em `CarregadorDeArvoresGedcom.carregar`, no ponto único onde a carga acontece | T006 | `[//]` | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T016 | Criar a fiação Flask: `instalar(aplicacao)` com `before_request` (novo identificador), `after_request` (cabeçalho `X-Request-ID` **antes** de qualquer resposta, inclusive as de erro) e a linha de acesso com método, rota, situação e duração | T003, T002 | `[//]` | `src/web/hooks_de_registro.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Auditar os cinco fluxos na borda: envio de GEDCOM (com `desfecho`), análise de DNA (contagens de resultados e descartados), busca de caminho (desfecho e meioses) e as **duas** tentativas de aposentar | T013, T014 | - | `src/app.py` | 🟢 | `[X]` |
| T018 | Chamar `configurar()` e `instalar()` em `create_app()`, mantendo a criação da instância de módulo no fim do arquivo | T002, T016 | - | `src/app.py` | 🟡 | `[X]` |
| T019 | Trocar o `print` de inicialização por linha `INFO` no logger do módulo, com o mesmo texto de endereço e threads | T018 | - | `src/app.py` | 🟢 | `[X]` |
| T020 | Trocar o `{e}` das três mensagens por "O detalhe foi registrado no log.", preservando cada prefixo; conferir se algum golden de tela captura os três textos e atualizá-lo se capturar | T018 | - | `src/app.py` | 🟢 | `[X]` |
| T021 | Publicar a pasta de auditoria no compose (volume `./logs`) e declarar a rotação `json-file` 5 × 5 MB no serviço da aplicação | T002 | `[//]` | `docker-compose.yml` | 🟢 | `[X]` |
| T022 | Acrescentar a linha da pasta de log no `.gitignore` — **BLOQUEADA POR POLÍTICA**: o caminho não está no `allowedPaths` de `.reversa/reversa-config.json`; sem liberação do operador a escrita é recusada | - | `[//]` | `.gitignore` | 🟢 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Rodar a suíte completa e a paridade, e registrar os números medidos (passam, pulados, falham, paridade) sem ajustar teste para passar | T017, T018, T019, T020, T021 | - | `tests/` | 🟢 | `[X]` |
| T024 | Escrever a decisão de observabilidade (ADR-37) no acervo de decisões da extração, citando esta feature e as decisões D-01 a D-14 | T023 | - | `_reversa_sdd/adrs/37-observabilidade-em-camadas.md` | 🟢 | `[X]` |

## Notas de execução

1. **Os testes da Fase 2 são escritos antes do alvo (TDD).** T009, T010, T011 e T012 nascem
   vermelhos e ficam verdes quando T016/T017/T018/T015 entram. Isso é o Princípio III em prática, e
   não uma falha de sequenciamento: o `actions.md` lista os testes na fase em que eles são escritos.
2. **Idempotência de `configurar()` não pode ser um booleano de módulo.** Medido na leitura do
   `tests/conftest.py`: o fixture `cliente_de_upload` reexecuta `src/app.py` com `exec_module` a cada
   uso (`conftest.py:170-174`), o que cria **novo namespace de módulo** a cada vez. O registro de
   handlers, porém, é global do processo `logging`. A guarda tem de ser **marcador no próprio
   handler** já instalado no destino, e não uma flag `_CONFIGURADO`.
3. **A pasta de log não pode nascer dentro de `src/`.** A resolução é a **raiz do projeto** (`logs/`),
   que é o caminho que o `.gitignore` cobre e que o volume `./logs:/app/logs` publica. T007 existe
   para a suíte não escrever na raiz durante os testes.
4. **T022 é a única ação bloqueada por política**, e não por código: `.gitignore` fora do
   `allowedPaths`. Se o operador não liberar antes do coding, a ação fica aberta com este motivo
   registrado e a feature segue sem ela, porque `.dockerignore` (lista de permissão) já exclui a
   pasta do contexto de build.
5. **Nada desta feature toca `src/application/traducao.py`.** Aquelas mensagens de erro de domínio
   têm par (mensagem, status) fixado por teste de igualdade (`T024` de `test_traducao_de_erros.py`) e
   continuam valendo; a máscara, ali, é só de log.
6. **Critério de `[//]`:** mesma fase, arquivo alvo distinto e nenhuma dependência entre si. É por
   isso que a Fase 1 não tem nenhuma marca — os quatro módulos são o **mesmo** arquivo
   (`src/utils/logs.py`) e escrevem um sobre o outro —, e a Fase 4 também não tem nenhuma entre
   T017 e T020, que editam todos `src/app.py`.

### Registros da execução

- **T007 mudou de plano no meio.** O `actions.md` previa uma *fixture* autouse; a leitura do
  `conftest.py` mostrou que vários módulos importam `src/app.py` **no nível do módulo**, antes de
  qualquer fixture — e o `configurar()` cria a pasta no primeiro import. A isolação passou a ser
  feita no **import do `conftest`** (`os.environ.setdefault`), que o pytest executa antes de coletar.
  O mesmo desvio entrou no involucro da paridade (`tests/rodar_paridade.py`), pelo mesmo mecanismo
  que ele já usava para isolar a pasta de upload.
- **Medição da suíte:** `1684 passed, 9 skipped, 0 failed` em 164,54 s — exatamente as 1656 do marco
  mais os 28 testes novos.
- **Paridade:** 30 divergências em `ancestral`, **medidas como pré-existentes** — o mesmo resultado
  foi obtido em um checkout limpo do `HEAD` (`344bfbd`), sem uma linha desta feature. Fica para o
  `/reversa-audit`; não é regressão da 049.
- **T022 recusada pela política** de edição do legado (`allowLegacyEdits: true` com `.gitignore`
  fora do `allowedPaths`).

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-25 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-25 | Execução do `/reversa-coding`: 23 de 24 ações fechadas; T022 recusada por política | reversa |
