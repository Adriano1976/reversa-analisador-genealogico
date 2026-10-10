# Unit `tela-de-entrada` — Tarefas de Implementação

> Spec gerada pelo Reversa-Writer na re-extração de **2026-10-10** (nível **Completo**). Unit **nova**.
> Cada tarefa cita o arquivo do legado de onde o comportamento foi extraído. As tarefas descrevem a **reimplementação** da unit a partir do legado, na ordem em que fazem sentido.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] A porta `ArmazenamentoDeArquivos` com os métodos `listar(dono)` e `aposentar(referencia, dono)` disponível, e a pasta de upload resolvida **pela borda** (`ANALISADOR_UPLOAD_FOLDER`, senão `<dir do app>/uploads`) — `ports/adaptadores.py:105-217`, `app.py:115-142` 🟢
- [ ] A autoridade sobre a forma do nome armazenado: `decompor_nome_armazenado`, `chave_recebida_e_valida`, `referencia_de_arquivo_da_pasta`, `motivo_de_indisponibilidade`, `pode_ser_usado` — `utils/validate.py:96-247` 🟢
- [ ] O template com as duas abas e a faixa de alerta, e os filtros `inteiro_br`, `data_br` e `rotulo_do_arquivo` registrados — `templates/index.html`, `app.py:99-110` 🟢
- [ ] Nenhuma variável de ambiente é exigida por esta unit. `DONO_DO_PROCESSO = "unico"` é constante de módulo — `app.py:70` 🟢
- [ ] Sem schema de banco: a unit **não persiste nada**; o único efeito em disco é o `os.replace` de aposentar 🟢

## Tarefas

- [ ] T-01, Implementar a transformação **pura** de entradas da pasta em itens de aba, sem abrir arquivo
  - Origem no legado: `src/reporting/lista_de_arquivos.py:146-178`
  - Critério de pronto: recebe uma lista de objetos com `nome`, `bytes` e `modificado_em` e devolve itens; nenhum `open`, nenhum `os.path` — verificável por teste que passaria em diretório inexistente
  - Confiança: 🟢

- [ ] T-02, Filtrar cada arquivo para a aba pela **extensão do nome visível cru** (`endswith`)
  - Origem no legado: `src/reporting/lista_de_arquivos.py:166-168`
  - Critério de pronto: `arvore.ged` só na aba `.ged`; `planilha.csv.ged` na aba `.ged`; `.xlsx` em nenhuma
  - Confiança: 🟢

- [ ] T-03, Agrupar por **chave de conteúdo** e tratar o arquivo **sem** chave como item próprio
  - Origem no legado: `src/reporting/lista_de_arquivos.py:164-172`
  - Critério de pronto: dois nomes com a mesma chave produzem **um** item; três nomes sem chave produzem **três**
  - Confiança: 🟢

- [ ] T-04, Escolher o **representante** do grupo pelo maior `mtime` e montar o item com quantidade e soma dos bytes
  - Origem no legado: `src/reporting/lista_de_arquivos.py:181-194`
  - Critério de pronto: grupo de dois arquivos mostra quantidade `2` e a soma exata; os metadados de data e tamanho são os do representante
  - Confiança: 🟢

- [ ] T-05, Definir a **disponibilidade** do item pela mesma função que o resolvedor usa
  - Origem no legado: `src/reporting/lista_de_arquivos.py:192-193`, `src/utils/validate.py:205-213`
  - Critério de pronto: existe **uma** implementação de alcance; alterá-la muda lista e resolvedor ao mesmo tempo
  - Confiança: 🟢

- [ ] T-06, Produzir os **dois motivos** de indisponibilidade, distintos entre si
  - Origem no legado: `src/utils/validate.py:160-161`, `:183-202`
  - Critério de pronto: arquivo sem os 16 hexadecimais → `sem chave de conteúdo no nome`; arquivo com chave e parte visível recusada → `nome com caractere que a referência não aceita`
  - Confiança: 🟢 *(ver `L-30`: o segundo motivo ficou praticamente inalcançável desde 2026-10-10)*

