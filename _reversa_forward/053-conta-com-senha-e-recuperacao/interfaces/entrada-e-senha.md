# Interface: entrada e senha (HTTP) e envio de e-mail (SMTP)

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Requirements: `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Visão geral

Sete rotas novas e uma alterada, todas de formulário e resposta HTML, ao lado das três da 051. O contrato é **de tela**: o navegador envia `application/x-www-form-urlencoded` e recebe a página inteira, como o resto do sistema — não há JSON nem API. As rotas públicas são as de quem ainda não tem sessão; `POST /logout` e `POST /definir-senha` continuam sob a guarda da 051.

| # | Método | Rota | Autenticada? | Papel |
|---|--------|------|--------------|-------|
| 1 | `GET` | `/login` | não | Mostra o cartão de entrada; com sessão, redireciona para `/` |
| 2 | `POST` | `/login` | não | Autentica e-mail e senha |
| 3 | `GET` | `/login?iniciar=1` | não | Inicia o OAuth Google (inalterado desde a 051) |
| 4 | `GET` | `/callback` | não | Retorno do Google (inalterado, com vínculo de identidade) |
| 5 | `POST` | `/logout` | sim | Encerra a sessão (inalterado) |
| 6 | `GET` | `/cadastro` | não | Mostra o formulário de cadastro |
| 7 | `POST` | `/cadastro` | não | Cria a conta não confirmada e dispara a confirmação |
| 8 | `GET` | `/confirmar?token=…` | não | Consome o token e confirma o e-mail |
| 9 | `POST` | `/reenviar-confirmacao` | não | Reenvia o link de confirmação |
| 10 | `GET` | `/recuperar-senha` | não | Mostra o formulário de pedido |
| 11 | `POST` | `/recuperar-senha` | não | Pede o link de redefinição |
| 12 | `GET` | `/redefinir-senha?token=…` | não | Mostra o formulário de nova senha (não consome) |
| 13 | `POST` | `/redefinir-senha` | não | Consome o token e troca a senha |
| 14 | `GET` | `/definir-senha` | sim | Mostra o formulário de primeira senha |
| 15 | `POST` | `/definir-senha` | sim | Define a primeira senha da conta autenticada |

## 2. Regras comuns a todas as rotas

| Regra | Valor |
|---|---|
| Corpo | `application/x-www-form-urlencoded`, `utf-8` |
| Resposta | HTML completo (`text/html; charset=utf-8`) |
| Cache | `Cache-Control: no-store` em **toda** resposta de identidade, autenticada ou não |
| Enquadramento | `X-Frame-Options: DENY`, herdado do gancho global da borda |
| Origem (só `POST`) | Recusa com **400** e mensagem genérica quando `Sec-Fetch-Site: cross-site`, ou quando `Origin`/`Referer` presente aponta host fora de `TRUSTED_HOSTS` |
| Erros de validação | **200** com a página e a mensagem; o sistema não usa 400 para erro de formulário, exceto a recusa de origem |
| Erro inesperado | 500 com a página de erro do Flask; nada de rastreamento na tela |
| `Referrer-Policy` | `no-referrer` nas páginas que carregam token na URL (`/confirmar`, `/redefinir-senha`) |
| Idioma | pt-BR, literais da `RN-13` |

## 3. Rotas, uma a uma

### 3.1 `GET /login`

- **Resposta 200**: cartão com banner no topo, título `Entre na sua conta`, botão `Entrar com Google`, campos `E-mail` e `Senha`, botão `Entrar`, links `Esqueci minha senha` e `Criar conta`, e o ícone da aba (`rel="icon"`).
- **Com sessão válida**: `302` para `/`.
- **Mensagem de falha**: quando vem de `/callback` com erro, a mesma página com a mensagem correspondente (as três da 051).

### 3.2 `POST /login`

| Campo | Obrigatório | Limite |
|---|---|---|
| `email` | sim | 254 caracteres |
| `senha` | sim | 1 a 128 caracteres |

| Situação | Resposta |
|---|---|
| Credenciais corretas e conta confirmada | `303` para `/`, cookie de sessão novo |
| Senha errada ou e-mail sem conta | `200`, `E-mail ou senha inválidos.`, nenhum cookie |
| Conta local não confirmada e **senha correta** | `200`, `Confirme seu e-mail para entrar. Enviamos um link para o endereço informado.`, com o formulário de reenvio |
| Limite de tentativas estourado | `200`, `E-mail ou senha inválidos.`, sem revelar o bloqueio |
| Origem cruzada | `400` |

- **Não idempotente**: cada sucesso emite um cookie novo, e `guardar_conta` limpa a sessão antes de gravar (defesa contra fixação).
- **Efeito colateral**: auditoria `entrar`/`sucesso` ou `falha`; a falha nunca identifica a conta.
- **Tempo**: o caminho de e-mail inexistente executa uma derivação falsa, para não distinguir pelo relógio.

### 3.3 `GET /login?iniciar=1` e `GET /callback`

Inalterados em contrato desde a 051. A única diferença é interna: o callback passa pelo **vínculo de identidade** antes de gravar a sessão, e a falha do vínculo é registrada sem interromper a entrada.

### 3.4 `POST /logout`

Inalterado: `303` para `/login`, idempotente, auditoria `sair`.

### 3.5 `GET /cadastro`

- **200**: cartão com `Crie sua conta`, campos `E-mail`, `Senha`, `Repita a senha`, a dica da política e o link `Voltar para entrar`.

### 3.6 `POST /cadastro`

| Campo | Obrigatório | Limite |
|---|---|---|
| `email` | sim | 254 caracteres |
| `senha` | sim | política completa (`RN-02`) |
| `repeticao` | sim | precisa ser igual a `senha` |

| Situação | Resposta |
|---|---|
| Senha fora da política ou repetição diferente | `200` com a mensagem que nomeia o que falta; **nenhuma conta é criada ou alterada** |
| Tudo válido, e-mail livre | `200` com `Se este e-mail puder ser usado, enviaremos as instruções.`; conta criada não confirmada; e-mail de confirmação enviado |
| Tudo válido, e-mail já com conta | **exatamente a mesma** resposta 200 e o mesmo corpo; **nenhuma conta é criada ou alterada**; e-mail de "conta já existente" enviado ao dono |
| Limite de cadastros por origem | mesma resposta genérica, sem envio |
| Origem cruzada | `400` |

- **Idempotência**: dois envios iguais com o mesmo e-mail resultam na mesma tela e em **um** e-mail (o segundo substitui o primeiro token; o primeiro link deixa de valer).
- **Antes de qualquer efeito**, a conta é buscada pelo e-mail normalizado; é essa busca que decide se há criação.

### 3.7 `GET /confirmar?token=…`

| Situação | Resposta |
|---|---|
| Token válido | `200`, `E-mail confirmado. Entre com a sua senha.`; conta marcada como confirmada; token removido |
| Token expirado, já usado ou inexistente | `200`, `Este link de confirmação expirou ou já foi usado. Peça outro.`, com o formulário de reenvio |
| Token ausente | mesma resposta de token inválido |

- **Idempotência**: o segundo `GET` com o mesmo token cai na mensagem de inválido. É o único ponto em que o `GET` consome — e é aceitável, porque a ação não expõe dado e o pior caso é um scanner de e-mail confirmar o endereço do próprio dono.

### 3.8 `POST /reenviar-confirmacao`

| Campo | Obrigatório |
|---|---|
| `email` | sim |

- **Resposta**: sempre `200` com `Se este e-mail puder ser usado, enviaremos as instruções.`
- **Efeito**: só envia quando existe conta local **não confirmada**; limite de três por conta por hora.

### 3.9 `GET /recuperar-senha`

- **200**: cartão com `Recupere sua senha`, a frase `Se você entra apenas com Google, recupere o acesso na sua conta Google.`, campo `E-mail`, botão `Solicitar instruções` e link `Voltar para entrar`.

### 3.10 `POST /recuperar-senha`

| Campo | Obrigatório |
|---|---|
| `email` | sim |

- **Resposta**: sempre `200` com `Se este e-mail estiver cadastrado, enviaremos as instruções.`
- **Efeito**: só gera token e envia quando existe conta local **com credencial**; limite de três por e-mail a cada quinze minutos.
- **Sem transporte configurado**: `200` com `O envio de e-mail não está configurado nesta instalação.` — a mensagem é própria porque, sem envio, prometer "enviaremos" seria mentira operacional.

### 3.11 `GET /redefinir-senha?token=…`

| Situação | Resposta |
|---|---|
| Token válido | `200` com `Defina uma nova senha`, campos `Senha` e `Repita a senha`, e a dica da política; **não consome** o token |
| Token expirado, usado ou inexistente | `200` com `Este link expirou ou já foi usado. Peça outro.` e o atalho para pedir outro |

### 3.12 `POST /redefinir-senha`

| Campo | Obrigatório |
|---|---|
| `token` | sim (oculto) |
| `senha` | sim (política) |
| `repeticao` | sim |

| Situação | Resposta |
|---|---|
| Token válido e senha válida | `303` para `/login` com `Senha alterada. Entre com a nova senha.`; token consumido; `versao_de_credencial` incrementada; sessão do navegador encerrada |
| Senha fora da política | `200` com a mensagem da política; **token não é consumido** |
| Token inválido | `200` com a mensagem de link expirado |

- **Idempotência**: o segundo `POST` com o mesmo token não altera a senha.
- **Efeito**: todas as sessões anteriores da conta passam a ser recusadas na próxima requisição (`RN-10`).

### 3.13 `GET /definir-senha`

- Sem sessão: `302` para `/login`.
- Com sessão e conta **sem** credencial: `200` com `Defina uma senha para entrar sem depender do Google.`, campos `Senha` e `Repita a senha`.
- Com sessão e conta **com** credencial: `302` para `/` (a tela não é de troca de senha nesta entrega).

### 3.14 `POST /definir-senha`

| Campo | Obrigatório |
|---|---|
| `senha` | sim (política) |
| `repeticao` | sim |

| Situação | Resposta |
|---|---|
| Sessão válida, conta sem credencial, senha válida | `303` para `/` com `Senha definida. Você já pode entrar com e-mail e senha.`; `sub` e pasta **não mudam** |
| Senha fora da política | `200` com a mensagem da política |
| Sem sessão | `302` para `/login` |

- **A definição não incrementa a versão de credencial**: não havia credencial anterior para revogar, e a sessão atual é legítima.
- **Efeito**: auditoria `definir_senha`/`sucesso` com `conta=<sub>`.

## 4. Limites de tentativa

| Escopo | Chave | Limite | Efeito ao estourar |
|---|---|---|---|
| Entrada | `email_normalizado` + IP | 5 falhas / 15 min | resposta genérica, sem autenticar |
| Cadastro | IP | 5 / hora | resposta genérica, sem criar |
| Recuperação | `email_normalizado` | 3 / 15 min | resposta genérica, sem enviar |
| Reenvio de confirmação | `email_normalizado` | 3 / hora | resposta genérica, sem enviar |

O contador vive no processo e reinicia com ele; a instância é única por construção (`ADR-12`), então não há divergência entre réplicas.

## 5. Envio de e-mail

### 5.1 Configuração

| Variável | Obrigatória | Padrão | Efeito |
|---|---|---|---|
| `ANALISADOR_SMTP_HOST` | sim | — | Servidor SMTP |
| `ANALISADOR_SMTP_PORT` | não | 587 | Porta |
| `ANALISADOR_SMTP_USUARIO` | não | — | Autenticação |
| `ANALISADOR_SMTP_SENHA` | não | — | Autenticação; nunca vai para log |
| `ANALISADOR_SMTP_REMETENTE` | sim | — | Endereço do remetente |
| `ANALISADOR_SMTP_SEGURANCA` | não | `starttls` | `starttls`, `ssl` ou `nenhuma` |

Sem `HOST` ou `REMETENTE`, o transporte é o **nulo**: a subida continua, com aviso no log, e as telas que dependem de envio mostram a mensagem de indisponibilidade.

### 5.2 Mensagens

| Evento | Assunto | Corpo |
|---|---|---|
| Confirmação | `Confirme seu e-mail — Analisador Genealógico` | Texto simples com o link `<URL_PUBLICA>/confirmar?token=…` e a validade de 24 h |
| Conta já existente | `Sua conta no Analisador Genealógico` | Texto simples dizendo que alguém tentou criar conta com o endereço, com o atalho para entrar ou recuperar; se a conta é Google, orienta a entrar pelo Google e usar "Definir senha" |
| Redefinição | `Redefinição de senha — Analisador Genealógico` | Texto simples com o link `<URL_PUBLICA>/redefinir-senha?token=…` e a validade de 60 min |

- **Formato**: `text/plain`, `utf-8`. Sem HTML — menos superfície e menos chance de cair em spam por markup.
- **Tempo limite**: 10 s por envio; falha vira aviso no log com motivo curto (`smtp_timeout`, `smtp_autenticacao`, `smtp_recusado`) e nunca 500 na tela.
- **Sem retentativa automática**: um envio repetido seria um segundo e-mail. O reenvio é explícito na tela.
- **Nunca em log**: endereço de destino, assunto, corpo, token e credencial.

## 6. Literais de contrato

Os literais de tela são os da `RN-13`, e os de e-mail são os assuntos da tabela acima. Nenhum deles muda sem que o teste de contrato mude junto; os 36 literais anteriores (29 da extração + 7 da 051) permanecem byte a byte.
