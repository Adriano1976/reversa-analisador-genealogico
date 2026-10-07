# Onboarding: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Requirements: `_reversa_forward/007-dono-no-port-e-baseline/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Para quem é este documento

Para quem vai **testar esta feature pela primeira vez**, sem ter acompanhado o
desenvolvimento. Ele é executável de ponta a ponta: cada passo traz o comando e o
resultado esperado, e o resultado esperado é um número, não uma impressão.

O que ele prova, em três frases: os 15 testes de rota que nunca executavam nesta
máquina **executam e passam**; o dono está na assinatura das duas portas e **não**
muda comportamento nenhum; e a paridade contra o oráculo congelado continua em 100 %
no interpretador oficial.

## 2. Pré-requisitos

| Item | Valor |
|---|---|
| Sistema | Windows com o defeito de `0o700` documentado, **ou** qualquer outro — a correção vale nos dois |
| Interpretador **oficial** | `.venv\Scripts\python.exe` (decisão de 2026-10-05, registrada em `requirements.txt`) |
| Pacotes | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| Raiz de trabalho | `D:\Projetos\reversa_analisador_gelealogico` |
| Estado de partida | Nenhum. Não há dado a migrar, não há schema, não há passo manual de ambiente |

⚠️ **Não use o `python` global para aferir esta feature.** Ele tem `ged4py 0.5.2`,
`networkx 3.6.1` e `pandas 3.0.3`, que são as versões do **manifesto do oráculo**, e
não as do pin do projeto (`0.5.5` / `3.7` / `3.0.6`). A medição de 2026-10-07 mostrou
que os dois dão o mesmo resultado observável — mas o instrumento oficial é o `.venv/`,
e é ele que a `RF-08` e a `RF-10` exigem.

## 3. Números esperados

| Medição | Antes desta feature | **Depois, esperado** |
|---|---|---|
| Suíte completa | `231 passed, 15 errors` | **`0 errors`** e nenhum teste a menos |
| `tests/test_upload_seguranca.py` | `21 passed, 15 errors` | **`36 passed`** |
| Paridade diferencial | `100 %`, exit 0 | **`100 %`, exit 0** |
| Resíduo em `tests/.tmp/` | *(não existia)* | **ausente ao fim** |

⚠️ **O total de aprovados vai crescer, e isso não é regressão.** A conta é
`231 + 15 = 246`, e os 15 **não são testes novos**: são os mesmos que já existiam e
não executavam. Depois entram os testes do contrato novo (`RF-05`), que somam a partir
de 246. **A regra de comparação é por conjunto, não por total:** nenhum teste que
passava pode passar a falhar, e nenhum teste pode ser removido ou desabilitado.

## 4. Passo 1 — a suíte executa os 15, e não há erro de ambiente

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
.venv\Scripts\python.exe -m pytest -q
```

Esperado: **`0 errors`** e nenhuma falha. Se aparecer qualquer `ERROR ... at setup`,
o passo 1 falhou — e o passo 4 abaixo diz o que fazer.

Para ver os 15 nominalmente:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_upload_seguranca.py -q -rE
```

Esperado: `36 passed`, e **nenhuma** linha `ERROR`. Antes desta feature este comando
terminava em `21 passed, 15 errors`, e os 15 nomes eram os de `TestReproducao` (9),
`TestRegressao` (4) e `TestExtensaoPreservada` (2).

**O que este passo prova.** O erro de ambiente não era do produto: era o pytest tentando
**listar** um diretório-base criado com `0o700` (`_pytest/tmpdir.py:168` →
`_pytest/pathlib.py:175`). Com o fixture `tmp_path` declarado em `tests/conftest.py`,
esse caminho não é percorrido.

**O que este passo NÃO deve mostrar.** Nenhum arquivo de teste foi editado. Se o
`git diff` listar `tests/test_upload_seguranca.py`, algo saiu do escopo — a `RF-06`
proíbe tocar nesse arquivo, inclusive para "melhorar" um fixture.

## 5. Passo 2 — a correção do ambiente é do repositório, não da máquina

```powershell
Test-Path tests\.tmp          # esperado: False
git status --short            # esperado: tests/.tmp/ NÃO aparece
```