- [ ] T-07, Limpar o rótulo: remover **só a última** extensão, trocar símbolos por espaço, preservar acentos
  - Origem no legado: `src/reporting/lista_de_arquivos.py:40`, `:81-107`
  - Critério de pronto: `Famílias_Sergipanas.csv` → `Famílias Sergipanas`; `planilha.csv.ged` → `planilha csv`; `.ged` permanece `.ged`
  - Confiança: 🟢

- [ ] T-08, Escolher o rótulo do grupo preferindo um nome visível **sem** chave
  - Origem no legado: `src/reporting/lista_de_arquivos.py:197-214`
  - Critério de pronto: nenhum rótulo exibido contém 16 hexadecimais seguidos de `__`
  - Confiança: 🟢

- [ ] T-09, Ordenar os itens por `mtime` **decrescente**, com empate pelo nome exibido
  - Origem no legado: `src/reporting/lista_de_arquivos.py:174-177`
  - Critério de pronto: `sort` estável com chave `(-mtime, nome_exibido)`; a ordem não muda entre duas leituras
  - Confiança: 🟢

- [ ] T-10, Formatar a data em `dd/mm/aaaa`, devolvendo **célula vazia** quando o instante não converte
  - Origem no legado: `src/reporting/lista_de_arquivos.py:122-143`
  - Critério de pronto: `OverflowError`, `OSError` e `ValueError` devolvem `""`; a rota continua `200`
  - Confiança: 🟢

- [ ] T-11, Registrar a listagem como **processador de contexto**, com as duas chaves de aba
  - Origem no legado: `src/app.py:341-353`
  - Critério de pronto: **toda** renderização de `index.html` traz `arvores_da_lista` e `relatorios_da_lista`, inclusive `GET /` sem envio prévio
  - Confiança: 🟢

- [ ] T-12, Ler a pasta **somente** pela porta, sem acesso a disco na rota
  - Origem no legado: `src/ports/adaptadores.py:105-162`
  - Critério de pronto: pasta ausente → `[]`, sem criar diretório; subdiretório ignorado; nenhum `open` em `listar`
  - Confiança: 🟢

- [ ] T-13, Implementar `aposentar`: mover para `<pasta>/_aposentados/` com as **duas camadas** de defesa
  - Origem no legado: `src/ports/adaptadores.py:164-217`
  - Critério de pronto: recusa caminho, `..`, barra, barra invertida e NUL; confere que o diretório pai do caminho resolvido é a pasta de upload; nunca sobrescreve
  - Confiança: 🟢

- [ ] T-14, Acrescentar sufixo `.1`…`.99` na colisão de nome aposentado e **desistir** se todos existirem
  - Origem no legado: `src/ports/adaptadores.py:205-214`
  - Critério de pronto: 100 arquivos de mesmo nome → o centésimo não é movido e a função devolve `False`
  - Confiança: 🟢

- [ ] T-15, Tratar `action=aposentar_arquivo` **antes** da resolução da árvore do formulário
  - Origem no legado: `src/app.py:381-404`
  - Critério de pronto: aposentar a árvore atualmente aberta responde com a confirmação de sucesso, e nunca com a mensagem de arquivo inexistente
  - Confiança: 🟢

- [ ] T-16, Responder o desfecho de aposentar com os **literais congelados**
  - Origem no legado: `src/app.py:395-404`
  - Critério de pronto: sucesso = `'ROTULO' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados.` com `success=True`; fracasso = `Não foi possível aposentar o arquivo: ele não está mais na pasta.` com `success=False`
  - Confiança: 🟢

- [ ] T-17, Implementar a fonte única das guardas de entrada dos fluxos pós-upload
  - Origem no legado: `src/app.py:173-235`
  - Critério de pronto: devolve `(referencia, arvore, erro)`; campo ausente → `Erro: Arquivo GEDCOM não encontrado.`; referência não resolvida → `Erro: Arquivo 'ROTULO' não existe mais.`
  - Confiança: 🟢

