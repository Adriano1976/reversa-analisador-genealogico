# Unit `upload-gedcom` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=upload_gedcom`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-05** (nível **Completo**).
> Substitui a versão de 2026-09-30, que descrevia a raiz `analisador-genealogico/` e o pacote `reconstructed/`. Snapshot: `.reversa/snapshots/2026-10-05-pre-reextracao/upload-gedcom/`
> Fontes: `code-analysis.md` §2 (20 regras `BR-U-*`), `flowcharts/upload-gedcom.md`, `data-dictionary.md` §2 e §3, `domain.md` §3.5, `adrs/` (06, 07, 11, 17)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Recebe um arquivo GEDCOM enviado pelo navegador, **decide se ele pode ser gravado**, grava-o sob uma chave derivada do próprio conteúdo e o traduz em estado de domínio consultável (pessoas, famílias e grafo). É a porta de entrada de **todas** as outras unidades: sem `upload-gedcom`, não há `analise-dna` nem `busca-caminho`. 🟢

A unit resolve três problemas ao mesmo tempo: **segurança do que entra em disco**, **continuidade entre requisições sem sessão** e **fidelidade de parsing ao legado**. 🟢

## Responsabilidades

- Decidir se o conteúdo recebido é um GEDCOM aceitável, **antes** de qualquer gravação. 🟢
- Derivar a chave de armazenamento do **conteúdo** e compor o nome em disco preservando a extensão original. 🟢
- Gravar de forma **idempotente** (mesmo conteúdo não reescreve) e devolver o **caminho completo**. 🟢
- Resolver, em requisições seguintes, o arquivo a partir da **chave recebida no formulário**, validada por forma fechada. 🟢
- Traduzir `INDI`/`FAM` em `people`, `families`, `child_to_family` e no grafo bipartido, **substituindo** o estado do processo. 🟢
- Devolver a **lista ordenada de nomes** da árvore, que alimenta os formulários das outras unidades. 🟢
- Ser a **autoridade única** da limpeza de mojibake de nomes. 🟢

## Regras de Negócio

