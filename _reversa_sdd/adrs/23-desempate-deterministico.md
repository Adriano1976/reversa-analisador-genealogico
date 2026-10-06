# ADR-23 — O desempate de candidatos deve ser determinístico

- **Status:** ✅ **Aceito e IMPLEMENTADO** em 2026-10-05
- **Data da decisão:** 2026-09-30 (resposta do usuário no `questions.md#pergunta-4`) · **Data da execução:** 2026-10-05 (`questions.md#pergunta-1`)
- **Implementação:** ✅ `src/core/matching.py:107-111` (quarto critério: menor `xref_id`) + **2 testes** em `tests/test_characterization_matching.py`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O matching difuso, quando o nome do CSV **não** casa exatamente com nenhum do GEDCOM, escolhe o melhor candidato por **três critérios em ordem**: mais sobrenomes em comum → maior similaridade de prenome → maior score. Se dois candidatos empatam **nos três**, o vencedor passa a ser **quem aparecer primeiro na iteração do conjunto de candidatos**.

O conjunto é um `set` de `xref_id`, e a ordem de iteração de um `set` de strings **varia entre processos**, porque o Python randomiza o hash de strings desde a versão 3.3 (`PYTHONHASHSEED`).

**Consequência:** duas execuções idênticas, sobre a mesma entrada, podem escolher **pessoas diferentes** — e a partir daí o caminho documental, o rótulo de parentesco, a janela de cM e o veredito do confronto **mudam todos**.

## Decisão

**Precisa ser determinístico.** Critério final sugerido pelo usuário: **o menor `xref_id` entre os empatados**.

## Evidência

- `_reversa_sdd/questions.md#pergunta-4` — o diagnóstico completo e a resposta registrada.
- Specs derivadas: `analise-dna/requirements.md` → **`RF-14`** (Must) + requisito não funcional de **Reprodutibilidade**; `analise-dna/tasks.md` → **`T-19`** e o teste **`TT-13`** (duas execuções com `PYTHONHASHSEED` diferente escolhem o mesmo candidato).
- `analise-dna/tasks.md` declara: *"É a única divergência deliberada do legado em toda a re-extração"* — declaração **superada**: com a execução desta ADR, são **duas** divergências deliberadas, e esta é a única que muda comportamento.

### Verificação no código de 2026-10-05 — **o requisito não está atendido**

- `src/core/matching.py:73` — `pool = set()`, alimentado por `pool.update(surname_index.get(sn, []))`.
- `src/core/matching.py:91` — `for pid in pool:` — a iteração do laço **é a iteração do conjunto**.
- `src/core/matching.py:107-111` — a condição de troca usa comparação **estrita** (`>`), e é ela que decide:

```python
if (inter_cnt_local > best_inter or
        (inter_cnt_local == best_inter and s_given > best_g) or
        (inter_cnt_local == best_inter and s_given == best_g and score > best_score)):
```

Empate exato nos três critérios **não** substitui o incumbente — logo, **o primeiro candidato encontrado na iteração do `set` vence**.

### Medição do mecanismo

Ordem de iteração do mesmo `set` de sete `xref_id`, em três sementes de hash:

```text
PYTHONHASHSEED=0 -> ['@I5@', '@I7@', '@I6@', '@I1@', '@I4@', '@I3@', '@I2@']
PYTHONHASHSEED=1 -> ['@I3@', '@I7@', '@I4@', '@I5@', '@I1@', '@I2@', '@I6@']
PYTHONHASHSEED=2 -> ['@I4@', '@I2@', '@I1@', '@I7@', '@I3@', '@I5@', '@I6@']
```

**Nenhuma** posição coincide entre as três execuções. Classificação: mecanismo 🟢 confirmado; **alcance prático** (quantas vezes o empate triplo ocorre em dado real) 🟡 **não medido** — exige exatamente três critérios iguais, o que é plausível mas não observado.

## O que **é** determinístico (para não se atribuir ao conjunto o que não é dele)