**O que este passo prova.** A correção não deixa estado na máquina: o diretório
temporário da suíte é criado e removido em cada execução, e nada depende de variável de
ambiente, de `--basetemp` na linha de comando nem de caminho absoluto de estação.

⚠️ **Ponto de atenção medido, e o motivo de ele estar aqui.** Sem a saída do diretório
corrente antes da remoção, **15 diretórios vazios sobrevivem por execução** — porque
`app_cliente` faz `monkeypatch.chdir(tmp_path)` e o pytest desmonta o `tmp_path` antes
de o `monkeypatch` desfazer o `chdir`. Se `tests/.tmp/` aparecer com 15 entradas vazias,
a remoção regrediu. Elas **não** são diretórios presos: apague com
`Remove-Item -Recurse -Force tests\.tmp` sem privilégio nenhum.

## 6. Passo 3 — a paridade continua em 100 %, no interpretador oficial

```powershell
.venv\Scripts\python.exe _reversa_sdd\parity\harness.py
```

Esperado: **`PARIDADE 100%`** nas 6 fixtures e **exit code 0**.

**O que este passo prova.** A costura do dono não tocou nenhum limiar, peso, ordem de
avaliação ou critério de matching. A assinatura de retorno do núcleo continua a tupla de
três com o indicador de sucesso, e o `Tree` continua com quatro elementos (`RF-11`).

## 7. Passo 4 — o contrato do port, à mão

Salve o script abaixo como `_verificar_dono.py` na **raiz do projeto** e rode com
`.venv\Scripts\python.exe _verificar_dono.py`. Apague-o depois.

```python
import sys
sys.path.insert(0, "src")

import inspect
import os
import tempfile
from pathlib import Path

from ports import ArmazenamentoDeArquivos, CarregadorDeArvores
from ports.adaptadores import ArmazenamentoEmDisco

# 1. O dono esta na assinatura e NAO tem valor padrao (RF-01, RF-12).
for classe, metodo in ((ArmazenamentoDeArquivos, "guardar"),
                       (ArmazenamentoDeArquivos, "resolver"),
                       (CarregadorDeArvores, "carregar")):
    assinatura = inspect.signature(getattr(classe, metodo))
    parametro = assinatura.parameters["dono"]
    assert parametro.default is inspect.Parameter.empty, (classe, metodo)
    print(f"OK  {classe.__name__}.{metodo}{assinatura}")

# 2. A chamada sem o dono e recusada pelo proprio contrato (RF-05).
assinatura = inspect.signature(ArmazenamentoDeArquivos.guardar)
try:
    assinatura.bind(object(), b"x", "a.ged", "gedcom")
except TypeError as erro:
    print(f"OK  chamada sem dono recusada: {erro}")
else:
    raise AssertionError("a chamada sem dono foi aceita")

# 3. O adaptador aceita o dono e NAO o usa para decidir chave nem caminho (RF-02).
pasta = os.path.join(tempfile.gettempdir(), "_verificar_dono_uploads")
os.makedirs(pasta, exist_ok=True)
armazenamento = ArmazenamentoEmDisco(pasta)
conteudo = b"0 HEAD\n1 SOUR TESTE\n0 TRLR\n"
caminho_a, motivo_a = armazenamento.guardar(conteudo, "arvore.ged", "gedcom", "dono-a")
caminho_b, motivo_b = armazenamento.guardar(conteudo, "arvore.ged", "gedcom", "dono-b")
assert motivo_a is None and motivo_b is None
assert caminho_a == caminho_b, (caminho_a, caminho_b)
assert os.listdir(pasta) == [os.path.basename(caminho_a)], os.listdir(pasta)
print(f"OK  dois donos, um arquivo so: {os.path.basename(caminho_a)}")

import shutil
shutil.rmtree(pasta, ignore_errors=True)
print("TUDO OK")
```

Esperado: quatro linhas `OK`, uma linha `TUDO OK` e nenhum `AssertionError`.

**O que este passo prova.** As três metades da costura: o dono é obrigatório e sem
padrão; a ausência dele é recusada pelo **próprio contrato**, não por validação em
tempo de execução; e o adaptador **ignora** o dono — dois donos diferentes, mesmo
conteúdo, **um** arquivo só.

