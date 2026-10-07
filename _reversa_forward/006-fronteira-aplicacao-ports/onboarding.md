# Onboarding: fronteira de aplicação em `src/` (Onda 2 do cutover)

> Identificador: `006-fronteira-aplicacao-ports`
> Data: `2026-10-07`
> Para quem vai testar esta feature pela primeira vez, do zero.

Este roteiro tem sete passos, na ordem. Do passo 1 ao 5 você confere que **nada mudou**; do 6 ao 7 você confere que a fronteira **existe**. Os dois lados importam: uma extração que preserva tudo e não cria fronteira nenhuma passaria nos passos 1 a 5.

Os comandos são de PowerShell, na raiz do projeto. Nenhum deles escreve no legado.

## 0. Antes de começar

**Nunca use dado real de DNA ou GEDCOM neste roteiro.** O Princípio I do projeto proíbe. Tudo aqui usa fixture sintética gerada pelo próprio repositório.

```powershell
# Confirme que está na raiz do projeto e veja o que já está sujo ANTES de mexer.
git status --short
```

Anote a saída. Se houver algo listado agora, não é desta feature — e no passo 7 você vai comparar contra esta lista, não contra o vazio.

## 1. Prepare o interpretador e as fixtures sintéticas

```powershell
# As fixtures de paridade são geradas, não versionadas.
python _reversa_sdd/parity/make_fixtures.py

# Confirme que as duas que este roteiro usa existem.
Get-ChildItem _reversa_sdd/parity/fixtures/gedcom/basic.ged, _reversa_sdd/parity/fixtures/dna/cm_boundaries.csv
```

Esperado: os dois caminhos aparecem, sem erro. Se o script reclamar, ele diz o que faltou — não invente fixture à mão.

## 2. Meça o baseline da suíte

O diretório temporário do sistema não é gravável neste ambiente. Sem apontar `TEMP` e `TMP` para uma pasta do projeto, **15 erros** de `test_upload_seguranca.py` aparecem no `setup` por `PermissionError` — e eles **não** são regressão de código. São a linha de base.

```powershell
New-Item -ItemType Directory -Force -Path .pytest-tmp | Out-Null
$env:TEMP = (Resolve-Path .pytest-tmp).Path
$env:TMP  = (Resolve-Path .pytest-tmp).Path
python -m pytest -q 2>&1 | Select-Object -Last 5
```

Esperado, ao fim de todas as três extrações desta feature:

```
178 passed, 15 errors
```

Os **15 errors** são esperados e não contam contra a feature. Qualquer outro número é regressão, e a `RF-16` recusa a entrega.

## 3. Meça o baseline da paridade

Este é o instrumento que prova que nenhum resultado de domínio mudou. Ele roda o oráculo congelado (`_reversa_sdd/oracle/app_legacy_e43ca22.py`) e o candidato (`src/`) em processos separados e compara **valores exatos**, sem tolerância.

```powershell
python _reversa_sdd/parity/harness.py
echo "exit=$LASTEXITCODE"
```

Esperado, ao fim de todas as três extrações:

```
exit=0
```

com **100 % de paridade nas 6 fixtures** e zero divergência. Se aparecer divergência, ela vem com a fixture e a chave — anote as duas antes de investigar.

## 4. Prove que a fronteira existe

Este passo não mede comportamento; mede **forma**. É o único que falha se você só tiver mexido em nomes.

```powershell
# 4a. A rota deixou de orquestrar? Não deve haver chamada de domínio em index().
Select-String -Path src/app.py -Pattern 'carregar_arvore|dna_analysis_flow|path_search_flow|aggregate_matches|detect_columns|generate_mermaid'

# 4b. A fronteira existe?
Get-ChildItem src/application, src/ports, src/core/erros.py

# 4c. O núcleo não importa a fronteira (RF-13).
python -m pytest tests/test_dependencias_nucleo.py -q
```

Esperado:

- **4a** só pode apontar o que o adaptador legitimamente faz: montar dependências e chamar o caso de uso. Se aparecer chamada direta a `carregar_arvore`, `dna_analysis_flow` ou `path_search_flow` dentro de `index()`, a `RF-01` não foi cumprida.
- **4b** lista `application/` com três casos de uso, `ports/` com as portas, e `erros.py`.
- **4c** passa, com 4 guardas verdes.

## 5. Prove que a hierarquia de exceção preserva o contrato antigo

Este é o ponto mais fácil de errar em silêncio: as quatro asserções da suíte capturam `ValueError` **e** conferem o texto. Os dois têm de continuar valendo.

```powershell
python -m pytest tests/test_confrontacao_gedcom_dna.py tests/test_dna_analysis.py -q -k "erro or coluna or raiz or matches"
```

Esperado: passa. Se falhar por tipo, a raiz `ErroDeDominio` deixou de herdar de `ValueError`. Se falhar por texto, algum literal mudou — e aí a `RN-04` foi violada.

