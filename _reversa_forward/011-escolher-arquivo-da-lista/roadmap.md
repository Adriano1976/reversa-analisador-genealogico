# Roadmap: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/011-escolher-arquivo-da-lista/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Esta é a **primeira feature que mexe na tela desde a reconstrução do legado**, e mexe em três lugares
ao mesmo tempo: a rota `GET /`, o ramo `dna_analysis` e o template. O núcleo não é tocado — ele já
recebe a árvore e o caminho do CSV por parâmetro.

O caminho técnico tem quatro movimentos: (a) a **listagem sai de uma capacidade nova da porta de
armazenamento**, e não de `os` dentro da rota, preservando a fronteira que a feature 006 estabeleceu
(a rota não fala com o disco); (b) o **agrupamento e a marca de "sem chave"** viram uma função **pura**
em `src/reporting/`, reusando a validação de forma fechada que já existe em `src/utils/validate.py`;
(c) o CSV escolhido viaja num **campo novo e opcional** (`matches_csv_filename`), e o campo de arquivo
`matches_csv` **continua existindo** — a mudança é aditiva, o contrato antigo fica intacto; (d) o
`GET /` passa a renderizar as duas abas com as listas, e o envio de arquivo se muda para dentro de cada
aba.

A prova de que a mudança de tela **não** quebra a paridade está no próprio instrumento: o harness
intercepta `render_template` (`harness.py:191`) e lê **chaves nomeadas** do contexto (`:211-221`), sem
comparar HTML, e só faz `POST` com `test_client()` — **nunca `GET /`**. Variável de contexto a mais é
invisível para ele.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A lista expõe **nomes de arquivo** no HTML — o mesmo regime que o contrato atual já pratica, que publica todos os nomes da árvore no `datalist`. As fixtures de teste da lista são sintéticas, e o inventário da pasta real não vai para nenhum teste | respeita |
| II. Comportamento observável é preservado em refatoração | **Não é refactor, é mudança de comportamento declarada** — e o `requirements.md` §6 diz isso. O que se preserva é o núcleo: ele continua recebendo árvore e caminho por parâmetro. A paridade de 100 % tem de continuar 100 % | respeita, com a natureza declarada |
| III. Nenhuma mudança sem teste que a cubra | Cada peça chega com teste: a função pura de agrupamento, a marca de "sem chave", a listagem pelo adaptador, o campo novo do CSV e o estado vazio. E a suíte **falha antes** de a tela mudar | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhum arquivo de `src/core/` é tocado | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhum número de cM, faixa ou heurística é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A listagem entra como **capacidade nova da porta de armazenamento** — `listar()` no `Protocol` e no `ArmazenamentoEmDisco` — e a rota consome a porta | A feature 006 tirou o acesso a disco da borda (`_arvore_do_formulario()` não resolve caminho, quem resolve é `CarregadorDeArvoresGedcom`). Fazer `os.listdir` na rota desfaria essa fronteira e tornaria a listagem não testável sem disco real | (a) `os.listdir` direto na rota — quebra a fronteira; (b) porta nova e separada só para listar — mais superfície do que a capacidade pede, porque é a **mesma** pasta | 🟢 |
| D-02 | O agrupamento pela chave e a marca de "sem chave" viram **função pura** em `src/reporting/`, reusando a forma fechada de `src/utils/validate.py` | `src/reporting/` é o pacote de "dado → apresentação", que é exatamente o que a lista é. Pura significa testável sem disco, e o reuso evita uma segunda definição da forma do nome — que é o contrato de segurança do armazenamento (`contracts.md#2.1`) | (a) agrupar no adaptador — mistura apresentação com I/O; (b) agrupar no template — Jinja não é lugar de regra, e não haveria teste de unidade; (c) reimplementar a forma do nome — duas verdades sobre a mesma regra | 🟢 |
| D-03 | O CSV escolhido viaja num **campo novo e opcional**, `matches_csv_filename`; o campo de arquivo `matches_csv` **permanece**, e o ramo usa a referência quando ela existe | Mudança **aditiva**: o caminho antigo (upload de arquivo) fica byte a byte igual, então a paridade, os testes de rota e o harness continuam exercitando exatamente o contrato de hoje. Nome espelha `gedcom_filename`, que já é "o nome armazenado da árvore" — a simetria é do operador, não invenção nossa | (a) reaproveitar `matches_csv` para texto — dois `input` do mesmo nome no mesmo formulário se atropelam, e o campo mudaria de lugar (`files` → `form`) no contrato; (b) `action` nova (`dna_analysis_from_list`) — duplica o ramo e dobra a superfície de paridade | 🟢 |
| D-04 | `GET /` passa a renderizar as duas abas com as listas **sempre**, e o envio de arquivo se muda para dentro de cada aba | É o `RF-06` e a resposta da §9: sem isso a feature não resolve o problema que a originou — o operador continua obrigado a enviar antes de ver qualquer coisa | (a) manter a tela de entrada como está — a lista só apareceria depois de um envio, que é o problema; (b) mostrar as abas e manter o formulário de envio acima delas — acumula duas telas de envio | 🟢 |
| D-05 | **O golden `SCR-001` NÃO é recapturado.** A premissa de que ele "deixa de valer" foi medida e é **falsa** | O golden captura o **oráculo legado congelado**, não a aplicação atual: `legacyOrigin: analisador-genealogico/templates/index.html:41-52`, `capture.command` aponta para `http://127.0.0.1:5001/` (a porta do oráculo) e `captureBy` é `_reversa_sdd/parity/_golden_capture.py`. O `inventory.json` cita `analisador-genealogico` 9 vezes e `src/templates` zero. Um oráculo congelado não deixa de valer porque o candidato mudou — é para isso que ele é congelado. O custo de recaptura que a §9 supunha **não existe** | (a) recapturar assim mesmo — gastaria trabalho para produzir uma cópia do legado, que é o que já está lá; (b) apagar o golden — destruiria a referência do pipeline de migração | 🟢 |
| D-06 | A consequência real da `D-04` fica **declarada como divergência**, não como golden: a aplicação atual deixa de ter a tela inicial "envie antes de tudo" que o legado tem | `_reversa_sdd/migration/` (35 arquivos) tem cenários `@paridade-visual` ancorados em `SCR-001` (`parity_specs.md`), e o alvo da migração foi desenhado sobre a tela legada. Nada disso fica errado — mas um leitor do pipeline precisa saber que o sistema **atual** não tem mais aquele estado inicial | (a) não declarar — o pipeline de migração seguiria supondo que o estado inicial do candidato é o do legado | 🟢 |
| D-07 | O estado vazio (`RF-07`) é tratado no template, e a pasta ausente **não** é erro: o adaptador devolve lista vazia | Uma instalação nova tem a pasta criada no import e vazia; e uma pasta que desapareça sob a aplicação em execução não pode virar exceção na tela | (a) `os.makedirs` na listagem — efeito colateral escondido numa leitura; (b) deixar estourar — a tela de entrada ficaria inutilizável | 🟢 |
| D-08 | O "arquivo escolhido que não serve" **não** é filtrado na lista; a recusa continua no uso (`RN-09`) | A validação de conteúdo já existe e já tem mensagem com motivo; a lista não lê conteúdo, e ler custaria 27,9 MB por renderização. **Correção medida na auditoria:** a segunda metade desta justificativa era **falsa** — a validação de conteúdo só roda no **envio**, e o arquivo escolhido por referência não passa por ela; o que existe é a recusa do resolvedor, com a mensagem falsa "não existe mais". A decisão de **não filtrar** continua valendo, e quem trata o caso na tela é a `D-11`. O cenário negativo continua na §7 | (a) validar na listagem — o custo que o RNF evita; (b) esconder o arquivo da lista — esconde dado do operador sem ele saber | 🟢 |
| D-09 | Quando o grupo tem **nomes visíveis diferentes**, o item exibe o nome **sem chave vazada**; contagem, tamanho e data acompanham, e a ordem é por data decrescente | **Medido:** o grupo da chave `080e7943572d2652` tem dois arquivos cujos nomes visíveis são `080e7943572d2652__Arvore_Unificada_Oficial_V1_2.ged` (chave **vazada**, porque o operador reenviou um arquivo que já tinha chave no nome) e `Arvore_Unificada_Oficial_V1_2.ged`. Exibir o primeiro por ordem alfabética mostraria a chave crua ao operador | (a) exibir o primeiro em ordem alfabética — vaza a chave; (b) exibir todos os nomes do grupo — polui a linha; (c) exibir o nome do arquivo mais recente — não é estável entre renderizações | 🟢 |
| D-10 | A **partição entre as abas** é pela extensão do **nome visível** — `.ged` na aba de árvore, `.csv` na de DNA — decidida na **mesma função pura** do agrupamento; arquivo de outra extensão não aparece em aba nenhuma | `RN-03` e `RN-09` mandam decidir por nome, sem ler conteúdo, e a extensão do nome visível é o único critério disponível sem abrir arquivo. **Medido:** o `.xlsx` (`Familias Sergipanas.xlsx`, 138.024 bytes) fica fora das duas abas, como hoje, e `Famílias_Sergipanas.csv.ged` entra na aba de árvore **apesar** de o conteúdo ser CSV — quem decide é o nome, e é o que `RN-09` declara. **Resíduo declarado:** `RN-03` diz "termina em `.ged`" na forma literal, e nenhum dos 19 arquivos medidos tem extensão em maiúsculas, de modo que a questão maiúscula/minúscula **não é exercitada** por dado nenhum — torná-la insensível é mudar `RN-03`, não esta linha | (a) particionar na rota — põe regra de negócio na borda e a deixa sem teste de unidade; (b) particionar no template — Jinja não é lugar de regra; (c) listar tudo nas duas abas — o operador escolheria na aba de árvore um arquivo que a validação de uso recusaria depois, escondendo o erro até o uso | 🟢 |
| D-11 | O item cujo arquivo **não pode ser usado por referência** é exibido **marcado como indisponível**, com o motivo, e **continua na lista**; a disponibilidade é decidida pela **mesma** `chave_recebida_e_valida` que o resolvedor usa | **Medido na pasta real, arquivo por arquivo** (`evidence/_sonda_forma_do_nome.py`): **6 dos 17 itens** que a lista desenha não podem ser escolhidos — 3 por **acento** no nome visível (`50a3dd36…__Famílias_Sergipanas.csv`, `94e2402671702cac__Famílias_Sergipanas.csv` e `…__Famílias_Sergipanas.csv.ged`), que a forma fechada de `validate.py:32` não admite, e 3 por **não terem chave**. Escolher qualquer um responde `Erro: Arquivo '…' não existe mais.`, que é **falso** — confirmado por execução da rota contra a pasta real (`evidence/_sonda_caso_negativo_real.py`). A `D-08` supunha que a "validação de uso" pegaria o caso: **não pega**, porque ela só roda no envio. Reusar `chave_recebida_e_valida` — em vez de reimplementar o teste de alcance — é o que garante que a marca da tela e o resolvedor nunca divirjam | (a) esconder os itens — esconde arquivo do operador e contradiz a `RN-10` e a `D-08`; (b) consertar a forma do nome aqui — mexe na defesa contra escape de caminho dentro de uma feature de listagem, e não alcança os 3 sem chave de qualquer modo; (c) deixar como está — 6 itens oferecidos que só produzem uma mensagem falsa | 🟢 |

