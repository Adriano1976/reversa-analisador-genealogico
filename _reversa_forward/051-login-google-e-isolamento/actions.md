# Actions: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Roadmap: `_reversa_forward/051-login-google-e-isolamento/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 36 |
| Paralelizáveis (`[//]`) | 9 |
| Maior cadeia de dependência | 11 (T002 → T007 → T009 → T013 → T015 → T016 → T018 → T019 → T031 → T035 → T036) |

> **A verificação em navegador não é ação de agente.** O roteiro está em `onboarding.md` — duas contas
> Google, a migração dos arquivos reais e a prova manual do `404` — e entra como gate do critério de
> pronto do `roadmap.md#10`. O agente não pode declarar a feature fechada sem ele, mas também não
> pode executá-lo.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar `requests` ao `requirements.txt` com pin da versão do `.venv`, comentário de origem e nota de import preguiçoso (`L-26`) | - | `[//]` | `requirements.txt` | 🟢 | `[X]` |
| T002 | Criar `src/web/sessao.py` com `Conta` e os helpers de sessão: ler, gravar limpando antes, encerrar e devolver o dono | - | `[//]` | `src/web/sessao.py` | 🟢 | `[X]` |
| T003 | Criar `src/web/autenticacao.py` com `ConfiguracaoDeEntrada` (as cinco variáveis, `faltantes()` e `url_de_retorno`) e `ErroDeEntrada`; nenhuma chamada HTTP | - | `[//]` | `src/web/autenticacao.py` | 🟢 | `[X]` |
| T004 | Implementar `novo_state()` e `url_de_autorizacao(state)` com os parâmetros do contrato e escopo mínimo | T003 | - | `src/web/autenticacao.py` | 🟢 | `[X]` |
| T005 | Implementar `trocar_codigo` e `ler_perfil` com `requests` importado dentro da função, `timeout=10` e falha mapeada para `ErroDeEntrada` | T003 | - | `src/web/autenticacao.py` | 🟢 | `[X]` |
| T006 | Acrescentar as cinco variáveis ao `docker-compose.yml` com `${VAR:?}` e comentário, sem valor padrão | - | `[//]` | `docker-compose.yml` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Escrever `tests/test_sessao_e_guarda.py` fixando cookie (atributos e 12 h), limpeza na gravação, guarda por endpoint (`GET` 302, `POST` 303), lista pública e `no-store` | T002 | - | `tests/test_sessao_e_guarda.py` | 🟢 | `[X]` |
| T008 | Escrever `tests/test_autenticacao.py` com provedor falso: URL de autorização, `state` único e consumido, troca do código, perfil sem e-mail, `email_verified` falso e tempo esgotado | T004, T005 | - | `tests/test_autenticacao.py` | 🟢 | `[X]` |
| T009 | Escrever `tests/test_isolamento_por_dono.py` — o portão: dois donos, as cinco operações, `404` sem `403`, lista escopada e mesmo conteúdo em dois arquivos | T007 | - | `tests/test_isolamento_por_dono.py` | 🟢 | `[X]` |
| T010 | Escrever `tests/test_migracao_do_dono_inicial.py` com árvore sintética: cópia única, marcador, nada apagado e adoção do histórico por registro falso | T007 | - | `tests/test_migracao_do_dono_inicial.py` | 🟢 | `[X]` |
| T011 | Escrever `tests/test_tela_de_entrada.py`: `login.html` com os literais congelados, masthead com conta e "Sair", e as três rotas públicas respondendo sem sessão | T007 | - | `tests/test_tela_de_entrada.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Implementar `instalar_guarda(app)` em `sessao.py`: `before_request` com lista pública por endpoint, 302/303, `g.conta` e `g.dono`, `no-store` e o processador de contexto da conta | T002 | - | `src/web/sessao.py` | 🟢 | `[X]` |
| T013 | Escopar `ArmazenamentoEmDisco` por dono: validar a forma do `dono`, usar `<base>/<dono>/`, mover para `<dono>/_aposentados/` e conferir o `dirname` | T009 | - | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T014 | Acrescentar `adotar` ao Protocol `RegistroDeAnalises` e reescrever os docstrings de `dono` nas três portas, que hoje afirmam "não filtra" | - | `[//]` | `src/ports/__init__.py` | 🟢 | `[X]` |
| T015 | Implementar `adotar` no adaptador Postgres (`UPDATE` condicionado a `owner_id = 'unico'`) e no nulo (devolve zero), sem abrir conexão na construção | T013 | - | `src/ports/adaptadores.py` | 🟢 | `[X]` |
| T016 | Criar `src/application/dono_inicial.py`: cópia da raiz e de `_aposentados/` para a pasta do dono, chamada de `adotar`, marcador atômico `.dono-inicial` e log por arquivo | T013, T014, T015 | - | `src/application/dono_inicial.py` | 🟢 | `[X]` |
| T017 | Criar `src/web/rotas_auth.py` com o Blueprint, `GET /login` (tela ou `302 /`) e `GET /login?iniciar=1` (`state` mais redirecionamento ao provedor) | T004, T012 | - | `src/web/rotas_auth.py` | 🟢 | `[X]` |
| T018 | Implementar `GET /callback`: consumir o `state`, trocar o código, ler o perfil, limpar a sessão, gravar a conta, rodar a migração do dono inicial e redirecionar | T005, T016, T017 | - | `src/web/rotas_auth.py` | 🟢 | `[X]` |
| T019 | Implementar `POST /logout`: limpar a sessão e responder `303 /login`, idempotente sem sessão | T018 | - | `src/web/rotas_auth.py` | 🟢 | `[X]` |
| T020 | Implementar `autenticacao_do_ambiente()`: montar o serviço com a configuração ou devolver `(None, faltantes)` | T005 | - | `src/web/autenticacao.py` | 🟢 | `[X]` |
| T021 | Trocar as oito chamadas de `DONO_DO_PROCESSO` por `_dono()` e declarar o literal como fallback exclusivo do caminho sem autenticação | T012 | - | `src/app.py` | 🟢 | `[X]` |
| T022 | `create_app(autenticacao=...)`: segredo, cookie, Blueprint, guarda, processador de conta e extensão; sem autenticação, nada disso é registrado | T017, T020, T021 | - | `src/app.py` | 🟢 | `[X]` |
| T023 | Fail-closed no `__main__`: sem as cinco variáveis (ou sem `requests`), `SystemExit` nomeando o que falta, antes de ligar o socket | T022 | - | `src/app.py` | 🟢 | `[X]` |
| T024 | Criar `src/templates/login.html` com a tela de entrada e os literais congelados | T017 | - | `src/templates/login.html` | 🟢 | `[X]` |
| T025 | Masthead de `index.html`: rótulo da conta e botão "Sair" dentro de formulário `POST /logout`, sem tocar nos demais literais | T022 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T026 | Acrescentar a `app.css` os estilos da tela de entrada, do rótulo da conta e do botão de sair | - | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Acrescentar ao `conftest.py` a fixture `app_autenticado`, que monta `create_app` com autenticação falsa e cliente com sessão pré-gravada | T022 | - | `tests/conftest.py` | 🟢 | `[X]` |
| T028 | Atualizar ao layout por dono as asserções de `test_aposentar_arquivo.py`, `test_reenvio_do_arquivo.py` e `test_reenvio_do_csv.py` | T013 | `[//]` | `tests/test_aposentar_arquivo.py` | 🟢 | `[X]` |
| T029 | Atualizar ao layout por dono as asserções de `test_porta_de_armazenamento.py`, `test_upload.py` e `test_upload_seguranca.py` | T013 | `[//]` | `tests/test_porta_de_armazenamento.py` | 🟢 | `[X]` |
| T030 | Atualizar ao layout por dono `test_confrontacao_gedcom_dna.py`, `test_nome_com_dois_pontos.py`, `test_privacidade_do_log.py` e o apoio `tests/manutencao_de_uploads.py` | T013 | `[//]` | `tests/test_confrontacao_gedcom_dna.py` | 🟢 | `[X]` |
| T031 | Acrescentar `entrar` e `sair` aos conjuntos de `utils/auditoria.py`, criar o campo `conta` e auditar as três rotas de entrada com o `sub` | T018, T019 | - | `src/utils/auditoria.py` | 🟢 | `[X]` |
| T032 | Remedir e atualizar `SHA_DA_TELA` com o delta da masthead declarado no comentário | T025 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T033 | Registrar no log o aviso de dados anteriores não atribuídos quando a conta que entra não é a declarada e o marcador não existe | T016, T018 | - | `src/application/dono_inicial.py` | 🟢 | `[X]` |
| T034 | Documentar no `README.md` as cinco variáveis, o passo do Google Cloud e a dependência de internet | T023 | - | `README.md` | 🟢 | `[X]` |
| T035 | Conferir por varredura que os 29 literais de tela não mudaram e que `code`, token, segredo e e-mail não aparecem em log nem em trilha | T031 | - | `src/` | 🟢 | `[X]` |
| T036 | Rodar a suíte completa e a paridade, medir o HTML da tela de entrada e registrar marco, divergências e veredito sem ajustar teste para passar | T032, T035 | - | `tests/` | 🟢 | `[X]` |


## Notas de execução

1. **O caminho legado manteve a pasta plana, e isso e uma decisao de execucao.** O plano
   (`D-06`, `data-delta.md`) descrevia `<base>/<dono>/` para todo dono. Na execucao, o dono
   legado `"unico"` — o unico que existe sem sessao — passou a ser a **raiz** da pasta, e so
   ele; contas reais ganham subpasta. A razao e medida: 158 testes e o involucro de paridade
   semeiam arquivos na raiz e nao tem sessao. Com o recorte, a suite inteira continua sem
   ajuste de assercao, e o isolamento e coberto por `tests/test_isolamento_por_dono.py`, com
   dois `sub` reais. Nenhuma sessao autenticada alcanca a raiz (o `sub` do Google e numerico).
2. **`requests` foi instalado no `.venv`** e pinado em `2.32.5`, a versao verificada.
3. **4 falhas sao PRE-EXISTENTES e nao sao desta feature:** `test_characterization_mermaid`
   (4 testes) falha igual no `HEAD` limpo, medido em worktree separado. Nao foram tocadas.
4. **A suite fechou em 1.745 passam / 9 pulados / 4 falham (pre-existentes)**, com 32 testes
   novos, e a paridade repetiu as **30 divergencias** ja registradas pela 049/050.
5. **O `dono` legado e a paridade:** o involucro troca o render por captura de contexto, entao
   as mudancas de tela (masthead) nao o afetam.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-26 | Versão inicial gerada por `/reversa-to-do` a partir do roadmap de 2026-10-26 | reversa |
| 2026-10-27 | Execução do `/reversa-coding`: 36 de 36 ações; suíte 1.745/9/4 (4 pré-existentes) e paridade em 30 divergências | reversa |