- **A validação é de conteúdo, não de extensão.** Um GEDCOM legítimo sem `.ged` é aceito; o `RISK-007` autoriza o relaxamento para não quebrar a paridade de parsing com o oráculo. 🟢
- **GEDCOM aceitável** = depois de remover **um** BOM UTF-8 e os espaços à esquerda, o conteúdo começa com `0 HEAD`. 🟢
- **Conteúdo vazio** é recusado com `arquivo vazio`; **byte NUL** é recusado com `conteudo binario`. 🟢
- **A chave de armazenamento é o sha256 do conteúdo truncado em 16 hexadecimais** — não um UUID aleatório. Mesmo conteúdo, mesma chave, porque o formulário devolve o valor no `POST` seguinte. 🟢
- **O nome do cliente nunca compõe o caminho.** Ele vira metadado legível **depois** da chave; a pasta é sempre a resolvida por `_pasta_uploads()`. 🟢
- **No nome visível**, `/`, `\` e NUL viram `_`; acentos, espaços e a **extensão original** são preservados. Nome vazio ou só pontos vira `arvore.ged`; nome sem extensão recebe `.ged`. 🟢
- **Arquivo já existente com a mesma chave não é reescrito.** 🟢
- **O caminho de escrita e o de leitura são o mesmo, sempre** — a pasta é ancorada no arquivo do app, e não no diretório corrente. 🟢
- **A validação da chave recebida é por forma** (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`), e não por lista negra: como a expressão exclui `/`, `\` e `..`, um valor manipulado não tem como escapar da pasta. 🟢
- **A substituição do estado é assimétrica e deliberada:** `people`, `families` e `child_to_family` são mutados *in place* (`clear()` + `update()`) para preservar os bindings importados no topo; `graph` é **reatribuído**. 🟢
- **`versao` é incrementado a cada carga** e é o sinal de invalidação dos índices derivados, porque `id()` não muda com mutação *in place*. 🟢
- **`get_name` devolve string vazia** quando o registro tem `Name` e o formato resulta vazio; o literal `Sem Nome` só aparece quando **não há** `name`. Isso **ocorre em dado real** (296 de 35.460 pessoas em uma árvore medida) e **não deve ser "melhorado"**: é contrato de paridade com o oráculo congelado (`DIV-001`). 🟢
- **Família sem `xref_id` é ignorada por completo**; arestas só são criadas para nós existentes no grafo. 🟢
- **A lista de nomes devolvida é ordenada** e tem exatamente um item por pessoa carregada. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Receber `POST` com `action=upload_gedcom`, exigindo o campo `gedcom` em `request.files` e `filename` não vazio | Must | Sem o campo → `"Nenhum arquivo GEDCOM enviado."`; `filename` vazio → `"Nenhum arquivo selecionado."`; ambos com `success=False` 🟢 |
| RF-02 | Ler o conteúdo **inteiro** e validá-lo **antes** de qualquer gravação | Must | Nenhum byte chega ao disco quando o conteúdo é recusado 🟢 |
| RF-03 | Recusar conteúdo vazio, com byte NUL, ou que não comece com `0 HEAD` após BOM e espaços | Must | Motivo nomeado em cada caso; mensagem `"Arquivo não reconhecido como GEDCOM: {motivo}."` 🟢 |
| RF-04 | Derivar a chave de armazenamento do conteúdo: `sha256(conteudo).hexdigest()[:16]` | Must | Mesmo conteúdo reenviado produz exatamente a mesma chave 🟢 |
| RF-05 | Compor o nome em disco como `<chave>__<nome visível>`, **preservando a extensão original** | Must | Enviar `matches.csv` gera `<chave>__matches.csv`, **nunca** `<chave>__matches.csv.ged` 🟢 |
| RF-06 | Sanear o nome visível: `/`, `\` e NUL viram `_`; acentos e espaços preservados; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged` | Must | `../../etc/passwd` não produz separador algum no nome resultante 🟢 |
| RF-07 | Gravar de forma idempotente: não reescrever arquivo existente com a mesma chave | Should | Segundo envio do mesmo conteúdo não altera o arquivo em disco 🟢 |
| RF-08 | Devolver o **caminho completo** do arquivo gravado, e não o nome | Must | A leitura seguinte usa exatamente o que foi escrito, sem remontar caminho 🟢 |
| RF-09 | Resolver, em `POST` de análise, o arquivo a partir da chave recebida, aceitando **apenas** a forma fechada | Must | Chave fora da forma → `"Erro: Arquivo '{valor}' não existe mais."`; chave ausente → `"Erro: Arquivo GEDCOM não encontrado."` 🟢 |
| RF-10 | Recusar corpo de requisição acima de 16 MB com `HTTP 413` e mensagem em português | Must | Resposta `413` com `"Arquivo maior que o limite de 16 MB."` e nenhum byte gravado 🟢 |
| RF-11 | Parsear os registros `INDI` e `FAM` e indexá-los por `xref_id` em `people` e `families` | Must | Cada `xref_id` do arquivo aparece no dicionário correspondente 🟢 |
| RF-12 | Construir o grafo bipartido pessoa↔família, com aresta para `HUSB`, `WIFE` e cada `CHIL` existente | Must | Nó de pessoa com `type="person"`, de família com `type="family"`; nenhuma aresta para id inexistente 🟢 |
| RF-13 | Manter `child_to_family` como **lista** de famílias por filho | Must | Pessoa filha em duas famílias aparece com as duas entradas 🟢 |
| RF-14 | Substituir o estado de forma assimétrica e incrementar `versao` | Must | `people` mantém identidade de objeto; `graph` muda de objeto; `versao` cresce a cada carga 🟢 |
| RF-15 | Devolver a lista de nomes **ordenada**, com um item por pessoa carregada | Must | A lista é igual à sua própria versão ordenada, e a contagem igual à de `people` 🟢 |
| RF-16 | Ser a **autoridade única** da limpeza de mojibake: `strip_bad_utf` e `demojibake` | Must | Nenhum outro módulo do projeto define limpeza própria 🟢 |
| RF-17 | Devolver `""` — e **não** `Sem Nome` — quando o registro tem `Name` com formato vazio | Must | Paridade com o oráculo congelado preservada 🟢 |
| RF-18 | Converter falha de parse em `"Erro ao processar GEDCOM: {e}"`, sem persistir estado parcial | Should | A exceção não derruba a requisição, e o estado anterior permanece íntegro 🟢 |
| RF-19 | Ancorar a pasta de upload no arquivo do app, com sobreposição por variável de ambiente | Should | `ANALISADOR_UPLOAD_FOLDER` redireciona a pasta; escrita e leitura usam o mesmo caminho 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| --- | --- | --- | --- |
| Segurança | A defesa contra escape de caminho é **por forma fechada**, sem lista negra | `src/utils/validate.py:31-32`, `:78-87` | 🟢 |
| Segurança | O teto de corpo é aplicado **antes** de ler o corpo da requisição | `src/app.py:32`, `:65-72` | 🟢 |
| Segurança | O arquivo é lido do disco por caminho **ancorado no arquivo do app**, e não no diretório corrente | `src/app.py:42-57`, `:99-108` | 🟢 |
| Segurança | ~~`app.secret_key` está **embutido no código e não tem consumidor**~~ ✅ **REMOVIDO em 2026-10-05** — não havia sessão a assinar | `src/app.py:22` (comentário da remoção); `from flask import Flask, render_template, request` | 🟢 |
| Reprodutibilidade | Mesmo conteúdo → mesma chave, estável entre requisições e entre processos | `src/utils/validate.py:68-70` | 🟢 |
| Confiabilidade | Gravação idempotente: arquivo existente não é reescrito | `src/app.py:93-95` | 🟢 |
| Confiabilidade | Estado anterior é preservado quando o parse falha (a mutação só ocorre após parse bem-sucedido) | `src/parsers/gedcom_parser.py:50-69` | 🟢 |
| Manutenibilidade | A decisão de gravação vive em módulo **puro** — não importa Flask e não toca o disco | `src/utils/validate.py:1-17` | 🟢 |
| Performance | O GEDCOM é **re-parseado integralmente** a cada requisição de análise; não há cache | `src/app.py:137` | 🟢 |
| Portabilidade | `SO_EXCLUSIVEADDRUSE` só existe no Windows; fora dele o padrão da plataforma já recusa a segunda ligação | `src/app.py:230-228` | 🟢 |
| Internacionalização | Todas as mensagens ao operador são literais em português | `src/app.py:70`, `:118-136` | 🟢 |
| Observabilidade | **Nenhum log, métrica ou trace é emitido.** A única saída textual é o `print` de inicialização | `src/app.py:259-263` | 🟢 |

