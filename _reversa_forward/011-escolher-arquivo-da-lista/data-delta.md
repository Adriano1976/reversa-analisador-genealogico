# Data Delta: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/011-escolher-arquivo-da-lista/requirements.md`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`

## 1. O que a extração descreve, e o que esta feature toca

| Elemento extraído | Onde está descrito | O que muda |
|---|---|---|
| `ARQUIVO_ARMAZENADO` — arquivos imutáveis sob chave derivada do conteúdo | `_reversa_sdd/erd-complete.md`; `_reversa_sdd/upload-gedcom/contracts.md#2.1` | **Nada.** Nenhum arquivo é criado, movido, renomeado ou apagado |
| Chave de conteúdo como identificador de continuidade | `_reversa_sdd/domain.md#3.5`; `contracts.md#3` | **Nada.** A árvore escolhida continua viajando no mesmo campo; o CSV escolhido ganha uma referência nova, com a mesma forma |
| Banco de dados relacional (feature 008) | `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | **Nada.** Nenhum campo, tabela ou migração |
| Estado entre requisições | `_reversa_sdd/architecture.md#7` (dívida 8) | **Nada.** A lista é derivada do disco a cada renderização e nada sobrevive à requisição (`RN-05`) |
| Pasta de upload | `_reversa_sdd/inventory.md#5`; adendo `012` | **Nada.** É a **fonte de leitura** da lista; a feature só lê |

## 2. Nada é escrito, e a leitura não é de conteúdo

Esta é uma feature de **leitura**: ela não grava arquivo, não altera registro e não cria estrutura nova
em disco. A prova exigida é o inventário por `sha256` da pasta **antes e depois de percorrer todas as
telas** (`RF-08`) — idêntico.

E a leitura também **não abre arquivo**: a lista usa o nome armazenado e os atributos do sistema de
arquivos (tamanho e data). É a consequência direta de o agrupamento usar a chave que **já está no nome**
(`contracts.md#2.1`), e o que evita reler 29,2 MB a cada renderização.

| O que a listagem lê | O que ela **não** lê |
|---|---|
| O nome do arquivo (do diretório) | O conteúdo de qualquer arquivo |
| Tamanho e data (atributos do sistema de arquivos) | O GEDCOM, para saber se é GEDCOM |
| A forma do nome, pelo padrão fechado já existente | O CSV, para saber se é CSV |

## 3. O inventário que a lista vai mostrar, medido em 2026-10-09

Pasta `src/uploads`: **19 arquivos e 29.166.183 bytes**, depois do expurgo de resíduo da feature 012.

### 3.1 Aba de árvore — 8 arquivos, **7 itens**

| Item | Arquivos | Bytes | Nome exibido | Marca |
|---|---|---|---|---|
| 1 | **2** | 5.332.198 | `Arvore_Unificada_Oficial_V1_2.ged` | chave `080e7943572d2652`, grupo |
| 2 | 1 | 1.240.340 | `Backup-Arvore-Sandro-12-11-2024.ged` | chave `4ee53cbc4914fadd` |
| 3 | 1 | 30.968 | `Famílias_Sergipanas.csv.ged` | chave `94e2402671702cac` — **CSV com nome de GEDCOM** (`RN-09`) |
| 4 | 1 | 3.063.082 | `Adriano_Santos.ged` | chave `b3211a52a933fdd0` |
| 5 | 1 | 5.332.198 | `Arvore_Unificada_Oficial_V1_2.ged` | chave `c84fd7fb4201b69f` — **conteúdo diferente do item 1** |
| 6 | 1 | 3.063.082 | `Adriano_Santos.ged` | **sem chave** (`RN-10`) |
| 7 | 1 | 5.332.198 | `Arvore_Unificada_Oficial_V1_2.ged` | **sem chave** |

### 3.2 Aba de DNA — 10 arquivos, **10 itens**

| Nome exibido | Bytes | Chave | Marca |
|---|---|---|---|
| `Genealogia_Mineira.csv` | 9.466 | `0e85a4f3052e19e3` | |
| `Projetos_Genealogicos_Unificados.csv` | 136.177 | `442e5bb013a121f6` | |
| `Famílias_Sergipanas.csv` | 30.591 | `50a3dd36fea8f8bb` | conteúdo distinto dos dois abaixo |
| `Best_of_British_DNA_Gedmatch_Project.csv` | 18.952 | `555c9871570e8044` | |
| `DNA_Nordestino.csv` | 36.714 | `7d693792453770c9` | |
| `African_Brazilian_Genealogy_and_Genetics.csv` | 2.248 | `877d18ad9c6ac1e6` | |
| `Famílias_Sergipanas.csv` | 30.968 | `94e2402671702cac` | |
| `Italian_Ancestors.csv` | 2.502 | `c7bf4be4bf7c4201` | |
| `Genealogia_Paulistana.csv` | 3.309 | `d8cdd388e5b6f432` | |
| `Famílias_Sergipanas.csv` | 30.968 | — | **sem chave**, e com o **mesmo conteúdo** do item acima |

### 3.3 Fora das duas abas

`Familias Sergipanas.xlsx` (`b70889273a505a5d`, 138.024 bytes) não termina em `.ged` nem em `.csv`, então
não aparece em aba nenhuma. Continua armazenado e invisível, como hoje.

