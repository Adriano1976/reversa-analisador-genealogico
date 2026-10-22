# Requirements: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Modo: express
> Pasta da extração reversa: `_reversa_sdd/`

## 1. Resumo executivo

O bloco 3 lista de **9 a 16** relações compatíveis com o cM e não diz qual delas é a mais
provável — por decisão: a fonte não ranqueia e o projeto recusa reduzir o cM a um parentesco
único. Na prática o operador precisa de um ponto de partida, e a pergunta "qual delas?" ficava
sem resposta na tela. O bloco passa a **destacar até três** relações, com uma regra declarada:
entra quem está a menos de **1,5×** a distância da mais próxima, no máximo **três**.

O destaque **não** substitui a lista: as N relações continuam na tabela, a linha destacada é
uma linha dela, e o texto traz o critério, o tamanho do conjunto ("entre as 9 compatíveis") e a
negativa ("não é confirmação"). Medido nos 456 kits do arquivo real: **423 com um destaque, 32
com dois, 1 com três**.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | O cM vira **lista** ordenada por distância da média; a confiança é heurística do projeto | 🟢 |
| `src/core/relationship_hypotheses.py` | `candidatas.sort(key=lambda c: (abs(c["average"] - cm), c["name_en"]))` — a grandeza do destaque já é a que ordena | 🟢 |
| `_reversa_sdd/addenda/043-tabela-do-antepassado-comum.md` | A tabela trouxe a posição na faixa e o antepassado comum; o destaque usa as duas como texto de apoio | 🟢 |
| `src/core/relationship_hypotheses.py` (`_confianca`) | O projeto **já** declara heurísticas próprias e as rotula como tal — o destaque segue a mesma régua | 🟢 |
| Medição de 2026-10-22 (456 kits) | d2/d1 mediana **1,88**; com banda 1,5×: 423 / 32 / 1 | 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — O bloco 3 destaca até três relações.** Entram as candidatas cuja distância à média
   publicada não passa de `BANDA_DE_DESTAQUE` (1,5) vezes a menor distância, no máximo
   `MAXIMO_DE_DESTAQUES` (3). 🟢
   - Tipo: nova.
2. **RN-02 — O destaque diz o critério e o tamanho do conjunto.** O rótulo fala em "média
   publicada", nunca em "mais provável"; a ressalva diz entre quantas relações compatíveis a
   escolha foi feita. 🟢
   - Tipo: nova.
3. **RN-03 — O destaque não é conclusão.** A ressalva diz "não é confirmação" e que o parentesco
   documental continua vindo do GEDCOM. 🟢
   - Tipo: nova.
4. **RN-04 — A lista continua inteira.** Nenhuma linha é removida ou reordenada; a destacada é
   marcada na própria tabela. 🟢
   - Tipo: preservada (043).
5. **RN-05 — A distância aparece em toda linha da tabela.** A coluna da faixa passa a trazer
   "distância da média", para a ordem da lista ser auditável linha a linha e não só no destaque. 🟢
   - Tipo: nova.
6. **RN-06 — Sem candidata, sem destaque.** Um valor sem faixa publicada continua com a frase
   "Nenhuma relação publicada cobre exatamente este valor." 🟢
   - Tipo: preservada.

## 7. Critérios de Aceitação

- Um cartão de 9,05 cM exibe **uma** hipótese destacada (`Primos de 8º grau`, 1,9 cM da média) e
  o rótulo "Hipótese mais próxima da média publicada".
- Um cartão de 42,6 cM exibe **duas** (`Primos de 3º grau (1× removido)` e `Primos de 4º grau`) e
  o rótulo "Duas relações praticamente empatadas pela distância da média".
- Um cartão de 154,5 cM exibe **três** (2C1R, meio-2C e 1C3R, com 32,5 / 34,5 / 37,5 cM da média)
  e o rótulo "Três relações praticamente empatadas".
- Cada item destacado mostra a distância, a média publicada e **onde procurar** o antepassado.
- A tabela continua com as 9 linhas, e as 3 destacadas trazem a marca visual.
- A palavra `Probabilidade` não aparece.
- Um valor de 5.000 cM continua sem caixa de destaque.
- A suíte completa segue verde e nenhum cM, veredito, contagem ou descarte muda.

## Emendas

*(vazio)*
