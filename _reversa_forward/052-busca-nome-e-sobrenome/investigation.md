# Investigation: busca por nome e sobrenome

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Requirements: `_reversa_forward/052-busca-nome-e-sobrenome/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. O problema, e o que já existe

A tela não oferece busca; oferece **preenchimento assistido de três campos**. O combobox da feature 037
([`_reversa_sdd/addenda/037-redesenho-das-tres-fases.md`](../../_reversa_sdd/addenda/037-redesenho-das-tres-fases.md))
carrega a lista inteira de nomes como `application/json` no documento (`index.html#L601`), filtra no
cliente com `indexOf` sobre o nome normalizado (`index.html#L665-L669`) e mostra até 50 opções.

Três consequências medidas, e é delas que a feature nasce:

1. **A lista abre pelo teclado, não pela digitação.** O `focus` só abre se o campo já tem texto; o
   `input` só refiltra se a lista já está aberta (`index.html#L714-L721`). Do vazio, o único caminho é
   `↓`. O comportamento não é preso por teste — vive em checklist manual (`D-14`,
   `tests/test_combobox_de_nomes.py#L11-L15`).
2. **O resultado é um preenchimento, não uma resposta.** O operador não vê ficha, data, pais nem xref;
   vê um nome para escolher.
3. **O CSV não tem nada.** O relatório de matches só é alcançável pela análise de DNA completa.

## 2. Alternativas avaliadas

| Alternativa | Custo | Por que foi descartada ou aceita |
|-------------|-------|----------------------------------|
| Manter tudo no cliente, sobre `all_names` | zero de servidor | Não escala para a segunda fonte: o CSV não está na página, e trazer os dois exigiria embutir também o relatório. Também não resolve a descoberta — o campo continua sendo um preenchimento |
| Busca servida sobre a árvore carregada | um índice, já existente | **Aceita.** O mapa de nomes já é construído uma vez por árvore (`core/homonimos.py#L71-L93`) |
| Busca no PostgreSQL (LIKE/trigram) | esquema e dependência | O banco é **opcional** e guarda o histórico da análise, não a árvore (`architecture.md#4`). Buscar ali responderia sobre o retrato de análises antigas, não sobre a árvore aberta |
| Índice ordenado por prefixo (`bisect`) | barato e simples | Cobre prefixo de token, não **trecho no meio**. O combobox de hoje casa por trecho; adotar só prefixo perderia resultado sem ninguém ter pedido (`RN-09`) |
| Dicionário `token → xrefs` com varredura linear na consulta | memória do índice | **Aceito.** O número de tokens distintos é uma fração do número de pessoas; a varredura é medida na fase de execução, não suposta |

## 3. A questão do Rust — o que o projeto já tem muda a resposta

A pergunta "dá para usar uma biblioteca em Rust?" tem uma resposta factual neste projeto: **já usa uma.**

O `requirements.txt` fixa `rapidfuzz==3.14.6` e `thefuzz==0.22.1`, e o comentário do próprio arquivo
declara que o RapidFuzz é o **backend real do matching difuso** (`RISK-006`), promovido a dependência
declarada de propósito:

> "deixa-lo livre permitiria que uma instalacao nova trouxesse outra versao e mudasse o resultado da
> analise sem uma linha de codigo mudar."

RapidFuzz é biblioteca com **núcleo em Rust** e binding Python. Ou seja: a opção "usar Rust" não exige
dependência nova — exige apenas reusar o que já está instalado.

### Por que, mesmo assim, não entra nesta entrega

