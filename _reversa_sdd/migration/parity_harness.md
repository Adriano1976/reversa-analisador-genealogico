---
schemaVersion: 1
generatedAt: "2026-09-28T05:40:00Z"
reversa:
  version: "1.2.58"
kind: parity_harness
producedBy: orchestrator
hash: "c84e9a2200990e1ee188791d2776fed6695178d0b996ee287c679dee7b4e59aa"
---

# Parity Harness — Execução Diferencial

> **Este é o instrumento que transforma os 102 cenários de `parity_tests/` em evidência.** Ele executa o oráculo congelado e o candidato sobre as **mesmas entradas** e compara com **igualdade exata**, materializando a métrica primária do brief: *"paridade de matching ≥ 100% nos casos de teste"*.

## Como executar

```powershell
# todas as fixtures sintéticas
python _reversa_sdd\parity\harness.py

# um GEDCOM específico (sintético ou real)
python _reversa_sdd\parity\harness.py --gedcom caminho\para\arvore.ged

# árvore real grande: reduz a amostra de pares e dá mais tempo por coletor
python _reversa_sdd\parity\harness.py --gedcom Arvore.ged --pares 8 --timeout 2400

# salva as observações completas em JSON (para inspeção/regressão)
python _reversa_sdd\parity\harness.py --json observacoes

# (re)gera as fixtures
python _reversa_sdd\parity\make_fixtures.py

# limpa o resíduo gerado pelos probes (_collect_*, _obs_*, .parity-*/)
python _reversa_sdd\parity\_clean_residue.py
```

| Opção | Padrão | Para que serve |
|---|---|---|
| `--pares N` | `40` (N×N = 1.600) | Lado da amostra de pares de caminho. Reduza em árvore real grande. |
| `--timeout S` | `600` | Segundos por coletor. Ao estourar, o harness reporta **INCONCLUSIVO** — nunca "paridade OK". |

As mesmas opções existem por variável de ambiente (`PARITY_SAMPLE`, `PARITY_TIMEOUT`), porque é assim que o harness as repassa aos dois subprocessos coletores.

## Lado ORÁCULO e lado CANDIDATO

| Papel | O que é | Por quê |
|---|---|---|
| **Oráculo** | `_reversa_sdd/oracle/app_legacy_e43ca22.py` (888 linhas, sha256 `44370b23…`) | Monolito original extraído do commit `e43ca22`. Único comportamento de referência legítimo. |
| **Candidato** | `analisador-genealogico/reconstructed/` | O núcleo reconstruído. **É o candidato imediato da Onda 1** — não o `analisador/`, que ainda não existe. |

⚠️ **Nunca troque o oráculo por `analisador-genealogico/app.py`.** Ele é um wrapper de 86 linhas que importa `reconstructed/`; usá-lo compara a reconstrução **com ela mesma** — a validação circular do RISK-002. O `app_legacy_e43ca22.py` existe exatamente para evitar isso.

## Arquitetura: dois subprocessos, não um

```
FASE 1 — COLETA                          FASE 2 — DIFF
┌────────────────────────────┐
│ subprocesso A: ORÁCULO     │──► _obs_oracle.json ─┐
│  copiado p/ dir temporário │                     ├─► comparação exata
│  chdir antes do import     │                     │   (após canonicalizar set)
└────────────────────────────┘                     │
┌────────────────────────────┐                     │
│ subprocesso B: CANDIDATO   │──► _obs_cand.json ──┘
│  importa reconstructed/    │
└────────────────────────────┘
```

**Por que dois subprocessos e não um só.** O oráculo mantém **estado global mutável** (`people`, `families`, `graph`, `child_to_family`) e executa `os.makedirs("uploads")` / `os.makedirs("static")` **relativos ao diretório de trabalho, no momento do import**. Importar oráculo e candidato no mesmo processo traria dois problemas:
1. As globais de um contaminariam as do outro — e o candidato deve ser **puro** (AD-01).
2. O `chdir` necessário para neutralizar o `makedirs` afetaria o candidato também.