## 4. Premissas

Nenhuma premissa vem de `[DÚVIDA]` não resolvida: o documento chegou ao plano com **0** marcadores,
depois da sessão de esclarecimento de 2026-10-09.

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| A paridade continua **100 %** apesar da mudança de template | Medido por leitura do instrumento: `harness.py:191` intercepta `render_template` e `:211-221` lê chaves nomeadas; não há `GET /` no harness | Se o harness de fato comparasse HTML, a paridade cairia e a feature teria de recapturar a referência do instrumento. **Verificação:** rodar `tests/rodar_paridade.py` antes e depois e conferir 100 % nos dois — é ação do `onboarding.md` 🟢 |
| O campo novo `matches_csv_filename` não muda a contagem de 16 MB nem o caminho de 413 | É campo de formulário curto; o teto é de corpo de requisição, e o corpo continua sendo multipart | A mensagem de 413 poderia mudar de texto se o teto fosse recalculado. **Verificação:** teste de rota do teto continua passando 🟢 |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Porta de armazenamento | `src/ports/__init__.py`; `_reversa_sdd/upload-gedcom/design.md` | contrato-novo | Ganha `listar()`: devolve as entradas da pasta (nome armazenado, bytes, data) sem ler conteúdo |
| Adaptador de disco | `src/ports/adaptadores.py` (`ArmazenamentoEmDisco`) | regra-alterada | Implementa `listar()` sobre a pasta canônica; pasta ausente devolve lista vazia, não exceção |
| Apresentação da lista | `src/reporting/` | componente-novo | Função pura que **seleciona pela extensão do nome visível**, agrupa entradas pela chave, marca as sem chave e calcula, para cada item, se ele é **alcançável por referência** e o motivo quando não é — reusando a forma fechada do `src/utils/validate.py` (`D-02`, `D-10`, `D-11`) |
| Borda HTTP, rota | `src/app.py` (`index()`, `_arvore_do_formulario()`) | contrato-alterado | O `GET /` monta as duas listas e as entrega ao template; o ramo `dna_analysis` passa a aceitar a referência do CSV |
| Contrato do formulário | `_reversa_sdd/openapi/index.yaml:167-179` | contrato-alterado | `dna_analysis` ganha campo opcional `matches_csv_filename`; `matches_csv` deixa de ser obrigatório quando a referência vem |
| Template da tela de entrada | `src/templates/index.html:41-63` | contrato-alterado | O ramo `{% if not gedcom_filename %}` deixa de ser um formulário de envio e passa a ser as duas abas; o envio se muda para dentro de cada aba, e o item indisponível (`D-11`) ganha a marca com o motivo |
| Domínio: fluxo de decisão por ação | `_reversa_sdd/domain.md` §4, linha de `action=dna_analysis` | **regra-alterada** | A pré-condição 🟢 "CSV presente" passa a **"CSV presente ou referência presente"** (`matches_csv_filename`). O caminho antigo continua válido e a mensagem de arquivo ausente (`domain.md:192`) é preservada; o que deixa de valer é a leitura **literal** da linha, que vira uma disjunção |
| Núcleo, parsers, casos de uso | `src/core/`, `src/parsers/`, `src/application/` | **sem mudança** | Continuam recebendo árvore e caminho por parâmetro; a paridade de 100 % é a prova |
| Instrumento de paridade | `_reversa_sdd/parity/harness.py` | **sem mudança** | Byte a byte igual; a insensibilidade ao template é propriedade dele, não ajuste nosso |
| Goldens de tela | `_reversa_sdd/screens/golden/` | **sem mudança** | Capturam o oráculo legado congelado (`D-05`); a divergência da app atual é declarada, não recapturada |

