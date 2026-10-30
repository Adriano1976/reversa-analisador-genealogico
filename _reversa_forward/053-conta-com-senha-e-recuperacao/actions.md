# Actions: cadastro com senha e e-mail confirmado, recuperação e a tela de entrada em verde

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Roadmap: `_reversa_forward/053-conta-com-senha-e-recuperacao/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 45 |
| Paralelizáveis (`[//]`) | 35 |
| Maior cadeia de dependência | 10 (T002 → T003 → T012 → T024 → T025 → T031 → T033 → T039 → T043 → T044) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar `dados/` ao `.gitignore` e o volume `./src/dados:/app/src/dados` ao serviço `app` do compose | - | `[//]` | `.gitignore`, `docker-compose.yml` | 🟢 | `[X]` |
| T002 | Criar `tests/fixtures/identidade.py` com os três dublês: `ContasEmMemoria` (implementação da porta, no molde de `ProvedorFalso`), `RelogioFalso` e `EmailQueGrava` | - | `[//]` | `tests/fixtures/identidade.py` | 🟢 | `[X]` |
| T003 | Acrescentar ao `tests/conftest.py` o fixture `app_com_contas`, que importa o módulo como os fixtures da 051 e injeta os três dublês em `create_app` | T002 | - | `tests/conftest.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever `tests/test_politica_de_senha.py`: cada exigência isolada (8, maiúscula, minúscula, dígito, especial), teto de 128, Unicode e a lista do que falta sem repetir a senha (`RN-02`) | - | `[//]` | `tests/test_politica_de_senha.py` | 🟢 | `[X]` |
| T005 | Escrever `tests/test_credencial.py`: derivação e verificação, sal diferente por conta, parâmetros gravados e relidos, senha errada, senha com acento e formato serializado (`RN-04`) | - | `[//]` | `tests/test_credencial.py` | 🟢 | `[X]` |
| T006 | Escrever `tests/test_token_de_uso_unico.py`: 32 bytes, hash guardado (nunca o texto), validade de 24 h e de 60 min, uso único e substituição do anterior (`RN-08`, `RN-19`) | - | `[//]` | `tests/test_token_de_uso_unico.py` | 🟢 | `[X]` |
| T007 | Escrever `tests/test_contas_em_arquivo.py`: criar e reler, e-mail normalizado único, `google_sub` único, arquivo ausente, duas criações simultâneas, cache por modificação e arquivo corrompido (`RNF-12`) | - | `[//]` | `tests/test_contas_em_arquivo.py` | 🟢 | `[X]` |
| T008 | Escrever `tests/test_cadastro_e_confirmacao.py`: política recusada, resposta idêntica para e-mail novo e existente, e-mail enviado, nenhuma sessão, confirmação pelo link, reenvio e limite (`RN-01`, `RN-07`, `RN-19`) | T003 | `[//]` | `tests/test_cadastro_e_confirmacao.py` | 🟢 | `[X]` |
| T009 | Escrever `tests/test_entrada_com_senha.py`: sucesso, senha errada, e-mail inexistente, conta não confirmada só revela depois da senha, mesmo caminho de comparação e limite (`RN-05`, `RN-10`, `RN-15`) | T003 | `[//]` | `tests/test_entrada_com_senha.py` | 🟢 | `[X]` |
| T010 | Escrever `tests/test_recuperacao_de_senha.py`: resposta genérica, envio só com credencial, 60 min, `GET` que não consome, `POST` que consome, política, incremento de versão e queda da sessão antiga (`RN-08`, `RN-09`, `RN-10`) | T003 | `[//]` | `tests/test_recuperacao_de_senha.py` | 🟢 | `[X]` |
| T011 | Escrever `tests/test_definir_senha.py`: exige sessão, define a primeira senha, preserva `sub`, recusa conta que já tem credencial (`RF-24`) | T003 | `[//]` | `tests/test_definir_senha.py` | 🟢 | `[X]` |
| T012 | Escrever `tests/test_vinculo_de_identidade.py`: Google anexa à conta local e confirma o e-mail, cadastro deslogado com e-mail existente não altera nada, linha de conta Google nasce uma vez e falha do repositório não derruba o login (`RN-20`) | T003 | `[//]` | `tests/test_vinculo_de_identidade.py` | 🟢 | `[X]` |
| T013 | Escrever `tests/test_sessao_com_versao.py`: guarda recusa sessão de versão anterior, aceita a atual e mantém `no-store` (`RN-10`, `RF-11`) | T003 | `[//]` | `tests/test_sessao_com_versao.py` | 🟢 | `[X]` |
| T014 | Escrever `tests/test_rotas_de_identidade.py`: lista de endpoints públicos, status de cada rota, recusa de origem cruzada, `no-store`, `no-referrer` nas páginas com token e os literais novos (`RN-13`, `RN-16`, `RN-17`) | T003 | `[//]` | `tests/test_rotas_de_identidade.py` | 🟢 | `[X]` |
| T015 | Atualizar `tests/test_tela_de_entrada.py` ao contrato novo: Google mais campos e links, `rel="icon"`, banner e as três frases de falha preservadas. Mudança declarada por `RN-17`, não ajuste para passar | T003 | `[//]` | `tests/test_tela_de_entrada.py` | 🟢 | `[X]` |
| T016 | Escrever `tests/test_dependencias_identidade.py` por AST: `core/` não importa framework, banco, correio nem `web/`/`ports/`; `web/rotas_conta.py` não importa `smtplib`; nenhum ciclo novo | - | `[//]` | `tests/test_dependencias_identidade.py` | 🟢 | `[X]` |
| T017 | Escrever `tests/test_auditoria_de_identidade.py`: as cinco ações novas no conjunto fechado e a linha sem e-mail, senha ou token (`RN-14`) | - | `[//]` | `tests/test_auditoria_de_identidade.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Implementar `src/core/conta.py`: `ContaDeAcesso`, `PoliticaDeSenha` (autoridade única), `Credencial` e `derivar_senha`/`conferir_senha` com `hashlib.scrypt` e `hmac.compare_digest`, sem I/O | T004, T005 | `[//]` | `src/core/conta.py` | 🟢 | `[X]` |
| T019 | Implementar `src/core/token_de_uso_unico.py`: `Token` congelado, emissão que devolve texto e registro, conferência em tempo constante e regras de validade por tipo | T006 | `[//]` | `src/core/token_de_uso_unico.py` | 🟡 | `[X]` |
| T020 | Declarar em `src/ports/__init__.py` os `Protocol` `RepositorioDeContas`, `TransporteDeEmail` e `Relogio`, com os tipos de payload que atravessam a fronteira | T018 | - | `src/ports/__init__.py` | 🟢 | `[X]` |
| T021 | Implementar `src/ports/contas_em_arquivo.py`: documento `{versao, contas, tokens}`, `RLock`, temporário mais `os.replace`, permissão restrita quando possível, cache por `(mtime_ns, tamanho)` e mapas derivados de e-mail e `google_sub` | T007, T020 | `[//]` | `src/ports/contas_em_arquivo.py` | 🟢 | `[X]` |
| T022 | Implementar `src/ports/email_smtp.py` com `smtplib` (import preguiçoso, 10 s, `starttls`/`ssl`/nenhuma) e `TransporteNulo` que levanta a falha tipada de envio não configurado | T020 | `[//]` | `src/ports/email_smtp.py` | 🟢 | `[X]` |
| T023 | Implementar `src/application/limite.py`: `Limitador` com `deque`, escopos da `RN-15` e `Relogio` injetado, mais o decorator `com_limite` | T009, T020 | `[//]` | `src/application/limite.py` | 🟡 | `[X]` |
| T024 | Implementar `src/application/vinculo.py`: `ao_entrar_com_google` e `definir_primeira_senha_na_conta`, sem nunca criar segunda conta nem mudar `sub` | T012, T020 | `[//]` | `src/application/vinculo.py` | 🟢 | `[X]` |
| T025 | Implementar `src/application/cadastro.py`: normalização, política, busca por e-mail, criação não confirmada, token e e-mail; resposta idêntica para conta nova e existente | T008, T018, T019, T020, T023, T024 | `[//]` | `src/application/cadastro.py` | 🟢 | `[X]` |
| T026 | Implementar `src/application/entrada_com_senha.py`: derivação falsa para e-mail inexistente, verificação em tempo constante, estado não confirmado só após a senha e sessão com versão | T009, T018, T020, T023 | `[//]` | `src/application/entrada_com_senha.py` | 🟢 | `[X]` |
| T027 | Implementar `src/application/recuperacao.py`: pedido, token de 60 min, redefinição com política, incremento de versão e encerramento da sessão | T010, T018, T019, T020 | `[//]` | `src/application/recuperacao.py` | 🟢 | `[X]` |
| T028 | Implementar `src/application/definir_senha.py`: primeira senha de conta autenticada, política aplicada e `sub` preservado | T011, T018, T020 | `[//]` | `src/application/definir_senha.py` | 🟢 | `[X]` |
| T029 | Implementar `src/application/sessao_da_conta.py`: verificador de versão que consulta a conta e devolve `False` para versão anterior | T013, T020 | `[//]` | `src/application/sessao_da_conta.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T030 | Alterar `src/web/sessao.py`: `Conta` ganha `versao`, `guardar_conta` grava, `instalar_guarda` recebe verificador e os endpoints públicos novos entram na lista fechada | T029, T013 | - | `src/web/sessao.py` | 🟢 | `[X]` |
| T031 | Criar `src/web/rotas_conta.py` com as seis rotas (`/cadastro`, `/confirmar`, `/reenviar-confirmacao`, `/recuperar-senha`, `/redefinir-senha`, `/definir-senha`), os cabeçalhos e a checagem de origem | T014, T025, T026, T027, T028 | - | `src/web/rotas_conta.py` | 🟢 | `[X]` |
| T032 | Alterar `src/web/rotas_auth.py`: `POST /login` autentica credencial local e o callback passa pelo vínculo antes de gravar a sessão | T024, T026 | `[//]` | `src/web/rotas_auth.py` | 🟢 | `[X]` |
| T033 | Alterar `src/app.py`: `create_app` recebe `contas`, `email` e `relogio`, monta os três, registra o Blueprint novo, avisa na subida sem SMTP e expõe `conta_tem_senha` ao template | T021, T022, T029, T031, T032 | - | `src/app.py` | 🟢 | `[X]` |
| T034 | Acrescentar as cinco ações ao conjunto fechado de `src/utils/auditoria.py` | T017 | `[//]` | `src/utils/auditoria.py` | 🟢 | `[X]` |
| T035 | Criar `src/templates/_entrada_base.html` e reescrever `src/templates/login.html` sobre ela: cartão, banner no topo, Google primeiro, campos, botão verde, links e `rel="icon"` | T031 | `[//]` | `src/templates/_entrada_base.html`, `src/templates/login.html` | 🟢 | `[X]` |
| T036 | Criar `src/templates/cadastro.html` e `src/templates/recuperar_senha.html` sobre a base, com a política visível e a frase do Google na recuperação | T031 | `[//]` | `src/templates/cadastro.html`, `src/templates/recuperar_senha.html` | 🟢 | `[X]` |
| T037 | Criar `src/templates/redefinir_senha.html`, `src/templates/definir_senha.html` e `src/templates/mensagem.html` sobre a base | T031 | `[//]` | `src/templates/redefinir_senha.html`, `src/templates/definir_senha.html`, `src/templates/mensagem.html` | 🟢 | `[X]` |
| T038 | Acrescentar a `src/assets/app.css` o bloco do cartão de entrada: campos, botão verde, links, dica da política e estados de mensagem, em tema claro e escuro | T035 | - | `src/assets/app.css` | 🟡 | `[X]` |
| T039 | Acrescentar o link `Definir senha` à masthead de `src/templates/index.html`, sob `conta_tem_senha`, sem tocar em `SHA_DA_TELA` | T033 | - | `src/templates/index.html` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T040 | Documentar no `README.md` a identidade local: variáveis SMTP, caminho do arquivo de contas, volume no compose e o aviso de que sem SMTP o cadastro não conclui | T033 | `[//]` | `README.md` | 🟢 | `[X]` |
| T041 | Varrer os literais de tela: os 36 anteriores (29 mais os 7 da 051) intactos e os novos catalogados em `RN-13` | T035, T036, T037 | `[//]` | `src/templates/` | 🟢 | `[X]` |
| T042 | Medir e registrar três números: custo de `derivar_senha` no `.venv`, custo da verificação de versão com cache quente e tamanho do arquivo com 1, 10 e 100 contas | T033 | `[//]` | `tests/` | 🟡 | `[X]` |
| T043 | Rodar a suíte completa e a paridade; registrar marco, divergências e veredito, sem ajustar teste existente para passar | T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T042 | - | `tests/` | 🟢 | `[X]` |
| T044 | Atestar os invariantes no mesmo commit: `requirements.txt` inalterado, `SHA_DA_TELA` inalterado e `tests/test_combobox_de_nomes.py` intocado | T043 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |
| T045 | Gerar `regression-watch.md` da feature com os itens de vigilância e o marco da suíte | T043 | - | `_reversa_forward/053-conta-com-senha-e-recuperacao/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

**Marco de 2026-10-30.** Suíte: **1.908 passam / 9 pulados / 5 falham** em 1.922 coletados. As cinco
falhas são exatamente as pré-existentes da linha de base — quatro de `test_characterization_mermaid` e uma
de `test_tres_fases_da_tela.py` (literal `1. Lista de Matches (CSV)`) —, nenhuma relacionada a esta
feature. São **107 testes novos** sobre a linha de base da 052.

**Paridade:** **30 divergências**, o mesmo número da linha de base de 049/050/051. Nenhuma divergência nova;
o instrumento rodou por `tests/rodar_paridade.py`, que isola a pasta de uploads.

**Medições (T042):**

| Medida | Valor |
|---|---|
| `derivar_senha` com `n=2**14` | 149–200 ms por verificação (alvo de até 250 ms) |
| Arquivo com 1 conta | 0,7 KB |
| Arquivo com 10 contas | 6,5 KB |
| Arquivo com 100 contas | 65,2 KB |
| 1.000 leituras com cache quente | 250 ms (0,25 ms por leitura) |

**Desvios declarados do plano:**

1. `Limitador` ficou como colaborador (`exigir`/`registrar`), e não como o decorator `com_limite` do
   `D-13`: as views do Flask não recebem argumentos de onde derivar a chave, e o decorator só funcionaria
   com uma indireção que esconderia a regra. O efeito é o mesmo — o contador continua fora do caso de uso.
2. Dois módulos de apoio não listados no plano: `web/origem.py` (checagem de origem compartilhada por
   `rotas_auth` e `rotas_conta`) e `web/textos_de_conta.py` (literais da `RN-13` em um lugar só). Nenhum
   muda contrato externo.
3. As exceções de conta moram em `core/conta.py`, não em um `core/erros_de_conta.py`: o módulo do domínio
   é a autoridade, e separar a exceção da regra que a levanta criaria dois lugares para a mesma coisa.
4. `token_vigente` foi acrescentado à porta `RepositorioDeContas` durante a execução: sem ele, o
   `GET /redefinir-senha` não distingue link válido de vencido sem consumir o token.
5. `ServicoDeDefinirSenha.ja_tem_senha` e `ServicoDeRecuperacao.link_valido` nasceram como métodos dos
   casos de uso, para a rota não importar o repositório diretamente.

**Invariantes:** `requirements.txt` sem alteração; `SHA_DA_TELA` sem alteração;
`tests/test_combobox_de_nomes.py` intocado; `tests/test_tela_de_entrada.py` atualizado por mudança
declarada de contrato (`RN-17`), e não por ajuste para passar.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-30 | Versão inicial gerada por `/reversa-to-do` a partir do `roadmap.md` com 18 decisões, do `data-delta.md` e da interface `entrada-e-senha.md` | reversa |
| 2026-10-30 | Execução de `/reversa-coding`: 45 de 45 ações concluídas; suíte 1.908/9/5 (5 pré-existentes) e paridade com 30 divergências, o mesmo número da linha de base | reversa |
| 2026-10-30 | Emendas `E001` a `E003` (pós-entrega): degradação da falha de armazenamento, alinhamento do botão do Google e repasse das variáveis de SMTP no compose e no lançador | reversa |
| 2026-10-30 | Emenda `E004` (pós-entrega): botão de mostrar/esconder senha nos quatro formulários, com aprimoramento progressivo e `RN-22` | reversa |
| 2026-10-30 | Emenda `E005` (pós-entrega): favicon transparente em `/favicon.png` para as abas, mantendo o ícone de atalho opaco | reversa |
| 2026-10-30 | Emenda `E006` (pós-entrega): alternância de senha no tipo do `bootstrap-show-password-toggle`, com ícone no campo e botão vazio sobreposto | reversa |

## Emendas

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| E001 | Falha de armazenamento na identidade vira mensagem e linha de log, nunca `500`: as rotas de cadastro, confirmação, reenvio, recuperação, redefinição, definição e o `POST /login` capturam `OSError` e `ArquivoDeContasCorrompido`, registram a causa e respondem a frase própria | - | - | `src/web/rotas_conta.py`, `src/web/rotas_auth.py`, `tests/test_falha_de_armazenamento.py` | 🟢 | `[X]` |
| E002 | Alinhar o botão "Entrar com Google" ao botão "Entrar": a regra global `.d-grid > .btn` devolvia largura natural no desktop, e os dois botões terminavam em pontos diferentes | - | - | `src/assets/app.css` | 🟢 | `[X]` |
| E003 | Repassar `ANALISADOR_SMTP_*` ao contêiner no compose e documentá-las no modelo do `iniciar.ps1`, com aviso no terminal quando `HOST`/`REMETENTE` faltarem | - | - | `docker-compose.yml`, `iniciar.ps1` | 🟢 | `[X]` |
| E004 | Alternância de visibilidade nos campos de senha: botão `Mostrar`/`Esconder` dentro do `input-group`, nascendo `hidden` para o formulário seguir funcionando sem JavaScript (`RF-18`), com `aria-pressed` e rótulo que acompanha o estado | - | - | `src/templates/_campo_de_senha.html`, `src/templates/_entrada_base.html`, `src/templates/login.html`, `src/templates/cadastro.html`, `src/templates/redefinir_senha.html`, `src/templates/definir_senha.html`, `src/assets/app.css`, `tests/test_alternar_senha.py` | 🟢 | `[X]` |
| E005 | Favicon transparente para a aba do navegador nas telas de identidade: derivada 128×128 com alfa da mesma arte canônica, servida em `/favicon.png`; o ícone de atalho opaco continua em `/apple-touch-icon.png` | - | - | `src/assets/favicon.png`, `tests/favicon_da_aba.py`, `src/web/rotas_assets.py`, `src/app.py`, `src/web/sessao.py`, `src/templates/_entrada_base.html`, `tests/test_favicon_da_aba.py` | 🟢 | `[X]` |
| E006 | Alternância de senha no tipo do `coliff/bootstrap-show-password-toggle`: ícone de olho como `background-image` do campo, botão vazio e invisível sobreposto, revelado no primeiro foco, com `aria-pressed` e rótulo alternando | E004 | - | `src/templates/_campo_de_senha.html`, `src/templates/_entrada_base.html`, `src/assets/app.css`, `tests/test_alternar_senha.py`, `_reversa_forward/053-conta-com-senha-e-recuperacao/onboarding.md` | 🟢 | `[X]` |
