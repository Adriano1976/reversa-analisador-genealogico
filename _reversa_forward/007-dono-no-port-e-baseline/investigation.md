# Investigation: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Requirements: `_reversa_forward/007-dono-no-port-e-baseline/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. As três perguntas desta investigação

| # | Pergunta | Por que ela decide o plano |
|---|---|---|
| P1 | Por que os 15 testes de rota não executam, exatamente? | A resposta determina **onde** a correção pode ser feita. "É o `0o700`" leva a uma correção; "é o `getbasetemp()`" leva a outra, incompatível com a primeira |
| P2 | Onde a correção pode viver, dado que `pytest.ini` está fora de `allowedPaths`? | A `RF-07` fixa `tests/conftest.py`. Era preciso confirmar que dava para corrigir a suíte inteira de lá, e não só o fixture de um arquivo |
| P3 | Como o dono entra nas duas portas sem mudar comportamento nenhum? | É a parte de contrato: onde o parâmetro fica, quem o repassa, e por que ele não vira escopo de armazenamento |

Nada aqui é conclusão sem medição. As medições foram feitas **antes** de escrever o
roadmap, com sondas descartáveis, e todas as sondas foram removidas depois — o
`git status` ao fim da investigação não lista nenhum arquivo de sonda.

## 2. P1 — a causa real não é o modo do diretório por teste

### 2.1 O que a leitura do pytest mostra

O pytest 9.1.1 do interpretador oficial (`.venv/`) cria diretórios temporários em
`.venv/Lib/site-packages/_pytest/tmpdir.py`, e a cadeia é esta:

1. O fixture `tmp_path` (`tmpdir.py:290-312`) chama `_mk_tmp(request, tmp_path_factory)`.
2. `_mk_tmp` (`:282-287`) chama `factory.mktemp(nome, numbered=True)`.
3. `TempPathFactory.mktemp` (`:121-143`) chama `_ensure_relative_to_basetemp`, que
   chama **`self.getbasetemp()`** (`:117`).
4. `getbasetemp` (`:145-229`), quando `--basetemp` não foi dado, monta
   `rootdir = <tempfile.gettempdir()>/pytest-of-<usuário>` e o cria com
   **`rootdir.mkdir(mode=0o700, exist_ok=True)`** (`:168`).
5. Em seguida chama `make_numbered_dir_with_cleanup(...)`, que varre o diretório-base
   com `find_prefixed(rootdir, "pytest-")`.
6. `find_prefixed` (`_pytest/pathlib.py:172-177`) faz **`os.scandir(rootdir)`** na
   linha **175** — e é aí que a exceção nasce.

O `mode=0o700` aparece três vezes no módulo (`mktemp` nos dois ramos, em `:139` e
`:141`, e no `getbasetemp`, em `:168` e `:218`). A diferença que importa: **o ramo do
`mktemp` nunca chega a rodar**, porque o passo 3 falha antes. Quem impede os 15 testes
de executarem é a **listagem** do diretório-base, não a criação do diretório do teste.

### 2.2 O que a medição mostra

O traceback cru, capturado com `.venv/Scripts/python.exe -m pytest
tests/test_upload_seguranca.py -q --tb=long -rE`, termina assim:

```text
kwargs = {'request': <SubRequest 'tmp_path' for <Function test_existe_teto_de_tamanho_de_requisicao>>,
          'tmp_path_factory': TempPathFactory(... _basetemp=None ...)}
>       path = _mk_tmp(request, tmp_path_factory)
.venv\Lib\site-packages\_pytest\tmpdir.py:300:
.venv\Lib\site-packages\_pytest\tmpdir.py:287:
.venv\Lib\site-packages\_pytest\tmpdir.py:136:
.venv\Lib\site-packages\_pytest\tmpdir.py:117:
E       PermissionError: [WinError 5] Acesso negado:
        'C:\Users\venda\AppData\Local\Temp\dsh-FL0MLw\pytest-of-Adriano Santos'
.venv\Lib\site-packages\_pytest\pathlib.py:175: PermissionError
```

O caminho nomeado pelo erro é o **diretório-base**, exatamente o do passo 4 — e a
linha apontada é o `os.scandir` do passo 6. A leitura do código e a medição concordam.

Isolando o modo, numa sonda que não toca no projeto:

```text
os.mkdir(p, 0o700)  -> NAO LISTAVEL: PermissionError(13, 'Acesso negado')
                       NAO GRAVAVEL: PermissionError(13, 'Permission denied')
                       NAO REMOVIDO:  PermissionError(13, 'Acesso negado')
os.makedirs(p)      -> LISTAVEL ([]) | GRAVAVEL | REMOVIDO
```

### 2.3 Conclusão de P1

