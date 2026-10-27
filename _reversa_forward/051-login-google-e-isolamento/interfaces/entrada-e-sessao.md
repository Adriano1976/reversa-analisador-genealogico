# Interface: entrada e sessão

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Tipo: HTTP (entrada) e HTTP de saída para o provedor de identidade
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Superfície

| Método | Caminho | Sessão | Resposta |
|---|---|---|---|
| GET | `/login` | pública | `200` com a tela de entrada; `302 /` se já autenticado |
| GET | `/login?iniciar=1` | pública | `302` para o provedor, com `state` novo na sessão |
| GET | `/callback` | pública | `302 /` no sucesso; `200` com a tela de entrada e uma frase na falha |
| POST | `/logout` | exige | `303 /login`, sessão limpa |
| GET | `/` | exige | `302 /login` sem sessão; `200` com a tela principal com sessão |
| POST | `/` (cinco `action`) | exige | `303 /login` sem sessão; comportamento atual com sessão |
| POST | `/descartes.csv` | exige | `303 /login` sem sessão; CSV com sessão |
| GET | `/app.css`, `/banner.png`, `/apple-touch-icon.png` | públicas | `200` (ou `404` da arte ausente), como hoje |

> A lista pública é fechada e por **endpoint**, não por prefixo de caminho. `POST /descartes.csv`
> entra na guarda por ser ação da tela de resultado, ainda que não leia dado de servidor.

## 2. `GET /login`

- Sem sessão: `200`, corpo da tela de entrada, com o botão **Entrar com Google** (link para
  `/login?iniciar=1`) e, opcionalmente, a frase de falha recebida.
- Com sessão: `302` para `/`, sem corpo.
- Não define cookie novo.

## 3. `GET /login?iniciar=1`

Gera `state = secrets.token_urlsafe(32)`, grava em `session["oauth_state"]` e responde `302` para:

```text
https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=<GOOGLE_CLIENT_ID>
  &redirect_uri=<ANALISADOR_URL_PUBLICA>/callback
  &response_type=code
  &scope=openid%20email%20profile
  &state=<state>
  &access_type=online
```

- O `redirect_uri` vem **só** da configuração; nunca de `request.host`, `request.url_root` ou cabeçalho.
- Um segundo `?iniciar=1` sobrescreve o `state` anterior: o fluxo antigo deixa de valer.

## 4. `GET /callback`

Parâmetros de retorno do provedor: `code`, `state` e, em falha, `error`.

| Situação | Comportamento | Corpo | Status |
|---|---|---|---|
| `error` presente (inclusive `access_denied`) | Limpa o `state`, mostra a entrada | "A entrada foi cancelada." | `200` |
| `state` ausente, divergente ou já consumido | Limpa o `state`, mostra a entrada | "A entrada expirou. Tente de novo." | `200` |
| Troca do código falha (HTTP ≠ 200, timeout, corpo sem `access_token`) | Loga o detalhe no servidor, mostra a entrada | "Não foi possível concluir a entrada agora." | `200` |
| Perfil sem e-mail ou com `email_verified` falso | Loga o detalhe, mostra a entrada | "Não foi possível concluir a entrada agora." | `200` |
| Sucesso | **Limpa a sessão** (fixação), grava a conta, `session.permanent = True`, roda a migração do dono inicial se for o caso | — | `302 /` |

O `code` é de uso único, e a troca acontece **no servidor**. O `id_token` que o provedor devolve é
**ignorado**: a identidade vem do endpoint de userinfo, sobre TLS, com o token de acesso que nunca sai
do servidor.

## 5. `POST /logout`

- Com sessão: limpa a sessão e redireciona `303` para `/login`.
- Sem sessão: `303` para `/login` do mesmo jeito (idempotente; não é erro).
- É `POST` para que um simples link ou pré-carregamento de página não derrube a sessão.

## 6. Guarda e conta

- A guarda roda em `before_request`, antes de qualquer handler.
- Sem sessão: `GET` → `302 /login`; `POST` → `303 /login`. **Nenhum handler roda**, então nenhum
  arquivo, árvore ou resultado é tocado.
