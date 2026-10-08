# Requirements: Persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Entrega o **histórico das análises de DNA**: o que hoje morre ao fim da requisição passa a
ser gravado — os dados das pessoas da árvore que a análise usou, os metadados dos kits de
DNA e o **veredito do confronto** (`COMPATIVEL` / `POSSIVEL` / `CONFLITANTE` /
`INCONCLUSIVO`), com o porquê de cada um. Entrega também a aplicação e o banco subindo
juntos, com os dois estados persistentes em volume: a pasta de uploads e os dados do banco.

Para quem: o **operador único** do sistema (hoje `DONO_DO_PROCESSO = "unico"`), que não
consegue comparar duas execuções nem reabrir uma análise de ontem, e o desenvolvimento da
onda seguinte, que herda um esquema alinhado ao modelo já especificado para o alvo.

Por decisão de **2026-10-08** (§9, `Q-01`), esta feature **reverte o adiamento** que o
`_reversa_sdd/gaps.md#6` havia registrado: a persistência entra no `src/` agora, e o esquema
passa a ser a **base que a Onda 3 herda**, em vez de algo que ela descarta.

O que **não** muda: nenhuma decisão da análise. A persistência é uma **camada de saída,
depois do processamento** — o núcleo continua puro e continua decidindo o que sempre
decidiu.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1` | A aplicação é descrita como "**sem banco de dados**, **sem persistência de resultados** e **sem autenticação**". O único estado persistente é `src/uploads/`, com arquivos **imutáveis** sob chave de conteúdo | 🟢 |
| `_reversa_sdd/architecture.md#4` | "**Sem banco de dados.** Não há DDL, migration, schema, ORM nem arquivo de configuração de persistência." O ERD tem 27 estruturas, **nenhuma tabela**, e os `PK`/`FK` são **lógicos** (não existe constraint) | 🟢 |
| `_reversa_sdd/architecture.md#6` | "**Zero integrações de rede.**" Hoje não há nenhuma dependência externa em runtime; o banco seria a **primeira** | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida #8: "**Nada é persistido entre requisições** e não há decisão de negócio sobre isso" | 🟡 |
| `_reversa_sdd/erd-complete.md#6` | As estruturas que esta feature persiste existem e estão nomeadas: `RESULTADO_ANALISE` (24), `DESCARTADO` (25), `EVIDENCIA_KIT` (11), `SEGMENTO` (12), `FICHA_PESSOA` (19), `CONFRONTO` (17) | 🟢 |
| `_reversa_sdd/erd-complete.md#7` | O que o modelo **não** tem: constraint de integridade, `owner_id`, e "**histórico, versionamento ou auditoria de dado**". Também não existe relação por `FK` entre `RESULTADO_ANALISE` e `PESSOA` — a ligação vive dentro de `documentary`, "reflexo de que não há persistência que precisasse da chave" | 🟢 |
| `_reversa_sdd/erd-complete.md#8` | `E-01`: "**Ordem é dado, não consequência**" — três ordens determinam o resultado e nenhuma tem estrutura que as proteja. `E-04`: nada é persistido | 🟢 |
| `_reversa_sdd/state-machines.md#3` | Máquina 1 — o veredito do confronto tem **quatro estados**, é decidido **por kit** e a junção é **conservadora** (o estado final é o mais grave entre os kits) | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#Visão Geral` | A análise de DNA é "a única cuja saída é um **veredito**" nos quatro estados; a regra que a define é negativa: o cM nunca é usado sozinho para afirmar parentesco | 🟢 |
| `_reversa_sdd/domain.md#7` | `L-21`: nada é persistido entre requisições | 🟢 |
| `_reversa_sdd/gaps.md#6` | **Requisito nº 1 encaminhado ao alvo**: "Persistir resultados e histórico de análises". A justificativa registrada é que "**criar persistência no legado é construir o que a Onda 3 substitui**" | 🟢 |
| `_reversa_sdd/questions.md#pergunta-4` | Resposta do operador em 2026-10-05: "✅ **Herança — quero histórico no alvo**", com a ressalva "**Nada muda no legado**" | 🟢 |
| `_reversa_sdd/migration/target_data_model.md#Schema (DDL)` | O alvo **já especifica** o esquema relacional: `uploaded_file`, `gedcom_tree`, `person`, `family`, `dna_analysis`, `match_result`, `skipped_match`, `match_path_node` | 🟢 |
| `_reversa_sdd/migration/target_data_model.md#Considerações específicas do paradigma alvo` | Três decisões que esta feature herda: `owner_id` como invariante; "**ordem é dado**" (`result_ordinal`); e "**sem colunas de estado mutável** — o resultado de uma análise não muda; se a árvore for reimportada, cria-se **nova** análise" | 🟢 |
| `_reversa_sdd/migration/risk_register.md#RISK-004` | "**Divergência aritmética silenciosa por ponto flutuante**": ao introduzir persistência, agregar com `SUM` em vez de reproduzir a ordem de leitura pode alterar o último dígito e **cruzar um limite de faixa de cM**, mudando a relação prevista | 🟢 |
| `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md#Resumo da entrega` | A porta `RepositorioDeArvores` foi **declarada sem implementação e sem consumidor**, "como contrato para a Onda 3" | 🟢 |
| `_reversa_sdd/addenda/007-dono-no-port-e-baseline.md#Vigência` | As **dívidas #3** (corrida entre requisições concorrentes) e **#4** (ausência de identidade e de isolamento) seguem **abertas**. O `dono` é costura de assinatura, **não funcionalidade** | 🟢 |
| `.reversa/principles.md#I` | "Dados reais de DNA/GEDCOM **nunca** entram no versionamento, em nenhum caminho" — inclui logs, fixtures e artefatos | 🟢 |
| `.reversa/principles.md#II` | "Comportamento observável é preservado em refatoração": mesmas entradas produzem as mesmas saídas | 🟢 |
| `.reversa/principles.md#III` | "**Nenhuma mudança sem teste que a cubra**" | 🟢 |

