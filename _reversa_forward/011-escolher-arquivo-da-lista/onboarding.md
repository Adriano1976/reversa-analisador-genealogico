# Onboarding: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/011-escolher-arquivo-da-lista/requirements.md`
> Roadmap: `_reversa_forward/011-escolher-arquivo-da-lista/roadmap.md`

Este documento é para quem vai **executar e conferir** a feature. Cada passo tem o comando e o que deve
sair. Onde o resultado for um número, o número está declarado — se sair diferente, pare e investigue.

## 1. Pré-requisitos

- PowerShell na raiz do repositório: `D:\Projetos\reversa_analisador_gelealogico`
- Interpretador oficial: `.\.venv\Scripts\python.exe`
- `$env:PYTHONIOENCODING = "utf-8"` na sessão — sem ele, contagem de acento no console do Windows mente
- **`DATABASE_URL` ausente do ambiente.** Com a variável, dois testes de
  `tests/test_persistencia_desabilitada.py` falham e a suíte dá `335 passed, 2 failed, 9 skipped` em vez
  de `337 passed, 9 skipped`. Não é regressão da feature — é o ambiente

```powershell
$env:PYTHONIOENCODING = "utf-8"
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
Write-Output "DATABASE_URL: [$env:DATABASE_URL]"
```

## 2. Linha de base — antes de mexer em qualquer coisa

```powershell
$ev = "_reversa_forward\011-escolher-arquivo-da-lista\evidence"
New-Item -ItemType Directory -Force $ev | Out-Null

# suite
.\.venv\Scripts\python.exe -m pytest -q 2>&1 | Tee-Object "$ev\linha-de-base-suite.txt" | Select-Object -Last 1

# paridade pelo involucro (nunca o harness.py direto)
.\.venv\Scripts\python.exe tests\rodar_paridade.py 2>&1 | Tee-Object "$ev\linha-de-base-paridade.txt" | Select-Object -Last 3

# inventario da pasta: e o que o RF-08 vai comparar no fim
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py duplicatas --pasta src\uploads --relatorio "$ev\duplicatas-antes.txt"
(Get-ChildItem src\uploads -File).Count
```

**Esperado:** suíte em **`335 passed, 9 skipped`** (a linha de base da feature 012 — esta feature
acrescenta testes, então o número depois será maior); paridade em **`PARIDADE 100 %`**; e **19** arquivos
na pasta.

> **Por que a paridade importa aqui.** Esta feature muda o template. Medido por leitura, o harness
> intercepta `render_template` (`harness.py:191`) e lê chaves de contexto (`:211-221`), sem comparar
> HTML — então a mudança deve ser invisível para ele. A premissa de §4 do roadmap diz o mesmo, e este
> passo é a verificação dela.

## 3. Criar a capacidade de listagem na porta (`D-01`)

O teste da porta já existe — `tests/test_porta_de_armazenamento.py` — e é nele que a capacidade nova
entra:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_porta_de_armazenamento.py -v
```

Esperado: passa. O que se confere no código:

- [ ] `listar()` está no `Protocol` de `src/ports/__init__.py`
- [ ] `ArmazenamentoEmDisco.listar()` devolve nome armazenado, bytes e data — **sem abrir arquivo**
- [ ] pasta ausente devolve **lista vazia**, e não exceção (`D-07`)

## 4. Conferir a função pura de agrupamento (`D-02`, `D-09`)

Arquivo de teste **novo**, a criar nesta feature: `tests/test_lista_de_arquivos.py`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_lista_de_arquivos.py -v
```

Esperado: passa, e os quatro casos medidos estão cobertos:

- [ ] nome com chave → agrupa pela chave
- [ ] **dois** arquivos com a mesma chave → **um** item, com contagem 2
- [ ] nome sem chave → item próprio, **marcado** (`RN-10`)
- [ ] grupo com nomes visíveis diferentes → exibe o nome **sem chave vazada** (`D-09`)
- [ ] nenhum caso lê conteúdo de arquivo

## 5. Subir a aplicação e ver a tela nova (`RF-06`)

```powershell
Remove-Item Env:\ANALISADOR_UPLOAD_FOLDER -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5000` **sem enviar arquivo nenhum** e confira:

- [ ] as duas abas aparecem **de imediato**, sem exigir envio — é o `RF-06`
- [ ] a aba **Buscar Conexão no GEDCOM** lista **7 itens** para os **8** arquivos `.ged`
- [ ] a aba **Analisador de DNA** lista **10 itens** para os **10** arquivos `.csv`
- [ ] o item agrupado declara **2 arquivos**
- [ ] os itens sem chave aparecem **marcados**, e são **3 no total** nas duas abas
- [ ] nenhum item mostra a chave crua no nome

## 6. A armadilha dos nomes repetidos — confira que dá para distinguir

Medido: a lista mostra **dois itens chamados `Arvore_Unificada_Oficial_V1_2.ged`** (conteúdos
diferentes) e **dois chamados `Famílias_Sergipanas.csv`** — e estes dois têm o **mesmo conteúdo**, um com
chave e um sem.

- [ ] cada linha mostra **tamanho** e **data**, e é por eles que se distingue
- [ ] a marca de "sem chave" aparece no item que a tem
- [ ] a ordem é por **data decrescente**

Se dois itens ficarem indistinguíveis na tela, **pare**: é o risco de probabilidade alta do roadmap.

## 7. Escolher a árvore e buscar (`RF-02`)

Escolha uma árvore na lista, informe duas pessoas e submeta a busca.

