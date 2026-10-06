# Fluxograma — módulo `upload-gedcom`

> Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração, nível **completo**).
> Fontes: `src/app.py`, `src/utils/validate.py`, `src/parsers/gedcom_parser.py`, `src/core/gedcom_state.py`, `src/utils/text_cleaning.py`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## 1. Fluxo principal do upload (POST `action=upload_gedcom`)

```mermaid
flowchart TD
    A[POST / com action=upload_gedcom] --> B{campo gedcom em request.files?}
    B -- nao --> B1[Nenhum arquivo GEDCOM enviado] --> Z[render index.html success=False]
    B -- sim --> C{filename vazio?}
    C -- sim --> C1[Nenhum arquivo selecionado] --> Z
    C -- nao --> D[arquivo.read - conteudo inteiro em memoria]
    D --> E{conteudo vazio?}
    E -- sim --> E1[recusa - arquivo vazio]
    E -- nao --> F{contem byte NUL?}
    F -- sim --> F1[recusa - conteudo binario]
    F -- nao --> G[remove BOM UTF-8 e espacos a esquerda]
    G --> H{comeca com 0 HEAD?}
    H -- nao --> H1[recusa - nao comeca com a declaracao 0 HEAD]
    H -- sim --> I[chave = sha256 do conteudo, 16 hex]
    I --> J[nome final = chave + __ + nome visivel]
    J --> K{arquivo ja existe no disco?}
    K -- sim --> L[nao reescreve]
    K -- nao --> M[grava o arquivo]
    L --> N[load_gedcom_and_build_graph com o CAMINHO COMPLETO]
    M --> N
    N --> O[GedcomReader abre o arquivo]
    O --> P[INDI para people, FAM para families]
    P --> Q[grafo bidirecional pessoa-familia + child_to_family]
    Q --> R[substitui estado: clear mais update; graph reatribuido; versao mais 1]
    R --> S[lista de nomes ordenada]
    S --> T[render index.html com sucesso e a lista de nomes]
    E1 --> Z
    F1 --> Z
    H1 --> Z
    N -. excecao .-> X[Erro ao processar GEDCOM] --> Z
```

## 2. Fluxo da requisição seguinte (`gedcom_filename` vindo do formulário)

```mermaid
flowchart TD
    A[POST / com action=dna_analysis ou path_search] --> B{gedcom_filename presente?}
    B -- nao --> B1[Erro: Arquivo GEDCOM nao encontrado] --> Z[render success=False]
    B -- sim --> C{casa com ^hex16__nome?}
    C -- nao --> C1[Erro: Arquivo X nao existe mais] --> Z
    C -- sim --> D{existe no disco?}
    D -- nao --> C1
    D -- sim --> E[load_gedcom_and_build_graph]
    E --> F[segue para o fluxo do action correspondente]
```

## 3. Decisão de aceitação do conteúdo (recorte de `utils/validate.py`)

```mermaid
flowchart TD
    A[validar_conteudo_gedcom conteudo] --> B{vazio?}
    B -- sim --> B1[arquivo vazio]
    B -- nao --> C{contem 0x00?}
    C -- sim --> C1[conteudo binario]
    C -- nao --> D[remove BOM UTF-8, uma vez]
    D --> E[remove espacos a esquerda, pega os 6 primeiros bytes]
    E --> F{igual a 0 HEAD?}
    F -- nao --> F1[nao comeca com a declaracao 0 HEAD]
    F -- sim --> G[None - conteudo aceito]
```

## 4. Composição do nome de arquivo armazenado

```mermaid
flowchart LR
    A[nome enviado pelo cliente] --> B[troca barra, contrabarra e NUL por _]
    B --> C[strip de espacos e de pontos nas pontas]
    C --> D{vazio?}
    D -- sim --> D1[arvore.ged]
    D -- nao --> E{tem raiz, ponto e extensao?}
    E -- nao --> E1[nome + .ged]
    E -- sim --> F{raiz nao fica vazia?}
    F -- nao --> F1[arvore.ged]
    F -- sim --> G[raiz + . + extensao - extensao PRESERVADA]
    G --> H[chave16 + __ + nome visivel]
```

## 5. Notas de leitura

* **A validação é de conteúdo, não de extensão.** Um GEDCOM legítimo sem a extensão `.ged` é aceito; o `RISK-007` autoriza esse relaxamento justamente para não quebrar a paridade de parsing com o oráculo. 🟢
* **O nome do cliente nunca decide o caminho.** Ele vira metadado legível depois da chave; a pasta é sempre a resolvida por `_pasta_uploads()`. 🟢
* **A chave é derivada do conteúdo, e não aleatória**, porque o formulário devolve o valor no POST seguinte: a mesma árvore reenviada precisa dar a mesma chave. 🟢
* **A assimetria de substituição do estado é deliberada**: dicionários mutados *in place* para preservar os bindings importados no topo; o grafo é reatribuído, e por isso é importado dentro da função por quem o consome. 🟢
* **O contador `versao`** existe porque `id()` não muda com mutação *in place*, e índices derivados (nome normalizado para ids) precisam de um sinal de invalidação. 🟢

---

*Gerado pelo Reversa-Archaeologist em 2026-10-05.*
