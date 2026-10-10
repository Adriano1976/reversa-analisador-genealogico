# Unit `upload-gedcom` — Requisitos

> Unit do tipo **endpoint** — cobre `POST /` com `action=upload_gedcom`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**).
> Substitui a versão de 2026-10-05, que descrevia o **estado global** em `core/gedcom_state.py`, a validação da referência **por alfabeto fechado** e a **ausência de reenvio**. Snapshot: `.reversa/snapshots/2026-10-10-pre-reextracao/upload-gedcom/`
> Fontes: `code-analysis.md` §2 (22 regras `BR-U-*`), `flowcharts/upload-gedcom.md`, `data-dictionary.md` §2, §3 e §8, `domain.md` §3.5, `adrs/` (06, 07, 11, 17, 24, 26, 30, 31, 32)
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

Recebe um arquivo GEDCOM enviado pelo navegador, **decide se ele pode ser gravado**, grava-o sob uma chave derivada do próprio conteúdo, **aposenta as versões anteriores de mesmo nome visível** e devolve a **árvore** como valor ao chamador. É a porta de entrada das demais unidades: sem `upload-gedcom`, não há `analise-dna` nem `busca-caminho`. 🟢

A unit resolve quatro problemas ao mesmo tempo: **segurança do que entra em disco**, **continuidade entre requisições sem sessão**, **fidelidade de parsing ao legado** e **substituição de versão sem apagar nada**. 🟢

> ⚠️ **O que mudou desde 2026-10-05.** A unit **deixou de publicar estado**: a árvore é o **retorno** do parse e entra por parâmetro em todo o núcleo (`ADR-24`). Ganhou o **reenvio com substituição** (`RN-17`), a **aposentadoria** de versões anteriores (`ADR-30`) e a **validação da referência por forma de nome** em vez de alfabeto fechado (`ADR-32`). E o acesso a disco saiu da rota para a **porta** (`ADR-25`).

## Responsabilidades

- Decidir se o conteúdo recebido é um GEDCOM aceitável, **antes** de qualquer gravação. 🟢
- Derivar a chave de armazenamento do **conteúdo** e compor o nome em disco preservando a extensão original. 🟢
- Gravar de forma **idempotente** (mesmo conteúdo não reescreve) e devolver o **caminho completo**. 🟢
- **Detectar reenvio** e declarar o desfecho: `novo`, `identico` ou `substituido`. 🟢
- **Aposentar** — mover para `_aposentados/` — as versões anteriores de mesmo nome visível, **sem apagar nada**. 🟢
- Resolver, em requisições seguintes, o arquivo a partir da **referência recebida no formulário**, validada por **forma de nome**. 🟢
- Parsear `INDI`/`FAM` e devolver `(people, families, graph, child_to_family)` **como valor**. 🟢
- Devolver a **lista ordenada de nomes** da árvore, que alimenta os formulários das outras unidades. 🟢
- Ser a **autoridade única** da limpeza de mojibake de nomes. 🟢

## Regras de Negócio

