# Adendo: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/domain.md` e `_reversa_sdd/busca-caminho/design.md`)
> Modo: **express** — a spec fina vive em `_reversa_forward/045-humanizar-geracao-de-diferenca/`

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

O rótulo do primo dizia `Primos de 2º grau (1× removido)` e `Primos de 1º grau (3× removidos)`. O
termo é jargão de quem já conhece a tabela — **removido de quê?** — e a forma oscilava: singular
`1× removido`, plural `2× removidos`, e um **terceiro** jeito no parentesco documental, `com 2×
remoção`. A tela passou a dizer:

| Antes | Agora |
|---|---|
| `Primos de 2º grau (1× removido)` | `Primos de 2º grau (uma geração de diferença)` |
| `Primos de 1º grau (3× removidos)` | `Primos de 1º grau (três gerações de diferença)` |
| `Primos de 1º grau com 2× remoção` | `Primos de 1º grau (duas gerações de diferença)` |
| `Primos de 3º grau com 4× remoção` | `Primos de 3º grau (quatro gerações de diferença)` |

A contagem vai por extenso até dez e em algarismo acima (`11 gerações de diferença`), porque a série
dos primos chega a `(11, 1)` no arquivo real e `onze` num rótulo de tabela não ajuda a ler.

**O ganho estrutural é maior que o de redação.** O rótulo passou a ter **fonte única**:
`nome_do_primo(grau, removidos)` em `core.graus_de_parentesco`. As duas superfícies que escreviam o
nome — a tabela publicada do Shared cM, no bloco 3 (`SCP40_ROWS`), e o parentesco documental
(`documentary_label`) — agora chamam a mesma função, e há teste que compara as duas: elas não podem
divergir. Nove `name_pt` literais saíram da tabela publicada.

**O que não mudou:** a chave canônica (`1C2R`, `2C1R`), as meioses, a ordenação, o destaque da 044,
os vereditos do confronto e qualquer cM. `core/cm_estimator.py` — legado, fora do fluxo, não exibido —
mantém os literais antigos de propósito, porque é superfície de compatibilidade do harness de paridade.

**5 ações concluídas** (`T001`–`T005`). Suíte em **1585 passed, 9 skipped** (antes: 1574/9, delta de
+11). `SHA_DA_TELA` inalterado. Varredura dos **456 kits** do arquivo real: 17 rótulos distintos,
**nenhum** com `×` ou com a palavra `remoção`.

### Correção de registro feita nesta feature

Ao editar `documentary_label` fui conferir quem lê o rótulo e encontrei `core/validator.py`: ele
**lê a chave**, não o texto, e documenta que "a coluna `meioses` de `SCP40_ROWS` é a chave da relação,
não o total do caminho". Isso desfaz o que a 043 registrou como defeito — a convenção é **declarada e
intencional**, não um erro de tabela. As três notas afetadas (`regression-watch` da 043, adendo da 043
e `regression-watch` da 044) foram corrigidas. O ponto que **segue aberto** é outro e menor:
`core/evidence_comparison._janela_do_documental` passa um **total** (4 para 1C) a `meioses_window`,
cuja coluna guarda **chaves** (2 para 1C), o que desloca a envoltória das relações não publicadas.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/data-dictionary.md#62-linha-publicada-do-shared-cm-project-40` | §6.2 Linha publicada do SCP 4.0 | delta-de-dados | `name_pt` deixa de ser literal e passa a ser **derivado** de `nome_do_primo(grau, removidos)` nas nove linhas com diferença de geração; o valor exibido muda (`(1× removido)` → `(uma geração de diferença)`) e a natureza do campo também (derivado, não transcrito) |
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | §3.3 Possibilidades (Shared cM Project 4.0) | regra-alterada | O rótulo de cada possibilidade passa a nomear a **geração de diferença**, com fonte única entre o bloco 3 e o parentesco documental |
| `_reversa_sdd/busca-caminho/design.md#tradução-de-graus-documentary_label` | Tradução de graus (`documentary_label`) | regra-alterada | A linha "Demais — Primos de `g` grau com `r` remoções" passa a "Primos de `g` grau (`r` geração/gerações de diferença)"; a **chave** (`gC`/`gCrR`) e as meioses continuam as mesmas. Nota: o 🟡 da mesma tabela que fala em `bis` repetido **já estava vencido desde 2026-10-14** (a série passou a `bisavô → trisavô`) — não é desta feature, mas está na mesma tabela |
| `_reversa_sdd/c4-components.md#inventário-de-componentes` | Inventário de componentes | regra-alterada | O componente folha criado pela 043 (`core/graus_de_parentesco`) ganha `nome_do_primo` e `geracoes_de_diferenca` e passa a ser a **fonte única do rótulo do primo**, consumida também por `documentary_relationship` (que importa `networkx`) |
| `_reversa_sdd/addenda/043-tabela-do-antepassado-comum.md#resumo-da-entrega` | Resumo da entrega | regra-alterada | A tabela de exemplo da 043 cita `Primos de 2º grau (1× removido)` e `Primos de 1º grau (3× removidos)`; a forma **vigente** é a da 045. O mesmo vale para o exemplo entre aspas do adendo 044 |

## Regras sob vigilância

- `W001` a `W005` — ver `_reversa_forward/045-humanizar-geracao-de-diferenca/regression-watch.md`.
  Os dois primeiros são os que um futuro `/reversa` deve conferir antes de reescrever as specs: o
  rótulo sai de uma função só, e as duas superfícies dizem o mesmo texto.
- As quatro observações sem peso estão no mesmo arquivo. Duas importam para não se perderem: o
  `cm_estimator` mantém os literais **de propósito** (é legado e superfície de paridade), e a forma
  relacional — "primo de 1º grau de um dos pais" — foi **descartada** porque o bloco 3 não sabe qual
  dos dois lados está mais alto: a linha da tabela é simétrica.

## Fontes

- `_reversa_forward/045-humanizar-geracao-de-diferenca/requirements.md`
- `_reversa_forward/045-humanizar-geracao-de-diferenca/roadmap.md`
- `_reversa_forward/045-humanizar-geracao-de-diferenca/actions.md`
- `_reversa_forward/045-humanizar-geracao-de-diferenca/legacy-impact.md`
- `_reversa_forward/045-humanizar-geracao-de-diferenca/regression-watch.md`
- `_reversa_forward/045-humanizar-geracao-de-diferenca/progress.jsonl`
