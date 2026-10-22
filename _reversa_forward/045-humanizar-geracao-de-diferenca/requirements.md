# Requirements: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Modo: express
> Pasta da extração reversa: `_reversa_sdd/`

## 1. Resumo executivo

O bloco 3 mostrava `Primos de 2º grau (1× removido)` e `Primos de 1º grau (3× removidos)`. O termo
é jargão de quem já conhece a tabela — **removido de quê?** — e as duas formas nem concordavam entre
si: `1× removido` (singular) contra `2× removidos` (plural), e ainda `com 2× remoção` no parentesco
documental, que é um **terceiro** jeito de escrever o mesmo fato.

A tela passa a dizer **`(uma geração de diferença)`**, **`(duas gerações de diferença)`**,
**`(três gerações de diferença)`** — a tradução corrente de *once removed*, sem dicionário. E o
rótulo ganhou **fonte única**: `nome_do_primo`, usada tanto pela tabela publicada (bloco 3) quanto
pelo parentesco documental (`documentary_label`), que antes divergiam.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `src/core/relationship_hypotheses.py` (`SCP40_ROWS`) | 9 das 27 linhas traziam `(N× removido)` em `name_pt` | 🟢 |
| `src/core/documentary_relationship.py` (`documentary_label`) | Escrevia a mesma relação de outro jeito: `(1× removido)` e `com N× remoção` | 🟢 |
| `_reversa_sdd/addenda/043-tabela-do-antepassado-comum.md` | O rótulo da relação passou a ser lido na tabela e na caixa de destaque | 🟢 |
| `_reversa_sdd/addenda/044-destaque-da-hipotese-mais-proxima.md` | O destaque repete o rótulo no topo do bloco, e o jargão ficou mais visível | 🟢 |
| `src/core/validator.py` (`_meioses_totais_da_relacao`) | Lê a **chave** (`1C2R`), não o rótulo — a mudança de texto não a alcança | 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — O rótulo do primo diz "geração de diferença".** `(uma geração de diferença)`,
   `(duas gerações de diferença)`, `(três gerações de diferença)`; contagem por extenso até dez e em
   algarismo acima disso. 🟢
   - Tipo: nova.
2. **RN-02 — O rótulo tem fonte única.** `nome_do_primo(grau, removidos)` é usada pela tabela
   publicada (`SCP40_ROWS`) e pelo parentesco documental (`documentary_label`), e as duas não podem
   divergir — há teste de igualdade entre elas. 🟢
   - Tipo: nova.
3. **RN-03 — O termo `removido` não aparece na tela.** Nenhum rótulo do bloco 3 carrega `×`, e o
   texto do parentesco documental também não. 🟢
   - Tipo: nova.
4. **RN-04 — A chave canônica não muda.** `1C2R`, `2C1R` e companhia continuam iguais: é por elas que
   o confronto casa a relação documental com a tabela publicada. 🟢
   - Tipo: preservada.
5. **RN-05 — A profundidade não muda.** `(2,3)` continua com 5 meioses e a mesma chave `1C1R`; só o
   texto muda. 🟢
   - Tipo: preservada.

## 7. Critérios de Aceitação

- `documentary_label(2, 3)` devolve `Primos de 1º grau (uma geração de diferença)`.
- `documentary_label(2, 4)` devolve `Primos de 1º grau (duas gerações de diferença)`.
- `documentary_label(4, 8)` devolve `Primos de 3º grau (quatro gerações de diferença)`.
- A linha `1C2R` de `SCP40_ROWS` traz o **mesmo** texto que `documentary_label(2, 4)`.
- Nenhum rótulo do arquivo real contém `×` nem a palavra `remoção` (medido nos 456 kits).
- A chave canônica e as meioses de cada par continuam as mesmas.
- A suíte completa segue verde e nenhum cM, veredito, contagem ou descarte muda.

## Emendas

*(vazio)*
