# Perguntas para Validação — teste_reversa

> Gerado pelo **Reversa-Reviewer** na re-extração de **2026-10-10**. Substitui integralmente o `questions.md` de 2026-10-05.
> Nível de documentação: **Completo** → **todos os 🔴** são apresentados, e não apenas os que bloqueiam a reimplementação.
> `answer_mode = "chat"` — pode responder aqui mesmo, numerando as respostas.
>
> **Esta é uma passada ÚNICA.** As **16 perguntas de 2026-10-05 não foram reabertas**: todas estão decididas, aplicadas e verificadas. As **6 primeiras** desta lista são as que já estavam registradas em `.reversa/state.json → recomendacao_para_a_retomada`; as **12 seguintes** nasceram da revisão de consistência desta rodada, nas duas units novas (`tela-de-entrada`, `recursos-da-tela`) e nos globais.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Como ler esta lista

| Grupo | Tema | Perguntas |
| --- | --- | --- |
| **A** | Decisões que podem mudar **código do legado** | 1 a 4 |
| **B** | **Dado pessoal** e persistência | 5 a 6 |
| **C** | A **arte** e o ambiente do container | 7 a 10 |
| **D** | A **tela de entrada** | 11 a 15 |
| **E** | **Custo**, cobertura e histórico | 16 a 18 |

**A pergunta 1 é a única desta lista cujo veredito é um EXPERIMENTO, e não uma decisão.** Foi por isso que ela ficou em primeiro lugar: as outras dezessete podem ser respondidas de memória, e esta exige uma medição que ainda não foi feita.

---

## Grupo A — Decisões que podem mudar código do legado

### Pergunta 1 — A colisão da chave do cache de nomes (`L-24` / `E-05`): medir primeiro?

