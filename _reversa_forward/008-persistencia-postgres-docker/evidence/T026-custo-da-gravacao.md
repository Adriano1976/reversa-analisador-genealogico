# T026 — Custo da gravação na análise

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08` · Ação: `T026`
> **Veredito: o critério FOI atendido — `1,08×` na escala representativa, contra o limite
> de `2,00×`.**
> ⚠️ **Este documento substitui uma conclusão anterior, que estava ERRADA.** A primeira
> medição deu `8,14×` e eu atribuí a falha ao critério. **Era o meu fixture.** Ver §3.

## 1. A medição, em três escalas

Dentro do contêiner, com a persistência desabilitada (`registro=None`, o estado da `D-02`)
e habilitada, valendo a **menor** de N execuções:

| Escala | Árvore | Matches | Sem | Com | Acréscimo | Razão | Veredito |
|---|---|---:|---:|---:|---:|---:|---|
| `pequena` | 5 pessoas | 2 | 5,5 ms | 44,9 ms | 39,4 ms | **8,16×** | ❌ FAIL |
| `media` | 728 pessoas | 21 | 128,2 ms | 203,0 ms | 74,8 ms | **1,58×** | ✅ **PASS** |
| `grande` | **19.682 pessoas** | **71** | 5.088,1 ms | 5.501,2 ms | **413,1 ms** | **1,08×** | ✅ **PASS** |

**Critério do `T026`:** abaixo de `2,00×`. **Atendido a partir de 728 pessoas, e com folga na
escala que corresponde ao caso real.**

## 2. Por que a escala `grande` é a que decide

O `RNF de Desempenho` fala da **análise real**: o `roadmap.md` §0 e o
`_reversa_sdd/architecture.md` §7 registram **71 conexões** sobre uma árvore de **35.460
pessoas**. O `Princípio I` **proíbe** medir com o GEDCOM real do operador.

A escala `grande` é o substituto legítimo: uma árvore **sintética** de 19.682 pessoas com
**exatamente 71 matches** — o mesmo número de conexões do caso real. Ela foi gerada por
`evidence/_gerar_fixture.py`, que constrói a árvore e o CSV do zero: nenhum byte de dado real
entrou na medição.

**O acréscimo absoluto é 413 ms** para gravar 71 conexões, com os seus 71 kits, as pessoas dos
caminhos e os descartes. É o número que importa para um operador único.

## 3. A correção: o defeito era do INSTRUMENTO, e eu o atribuí ao critério

A primeira medição usou o fixture de `tests/fixtures/sample_dna.py` — **cinco pessoas, dois
matches** — e deu `8,14×`. Concluí que o critério era inaplicável porque *"qualquer trabalho de
banco maior que 5 ms dobra uma análise de 5 ms"*.

**A frase está certa e a conclusão estava errada.** O que se seguia dela não era "o critério é
ruim", e sim **"o fixture não serve para medir isso"**. A tabela acima mostra a razão caindo de
`8,16×` para `1,08×` conforme o instrumento fica representativo — e a curva é a prova de que o
que a primeira medição mediu foi **o tamanho do fixture**, não o custo da persistência.

⚠️ **É o segundo defeito de instrumento desta feature, e os dois têm a mesma forma.** O
primeiro foi o CSV com `KIT-A`, que não exercitava o caso de dois kits e parecia defeito de
agregação (`OBS-22`). Este é o fixture pequeno demais, que parecia defeito de desempenho. Nos
dois, **um resultado convincente apontava para o lugar errado**.

**O que eu NÃO fiz, e continua valendo:** não troquei o critério por um mais frouxo. Não foi
preciso — bastou medir na escala em que o critério tem significado.

## 4. A linha `pequena` fica na tabela de propósito

Ela é o registro de por que a primeira medição enganou: com cinco pessoas a análise leva
**5,5 ms**, e nenhuma persistência caberia em 11 ms. Quem repetir esta medição com o fixture
pequeno vai ver o mesmo `8×` — e agora tem aqui a explicação, em vez de uma conclusão errada.

## 5. O instrumento, para ser reproduzível

| Arquivo | Papel |
|---|---|
| `evidence/_gerar_fixture.py` | Gera as árvores sintéticas de tamanho controlado e os CSVs de matches. Roda no host, sem Docker |
| `evidence/_t026_medir_custo.py` | Mede os três cenários dentro do contêiner, onde o driver `psycopg2` existe |
| `evidence/_tmp_e2e/arvore_media.ged`, `arvore_grande.ged` | **Gerados**, não versionados — recriáveis pelo gerador em segundos |

⚠️ **Os arquivos grandes não ficam no repositório.** O `arvore_grande.ged` tem 1,5 MB e é
inteiramente derivável do gerador; guardá-lo seria ruído. O gerador e o medidor ficam, e a
medição é reproduzível com dois comandos.

## 6. O que esta medição **não** prova

- **Que o custo é o mesmo sob carga concorrente.** A medição é serial: uma análise por vez, com
  os contêineres ociosos. Com 4 threads simultâneas o acréscimo pode ser maior, e isso **não**
  foi medido.
- **Que 413 ms é aceitável para o operador.** O critério do RNF é uma razão; se ele quer um
  orçamento absoluto, o número está aqui e a decisão é dele.
- **Onde os 413 ms são gastos.** Parte é conexão (`D-04`: uma por análise, sem pool), parte são
  os `INSERT`s, e parte é a ida e volta entre contêineres no Docker Desktop. **Não foi
  decomposto** — e a decomposição seria o próximo passo natural se o número incomodasse.
