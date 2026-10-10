# Unit `tela-de-entrada` — Requisitos

> Unit do tipo **endpoint** — cobre `GET /` (a montagem da tela de entrada), `POST /` com `action=aposentar_arquivo` e `POST /` com `action=selecionar_arvore`.
> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**).
> Unit **nova**: esta é a sua primeira especificação. Ela nasceu nas features `011-escolher-arquivo-da-lista` e `012`, e **não tem equivalente** nas extrações de 2026-08-03, 2026-09-30 e 2026-10-05 — nelas a rota `GET /` era só um formulário de envio.
> Fontes: `code-analysis.md` §3 (19 regras `BR-T-01`..`BR-T-19`), `flowcharts/tela-de-entrada.md`, `data-dictionary.md` §5, `domain.md` §3, `state-machines.md` §2, `permissions.md` §2, `adrs/` 25, 26, 27, 30, 32
> Evidência de execução (2026-10-10): suíte **527 passam / 9 pulados / 0 falham**; **8** arquivos de teste cobrem esta unit (`test_lista_de_arquivos.py`, `test_lista_na_tela.py`, `test_aposentar_arquivo.py`, `test_voltar_para_a_lista.py`, `test_tabela_da_tela.py`, `test_porta_de_armazenamento.py`, `test_manutencao_de_uploads.py`, `test_gedcom_ilegivel_nao_derruba.py` — **132 testes**). ⚠️ **Corrigido em 2026-10-10 pelo Revisor:** o oitavo arquivo faltava nesta lista embora a própria `tasks.md` o cite (TT-12) e a `code-spec-matrix.md` o atribua a esta unit; o número anterior era "7 arquivos / 126 testes".
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Visão Geral

É a **tela inicial** do sistema e a única superfície de **escolha** de arquivos. Ela entrega, em toda renderização, as **duas abas** já preenchidas com o que está guardado na pasta de upload — árvores GEDCOM de um lado, relatórios de matches do outro — e trata as duas ações que a lista oferece: **aposentar** um arquivo (tirá-lo da lista sem apagá-lo) e **escolher** uma árvore para trabalhar. 🟢

A unit existe porque a aplicação **não tem sessão nem identificador público de árvore**: a continuidade entre requisições é feita pelo valor que a tela devolve no campo oculto `gedcom_filename`, e o insumo de toda análise é um arquivo que o operador precisa **ver** antes de escolher. 🟢

Ela resolve três problemas de uma vez: **montar a lista sem ler 29 MB de conteúdo a cada renderização**, **mostrar o arquivo que a referência não alcança em vez de escondê-lo**, e **aposentar sem apagar**. 🟢

## Responsabilidades

- Entregar as **duas listas** de arquivos armazenados em **toda** renderização de `index.html`, por processador de contexto. 🟢
- Ler a pasta **pela porta** (`listar`) — nome, tamanho e data por `os.stat`, **sem abrir arquivo**. 🟢
- Particionar os arquivos em duas abas pela **extensão do nome visível cru**. 🟢
- **Agrupar** arquivos que compartilham a mesma chave de conteúdo e escolher o **representante** do grupo. 🟢
- Produzir o **rótulo de tela** sem vazar a chave de conteúdo. 🟢
- Decidir e **exibir** a disponibilidade de cada item, com o **motivo** da indisponibilidade. 🟢
- Ordenar os itens por **data decrescente** e formatar data e tamanho para leitura humana. 🟢
- Tratar `action=aposentar_arquivo`: mover o arquivo para `_aposentados/` e responder o desfecho em português. 🟢
- Tratar `action=selecionar_arvore`: resolver a árvore clicada e renderizar o estado "árvore aberta". 🟢
- Ser a **fonte única das guardas de entrada** dos fluxos pós-upload (`_arvore_do_formulario`). 🟡 *(a função é compartilhada com `analise-dna` e `busca-caminho`; ver a ressalva de fronteira em `design.md`)*

## Regras de Negócio