**Contexto:** Unit `busca-caminho` — `_chave_de` em `src/core/documentary_relationship.py` devolve `(len(people), chaves[0], chaves[-1])` com `chaves = sorted(people)`. O índice `nome → ids` é um **cache de módulo**: ele só é reconstruído quando essa chave muda. Dois GEDCOMs de **mesmo tamanho** e com os **mesmos xrefs extremos** reaproveitam o índice da árvore anterior, e o dossiê de homônimos passa a listar xrefs que **não existem** na árvore carregada — sem exceção nenhuma, porque `get_name(None)` devolve `Sem Nome` e as consultas devolvem `[]`/`None`. Nada é levantado, nada é logado. Esta unit **alimenta** com esse dossiê os avisos de identidade ambígua da unit `analise-dna`.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`] § Riscos (`L-24`), [`_reversa_sdd/busca-caminho/tasks.md`] (`T-24`, `TT-20`), [`_reversa_sdd/analise-dna/design.md`] § Riscos, [`_reversa_sdd/flowcharts/busca-caminho.md`] §13
**Pergunta:** O cenário é **inferido, não executado**. Como proceder:
(a) **medir primeiro** — carregar dois GEDCOMs reais do mesmo tamanho com os mesmos xrefs extremos no mesmo processo e verificar se o dossiê da segunda árvore lista xrefs inexistentes — e só depois decidir a correção;
(b) **corrigir já**, acrescentando à chave algo derivado do conteúdo;
(c) **aceitar o risco**, declarando-o, sem medir nem corrigir?
**Impacto:** Em (a) e (b), a lacuna fecha no legado ou vira feature forward. Em (c), ela passa a ser dívida declarada — e é a única lacuna de gravidade alta desta rodada cujo alcance **ninguém mediu**.
**Recomendação do Revisor:** **(a) medir primeiro.** É o único achado de gravidade alta desta rodada que é **inferido** e não medido. Existe precedente no próprio projeto: o oráculo de 2026-09-28 achou no primeiro minuto um erro de spec que sobreviveu a 6 agentes e 7 gates humanos, porque todos operavam no nível das specs. O teste que hoje falharia (`TT-20`) já está escrito. E a correção, quando vier, é pequena e **não muda comportamento nenhum** — só o custo de reconstrução. ⚠️ `id()` **não** serve como chave: é reciclado.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 2 — A ordem de `common_ancestors` sensível ao `PYTHONHASHSEED` (`L-25`)

**Contexto:** Unit `busca-caminho` — `find_all_common_ancestors` em `src/core/documentary_relationship.py` varre `set(de_a) & set(de_b)` e ordena por `(meioses totais, maior distância, nome)`. Quando **dois ancestrais empatam nos três critérios**, a ordem final é a da iteração do `set` — que muda a cada processo. O mesmo vale para `additional_paths`. É **exatamente a mesma classe** do defeito que o `matching` de `analise-dna` fechou em 2026-10-05 com um quarto critério determinístico (o menor `xref_id`).
**Spec afetada:** [`_reversa_sdd/busca-caminho/requirements.md`] (`RF-25`, `BR-C-43`), [`_reversa_sdd/busca-caminho/design.md`] § Riscos, [`_reversa_sdd/busca-caminho/tasks.md`] (`T-22`, `TT-21`)
**Pergunta:** (a) dar a esta unit o **mesmo tratamento** que o `matching` recebeu — um quarto critério determinístico, o menor `xref_id`; (b) aceitar e declarar como contrato que a ordem só é estável até o empate triplo; (c) registrar apenas como requisito do alvo?
**Impacto:** Em (a), o legado ganha código novo e um teste de caracterização nas duas ordens de *pool* — como foi feito no `matching`. Em (b) e (c), a lacuna permanece aberta e **auditável**: quem reimplementar precisa saber que o desempate não é reprodutível.
**Recomendação do Revisor:** **(a)**. O desenho já existe no projeto, o custo é de poucas linhas e a assimetria atual é difícil de justificar: o mesmo projeto resolveu o mesmo problema em um lugar e não no outro. Se a resposta for (b) ou (c), o registro precisa dizer **por que** aqui é aceitável.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 3 — O motivo "fora da forma" ficou inalcançável (`L-30`)

**Contexto:** Unit `tela-de-entrada` — `motivo_de_indisponibilidade` em `src/utils/validate.py:183-202`. A docstring justifica o segundo motivo (`FORA_DA_FORMA` = `nome com caractere que a referência não aceita`) dizendo que é *"o caso do acento e do espaço, medido na pasta real"*. Mas a `_FORMATO_CHAVE` que recusava acento e espaço foi **removida em 2026-10-10** (`RN-20`, `ADR-32`): `chave_recebida_e_valida` passou a exigir apenas que a parte visível seja um **nome**. Verificado por leitura: `94e2402671702cac__Famílias_Sergipanas.csv` é **disponível** hoje. O ramo do template continua correto — ele apenas quase nunca será exercido.
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/design.md`] § Riscos, [`_reversa_sdd/tela-de-entrada/tasks.md`] (`T-06`), [`_reversa_sdd/tela-de-entrada/contracts.md`] §2.4, [`_reversa_sdd/tela-de-entrada/requirements.md`] (`BR-T-11`)
**Pergunta:** (a) **corrigir a docstring e manter o ramo** como defesa em profundidade; (b) **remover o ramo** e o literal, junto com a entrada correspondente na tabela de indisponibilidade; (c) deixar como está?
**Impacto:** Em (a), zero mudança de comportamento — uma linha de comentário que hoje descreve uma validação que não existe mais. Em (b), o contrato perde um motivo que ainda pode ocorrer para valores que **não podem existir como entrada de diretório** (barra, NUL) ou para o caso degenerado de parte visível vazia.
**Recomendação do Revisor:** **(a) corrigir a docstring e manter o ramo.** Custo mais baixo e mais honesto: o ramo é uma segunda camada legítima, e o defeito é o **comentário**, não o código. A tarefa `T-06` não pode ser fechada sem esta resposta.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 4 — O bytecode órfão do módulo removido (`CS-06`)

**Contexto:** `src/core/__pycache__/gedcom_state.cpython-314.pyc` continua em disco **sem** o `.py` correspondente. É o resíduo do módulo que a `ADR-24` eliminou. Medido: é o **único** bytecode órfão de `src/` (os outros 34 conferem com um `.py` existente). Inofensivo em execução, mas sugere que o módulo existe.
**Spec afetada:** [`_reversa_sdd/traceability/code-spec-matrix.md`] (`CS-06`)
**Pergunta:** (a) **apagar** o arquivo; (b) manter e deixar a matriz como registro?
**Impacto:** Apagar `src/**` está dentro de `allowedPaths` de `.reversa/reversa-config.json`, então a limpeza é tecnicamente autorizada. É o único item desta lista que é **higiene**, sem consequência de contrato.
**Recomendação do Revisor:** **(a) apagar.** É bytecode, não fonte: nenhuma linha de código do projeto se perde, e a alternativa é deixar no repositório um arquivo que documenta um módulo que não existe. Se preferir que eu não toque em nada sob `src/` nesta rodada, a resposta (b) é perfeitamente defensável — a matriz já o registra.