Isolando em subprocessos, cada lado roda com o ambiente que precisa.

## Cobertura dos probes

| Probe | O que compara | Regras cobertas |
|---|---|---|
| `person_count` / `family_count` | contagens do parse | BR-MIGRAR-001, 002 |
| `names` | **lista completa** de nomes ordenados | BR-MIGRAR-003, 004 |
| `get_name` | nome de exibição **por pessoa** | BR-MIGRAR-003 (crítico) |
| `graph` | nós e arestas do grafo | BR-MIGRAR-002 |
| `child_to_family` | índice filho→família | BR-MIGRAR-002 |
| `get_parents` / `get_spouses` | arestas por pessoa | BR-MIGRAR-022 |
| `norm_name`, `strip_bad_utf`, `demojibake` | normalização e mojibake | BR-MIGRAR-006, 007 |
| `split_name_pt`, `surnames_set` | decomposição pt-BR | BR-MIGRAR-007, 012 |
| `top_given_tokens`, `token_prefixes`, `drop_short_tokens`, `surname_core_tokens` | índices de candidatos | BR-MIGRAR-008, 011, 012 |
| `cm` | **40 valores** de cM, incluindo fronteiras e ≤ 0 | BR-MIGRAR-020, 021 |
| `ancestral` | caminho direto para **1.600 pares** (40×40) | BR-MIGRAR-022, 023 |
| `indirect` | caminho indireto para os mesmos pares | BR-MIGRAR-024, 025 |

## Fixtures

`make_fixtures.py` materializa 13 arquivos em `_reversa_sdd/parity/fixtures/`. Os `tests/fixtures/*.py` existentes são **geradores Python** (constantes string), não arquivos consumíveis pelo `GedcomReader(file_path)` do oráculo — por isso a materialização era necessária.

| GEDCOM | Propósito |
|---|---|
| `basic.ged` | árvore base: direto, indireto, sem conexão, homônimos |
| `variants.ged` | grafias variantes (`netto`/`neto`, `gouvea`/`gouvêa`), nome genérico, sufixos salvadores |
| `no_name.ged` | **nome ausente vs nome com formato vazio** (BR-MIGRAR-003) |
| `mojibake_latin1.ged` | arquivo gravado em **Latin-1** — exercita fallback de encoding |
| `deep25.ged` | cadeia de **25 gerações** — exercita `max_depth=20` |
| `affinity.ged` | **múltiplas afinidades** — exercita `split_path_by_marriage` (RISK-011) |

CSVs de DNA: `utf8`, `duplicated` (agregação), `no_intersection` (anti-falso-positivo), `generic` (interseção adaptativa), `cm_boundaries`, `latin1`, `missing_col`.

## Como o diff evita falsos positivos

Três correções foram necessárias durante a construção, todas de **probe mal escrito**, não do sistema. A terceira foi encontrada **depois** de o harness já estar "pronto" — porque um resultado que mudava entre execuções idênticas obrigou a investigar.

