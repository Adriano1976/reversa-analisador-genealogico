# 033 — Medições

Data: `2026-10-19`. Ambiente: `.venv` Python 3.14.6, GEDCOMs reais em `src/uploads/`.
A sonda que produz estes números é `_reversa_sdd/parity/_probe_sugestao.py`
(`python _reversa_sdd/parity/_probe_sugestao.py <gedcom> <csv> <raiz>`); ela ficou na pasta de
sondas da paridade porque toda medição descartável do projeto mora lá.

## 1. As quatro árvores ativas, mesmo CSV (`Famílias_Sergipanas`, 56 KB), raiz `adriano`

| Árvore | Cartões | Com caminho | Recusados pela idade | Blocos de árvore sugerida | Vereditos |
|---|---:|---:|---:|---:|---|
| `..._V1_2_Tratado.ged` | 90 | 6 | 3 | 0 | 87 inconclusivos, 3 validados |
| `..._V1_2.ged` | 92 | 11 | — | 0 | 87 inconclusivos, 4 validados, 1 em conflito |
| `..._V2_tratado.ged` | 8 | 1 | — | 1 (3 gerações) | 7 inconclusivos, 1 validado |
| `Arvore-Sandro_tratado.ged` | 38 | 7 | — | **8** (1, 2, 3, 3, 3, 4, 5) | 30 inconclusivos, 4 validados, 4 em conflito |

Leitura: a árvore sugerida **não** aparece onde a documentação é funda (as duas primeiras) e
aparece onde é rasa (as duas últimas). Ela mede a **falta** de geração, não a existência de
caminho — por isso não pode aumentar a contagem de "com caminho".

## 2. Por que os 6 caminhos da `Tratado` não geram sugestão

| cM | a_up | meioses do kit | hiato |
|---:|---:|---:|---:|
| 34,5 | 9 | 4,35 | −5 |
| 31,9 | 9 | 4,41 | −5 |
| 9,8 | 8 | 5,48 | −2 |
| 6,9 | 9 | 7,51 | −2 |
| 6,7 | 9 | 7,54 | −2 |
| 6,4 | 9 | 7,57 | −1 |

`hiato = floor(meioses + 0,5) − a_up`. Negativo nos seis: a árvore documenta mais gerações do
que o cM paga.

## 3. Uma assimetria que a medição revelou

Na árvore Sandro, **1 cartão** mostra bloco de árvore sugerida e, ao mesmo tempo, é contado como
"sem caminho" pela frase antiga: o contador lê o parentesco **apresentado** (já trocado pela
janela de vida) e a cirurgia lê o **original** (`documentary_do_registro`). É a mesma assimetria
que escondia os 3 caminhos da `Tratado` — a feature `033` a torna visível na contagem.

## 4. Descartados (rejeitados antes de qualquer trabalho de grafo)

| Motivo | Nomes (`Tratado`) |
|---|---:|
| score insuficiente ou conflito de sobrenome | 274 |
| o nome não tem sobrenome | 68 |
| o sobrenome foi lido como prenome | 11 |
| sem sobrenome em comum | 7 |
| nenhum sobrenome do nome existe no GEDCOM | 5 |
| sobrenome curto demais para buscar | 1 |
| **total** | **366** |

Nenhum deles tem nó de ancoragem na árvore: a cirurgia não os alcança. É o reservatório real
(4× os cartões), mas é motor de identidade — fora de escopo por decisão registrada.