**Resposta:** <!-- preencha aqui -->

---

## Grupo B — Dado pessoal e persistência

### Pergunta 5 — Dado pessoal de **pessoas vivas** sem retenção, expurgo ou consentimento (`L-29` / `P-07`)

**Contexto:** A tabela `analysis_person` do histórico Postgres persiste `xref`, `nome`, `sexo`, `nascimento`, `local_nascimento` e `falecimento` de **todas** as pessoas que a análise tocou — inclusive **pessoas vivas**. Não há expurgo, não há prazo de retenção, não há consentimento registrado. **Desde que a persistência existe, o dado sobrevive ao arquivo de origem:** apagar o GEDCOM não apaga o retrato. É a única lacuna desta rodada que é **bloqueante para uso real com dado de terceiros**.
**Spec afetada:** [`_reversa_sdd/analise-dna/requirements.md`] (RNF Privacidade, `TM-04`), [`_reversa_sdd/analise-dna/design.md`] § Riscos, [`_reversa_sdd/erd-complete.md`], [`_reversa_sdd/init.sql`]
**Pergunta:** (a) **declarar a proibição agora** — uso restrito à própria árvore do operador — e levar retenção, expurgo e consentimento como **requisitos do sistema alvo**; (b) construir retenção/expurgo **no legado** nesta rodada; (c) registrar como dívida sem restrição de uso?
**Impacto:** Em (a), o legado ganha uma restrição de uso declarada e o alvo ganha um requisito rastreável — sem uma linha de código executada. Em (b), a rodada deixa de ser extração e vira construção de feature. Em (c), o sistema segue **sem** dizer o que não se pode fazer com ele.
**Recomendação do Revisor:** **(a)**. É a mesma solução que o projeto já adotou quatro vezes em 2026-10-05 (persistir histórico, registrar veredito, restringir a lista de nomes, validar o CSV): o requisito vai para o alvo, porque construir retenção no legado significaria construir o que a Onda 3/5 da migração substitui.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 6 — Não há teste do caminho **feliz** de gravação no banco (`L-28` / `X-05`)

**Contexto:** `RegistroDeAnalisesPostgres._escrever` grava 6 tabelas numa transação, em ordem de chave estrangeira. Os testes de persistência exercitam, **por desenho**, só os estados **desabilitado** e **indisponível** — porque `psycopg2-binary` está **pinado e ausente do `.venv/`**. Ou seja: erro de SQL, de ordem de FK ou de tipo só apareceria **dentro do container**, que é onde ninguém roda a suíte.
**Spec afetada:** [`_reversa_sdd/analise-dna/tasks.md`] (`TT-27`), [`_reversa_sdd/analise-dna/design.md`] § Riscos, [`_reversa_sdd/traceability/spec-impact-matrix.md`] (`X-05`)
**Pergunta:** (a) criar um **ambiente de teste com o driver** — venv dedicado, ou alvo de teste dentro do `docker-compose`; (b) manter como dívida declarada e levar a verificação para o alvo; (c) instalar o driver **no `.venv/` oficial**?
**Impacto:** Em (a), o caminho de escrita passa a ter cobertura real e o histórico deixa de ser o subsistema menos verificado do projeto. Em (c), o `.venv/` deixa de reproduzir o estado que a paridade mediu.
**Recomendação do Revisor:** **(a)**, com uma ressalva explícita: **não mexer no `.venv/` oficial.** Ele é o interpretador da paridade e foi realinhado de propósito em 2026-10-05; instalar o driver lá mudaria o ambiente que a decisão `L-19` fixou.

**Resposta:** <!-- preencha aqui -->

---

## Grupo C — A arte e o ambiente do container