> ⚠️ **Conflito declarado, não escondido — e resolvido em 2026-10-08.** O `gaps.md#6` registra
> que persistir no legado é construir o que a Onda 3 substitui, e o `questions.md#pergunta-4`
> registra a decisão do operador de manter o histórico **no alvo**. Esta feature pede
> exatamente o contrário — persistência **agora**, no `src/`. **O adiamento foi revertido por
> decisão explícita do operador em 2026-10-08** (§9, `Q-01`): a gravação no `src/` é
> deliberada, e o esquema desta feature é a **base que a Onda 3 herda**, não algo que ela
> descarta. O `gaps.md#6` continua correto como **registro histórico** e passa a ser lido como
> "atendido antecipadamente no `src/`", não como "cancelado" — a consequência prática está na
> `RN-09`.
>
> 🔴 **Achado desta leitura, que a extração ainda não registra:** o DDL congelado do alvo
> (`migration/target_data_model.md`, escrito em **2026-09-28**) é **anterior** ao nascimento
> da capacidade de confronto (2026-10-05). Varredura no diretório `migration/`: **zero**
> ocorrências de `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`, `confronto` ou
> `veredito`. O DDL do alvo, portanto, **não tem onde guardar o veredito**, e também **não
> tem tabela de metadados de kit** — só `match_result.total_cm`. O esquema desta feature
> cobre essas duas lacunas e, ao fazê-lo, diverge do alvo: a divergência está declarada em
> `RN-09` e em §12.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Operador único** (o dono do dado) | Reabrir uma análise de ontem sem refazer o upload; comparar duas execuções da mesma árvore | Envia o GEDCOM e o CSV, vê o resultado na tela, e semanas depois consegue recuperar o mesmo veredito sem ter guardado nada à mão |
| **Operador em auditoria** | Responder "por que este match foi considerado conflitante?" | Consulta o veredito gravado e lê o método da janela, a faixa esperada e o porquê, em vez de repetir o cálculo e torcer para dar igual |
| **Desenvolvedor da onda seguinte** | Não construir duas vezes a mesma coisa | Encontra um esquema alinhado ao `target_data_model.md`, com as duas lacunas (veredito e kits) já resolvidas e rotuladas |
| **Operador em máquina nova** | Subir o sistema inteiro sem instalar nada à mão | Roda um comando único na raiz e passa a ter banco e aplicação, com os uploads e o histórico preservados entre execuções |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — A persistência é camada de saída, depois do processamento.** A gravação acontece
   **depois** de a análise ter terminado e não participa de nenhuma decisão. Nenhum módulo de
   `src/core/` conhece o banco: não existe import de acesso a dados dentro do núcleo. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#1` (núcleo "não conhece HTTP" — passa a
     valer também "não conhece persistência") e `.reversa/principles.md#II`.
   - Tipo: nova.
2. **RN-02 — Nenhuma decisão da análise muda.** Mesmos matches aceitos, mesmos descartados,
   mesmas contagens de cM, mesma ordem de apresentação, mesmos vereditos. A persistência não
   pode ser citada como tendo alterado qualquer uma das 118 regras catalogadas. 🟢
   - Origem no legado: `.reversa/principles.md#II`;
     `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md`.
   - Tipo: nova (restrição de escopo).
