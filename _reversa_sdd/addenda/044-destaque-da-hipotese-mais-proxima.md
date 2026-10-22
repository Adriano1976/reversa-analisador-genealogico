# Adendo: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/data-dictionary.md`)
> Modo: **express** — a spec fina vive em `_reversa_forward/044-destaque-da-hipotese-mais-proxima/`

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

O bloco 3 lista de **9 a 16** relações compatíveis e não dizia qual delas é o ponto de partida — por
decisão, porque a fonte não ranqueia e a 043 recusou a coluna de probabilidade. O bloco passou a
**destacar até três** relações, com uma regra declarada:

| Constante | Valor | O que faz |
|---|---|---|
| `BANDA_DE_DESTAQUE` | **1,5** | entra quem está a menos de 1,5× a distância da mais próxima |
| `MAXIMO_DE_DESTAQUES` | **3** | teto, para o destaque não virar um segundo bloco 3 |

A grandeza é a **mesma** que já ordenava a lista: `|média publicada − cM|`. Não entrou peso, soma nem
segunda medida — entrou um corte e um teto. O que o destaque mostra, no cartão da Clezia Santos
(kit `AZ4078391`, 154,5 cM):

> **Três relações praticamente empatadas pela distância da média**
> - **Primos de 2º grau (1× removido)** — 32,5 cM da média publicada (122 cM) · onde procurar: **bisavós e trisavós**
> - **Meio-primos de 2º grau** — 34,5 cM da média publicada (120 cM) · onde procurar: **bisavós (um de dois)**
> - **Primos de 1º grau (3× removidos)** — 37,5 cM da média publicada (117 cM) · onde procurar: **avós e tetravós**
>
> Entre as **9 relações compatíveis**, estas são as mais próximas da média das faixas publicadas — e
> isso **não é confirmação**: o parentesco documental continua vindo do GEDCOM.

Três freios mantêm o invariante da 043, e **os três são obrigatórios**: o rótulo fala em "média
publicada", nunca em "mais provável"; a ressalva diz **entre quantas** relações a escolha foi feita; e
a lista completa continua na tabela, com a destacada sendo uma linha dela. A tabela ganhou a
**distância da média em todas as linhas**, para a ordem da lista ser auditável fora da caixa.

**Calibração medida** no `Famílias_Sergipanas.csv`, em dois recortes de propósito — são populações
diferentes e a diferença é informação:

| Recorte | 1 destaque | 2 destaques | 3 destaques |
|---|---:|---:|---:|
| 456 kits do CSV | 423 | 32 | 1 |
| 68 cartões da análise | 57 | 10 | 1 |

A mediana de `d2/d1` é **1,88**: a segunda candidata costuma estar quase duas vezes mais longe que a
primeira. Os casos de dois são quase todos **vizinhos de uma remoção** (`4º grau` com `4º grau 1×
removido`) — exatamente o que o cM não distingue —, e o único caso de três, nos dois recortes, é o kit
`AZ4078391`.

**5 ações concluídas** (`T001`–`T005`). Suíte em **1574 passed, 9 skipped** (antes: 1548/9, delta de
+26). `SHA_DA_TELA` inalterado; 68 cartões e 448 descartes, os mesmos da 039, 040 e 043.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | O bloco 3 da resposta HTML de `POST /` (`action=dna_analysis`) ganha uma caixa de destaque antes da tabela (rótulo, itens com distância/média/onde procurar, ressalva) e a coluna da faixa passa a trazer a distância da média em **todas** as linhas |
| `_reversa_sdd/data-dictionary.md#61-bloco-de-hipótese-por-kit-possible_relationships` | §6.1 Bloco de hipótese por kit | delta-de-dados | O bloco ganha `destaque`, com `quantidade`, `rotulo`, `itens[]` e `ressalva` — `None` quando não há candidata |
| `_reversa_sdd/data-dictionary.md#62-linha-publicada-do-shared-cm-project-40` | §6.2 Linha publicada do SCP 4.0 (o **item** de `possible_relationships`) | delta-de-dados | Cada item ganha `distancia_da_media` (`\|média publicada − cM\|`, arredondada a 1 casa) e `destaque` (booleano) — aditivos; os campos da 043 não mudam e a ordenação também não |
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | §3.3 Possibilidades (Shared cM Project 4.0) | regra-alterada | Entra a **heurística do destaque**: até três relações, banda de 1,5× e teto 3, com a obrigação de o texto dizer o critério, a contagem do conjunto e negar confirmação |
| `_reversa_sdd/adrs/19-heuristicas-declaradas-como-heuristicas.md#contexto` | §Contexto — "Três números do sistema parecem publicados e não são" | regra-alterada | O inventário passa de **três** para **quatro** números: a banda de 1,5× e o teto de 3 são critério do projeto, declarados no código e no texto da tela, e a fonte não ranqueia nada |
| `_reversa_sdd/addenda/043-tabela-do-antepassado-comum.md#resumo-da-entrega` | Resumo da entrega | regra-alterada | A tabela da 043, que só ordenava, passa a **apontar** até três relações; a lista continua inteira, e a destacada continua sendo uma linha dela |

## Regras sob vigilância

- `W001` a `W005` — ver `_reversa_forward/044-destaque-da-hipotese-mais-proxima/regression-watch.md`.
  Os três primeiros são os que um futuro `/reversa` deve conferir antes de reescrever as specs: a
  banda e o teto, o destaque que **marca** sem remover, e a ressalva com as três partes.
- As cinco observações sem peso (os três casos de referência, os dois recortes da medição, o único kit
  de três destaques, a caixa sem cor de veredito e a divergência de `meioses` ainda aberta) estão no
  mesmo arquivo.

## Fontes

- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/requirements.md`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/roadmap.md`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/actions.md`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/legacy-impact.md`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/regression-watch.md`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/progress.jsonl`
- `_reversa_forward/044-destaque-da-hipotese-mais-proxima/interfaces/bloco-3-destaque.html` (mock estático)