## 6. Delta no modelo de dados

- **Banco: nada muda.** Nenhum campo, nenhuma tabela, nenhuma migração.
- **Disco: nada é escrito.** Esta feature **lê** a pasta e não cria, move nem apaga arquivo — é o
  `RF-08`, e a prova é o inventário por `sha256` antes e depois de percorrer todas as telas.
- A "lista" **não é dado armazenado**: é derivada a cada renderização, e nada dela sobrevive à
  requisição (`RN-05`).
- Detalhe completo em: `_reversa_forward/011-escolher-arquivo-da-lista/data-delta.md`

## 7. Delta de contratos externos

A superfície HTTP muda em **um** ponto: o ramo `dna_analysis` ganha um campo **opcional**, e o `GET /`
muda o que renderiza. As três `action` mantêm nome, e **nenhum campo existente é renomeado ou
removido** (`RN-08`) — por isso o detalhe vive em `interfaces/`.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Formulário HTTP de `POST /` (`action=dna_analysis`) e a tela do `GET /` | HTTP (formulário) | `_reversa_forward/011-escolher-arquivo-da-lista/interfaces/formulario-http.md` |

## 8. Plano de migração

Não há migração de dados. O que existe é uma **sequência de construção**, com a paridade medida antes
de a tela mudar.

