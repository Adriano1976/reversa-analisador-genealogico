# Onboarding: validar a feature `028` pela primeira vez

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Público: pessoa que vai testar a feature depois do `/reversa-coding`
> Ambiente oficial: Windows + PowerShell + `.venv` do repositório

## 1. Antes de começar

1. Abra o PowerShell na raiz do repositório:

   ```powershell
   Set-Location 'D:\Projetos\reversa_analisador_gelealogico'
   ```

2. Confirme o interpretador oficial:

   ```powershell
   .venv\Scripts\python.exe --version
   ```

   Esperado: Python 3.14.x.

3. Confirme que você **não** está apontando para dado real. Todo teste desta feature usa
   `tests/fixtures/` sintético. Nunca use um arquivo de `src/uploads/` para testar.

## 2. Rodar os testes unitários do núcleo

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validator.py -q
```

O que deve passar:

- os três status (`VALIDADO`, `INCONCLUSIVO`, `ERRO CRONICO / QUEBRA DE LINHA`);
- cada código crítico (`GENITOR_FORA_DA_JANELA_BIOLOGICA`, `MRCA_POSTERIOR_A_DESCENDENTE`,
  `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL`, `CM_INCOMPATIVEL_COM_PROFUNDIDADE`,
  `MRCA_DOCUMENTADO_FORA_DA_JANELA`, `CONFLITO_CM_DOCUMENTAL`,
  `DOADOR_VIVO_EM_LINHA_INCOMPATIVEL`);
- os casos de borda: data ausente, data estimada, sem cobertura de cM, sem caminho, afinidade,
  múltiplos kits e precedência.

Se algum teste falhar, leia o nome do teste: ele nomeia a regra (ex.:
`test_doador_vivo_com_mrca_de_1650_e_erro_cronico`).

## 3. Rodar o teste de integração da fachada

```powershell
.venv\Scripts\python.exe -m pytest tests/test_validacao_de_arquivos.py -q
```

Esse teste monta um GEDCOM sintético com datas e um CSV sintético, grava os dois em
`tests/.tmp/` (o `tmp_path` da suíte) e chama `validar_arquivos`. Ele verifica:

- a árvore é parseada uma vez;
- cada kit gera um resultado;
- nenhum match é inventado;
- o resumo usa o pior status entre os kits;
- a ausência de evidência devolve `INCONCLUSIVO` com `SEM_EVIDENCIA`.

## 4. Rodar a suíte completa

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Referência: a suíte tem mais de mil testes e roda em menos de um minuto. O esperado é
**todos passam, 9 pulados, 0 falham** (o número de pulados é o do ambiente sem `DATABASE_URL`;
se você tiver a variável, confira a seção de persistência do README).

## 5. Smoke test manual da estimativa

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from core.validator import estimar_mrca; print(estimar_mrca(cm=200, nasc_doador=1970, mrca_do_kit=2.0, relacoes=[{'meioses': 4}], intervalo_de_geracao=25.0))"
```

Esperado: um dicionário com `ano` em torno de 1920, `geracoes` 2.0 e `metodo` `mrca_do_kit`.

Sem `mrca_do_kit`, a mesma chamada usa `scp40:mediana` e devolve `geracoes` 2.0 (mediana de
`meioses` 4 ÷ 2), com o mesmo ano.

## 6. Smoke test manual de uma comparação validada

Cole o bloco abaixo no PowerShell. Ele não lê arquivo, não usa banco e não toca na tela.

