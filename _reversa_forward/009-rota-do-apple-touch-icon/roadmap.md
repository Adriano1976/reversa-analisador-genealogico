# Roadmap: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Requirements: `_reversa_forward/009-rota-do-apple-touch-icon/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Uma rota de leitura, registrada em `src/app.py` ao lado da rota do formulário, que devolve um
PNG **opaco de 180×180** — a arte do projeto composta sobre branco. A imagem é gerada **uma
vez**, a partir da arte canônica, e **commitada** dentro de `src/assets/`; em tempo de execução
nada é gerado, nada é lido de `docs/` e nenhuma conexão nova existe.

O caminho não é escolha nossa: é o que o sistema móvel procura por convenção na raiz do site.
Por isso a entrega é **acréscimo puro** — o template não é tocado, `GET /` continua byte a byte
idêntico, e as três linhas atuais do contrato HTTP ficam como estão, com uma quarta ao lado.

Como o alvo é um arquivo fixo de propriedade do projeto, a rota **não tem entrada**: nada do
cliente entra na composição do caminho. É a mesma disciplina de forma que protege o upload
desde o `BUG-20260929-QMLY`, aplicada a um caso em que ela é ainda mais simples — aqui não há
formulário.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A arte é **marca do projeto**, não dado de genealogia. Nenhum GEDCOM, CSV, nome ou kit é tocado. A nova pasta `src/assets/` recebe um único binário derivado do logo | respeita |
| II. Comportamento observável é preservado em refatoração | `GET /` continua **byte a byte** idêntico (`RF-05`). Esta feature não é refatoração: é capacidade nova, e a parte que existia fica intocada | respeita |
| III. Nenhuma mudança sem teste que a cubra | `RF-08`: o teste da rota falha antes e passa depois. Além dele, `RF-10` cria o teste de deriva, que é o que impede a arte de runtime envelhecer em silêncio | respeita |
| IV. Arestas do grafo são tipadas | n/a — a feature não percorre o grafo | n/a |
| V. Toda suposição de genealogia genética cita a fonte | n/a — nenhum número de domínio é criado ou alterado | n/a |

**Nenhum princípio conflita.** Não há, portanto, seção de conflito a escalar ao
`/reversa-principles`.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| `D-01` | A rota vive em **`src/app.py`**, registrada com `GET` apenas, ao lado da rota do formulário | Servir um arquivo fixo é **adaptação de entrada**, não caso de uso: não há regra, não há porta, não há núcleo a chamar. É a mesma fronteira que a `RF-01` da 006 desenhou | (a) criar caso de uso em `src/application/` — cerimônia sem consumidor; (b) criar um *blueprint* novo para uma rota — estrutura para um arquivo; (c) servir pelo próprio `index()` negociando conteúdo — polui a rota que tem de ficar idêntica | 🟢 |
| `D-02` | A arte de runtime é uma **renderização derivada** da arte canônica: `docs/assets/img/logo.png` **composta sobre branco `#ffffff`** e redimensionada para **180×180**, commitada como binário | A fonte não pode ser lida em runtime: `docs/` **não entra no contexto de build** (`.dockerignore` é lista de permissão), então gerar no container é impossível. Gerar no host, a cada partida, seria I/O no *import* — o `src/app.py` é importado pela suíte e pelo harness de paridade | (a) gerar em tempo de build — impossível, a fonte está fora do contexto; (b) gerar em tempo de execução no *import* — I/O e dependência de imagem no runtime; (c) commitá-la transparente como a canônica — produz o ícone de fundo **preto** (medido: 32,5 % de pixels transparentes) | 🟢 |
| `D-03` | A arte mora em **`src/assets/`** | É a única pasta do projeto que pode receber binário de propriedade do produto: `src/templates/` misturaria marcação com imagem, e `src/static/` é **proibida** pelo `W004` desde a feature 003 | (a) `src/templates/` — mistura duas naturezas de arquivo; (b) `src/static/` — **proibida**, reabre o `W004`; (c) a raiz do projeto — **não entra** na imagem | 🟢 |
| `D-04` | Servir com a facilidade de arquivo do próprio framework, que já responde `Last-Modified` e marca de versão e trata a requisição condicional sozinha | Entrega o comportamento do `RF-07` sem uma linha de código nossa para calcular marca de versão, e sem reabrir o arquivo a cada requisição | (a) devolver os bytes num corpo simples — perde a revalidação condicional e o `304`; (b) servir por diretório — desnecessário para **um** arquivo, e convida a caminho parametrizado | 🟢 |
| `D-05` | **Nenhuma** validade longa de cache é declarada | `RN-04` da sessão de esclarecimento (§9, `Q-04`): a arte foi trocada **duas vezes em 2026-10-08**, e uma validade de um ano congelaria o cliente que já tivesse buscado | (a) validade de um ano — o ícone antigo ficaria preso até 2027; (b) nenhum cabeçalho — perde a revalidação barata | 🟢 |
| `D-06` | O caminho do arquivo é derivado de `__file__`, **nunca** de entrada do cliente | Não existe parâmetro de rota, não existe `query string` lida, não existe nome de arquivo vindo de fora. A rota é imune por construção à classe de falha do `BUG-20260929-QMLY` | (a) `/icone/<nome>` — abriria travessia de caminho gratuitamente; (b) ler a arte de `docs/` por caminho relativo ao diretório corrente | 🟢 |
| `D-07` | A recusa de método sai **de graça**: registrar a rota só com `GET` faz o framework responder a recusa sozinho | `RF-06` fica satisfeito sem código nosso, e sem chance de a validação divergir da convenção | (a) inspecionar o método à mão dentro do tratador — código para reproduzir o que o roteador já faz | 🟢 |
| `D-08` | O teste de deriva **regenera** a imagem a partir da canônica e compara **pixel a pixel**, na mesma transformação de `D-02` | É a única comparação que funciona: o arquivo de runtime é **derivado**, então comparar os dois arquivos crus seria comparar 512×512 transparente com 180×180 opaco. Regenerar também detecta troca de desenho, que uma comparação de dimensões não pegaria | (a) comparar `sha256` dos dois arquivos — **medido**: o mesmo desenho existe com 32.317 e com 44.069 bytes e diferença de pixel **zero**, então daria alarme falso na primeira recompressão; (b) comparar só dimensões e modo — não detecta arte trocada | 🟢 |
| `D-09` | O teste usa a biblioteca de imagem que **já está** no `.venv/`, **sem** acrescentá-la a `requirements.txt` | `requirements.txt` é a lista de **runtime** — e o container não precisa de biblioteca de imagem, porque `D-02` gera a arte uma vez, fora dele. Acrescentá-la seria pagar peso na imagem por um teste | (a) acrescentar a biblioteca ao `requirements.txt` — peso no runtime por dependência de teste; (b) não fazer o teste de deriva — perde o `RF-10` | 🟡 |
| `D-10` | O `interfaces/` desta feature documenta **a quarta linha** do contrato HTTP, e é o **primeiro** do projeto | A regra manda criar o diretório quando a feature toca contrato externo — e esta toca: `contracts.md#1` tem três linhas e passa a ter quatro. Nenhuma feature anterior criou um contrato externo novo, então nenhuma teve o que documentar ali | (a) omitir e anotar só no `roadmap.md` — contraria a regra do próprio skill; (b) reescrever `contracts.md` — é artefato da extração, e a regra é adendo | 🟢 |