- [ ] T-18, Não deixar a requisição cair quando o GEDCOM alcançado é ilegível
  - Origem no legado: `src/app.py:222-232`
  - Critério de pronto: exceção do parser vira mensagem em português + `app.logger.exception`; nenhum traceback vai para a tela
  - Confiança: 🟢

- [ ] T-19, Tratar `action=selecionar_arvore` renderizando o **mesmo** estado do envio
  - Origem no legado: `src/app.py:415-428`
  - Critério de pronto: a resposta traz `gedcom_filename` e `all_names`; sem o ramo o `action` cairia no `return` final e descartaria a árvore resolvida
  - Confiança: 🟢

- [ ] T-20, Registrar o filtro de template do nome visível da árvore aberta
  - Origem no legado: `src/app.py:104-110`, `templates/index.html:285`
  - Critério de pronto: `{{ gedcom_filename | rotulo_do_arquivo }}` exibe o nome sem a chave; nenhuma renderização precisa passar o rótulo como parâmetro
  - Confiança: 🟢

- [ ] T-21, Desenhar as duas tabelas com as seis colunas, o item indisponível marcado, e os botões "Abrir" e "Apagar" nas regras de cada aba
  - Origem no legado: `src/templates/index.html:103-269`
  - Critério de pronto: colunas `Nome`, `Situação`, `Arquivos`, `Tamanho`, `Enviado em`, `Gerenciar`; "Abrir" só no disponível da aba de árvores; "Apagar" em todo item, inclusive indisponível; `onsubmit` com a confirmação
  - Confiança: 🟢

- [ ] T-22, Implementar os **estados vazios** de cada aba e o markup idêntico nos dois ramos do template
  - Origem no legado: `src/templates/index.html:96-102`, `:190-192`, `:261-268`
  - Critério de pronto: nenhum formulário de envio na aba de DNA; os rótulos das abas são os mesmos antes e depois de escolher a árvore
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Teste da função pura: agrupamento, item sem chave, ordenação, quantidade e soma — `tests/test_lista_de_arquivos.py` (31 testes)
- [ ] TT-02, Teste de pureza: a função não abre arquivo e roda sem diretório — `tests/test_lista_de_arquivos.py:380`
- [ ] TT-03, Teste do rótulo: última extensão, símbolos, acentos, nome que é só extensão — `tests/test_lista_de_arquivos.py`
- [ ] TT-04, Teste da listagem na tela: as duas chaves no contexto em `GET /` — `tests/test_lista_na_tela.py` (14 testes)
- [ ] TT-05, Teste da tabela: colunas, ordem, marcação do indisponível, presença e ausência dos botões — `tests/test_tabela_da_tela.py` (14 testes)
- [ ] TT-06, Teste do happy path de aposentar: o arquivo sai da lista e continua íntegro em `_aposentados/` — `tests/test_aposentar_arquivo.py` (25 testes)
- [ ] TT-07, Teste do caso de erro: aposentar arquivo ausente devolve `False` e a mensagem de fracasso — `tests/test_aposentar_arquivo.py`
- [ ] TT-08, Teste de contenção de caminho em aposentar: `..`, barra, barra invertida, NUL, vazio — `tests/test_aposentar_arquivo.py`
- [ ] TT-09, Teste de colisão: sufixo `.1`…`.99` e desistência no centésimo — `tests/test_aposentar_arquivo.py`
- [ ] TT-10, Teste de escolher a árvore: `selecionar_arvore` renderiza `gedcom_filename` e `all_names` — `tests/test_voltar_para_a_lista.py` (5 testes)
- [ ] TT-11, Teste de ordem dos ramos: aposentar a árvore aberta responde a confirmação — `tests/test_aposentar_arquivo.py`, `tests/test_voltar_para_a_lista.py`
- [ ] TT-12, Teste da guarda de parse: GEDCOM ilegível não derruba a requisição — `tests/test_gedcom_ilegivel_nao_derruba.py`
- [ ] TT-13, Teste da porta: `listar` sem abrir arquivo, pasta ausente, subdiretório ignorado — `tests/test_porta_de_armazenamento.py` (18 testes)
- [ ] TT-14, Teste de manutenção da pasta: o que a tela enxerga depois de mover à mão — `tests/test_manutencao_de_uploads.py` (19 testes)