## 6. Verificação manual de ponta a ponta

Suba o servidor de produção. A porta é escolhida aqui para não colidir com nada; a guarda de exclusividade do `app.py` recusa duas instâncias na mesma porta.

```powershell
$env:ANALISADOR_PORT = "58041"
$env:ANALISADOR_UPLOAD_FOLDER = "$PWD\src\uploads"
Start-Process -NoNewWindow python -ArgumentList "src/app.py"
Start-Sleep -Seconds 3
```

### 6.1 A raiz responde

```powershell
curl.exe -s -o $env:TEMP\raiz.html -w "status=%{http_code}`n" http://127.0.0.1:58041/
Select-String -Path $env:TEMP\raiz.html -Pattern 'Arquivo GEDCOM|Carregar e Analisar' | Select-Object -First 3
```

Esperado: `status=200`, e o formulário de upload presente com o rótulo `Arquivo GEDCOM`.

### 6.2 Upload do GEDCOM

```powershell
curl.exe -s -o $env:TEMP\upload.html -w "status=%{http_code}`n" `
  -F "action=upload_gedcom" `
  -F "gedcom=@_reversa_sdd/parity/fixtures/gedcom/basic.ged" `
  http://127.0.0.1:58041/
```

Esperado: `status=200`, e a mensagem de sucesso com o **nome original** do arquivo. Guarde a referência devolvida — é ela que os próximos POST carregam:

```powershell
$chave = (Select-String -Path $env:TEMP\upload.html -Pattern 'name="gedcom_filename" value="([^"]+)"').Matches[0].Groups[1].Value
echo "chave=$chave"
```

Esperado: algo da forma `c6926bb74ce64b88__basic.ged` — chave de conteúdo, dois underscores, nome original preservado. A lista de nomes sugeridos tem **7** entradas.

### 6.3 Análise de DNA

```powershell
curl.exe -s -o $env:TEMP\dna.html -w "status=%{http_code}`n" `
  -F "action=dna_analysis" `
  -F "gedcom_filename=$chave" `
  -F "root_name=Ana Silva" `
  -F "matches_csv=@_reversa_sdd/parity/fixtures/dna/cm_boundaries.csv" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\dna.html -Pattern 'Resultados da Análise de DNA|Matches descartados|Relacionamento Provável' | Select-Object -First 3
```

Esperado: `status=200` e os três cabeçalhos presentes. **Não** pode aparecer `Ocorreu um erro`.

### 6.4 Busca de caminho — direto e por afinidade

```powershell
# Direto: ancestral comum.
curl.exe -s -o $env:TEMP\direto.html -w "status=%{http_code}`n" `
  -F "action=path_search" -F "gedcom_filename=$chave" `
  -F "person1_name=Carlos Silva" -F "person2_name=Ana Silva" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\direto.html -Pattern 'Conexão entre|Resultado da Busca' | Select-Object -First 2

# Por afinidade: casamento no trajeto — NÃO pode ser apresentado como consanguíneo.
curl.exe -s -o $env:TEMP\afinidade.html -w "status=%{http_code}`n" `
  -F "action=path_search" -F "gedcom_filename=$chave" `
  -F "person1_name=Carlos Silva" -F "person2_name=Bia Oliveira" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\afinidade.html -Pattern 'afinidade|NÃO representa parentesco consanguíneo' | Select-Object -First 2
```

Esperado, nos dois: `status=200`. No segundo, o aviso de afinidade **presente** e em maiúsculas — ele é contrato do Princípio IV e a extração não pode tê-lo perdido.

### 6.5 O desfecho decide o modo de renderização

Este passo é o que prova o achado `A003` fechado, e é o mais fácil de perder de vista: dois retornos que **parecem** iguais precisam render **diferente**.

```powershell
# Sucesso COM resultado: deve aparecer o cartão de resultado.
Select-String -Path $env:TEMP\direto.html -Pattern 'Resultado da Busca de Conexão|Conexão entre' | Select-Object -First 2

# Sucesso SEM resultado: "nenhuma conexão" é resultado BEM-SUCEDIDO, não alerta de erro.
curl.exe -s -o $env:TEMP\semconexao.html -w "status=%{http_code}`n" `
  -F "action=path_search" -F "gedcom_filename=$chave" `
  -F "person1_name=Lone Ranger" -F "person2_name=Ana Silva" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\semconexao.html -Pattern 'Nenhuma conexão encontrada' | Select-Object -First 1

# Falha sinalizada: deve vir como alerta de ERRO, com o prefixo do literal de erro.
curl.exe -s -o $env:TEMP\naoencontrada.html -w "status=%{http_code}`n" `
  -F "action=path_search" -F "gedcom_filename=$chave" `
  -F "person1_name=Zzz Ninguem" -F "person2_name=Ana Silva" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\naoencontrada.html -Pattern "Pessoa 1 'Zzz Ninguem' não encontrada" | Select-Object -First 1
```

