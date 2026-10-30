# Onboarding: testar a entrada com senha pela primeira vez

> Identificador: `053-conta-com-senha-e-recuperacao`
> Data: `2026-10-30`
> Requirements: `_reversa_forward/053-conta-com-senha-e-recuperacao/requirements.md`

Este roteiro é para uma pessoa que nunca viu a feature. Ele leva de zero a uma conta criada, confirmada, usada e recuperada, sem precisar ler o código. Use **dados sintéticos** em todo o caminho: o princípio I proíbe GEDCOM, DNA, nome ou e-mail de terceiros em teste, fixture, log ou captura de tela.

## 1. Pré-requisitos

| Item | Como conferir |
|---|---|
| `git`, Python 3.14 e o `.venv` do projeto | `py -3.14 --version` e `.venv\Scripts\python --version` |
| Dependências instaladas no `.venv` | `.venv\Scripts\python -m pip install -r requirements.txt` |
| Uma caixa de e-mail de teste | Um endereço que você controla, **não** o de outra pessoa |
| Credencial SMTP de teste | Servidor, porta, usuário, senha e remetente (o `.env` não é versionado) |

## 2. Configurar o ambiente

Crie ou edite o `.env` na raiz do projeto. As cinco variáveis da 051 continuam obrigatórias para a instância subir; as do e-mail são novas:

```ini
# Entrada Google (já existentes desde a 051)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ANALISADOR_SECRET_KEY=...
ANALISADOR_URL_PUBLICA=http://127.0.0.1:5080
ANALISADOR_DONO_INICIAL=voce@example.com

# Envio de e-mail (novas nesta feature)
ANALISADOR_SMTP_HOST=smtp.exemplo.test
ANALISADOR_SMTP_PORT=587
ANALISADOR_SMTP_USUARIO=usuario-de-teste
ANALISADOR_SMTP_SENHA=senha-de-teste
ANALISADOR_SMTP_REMETENTE=nao-responda@exemplo.test
ANALISADOR_SMTP_SEGURANCA=starttls
```

`ANALISADOR_URL_PUBLICA` é o que forma os links dos e-mails. Em uso local, `http://127.0.0.1:5080`; em uso compartilhado, **precisa** ser `https://…`, senão o cookie não ganha `Secure`.

> Sem `ANALISADOR_SMTP_HOST` e `ANALISADOR_SMTP_REMETENTE`, a instância sobe, mas cadastro e recuperação avisam que o envio não está configurado. É o comportamento esperado (`RN-18`).

## 3. Rodar a suíte antes de mexer na tela

```powershell
.venv\Scripts\python -m pytest -q
```

Espere o mesmo marco da linha de base (1.801 passam, 9 pulados, 5 falham — as cinco falhas são pré-existentes, `addenda/052`). Se o número de falhas mudar, pare: a feature não está pronta para o roteiro manual.

## 4. Subir a aplicação

```powershell
.venv\Scripts\python src\app.py
```

A aplicação escuta em `127.0.0.1:5080` (ou na porta que o compose publica). Abra `http://127.0.0.1:5080/login`.

## 5. Roteiro manual