- **A validação é de conteúdo, não de extensão.** Um GEDCOM legítimo sem `.ged` é aceito; o `RISK-007` autoriza o relaxamento para não quebrar a paridade de parsing com o oráculo. 🟢
- **GEDCOM aceitável** = depois de remover **um** BOM UTF-8 e os espaços à esquerda, o conteúdo começa com `0 HEAD`. 🟢
- **Conteúdo vazio** é recusado com `arquivo vazio`; **byte NUL** é recusado com `conteudo binario`. 🟢
- **A mensagem de recusa de conteúdo é FIXA** (`RN-18`): as três recusas têm o **mesmo texto** — `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."` —, a pedido do operador. O motivo **não se perdeu**: continua dentro da exceção, a um `str(erro)` de distância de quem depura. 🟢
- **A chave de armazenamento é o sha256 do conteúdo truncado em 16 hexadecimais** — não um UUID aleatório. Mesmo conteúdo, mesma chave, porque o formulário devolve o valor no `POST` seguinte. 🟢
- **O nome do cliente nunca compõe o caminho.** Ele vira metadado legível **depois** da chave; a pasta é sempre a resolvida pela porta. 🟢
- **No nome visível**, `/`, `\` e NUL viram `_`; acentos, espaços e a **extensão original** são preservados. Nome vazio ou só pontos vira `arvore.ged`; nome sem extensão recebe `.ged`. 🟢
- **A elegibilidade da referência é por FORMA DE NOME, e não por alfabeto fechado.** O alfabeto `^[0-9a-f]{16}__[A-Za-z0-9._-]+$` recusava acento e espaço — que o gravador **preserva de propósito** —, e **três arquivos com acento e um com espaço** da pasta real ficaram inalcançáveis, com a tela dizendo que **não existiam** (`BUG-20261009-6RKP` / `RN-20`). 🟢
- **São duas perguntas, e portanto duas funções:** `chave_recebida_e_valida` responde *"tem chave?"* e é o que a **leitura** exige; `referencia_de_arquivo_da_pasta` responde *"posso tratar como nome da pasta?"* e é o que a **aposentadoria** exige. `resolver` **não** afrouxou. 🟢
- **O reenvio tem três desfechos com mensagem própria** (`RN-17`): `identico` (a mesma referência já estava lá), `substituido` (havia versão anterior de mesmo nome visível, e ela foi aposentada) e `novo` (nome visível inédito). O literal congelado `"Arquivo '{nome}' carregado!"` é preservado no caminho comum. 🟢
- **A ordem da `RN-17` é a regra: listar ANTES de guardar.** Só a **foto de antes** separa "já existia" de "acabou de nascer", porque `guardar` **não sobrescreve**. 🟢
- **Aposentar move, e nunca apaga** (`RN-14`): o arquivo vai para `<pasta>/_aposentados/`, inteiro e com o mesmo nome. Havendo colisão, um sufixo `.1`…`.99` é acrescentado; esgotadas as 99 tentativas, a operação **desiste** em vez de sobrescrever. 🟢
- **Arquivo já existente com a mesma chave não é reescrito.** 🟢
- **O caminho de escrita e o de leitura são o mesmo, sempre** — a pasta é ancorada no arquivo do app, e não no diretório corrente. 🟢
- **A árvore entra e sai por parâmetro.** O parse **não** substitui estado global: ele **devolve** a tupla `(people, families, graph, child_to_family)`. Não há contador de versão nem mutação *in place*. 🟢
- **`get_name` devolve string vazia** quando o registro tem `Name` e o formato resulta vazio; o literal `Sem Nome` só aparece quando **não há** `name`. Isso **ocorre em dado real** (**301** de 35.460 pessoas em `Arvore_Unificada_Oficial_V1_2.ged`, medido em 2026-10-10 nas três cópias da árvore; o `296` que circulava vinha do harness de paridade de 2026-09-28 e media **divergências do `DIV-001`**, não nomes vazios) e **não deve ser "melhorado"**: é contrato de paridade com o oráculo congelado (`DIV-001`). 🟢
- **Família sem `xref_id` é ignorada por completo**; arestas só são criadas para nós existentes no grafo. 🟢
- **A lista de nomes devolvida é ordenada** e tem exatamente um item por pessoa carregada. 🟢
- **O `dono` entra sem comportamento.** Ele é parâmetro obrigatório de **todos** os métodos da porta e **não** participa da chave, do nome armazenado nem do caminho: dois envios do mesmo conteúdo por donos diferentes reencontram o **mesmo** arquivo (`RN-02`). 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Receber `POST` com `action=upload_gedcom`, exigindo o campo `gedcom` em `request.files` e `filename` não vazio | Must | Sem o campo → `"Nenhum arquivo GEDCOM enviado."`; `filename` vazio → `"Nenhum arquivo selecionado."`; ambos com `success=False` 🟢 |
| RF-02 | Ler o conteúdo **inteiro** e validá-lo **antes** de qualquer gravação | Must | Nenhum byte chega ao disco quando o conteúdo é recusado 🟢 |
| RF-03 | Recusar conteúdo vazio, com byte NUL, ou que não comece com `0 HEAD` após BOM e espaços, com **mensagem única e fixa** | Must | Os três casos produzem `"Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."`; o motivo permanece acessível por `str(erro)` 🟢 |
| RF-04 | Derivar a chave de armazenamento do conteúdo: `sha256(conteudo).hexdigest()[:16]` | Must | Mesmo conteúdo reenviado produz exatamente a mesma chave 🟢 |
| RF-05 | Compor o nome em disco como `<chave>__<nome visível>`, **preservando a extensão original** | Must | Enviar `matches.csv` gera `<chave>__matches.csv`, **nunca** `<chave>__matches.csv.ged` 🟢 |
| RF-06 | Sanear o nome visível: `/`, `\` e NUL viram `_`; acentos e espaços preservados; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged` | Must | `../../etc/passwd` não produz separador algum no nome resultante 🟢 |
| RF-07 | Gravar de forma idempotente: não reescrever arquivo existente com a mesma chave | Should | Segundo envio do mesmo conteúdo não altera o arquivo em disco 🟢 |
| RF-08 | Devolver o **caminho completo** do arquivo gravado, e não o nome | Must | A leitura seguinte usa exatamente o que foi escrito, sem remontar caminho 🟢 |
| RF-09 | Resolver a referência recebida aceitando **apenas** a forma canônica com chave, e **antes** de qualquer acesso ao disco | Must | Referência sem chave, com separador de caminho ou ausente → `None`; arquivo inexistente → `None` 🟢 |
| RF-10 | Recusar corpo de requisição acima de 16 MB com `HTTP 413` e mensagem em português | Must | Resposta `413` com `"Arquivo maior que o limite de 16 MB."` e nenhum byte gravado 🟢 |
| RF-11 | Parsear os registros `INDI` e `FAM` e indexá-los por `xref_id` em `people` e `families` | Must | Cada `xref_id` do arquivo aparece no dicionário correspondente 🟢 |
| RF-12 | Construir o grafo bipartido pessoa↔família, com aresta para `HUSB`, `WIFE` e cada `CHIL` existente | Must | Nó de pessoa com `type="person"`, de família com `type="family"`; nenhuma aresta para id inexistente 🟢 |
| RF-13 | Manter `child_to_family` como **lista** de famílias por filho | Must | Pessoa filha em duas famílias aparece com as duas entradas 🟢 |
| RF-14 | **Devolver a árvore como valor**, sem publicar nem substituir estado de processo | Must | Duas chamadas ao parse produzem **dois** objetos independentes; nenhuma variável de módulo é escrita 🟢 |
| RF-15 | Devolver a lista de nomes **ordenada**, com um item por pessoa carregada | Must | A lista é igual à sua própria versão ordenada, e a contagem igual à de `people` 🟢 |
| RF-16 | Ser a **autoridade única** da limpeza de mojibake: `strip_bad_utf` e `demojibake` | Must | Nenhum outro módulo do projeto define limpeza própria 🟢 |
| RF-17 | Devolver `""` — e **não** `Sem nome` — quando o registro tem `Name` com formato vazio | Must | Paridade com o oráculo congelado preservada 🟢 |
| RF-18 | Converter falha de parse em mensagem própria, sem deixar arquivo parcial utilizável | Should | `"Erro: o arquivo 'X' não pôde ser lido como GEDCOM. Ele pode estar corrompido, vazio, ou não ser um GEDCOM de verdade."` 🟢 |
| RF-19 | Ancorar a pasta de upload no arquivo do app, com sobreposição por variável de ambiente | Should | `ANALISADOR_UPLOAD_FOLDER` redireciona a pasta; escrita e leitura usam o mesmo caminho 🟢 |
| RF-20 | Declarar o desfecho do reenvio: `novo`, `identico` ou `substituido` | Must | Mesmo arquivo duas vezes → `identico`; mesmo nome com conteúdo novo → `substituido`; nome inédito → `novo` 🟢 |
| RF-21 | Aposentar **todas** as versões anteriores de mesmo nome visível, movendo-as para `_aposentados/` | Must | Após o reenvio, a lista tem **um** item com aquele rótulo e o anterior continua no disco 🟢 |
| RF-22 | Nunca sobrescrever um aposentado de mesmo nome: acrescentar sufixo `.1`…`.99` e **desistir** no esgotamento | Must | Dois reenvios com o mesmo nome visível produzem `<nome>` e `<nome>.1` em `_aposentados/` 🟢 |
| RF-23 | Validar a elegibilidade da referência por **forma de nome**, em duas funções distintas para ler e para aposentar | Must | Referência com acento ou espaço **é elegível** para aposentar; sem chave **não** é elegível para ler 🟢 |
| RF-24 | Aceitar `dono` em todos os métodos do armazenamento sem que ele altere comportamento algum | Must | Dois envios do mesmo conteúdo com donos diferentes reencontram o mesmo arquivo 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| --- | --- | --- | --- |
| Segurança | A defesa contra escape de caminho é por **forma de nome**, **antes** de qualquer `os.path.exists` | `src/utils/validate.py` (`chave_recebida_e_valida`, `referencia_de_arquivo_da_pasta`) | 🟢 |
| Segurança | A aposentadoria confere que o `dirname` do caminho resolvido é **exatamente** a pasta de upload — segunda camada que não confia na primeira | `src/ports/adaptadores.py:aposentar` | 🟢 |
| Segurança | O teto de corpo é aplicado **antes** de ler o corpo da requisição | `src/app.py:TETO_DE_UPLOAD_EM_BYTES` | 🟢 |
| Segurança | 🔴 **O `dono` **não** isola nada:** não entra na chave, no nome nem no caminho. As dívidas #3 e #4 seguem abertas | `src/ports/adaptadores.py`; `permissions.md` §1.1 | 🟢 |
| Reprodutibilidade | Mesmo conteúdo → mesma chave, estável entre requisições e entre processos | `src/utils/validate.py:chave_de_armazenamento` | 🟢 |
| Confiabilidade | Gravação idempotente e **nunca destrutiva**: arquivo existente não é reescrito e nada é apagado pelo sistema | `src/ports/adaptadores.py:guardar` e `:aposentar` | 🟢 |
| Confiabilidade | O **conteúdo** do arquivo é imutável; o que muda é a **posição** (pasta ↔ `_aposentados/`) | `state-machines.md` §7 | 🟢 |
| Manutenibilidade | A decisão de gravação vive em módulo **puro** — não importa Flask e não toca o disco | `src/utils/validate.py` | 🟢 |
| Manutenibilidade | O import de `src/app.py` **não pode** exigir driver de banco, rede nem biblioteca de imagem: a suíte e o harness de paridade o importam | `src/app.py`; `adrs/27` | 🟢 |
| Performance | `listar` **não abre arquivo nenhum**: do diretório lê o nome e do arquivo apenas tamanho e data | `src/ports/adaptadores.py:listar` | 🟢 |
| Performance | A árvore é **parseada a cada requisição**; não há cache entre requisições | `src/app.py` | 🟢 |
| Internacionalização | Todas as mensagens ao operador são literais em português | `src/app.py`, `src/application/traducao.py` | 🟢 |
| Observabilidade | **Nenhum log, métrica ou trace é emitido.** A única saída textual é o `print` de inicialização | `src/app.py:__main__` | 🟢 |
| Portabilidade | `SO_EXCLUSIVEADDRUSE` só existe no Windows; fora dele o padrão da plataforma já recusa a segunda ligação | `src/app.py:__main__` | 🟢 |