> **A receita de `D-02`, medida e não descrita.** Ela foi executada nesta sessão sobre a arte
> canônica: compor sobre branco, reamostrar para 180×180 com reamostragem de alta qualidade e
> salvar como PNG otimizado produz **16.504 bytes**, com canal alfa em `(255, 255)` e os quatro
> cantos em `(255, 255, 255)`. É 21 % menor que os 20.954 bytes da mesma arte **transparente**,
> porque o fundo branco chapado comprime melhor. Quem implementar tem, portanto, um valor
> esperado para conferir — e ele **não** é o mesmo da arte canônica.
>
> **Refinamento declarado de redação no `requirements.md`.** A `RN-05` diz que a feature
> "acrescenta uma **cópia** de runtime sob `src/`". O termo é frouxo: `D-02` estabelece que não
> é cópia, é **renderização derivada** (opaco, 180×180, composta sobre branco). A decisão
> técnica está tomada aqui e é a que vale; a palavra na `RN-05` fica registrada como imprecisa,
> e **não** foi corrigida por este skill, que não escreve no `requirements.md`. Quem quiser a
> redação exata roda `/reversa-clarify` ou corrige o termo — a diferença é de vocabulário, não
> de escopo, e o `RF-10` já está escrito de forma compatível com a versão precisa.

## 4. Premissas

n/a — nenhuma `[DÚVIDA]` em aberto no `requirements.md` (as três foram resolvidas na sessão de
2026-10-08). Nenhuma premissa foi adotada.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Camada de rota | `_reversa_sdd/c4-components.md` § "Camada de rota"; `_reversa_sdd/upload-gedcom/contracts.md#1` | `contrato-alterado` | A camada de rota deixa de ter **uma** rota. O contrato HTTP passa de três para quatro linhas: `GET /apple-touch-icon.png` → `200` com imagem. Nenhuma das três linhas existentes muda |
| Arte do produto | `_reversa_sdd/architecture.md#3` (inventário de pacotes) | `componente-novo` | `src/assets/` não existe no inventário. Recebe **um** binário derivado da arte canônica |
| Dívida #17 | `_reversa_sdd/architecture.md#7` | `presença` | ❌ **INALTERADA, de propósito.** A dívida era *"superfícies de compatibilidade reexportando nomes históricos que ninguém usa"* e está **fechada**. A `RN-09` existe para que esta entrega não a reabra: nenhum caminho sem consumidor é criado |
| `src/static/` | `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#W004` | `presença` | ❌ **INALTERADA.** A pasta continua **ausente**. Um binário em `src/assets/` **não** é pasta estática, e não há configuração de diretório estático |
| Superfície HTTP | `_reversa_sdd/addenda/008-persistencia-postgres-docker.md` § "O que a extração não precisa mudar" | `presença` | ❌ **INALTERADA.** A 008 declarou "mesmas rotas, mesmos campos, mesmos status, mesmo template". Esta entrega acrescenta uma rota e **não** altera nenhuma das existentes: o template não é tocado |
| Mapa de integrações externas | `_reversa_sdd/architecture.md#6` | `presença` | ❌ **INALTERADA.** Nenhuma dependência externa nova. A feature é servida do próprio processo, sem rede de saída |

