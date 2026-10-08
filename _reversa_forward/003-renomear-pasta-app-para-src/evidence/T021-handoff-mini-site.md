# Handoff: `T021` — regenerar o mini-site de documentação

> Origem: sessão do ciclo forward que entregou e convergiu a feature **008** e depois retomou a
> **003** (`/reversa-resume`).
> Destino: sessão dedicada à **Onda 3**.
> Data: `2026-10-08`.
> Motivo do handoff: a `T021` **não é trabalho de codificação**. Ela pertence ao pipeline de
> documentação, e este relatório existe para que a outra sessão não repita a tentativa.

## 1. A tarefa, na letra do `actions.md`

| Campo | Valor |
| --- | --- |
| ID | `T021` |
| Descrição | Regenerar o mini-site de documentação para refletir a árvore nova |
| Alvo | `_reversa_docs/` |
| Dependência | `T020` — já concluída |
| Confiança declarada | 🟡 |
| Status | `[ ]` — **única ação aberta da feature** |

Feature: `_reversa_forward/003-renomear-pasta-app-para-src` (`003`), que renomeou a raiz de
código de `analisador-genealogico/` para `src/`.

## 2. Estado do projeto no momento deste handoff

- `.reversa/active-requirements.json` aponta para a **003**, com `current-stage:
  "coding-em-progresso"` e `paused-features: []`.
- A feature **003** está em **20 de 21 ações**; a aberta é a `T021`.
- A feature **008** (`008-persistencia-postgres-docker`) está **`done` e convergida**: o adendo
  `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` está **vigente**. **Não** rode
  `/reversa-sync` para ela de novo.
- Quando a **003** chegar a `done`, ela também **não** precisará de `/reversa-sync`: o adendo
  `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md` existe mas está **superado pela
  re-extração de 2026-10-05** — o delta dela já foi absorvido.

## 3. Por que a `T021` travou duas vezes

Duas rodadas de `/reversa-coding` registraram `blocked` com a mesma conclusão, e a decisão
explícita foi **manter `[ ]` em vez de simular conclusão**. Registros em
`_reversa_forward/003-renomear-pasta-app-para-src/progress.jsonl`:

| Data | Registro |
| --- | --- |
| `2026-10-03T18:55:47Z` | "rodada 2 de reversa-coding: zero acoes de codigo a executar. T021 e regeneracao do mini-site e pertence ao pipeline de documentacao, nao ao ciclo de codificacao" |
| `2026-10-07T15:20:00Z` | "rodada 3 de reversa-coding: zero acoes de codigo a executar, resultado identico ao da rodada 2" |

⚠️ **Um quarto `/reversa-coding` produziria o terceiro registro idêntico.** Não é o veículo certo.

## 4. O que já foi medido — não precisa refazer

Tudo abaixo foi verificado em **2026-10-08**, por leitura direta do repositório.

**4.1. A premissa literal da `T021` já foi cumprida, por outro caminho.** O mini-site foi
**regenerado por inteiro em 2026-10-06**, e `_reversa_docs/.state.json` declara o motivo:

> "O mini-site havia sido gerado em 2026-10-01 e descrevia o código anterior ao refactor que
> achatou `analisador-genealogico/reconstructed/` para `src/`, e o SDD anterior à re-extração
> de 2026-10-05. Todos os caminhos de módulo, as contagens, as métricas e as 3 features estavam
> defasados."

E o resultado confirma: `_reversa_docs/assets/data/modules.json` mapeia `src/core/`,
`src/parsers/`, `src/reporting/`, `src/utils/`, `src/templates/` e `tests/`, com **zero**
ocorrências de `reconstructed`.

**4.2. O site está defasado, mas por outro motivo.** Ele é de **2026-10-06**, e duas features
vieram depois:

| Feature | Quando | O que o site não conhece |
| --- | --- | --- |
| `006-fronteira-aplicacao-ports` | adendo de **2026-10-07** | `src/application/` e `src/ports/` |
| `008-persistencia-postgres-docker` | **2026-10-08** | a persistência, `adaptadores.py`, `docker-compose.yml`, `init.sql` |

Medido em `_reversa_docs/` (29 arquivos varridos): `ports` → **0** ocorrências; `adaptadores`
→ **0**; `psycopg2` → **0**; `docker-compose` → **0**.

**4.3. As citações de `analisador-genealogico/` que sobraram NÃO são pendência.** São três, e
nenhuma é caminho atual:

- `analisador-genealogico` como **nome do projeto** (`"project"` em `timeline.html`,
  `timeline.json` e `assets/js/data.js`);
- duas descrições de **eventos passados** — "raiz de código de `analisador-genealogico/` para
  `src/`", e "escavação do módulo `analisador-genealogico`".

**Reescrevê-las falsificaria o registro histórico.** O mesmo vale para as quatro menções a
`reconstructed`, todas em arquivos históricos (`timeline.html`, `assets/data/timeline.json`,
`assets/js/data.js`, `.state.json`).

## 5. A armadilha em que eu mesmo caí — leia antes de varrer

Minha primeira varredura contou "11 arquivos citam `application/`" e eu quase registrei isso
como o site conhecendo `src/application/`. **Era falso positivo do meu próprio grep:** os 11 são
`<script type="application/json">`, o JSON embutido de cada página.

**Não use `application/` como sinal de que o site conhece o pacote.** Verifique por
`assets/data/modules.json`, que é a fonte estrutural.

## 6. As duas saídas honestas — a escolha é do operador

**(a) Rodar `/reversa-docs` — recomendada.** Regenera o mini-site, que passa a conhecer
`src/application/`, `src/ports/` e a persistência. Ao fim, a `T021` fecha com prova em disco em
vez de ficar em `[ ]`. É a única saída que produz trabalho novo e útil.

**(b) Fechar a `T021` como satisfeita por evidência.** Aceitar a regeneração de 2026-10-06 como
cumprimento do que ela pede literalmente ("refletir a árvore nova") — com o registro de que o
site continua ignorando as features 006 e 008. Isso exige editar
`_reversa_forward/003-renomear-pasta-app-para-src/actions.md` (trocar `[ ]` por `[X]`) e
justificar no `progress.jsonl`. **É ato deliberado, não atalho.**

## 7. Ferramental e fatos de ambiente que importam

- **Os cinco skills de documentação estão instalados:** `reversa-docs` (orquestrador) e os
  quatro que ele dirige — `reversa-docs-mapper`, `reversa-docs-analyst`,
  `reversa-docs-storyteller`, `reversa-docs-publisher`.
- **`templates/documentation/` NÃO existe neste repositório.** O `.state.json` do site registra
  exatamente isso: sem `viewer.html`, `.tpl`, `sidebar.js`, `extract_modules.py`,
  `extract_deps.py`, `convert_chronicle.py` nem `convert_soul.py`. A execução de 2026-10-06 foi
  feita com **scripts determinísticos próprios**, guardados em `.reversa/`: `_docs_extract_modules.py`,
  `_docs_extract_metrics.py`, `_docs_extract_features.py`, `_docs_nav.py`, `_docs_build_datajs.py`,
  `_docs_inject_pages.py`, `_docs_smoke_test.py`, `_docs_render_check.js`, `_docs_state.py`,
  `_docs_finalize.py`, `_docs_fix_whatchanged.py`, `_docs_inline_hero.py`, `_docs_seal.py`,
  `_docs_telemetry.py`, `_docs_step8_check.py` (16 arquivos). **Eles são o caminho de trabalho
  comprovado** — se o skill padrão não fechar, use-os.
- **`_reversa_docs/` é versionado pelo git** (31 arquivos rastreados) e **não** está no
  `.gitignore`. Mudanças aparecem em `git status` e o commit é decisão do operador.