```powershell
@'
from core.validator import ComparacaoParaValidar, validar_comparacao

comparacao = ComparacaoParaValidar(
    doador={"id": "@I1@", "nome": "Doador", "nascimento": "1970"},
    match={"id": "@I2@", "nome": "Match", "nascimento": "1950"},
    documental={
        "status": "found",
        "label": "Primos de 1º grau",
        "relationship_key": "1C",
        "meioses": 4,
        "degrees": {"a_up": 2, "b_up": 2},
        "common_ancestor": {"id": "@I3@", "name": "MRCA", "birth": "1900"},
        "path": {
            "ids": ["@I1@", "@I4@", "@I3@", "@I5@", "@I2@"],
            "names": ["Doador", "Pai", "MRCA", "Mãe", "Match"],
        },
        "evidence": [
            {"parent_birth": "1900", "child_birth": "1945", "age_at_birth": 45, "plausible": True},
            {"parent_birth": "1945", "child_birth": "1970", "age_at_birth": 25, "plausible": True},
            {"parent_birth": "1900", "child_birth": "1925", "age_at_birth": 25, "plausible": True},
            {"parent_birth": "1925", "child_birth": "1950", "age_at_birth": 25, "plausible": True},
        ],
        "ambiguous_identity": False,
    },
    kit={
        "kit": "SYN-1",
        "total_cm": 200.0,
        "largest_segment_cm": 80.0,
        "mrca_generations": 2.0,
    },
    ano_referencia=2026,
    intervalo_de_geracao=25.0,
    comparacao_existente={"status": "COMPATIVEL"},
)

print(validar_comparacao(comparacao))
'@ | .venv\Scripts\python.exe -
```

Esperado: `status` **VALIDADO**, nenhum código crítico, `mrca_estimado.ano` em torno de 1920 e
`geracoes_documentais` `{doador: 2, match: 2, total: 4}`.

Para ver o caso de erro, troque `doador.nascimento` para `1985`, `common_ancestor.birth` para
`1650` e `degrees` para `{a_up: 2, b_up: 2}`. O resultado deve ser
`ERRO CRONICO / QUEBRA DE LINHA`, com `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` e
`DOADOR_VIVO_EM_LINHA_INCOMPATIVEL`.

## 7. Conferir que nada fora do escopo mudou

```powershell
git status --short
git diff --stat
```

Esperado:

- novos: `src/core/validator.py`, `src/application/validacao.py`,
  `tests/test_validator.py`, `tests/test_validacao_de_arquivos.py`,
  `tests/fixtures/arvore_com_datas.py`;
- alterado: `src/core/janela_de_vida.py` (apenas o wrapper público `data_imprecisa`);
- `src/app.py`, `src/templates/index.html`, `src/assets/app.css`, `init.sql`,
  `requirements.txt` e as tabelas do banco **não** aparecem no diff;
- `src/uploads/` não aparece no `git status` (princípio I).

## 8. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| `ModuleNotFoundError: core` | O comando não rodou da raiz ou o `src` não está no caminho | Rode da raiz; nos testes, o `sys.path` é ajustado no topo de cada arquivo; no `python -c`, use `sys.path.insert(0, 'src')` |
| `ModuleNotFoundError: pandas` / `flask` | Você usou o Python do sistema, não o `.venv` | Use `.venv\Scripts\python.exe` |
| Teste de integração não acha o GEDCOM/CSV | O teste escreve em `tests/.tmp/`; a pasta pode ter sido limpa | Rode novamente; o fixture recria o diretório |
| `PermissionError` em `tests/.tmp` | Diretório preso de execução anterior | Veja `tests/conftest.py` §4; a receita é remover o diretório preso e rodar de novo |
| `VALIDADO` não aparece no caso que você montou | Falta data em algum salto, ou a data é `ABT`/`EST` | Confira `SEM_DATA_DE_NASCIMENTO` / `DATA_ESTIMADA` no resultado; `VALIDADO` exige a linha inteira datada |
| `INCONCLUSIVO` com `AFINIDADE_NAO_BIOLOGICA` | O caminho chega ao outro ramo por casamento | É o comportamento correto; o validador não trata afinidade como consanguinidade |

## 9. Checklist de aceite manual

- [ ] `tests/test_validator.py` passa
- [ ] `tests/test_validacao_de_arquivos.py` passa
- [ ] suíte completa passa no `.venv`
- [ ] smoke test de `estimar_mrca` devolve ano, janela e método
- [ ] smoke test de `validar_comparacao` devolve `VALIDADO`
- [ ] caso do doador vivo com MRCA de 1650 devolve `ERRO CRONICO / QUEBRA DE LINHA`
- [ ] `git status` não mostra `uploads/` nem mudança em `app.py`/template/banco
- [ ] nenhum dado real foi usado
