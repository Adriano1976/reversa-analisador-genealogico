# Onboarding: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Requirements: `_reversa_forward/026-polimento-visual-da-tela/requirements.md`

## 1. O que esta feature faz, em uma frase

Consolida as cores dos quatro estados do confronto numa única família de tokens, documenta o
contraste de cada um e corrige os comentários da folha que ainda descrevem a arte do topo antiga —
**sem mudar nada do que o operador vê**.

## 2. O que você precisa ter

- O repositório no estado do commit da feature, com o `.venv` oficial (Python 3.14.6).
- `waitress` instalado no `.venv` (vem do `requirements.txt`).
- `DATABASE_URL` **ausente** do ambiente: a suíte tem casos que dependem disso.
- Um navegador com DevTools, para conferir a cor computada dos selos.
- Nenhum dado real é necessário: a tela de entrada vazia já serve para tudo, e nenhum passo lê árvore
  ou CSV.

## 3. Passo a passo

### Passo 0 — congelar a linha de base

```powershell
git status --porcelain
git log -1 --oneline
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: árvore limpa (ou só artefatos de outra sessão, nunca `src/`), HEAD registrado e suíte com
**1.048 passam, 9 pulados, 0 falham**. Guarde a saída em `evidence/antes/suite.txt` se for registrar
evidência.

> Se o pytest falhar com `PermissionError` em `tests/.tmp`, é permissão de pasta do Windows, não a
> feature. Rode em um workspace com escrita liberada (ver §5).

### Passo 1 — subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5000/`. A tela de entrada vazia basta: ela carrega o `<head>`, o botão de tema
e o topo, que é tudo o que esta feature toca.

### Passo 2 — conferir o ícone da aba e o ícone de atalho

1. Na aba do navegador, o ícone continua aparecendo (é o `data URI` embutido).
2. Em DevTools → Elements, o `<head>` tem **um** `link rel="icon"` e **nenhum** `apple-touch-icon`.
3. Na barra de endereço, abra:

```text
http://127.0.0.1:5000/apple-touch-icon.png
```

Deve responder a imagem 180×180 (o atalho é descoberto por convenção, sem declaração no documento).

4. Abra `http://127.0.0.1:5000/favicon.ico`: deve responder **404**, e isso é o contrato.

### Passo 3 — conferir a cor do estado `INCONCLUSIVO`

1. Na tela de entrada, abra DevTools → Console e crie um selo só para inspeção (nenhum dado real é
   necessário):

   ```javascript
   const selo = document.createElement('span');
   selo.className = 'badge estado-INCONCLUSIVO';
   selo.textContent = 'Inconclusivo';
   document.querySelector('.card-body').prepend(selo);
   ```

   O selo aparece no topo do cartão e pode ser inspecionado como qualquer elemento da tela.

2. Em DevTools → Elements, selecione `span.badge.estado-INCONCLUSIVO` e confira em **Computed**:
   - `background-color` = `rgb(106, 97, 80)` (`#6A6150`);
   - `color` = `rgb(255, 255, 255)`.
3. Faça a mesma conferência no **tema escuro** (botão no canto superior direito): os dois valores
   continuam os mesmos. O selo **não** acompanha o `--muted` do tema escuro (`#A99F88`).
4. Se quiser medir: branco sobre `#6A6150` = **6,11:1**, acima dos 4,5:1 de WCAG AA.
5. Ao terminar, remova o selo de inspeção com `document.querySelector('.badge.estado-INCONCLUSIVO').remove()`.

### Passo 4 — conferir a limpeza dos tokens

```powershell
Select-String -Path src\assets\app.css -Pattern '^\s*--(ok|poss|conf|inc):'
```

Esperado: **nenhuma linha**. As cores dos estados continuam declaradas em `--st-compativel`,
`--st-possivel`, `--st-conflitante` e `--st-inconclusivo`.

### Passo 5 — conferir os comentários do bloco do banner

Abra `src/assets/app.css` no fim do arquivo e leia o bloco do banner. Esperado: o comentário declara
que a arte atual **não traz texto** e que o `<h1>` é a identificação em português; a placa branca do
tema escuro continua explicada pela arte desenhada para fundo claro.

### Passo 6 — rodar os testes que cobrem a tela

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_estilo_da_tela.py tests\test_icone_de_atalho.py tests\test_banner_do_topo.py -q
```

Esperado: **zero falhas**. Três guardas importam aqui:

- `TestOContrasteDosSelos` — reprova o selo ilegível nos dois temas, inclusive o alias com `--muted`;
- `test_a_tela_nao_mudou_sem_mudanca_declarada` — o `sha256` de `GET /` continua `c4a34f7b…`;
- `test_o_titulo_do_produto_esta_sempre_visivel` — o `h1` não ganhou `visually-hidden`.

### Passo 7 — provar o escopo e rodar a suíte inteira

```powershell
git diff --stat
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: o diff lista **apenas** `src/assets/app.css`; a suíte repete **1.048 passam / 9 pulados /
0 falhas**. Se o diff listar `src/templates/index.html` ou `tests/`, algo saiu do escopo: pare e
revise.

### Passo 8 — registrar

Grave a saída dos passos 0, 6 e 7 em `evidence/`. No `/reversa-sync`, o adendo
`_reversa_sdd/addenda/026-polimento-visual-da-tela.md` registra as três decisões, a medição e a
declaração de que o documento não mudou.

## 4. Como interpretar o resultado

Esta feature **não promete** mudança visível: as cores efetivas, o layout, os textos e o documento
servido ficam iguais. O que ela entrega é:

- uma cor de estado **sem ambiguidade de fonte**, com a proibição do alias registrada;
- os quatro contrastes **medidos e escritos** ao lado da regra;
- comentários que descrevem a arte que existe hoje.

Se você vir qualquer diferença de cor na tela, ela é defeito, não entrega.

## 5. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| `PermissionError: ... tests\.tmp` no pytest | permissão de pasta do Windows/sandbox, não a feature | rodar em workspace com escrita liberada ou reparar a permissão da pasta `tests` |
| `Recusando subir: 127.0.0.1:5000 ja esta em uso` | outra instância no ar | encerrar a outra ou usar `$env:ANALISADOR_PORT = "5080"` |
| Aviso de persistência no console | `DATABASE_URL` presente sem o driver | remover a variável do ambiente; a suíte espera o caminho silencioso |
| O selo parece acinzentado no tema escuro | é o esperado: o estado não acompanha `--muted` | nada a fazer; é a decisão `D-03` |
| `git diff --stat` mostra o template | alguém tocou o documento | reverter; o `SHA_DA_TELA` e as 8 telas literais não podem mudar |
