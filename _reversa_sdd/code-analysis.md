# Análise de Código — analisador-genealogico

> Nível de documentação: **Completo** (`state.json` → `doc_level`)
> Re-extração de **2026-10-10**. Substitui a análise de 2026-10-05, que descrevia o estado global em `core/gedcom_state.py`, o `app.py` de 262 linhas e a ausência de persistência.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Fluxogramas por módulo: `_reversa_sdd/flowcharts/` · Dicionário de dados: `_reversa_sdd/data-dictionary.md` · Dados por módulo (JSON): `.reversa/context/modules.json`

## Como ler os IDs de regra, e por que a numeração continua

Os IDs `BR-U-xx` (upload), `BR-D-xx` (DNA) e `BR-C-xx` (busca) vêm das rodadas anteriores e são **citados por artefatos que não são regerados nesta rodada** — `_reversa_forward/005-nucleo-puro-src/legacy-impact.md`, `_reversa_forward/005-.../requirements.md` e `_reversa_forward/006-fronteira-aplicacao-ports/data-delta.md`. Por isso eles **não são renumerados**:

* **regra preservada** — o ID e o sentido continuam os mesmos, com a localização reconferida;
* **regra revogada** — o ID fica registrado como revogado, e **não** é reaproveitado para outra coisa (reaproveitar faria uma citação histórica apontar para uma afirmação diferente);
* **regra nova** — recebe o ID seguinte na mesma sequência (`BR-U-21`, `BR-D-63`, `BR-C-37`, …).

Unidades que **não existiam** na rodada anterior recebem esquema próprio: `BR-T-xx` (`tela-de-entrada`) e `BR-E-xx` (`recursos-da-tela`).

**Método de contagem de linhas:** "linhas úteis" = linhas não vazias (`Get-Content | Measure-Object -Line`); "linhas cruas" = `.Count`. A diferença é declarada porque o contador ingênuo já reportou `app.py` com 227 linhas quando o arquivo tem 262 cruas / 559 úteis com o de 2026-10-10. **Localização de regra é por ARQUIVO + SÍMBOLO**, não por número de linha: a citação de linha deste artefato envelhece a cada commit, e o número de linha vivo está nos fluxogramas, reconferido na leitura.

---

## 1. Visão Geral da Escavação

| Unidade funcional | Arquivos | Linhas úteis | Regras |
| --- | --- | ---: | ---: |
| `upload-gedcom` | `application/upload_gedcom.py`, `application/reenvio.py`, `utils/validate.py`, `parsers/gedcom_parser.py`, `utils/text_cleaning.py` | 678 | 22 |
| `tela-de-entrada` | `reporting/lista_de_arquivos.py`, `app.py` (`_listas_da_tela`, `index` GET, `aposentar_arquivo`, `selecionar_arvore`, `_arvore_do_formulario`) | 512 | 19 |
| `analise-dna` | `application/dna_analysis.py`, `core/{dna_analysis,genetic_evidence,relationship_hypotheses,evidence_comparison,matching,name_normalization,registro,cm_estimator,erros}.py`, `parsers/csv_ingest.py`, `ports/*` (registro), `application/traducao.py` | 1622 | 95 |
| `busca-caminho` | `application/path_search.py`, `application/__init__.py`, `core/{path_search,path_finding,family_navigation,documentary_relationship,diagram_domain}.py`, `reporting/mermaid_render.py` | 1213 | 67 |
| `recursos-da-tela` | `app.py` (as duas rotas de arte), `src/assets/*`, `tests/{icone_de_atalho,banner_da_tela}.py` | 0 próprias | 30 |
| *Transversal* | `app.py` (montagem, servidor, `_DEPENDENCIAS`, `_REGISTRO`, filtros), `ports/__init__.py`, `utils/number_format.py` | 1615 | — |
| **Total** | **35 arquivos `.py` em `src/`** | **5130** | **233** |

> **A atribuição de arquivo a unidade é do Arqueólogo** e segue a responsabilidade declarada na docstring de cada módulo. `ports/adaptadores.py` (326 linhas) é contado na unidade que o consome com mais peso — `analise-dna` para o `RegistroDeAnalisesPostgres`, `upload-gedcom` para o armazenamento e a listagem — e está declarado como transversal na §7.
>
> 🟡 **`recursos-da-tela` tem zero linhas próprias de módulo** porque as duas rotas moram em `src/app.py`, dentro do balde transversal. Ela existe como unidade porque são **dois contratos HTTP distintos**, com regras próprias de degradação (404), cache (ETag/304), derivação de arte e contrato de teste dedicado.

**Correção de rota em relação à extração anterior.** A análise de 2026-10-05 descrevia 3 unidades, 3.489 linhas e 118 regras, e afirmava que o sistema **não tinha banco de dados**. O código de hoje tem **5 unidades, 5.130 linhas úteis e 233 regras**, um banco PostgreSQL **opcional** para o histórico das análises, uma fronteira de aplicação com quatro portas, e toda a persistência por conteúdo com aposentadoria. O que segue foi extraído do código atual.

---

## 2. Unidade `upload-gedcom`

### 2.1 Escopo e arquivos

| Arquivo | Linhas úteis | Responsabilidade |
| --- | ---: | --- |
| `src/application/upload_gedcom.py` | 104 | Caso de uso do envio: transforma o motivo em texto do armazenamento na exceção de domínio tipada. |
| `src/application/reenvio.py` | 74 | A regra de reenvio (`RN-17`): foto de antes, aposentadoria das versões anteriores e os três desfechos. |
| `src/utils/validate.py` | 197 | Autoridade única sobre o que pode ser gravado: nome visível, chave, conteúdo e forma da referência. |
| `src/parsers/gedcom_parser.py` | 76 | Traduz o GEDCOM em registros e no grafo; devolve a **árvore** como valor (`carregar_arvore`). |
| `src/utils/text_cleaning.py` | 74 | Autoridade única da limpeza de mojibake. |
| *(transversal)* `src/ports/adaptadores.py` | 326 | `ArmazenamentoEmDisco` (`guardar`, `resolver`, `listar`, `aposentar`) e `CarregadorDeArvoresGedcom`. |

Fluxo completo: `flowcharts/upload-gedcom.md`.

### 2.2 Funções principais

| Função | Arquivo | Parâmetros | Retorno |
| --- | --- | --- | --- |
| `upload_gedcom` | `application/upload_gedcom.py` | `conteudo: bytes`, `nome_original`, `dono`, `armazenamento`, `carregador` | `ResultadoDeUpload` |
| `guardar_com_substituicao` | `application/reenvio.py` | `armazenamento`, `conteudo`, `nome_original`, `tipo`, `dono` | `Armazenado` (caminho, motivo, desfecho, visível) |
| `nome_visivel_seguro` | `utils/validate.py` | `nome_original` | `str` |
| `chave_de_armazenamento` | `utils/validate.py` | `conteudo: bytes` | `str` (16 hex) |
| `nome_do_arquivo_armazenado` | `utils/validate.py` | `chave`, `nome_original` | `str` |
| `chave_recebida_e_valida` | `utils/validate.py` | `referencia` | `bool` (forma **canônica** com chave) |
| `referencia_de_arquivo_da_pasta` | `utils/validate.py` | `referencia` | `bool` (qualquer **nome** simples) |
| `pode_ser_usado` / `motivo_de_indisponibilidade` | `utils/validate.py` | `nome` | `bool` / `str \| None` |
| `validar_conteudo_gedcom` | `utils/validate.py` | `conteudo: bytes` | `str \| None` (motivo ou aceite) |
| `carregar_arvore` | `parsers/gedcom_parser.py` | `caminho: str` | `(people, families, graph, child_to_family)` |
| `strip_bad_utf` / `demojibake` | `utils/text_cleaning.py` | `s` | `str` |
| `guardar` / `resolver` / `listar` / `aposentar` | `ports/adaptadores.py` | ver `data-dictionary.md` §8.4 | `(caminho, motivo)` / `str \| None` / `list[EntradaArmazenada]` / `bool` |

### 2.3 Algoritmos e lógica não trivial

**Chave por conteúdo, e não UUID.** `sha256(conteudo).hexdigest()[:16]`. É derivada do conteúdo por uma razão de contrato: o formulário devolve `gedcom_filename` no POST seguinte, então a mesma árvore reenviada **precisa** produzir a mesma chave, e `guardar` **não sobrescreve** o que já existe. 🟢

**Validação de conteúdo estreita e deliberada.** Apenas o cabeçalho `0 HEAD` é verificado, após remover um BOM UTF-8 e espaços à esquerda. Conteúdo vazio e byte NUL têm motivo próprio. A validação é de **conteúdo**, nunca de extensão (`RISK-007`). 🟢

**A defesa contra escape passou a ser por FORMA DE NOME, e não por alfabeto fechado.** O alfabeto `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` recusava acento e espaço — que o **gravador preserva de propósito** (`RF-06`). Medido: três arquivos com acento e um com espaço estavam inalcançáveis, e a tela dizia que não existiam (`BUG-20261009-6RKP` / `RN-20`). As duas perguntas que antes eram uma agora são duas funções distintas: `_PREFIXO_CHAVE` responde "tem chave?", e `chave_recebida_e_valida` responde "posso resolver?". 🟢

**Preservação da extensão no nome visível.** `rpartition(".")` separa raiz e extensão, e a extensão é **preservada**: fixá-la em `.ged` renomeava o CSV para `<...>.csv.ged` e quebrava a análise (regressão do `BUG-20260929-QMLY`, corrigida em 2026-10-02). 🟢

**A ordem da `RN-17`: listar ANTES de guardar.** `guardar_com_substituicao` tira uma **foto de antes** (`listar`, que lê só nomes, tamanho e data) e depois grava. Só a foto separa "já existia" de "acabou de nascer", porque `guardar` não sobrescreve. Em seguida, cada versão anterior **de mesmo nome visível** é aposentada, e o desfecho é `identico`, `substituido` ou `novo`. 🟢

**Aposentar move, nunca apaga.** `os.replace` para `<pasta>/_aposentados/`, com sufixo numérico `.1`…`.99` quando já existe um aposentado com o mesmo nome, e **desistência** (`False`) depois de 99 tentativas em vez de sobrescrever. Para nomes **sem** chave o nome não carrega conteúdo, e sobrescrever apagaria outro arquivo. A subpasta fica **dentro** da pasta de upload porque `listar` já ignora subdiretório: o arquivo sai da lista sem nenhum filtro novo. 🟢

**Listar é leitura pura.** `os.listdir` + `os.stat`, e **nenhum `open`** — é o que permite montar a tela sem reler os 29 MB da pasta a cada renderização. Pasta ausente devolve lista vazia e **não** é criada: `os.makedirs` dentro de uma leitura seria efeito colateral escondido (`D-07`). 🟢

### 2.4 Regras de negócio — preservadas

