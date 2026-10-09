# Onboarding: Uploads fora do repositório

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/010-uploads-fora-do-repositorio/roadmap.md`

Este documento é para um humano que vai aplicar e **testar** a feature pela primeira vez. Ele é
executável na ordem, do começo ao fim, e cada passo tem uma conferência que não depende de interpretação.

---

> **AVISO — documento revisto em 2026-10-09 pela feature `012-pasta-canonica-no-repositorio`.**
>
> A decisão que este documento ensina foi **revertida**: a pasta canônica de dados voltou a ser
> `src/uploads`, **dentro** do repositório, e é a única. O que segue é o registro de como a feature 010
> foi aplicada e testada; cada seção afetada recebeu um marcador
> `> **Revisto em 2026-10-09 (feature 012).**` com o procedimento válido, e o texto original ficou
> preservado abaixo dele.
>
> **Não execute o passo 12.** Ele manda apagar `src\uploads\`, que depois da feature 012 **é** o dado
> canônico: apagá-la destrói a única cópia do dado.
>
> Continuam valendo: os passos 10 e 11 (manifesto e expurgo, com simulação antes de aplicar), a
> explicação de por que a paridade não se roda direto pelo `harness.py`, e as linhas de diagnóstico
> sobre instância única, `DATABASE_URL` e paridade. O procedimento válido de ponta a ponta está em
> `_reversa_forward/012-pasta-canonica-no-repositorio/onboarding.md`.

---

## 0. O que você vai provar

> **Revisto em 2026-10-09 (feature 012).** Os itens 1 e 4 descrevem o destino **fora** do repositório, e
> o item 6 descreve o expurgo como passo opcional. O válido agora: existe **um** destino canônico,
> `src/uploads`, **dentro** do repositório (`D-01` revertida); os arquivos que existem hoje ali são
> **18** depois do expurgo; e o expurgo é a **última** ação da feature 012, não um passo que o operador
> adia. Os itens 2, 3 e 5 continuam valendo como registro. Texto original preservado abaixo.

1. Que existe **um** destino canônico, fora do repositório, e que os dois modos de execução apontam
   para ele (D-01).
2. Que a migração **copia com conferência por hash** e deixa a origem intacta (D-04, `RF-07`).
3. Que a continuidade entre requisições continua funcionando: envio → busca de caminho → análise de DNA.
4. Que os **36 arquivos e 27.932.474 bytes** existem nos dois lados, com os mesmos hashes.
5. Que a paridade continua em **100 %** e que a pasta real **não** ganha arquivo nenhum (D-07, `RF-04`).
6. Que o expurgo, em simulação, não remove nada — e que a aplicação remove só o que está no manifesto.

## 1. Pré-requisitos

- `.venv\Scripts\python.exe` funcionando (é o interpretador oficial da suíte e da paridade).
- Docker Desktop no ar, com o drive do projeto e o drive do destino acessíveis ao contêiner (o destino
  proposto é `D:\dados-genealogicos\uploads`, e o projeto já está em `D:`).
- `.env` com `DATABASE_URL` definido, como o `docker-compose.yml` exige para subir o serviço `app`.
- Nenhum processo da aplicação no ar (a guarda de instância única recusa a segunda subida).

## 2. Linha de base — antes de mexer em qualquer coisa

```powershell
$origem  = "src\uploads"
$destino = "D:\dados-genealogicos\uploads"
$evid    = "_reversa_forward\010-uploads-fora-do-repositorio\evidence"
New-Item -ItemType Directory -Force $evid | Out-Null

