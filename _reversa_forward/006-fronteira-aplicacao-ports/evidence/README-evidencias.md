# Evidências da execução do `actions.md` — feature `006-fronteira-aplicacao-ports`

> Rodada de `/reversa-coding`, 2026-10-07.
> Este diretório guarda as **medições**, não as conclusões. As conclusões ficam em
> `../legacy-impact.md` e `../regression-watch.md`; os avisos de execução ficam em
> `../actions.md` § "Notas de execução".

## 1. Os quatro instrumentos, e o que cada um responde

| Instrumento | Comando | Pergunta que responde |
|---|---|---|
| Suíte | `python -m pytest -q` | Algum teste regrediu? Algum teste sumiu? |
| Paridade diferencial | `python _reversa_sdd/parity/harness.py` | O comportamento do núcleo continua idêntico ao oráculo congelado? |
| Sonda de mensagens | `python evidence/probe_mensagens.py {antes,depois}` + `python evidence/_comparar.py` | O **texto da tela** e o **modo de renderização** continuam idênticos, caso a caso? |
| Varredura de forma | `python evidence/_t020_varredura.py` | `index()` deixou de conter passo de domínio? |

O terceiro existe porque a suíte **não** exercita a rota nesta máquina (ver §2): sem
ele, a reescrita do `app.py` ficaria sem medição de comportamento observável.

## 2. Dois defeitos de ambiente, ambos medidos, nenhum do projeto

### 2.1 `os.mkdir(caminho, 0o700)` cria diretório inutilizável nesta máquina

Medido com um diretório novo, fora de qualquer dúvida:

```
os.mkdir default      -> LISTAVEL
os.mkdir 0o700        -> NEGADO   (PermissionError ao listar)
Path.mkdir 0o700      -> NEGADO
Path.mkdir 0o777      -> LISTAVEL
```

O diretório criado com `0o700` não pode ser **listado**, **escrito**, **apagado**,
nem ter a ACL redefinida — nem pelo dono (`icacls /reset`, `takeown`, `rd /s /q` e
`os.rmdir` falham; `Get-Acl` responde "operação não autorizada"). É a combinação
Windows + Python 3.14 desta estação.

**É a causa dos 15 erros da linha de base.** O `tmp_path_factory` do pytest cria o
seu diretório-base com `mode=0o700` (`_pytest/tmpdir.py`), então os 15 testes de
`tests/test_upload_seguranca.py` que usam `app_cliente` morrem no *setup* com
`PermissionError: [WinError 5]` — o mesmo número e os mesmos 15 nomes de antes da
feature. Nenhum deles é regressão de código, e nenhum é alcançável por esta
máquina.

**Consequências para esta execução:**

1. `--basetemp=<qualquer coisa>` **não** ajuda: o pytest apaga e recria o diretório
   dado com `mode=0o700`. Tentado; o erro se repetiu.
2. Teste novo **não** pode usar `tmp_path`, `tempfile.mkdtemp` nem
   `TemporaryDirectory`. `tests/conftest.py` fornece `pasta_temporaria` e
   `cliente_de_upload`, que criam o diretório com o modo padrão.
3. O diretório temporário do sistema também não serve para escrita a partir do
   processo: `tempfile.mkdtemp` cria, e a escrita dentro dele é negada. Por isso as
   sondas trabalham em `evidence/_tmp_probe/`, dentro do workspace.

### 2.2 Diretórios presos: um problema **recorrente do projeto**, não desta rodada

Uma varredura do workspace que tenta listar cada diretório encontrou **13
diretórios inacessíveis**. Oito deles **já existiam** antes desta feature:

```
.pytest-tmp\final                     <- pre-existente
.pytest-tmp\pytest-of-Adriano Santos  <- pre-existente
.pytest-tmp\refactor-run              <- pre-existente
.pytest-tmp\run                       <- pre-existente
.pytest-tmp\run1                      <- pre-existente
.pytest-tmp\run2                      <- pre-existente
.pytest-tmp\verify                    <- pre-existente
_reversa_refactor\.pytest-baseline    <- pre-existente
_probe_acl2\sete                      <- desta rodada (experimento de ACL)
_probe_acl\os_mkdir_700               <- desta rodada (experimento de ACL)
_probe_acl\path_mkdir_700             <- desta rodada (experimento de ACL)
src\uploads\_pytest                   <- desta rodada (tentativa de --basetemp)
tests\_basetemp_probe                 <- desta rodada (tentativa de --basetemp)
```

Os oito primeiros explicam duas coisas que já estavam no repositório antes desta
feature: a entrada `.pytest-tmp/` no `.gitignore` e a anotação de "15 erros de
ambiente" na linha de base. **A armadilha é conhecida e recorrente neste
projeto** — a rodada atual caiu nela três vezes, e as três tentativas foram
registradas aqui em vez de escondidas.

**A remoção exige shell elevado.** Num PowerShell como Administrador, o comando
abaixo resolve os treze de uma vez:

```powershell
$presos = @(
  '.pytest-tmp\final', '.pytest-tmp\pytest-of-Adriano Santos', '.pytest-tmp\refactor-run',
  '.pytest-tmp\run', '.pytest-tmp\run1', '.pytest-tmp\run2', '.pytest-tmp\verify',
  '_reversa_refactor\.pytest-baseline', '_probe_acl', '_probe_acl2',
  'src\uploads\_pytest', 'tests\_basetemp_probe'
)
foreach ($p in $presos) {
  takeown /f $p /r /a 2>$null
  icacls $p /reset /t 2>$null
  rd /s /q $p 2>$null
}
```

