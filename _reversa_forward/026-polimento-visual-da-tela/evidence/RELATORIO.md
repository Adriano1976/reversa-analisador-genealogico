# Relatório da feature: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Execução: `/reversa-coding`, ações `T001` a `T014` (a `T015` é do estágio `/reversa-sync`)

## 1. O que mudou

Uma única edição de apresentação em `src/assets/app.css`: a família curta de tokens de estado
(`--ok`, `--poss`, `--conf`, `--inc`) saiu, a família `--st-*` ficou como única declaração das quatro
cores, o token do `INCONCLUSIVO` ganhou o comentário que proíbe o alias com `--muted`, o comentário
dos estados ganhou os quatro contrastes medidos e os dois comentários do bloco do banner passaram a
descrever a arte atual.

## 2. Antes e depois

| Métrica | Antes | Depois |
|---------|-------|--------|
| Bytes de `src/assets/app.css` | 22.224 | 23.242 |
| Linhas de `src/assets/app.css` | 391 | 399 |
| Definições de token de estado | 8 (4 curtas + 4 `--st-*`) | 4 (`--st-*`) |
| Tokens mortos (`--ok/--poss/--conf/--inc`) | 4 | 0 |
| Contraste branco/`INCONCLUSIVO` | 6,11:1 | 6,11:1 |
| `SHA_DA_TELA` de `GET /` | `c4a34f7b…` (30.781 bytes) | `c4a34f7b…` (30.781 bytes) |
| Guardas da tela (`3` arquivos) | 90 passam | 90 passam |
| Suíte completa | 1.048 passam, 9 pulados, 0 falham | 1.048 passam, 9 pulados, 0 falham |

`git diff --numstat` da folha: **15 inserções, 7 remoções**. Nenhuma regra de cor aplicada mudou de
valor.

## 3. Contrastes documentados na folha

| Estado | Fundo | Texto | Contraste |
|--------|-------|-------|-----------|
| `COMPATIVEL` | `#2F6B3A` | `#fff` | 6,39:1 |
| `POSSIVEL` | `#7A4F00` | `#fff` | 7,13:1 |
| `CONFLITANTE` | `#A8321F` | `#fff` | 6,69:1 |
| `INCONCLUSIVO` | `#6A6150` | `#fff` | 6,11:1 |

O caso histórico do laranja (`#fd7e14` = 2,57:1) foi preservado no comentário, como precedente.
O alias proibido (`--muted` no tema escuro, `#A99F88`) mede 2,62:1 e é reprovado pelo teste.

## 4. Escopo

- `git diff --stat -- src/ tests/` lista **apenas** `src/assets/app.css`.
- `git diff --stat -- src/templates src/app.py tests` é **vazio**: o documento, a borda e os testes não
  foram tocados.
- Existe uma modificação em `.gitignore` **anterior à feature**: ela já aparecia no `git status` da
  linha de base (`evidence/antes/suite.txt`, HEAD `f49bc47`) e não foi produzida por esta execução.
  Não foi revertida (trabalho de outra sessão; a política é não destruir).
- O `HEAD` mudou de `c12fcea` para `f49bc47` antes da linha de base, por um commit de documentação de
  outra sessão. Nenhum arquivo de `src/` entrou nesse commit.

## 5. Prova por execução

| Prova | Arquivo |
|-------|---------|
| Linha de base (HEAD, status, suíte) | `evidence/antes/suite.txt` |
| Guardas da tela antes | `evidence/antes/testes-da-tela.txt` |
| Recorte da folha antes | `evidence/antes/folha.txt` |
| Guardas da tela depois | `evidence/depois/testes-da-tela.txt` |
| Suíte depois | `evidence/depois/suite.txt` |
| Escopo do diff | `evidence/depois/escopo.txt` |
| Conferência da tela (medição) | `evidence/depois/tela.md` |

## 6. Conclusão

A feature cumpre os requisitos sem mudança de comportamento observável: as cores efetivas, o
documento, as rotas e os textos permanecem idênticos. O que passa a existir é a **declaração única**
da cor de cada estado, a **medição escrita** ao lado da regra e a **correção dos comentários** que
sustentavam a premissa vencida do banner.

A ação `T015` (adendo `026` em `_reversa_sdd/addenda/`) fica para o `/reversa-sync`, como declarado
no `actions.md`.
