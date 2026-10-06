# Fluxograma — módulo `busca-caminho`

> Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração, nível **completo**).
> Fontes: `src/core/path_search.py`, `path_finding.py`, `family_navigation.py`, `documentary_relationship.py`, `src/reporting/mermaid_render.py`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> **Regra do projeto:** esta busca é **documental**. Não há DNA nesta tela, e a conexão por casamento **nunca** é apresentada como parentesco consanguíneo.

## 1. Fluxo da busca (`path_search`)

```mermaid
flowchart TD
    A[POST action=path_search] --> B[resolver pessoa 1 e pessoa 2 por nome]
    B --> C{achou as duas?}
    C -- nao --> C1[Pessoa N nao encontrada] --> Z[fim com success False]
    C -- sim --> D[montar dossie de homonimos dos dois nomes]
    D --> E{ha homonimos?}
    E -- sim --> E1[testar combinacoes ate 5 de cada lado<br/>vence a primeira COM caminho]
    E -- nao --> E2[usar o par direto]
    E1 --> F[documentary_relationship]
    E2 --> F
    F --> G{tem caminho por ancestral comum?}
    G -- sim --> H[CONEXAO DIRETA<br/>mensagem ancestral comum]
    G -- nao --> I[find_indirect_path - BFS no grafo<br/>comprimindo os nos de familia]
    I --> J{achou caminho indireto?}
    J -- nao --> J1[Nenhuma conexao encontrada] --> Z2[fim com success True]
    J -- sim --> K[CONEXAO INDIRETA<br/>status affinity + aviso de afinidade]
    H --> L[texto do caminho + diagrama Mermaid + observacoes]
    K --> L
```

## 2. Caminho direto — BFS bidirecional subindo por pais

```mermaid
flowchart TD
    A[find_ancestral_path a, b, max_depth 20] --> B{a igual a b?}
    B -- sim --> B1[devolve a propria pessoa como ancestral]
    B -- nao --> C[duas fronteiras: uma de a, uma de b]
    C --> D[iteracao: expande UM nivel do lado 1]
    D --> E{algum no desta fronteira ja foi visitado pelo lado 2?}
    E -- sim --> E1[ponto de encontro: concatena os dois caminhos]
    E -- nao --> F[expande UM nivel do lado 2]
    F --> G{algum no desta fronteira ja foi visitado pelo lado 1?}
    G -- sim --> G1[ponto de encontro]
    G -- nao --> H{atingiu 20 iteracoes?}
    H -- nao --> D
    H -- sim --> H1[None - nenhum caminho dentro do teto]
```

> O teto conta **iterações de profundidade** do BFS bidirecional, e não gerações: cada iteração expande um nível de **um** dos dois lados, alternadamente. A extração anterior descrevia isso como "profundidade máxima de 20 níveis".

## 3. Caminho indireto por afinidade

```mermaid
flowchart TD
    A[find_indirect_path a, b, max_hops 40] --> B[importa graph DENTRO da funcao]
    B --> C{grafo tem os dois nos?}
    C -- nao --> C1[None]
    C -- sim --> D[nx.shortest_path - BFS nao ponderado]
    D --> E{arestas acima de 40?}
    E -- sim --> E1[None]
    E -- nao --> F[remove os nos de familia]
    F --> G{sobraram 2 ou mais pessoas?}
    G -- nao --> G1[None]
    G -- sim --> H[caminho apenas de pessoas]
    H --> I[split_path_by_marriage:<br/>primeiro par adjacente que sao conjuges]
    I --> J{achou o par?}
    J -- nao --> J1[diagrama direto, sem casal]
    J -- sim --> K[diagrama com os dois ramos<br/>e a aresta Casamento entre ancoras invisiveis]
```

## 4. Parentesco documental (`documentary_relationship`)