1. **Linha de base**: suíte e paridade medidas **antes** de qualquer edição, com o número registrado. É
   o que permite dizer "não caiu" depois.
2. **Porta e adaptador** (`D-01`): `listar()` no `Protocol` e no `ArmazenamentoEmDisco`, com teste de
   unidade sobre pasta temporária — incluindo pasta ausente devolvendo lista vazia (`D-07`).
3. **Função pura de apresentação** (`D-02`): agrupamento pela chave e marca de "sem chave", com teste
   sobre nomes sintéticos que cobrem os quatro casos medidos: com chave, com chave dupla, sem chave, e
   dois arquivos com a mesma chave.
4. **Borda** (`D-03`): o `GET /` monta as listas; o ramo `dna_analysis` aceita `matches_csv_filename`.
5. **Template** (`D-04`): as duas abas com a lista, o envio dentro de cada aba, o estado vazio, e o
   campo de escolha do CSV.
6. **Testes de rota**: `GET /` sem envio prévio responde 200 com as duas listas; a análise com a
   referência escolhida conclui; a análise com arquivo continua funcionando (o caminho antigo).
7. **Paridade e suíte depois** (`RF-08`, premissa de §4): 100 % e a suíte sem regressão.
8. **Inventário de escopo** (`RF-08`): `sha256` da pasta antes e depois de percorrer todas as telas —
   idêntico.