### Pergunta 7 — A arte servida não é verificada **dentro do container** (`L-33`)

**Contexto:** Unit `recursos-da-tela` — as duas rotas servem `src/assets/*.png`. Os testes rodam **no host**, onde `docs/` (as fontes canônicas) existe. Se a arte falhar **dentro da imagem**, a degradação é o `404` — **silencioso**: sem log, sem teste, e a tela continua de pé, agora sem banner e com o ícone genérico. É exatamente o caso que a escolha de `src/assets/` (por causa da lista de **permissão** do `.dockerignore`) existe para evitar.
**Spec afetada:** [`_reversa_sdd/recursos-da-tela/design.md`] § Riscos, [`_reversa_sdd/recursos-da-tela/tasks.md`] (`TT-17`), [`_reversa_sdd/traceability/spec-impact-matrix.md`] (`X-06`)
**Pergunta:** (a) um **teste que rode na imagem**; (b) um **health check no arranque** que confira a presença (e o tamanho) das duas artes; (c) declarar e aceitar?
**Impacto:** Em (a), a verificação passa a existir no ambiente do operador. Em (b), a falha deixa de ser silenciosa **em produção**, e não só no CI. Em (c), o modo de falha continua invisível por construção.
**Recomendação do Revisor:** **(b) um health check no arranque** — é a única das três que protege o ambiente que o operador realmente usa, e não o ambiente de quem desenvolve. Um teste na imagem protege o CI; o arranque protege a operação.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 8 — O `sha256` do HTML mantido à mão (`L-34`)

**Contexto:** `tests/test_icone_de_atalho.py:58` guarda `SHA_DA_TELA = "17240e5a…"`, o hash do HTML de `GET /`. A rota de arte é um acréscimo **puro**, então o hash é o que prova que a tela não mudou. Ele foi **atualizado três vezes em 2026-10-10**.
**Spec afetada:** [`_reversa_sdd/recursos-da-tela/design.md`] § Riscos, [`_reversa_sdd/recursos-da-tela/tasks.md`] (lacuna 2), [`_reversa_sdd/traceability/spec-impact-matrix.md`] (`SHA_DA_TELA`)
**Pergunta:** (a) manter o hash, com cada atualização sendo decisão humana registrada; (b) trocá-lo por uma **âncora estrutural** (presença/ausência das marcas da masthead e do ícone, em vez do documento inteiro)?
**Impacto:** Enquanto cada atualização for uma decisão registrada, o hash prende o que promete. Se virar rotina, ele deixa de prender — um invariante que se atualiza sozinho não protege nada.
**Recomendação do Revisor:** **(b)**, mas sem pressa: o hash **funcionou** nesta rodada e o fato de ter sido atualizado três vezes foi consequência de três decisões humanas legítimas sobre a tela. A âncora estrutural é mais durável; o hash é mais estrito. Se preferir mantê-lo, registre na spec **quem** pode atualizá-lo e sob que condição.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 9 — O custo de servir 317 KB por requisição, sem cache em memória

**Contexto:** Unit `recursos-da-tela` — as duas rotas **não** têm cache em memória: `send_file` entrega o arquivo do disco a cada requisição, e o banner tem **317.058 bytes**. Não há medição de impacto no repositório. É uma escolha **implícita**, não uma decisão registrada.
**Spec afetada:** [`_reversa_sdd/recursos-da-tela/design.md`] § Estado Interno, [`_reversa_sdd/recursos-da-tela/tasks.md`] (lacuna 3)
**Pergunta:** (a) **medir** o custo antes de decidir; (b) aceitar como está — o `ETag` já evita o tráfego repetido, e o custo é do sistema operacional via `send_file`; (c) acrescentar cache em memória?
**Impacto:** Em (c), o cache introduz um problema novo: a arte **muda com o pedido do operador**, e é justamente por isso que não há validade longa. Um cache em memória precisaria de invalidação — exatamente o tipo de estado que a `ADR-24` acabou de remover do projeto.
**Recomendação do Revisor:** **(b) aceitar, com a decisão registrada.** Para dois arquivos estáticos servidos por `send_file`, o `ETag` já resolve o caso real; e a alternativa reintroduz estado de processo no único lugar do sistema que hoje não tem nenhum. Se quiser o número, (a) é barato.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 10 — A caixa de regressão do banner descreve uma composição que não existe mais

