# ADR-13 — Fixar as seis dependências diretas

- **Status:** Aceito e vigente — ✅ **AMPLIADO em 2026-10-05** por decisão do usuário: o `.venv/` é o interpretador **oficial**, o pin foi realinhado a ele, e as **duas transitivas que decidem o matching** passaram a ser declaradas
- **Data da decisão:** 2026-10-04
- **Commit(s):** `db42eb7` — "chore(deps): fixa as seis dependencias diretas com versao validada"
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O `requirements.txt` **não declarava nenhuma versão**. Em um sistema cujo resultado de negócio depende de **comparação exata de números** (cM) e de **matching difuso de nomes**, isso significa que uma atualização de biblioteca pode mudar quem casa com quem e qual veredito o confronto emite, **sem uma linha de código mudar**.

## Decisão

Fixar as **seis dependências diretas** com `==`, e substituir `gunicorn` por `waitress` como servidor declarado (ADR-12).

```text
Flask==3.1.3
ged4py==0.5.2
networkx==3.6.1
pandas==3.0.3
thefuzz==0.22.1
waitress==3.0.2
```

## Evidência

- `requirements.txt` — as seis linhas acima, todas com `==`.
- `surface.json` → `pinned_versions: true` e `pinned_versions_note`: *"A lacuna anterior ('nenhuma versão declarada') está fechada."*
- A mensagem de `SystemExit` em `src/app.py:199-203` **nomeia o arquivo de dependências**, e não o pacote avulso, por causa desta decisão: instalar o pacote solto traria uma versão diferente da validada.
- `migration/.state.json` → `oracle.dependencyVersions` registra as versões contra as quais o oráculo foi validado.

## Justificativa

O `RISK-004` (divergência aritmética) e o `RISK-009` já registravam que **congelar o ambiente é pré-requisito da paridade**. Fixar as diretas é o mínimo; a transitiva que decide o matching é conhecida e está nomeada no `surface.json`.

## Consequências

- ✅ **A divergência foi ENCERRADA em 2026-10-05, por decisão sua** (`questions.md#pergunta-11`): o interpretador **oficial** é o `.venv/`. O `requirements.txt` foi realinhado às versões verificadas **dentro do `.venv`**:

  | Pacote | Pin antigo | **Pin novo** |
  | --- | --- | --- |
  | `ged4py` | 0.5.2 | **0.5.5** |
  | `networkx` | 3.6.1 | **3.7** |
  | `pandas` | 3.0.3 | **3.0.6** |
  | `Flask` · `thefuzz` · `waitress` | já coincidiam | inalterados |

- ✅ **A ADR foi além do pin das diretas, e isso é uma mudança de decisão.** O `rapidfuzz==3.14.6` e o `python-Levenshtein==0.27.5` — **transitivas do `thefuzz`** — passaram a ser **declaradas**. O motivo é o que a própria dívida registrava: o `RapidFuzz` é o **backend real do matching difuso** (`RISK-006`), e deixá-lo livre permitiria que uma instalação nova trouxesse outra versão e mudasse o resultado da análise sem uma linha de código mudar. A alternativa escolhida antes (nomear as transitivas no `surface.json` para tornar a divergência *detectável*) foi **substituída** por torná-la **impossível**.
- ✅ **Verificação:** a suíte passa **igual nos dois interpretadores** — **163 passam + 15 erros de ambiente** em cada um. A diferença de versões (incluindo `RapidFuzz` 3.14.5 vs 3.14.6) **não** alterou o comportamento coberto pelos testes.
- ⚠️ **Pendência de documentação, declarada e não corrigida:** o `README.md` da raiz descreve o fluxo pelo interpretador **global** (`pip install -r requirements.txt`, `python src/app.py`, sem ativar o venv). Com esta decisão, ele **contradiz** o pin. Não editei o README por ser documento do usuário — fica registrado para ele decidir.
- ⚠️ **Resíduo de ambiente, não dívida de código:** `gunicorn 26.0.0`, `matplotlib 3.11.1` e `pyvis 0.3.2` continuam **instalados no global**, sem constar do `requirements.txt` e sem nenhum `import` no código. Herança do estado anterior ao ADR-03.
- 🟢 **Consequência operacional assumida:** o fluxo oficial é o interpretador **global** (`pip install -r requirements.txt`, `python src/app.py`), e o `.venv` existe sem ser o ambiente documentado. Qual dos dois é o oficial **não está decidido** — ver `P-01`… `P-05` de `permissions.md` e a lacuna equivalente em `surface.json.confidence.gaps`.

## Alternativas consideradas

- **Fixar apenas as diretas e deixar a transitiva livre.** É o que foi feito, com uma diferença: o `surface.json` **nomeia** as transitivas críticas e suas versões esperadas, para que a divergência seja **detectável** em vez de silenciosa.
- **Congelar com `pip freeze` integral.** Descartada: engessaria transitivas irrelevantes e dificultaria ler o que o projeto realmente usa.
