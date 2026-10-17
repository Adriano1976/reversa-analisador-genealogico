# Onboarding: desempenho da carga da árvore GEDCOM

> Identificador: `025-desempenho-carga-arvore`
> Data: `2026-10-17`
> Para: quem vai testar esta feature pela primeira vez
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. O que esta feature faz, em uma frase

Elimina a **segunda leitura dos registros de família** no parse do GEDCOM, entregando à construção do
grafo a lista que a carga já leu — e prova, com medição e com impressão digital, que a árvore e o
resultado da análise de DNA continuam **idênticos**.

## 2. O que você precisa ter

- O `.venv` do projeto (Python 3.14.6) — é o interpretador oficial.
- `DATABASE_URL` **ausente** do ambiente. Com ela presente o resultado da suíte muda (dívida `L-27`).
- A árvore real e o CSV, em `src/uploads/`:
  - `0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged` (5,5 MB, 35.460 pessoas, 6.930 famílias)
  - `54f4887e89705735__Famílias_Sergipanas.csv`
- Cerca de **10 minutos**. Só a análise de DNA leva ~54 s, e a carga ~28 s (mediana).

> **Atenção de ambiente (medido em 2026-10-17):** nesta máquina o sandbox de arquivos bloqueia a
> escrita dentro de subpastas do projeto, e a suíte cria `tests/.tmp`. Se os comandos falharem com
> "Acesso negado", rode-os com permissão total — é limitação de execução, não do código.

## 3. Passo a passo

Todos os comandos rodam da **raiz do repositório**.

### Passo 0 — preparar as pastas de evidência

```powershell
$EVID = "_reversa_forward\025-desempenho-carga-arvore\evidence"
New-Item -ItemType Directory -Force "$EVID\antes", "$EVID\depois" | Out-Null
```

### Passo 1 — conferir a linha de base da suíte

```powershell
$env:DATABASE_URL=$null
.venv\Scripts\python.exe -m pytest -q
```

Esperado: **1.046 passed, 9 skipped**, zero falhas, ~104 s. Se o número de coletados for menor que
1.046, alguma coisa foi removida — pare.

### Passo 2 — capturar a paridade ANTES

```powershell
.venv\Scripts\python.exe tests\rodar_paridade.py 2>&1 | Tee-Object "$EVID\antes\paridade.txt"
```

Esperado no dia 2026-10-17: **24 divergências em 5 das 6 fixtures**, `exit 1`, só `affinity.ged`
limpo. **Isso é a linha de base, não um defeito desta feature** — o vermelho é anterior a ela. Guarde
o arquivo: é ele que você vai comparar item a item no fim.

### Passo 3 — medir a carga e a análise de DNA ANTES

```powershell
$env:DATABASE_URL=$null
.venv\Scripts\python.exe _reversa_sdd\parity\_perfil_da_carga.py --repeticoes 3 `
    --gedcom "src\uploads\0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged" `
    --csv "src\uploads\54f4887e89705735__Famílias_Sergipanas.csv" `
    --raiz "Adriano Santos"
```

O que olhar, em ordem de importância:

1. **`records0("FAM")` = 2** e **`read_record` = 49.321** — é o desperdício que a feature remove.
2. **`_init_index` = 1** — prova que a indexação **não** se repetia.
3. **`records0("INDI")` = 1**.
4. As linhas de tempo: `INDI`, `FAM`, `grafo`, `carga` (3 repetições, mediana) e `DNA`.

A **carga** roda 1 aquecimento descartado mais 3 repetições; o **DNA** roda **uma** vez por lado, e
isso é declarado no relatório — ele não é alvo da mudança e leva ~54 s por execução.

Não se assuste com a variação: a mesma carga já deu 26,55 / 28,02 / 32,71 s aqui. A **primeira**
execução em processo novo foi 51,68 s (cache frio).

### Passo 4 — imprimir a identidade da árvore ANTES

```powershell
.venv\Scripts\python.exe _reversa_forward\025-desempenho-carga-arvore\evidence\_impressao_da_arvore.py `
    --gedcom "src\uploads\0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged" `
    --csv "src\uploads\54f4887e89705735__Famílias_Sergipanas.csv" `
    --raiz "Adriano Santos" --saida "$EVID\antes\impressao.txt"
```

Ele grava **dois hashes**: um da árvore (pessoas, famílias, nós com `label`/`type` na ordem,
arestas na ordem, `child_to_family` na ordem) e um do resultado da análise. Nenhum nome de pessoa
sai no arquivo — é o Princípio I.

### Passo 5 — aplicar a mudança