🟢 **Medido:** os 15 erros são o `os.scandir` sobre um diretório-base criado com
`0o700`, e um diretório `0o700` não é listável, gravável nem removível nesta
combinação Windows + Python 3.14. A causa registrada na evidência da feature 006
("o `tmp_path_factory` cria o seu diretório-base com `mode=0o700`") está **correta**;
o que esta investigação acrescenta é **qual passo** dela falha, e isso muda a correção:
não basta criar o diretório do teste em outro modo, porque o passo que falha é anterior.

🟡 **Inferido da leitura, não medido:** na primeira execução de uma sessão nova o
mesmo defeito acontece, porque `rootdir.mkdir(mode=0o700)` cria o diretório e a
listagem vem na linha seguinte. Não foi possível medir esse caso isolado porque a
primeira execução de uma sessão é justamente a que cria o diretório — depois dele
existir, toda execução seguinte falha pelo mesmo motivo e na mesma linha.

## 3. P2 — a correção pode viver inteiramente em `tests/conftest.py`

### 3.1 A restrição de escopo

`.reversa/reversa-config.json` libera a escrita em `tests/**`, `src/**`,
`README.md`, `pyrefly.toml`, `.vscode/**`, `requirements.txt`,
`.markdownlint-cli2.jsonc` e `analisador-genealogico/**`. **`pytest.ini` e
`.gitignore` não estão na lista.** As duas consequências:

- A correção **não** pode ser uma opção de ini. Isso já era sabido pela resposta da
  sessão de esclarecimento, e a investigação confirma que não é necessária.
- Não há como acrescentar `tests/.tmp/` ao `.gitignore` por esta feature. A remoção
  correta do diretório (§3.3) passa a ser a única rede contra resíduo, e o roadmap
  declara isso como consequência em vez de escondê-la.

### 3.2 Onde exatamente a correção entra, e por que ela cobre a suíte inteira

Um fixture declarado em `conftest.py` **substitui** o fixture de mesmo nome de qualquer
plugin. `tmp_path` é um fixture de plugin (`_pytest.tmpdir`), então declará-lo no
`conftest.py` é uma substituição, não uma redefinição ambígua — e vale para **toda** a
suíte, não só para `tests/test_upload_seguranca.py`.

Como isso foi verificado antes de virar decisão: a sonda foi injetada como **plugin**
(`-p`), que tem precedência **menor** que a de um `conftest.py`. Se um plugin já
substitui o `tmp_path` do pytest, um `conftest.py` substitui com folga. Resultado cru
da sonda, com um único arquivo de entrada:

```text
$ .venv\Scripts\python.exe -m pytest tests/test_upload_seguranca.py -q --tb=line -p _probe007_plugin_tmp
....................................                                     [100%]
36 passed in 7.80s
```

E na suíte inteira:

```text
$ .venv\Scripts\python.exe -m pytest tests -q --tb=line -p _probe007_plugin_tmp
246 passed in 14.64s
```

### 3.3 A segunda armadilha, também medida

A primeira versão da sonda limitava-se a criar e remover o diretório. Resultado:

```text
246 passed in 14.64s
resíduo em _probe007_tmp: 30 entradas
```

**30 diretórios vazios** ao fim de duas execuções — exatamente 15 por execução, que é o
número de testes que usam `app_cliente`. A causa está em `tests/test_upload_seguranca.py:119`:
o fixture faz `monkeypatch.chdir(tmp_path)`, e o pytest desmonta o `tmp_path` **antes**
de o `monkeypatch` desfazer o `chdir`. O `rmtree` do teardown roda com o diretório
corrente **dentro** do diretório a remover; o Windows recusa, e o
`ignore_errors=True` engole a recusa em silêncio.

Os 30 diretórios foram removidos com `Remove-Item -Recurse -Force`, **sem privilégio
nenhum** — 30 de 30. Isso é importante: eles **não** são "diretórios presos" como os
13 do inventário, que exigem `takeown`/`icacls` em shell elevado. São resíduo comum.

Com a saída de CWD no `finally`, remedido:

```text
246 passed in 11.74s
resíduo: raiz removida (zero resíduo)
```

### 3.4 Alternativas avaliadas para P2