# inventario de origem: nome, bytes e sha256 por arquivo
Get-ChildItem -File $origem | Sort-Object Name |
  ForEach-Object { "{0}`t{1}`t{2}" -f $_.Name, $_.Length, (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } |
  Set-Content -Encoding utf8 "$evid\inventario-origem.txt"

"arquivos: " + (Get-ChildItem -File $origem).Count
"bytes:    " + (Get-ChildItem -File $origem | Measure-Object Length -Sum).Sum

# linha de base da SUITE
.\.venv\Scripts\python.exe -m pytest -q

# linha de base da PARIDADE, com a pasta definida A MAO: no estado de partida o
# involucro (tests\rodar_paridade.py) ainda NAO existe — ele e entrega desta feature
New-Item -ItemType Directory -Force "$PWD\.parity-tmp\uploads" | Out-Null
$env:ANALISADOR_UPLOAD_FOLDER = "$PWD\.parity-tmp\uploads"
.\.venv\Scripts\python.exe _reversa_sdd\parity\harness.py
Remove-Item Env:\ANALISADOR_UPLOAD_FOLDER
```

**Esperado:** `36` arquivos e `27932474` bytes; a suíte em **`302 passed, 8 skipped`** — medido em
2026-10-09 em `evidence\linha-de-base-suite.txt` — e a paridade em **`PARIDADE 100%`** com `exit 0`,
medida em `evidence\linha-de-base-paridade.txt`.

> **Por que a paridade não se roda direto.** O `harness.py` lança os coletores herdando o ambiente
> (`_reversa_sdd/parity/harness.py:465`) e o coletor candidato importa a aplicação, que resolve a pasta de
> upload no import. Executado direto **sem** a variável, ele escreve as sondas na pasta **real** — foi
> assim que nasceu o resíduo de 18 arquivos. Por isso a linha de base já define a variável à mão; a partir
> do passo 9, o caminho documentado passa a ser o invólucro `tests\rodar_paridade.py`, que faz o mesmo sem
> você precisar lembrar da variável — e **sem editar o instrumento** (`D-07`).

## 3. Definir o destino canônico

> **Revisto em 2026-10-09 (feature 012).** **Este passo deixou de existir.** Não há destino a definir: a
> pasta canônica é `src/uploads`, dentro do repositório, resolvida pelo próprio aplicativo a partir de
> `__file__` e criada na importação. `D:\dados-genealogicos\uploads` **não existe mais** — a cópia foi
> removida em 2026-10-09, com inventário conferido por `sha256` antes e depois
> (`_reversa_forward/012-pasta-canonica-no-repositorio/evidence/remocao-da-copia-externa.txt`). O
> diretório-pai `D:\dados-genealogicos` continua no disco, vazio. Texto original preservado abaixo.

O destino proposto é `D:\dados-genealogicos\uploads`. Se você trocar o caminho, troque **nos dois
modos** — passo 6 e passo 8 — e mantenha exatamente o mesmo valor.

```powershell
New-Item -ItemType Directory -Force $destino | Out-Null
Test-Path $destino
```

## 4. Migrar — cópia verificada, nunca movimento

> **Revisto em 2026-10-09 (feature 012).** **Este passo não é mais procedimento.** Não há para onde
> migrar. O verbo `migrar` continua na ferramenta, mas como **cópia avulsa**, sem papel no modo de
> operação (`RN-06` da feature 012): um verbo de migração apresentado como procedimento reabriria a
> dúvida sobre qual pasta é a fonte de leitura, que é exatamente o problema que a 012 fechou. Os passos
> 4 e 5 ficam como registro de como a cópia verificada foi feita. Texto original preservado abaixo.

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py migrar `
    --origem $origem `
    --destino $destino `
    --relatorio "$evid\migracao.txt"
```

**Esperado:** relatório com 36 arquivos copiados, nenhuma divergência, e a mensagem final com os totais
dos dois lados.

## 5. Provar a migração

```powershell
# (1) contagem e total no destino
"arquivos no destino: " + (Get-ChildItem -File $destino).Count          # 36
"bytes no destino:    " + (Get-ChildItem -File $destino | Measure-Object Length -Sum).Sum   # 27932474

# (2) os hashes dos dois lados tem de coincidir: a saida deve ser VAZIA
Compare-Object `
  (Get-ChildItem -File $origem  | Sort-Object Name | ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }) `
  (Get-ChildItem -File $destino | Sort-Object Name | ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash })

# (3) a origem continua intacta
"arquivos na origem: " + (Get-ChildItem -File $origem).Count            # 36

# (4) idempotencia: rodar de novo nao copia nem regrava nada
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py migrar --origem $origem --destino $destino
```

Registre a saída em `$evid\migracao-conferida.txt`. **Enquanto a comparação do item 2 não vier vazia,
não siga para o passo 6.**

## 6. Modo local — apontar e subir

> **Revisto em 2026-10-09 (feature 012).** **Não defina a variável.** Suba a aplicação sem configurar
> nada: ela grava em `src/uploads`, que é a pasta canônica. A variável continua existindo, mas como
> **sobreposição de processo** usada pela suíte de testes e pelo invólucro de paridade — defini-la no uso
> normal só faz o dado ir para outro lugar. Texto original preservado abaixo.

A variável é lida **no import**, então ela precisa existir **antes** de o processo subir.

```powershell
$env:ANALISADOR_UPLOAD_FOLDER = $destino
.\.venv\Scripts\python.exe src\app.py
```

Abra `http://127.0.0.1:5000`.