| Caminho | Estado | Por quê |
| --- | --- | --- |
| Casamento **exato** de nome | ✅ determinístico | `ged_index.get(key, [])` devolve **lista**, na ordem de inserção do GEDCOM |
| Escolha entre **homônimos** na busca de caminho | ✅ determinístico | `candidatos` é **lista** (`dict.fromkeys`), percorrida com teto de 5×5; vence a primeira com caminho |
| Resolução da **raiz** da análise | ✅ determinístico | primeiro registro na ordem de inserção (`people`) |
| Ordem de **apresentação** dos resultados | ✅ determinístico | chave de ordenação (grupo, −cM) sobre lista em ordem estável |
| **Desempate do ramo difuso** do matching | ❌ **NÃO determinístico** | é o objeto desta ADR |

## Por que a decisão ficou quase um mês sem execução — e como foi executada

🟢 **Registrado, não inferido.** A regra final da análise (ADR-14) reescreveu o fluxo de DNA em 2026-10-04 — commits `7bf2676` e `cd8d7f3` — **sem ciclo forward**: não há feature `005+` em `_reversa_forward/`, e portanto não há roadmap, tarefa nem adendo. O requisito ficou nas specs de 2026-09-30, que descrevem o código **anterior** ao refactor. **A decisão humana sobreviveu; a tarefa que a executaria não.**

**Execução (2026-10-05).** Em vez de manter o requisito apenas para o sistema alvo, você autorizou **corrigir o legado**. A mudança é pequena e localizada: um **quarto critério** no desempate — o menor `xref_id` lexicográfico vence quando os três critérios do legado empatam.

| Item | Antes | Depois |
| --- | --- | --- |
| Critérios de desempate | 3, com empate caindo na ordem de iteração do `set` | **4**, com o menor `xref_id` como critério final |
| `matching.py` | `:103-105` — comparação estrita | `:107-110` — estrita + `pid < best_pid` no empate triplo |
| Cobertura | nenhuma (`TT-15` era lacuna) | 2 testes sob **duas ordens de *pool*** |
| Reprodutibilidade | vencedor variava entre processos | **estável** |

## Consequências

- ✅ **`L-15` FECHADA em 2026-10-05.** Era a **única decisão humana vigente não honrada** pelo código, do conjunto de 13 verificadas nesta re-extração. Agora as 13 estão honradas.
- ⚠️ **É uma divergência deliberada de COMPORTAMENTO — a primeira de toda a extração.** Nos casos de **empate triplo**, o vencedor pode ser outro depois da correção. Fora do empate, nada muda. A declaração das faixas de cM como heurística (ADR-19) foi a primeira divergência *de spec*, mas não alterou comportamento.
- 🔴 **É uma divergência entre spec e código, e a spec está certa.** `RF-14` é o único requisito da extração anterior que o código de 2026-10-05 **viola**, e viola porque a reescrita não passou pelo ciclo que o implementaria.
- ⚠️ **O efeito é mais amplo do que "escolher outra pessoa".** O candidato escolhido determina o caminho documental, que determina o rótulo, que determina a **janela de cM**, que determina o **veredito do confronto**. Uma escolha instável propaga até o resultado de negócio mais visível do sistema.
- 🟢 **A correção é pequena e localizada:** um critério final determinístico no desempate (menor `xref_id` entre os empatados), ou trocar `pool` por estrutura ordenada. Não exige reescrita.

## Alternativas consideradas

- **Aceitar o desempate pelo conjunto.** Descartada pelo usuário: um resultado que muda entre execuções idênticas é pior que um erro determinístico, porque **não é reproduzível** — o mesmo argumento já registrado no `parity_harness.md` a respeito de um falso positivo intermitente do harness.
- **Menor `xref_id`** (sugerida pelo usuário). Escolhida como critério; **não implementada**.
- **Critério por ordem de inserção no GEDCOM.** Equivalente em efeito e também determinístico; **não adotado** porque `xref_id` é estável entre arquivos com a mesma pessoa, enquanto a posição no arquivo não é.