- **As listas são entregues SEMPRE**, por processador de contexto, e não só depois de um envio (`BR-T-01`). A rota tem 23 `render_template`; repetir o argumento em cada um seria 23 lugares para esquecer um. 🟢
- **Quem lê o diretório é a porta** (`BR-T-02`). Não há `os.listdir` na rota: a borda não acessa disco. 🟢
- **A aba de um arquivo é decidida pela extensão do nome visível CRU** (`BR-T-03`): `planilha.csv.ged` entra na aba de árvores mesmo tendo conteúdo de CSV, e o `.xlsx` da pasta real não entra em aba nenhuma. Quem recusa conteúdo é o **uso**, não a listagem. 🟢
- **Arquivos com a mesma chave de conteúdo são UM item** (`BR-T-04`), e o representante é o de **maior `mtime`**. 🟢
- **Arquivo SEM chave vira item próprio e nunca é agrupado** (`BR-T-05`): a chave não o alcança, e lê-lo para agrupar custaria os 29 MB que a listagem evita. Dois arquivos sem chave nunca caem no mesmo item. 🟢
- **O rótulo do grupo prefere um nome visível SEM chave** (`BR-T-06`), porque exibir a chave crua é pior do que exibir um rótulo sem ela. 🟢
- **O rótulo tira apenas a ÚLTIMA extensão** (`BR-T-07`): `planilha.csv.ged` vira `planilha csv` — o `.csv` do meio é informação, e é o único sinal que sobra de que aquele `.ged` é, no conteúdo, um relatório. Ponto inicial não é extensão: `.ged` não vira rótulo vazio. 🟢
- **O rótulo troca símbolos por espaço** (`RN-13`): `Famílias_Sergipanas.csv` vira `Famílias Sergipanas`, e acentos sobrevivem (`\w` em Python 3 é sensível a acento). 🟢
- **A ordem é `mtime` decrescente, com empate pelo nome exibido** (`BR-T-08`). O nome exibido **não é único** — há três `Arvore_Unificada_Oficial_V1_2` na pasta real — e é a data que distingue; a ordenação é estável para não depender da ordem de leitura do diretório. 🟢
- **A data vem de `os.stat` e a coluna se chama "Enviado em"** (`BR-T-09`). Para arquivo guardado pela aplicação essa é a data do envio, porque a gravação é a única coisa que toca o arquivo; o cabeçalho carrega `title` dizendo de onde o número vem, em vez de prometer mais do que entrega. 🟢
- **Instante que o sistema não converte devolve CÉLULA VAZIA, e não `500`** (`BR-T-09`): um `OverflowError`/`OSError` numa célula não pode derrubar a tela que lista tudo. 🟢
- **A disponibilidade é decidida pela MESMA função que o resolvedor usa** (`BR-T-10`): `pode_ser_usado` → `chave_recebida_e_valida`. Dois testes equivalentes divergem com o tempo, e a tela passaria a dizer "disponível" para um arquivo que a leitura recusa. 🟢
- **O item indisponível APARECE marcado, com o motivo** (`BR-T-11`). Esconder o inalcançável tiraria do operador justamente o arquivo que ele mais quer aposentar. 🟢
- **Os dois motivos são distintos**: `sem chave de conteúdo no nome` (arquivo anterior à chave por conteúdo) e `nome com caractere que a referência não aceita`. Dizer "sem chave" para o arquivo acentuado seria **mentir sobre o motivo**, e o operador concluiria que o arquivo é antigo quando não é. 🟢 *(ressalva de alcance atual em `design.md` § Riscos, lacuna `L-30`)*
- **`aposentar_arquivo` é tratado ANTES da resolução da árvore do formulário** (`BR-T-12`), e a ordem é a regra, não estilo: `_arvore_do_formulario` resolve e **parseia** a árvore escolhida, e a árvore escolhida pode ser exatamente a que se está aposentando — depois do move, o parse falharia e o operador veria "arquivo não existe mais" no lugar da confirmação. 🟢
- **Aposentar bem-sucedido diz que o arquivo saiu da lista e NÃO foi apagado** (`BR-T-13`); o fracasso diz que ele não está mais na pasta. 🟢
- **`selecionar_arvore` renderiza o MESMO estado do envio** (`BR-T-14`), com `gedcom_filename` e `all_names`. Sem o ramo, o `action` cairia no `return` final de `index()`, que renderiza **sem** `gedcom_filename`: a árvore resolvida seria descartada e o clique não faria nada — o defeito medido em 2026-10-09. 🟢
- **Nenhuma ação da lista escreve arquivo além do move de aposentar** (`BR-T-16`). 🟢
- **O nome visível da árvore aberta vem por FILTRO de template** (`BR-T-17`, `rotulo_do_arquivo`), não por parâmetro repetido nas renderizações — pelo mesmo motivo das listas: um argumento a mais em cada `render_template` é um lugar a mais para esquecer um. 🟢
- **O rótulo exibido NÃO contém a chave de conteúdo** (`BR-T-18`, `D-09`). O operador vê o **nome**; a chave é assunto do armazenamento. 🟢
- **A quantidade do grupo é o número de ARQUIVOS, e o tamanho é a SOMA dos bytes do grupo** (`BR-T-19`). 🟡 *(o grupo conta arquivos, e não versões úteis: se o operador copiar dois arquivos de mesmo nome e conteúdos diferentes à mão, o grupo volta a ter dois)*
- **A aba de DNA não oferece envio nem "Abrir"**: não existe ação que guarde um CSV sozinho — o relatório entra pela análise de DNA, que exige uma árvore. Oferecer "Abrir" prometeria o que a rota não atende. 🟢
- **A pasta é a superfície de confiança da tela**: a listagem **não filtra nada**, por decisão — nem por nome, nem por extensão, nem por forma da chave. Um arquivo colocado ali por fora da aplicação aparece na lista. 🔴

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
| --- | --- | --- | --- |
| RF-01 | Entregar as duas listas (`arvores_da_lista`, `relatorios_da_lista`) em **toda** renderização de `index.html`, por processador de contexto | Must | `GET /` com a pasta vazia e `GET /` com 13 arquivos produzem as duas chaves no contexto do template 🟢 |
| RF-02 | Ler a pasta **somente** pela porta `listar`, com `os.stat` por entrada e **nenhum `open`** | Must | Nenhum `os.listdir` existe em `app.py`; renomear a pasta faz `listar` devolver `[]` e a tela continuar de pé 🟢 |
| RF-03 | Decidir a aba pela extensão do **nome visível cru** (`endswith`) | Must | `planilha.csv.ged` aparece na aba de árvores; `.xlsx` não aparece em nenhuma aba 🟢 |
| RF-04 | Agrupar por chave de conteúdo, com o representante sendo o de **maior `mtime`** | Must | Dois nomes com a mesma chave produzem **um** item, e os metadados exibidos são os do mais recente 🟢 |
| RF-05 | Tratar arquivo **sem** chave como item próprio, nunca agrupado | Must | Três arquivos sem chave produzem **três** itens 🟢 |
| RF-06 | Escolher o rótulo do grupo preferindo um nome visível **sem** chave | Must | Grupo com um nome chaveado e um limpo exibe o limpo; grupo só com chaveados exibe o primeiro em ordem alfabética, sem a chave 🟢 |
| RF-07 | Limpar o rótulo: remover **só a última** extensão e trocar símbolos por espaço | Should | `Backup-Arvore-Sandro-12-11-2024.ged` → `Backup Arvore Sandro 12 11 2024`; `planilha.csv.ged` → `planilha csv`; `.ged` permanece `.ged` e nunca vira vazio 🟢 |
| RF-08 | Ordenar os itens por `mtime` decrescente, com empate pelo nome exibido | Should | A ordem não muda entre duas leituras do mesmo diretório 🟢 |
| RF-09 | Formatar a coluna "Enviado em" de `os.stat`, devolvendo **célula vazia** quando o instante não converte | Must | `formatar_data_br` de um valor fora do alcance devolve `""` e a resposta continua `200` 🟢 |
| RF-10 | Decidir `disponivel` pela **mesma** função que o resolvedor usa (`pode_ser_usado`) | Must | Um nome recusado pelo resolvedor aparece como indisponível na lista 🟢 |
| RF-11 | Exibir o item indisponível **marcado**, com o motivo textual ao lado | Must | Item indisponível continua na tabela, com `⚠` e o texto do motivo 🟢 |
| RF-12 | Tratar `action=aposentar_arquivo` **antes** de resolver a árvore do formulário | Must | Aposentar a árvore atualmente aberta devolve a confirmação, e não "não existe mais" 🟢 |
| RF-13 | Responder o desfecho de aposentar em português, com os literais congelados | Must | Sucesso: `'ROTULO' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados.`; fracasso: `Não foi possível aposentar o arquivo: ele não está mais na pasta.` 🟢 |
| RF-14 | Tratar `action=selecionar_arvore` renderizando o mesmo estado do envio | Must | A resposta contém `gedcom_filename` e `all_names`; a tela mostra "Árvore aberta: ROTULO" 🟢 |
| RF-15 | Responder `Erro: Arquivo 'ROTULO' não existe mais.` quando a referência **não resolve** | Must | Referência com forma válida e arquivo ausente produz essa mensagem, com o **rótulo**, e não a chave 🟢 |
| RF-16 | Não escrever arquivo em nenhuma ação da lista, além do `os.replace` de aposentar | Must | `GET /` e `selecionar_arvore` não alteram `mtime` de nenhum arquivo da pasta 🟢 |
| RF-17 | Obter o nome visível da árvore aberta por **filtro de template** (`rotulo_do_arquivo`) | Should | A tela aberta exibe o nome **sem** os 16 hexadecimais, em qualquer uma das renderizações 🟢 |
| RF-18 | Exibir, por item, a **quantidade de arquivos** do grupo e a **soma dos bytes** | Must | Grupo de dois arquivos mostra `2` e a soma exata dos tamanhos 🟢 |
| RF-19 | Oferecer o botão **Abrir** apenas no item disponível da aba de árvores; a aba de DNA **não** ganha esse botão | Must | Item indisponível não tem formulário `selecionar_arvore`; a aba de DNA não tem nenhum 🟢 |
| RF-20 | Oferecer o botão **Apagar** em **todo** item, inclusive no indisponível, com confirmação no navegador | Must | O `onsubmit` pergunta `Apagar "ROTULO"? Ele sai da lista e continua guardado no disco, na pasta de aposentados.` 🟢 |
| RF-21 | Renderizar estado vazio próprio por aba, e **não** oferecer envio na aba de DNA | Should | Árvores vazias: `Nenhuma árvore armazenada ainda. Envie uma para começar.`; relatórios vazios: parágrafo que orienta para a aba de árvores; nenhum `<form>` de upload na aba de DNA 🟢 |
| RF-22 | Manter as abas e seus rótulos **idênticos** antes e depois de escolher a árvore | Should | Os dois ramos do template usam o mesmo markup: `Buscar Conexão no GEDCOM` e `Analisador de DNA` 🟢 |
| RF-23 | Não derrubar a requisição quando o GEDCOM alcançado pela referência **não pode ser lido**: mensagem em português + `app.logger.exception` | Must | `POST /` com `gedcom_filename` apontando para CSV real devolve a mensagem de arquivo ilegível e **não** `500` 🟢 |
| RF-24 | Responder `Erro: Arquivo GEDCOM não encontrado.` quando o `POST` chega **sem** `gedcom_filename` | Must | `POST /` com `action=dna_analysis` e sem o campo devolve essa mensagem 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | A listagem **não abre arquivo**: só `os.listdir` + `os.stat`, para montar a tela sem reler os ~29 MB da pasta a cada renderização | `ports/adaptadores.py:143-162`, `reporting/lista_de_arquivos.py:19-27` | 🟢 |
| Robustez | Três degradações silenciosas em vez de erro: pasta ausente → `[]`; entrada que sumiu entre `listdir` e `stat` → pulada; data inconversível → célula vazia | `ports/adaptadores.py:143-156`, `lista_de_arquivos.py:140-143` | 🟢 |
| Segurança | Aposentar tem defesa de escape em **duas camadas**: `referencia_de_arquivo_da_pasta` (recusa caminho, `..`, vazio) e a conferência de que o diretório pai do caminho resolvido é **exatamente** a pasta de upload | `utils/validate.py:216-247`, `ports/adaptadores.py:193-200` | 🟢 |
| Segurança | A rota **não tem autenticação alguma**: qualquer cliente que alcance a porta lista, abre e aposenta arquivos. O padrão de escuta é `127.0.0.1`, e atender a rede é ato explícito de quem opera | `app.py:540-541`, `permissions.md` §2 | 🟢 |
| Observabilidade | **Um** log na unit: `app.logger.exception` quando o GEDCOM alcançado não pode ser lido. Nenhuma métrica, nenhum log de listagem ou de aposentadoria | `app.py:228` | 🟢 |
| Escalabilidade | `listar` roda **a cada renderização**, sem cache, em `O(n)` sobre a pasta — aceitável para 13 arquivos, não medido em pasta grande | `app.py:349`, `ports/adaptadores.py:146-162` | 🟡 |
| Usabilidade | A coluna de data carrega `title` declarando que o valor é a data de modificação no disco: o rótulo não promete mais do que entrega | `templates/index.html:158`, `:240` | 🟢 |