**O que este passo NÃO prova.** Nada de isolamento. Ver a §10.

## 8. Passo 5 — o contrato novo, pelos testes do repositório

```powershell
.venv\Scripts\python.exe -m pytest tests\test_porta_de_armazenamento.py -v
```

Esperado: todos passam, incluindo a classe nova do contrato de armazenamento, ao lado do
teste estrutural do `RepositorioDeArvores` que a feature 006 deixou (`T028`).

## 9. Passo 6 — a aplicação de ponta a ponta

Prepare a pasta descartável e o GEDCOM **sintético** (Princípio I: nunca use dado real):

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
$pasta = "$PWD\_reversa_forward\007-dono-no-port-e-baseline\evidence\_tmp_e2e"
New-Item -ItemType Directory -Force -Path "$pasta\uploads" | Out-Null
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'tests'); from fixtures.sample_gedcom import SAMPLE_GED; open(r'$pasta\arvore.ged', 'w', encoding='utf-8').write(SAMPLE_GED)"
Set-Content -Path "$pasta\matches.csv" -Value "Name,cM`nCarlos Silva,150" -Encoding ascii
```

Suba o servidor em outra janela:

```powershell
cd D:\Projetos\reversa_analisador_gelealogico\src
$env:ANALISADOR_UPLOAD_FOLDER = "D:\Projetos\reversa_analisador_gelealogico\_reversa_forward\007-dono-no-port-e-baseline\evidence\_tmp_e2e\uploads"
$env:ANALISADOR_PORT = "5057"
..\.venv\Scripts\python.exe app.py
```

Esperado na janela: `Servindo com waitress em http://127.0.0.1:5057 com 4 threads`.

Os três fluxos, em outra janela:

```powershell
$pasta = "D:\Projetos\reversa_analisador_gelealogico\_reversa_forward\007-dono-no-port-e-baseline\evidence\_tmp_e2e"

# Fluxo 1 — upload do GEDCOM
curl.exe -s -X POST http://127.0.0.1:5057/ -F "action=upload_gedcom" -F "gedcom=@$pasta\arvore.ged" -o "$pasta\1_upload.html"
Select-String -Path "$pasta\1_upload.html" -Pattern 'gedcom_filename" value="([^"]+)"'

# Copie a chave que o comando acima imprime e use nas duas chamadas seguintes:
$chave = "<cole aqui a chave>"

# Fluxo 2 — busca de caminho (Carlos e Ana sao irmaos: caminho direto)
curl.exe -s -X POST http://127.0.0.1:5057/ -F "action=path_search" -F "gedcom_filename=$chave" -F "person1_name=Carlos Silva" -F "person2_name=Ana Silva" -o "$pasta\2_busca.html"

# Fluxo 3 — analise de DNA
curl.exe -s -X POST http://127.0.0.1:5057/ -F "action=dna_analysis" -F "gedcom_filename=$chave" -F "root_name=Carlos Silva" -F "matches_csv=@$pasta\matches.csv" -o "$pasta\3_dna.html"
```

Esperado em cada HTML: a mensagem de sucesso correspondente, e nenhuma tela de erro.
As dez mensagens da camada de rota são **contrato congelado** e continuam ao caractere
(`RN-03`) — nenhuma delas foi tocada por esta feature.

Pare o servidor com `Ctrl+C` ao terminar.

## 10. Passo 7 — o que esta feature **não** fez

Leia esta seção antes de escrever qualquer conclusão. Ela existe para impedir a leitura
errada mais provável desta entrega.