> Inferido a partir do código. **Não** há middleware de autenticação, cache, fila, worker ou lógica de retry — essas linhas foram omitidas por falta de evidência.

## Critérios de Aceitação

```gherkin
Dado que o operador está na tela inicial
Quando envia um arquivo GEDCOM válido chamado exemplo_familia.ged
Então o arquivo é gravado em src/uploads sob a chave <sha256 truncado>__exemplo_familia.ged
E a tela mostra "Arquivo 'exemplo_familia.ged' carregado!" com success=True
E a lista completa de nomes da árvore é devolvida ao formulário

Dado que o operador envia o mesmo GEDCOM uma segunda vez
Quando a gravação é executada
Então o arquivo existente NÃO é reescrito
E a chave derivada é exatamente a mesma

Dado um conteúdo que não começa com a declaração 0 HEAD
Quando o upload é executado
Então a resposta é "Arquivo não reconhecido como GEDCOM: não começa com a declaração 0 HEAD."
E nenhum byte é gravado em disco
E success=False

Dado um arquivo de 20 MB
Quando o upload é executado
Então a resposta tem status HTTP 413
E a mensagem é "Arquivo maior que o limite de 16 MB."
E nenhum byte é gravado em disco

Dado um POST de análise com gedcom_filename igual a ../../etc/passwd
Quando a chave é validada
Então o valor é recusado por forma
E a resposta é "Erro: Arquivo '../../etc/passwd' não existe mais."
E nenhum arquivo fora de src/uploads é aberto

Dado um GEDCOM em que uma pessoa tem Name cujo formato resulta vazio
Quando a árvore é carregada e o nome é lido
Então get_name devolve string vazia
E NÃO devolve o literal "Sem Nome"
E a contagem de nomes continua igual à contagem de pessoas
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
| --- | --- | --- |
| Validar conteúdo antes de gravar (RF-02, RF-03) | **Must** | Caminho crítico: toda escrita em disco passa por aqui |
| Chave derivada do conteúdo (RF-04) | **Must** | As outras duas units dependem dela para a continuidade entre requisições |
| Validar a chave recebida por forma (RF-09) | **Must** | É o único controle sobre o arquivo; a ausência reabre o `BUG-20260929-QMLY` |
| Construir o estado e o grafo (RF-11 a RF-14) | **Must** | Sem isso, as outras duas units não têm dado |
| Preservar a extensão no nome visível (RF-05) | **Must** | Fixá-la em `.ged` **quebrou** a análise de DNA (regressão do QMLY) |
| Teto de 16 MB com 413 (RF-10) | **Must** | Impede que o dado chegue ao disco antes da defesa |
| `get_name` devolver `""` (RF-17) | **Should** | Essencial para paridade, mas o caso só aparece em dado real específico |
| Gravação idempotente (RF-07) | **Should** | Há alternativa (reescrever), com custo de I/O e mudança de `mtime` |
| Autoridade única de mojibake (RF-16) | **Should** | Com duas cópias o sistema funcionava — e divergia em 5 de 9 casos |
| Ancoragem da pasta de upload (RF-19) | **Should** | O caminho relativo funcionava até o diretório corrente mudar |
| Limpeza de mojibake em si | **Could** | Acionada apenas quando o arquivo vem corrompido |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
| --- | --- | --- |
| `src/app.py` | `index` ramo `upload_gedcom` `:111-124`; `_guardar_upload` `:70-91`; `_resolver_caminho_armazenado` `:94-103`; `_pasta_uploads` `:37-52`; `_requisicao_grande` `:60-67` | 🟢 |
| `src/utils/validate.py` | `validar_conteudo_gedcom` `:90-105`; `chave_de_armazenamento` `:68-70`; `nome_do_arquivo_armazenado` `:73-75`; `nome_visivel_seguro` `:40-65`; `chave_recebida_e_valida` `:78-87` | 🟢 |
| `src/parsers/gedcom_parser.py` | `load_gedcom_and_build_graph` `:50-69`; `build_graph_from_parser` `:18-48` | 🟢 |
| `src/core/gedcom_state.py` | `people`, `families`, `graph`, `child_to_family`, `versao` `:20-30`; `ref_id` `:33-36`; `get_name` `:38-52` | 🟢 |
| `src/utils/text_cleaning.py` | `strip_bad_utf` `:37`; `demojibake` `:56` | 🟢 |
| `src/templates/index.html` | formulário de upload e campo oculto `gedcom_filename` | 🟢 |
| `tests/test_upload.py`, `tests/test_upload_seguranca.py`, `tests/test_domain.py` | cobertura do núcleo, da segurança do upload e da limpeza | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