Esperado: os três retornam `status=200` — **o status não distingue os casos**. O que distingue é o **modo de renderização**, e ele vem do campo de desfecho do resultado, nunca do texto da mensagem. Se você trocar o texto de uma das mensagens e o modo não mudar, o `A003` está de fato fechado; se o modo mudar junto com o texto, o adaptador está inferindo do texto e a `RF-20` foi violada.

### 6.6 As três mensagens negativas de upload

```powershell
# Sem arquivo no campo.
curl.exe -s -o $env:TEMP\sem.html -w "status=%{http_code}`n" `
  -F "action=upload_gedcom" http://127.0.0.1:58041/
Select-String -Path $env:TEMP\sem.html -Pattern 'Nenhum arquivo GEDCOM enviado' | Select-Object -First 1

# Nome de arquivo vazio.
curl.exe -s -o $env:TEMP\vazio.html -w "status=%{http_code}`n" `
  -F "action=upload_gedcom" -F "gedcom=@_reversa_sdd/parity/fixtures/gedcom/basic.ged;filename=" `
  http://127.0.0.1:58041/
Select-String -Path $env:TEMP\vazio.html -Pattern 'Nenhum arquivo selecionado' | Select-Object -First 1
```

Esperado, nos dois: `status=200` e o literal exato presente, ao caractere, incluindo o ponto final.

### 6.7 Encerre o servidor

```powershell
Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-10) } |
  Stop-Process -Force
```

Confirme que a porta voltou a responder erro de conexão recusada. Se o servidor ficar de pé, a próxima execução falha na guarda de exclusividade — e o sintoma não parece com a causa.

## 7. Limpe o resíduo e confira o repositório

O passo 6 gravou o GEDCOM e o CSV em `src/uploads/`. **O `_clean_residue.py` não limpa isso** — ele cuida apenas do instrumento de paridade (`OBS-10`). A limpeza é manual:

```powershell
# Veja o que a verificação deixou.
Get-ChildItem src/uploads -ErrorAction SilentlyContinue

# Remova SÓ o resíduo da verificação, e só depois de conferir a lista acima.
Remove-Item src/uploads/* -Force -ErrorAction SilentlyContinue

# O instrumento de paridade tem limpador próprio.
python _reversa_sdd/parity/_clean_residue.py

# Compare com a anotação do passo 0. Nada novo pode ter sobrado.
git status --short
```

Esperado: a saída do `git status` é a mesma do passo 0. Se aparecer arquivo em `src/uploads/` ou qualquer `.json` de observação do harness, o Princípio I foi violado e a entrega não fecha.

## Tabela de resultados esperados

| Passo | O que mede | Esperado |
|---|---|---|
| 1 | Fixtures sintéticas | `basic.ged` e `cm_boundaries.csv` existem |
| 2 | Suíte | `178 passed, 15 errors` |
| 3 | Paridade | `exit=0`, 100 % em 6 fixtures |
| 4 | A fronteira existe | `application/`, `ports/`, `erros.py` presentes; `index()` sem chamada de domínio; guardas verdes |
| 5 | Contrato de exceção | 4 asserções de `ValueError` passando sem reescrita |
| 6.1–6.2 | Upload | `200`, formulário, chave de conteúdo, 7 nomes |
| 6.3 | DNA | `200`, três cabeçalhos, sem `Ocorreu um erro` |
| 6.4 | Caminho | `200` nos dois modos, aviso de afinidade presente |
| 6.5 | Mensagens negativas | os dois literais exatos |
| 7 | Resíduo | `git status` igual ao do passo 0 |

## Se algo falhar

| Sintoma | Causa provável | Onde olhar |
|---|---|---|
| 15 erros viram mais que 15 | `TEMP`/`TMP` não apontados para `.pytest-tmp`, ou regressão real | passo 2; compare a lista de erros, não só a contagem |
| Paridade com divergência | alguma extração mexeu em ordem de avaliação, ordem de inserção ou arredondamento | passo 3; a divergência diz a fixture e a chave |
| Teste de exceção falha por tipo | a raiz deixou de herdar de `ValueError` | passo 5; `RF-05` |
| Teste de exceção falha por texto | um literal de tela mudou | passo 5; `RF-04` e `RN-04` |
| Nenhum literal negativo aparece | a tradução de exceção → mensagem não cobre o caso | passo 6.5; a tabela em `src/application/` |
| `index()` ainda chama o núcleo direto | a extração parou no meio | passo 4a; `RF-01` e a ordem de `D-08` |
| O servidor não sobe | instância anterior na mesma porta | passo 6.7; a guarda de exclusividade recusa a segunda |
| `git status` com arquivo novo | resíduo da verificação | passo 7; o limpador não cobre `src/uploads/` |
