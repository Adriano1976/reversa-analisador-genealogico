# Roadmap: Pasta canônica de uploads dentro do repositório

> Identificador: `012-pasta-canonica-no-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Esta é uma feature de **operação, higiene de repositório e prova** — não de código de aplicação.
**Nenhum arquivo de `src/` é tocado**, porque o padrão do código nunca deixou de ser o desejado:
`_pasta_uploads()` (`src/app.py:103-118`) resolve `<diretório do app>/uploads` e o adaptador congela o
caminho no import (`src/app.py:129`). O delta tem cinco frentes: (a) a composição de contêineres volta a
montar `./src/uploads`; (b) a documentação volta a declarar a pasta do repositório como canônica e
**única**, e passa a declarar as duas guardas do Princípio I e o risco do `git clean`; (c) as **três
cópias de arrasto** de dado real em `_reversa_refactor/…/before-after/src-antes/uploads/` são removidas
por instrumento *fail-closed*, com o critério de cancelamento medido nesta rodada; (d) as duas guardas
do Princípio I ganham **teste que as prende**, porque hoje nada as protege; (e) o resíduo de instrumento
é expurgado por manifesto, como **última** ação. O `harness.py` continua sem edição e o invólucro de
paridade continua sendo o caminho de execução.

O que **não** muda e é o ponto: a ferramenta de manutenção, o invólucro, o padrão do código, o leiaute
dos nomes em disco, o teto de 16 MB e os três valores de `action`.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A feature **serve** o princípio em três movimentos: remove 50.762.352 bytes de dado real que hoje vivem em três artefatos do framework dentro da árvore do repositório; torna o `.gitignore` e o `.dockerignore` as únicas barreiras **nomeadas e testadas**; e declara o risco residual (`git clean`) em vez de o deixar invisível. **Conflito declarado, não escondido:** manter o dado dentro da árvore do repositório é uma escolha do operador, e o que a sustenta é a regra de ignore — não o código. Se a linha `uploads/` do `.gitignore` sair, a decisão passa a violar o princípio, e é por isso que ela ganha teste (`RN-09`, `RF-11`) | respeita, com conflito declarado |
| II. Comportamento observável é preservado em refatoração | Nada de comportamento muda: a paridade tem de continuar **100 %** e as análises têm de produzir os mesmos resultados. A única peça nova é operacional (remoção de cópias e expurgo de resíduo), acionada à mão | respeita |
| III. Nenhuma mudança sem teste que a cubra | É o princípio mais acionado: `RF-11` cria o teste que faltava para as guardas, `RF-08` corrige a justificativa do teste de documentação, e as três remoções exigem instrumento com critério de cancelamento medido, não `Remove-Item` | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhum arquivo de `src/core/` é tocado | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhum número de cM, faixa ou heurística é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | **Nenhuma linha de `src/` é tocada.** A entrega é reverter o que a 010 *declarou*, não mudar o que o código *faz* | Medido: o `git diff` de `src/` está vazio desde a feature 010, e o padrão já é `src/uploads`. Qualquer edição ali poria a paridade de 100 % em risco sem ganho — o que estava errado era a documentação e a montagem, não o código | (a) declarar `ANALISADOR_UPLOAD_FOLDER` dentro do serviço do compose — recria o segundo ponto de configuração que a `D-02` da 010 já tinha recusado; (b) tornar o padrão do código explícito e absoluto — muda comportamento sem necessidade | 🟢 |
| D-02 | O *bind mount* volta a ser **relativo** (`./src/uploads`), e não um caminho absoluto do host | É o que restaura o arquivo **byte a byte**: o critério do `RF-01` é `git diff HEAD -- docker-compose.yml` **vazio**, e a linha entregue pela feature 008 (`git log`: `80964c4`) era exatamente `- ./src/uploads:/app/src/uploads`. O relativo também mantém o checkout portátil | (a) `D:/Projetos/reversa_analisador_gelealogico/src/uploads` — prende a máquina, quebra o critério do diff vazio e obriga a editar o compose em cada clone; (b) caminho vindo do `.env` — acrescenta configuração ao que não precisa de nenhuma | 🟢 |
| D-03 | A remoção das três cópias de arrasto usa o **mesmo padrão de instrumento fail-closed** da remoção da cópia externa (`evidence/_remover_copias_de_arrasto.py`), e **não** um verbo novo na ferramenta de manutenção. Critério de cancelamento: **qualquer arquivo cujo `sha256` não ocorra em `src/uploads` cancela a remoção daquele diretório** | **Medido nesta rodada:** os 27 arquivos das três cópias têm o conteúdo presente na canônica — **0 órfãos**. Sem essa medição, remover seria fé; com ela, é prova de que nenhum conteúdo único se perde. O critério é sobre conteúdo, não sobre nome, porque a cópia contém nomes do formato anterior à chave derivada (`Adriano_Santos.ged`, `Arvore_Unificada_Oficial_V1_2.ged`) | (a) verbo `arrasto` permanente na ferramenta — peso morto para operação de uma vez, e alarga uma ferramenta que o operador acabou de decidir **não** ampliar (recusou até o verbo de backup, §9 Q3); (b) `Remove-Item -Recurse` manual — sem condição de cancelamento e sem evidência auditável | 🟢 |
| D-04 | O teste das guardas (`RF-11`) faz **duas asserções complementares**: a presença literal das linhas, e o **efeito** — para o `.gitignore`, `git check-ignore -v` tem de nomear `.gitignore` para um caminho `uploads/`; e, por o `.dockerignore` ser lista de permissão em que **a última regra que casa vence**, a linha `src/uploads/` tem de vir **depois** de `!src/**` | Só a asserção literal não pega a reordenação do `.dockerignore`, que exporia o dado sem remover linha nenhuma. Só a de efeito não distingue "esta linha existe" de "outra regra cobre o caminho", e o `RF-11` prende a linha. A ordem é uma regra real do Docker, declarada no próprio arquivo (`:22-23`) | (a) só a asserção literal; (b) só `git check-ignore`; (c) um teste que edita o `.gitignore` real e restaura depois — destrutivo e frágil se o teste falhar no meio | 🟢 |
| D-05 | A verificação por **mutação** do teste das guardas roda sobre **cópias temporárias** dos dois arquivos, nunca sobre os originais: o teste copia, remove a linha na cópia, aponta a asserção para a cópia e confirma que ela falha | É o que dá sentido ao teste — uma asserção que nunca foi vista falhar não é prova (Princípio III). Fazer isso no arquivo real deixaria o repositório exposto se o teste abortasse no meio | (a) confiar na asserção sem exercitá-la; (b) mutar o arquivo real com `try/finally` — o `finally` não protege contra `KeyboardInterrupt` nem contra queda de processo | 🟢 |
| D-06 | O `onboarding.md` da 010 é revisado **no lugar**, com um bloco `> **Revisto em 2026-10-09 (feature 012).**` por seção afetada e o texto anterior preservado em bloco citado | Decisão do operador (§9 Q5). O precedente do projeto é a `D-02` da feature 004 ("**Revista em 2026-10-04.**"), que manteve o registro. Sem isso, a seção 12 do documento manda apagar a pasta que passou a ser a canônica — um procedimento que agora **destrói** o dado | (a) só um aviso no topo do documento — quem lê a seção 12 não vê; (b) reescrever substituindo o texto antigo — recusado pelo operador, perde o registro de que houve outro caminho | 🟢 |
| D-07 | O manifesto do resíduo é **regenerado** antes de aplicar o expurgo, em vez de usar o da 010 como está | O manifesto da 010 foi gerado em `2026-10-09T14:51:46Z`, e o `expurgar` **recusa** arquivo cujo hash mudou desde a geração — um manifesto velho transformaria o expurgo em uma lista de recusas. Regenerar também mantém o cabeçalho `# Pasta:` apontando para a pasta certa, que é o que dispensa repetir o caminho na linha de comando | (a) usar o manifesto da 010 — funciona se nada mudou, e falha de forma confusa se mudou; (b) apagar por padrão de nome — a `D-05` da 010 já mediu que padrão de nome não distingue resíduo de dado real | 🟢 |
| D-08 | A ordem das operações é: documentação e compose → **cópias de arrasto** → adendo → **expurgo do resíduo**, por último | Dois motivos medidos: (1) o critério de cancelamento da `D-03` compara contra `src/uploads`, então o `src/uploads` tem de estar no estado em que foi medido — expurgar antes mudaria a referência da comparação no meio da feature; (2) o expurgo derruba a pasta de **36 para 18 arquivos**, e os números publicados nos artefatos precisam ser os dois: o de antes nas medições e o de depois no estado final | (a) expurgar primeiro — quebra a referência da `D-03` e mistura dois estados nos documentos; (b) expurgar junto com as cópias de arrasto — idem, e sem relatório separado | 🟢 |
| D-09 | O diretório `D:\dados-genealogicos` fica no disco, **vazio**, e não é removido por esta feature | O pedido do operador foi sobre os **arquivos**, e a remoção já executada cumpriu isso. Um diretório vazio não é lido por nada: não está na árvore do repositório, não entra em build e não é resolvido pelo app. Removê-lo seria ação destrutiva fora do escopo declarado | (a) remover agora — ato além do pedido, e sem ganho medido; (b) recriá-lo com um marcador — reintroduz um caminho que a decisão acabou de esvaziar | 🟢 |
| D-10 | O adendo `012` marca a reversão do adendo `010` **em parte**, dizendo explicitamente **o que continua valendo** | Dos 13 impactos declarados pelo 010, a reversão **cancela 10 e mantém 3** (contagem linha a linha, corrigida no sync — ver abaixo). Uma linha genérica de "superado" tornaria invisível que a ferramenta e o invólucro seguem sendo entrega válida — e um leitor futuro concluiria que `tests/manutencao_de_uploads.py` e `tests/rodar_paridade.py` podem sair. **Revisto em 2026-10-09, no `/reversa-sync`:** (1) a contagem original era "9 e 4", escrita antes da conferência — a linha `architecture.md` §7 também cai, porque o que ela declara é que a pasta compartilhada passou a ser *a canônica fora do repositório*; (2) a forma mudou por **decisão do operador**: o adendo 010 **não é tocado**, e a relação fica declarada dentro do adendo 012. Motivo: a skill do sync proíbe escrever a linha de superação — ela pertence à pipeline reversa — e o 010 está provadamente intocado (`sha256` conferido antes e depois: `DC09A491399FE87A4FA45FF1D40A02D95A9E22EAE3385ECBEB8CF5E71C478626`) | (a) "Superado pelo adendo 012", genérico — apaga a distinção entre o que caiu e o que ficou; (b) reescrever o adendo 010 — a convenção proíbe, e o registro histórico se perde | 🟢 |
| D-11 | A verificação de "nenhum processo com a pasta em uso" usa **`docker compose ps` mais os processos do host**, e **não** a tabela de portas | **Medido nesta rodada:** `Get-NetTCPConnection` não é instrumento confiável sob o confinamento — ele não listou a porta 5080 nem a 5000 em uma execução, listou a 5432 em outra e, na terceira, não listou nenhuma das duas, **enquanto `docker compose ps` mostrava os dois contêineres no ar e saudáveis**. Uma verificação que pode devolver "nada escutando" com o serviço no ar não serve para liberar nem para bloquear uma remoção | (a) confiar na tabela de portas — foi o que quase fez esta feature remover uma pasta de um contêiner vivo; (b) confiar só no `Get-Process` — não enxerga processo dentro de contêiner | 🟢 |
| D-12 | O critério de resíduo continua sendo o **conjunto fechado de nomes** do manifesto (`NOMES_DE_INSTRUMENTO`, 12 nomes), e o limite fica **declarado**: ele não alcança nome novo de instrumento. Fechamento testável: regenerar o manifesto depois do expurgo tem de devolver **0** entradas | Ampliar o conjunto com os nomes da sonda da 010 (`sonda_t014`) não mudaria nada hoje — os arquivos não existem mais (medido por varredura) — e manteria a fragilidade: o critério é por **nome conhecido**, não por autoria. A 010 deixou 4 arquivos sintéticos no destino (`*__sonda_t014.ged` e `.csv`) que o conjunto **não** alcança, e isso está declarado nos artefatos dela (`onboarding.md` §16, `regression-watch.md`). Um critério por autoria exigiria registro de quem enviou, que o sistema não tem | (a) ampliar o conjunto com `sonda_t014`; (b) critério por "não está em nenhuma linha do histórico do banco" — depende do banco estar no ar e confunde resíduo com arquivo não analisado; (c) critério por padrão de nome — a `D-05` da 010 já mediu que não distingue resíduo de dado real | 🟡 |
| D-13 | O histórico do banco com **2 referências não resolvidas** (`sonda_t014`) fica como está, **declarado**; não é corrigido por esta feature | Medido: `dna_analysis` tem 2 linhas, com `tree_ref` apontando para `0646f8431ba58cca__sonda_t014.ged` e `dbc25ecc1cb17db3__sonda_t014.ged`, e **nenhum arquivo com `sonda` no nome existe em lugar nenhum do projeto**. A referência já estava quebrada antes desta feature, e o impacto é **latente, não observável**: a varredura de `src/` mostra **zero `SELECT`** — o histórico é só de escrita, e nenhuma das três `action` o consulta. Corrigir exigiria escolher entre apagar as linhas ou marcar a análise como indisponível, e isso é decisão de produto, não desta feature | (a) apagar as 2 linhas — destrói registro histórico para consertar algo que ninguém lê; (b) marcar as análises como indisponíveis — inventa um estado que o schema não tem; (c) declarar e encaminhar a quem rastreia defeito | 🟢 |

## 4. Premissas

Nenhuma premissa vem de `[DÚVIDA]` não resolvida: o documento chegou ao plano com **0** marcadores,
depois da sessão de esclarecimento de 2026-10-09.

| Premissa | Origem (`requirements.md`) | Risco se errada |
|----------|----------------------------|-----------------|
| Os dois instrumentos do refactor (`registrar-diff.py` e `verificar-estrutura.py`) continuam executando depois da remoção das cópias de arrasto | §10, nota sobre `registrar-diff.py:105-113` e `verificar-estrutura.py:269-274` | **Resolvida no `T013`, e o resultado é mais duro do que a premissa supunha:** os dois instrumentos **já falhavam antes desta feature** (`registrar-diff.py` aborta em `src/core/gedcom_state.py`, apagado pela feature 005; `verificar-estrutura.py` acusa o `src/` de hoje contra o congelado de 2026-10-03). O que a prova A/B estabelece é o que importa: **a retirada não muda a saída de nenhum dos dois**, e nenhuma reclamação menciona `uploads`. Achado colateral declarado: sobra um `__pycache__/gedcom_state.cpython-314.pyc` de um módulo que não existe mais, resíduo que pode confundir uma extração futura 🟢 |
| O Docker Desktop monta `./src/uploads` relativo no contêiner | `RF-01`, `D-02` | Se falhar, o modo contêiner cai para volume nomeado. **Mitigação:** é a linha exata que a feature 008 entregou e usou; o risco é de regressão de ambiente, não de desenho, e a verificação está no `onboarding.md` §5 🟢 |
| O contêiner da aplicação pode ser **recriado** sem tocar no volume do banco | `RF-01`; medição do ambiente em 2026-10-09 | **Medido:** `genealogia-app-1` e `genealogia-db-1` estão no ar, e o app publica `127.0.0.1:5080`. O contêiner do app monta um caminho de host que **não existe mais**, e por isso `/app/src/uploads` responde "No such file or directory" dentro dele. A correção é `docker compose up -d`, que recria só o serviço cujo arquivo mudou. **`docker compose down -v` apaga o volume do banco** — nunca usar para isto, e o próprio `.env` avisa disso. Verificado: `docker compose ps` responde e o serviço `db` está `healthy` 🟢 |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Armazenamento dos arquivos enviados | `_reversa_sdd/architecture.md#1`; `_reversa_sdd/upload-gedcom/contracts.md#2.2` | contrato-alterado | A raiz declarada volta a ser a pasta do repositório. A regra de resolução, a criação no import e o leiaute dos nomes **não** mudam |
| Composição de contêineres | `_reversa_sdd/c4-containers.md#2`; `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` | contrato-alterado | O ponto de montagem volta a `./src/uploads`, com o mesmo alvo interno `/app/src/uploads` e sem variável de ambiente no serviço |
| Documentação do operador | `_reversa_sdd/inventory.md#4`; `README.md`; `_reversa_forward/010-uploads-fora-do-repositorio/onboarding.md` | contrato-alterado | A pasta canônica volta a ser declarada dentro do repositório; as duas guardas do Princípio I e o risco do `git clean` passam a ser declarados; o onboarding da 010 recebe marcador de revisão |
| Testes de documento e de guarda | `README.md`; `.gitignore:30`; `.dockerignore:24` | contrato-novo | `tests/test_guardas_do_armazenamento.py` prende as duas guardas, com asserção de ordem no `.dockerignore` e verificação por mutação (`RF-11`, `D-04`, `D-05`); `RF-08` corrige a justificativa do teste de documentação existente |
| Cópias de arrasto em `_reversa_refactor/**` | fora da extração (a extração não descreve `_reversa_refactor/`) | componente-extinto | Os três diretórios `…/before-after/src-antes/uploads/` deixam de existir; os `.py` irmãos em `src-antes/` ficam intactos |
| Ferramenta de manutenção e invólucro | `tests/manutencao_de_uploads.py`; `tests/rodar_paridade.py` | **sem mudança** | Permanecem íntegros. O verbo `migrar` perde o papel de procedimento recomendado e fica como cópia avulsa (`RN-06`) |
| Borda HTTP, casos de uso, núcleo, parsers, reporting, utils, adaptadores, template | `src/app.py`, `src/application/`, `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/`, `src/ports/`, `src/templates/` | **sem mudança** | Provado por `git diff` vazio (`D-01`) |

## 6. Delta no modelo de dados

- **Banco: nada muda.** Nenhum campo, nenhuma tabela, nenhuma migração. As colunas `tree_ref` e
  `match_file_ref` continuam resolvíveis porque guardam o **nome** derivado de conteúdo, e nenhum nome
  de arquivo em `src/uploads` é renomeado ou removido pelo `RF-09`.
- **Disco:** o número de diretórios que contêm dado real cai de **4 para 1**; 50.762.352 bytes saem por
  remoção de cópias redundantes e 6.631 bytes por expurgo de resíduo. `src/uploads` termina com
  **18 arquivos**, contra 36 no início — e nenhum deles é arquivo do operador.
- Detalhe completo em: `_reversa_forward/012-pasta-canonica-no-repositorio/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato **HTTP** é afetado: rota, campos de formulário, códigos de status e mensagens ficam
intactos, e isso é provado por `git diff` de `src/` vazio (`D-01`), não afirmado. Por esse motivo **não
há diretório `interfaces/`**: o que muda é contrato de **operação** — onde a pasta vive, quem a monta e
o que a protege — e ele é documental e de configuração de composição.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a — nenhum contrato externo de runtime afetado | — | n/a |

## 8. Plano de migração

Não há migração de dados: nada é movido. O que existe é uma **sequência de retirada**, com conferência
antes de cada passo destrutivo.

0. **Conferir o estado do ambiente antes de tudo** (`D-11`): `docker compose ps` para ver se há
   contêiner no ar, e os processos `python` do host. **Não** usar a tabela de portas. Estado medido em
   2026-10-09: os dois contêineres no ar, o app em `127.0.0.1:5080`, e `/app/src/uploads` inexistente
   dentro do contêiner porque o *bind mount* aponta para um caminho de host que foi removido.
1. **Compose e documentação primeiro** (`RF-01`, `RF-02`, `RF-03`): restaurar `./src/uploads` no
   `docker-compose.yml` e reescrever a seção "Onde ficam os arquivos enviados" do `README.md`. Nada
   destrutivo ainda. **Depois da edição do compose, `docker compose up -d`** para recriar o serviço
   `app` — é o que devolve `/app/src/uploads` ao contêiner. `down -v` está proibido aqui: ele apaga o
   volume do banco.
2. **Testes** (`RF-08`, `RF-11`): corrigir a justificativa do teste de documentação e escrever o teste
   das guardas, com a verificação por mutação sobre cópias temporárias (`D-05`).
3. **Retirada das cópias de arrasto** (`RF-09`, `D-03`): instrumento *fail-closed* que, por diretório,
   confere que todo `sha256` ocorre em `src/uploads`; qualquer órfão cancela aquele diretório. Registra
   inventário antes e depois.
4. **Prova de que a retirada não quebrou instrumento** (premissa de §4): executar `registrar-diff.py` e
   `verificar-estrutura.py` e registrar a saída; conferir que `git status --porcelain` não ganhou linha.
5. **Prova de que `src/` não mudou** (`D-01`): `git diff -- src` vazio, registrado como evidência.
6. **Suíte e paridade** (`RF-06`, `RF-07`): suíte sem `DATABASE_URL` e paridade pelo invólucro, com
   inventário de `src/uploads` conferido antes e depois da paridade.
7. **Adendo** (`RF-05`, executado pelo `/reversa-sync`): escrever `_reversa_sdd/addenda/012-*.md`,
   superando **em parte** o adendo 010 (ver `D-10` em §3 — parcial, não total).
8. **Revisão do onboarding da 010** (`RF-12`, `D-06`): marcador de revisão por seção afetada, com o
   texto anterior preservado. **Atenção medida:** a seção 12 do documento manda apagar `src/uploads/` —
   depois desta feature isso destrói o dado canônico, e é a seção mais crítica da revisão.
9. **Expurgo do resíduo, por último** (`RF-10`, `D-07`, `D-08`): regenerar o manifesto, revisar, rodar a
   simulação e só então aplicar. `src/uploads` passa de 36 para 18 arquivos.
10. **Recaptura dos números** (`D-08`): registrar o estado final para a feature 011, nas **duas**
    unidades, porque elas divergem — a aba de árvore passa de 16 arquivos / 15 itens para 7 arquivos /
    **6 itens** (dois arquivos compartilham a chave `080e7943572d2652`), e a de DNA de 19 / 19 para
    10 arquivos / 10 itens.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `git clean -xdf` (ou `-Xdf`) apagar `src/uploads`, que é não rastreada | alto | média | `RF-03` declara o risco no `README.md`; `RF-11` prende a linha do `.gitignore` com teste. A decisão de 2026-10-09 é consciente: **não** há verbo de backup — a proteção é documentação mais backup do operador (`RN-06`) |
| A remoção das cópias de arrasto destruir o único exemplar de algum conteúdo | alto | **baixa** | `D-03`: critério de órfão por `sha256` contra `src/uploads`, **medido em 0** antes do plano. Qualquer órfão cancela a remoção daquele diretório e é nomeado no relatório |
| O teste das guardas passar mesmo com o `.dockerignore` reordenado, expondo o dado sem remover linha | alto | média | `D-04`: asserção explícita de que `src/uploads/` vem **depois** de `!src/**`, porque no `.dockerignore` a última regra que casa vence |
| O teste das guardas nunca ter sido visto falhar | médio | média | `D-05`: verificação por mutação sobre cópias temporárias, no próprio teste |
| O onboarding da 010 continuar mandando apagar `src/uploads/` | alto | **alta** se não revisado | `RF-12` e `D-06`: revisão no lugar, seção por seção; a seção 12 é a mais crítica e a revisão dela é critério de pronto |
| O expurgo remover dado real por manifesto velho ou classificação errada | alto | baixa | `D-07`: manifesto regenerado; simulação obrigatória antes de aplicar; `expurgar` recusa hash divergente e caminho fora da pasta |
| Alguém voltar a apontar `ANALISADOR_UPLOAD_FOLDER` para fora e recriar a segunda pasta | médio | média | `RF-02`: o `README.md` apresenta a variável como sobreposição de teste, não como modo de operação; a linha continua na tabela porque os testes dela dependem |
| `DATABASE_URL` presente no ambiente mascarar regressão da suíte | médio | **alta** nesta máquina | Declarado na §10 do `requirements.md` com os dois números (`325/2/9` com a variável, `327/9` sem). A linha de base é medida **sem** a variável, e a diferença é conferida antes de qualquer conclusão de regressão |
| A montagem relativa `./src/uploads` não funcionar em algum cenário do Docker Desktop | baixo | baixa | É a linha que a feature 008 entregou e usou (`git log`: `80964c4`); a verificação está no `onboarding.md` §5 |
| Alguém "consertar" o contêiner com `docker compose down -v` e **apagar o volume do banco** | alto | baixa | Declarado no passo 1 do plano e no `onboarding.md`: a recriação é `docker compose up -d`. O `.env` já avisa que `down -v` apaga o histórico |
| Confirmar que "nada está usando a pasta" com a tabela de portas e concluir errado | alto | **média** | `D-11`: a verificação é `docker compose ps` mais processos do host. Medido: a tabela de portas devolveu resultados contraditórios em três execuções seguidas, com os serviços no ar |
| O critério de resíduo, por ser conjunto fechado de nomes, deixar resíduo novo para trás | médio | **alta** | `D-12`: o limite fica declarado, e o `RF-10` não promete limpeza geral — promete remover os arquivos do manifesto revisado. O fechamento testável é o manifesto regenerado devolver 0 para o conjunto |
| O histórico do banco com 2 referências não resolvidas ser lido como defeito desta feature | baixo | média | `D-13`: medido e declarado — as `sonda_t014` não existem em lugar nenhum desde antes desta feature, e nada lê o histórico (zero `SELECT` em `src/`). Encaminhamento: `/reversa-debugger` |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `git diff -- src` vazio, registrado como evidência (`D-01`)
- [ ] `git diff HEAD -- docker-compose.yml` **vazio**: a linha `./src/uploads:/app/src/uploads` restaurada (`D-02`)
- [ ] Os três `…/before-after/src-antes/uploads/` não existem, e os `.py` irmãos em `src-antes/` continuam intactos
- [ ] `registrar-diff.py` e `verificar-estrutura.py` executam sem erro depois da retirada ~~(critério original)~~ — **Revisto em 2026-10-09, no `T013`.** Medido: os dois **já saíam com código 1 antes desta feature**. O `registrar-diff.py` aborta em `src/core/gedcom_state.py`, módulo **apagado pelo `T023` da feature 005** (`src/core/registro.py:9`), e o `verificar-estrutura.py` acusa divergência de pacotes porque o `src/` andou por sete features desde 2026-10-03. O critério passa a ser o que a ação de fato prova, e que é **mais forte**: **a retirada das cópias de arrasto não altera a saída de nenhum dos dois**, provado por controle A/B com as cópias reconstruídas a partir de `src/uploads` (`evidence/T013-instrumentos-do-refactor.txt`)
- [ ] `git status --porcelain` sem nenhuma linha nova depois das remoções
- [ ] Zero órfãos: todo `sha256` das cópias removidas ocorre em `src/uploads`
- [ ] `src/uploads` termina com **18 arquivos**, e nenhum arquivo do operador foi removido em nenhum passo
- [ ] Suíte em `327 passed, 9 skipped` **sem** `DATABASE_URL` no ambiente
- [ ] `PARIDADE 100 %` executada pelo invólucro, com o `harness.py` byte a byte idêntico
- [ ] Inventário de `src/uploads` idêntico antes e depois de uma execução completa da paridade
- [ ] O teste das guardas existe, falha quando a linha é removida numa cópia temporária, e assere a ordem no `.dockerignore`
- [ ] O `README.md` declara `src/uploads` como canônica e única, apresenta a variável como sobreposição, nomeia as duas guardas e o aviso do `git clean`
- [ ] O `onboarding.md` da 010 traz o marcador de revisão e **não** manda mais apagar `src/uploads/`
- [ ] Adendo `012` escrito pelo `/reversa-sync`, superando **em parte** o `010` (`D-10`)
- [ ] `docker compose ps` conferido antes de qualquer remoção (`D-11`), e o serviço `app` recriado com `up -d` depois da edição do compose, com `/app/src/uploads` voltando a existir dentro do contêiner
- [ ] O volume do banco **não** foi recriado: `db` continua `healthy` e com o mesmo volume (nenhum `down -v`)
- [ ] Manifesto regenerado depois do expurgo devolve **0** entradas para o conjunto de nomes (`D-12`)
- [ ] As 2 referências não resolvidas do banco ficam declaradas em `data-delta.md`, e nenhuma linha de `src/` foi alterada por causa delas (`D-13`)
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-plan` | reversa |
