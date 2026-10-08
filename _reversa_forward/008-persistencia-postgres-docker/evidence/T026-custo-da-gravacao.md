# T026 — Custo da gravação na análise

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T026`
> **Veredito: o critério NÃO foi atendido — `8,14×` contra o limite de `2,00×`.**
> **A falha é do critério, e não da implementação.** O registro abaixo mostra por quê.

## 1. A medição

Dentro do contêiner, com o GEDCOM e o CSV **sintéticos** que produzem duas conexões, cinco
execuções de cada lado, valendo a **menor** de cada uma:

| | Menor | Média |
|---|---|---|
| Análise **sem** persistência (`registro=None`) | **5,1 ms** | 8,7 ms |
| Análise **com** persistência | **41,5 ms** | 42,9 ms |
| **Razão** | **8,14×** | 4,9× |
| Análises gravadas | 5 de 5 — a medição não mentiu sobre o que gravou | |

**Critério do `T026`:** abaixo de `2,00×`. **Resultado: `FAIL`.**

## 2. Por que o critério está errado — e não a implementação

O `RNF de Desempenho` diz que "a gravação não pode dobrar o tempo da análise". A frase foi
escrita pensando na **análise real**, e o número medido mostra o defeito dela:

- a análise **sem** persistência leva **5,1 ms** neste fixture — cinco pessoas, dois matches.
  É um trabalho trivial, e o fixture é sintético **por exigência do Princípio I**, que proíbe
  usar o GEDCOM real do operador para medir;
- a persistência acrescenta **36,4 ms absolutos** — uma conexão, uma transação e doze `INSERT`
  por análise;
- **qualquer** trabalho de banco maior que 5 ms "dobra" uma análise de 5 ms. O critério
  transforma o tamanho do fixture em veredito sobre a feature.

O acréscimo absoluto é a informação útil, e ela é **pequena**: 36,4 ms para gravar a análise
inteira, em um valor que não depende do tamanho da árvore e sim do número de conexões. Sob a
análise real — **71 conexões**, que o `roadmap.md` §0 registra — a razão seria uma fração
disso, porque o tempo do núcleo cresce com a árvore e com o matching, e o da gravação cresce
com as conexões.

⚠️ **A medição que provaria isso não pode ser feita, e a razão é um princípio do projeto.**
O `Princípio I` proíbe usar dado real de DNA/GEDCOM em qualquer artefato, evidência ou
medição. Então a razão sobre o caso real **não é mensurável aqui** — e um critério que só pode
ser satisfeito no caso que o projeto proíbe medir não é um critério.

## 3. Hipótese de ambiente, declarada como hipótese

Os 36,4 ms incluem a ida e volta entre o contêiner da aplicação e o do banco, e no **Docker
Desktop para Windows** esse tráfego passa pela VM. Parte do custo é de rede do ambiente, e não
do banco nem do código. **Não foi medido** — separar as duas parcelas exigiria instrumentar o
`connect` e os `INSERT` por dentro, e isso não estava no escopo da ação.

## 4. O que **não** vou fazer

**Não vou ajustar o critério para bater com o resultado.** O `risk_register.md` do projeto
nomeia esse movimento como o antipadrão a evitar: *"Nunca 'ajustar o alvo para bater com a nova
implementação'".* Trocar "abaixo do dobro" por "abaixo de 10×" faria o `T026` fechar e
destruiria a única informação que ele produziu.

## 5. O que precisa acontecer para esta ação fechar

Uma decisão **de requisito**, e não de execução. Duas saídas, e a escolha é do humano:

1. **Trocar a razão por um orçamento absoluto** — por exemplo, "a gravação não acrescenta mais
   de 100 ms à análise". É verificável em fixture sintético, não depende do tamanho do fixture,
   e mede o que importa para um operador único.
2. **Definir o fixture da medição** — se a razão for mantida, ela precisa de um `n` declarado
   em que a análise seja grande o bastante para o critério ter significado. Hoje o único `n`
   real é proibido pelo Princípio I.

Até que isso seja decidido, o `T026` fica **aberto**, e a fase de polimento **para aqui** — como
manda o skill quando uma ação falha.

## 6. O que esta medição deixou de bom

- **A gravação não perde dado nem grava a menos:** 5 análises pedidas, 5 gravadas.
- **O acréscimo absoluto é conhecido**: 36,4 ms. É o número que faltava para qualquer decisão
  sobre desempenho, e é ele que a próxima rodada vai usar.
- **O `T022` mede a suíte**, e ela ficou em 43,5 s com o mesmo conjunto de 282 testes — a
  persistência não aparece no custo dos testes, porque o `T014` é pulado.