## 7. Provar a continuidade e o não-vazamento para o repositório

> **Revisto em 2026-10-09 (feature 012).** A continuidade continua sendo o que se prova, e o comando
> abaixo continua válido — mas ele deixou de ser "prova de não-vazamento" e passou a ser **conferência de
> que o arquivo caiu no lugar certo**. Sem a variável definida, `src\uploads` **é** o destino, e o
> número esperado sobe em vez de ficar parado. Texto original preservado abaixo.

Na tela: envie a árvore GEDCOM, depois use **Buscar Conexão no GEDCOM** com dois nomes e, em seguida,
**Analisador de DNA** com o CSV e o seu nome. Os três passos têm de concluir sem a mensagem
`Arquivo '...' não existe mais`.

```powershell
# a pasta DENTRO do repositorio nao pode ter ganhado nada
"arquivos em src\uploads: " + (Get-ChildItem -File src\uploads).Count    # 36
```

Se o número subiu, a variável não estava definida na sessão que subiu a aplicação.

## 8. Modo contêiner — a pasta do host montada no alvo que o app já deriva

> **Revisto em 2026-10-09 (feature 012).** A linha de volume válida é a do **repositório**, não a do
> caminho absoluto:
>
> ```yaml
>     volumes:
>       - ./src/uploads:/app/src/uploads
> ```
>
> É exatamente o que a feature 008 entregou, e por isso `git diff HEAD -- docker-compose.yml` fica
> **vazio** depois da 012. O aviso sobre drive compartilhado deixa de se aplicar: um caminho relativo
> dentro do contexto do compose não depende de compartilhamento de drive. Texto original preservado
> abaixo.

No `docker-compose.yml`, a linha de volume do serviço `app` passa a apontar para o destino canônico,
mantendo o alvo interno:

```yaml
    volumes:
      - D:/dados-genealogicos/uploads:/app/src/uploads
```

```powershell
docker compose up -d --build
# na tela: http://127.0.0.1:5080 — repita o passo 7 (envio, busca, DNA)
docker compose down      # preserva os arquivos
docker compose up -d
# na tela de novo: os mesmos arquivos continuam disponiveis e a analise conclui
```

**Se a montagem falhar** (o contêiner sobe e a pasta aparece vazia), o drive não está compartilhado com
o Docker Desktop. O recuo declarado no plano é o volume nomeado — e é uma decisão sua: ele dá
durabilidade, mas tira o acesso direto pelo sistema de arquivos.

## 9. Provar que o instrumento não suja mais a pasta real

```powershell
$antes = Get-ChildItem -File src\uploads | Sort-Object Name |
         ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }

.\.venv\Scripts\python.exe tests\rodar_paridade.py

$depois = Get-ChildItem -File src\uploads | Sort-Object Name |
          ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }

Compare-Object $antes $depois      # a saida DEVE ser vazia: nenhum arquivo novo, nenhum hash alterado
```

**Esperado:** `PARIDADE 100%` e comparação vazia. Antes desta feature, esta mesma execução acrescentava
sondas com nome `*__probe.ged` e as fixtures de CSV de DNA — é o resíduo que a feature existe para
impedir.

## 10. Manifesto de resíduo e expurgo em simulação

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py manifesto `
    --pasta $origem `
    --saida "$evid\manifesto-residuo.txt"

# LEIA o manifesto antes de seguir: nome, sha256 e motivo por arquivo
Get-Content "$evid\manifesto-residuo.txt"

.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py expurgo `
    --manifesto "$evid\manifesto-residuo.txt" --dry-run

"arquivos depois da simulacao: " + (Get-ChildItem -File $origem).Count   # 36 — nada saiu
```

## 11. Expurgo real — só depois de ler o manifesto

```powershell
.\.venv\Scripts\python.exe tests\manutencao_de_uploads.py expurgo `
    --manifesto "$evid\manifesto-residuo.txt" --aplicar --relatorio "$evid\expurgo.txt"

