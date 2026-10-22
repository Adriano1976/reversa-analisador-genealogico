# Actions: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/044-destaque-da-hipotese-mais-proxima/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 5 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 3 (T001 → T002 → T003 → T004) |

## Fase 1, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar a banda, o teto, os rótulos e `destaque_das_candidatas`, com `destaque` e `distancia_da_media` no payload | - | `[//]` | `src/core/relationship_hypotheses.py` | 🟢 | `[X]` |

## Fase 2, Apresentação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Caixa de destaque antes da tabela, marca na linha destacada e distância em cada linha | T001 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T003 | Estilos da caixa e da linha destacada | T002 | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |

## Fase 3, Verificação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Cobrir a banda, o teto, os três casos reais e a tela; e conferir na análise real | T003 | `[//]` | `tests/test_destaque_da_hipotese.py`, `tests/test_destaque_na_tela.py`, `tests/fixtures/sample_dna.py` | 🟢 | `[X]` |
| T005 | Rodar a suíte completa e registrar os números dos dois recortes (kits e cartões) | T004 | - | — | 🟢 | `[X]` |

## Notas de execução

- **T001:** a grandeza do destaque é a **mesma** que já ordena a lista (`|média publicada − cM|`).
  Não entrou peso, soma nem segunda medida: entrou um corte declarado — `1,5×` a menor distância —
  e um teto de três. `destaque=False` nasce em toda candidata, para o template não precisar de
  `default`.
- **T001 (o empate exato):** quando o valor é exatamente a média publicada, a menor distância é
  `0` e a banda é `0` — só as empatadas na média entram. É o comportamento desejado: um acerto
  exato não precisa de companhia.
- **T001 (o texto):** o rótulo fala em "média publicada", nunca em "mais provável", e a ressalva
  carrega três informações: o critério, o tamanho do conjunto ("entre as 9 relações compatíveis")
  e a negativa ("não é confirmação: o parentesco documental continua vindo do GEDCOM"). Sem a
  contagem, o destaque apagaria o fato de que a lista não discrimina.
- **T002:** a caixa fica **antes** da tabela e a tabela continua inteira — a destacada é uma linha
  dela, marcada com `linha-destacada`. A coluna da faixa ganhou "distância da média" em **todas**
  as linhas, para a ordem ser auditável fora da caixa.
- **T003:** `.destaque-da-hipotese` usa `border-left` na cor primária e `--surface-2`; a marca da
  linha é só o fundo — nenhuma cor de veredito (verde/vermelho) foi usada, porque o destaque não é
  um veredito.
- **T004:** 26 casos novos — 17 de núcleo, 9 de tela. Os três casos reais estão presos por valor:
  9,05 cM (uma), 42,6 cM (duas) e 154,5 cM (três), este último com as distâncias exatas
  `32,5 / 34,5 / 37,5`. Se a banda mudar, o teste fica vermelho em vez de a tela mudar em silêncio.
- **T005:** suíte completa em **1574 passed, 9 skipped** (antes: 1548/9, delta de +26).
  `SHA_DA_TELA` inalterado.

## Conferência na análise real

`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`, raiz `Adriano Santos`: **68 cartões,
448 descartes** — os mesmos da 039, 040 e 043.

Dois recortes, de propósito, porque medem populações diferentes:

| Recorte | 1 destaque | 2 destaques | 3 destaques |
|---|---:|---:|---:|
| **456 kits do CSV** (todos os pares nome+kit) | 423 | 32 | 1 |
| **68 cartões da análise** (só os que casam com a árvore) | 57 | 10 | 1 |

Nenhum cartão ficou sem destaque. O único de três, nos dois recortes, é o kit `AZ4078391`
(Clezia Santos, 154,5 cM):

```
Três relações praticamente empatadas pela distância da média
 - Primos de 2º grau (1× removido) — 32,5 cM da média (122 cM) · onde procurar: bisavós e trisavós
 - Meio-primos de 2º grau          — 34,5 cM da média (120 cM) · onde procurar: bisavós (um de dois)
 - Primos de 1º grau (3× removidos) — 37,5 cM da média (117 cM) · onde procurar: avós e tetravós
Entre as 9 relações compatíveis, estas são as mais próximas da média das faixas publicadas
— e isso não é confirmação: o parentesco documental continua vindo do GEDCOM.
```

Tabela do cartão: **9 linhas**, **3 marcadas**. Nenhuma linha removida.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-code-express` | reversa |
| 2026-10-22 | Execução: 5/5 ações concluídas | reversa |