### 3.4 Alcance por referência — medido, arquivo por arquivo

A feature **oferece** tudo o que está na pasta, mas a referência só alcança o arquivo cujo nome passa na
forma fechada de `utils/validate.py:32` — a **mesma** função que `ArmazenamentoEmDisco.resolver` aplica
(`adaptadores.py:93`). Medido em 2026-10-09 por `evidence/_sonda_forma_do_nome.py`:

| Grupo | Arquivos | Alcançável por referência? |
|---|---|---|
| Chave + nome visível em ASCII | **12** | **sim** |
| Nome visível com **acento** | **3** — `50a3dd36fea8f8bb__Famílias_Sergipanas.csv`, `94e2402671702cac__Famílias_Sergipanas.csv`, `94e2402671702cac__Famílias_Sergipanas.csv.ged` | **não** |
| **Sem chave** no nome | **3** — `Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged`, `Famílias_Sergipanas.csv` | **não** |
| Chave + **espaço** no nome visível | **1** — `b70889273a505a5d__Familias Sergipanas.xlsx` (fora das abas) | **não** |

**Por aba, isso significa:** dos **7 itens** da aba de árvore, **3** não podem ser escolhidos; dos
**10 itens** da aba de DNA, também **3**. E escolher um deles responde
`Erro: Arquivo '…' não existe mais.` — **falso**: o arquivo está na pasta, e o inventário da §3 o lista.

Confirmado por execução da rota contra a pasta real, em modo somente leitura
(`evidence/_sonda_caso_negativo_real.py`), com o inventário por `sha256` **idêntico** antes e depois.

**Consequência para o desenho:** o item não pode ser oferecido como se fosse funcionar. `RN-11` e `D-11`
mandam **marcá-lo como indisponível**, com o motivo, sem escondê-lo. O defeito de raiz — o gravador
preserva acento (`validate.py:40-65`) e o resolvedor o recusa (`:32`) — é **bug próprio**, fora do escopo
desta feature.

## 4. Nomes visíveis repetidos — o efeito medido do agrupamento por chave

Este é o custo aceito na §9 da sessão de esclarecimento, e ele tem instâncias concretas:

| Nome exibido | Arquivos | Conteúdos distintos | Consequência na lista |
|---|---|---|---|
| `Arvore_Unificada_Oficial_V1_2.ged` | 3 | **2** | **2 itens** com o mesmo nome: o grupo da chave `080e…` (2 arquivos) e a chave `c84f…` (conteúdo diferente) |
| `Famílias_Sergipanas.csv` | 3 | **2** | **2 itens** com o mesmo nome: o da chave `94e2…` e o sem chave — e os dois têm o **mesmo conteúdo**, byte a byte |
| `Adriano_Santos.ged` | 2 | 1 | **1 item** só: os dois arquivos têm a mesma chave e são agrupados |

**Três consequências que o desenho precisa honrar** (decididas em `D-09` e no risco correspondente do
roadmap):

1. **O nome exibido não é único.** Tamanho e **data** são o que distingue; por isso a data é coluna
   obrigatória e a ordem é por data decrescente.
2. **O mesmo arquivo pode aparecer como dois itens.** O par `94e2402671702cac__Famílias_Sergipanas.csv`
   e `Famílias_Sergipanas.csv` tem o **mesmo `sha256`**, e a marca de "sem chave" é a única coisa que
   explica por que são dois.
3. **Um nome visível pode carregar chave vazada.** `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged`
   é um nome visível — o operador reenviou um arquivo que já tinha chave no nome. O item exibe o nome
   **sem** chave, não esse.

## 5. Banco de dados

**Nenhuma mudança.** Nenhum campo novo, nenhum removido, nenhuma migração. As seis tabelas da feature
008 ficam como estão, e nenhuma delas é lida ou escrita por esta feature.

As duas referências não resolvidas já declaradas na feature 012 (`OBS-02`: `sonda_t014.ged`) continuam
como estão — esta feature não as toca, e a lista **não** consulta o banco.

## 6. Migrações necessárias

**Nenhuma.** Não há dado novo, não há dado movido e não há formato alterado. A única "migração" é de
**estado inicial de tela**: a aplicação atual deixa de ter o estado "envie um arquivo antes de tudo",
que o legado tem (`D-06`) — e isso é divergência declarada, não migração de dados.

## 7. Registro de rastreabilidade

| Unidade do `_reversa_sdd/` | Como fica |
|---|---|
| `upload-gedcom` | Ganha um caminho de **entrada** novo para a árvore (escolher da lista), e mantém o antigo (enviar). O armazenamento não muda |
| `analise-dna` | Ganha uma **fonte** nova para o CSV (referência por nome), e mantém a antiga (arquivo). O contrato do CSV e o veredito não mudam |
| `busca-caminho` | Sem mudança: já recebia a árvore por referência |
| Persistência (feature 008) | Sem mudança; a feature não lê nem escreve o banco |
| Instrumento de paridade | Sem mudança; ganha uma medição antes e depois, e deve continuar em 100 % |
| Goldens de tela | Sem mudança (`D-05`): capturam o oráculo legado congelado |
| Pipeline de migração | **Divergência declarada**: o alvo foi desenhado sobre a tela inicial do legado, que a aplicação atual deixa de ter (`D-06`) |