1. **Função errada comparada.** O oráculo tem **uma** `strip_bad_utf` que faz dicionário de mojibake **e** limpeza de não-alfanuméricos. A reconstrução **dividiu** isso: `dna_analysis.strip_bad_utf` é a cópia fiel (L74-90) e `domain.strip_bad_utf` é outra coisa (só remove `U+FFFD`). Comparar `domain.strip_bad_utf` com o oráculo acusava divergência que **não existe em comportamento** — a função certa é `dna_analysis.strip_bad_utf`.
2. **Ordem de `set` tratada como contrato.** `split_name_pt` devolve `set` para sufixos. Um lado materializava em ordem diferente do outro, e comparar listas cruas acusava divergência. `set` não tem ordem: o diff agora **canonicaliza recursivamente** qualquer `set`/`frozenset` para lista ordenada — mas **preserva a ordem de `list`/`tuple`**, porque aí a ordem *é* contrato.
3. **O `set` era materializado antes de chegar ao canonicalizador** — o mais sutil dos três, e o mais instrutivo. O probe estava escrito assim:

   ```python
   obs["split_name_pt"] = {n: safo(lambda x: [list(v) if isinstance(v, (set, tuple)) else v
                                              for v in m.split_name_pt(x)], n) for n in names}
   ```

   `split_name_pt` devolve a **tupla** `(given, surnames, {suffixes})`. A compreensão via a tupla e aplicava `list(v)` — o que converte a tupla, mas deixa o **`set` de sufixos aninhado dentro de uma lista**. O `_canon()` só reconhece `set` no nível em que o encontra; encontrando uma `list`, ele preserva a ordem — que era a ordem arbitrária de iteração do `set`.

   **Consequência: a divergência era intermitente.** Ordem de iteração de um `set` de strings depende do **PYTHONHASHSEED**, que muda a cada processo. Como oráculo e candidato rodam em **subprocessos separados**, o mesmo par podia coincidir numa execução e divergir na seguinte. O `variants.ged` apareceu divergente numa execução e com paridade total na seguinte — **sem nenhuma mudança no código sob teste**.

   A correção foi aplicar uma normalização recursiva (`jsonable`) no ponto de coleta, nos **dois** coletores — ordenar `set` e preservar `list`/`tuple`. Note que a correção ingênua (`list(...)` direto) **quebra a serialização**: `set` não é JSON-serializável, e o coletor morre com `TypeError: Object of type set is not JSON serializable`. Normalizar na coleta resolve as duas coisas de uma vez.

> **Lição registrada**: um harness diferencial mal escrito produz divergências falsas, e uma divergência falsa custa tanto quanto uma real — obriga a investigar. Os três casos acima foram encontrados **investigando a causa raiz antes de reportar**, nunca aceitando o número do diff como resposta. O terceiro é o mais perigoso porque **não é reprodutível**: um resultado que muda entre execuções idênticas é pior que um erro determinístico, e a única defesa é canonicalizar na fronteira de coleta.

## Resultado

### Fixtures sintéticas — 6/6 com paridade (após aplicar DIV-001)

| Fixture | Resultado |
|---|---|
| `affinity.ged` | ✅ paridade |
| `basic.ged` | ✅ paridade |
| `deep25.ged` | ✅ paridade |
| `mojibake_latin1.ged` | ✅ paridade |
| `variants.ged` | ✅ paridade |
| `no_name.ged` | ✅ paridade *(antes da correção: ❌ 2 pessoas, `@K1@` e `@K3@`)* |

Antes da correção, `no_name.ged` era a **única** das seis a falhar — e é exatamente a fixture desenhada para o caso de borda do nome. O harness localizou o defeito na fixture que existia para encontrá-lo.

### Dados reais — 5 árvores reais do usuário

Todas trazem dados reais dos 12 arquivos que o usuário já havia enviado (`analisador-genealogico/uploads/`). É a validação que mais importa. **Resultado após aplicar DIV-001: paridade total nas cinco.**

| GEDCOM | Tamanho | Antes da correção | Depois |
|---|---|---|---|
| `SandroTree.ged` | 927 KB | ✅ paridade | ✅ paridade |
| `sssazevedo_2025-10-07.ged` | — | ✅ paridade | ✅ paridade |
| `Gedcom_Sandro.ged` | — | ✅ paridade | ✅ paridade |
| `Backup-Arvore-Sandro-12-11-2024.ged` | — | ✅ paridade | ✅ paridade |
| `Adriano_Santos.ged` | 3,3 MB · 3.056 pessoas · 1.105 famílias | ❌ **17** divergências | ✅ **paridade total** |
| `Arvore_Unificada_Oficial_V1_2.ged` | 5.207 KB · 35.460 pessoas · 6.930 famílias | ❌ **296** divergências | ✅ **paridade total** |

