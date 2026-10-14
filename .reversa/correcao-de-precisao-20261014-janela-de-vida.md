# Correção de precisão — a janela de vida do doador de DNA

**Data:** 2026-10-14
**Tipo:** camada de **verificação** nova no núcleo e na tela. **Nenhuma regra de matching foi
alterada** — a escolha de pessoa é exatamente a mesma de antes.
**Arquivos novos:** `src/core/janela_de_vida.py`, `tests/test_janela_de_vida.py`
**Arquivos alterados:** `src/core/dna_analysis.py`, `src/templates/index.html`,
`src/assets/app.css`, `tests/test_estado_do_resultado.py`

## O caso que originou

O cartão **"Análise de conexão com Manoel da Silva Vieira — 25,4 cM — Compatível"** apresentava
"Primos de 1º grau com 7× remoção", com ancestral comum nascido em **ABT 1720**.

O kit `TG8027863` é de **Manoel Vieira da Silva, nascido em 25/01/1936** (confirmado na ficha do
GEDmatch enviada pelo operador). A árvore tem **quatro** registros com o nome "Manoel da Silva
Vieira" — 1720, 1790, 1793 e 1845 — e o motor escolheu o de **1793**: **233 anos** em 2026 para
quem doou o DNA.

## O que foi decidido, e o que foi medido antes

Medi as duas regras candidatas nos 62 cartões da análise real **antes** de escrever código:

| Regra candidata | Cartões que trocam de pessoa | Corrige | **Perde cartão** | Veredito |
|---|---|---|---|---|
| Prenome antes de sobrenomes no desempate | 3 | 1 | **1** | ❌ recusada |
| Janela de vida, **recusando** o candidato | 2 | 1 | **1** | ❌ recusada |
| **Janela de vida, avisando** | 10 marcados | 0 | **0** | ✅ adotada |

Duas descobertas mudaram a decisão:

1. **Das 10 escolhas com idade impossível, 9 não têm candidato melhor.** A árvore simplesmente
   não tem a pessoa certa — o "Manoel Vieira da Silva" casou com **1 único candidato**. Nenhuma
   regra conserta isso; a regra só pode parar de afirmar.
2. **A variante "prenome primeiro" não é ganho, é troca.** Ela corrige `Jose Vicente de Souza`
   (1815 → 1941) e **piora** `Luiza Bertolucci` (1974 → 1909), além de rejeitar a `Margarida`.
   Foi **retirada** — não vale mexer em contrato congelado (`RF-28`/`RF-29`, ADR-23) por isso.

## Os dois limiares

| Constante | Valor | Papel |
|---|---|---|
| `IDADE_IMPOSSIVEL` | **122** | Teto duro. É o recorde humano **verificado** (Jeanne Calment, 1875–1997). Acima disso não existe pessoa documentada — é dado errado, não exceção |
| `IDADE_SUSPEITA` | **105** | Aviso. Ninguém usa kit de DNA comercial habitualmente nessa idade |

**O número não é sensível**, e isso foi medido: os cartões marcados têm de **116 a 666 anos**,
então qualquer limiar entre 100 e 110 dá o mesmo resultado. O mais apertado (116 anos) está 11
anos acima do aviso e 6 abaixo do teto. Ambos são **heurísticos declarados**, no mesmo padrão do
`0.33` do Jaccard e dos limiares de prenome do selo de identidade.

## A assimetria, que é o que torna a regra segura

O teste é **`idade > limite`**: acusa quando o registro é **jovem demais** para a distância —
alguém nascido em 1673 apresentado como match de DNA. Ele **nunca** acusa um ancestral legítimo,
porque o teste é sobre o **match** (quem doou o DNA), e **não** sobre os nós do caminho.

Se fosse uma faixa estreita ("a idade tem de ficar entre X e Y"), começaria a descartar
parentesco verdadeiro. **Não é o que está aqui.**

## A âncora é o próprio dado

```
ano_de_referencia = max(ano_atual, nascimento_da_raiz + 16)
```

Ancorar só no relógio faria a mesma análise mudar de resultado em 2035. Ancorar só no nascimento
da raiz quebraria com uma raiz viva de agora. O `max` cobre os dois casos e é reproduzível.

