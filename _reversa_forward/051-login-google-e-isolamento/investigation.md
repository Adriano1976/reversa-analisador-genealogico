# Investigation: login com Google e isolamento por dono

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Suporta: `_reversa_forward/051-login-google-e-isolamento/roadmap.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. A pergunta de pesquisa

O que o legado **não** tem, o que ele já preparou, e qual é o caminho de menor risco para ligar
identidade e isolamento sem transformar a instalação local em um sistema que só funciona com Docker.

O ponto de partida está medido: `permissions.md#1` registra **zero** login, sessão, papel e token;
`#1.1` registra que o `dono` existe nas assinaturas e é **ignorado** pelos quatro métodos do
adaptador; `#4.3` registra que "a chave é portadora do acesso". A Onda 3 foi decidida em 2026-10-05
como o lugar da correção (`P-01`), e o alvo já escreveu o critério: `owner_id` como invariante,
repositório sempre escopado e **teste negativo com `404`, não `403`** (`risk_register.md#RISK-005`).

## 2. O que o legado já resolve, e o que ele deixa em aberto

| Já resolvido | Consequência para o plano |
|---|---|
| `dono` é parâmetro obrigatório em todas as portas, sem valor padrão (`adrs/26`) | Não é preciso reabrir assinatura nenhuma para escopar; basta dar comportamento ao parâmetro |
| A árvore entra por parâmetro e não há estado global (`adrs/24`) | Duas contas concorrentes não se contaminam no domínio; resta o disco |
| O cache da árvore é chaveado por caminho absoluto (`adrs/38`) | Com pasta por dono, o caminho já distingue e o cache continua correto, sem alteração |
| A auditoria é uma linha por ação de servidor, com conjuntos fechados (`adenda 049`) | Entrar e sair entram como ações novas, sem inventar formato |
| O `TRUSTED_HOSTS` recusa `Host` estranho antes da rota (`adenda 014`) | O retorno do provedor não precisa de defesa própria contra DNS rebinding |
| A suíte e o harness importam `app` sem credencial | A autenticação tem de ser injetável, ou o seam quebra 1.717 testes |

| Em aberto no legado | Como o plano trata |
|---|---|
| Nenhum armazenamento de conta | Identidade = `sub` do provedor, na sessão assinada (D-01) |
| Nenhuma noção de sessão | Cookie assinado, sem estado de processo (D-02) |
| A pasta de upload é plana | Pasta por dono, com migração por cópia (D-06, D-07) |
| Nenhuma verificação de propriedade | Guarda única mais escopo na porta; recusa `404` (D-05, D-06) |

## 3. Alternativas avaliadas

### 3.1 Identidade no retorno do provedor: `id_token` ou userinfo?

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| Validar `id_token` (OIDC) | Não exige segunda chamada; identidade assinada pelo provedor | Exige validação de JWT, JWKS, relógio e biblioteca de criptografia; `cryptography`/`joserfc` é cadeia pesada e risco de wheel em cp314 | **descartada** |
| Trocar o código no servidor e ler o perfil no endpoint de userinfo | Uma chamada HTTPS a mais; nenhuma criptografia; o token nunca sai do servidor | Depende de uma segunda chamada e de timeout próprio | **escolhida** |
| Confiar no que o navegador devolve | — | Inaceitável: a identidade viria do cliente | descartada |

### 3.2 Biblioteca de OAuth

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| `Authlib` | Fluxo pronto, `state` e PKCE resolvidos | Arrasta `cryptography` e a cadeia JOSE; o projeto já pagou caro por dependência indisponível no interpretador oficial (`L-26`) | descartada |
| `requests-oauthlib` | Menor que Authlib | Traz `oauthlib`; ainda é uma camada a mais para um fluxo de um provedor só | descartada |
| Biblioteca oficial do Google (`google-auth-oauthlib`) | Recomendada pela documentação do Google | Cadeia maior ainda (`google-auth`, `rsa`, `pyasn1`, `oauthlib`) e um modelo de credenciais que não encaixa no pin do projeto | descartada |
| Fluxo manual com `requests` | ~80 linhas, testável com provedor falso, zero criptografia, pin de uma dependência | Exige disciplina: `state`, uso único do código e URL de retorno fixa precisam de teste | **escolhida** |

> A documentação do Google **recomenda** usar biblioteca de cliente. A divergência é consciente: o
> fluxo é pequeno, o provedor é um só, e as partes sensíveis (`state`, troca server-side, URL de
> retorno fixa, TLS) são exatamente as que o projeto consegue prender em teste com um provedor falso.
> O risco aceito é o de manter ~80 linhas próprias; o risco evitado é o de uma cadeia de criptografia
> que o interpretador oficial não tem.