3. **RN-03 — O que se persiste é o resultado, e ele é imutável.** Uma análise gravada não é
   recalculada nem atualizada. Reimportar a árvore ou reenviar o CSV produz **nova** análise,
   nunca uma reescrita da anterior. 🟢
   - Origem no legado:
     `_reversa_sdd/migration/target_data_model.md#Considerações específicas do paradigma alvo`.
   - Tipo: nova.
4. **RN-04 — A árvore completa não é duplicada no banco.** O GEDCOM continua sendo o arquivo
   **imutável** de `src/uploads/`, referenciado pela sua chave de conteúdo. O banco guarda os
   **dados das pessoas que a análise usou e exibiu** — a raiz, a pessoa do GEDCOM casada com
   o match, os nós do caminho documental e as fichas usadas para desambiguar homônimos. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#4` (o arquivo em disco é o único estado persistente, e é imutável).
   - Tipo: nova. **Escopo confirmado pelo operador em 2026-10-08** (§9, `Q-02`): o banco **não**
     recebe a árvore inteira. O motivo é duplo — a árvore real tem 5,3 MB e já está persistida
     por conteúdo em `src/uploads/`, e duplicá-la no banco criaria duas verdades sobre o mesmo
     dado.
5. **RN-05 — O cM gravado é o cM que o núcleo calculou.** O total é **transportado**, nunca
   reagregado pelo banco. O cM acumulado **não é arredondado** em nenhum ponto, e somar de
   novo no banco pode mudar o último dígito e **cruzar um limite de faixa**. 🟢
   - Origem no legado: `_reversa_sdd/migration/risk_register.md#RISK-004`;
     `_reversa_sdd/analise-dna/requirements.md#Evidência genética`.
   - Tipo: nova (mitigação de risco já registrado).
6. **RN-06 — Os quatro estados são dado de primeira classe, com o porquê e com o recorte por
   kit.** Grava-se o estado final, o estado de **cada** kit, o método pelo qual a janela foi
   obtida, a faixa esperada e o texto do motivo. O estado final continua sendo o **mais
   conservador** entre os kits. 🟢
   - Origem no legado: `_reversa_sdd/state-machines.md#3`.
   - Tipo: nova.
7. **RN-07 — Os descartes são auditáveis.** O match que não casou com nenhum registro é
   gravado com nome do CSV, kit, cM e motivo — a lista que hoje só existe na tela. 🟢
   - Origem no legado: `_reversa_sdd/erd-complete.md#6` (`DESCARTADO`, 25).
   - Tipo: nova.
8. **RN-08 — A ordem de apresentação é gravada como dado.** A ordem que o núcleo decide é
   persistida de forma que uma leitura posterior devolva a **mesma** ordem, inclusive nos
   empates. 🟢
   - Origem no legado: `_reversa_sdd/erd-complete.md#8` (`E-01`) e
     `_reversa_sdd/migration/target_data_model.md#Considerações específicas do paradigma alvo`.
   - Tipo: nova.
9. **RN-09 — O esquema segue o DDL do alvo onde ele existe, e declara onde ele é defasado.**
   Nomes de tabela e de coluna do alvo são reusados quando existem. Onde o DDL congelado não
   alcança — o veredito e os metadados de kit —, a extensão é **nomeada como extensão** e
   registrada em §12, para a onda seguinte reconciliar em vez de descobrir. 🟢
   - Origem no legado: `_reversa_sdd/migration/target_data_model.md#Schema (DDL)`; achado desta leitura (§2).
   - Tipo: nova.
10. **RN-10 — O `dono` continua sendo costura, não isolamento.** O valor passa a ter uma
    coluna, e **nenhuma** consulta filtra por ele. As dívidas #3 e #4 seguem **abertas**, e
    nenhuma entrega desta feature pode ser citada como tendo implementado isolamento. 🟢
    - Origem no legado: `_reversa_sdd/addenda/007-dono-no-port-e-baseline.md#Vigência`;
      `_reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md`.
    - Tipo: nova (preservação explícita).
11. **RN-11 — Ausência é `null`, nunca zero.** Vale para cM não utilizável, maior segmento,
    data de nascimento e qualquer campo do confronto que não se aplica — o invariante do
    sistema ("`None` significa 'não sei / não existe', nunca zero") atravessa a fronteira da
    persistência. 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#4`.
    - Tipo: nova.
12. **RN-12 — O banco é histórico, não fonte de leitura da tela.** A tela continua calculando
    do zero a cada requisição, a partir do arquivo de upload. Nenhum fluxo de análise passa a
    consultar o banco para decidir, completar ou corrigir o resultado. 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#1` (análise sob demanda, sem cache entre requisições).
    - Tipo: nova.
