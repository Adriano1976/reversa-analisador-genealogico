---
schemaVersion: 1
generatedAt: "2026-09-28T05:40:00Z"
reversa:
  version: "1.2.58"
kind: parity_harness
producedBy: orchestrator
hash: "96229d750307cf294de3f79cfc57156b5d34a2e31691777ebc3244cfe4a5e6e6"
---

# Parity Harness — Execução Diferencial

> **Este é o instrumento que transforma os 102 cenários de `parity_tests/` em evidência.** Ele executa o oráculo congelado e o candidato sobre as **mesmas entradas** e compara com **igualdade exata**, materializando a métrica primária do brief: *"paridade de matching ≥ 100% nos casos de teste"*.

## Como executar

```powershell
# todas as fixtures sintéticas
python _reversa_sdd\parity\harness.py

# um GEDCOM específico (sintético ou real)
python _reversa_sdd\parity\harness.py --gedcom caminho\para\arvore.ged

# salva as observações completas em JSON (para inspeção/regressão)
python _reversa_sdd\parity\harness.py --json observacoes

# (re)gera as fixtures
python _reversa_sdd\parity\make_fixtures.py
```

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

Duas correções foram necessárias durante a construção, ambas de **probe mal escrito**, não do sistema:

1. **Função errada comparada.** O oráculo tem **uma** `strip_bad_utf` que faz dicionário de mojibake **e** limpeza de não-alfanuméricos. A reconstrução **dividiu** isso: `dna_analysis.strip_bad_utf` é a cópia fiel (L74-90) e `domain.strip_bad_utf` é outra coisa (só remove `U+FFFD`). Comparar `domain.strip_bad_utf` com o oráculo acusava divergência que **não existe em comportamento** — a função certa é `dna_analysis.strip_bad_utf`.
2. **Ordem de `set` tratada como contrato.** `split_name_pt` devolve `set` para sufixos. Um lado materializava em ordem diferente do outro, e comparar listas cruas acusava divergência. `set` não tem ordem: o diff agora **canonicaliza recursivamente** qualquer `set`/`frozenset` para lista ordenada — mas **preserva a ordem de `list`/`tuple`**, porque aí a ordem *é* contrato.

> **Lição registrada**: um harness diferencial mal escrito produz divergências falsas, e uma divergência falsa custa tanto quanto uma real — obriga a investigar. Os dois casos acima foram encontrados **investigando a causa raiz antes de reportar**, nunca aceitando o número do diff como resposta.

## Resultado

### Fixtures sintéticas — 6/6

| Fixture | Resultado |
|---|---|
| `affinity.ged` | ✅ paridade |
| `basic.ged` | ✅ paridade |
| `deep25.ged` | ✅ paridade |
| `mojibake_latin1.ged` | ✅ paridade |
| `variants.ged` | ✅ paridade |
| `no_name.ged` | ❌ **1 causa raiz**: `get_name` |

### Dados reais — 4 árvores reais do usuário

Todas trazem dados reais de 12 arquivos que o usuário já havia enviado (`analisador-genealogico/uploads/`). É a validação que mais importa, porque é onde o comportamento divergente **de fato ocorre**.

| GEDCOM | Tamanho | Resultado |
|---|---|---|
| `SandroTree.ged` | — | ✅ paridade total |
| `sssazevedo_2025-10-07.ged` | — | ✅ paridade total |
| `Gedcom_Sandro.ged` | — | ✅ paridade total |
| `Adriano_Santos.ged` | 3,3 MB · 3.056 pessoas · 1.105 famílias | ❌ **1 causa raiz** → 17 nomes divergentes |
| `Arvore_Unificada_Oficial_V1_2.ged` | 5.207 KB · 35.460 pessoas | ⏳ não concluiu nesta sessão (ver lacuna 5) |

Em `Adriano_Santos.ged`: ✅ paridade em **3.039 de 3.056 pessoas** (99,44%); ❌ **17 divergências** — exatamente os **17 nomes vazios** medidos na análise do AMB-024; ✅ grafo, `child_to_family`, `get_parents`, `get_spouses`, cM e caminhos: **paridade total**.

**Leitura correta deste resultado**: 3 de 4 árvores passam com paridade **total**, e a única que falha falha **por uma causa raiz única e já isolada em uma linha**. A divergência não se espalha: cM, grafo e caminhos ficam em paridade mesmo na árvore que falha. Isso é o oposto de uma reconstrução defeituosa — é uma reconstrução fiel com **uma** alteração deliberada de comportamento.

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

Em dado real, o caminho do `''` é o que **de fato ocorre** (318 pessoas em 55.523 nomes; 17 só em `Adriano_Santos.ged`), e o caminho do `'Sem Nome'` **nunca foi observado** (0 ocorrências). Ou seja: a "melhoria" altera o comportamento **justamente no caso que existe**, e o fallback que ela adiciona protege um caso que os dados não produzem.

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

**A conclusão é o inverso da intuição**: a suíte não protege o comportamento — ela **acomoda** a divergência. Depois da correção, `test_get_name_missing_returns_sem_nome` continuaria passando, e **deveria ser apertado para `== ""`**, senão o ponto cego permanece.