1. **A tela de entrada.** Confira: banner no topo do cartão, na posição de antes; título `Entre na sua conta`; botão `Entrar com Google` **acima** dos campos; `E-mail` e `Senha`; botão `Entrar` **verde**; links `Esqueci minha senha` e `Criar conta`; e o ícone do app na **aba** do navegador.
2. **Senha fraca.** Em `Criar conta`, tente `abc123`. Espere a recusa nomeando o que falta (oito caracteres, maiúscula, minúscula, número, especial) e **nenhuma** conta criada.
3. **Cadastro válido.** Use um e-mail de teste e uma senha como `Teste#2026`. A tela deve mostrar `Se este e-mail puder ser usado, enviaremos as instruções.` e **nenhuma** sessão aberta.
4. **Confirmação.** Abra o e-mail, clique no link e espere `E-mail confirmado. Entre com a sua senha.`. Volte para `/login`.
5. **Entrada.** Entre com o e-mail e a senha. Espere cair na tela principal, com a conta na masthead. Recarregue: a sessão persiste.
6. **Falha indistinguível.** Saia, tente senha errada e tente um e-mail que não existe. As duas respostas precisam ser idênticas (`E-mail ou senha inválidos.`).
7. **Cadastro duplicado.** Saia e tente criar conta de novo com o mesmo e-mail. A tela deve mostrar a **mesma** frase do passo 3, e o dono do endereço recebe um e-mail de "conta já existente". Nada é criado.
8. **Recuperação.** Em `Esqueci minha senha`, peça o link. Espere a frase genérica e o e-mail com o link de 60 minutos. Defina uma senha nova (diferente) e entre com ela.
9. **Revogação.** Antes do passo 8, deixe uma segunda janela aberta e autenticada. Depois da redefinição, recarregue essa janela: ela precisa voltar para `/login`.
10. **Conta Google ganha senha.** Entre com o Google, use `Definir senha` na masthead, defina uma senha e saia. Entre agora com e-mail e senha: você precisa cair na **mesma** conta, com os **mesmos** arquivos.
11. **Isolamento.** Crie uma segunda conta confirmada e envie um GEDCOM sintético na primeira. Na segunda, a lista não pode mostrar o arquivo da primeira, e uma referência direta precisa responder `404`.
12. **Durabilidade e concorrência.** Pare a aplicação e suba de novo: as duas contas continuam lá. Em teste automatizado, duas criações simultâneas precisam resultar em duas contas, sem corromper o arquivo.
13. **Limite.** Erre a senha seis vezes em quinze minutos: a resposta continua genérica, e o acesso com a senha certa só volta depois da janela.
14. **Sem SMTP.** Remova `ANALISADOR_SMTP_HOST`, suba de novo e peça recuperação: a tela precisa dizer que o envio não está configurado, e o login de conta confirmada precisa continuar funcionando.
15. **Mostrar e esconder senha.** O ícone de olho já aparece à direita do campo de senha, mesmo vazio. Clique no olho — a senha fica legível e o ícone vira olho cortado —, clique de novo e confira que volta a ficar oculta. Com JavaScript desabilitado no navegador, o ícone **não** aparece e o campo continua funcionando como senha.

## 6. Conferir o que ficou gravado

O arquivo de contas fica em `src/dados/contas.json` (ou no caminho de `ANALISADOR_CONTAS`).

```powershell
Get-Content src\dados\contas.json -Raw | ConvertFrom-Json |
  Select-Object -ExpandProperty contas |
  ConvertTo-Json -Depth 5
```

O que conferir:

- `credencial.hash` e `credencial.sal` existem; **nenhum** campo contém a senha digitada.
- `verificado_em` preenchido depois do passo 4.
- `versao_de_credencial` maior depois do passo 8.
- `tokens` vazio ou só com o token vigente — nunca o texto do token.
- O arquivo **não** aparece no `git status`.

## 7. Conferir logs e auditoria

Procure a trilha de auditoria (`logs/`):

```powershell
Select-String -Path logs\*.log -Pattern "acao=(cadastrar|confirmar|definir_senha|pedir_senha|redefinir_senha|entrar|sair)"
```

- Cada linha tem `conta=<sub>`.
- **Nenhuma** linha contém e-mail, senha ou token.
- Falha de envio aparece como aviso com motivo curto.

## 8. Limpeza

1. Apague as contas de teste: remova `src/dados/contas.json` (ou as chaves de teste) com a aplicação parada.
2. Apague as pastas de upload das contas de teste em `src/uploads/`.
3. Não commite `.env`, `src/dados/` nem `src/uploads/` — os três já estão cobertos pelo `.gitignore`.

## 9. O que não fazer

- Não use e-mail, nome ou árvore de outra pessoa para testar.
- Não cole captura de tela com dado real em issue, chat ou documentação.
- Não configure o SMTP com uma conta pessoal principal: use uma caixa dedicada ao teste.
- Não abra a instância para a rede antes de ler os portões de abertura na seção 10 do `requirements.md` (TLS, cota, retenção, convite, entregabilidade).