9. **Documentação**: `README.md` (a tela de entrada descrita deixa de existir) e o `onboarding.md`
   desta feature.
10. **Declarar a divergência** (`D-06`): `legacy-impact.md` registra que a app atual não tem mais o
    estado inicial do legado, para o pipeline de migração não supor o contrário.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A mudança de template quebrar a paridade de 100 % | alto | **baixa** | Medido por leitura: o harness lê chaves de contexto, não HTML (`harness.py:191`, `:211-221`), e não faz `GET /`. Ainda assim a paridade é medida **antes e depois** — a premissa de §4 tem verificação, não confiança |
| O campo novo do CSV mexer no contrato antigo e derrubar teste de rota ou paridade | alto | baixa | `D-03`: é **aditivo**. O caminho do arquivo fica intocado, e a paridade continua enviando `matches_csv` como arquivo |
| A listagem reler conteúdo e transformar a tela num gargalo | médio | baixa | `D-02`/`D-08`: a função pura só olha o **nome**; nenhum teste permite leitura de conteúdo |
| `os.listdir` na rota desfazer a fronteira da feature 006 | médio | média | `D-01`: a listagem entra pela porta; revisão de código com um teste que usa adaptador falso |
| Agrupar por chave esconder arquivo do operador | **alto** | baixa | Junto ao item agrupado vai a **contagem** de arquivos e o nome visível; e os sem chave aparecem em item próprio, nunca agrupados (`RN-10`) |
| O operador escolher um item que **não funciona** e concluir que o arquivo sumiu | **alto** | **certa — já ocorre hoje, medido** | **6 dos 17 itens** não podem ser usados por referência (`D-11`), e a resposta a eles é a mensagem falsa "não existe mais". Mitigação: o item é exibido **marcado como indisponível**, com o motivo (`RN-11`, `RF-09`), e a tela não oferece a escolha como se ela fosse funcionar |
| A pasta mudar entre a renderização e o uso (arquivo removido por fora) | médio | baixa | O caminho de "arquivo não existe mais" já existe e tem mensagem; a tela tem de continuar utilizável — entra no `onboarding.md` |
| A divergência com o legado passar despercebida pelo pipeline de migração | médio | média | `D-06` e o passo 10 do plano: declarada em `legacy-impact.md` e no adendo |
| Vários itens com o **mesmo nome exibido** na mesma aba, sem o operador saber qual é qual | médio | **alta — já ocorre hoje** | Medido: **3 arquivos** chamados `Arvore_Unificada_Oficial_V1_2.ged` na aba de árvore (com **2 conteúdos distintos**) e **3** chamados `Famílias_Sergipanas.csv` na de DNA (também 2 conteúdos) — incluindo um par com chave e sem chave com o **mesmo** conteúdo, que a lista mostrará como **dois itens**. Mitigação: a linha mostra tamanho e **data** (`D-09`), o item sem chave é marcado (`RN-10`) e a ordem é por data decrescente |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte medida antes e depois, sem regressão — o número de antes registrado em evidência
- [ ] `PARIDADE 100 %` pelo invólucro, com o `harness.py` byte a byte idêntico
- [ ] `GET /` responde 200 **sem** envio prévio e renderiza as duas abas com as listas (`RF-06`)
- [ ] A aba de árvore mostra 8 arquivos e 7 itens; a de DNA, 10 arquivos e 10 itens (`RF-01`, `RF-03`)
- [ ] Os três arquivos sem chave aparecem como item próprio, marcados (`RN-10`)
- [ ] O `.xlsx` da pasta **não** aparece em aba nenhuma, e `Famílias_Sergipanas.csv.ged` aparece na aba de árvore (`RN-03`, `D-10`)
- [ ] Os **6 itens indisponíveis** (3 na aba de árvore, 3 na de DNA) aparecem **marcados**, com o motivo, e continuam na lista (`RF-09`, `RN-11`, `D-11`)
- [ ] Nenhum item marcado como disponível falha ao ser escolhido — a marca e o resolvedor concordam (`D-11`)
- [ ] Escolher uma árvore e submeter a busca conclui **sem** novo envio (`RF-02`)
- [ ] Duas análises seguidas com CSVs diferentes escolhidos na lista concluem sem reenvio (`RF-04`)
- [ ] O envio pela aba continua validando conteúdo, gravando sob chave e aparecendo na lista (`RF-05`)
- [ ] Pasta vazia orienta o envio e responde 200 (`RF-07`)
- [ ] Inventário por `sha256` da pasta **idêntico** antes e depois de percorrer todas as telas (`RF-08`)
- [ ] `git diff -- src/core src/parsers src/application` **vazio** — o núcleo não foi tocado
- [ ] O golden `SCR-001` **não** foi alterado (`D-05`), e a divergência está declarada em `legacy-impact.md`
- [ ] `README.md` atualizado: a tela de entrada descrita não existe mais
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-plan` | reversa |
| 2026-10-09 | Correção vinda do `/reversa-audit`: `D-10` fecha o `A001` (a partição por extensão não tinha dono), e a linha de `domain.md` §4 entra no §5 como `regra-alterada`, fechando o `A003` | reversa |
| 2026-10-09 | Correção vinda do `/reversa-audit` (`A007`, `CRITICAL`): acrescentada a `D-11` (item indisponível marcado, com o motivo), corrigida a justificativa da `D-08` — a "validação de uso" **não** pega o caso, ela só roda no envio —, e atualizados o §5, o §9 e o §10. O defeito do contrato do nome (o gravador preserva acento, o resolvedor o recusa) fica fora do escopo, como bug próprio | reversa |