Get-Content "$evid\expurgo.txt"     # removidos, preservados e duplicatas relatadas
```

**Esperado:** saem os 18 arquivos de resíduo de instrumento (6.631 bytes); os seus arquivos permanecem,
com os mesmos hashes; as **três** cópias idênticas da árvore e a **quarta** de conteúdo distinto
aparecem como duplicatas **relatadas e preservadas** (D-06).

## 12. O passo que só você pode decidir

> **Revisto em 2026-10-09 (feature 012) — NÃO EXECUTE ESTE PASSO.**
>
> Este é o trecho mais perigoso do documento depois da reversão. Ele manda apagar `src\uploads\`, e
> depois da feature 012 **essa pasta é o dado canônico**: apagá-la destrói a única cópia, porque a
> segunda pasta deixou de existir. O comando `Remove-Item -Recurse -Force src\uploads` no fim da seção
> está preservado apenas como registro do que a feature 010 previa.
>
> O que a feature 012 faz no lugar disto: remove as **cópias de arrasto** dentro de
> `_reversa_refactor/…/before-after/src-antes/uploads/` (27 arquivos, 50.762.352 bytes, com conferência
> de órfão por `sha256`) e **expurga o resíduo de instrumento** por manifesto, com simulação antes de
> aplicar. Nada em `src/uploads` que seja arquivo do operador é removido. Texto original preservado
> abaixo.

Só **depois** de os passos 5, 7 e 9 estarem verdes, e com o destino conferido, você pode apagar
`src\uploads\` — é este passo manual que retira os 27,9 MB de dado genético da árvore do repositório. A
feature não o executa, e nada neste documento o executa por você.

```powershell
# confira uma ultima vez que o destino tem tudo
Compare-Object `
  (Get-ChildItem -File $origem  | Sort-Object Name | ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }) `
  (Get-ChildItem -File $destino | Sort-Object Name | ForEach-Object { $_.Name + " " + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash })
# se vazio, a decisao e sua:
# Remove-Item -Recurse -Force src\uploads
```

## 13. Diagnóstico

> **Revisto em 2026-10-09 (feature 012).** Três linhas da tabela abaixo perderam a causa. As
> substituições:
>
> | Sintoma | Causa agora | Ação agora |
> |---|---|---|
> | `Arquivo '...' não existe mais` na tela | A variável `ANALISADOR_UPLOAD_FOLDER` foi definida em uma sessão e não na outra — não há mais "dois destinos" | Confira `$env:ANALISADOR_UPLOAD_FOLDER` nas duas sessões e **remova a variável** do uso normal |
> | A pasta aparece vazia e a tela diz que o arquivo não existe | O aplicativo está rodando com a variável apontando para outra pasta | Remova a variável e suba de novo |
> | O contêiner sobe, mas não vê os arquivos | O *bind mount* aponta para um caminho de host que não existe (foi o caso depois da remoção da cópia externa) | Edite o compose para `./src/uploads:/app/src/uploads` e rode `docker compose up -d`. **Nunca `down -v`** — ele apaga o volume do banco |
>
> As linhas sobre instância única, `DATABASE_URL` e paridade continuam corretas. Texto original
> preservado abaixo.

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `Arquivo '...' não existe mais` na tela | A referência do formulário aponta para o outro destino: a variável não foi definida na sessão, ou o valor difere entre os dois modos | Confira `$env:ANALISADOR_UPLOAD_FOLDER` e procure o arquivo citado nos dois destinos |
| `src\uploads` ganhou arquivos depois de uma verificação | A paridade foi executada direto, sem o invólucro | Rode `tests\rodar_paridade.py`; o resíduo novo entra no manifesto do passo 10 |
| A pasta de destino aparece vazia e a tela diz que o arquivo não existe | A aplicação foi apontada para o destino **antes** da migração | Volte ao passo 4 e conclua a cópia |
| O contêiner sobe, mas não vê os arquivos | Drive não compartilhado com o Docker Desktop, ou caminho com a sintaxe errada | Confira o compartilhamento e use `D:/...` com barra normal na composição |
| O contêiner não sobe | `DATABASE_URL` ausente no `.env` | O `docker-compose.yml` exige a variável para o serviço `app` |
| A segunda instância recusa subir | Guarda de instância única (porta ocupada) | Encerre a instância anterior ou troque `ANALISADOR_PORT` |

## 14. Encerrar

> **Revisto em 2026-10-09 (feature 012).** O segundo comando continua válido e agora é **recomendado** em
> qualquer sessão: a variável não deve ficar definida no uso normal. O parágrafo abaixo está **invertido**
> depois da reversão: esquecer a variável passou a ser o comportamento correto — a aplicação grava em
> `src/uploads`, que é a pasta canônica. Texto original preservado abaixo.

```powershell
docker compose down                      # preserva o volume do banco e a pasta canonica
Remove-Item Env:\ANALISADOR_UPLOAD_FOLDER   # a variavel vale so nesta sessao
```

Lembre que a variável é **de sessão**: em cada nova janela de terminal é preciso defini-la de novo antes
de subir a aplicação — esquecer não gera erro, e a aplicação volta a gravar dentro do repositório.

## 15. Fontes

- `_reversa_forward/010-uploads-fora-do-repositorio/roadmap.md` — decisões D-01 a D-08
- `_reversa_forward/010-uploads-fora-do-repositorio/investigation.md` — alternativas e medições
- `_reversa_sdd/upload-gedcom/contracts.md#2.2` — contrato da pasta
- `_reversa_sdd/parity/harness.py:356,465` — o que o invólucro explora
- `_reversa_forward/007-dono-no-port-e-baseline/evidence/T015-verificacao-manual.md:26` — precedente do
  redirecionamento da pasta em verificação manual