> Inferido a partir do código. Validar com a equipe de operações — em especial a ausência de autenticação e a ausência de log de aposentadoria.

## Critérios de Aceitação

```gherkin
Dado que a pasta de upload contém árvores e relatórios de matches
Quando o operador abre GET /
Então as duas abas aparecem com suas listas já preenchidas, sem nenhum envio prévio

Dado um grupo de dois arquivos com a mesma chave de conteúdo
Quando a lista é montada
Então eles aparecem como UM item, com a quantidade 2 e o tamanho igual à soma dos bytes

Dado um arquivo sem os 16 hexadecimais no nome
Quando a lista é montada
Então ele aparece como item próprio, marcado com "sem chave de conteúdo no nome", e continua na tabela

Dado um arquivo cujo nome visível tem acento, com chave válida
Quando a lista é montada
Então ele aparece disponível e o rótulo exibido não contém a chave

Dado um arquivo na pasta e o formulário da lista
Quando o operador confirma "Apagar"
Então o arquivo sai da lista, continua íntegro em _aposentados/ e a tela responde que ele não foi apagado

Dado que o operador tenta aposentar um arquivo que já não está na pasta
Quando o POST chega com action=aposentar_arquivo
Então a tela responde "Não foi possível aposentar o arquivo: ele não está mais na pasta." com success=False

Dado um item disponível na aba de árvores
Quando o operador clica em "Abrir"
Então a tela mostra "Árvore aberta: ROTULO" e o formulário das outras abas passa a ter a árvore

Dado um arquivo de conteúdo ilegível pelo parser, alcançado pela referência
Quando o POST chega com esse gedcom_filename
Então a tela responde que o arquivo não pôde ser lido como GEDCOM e o traceback vai para o log, nunca para a tela
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-01, RF-02 — as duas listas, lidas pela porta | Must | É a razão de existir da unit; sem elas não há como escolher arquivo nenhum |
| RF-03, RF-04, RF-05 — partição e agrupamento | Must | Sem eles a lista mostraria itens duplicados ou misturados, e o operador escolheria o arquivo errado |
| RF-10, RF-11 — disponibilidade e motivo | Must | Impede a tela de oferecer como funcional um item que a referência não alcança |
| RF-12, RF-13 — aposentar antes de resolver, com mensagem honesta | Must | A ordem errada produz uma confirmação falsa; a mensagem é o único sinal de que o arquivo continua no disco |
| RF-14, RF-15 — escolher a árvore | Must | É a ação que destrava as outras duas units |
| RF-18 — quantidade e tamanho | Must | O nome exibido não é único; sem esses números o operador não distingue dois itens |
| RF-23, RF-24 — não derrubar a requisição | Must | 10 dos 13 arquivos da pasta real derrubavam o parser antes da guarda |
| RF-06, RF-07, RF-17 — rótulo sem chave | Should | Importante para legibilidade e para o `D-09`; o item continua utilizável com um rótulo pior |
| RF-08 — ordenação estável | Should | A leitura fica pior sem ela, mas nenhuma ação depende da ordem |
| RF-09 — data inconversível | Should | O caso não ocorreu em dado real; a degradação é preventiva |
| RF-19, RF-20 — os dois botões | Should | O fluxo alternativo existe: a ação pode ser disparada pelo formulário da aba correspondente |
| RF-21, RF-22 — estados vazios e simetria das abas | Could | Acionados só na primeira execução ou em pasta vazia |
| RF-16 — nenhuma escrita | Could | Garantia verificável, mas não uma funcionalidade que o operador aciona |

> Prioridade inferida por frequência de chamada, posição na cadeia de dependências e presença de testes (**132** testes em **8** arquivos cobrem esta unit).

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `src/reporting/lista_de_arquivos.py` | `itens_da_aba`, `_montar_item`, `_rotulo_do_grupo`, `rotulo_limpo`, `rotulo_de_referencia`, `formatar_data_br`, `ItemDaLista`, `Entrada` | 🟢 |
| `src/app.py` | `_listas_da_tela` (processador de contexto), `index` (ramo `aposentar_arquivo`, ramo `selecionar_arvore`, `GET /`), `_arvore_do_formulario`, filtros `inteiro_br` / `data_br` / `rotulo_do_arquivo` | 🟢 |
| `src/ports/adaptadores.py` | `ArmazenamentoEmDisco.listar`, `ArmazenamentoEmDisco.aposentar` | 🟢 |
| `src/utils/validate.py` | `decompor_nome_armazenado`, `motivo_de_indisponibilidade`, `pode_ser_usado`, `referencia_de_arquivo_da_pasta`, `chave_recebida_e_valida` | 🟢 |
| `src/templates/index.html` | as duas abas, as duas tabelas, os formulários `selecionar_arvore` e `aposentar_arquivo`, os estados vazios | 🟢 |
| `src/ports/__init__.py` | `EntradaArmazenada` (nome, bytes, modificado_em) | 🟢 |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova — não substitui artefato anterior.*
