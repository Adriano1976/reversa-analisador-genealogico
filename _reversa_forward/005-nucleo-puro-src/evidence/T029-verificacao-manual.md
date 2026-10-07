# T029 — verificacao manual de ponta a ponta

Servidor de producao (`waitress`) em `127.0.0.1:58037`, pelo protocolo HTTP.
Entradas: `basic.ged` e `cm_boundaries.csv` (fixtures sinteticas).

## Passo 6.2 — a raiz responde

| Item | Esperado | Medido |
| --- | --- | --- |
| Status HTTP | `200` | `200` |
| Cabecalho `Server` | `waitress` | `waitress` |
| Formulario de upload | presente | presente |

## Passo 6.3 — upload do GEDCOM

- Status HTTP: `200`
- `gedcom_filename` devolvido: `c6926bb74ce64b88__basic.ged`
- Nomes oferecidos no campo de sugestao: **7**
- Amostra: Ana Silva, Bia Oliveira, Carlos Silva, Diego Silva, Jo©Đo Silva, Lone Ranger

## Passo 6.4 — analise de DNA

- Status HTTP: `200`
- Raiz usada: `Ana Silva`
- O aviso de **lista vazia** para `cM <= 0` (AMB-023) e o teste
  que separa a fronteira; a verificacao direta esta abaixo.

| cM | Relacionamentos devolvidos |
| --- | --- |
| `0` | `[]` (lista vazia) |
| `-5` | `[]` (lista vazia) |
| `15` | ['Primos de 3º grau (1× removido), Primos de 4º grau', 'Primos de 4º/5º grau ou mais distantes'] |
| `300` | ['Primos de 1º grau (1× removido), Meios-primos, Tios-avós ↔ Sobrinhos-netos', 'Primos de 2º grau', 'Primos de 2º grau (1× removido), Primos de 3º grau'] |
| `3400` | ['Pai/Mãe ↔ Filho(a)', 'Irmãos completos'] |
| `99999` | ['Relação distante ou indeterminada'] |

- `0` e `-5` devolvem lista vazia: **SIM**
- Positivo fora de todas as faixas devolve o literal: **SIM**

## Passo 6.5 — busca de caminho

- **direto** — `Carlos Silva` -> `Ana Silva`
  - status `200`, caminho: `Carlos Silva → Jo©Đo Silva → Ana Silva`
  - marcacao de afinidade presente: nao
  - **nao** apresentado como parentesco sanguineo: sim
- **afinidade** — `Carlos Silva` -> `Bia Oliveira`
  - status `200`, caminho: `Carlos Silva → Bia Oliveira`
  - marcacao de afinidade presente: sim
  - **nao** apresentado como parentesco sanguineo: sim

## Passos 7 e 8 — varreduras estaticas

- Passo 7 (estado mutavel de modulo em `src/core/`): **nenhum**
- Passo 8 (`gedcom_parser` escreve estado ou usa `.clear()`/`.update()`): **nenhum**

## Resultado

**APROVADO** — o app sobe por `waitress`, responde `200`, serve o formulario,
aceita o GEDCOM, roda a analise de DNA, busca caminho nos dois modos, e o
nucleo nao declara estado nem escreve globais.

Servidor encerrado e porta `58037` liberada.
