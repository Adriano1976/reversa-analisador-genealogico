# Evidências — feature `009-rota-do-apple-touch-icon`

> Feature: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`

## 1. Os instrumentos desta rodada

| Instrumento | O que mede | Onde |
|---|---|---|
| **Sonda independente da arte** | Dimensão, tipo de cor, integridade do fluxo — **sem** biblioteca de imagem na prova principal | `evidence/_t003_sonda_arte.py` |
| **Suíte** | `282 → 302 passed`, `8 skipped` iguais aos de antes | `evidence/_t010_suite.txt` |
| **Paridade diferencial** | 100 %, exit 0, contra o oráculo congelado | `evidence/_t010_suite.txt` |
| **Contêiner** | A arte na imagem e a rota respondendo **de dentro** | `evidence/_t008_t009_conteiner.txt` |
| **`git diff`** | O que foi tocado, e o que **não** foi | `evidence/T012-conferencia-de-escopo.md` |
| **Verificação manual** | Os passos do `onboarding.md` que o host e o contêiner provam | `evidence/T015-verificacao-manual.md` |

## 2. O achado que dispensou a biblioteca de imagem na prova principal

O formato PNG declara o **tipo de cor** no próprio cabeçalho, e o tipo **2** é `truecolor`
sem canal alfa. Isso torna a opacidade (`RF-03`) uma **propriedade do formato**, e não uma
leitura de amostra: não há onde guardar transparência em um PNG que declara não ter canal
alfa.

A canônica é tipo **6** (com alfa). A derivada é tipo **2**. O contraste entre os dois é a
prova de que a `D-02` foi aplicada — e é uma prova que **não** depende da biblioteca que
produziu o arquivo.

## 3. Resíduo deixado em disco

| Resíduo | Origem | Situação |
|---|---|---|
| `.parity-run-oracle/`, `.parity-run-cand/` | harness de paridade | no `.gitignore` (ato do usuário em 2026-10-07) |
| `_reversa_sdd/parity/_collect_oracle.py`, `_collect_cand.py` | harness de paridade | **não** ignorados; regenerados a cada execução |
| `tests/.tmp/` | pasta temporária da suíte | no `.gitignore` |
| `src/assets/apple-touch-icon.png` | **entrega**, não resíduo | versionado |
| `icone-servido.png` | sonda do `onboarding.md` §4 | **efêmero**; o passo 10 do onboarding manda remover |

**Nenhum resíduo novo foi criado dentro de `src/uploads/`.** A pasta continua com as mesmas
entradas de antes desta feature.

## 4. Lacunas declaradas desta rodada

| # | Lacuna | Onde está registrado |
|---|---|---|
| 1 | **Nada foi testado em aparelho real.** A prova visual do atalho depende do operador | `investigation.md` §6.1; `regression-watch.md` `OBS-30`; `onboarding.md` §8 |
| 2 | **A paridade em 100 % é ausência no núcleo, não conquista desta entrega** | `T010` §"Leitura honesta dos números" |
| 3 | **A `RN-05` diz "cópia"** onde a decisão diz "renderização derivada". Não corrigido aqui | `roadmap.md` §3; `legacy-impact.md` §7 |
| 4 | **A biblioteca de imagem dos testes não está em `requirements.txt`** | `D-09`; `OBS-33` |
| 5 | **Os artefatos desta feature não são lintados** — a config ignora `_reversa_forward/**` | `OBS-35` |
| 6 | **Outra sessão commitou artefatos desta feature em curso**, e alterou `src/app.py` no meio da execução | `T015` §5 |

## 5. Todos os arquivos desta pasta

| Arquivo | Ação | Conteúdo |
|---|---|---|
| `README-evidencias.md` | `T013` | Este arquivo |
| `_t003_sonda_arte.py` | `T003` | A sonda independente |
| `T003-arte-derivada.md` | `T003` | Medição da arte: tipo de cor, dimensão, cantos, fluxo |
| `_t008_t009_conteiner.txt` | `T008`, `T009` | Saída bruta do contêiner |
| `T008-arte-na-imagem.md` | `T008` | A arte existe **dentro** da imagem |
| `T009-rota-no-conteiner.md` | `T009` | A rota responde de dentro, com o cache decidido |
| `_t010_suite.txt` | `T010` | Saída bruta da suíte e da paridade |
| `T010-linha-de-base.md` | `T010` | Linha de base, e a prova do "falha antes" |
| `T011-varredura-de-forma.md` | `T011` | Pasta proibida, superfície sem consumidor, contexto de build |
| `T012-conferencia-de-escopo.md` | `T012` | O que foi tocado e o que tem `diff` vazio |
| `T015-verificacao-manual.md` | `T015` | Os passos do onboarding que dá para executar |

## Fontes

- `_reversa_forward/009-rota-do-apple-touch-icon/actions.md`
- `_reversa_forward/009-rota-do-apple-touch-icon/onboarding.md`
- `_reversa_forward/008-persistencia-postgres-docker/evidence/README-evidencias.md` (o formato)