**Contexto:** Unit `recursos-da-tela` — o teste do banner exige **resíduo zero** na caixa `(778,232)–(918,338)`. Essa caixa foi escolhida sobre uma composição **anterior** (a que tinha um abajur). A composição atual é outra; ali é fundo hoje, então o teste continua válido — e o comentário do teste registra a origem.
**Spec afetada:** [`_reversa_sdd/recursos-da-tela/tasks.md`] (lacuna 5), [`_reversa_sdd/recursos-da-tela/design.md`] § Constantes
**Pergunta:** (a) **redefinir a caixa** sobre a composição atual; (b) manter a caixa e o comentário de origem, como está?
**Impacto:** A caixa é a **única** prova não-circular de que a remoção de fundo está correta naquela região. Redefini-la sobre a arte de hoje a torna mais forte; mantê-la preserva a memória do defeito que ela pegou.
**Recomendação do Revisor:** **(b) manter como está.** A caixa prende o que promete (ali é fundo, e o resíduo tem de ser zero) e o comentário impede que alguém a leia como medida da arte atual. Trocar a caixa **enfraqueceria** a prova: a nova seria escolhida olhando o resultado que se quer aprovar.

**Resposta:** <!-- preencha aqui -->

---

## Grupo D — A tela de entrada

### Pergunta 11 — Os arquivos **sem chave** da pasta real (`TM-02`)

**Contexto:** Unit `tela-de-entrada` — a pasta do operador tem **13 arquivos** (mais 4 aposentados). Os arquivos anteriores à chave por conteúdo **não são alcançáveis pela leitura** (`resolver` exige a chave canônica), mas **são** aposentáveis, e aparecem na lista marcados com o motivo `sem chave de conteúdo no nome`. São justamente os que o operador mais quer tirar da lista.
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/tasks.md`] (`TM-02`), [`_reversa_sdd/upload-gedcom/contracts.md`] §2.2
**Pergunta:** (a) a aplicação deve oferecer alguma forma de **regularizá-los** (regravá-los com a chave do próprio conteúdo, passando a serem legíveis); (b) eles continuam sendo movidos à mão pelo operador; (c) vira requisito do alvo?
**Impacto:** Em (a), a aplicação ganha uma ação nova — e ela **grava arquivo**, o que hoje nenhuma ação da lista faz além do `os.replace` de aposentar. Em (b), o comportamento atual está **correto e declarado**; o que falta é dizer que é definitivo.
**Recomendação do Revisor:** **(b) declarar como definitivo**, e (c) para o alvo. A ação de regularizar é tentadora, mas ela mudaria a única garantia forte da unit — *"nenhuma ação da lista escreve arquivo além do move"* (`BR-T-16`) — e o ganho é de conveniência, não de correção.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 12 — A disponibilidade do grupo é a do **representante** (`L-31`)

**Contexto:** Unit `tela-de-entrada` — `_montar_item` calcula `disponivel` e `motivo_indisponivel` a partir do **representante** do grupo apenas (`lista_de_arquivos.py:192-193`). Um grupo "com chave" pode conter nomes visíveis **diferentes** (o operador reenviou o mesmo conteúdo com outro nome), e nada garante que a elegibilidade seja a mesma para todos os membros. Nenhum caso real foi medido.
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/design.md`] § Riscos (`L-31`)
**Pergunta:** (a) decidir a disponibilidade pelo **conjunto** (o item só é disponível se todos os membros forem); (b) manter a decisão pelo representante; (c) **[medir]**: verificar em dado real se algum grupo tem membros com elegibilidade divergente e decidir com o número.
**Impacto:** Hoje o item anuncia disponível e a referência exibida (`nome_armazenado`) é a do representante — que **é** elegível. A consequência de (a) seria esconder o botão "Abrir" de grupos que funcionam. A consequência de (b) é que a decisão depende de um membro que pode não ser representativo.
**Recomendação do Revisor:** **(c) medir**. É uma pergunta de uma linha de código: agrupar por chave e comparar `pode_ser_usado(nome)` entre os membros. Se nenhum grupo divergir no dado real, (b) está provado; se divergir, (a) passa a ter caso concreto. Decidir sem o número é escolher entre dois comportamentos sem saber se a diferença existe.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 13 — `_arvore_do_formulario`: dependência compartilhada **sem dono declarado**

