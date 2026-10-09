# Onboarding: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`
> Roadmap: `_reversa_forward/012-pasta-canonica-no-repositorio/roadmap.md`

Este documento é para quem vai **executar e conferir** a feature. Cada passo tem o comando e o que deve
sair. Onde o resultado for um número, o número está declarado — se sair diferente, pare e investigue,
porque a medição é o contrato.

## 1. Pré-requisitos

- PowerShell na raiz do repositório: `D:\Projetos\reversa_analisador_gelealogico`
- Interpretador oficial: `.\.venv\Scripts\python.exe`
- Ancoragem: `$env:PYTHONIOENCODING = "utf-8"` na sessão. Sem ele, contagem de acento e de emoji no
  console do Windows mente — e este projeto já foi mordido por isso duas vezes.
- **`DATABASE_URL` deve estar ausente do ambiente.** Medido em 2026-10-09: com a variável definida,
  `tests/test_persistencia_desabilitada.py` falha em 2 testes, e a suíte dá `325 passed, 2 failed,
  9 skipped` em vez de `327 passed, 9 skipped`. Não é regressão da feature — é o ambiente.

```powershell
$env:PYTHONIOENCODING = "utf-8"
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
Write-Output "DATABASE_URL: [$env:DATABASE_URL]"
```

## 2. Conferir o estado do ambiente

**Não use a tabela de portas** (`Get-NetTCPConnection`). Medido em 2026-10-09: ela devolveu resultados
contraditórios em três execuções seguidas, com os dois serviços no ar. Use o Compose:

```powershell
docker compose ps
Get-Process python,pythonw -ErrorAction SilentlyContinue
```

Estado esperado no início desta feature: `genealogia-app-1` e `genealogia-db-1` **no ar**, `db`
`healthy`, nenhum processo `python` do host.

E o estado que **motiva o passo 3**:

```powershell
docker compose exec -T app ls -la /app/src/uploads
```

Esperado hoje: `ls: cannot access '/app/src/uploads': No such file or directory`. O contêiner monta um
caminho de host que foi esvaziado, e é isso que o `RF-01` corrige.

## 3. Restaurar a composição e recriar o contêiner (`RF-01`)

1. Em `docker-compose.yml`, a linha de `volumes:` do serviço `app` passa a ser, exatamente:

```yaml
      - ./src/uploads:/app/src/uploads
```

2. Recrie **só** o serviço cujo arquivo mudou:

```powershell
docker compose up -d
```

> **`docker compose down -v` é proibido aqui.** O `-v` remove os volumes nomeados, e o volume
> `genealogia_dados_do_banco` é o histórico do banco. O próprio `.env` avisa: `POSTGRES_PASSWORD` só
> tem efeito na primeira inicialização, e trocar depois exige `down -v`, que **apaga o histórico**.

3. Confirme que o alvo interno voltou:

```powershell
docker compose exec -T app ls -A /app/src/uploads | Measure-Object -Line
```

Esperado: **36** entradas.

4. Confirme que o banco **não** foi recriado:

```powershell
docker compose ps
```

Esperado: `db` com o mesmo `CREATED` de antes e `healthy`.

## 4. Provar que a composição voltou ao estado entregue (`RF-01`)

```powershell
git diff --stat -- docker-compose.yml
git diff HEAD -- docker-compose.yml
```

Esperado: **as duas saídas vazias.** O critério do `RF-01` não é "parece certo": é o arquivo idêntico ao
que a feature 008 entregou (`git log`: `80964c4`).

## 5. Testar o modo local sem configuração (`RF-02`)

Com `ANALISADOR_UPLOAD_FOLDER` **ausente**:

```powershell
Remove-Item Env:\ANALISADOR_UPLOAD_FOLDER -ErrorAction SilentlyContinue
Get-ChildItem src\uploads -File | Measure-Object | Select-Object -ExpandProperty Count
```

Esperado: **36** antes do passo 11.

Suba a aplicação e envie um GEDCOM de teste; o arquivo tem de aparecer em `src\uploads` e em nenhum
outro lugar. Encerre com Ctrl+C.

## 6. Conferir a documentação (`RF-02`, `RF-03`)

No `README.md`, seção "Onde ficam os arquivos enviados", verifique os quatro pontos:

- [ ] `src/uploads` declarada como a pasta canônica e **única**
- [ ] `ANALISADOR_UPLOAD_FOLDER` apresentada como **sobreposição**, não como modo de operação
- [ ] as duas guardas nomeadas: `.gitignore` (`uploads/`) e `.dockerignore` (`src/uploads/`)
- [ ] o aviso de que `git clean -xdf` (e `-Xdf`) **apaga** a pasta, porque ela é não rastreada

E na tabela de configurações: a variável continua listada (os testes dependem dela).

