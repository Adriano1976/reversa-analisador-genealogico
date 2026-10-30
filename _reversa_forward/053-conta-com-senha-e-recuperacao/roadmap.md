# Roadmap: cadastro com senha e e-mail confirmado, recuperação e a tela de entrada em verde

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Requirements: `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A identidade local entra como **quatro casos de uso** na fronteira de aplicação — cadastro/confirmação, entrada com senha, recuperação/redefinição e definição de senha autenticada —, servidos por um Blueprint novo (`web/rotas_conta.py`) ao lado do `auth_bp` da 051. Duas portas novas sustentam tudo: `RepositorioDeContas`, cujo primeiro adaptador é um arquivo JSON com escrita atômica e trava, e `TransporteDeEmail`, cujo adaptador é SMTP da biblioteca padrão e cuja ausência vira um objeto nulo que não derruba a subida. O núcleo ganha `core/conta.py` (conta, política de senha, credencial e comparação em tempo constante) e `core/token_de_uso_unico.py` (emissão, expiração e consumo), ambos puros. A sessão da 051 ganha a **versão de credencial**, conferida pela guarda por um verificador injetado. A unificação de identidade é uma regra única, aplicada no retorno do Google e na definição de senha autenticada, e **nunca** pelo cadastro deslogado. A tela de entrada vira uma base de cartão com cinco páginas, no verde do app, com o banner na posição atual e o ícone da aba reusando a rota da 009. Nenhuma dependência, tabela ou migração de esquema nova.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | E-mail e senha de teste são sintéticos; o arquivo de contas fica fora do Git pelo mesmo padrão de `src/uploads/`; e-mail, senha e token nunca entram em log nem em auditoria | respeita |
| II. Comportamento observável é preservado em refatoração | A feature muda a tela de entrada de forma declarada (`RN-17`) e não toca em análise, busca, listas nem no fluxo Google; `SHA_DA_TELA` mede `GET /` com pasta vazia, não a tela de entrada | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada `RF` tem teste nomeado no `actions.md`; pré-sequestro, token de uso único, revogação de sessão e concorrência do arquivo são portões | respeita |
| IV. Arestas do grafo são tipadas | Nenhum fluxo de genealogia é tocado; a conta é identidade de acesso, não aresta | respeita (não se aplica) |
| V. Toda suposição de genealogia genética cita a fonte | Nenhuma faixa de cM, MRCA ou heurística nova | respeita (não se aplica) |

Nenhum conflito: nenhum princípio precisa ser atenuado ou reescrito. O único ponto sensível é o princípio I, e ele é atendido **por construção** — o e-mail do titular é dado pessoal e não sai da conta, nem em log, nem na auditoria da 049.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Quatro casos de uso em `src/application/` (`cadastro.py`, `entrada_com_senha.py`, `recuperacao.py`, `definir_senha.py`), mais `vinculo.py` e `limite.py`; as rotas ficam em `src/web/rotas_conta.py` e o `auth_bp` mantém `/login?iniciar=1`, `/callback` e `/logout` | `rotas_auth.py` tem 158 linhas e três rotas; somar seis rotas e a lógica de cadastro quebraria a coesão. Blueprint próprio é o padrão que 052 e 009 já usam | (a) tudo em `rotas_auth.py`; (b) mais um `action` em `POST /` — a rota tem 23 `render_template` | 🟢 |
| D-02 | `POST /login` com e-mail e senha continua sendo o formulário; o Google segue em `GET /login?iniciar=1` | A tela tem dois caminhos e um só cartão: o POST autentica a credencial local, o GET com `iniciar` inicia o OAuth como hoje | (a) rota `/entrar` separada — divide a mesma tela em duas URLs; (b) `POST /login/google` | 🟢 |
| D-03 | `core/conta.py` puro: `ContaDeAcesso`, `PoliticaDeSenha` (autoridade única), `Credencial` e `derivar_senha`/`conferir_senha` com `hashlib.scrypt` (n=2¹⁴, r=8, p=1, sal de 16 bytes) e `hmac.compare_digest` | Política e derivação são regra, não HTTP (`ADR-24`); os parâmetros ficam gravados junto do hash, o que permite endurecer depois sem quebrar contas antigas; scrypt é biblioteca padrão (`RNF-11`) | (a) bcrypt/argon2 — dependência nova; (b) PBKDF2 — resistência a memória menor; (c) derivação na borda — acopla regra ao Flask | 🟢 |
| D-04 | `core/token_de_uso_unico.py`: `Token` congelado com hash, validade e tipo; `emitir` devolve o texto e o registro, `conferir` compara em tempo constante | `RN-08` e `RN-19`: dois tipos com validades distintas e a mesma mecânica; o texto do token nunca é guardado | (a) token = hash do e-mail + segredo — previsível; (b) JWT — precisa de assinatura e não resolve revogação | 🟡 |
| D-05 | Portas em `src/ports/__init__.py`: `RepositorioDeContas` (`criar`, `por_email`, `por_sub`, `por_google_sub`, `salvar`, `anexar_token`, `consumir_token`) e `TransporteDeEmail` (`enviar`), mais `Relogio` (`agora`) injetável | É a fronteira que permite trocar arquivo por Postgres sem tocar domínio; o relógio injetado testa expiração sem dormir nem monkeypatch | (a) `open()` no caso de uso; (b) data/hora de `datetime.now()` espalhado | 🟢 |
| D-06 | Adaptador `ports/contas_em_arquivo.py`: documento JSON `{versao, contas, tokens}`, `RLock`, escrita em temporário mais `os.replace`, `chmod 0600` quando o sistema permitir, cache de leitura por `(mtime_ns, tamanho)` invalidado na escrita do próprio processo | `RNF-12` e `RN-21`; a escrita é rara (a linha da conta Google nasce uma vez), então o custo do arquivo inteiro é irrelevante; o backup é a cópia do arquivo | (a) SQLite — ACID, mas binário e sem runner de migração no projeto; (b) Postgres — driver ausente no `.venv`; (c) um arquivo por conta — sem transação entre contas e tokens | 🟢 |
| D-07 | Adaptador `ports/email_smtp.py` mais `TransporteNulo`; variáveis `ANALISADOR_SMTP_HOST`, `_PORT`, `_USUARIO`, `_SENHA`, `_REMETENTE`, `_SEGURANCA`; import preguiçoso; tempo limite de 10 s; falha de envio vira aviso, nunca 500 | `RN-18`: o transporte é canal de confirmação e recuperação, não de entrada, e não pode derrubar a subida; o padrão do registrador nulo e do import preguiçoso já existe (`RN-13` da 008, `L-26`) | (a) biblioteca de e-mail — dependência nova; (b) serviço HTTP — dependência mais chave; (c) recusar a subida sem SMTP — tira o acesso de quem já tem conta | 🟢 |
| D-08 | `web/sessao.Conta` ganha `versao`; `instalar_guarda(aplicacao, verificar_versao=None)`; o verificador vive em `application/sessao_da_conta.py` e usa o cache do adaptador | `RN-10`: sem conferência por requisição a revogação não existe; com o cache por `(mtime, tamanho)` o custo é um `stat` por requisição autenticada de conta local | (a) tabela de sessões — contra o desenho sem estado de processo; (b) expirar todas as sessões no reset — não há como enumerá-las | 🟢 |
| D-09 | Vínculo em `application/vinculo.py`: `ao_entrar_com_google` anexa o `google_sub` à conta local do mesmo e-mail verificado, confirma o e-mail local de passagem e devolve o `sub` canônico; `definir_primeira_senha` só roda com sessão. O cadastro deslogado **nunca** altera conta existente | `RN-20`; anexar senha a conta existente sem sessão é pré-sequestro: quem escolhe a senha primeiro ganharia a conta, mesmo com o link indo para a caixa do dono. O Google prova o e-mail (`email_verified`), então a direção Google → local é segura | (a) anexar a senha no cadastro deslogado — vulnerável; (b) manter contas separadas — duas pastas e dois históricos | 🟢 |
| D-10 | Cadastro e reenvio respondem **sempre** a mesma frase; a diferença (conta criada ou já existente) vai só por e-mail; confirmação com token de 24 h; reenvio em `POST /reenviar-confirmacao` | `RN-07` e `RF-04`: com a instância compartilhada, a tela de cadastro não pode ser oráculo de contas. O e-mail é o canal que distingue os dois casos | (a) mensagem específica — oráculo; (b) sem feedback nenhum — o operador não sabe se o formulário funcionou | 🟢 |
| D-11 | Entrada local: sal aleatório e derivação "falsa" quando o e-mail não existe, para igualar o caminho e o custo; conta não confirmada só revela o estado **depois** de a senha conferir | `RN-05`: sem a derivação falsa, o tempo de resposta denuncia o e-mail; revelar o estado antes da senha criaria um oráculo novo | (a) só comparar hash — tempo distingue e-mail inexistente; (b) revelar a confirmação antes da senha | 🟡 |
| D-12 | Recuperação: token de 60 min, hash no arquivo, `GET` não consome e a página leva `Referrer-Policy: no-referrer` e `Cache-Control: no-store`; `POST` consome, aplica a política, incrementa `versao` e encerra a sessão do navegador que redefiniu | `RN-08`, `RN-09` e `RN-10`; o token viaja na URL, e o `Referer` é o vazamento clássico desse desenho | (a) token no corpo do POST — o link do e-mail precisa de GET; (b) consumir no GET — scanners de e-mail quebram o link | 🟢 |
| D-13 | Limite de tentativas em `application/limite.py`: `deque` de instantes por escopo, `Relogio` injetado e o decorator `com_limite` envolvendo os casos de uso; números da `RN-15` | Mantém os casos de uso sem contador e o limite testável com relógio falso; a instância é única, então memória de processo é suficiente | (a) middleware Flask — não distingue e-mail nem escopo; (b) Redis ou banco — dependência nova; (c) arquivo — escrita no caminho quente | 🟡 |
| D-14 | Os `POST` de identidade validam a origem: recusam `Sec-Fetch-Site: cross-site` e `Origin` de host fora de `TRUSTED_HOSTS`; sem token anti-CSRF nesta entrega | Login CSRF é o vetor que sobra com `SameSite=Lax` e não precisa de estado; a checagem é de poucas linhas e não cria tela nova | (a) token CSRF em sessão anônima — mais estado e mais uma tela; (b) `SameSite=Strict` — quebraria o retorno do OAuth; (c) não fazer nada — aceitável só em single-operator | 🟡 |
| D-15 | Apresentação: `_entrada_base.html` (cartão, banner, título) mais `login.html` reformulado, `cadastro.html`, `recuperar.html`, `redefinir.html`, `definir.html` e `mensagem.html`; estilos novos em `src/assets/app.css`; ícone `rel="icon"` reusando `/apple-touch-icon.png` | `RN-16` e `RN-17`; a base única evita cinco cópias do cartão e mantém o banner na posição atual; a rota do ícone já existe desde a 009 e tem `ETag` | (a) uma página com estados — Jinja maior e mais difícil de testar; (b) rota de favicon nova — arte duplicada | 🟢 |
| D-16 | Auditoria: `cadastrar`, `confirmar`, `definir_senha`, `pedir_senha`, `redefinir_senha` entram no conjunto fechado de `utils/auditoria.py`; a linha leva `conta=<sub>` e nunca e-mail, senha ou token | `RN-14`; o conjunto fechado é o que impede a mesma ação aparecer com dois nomes | (a) reusar `entrar` para tudo — perde a distinção de fluxo | 🟢 |
| D-17 | Sem `ANALISADOR_CONTAS`, o arquivo é `<raiz>/src/dados/contas.json`; a pasta nasce no primeiro uso; `.gitignore` ganha `dados/`; o compose ganha volume para `/app/src/dados` | Mesmo padrão de `src/uploads/` (`ADR-35`) e do log da 049: dado de runtime dentro do repositório, garantido pelo `.gitignore`, com volume no contêiner | (a) fora do repositório — contraria a decisão da 012/`ADR-35`; (b) dentro de `src/uploads/` — a tela varre essa pasta e o item apareceria na lista | 🟢 |
| D-18 | Nenhuma dependência nova, nenhuma tabela nova, `init.sql` intocado | `RNF-11`; derivação, token, SMTP e o arquivo saem da biblioteca padrão; o Postgres continua opcional e o histórico segue como está | (a) tabela `app_user` no Postgres — exigiria o driver e o banco de pé para entrar | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` chegou ao plano com **zero** marcadores de dúvida: os três de 2026-10-29 foram resolvidos na sessão de esclarecimentos e viraram `RN-19` a `RN-21` e `RF-21` a `RF-24`. A única mudança de escopo foi **correção de segurança**, não premissa: a definição de senha para conta Google existente passou a exigir sessão (`RN-20`, `RF-24`), porque o caminho deslogado permitia pré-sequestro.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Domínio de identidade (novo) | — | componente-novo | `src/core/conta.py`: conta, política de senha, credencial e derivação |
| Token de uso único (novo) | — | componente-novo | `src/core/token_de_uso_unico.py`: emissão, validade, comparação e consumo |
| Portas | `_reversa_sdd/architecture.md#3` | contrato-novo | `RepositorioDeContas`, `TransporteDeEmail` e `Relogio` (`Protocol`) |
| Adaptadores | `_reversa_sdd/architecture.md#3` | componente-novo | `ports/contas_em_arquivo.py`, `ports/email_smtp.py` e `TransporteNulo` |
| Casos de uso (novos) | `_reversa_sdd/architecture.md#3` | componente-novo | `application/cadastro.py`, `entrada_com_senha.py`, `recuperacao.py`, `definir_senha.py`, `vinculo.py`, `limite.py`, `sessao_da_conta.py` |
| Borda HTTP | `_reversa_sdd/architecture.md#1` | contrato-novo | `web/rotas_conta.py` com seis rotas; `POST /login` ganha o corpo de credenciais |
| Entrada Google | `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | regra-alterada | O callback passa pelo vínculo (best-effort) antes de gravar a sessão e adotar dados |
| Sessão | `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | regra-alterada | `Conta` ganha `versao`; a guarda confere a versão por verificador injetado |
| Composição | `_reversa_sdd/architecture.md#1` | contrato-alterado | `create_app` monta as duas portas, injeta o verificador e avisa na subida quando o e-mail não está configurado |
| Apresentação | `_reversa_sdd/architecture.md#3` | componente-novo | Base do cartão mais cinco páginas; `login.html` reformulado |
| Estilos | `_reversa_sdd/architecture.md#3` | regra-alterada | Bloco do cartão de entrada, campos, botão verde e links |
| Auditoria | `_reversa_sdd/addenda/049-sistema-de-log.md` | regra-alterada | Cinco ações novas no conjunto fechado |
| Modelo de dados | `_reversa_sdd/architecture.md#4` | delta-de-dados | Arquivo `src/dados/contas.json`; o esquema Postgres não muda |
| Integrações externas | `_reversa_sdd/architecture.md#6` | delta-de-contrato-externo | SMTP entra como segunda saída de rede, depois do Google |
| Contexto C4 | `_reversa_sdd/c4-context.md` | regra-alterada | Servidor SMTP como sistema externo e a persona que se autentica |
| Máquinas de estado | `_reversa_sdd/state-machines.md#11` lido com o adendo 051 | regra-nova | Ciclo da conta local: não confirmada → confirmada → com senha; a sessão ganha a transição de revogação |