**Contexto:** A função vive em `src/app.py:173-235` e é a **fonte única das guardas de entrada** de **três** units (`tela-de-entrada`, `analise-dna` e `busca-caminho`): ela lê o `gedcom_filename`, resolve pela porta, parseia a árvore e converte a falha em mensagem. A `tela-de-entrada` a declara como sua responsabilidade, mas ela também é o primeiro passo dos outros dois fluxos — e mudar nela altera o contrato das três.
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/design.md`] § Riscos, [`_reversa_sdd/tela-de-entrada/tasks.md`] (`T-17`, lacuna 4)
**Pergunta:** (a) **nomear** esse ponto em módulo próprio antes de `analise-dna` e `busca-caminho` serem reimplementadas; (b) declará-lo em `contracts.md` como ponto compartilhado e mantê-lo em `app.py`?
**Impacto:** É a mesma classe de problema que a `CS-01` já registra para o `app.py` inteiro ("o único arquivo com cinco donos"). Em (a), a fronteira ganha um dono e uma assinatura própria. Em (b), nada muda no código e a fronteira fica apenas documentada.
**Recomendação do Revisor:** **(b)**, por coerência com a decisão de arquitetura já tomada: a `ADR-25` pôs a fronteira em `ports/`, e `_arvore_do_formulario` é uma **borda HTTP** (lê `request.form`), não uma porta. Movê-la para um módulo próprio seria extrair a borda — uma decisão de arquitetura maior do que uma re-extração autoriza. Declarar em contrato resolve o risco real, que é **mudar sem saber que se mudou o contrato de três units**.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 14 — A aposentadoria não deixa **rastro nenhum** no servidor

**Contexto:** Unit `tela-de-entrada` — a única ação da tela que **move arquivo do operador** não emite log, métrica nem trace. Uma tentativa de aposentar arquivo ausente responde na tela e não deixa nada no servidor. A unit tem **um** log no total (`app.logger.exception`, quando o GEDCOM alcançado não parseia).
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/requirements.md`] (RNF Observabilidade), [`_reversa_sdd/tela-de-entrada/tasks.md`] (lacuna 5)
**Pergunta:** (a) acrescentar log de servidor nas duas tentativas (sucesso e fracasso); (b) aceitar — a pasta **é** o registro, e o operador vê o resultado na tela; (c) logar só o fracasso?
**Impacto:** É uma ação **destrutiva do ponto de vista do operador** (o arquivo sai da lista, ainda que nada seja apagado). Sem rastro, não há como responder depois "quando isso saiu da lista e por quê".
**Recomendação do Revisor:** **(a)**, e é a mais barata desta lista: uma linha em cada ramo, sem mudar comportamento nem contrato. O projeto inteiro tem **um** log — e a única ação que move dado do operador não é ele. Uma ação que o operador percebe como destrutiva merece um rastro no servidor.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 15 — A listagem **não filtra nada**, por decisão

**Contexto:** Unit `tela-de-entrada` — a pasta é a superfície de confiança da tela: a listagem não filtra por nome, extensão nem forma da chave. O efeito medido: o `.xlsx` da pasta real é listado como entrada da pasta (e **não** aparece em aba nenhuma, porque a aba é decidida pela extensão). Um arquivo colocado ali por fora da aplicação também aparece.
**Spec afetada:** [`_reversa_sdd/tela-de-entrada/requirements.md`] (`BR-T-03`, RNF), [`_reversa_sdd/tela-de-entrada/tasks.md`] (lacuna 2)
**Pergunta:** (a) **confirmar** que a decisão continua valendo agora que a pasta passou a ser alimentada pela própria aplicação; (b) passar a filtrar (por extensão, ou por forma da chave), escondendo o que não é de nenhum tipo conhecido?
**Impacto:** Em (b), o `.xlsx` do operador **desapareceria** da tela — e com ele a informação de que ele está lá. Em (a), nada muda e a decisão passa a estar declarada como vigente.
**Recomendação do Revisor:** **(a) confirmar.** A decisão é coerente com a `BR-T-11` (o item indisponível **aparece** marcado, em vez de escondido) e com a ideia de que a pasta é o inventário do operador, não uma visão curada pela aplicação. Filtrar reintroduziria o defeito que a `L-30` acabou de expor: a tela escondendo o que existe.