**A divergência escalava com o dado — e é isso que a tornava material.** Em `Adriano_Santos.ged` eram 17 pessoas (0,56%); em `Arvore_Unificada`, **296 em 35.460 (0,83%)**. Não era caso de borda: era uma fração consistente da base, crescendo em termos absolutos com o tamanho da árvore. Em ambas, a causa raiz era **uma única linha**.

**O que o resultado pré-correção já mostrava, e continua valendo como diagnóstico:** a divergência **não se espalhava**. cM, grafo e caminhos ficavam em paridade **mesmo nas árvores que falhavam** — inclusive na de 35.460 pessoas. Os 8 probes de função de nome não eram avaliados nessas árvores, e o harness dizia isso explicitamente em vez de reportar zeros enganosos:

```
[[probes de nome]] NAO avaliados nesta fixture: as entradas sao diferentes
                   (causa raiz acima). Corrija `get_name` e re-execute.
```

Depois da correção, os nomes coincidem, os probes **passam a ser avaliados** e todos dão paridade — sobre 35.460 pessoas reais e 9 funções de normalização e decomposição de nome cada. Era o oposto de uma reconstrução defeituosa: uma reconstrução fiel com **uma** alteração deliberada de comportamento, isolada e com efeito mensurado.

> **Limite de reporte honesto do harness.** Ele imprime no máximo 5 pessoas divergentes e resume o resto em `... e mais N`. Nos 296 divergentes de `Arvore_Unificada` (estado pré-correção), o diff mostrava 5 pessoas e agregava as outras 291. O número de **linhas** de diff (8) era um artefato do formato de relatório e **não** media a escala do problema — quem media era a contagem de pessoas (`296`).

## ✅ Contraprova — corrigido `get_name`, a paridade é TOTAL

Uma divergência isolada só é conclusiva se, removida ela, **nada mais sobrar**. Se restasse um segundo problema escondido atrás do primeiro, a conclusão "DIV-001 é a única divergência" seria falsa. Isso é testável, então foi testado — **antes** de a correção ser aplicada.

`_verify_fix_gives_parity.py` copia `reconstructed/` para um stub temporário, substitui **apenas** `get_name` pela versão do oráculo, aponta o coletor do candidato para o stub e roda o harness. **Não toca** em `analisador-genealogico/reconstructed/`.

| Alvo (no stub) | Resultado |
|---|---|
| 6 fixtures sintéticas | ✅ **PARIDADE 100%** (zero divergência em todas, inclusive `no_name.ged`) |
| `Arvore_Unificada_Oficial_V1_2.ged` — 35.460 pessoas | ✅ **PARIDADE 100%** (zero divergência) |

O resultado na árvore grande é o mais forte do harness inteiro. Note o que ele significa: nas árvores com DIV-001, os **8 probes de função de nome nem eram avaliados** (`NAO avaliados nesta fixture: as entradas sao diferentes`). Com a correção, os nomes passam a coincidir, os probes **são** avaliados e **todos** dão paridade — sobre 35.460 pessoas reais, 9 funções de normalização e decomposição de nome cada.

**Conclusão estabelecida por execução, não por inspeção:** DIV-001 é a **única** divergência de comportamento entre o oráculo congelado e o candidato `reconstructed/`. A reconstrução não tinha um segundo defeito.

**A contraprova previu o resultado da correção real.** Depois de aplicada em `reconstructed/`, o harness rodado **contra o código real** (sem stub) deu exatamente o previsto: 6/6 fixtures e as 5 árvores reais em paridade total. O artefato fica no repositório como **teste de regressão**: se alguém reintroduzir o fallback, o stub volta a divergir enquanto o código real passaria — sinal claro de que a divergência foi reintroduzida.

> **O que esta contraprova NÃO prova.** Ela não cobria se a correção *devia* ser aplicada — isso era decisão de comportamento canônico, e coube ao humano (ver DIV-001). Ela provava que a correção era **suficiente** e **completa**. Também não cobre o nível de análise de DNA ponta a ponta nem a paridade visual (lacunas 1 e 3).