## 16. Resultados medidos nesta execução (2026-10-09)

> **Revisto em 2026-10-09 (feature 012).** Esta tabela é **registro histórico** da execução da feature
> 010, naquele dia, quando o destino canônico ainda era `D:\dados-genealogicos\uploads`. Nada dela deve
> ser reproduzido: a pasta externa não existe mais, a linha de volume do compose voltou a ser
> `./src/uploads`, e o `src/uploads` que a tabela diz ter ficado em 36 arquivos tem hoje **18**, depois
> do expurgo do resíduo feito pela feature 012. As duas últimas linhas — a nota sobre os quatro
> arquivos sintéticos e o fato de o passo 11 não ter sido executado — ficam como estavam, porque
> descrevem o estado em que a feature 010 terminou.
>
> **Correção medida em 2026-10-09, na feature 012:** os quatro arquivos `*__sonda_t014.*` que a nota
> abaixo diz estarem no destino canônico **não existem em lugar nenhum** — varredura completa do
> repositório. O banco, porém, guarda **duas linhas** de `dna_analysis` cujo `tree_ref` aponta para
> `0646f8431ba58cca__sonda_t014.ged` e `dbc25ecc1cb17db3__sonda_t014.ged`: são referências que já não
> resolvem, e nada no runtime as lê (zero `SELECT` em `src/`). Registrado em
> `_reversa_forward/012-pasta-canonica-no-repositorio/data-delta.md` §6.

| Passo | Medição | Evidência |
|---|---|---|
| 2 | `302 passed, 8 skipped` na suíte; `PARIDADE 100%` com a variável definida à mão | `evidence/linha-de-base-suite.txt`, `evidence/linha-de-base-paridade.txt` |
| 3 a 5 | Migração: **36 copiados, 0 divergentes**, `27.932.474` bytes nos dois lados, origem intacta | `evidence/migracao-conferida.txt` |
| 6 e 7 | Modo local: as três etapas concluíram e **`src/uploads` ficou em 36** enquanto o destino ia de 36 para 38 | `evidence/T014-verificacao-local.md` |
| 8 | Modo contêiner pela porta 5080, com `down`/`up`: destino `38 → 39 → 40`, três etapas concluídas antes e depois do ciclo | `evidence/T016-conteiner.md` |
| 9 | `PARIDADE 100%` pelo invólucro, pasta real **36 → 36 sem alteração**, **13 arquivos** na pasta descartável (controle positivo) | `evidence/T017-isolamento-do-instrumento.md` |
| 10 | Manifesto com **18 arquivos**; simulação com **18 removidos simulados, 0 recusados** e inventário idêntico ao final | `evidence/manifesto-residuo.txt`, `evidence/T018-expurgo-simulado.txt` |
| 10 | Duplicatas relatadas e preservadas: **3 grupos** — três cópias da árvore unificada, três de `Famílias_Sergipanas.csv` e duas de `Adriano_Santos.ged` | `evidence/T018-expurgo-simulado.txt` |
| 12 | Escopo: `git diff` **vazio** em `src/` e `_reversa_sdd/`; `harness.py` sem alteração | `evidence/T020-conferencia-de-escopo.md` |

**Arquivos sintéticos deixados no destino canônico pelas provas:** quatro (`*__sonda_t014.ged` e
`*__sonda_t014.csv`, dos passos 7 e 8). São de fixture, não do operador, e saem com o próprio expurgo ou à
mão. O **passo 11 não foi executado**: o expurgo real é decisão sua, no passo 12.
