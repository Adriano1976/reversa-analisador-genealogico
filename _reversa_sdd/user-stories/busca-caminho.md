# User Stories — Fluxo `busca-caminho`

> Re-extração de **2026-10-05** (nível **Completo**). Artefato novo: o nível `essencial` não o gerava.
> Persona única do sistema. Fontes: `busca-caminho/requirements.md`, `busca-caminho/design.md`, `domain.md` §3.1, `adrs/05`, `adrs/22`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético**, com a árvore carregada e sem autenticação. Quer responder a uma pergunta simples: **estas duas pessoas são parentes, e como?** 🟢

## História principal

> **Como** genealogista, **quero** informar dois nomes e ver **como** eles se conectam na árvore **para que** eu entenda a relação sem percorrer os registros à mão.

**Valor de negócio:** é a análise **documental** do sistema. Não há DNA nesta tela — a resposta é o que o GEDCOM afirma. 🟢

## Histórias de resultado

### US-C-01 — Conexão direta por ancestral comum

> **Como** genealogista, **quero** que o sistema suba pelos pais das duas pessoas e encontre o ancestral comum **para que** eu veja o parentesco e o caminho exato até ele.

#### Critérios de aceite

```gherkin
Dado duas pessoas com ancestral comum na árvore
Quando busco a conexão entre elas
Então a tela exibe "Conexão direta encontrada (ancestral comum)."
E o resultado traz o rótulo do parentesco, os graus e o número de meioses
E cada salto do caminho traz a família, o casal declarado e as datas que o sustentam
E um diagrama Mermaid é emitido na forma direta
```

### US-C-02 — Conexão por afinidade, marcada como tal

> **Como** genealogista, **quero** que uma conexão que passa por **casamento** seja claramente marcada assim **para que** eu não a confunda com parentesco de sangue.

**Contexto:** quando não há ancestral comum, o sistema procura um caminho no grafo de famílias — que pode passar por um casamento entre dois ramos.

#### Critérios de aceite

```gherkin
Dado duas pessoas sem ancestral comum, mas ligadas por um casamento
Quando busco a conexão entre elas
Então a tela exibe "Conexão indireta encontrada (via casamento/afinidade)."
E o status do parentesco é "affinity"
E o rótulo é "Sem ancestral comum: conexão por afinidade (casamento)"
E um aviso afirma, em maiúsculas, que aquilo NÃO representa parentesco consanguíneo
```

> A marca aparece em **três lugares** de propósito (`contracts.md` §4). O risco que ela combate é o operador ler afinidade como consanguinidade. 🟢

### US-C-03 — Homônimos não decidem em silêncio

> **Como** genealogista, **quero** que, havendo mais de um registro com o mesmo nome, o sistema **encontre a conexão** e me **avise** da ambiguidade **para que** eu possa conferir se a pessoa certa foi usada.

**Contexto:** nomes comuns repetem-se na árvore, e nem todo registro tem pais cadastrados. Antes, o sistema usava o primeiro registro e respondia "nenhuma conexão" quando **havia** conexão — pelo outro homônimo.

#### Critérios de aceite

```gherkin
Dado um nome com três registros no GEDCOM, dos quais só um tem pais
Quando busco a conexão
Então as combinações são testadas e a conexão é encontrada pelo registro com pais
E o resultado sai com status "ambiguous"
E um aviso informa quantos registros existem e pede conferência das fichas
E o aviso lista os IDs e as diferenças entre as fichas

Dado um nome gravado sem acento que existe na árvore com acento
Quando busco a conexão
Então o registro com acento é encontrado
```

### US-C-04 — Vínculo cronologicamente impossível é sinalizado, não corrigido

> **Como** genealogista, **quero** ser avisado quando o GEDCOM declara um vínculo impossível **para que** eu confira o registro — sem que o sistema "conserte" a árvore por mim.

#### Critérios de aceite

```gherkin
Dado um caminho em que o genitor declarado nasceu 11 anos depois do filho
Quando o parentesco é calculado
Então o aviso "data_impossivel" é emitido com as datas e a diferença de anos
E o vínculo NÃO é invalidado
E o caminho é exibido como o GEDCOM o declara
```