## 🔴 DIV-001 — `get_name`: a reconstrução "corrigiu" o legado e quebrou paridade

**Causa raiz encontrada, isolada em uma linha.**

```python
# ORÁCULO — _reversa_sdd/oracle/app_legacy_e43ca22.py:42-43
def get_name(person):
    return person.name.format() if person and person.name else "Sem Nome"

# CANDIDATO — analisador-genealogico/reconstructed/upload.py:33-38
def get_name(person) -> str:
    """Nome formatado do registro; 'Sem Nome' se ausente ou vazio."""
    if not person or not person.name:
        return "Sem Nome"
    formatted = person.name.format()
    return formatted if formatted and formatted.strip() else "Sem Nome"   # ← LINHA ADICIONADA
```

A reconstrução **adicionou deliberadamente** um fallback para o caso em que o formato resulta vazio. A própria docstring documenta a intenção: *"'Sem Nome' se ausente **ou vazio**"*.

**Por que está errado, apesar de parecer melhor:**

| | Comportamento |
|---|---|
| Oráculo | `person.name` existe, `.format()` → `''` → retorna **`''`** |
| Candidato | mesmo caso → retorna **`'Sem Nome'`** |

Em dado real, o caminho do `''` é o que **de fato ocorre** — medido: **17 pessoas** em `Adriano_Santos.ged` (3.056) e **296 pessoas** em `Arvore_Unificada_Oficial_V1_2.ged` (35.460); 318 nomes vazios em 55.523 nomes no total da base. Já o caminho do `'Sem Nome'` **nunca foi observado: 0 ocorrências**. Ou seja: a "melhoria" altera o comportamento **justamente no caso que existe**, e o fallback que ela adiciona protege um caso que os dados não produzem.

**Impacto observável**: a lista de nomes oferecida ao usuário muda. Onde o legado mostra uma **entrada vazia**, o sistema novo mostraria **"Sem Nome"**. Isso é comportamento visível e é exatamente o que a invariante de diff textual zero de `parity_specs.md` proíbe.

**Relação com o pipeline**: é a materialização executável do **AMB-024**, encontrado hoje ao confrontar as specs com o oráculo. O `parity_tests/01-carregar-gedcom.feature` **já cobre este caso** com dois cenários distintos (nome ausente → `"Sem Nome"`; formato vazio → `""`). O candidato **falha** no segundo.

## 🔴 DIV-001a — Por que 47 testes da reconstrução nunca detectaram isso

O achado mais instrutivo do harness **não é a divergência**: é que a suíte de 47 testes da reconstrução **não podia** detectá-la. Investigado com `_probe_fix_impact.py`, que monkey-patcha `get_name` para o comportamento exato do oráculo e roda a suíte real:

**A asserção é permissiva por construção** — `tests/test_upload.py:72-79`:

```python
def test_get_name_missing_returns_sem_nome():
    ged = SAMPLE_GED.replace("1 NAME Joao /Silva/", "1 SEX M")  # remove so nome
    ...
    assert get_name(upload.people["@I1@"]) in ("Sem Nome", "")   # ← aceita OS DOIS
```

O nome do teste diz `returns_sem_nome`, mas a asserção aceita `"Sem Nome"` **e** `""`. Medido:

| Se `get_name` devolvesse | A asserção |
|---|---|
| `''` (oráculo) | **PASSA** |
| `'Sem Nome'` (candidato) | **PASSA** |

**A asserção não pode falhar.** Ela não distingue os dois comportamentos, então DIV-001 é indetectável por ela — por construção, não por acidente.

Há um segundo ponto cego em `tests/test_upload.py:119`:

```python
assert "Sem Nome" in names or any(n.strip() for n in names)
```

A disjunção é satisfeita pelos **outros** nomes da árvore, então passa mesmo com nome vazio presente.

**Medição do impacto da correção** (`_probe_fix_impact.py`, exit real da suíte):