| Aspecto | Leitura |
|---------|---------|
| Custo de dependência | **zero** — já instalado e pinado |
| Custo de acoplamento | **real** — o pin existe para que uma instalação nova não mude o resultado da **análise**. Se a busca também depender dele, um bump de versão passa a mexer em **dois** comportamentos, e o teste de busca teria de ser revalidado junto com o de paridade da análise |
| Ganho de desempenho | **nenhum medido** — o gargalo é construir o índice (~0,9 s, uma vez por árvore), não comparar tokens; a comparação é `in` de string em Python |
| Ganho de qualidade | **condicional** — casamento aproximado só vale se o operador errar a digitação; nenhum requisito pede isso (`requirements.md#8`, "Could") |
| Biblioteca nova com núcleo compilado (extensão própria ou de terceiro) | **descartada** — wheel para o interpretador oficial, `.dockerignore` como lista de permissão e ausência de CI já produziram a `L-26` e a `L-33`; repetir o padrão sem medição seria preferência, não engenharia |

**Decisão (D-07):** o casamento da busca é stdlib e determinístico; o aproximado fica de fora. Quando
entrar, entra atrás de `EstrategiaDeCasamento` — a interface já existe para isso —, reusando o
`thefuzz` pinado e com medição. Se a medição desmentir, `difflib.SequenceMatcher` cobre o caso simples
sem dependência nenhuma.

### A fronteira que torna a pergunta irrelevante

O desenho escolhido faz a linguagem da implementação ser **detalhe de adaptador**: o domínio recebe
`Sequence[NomeDaFonte]` e devolve `ResultadoDaBusca`. Trocar a implementação do casamento por uma
extensão em Rust, por um serviço ou por SQL não muda uma linha de `core/`, de `application/` nem do
template. É exatamente o que `ports/` já é no projeto.

## 4. Padrões aplicáveis, e os recusados

| Padrão | Onde | Por que paga |
|--------|------|--------------|
| **Ports & Adapters** | `FonteDeNomes` + dois adaptadores | É o que atende "duas fontes" sem `if` de formato no domínio |
| **Strategy** | `EstrategiaDeCasamento` | Os critérios são intercambiáveis, a **ordem** é política de negócio e cada um se testa isolado |
| **Value Object** | `TermoDeBusca`, `AcertoDeBusca`, `ResultadoDaBusca` (frozen) | Impede que o termo mude no meio da consulta e torna o resultado comparável em teste |
| **Specification** | Cada estratégia responde "casa ou não" | Compor `E`/`OU` fica trivial quando aparecer |
| **Facade** | O caso de uso | Esconde duas fontes, o ranking e o truncamento atrás de uma chamada |
| *Factory* | recusado | Duas fontes se instanciam na borda; uma fábrica seria cerimônia |
| *Singleton* | recusado | O projeto removeu o último estado global de módulo na 048; reintroduzir um por conveniência seria regressão |
| *Observer* | recusado | Não há notificação: a resposta é síncrona e por requisição |
| *Command* | recusado | Uma operação, sem desfazer e sem fila |

## 5. Fontes consultadas

- `_reversa_sdd/architecture.md#1`, `#2`, `#3`, `#4` — camadas, concorrência, pacotes, modelo de dados.
- `_reversa_sdd/code-analysis.md#5.6`, `#5.7` — constantes da busca e as lacunas `L-24`/`L-25`.
- `_reversa_sdd/state-machines.md#6` — a Máquina 4 é da busca de caminho; não há máquina nova aqui.
- `_reversa_sdd/addenda/037`, `048`, `051` — combobox, índice sem colisão, escopo por dono.
- `requirements.txt` — os pins, com o comentário do `RISK-006` sobre o RapidFuzz.
- RapidFuzz (documentação oficial): <https://github.com/rapidfuzz/RapidFuzz>
- `difflib` (stdlib): <https://docs.python.org/3/library/difflib.html>
- `unicodedata` (normalização NFKD usada pelos dois normalizadores): <https://docs.python.org/3/library/unicodedata.html>
- `networkx` (atributos de grafo, usados para prender o índice): <https://networkx.org/documentation/stable/>

## 6. O que esta investigação **não** decidiu

- Se o casamento aproximado entra — depende de medição e de uso real, e o `requirements.md` o deixou
  como `Could`.
- Se o `all_names` sai do HTML — decidido que **não** nesta entrega; a remoção é a próxima, e é ela que
  traz a auditoria da busca junto (§9 do requirements).