## 6. Delta no modelo de dados

- Resumo das mudanças: **nenhuma**. Nenhuma estrutura do ERD é criada, alterada ou removida;
  nenhum campo, nenhum índice, nenhuma migração. O único arquivo novo em disco é um binário de
  arte, que não é entidade do modelo.
- Detalhe completo em: `_reversa_forward/009-rota-do-apple-touch-icon/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Ícone de atalho — `GET /apple-touch-icon.png` | HTTP | `_reversa_forward/009-rota-do-apple-touch-icon/interfaces/apple-touch-icon.md` |

## 8. Plano de migração

**n/a — não há dado a migrar.** Nenhum arquivo é renomeado ou movido, nenhum registro é
convertido, e a pasta `src/uploads/` não é tocada. A aplicação passa a responder a um caminho
que hoje responde `404`; nada que existe deixa de funcionar.

Consequência operacional, e não migração: **quem já tiver salvado o atalho antes desta feature**
continua vendo o ícone antigo até o sistema móvel refazer a busca. O sistema guarda o ícone do
atalho de forma agressiva e **ignora os cabeçalhos** nesse ponto — remover e salvar o atalho de
novo é o caminho, e está no `onboarding.md`. Não há o que fazer em código contra isso.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A rota responde `200` no host e `404` no contêiner, porque a arte ficou fora do contexto de build | alto | média | `RF-04` + cenário Gherkin próprio: a verificação é feita **dentro do contêiner**, e não só no host. `D-03` fixa a pasta em `src/` |
| O teste de deriva dá **alarme falso** e é desativado por ruído | médio | média | `D-08`: comparação por pixel, com a transformação de `D-02` reproduzida no teste. O risco já se materializou uma vez em medição — o mesmo desenho em 32.317 e 44.069 bytes |
| `src/assets/` é confundido com `src/static/` e a pasta proibida é reaberta | alto | baixa | `D-03` + `RN-07`; a ausência de `src/static/` continua vigiada pelo `W004`, e o nome escolhido não é `static` |
| Um caminho sem consumidor é criado "por simetria" (o alias legado, ou o `favicon.ico`) | médio | média | `RN-09` + `RF-11` + cenário Gherkin que afirma que os dois continuam **sem resposta**. A dívida #17 está nomeada na decisão |
| A biblioteca de imagem do teste não estar declarada em `requirements.txt` surpreende quem montar o ambiente do zero | baixo | média | `D-09` declara a separação: `requirements.txt` é de **runtime**. O ambiente de teste é o `.venv/`, que já a tem. Quem for rodar o teste em ambiente novo precisa dela, e o `onboarding.md` diz |
| O ícone opaco de 180×180 perder detalhe fino do desenho (galhos) na tela inicial | baixo | baixa | Aceito: a arte é a identidade visual e `RN-03` proíbe reinterpretá-la. Uma versão simplificada seria desenho novo, e é outra feature |
| A tela inicial continuar com o ícone antigo por cache do sistema | baixo | alta | Sem mitigação em código — é comportamento da plataforma. Documentado no `onboarding.md` com o procedimento de re-salvar o atalho |

## 10. Critério de pronto

- [ ] `GET /apple-touch-icon.png` responde `200` com imagem de **180×180** e **nenhum pixel transparente** (`RF-01`, `RF-02`, `RF-03`)
- [ ] A resposta `200` acontece **dentro do contêiner**, e não apenas no host (`RF-04`)
- [ ] `GET /` continua **byte a byte** idêntico ao de antes da feature (`RF-05`)
- [ ] Requisição repetida recebe resposta de "não modificado", sem corpo, e nenhuma resposta declara validade superior a um dia (`RF-07`)
- [ ] Os caminhos não servidos (`-precomposed` e `favicon.ico`) continuam **sem resposta** (`RF-11`)
- [ ] Nenhum byte foi acrescentado ao HTML de `GET /` (`RF-09`)
- [ ] O teste da rota **falha** contra o estado anterior e passa contra a entrega (`RF-08`)
- [ ] O teste de deriva falha ao alterar **um pixel** da arte de runtime, e **não** falha ao reencodar a canônica (`RF-10`)
- [ ] `src/static/` continua **ausente** (`W004`, `RN-07`)
- [ ] Suíte verde e paridade diferencial em **100 %** — a feature não toca o núcleo, então a paridade é a mesma de antes por construção, e isso tem de ser medido, não presumido
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-plan` | reversa |