### 3.3 Onde a sessão vive

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| Cookie assinado do Flask | Sem estado no processo; sobrevive a reinício; nenhuma tabela | Segredo obrigatório; revogação só por expiração | **escolhida** |
| Dicionário em memória | Simples | Perde tudo no reinício; é estado global de processo, que a feature 005 removeu | descartada |
| Arquivo de sessões | Sobrevive a reinício | Concorrência de disco e lixo acumulado | descartada |
| Tabela de sessões | Revogação por linha | Exige PostgreSQL para entrar | descartada |

### 3.4 Registro de conta: tabela ou `sub`?

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| Tabela `app_user` (documento de entrada) | Lista de contas, papéis futuros, FK | **Obriga PostgreSQL para entrar**: o uso local sem Docker deixa de funcionar | descartada nesta entrega |
| Apenas o `sub` na sessão e no `owner_id` | Nenhuma dependência nova; identidade estável | Não há lista de contas nem como revogar alguém | **escolhida** |
| SQLite local | Sem Docker | Terceiro regime de persistência (o projeto declara dois) | descartada |

O `sub` é estável e não muda com o e-mail; a decisão também resolve o cenário "a conta troca de
e-mail" sem nenhum código. A tabela do alvo continua sendo o destino da migração, e a entrega
**não** a antecipa.

### 3.5 Escopo do armazenamento em disco

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| Pasta por dono | Mantém `<chave>__<nome>`; isola listagem, leitura e aposentadoria; cache por caminho continua correto | Muda o layout; ~15 asserções de teste existentes mudam | **escolhida** |
| Dono no nome do arquivo | Layout plano | Quebra o formato da referência e a validação de forma | descartada |
| Índice lateral (`dono` por referência) | Layout plano | Concorrência de disco em toda escrita; um arquivo a mais para corromper | descartada |
| Balde único com filtro só na listagem | Nada muda no disco | Não impede abrir a referência alheia: a chave é portadora do acesso | descartada |

### 3.6 Migração dos dados anteriores

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| Copiar para a pasta do dono inicial | Original preservado para rollback; nenhuma operação destrutiva | Dobra o uso de disco (≈29 MB) até limpeza manual | **escolhida** |
| Mover | Não duplica | Operação destrutiva sobre dado real; rollback exige desfazer | descartada |
| Atribuir no primeiro login de qualquer conta | Nenhuma configuração | Com a entrada aberta (D1), entrega o acervo ao primeiro estranho | descartada |

### 3.7 CSRF

| Opção | Prós | Contras | Decisão |
|---|---|---|---|
| `SameSite=Lax` no cookie | Bloqueia `POST` de outra origem; nenhuma tela muda | Não cobre navegador antigo nem subdomínio | **escolhida**, declarada |
| Token por formulário | Defesa em profundidade | Muda todos os formulários e exige armazenamento do token | adiada; reabrir se a aplicação sair do loopback |

## 4. Padrões aplicáveis

- **OAuth 2.0, authorization code** (RFC 6749 §4.1): o código é trocado no servidor e o token nunca
  chega ao navegador; `state` amarra o retorno à sessão que iniciou o fluxo.
- **Prevenção de fixação de sessão:** a sessão é limpa no sucesso do retorno, antes de gravar a conta.
- **Negação indistinguível:** recurso de outro dono responde como inexistente (`404`), para não vazar
  a existência — o critério do `RISK-005` e a prática de APIs multiusuário.
- **Fail-closed na configuração:** a falta de credencial impede o servidor de servir, não degrada em
  silêncio; é o oposto do registrador nulo da feature 008, e a diferença é que ali o acessório
  degradava e aqui o essencial é a identidade.

## 5. Fontes externas consultadas

- [RFC 6749 — The OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [Google — Como usar o OAuth 2.0 para aplicativos de servidor da Web](https://developers.google.com/identity/protocols/oauth2/web-server?hl=pt_BR)
  (confirmado: URI de redirecionamento de teste pode ser `http://localhost:8080`, o valor tem de casar
  exatamente com o registrado, e `state` é recomendado)
- [Flask — Sessions](https://flask.palletsprojects.com/en/stable/quickstart/#sessions)
- [OWASP — Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP — Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

## 6. O que ainda não se sabe, e onde é barato descobrir

| Ponto | Como fechar |
|---|---|
| O `requests` instalado no `.venv` cobre a chamada de token e de userinfo com `timeout` | Primeira ação do bloco de código, com o provedor falso e depois com o real |
| A URL de userinfo do Google responde ao token com os escopos `openid email profile` | Verificação manual no onboarding, antes do teste com a segunda conta |
| O cabeçalho `Cache-Control` não é sobrescrito por nenhum gancho existente | Ler `src/app.py#after_request` e `src/web/hooks_de_registro.py` na ação que implementa a guarda |
| O `SHA_DA_TELA` muda com a masthead | Medição no commit que toca o template, como a `050` fez |