- Com sessão: `g.conta` recebe o `sub`, o e-mail e o nome; `g.dono` recebe o `sub`.
- As respostas autenticadas saem com `Cache-Control: no-store` (e `X-Frame-Options: DENY`, que já
  existia), para o "voltar" não reexibir a tela depois do logout.

## 7. Cookie de sessão

| Atributo | Valor |
|---|---|
| Nome | `analisador_sessao` |
| Conteúdo | `{"conta": {"sub", "email", "nome"}, "oauth_state": "..."}` — assinado, nunca cifrado |
| `HttpOnly` | sim |
| `SameSite` | `Lax` |
| `Secure` | sim quando `ANALISADOR_URL_PUBLICA` começa com `https://`; não no uso local em `http://` |
| Validade | 12 horas, renovada a cada requisição (`PERMANENT_SESSION_LIFETIME`, `SESSION_REFRESH_EACH_REQUEST`) |
| `Path` | `/` |
| `Domain` | ausente |

O cookie **não** carrega token de acesso, código de autorização nem dado genealógico — só a identidade
mínima para a tela.

## 8. Literais novos (congelados por teste)

| Literal | Onde |
|---|---|
| `Entrar com Google` | botão da tela de entrada |
| `Entre com a sua conta Google para continuar.` | frase da tela de entrada |
| `A entrada foi cancelada.` | retorno com `error` |
| `A entrada expirou. Tente de novo.` | `state` inválido ou consumido |
| `Não foi possível concluir a entrada agora.` | falha de troca ou de perfil |
| `Sair` | botão da masthead |

Os **29 literais** catalogados em `domain.md#5` não mudam. A recusa por recurso de outro dono
reaproveita os literais de inexistência que já existem (`Erro: Arquivo 'X' não existe mais.` e
`Não foi possível aposentar o arquivo: ele não está mais na pasta.`).

## 9. Saída para o provedor

O contrato de saída — pedido de autorização, troca do código, leitura do perfil, tempos limite e
mapeamento de erro — vive em `_reversa_forward/051-login-google-e-isolamento/interfaces/provedor-de-identidade.md`.
A entrada depende de três fatos dele: a troca acontece no servidor, o perfil entrega `sub` e e-mail
verificado, e nenhuma chamada passa de 10 s.

## 10. Contrato de configuração

| Variável | Obrigatória com autenticação | Efeito se ausente |
|---|---|---|
| `GOOGLE_CLIENT_ID` | sim | o servidor não sobe |
| `GOOGLE_CLIENT_SECRET` | sim | o servidor não sobe |
| `ANALISADOR_SECRET_KEY` | sim | o servidor não sobe (não há como assinar a sessão) |
| `ANALISADOR_URL_PUBLICA` | sim | o servidor não sobe (não há URL de retorno confiável) |
| `ANALISADOR_DONO_INICIAL` | sim | o servidor não sobe (os dados anteriores ficariam sem destino) |

A verificação acontece na **subida** (`__main__`), e não no import: `create_app` sem autenticação
continua sendo o caminho da suíte e do harness de paridade. A mensagem de recusa nomeia todas as
variáveis ausentes de uma vez.

## 11. Ameaças cobertas e não cobertas

| Vetor | Coberto? | Como |
|---|---|---|
| Retorno forjado (CSRF do fluxo) | ✅ | `state` de 32 bytes, de uso único, ligado à sessão |
| Redirecionamento aberto | ✅ | URL de retorno fixa na configuração; nenhum parâmetro de destino |
| Fixação de sessão | ✅ | Sessão limpa antes de gravar a conta |
| Reuso do código | ✅ | Uso único no provedor; o `state` é consumido |
| Vazamento de token em URL/log/trilha | ✅ | Token só no servidor; a trilha grava `sub` |
| Recurso de outro dono | ✅ | Escopo na porta; `404` indistinguível |
| "Voltar" após logout | ✅ | `Cache-Control: no-store` |
| DNS rebinding | ✅ | `TRUSTED_HOSTS` já existente (adendo 014) |
| CSRF em formulário | 🟡 parcial | `SameSite=Lax`; token por formulário fica declarado como não feito |
| Criação massiva de contas | ❌ | Nenhum limite; o perímetro é o loopback por padrão |
| Força bruta de credencial | n/a | Não há senha no sistema |