**Resposta:** <!-- preencha aqui -->

---

## Grupo E — Custo, cobertura e histórico

### Pergunta 16 — O custo do dossiê de homônimos (`L-20`)

**Contexto:** Unit `busca-caminho` — `get_children` **varre todas as famílias** do arquivo, sem índice, a cada chamada; `person_summary` o chama uma vez por ficha; e `_diferencas` é chamado **duas vezes** em `homonym_dossier`, remontando as fichas de todos os ids. Além disso, `person_a` e `person_b` são **fichas completas** em cada resultado: no caso real de **71 conexões**, são **142 fichas** para uma tela que exibe poucas.
**Spec afetada:** [`_reversa_sdd/busca-caminho/design.md`] § Riscos, [`_reversa_sdd/busca-caminho/tasks.md`] (`T-20`, `T-21`, lacuna 3)
**Pergunta:** (a) **medir** o custo com a árvore real antes de otimizar; (b) otimizar agora (índice de filhos, uma chamada de `_diferencas`, ficha preguiçosa); (c) aceitar e declarar?
**Impacto:** (b) é a mudança de maior risco desta lista: `get_children` alimenta tanto a ficha quanto a detecção de colapso, e a ordem de inserção das arestas é **contrato de paridade** com o oráculo. Otimizar sem medir pode trocar um custo invisível por uma divergência de comportamento.
**Recomendação do Revisor:** **(a) medir**. É o mesmo raciocínio da pergunta 1, e aqui pesa mais: o projeto tem um oráculo congelado e um harness diferencial, então o custo e o efeito da otimização são **ambos** mensuráveis. Sem o número, "está lento" é impressão.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 17 — Duas análises iguais gravam **duas linhas** no histórico

**Contexto:** Unit `analise-dna` — nada deduplica uma análise repetida: o mesmo CSV com o mesmo `root_name` produz um **segundo** registro em `dna_analysis`, com todo o retrato de pessoas de novo. Não há decisão registrada sobre isso em lugar nenhum.
**Spec afetada:** [`_reversa_sdd/analise-dna/design.md`] § Estado Interno, [`_reversa_sdd/analise-dna/tasks.md`] § Lacunas
**Pergunta:** (a) **deduplicar** (mesma árvore + mesmo CSV + mesma raiz não grava de novo); (b) aceitar — o histórico é o **log de execuções**, e repetir uma análise é um evento legítimo que se quer registrar; (c) requisito do alvo?
**Impacto:** Em (a), o histórico deixa de responder "quantas vezes eu rodei isso". Em (b), ele deixa de ser um conjunto e passa a ser uma trilha — e o dado pessoal da pergunta 5 é **duplicado a cada repetição**.
**Recomendação do Revisor:** **(b) aceitar e declarar**, com uma consequência explícita: o histórico é uma **trilha de execuções**, não um catálogo de análises. É a leitura mais coerente com o nome das tabelas e com o fato de a gravação acontecer **depois** do núcleo, sem consultar o que já existe. Mas a interação com a pergunta 5 é real: sem retenção, cada repetição multiplica o dado pessoal persistido.

**Resposta:** <!-- preencha aqui -->

---

### Pergunta 18 — Remedir a cobertura agora (`CS-04`)

**Contexto:** A cobertura de `src/` foi medida em **83 %** em 2026-10-05, e a matriz registra que ela é **de arquivo, não de comportamento**: "🟢 coberto" significa que há requisito, design e tarefa para o arquivo, e **não** que todo caminho de execução dele esteja especificado. A medição **de linha não foi refeita** nesta rodada, e `src/` quase dobrou de tamanho (24 → 35 arquivos).
**Spec afetada:** [`_reversa_sdd/traceability/spec-impact-matrix.md`] (`X-03`), [`_reversa_sdd/traceability/code-spec-matrix.md`] (`CS-04`)
**Pergunta:** (a) **remedir** agora com `pytest-cov` (a ferramenta já está no `.venv/`); (b) deixar a medição de 2026-10-05 como referência, declarando a defasagem?
**Impacto:** Em (a), a `X-03` deixa de citar números de uma medição que não corresponde mais ao `src/` atual — e o `number_format.py`, que era a pior cobertura do projeto (53 %), é justamente o tipo de módulo que pode ter mudado. Em (b), a matriz continua afirmando "a medição não foi refeita nesta rodada" — o que é **honesto**, e é o que ela já diz.
**Recomendação do Revisor:** **(a) remedir.** É uma execução, a ferramenta já está instalada, e o número velho sobre um `src/` que dobrou de tamanho é pior do que número nenhum: ele dá a impressão de estar medindo o código atual.