## 7. Exercitar as guardas (`RF-11`, `D-04`, `D-05`)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_guardas_do_armazenamento.py -q
```

Esperado: passa. O teste tem de fazer **duas** asserções para cada guarda, e é isso que se confere no
código dele:

- [ ] a linha existe literalmente no arquivo;
- [ ] o **efeito**: `git check-ignore -v` nomeia `.gitignore` para um caminho `uploads/`;
- [ ] a **ordem** no `.dockerignore`: `src/uploads/` depois de `!src/**`;
- [ ] a mutação, sobre cópia temporária: removida a linha na cópia, a asserção **falha**.

Se a mutação não falhar, o teste é decorativo — e o Princípio III não aceita teste decorativo.

## 8. Remover as três cópias de arrasto (`RF-09`, `D-03`)

O instrumento é *fail-closed*: ele confere, por diretório, que **todo `sha256` ocorre em `src/uploads`**.
Qualquer órfão cancela a remoção daquele diretório.

```powershell
.\.venv\Scripts\python.exe _reversa_forward\012-pasta-canonica-no-repositorio\evidence\_remover_copias_de_arrasto.py
```

Esperado: `0 órfãos` nos três, os três diretórios removidos, e o inventário de `src/uploads` inalterado
em **36 arquivos / 27.932.474 bytes**.

Depois, prove que os instrumentos do refactor continuam funcionando — **execução, não leitura**:

```powershell
.\.venv\Scripts\python.exe "_reversa_refactor\pacote-reconstructed\transformations\OPP-20261003-FLAT-achatar-o-nivel-de-pacote\registrar-diff.py"
.\.venv\Scripts\python.exe "_reversa_refactor\pacote-reconstructed\transformations\OPP-20261003-FLAT-achatar-o-nivel-de-pacote\verificar-estrutura.py"
```

E que o git não ganhou nada:

```powershell
git status --porcelain
```

## 9. Provar que `src/` não mudou (`D-01`)

```powershell
git diff --stat -- src
git diff -- src
git status --porcelain -- src _reversa_sdd
```

Esperado: **as três saídas vazias.**

## 10. Suíte e paridade (`RF-06`, `RF-07`)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: **`327 passed, 9 skipped`**. Se aparecer `2 failed` em `test_persistencia_desabilitada.py`,
volte ao passo 1: é o `DATABASE_URL` no ambiente, não a feature.

```powershell
$antes = (Get-ChildItem src\uploads -File).Count
.\.venv\Scripts\python.exe tests\rodar_paridade.py
$depois = (Get-ChildItem src\uploads -File).Count
Write-Output "uploads antes=$antes depois=$depois"
```

Esperado: a saída termina em **`PARIDADE 100 %`** e `antes = depois = 36`. **Não** execute o
`harness.py` direto: ele escreve as sondas na pasta real, e é essa a origem do resíduo.

## 11. Revisar o `onboarding.md` da 010 (`RF-12`, `D-06`)

Arquivo: `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md`.

- [ ] cada seção afetada tem o bloco `> **Revisto em 2026-10-09 (feature 012).**`
- [ ] o texto anterior continua legível
- [ ] **a seção 12 não manda mais apagar `src/uploads/`** — depois desta feature, esse passo destrói o
      dado canônico. É a revisão mais crítica do documento

## 12. Expurgar o resíduo, por último (`RF-10`, `D-07`)

Regenere o manifesto — **não** use o da 010, que é de 14:51 e o `expurgar` recusa hash divergente:

```powershell
$ev = "_reversa_forward\012-pasta-canonica-no-repositorio\evidence"
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py manifesto --pasta src\uploads --saida "$ev\manifesto-residuo-012.txt"
Get-Content "$ev\manifesto-residuo-012.txt" | Select-Object -First 6
```

Esperado: **18 arquivos listados**.

Revise a lista e rode a **simulação**:

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py expurgo --manifesto "$ev\manifesto-residuo-012.txt" --dry-run --relatorio "$ev\expurgo-simulado-012.txt"
Get-Content "$ev\expurgo-simulado-012.txt" | Select-Object -First 6
```

Esperado: `removidos: 18`, `recusados: 0`, e `src/uploads` **ainda com 36 arquivos**.

Só então aplique:

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py expurgo --manifesto "$ev\manifesto-residuo-012.txt" --aplicar --relatorio "$ev\expurgo-aplicado-012.txt"
Get-ChildItem src\uploads -File | Measure-Object | Select-Object -ExpandProperty Count
```

Esperado: **18** arquivos.

## 13. Recapturar os números e fechar (`D-08`, `D-12`)

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py manifesto --pasta src\uploads --saida "$ev\manifesto-pos-expurgo.txt"
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py duplicatas --pasta src\uploads --relatorio "$ev\duplicatas-pos-expurgo.txt"
```

Esperado: o manifesto regenerado devolve **0** entradas para o conjunto de nomes conhecidos.

E a lista da feature 011, nas duas unidades:

| Aba | Antes | Depois |
|---|---|---|
| Árvore (`.ged`) | 16 arquivos / 15 itens | 7 arquivos / **6 itens** |
| DNA (`.csv`) | 19 arquivos / 19 itens | 10 arquivos / 10 itens |

## 14. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ls: cannot access '/app/src/uploads'` no contêiner | O *bind mount* aponta para caminho de host inexistente | Passo 3: editar o compose e `docker compose up -d`. **Nunca** `down -v` |
| `2 failed` em `test_persistencia_desabilitada.py` | `DATABASE_URL` no ambiente da sessão | `Remove-Item Env:\DATABASE_URL` e repetir. Não é a feature |
| `Get-NetTCPConnection` diz que nada escuta, mas o site responde | A tabela de portas não é confiável sob confinamento | Use `docker compose ps` (`D-11`) |
| O expurgo recusa tudo com "hash diferente do manifesto" | Manifesto velho | Regenere com o passo 12 — é o `D-07` |
| O expurgo remove menos de 18 | Algum arquivo do manifesto mudou de conteúdo, ou foi lido de outra pasta | Confira o `# Pasta:` no cabeçalho do manifesto |
| A paridade deixou arquivo novo em `src/uploads` | O `harness.py` foi chamado direto, sem o invólucro | Use `tests\rodar_paridade.py`; o resíduo novo entra no próximo manifesto |
| Sobrou arquivo de sonda depois do expurgo | O critério é conjunto fechado de nomes (`D-12`), e o nome é novo | Declare no manifesto: acrescente o nome visível a `NOMES_DE_INSTRUMENTO` |
| Suíte abaixo de 327 | Ambiente, não código | Confira o passo 1 antes de concluir regressão. A linha de base **com esta feature** é `335 passed, 9 skipped`: 327 mais os 8 testes de `test_guardas_do_armazenamento.py` |

## 15. Resultados medidos (preenchido na execução)

| Passo | O que se esperava | Medido em 2026-10-09 |
|---|---|---|
| 2 | `/app/src/uploads` inexistente no contêiner | **Confirmado:** `ls: cannot access '/app/src/uploads'`; `app` e `db` no ar havia 2 horas, `db` `healthy` |
| 3 | 36 entradas dentro do contêiner, `db` no mesmo volume | **36 entradas**; `app` recriado (`Recreated`), `db` apenas `Running`, com o mesmo `CREATED` e `healthy` |
| 4 | `git diff HEAD -- docker-compose.yml` vazio | **Vazio**, e o `git status --porcelain` do arquivo também |
| 8 | 3 diretórios removidos, 0 órfãos, `src/uploads` intacto | **3 removidos, 0 órfãos**; 27 arquivos e 50.762.352 bytes fora do disco; `src/uploads` intacto em 36 arquivos e 27.932.474 bytes; `app.py` e `reconstructed/` preservados nos três |
| 9 | `git diff -- src` vazio | **Vazio** (`git diff` e `git diff --stat`); `git status --porcelain` com as mesmas 12 linhas do início |
| 10 | `327 passed, 9 skipped`; `PARIDADE 100 %`; inventário idêntico | **`335 passed, 9 skipped`**; **`PARIDADE 100 %`** com exit 0; inventário idêntico: 36 arquivos e 27.932.474 bytes antes e depois |
| 12 | simulação 18/0; aplicado 18; `src/uploads` com 18 arquivos | **Simulação: 18 removidos, 0 recusados.** Aplicado: **18**. `src/uploads` com **18 arquivos e 27.925.843 bytes** |
| 13 | manifesto pós-expurgo com 0 entradas; árvore 6 itens, DNA 10 itens | **0 entradas**; árvore **7 arquivos / 6 itens**, DNA **10 arquivos / 10 itens**; **3 grupos** de duplicatas relatados e preservados |

### Duas medições contrariaram o que este documento previa

1. **A suíte não deu `327 passed`: deu `335 passed`.** A previsão foi escrita antes de
   `tests/test_guardas_do_armazenamento.py` existir, e ele acrescenta **8** testes. `327 + 8 = 335`,
   sem regressão: nenhum teste antigo deixou de passar.
2. **Os dois instrumentos do refactor já falhavam antes desta feature**, e continuam falhando por
   motivo próprio: o `registrar-diff.py` aborta em `src/core/gedcom_state.py`, módulo apagado pelo
   `T023` da feature 005, e o `verificar-estrutura.py` compara o `src/` de hoje com o congelado de
   2026-10-03. O critério do roadmap foi **revisado**: o que se prova é que **a retirada não altera a
   saída de nenhum dos dois**, por controle A/B com as cópias reconstruídas a partir de `src/uploads`
   (`evidence/T013-instrumentos-do-refactor.txt`).