## 6. Delta no modelo de dados

- Resumo: **nenhuma tabela, coluna, índice ou migração no Postgres**. Nasce um documento JSON local com duas coleções — `contas` e `tokens` —, coberto pelo `.gitignore` e montado como volume no contêiner. O Diagrama E do `erd-complete.md` fica intocado.
- Detalhe completo em: `_reversa_forward/053-conta-com-senha-e-recuperacao/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Entrada e senha (`/login`, `/cadastro`, `/confirmar`, `/reenviar-confirmacao`, `/recuperar-senha`, `/redefinir-senha`, `/definir-senha`) | HTTP (formulário, resposta HTML) | `_reversa_forward/053-conta-com-senha-e-recuperacao/interfaces/entrada-e-senha.md` |
| Envio de e-mail (SMTP) | Protocolo de saída | `_reversa_forward/053-conta-com-senha-e-recuperacao/interfaces/entrada-e-senha.md#envio-de-e-mail` |

## 8. Plano de migração

1. Acrescentar `dados/` ao `.gitignore` e o volume `./src/dados:/app/src/dados` ao `docker-compose.yml`. O arquivo nasce vazio no primeiro uso; nada é movido.
2. Configurar o transporte: `ANALISADOR_SMTP_HOST`, `_PORT`, `_USUARIO`, `_SENHA`, `_REMETENTE` e `_SEGURANCA` no `.env`; em ambiente compartilhado, `ANALISADOR_URL_PUBLICA` precisa ser `https://` para o cookie ganhar `Secure` e para os links do e-mail apontarem para o host certo.
3. Subir a aplicação. As contas Google existentes **não são migradas em lote**: a linha local de cada uma nasce no primeiro login Google depois do deploy, já com `verificado_em` preenchido, sem credencial e com o mesmo `sub` — a pasta de uploads não muda de nome.
4. O primeiro acesso local de uma conta antiga é o login Google seguido de "Definir senha"; não há senha provisória nem e-mail de boas-vindas em massa.
5. Reverter é remover o volume e o código: o arquivo é ignorado, e o caminho Google volta a funcionar sozinho. Nenhum dado do operador é apagado pela reversão.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Sem SMTP configurado, ninguém novo entra | alto | média | Aviso na subida e na tela; teste que garante que login de conta confirmada continua funcionando; onboarding com o passo de configuração antes do primeiro uso |
| Pré-sequestro por cadastro deslogado com e-mail alheio | alto | baixa | `RN-20` e `D-09`: cadastro deslogado nunca altera conta existente; teste dedicado ataca o cenário (atacante cria, dono confirma, atacante tenta entrar) |
| Token vazar pelo cabeçalho `Referer` | médio | baixa | `Referrer-Policy: no-referrer` e `no-store` nas páginas com token; teste de cabeçalho |
| Custo do scrypt travar as quatro threads | médio | média | Medir no interpretador oficial e registrar; alvo de até 250 ms por verificação; se estourar, reduzir n e documentar o número |
| Arquivo de contas corrompido por escrita concorrente ou queda | alto | baixa | Trava, temporário mais `os.replace`, teste de duas criações simultâneas e teste de releitura após escrita interrompida |
| Cache de versão servir sessão já revogada | alto | baixa | Invalidação na escrita do próprio processo; teste que redefine a senha e usa a sessão antiga na mesma execução |
| Enumeração de contas pelo tempo de resposta | médio | média | Derivação falsa no caminho de e-mail inexistente; teste compara o **caminho**, não o relógio (teste de tempo é instável) |
| O callback do Google quebrar porque o arquivo está indisponível | alto | baixa | Escrita best-effort: falha no vínculo é registrada e o login Google segue com o `sub` do provedor; teste com repositório que levanta |
| SMTP do provedor bloquear ou cair em spam | médio | média | Documentar provedor e remetente; registrar a falha com motivo curto; o reenvio é explícito na tela |
| E-mail de confirmação consumido por scanner de segurança | baixo | média | Consumir no `GET` só para confirmação (ação idempotente e sem dano), nunca para redefinição; teste do segundo `GET` |
| JSON crescer com o uso compartilhado | baixo | baixa | Volume de escrita é raro e o documento é pequeno; a porta permite trocar por Postgres sem tocar domínio |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte com **1.801 + os testes novos** passando, e as **5 falhas pré-existentes** continuando exatamente as mesmas (`addenda/052`)
- [ ] Paridade sem divergência nova contra a linha de base
- [ ] Teste negativo A→B: conta B não lê arquivo de A, recebe `404` e nenhum nome de A no corpo
- [ ] Token de confirmação e de redefinição: uso único, expiração, reenvio invalida o anterior
- [ ] Cadastro com e-mail novo e com e-mail existente produz o **mesmo** corpo e o mesmo status
- [ ] Pré-sequestro coberto: cadastro deslogado com e-mail de conta existente não cria nem altera nada
- [ ] Definir senha autenticado preserva `sub` e pasta, e a entrada pelos dois caminhos cai no mesmo dono
- [ ] Redefinição derruba a sessão anterior, e a sessão nova entra com a senha nova
- [ ] Arquivo de contas: duas criações simultâneas, releitura após reinício e permissão restrita (ou limitação do SO declarada)
- [ ] `no-store` em toda resposta autenticada e `no-referrer` nas páginas com token
- [ ] Nenhuma dependência nova; `requirements.txt` inalterado
- [ ] Auditoria das cinco ações sem e-mail, senha ou token
- [ ] Medição do custo de derivação registrada
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-30 | Versão inicial gerada por `/reversa-plan` a partir do `requirements.md` sem marcadores, da sessão de esclarecimentos de 2026-10-30 e dos adendos 051 e 052 | reversa |