> Inferido a partir do código. **Não** há middleware de autenticação, cache, fila, worker ou lógica de retry — essas linhas foram omitidas por falta de evidência.

## Critérios de Aceitação

```gherkin
Dado que o operador está na tela inicial
Quando envia um arquivo GEDCOM válido chamado exemplo_familia.ged
Então o arquivo é gravado em src/uploads sob a chave <sha256 truncado>__exemplo_familia.ged
E o desfecho é "novo"
E a tela mostra "Arquivo 'exemplo_familia.ged' carregado!" com success=True
E a lista completa de nomes da árvore é devolvida ao formulário

Dado que o operador envia o MESMO arquivo uma segunda vez
Quando a gravação é executada
Então o arquivo existente NÃO é reescrito
E o desfecho é "identico"
E a mensagem é "Arquivo 'exemplo_familia.ged' já estava armazenado com o mesmo conteúdo: nada mudou."

Dado que o operador envia um arquivo de MESMO nome com conteúdo diferente
Quando a gravação é executada
Então a versão anterior é MOVIDA para src/uploads/_aposentados/
E o desfecho é "substituido"
E a mensagem diz que a versão anterior saiu da lista e continua guardada, inteira
E o arquivo anterior continua no disco, com o mesmo nome e o mesmo conteúdo

Dado que já existe um aposentado com o mesmo nome visível
Quando um terceiro envio é aposentado
Então o destino recebe o sufixo ".1", e não sobrescreve o aposentado anterior

Dado um conteúdo que não começa com a declaração 0 HEAD
Quando o upload é executado
Então a resposta é "Arquivo não reconhecido como GEDCOM. Favor, enviar o arquivo correto."
E nenhum byte é gravado em disco
E success=False

Dado um arquivo de 20 MB
Quando o upload é executado
Então a resposta tem status HTTP 413
E a mensagem é "Arquivo maior que o limite de 16 MB."
E nenhum byte é gravado em disco

Dado um POST de análise com referência igual a ../../etc/passwd
Quando a referência é validada
Então o valor é recusado por forma de nome
E a resposta é "Erro: Arquivo '../../etc/passwd' não existe mais."
E nenhum arquivo fora de src/uploads é aberto

Dado um arquivo da pasta cujo nome visível tem ACENTO e que foi gravado pela aplicação
Quando o operador escolhe esse arquivo na lista
Então a referência é ACEITA (o caso era o BUG-20261009-6RKP)
E a árvore é carregada normalmente

Dado um GEDCOM em que uma pessoa tem Name cujo formato resulta vazio
Quando a árvore é carregada e o nome é lido
Então get_name devolve string vazia
E NÃO devolve o literal "Sem Nome"
E a contagem de nomes continua igual à contagem de pessoas

Dado que duas análises consecutivas usam GEDCOMs diferentes no mesmo processo
Quando a segunda árvore é carregada
Então a primeira árvore permanece intacta e consultável
E nenhuma variável de módulo do núcleo foi escrita
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
| --- | --- | --- |
| Validar conteúdo antes de gravar (RF-02, RF-03) | **Must** | Caminho crítico: toda escrita em disco passa por aqui |
| Chave derivada do conteúdo (RF-04) | **Must** | As outras units dependem dela para a continuidade entre requisições |
| Validar a referência por forma (RF-09, RF-23) | **Must** | É o único controle sobre o arquivo; o afrouxamento indevido reabre o `BUG-20260929-QMLY`, e o exagero reabre o `BUG-20261009-6RKP` |
| Devolver a árvore como valor (RF-14) | **Must** | É o que permite duas árvores coexistirem sem contaminação (`ADR-24`) |
| Construir o grafo e o índice (RF-11 a RF-13) | **Must** | Sem isso, as outras units não têm dado |
| Declarar o desfecho do reenvio (RF-20) | **Must** | Sem ele, a lista mostra duas versões do mesmo arquivo e o operador não sabe qual é a vigente |
| Aposentar versões anteriores (RF-21, RF-22) | **Must** | É o que mantém o rótulo único na lista, **sem apagar** (`RN-07`) |
| Preservar a extensão no nome visível (RF-05) | **Must** | Fixá-la em `.ged` **quebrou** a análise de DNA (regressão do QMLY) |
| Teto de 16 MB com 413 (RF-10) | **Must** | Impede que o dado chegue ao disco antes da defesa |
| `dono` sem comportamento (RF-24) | **Must** | É a costura que a Onda 3 preenche; adiar reabriria toda assinatura de porta |
| `get_name` devolver `""` (RF-17) | **Should** | Essencial para paridade, mas o caso só aparece em dado real específico |
| Gravação idempotente (RF-07) | **Should** | Há alternativa (reescrever), com custo de I/O e mudança de `mtime` |
| Autoridade única de mojibake (RF-16) | **Should** | Com duas cópias o sistema funcionava — e divergia em 5 de 9 casos |
| Ancoragem da pasta de upload (RF-19) | **Should** | O caminho relativo funcionava até o diretório corrente mudar |
| Limpeza de mojibake em si | **Could** | Acionada apenas quando o arquivo vem corrompido |

## Rastreabilidade de Código

| Arquivo | Função / símbolo | Cobertura |
| --- | --- | --- |
| `src/application/upload_gedcom.py` | caso de uso; converte o **motivo em texto** em exceção de domínio tipada (achado `A002`) | 🟢 |
| `src/application/reenvio.py` | `guardar_com_substituicao` — foto de antes, aposentadoria e os três desfechos | 🟢 |
| `src/app.py` | ramo `upload_gedcom` do `index`; `_pasta_uploads`; `_arvore_do_formulario`; handler de `RequestEntityTooLarge`; `_DEPENDENCIAS`, `_REGISTRO`, `DONO_DO_PROCESSO` | 🟢 |
| `src/utils/validate.py` | `validar_conteudo_gedcom`, `chave_de_armazenamento`, `nome_do_arquivo_armazenado`, `nome_visivel_seguro`, `chave_recebida_e_valida`, `referencia_de_arquivo_da_pasta`, `pode_ser_usado`, `motivo_de_indisponibilidade` | 🟢 |
| `src/ports/adaptadores.py` | `ArmazenamentoEmDisco.guardar`/`resolver`/`listar`/`aposentar`, `CarregadorDeArvoresGedcom.carregar`, `PASTA_DE_APOSENTADOS` | 🟢 |
| `src/ports/__init__.py` | `ArmazenamentoDeArquivos`, `CarregadorDeArvores`, `RepositorioDeArvores`, `EntradaArmazenada` | 🟢 |
| `src/parsers/gedcom_parser.py` | `carregar_arvore` (devolve a tupla), construção do grafo e de `child_to_family` | 🟢 |
| `src/core/registro.py` | `get_name`, `ref_id` | 🟢 |
| `src/core/erros.py` | `ErroDeDominio`, `GedcomNaoSuportado` | 🟢 |
| `src/application/traducao.py` | `_gedcom_nao_suportado` (mensagem fixa da `RN-18`) | 🟢 |
| `src/utils/text_cleaning.py` | `strip_bad_utf`, `demojibake` | 🟢 |
| `tests/test_upload.py`, `tests/test_upload_seguranca.py`, `tests/test_forma_da_referencia.py`, `tests/test_reenvio_do_arquivo.py`, `tests/test_aposentar_arquivo.py`, `tests/test_porta_de_armazenamento.py` | cobertura do núcleo, da segurança, da forma da referência, do reenvio e da porta | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração, nível completo).*
