# Onboarding — feature 054

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Para quem nunca viu esta feature: este roteiro leva do zero à conferência de que a tela abre **sem internet**,
> com o mesmo desenho, o mesmo diagrama e as mesmas abas.

## 1. Pré-requisitos

- Windows com PowerShell, o projeto em `D:\Projetos\reversa_analisador_gelealogico`.
- O interpretador oficial é o do projeto: `.\.venv\Scripts\python.exe`.
- Nenhuma conta, nenhum SMTP e **nenhuma rede** são necessários para a conferência — é justamente o ponto.

## 2. Subir a aplicação

Há dois caminhos. O primeiro é o do dia a dia; o segundo é o atalho para conferir a tela principal sem passar
pela entrada.

**Caminho A — modo de identidade `local` (o de uso real):**

```powershell
$env:ANALISADOR_MODO = "local"
.\.venv\Scripts\python.exe src\app.py
```

A aplicação sobe em `http://127.0.0.1:5000/` e a primeira tela é a de entrada. Para chegar à tela principal é
preciso uma conta confirmada — e a confirmação passa por e-mail (SMTP). Sem SMTP, o cadastro não conclui.

**Caminho B — escape de teste (só para esta conferência, só em `localhost`):**

```powershell
$env:ANALISADOR_MODO_TESTE = "1"
.\.venv\Scripts\python.exe src\app.py
```

O escape dispensa a declaração de modo e a aplicação sobe no caminho legado, **sem guarda de sessão**: você cai
direto na tela principal. Use apenas na sua máquina e nunca como configuração de produção.

Em qualquer caminho, a porta pode ser trocada com `$env:ANALISADOR_PORT = "5055"` se a 5000 estiver ocupada.

## 3. Conferência 1 — de onde vêm os recursos

1. Abra `http://127.0.0.1:5000/`.
2. Abra as ferramentas de desenvolvimento do navegador (`F12`) na aba **Rede** e recarregue com `Ctrl+F5`.
3. Confira que **nenhuma** requisição vai para `cdn.jsdelivr.net`, `fonts.googleapis.com` ou `fonts.gstatic.com`.
4. Confira que aparecem, com `200`:

| Requisição | Tipo de mídia esperado |
|------------|------------------------|
| `/bootstrap.css` | `text/css` |
| `/fontes.css` | `text/css` |
| `/app.css` | `text/css` |
| `/mermaid.js` | `text/javascript` |
| `/bootstrap.js` | `text/javascript` |
| `/fontes/<algo>.woff2` (só os subconjuntos usados) | `font/woff2` |

5. Recarregue de novo (sem `Ctrl+F5`) e confira que os recursos voltam como `304` ou saem do cache — não como
   `200` com o corpo inteiro.

## 4. Conferência 2 — a tela sem internet

1. Na aba **Rede** do navegador, marque **Offline** (ou desligue o adaptador de rede).
2. Recarregue a página (`Ctrl+F5` — o `F5` comum pode reaproveitar o cache).
3. Verifique, na ordem:
   - a página sai **com** estilo: cabeçalho, arte do topo, cartões, botões e tabelas com o desenho de sempre;
   - o título sai em `Cormorant Garamond` e o texto em `Manrope` (compare com a captura de antes da mudança: as
     letras não podem ter virado `Georgia`/`Segoe UI`);
   - o botão de tema alterna claro/escuro e a escolha sobrevive ao recarregar;
   - com uma árvore aberta e uma análise feita, as três abas das fases alternam ao clique (e com ↑/↓ na barra
     lateral);
   - o diagrama da conexão é desenhado, com o mesmo traço e as mesmas cores de antes;
   - um alerta dispensável fecha no `×`.
4. Faça uma captura de tela e guarde em `evidence/` (dado sintético apenas — use `SAMPLE_GED`; nunca um GEDCOM
   real).

## 5. Conferência 3 — as telas de identidade

1. No modo `local` (caminho A), abra `http://127.0.0.1:5000/login`.
2. Com a rede desligada, recarregue e confira que o cartão, o banner, os campos e o botão continuam com o desenho
   de hoje.
3. Confira a tipografia: estas telas **não** carregam a webfont hoje, e devem continuar iguais — se o texto delas
   aparecer em `Cormorant`/`Manrope`, algo vazou a folha de fontes para a base e a mudança não foi declarada.
4. Repita em `/cadastro` e `/recuperar-senha` (as demais herdam da mesma base).

## 6. Conferência 4 — dentro do contêiner

A imagem é a forma de uso real, e o `.dockerignore` é lista de permissão: um recurso fora de `src/` responderia
`200` no host e `404` na imagem.

```powershell
docker compose build
docker compose run --rm app python tests\verificacao_no_conteiner.py
```

Confira que a verificação reporta `OK` para `/bootstrap.css`, `/bootstrap.js`, `/mermaid.js`, `/fontes.css` e para
os `woff2`, além das rotas de arte que já existiam.

## 7. Conferência 5 — o que não pode ter mudado

1. `git status` não pode listar `src/uploads/` nem `src/dados/`.
2. `src/static/` continua **inexistente** (o teste que a proíbe continua passando).
3. O `requirements.txt` não tem linha nova.
4. A ordem das folhas no `<head>` continua Bootstrap antes de `app.css`.
5. O script do Bootstrap continua no fim do `<body>`, e o do Mermaid no `<head>`.

## 8. Rodar a suíte

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe tests\rodar_paridade.py
```

## 9. Se algo der errado

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| A tela continua sem estilo | o navegador serviu o HTML do cache, ou a rota do Bootstrap respondeu `404` | `Ctrl+F5`; confira `/bootstrap.css` direto na barra de endereços |
| O diagrama sai em branco | `/mermaid.js` não carregou, ou o `<script>` saiu depois do bloco que usa `mermaid` | confira a ordem no `<head>` e o console do navegador |
| As abas não alternam | `/bootstrap.js` não carregou | confira o `200` da rota e o console (erro de script interrompe o resto) |
| O texto perdeu a tipografia | `/fontes.css` não carregou, ou os `woff2` deram `404` | confira as requisições de fonte: devem ser locais e `200` |
| `404` em `/fontes/<nome>.woff2` | o nome não está no conjunto fechado da receita | rode o teste de fontes; se o CSS foi regerado, atualize a constante dos nomes |
| O teste do `SHA_DA_TELA` falha | a tela mudou e a declaração não foi feita | declare o delta no adendo; **não** atualize o valor sem registrar a razão |
| A verificação no contêiner dá `FALHA` num recurso | o arquivo não entrou na imagem | confira se ele está sob `src/assets/` e se o `.dockerignore` continua permitindo `!src/**` |
