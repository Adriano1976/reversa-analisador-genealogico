# Correção — um prenome só não confirma identidade, e o parentesco do índice

**Data:** 2026-10-14
**Tipo:** defeito de **precisão** no eixo da identidade + **apresentação** no índice.
**Arquivos alterados:** `src/core/identidade_do_match.py`, `src/templates/index.html`,
`src/assets/app.css`, `tests/test_identidade_do_match.py`, `tests/test_estilo_da_tela.py`,
`tests/test_profundidade_do_caminho.py`, `README.md`
**Sonda:** `_reversa_bugs/_sondas-matching/pista_documental_da_margarida.py`

## De onde veio

O operador perguntou o que era, afinal, a "pista documental" que eu tinha dito que existia no
cartão da Margarida — *"se o nome que aparece no diagrama não tem nada a ver com o doador?"*

Ele estava certo, e eu tinha exagerado. A sonda mediu:

```
nome no CSV .............. "Margarida"   (uma palavra, sem sobrenome)
candidatos ............... 8, TODOS com o nome exato "Margarida"
dos 8, com caminho ....... 2  ->  1673 (12 meioses)  e  sem data (8 meioses)
escolhido ................ o de 1673
Margarida de 1673 ........ 0 cônjuges, 0 filhos  (é folha)
ancestral comum .......... João Rodrigues Caldeira (1640), EXCLUSIVO deste cartão
dos 5 filhos dele ........ só Beatriz Machado chega ao presente (117 descendentes)
                           — e essa é a linha do próprio Adriano
```

Com uma palavra só, **todo termo de semelhança da nota do matching fica igual** entre os oito
candidatos: a ordem entre eles é do **desempate congelado**, não de evidência. E a única linha
que desce daquele ancestral até hoje é a do próprio Adriano — não há linha independente por onde
um doador chamado "Margarida" pudesse estar.

Ou seja: não havia pista nenhuma. Eu chamei de "pista documental" o que é **artefato da ordenação
de candidatos**.

## O defeito que isso expôs

O cartão dizia **"identidade confirmada"**. `conferir("Margarida", "Margarida")` compara as duas
strings, são iguais, e devolve `CONFIRMADA` — sem olhar que o relatório não trouxe sobrenome
nenhum. Um casamento exato de um prenome confirma que a **palavra** é a mesma; não que a pessoa é.

### A regra, e por que NÃO é "não tem sobrenome"

A primeira formulação que eu tentei era "sem sobrenome no relatório não confirma". Ela estava
errada, e o próprio teste existente apontou: `("*Maria Natividade", "Maria Natividade")` está
declarado como `CONFIRMADA`, e `split_name_pt` chama **`natividade` de prenome** quando o nome
começa por um prenome genérico — o mesmo vale para `José Francisco Alves`, onde `alves` vira
prenome. Esses nomes **têm** parte que discrimina, e marcá-los seria transformar o aviso em ruído.

A regra adotada é por **número de palavras**: **um nome de uma palavra só não confirma.** Duas ou
mais palavras dão ao menos duas partes para confrontar, e a partir daí quem julga é
`core.matching`.

## A medição, e uma coincidência que precisou ser desfeita

```
2026-10-14, 62 cartões:  36 confirmada · 16 grafia · 10 a_confirmar
sob a regra anterior:    37 · 16 · 9        (o único movido é o Margarida)
```

O docstring do módulo já trazia "36 / 16 / 10", medidos em 2026-10-13 — e a coincidência é
**enganosa**: aqueles números foram colhidos **antes** de a busca de ancestral comum ser
corrigida, que mudou quais cartões têm caminho e, com isso, quem é a pessoa escolhida em alguns
deles. Medi de novo, escrevi a data, e deixei no docstring que os antigos coincidem por acaso e
mediam outra análise. Um número de docstring sem data é um número que mente em silêncio.

## O selo no índice

Na mesma medição apareceu a lacuna de proximidade: na linha da Margarida, o único sinal de que
aquele parentesco não é do doador ficava **duas colunas depois**, em `Janela de vida`. Quem varre
o índice lê o parentesco **antes** de chegar lá, e forma a crença no lugar errado.

Agora os 3 cartões recebem, **na mesma célula** do parentesco, o selo `não atribuível ao doador`
(com a frase inteira no `title` e o complemento no `visually-hidden`, como os outros selos).

**O rótulo não virou "Parentesco documental não encontrado"** — e essa era a proposta original do
operador. Ela alcançaria os mesmos 3 cartões, mas custaria a única comparação de cM da análise
(`TG8027863` sairia de `COMPATIVEL` para `INCONCLUSIVO`), 1 dos 5 cartões que apontam para o mesmo
ancestral, e faria o app imprimir *"nenhum caminho genealógico foi encontrado no GEDCOM"* — falso:
a árvore tem o caminho, em 11, 12 e 10 meioses. A mensagem mandaria procurar **registro faltando**
quando o trabalho é procurar **homônimo**.

## Verificação

- **955 testes, zero falhas** (943 → 955; 12 novos).
- Os 70 testes de identidade passam **sem edição**, incluindo o par `*Maria Natividade`, que a
  regra por contagem de palavras preserva.
- Medido no HTML servido pelo processo no ar, nos 62 cartões: **3** selos
  `parentesco-do-registro`; o cabeçalho da Margarida passou a `Identidade a confirmar` com a frase
  própria (*"O relatório traz um prenome só, sem sobrenome, e prenome se repete…"*), no lugar do
  silêncio de antes.
- O `SHA_DA_TELA` **não** mudou: o índice só é renderizado com resultado, e o `<script>` não foi
  tocado nesta rodada. Nenhum adendo novo foi necessário.

## Dívida declarada

O `identidade_do_match` continua comparando **duas strings**. A regra nova impede o caso mais
grosseiro (uma palavra), mas o eixo ainda não olha nada além do nome — nem pais, nem cônjuge, nem
datas. No cartão da Margarida, isso significa que o aviso existe e a escolha **continua a mesma**:
o registro de 1673, com o caminho de 12 meioses. Mudar a escolha é a camada congelada, e não foi
tocada.
