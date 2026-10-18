# Onboarding: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md`

## 1. O que esta feature faz, em uma frase

Traz os alertas de retorno para a paleta, alivia a ação principal no desktop, desce um degrau a escala
do `h1` e da arte do topo e corrige o comentário que descrevia a introdução como alinhada à esquerda —
**sem tocar no alinhamento** (que é a `RN-24`) e sem tocar nos cartões de resultado.

## 2. O que você precisa ter

- O `.venv` oficial (Python 3.14.6) com as dependências do `requirements.txt`.
- `DATABASE_URL` **ausente** do ambiente.
- Um navegador com DevTools e o modo de dispositivo responsivo.
- Nenhum dado real: o passo 2 cria um GEDCOM sintético de três linhas.

## 3. Passo a passo

### Passo 0 — congelar a linha de base

```powershell
git status --porcelain
git log -1 --oneline
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: **1.048 passam, 9 pulados, 0 falham**. Registre também o `sha256` atual de `GET /` (o
`SHA_DA_TELA` em `tests/test_icone_de_atalho.py`) para comparar no passo 6.

### Passo 1 — subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5000/`.

### Passo 2 — conferir o alerta de sucesso e o de erro

1. Crie um arquivo `sintetico.ged` com exatamente:

   ```text
   0 HEAD
   0 @I1@ INDI
   1 NAME Teste /Silva/
   0 TRLR
   ```

2. Envie pela aba **Buscar Conexão no GEDCOM**. O alerta de sucesso aparece no topo.
3. Confira em DevTools → Elements/Computed:
   - o fundo é o token `--sucesso-bg` (claro `#EDF4E6`, escuro `#1E2A17`);
   - a borda é `--sucesso-line` (claro `#3F6B2E`, escuro `#8DBB6E`) e está **visível**;
   - o texto usa `--ink` e não a cor padrão do framework.
4. Clique no **X** do alerta: ele deve fechar normalmente.
5. Repita com o tema escuro (botão no canto): o alerta escurece e o X continua visível.
6. Para o alerta de erro, envie um arquivo com extensão `.ged` mas **sem `0 HEAD`** (um `.txt`
   renomeado serve). O alerta de perigo deve aparecer com a mesma forma, em `--perigo-*`.

> Se o upload guardar o arquivo sintético, aposente-o depois pela própria tela.

### Passo 3 — conferir a ação principal

1. Com a janela em **mais de 576 px**, abra a aba com o formulário e confira: o botão de ação **não**
   ocupa a largura do cartão; ele tem largura natural e altura menor.
2. No modo responsivo, com **menos de 576 px**, o botão volta a ocupar a largura total.
3. O mesmo vale para os três botões (Carregar, Encontrar Conexão, Analisar Matches de DNA), porque a
   regra é a mesma.

### Passo 4 — conferir a escala do topo

1. O `h1` "Analisador Genealógico" deve medir **no máximo 2,2 rem** (35,2 px) em tela larga.
2. A arte do topo deve medir **no máximo 280 px** de largura.
3. O `h1` continua o maior texto da tela, acima dos títulos dos cartões (1,2 rem).

### Passo 5 — confirmar que a introdução não mudou

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_banner_do_topo.py::TestTopoDaTela::test_o_texto_de_apresentacao_esta_centralizado_e_em_coluna_estreita -q
```

Esperado: **1 passed**. O texto continua dentro de `row justify-content-center` + `col-lg-*`, e não
existe `text-start` no documento. A `RN-24` está preservada.

### Passo 6 — conferir a declaração da tela

1. O `SHA_DA_TELA` mudou (a mudança do comentário entra no HTML servido).
2. O novo valor está em `tests/test_icone_de_atalho.py`, com um bloco datado explicando a contribuição.
3. O teste do hash passa:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_icone_de_atalho.py -q
```

### Passo 7 — rodar as guardas e a suíte inteira

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_banner_do_topo.py tests\test_estilo_da_tela.py tests\test_icone_de_atalho.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --stat
```

Esperado: guardas verdes; suíte em **1.048 / 9**; `git diff --stat` listando **apenas**
`src/assets/app.css` e `src/templates/index.html`.

### Passo 8 — registrar

Grave a saída dos passos 0, 5, 6 e 7 em `evidence/`. O adendo `027` é escrito no `/reversa-sync`.

## 4. Como interpretar o resultado

Esta feature **não** alinha o texto da introdução ao formulário: isso foi decidido em 2026-10-10
(`RN-24`) e continua valendo. O que muda é:

- a cor e a forma dos alertas de retorno;
- o peso da ação principal no desktop;
- a escala do `h1` e da arte do topo;
- um comentário que descrevia o layout errado.

Os cartões de resultado, o selo de cM e os textos continuam exatamente como estavam.

## 5. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| O X do alerta some no tema escuro | ícone do framework não invertido ou sobreposto | conferir o `filter` do `.btn-close` no escuro; o teste de contraste não pega ícone |
| O alerta dentro do cartão de DNA mudou de cor | regra genérica `.alert` pegou o `.alert-warning` | restringir a `.alert-success` e `.alert-danger` |
| O botão continua em barra no desktop | a regra está fora da media query ou o seletor não casa | conferir `.d-grid > .btn` dentro de `@media (min-width:576px)` |
| O teste da `RN-24` falha | alguém tocou no markup da introdução | reverter o markup; o comentário é o único texto a mudar ali |
| O teste do hash falha | o valor não foi atualizado ou foi atualizado sem recalcular | medir o `sha256` do HTML servido e atualizar com o bloco datado |
| `PermissionError` em `tests/.tmp` | permissão de pasta do Windows/sandbox | rodar em workspace com escrita liberada |