| Alternativa | Por que foi descartada |
|---|---|
| `--basetemp=<dir>` | **Medido na feature 006 e reconfirmado pela documentação:** o pytest apaga e recria o diretório dado com `0o700` antes de rodar. Não ajuda |
| Opção em `pytest.ini` | O arquivo está fora de `allowedPaths`; e nenhuma opção de ini muda o modo de criação dos diretórios |
| Substituir `tmp_path_factory` por um proxy que reimplemente `mktemp` | Funciona, mas duplica interno do pytest (dois ramos de `mktemp`, mais `getbasetemp`, mais a política de retenção), fica frágil a upgrade, e não tem ganho sobre substituir `tmp_path`: nenhum teste do repositório pede `tmp_path_factory` (varredura: só `tmp_path`, em um arquivo) |
| `monkeypatch` do modo em `_pytest.pathlib.make_numbered_dir` | Acopla o projeto a nome interno de biblioteca, e o `getbasetemp` tem caminho próprio que não passaria por ali |
| Corrigir apenas o fixture `app_cliente` dentro de `tests/test_upload_seguranca.py` | Deixa o defeito de pé para todo teste futuro, que é o que a resposta da sessão de esclarecimento recusa explicitamente |
| Ancorar a raiz temporária no temp do sistema | **Medido: funciona** no modo padrão (`os.makedirs` no temp da sessão → listável, gravável, removível). Descartado por outro motivo: criaria uma **segunda** raiz temporária no projeto, porque `pasta_temporaria` (feature 006, entregue) usa `tests/.tmp/`, e unificar as duas exigiria mexer no fixture de uma feature já entregue sem ganho |
| Criar `tests/.tmp/.gitignore` | O arquivo é versionado e impede a própria raiz de ser removida quando vazia — criaria o resíduo que existiria para evitar |

### 3.5 Conclusão de P2

🟢 Declarar o fixture `tmp_path` em `tests/conftest.py`, criando o diretório com
`os.makedirs` no modo padrão sob a raiz `tests/.tmp/` que `pasta_temporaria` já usa, e
sair do diretório antes de removê-lo. Cobre a suíte inteira, não depende de estado da
máquina, não exige variável de ambiente nem `--basetemp`, e não toca `pytest.ini`.

⚠️ Uma consequência que o roadmap declara: o `tmp_path` da suíte deixa de ficar sob o
temporário do sistema. Quem depurar procurando o diretório em `%TEMP%` não vai achá-lo
em `tests/.tmp/`.

## 4. P3 — a costura do dono

### 4.1 O que já existe, medido no código

| Ponto | Estado hoje | Arquivo |
|---|---|---|
| `ArmazenamentoDeArquivos.guardar(conteudo, nome_original, tipo)` | sem dono | `src/ports/__init__.py:45` |
| `ArmazenamentoDeArquivos.resolver(referencia)` | sem dono | `src/ports/__init__.py:63` |
| `RepositorioDeArvores.guardar/obter` | **com** dono obrigatório | `src/ports/__init__.py:109`, `:113` |
| `CarregadorDeArvores.carregar(referencia)` | sem dono; **um** método | `src/ports/__init__.py:83` |
| `upload_gedcom(conteudo, nome_original, dono, armazenamento, carregador)` | **já recebe** o dono e não o repassa | `src/application/upload_gedcom.py:44`, `:59` |
| `DONO_DO_PROCESSO = "unico"` | já existe, único, em `src/app.py:45` | `src/app.py` |
| Chamadas de produção a `guardar` | duas: GEDCOM (`upload_gedcom.py:59`) e CSV (`app.py:193`) | — |
| Chamada de produção a `resolver` | uma: dentro de `CarregadorDeArvoresGedcom.carregar` (`adaptadores.py:92`) | — |

### 4.2 A origem da exigência

O `cutover_plan.md:33` exige que a **Onda 3** prove isolamento por usuário com teste
negativo — usuário A recebe `404` ao alcançar recurso de B, e não `403`. O adendo
vigente da 006 registra que o dono já é parâmetro obrigatório do
`RepositorioDeArvores` exatamente para que a Onda 3 não precise reabrir assinatura, e
que **nenhum** comportamento de isolamento existe hoje (`RN-06`). A assimetria que esta
feature fecha é a mesma dívida, vista do outro lado: o port de armazenamento de
**arquivo** — o que grava o GEDCOM e o CSV — ficou sem o parâmetro.

### 4.3 A decisão que a investigação teve de tomar

A chamada de `resolver` acontece **dentro do adaptador do carregador**, que hoje não
recebe dono nenhum. Duas formas de resolver:

| Opção | Argumento a favor | Argumento contra |
|---|---|---|
| Dono **por chamada**: `carregar(referencia, dono)` | O fluxo do dono fica idêntico ao do `guardar`: sai da borda e chega à porta, sem escala intermediária | Muda a assinatura de um método que a `D-02` da feature 006 congelou |
| Dono na **construção** do adaptador | Não muda a assinatura do método | Os adaptadores são **singletons de processo**, montados uma vez no import (`_ARMAZENAMENTO` e `_CARREGADOR`, `src/app.py:106-107`). Congelar identidade ali é exatamente o que a Onda 3 teria de desfazer — e o custo de reabrir a montagem é o custo que esta feature existe para não pagar |