13. **RN-13 — Falha de persistência nunca bloqueia a análise.** Se a gravação não acontecer, a
    análise **conclui** e o resultado é exibido exatamente como seria com o banco no ar; a falha
    vira **aviso não bloqueante** ao operador. O histórico é um benefício, nunca uma condição
    para ver o resultado. 🟢
    - Origem no legado: decisão de **2026-10-08** (§9, `Q-03`);
      `_reversa_sdd/architecture.md#1` (a análise é sob demanda e não depende de nada além do
      arquivo enviado).
    - Tipo: nova. **Consequência:** o `RF-13` passa a valer no sentido **forte** — a análise não
      depende do banco nem para decidir, nem para ser exibida.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Subir o banco e a aplicação com **um único comando** na raiz do projeto, com dois serviços declarados | Must | O comando sobe os dois serviços; a aplicação atende em `127.0.0.1`; o banco **não** é publicado fora do host (bind em `127.0.0.1`) | 🟢 |
| RF-02 | Persistir a pasta `src/uploads/` **e** os dados do banco em volume, de modo que `down` seguido de `up` preserve os dois | Must | Enviar um GEDCOM, derrubar os serviços, subir de novo: o arquivo continua em `src/uploads/` e o registro da análise continua consultável | 🟢 |
| RF-03 | Persistir o **contexto de cada análise**: referência (chave de conteúdo) do GEDCOM e do CSV, data e hora, nome informado como raiz, se a raiz era **ambígua**, e as contagens de aceitos e descartados | Must | Depois de uma análise, existe um registro com a chave do GEDCOM, a chave do CSV, o nome digitado e as duas contagens, coerentes com a mensagem exibida | 🟢 |
| RF-04 | Persistir os **dados das pessoas** que a análise usou: identificador GEDCOM, nome, sexo, data e local de nascimento, data de falecimento — para a raiz, para a pessoa casada e para os nós do caminho documental | Must | Numa análise com caminho documental, cada nó do caminho tem seu registro, com os mesmos valores que a tela exibiu; campo desconhecido entra `null` | 🟢 |
| RF-05 | Persistir os **metadados de cada kit de DNA** por `(nome do CSV, kit)`: identificador do kit, fonte/empresa, cM total **daquele kit**, número de segmentos e maior segmento em cM | Must | Análise com dois kits do mesmo nome grava **dois** registros, e nenhum total somado entre eles | 🟢 |
| RF-06 | Persistir o **status do confronto** por conexão e **por kit**, com exatamente um de `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO` | Must | Os quatro valores são gravados, e o valor gravado é igual ao exibido na tela, caso a caso | 🟢 |
| RF-07 | Persistir o **porquê** do veredito: o método da janela usada, a faixa esperada (mínimo, máximo, média), o rótulo em português e o texto do motivo | Must | Para uma conexão compatível, o método e a faixa estão gravados; para uma inconclusiva sem DNA, o motivo gravado é o mesmo da tela | 🟢 |
| RF-08 | Persistir os **descartes** com nome do CSV, kit, cM e motivo | Must | A contagem de descartados no banco é igual à da mensagem; cada descartado tem motivo não vazio | 🟢 |
| RF-09 | Persistir a **ordem de apresentação**, de modo que a leitura posterior devolva a mesma sequência | Must | Ler os resultados gravados e comparar com a ordem exibida: idêntica, incluindo empates | 🟢 |
| RF-10 | Gravar a análise inteira em **uma única transação** | Must | Uma falha no meio da gravação não deixa análise parcial: ou todos os registros da análise existem, ou nenhum | 🟢 |
| RF-11 | Ler a **string de conexão exclusivamente de variável de ambiente** | Must | Nenhuma credencial em código, arquivo versionado, template, mensagem de tela, log ou camada da imagem | 🟢 |
| RF-12 | O esquema é criado por um **script de inicialização idempotente**, executado na primeira subida do banco | Must | Rodar o script duas vezes não destrói nem duplica; o esquema resultante é o mesmo | 🟢 |
| RF-13 | A análise **não depende do banco**: a suíte existente continua passando e a paridade continua em 100 % com o banco indisponível | Must | Suíte completa e paridade diferencial executadas com o banco derrubado: mesmo resultado de antes desta feature | 🟢 |
| RF-14 | Permitir **consultar a última análise** de um par (raiz, match) com o veredito e os kits, sem interface nova | Should | Uma consulta direta ao banco devolve o veredito e os kits da análise mais recente daquele par | 🟢 |
| RF-15 | Gravar a dependência de acesso a dados com **versão fixada** no arquivo de dependências do projeto | Should | A versão está pinada, como as seis diretas já estão | 🟢 |
| RF-16 | Manter a pasta de uploads e o volume do banco **fora do versionamento** | Should | `git status` não lista arquivo de upload nem dado de banco depois de uma execução | 🟢 |
| RF-17 | Concluir e exibir a análise **mesmo quando a gravação falha**, sinalizando o operador com **aviso não bloqueante** | Must | Com o banco derrubado, um GEDCOM e um CSV válidos produzem a **mesma tela** e o **mesmo veredito** de quando o banco está no ar, mais um aviso de que o histórico não foi registrado | 🟢 |

