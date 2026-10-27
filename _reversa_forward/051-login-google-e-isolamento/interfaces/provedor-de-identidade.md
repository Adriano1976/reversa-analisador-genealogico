# Interface: provedor de identidade (Google OAuth 2.0)

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Tipo: HTTP de saída — primeiro contrato de rede com terceiro do sistema
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Papel

O sistema delega ao Google a prova de que a pessoa é dona da conta. O sistema **não** recebe senha,
não guarda token de atualização e não pede escopo além de identidade. Todo o tráfego de ida e volta
acontece no servidor, exceto o redirecionamento do navegador para a tela de consentimento.

## 2. Pedido de autorização (navegador)

```text
GET https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=<GOOGLE_CLIENT_ID>
  &redirect_uri=<ANALISADOR_URL_PUBLICA>/callback
  &response_type=code
  &scope=openid%20email%20profile
  &state=<32 bytes url-safe>
  &access_type=online
```

| Parâmetro | Valor | Regra |
|---|---|---|
| `client_id` | configuração | Nunca vai para tela fora deste redirecionamento |
| `redirect_uri` | `<ANALISADOR_URL_PUBLICA>/callback` | Fixo; tem de casar **exatamente** com o cadastrado no Console |
| `scope` | `openid email profile` | Só identidade; nenhum escopo de dado do usuário |
| `state` | aleatório, 32 bytes | Gravado na sessão; de uso único |
| `access_type` | `online` | Sem `refresh_token`: a sessão é do app, não do provedor |
| `prompt` / `login_hint` | não enviados | Entrada em um clique quando já há conta no navegador |

## 3. Troca do código (servidor)

```text
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code=<code>&client_id=<id>&client_secret=<segredo>
&redirect_uri=<ANALISADOR_URL_PUBLICA>/callback&grant_type=authorization_code
```

| Item | Contrato |
|---|---|
| Sucesso | `200` com `access_token`, `expires_in`, `token_type` e, por `openid` no escopo, `id_token` |
| Falha esperada | `400`/`401` com `error` (`invalid_grant`, `redirect_uri_mismatch`, `invalid_client`) |
| Tempo limite | **10 s** |
| Retentativa | nenhuma automática; o operador repete a entrada |
| Uso do token | uma chamada de perfil; não é persistido em lugar nenhum |

## 4. Leitura do perfil (servidor)

```text
GET https://openidconnect.googleapis.com/v1/userinfo
Authorization: Bearer <access_token>
```

| Campo | Uso | Obrigatório |
|---|---|---|
| `sub` | **o dono**; vai para a sessão e para `owner_id` | sim |
| `email` | rótulo de tela e decisão da adoção dos dados anteriores | sim |
| `email_verified` | pré-condição da adoção e da conta | sim — o retorno precisa ser verdadeiro |
| `name` | rótulo da masthead | não (cai para o e-mail) |

- `sub` ausente ou vazio → falha: não existe identidade a usar.
- `email` ausente, ou `email_verified` falso → falha.
- Tempo limite: **10 s**.

## 5. Mapeamento de erro para a tela

| Origem | Frase na tela | Log |
|---|---|---|
| Retorno com `error` (inclusive `access_denied`) | `A entrada foi cancelada.` | uma linha com o código do erro |
| Troca do código falha | `Não foi possível concluir a entrada agora.` | status e `error` do provedor; nunca `code`, token ou segredo |
| Perfil sem e-mail ou não verificado | `Não foi possível concluir a entrada agora.` | o motivo, sem o perfil |
| Tempo limite em qualquer chamada | `Não foi possível concluir a entrada agora.` | a chamada e o tempo |

## 6. O que o sistema **não** consome

- `id_token`: devolvido e ignorado. A identidade vem do endpoint de perfil, sobre TLS, com token que
  nunca sai do servidor — por isso não há validação de assinatura, JWKS nem biblioteca de criptografia.
- `refresh_token`: não pedido (`access_type=online`); a sessão do app não é renovada no provedor.
- Qualquer API do Google além de `userinfo`.

## 7. Segredos e rastro

- `client_secret`, `access_token`, `code` e `state` **nunca** entram em URL de tela, log, trilha de
  auditoria ou mensagem de erro.
- A trilha grava `conta=<sub>`; o e-mail não.
- O `ANALISADOR_SECRET_KEY` assina o cookie e não tem relação com o provedor.

## 8. Verificação manual (onboarding)

1. Abrir `/login` e clicar em **Entrar com Google**.
2. Conferir que a URL do provedor carrega `redirect_uri` igual à cadastrada e um `state` novo.
3. Voltar autenticado e conferir a masthead.
4. Repetir com `?iniciar=1` duas vezes seguidas: o segundo fluxo invalida o primeiro.
5. Cancelar o consentimento: a tela precisa dizer `A entrada foi cancelada.` sem criar sessão.
