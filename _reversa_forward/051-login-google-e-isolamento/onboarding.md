# Onboarding: testar o login com Google pela primeira vez

> Identificador: `051-login-google-e-isolamento`
> Data: `2026-10-26`
> Para quem vai executar: o operador (Adriano), em uma máquina com o `.venv` do projeto.

Este roteiro leva do zero ao isolamento provado com **duas contas Google**. Ele usa dado sintético
no passo 8; os passos 5 e 6 tocam os arquivos reais do operador, e é por isso que a migração **copia**
em vez de mover.

## 1. Pré-requisitos

- Projeto clonado, `.venv/` criado e as dependências instaladas (`python -m pip install -r requirements.txt`).
- Acesso ao [Google Cloud Console](https://console.cloud.google.com/) com a conta que será a **conta inicial**.
- Internet no navegador do operador (a aplicação passa a depender do provedor para entrar).
- Opcional: Docker, se o banco do histórico for usado.

## 2. Criar o cliente OAuth no Google

1. No Console, crie (ou escolha) um projeto.
2. Em **APIs e serviços → Tela de consentimento OAuth**, escolha **Externo** e preencha nome do app,
   e-mail de suporte e e-mail do desenvolvedor. Enquanto o app estiver em **Teste**, só as contas
   cadastradas em **Usuários de teste** conseguem entrar — cadastre a conta inicial e a segunda conta.
3. Em **APIs e serviços → Credenciais → Criar credenciais → ID do cliente OAuth**, escolha
   **Aplicativo da Web**.
4. Em **URIs de redirecionamento autorizados**, cadastre as quatro, exatamente assim (a porta e o
   nome do host participam da comparação):

   ```text
   http://127.0.0.1:5000/callback
   http://localhost:5000/callback
   http://127.0.0.1:5080/callback
   http://localhost:5080/callback
   ```

5. Copie o **ID do cliente** e a **chave secreta**. A chave só aparece uma vez.

## 3. Configurar as cinco variáveis

| Variável | Exemplo | Para que serve |
|---|---|---|
| `GOOGLE_CLIENT_ID` | `1234567890-abc.apps.googleusercontent.com` | Identifica o app no provedor |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | Troca o código pelo token, no servidor |
| `ANALISADOR_SECRET_KEY` | saída de `secrets.token_urlsafe(48)` | Assina o cookie de sessão; **nunca** versionar |
| `ANALISADOR_URL_PUBLICA` | `http://127.0.0.1:5000` | Monta a URL de retorno; tem de casar com a cadastrada |
| `ANALISADOR_DONO_INICIAL` | o e-mail da conta inicial | Diz quem herda os dados anteriores |

Gere o segredo com:

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

No PowerShell da sessão:

```powershell
$env:GOOGLE_CLIENT_ID="..."
$env:GOOGLE_CLIENT_SECRET="..."
$env:ANALISADOR_SECRET_KEY="..."
$env:ANALISADOR_URL_PUBLICA="http://127.0.0.1:5000"
$env:ANALISADOR_DONO_INICIAL="seu-email@gmail.com"
```

Para o Docker, as mesmas cinco entram no `.env` (que o `.gitignore` já exclui). O `docker-compose.yml`
passa a usá-las com `${VAR:?}`, que **para** a subida se faltar alguma — mesmo padrão das credenciais do
banco.

## 4. Subir

```powershell
.venv\Scripts\python.exe src\app.py
```

Esperado: a linha de inicialização de sempre. Se faltar qualquer uma das cinco variáveis, o processo
**não sobe** e a mensagem nomeia as que faltam.

Pelo Docker:

```powershell
docker compose up -d --build
```

## 5. Primeiro login e migração

1. Abra `http://127.0.0.1:5000`. A resposta é a tela de entrada, com o botão **Entrar com Google**.
2. Clique e escolha a **conta inicial** (a mesma de `ANALISADOR_DONO_INICIAL`).
3. Depois do retorno, a tela principal abre com o nome da conta na masthead e o botão **Sair**.
4. A lista deve mostrar os arquivos que já existiam. Confira no disco:

   ```powershell
   Get-ChildItem src\uploads
   Get-ChildItem src\uploads\<sub>          # os 13 arquivos, copiados
   Get-Content src\uploads\.dono-inicial    # o sub, uma linha
   ```

   O `<sub>` é um número longo. Se a lista estiver vazia e houver arquivos na raiz, o e-mail de
   `ANALISADOR_DONO_INICIAL` não casa com a conta que entrou — ver o diagnóstico no passo 10.

## 6. Segundo login, com outra conta

1. **Sair** e entrar com a segunda conta Google (precisa estar em **Usuários de teste**).
2. Esperado: as duas abas **vazias**, e nenhum rótulo de arquivo da primeira conta no HTML.
3. Prova manual do isolamento: com a primeira conta, abra o DevTools de um cartão de resultado e copie
   o valor de `gedcom_filename`; com a segunda conta, envie esse valor num `POST` (por exemplo, pelo
   console do navegador, trocando o campo oculto do formulário). Esperado: a mensagem
   `Erro: Arquivo '<rótulo>' não existe mais.` e status `404` — **nunca** `403` e nunca a árvore.
4. A prova automatizada é o portão: `tests/test_isolamento_por_dono.py` cobre as cinco operações.

## 7. Sair e expirar

- **Sair** limpa o cookie e devolve a tela de entrada; o botão "voltar" não reabre a tela autenticada
  (as respostas autenticadas saem com `Cache-Control: no-store`).
- A sessão expira em **12 horas de inatividade**. Para testar sem esperar, apague o cookie
  `analisador_sessao` nas ferramentas do navegador e recarregue: a próxima operação pede entrada.

## 8. Auditoria

Com a aplicação em uso, `logs/auditoria-<data>.log` passa a ter linhas de entrada e saída:

```text
acao=entrar desfecho=sucesso ip=... origem=... conta=<sub>
acao=sair desfecho=sucesso ip=... origem=... conta=<sub>
```

O e-mail da conta **não** aparece na trilha, por decisão de privacidade (`RN-12`).

## 9. Voltar ao estado anterior

Não existe modo legado servível, por decisão (`D3`/`RN-16`). Para desligar a entrada:

1. Reverta o commit da feature (o código anterior não tem a guarda).
2. Se o layout novo tiver sido usado, os arquivos originais **continuam na raiz** de `src/uploads/` —
   basta remover a pasta `<sub>` e o marcador `.dono-inicial` para a aplicação antiga voltar a vê-los.

## 10. Diagnóstico

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `redirect_uri_mismatch` na tela do Google | URL de retorno diferente da cadastrada (host, porta, `http`/`https` ou barra final) | Conferir `ANALISADOR_URL_PUBLICA` contra a lista do passo 2.4 |
| O servidor não sobe e lista variáveis | Falta uma das cinco | Definir a que falta; a mensagem nomeia todas |
| `400` com `Host '...' is not trusted` | O acesso saiu do loopback sem a lista de hosts | Usar `127.0.0.1`/`localhost` ou acrescentar o host em `ANALISADOR_HOSTS_PERMITIDOS` |
| Lista vazia, com arquivos na raiz de `src/uploads/` | `ANALISADOR_DONO_INICIAL` não é o e-mail da conta que entrou | Corrigir a variável e entrar de novo; o log avisa que há dados não atribuídos |
| `500` no retorno do provedor | `requests` ausente no interpretador | `python -m pip install -r requirements.txt`; com a autenticação ligada, a ausência impede a subida |
| Entrada cancelada ou expirada | Fluxo abandonado ou cookie perdido | Repetir a entrada; a tela explica o motivo |
| Nenhum dado antigo no histórico do banco | `DATABASE_URL` ausente na primeira entrada | Subir com a variável e entrar de novo; a adoção roda no próximo login enquanto o marcador não existir |