**Resposta:** <!-- preencha aqui -->

---

## Perguntas **já decididas** — NÃO são pendências

Verificadas contra o código de 2026-10-10. Nenhuma precisa ser refeita, e nenhuma é reperguntada nesta rodada.

| Assunto | Resposta vigente | Verificação no código | Conf. |
| --- | --- | --- | --- |
| Desempate do matching é determinístico | **Implementado** (menor `xref_id`) | `matching.py:116-125`; `test_characterization_matching.py` | 🟢 |
| `app.secret_key` | **Removido** | nenhuma atribuição existe em `src/app.py` | 🟢 |
| Ausência de autenticação | **Omissão** — corrigir na Onda 3 | `permissions.md` §5-6 (`P-01`) | 🟢 |
| Histórico de análises | **Requisito do alvo nº 1** — e **implementado** no legado na feature 008 | `init.sql` (6 tabelas), `ports/adaptadores.py` | 🟢 |
| Descartes são **acionáveis** | `RF-27` é **Must** | `analise-dna/design.md` § Descartes | 🟢 |
| Restringir a lista de nomes | **Requisito do alvo nº 3** | `permissions.md` (`P-03`) | 🟢 |
| Endogamia e colapso: **avisar basta** | Confirmado; veredito **não** muda | `adrs/21`; `evidence_comparison.py` | 🟢 |
| Veredito do operador | **Requisito do alvo nº 2** | `state-machines.md` (`M-04`) | 🟢 |
| O `0,33` do Jaccard | **Chute** que funcionou — heurístico e ajustável | `matching.py`; `analise-dna/requirements.md` (`BR-D-49`) | 🟢 |
| Exportadores de CSV | **Só o GEDmatch** — cobertura declarada | `analise-dna/contracts.md` §2.1 | 🟢 |
| `.venv/` é o interpretador oficial | Pin realinhado; transitivas declaradas | `requirements.txt` | 🟢 |
| Cobertura medida | 83 % em 2026-10-05 (a remedição é a pergunta 18) | `spec-impact-matrix.md` (`X-03`) | 🟢 |
| Assimetria da ambiguidade | **Intencional** — vira contrato | `state-machines.md` (`M-02`) | 🟢 |
| CSV sem validação de conteúdo | **Herdado** — corrigir no alvo nº 4 | `validate.py:76`; `analise-dna/requirements.md` | 🟢 |
| Sentinela `SEM-KIT` | **Corrigida**: `" SEM-KIT"`, com espaço | `genetic_evidence.py`; medido | 🟢 |
| Corrida entre threads sobre a **árvore** | **Deixou de existir** estruturalmente (`ADR-24`) | `test_arvore_devolvida.py`, `test_dependencias_nucleo.py` | 🟢 |
| Homônimos: 1º ID | **Recuo**, não comportamento principal | `core/path_search.py` (5×5 combinações) | 🟢 |
| Teto de 20 iterações do BFS | Preservar fidelidade, **sem sinalização** | `path_finding.py`; `BR-C-04` | 🟢 |
| Varredura de `get_spouses` | **Condicional** é contrato | `family_navigation.py`; `BR-C-03` | 🟢 |
| Faixas de cM escritas à mão | Declaradas **fora do fluxo** (`cm_estimator`) | `cm_estimator.py`; `BR-D-62` | 🟢 |
| Legado permanece single-tenant | Aceite de risco, temporário | `adrs/18`; `BUG-20260929-BJJH` | 🟢 |

---

*Gerado pelo Reversa-Reviewer em 2026-10-10 (re-extração, nível completo).*
