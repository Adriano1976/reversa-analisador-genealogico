# T004 — linha de base do Bloco 0

> Rodada de `/reversa-coding`, 2026-10-07.
> Interpretador: **oficial**, `.venv/Scripts/python.exe` (`RF-08`, `RF-10`).
> Este arquivo guarda a **medição**. A leitura dela está em `../roadmap.md` §11 e no
> `../legacy-impact.md`.

## 1. Comandos, e o resultado de cada um

```text
.venv\Scripts\python.exe -m pytest -q
    -> 249 passed in 21.67s
    -> exit code 0

.venv\Scripts\python.exe _reversa_sdd\parity\harness.py
    -> RESULTADO: PARIDADE 100% (zero divergencia)
    -> CANDIDATO coletado: 6 pessoas, 2 familias
    -> exit code 0
```

Saídas cruas: `T004-suite-bloco0.txt` e `T004-paridade-bloco0.txt`.

## 2. Contra a linha de base anterior

| Medição | Antes do Bloco 0 | **Depois do Bloco 0** |
|---|---|---|
| Suíte | `231 passed, 15 errors` | **`249 passed, 0 errors`** |
| Erros de ambiente | **15** | **0** |
| `tests/test_upload_seguranca.py` | `21 passed, 15 errors` | **`36 passed, 0 errors`** |
| Paridade diferencial | `100 %`, exit 0 | **`100 %`, exit 0** |
| Resíduo em `tests/.tmp/` | *(a pasta não existia)* | **ausente** |

A aritmética fecha, e ela importa para a leitura da `RN-04`:

```text
231 aprovados que já existiam
+15 que passaram a EXECUTAR (não são testes novos)
+ 3 do arquivo novo `tests/test_ambiente_temporario_da_suite.py`
= 249
```

**Zero teste de produto foi acrescentado, removido, desabilitado ou reescrito.** O que
mudou foi o **instrumento**, e o número novo não é comparável ao antigo por total — é
comparável por **conjunto**: nenhum aprovado virou falha.

## 3. O que o Bloco 0 tinha de provar, e provou

1. **A causa estava certa.** `getbasetemp()` criava `pytest-of-<usuário>` com `0o700` e o
   `os.scandir` de `_pytest/pathlib.py:175` falhava ao listá-lo. Com o fixture `tmp_path`
   declarado em `tests/conftest.py`, esse caminho não é percorrido e os 15 executam.
2. **A precedência do `conftest` sobre o plugin se confirmou.** Era a **única inferência**
   do plano — a medição prévia usara um plugin (`-p`), de precedência menor. Medido agora
   no artefato real: `0 errors`.
3. **O resíduo está fechado.** A saída do diretório corrente antes do `rmtree` era
   necessária: sem ela, 15 diretórios vazios sobreviviam **por execução**. Medido agora:
   `tests/.tmp/` não existe ao fim da suíte.

## 4. Uma falha, e ela era do teste novo

A primeira execução do Bloco 0 deu `1 failed, 248 passed`. A falha estava no arquivo que o
`T003` acabara de criar, e **não** no produto nem na correção do ambiente:

```text
tests\test_ambiente_temporario_da_suite.py:97:
    assert tmp_path != Path(pasta_temporaria)
E   AssertionError: ... os dois deixaram de ser diretorios independentes por teste
E   assert WindowsPath('.../tests/.tmp/240523bc0f8848af...')
       != WindowsPath('.../tests/.tmp/240523bc0f8848af...')
```

A asserção supunha dois diretórios independentes no mesmo teste. **Não são:** o pytest
**cacheia a instância do fixture** por teste, então pedir `tmp_path` e `pasta_temporaria`
no mesmo teste devolve o **mesmo** objeto — que é exatamente o que a `D-02` quis dizer com
"implementação única". Cada teste continua recebendo um diretório próprio, porque
`pasta_temporaria` é de escopo de função; o que não existe é um diretório *por nome de
fixture*.

Correção aplicada na mesma ação: a asserção passou a exigir a **igualdade** (e a raiz
única), com o motivo registrado no docstring do teste. Nenhuma asserção foi enfraquecida —
a nova versão mede mais, e mede a coisa certa. A `RF-09` não se aplica: não era falha de
produto nem de ambiente, era asserção errada de teste novo, corrigida aqui com o motivo
declarado.