Na árvore do operador: raiz nascida em 1976 → `1976 + 16 = 1992` < 2026 → referência **2026**.

## O resultado, medido nos 62 cartões

| Estado | Cartões |
|---|---|
| `possivel` | 39 |
| `suspeita` (106 a 122 anos) | 5 |
| `impossivel` (> 122 anos) | 8 |
| `sem_data` (fora da regra) | 10 |

Os 8 impossíveis, na tela:

| Nome no CSV | cM | Nascimento | Idade |
|---|---|---|---|
| Gracia Martins | 8,2 | 1360 | **666 anos** |
| Margarida | 21,6 | MAY 1673 | 353 |
| Mateus de Castro | 21,1 | 1673 | 353 |
| **Manoel da Silva Vieira** | **25,4** | **1793** | **233** |
| Maria Ribeiro Da Silva | 24,3 | ABT 1798 | 228 |
| JOSÉ VICENTE de Souza | 10,8 | 1815 | 211 |
| Camilla Maria de Jesus | 8,5 | ABT 1852 | 174 |
| Francisco Alves de Lima | 10,2 | 1881 | 145 |

E os 5 suspeitos: 110, 112, 115, 116 e 117 anos — todos **abaixo** do recorde verificado, e por
isso tratados como aviso, não como impossibilidade.

## O que a decisão **não** fez

- **Não descartou nenhum match.** O cartão continua com o cM, o caminho, o grafo e a
  confrontação. Descartar perderia a evidência genética por causa de uma suspeita.
- **Não tocou em `core/matching.py`.** Score, ramos A/B/C/D, Jaccard e desempate intactos.
- **Não inventou pessoa.** Os 9 cartões sem alternativa continuam sem alternativa; o que muda é
  que agora **dizem** isso.
- **Datas estimadas** (`ABT`, `BEF`, `EST`, `CAL`, `AFT`, `CIRCA`) ficam registradas como
  imprecisas, sem substituir o veredicto da idade. `ABT 1852` tem 174 anos: o estado é
  `impossivel` **e** a data é estimada — as duas informações convivem.
- **Sem data não alarma.** 10 cartões não trazem nascimento; não saber não é o mesmo que ser
  impossível, e marcar aqui ensinaria o operador a ignorar o selo.

## O aviso, como sai no cartão

> **Idade impossível para o doador do DNA.** O relatório de DNA traz "Manoel Vieira da Silva" e a
> pessoa escolhida no GEDCOM é "Manoel da Silva Vieira", com nascimento em 1793 — 233 anos em
> 2026. Nenhuma pessoa com essa idade pode ter doado DNA: ou o registro é de outra pessoa com o
> mesmo nome, ou falta o vínculo que liga o doador a esta árvore. **O parentesco abaixo é o do
> registro escolhido, e não pode ser lido como o do doador.**

E no índice, uma coluna nova **"Janela de vida"** com o selo e a idade, para o operador não
precisar abrir 62 cartões.

## O que ainda falta (não resolvido aqui)

1. **O elo 1845 → 1936.** O único candidato que a idade aprova (`@I3052bc4c@`, MAY 1845) tem
   **zero filhos** registrados na árvore. O dado da família do Manoel de 1936 — pais, esposa,
   irmão, filho — **não existe em nenhum dos três GEDCOMs** do projeto (V1, V2 e o antigo),
   e o FamilySearch não pôde ser lido sem sessão autenticada.
2. **A lista de homônimos alternativos** (sugestão 4) — o app escolhe 1 dos 4 "Manoel da Silva
   Vieira" e não mostra que havia 4. Fica para a próxima rodada.
3. **A divergência de `MRCA`** — medi: apenas **1 de 62** cartões tem divergência de 2× ou mais
   entre o `MRCA` do CSV e a árvore. É verificação fraca, ao contrário do que eu havia suposto.

## Nota de método

Três medições minhas nasceram erradas e foram corrigidas contra o comportamento observado:
o número de cartões afetados (5 → 7, por colapso de chave e reordenação), o poder discriminante
do `MRCA` (supus forte, é fraco), e a faixa etária do teste "doador plausível" (1900 e 1920
**não** são plausíveis — 126 e 106 anos). As três estão registradas nos testes com o comentário
do engano, para o próximo leitor não repetir o raciocínio.
