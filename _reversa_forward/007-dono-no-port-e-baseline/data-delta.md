# Data Delta: dono no port de armazenamento e linha de base da suíte

> Identificador: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md`,
> `_reversa_sdd/data-dictionary.md`, `_reversa_sdd/architecture.md#4`, `_reversa_sdd/domain.md#3.5`
> Requirements: `_reversa_forward/007-dono-no-port-e-baseline/requirements.md`

## 0. Veredito em uma linha

**Não há delta de dados.** Esta feature acrescenta um **parâmetro** a duas assinaturas de
porta e corrige o diretório temporário da suíte. Nenhuma estrutura de domínio é criada,
alterada, removida ou migrada; nenhum campo muda de nome ou de tipo; nada passa a ser
persistido; e o leiaute de armazenamento em disco **não muda** — o dono não entra na
chave nem no caminho, por decisão (`RN-02`).

A parte deste documento que tem conteúdo real é a §3, porque o leiaute de
armazenamento é a única coisa nesta feature que se parece com dado, e a decisão
principal dela é que ele **não** muda.

## 1. Entidades do ERD — verificação uma a uma

`_reversa_sdd/erd-complete.md` documenta 27 estruturas. Esta feature não chega perto de
nenhuma delas, e a conferência é feita contra a da feature 006 para deixar a cadeia
rastreável:

| # | Estrutura | 007 | Observação |
|---|---|---|---|
| 1 | `PESSOA` | **inalterada** | Nenhum campo tocado. O arquivo que a consome (`core/registro.py`) não é editado por esta feature |
| 2 | `FAMILIA` | **inalterada** | Idem |
| 3 | `GRAFO_BIPARTIDO` | **inalterada** | Continua `networkx.Graph` não direcionado e **sem tipo de aresta**. O conflito do Princípio IV segue herdado e declarado |
| 4 | `CHILD_TO_FAMILY` | **inalterada** | Idem |
| 5 | `ESTADO_VERSAO` | **já extinta** | Apagada pela feature 005. Registrada aqui só para a lista fechar |
| — | `DNA_MATCH` e as demais derivadas do CSV | **inalteradas** | A leitura do CSV não é tocada; `utils/validate.py` e `parsers/csv_ingest.py` não são editados |
| — | As 22 estruturas restantes do ERD | **não tocadas** | A feature não chega perto delas |

**Forma da árvore.** A tupla `Arvore = (people, families, graph, child_to_family)`
atravessa a fronteira **sem alteração**, e o `CarregadorDeArvores` continua devolvendo o
mesmo `Tree` de quatro elementos. A `RF-11` fixa isso: a assinatura de retorno do núcleo
continua congelada, e nenhum campo de desfecho entra no núcleo.

## 2. Nenhuma estrutura nova

| Candidato a estrutura nova | Veredito |
|---|---|
| O parâmetro `dono` | **Não é estrutura.** É um `str` que atravessa uma assinatura. Não tem ciclo de vida, não tem identidade própria e não sobrevive à requisição |
| Um tipo `Dono` (value object) | **Não criado.** Seria uma quarta abstração para o que hoje é uma constante de processo com valor `"unico"` — o mesmo tipo zumbi que o achado `A002` da 006 mandou remover |
| Um campo de dono em `ResultadoDeUpload` ou nos demais resultados | **Não criado.** O dono é insumo, não produto: quem o fornece é a borda, e nada na tela o exibe (`RN-03`) |
| Um campo de dono no `Tree` | **Não criado, e proibido.** O `Tree` é contrato de paridade; acrescentar campo a ele quebra o harness e nove asserções (`D-12` da 006) |

## 3. O leiaute de armazenamento — verificado item a item

Esta é a única parte da feature com aparência de dado, e a decisão central é que ela
**não muda**. Verificação contra `_reversa_sdd/domain.md#3.5`:

| Propriedade do armazenamento | Antes | Depois | Veredito |
|---|---|---|---|
| Origem da chave | `sha256` do conteúdo, truncado em 16 hex | idêntica | **inalterada** |
| Forma da referência | `<16 hex>__<nome visível>` | idêntica | **inalterada** |
| **O dono no nome ou na chave** | ausente | **ausente** | **inalterado de propósito** (`RN-02`) |
| Mesmo conteúdo enviado duas vezes | reencontra o mesmo arquivo, sem regravar | idêntico | **inalterado** (`RF-02`) |
| Extensão original | preservada | idêntica | **inalterada** |
| Teto de upload | `16 * 1024 * 1024` | idêntico | **inalterado** |
| Ordem validação → gravação | valida **antes** de escrever; recusa não deixa resíduo | idêntica | **inalterada** |
| Validação de conteúdo do GEDCOM | presente | idêntica | **inalterada** |
| Validação de conteúdo do CSV de DNA | **ausente** | **ausente** | **inalterado de propósito** (dívida #10) |
| Pasta | `src/uploads/` | idêntica | **inalterada** |

**Por que o dono fica fora, e o que isso custa.** `_reversa_sdd/domain.md#3.5` registra
que "é a chave de conteúdo que faz o papel de identificador de sessão" no legado. Pôr o
dono no caminho ou na chave faria dois envios do **mesmo conteúdo** por donos diferentes
deixarem de encontrar o mesmo arquivo — mudança de comportamento observável, quebra de
paridade e violação do Princípio II. O custo aceito é explícito: **até a Onda 3, o
armazenamento continua único por processo**, e dois operadores continuam compartilhando
os mesmos arquivos. A dívida #4 permanece aberta, e a `RN-06` proíbe declarar o contrário.

## 4. Migrações necessárias

**Nenhuma.** Não há SGBD, não há schema, não há arquivo em formato próprio.

- Sem ETL, sem backfill, sem captura de delta, sem janela de congelamento de escrita.
- Sem migration de schema: não existe schema.
- Sem conversão de arquivo: os formatos de entrada (GEDCOM, CSV de matches) não são tocados.
- **Sem renomear arquivo já gravado.** Como o dono não entra na chave, nenhum arquivo
  existente em `uploads/` precisa ser movido — e isso é sorte do desenho, não acidente:
  é consequência direta da `RN-02`. Se o dono entrasse na chave, esta seção deixaria de
  ser "nenhuma" e a feature passaria a ter migração de dados em disco.
- **Nada é removido.** A feature é aditiva em assinatura e subtrativa apenas em resíduo
  temporário de teste.

## 5. Impacto em disco

| Caminho | Efeito |
|---|---|
| `src/ports/__init__.py` | assinaturas alteradas; nenhum arquivo novo |
| `src/ports/adaptadores.py` | assinaturas alteradas; nenhum arquivo novo |
| `src/application/upload_gedcom.py` | uma linha alterada |
| `src/app.py` | dois pontos de chamada e um comentário |
| `src/uploads/` | **leiaute inalterado**. A verificação manual aponta a pasta para um diretório descartável, como na 006 |
| `tests/conftest.py` | autoridade nova do temporário da suíte |
| `tests/.tmp/` | **novo** — raiz temporária da suíte, criada em modo padrão e removida ao fim. **Não é dado do produto**: é infraestrutura de teste, vive sob `tests/**` e não é versionada. `.gitignore` está fora de `allowedPaths`, então não ganha linha de ignore nesta feature; a rede é a remoção medida em `D-03` do roadmap |
| `pytest.ini`, `.gitignore` | **não tocados** |

## 6. Delta de dívidas do modelo

| Dívida (`architecture.md#7`) | 007 | Por quê |
|---|---|---|
| #3 — contaminação entre requisições concorrentes | **INALTERADA** | A guarda continua de processo, não de thread. A `RF-04` manda a constante de dono **nomear** a dívida, e isso é registro, não conserto |
| #4 — ausência de identidade e isolamento | **INALTERADA** | O dono entra na segunda porta sem comportamento nenhum. Nenhum arquivo é separado por dono, nenhuma consulta é filtrada, nenhum `404` novo existe |
| #8 — nada é persistido entre requisições | **INALTERADA** | Persistência é a Onda 3. O re-parse por requisição continua |
| #10 — o CSV de DNA não tem validação de conteúdo | **INALTERADA, e de propósito** | O `guardar` do CSV passa a receber o dono e continua **sem** validar conteúdo. A assimetria com o GEDCOM fica declarada |
| #17 — superfícies de compatibilidade | **INALTERADA** | A `RF-12` existe exatamente para não abrir uma: o dono não tem valor padrão e não há forma alternativa de chamada |
| #18 — `cm_estimator` em disco | **INALTERADA** | Sem reexport e sem consumidor |

## 7. O que um reimplementador precisa saber

1. **Não há dado a migrar, e não há arquivo a renomear.** Qualquer documento desta
   feature que sugira backfill ou reindexação de `uploads/` está errado.
2. **O dono não é dado, é costura.** Ele atravessa `borda → caso de uso → porta` e
   **morre** na porta: não chega à chave, ao caminho, ao nome do arquivo nem à tela.
3. **A chave de conteúdo continua sendo o identificador do armazenamento.** É o que o
   legado já fazia, e é o que a Onda 3 vai ter de conviver com — ou substituir com
   migração de disco, que esta feature deliberadamente evita criar.
4. **A tupla da árvore é o contrato.** Nada nesta feature a altera.
5. **A linha de base da suíte mudou de instrumento, não de produto.** `231 aprovados +
   15 erros de ambiente` passa a `246 aprovados, 0 erros`, e os 15 não são testes novos:
   são os mesmos, que nunca executavam. Comparar totais antigos com totais novos compara
   coisas diferentes (`RN-04`).