## Tarefas de Migração de Dados

**Não aplicável.** 🟢 A unit **não persiste nada** e o legado não tem banco: o único efeito em disco é o `os.replace` de aposentar. Não há dado a migrar.

O que existe, e **não** é migração de dados:

- [ ] TM-01, Decidir o destino dos arquivos que já estão em `_aposentados/` na pasta do operador, criados pela própria aplicação (nenhum é apagado por esta unit) 🟢
- [ ] TM-02, Decidir o destino dos arquivos **sem chave** da pasta real — os inalcançáveis que a tela marca como indisponíveis e que a aposentadoria consegue mover, mas a leitura não alcança 🔴 *(requer decisão humana; ver `L-30` e a dívida #3 do `code-analysis.md`)*

## Ordem Sugerida

1. **T-01 a T-10** (o núcleo puro) — não dependem de Flask nem de disco, e é o que os testes cobrem de forma mais direta. Começar por T-03 e T-04: o agrupamento define a forma do item, e tudo o mais (rótulo, ordenação, disponibilidade) opera sobre grupos já formados.
2. **T-12 a T-14** (a porta) — `listar` antes de `aposentar`: aposentar só faz sentido se a listagem já reflete a pasta, e o `os.replace` para subpasta é o que faz o arquivo sair da lista.
3. **T-11** (o processador de contexto) — depende de T-01 e T-12 prontos.
4. **T-15 a T-20** (a rota) — a ordem dos ramos (T-15) **antes** de tudo o que depende da árvore (T-17, T-19); T-15 é a única tarefa cuja violação produz uma mensagem **falsa** para o operador.
5. **T-21 e T-22** (o template) — por último: os rótulos e as colunas dependem de todos os campos do item já existirem, e os estados vazios dependem de as chaves de contexto estarem certas.
6. **TT-01 a TT-14** em paralelo a cada bloco, com TT-10 e TT-12 fechando a unit: são os dois casos que já produziram defeito **medido** no operador (o `500` do parser ilegível e o clique que não fazia nada).

**Bloqueios:** T-19 depende de T-17 (a guarda é a mesma fonte); T-05 depende de T-01; T-11 depende de T-01 e T-12.

## Lacunas Pendentes (🔴)

1. **`L-30` — o motivo "fora da forma" ficou praticamente inalcançável** e a docstring que o justifica (`utils/validate.py:189-192`) descreve a forma fechada removida em 2026-10-10. **Decisão humana:** manter o ramo como defesa em profundidade corrigindo a docstring, ou removê-lo? A tarefa **T-06** não pode ser fechada sem essa resposta.
2. **A listagem não filtra nada, por decisão.** O `.xlsx` da pasta real aparece na lista de entradas da pasta (e em nenhuma aba). Confirmar que a decisão continua valendo depois que a pasta passou a ser alimentada pela aplicação.
3. **TM-02 — os arquivos sem chave da pasta real.** São os que o operador mais quer aposentar e que a leitura não alcança. Decidir se a aplicação deve oferecer alguma forma de regularizá-los (renomear com chave) ou se continuam sendo movidos à mão.
4. **`_arvore_do_formulario` é dependência compartilhada sem dono** (`design.md` § Riscos). Decidir se a fronteira deve nomear esse ponto em módulo próprio antes de `analise-dna` e `busca-caminho` serem reimplementadas.
5. **Observabilidade da aposentadoria:** nenhuma tentativa de aposentar deixa rastro no servidor. Decidir se isso é aceitável para uma ação destrutiva do ponto de vista do operador.

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Unit nova.*