- [ ] a busca conclui **sem novo envio de arquivo**
- [ ] o caminho encontrado aparece na tela

## 8. Escolher o CSV e analisar duas vezes (`RF-04`, `D-03`)

- [ ] escolha o primeiro CSV da lista e rode a análise — conclui sem envio
- [ ] escolha um **segundo** CSV e rode de novo — conclui, com resultado diferente
- [ ] o caminho antigo continua: envie um CSV **como arquivo** e rode — conclui igual a antes

> O caminho do arquivo **não pode** ter mudado de comportamento: é o que a paridade e os testes de rota
> exercitam, e é a razão de o campo novo ser **aditivo**.

## 9. Enviar um arquivo novo pela aba (`RF-05`)

- [ ] envie um GEDCOM sintético pela aba de árvore: ele é validado **antes** de gravar, gravado sob
  chave de conteúdo e **passa a aparecer na lista**
- [ ] envie um arquivo que não é GEDCOM: a mensagem de conteúdo não reconhecido aparece, e a lista
  continua utilizável

## 10. O arquivo que não serve ao uso (`RN-09`, caso negativo)

Na aba de árvore existe `Famílias_Sergipanas.csv.ged` — um CSV com nome de GEDCOM. Escolha-o.

- [ ] a aplicação responde com a mensagem de conteúdo não reconhecido
- [ ] nenhuma árvore é carregada e a tela continua utilizável
- [ ] o arquivo **continua na lista** (não foi filtrado nem escondido)

## 11. Estado vazio (`RF-07`)

```powershell
$tmp = Join-Path $env:TEMP "vazia-011"
New-Item -ItemType Directory -Force $tmp | Out-Null
$env:ANALISADOR_UPLOAD_FOLDER = $tmp
.\.venv\Scripts\python.exe src\app.py
```

- [ ] a aba orienta o envio e **não** falha; a página responde `200`
- [ ] encerre com Ctrl+C e remova a variável: `Remove-Item Env:\ANALISADOR_UPLOAD_FOLDER`

## 12. Nada foi escrito na pasta (`RF-08`)

Depois de percorrer todas as telas do passo 5 ao 11:

```powershell
$ev = "_reversa_forward\011-escolher-arquivo-da-lista\evidence"
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py duplicatas --pasta src\uploads --relatorio "$ev\duplicatas-depois.txt"
Compare-Object (Get-Content "$ev\duplicatas-antes.txt") (Get-Content "$ev\duplicatas-depois.txt")
(Get-ChildItem src\uploads -File).Count
```

**Esperado:** a comparação **vazia** e a contagem igual à do passo 2 — **19**, ou 20 se você enviou a
fixture sintética do passo 9 (e, nesse caso, remova-a antes de comparar, ou registre a diferença).

## 13. Suíte, paridade e escopo depois

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests\rodar_paridade.py 2>&1 | Select-Object -Last 3
git diff --stat -- src/core src/parsers src/application
git diff --stat -- _reversa_sdd\screens
```

**Esperado:** suíte **acima** de 335 passando e 9 pulados, sem falha; **`PARIDADE 100 %`**; os dois
`git diff --stat` **vazios** — o núcleo não foi tocado e o golden **não** foi alterado (`D-05`).

## 14. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| A primeira tela ainda pede envio | O ramo `{% if not gedcom_filename %}` do template não foi trocado | Passo 5; é a `D-04` |
| A paridade caiu de 100 % | Um dos três ramos de `action` mudou campo, ou uma chave de contexto lida pelo harness saiu | Passo 2 e `D-03`: o campo novo é **aditivo**; nada existente pode sair |
| A análise com o CSV escolhido falha com "arquivo não existe mais" | A referência enviada não é o **nome armazenado** | Use o nome como está na lista (com a chave e o `__`) |
| Dois itens idênticos na DNA | Esperado: `94e2402671702cac__Famílias_Sergipanas.csv` e `Famílias_Sergipanas.csv` têm o mesmo conteúdo, e o segundo não tem chave | Passo 6; é o custo aceito na §9 |
| A lista demora | Alguma coisa está lendo conteúdo | `D-02`/`D-08`: a lista só olha o **nome** e os atributos |
| `2 failed` em `test_persistencia_desabilitada.py` | `DATABASE_URL` no ambiente | Passo 1; não é a feature |
| Suíte abaixo de 335 passando | Ambiente, ou regressão | Passo 1 antes de concluir regressão |

## 15. Resultados medidos (preenchido na execução)

| Passo | O que se espera | Medido |
|---|---|---|
| 2 | suíte `335 passed, 9 skipped`; `PARIDADE 100 %`; 19 arquivos | *(a preencher)* |
| 3 | `listar()` na porta, pasta ausente devolve lista vazia | *(a preencher)* |
| 4 | quatro casos de agrupamento cobertos, nenhum lê conteúdo | *(a preencher)* |
| 5 | duas abas sem envio; árvore 7 itens / 8 arquivos; DNA 10 / 10 | *(a preencher)* |
| 6 | nomes repetidos distinguíveis por data e marca | *(a preencher)* |
| 8 | duas análises com CSVs escolhidos, e o caminho do arquivo intacto | *(a preencher)* |
| 11 | estado vazio responde 200 e orienta o envio | *(a preencher)* |
| 12 | inventário por `sha256` idêntico antes e depois | *(a preencher)* |
| 13 | suíte sem falha; `PARIDADE 100 %`; núcleo e goldens com diff vazio | *(a preencher)* |