### US-C-05 — Colapso de pedigree é detectado

> **Como** genealogista, **quero** saber quando o mesmo ancestral é alcançado por mais de uma cadeia de pais **para que** eu saiba que a árvore tem colapso ou endogamia.

#### Critérios de aceite

```gherkin
Dado um par que compartilha um ancestral alcançado por mais de uma cadeia
Quando o parentesco é calculado
Então o aviso "colapso_de_pedigree" nomeia o ancestral e o número de cadeias
E o caminho principal continua sendo exibido
```

### US-C-06 — Todos os caminhos são mostrados

> **Como** genealogista, **quero** ver que existem **outros** caminhos além do principal **para que** eu não conclua que a relação é mais simples do que é.

#### Critérios de aceite

```gherkin
Dado um par ligado por mais de um percurso na árvore
Quando o parentesco é calculado
Então os caminhos alternativos são listados
E nenhum é descartado
E o aviso "caminhos_multiplos" informa quantos são
```

### US-C-07 — Nomes hostis não derrubam o diagrama

> **Como** genealogista, **quero** que nomes com aspas, crases, `&`, `<` ou `>` **não quebrem** o diagrama **para que** eu não perca a visualização por causa de um caractere no GEDCOM.

**Contexto:** o texto do nó é interpretado pela gramática do Mermaid. A sequência **aspa dupla + crase** já derrubou o diagrama inteiro (`BUG-20260929-J6PQ`).

#### Critérios de aceite

```gherkin
Dado um nome que contém aspa dupla seguida de crase
Quando o diagrama é emitido
Então o rótulo do nó é neutralizado
E o diagrama continua sendo um flowchart válido
E nenhuma aspa dupla crua ou crase sobrevive no rótulo

Dado um nome com "&", "<" ou ">"
Quando o diagrama é emitido
Então esses caracteres aparecem como entidades HTML
E acentos, pontos e parênteses legítimos sobrevivem intactos
```

### US-C-08 — "Não achei" não é erro

> **Como** genealogista, **quero** distinguir "não existe conexão" de "digitei um nome que não existe" **para que** eu saiba se o problema é a árvore ou a minha consulta.

#### Critérios de aceite

```gherkin
Dado duas pessoas existentes e nenhum caminho entre elas
Quando busco a conexão
Então a tela exibe "Nenhuma conexão encontrada entre 'X' e 'Y'."
E a resposta NÃO é apresentada como erro

Dado um nome que não existe na árvore
Quando busco a conexão
Então a tela exibe "Pessoa 1 'X' não encontrada." (ou Pessoa 2)
E a resposta É apresentada como erro
```

## O que o usuário **não** recebe — e por quê

| Ausência | Motivo | Conf. |
| --- | --- | --- |
| Aviso de que a busca foi cortada pelo limite de profundidade | Decisão humana de 2026-09-30: preservar a fidelidade ao legado. O corte é silencioso, e o aviso apenas diz que a ausência de caminho **não prova** ausência de parentesco | 🟢 |
| Cônjuges de uma segunda família, em alguns casos | A varredura global só roda quando a lista por `FAMS` fica **vazia** — contrato aceito | 🟢 |
| Checagem de datas no caminho por afinidade | A faixa de 12–70 anos só é aplicada ao caminho **direto** | 🟡 |
| Detecção de colapso além de 12 níveis / 8 cadeias | O teto existe; o silêncio é idêntico a "não há colapso" | 🟡 |
| Qualquer registro histórico das buscas | Nada é persistido | 🔴 |

## Lacunas que afetam esta história 🔴

- ✅ **`L-06` fechada** em 2026-10-05 por verificação no template: os dois casos se distinguem pela cor do alerta (por `success`) e pela presença do cartão de resultado (por `path_result`).
- **`M-01`:** o estado `affinity` é atribuído a uma **cópia** do dicionário.
- **`M-02`:** a ambiguidade rebaixa `found` para `ambiguous`, mas **não** rebaixa `not_found`.
- **`L-20`:** fichas completas por resultado (142 fichas nos 71 casos reais) e `get_children` sem índice — custo real.

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
