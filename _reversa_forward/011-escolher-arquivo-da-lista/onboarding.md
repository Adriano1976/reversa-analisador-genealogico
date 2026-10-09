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
  `tests/test_persistencia_desabilitada.py` **falham** — medido na feature 012 (`325 passed, 2 failed,
  9 skipped` contra `327 passed, 9 skipped`, naquele momento). Os números absolutos mudam a cada teste
  acrescentado e **não** são a referência: o que não muda é que a suíte roda sem a variável, e que essas
  duas falhas são de ambiente, não de regressão

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

**Esperado:** suíte **sem falha** — a referência da feature 012 é `335 passed, 9 skipped`, e esta feature
acrescenta testes, então o número tende a ser maior; **o número que vale é o que sair**, e é ele que vai
para a evidência. Paridade em **`PARIDADE 100 %`**; e **19** arquivos na pasta.

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
- [ ] nome visível com **acento** → item marcado **indisponível**, com o motivo (`RN-11`, `D-11`)
- [ ] nome **sem chave** → item marcado **indisponível**, e ainda assim **presente** na lista
- [ ] nome ASCII **com** chave → item **disponível** — é o que prova que a marca e o resolvedor concordam
- [ ] o **mesmo** `.xlsx` do passo 5 não entra em aba nenhuma (`RN-03`, `D-10`)

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
- [ ] os itens **indisponíveis** aparecem marcados, com o motivo: **3 na aba de árvore** e **3 na de DNA** (`RF-09`, `D-11`)
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

## 10. O arquivo que não pode ser escolhido (`RN-09`, `RN-11`, `D-11`)

Na aba de árvore existe `Famílias_Sergipanas.csv.ged` — um CSV com nome de GEDCOM, **e com acento** no
nome visível. Ele reúne as duas causas de indisponibilidade medidas na auditoria. Escolha-o.

- [ ] o item aparece **marcado como indisponível**, com o motivo — ele **não** é oferecido como se fosse funcionar
- [ ] se você forçar a escolha dele, a aplicação responde `Erro: Arquivo '…' não existe mais.` — e essa mensagem é **falsa**, porque o arquivo está na pasta. É o **defeito de raiz `A007`**, registrado como bug próprio, e **não** é falha desta feature
- [ ] nenhuma árvore é carregada e a tela continua utilizável
- [ ] o arquivo **continua na lista** (não foi filtrado nem escondido)

> **Por que não há mais um passo de "conteúdo não reconhecido" aqui.** O único arquivo da pasta com nome
> `.ged` e conteúdo CSV é justamente o de nome acentuado, e a referência **não o alcança** — a validação de
> conteúdo, que só roda no **envio** (passo 9), nunca chega a ser exercitada por referência. Um arquivo
> sintético com nome ASCII e conteúdo inválido **não** reproduz o caso real: ele derruba a requisição com
> `500` por exceção não capturada, que é um **segundo** defeito, também registrado na auditoria (`A008`) e
> fora do escopo desta feature.

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
| A análise com o CSV escolhido falha com "arquivo não existe mais" | Ou a referência enviada não é o **nome armazenado**, ou o item é **indisponível** — nome com acento, ou sem chave | Use o nome como está na lista (com a chave e o `__`); se o item estava marcado como indisponível, é o defeito `A007`, não a feature |
| Dois itens idênticos na DNA | Esperado: `94e2402671702cac__Famílias_Sergipanas.csv` e `Famílias_Sergipanas.csv` têm o mesmo conteúdo, e o segundo não tem chave | Passo 6; é o custo aceito na §9 |
| A lista demora | Alguma coisa está lendo conteúdo | `D-02`/`D-08`: a lista só olha o **nome** e os atributos |
| `2 failed` em `test_persistencia_desabilitada.py` | `DATABASE_URL` no ambiente | Passo 1; não é a feature |
| Suíte abaixo de 335 passando | Ambiente, ou regressão | Passo 1 antes de concluir regressão |

## 15. Resultados medidos (preenchido na execução)

| Passo | O que se espera | Medido |
|---|---|---|
| 2 | suíte sem falha; `PARIDADE 100 %`; 19 arquivos | **`335 passed, 9 skipped`**; **`PARIDADE 100% (zero divergencia)`**; **19 arquivos / 29.166.183 bytes** — os tres conferem com o plano (evidencias `T001`, `T002`, `T003`) |
| 3 | `listar()` na porta, pasta ausente devolve lista vazia | **26 passed** em `tests/test_porta_de_armazenamento.py`, incluindo os 6 novos da `TestListagemDaPasta`. Pasta ausente devolve `[]` e a listagem **nao cria** a pasta |
| 4 | os quatro casos de agrupamento, a partição por extensão e o alcance por referência, sem ler conteúdo | **21 passed** em `tests/test_lista_de_arquivos.py` |
| 5 | duas abas sem envio; árvore 7 itens / 8 arquivos; DNA 10 / 10; **3 + 3 itens marcados como indisponíveis** | **10 passed** em `tests/test_lista_na_tela.py` (T007/T008). As contagens reais da pasta **nao** foram remedidas depois da mitigacao do bug, que renomeou 4 arquivos sem mudar o numero de itens |
| 6 | nomes repetidos distinguíveis por data e marca | Coberto pela `D-09` na funcao pura e pelo campo `modificado_em` do item; **nao** ha passo manual executado |
| 8 | duas análises com CSVs escolhidos, e o caminho do arquivo intacto | **14 passed** em `tests/test_dna_analysis.py`: referencia sem arquivo, precedencia da referencia e a mensagem de hoje preservada |
| 10 | item indisponível marcado, com o motivo; forçado, recusa sem carregar árvore | **12 passed** em `tests/test_path_search.py`. A recusa responde `200` com mensagem — o literal nao e fixado, porque e o falso `nao existe mais` do `BUG-20261009-6RKP` |
| 11 | estado vazio responde 200 e orienta o envio | Coberto pelos testes da T008 no passo 5; nao ha passo manual executado |
| 12 | inventário por `sha256` idêntico antes e depois | **IDÊNTICO**: o conjunto de sha256 dos 19 arquivos nao mudou (`T025`, `RF-08`) |
| 13 | suíte sem falha; `PARIDADE 100 %`; núcleo e goldens com diff vazio | **`379 passed, 2 failed, 9 skipped`** — a paridade segue **100 %**, o nucleo tem `git diff` **vazio** e o golden tem sha256 `ec07f71b4084269a` e `git status` vazio (`T026`, `T027`). **A suite NAO fecha**: as 2 falhas sao `test_icone_de_atalho.py`, o conflito com a feature 009, e dependem de decisao humana |

> **Como ler esta tabela.** As linhas de teste foram medidas por execucao; as de passo manual (6 e 11)
> ficaram cobertas por teste de rota e **nao** foram percorridas a mao. A linha 13 e a unica com
> ressalva, e ela esta declarada em vez de arredondada: o criterio de pronto do `roadmap.md` §10 pede
> suite sem regressao, e ha 2 falhas reais de outra feature.