```
46 passed, 1 error in 0.58s
unico erro = tests/test_upload.py::test_ensure_dirs_creates_uploads (PermissionError)
```

⚠️ **Correção de uma afirmação minha anterior.** Eu havia registrado que aplicar a correção *"pode quebrar testes que assertam `"Sem Nome"` para nome vazio"*. **A medição refuta isso.** O único teste que asserta `"Sem Nome"` para o caso **ausente** é `test_get_name_empty_none` (L56, `get_name(None) == "Sem Nome"`) — e esse caso é **idêntico nos dois lados**, então continua passando. Nenhum teste quebra.

**A conclusão é o inverso da intuição**: a suíte não protegia o comportamento — ela **acomodava** a divergência. Foi exatamente por isso que a correção dos testes precisou acompanhar a do código: sem ela, o ponto cego permaneceria mesmo depois de o comportamento ser corrigido.

> **Lição registrada**: uma asserção com `in (A, B)` sobre exatamente os dois valores em disputa não é um teste fraco — é um teste **nulo**. Ela dá cobertura aparente e nenhuma capacidade de discriminação. O harness diferencial encontrou em minutos o que 47 testes não podiam encontrar por construção. É o RISK-002 (validação circular) se materializando: a suíte testa a reconstrução **contra a sua própria suposição**, não contra o oráculo.

**Onde foi corrigido**: `analisador-genealogico/reconstructed/upload.py:33-38` — a terceira linha de retorno (`return formatted if formatted and formatted.strip() else "Sem Nome"`) foi **removida**, deixando o corpo reduzido à expressão única do legado. Aplicado em 2026-09-28 com autorização do usuário. ⚠️ O oráculo **não** foi alterado: continua a referência congelada e somente-leitura.

**Resultado após aplicar** (medido, não presumido):

| Alvo | Antes | Depois |
|---|---|---|
| 6 fixtures sintéticas | 5 ok, `no_name.ged` divergente | ✅ **6/6 paridade** |
| `Adriano_Santos.ged` (3.056) | 17 divergências | ✅ **paridade total** |
| `Arvore_Unificada_Oficial_V1_2.ged` (35.460) | 296 divergências | ✅ **paridade total** |
| Suíte de testes | 47 passed | ✅ **49 passed**, 1 erro ambiental |

**Correção dos testes que acompanha o código.** Aplicar só o código deixaria o ponto cego de pé. Em `tests/test_upload.py`:

- a asserção nula `in ("Sem Nome", "")` (L77) foi **substituída por três testes** que distinguem os casos;
- `assert "Sem Nome" in names or any(n.strip() for n in names)` (L119) — disjunção satisfeita pelos outros nomes da árvore — foi trocada por uma asserção de contagem exata (7 pessoas, 7 nomes, sem entrada vazia).

**Achado colateral que a correção dos testes expôs.** Ao escrever o teste do caso "ausente", descobriu-se que **remover a tag `NAME` de um `INDI` não produz `person.name is None`**: o ged4py ainda entrega um objeto `Name` cujo `.format()` é `''`. E um registro que realmente não tem o atributo `name` (um `FAM`) faz o ged4py **levantar `AttributeError`** — que a expressão do legado nunca dispara, porque `person and person.name` curto-circuita em `person` antes de tocar em `.name`.

Conclusão: **o literal `"Sem Nome"` é inalcançável a partir de registros INDI reais.** Só é exercitável por um duplo de teste (`person` falsy, ou `person.name` falsy). Isso explica de forma definitiva por que ele tem 0 ocorrências nos 55.523 nomes da base real, e está documentado no teste para que ninguém "conserte" a função tentando cobrir um caso de dados que não existe.

**A correção é segura para a suíte** — medido, não suposto: com o comportamento do oráculo, `46 passed, 1 error`, e o único erro é o `PermissionError` ambiental de `tmp_path` em `test_ensure_dirs_creates_uploads`, que não toca `get_name`. Nenhum teste asserta `"Sem Nome"` para o caso de formato vazio. O que a correção **exige** é apertar a asserção permissiva de `tests/test_upload.py:77` para `== ""`, senão o ponto cego continua aberto.