> **Lição registrada**: uma asserção com `in (A, B)` sobre exatamente os dois valores em disputa não é um teste fraco — é um teste **nulo**. Ela dá cobertura aparente e nenhuma capacidade de discriminação. O harness diferencial encontrou em minutos o que 47 testes não podiam encontrar por construção. É o RISK-002 (validação circular) se materializando: a suíte testa a reconstrução **contra a sua própria suposição**, não contra o oráculo.

**Onde corrigir**: `analisador-genealogico/reconstructed/upload.py:33-38` — remover a terceira linha de retorno (`return formatted if formatted and formatted.strip() else "Sem Nome"`) para igualar o oráculo, deixando o corpo reduzido à expressão única do legado. ⚠️ **Não** alterar o oráculo: ele é a referência congelada e somente-leitura.

**A correção é segura para a suíte** — medido, não suposto: com o comportamento do oráculo, `46 passed, 1 error`, e o único erro é o `PermissionError` ambiental de `tmp_path` em `test_ensure_dirs_creates_uploads`, que não toca `get_name`. Nenhum teste asserta `"Sem Nome"` para o caso de formato vazio. O que a correção **exige** é apertar a asserção permissiva de `tests/test_upload.py:77` para `== ""`, senão o ponto cego continua aberto.

## Estado da Onda 0

| Item | Status |
|---|---|
| Oráculo congelado e verificado | ✅ |
| Runner do oráculo (`run_oracle.py`) | ✅ |
| **Harness diferencial** | ✅ **este artefato** |
| Fixtures materializadas (13) | ✅ |
| Cobertura de probes (14 famílias) | ✅ |
| **Paridade 100%** | ❌ **1 causa raiz aberta** (DIV-001) |
| **Ponto cego da suíte diagnosticado** | ✅ DIV-001a — asserção permissiva, medido |
| **Impacto da correção medido** | ✅ 46 passed / 1 error ambiental — correção segura |

## O que ainda NÃO está coberto

Registrado para não dar impressão de cobertura maior do que a real:

1. **Nível de análise de DNA ponta a ponta.** O harness cobre o **núcleo** (parsing, normalização, índices, cM, caminhos) exaustivamente, mas **não** orquestra `dna_analysis(csv, root)` contra o fluxo equivalente do oráculo — porque no oráculo esse fluxo vive **dentro da rota Flask** (`index()`), não como função isolada. Compará-lo exige executar o app e extrair o resultado do HTML. É o próximo incremento natural do harness.
2. **`generate_mermaid_graph`.** Existe nos dois lados, mas o alvo **descarta a emissão de Mermaid** (BR-DESCARTAR-005 / DEV-004). Compará-lo teria valor apenas como diagnóstico, não como requisito.
3. **Golden files de tela.** Continuam **0 capturados** (AMB-022). A paridade **visual** das 8 entradas literais permanece especificada e não provada.
4. **Pares de caminho amostrados.** O harness usa 40×40 = 1.600 pares por fixture, não todos. Em `Arvore_Unificada_Oficial_V1_2.ged` (35.460 pessoas) a cobertura por amostragem é uma fração pequena do espaço — honesto registrar.
5. **`Arvore_Unificada_Oficial_V1_2.ged` (5.207 KB, 35.460 pessoas) não concluiu** dentro do tempo desta sessão. A causa é estrutural, não um travamento: o probe de caminhos roda 1.600 pares × 2 buscas (`find_ancestral_path` + `find_indirect_path`) **em cada lado**, e em grafo desse tamanho o custo por busca cresce muito. Os 4 GEDCOMs menores completaram. Para fechar a cobertura do arquivo grande, reduza a amostra (`sample = ids[:40]`) ou torne-a configurável por `--pares N` — o resultado dos menores já estabelece o comportamento.
6. **Semeadura da amostra é posicional.** `sample = ids[:40]` pega os 40 primeiros IDs, não uma amostra aleatória nem representativa. Em GEDCOM real os IDs costumam ser sequenciais por ordem de registro, então a amostra pode concentrar-se em um ramo. Isso **subestima** a cobertura do espaço de pares e deve ser lido como piso, não como estimativa.

## Notas

- **O harness roda contra `reconstructed/`, não contra `analisador/`.** Isso é deliberado e é o que dá valor imediato: `reconstructed/` é o núcleo candidato da Onda 1, e agora ele tem uma **medida real** de paridade, não uma estimativa. Quando o `analisador/core/` existir, basta apontar o coletor do candidato para ele — o lado do oráculo não muda.
- **DIV-001 é uma correção de uma linha** em `reconstructed/upload.py`. Ela ainda **não foi aplicada** — e a razão não é risco de quebra (medido: nenhum teste quebra), e sim que a reconstrução é artefato de trabalho anterior e a decisão de qual comportamento é canônico pertence ao humano. O oráculo responde: `''`. Aplicar a correção sem apertar `tests/test_upload.py:77` deixaria o ponto cego de pé.
- **Dois artefatos de medição acompanham este documento**: `_reversa_sdd/parity/_probe_fix_impact.py` (mede o impacto da correção nos 47 testes, provando que a asserção permissiva é o ponto cego) e `_reversa_sdd/parity/make_fixtures.py` (materializa as 13 fixtures).
- **Nenhum arquivo do legado foi tocado.** O harness lê o oráculo e o candidato, escreve apenas em `_reversa_sdd/parity/` e em diretórios temporários que remove ao final.