```mermaid
flowchart TD
    A[documentary_relationship a, b] --> B{os dois existem no GEDCOM?}
    B -- nao --> B1[status not_found + aviso pessoa_ausente]
    B -- sim --> C[find_ancestral_path com teto 20]
    C --> D{tem caminho?}
    D -- nao --> D1[status not_found + aviso sem_caminho<br/>e aviso de homonimo, se houver]
    D -- sim --> E[graus: subidas de cada lado ate o ancestral comum]
    E --> F[documentary_label: rotulo + chave canonica + meioses]
    F --> G[evidencia por salto: hop_evidence]
    G --> H{idade do genitor fora de 12 a 70?}
    H -- sim --> H1[aviso data_impossivel<br/>o vinculo NAO e invalidado]
    H -- nao --> I[enumerar todos os ancestrais comuns ate 12 niveis]
    H1 --> I
    I --> J{ha outros ancestrais comuns?}
    J -- sim --> J1[listar caminhos alternativos<br/>+ aviso caminhos_multiplos]
    J -- nao --> K{algum ancestral alcancado por mais de 1 cadeia?}
    J1 --> K
    K -- sim --> K1[aviso colapso_de_pedigree]
    K -- nao --> L{identidade ambigua?}
    K1 --> L
    L -- sim --> L1[status ambiguous + aviso homonimo]
    L -- nao --> M[resultado completo]
    L1 --> M
```

## 5. Tradução de graus em parentesco (`documentary_label`)

```mermaid
flowchart TD
    A[deg_a, deg_b] --> B{os dois zero?}
    B -- sim --> B1[SELF - a mesma pessoa]
    B -- nao --> C{um dos dois zero?}
    C -- sim --> C1[linha direta: 1 Pai/Mae, 2 Avo,<br/>n com prefixo bis repetido n-2 vezes]
    C -- nao --> D{menor grau igual a 1?}
    D -- sim --> E{maior grau igual a 1?}
    E -- sim --> E1[SIBLINGS - irmaos]
    E -- nao --> F{removidos = maior - 2 igual a 0?}
    F -- sim --> F1[AUNT_UNCLE - tio/tia]
    F -- nao --> F2[GREAT_AUNT_k - tio/tia-avo, com bis repetido]
    D -- nao --> G[grau = menor - 1; removidos = maior - menor]
    G --> H[chave gC ou gCrR; rotulo Primos de g grau<br/>com remocao]
```

## 6. Contrato de escape do rótulo Mermaid

```mermaid
flowchart TD
    A[texto do rotulo] --> B[normaliza NFC]
    B --> C[espaco inquebravel vira espaco<br/>travessao vira hifen<br/>aspas curvas viram apostrofo]
    C --> D[aspa dupla vira apostrofo]
    D --> E[quebra de linha vira espaco]
    E --> F[lista BRANCA remove o que sobra]
    F --> G[ampersand, menor e maior viram entidade]
    G --> H[rotulo seguro]
```

> A lista é **branca**, e não negra: a negra anterior era furada pela **crase**, que logo após a aspa de abertura desvia o lexer do Mermaid para markdown-string e faz o fecha-colchete nunca virar o token exigido pela gramática (`BUG-20260929-J6PQ`). A versão seguinte era estreita demais e descartava 14 caracteres sem intenção (`BUG-20261002-T4ZM`).

## 7. Notas de leitura

* **A conexão indireta é marcada como afinidade em três lugares**: o `status` vira `affinity`, o rótulo diz "Sem ancestral comum: conexão por afinidade (casamento)" e um aviso afirma em maiúsculas que não há parentesco consanguíneo. 🟢
* **Nenhuma data invalida um vínculo.** O GEDCOM manda; o sistema **registra a evidência** (`age_at_birth`, `plausible`) e **avisa**. O caso medido está no próprio código: mãe nascida 11 anos depois do filho (`@F6@`, Celso Gomes Gama n. 1961, filho de Maria Auxiliadora n. 1972) apresentado pelo legado como "conexão direta por ancestral comum". 🟢
* **Escolha de homônimos: comportamento do legado preservado, mas declarado.** Na busca de caminho, as combinações são testadas e vence a primeira com caminho (medido: "Jose Vicente de Souza" tem três registros e só um tem pais — antes a tela dizia "nenhuma conexão"); na análise de DNA, mantém-se o primeiro candidato do legado. Em ambos os casos a ambiguidade é **avisada**. 🟢
* **O teto de 20 iterações corta em silêncio** quando a árvore é mais funda: o retorno é `(None, None)`, e o aviso diz que isso **não prova** ausência de parentesco. Decisão humana de 2026-09-30: preservar a fidelidade ao legado. 🟢
* **`get_spouses` busca no registro FAMS e, se nada achar, varre todas as famílias.** A varredura só roda quando a lista por FAMS fica vazia — e é isso que faz o cônjuge de uma segunda família desaparecer quando a primeira resolve. A decisão de 2026-09-30 foi documentar como contrato explícito. 🟢

---

*Gerado pelo Reversa-Archaeologist em 2026-10-05.*