> **Nota sobre `RF-13` e `RF-17`.** Os dois juntos são o que protege o `Princípio II`. O
> `RF-13` garante que a **suíte e a paridade** não passam a depender do banco; o `RF-17`
> garante que a **análise em produção** também não — e é ele que dá sentido forte ao `RF-13`,
> por decisão de 2026-10-08 (§9, `Q-03`). Se qualquer um dos dois cair, a feature deixa de ser
> camada de saída e passa a ser dependência do caminho crítico — que é exatamente o que a
> `RN-01` existe para impedir.

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A gravação não pode dobrar o tempo da análise. Alvo: acréscimo medido, e registrado, sobre a linha de base de `261 aprovados` da feature 007 | A análise real medida tem 71 conexões e produz **142 fichas completas** de pessoa, cada uma com pais, cônjuges e filhos (`_reversa_sdd/architecture.md#7`, dívida #7). Gravar ficha por ficha é o caminho que estoura | 🟡 |
| Segurança | A credencial do banco entra por variável de ambiente; o `.env` já está no `.gitignore` e **não** é versionado; o banco não é exposto fora do host | `RF-11`; `_reversa_sdd/permissions.md` (zero autenticação no sistema); `.gitignore` linha 6 | 🟢 |
| Segurança | O volume do banco contém **dado genético real** (nome, kit, cM, veredito) **sem criptografia em repouso**, por **aceite de risco declarado em 2026-10-08** (§9, `Q-04`): máquina local, um usuário só, mesmo regime do aceite do `BUG-20260929-BJJH`. A condição que **reabre** o assunto é a mesma daquele aceite — qualquer pessoa além do operador passar a ter acesso antes da Onda 5. Criptografia, retenção e expurgo seguem especificados para a **Onda 5** do alvo | `.reversa/principles.md#I`; `_reversa_sdd/migration/ambiguity_log.md` (`AMB-017`); `_reversa_sdd/migration/risk_register.md#RISK-005`; `_reversa_sdd/adrs/18-single-tenant-por-aceite-de-risco.md` (o precedente do aceite) | 🟢 |
| Observabilidade | O operador precisa saber **se a análise foi gravada**, sem ter de abrir o banco. Uma gravação que falha em silêncio é pior que uma que não existe — e é o **único** sinal possível, porque a `RN-13` manda a análise concluir de qualquer forma | `RF-17`; decisão de 2026-10-08 (§9, `Q-03`); RNF de Observabilidade já praticado na feature 007 (`T002`); `_reversa_sdd/architecture.md#6` (hoje não há nenhum log de integração externa) | 🟢 |
| Operação | O comando de subida roda a partir da raiz, com a aplicação e o banco em contêineres próprios, e os dois estados persistentes em volume nomeado. Os artefatos de infraestrutura ficam **na raiz** (`docker-compose.yml`, `init.sql`) e em **`docker/`** (`Dockerfile`, `.dockerignore`), por decisão de 2026-10-08 (§9, `Q-05`) | `_reversa_sdd/architecture.md#2` ("Não há container de banco, fila, cache, worker assíncrono, serviço externo ou container de aplicação adicional"). Confirmado por varredura: **não existe** `Dockerfile`, `docker-compose.yml` nem `.dockerignore` na raiz. É também o motivo declarado de o `deployment.md` da extração não ter sido gerado (`.reversa/state.json`, checkpoint `architect_reextracao_2026_10_05`) | 🟢 |
| Concorrência | A aplicação serve com **4 threads** e a guarda de instância única é de **processo**, não de thread. Cada requisição usa a **sua própria** conexão, e a gravação de uma análise não depende de estado compartilhado de conexão | `_reversa_sdd/architecture.md#2` e `#7` (dívida #3); `src/app.py` (`ANALISADOR_THREADS = 4`) | 🟢 |
| Manutenibilidade | O esquema não pode contradizer o DDL do alvo sem declarar a contradição | `RN-09`; o DDL congelado é anterior ao confronto (§2) | 🟢 |
| Compatibilidade | A dependência nova é instalada no interpretador **oficial** do projeto, o `.venv/`, e pinada; a suíte passa **igual** nos dois interpretadores | `requirements.txt` (cabeçalho da decisão de 2026-10-05, `questions.md#pergunta-11`); dívida #2 fechada | 🟢 |
| Reprodutibilidade | Gravar e reler duas vezes a mesma análise produz exatamente os mesmos valores, sem alterar nenhum veredito | `.reversa/principles.md#II`; `RISK-004` (`SUM` do banco no lugar do total do núcleo pode cruzar limite de faixa) | 🟢 |
| Privacidade | Nenhum dado real é usado em teste, fixture, evidência ou captura desta feature | `.reversa/principles.md#I` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: análise com um kit é registrada com o veredito
  Dado um GEDCOM sintético com caminho documental entre a raiz e um match
  E um CSV sintético com um kit e cM dentro da faixa esperada
  Quando a análise de DNA é executada
  Então existe uma análise gravada com a chave de conteúdo do GEDCOM e a do CSV
  E o veredito gravado é COMPATIVEL
  E o método da janela, a faixa esperada e o motivo estão gravados
  E as pessoas do caminho e o kit estão gravados com os mesmos valores da tela

Cenário: dois kits do mesmo nome geram dois registros e um veredito final conservador
  Dado um CSV sintético com dois kits para o mesmo nome, com cM em faixas diferentes
  Quando a análise é executada
  Então existem dois registros de kit, e nenhum total somado entre eles
  E cada kit tem o seu próprio estado gravado
  E o estado final gravado é o mais conservador entre os dois
  E o motivo registra que o estado final é o mais conservador

Cenário: análise sem evidência genética utilizável não inventa número
  Dado um CSV sintético cujo match não tem valor de cM utilizável
  Quando a análise é executada
  Então o veredito gravado é INCONCLUSIVO
  E o motivo gravado explica a ausência de dado utilizável
  E o total de cM está nulo, e não zero

Cenário: falha de gravação não deixa análise pela metade
  Dado que a gravação falha depois de gravar parte dos registros da análise
  Quando a transação é encerrada
  Então nenhum registro daquela análise permanece no banco
  E o resultado exibido na tela não é alterado pela falha

Cenário: a análise conclui e é exibida com o banco fora do ar
  Dado o banco de dados indisponível
  E um GEDCOM sintético e um CSV sintético válidos
  Quando a análise de DNA é executada
  Então a tela exibe o mesmo resultado e o mesmo veredito de quando o banco está no ar
  E o operador recebe um aviso não bloqueante de que o histórico não foi registrado
  E nenhum registro parcial permanece no banco

Cenário: o histórico sobrevive ao reinício dos serviços
  Dada uma análise já gravada
  Quando os serviços são derrubados e sobem de novo
  Então a análise continua consultável
  E os resultados relidos estão na mesma ordem em que foram exibidos
  E o arquivo enviado continua presente na pasta de uploads

Cenário: nenhuma credencial vaza para o repositório, a imagem ou a tela
  Dado o projeto com a feature implementada
  Quando o repositório, os arquivos versionados, a saída de erro e a tela são inspecionados
  Então nenhuma credencial de banco aparece
  E a string de conexão só existe na variável de ambiente
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem os dois serviços subindo juntos e sem volume, não há histórico: o dado morre com o contêiner |
| RF-03, RF-04, RF-05, RF-06, RF-07, RF-08 | Must | São exatamente as três coisas pedidas: pessoas, metadados de kit e o status do confronto — mais o porquê e os descartes, sem os quais o histórico não responde à pergunta de auditoria |
| RF-09 | Must | Sem a ordem gravada, a releitura devolve outra sequência e o histórico passa a contradizer a tela (`E-01`: ordem é dado) |
| RF-10 | Must | Análise pela metade é pior que análise ausente: o veredito de um par ficaria gravado com dados de outro |
| RF-11 | Must | Credencial versionada em dado genético é falha irreversível, e o `.gitignore` já protege o caminho — o código não pode furá-lo |
| RF-12 | Must | `init.sql` não idempotente torna cada subida um risco de perda do histórico |
| RF-13 | Must | É o portão do `Princípio II`: se o banco entrar no caminho crítico, a feature deixa de ser camada de saída |
| RF-14 | Should | É o valor prático do histórico (reabrir sem refazer), mas depende de decisão de interface que esta feature não toma |
| RF-15 | Should | O projeto já paga caro por dependência sem pin (dívida #2, `RISK-006`); repetir não se justifica |
| RF-16 | Should | Protege o `Princípio I`; já há precedente no `.gitignore` |
| RF-17 | Must | Sem ele, o banco fora do ar esconde o resultado do operador, e o histórico deixa de ser benefício para virar dependência do caminho crítico (`RN-13`, decisão de 2026-10-08) |
| RNF de Desempenho | Should | Importa para o uso real (71 conexões), mas a corretude vem antes |
| RNF de Observabilidade | Must | É o **único** sinal de que a gravação falhou: pela `RN-13` a análise conclui de qualquer forma, então sem aviso a falha é indistinguível de sucesso — e o histórico passa a mentir por omissão |
| RNF de Segurança (criptografia em repouso) | Could | Por **aceite de risco de 2026-10-08** (§9, `Q-04`): o alvo o especifica para a Onda 5, e antecipá-lo agora não foi pedido |

## 9. Esclarecimentos

### Sessão 2026-10-08

Cinco perguntas dirigidas, todas respondidas. Cada resposta foi integrada **in-place** no
ponto do documento onde a dúvida vivia; o mapa pergunta → mudança está em cada item.

- **Q-01 (escopo) — esta feature reverte o adiamento registrado no `gaps.md#6` e grava no `src/`?**
  **R:** ✅ **Deliberada — o adiamento caduca.** A aplicação passa a gravar de verdade no banco,
  e o esquema vira a base real quando a Onda 3 chegar, em vez de ser descartado por ela.
  *Aplicado em:* §1 (parágrafo novo), §2 (conflito resolvido), `RN-09`. `[DÚVIDA-01]` removida.
- **Q-02 (modelo de dados) — quais pessoas da árvore entram no banco?**
  **R:** ✅ **Só as que a análise usou e exibiu** — a raiz, o match casado, os nós do caminho
  documental e as fichas de desambiguação de homônimos. A árvore inteira **não** é duplicada.
  *Aplicado em:* `RN-04`, que passa de 🟡 para 🟢.
- **Q-03 (falha de gravação) — o que acontece quando o banco está fora?**
  **R:** ✅ **A análise conclui e é exibida normalmente**; a falha vira **aviso não bloqueante**.
  O operador nunca perde o resultado por causa do histórico. É a política **(i)**.
  *Aplicado em:* `RN-13` (nova), `RF-17` (novo), cenário Gherkin novo, RNF de Observabilidade
  (🟡 → 🟢), nota de `RF-13`/`RF-17` e MoSCoW. `[DÚVIDA-03]` removida.
- **Q-04 (privacidade) — como o volume do banco nasce?**
  **R:** ✅ **Sem criptografia, com aceite de risco** — máquina local, um usuário só, mesmo regime
  do aceite do `BUG-20260929-BJJH`, com a mesma condição de reabertura nomeada.
  *Aplicado em:* RNF de Segurança (🟡 → 🟢, com o aceite escrito), MoSCoW, §12. `[DÚVIDA-02]`
  removida.
- **Q-05 (caminhos da raiz) — como os artefatos de infraestrutura entram?**
  **R:** ✅ **`docker/**` mais os dois arquivos da raiz.** O `docker-compose.yml` e o `init.sql`
  permanecem na **raiz**, como no pedido original (itens 1 e 2); `Dockerfile` e `.dockerignore`
  vão para **`docker/`**. A liberação é **ato do usuário** em `.reversa/reversa-config.json`;
  o conteúdo exato está em §10.
  *Aplicado em:* RNF de Operação e §10.

## 10. Lacunas

Nenhuma lacuna aberta nesta feature. As três dúvidas da versão inicial foram resolvidas na
sessão de 2026-10-08 (§9) e as respostas foram integradas ao documento, sem sobra:

| Dúvida | Resposta | Onde mudou |
|--------|----------|------------|
| `[DÚVIDA-01]` — escopo | `Q-01`, deliberada | §1, §2, `RN-09` |
| `[DÚVIDA-02]` — privacidade | `Q-04`, aceite de risco | RNF de Segurança, MoSCoW, §12 |
| `[DÚVIDA-03]` — falha de gravação | `Q-03`, aviso não bloqueante | `RN-13`, `RF-17`, Gherkin, RNF de Observabilidade |

Duas questões que **não** eram lacunas também foram decididas na mesma sessão: o escopo dos
dados de pessoa (`Q-02` → `RN-04`) e o layout dos artefatos de infraestrutura (`Q-05` → RNF de
Operação).

> ⚠️ **Impedimento declarado, que não é lacuna — ação do usuário, ainda pendente.** A política
> de edição do legado em `.reversa/reversa-config.json` libera `src/**`, `tests/**`,
> `requirements.txt`, `README.md`, `pyrefly.toml`, `.vscode/**` e `.markdownlint-cli2.jsonc`.
> Por decisão de 2026-10-08 (§9, `Q-05`), ela precisa passar a liberar também `docker/**`,
> `docker-compose.yml` e `init.sql`:
>
> ```json
> "allowedPaths": ["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml",
>                  "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc",
>                  "docker/**", "docker-compose.yml", "init.sql"]
> ```
>
> Sem isso, o `/reversa-coding` **recusa** esses arquivos e a feature para no meio. O Reversa
> não edita `reversa-config.json` por iniciativa própria: a liberação é ato do usuário, e
> precisa acontecer antes do coding. **Esta pendência não bloqueia o `/reversa-plan`.**

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-08 | Sessão de esclarecimento (`/reversa-clarify`): cinco perguntas respondidas, três `[DÚVIDA]` zeradas. `RN-13` e `RF-17` criados, `RN-04` confirmado, aceite de risco de privacidade registrado, layout da infraestrutura fixado | reversa |

## 12. Fora de escopo declarado

O que segue **não** é entregue por esta feature, e o registro existe para que a ausência não
seja lida como esquecimento:

| Item | Por quê |
|------|---------|
| **Registrar o veredito do operador** por conexão (aceitei / rejeitei / corrigi) | É o requisito nº 2 do `_reversa_sdd/gaps.md#6`, **dependente** deste. Exige decisão de interface que esta feature não toma |
| **Interface de histórico** — tela para listar, comparar ou reabrir análises | Esta feature entrega o **armazenamento** e a consulta direta (`RF-14`). A tela é escopo da onda de apresentação |
| **Isolamento por dono** | Dívidas #3 e #4 seguem **abertas** (`RN-10`); o `dono` vira coluna, não filtro |
| **Substituir o arquivo de upload pelo banco** | O `RN-04` mantém a árvore como arquivo imutável; o banco guarda o resultado, não o insumo |
| **Migrar as regras do núcleo para o banco** (matching, faixas, confronto) | `RN-01` e `RN-02`: a decisão continua no núcleo. Este é o escopo do alvo, não desta feature |
| **Reconciliar as duas lacunas do DDL do alvo** (veredito e kits) no próprio artefato de migração | Os artefatos de `_reversa_sdd/migration/` estão **preservados sem regeneração** desde 2026-09-28. Esta feature **nomeia** a divergência (§2, `RN-09`); corrigir o artefato é ato da onda seguinte |
| **Criptografia em repouso, retenção e expurgo** | Especificados para a Onda 5 do alvo. O aceite de risco de 2026-10-08 (§9, `Q-04`) cobre a **ausência deles agora**, não a dispensa deles |
| **Pipeline de CI, build ou análise estática** | Ausente desde sempre (`_reversa_sdd/architecture.md#7`, dívida da extração anterior) e não é o que esta feature resolve |

## Pendências de Qualidade

Auto-validação contra `.reversa/templates/quality-template.md`, aplicada após a escrita. Uma
reprovação **deliberada**, declarada em vez de silenciada:

### Q-018 | SoluçãoImplícita — REPROVADO, por decisão do solicitante

> motivo: o requisito do template manda não haver "nome de biblioteca, framework ou produto
> comercial no documento", e este documento nomeia PostgreSQL, Docker, `docker-compose`,
> `init.sql`, `DATABASE_URL` e `psycopg2`/SQLAlchemy em §2, §6 e §12.
> decisão: **mantidos**. A intenção do item é impedir que o **redator** invente a solução; aqui
> a tecnologia é **restrição dada pelo solicitante**, não escolha do redator. Removê-la
> produziria um documento que não descreve o que foi pedido.
> mitigação aplicada: o núcleo do documento (§4, §5, §7) permanece no **quê** — estados,
> dados, invariantes, ordem, transação —, e os nomes de produto ficam concentrados nas seções
> de restrição (RNF de Operação, `RF-11`, `RF-12`, `RF-15`) e nesta nota. Um reimplementador
> pode trocar o produto mantendo o contrato.
> reavaliado depois da sessão de esclarecimento de 2026-10-08: a reprovação **permanece**, pelos
> mesmos motivos — e a decisão de `Q-05` até **acrescenta** nomes de arquivo ao documento.

### Q-014 | EdgeCases — Concorrência

> motivo: avaliado e **aprovado**, mas o registro fica explícito porque é o ponto onde a
> feature mais facilmente quebra o sistema. A aplicação serve 4 threads com estado de processo
> e a guarda de instância única não cobre thread (dívida #3).
> mitigação: o RNF de Concorrência exige conexão **por requisição**, e o `RF-10` exige
> transação por análise; nenhum estado de conexão é compartilhado entre threads.