`tests/conftest.py` tem `collect_ignore = ["_basetemp_probe"]` para que a coleta
da suíte não aborte enquanto o diretório estiver lá. Removido o diretório, a linha
`collect_ignore` perde a razão de existir — mas **não** as fixtures temporárias do
mesmo arquivo (ver §2.1).

## 3. Linha de base e resultado

| Medição | Antes (feature 005) | Depois da integração |
|---|---|---|
| Suíte | `178 passed, 15 errors` | ver `T023-medicao-bloco-3.md` |
| Paridade | `PARIDADE 100%`, exit 0 | `PARIDADE 100%`, exit 0 |
| Mensagens de tela (19 casos) | `mensagens_antes.json` | `mensagens_depois.json` — **zero divergência** |
| Passos de domínio em `index()` | presente | `T020-varredura.txt` — APROVADO |

A comparação dos 19 casos inclui **status HTTP**, **classe do alerta**
(`success`/`danger`) e **texto**, porque comparar só o texto deixaria passar
justamente a mudança que a decisão `D-11` existia para impedir: o modo de
renderização trocando de alerta de erro para cartão de resultado.

## 4. Como reproduzir cada medição

```powershell
# suíte (a linha de base tem 15 erros de ambiente; ver §2.1)
python -m pytest -q

# paridade contra o oráculo congelado
python _reversa_sdd/parity/harness.py

# mensagens: o lado "antes" sai do app.py versionado em `_antes/app.py`,
# que e o `git show HEAD:src/app.py` (o codigo imediatamente anterior a extracao)
$env:PROBE_APP = '_reversa_forward/006-fronteira-aplicacao-ports/evidence/_antes/app.py'
python _reversa_forward/006-fronteira-aplicacao-ports/evidence/probe_mensagens.py antes
Remove-Item Env:\PROBE_APP
python _reversa_forward/006-fronteira-aplicacao-ports/evidence/probe_mensagens.py depois
python _reversa_forward/006-fronteira-aplicacao-ports/evidence/_comparar.py

# varredura de forma
python _reversa_forward/006-fronteira-aplicacao-ports/evidence/_t020_varredura.py
```

## 5. Arquivos deste diretório

| Arquivo | O que é |
|---|---|
| `probe_mensagens.py` | A sonda. Roda os 19 casos contra o `app.py` atual ou contra o de `_antes/` |
| `_comparar.py` | Compara as duas saídas caso a caso; sai 1 em qualquer divergência |
| `mensagens_antes.json` | Saída do lado anterior à extração |
| `mensagens_depois.json` | Saída do lado atual |
| `_t020_varredura.py` | Varredura por AST de que `index()` não chama passo de domínio |
| `T020-varredura.txt` | Saída da varredura |
| `T021-medicao-bloco-1.md` | Medição do bloco `upload_gedcom` |
| `T022-medicao-bloco-2.md` | Medição do bloco `path_search` |
| `T023-medicao-bloco-3.md` | Medição do bloco `dna_analysis` e o resultado final |
| `T025-verificacao-manual.md` | Verificação de ponta a ponta no `waitress`, e os dois achados do `onboarding.md` |
| `_antes/app.py` | Cópia do `app.py` imediatamente anterior à extração (`git show HEAD:src/app.py`) |
| `_tmp_e2e/out/*.html` | Saídas cruas dos `curl` da verificação manual, uma por passo |

## 6. Desvios declarados nas medições

1. **Os três blocos foram integrados num só passo (`T016` a `T019`), e a medição
   foi feita uma vez ao fim, não ao fim de cada bloco.** A `D-09` pede uma medição
   por bloco. Duas razões, as duas verificáveis: (a) as quatro ações editam o
   MESMO arquivo (`src/app.py`), e o próprio `actions.md` diz que elas são
   "sequenciais de fato — cinco ações, um arquivo"; (b) medir **antes** da
   integração teria sido vazio, porque os casos de uso são aditivos — nada os
   chamava, e a medição daria a linha de base por construção. O que a `D-09`
   protege — atribuir uma regressão ao bloco que a introduziu — é atendido aqui por
   um instrumento mais fino: a sonda nomeia o caso (`dna_csv_sem_colunas`,
   `path_indireto`, ...), e a divergência apareceria com nome próprio. As três
   medições de bloco em `T021`–`T023` são **recortes do mesmo ponto de medição**,
   por conjunto de casos, e não três instantes distintos.
2. **O `T015` cresceu de três para quatro consumidores.** A `D-06` afirma que o
   `harness.py` "já consome `carregar_arvore`" e que só sairia uma menção textual.
   **A afirmação é falsa e foi medida:** o coletor de candidatos chamava
   `GP.load_gedcom_and_build_graph(GED)` de fato (`harness.py`, dentro da string
   `CANDIDATE_COLLECTOR`), na linha imediatamente anterior a
   `GP.carregar_arvore(GED)` — parse duplo por fixture. A remoção da casca quebrava
   a paridade. O coletor do candidato passou a derivar `names` da árvore, com a
   mesma fórmula da casca; o coletor do **oráculo** não foi tocado, porque o
   oráculo é congelado. Paridade remedida depois da mudança: 100%, exit 0.