## Estado da Onda 0

| Item | Status |
|---|---|
| Oráculo congelado e verificado | ✅ |
| Runner do oráculo (`run_oracle.py`) | ✅ |
| **Harness diferencial** | ✅ **este artefato** |
| Fixtures materializadas (13) | ✅ |
| Cobertura de probes (14 famílias) | ✅ |
| **DIV-001 corrigido no candidato** | ✅ **aplicado, com os testes apertados** |
| **Paridade 100% (candidato real, sem stub)** | ✅ **6/6 fixtures + árvores reais medidas** |
| **Ponto cego da suíte fechado** | ✅ asserção nula substituída por 3 testes discriminantes |
| **Artefato do stub (contraprova)** | 🔒 mantido para regressão: `_verify_fix_gives_parity.py` |

## O que ainda NÃO está coberto

Registrado para não dar impressão de cobertura maior do que a real:

1. **Nível de análise de DNA ponta a ponta.** O harness cobre o **núcleo** (parsing, normalização, índices, cM, caminhos) exaustivamente, mas **não** orquestra `dna_analysis(csv, root)` contra o fluxo equivalente do oráculo — porque no oráculo esse fluxo vive **dentro da rota Flask** (`index()`), não como função isolada. Compará-lo exige executar o app e extrair o resultado do HTML. É o próximo incremento natural do harness.
2. **`generate_mermaid_graph`.** Existe nos dois lados, mas o alvo **descarta a emissão de Mermaid** (BR-DESCARTAR-005 / DEV-004). Compará-lo teria valor apenas como diagnóstico, não como requisito.
3. **Golden files de tela.** Continuam **0 capturados** (AMB-022). A paridade **visual** das 8 entradas literais permanece especificada e não provada.
4. **Pares de caminho amostrados.** O harness usa 40×40 = 1.600 pares por fixture, não todos. Em `Arvore_Unificada_Oficial_V1_2.ged` (35.460 pessoas) a cobertura por amostragem é uma fração pequena do espaço — honesto registrar.
5. **`Arvore_Unificada_Oficial_V1_2.ged` (5.207 KB, 35.460 pessoas) — MEDIDO.** Com `--pares 8` o harness completou: **1 causa raiz única `get_name`**, com **296 pessoas divergentes em 35.460 (0,83%)**. Custo por fase, medido **sem outros processos** (medido 2×, com variação):

   | Fase | Tempo |
   |---|---|
   | import do oráculo | 2,2 s |
   | **`load_gedcom_and_build_graph`** | **21,8 s e 33,0 s** (variação entre execuções) |
   | `get_name` (35.460 pessoas) | 0,5 s |
   | probes de nome (9 funções × 35.460 nomes) | ~12 s |
   | **pares de caminho 40×40 = 1.600** | **12,5 s** |
   | pares de caminho 8×8 = 64 | 0,3 s |
   | **total por coletor** | **~50–65 s** |

   O gargalo é o **parse** (`load_gedcom_and_build_graph`), que sozinho é a maior parcela. Os pares de caminho crescem de forma **quadrática** (64→0,3 s; 256→2,4 s; 1.600→12,5 s) e são a **segunda** parcela — reduzir a amostra continua sendo a alavanca certa, mas o parse domina.

   > **Duas hipóteses minhas, ambas refutadas por medição — registradas porque errar assim é o modo de falha real deste trabalho.**
   >
   > **(a) "Os pares de caminho são o gargalo."** Falso: o parse é maior. A hipótese veio de supor que caminhada em grafo grande domina — plausível, e errada.
   >
   > **(b) "Os pares custam ≈0,0 s."** Também falso, e pior: era uma **extrapolação de 20 repetições de UM ÚNICO par** (`ids[0]` com `ids[-1]`), que cai em cache e mede ≈0. Escalar isso por 1.600 deu um número sem significado. Medido de verdade: **12,5 s**. *Um probe barato não prova que o espaço inteiro é barato.*
   >
   > **(c) E o erro de método mais grave: tempo de parede medido com outro job rodando.** Um run instrumentado atribuiu **565 s** ao probe `norm_name` — 91% do total, e parecia um achado. Era contaminação: o harness completo rodava **em paralelo**, sobre o mesmo arquivo de 35.460 pessoas. Medido limpo e com 3 repetições, `norm_name` custa **2,6–3,3 s** (0,07–0,09 ms/nome). Fator de erro: **~200×**. Os nomes são benignos (máximo 107 caracteres, p99 42, zero acima de 200) — não havia caso patológico algum. **Nunca meça tempo de parede com outro job sobre a mesma entrada, e sempre repita antes de acreditar num número.**
