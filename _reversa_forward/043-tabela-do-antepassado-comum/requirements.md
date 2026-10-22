# Requirements: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Modo: express
> Pasta da extração reversa: `_reversa_sdd/`

## 1. Resumo executivo

O bloco 3 lista as relações compatíveis com o cM como uma lista de nomes, e o nome é
tudo o que a lista entrega: `Primos de 2º grau (0–234 cM na fonte; média 73 cM)`. Duas
informações ficam de fora — **onde procurar o antepassado comum** e **onde o valor
observado cai dentro da faixa publicada** —, e a ordem da lista (da relação mais
próxima da média para a mais distante) nunca é declarada. O bloco passa a ser uma
tabela de quatro colunas que entrega as duas e nomeia a ordem, **sem nenhum
percentual de probabilidade**: a fonte não publica probabilidade por relação, e uma
coluna assim somaria 100% e fecharia o mundo num conjunto que o projeto recusa fechar.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | O cM vira **lista** ordenada por distância da média; a confiança é heurística do projeto; a fonte não publica mediana | 🟢 |
| `src/core/relationship_hypotheses.py` | `SCP40_ROWS` já traz `meioses`, `average` e a faixa; o payload de cada candidata é a única superfície que a tela lê | 🟢 |
| `src/core/documentary_relationship.py` (`documentary_label`) | A chave canônica de cada relação nasce dos dois graus de subida até o MRCA — a mesma grandeza que o bloco 3 precisa para dizer onde procurar | 🟢 |
| `src/templates/index.html` (bloco 3) | `<ul>` com `(faixa cM na fonte; média N cM)`; a ordem não é declarada em lugar nenhum | 🟢 |
| `_reversa_forward/040-fonte-e-cobertura-do-arquivo` | A coluna de fonte e o painel de cobertura ensinaram o cartão a dizer o que cada número é; a tabela segue a mesma régua | 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Toda relação compatível diz onde procurar o antepassado comum.** A coluna
   "Antepassado comum mais recente" traz o coletivo do grau (`bisavós`, `trisavós`,
   `avós`, `pais`). Ela é **definição de parentesco**, não dado do Shared cM Project, e
   a tela diz isso. 🟢
   - Tipo: nova.
2. **RN-02 — Profundidade diferente mostra os dois lados.** Numa relação com remoção ou
   avuncular, os dois lados não sobem o mesmo número de gerações — `2C1R` ("primo de 2º
   grau dos pais") fica a 3 de um lado e a 4 do outro. Os dois números aparecem
   (`bisavós e trisavós`, `3 e 4 gerações acima`); escolher um só seria inventar qual
   das pessoas é a raiz. 🟢
   - Tipo: nova.
3. **RN-03 — Meia-relação não é mais funda, é mais estreita.** `HALF_SIBLINGS`,
   `HALF_1C` e `HALF_2C` têm o grau do equivalente completo e a coluna diz "um de dois",
   com o detalhe de que só um dos antepassados daquele grau é compartilhado. 🟢
   - Tipo: nova.
4. **RN-04 — A posição do valor na faixa é descrição, não probabilidade.** A coluna
   "Onde o valor cai" usa cinco rótulos sobre a faixa publicada (`na ponta inferior`,
   `abaixo do centro`, `no centro`, `acima do centro`, `na ponta superior`) e uma barra
   que desenha o valor dentro do intervalo. Nenhum percentual de parentesco. 🟢
   - Tipo: nova.
5. **RN-05 — A ordem da lista passa a ser dita.** O rodapé da tabela declara "ordenado
   da relação mais próxima da média da faixa para a mais distante" — a ordenação já
   existia no núcleo e era invisível. 🟢
   - Tipo: alterada (o critério não mudou; passou a ser declarado).
6. **RN-06 — Nenhum valor sem cobertura publicada ganha tabela.** Sem candidata, o
   cartão continua com a frase "Nenhuma relação publicada cobre exatamente este valor." 🟢
   - Tipo: preservada.

## 7. Critérios de Aceitação

- O bloco 3 exibe uma tabela com as colunas `Relação`, `Faixa na fonte`, `Onde o valor
  cai` e `Antepassado comum mais recente`.
- Um cartão de 200 cM traz, na primeira linha, `Primos de 1º grau (2× removidos)`,
  `abaixo do centro`, `avós e trisavós` e `2 e 4 gerações acima`.
- A barra da faixa marca 38% para esse cartão: `(200-33)/438`.
- A tela diz que o antepassado comum não vem da fonte, e por quê.
- A palavra `Probabilidade` não aparece, e nenhuma candidata carrega chave de probabilidade.
- Um valor acima do máximo publicado (5.000 cM) não renderiza tabela.
- A suíte completa segue verde, `SHA_DA_TELA` inalterado, e nenhum cM, veredito,
  contagem ou descarte muda.

## Emendas

*(vazio)*