A mudança é em `src/parsers/gedcom_parser.py` (ver `roadmap.md` §3, `D-02` e `D-03`) e nos dois
testes de `tests/test_upload.py` que chamam o grafo (`D-07`). O teste novo do `RF-09` deve ser
escrito **antes** e **falhar** com a contagem 2.

### Passo 6 — medir DEPOIS, do mesmo jeito

Repita os passos 1 a 4, gravando em `$EVID\depois\`. O que deve ter mudado **só**:

| Contador | Antes | Depois |
|---|---:|---:|
| `records0("FAM")` | 2 | **1** |
| `read_record` | 49.321 | **42.391** |
| `_init_index` | 1 | 1 |
| `index0` | 3 | 3 |

E o que **não pode** ter mudado: os dois hashes do passo 4 e a lista de divergências da paridade.

### Passo 7 — conferir na tela (opcional, mas recomendado)

```powershell
.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5080`, envie a árvore real, depois o CSV, com a raiz `Adriano Santos`.
Espere cerca de **1min45** (é a requisição completa de hoje). O resultado deve trazer os **mesmos 93
cartões** e os **mesmos 363 descartes** de antes. Se o número de cartões mudar, a mudança está
errada, por menor que seja o ganho de tempo.

## 4. Como interpretar o resultado (o que esta feature NÃO promete)

- O ganho é de **~1,5 s** numa requisição de **~105 s**. É remoção de trabalho redundante, não uma
  melhora percebida pelo operador. Se o número medido ficar **dentro da dispersão** (23 %), o
  relatório diz isso — e isso **não** é falha da entrega.
- **Não** houve troca de parser, cache de árvore, mudança no matching ou no RapidFuzz. Se algum
  desses aparecer no diff, é desvio de escopo.
- O tempo dominante continua sendo a passada `INDI` (~19 s) e a análise de DNA (~54 s). As duas são
  assunto de outra feature.

## 5. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `PermissionError` em `tests/.tmp` | sandbox de arquivos bloqueando subpasta | rode o comando com acesso total |
| `records0("FAM")` continua 2 depois da mudança | a lista não chegou ao grafo, ou há um segundo chamador | confira `src/parsers/gedcom_parser.py` e busque `records0("FAM")` no projeto |
| Hashes diferentes antes/depois | ordem de inserção mudou, ou o par árvore+CSV não é o mesmo | confira o `sha256` do `.ged` e do `.csv`; se o arquivo mudou, refaça os dois lados |
| Paridade com divergência **nova** | regressão de comportamento | pare: é `RISK-004`, divergência de um item já invalida |
| Números muito diferentes de 28 s | cache frio, antivírus ou máquina ocupada | rode de novo; o protocolo já descarta o aquecimento |
| `DATABASE_URL` presente e 2 testes falhando | dívida `L-27`, alheia a esta feature | remova a variável do ambiente |

## 6. Checklist de aceite

- [ ] Suíte: 0 falhas, coletados ≥ 1.046
- [ ] `records0("FAM")` = 1 e `read_record` = 42.391
- [ ] `_init_index` = 1 (não mudou)
- [ ] Hash da árvore idêntico ao de antes
- [ ] Hash do resultado de DNA idêntico ao de antes (93 cartões, 363 descartes)
- [ ] Paridade: as mesmas 24 divergências, nenhuma nova
- [ ] `git diff --stat` só com parser, testes e instrumento
- [ ] `requirements.txt` intacto

## 7. Resultados efetivamente medidos (2026-10-17)

Os valores esperados da §3 foram **confirmados**, com uma ressalva importante sobre
o tempo. Números completos em `evidence/RELATORIO.md`.

| Contador | Antes | Depois |
|---|---:|---:|
| `records0("INDI")` | 1 | 1 |
| `records0("FAM")` | 2 | **1** |
| `index0` | 3 | **2** |
| `_init_index` | 1 | 1 |
| `read_record` | 49.321 | **42.391** |

| Tempo | Antes | Depois |
|---|---:|---:|
| Carga, mediana de 3 | 34,47 s | 23,72 s |
| Carga, dispersão | **83 %** | 6 % |
| DNA (1 execução) | 22,40 s | 29,37 s |

**A diferença de medianas não é o ganho.** A rodada "antes" variou 83 % e a "depois",
6 %: a máquina estava mais calma. O ganho atribuível é o custo da leitura removida,
medido 3 vezes na árvore real: **mediana 1,59 s** (1,35 / 1,59 / 2,77 s), coerente
com os 1,80 s medidos na fase isolada antes da mudança.

Hashes: árvore `8bf55afb…cc1d925` e DNA `d369611f…585c5163`, **idênticos** antes e
depois. Paridade: os dois arquivos de saída têm **0 linhas diferentes**. Suíte:
1.046 → **1.048 passed, 9 skipped**, zero falhas.