6. **Semeadura da amostra é posicional.** `sample = ids[:N]` pega os N primeiros IDs, não uma amostra aleatória nem representativa. Em GEDCOM real os IDs costumam ser sequenciais por ordem de registro, então a amostra pode concentrar-se em um ramo. Isso **subestima** a cobertura do espaço de pares e deve ser lido como piso, não como estimativa.
7. **O harness não limpa o próprio resíduo.** Ele grava `_collect_oracle.py`, `_collect_cand.py`, `_obs_oracle.json` e `_obs_cand.json` em `_reversa_sdd/parity/` a cada execução, e cria `.parity-run-oracle/` e `.parity-run-cand/` na raiz. Nada disso é artefato registrado — é resíduo. Use `_clean_residue.py`. Os dois `_collect_*.py` são **cópias geradas** dos coletores embutidos em `harness.py`; a fonte da verdade é o `harness.py`, nunca os `_collect_*.py`.

## Notas

- **O harness roda contra `reconstructed/`, não contra `analisador/`.** Isso é deliberado e é o que dá valor imediato: `reconstructed/` é o núcleo candidato da Onda 1, e agora ele tem uma **medida real** de paridade, não uma estimativa. Quando o `analisador/core/` existir, basta apontar o coletor do candidato para ele — o lado do oráculo não muda.
- **DIV-001 foi corrigido e aplicado.** A mudança é pequena — remover uma linha de `reconstructed/upload.py` — mas a decisão **não** era só de código: era decidir qual comportamento é canônico. O oráculo respondeu `''`, o usuário autorizou, e a correção foi acompanhada do **apertar dos testes**, sem o qual o ponto cego permaneceria. `_probe_fix_impact.py` continua no repositório como verificação de regressão (o monkey-patch virou no-op, e o arquivo documenta por quê).
- **Artefatos de apoio** em `_reversa_sdd/parity/`: `harness.py` (o instrumento), `make_fixtures.py` (materializa as 13 fixtures), `_probe_fix_impact.py` (mede o impacto da correção nos 47 testes), `_verify_fix_gives_parity.py` (**a contraprova**), `_clean_residue.py` (limpa o resíduo gerado) e `_verify_hashes.py` (confere os hashes do `.state.json` contra o disco).
- **Confirmação de integridade**: `_verify_hashes.py` reporta **30 hashes conferem, 0 divergem, 0 ausentes**. Convenção: `.md` → sha256 do **corpo** (abaixo do front-matter, LF-normalizado); `.py`/`.json`/`.yaml` → sha256 do **arquivo inteiro**.
- **Scripts de diagnóstico não registrados**: `_profile_big.py` e `_profile_collector_costs.py` (perfil de tempo) existem como ferramentas de investigação, mas **não** estão em `.state.json` — não são artefatos do pipeline. São o que permitiu refutar as duas hipóteses erradas de gargalo descritas na lacuna 5.
- **Nenhum arquivo do legado foi tocado.** O harness lê o oráculo e o candidato, escreve apenas em `_reversa_sdd/parity/` e em diretórios temporários que remove ao final.

---
*Gerado pelo Reversa em 2026-09-28.*