- **Não existe backup do site no disco agora.** O `.state.json` cita
  `.backup-20261006-004310/` e `.backup-20261006-022411/`, mas as pastas **não estão lá** —
  apenas `assets/` e `features/`. **Faça backup antes de regenerar.**
- **`assets/vendor/` está populado** com as 9 libs (`three.min.js`, `OrbitControls.js`,
  `d3.v7.min.js`, `highcharts.js` e os 4 módulos). O passo de bundle vendor pode ser pulado
  enquanto os arquivos estiverem no disco.
- **Ações de usuário já registradas no site e que não devem ser revertidas:** o selo foi
  regerado na variante **dark** por contraste (`reversa-selo-generativo`), o selo do hero é
  **SVG inline** (não `<img>`), e o `data.js` tem **11 chaves** de dados. Leia
  `_reversa_docs/.state.json` antes de mexer.
- **Verificações que o pipeline de 2026-10-06 usou, e que valem repetir:**
  `node .reversa/_docs_render_check.js` (carrega o `data.js` num `window` falso e confere o
  inventário, os 10 itens do nav e a sintaxe do script inline das 10 páginas) e
  `.venv/Scripts/python.exe .reversa/_docs_smoke_test.py` (sobe `http.server` efêmero, faz GET
  nas 10 páginas e nos 29 assets, e valida links relativos contra o disco).

## 8. Regras que não podem ser violadas

1. **Nunca apague, modifique ou sobrescreva arquivos pré-existentes do projeto** fora dos
   caminhos liberados em `.reversa/reversa-config.json`. `_reversa_docs/` é pasta própria do
   Reversa e é sempre gravável; o resto depende de `allowedPaths`.
2. **Nunca edite `.reversa/reversa-config.json`** — é ato exclusivo do usuário.
3. **Não reescreva o histórico do mini-site.** As citações de `analisador-genealogico/` e de
   `reconstructed/` são registro de eventos, não caminho atual.
4. **Não rode `/reversa-coding` para a `T021`.** Vai travar pela terceira vez.
5. **Não rode `/reversa-sync`** para a 003 nem para a 008 — as duas já estão resolvidas nesse
   aspecto.
6. O `.venv/` do host **não** tem `psycopg2` e o `pip` é inutilizável nele (`Errno 13`, `0o700`);
   a suíte roda **sem** `DATABASE_URL`. Nada disso afeta o mini-site, mas explica por que a
   suíte reporta `8 skipped`.

## 9. Verificação rápida, para colar

```powershell
# 1. Em que estágio esta a 003?
Select-String -Path "_reversa_forward\003-renomear-pasta-app-para-src\actions.md" -Pattern '\| `\[ \]` \|$'

# 2. O site conhece a arvore nova?
Select-String -Path "_reversa_docs\assets\data\modules.json" -Pattern 'src/core/|reconstructed'

# 3. O site conhece ports/ e a persistencia?
Get-ChildItem "_reversa_docs" -Recurse -File -Include *.html,*.js,*.json |
  Select-String -Pattern 'ports|adaptadores|psycopg2' -List | ForEach-Object { $_.Path }
```

## 10. A pergunta a responder nesta outra sessão

> A `T021` deve ser cumprida com `/reversa-docs` (opção **a**), ou encerrada por evidência
> aceitando a regeneração de 2026-10-06 (opção **b**)?

Se a resposta for **(a)**, o escopo é o mini-site inteiro — 10 páginas — e o resultado natural é
o site passando a refletir as features **006** e **008**, não apenas a renomeação da **003**.

## Fontes

- `_reversa_forward/003-renomear-pasta-app-para-src/actions.md` (`T021`) e `progress.jsonl`
- `.reversa/active-requirements.json`
- `_reversa_docs/.state.json` e `.config.json`
- `_reversa_docs/assets/data/modules.json`
- `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md` (superado) e
  `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` (vigente)