| ID | Regra | Onde |
| --- | --- | --- |
| BR-U-01 | O upload só ocorre em `POST` com `action=upload_gedcom`. | `app.py:index` |
| BR-U-02 | Sem o campo `gedcom`: `Nenhum arquivo GEDCOM enviado.` | `app.py:index` |
| BR-U-03 | Com `filename` vazio: `Nenhum arquivo selecionado.` | `app.py:index` |
| BR-U-04 | O conteúdo é lido **inteiro** e validado **antes** de qualquer gravação. | `ports/adaptadores.py:guardar` |
| BR-U-05 | GEDCOM aceitável = após remover BOM UTF-8 e espaços à esquerda, começa com `0 HEAD`. | `validate.py:validar_conteudo_gedcom` |
| BR-U-06 | Conteúdo vazio é recusado com o motivo `arquivo vazio`. | idem |
| BR-U-07 | Conteúdo com byte NUL é recusado com o motivo `conteudo binario`. | idem |
| BR-U-08 | A chave é o `sha256` do conteúdo truncado em 16 hexadecimais. | `validate.py:chave_de_armazenamento` |
| BR-U-09 | O nome final é `<chave>__<nome visível>`; o nome do cliente nunca compõe o caminho. | `validate.py:nome_do_arquivo_armazenado` |
| BR-U-10 | No nome visível, `/`, `\` e NUL viram `_`; acentos, espaços e a extensão são preservados. | `validate.py:nome_visivel_seguro` |
| BR-U-11 | Nome visível vazio (ou só pontos) vira `arvore.ged`; sem extensão recebe `.ged`. | idem |
| BR-U-12 | Arquivo já existente com a mesma chave **não** é reescrito. | `ports/adaptadores.py:guardar` |
| BR-U-13 | O armazenamento devolve o **caminho completo**; quem lê depois usa exatamente o que foi escrito. | idem |
| BR-U-14 | A referência recebida do formulário é aceita pela **forma de nome** (sem separador de caminho, NUL, `.` ou `..`) **e** pela existência do arquivo; fora disso: `Erro: Arquivo 'X' não existe mais.` **REESCRITA em 2026-10-10 pelo `RN-20`** — antes exigia o alfabeto com chave. | `validate.py:chave_recebida_e_valida`, `app.py:_arvore_do_formulario` |
| BR-U-15 | Requisição sem `gedcom_filename`: `Erro: Arquivo GEDCOM não encontrado.` | `app.py:_arvore_do_formulario` |
| BR-U-16 | Corpo acima de 16 MB é recusado pelo Flask com `413` e a mensagem do teto em MB. | `app.py:TETO_DE_UPLOAD_EM_BYTES`, handler de `RequestEntityTooLarge` |
| BR-U-17 | Falha de parse vira `Erro: o arquivo 'X' não pôde ser lido como GEDCOM.` | `app.py:_arvore_do_formulario` |
| BR-U-18 | Família sem `xref_id` é ignorada; arestas só são criadas para nós existentes no grafo. | `parsers/gedcom_parser.py` |
| BR-U-19 | A lista de nomes devolvida é **ordenada** e tem exatamente um item por pessoa carregada. | `application/__init__.py:nomes_de_exibicao` |
| BR-U-20 | `get_name` devolve string vazia quando o registro tem `Name` mas o formato resulta vazio; `Sem Nome` só quando não há `name`. | `core/registro.py:get_name` |

### 2.5 Regras de negócio — novas (2026-10-10)

| ID | Regra | Onde |
| --- | --- | --- |
| BR-U-21 | O reenvio tem três desfechos com mensagem própria: `identico` (nada mudou), `substituido` (a versão anterior foi para `_aposentados/`) e `novo` (o literal congelado `Arquivo 'X' carregado!`). | `application/reenvio.py:guardar_com_substituicao` |
| BR-U-22 | Antes de aposentar, a versão nova é **gravada**; e toda versão anterior de mesmo nome visível é aposentada — podem ser **várias**, limpando o acúmulo que existia antes da `RN-17`. | idem |

### 2.6 Regra revogada

| ID | Regra | Estado |
| --- | --- | --- |
| — | `_FORMATO_CHAVE = ^[0-9a-f]{16}__[A-Za-z0-9._-]+$` como defesa única contra escape de caminho. | **REVOGADA em 2026-10-10.** O alfabeto fechado recusava acento e espaço preservados pelo gravador; a defesa passou a ser a forma de NOME, em duas funções separadas (`BR-U-14` reescrita). O símbolo `_FORMATO_CHAVE` **não existe mais** no código. |

### 2.7 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `CABECALHO_GEDCOM` | `"0 HEAD"` | `validate.py` | Declaração que abre todo GEDCOM válido. |
| `BOM_UTF8` | `b"\xef\xbb\xbf"` | `validate.py` | Removido uma única vez, no início. |
| `PASTA_DE_APOSENTADOS` | `"_aposentados"` | `ports/adaptadores.py` | Subpasta da pasta de upload. |
| `_PREFIXO_CHAVE` | `16` hexadecimais + `__` | `validate.py` | Reconhece a **presença** da chave. |
| `TETO_DE_UPLOAD_EM_BYTES` | `16 * 1024 * 1024` | `app.py` | Teto de corpo de requisição. |
| `DONO_DO_PROCESSO` | `"unico"` | `app.py` | Único lugar onde o valor do dono é declarado. **Não é mecanismo de segurança.** |
| Mapa de mojibake | 18 entradas, 17 chaves efetivas | `text_cleaning.py` | `"A�"` duplicada e `"Ã": "Ã"` é no-op. |

### 2.8 Observações e lacunas

* 🟢 **O ramo "idêntico" só existe porque a foto de antes é tirada.** Depois de `guardar`, "já existia" e "acabou de nascer" são indistinguíveis na pasta.
* 🟡 **A mensagem de "novo" usa `nome_original`, e não o nome visível seguro.** Os dois divergem quando o operador envia um nome com separador de caminho. É o literal congelado, preservado de propósito.
* 🔴 **Não há validação de conteúdo para o CSV** (`tipo == "csv"` pula `validar_conteudo_gedcom`). A assimetria é dívida preservada de propósito (`RF-10`).
* 🔴 **`dono` não participa de decisão nenhuma** nas quatro operações do armazenamento. Dívidas #3 (corrida entre requisições) e #4 (ausência de isolamento) seguem abertas.
* 🔴 **`RuntimeError("a árvore recém-gravada não pôde ser relida")` é inalcançável em execução**; existe para o checador de tipos estreitar a união do retorno.

---

## 3. Unidade `tela-de-entrada` (unidade **nova** nesta rodada)

### 3.1 Escopo e arquivos

| Arquivo | Linhas úteis | Responsabilidade |
| --- | ---: | --- |
| `src/reporting/lista_de_arquivos.py` | 168 | Funções **puras** que transformam entradas da pasta em itens de aba: agrupamento pela chave, rótulo, disponibilidade, data e tamanho. |
| `src/app.py` (`_listas_da_tela`, `index` GET, `aposentar_arquivo`, `selecionar_arvore`, `_arvore_do_formulario`) | 344 | Processador de contexto, os dois ramos de ação da lista e a resolução da árvore escolhida. |

Fluxo completo: `flowcharts/tela-de-entrada.md`.

### 3.2 Funções principais

| Função | Arquivo | Parâmetros | Retorno |
| --- | --- | --- | --- |
| `itens_da_aba` | `reporting/lista_de_arquivos.py` | `entradas`, `extensao` | `list[dict]` (itens da aba) |
| `decompor_nome_armazenado` | idem | `nome` | `(chave \| None, visível, marca)` |
| `rotulo_de_referencia` / `rotulo_limpo` | idem | `referencia` / `visível` | `str` |
| `formatar_data_br` | idem | `segundos` | `str` (célula vazia se não converter) |
| `pode_ser_usado` / `motivo_de_indisponibilidade` | `utils/validate.py` | `nome` | `bool` / `str \| None` |
| `_listas_da_tela` | `app.py` | — (processador de contexto) | `{arvores_da_lista, relatorios_da_lista}` |
| `_arvore_do_formulario` | `app.py` | — | `(referencia, arvore, erro)` |

### 3.3 Algoritmos e lógica não trivial

**As duas listas entram por processador de contexto.** A `D-04` fez o `GET /` entregar as duas abas **sempre**, e não só depois de um envio. A rota tem oito `render_template("index.html", …)`; repetir o argumento em cada um seria oito lugares para esquecer um, e o nono nasceria desatualizado. 🟢

**Não há `os.listdir` na rota.** Quem lê a pasta é a **porta**; um `listdir` na borda traria de volta o acesso a disco que a feature 006 tirou de lá. 🟢

**Agrupamento pela chave, item próprio quando não há chave.** Dois arquivos **sem** chave não podem cair no mesmo item: a chave não os alcança, e lê-los para agrupar custaria os 29 MB que a listagem evita. 🟢

**A aba é decidida pela extensão do nome visível cru.** `planilha.csv.ged` entra na aba de árvore mesmo tendo conteúdo de CSV; quem recusa é o **uso** (`D-08`). 🟢

**O item indisponível APARECE marcado, com motivo distinto.** `RN-11`/`D-11`: esconder o inalcançável tiraria do operador justamente o arquivo que ele mais quer aposentar. Há dois motivos: "sem chave" (arquivo anterior à chave por conteúdo) e "fora da forma" (acento/ espaço recusados) — dizer "sem chave" para o acentuado seria mentir sobre o motivo. 🟢

**A tela pergunta a MESMA função que o resolvedor.** `pode_ser_usado` → `chave_recebida_e_valida`: dois testes equivalentes divergem com o tempo, e a tela passaria a dizer "disponível" para um arquivo que o resolvedor recusa. 🟢

**A ordem dos ramos é a regra.** `aposentar_arquivo` vem **antes** de `_arvore_do_formulario()`, porque essa função resolve e **parseia** a árvore escolhida — e a árvore escolhida pode ser exatamente a que se está aposentando. Depois do move, o parse falharia e o operador veria "arquivo não existe mais" no lugar da confirmação. 🟢

**O ramo `selecionar_arvore` existe por um defeito medido.** Sem ele, o `action` cairia no `return` do fim de `index()`, que renderiza `index.html` **sem** `gedcom_filename`: a árvore resolvida seria descartada e o clique não faria nada (defeito medido em 2026-10-09). 🟢

### 3.4 Regras de negócio

| ID | Regra | Onde |
| --- | --- | --- |
| BR-T-01 | As duas abas com as listas são entregues em **toda** renderização da tela de entrada, por processador de contexto. | `app.py:_listas_da_tela` |
| BR-T-02 | Quem lê a pasta é a **porta** (`listar`); não há `os.listdir` na rota. | `app.py:_listas_da_tela`, `ports/adaptadores.py:listar` |
| BR-T-03 | A aba de cada arquivo é decidida pela extensão do **nome visível cru**, e não pelo conteúdo. | `reporting/lista_de_arquivos.py:itens_da_aba` |
| BR-T-04 | Arquivos com a mesma chave de conteúdo são agrupados em um item; o representante é o de maior `mtime`. | idem |
| BR-T-05 | Arquivo **sem** chave vira item próprio e **nunca** é agrupado. | idem |
| BR-T-06 | O rótulo do grupo prefere um nome visível **sem** chave, para não vazar a chave na tela. | `lista_de_arquivos.py:_rotulo_do_grupo` |
| BR-T-07 | O rótulo remove **apenas a última** extensão: `planilha.csv.ged` vira `planilha csv`. | `lista_de_arquivos.py:rotulo_limpo` |
| BR-T-08 | A ordem dos itens é `mtime` decrescente, com empate pelo nome exibido. | `lista_de_arquivos.py:itens_da_aba` |
| BR-T-09 | A data exibida vem de `os.stat` (a coluna se chama "Enviado em"); data que o sistema não converte devolve **célula vazia**, e não `500`. | `lista_de_arquivos.py:formatar_data_br` |
| BR-T-10 | A disponibilidade do item é decidida pela **mesma** função que o resolvedor usa. | `utils/validate.py:pode_ser_usado` |
| BR-T-11 | O item indisponível **aparece marcado**, com o motivo distinto para "sem chave" e "fora da forma". | `utils/validate.py:motivo_de_indisponibilidade` |
| BR-T-12 | A ação `aposentar_arquivo` é tratada **antes** da resolução da árvore do formulário. | `app.py:index` |
| BR-T-13 | Aposentar bem-sucedido responde `'ROTULO' saiu da lista. O arquivo não foi apagado: …`; o fracasso responde `Não foi possível aposentar o arquivo: ele não está mais na pasta.` | `app.py:index` |
| BR-T-14 | A ação `selecionar_arvore` renderiza o **mesmo** estado do envio: tela com `gedcom_filename` e `all_names`. | `app.py:index` |
| BR-T-15 | Referência de árvore que não resolve: `Erro: Arquivo 'ROTULO' não existe mais.` | `app.py:_arvore_do_formulario` |
| BR-T-16 | Nenhuma ação da lista escreve arquivo além do move de `aposentar`. | `app.py:index` |
| BR-T-17 | O nome visível da árvore aberta é obtido por **filtro** de template (`rotulo_do_arquivo`), não por parâmetro repetido nas **23** renderizações (medidas em 2026-10-10; **12** passam `gedcom_filename`). | `app.py:app.add_template_filter`, `index.html` |
| BR-T-18 | O rótulo exibido **não** contém a chave de conteúdo (`D-09`). | `lista_de_arquivos.py:rotulo_de_referencia` |
| BR-T-19 | A quantidade do grupo é o número de **arquivos** nele, e o tamanho exibido é a **soma** dos bytes do grupo. | `lista_de_arquivos.py:_montar_item` |

### 3.5 Observações e lacunas

* 🟢 **O instrumento de paridade não enxerga as listas.** `_reversa_sdd/parity/harness.py` substitui `render_template` por uma captura de contexto, então o processador de contexto nem chega a rodar. Acrescentar chave ao contexto é invisível para ele, **por construção** — é lacuna de cobertura do harness, não defeito.
* 🟡 **A quantidade do grupo é o número de arquivos, e não de versões úteis.** Depois de uma substituição o grupo fica com um arquivo; se o operador reenviar duas vezes o mesmo nome com conteúdos diferentes **sem** passar pela aplicação, o grupo volta a ter dois.
* 🔴 **A listagem não filtra nada, por decisão** — nem por nome, nem por extensão, nem por forma da chave. A pasta é a superfície de confiança da tela.

---

## 4. Unidade `analise-dna`

### 4.1 Escopo e arquivos

| Arquivo | Linhas úteis | Responsabilidade |
| --- | ---: | --- |
| `src/application/dna_analysis.py` | 248 | Caso de uso: chama o núcleo, **projeta** o resultado no payload da porta e registra o histórico. |
| `src/core/dna_analysis.py` | 253 | Orquestra os três eixos e monta o payload da tela. |
| `src/core/genetic_evidence.py` | 229 | Evidência genética descritiva por (nome, kit). Não conhece o GEDCOM. |
| `src/core/relationship_hypotheses.py` | 198 | cM → possibilidades, pela tabela publicada do Shared cM Project 4.0. |
| `src/core/evidence_comparison.py` | 209 | Confronto entre documento e genética: quatro estados, com o porquê. |
| `src/core/matching.py` | 155 | Índices do GEDCOM e decisão de aceitação de candidatos. |
| `src/core/name_normalization.py` | 85 | Normalização, decomposição de nomes e o vocabulário que isso usa. |
| `src/core/registro.py` | 33 | Acesso a registro puro: `get_name` e `ref_id`. **Cópia literal do oráculo.** |
| `src/core/cm_estimator.py` | 53 | **Legado fora do fluxo**, só superfície de compatibilidade. |
| `src/core/erros.py` | 77 | As cinco exceções de domínio tipadas. |
| `src/parsers/csv_ingest.py` | 192 | Leitura tolerante do CSV e a agregação legada. |
| `src/ports/__init__.py` + `adaptadores.py` (registro) | 343 + 148 | A porta `RegistroDeAnalises` e o adaptador Postgres. |
| `src/application/traducao.py` | 99 | Exceção de domínio → literal de tela e status HTTP. |

Fluxo completo: `flowcharts/analise-dna.md`.

### 4.2 Funções principais

| Função | Arquivo | Parâmetros | Retorno |
| --- | --- | --- | --- |
| `dna_analysis` (caso de uso) | `application/dna_analysis.py` | `caminho_do_csv`, `root_name`, `arvore`, `deps`, `dono`, `referencia_da_arvore`, `registro` | `ResultadoDeAnalise` |
| `projetar_analise` | idem | `resultados`, `descartados`, `mensagem`, `referencia_da_arvore`, `referencia_do_csv`, `root_name` | `AnaliseParaRegistrar` |
| `_juntar` / `_ficha` / `_pessoas` | idem | — | retrato das pessoas |
| `_papeis_do_caminho` | idem | `documentary` | `tuple[(xref, papel)]` |
| `_kits` / `_conexao` | idem | `evidence`, `comparison` / `ordinal`, `resultado` | `KitDaAnalise` / `ConexaoDaAnalise` |
| `dna_analysis` (núcleo) | `core/dna_analysis.py` | `csv_path`, `root_name`, `deps`, `arvore` | `(results_sorted, skipped, message)` |
| `_montar_diagrama` / `_observacoes` | idem | ver fluxograma | `str \| None` / `list[str]` |
| `read_csv_with_fallback` | `parsers/csv_ingest.py` | `path` | `DataFrame` (com `attrs`) |
| `detectar_separador` / `localizar_cabecalho` / `linhas_irregulares` | idem | — | `str` / `int` / `list[int]` |
| `detect_columns` / `aggregate_matches` | idem | `df`, … | `(name, cm, id, email)` / `DataFrame` |
| `detect_segment_columns` / `build_genetic_evidence` / `evidence_for` | `core/genetic_evidence.py` | `df` / `dossie`, `avisos`, `kit_key` | `dict` / `(evidencias, avisos)` / `dict` |
| `possible_relationships` / `hypotheses_for_evidence` | `core/relationship_hypotheses.py` | `total_cm` / `evidence` | `dict` / `list[dict]` |
| `row_for_key` / `rows_by_meioses` / `meioses_window` | idem | `key` / `meioses` | `dict \| None` / `list` / `dict \| None` |
| `compare` / `_avaliar_kit` / `_janela_do_documental` | `core/evidence_comparison.py` | — | `dict` |
| `build_ged_indexes` / `match_candidates` | `core/matching.py` | `arvore`, … | `(ged_index, surname_index, features)` / `(candidate_pids, reason)` |
| `norm_name` / `split_name_pt` / `surname_core_tokens` / `soft_prefix_jaccard` | `core/name_normalization.py` | — | `str` / `tuple` / `tuple` / `float` |
| `traduzir` | `application/traducao.py` | `erro: ErroDeDominio` | `RespostaDeErro` |
| `RegistroDeAnalisesPostgres.registrar` / `._escrever` | `ports/adaptadores.py` | `analise`, `dono` / `cursor`, … | `(referencia, aviso)` / `str` |
| `get_relationships_by_cm` | `core/cm_estimator.py` | `cm_value` | `list[str]` (**legado**) |

### 4.3 Algoritmos e lógica não trivial

**Três eixos que não se misturam.** `core/dna_analysis.py` passou a **orquestrar** três etapas que antes estavam misturadas: parentesco documental (não lê cM), evidência genética (não lê o GEDCOM) e confronto. A regra absoluta está na docstring: o DNA **não** altera o parentesco documental, e o cM **não** é usado sozinho para afirmar parentesco. 🟢

**Leitura tolerante em quatro frentes.** `utf-8` e, na falha, `latin-1`; separador decidido pelo cabeçalho entre `,`, `;`, TAB e `|` (nunca `csv.Sniffer`, que erra em arquivo de uma coluna); cabeçalho localizado por **moda do número de campos** com três guardas contra falsos positivos medidos; e, no erro de tokenização do pandas, **releitura** com `on_bad_lines="skip"` em vez de derrubar a análise. O que foi descartado não desaparece: vai para `df.attrs["linhas_ignoradas"]`. 🟢

**A chave da evidência é (nome, kit), nunca só o nome.** Duas linhas com o mesmo nome e kits diferentes são **duas** evidências. O sentinela `" SEM-KIT"` tem um espaço à esquerda porque `_clean` faz `strip` em todo valor do CSV — era assim que o literal `"SEM-KIT"` colidia com um kit de verdade (`E-03`). Quando há mais de um kit e não se sabe qual é a pessoa do GEDCOM, `totals.cm` é `None`: é o número honesto, e somar laboratórios produziria um valor que nenhuma das duas fontes sustenta. 🟢

**Soma de cM sem arredondamento.** O contrato está congelado em `tests/test_formatacao_cm.py` (`19.200000000000003` é o valor esperado): arredondar na acumulação quebraria a paridade contra o oráculo. 🟢

**Matching com desempate determinístico, e essa é a mudança da rodada.** O score continua `round(0.55·token_sort + 0.25·partial + 0.20·given + (8·interseção − 4·comuns), 2)`, com cinco ramos de aceitação, filtro anti-falso-positivo e penalidade de token do meio. O que mudou é o **4º critério de desempate: o menor `xref_id`**. Sem ele, empate exato nos três critérios caía na ordem de iteração de um `set` — medida como variável a cada `PYTHONHASHSEED`. É a implementação da decisão humana de 2026-10-05, e `tests/test_characterization_matching.py` a congela nas duas direções. 🟢

**Máquina de estados do confronto.** cM dentro da janela → `COMPATIVEL`; fora dela → `POSSIVEL` **apenas** quando alguma relação publicada que contém o valor tem faixa que **se sobrepõe** à janela (as distribuições se tocam e o cM não separa as leituras); caso contrário → `CONFLITANTE`. Distância em meioses **não** serve de critério, e o código registra por quê: irmãos (1613–3488) e primos de 1º grau com 1 remoção (102–980) estão a **uma** meiosa e não se sobrepõem. Sem DNA, sem caminho ou com identidade ambígua → `INCONCLUSIVO`. Com mais de um kit, o estado final é o **mais conservador**. 🟢

**Nada é inventado quando a fonte não publica.** Seis relações não são publicadas na 4.0 — justamente as mais distantes; a janela passa a ser a **envoltória** das publicadas com o mesmo número de meioses, e sem nenhuma o confronto fica `INCONCLUSIVO`. 🟢

**A projeção é pura.** `projetar_analise` lê o que o núcleo devolveu e **nada mais**: não chama o núcleo, não recalcula cM, não reordena e não formata (`D-15`). Ela é pública para poder ser exercitada **sem banco**, o que é o que sustenta os testes de projeção. O pareamento entre metadados de kit e veredito é **por índice**, e não por rótulo: é o que impede dois kits de mesmo nome — ou ambos sem kit — de trocarem o cM de um com o estado do outro. 🟢

**A persistência fica depois e fora da decisão.** `registro is None` **ou** `referencia_da_arvore` vazia ⇒ não registra (estado desabilitado, `D-02`, e a tela não muda um byte). Exceção na projeção **ou** na gravação vira **aviso**, nunca interrupção (`RN-13` vale para as duas metades): uma falha aqui seria a persistência bloqueando a análise, exatamente o que ela não pode. No adaptador, o import de `psycopg2` é **preguiçoso** e nada acontece na construção — sem isso, `import app` cairia no `.venv`, que é o interpretador oficial da suíte e da paridade. Uma conexão e **uma transação** por análise; a ordem de escrita respeita as chaves estrangeiras. 🟢

### 4.4 Regras de negócio — preservadas

| ID | Regra | Onde |
| --- | --- | --- |
| BR-D-01 | O CSV é lido como `utf-8` e, na falha, como `latin-1`. | `csv_ingest.py:read_csv_with_fallback` |
| BR-D-02 | O separador vence pela maior contagem no cabeçalho; empate fica com a vírgula. | `csv_ingest.py:detectar_separador` |
| BR-D-03 | O cabeçalho é a primeira linha com o número de campos **modal**, exigindo frequência ≥ 2, primeira linha divergente e posição entre as 10 primeiras. | `csv_ingest.py:localizar_cabecalho` |
| BR-D-04 | Linhas antes do cabeçalho são preâmbulo, reportadas à parte. | `csv_ingest.py:read_csv_with_fallback` |
| BR-D-05 | Linha com número de campos diferente **não** derruba a análise: o arquivo é relido descartando-a, e ela é reportada. | idem + `linhas_irregulares` |
| BR-D-06 | Sem nenhuma tentativa utilizável, o erro é `CsvIlegivel`, em português, listando as tentativas. | idem |
| BR-D-07 | Os nomes das colunas são normalizados com `strip`. | idem |
| BR-D-08 | Coluna de nome: `Name`/`MatchedName`/`Nome`; de cM: `cM`/`TotalCM`/`Total cM`. | `csv_ingest.py:detect_columns` |
| BR-D-09 | Coluna de ID de match: a primeira em que >30 % dos valores casam `[A-Z]{2}\d{7}`. | idem |
| BR-D-10 | Coluna de e-mail: a **última** cujo nome contém `mail`. | idem |
| BR-D-11 | O agrupamento legado soma cM por `nome normalizado + cauda` (id, e-mail ou nada), vetorizado. | `csv_ingest.py:aggregate_matches` |
| BR-D-12 | A evidência é agrupada por **(nome, kit)**; mesmo nome com kits diferentes são evidências separadas. | `genetic_evidence.py:build_genetic_evidence` |
| BR-D-13 | Sem coluna de kit, o e-mail assume o papel; sem ambos, a chave é a sentinela e sai o aviso `kit_ausente`. | idem |
| BR-D-14 | Mais de um kit para o mesmo nome gera o aviso `multiplos_kits`, e nenhum total é somado entre kits. | idem |
| BR-D-15 | O cM acumulado **não** é arredondado. | idem |
| BR-D-16 | A coluna de kit é a que tem nome casando `kit\|gedmatch\|teste\|test` com >50 % em `[A-Z]{1,3}\d{4,8}`; senão, a que tem >30 % em `[A-Z]{2}\d{7}`. | `genetic_evidence.py:detect_segment_columns` |
| BR-D-17 | O maior segmento abaixo de **15 cM** marca a evidência como fraca e gera o aviso `segmento_fraco`. | idem |
| BR-D-18 | Os segmentos são ordenados por cM decrescente; os cromossomos, por tamanho e depois por valor. | idem |
| BR-D-19 | Sem kit informado, `evidence_for` reúne os kits **sem somar** e deixa `totals.cm` como `None` quando há mais de um. | `genetic_evidence.py:evidence_for` |
| BR-D-20 | Sem evidência genética, `available: False` com o aviso `sem_evidencia`. | idem |
| BR-D-21 | cM vira **lista** de possibilidades pelo SCP 4.0; nunca um parentesco único. | `relationship_hypotheses.py:possible_relationships` |
| BR-D-22 | As candidatas são ordenadas por distância da média e, em empate, pelo nome em inglês. | idem |
| BR-D-23 | A confiança da lista é heurística do projeto: 0 → indeterminada; 1 e 2–3 → baixa; 4–6 e >6 → muito baixa. | `relationship_hypotheses.py:_confianca` |
| BR-D-24 | Valor sem cobertura publicada devolve lista vazia e a leitura de que **isso não descarta parentesco**. | `relationship_hypotheses.py:possible_relationships` |
| BR-D-25 | Seis relações não são publicadas na 4.0 e não recebem número inventado. | `relationship_hypotheses.py:SCP40_NOT_PUBLISHED` |
| BR-D-26 | Sem faixa publicada para a relação exata, a janela é a envoltória das publicadas com o mesmo número de meioses. | `relationship_hypotheses.py:meioses_window` |
| BR-D-27 | O confronto devolve sempre um de quatro estados, cada um com mensagem própria. | `evidence_comparison.py:MENSAGENS` |
| BR-D-28 | cM dentro da janela → `COMPATIVEL`. | `evidence_comparison.py:_avaliar_kit` |
| BR-D-29 | cM fora da janela → `POSSIVEL` com sobreposição de faixas; senão `CONFLITANTE`. | idem |
| BR-D-30 | Sem evidência genética → `INCONCLUSIVO`, registrando que o parentesco documental continua valendo por si. | `evidence_comparison.py:compare` |
| BR-D-31 | Com DNA e sem caminho documental → `INCONCLUSIVO`: nenhum caminho é inventado a partir do DNA. | idem |
| BR-D-32 | Identidade ambígua → `INCONCLUSIVO`, listando os homônimos. | idem |
| BR-D-33 | Sem faixa publicada (nem por meioses) → `INCONCLUSIVO`. | idem |
| BR-D-34 | Com mais de um kit, o estado final é o mais conservador (`CONFLITANTE > POSSIVEL > COMPATIVEL > INCONCLUSIVO`). | idem |
| BR-D-35 | `CONFLITANTE` recebe o rol de 12 causas; `POSSIVEL`, um subconjunto de **8** — **CORRIGIDO em 2026-10-10 pelo Revisor**: o texto dizia 9, e a medição por importação (`CAUSAS_POSSIVEIS[:1] + [3:8] + [10:]` = 1+5+2) dá **8**. | idem |
| BR-D-36 | A raiz é resolvida por substring sem diferenciar maiúsculas; ausente → `PessoaNaoEncontrada`. | `core/dna_analysis.py:dna_analysis` |
| BR-D-37 | Raiz ambígua usa o **primeiro** registro e **avisa** quantos e quais são. | idem |
| BR-D-38 | O matching recebe o cM **do kit**, nunca a soma. | idem |
| BR-D-39 | Entre os candidatos, vence o primeiro que tenha caminho documental; se nenhum tiver, o primeiro da lista. | idem |
| BR-D-40 | O dossiê de homônimos é calculado uma vez por nome, e o parentesco uma vez por pessoa. | idem |
| BR-D-41 | A ordem de apresentação é: primeiro os que têm caminho documental, depois cM decrescente. | idem |
| BR-D-42 | A mensagem final é `N conexões encontradas. M descartadas.` | idem |
| BR-D-43 | Sem nenhum resultado, os avisos do arquivo são anexados à mensagem. | idem |
| BR-D-44 | O matching exato é por `norm_name` sobre o índice de nomes do GEDCOM. | `matching.py:match_candidates` |
| BR-D-45 | Sem acerto exato, busca por sobrenome; sem nenhum, por prefixo de 3 letras. | idem |
| BR-D-46 | `score = 0.55·token_sort + 0.25·partial + 0.20·given + (8·interseção − 4·comuns)`, em 2 casas. | idem |
| BR-D-47 | O melhor candidato é escolhido por: mais sobrenomes em comum, depois melhor prenome, depois melhor score. | idem |
| BR-D-48 | Sem sobrenome em comum e sem sufixo coincidente, o candidato é descartado. | idem |
| BR-D-49 | Com ≥2 sobrenomes no CSV, exige-se Jaccard de prefixo ≥ 0,50 — e ≥ 0,33 quando o cM ≥ 150 e o prenome não é genérico. | idem |
| BR-D-50 | Prenome genérico exige ≥2 sobrenomes em comum; não genérico exige ≥1. | idem |
| BR-D-51 | Aceitação por cinco ramos alternativos, com limiares explícitos. | idem |
| BR-D-52 | Ramo adicional: prefixo de sobrenome coincidente com `given ≥ 90`, `score ≥ 86`, interseção ≥ 1. | idem |
| BR-D-53 | Tokens do meio ausentes no GEDCOM exigem `score ≥ 96` e `given ≥ 92`; o motivo da recusa é registrado. | idem |
| BR-D-54 | `norm_name`: limpa mojibake, decompõe NFKD, remove diacríticos, troca `/` e pontuação por espaço, minúsculas, colapsa espaços. | `utils/name_keys.py:norm_name` (reexportada por `name_normalization`) |
| BR-D-55 | `STOP_WORDS` = `de`, `da`, `do`, `das`, `dos`, `e`. | `name_normalization.py` |
| BR-D-56 | `GENERIC_GIVENS` = 20 prenomes comuns, com variantes acentuadas. | idem |
| BR-D-57 | `SURNAME_SUFFIXES` = `filho`, `neto`, `junior`, `júnior`, `sobrinho`. | idem |
| BR-D-58 | `COMMON_SURNAMES` = 16 entradas com `souza` duplicada (15 efetivas). | idem |
| BR-D-59 | `SURNAME_EQUIV` unifica `netto→neto` e `gouvea`/`gouvêa`/`gouvéia→gouveia`. | idem |
| BR-D-60 | O prenome é o primeiro token que não é stop word nem genérico; os sobrenomes são os **últimos 3** tokens úteis, sem genéricos, com equivalências; sufixos são separados. | idem |
| BR-D-61 | `soft_prefix_jaccard` compara prefixos de 4 quando algum lado tem token curto (≤ 4) ou terminando em ponto. | idem |
| BR-D-62 | `get_relationships_by_cm` (legado) devolve **lista**; cM ≤ 0 ou não numérico devolvem lista vazia. | `cm_estimator.py` |

### 4.5 Regras de negócio — novas (2026-10-10)

| ID | Regra | Onde |
| --- | --- | --- |
| BR-D-63 | O **4º critério de desempate é o menor `xref_id`**, tornando a escolha entre empatados independente da ordem do `set`. | `matching.py:match_candidates` |
| BR-D-64 | O resolvedor de diagrama é montado **uma vez por análise**, fora do laço de evidências. | `core/dna_analysis.py:dna_analysis` |
| BR-D-65 | As observações de um resultado são **deduplicadas** preservando a ordem: documental → genética → confronto → avisos da raiz e do arquivo. | `core/dna_analysis.py:_observacoes` |
| BR-D-66 | O diagrama só é montado quando há caminho documental; sem caminho, o campo é `None`. | `core/dna_analysis.py:_montar_diagrama` |
| BR-D-67 | `dono` está na assinatura do caso de uso e **não** participa de decisão nenhuma. | `application/dna_analysis.py` |
| BR-D-68 | A ficha **completa** vence a identificação ao juntar pessoas, e uma identificação sem nome cede lugar a uma com nome. | idem (`_juntar`) |
| BR-D-69 | Ficha sem `id` é descartada: não há pessoa sem xref. | idem (`_ficha`) |
| BR-D-70 | O papel de cada nó do caminho é **derivado**, com corte no ancestral comum; sem MRCA, o corte cai no penúltimo nó. | idem (`_papeis_do_caminho`) |
| BR-D-71 | `afinidade` **nunca** é atribuída pela projeção da análise de DNA. | idem |
| BR-D-72 | O pareamento entre metadados de kit e veredito é **por índice**, e um kit sem avaliação herda o estado final com `status_note` nulo. | idem (`_kits`) |
| BR-D-73 | A raiz do retrato é `documentary.person_a.id` da **primeira** conexão. | idem (`_pessoas`) |
| BR-D-74 | `ordinal` é a posição na ordem **apresentada**; os defaults são `INCONCLUSIVO`, `not_found` e string vazia. | idem (`_conexao`) |
| BR-D-75 | `projetar_analise` é **pura**: não reordena, não recalcula cM, não formata e não chama o núcleo. | idem |
| BR-D-76 | O motivo do descarte é transportado como **texto**, sem virar código. | `ports/__init__.py:DescartadoDaAnalise` |
| BR-D-77 | `match_file_ref` é o **nome do arquivo armazenado**, derivado do caminho do CSV. | `application/dna_analysis.py` |
| BR-D-78 | Sem registro **ou** sem referência da árvore, a análise **não** é registrada: é o estado desabilitado. | idem |
| BR-D-79 | Sem `DATABASE_URL` a borda monta registrador **nulo**. | `app.py:_REGISTRO` |
| BR-D-80 | A gravação acontece **depois** do núcleo, e nenhum módulo de `core/` conhece o registro. | `ports/__init__.py:RegistroDeAnalises` |
| BR-D-81 | Exceção na projeção **ou** na gravação vira aviso `Histórico não registrado: …`, e o resultado chega à tela. | `application/dna_analysis.py` |
| BR-D-82 | O adaptador faz **import preguiçoso** de `psycopg2`; driver ausente → aviso, nunca exceção. | `ports/adaptadores.py:RegistroDeAnalisesPostgres.registrar` |
| BR-D-83 | Nada acontece na **construção** do adaptador: não abre conexão, não valida a URL e não toca a rede. | idem (`__init__`) |
| BR-D-84 | Uma conexão por análise (sem pool) e **uma transação por análise**; o `finally` fecha a conexão. | idem |
| BR-D-85 | A ordem de escrita respeita as chaves estrangeiras: `dna_analysis` → `analysis_person` → `match_result` → `match_kit`/`match_path_node` → `skipped_match`. | idem (`_escrever`) |
| BR-D-86 | `is_affinity_anchor` é **sempre** `FALSE` na escrita da análise de DNA. | idem |
| BR-D-87 | `dono` vira a coluna `owner_id`, e **nenhuma** consulta filtra por ele. | idem |
| BR-D-88 | `aviso_de_persistencia` nulo significa "nada a avisar", e a tela não renderiza nada. | `application/dna_analysis.py:ResultadoDeAnalise` |
| BR-D-89 | A referência de CSV escolhida na **lista** tem precedência sobre o arquivo enviado, e o campo é opcional. | `app.py:index` |
| BR-D-90 | Referência de CSV que não resolve: `Erro: Arquivo 'X' não existe mais.` | idem |
| BR-D-91 | O CSV passa pela **mesma** porta do GEDCOM com `tipo="csv"` (sem validação de conteúdo) e pela **mesma** regra de reenvio. | idem + `application/reenvio.py` |
| BR-D-92 | O aviso de substituição do CSV é **acrescentado** à mensagem do resultado, nunca a substitui. | `app.py:index` |
| BR-D-93 | Erro de domínio → tabela de tradução (mensagem + status); falha inesperada → `Ocorreu um erro: {e}` com `success=False`. | `application/traducao.py`, `app.py:index` |
| BR-D-94 | As cinco exceções de domínio são **irmãs** (não uma cadeia); `ErroDeDominio` herda de `ValueError` para preservar asserções existentes. | `core/erros.py` |
| BR-D-95 | O status HTTP da tradução **não tem consumidor** nesta onda: vale só para a API nova, que não existe. | `application/traducao.py` |

### 4.6 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `SEPARADORES` | vírgula, `;`, TAB, `\|` | `csv_ingest.py` | A ordem importa no empate. |
| `LIMITE_DE_PREAMBULO` | `10` | idem | Teto de linhas antes do cabeçalho. |
| `LIMITE_SEGMENTO_FRACO` | `15.0` | `genetic_evidence.py` | **Critério do projeto**, não da fonte. |
| `SEM_KIT` | `" SEM-KIT"` | idem | O espaço à esquerda é a defesa contra colisão. |
| Regex de kit | estreito `[A-Z]{2}\d{7}` · largo `[A-Z]{1,3}\d{4,8}` · nome casando `kit\|gedmatch\|teste\|test` | idem | O largo só vale para coluna cujo nome fala de kit. |
| `SCP40_ROWS` / `SCP40_META` / `SCP40_NOT_PUBLISHED` | 27 relações / versão 4.0, março/2020, 59.714 envios / 6 relações | `relationship_hypotheses.py` | Fonte declarada, com a definição de "faixa" (1 % removido nas pontas). |
| `CAUSAS_POSSIVEIS` | 12 itens | `evidence_comparison.py` | Rol de causas; não é diagnóstico automático. |
| `STATUS_LABEL` | 4 rótulos | idem | **Também** são nomes de classe CSS no template. |
| Pesos do score / bônus | `0.55`/`0.25`/`0.20` · `+8.0`/`−4.0` | `matching.py` | Herdados do legado. |
| Limiar de cM no Jaccard | `150` | idem | Abaixo disso o limiar fica em 0,50. |
| `SHARED_CM_DATA` | 9 faixas escritas à mão | `cm_estimator.py` | **Legado fora do fluxo**, sem fonte verificável. |
| `LIMITE_DE_CADEIAS` / `MAX_DEPTH_ALTERNATIVOS` | `8` / `12` | `documentary_relationship.py` | Usados pelo colapso de pedigree. |

### 4.7 Observações e lacunas

* 🟢 **A divergência viva da rodada anterior foi FECHADA.** O `_reversa_sdd/analise-dna/` de 2026-10-05 registrava `RF-26`/`T-31` (determinismo) como decidido e **não implementado**; hoje o 4º critério existe e tem teste.
* 🟡 **A fonte do SCP 4.0 não publica mediana**, e o código registra isso: existe `average`, não `median`.
* 🟡 **A coluna "Range" da fonte exclui 1 % dos envios**, e a janela do confronto herda essa limitação.
* 🟡 **`_avaliar_kit` recebe `meioses_documental` e não o usa.** Superfície morta que convida a reintroduzir o critério por meioses.
* 🟡 **`INCONCLUSIVO` é o último da ordem de conservadorismo:** um kit sem cM utilizável não rebaixa o resultado quando outro kit é `COMPATIVEL`.
* 🟡 **Os quatro estados são também nomes de classe CSS** (`badge estado-{{ status }}`), e não há teste que compare o nome do estado com a folha de estilo.
* 🔴 **Endogamia e colapso de pedigree não são corrigidos.** O cM lido é um teto otimista nesses casos; a fonte declara a limitação e o confronto lista as duas entre as causas possíveis — mas não as detecta.
* 🔴 **Faltam justamente as relações mais distantes** (`1C4R`, `1C5R`, `1C6R`, `3C2R`, bisavôs distantes), que é onde o caso real deste repositório cai.
* 🔴 **Não há teste de caminho feliz de INSERT.** Os testes de persistência exercitam a persistência **desabilitada** e **indisponível** por desenho, porque o driver não existe no `.venv`: erro de SQL, de ordem de FK ou de tipo só apareceria no contêiner.
* 🟢 **`cm_estimator` não é consultado pelo fluxo nem pela interface**, e a superfície que o reexportava para `core/dna_analysis` saiu (`T022`).

---

## 5. Unidade `busca-caminho`

### 5.1 Escopo e arquivos

| Arquivo | Linhas úteis | Responsabilidade |
| --- | ---: | --- |
| `src/core/documentary_relationship.py` | 531 | Parentesco **documental** completo: caminho, ancestral comum, graus, homônimos, caminhos múltiplos, colapso e evidência de cada salto. |
| `src/reporting/mermaid_render.py` | 252 | Emissão do diagrama e o contrato de escape do rótulo. **Não importa `core`.** |
| `src/core/path_search.py` | 180 | Fachada do fluxo: resolve pessoas, escolhe entre homônimos, decide direto × indireto. |
| `src/core/family_navigation.py` | 119 | Resolução de pessoa por nome e navegação de parentesco. |
| `src/core/path_finding.py` | 72 | Os dois algoritmos: BFS bidirecional por pais e caminho curto no grafo. |
| `src/core/diagram_domain.py` | 62 | O **resolvedor de diagrama**: as sete consultas de domínio que o renderizador precisa. |
| `src/application/path_search.py` | 79 | Caso de uso: devolve `ResultadoDeBusca` com o **desfecho**. |
| `src/application/__init__.py` | 59 | O enum `Desfecho` e `nomes_de_exibicao`. |

Fluxo completo: `flowcharts/busca-caminho.md`.

### 5.2 Funções principais

| Função | Arquivo | Parâmetros | Retorno |
| --- | --- | --- | --- |
| `path_search` (caso de uso) | `application/path_search.py` | `person1_name`, `person2_name`, `arvore`, `deps`, `dono` | `ResultadoDeBusca` |
| `_desfecho` | idem | `dados`, `sucesso` | `Desfecho` |
| `path_search` (núcleo) | `core/path_search.py` | `person1_name`, `person2_name`, `deps`, `arvore` | `(path_result, msg, success)` |
| `_candidatos` / `_homonimos` | idem | `arvore`, `nome`, `ids_do_legado` / os dois nomes e ids | `(dossie, candidatos)` / `dict` |
| `documentary_relationship` | `core/documentary_relationship.py` | `arvore`, `a_id`, `b_id`, `homonyms` | `dict` |
| `documentary_label` | idem | `deg_a`, `deg_b` | `dict` (key, label, meioses) |
| `person_summary` / `hop_evidence` / `homonym_dossier` | idem | — | `dict` |
| `find_all_common_ancestors` | idem | `arvore`, `a_id`, `b_id`, `max_depth=12`, `limit=12` | `list[dict]` |
| `normalizar` / `parse_year` / `get_children` | idem | — | `str` / `int \| None` / `list[str]` |
| `find_person_by_name` / `get_parents` / `get_spouses` | `core/family_navigation.py` | `arvore`, … | `list[str]` |
| `are_spouses` / `split_path_by_marriage` / `pick_spouse_for_couple` / `exclude_tail` | idem | — | `bool` / `(left, right, par)` / `str \| None` / `list` |
| `find_ancestral_path` / `find_indirect_path` | `core/path_finding.py` | `arvore`, `start_id`, `end_id`, … | `(path, ancestral)` / `list[str] \| None` |
| `resolvedor_de_diagrama` | `core/diagram_domain.py` | `arvore` | `dict` de sete consultas ligadas à árvore |
| `_mermaid_sid` / `_mermaid_label` | `reporting/mermaid_render.py` | `raw` / `txt` | `str` |
| `generate_mermaid_graph` / `generate_mermaid_graph_indirect_bridge` | idem | `path`, `p1`, `p2`, `mrca`, `dominio` / `p1`, `p2`, `person_path`, `dominio` | `str` (Mermaid) |

### 5.3 Algoritmos e lógica não trivial

**BFS bidirecional por pais.** Duas fronteiras sobem por `get_parents`, e a cada iteração **um** nível de **um** dos lados é expandido, alternadamente. O encontro é o nó já visitado pelo outro lado, e o caminho é a concatenação sem repetir o ponto de encontro. O teto é de **20 iterações**, e não de gerações. 🟢

**Caminho indireto com compressão de famílias.** `nx.shortest_path` (BFS não ponderado) sobre o grafo bipartido, com teto de **40 arestas**; depois os nós de família são removidos, e sobram só pessoas. O grafo vem da **árvore recebida** — o import tardio que existia por causa do rebind de global não existe mais. 🟢

**Escolha entre homônimos por até 5×5 combinações.** O dossiê compara nomes **sem acento** e com correção de mojibake, porque `find_person_by_name` compara com acento e um nome sem acento não acharia o registro GEDCOM. Medido no GEDCOM real: "Jose Vicente de Souza" tem três registros e **só um** tem pais — antes, a tela respondia "nenhuma conexão" para uma conexão que o GEDCOM contém. 🟢

**Tradução de graus em parentesco.** `documentary_label` converte (subidas de A, subidas de B) na chave canônica (que depois casa com a tabela do SCP 4.0) e em **meioses** — os saltos pai-filho entre as duas pessoas, que é a grandeza que o cM mede. 🟢

**Evidência de cada salto, com idade implícita.** Idade de genitor fora de **12–70** marca `plausible: False` e gera o aviso `data_impossivel`, **sem invalidar o vínculo**. O caso medido está no próprio código: mãe nascida 11 anos depois do filho. 🟢

**Colapso de pedigree por contagem de cadeias**, com teto de 8 — e o aviso declara a consequência no cM. 🟢

**O contrato de domínio do renderizador.** `reporting/mermaid_render.py` **não importa `core`**: recebe `dominio`, o mapeamento de sete consultas devolvido por `resolvedor_de_diagrama`, já ligadas à árvore por `functools.partial`. Isso fechou o ciclo `core/` ↔ `reporting/` **sem** mover as decisões de layout — que continuam no renderizador, porque decidir o casal do ancestral comum é decisão de negócio (`ADR-11`). O renderizador continua chamando `get_spouses(pid)`, e não `get_spouses(arvore, pid)`. 🟢

**Subgrafo com fechamento garantido.** O `end` de cada `subgraph` do diagrama indireto é escrito pelo fim de um `contextmanager`: um `end` a mais ou a menos muda a árvore do diagrama **sem levantar erro nenhum** (`OPP-20260929-H2YY`). 🟢

**O desfecho da busca em três valores.** O núcleo sinaliza três estados, e os três viram tela de formas diferentes. Sem o enum, o adaptador teria de distinguir "pessoa não encontrada" (erro) de "nenhuma conexão encontrada" (cartão, **com sucesso**) pelo **texto** da mensagem — dando ao literal de tela autoridade semântica, que é o que a `RF-20` proíbe. 🟢

### 5.4 Regras de negócio — preservadas

| ID | Regra | Onde |
| --- | --- | --- |
| BR-C-01 | A pessoa é resolvida por nome: match **exato** sem diferenciar maiúsculas; sem exato, por **substring**. | `family_navigation.py:find_person_by_name` |
| BR-C-02 | Os pais vêm do `FAMC`; sem `FAMC`, do índice `child_to_family`. Duplicados são removidos. | `family_navigation.py:get_parents` |
| BR-C-03 | Os cônjuges vêm dos `FAMS`; **só quando essa lista fica vazia** roda a varredura global. | `family_navigation.py:get_spouses` |
| BR-C-04 | A busca direta é BFS **bidirecional** subindo por pais, com teto de **20 iterações**. | `path_finding.py:find_ancestral_path` |
| BR-C-05 | Se as duas pessoas são a mesma, o caminho é ela própria e ela é o ancestral. | idem |
| BR-C-06 | A cada iteração, **um** nível de **um** dos lados é expandido, alternadamente. | idem |
| BR-C-07 | A busca indireta usa o caminho mais curto no grafo pessoa↔família, com teto de **40 arestas**; os nós de família são comprimidos. | `path_finding.py:find_indirect_path` |
| BR-C-08 | O grafo vem da **árvore recebida** por parâmetro — não há mais import tardio nem estado de processo. **REESCRITA em 2026-10-10** (a versão anterior descrevia o import dentro da função). | idem |
| BR-C-09 | Sem os dois registros no GEDCOM, `status: not_found` com o aviso `pessoa_ausente`. | `documentary_relationship.py:documentary_relationship` |
| BR-C-10 | Sem caminho dentro do teto, o aviso diz que isso **não prova** ausência de parentesco. | idem |
| BR-C-11 | Os graus são as posições do ancestral comum no caminho. | idem |
| BR-C-12 | Linha direta: 1 → pai/mãe; 2 → avô/avó; n → com `bis` repetido `n−2` vezes. | `documentary_relationship.py:documentary_label` |
| BR-C-13 | Colateral com menor grau 1: (1,1) irmãos; (1,2) tio/tia; (1,n) tio/tia-avô com `bis` repetido. | idem |
| BR-C-14 | Demais colaterais: chave `gC` ou `gCrR`, com grau `= menor−1` e remoções `= maior−menor`. | idem |
| BR-C-15 | Cada salto carrega a evidência do registro que o sustenta: família, casal declarado, datas e idade implícita. | `documentary_relationship.py:hop_evidence` |
| BR-C-16 | Idade do genitor fora de **12–70** marca `plausible: False` e gera o aviso `data_impossivel`; **o vínculo não é invalidado**. | idem |
| BR-C-17 | Sem data para julgar, `plausible` é `None` (não é falso). | idem |
| BR-C-18 | O ano é o primeiro número de 3 ou 4 dígitos; `ABOUT`/`BEFORE` são tolerados e **não** normalizados. | `documentary_relationship.py:parse_year` |
| BR-C-19 | Todos os ancestrais comuns são enumerados até **12** níveis, limitados a **12**, ordenados por meioses totais, depois maior distância, depois nome. | `documentary_relationship.py:find_all_common_ancestors` |
| BR-C-20 | Caminhos alternativos são listados e **nenhum é descartado**; a existência gera `caminhos_multiplos`. | `documentary_relationship.py:documentary_relationship` |
| BR-C-21 | Mais de uma cadeia de pais até o mesmo ancestral gera `colapso_de_pedigree`, com teto de 8 cadeias. | idem + `_cadeias_ate` |
| BR-C-22 | O índice nome→ids é reconstruído quando a **chave derivada do conteúdo** da árvore muda. **REESCRITA em 2026-10-10** — antes era `gedcom_state.versao`, que não existe mais. | `documentary_relationship.py:_chave_de`, `_indice_por_nome` |
| BR-C-23 | A comparação de nomes ignora acento e aplica a correção de mojibake antes de comparar. | `documentary_relationship.py:normalizar` |
| BR-C-24 | O dossiê devolve **todos** os registros possíveis, sem escolher; `ambiguous` é verdadeiro com mais de um nome exato, **ou** com `similar_ids` não vazio. | `documentary_relationship.py:homonym_dossier` |
| BR-C-25 | Com identidade ambígua, o parentesco sai com `status: ambiguous` e o aviso `homonimo`. | `documentary_relationship.py:documentary_relationship` |
| BR-C-26 | Pessoa 1 ou 2 não encontrada: `Pessoa N 'X' não encontrada.` e `success = False`. | `core/path_search.py:path_search` |
| BR-C-27 | Com homônimos, até **5 × 5** combinações são testadas (em cache) e vence a **primeira que tiver caminho**; sem nenhuma, usa-se o primeiro id de cada lado. | idem |
| BR-C-28 | Caminho por ancestral comum: `Conexão direta encontrada (ancestral comum).` | idem |
| BR-C-29 | Sem caminho direto, tenta-se o indireto; sem indireto, `Nenhuma conexão encontrada entre 'X' e 'Y'.` com `success = True`. | idem |
| BR-C-30 | Conexão indireta vira `status: affinity`, com rótulo "Sem ancestral comum: conexão por afinidade (casamento)" e o aviso de afinidade. | idem |
| BR-C-31 | A conexão por afinidade **nunca** é apresentada como parentesco consanguíneo. | idem (`AVISO_AFINIDADE`) |
| BR-C-32 | O rótulo Mermaid passa por NFC, converte espaço inquebrável, travessões e aspas curvas, troca aspa dupla por apóstrofo e achata quebras de linha. | `mermaid_render.py:_mermaid_label` |
| BR-C-33 | O rótulo usa **lista branca**: o que não está nela é removido, e `&`, `<`, `>` viram entidades HTML. | idem (`_LABEL_SEGURO`) |
| BR-C-34 | O id de nó Mermaid mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e recebe o prefixo `N_`. | `mermaid_render.py:_mermaid_sid` |
| BR-C-35 | No diagrama direto, o casal do ancestral comum vira **um** nó quando o ancestral não está numa das pontas do caminho. | `mermaid_render.py:generate_mermaid_graph` |
| BR-C-36 | Cada `subgraph` do diagrama indireto é fechado pelo fim de um `contextmanager`. | `mermaid_render.py:generate_mermaid_graph_indirect_bridge` |

### 5.5 Regras de negócio — novas (2026-10-10)

| ID | Regra | Onde |
| --- | --- | --- |
| BR-C-37 | Os dois nomes recebem `strip` antes de qualquer coisa. | `core/path_search.py:path_search` |
| BR-C-38 | Os candidatos unem os ids do legado aos **exatos** do dossiê, sem repetir e preservando a ordem; os "parecidos" entram só como `similar_matches`, limitados a 5. | `core/path_search.py:_candidatos` |
| BR-C-39 | O dossiê agregado só é ambíguo se **algum lado** for ambíguo; contagem e fichas vêm só dos lados ambíguos. | `core/path_search.py:_homonimos` |
| BR-C-40 | Sem ambiguidade e sem parecidos, o dossiê é `{}` e a seção não aparece na tela. | idem |
| BR-C-41 | Os pares `(cand1, cand2)` já calculados são reaproveitados por cache local. | `core/path_search.py:path_search` |
| BR-C-42 | O teto de combinações é `LIMITE_DE_CANDIDATOS = 5` por lado. | idem |
| BR-C-43 | O `set` de ancestrais comuns é ordenado por `(meioses, maior distância, nome)` — **e o empate nos três critérios herda a ordem do `set`** (ver §5.7). | `documentary_relationship.py:find_all_common_ancestors` |
| BR-C-44 | A contagem de cadeias devolve um **piso**: ela para no teto de 8. | `documentary_relationship.py:_cadeias_ate` |
| BR-C-45 | `person_summary` monta a ficha comparável com **13** campos — **CORRIGIDO em 2026-10-10 pelo Revisor**: o texto dizia 12, e a leitura do fonte enumera 13 (`id`, `name`, `sex`, `birth`, `birth_year`, `birth_place`, `death`, `death_year`, `parents`, `parent_names`, `spouses`, `children`, `family_as_child`) | `documentary_relationship.py:person_summary` |
| BR-C-46 | `_diferencas` compara data e local de nascimento, data de falecimento, pais, filhos e sexo entre homônimos. | `documentary_relationship.py:_diferencas` |
| BR-C-47 | `identical_data` é verdadeiro quando há mais de um registro e **nenhum** campo diverge. | `documentary_relationship.py:homonym_dossier` |
| BR-C-48 | `hop_evidence` resolve a família por `FAMC` e, sem ele, pelo índice filho→famílias; sem família localizada, `link_source` diz isso. | `documentary_relationship.py:hop_evidence` |
| BR-C-49 | `split_path_by_marriage` devolve o **primeiro** par adjacente de cônjuges e as duas metades do caminho. | `family_navigation.py:split_path_by_marriage` |
| BR-C-50 | `pick_spouse_for_couple` prefere o cônjuge que aparece no caminho candidato; senão, o primeiro. | `family_navigation.py:pick_spouse_for_couple` |
| BR-C-51 | `exclude_tail(seq, n=1)` corta a cauda para não duplicar o ancestral na ponta. | `family_navigation.py:exclude_tail` |
| BR-C-52 | O `sid` do par de cônjuges é o dos dois ids **ordenados** unidos por `+` — logo, independente da ordem recebida. | `mermaid_render.py` |
| BR-C-53 | Linhagem direta é `ac_idx` em `-1`, `0` ou no último nó; só fora disso o MRCA vira nó de casal. | idem |
| BR-C-54 | Os dois membros do casal são **omitidos** como nós próprios quando o casal é emitido. | idem |
| BR-C-55 | O diagrama indireto abre `subgraph`s aninhados, todos com `direction BT`. | `mermaid_render.py:generate_mermaid_graph_indirect_bridge` |
| BR-C-56 | Sem par de cônjuges, sem caminho até A, ou sem caminho até B, o diagrama indireto **cai no direto** com `mrca=None`. | idem |
| BR-C-57 | O casamento é uma aresta rotulada entre duas **âncoras invisíveis**, e não uma seta de filiação. | idem |
| BR-C-58 | As cores são fixas por papel: p1 verde, p2 vermelho, MRCA/casal amarelo e o casal da afinidade laranja. | idem |
| BR-C-59 | `resolvedor_de_diagrama` devolve sete consultas **ligadas à árvore**, e o renderizador não importa `core`. | `core/diagram_domain.py` |
| BR-C-60 | O desfecho é derivado de (payload, sucesso), nunca do texto: payload presente → `RESULTADO`; sem payload e com sucesso → `SEM_RESULTADO`; sem payload e sem sucesso → `ERRO_DE_ENTRADA`. | `application/path_search.py:_desfecho` |
| BR-C-61 | O campo de template **não** atravessa a fronteira: `dados` é o payload do núcleo sem renomear nada. | `application/path_search.py:ResultadoDeBusca` |
| BR-C-62 | O caso de uso **não** monta as dependências de diagrama por requisição: elas chegam por parâmetro, montadas uma vez na borda. | idem |
| BR-C-63 | `dono` está na assinatura e **não** participa de decisão nenhuma. | idem |
| BR-C-64 | A rota escolhe o modo de renderização pelo **desfecho**, nunca pelo texto da mensagem. | `app.py:index` |
| BR-C-65 | Erro de domínio passa pela tabela de tradução; falha inesperada vira `Ocorreu um erro: {e}` com `success=False`. | `app.py:index`, `application/traducao.py` |
| BR-C-66 | `__all__` de `core/path_search.py` declara **apenas** `path_search`: o bloco que reexportava 17 nomes foi removido. | `core/path_search.py` |
| BR-C-67 | `nomes_de_exibicao` é a lista **ordenada** de `get_name` sobre a árvore, compartilhada pelos três fluxos. | `application/__init__.py:nomes_de_exibicao` |

### 5.6 Constantes, parâmetros e configuração

| Nome | Valor | Onde | Observação |
| --- | --- | --- | --- |
| `MAX_DEPTH` | `20` | `path_finding.py` | Teto de **iterações** do BFS bidirecional, não de gerações. |
| `MAX_HOPS` | `40` | idem | Teto de **arestas** do grafo bipartido — o teto efetivo em vínculos pessoa-a-pessoa é ≈ metade. |
| `MAX_DEPTH_ALTERNATIVOS` | `12` | `documentary_relationship.py` | Teto da enumeração de ancestrais comuns. |
| `LIMITE_DE_CADEIAS` | `8` | idem | Teto da contagem de cadeias. |
| `LIMITE_DE_CANDIDATOS` | `5` | `core/path_search.py` | Teto por lado nas combinações com homônimos. |
| `IDADE_MINIMA_GENITOR` / `IDADE_MAXIMA_GENITOR` | `12` / `70` | `documentary_relationship.py` | Não é regra biológica: é filtro de evidência. |
| `AVISO_AFINIDADE` | texto fixo | `core/path_search.py` | Impede a leitura da afinidade como consanguinidade. |
| `_LABEL_SEGURO` | lista branca (regex negada) | `mermaid_render.py` | Documentada no código, com os dois bugs que a moldaram. |
| Cores dos nós | verde/vermelho/amarelo/âmbar | idem | Papel visual de cada nó. |
| Direção do diagrama | `flowchart BT` | idem | Base para o topo. |

### 5.7 Observações e lacunas

* 🟢 **O teto de 20 corta em silêncio, e isso é contrato aceito** (decisão humana de 2026-09-30): o aviso diz que isso não prova ausência de parentesco.
* 🟢 **A varredura de `get_spouses` é condicional, e isso é contrato explícito.** Se a pessoa tem um `FAMS` que resolve e outro que não, o fallback **não roda** e o cônjuge da segunda família desaparece. Torná-la complementar **muda o resultado**.
* 🟡 **A ordem de `common_ancestors` e de `additional_paths` pode variar com o `PYTHONHASHSEED`** quando dois ancestrais empatam em meioses, distância **e** nome: a varredura parte de `set(de_a) & set(de_b)` e a ordenação é estável, de modo que o empate herda a iteração do `set`. É a mesma classe do defeito que o `matching` fechou em 2026-10-05, e aqui segue **aberta**.
* 🔴 **Colisão possível da chave do cache de nomes** (`_chave_de` = `(len, primeira chave, última chave)`): dois GEDCOMs do mesmo tamanho com os mesmos xrefs extremos reaproveitam o índice da árvore anterior, e o dossiê de homônimos passa a listar xrefs de outra árvore, **sem exceção**. Detalhamento em `flowcharts/busca-caminho.md` §13.
* 🟡 **`get_children` varre todas as famílias** a cada chamada, sem índice; em `person_summary`, chamada por homônimo, isso custa uma varredura completa por ficha.
* 🟡 **`_diferencas` é chamado duas vezes** em `homonym_dossier` — o comentário do código diz que as fichas são montadas "UMA vez", e isso vale dentro de uma chamada, não entre as duas.
* 🟡 **O caminho indireto não passa pela checagem de plausibilidade de datas**; ela existe só sobre os saltos do caminho **direto**.
* 🟡 **A contagem de cadeias é truncada em 8**, então o aviso de colapso exibe um piso.
* 🟡 **`bis` é repetido, não traduzido:** "bisbisavô" onde o português genealógico diria "trisavô".
* 🔴 **`person_a` e `person_b` são fichas completas em cada resultado** (142 fichas no caso real de 71 conexões), para uma tela que exibe poucas — custo real, sem limite medido.

---

## 6. Unidade `recursos-da-tela` (unidade **nova** nesta rodada)

### 6.1 Escopo e arquivos

| Arquivo | Linhas úteis | Responsabilidade |
| --- | ---: | --- |
| `src/app.py` (`ARTE_DO_ICONE`/`icone_de_atalho`, `ARTE_DO_TOPO`/`banner_do_topo`) | ~90 | As duas rotas de arte: `GET /apple-touch-icon.png` e `GET /banner.png`. |
| `src/assets/apple-touch-icon.png` | 16.504 bytes | **Derivada de runtime**: canônica composta sobre branco, 180×180, sem alfa. |
| `src/assets/banner-da-tela.png` | 317.058 bytes | **Derivada de runtime**: fonte com o fundo quadriculado removido. |
| `tests/icone_de_atalho.py` | 94 | A **receita** do ícone (fonte única). |
| `tests/banner_da_tela.py` | 182 | A **receita** do banner (fonte única). |
| `tests/test_deriva_da_arte.py` | 84 | O teste de deriva: regenera e compara **pixel** com o arquivo commitado. |

Fluxo completo: `flowcharts/recursos-da-tela.md`.

### 6.2 Algoritmos e lógica não trivial

**A arte servida não é a arte canônica.** O ícone é a canônica (`docs/assets/img/logo.png`, 32,5 % transparente) **composta sobre branco** e reamostrada para 180×180 com cantos retos — porque o sistema móvel compõe transparência sobre **preto** e servir a arte crua daria um quadrado preto com o desenho por cima. O banner é a fonte (`docs/assets/img/banner-analisador.png`) com o **quadriculado de transparência gravado no bitmap** removido, porque a fonte chegou em `RGB`, sem alfa. 🟢

**A remoção de fundo é global, em duas faixas de brilho.** A versão por inundação a partir da borda foi **medida como insuficiente**: a árvore, o livro e o texto formam anúncios fechados, e sobraram 8.379 pixels de fundo opacos numa amostra de 1/9 da imagem. Um limite único de brilho, por sua vez, comia o preenchimento do texto dourado e deixava as letras **ocas**. Por isso: brilho ≥190 com saturação ≤50; brilho 160–190 com saturação ≤12; abaixo de 160 nunca é fundo. Uma segunda passada dá **alfa proporcional** à fronteira, para o serrilhado não virar halo. 🟢

**O resíduo é medido com limite mais estrito que o da regra.** Medir com o mesmo limite devolve **sempre zero**, e foi esse erro que deixou um bloco de quadriculado passar duas vezes. 🟢

**A deriva é comparada pixel a pixel, nunca por `sha256`:** o **mesmo** desenho existe em disco com 32.317 e com 44.069 bytes, com diferença de pixel **zero**. 🟢

### 6.3 Regras de negócio

| ID | Regra | Onde |
| --- | --- | --- |
| BR-E-01 | As duas rotas são registradas **somente** com `GET`; a escrita é recusada pelo roteador com `405`. | `app.py` |
| BR-E-02 | A rota do ícone serve `app.config["ARTE_DO_ICONE"]`; a do banner, `app.config["ARTE_DO_TOPO"]`. | idem |
| BR-E-03 | Arte ausente devolve resposta **vazia** com `404`, e nada mais muda. | idem |
| BR-E-04 | As duas rotas declaram `mimetype="image/png"`. | idem |
| BR-E-05 | Os caminhos são ancorados no arquivo do app, e não no diretório corrente. | idem |
| BR-E-06 | Não há `Cache-Control` de validade longa; a revalidação é o `ETag` do `send_file`, que responde `304` sem corpo. | idem |
| BR-E-07 | O ícone de atalho é descoberto por **caminho convencional**; o template **não** o declara. | `tests/test_icone_de_atalho.py` |
| BR-E-08 | O ícone da aba continua sendo um `data URI` embutido, e não uma segunda rota. | `index.html` |
| BR-E-09 | `favicon.ico` e `apple-touch-icon-precomposed.png` **não** têm rota. | `test_icone_de_atalho.py` |
| BR-E-10 | O ícone é a canônica composta sobre branco e reamostrada para **180×180**. | `tests/icone_de_atalho.py:arte_derivada` |
| BR-E-11 | O fundo do ícone é **branco** (a arte tem creme em duas tonalidades). | idem |
| BR-E-12 | Os cantos do ícone ficam **retos** (o sistema aplica a própria máscara). | idem |
| BR-E-13 | O PNG do ícone tem **16.504 bytes**, e esse número é a âncora contra reamostragem, fundo ou compressão diferentes. | idem (`TAMANHO_ESPERADO`) |
| BR-E-14 | A opacidade do ícone é provada pelo **tipo de cor 2** do IHDR, sem biblioteca de imagem. | `test_icone_de_atalho.py` |
| BR-E-15 | O banner é a fonte com o fundo removido, porque a fonte chegou em `RGB` com o quadriculado gravado. | `app.py`, `tests/banner_da_tela.py` |
| BR-E-16 | A remoção de fundo é **global**, e não por inundação a partir da borda. | `tests/banner_da_tela.py:mascara_do_fundo` |
| BR-E-17 | Um pixel é fundo em **duas faixas**: ≥190 com saturação ≤50, e 160–190 com saturação ≤12; abaixo de 160 nunca. | idem (`_e_fundo`) |
| BR-E-18 | `CLARO_MINIMO = 160` e `SATURACAO_MAXIMA = 50` saem de medição, com folga declarada nos dois lados. | idem |
| BR-E-19 | A fronteira recebe **alfa proporcional** à distância do fundo. | idem (`arte_limpa`) |
| BR-E-20 | O resíduo é medido com limite **mais estrito** que o da regra, e precisa ser **zero** na caixa de regressão. | idem (`residuo_de_fundo`), `test_banner_do_topo.py` |
| BR-E-21 | Onze pontos da arte têm de continuar opacos, cobrindo arte escura pouco saturada e arte clara quase neutra. | `test_banner_do_topo.py` |
| BR-E-22 | A arte de runtime mora em `src/assets/`, porque o `.dockerignore` é lista de **permissão**. | `.dockerignore`, `app.py` |
| BR-E-23 | `src/static/` é proibida (`W004`), com teste que falha se a arte cair numa pasta estática. | `test_deriva_da_arte.py` |
| BR-E-24 | `src/uploads/` é reexcluído do contexto de build **depois** de `!src/**`, porque carrega dado real do operador. | `.dockerignore` |
| BR-E-25 | A arte derivada é **commitada**, e não gerada em tempo de execução. | `tests/icone_de_atalho.py` |
| BR-E-26 | A receita tem **fonte única** em `tests/`, e o teste de deriva a importa e compara **pixel** com o arquivo commitado. | `test_deriva_da_arte.py` |
| BR-E-27 | A comparação por `sha256` entre canônica e derivada é proibida na prática: recompressão muda bytes e não pixels. | idem |
| BR-E-28 | A biblioteca de imagem **não** entra em `requirements.txt` (que é lista de runtime). | idem |
| BR-E-29 | A masthead segue a ordem **imagem → subtítulo → título em texto → texto de apresentação**. | `index.html`, `test_banner_do_topo.py` |
| BR-E-30 | A arte do topo é reduzida a `w-50`, e o `alt` descreve a **ilustração**, nunca o título. | idem |

### 6.4 Observações e lacunas

* 🟢 **As duas rotas são o mesmo desenho, e isso é deliberado:** `GET` sozinho, `ETag`, `404` com resposta vazia, caminho ancorado no arquivo do app e a arte em `src/assets/`.
* 🟢 **`docs/assets/img/apple-touch-icon.png` existe e é byte a byte igual à de runtime** (16.504 bytes): é a cópia que o mini-site publicado consome.
* 🟡 **O `sha256` da tela em `test_icone_de_atalho.py` é um invariante mantido à mão**, atualizado três vezes em 2026-10-10, cada atualização amarrada a uma `RN` de um adendo vigente. Enquanto for assim, o teste prende o que promete.
* 🟡 **A caixa de regressão `(778,232)–(918,338)` descreve uma composição que não existe mais** (a que tinha abajur), mas continua valendo como caixa.
* 🔴 **Não há verificação de que a arte servida é a derivada correta no ambiente do container:** os testes rodam no host, onde `docs/` existe. Se a arte falhar dentro da imagem, a degradação é o `404` — exatamente o caso que a escolha de `src/assets/` existe para evitar.

---

## 7. Estruturas Transversais

### 7.1 A fronteira de aplicação (`src/application/` + `src/ports/`)

**Quatro portas, cinco tipos de payload.** As portas são `Protocol` — a interface que o caso de uso consome **por parâmetro**, sem nunca instanciar a implementação concreta. `ArmazenamentoDeArquivos` (4 métodos), `CarregadorDeArvores` (1), `RepositorioDeArvores` (**2, sem implementação e sem consumidor** — `D-03`) e `RegistroDeAnalises` (1). Os payloads são `EntradaArmazenada`, `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise` e `AnaliseParaRegistrar`. Detalhamento em `data-dictionary.md` §8.4. 🟢

**`dono` em todas as assinaturas, e sem comportamento em nenhuma.** É **costura**, e não funcionalidade: não entra na chave, no nome armazenado nem no caminho, e nenhum arquivo é separado por dono. A assimetria entre as portas acabou na feature 007 — o motivo é o custo, não a simetria: adiar o parâmetro reabriria toda assinatura de porta e todos os chamadores depois. As dívidas #3 e #4 seguem **abertas**, e nenhuma entrega pode ser citada como tendo implementado isolamento. 🟢

**A regra de composição da borda.** `src/app.py` monta **uma vez** as dependências de borda que o núcleo consome (`_DEPENDENCIAS`, com as quatro funções de CSV e as duas de diagrama), os dois adaptadores de arquivo (`_ARMAZENAMENTO`, `_CARREGADOR`) e o registrador (`_REGISTRO`, nulo sem `DATABASE_URL`). Até a extração havia uma segunda montagem idêntica dentro do ramo de DNA, a cada requisição; ela saiu no `T018`. 🟢

### 7.2 Exceções de domínio

Cinco tipos irmãos, com raiz `ErroDeDominio` herdando de `ValueError`: `PessoaNaoEncontrada`, `GedcomNaoSuportado`, `DnaCsvSemColunas`, `CsvIlegivel`. A herança é **deliberada** — sem ela, quatro asserções que a suíte já escreve quebrariam, e distinguir casos pela **mensagem** passa a ser proibido (a distinção é sempre pelo **tipo**). A moldura de apresentação fica na tabela de tradução, nunca na exceção. 🟢

### 7.3 Docker e empacotamento

`docker/Dockerfile` (`python:3.14-slim`), `docker-compose.yml` (serviços `db` e `app`, portas fixadas em `127.0.0.1`), `init.sql` (6 tabelas, idempotente por requisito) e `.dockerignore` em **lista de permissão**. Nenhum workflow de CI/CD existe: o workflow de GitHub Pages foi removido em 2026-10-08 e a publicação do mini-site virou passo manual (`python publicar_docs.py`). 🟢

### 7.4 O que está FORA do escopo de runtime

`_reversa_sdd/migration/`, `oracle/`, `parity/`, `screens/` e `_reversa_docs/` são **instrumentação de desenvolvimento**. O harness de paridade importa `src/app.py`, e é por isso que nada no import do app pode exigir driver, rede ou biblioteca de imagem. 🟢

---

## 8. Dados Transversais

O dicionário consolidado — campos, tipos, obrigatoriedade, valores padrão e origem de cada estrutura — está em **`data-dictionary.md`**, e os dados por módulo em `.reversa/context/modules.json`. Cobrem: a árvore em memória e seu cache de nomes; o armazenamento em disco e a listagem; o CSV e a evidência genética; as estruturas de decisão (possibilidades, confronto); o parentesco documental; os payloads da fronteira; **o esquema PostgreSQL de 6 tabelas**; a configuração por ambiente; e as sentinelas.

---

## 9. Dívidas Técnicas e Observações Consolidadas

| # | Dívida / observação | Onde | Gravidade | Confiança |
| ---: | --- | --- | --- | --- |
| 1 | `app.secret_key` foi **removido** em 2026-10-05 (não tinha consumidor). **FECHADA.** | — | — | 🟢 |
| 2 | Estado global em `core/gedcom_state.py`. **FECHADA:** o módulo foi apagado (`T023`) e a árvore entra por parâmetro. | — | — | 🟢 |
| 3 | Corrida entre requisições concorrentes: a guarda de exclusividade é de **processo**, não de thread. | `app.py:__main__` | Média | 🟢 |
| 4 | Ausência de identidade e de isolamento entre donos: o armazenamento é único por processo. | `ports/adaptadores.py` | **Alta para multiusuário** | 🟢 |
| 5 | O teto de 20 iterações do BFS direto corta em silêncio. | `path_finding.py` | Média (contrato aceito) | 🟢 |
| 6 | `get_spouses` esconde cônjuges quando o primeiro `FAMS` resolve. | `family_navigation.py` | Média (contrato aceito) | 🟢 |
| 7 | `get_children` varre todas as famílias, sem índice. | `documentary_relationship.py` | Média (custo) | 🟢 |
| 8 | Fichas completas por pessoa em cada resultado (142 no caso real de 71 conexões). | idem | Média (custo) | 🟢 |
| 9 | O caminho indireto não passa pela checagem de plausibilidade de datas. | `core/path_search.py` | Média | 🟢 |
| 10 | O CSV não tem validação de conteúdo, só de forma de nome. | `ports/adaptadores.py:guardar` | Média | 🟢 |
| 11 | `cm_estimator` segue como legado fora do fluxo, com faixas sem fonte verificável. | `core/cm_estimator.py` | Baixa (declarada) | 🟢 |
| 12 | `COMMON_SURNAMES` tem duplicata literal; o mapa de mojibake tem chave duplicada e um no-op. | `name_normalization.py`, `text_cleaning.py` | Baixa | 🟢 |
| 13 | **`psycopg2-binary==2.9.13` está pinado e NÃO está instalado no `.venv`** (o interpretador oficial): a persistência fica desligada no ambiente oficial. É o **inverso** da divergência da rodada anterior. | `requirements.txt`, `.venv/` | **Alta** | 🟢 |
| 14 | O resultado da suíte depende do ambiente: com `DATABASE_URL` presente e sem o driver, 2 testes falham. | `tests/test_persistencia_desabilitada.py` | Média | 🟢 |
| 15 | Endogamia e colapso de pedigree não são corrigidos no confronto: o cM lido é um teto otimista. | `evidence_comparison.py` | Média (declarada na fonte) | 🟢 |
| 16 | Relações mais distantes não publicadas na 4.0, que é onde o caso real cai. | `relationship_hypotheses.py` | Média | 🟢 |
| 17 | Ordem de `common_ancestors`/`additional_paths` sensível ao `PYTHONHASHSEED` em empate triplo. | `documentary_relationship.py` | Média | 🟡 |
| 18 | Colisão possível da chave do cache de nomes entre duas árvores de mesmo tamanho. | `documentary_relationship.py:_chave_de` | **Alta** (resultado pode divergir) | 🟡 |
| 19 | Não há teste de caminho feliz de INSERT: erro de SQL ou de ordem de FK só apareceria no contêiner. | `tests/`, `init.sql` | Média | 🟢 |
| 20 | `LIMITE_SEGMENTO_FRACO` é heurística do projeto apresentada ao lado de números publicados. | `genetic_evidence.py` | Baixa | 🟢 |
| 21 | Os quatro estados do confronto são também nomes de classe CSS, sem teste que prenda o par. | `evidence_comparison.py`, `index.html` | Baixa | 🟢 |
| 22 | `sha256` da tela mantido à mão em três atualizações no mesmo dia. | `test_icone_de_atalho.py` | Baixa | 🟡 |
| 23 | Sem verificação de que a arte derivada é a servida dentro do container. | `src/assets/`, `.dockerignore` | Baixa | 🔴 |
| 24 | `.env` tem credencial em claro (usuário, senha, banco). Está no `.gitignore`, e **nenhum valor** foi transcrito para os artefatos. | `.env` | Média | 🟢 |
| 25 | Sobrou `.pyc` de `core/gedcom_state.py`, apagado no `T023`. | `src/core/__pycache__/` | Baixa | 🟢 |
| 26 | As matrizes de `_reversa_bugs/*/generated/` derivam das specs de 2026-10-05 e ancoram em contratos que esta rodada reescreve. | `_reversa_bugs/` | Média | 🟢 |
| 27 | O mini-site (`_reversa_docs/` e `docs/`) é de 2026-10-08, anterior às features 009–012. | `docs/` | Média | 🟢 |
| 28 | CI/CD ausente: a publicação do mini-site é passo manual. | — | Baixa | 🟢 |

---

*Gerado pelo Reversa-Archaeologist em 2026-10-10 (re-extração). Fim da análise técnica consolidada.*