🟢 Escolhido: **por chamada**. A condição declarada da `D-02` da 006 era a **contagem
de métodos** ("um único método, e essa é a condição"), e ela continua em um; o que muda
é a forma do parâmetro. O roadmap registra essa leitura explicitamente para que a
decisão não seja lida como violada — nem reaberta por engano.

### 4.4 Por que o dono não entra na chave nem no caminho

`_reversa_sdd/domain.md#3.5` registra que **é a chave de conteúdo que faz o papel de
identificador de sessão** no legado, e que não existe sessão nem dono. Usar o dono no
caminho ou na chave seria mudança de comportamento observável: dois envios do mesmo
conteúdo por donos diferentes deixariam de encontrar o mesmo arquivo. Isso quebraria a
paridade do armazenamento e violaria o Princípio II, então é **não-objetivo** desta
feature, e não efeito colateral aceito.

## 5. Padrões aplicáveis

| Padrão | Como aparece aqui |
|---|---|
| **Branch by Abstraction** | É o padrão que a Onda 2 usou e que esta feature continua: a porta existe com a forma final antes de a implementação final existir. O dono entra na assinatura **antes** de haver isolamento, pelo mesmo motivo que a porta entrou antes de haver persistência |
| **Seam (costura)** | O dono é uma costura declarada: ponto de extensão sem comportamento. O projeto já usa esse vocabulário no comentário de `DONO_DO_PROCESSO` e no `OBS-17` da 006 |
| **Instrumento versus produto** | A distinção que esta feature tem de manter explícita: ativar 15 testes muda o **relatório**, não o comportamento. Só é honesto afirmar isso porque foi medido — os 15 passam sem tocar em uma linha de produto |
| **Prova por forma de contrato** | Precedente interno: o `T028` da feature 006 prova que `RepositorioDeArvores` exige o dono usando `inspect.signature` e `bind`, **sem implementação**. O `RF-05` desta feature repete o padrão para `ArmazenamentoDeArquivos` |
| **Medir antes de concluir** | Prática consolidada nas features 005 e 006, e é o que esta investigação faz: nenhuma das três conclusões acima é afirmação sem número ao lado |

## 6. Fontes externas

- [How to use temporary directories and files in tests — pytest (stable)](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
  — confirma o template `{temproot}/pytest-of-{user}/pytest-{num}/{testname}/`, que é
  exatamente o caminho nomeado pelo `PermissionError`, e confirma que `--basetemp` é
  **limpo antes de cada execução**, o que explica por que ele não ajuda.
- [Windows sandbox blocks pytest-xdist temp dirs created with Python 3.14/pytest 0o700 permissions — openai/codex #19791](https://github.com/openai/codex/issues/19791)
  — relato independente do mesmo par Python 3.14 + `0o700` em Windows.
- [Bug Report: `tempfile.mkdtemp` (mode 0o700) em Windows cria diretório com descritor
  de segurança explícito, descarta a herança do pai e "se tranca" sob token restrito —
  `pytest tmp_path` deixa de funcionar — deepseek-ai/deepseek-harness #463](https://github.com/deepseek-ai/deepseek-harness/discussions/463)
  — é o relato que nomeia o **mecanismo**: descritor de segurança explícito com a
  herança do diretório pai descartada. Explica o fato que a evidência da 006 já tinha
  medido e que parecia implausível — "nem pelo dono". ⚠️ Lido como **relato
  corroborante**, não como medição: a prova local é a sonda da §2.2, que produziu o
  mesmo resultado sem depender de fonte externa.

## 7. O que ficou fora desta investigação

1. **Remover os 13 diretórios presos.** A resposta da sessão de esclarecimento os
   exclui do escopo: exigem shell elevado e são resíduo de execução, não defeito do
   produto. Continuam apenas documentados.
2. **Consertar o `0o700` na origem** — no Python ou no pytest. Não é escopo do projeto,
   e esta feature não toca biblioteca instalada.
3. **Isolamento por dono.** É a Onda 3. A `RN-06` proíbe que qualquer entrega desta
   feature seja citada como tendo implementado isolamento, e a dívida #4 continua aberta.
4. **A corrida entre requisições concorrentes (dívida #3).** Também não é desta feature;
   o que ela faz é **nomear** a dívida no comentário da constante de dono, para que a
   costura não seja lida como conserto.
5. **O `RepositorioDeArvores`.** Continua declarado, sem implementação e sem consumidor.
   Esta feature prepara a mesma porta de armazenamento, não a persistência.
6. **Um único `dono` por processo continua sendo o modelo.** Não há sessão, login nem
   identidade de usuário no legado (`_reversa_sdd/permissions.md`, `P-01` a `P-05`), e
   esta feature não introduz nenhuma.