| Afirmação | Veredito |
|---|---|
| "O dono isola os arquivos de cada usuário" | ❌ **FALSO.** O armazenamento continua **único por processo**: a chave vem do conteúdo, e dois donos com o mesmo conteúdo chegam ao **mesmo** arquivo — é literalmente o que o passo 4 prova. Nenhum arquivo é separado por dono |
| "A dívida #4 (isolamento) foi fechada" | ❌ **FALSO.** Ela segue aberta. A `RN-06` proíbe esta afirmação em qualquer artefato da feature |
| "A dívida #3 (corrida entre requisições) foi fechada" | ❌ **FALSO.** A guarda de exclusividade continua de **processo**, não de thread. O que a feature faz é **nomear** a dívida no comentário da constante de dono |
| "O `RepositorioDeArvores` ganhou implementação" | ❌ **FALSO.** Continua declarado, sem implementação e **sem consumidor**. Esta feature prepara a porta de armazenamento, não a persistência |
| "Os cinco testes novos são de produto" | ⚠️ Depende. A correção do ambiente **não** acrescenta teste de produto: ela faz 15 testes existentes executarem. Os testes do `RF-05` são de contrato, e nenhum deles muda comportamento |
| "A linha de base antiga estava errada" | ❌ **FALSO.** `178 aprovados, 15 erros` e `231 aprovados, 15 erros` foram medições **reais**, feitas numa máquina onde 15 testes não executavam. Elas ficam **históricas**, não erradas (`RN-04`) |
| "O dono é autenticação" | ❌ **FALSO.** Não há sessão, login nem papel no sistema (`_reversa_sdd/permissions.md`, `P-01` a `P-05`). O dono é marcador de costura com valor único, não credencial |

## 11. Passo 8 — os 13 diretórios presos continuam lá, e isso é o esperado

```powershell
git status --short
```

Esperado: nenhum resíduo de `src/uploads/`, de `uploads/` nem de `tests/.tmp/`. Um
`warning: could not open directory '...'` nas pastas presas é **esperado** e não é
defeito desta feature: são os 13 diretórios inacessíveis, 8 deles anteriores à feature
006. Eles continuam apenas **documentados**, com o comando de remoção que exige shell
elevado, em `_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md` §2.2.

⚠️ Eles **não** foram removidos por esta feature, por decisão registrada na sessão de
esclarecimento: são resíduo de execução, não defeito do produto, e removê-los exige
privilégio que a sessão não tem. Por isso o `collect_ignore = ["_basetemp_probe"]` de
`tests/conftest.py` **permanece** — sem ele, a coleta da suíte aborta inteira ao descer
em `tests/_basetemp_probe/`.

## 12. Se algo divergir

| Sintoma | O que significa | O que fazer |
|---|---|---|
| `ERROR ... at setup` com `PermissionError [WinError 5]` em `pytest-of-<usuário>` | O fixture `tmp_path` de `tests/conftest.py` saiu de vigor, ou alguém voltou a pedir `tmp_path_factory`/`tmpdir` | Restaure a substituição. A causa medida está na §2 do `investigation.md`, e o teste do `D-04` existe para acusar isso antes de você |
| `tests/.tmp/` com 15 entradas vazias | A saída de CWD antes do `rmtree` regrediu (`D-03`) | Ver o ponto de atenção da §5 |
| Uma falha em `tests/test_upload_seguranca.py` que **não** é de setup | É um teste que **nunca executou** nesta máquina e está falhando por motivo de produto | **Pare.** A `RF-09` exige veredito explícito e datado: **defeito de produto** vira requisito próprio, com arquivo e linha, e **não** é corrigido nesta feature; **defeito de teste** é corrigido aqui, com o motivo declarado. Nenhuma falha fica sem veredito |
| `PARIDADE` abaixo de 100 % | Alguma constante de domínio mudou de valor | Reverta a mudança: ela está fora do escopo desta feature (`RF-10`, `RF-11`) |
| Diferença no `git diff` de `tests/test_upload_seguranca.py` | A `RF-06` foi violada | Reverta. Nenhum teste pode ser removido, desabilitado, renomeado ou ter asserção reescrita |
| O total de aprovados caiu em relação ao bloco anterior | Regressão real | A regra é por conjunto: nenhum aprovado pode virar falha (`D-12`) |

## 13. Roteiro mínimo, em uma tela

```powershell
cd D:\Projetos\reversa_analisador_gelealogico

# 1. os 15 executam, e nao ha erro de ambiente
.venv\Scripts\python.exe -m pytest -q

# 2. a correcao nao deixa estado na maquina
Test-Path tests\.tmp

# 3. a paridade continua em 100 %, no interpretador oficial
.venv\Scripts\python.exe _reversa_sdd\parity\harness.py

# 4. o contrato do port, a mao
.venv\Scripts\python.exe _verificar_dono.py

# 5. nada de residuo
git status --short
```

Se os cinco passos derem o resultado esperado, a feature está aceita.
