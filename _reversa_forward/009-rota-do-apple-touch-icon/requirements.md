# Requirements: Rota do ícone de atalho para tela inicial

> Identificador: `009-rota-do-apple-touch-icon`
> Data: `2026-10-08`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Entrega o **ícone do atalho de tela inicial**. Hoje o projeto tem ícone na **aba** do
navegador, e nada além disso: quem salva o endereço na tela inicial do celular recebe um ícone
genérico do sistema, não o logo do projeto.

O motivo é de plataforma, e está medido: o ícone de atalho **não é o mesmo recurso** que o
ícone da aba. O sistema móvel procura um **caminho convencional na raiz do site** —
`/apple-touch-icon.png` — e espera um `200` com uma imagem. Ele **ignora** a imagem embutida no
documento, que é exatamente a forma como o ícone da aba é entregue hoje: um `data URI`, isto é,
a imagem codificada dentro do próprio HTML em vez de servida como arquivo.

Para quem: o **operador único** do sistema, que usa a aplicação no celular e quer reconhecê-la
pelo logo na tela inicial; e o desenvolvimento da onda seguinte, que herda a primeira rota
pública que **não** é o formulário.

O que **não** muda: a tela, o formulário, as mensagens, os status e o ícone da aba. Esta
entrega **acrescenta** um recurso e não toca em nada que já existe.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/upload-gedcom/contracts.md#1` | O contrato HTTP tem **três linhas** (`GET /`, `POST /` de upload, `POST /` com `413`) e afirma: "🟢 **Não há contrato JSON, redirect, `201`, `400` ou `409`.**" Esta feature **acrescenta a quarta linha** ao contrato | 🟢 |
| `_reversa_sdd/upload-gedcom/contracts.md#1.1` | O contrato da requisição é `multipart/form-data` com o campo `gedcom`. A rota nova **não tem requisição**: nenhum campo, nenhum corpo, nenhum estado | 🟢 |
| `_reversa_sdd/architecture.md#1` | A rota **adapta**, não orquestra; a orquestração vive nos casos de uso. Servir um arquivo fixo é adaptação pura, sem passo de domínio | 🟢 |
| `_reversa_sdd/domain.md#5.1` | As **dez mensagens** da camada de rota, literais e caso a caso. Nenhuma é criada, alterada ou removida: a rota nova não tem caminho de erro visível | 🟢 |
| `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#Impacto por artefato da extração` | A 008 declara a superfície HTTP como "**mesmas rotas**, mesmos campos, mesmos status, mesmos redirecionamentos, mesmo template" e registra o template com "+3 linhas, zero remoções". Esta feature **não toca no template** | 🟡 |
| `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#W004` | 🟢 Vigia a **ausência** de `src/static/`: "Reaparecimento de `src/README.md`, `src/.gitignore.txt` ou `src/static/`". O ícone **não** pode ser entregue por pasta estática | 🟢 |
| `.dockerignore` (medido, raiz do projeto) | O contexto de build é **lista de permissão**: `*`, depois `!requirements.txt`, `!src/`, `!src/**`, e por fim a reexclusão de `src/uploads/`. **Nada fora de `src/` entra na imagem** — um ícone em qualquer outra pasta não existiria em runtime | 🟢 |
| `src/app.py` (medido) | **378 linhas**, uma única rota (`@app.route("/", methods=["GET", "POST"])`, linha 193) e um único tratador de erro (`RequestEntityTooLarge`, linha 152). A rota nova é a **segunda** do arquivo | 🟢 |
| `src/templates/index.html:8` (medido) | O ícone da aba existe e é um **data URI embutido**, 128×128, PNG de 14.456 bytes (19.298 em base64), commitado em `b931062`. Ele responde por **19,3 KB** de cada página servida | 🟢 |
| `docs/assets/img/logo.png` (medido) | A arte canônica tem 512×512, 32.317 bytes, modo RGBA, e **32,5 % de pixels totalmente transparentes**; os quatro cantos são `(0, 0, 0, 0)`. ⚠️ Esta pasta **não** entra no contexto de build | 🟢 |
| `_reversa_sdd/screens/golden/SCR-001-initial-upload.html.txt:3-8` | O golden da tela inicial registra o `<head>` **sem** ícone: `<title>` seguido direto do Bootstrap. A tela inicial observada pelo golden **não muda** nesta entrega | 🟢 |
| `.reversa/principles.md#II` | "Comportamento observável é preservado em refatoração": mesmas entradas produzem as mesmas saídas | 🟢 |
| `.reversa/principles.md#III` | "**Nenhuma mudança sem teste que a cubra**": o teste novo tem de falhar antes | 🟢 |
| `.reversa/reversa-config.json` | `allowLegacyEdits: true` com `allowedPaths` cobrindo `src/**` e `tests/**`. A feature **cabe** na política sem pedir liberação nova | 🟢 |

> ⚠️ **Dois fatos medidos que moldam o requisito, e nenhum deles está registrado na extração.**
>
> 1. **O ícone da aba já foi resolvido por dentro do documento, e essa solução não serve para o
>    atalho.** O `data URI` é a resposta certa para a aba — não cria rota nova, que é uma
>    restrição declarada do próprio gerador (`.reversa/_favicon.py`: *"nao cria rota nova (a
>    aplicacao tem rota unica, documentada)"*). Para o atalho ele é **inerte**: o sistema móvel
>    não lê a imagem do documento, ele busca o caminho convencional.
> 2. **A arte tem fundo transparente, e isso é um defeito visível na tela inicial.** O sistema
>    móvel compõe o ícone sobre fundo **preto** quando o PNG tem transparência. Servir
>    `logo.png` como está produziria um ícone de fundo preto com o desenho por cima — e as
>    aberturas internas entre folhas e galhos também ficariam pretas. O ícone do atalho precisa
>    ser **opaco**; o PNG transparente continua correto para a aba, onde a composição é do
>    navegador.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Operador no celular** | Reconhecer e abrir o analisador a partir da tela inicial | Salva o endereço na tela inicial e vê o logo do projeto, não um ícone genérico do sistema |
| **Operador em uso repetido** | Voltar à aplicação sem digitar o endereço | Toca o atalho e a aplicação abre no formulário, com o ícone correto já cacheado pelo sistema |
| **Desenvolvedor da onda seguinte** | Ter precedente para a primeira rota que não é o formulário | Encontra o contrato HTTP com quatro linhas, a nova documentada com o mesmo rigor das três antigas |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Nenhuma regra de negócio é criada, alterada ou removida.** O núcleo continua
   puro e continua decidindo o que sempre decidiu. A entrega é recurso estático e não
   atravessa caso de uso nenhum. 🟢
   - Origem no legado: `.reversa/principles.md#II`;
     `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#Impacto por artefato da extração`.
   - Tipo: nova (restrição de escopo).
2. **RN-02 — A entrega acrescenta; não altera nenhuma resposta existente.** O HTML de `GET /`
   tem de continuar **byte a byte** o mesmo. Isso exclui, deliberadamente, acrescentar ao
   template um aviso do tipo de ícone: o caminho convencional é descoberto sem declaração, e
   declarar custaria mexer na tela e no `W005`. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#1`;
     `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md#W005`.
   - Tipo: nova (restrição de escopo).
3. **RN-03 — O ícone do atalho é a mesma arte do ícone da aba.** Não é uma variação, uma
   reinterpretação nem um segundo desenho. O que muda entre os dois é **fundo e tamanho**,
   nunca a identidade visual. 🟢
   - Origem no legado: arte medida em `docs/assets/img/logo.png` e em `src/templates/index.html:8`.
   - Tipo: nova.
4. **RN-04 — O ícone do atalho é opaco.** O arquivo servido não pode ter transparência: fundo
   sólido cobrindo a área inteira. O PNG transparente permanece válido para a aba. 🟢
   - Origem no legado: medido — 32,5 % de pixels transparentes e cantos `(0, 0, 0, 0)` em
     `docs/assets/img/logo.png`.
   - Tipo: nova.
5. **RN-05 — A arte servida mora dentro de `src/`.** O contexto de build só admite
   `requirements.txt` e `src/**`; qualquer outro caminho produz uma rota que responde `200` na
   máquina de desenvolvimento e `404` no contêiner. 🟢
   - Origem no legado: `.dockerignore` na raiz (lista de permissão) e
     `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#Impacto por artefato da extração`.
   - Tipo: nova.
6. **RN-06 — A rota nova é de leitura, sem entrada e sem estado.** Nenhum campo de formulário,
   nenhum parâmetro de consulta interpretado, nenhuma escrita, nada guardado entre requisições.
   Ela não pode ser confundida com o formulário. 🟢
   - Origem no legado: `_reversa_sdd/upload-gedcom/contracts.md#3` (contrato de estado).
   - Tipo: nova.
7. **RN-07 — `src/static/` continua ausente.** A entrega não pode reintroduzir pasta estática
   nem configurar diretório estático: é o `W004`, vigiado desde a feature 003. 🟢
   - Origem no legado: `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#W004`.
   - Tipo: nova (restrição de escopo).
8. **RN-08 — O que a tela mostra não passa a depender do ícone.** Se o ícone faltar, a
   aplicação continua funcionando por inteiro: o atalho degrada para ícone genérico e nenhuma
   rota existente muda de resposta. 🟢
   - Origem no legado: `.reversa/principles.md#II`.
   - Tipo: nova.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A aplicação responde a `/apple-touch-icon.png`, com status `200` e tipo de imagem declarado | Must | Requisição de leitura a `/apple-touch-icon.png` devolve `200` e `Content-Type` de imagem; medido por requisição real, não por leitura de código | 🟢 |
| RF-02 | O ícone servido tem **180×180** pixels | Must | O corpo da resposta decodifica em imagem de 180×180; dimensão medida no binário | 🟢 |
| RF-03 | O ícone servido é **opaco** | Must | Varredura do canal alfa do arquivo servido: nenhum pixel com alfa menor que 255 | 🟢 |
| RF-04 | A arte servida está sob `src/` | Must | O arquivo existe dentro de `src/` e a rota responde `200` **a partir do contêiner**, não apenas no host | 🟢 |
| RF-05 | `GET /` devolve exatamente a mesma resposta de antes da feature | Must | Comparação byte a byte da resposta de `GET /` antes e depois; zero diferença | 🟢 |
| RF-06 | A rota aceita apenas leitura, e recusa qualquer outro método | Should | Requisição de escrita ao caminho do ícone recebe recusa de método, e nenhuma escrita acontece no disco | 🟡 |
| RF-07 | A resposta do ícone é cacheável pelo cliente | Should | A resposta traz indicador de validação por conteúdo (marca de versão), para que o sistema móvel não rebusque a cada abertura | 🟡 |
| RF-08 | Existe teste automatizado que **falha antes** da mudança e passa depois | Must | O teste novo, executado contra o commit anterior, falha; contra a entrega, passa. `.reversa/principles.md#III` | 🟢 |
| RF-09 | A entrega **não** acrescenta bytes ao HTML de `GET /` | Must | A resposta de `GET /` mantém o mesmo tamanho em bytes de antes da feature | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | O ícone é servido **sem** recompô-lo nem lê-lo do disco a cada requisição; nenhuma rota existente fica mais lenta | O ícone da aba já custa 19,3 KB por página; a rota nova não pode somar a esse custo | 🟡 |
| Desempenho | A resposta do ícone é inferior a **50 ms** no host | Mesma ordem de grandeza das demais respostas locais do sistema | 🟡 |
| Segurança | A rota não interpola entrada do cliente em caminho de arquivo | É a mesma classe de falha do `BUG-20260929-QMLY`: nome controlado pelo cliente usado para montar caminho. A rota nova **não tem** entrada, e o requisito existe para que continue assim | 🟢 |
| Segurança | A rota não expõe listagem nem qualquer outro arquivo do projeto | Sem entrada, não há como endereçar outro recurso | 🟢 |
| Compatibilidade | O ícone é opaco, porque o sistema móvel compõe transparência sobre preto | Medido: `docs/assets/img/logo.png` tem 32,5 % de pixels transparentes | 🟢 |
| Compatibilidade | A arte servida **não** substitui o ícone da aba, que continua embutido no documento | O `data URI` é a forma que respeita a rota única e o `W004` | 🟢 |
| Conformidade | Nenhum dado real do operador é versionado ou embutido nesta entrega | `.reversa/principles.md#I`. A arte é marca do projeto, não dado de genealogia | 🟢 |
| Concorrência | n/a — a rota é leitura pura sobre recurso **imutável**; não há escrita, retentativa nem tempo limite a considerar | A única escrita do sistema continua sendo o upload, cuja chave é derivada do conteúdo | 🟢 |
| Observabilidade | n/a — a rota não tem caminho de falha visível e não produz mensagem ao operador | `_reversa_sdd/domain.md#5.1`: as dez mensagens permanecem as mesmas | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: O atalho da tela inicial mostra o logo do projeto
  Dado que a aplicação está no ar
  Quando o sistema móvel busca /apple-touch-icon.png
  Então a resposta tem status 200 e tipo de imagem
  E a imagem tem 180x180 pixels
  E nenhum pixel da imagem é transparente

Cenário: O ícone existe no contêiner, e não só na máquina de desenvolvimento
  Dado que a aplicação foi construída a partir da raiz do projeto
  Quando /apple-touch-icon.png é buscado dentro do contêiner
  Então a resposta tem status 200

Cenário: A tela inicial não muda
  Dado o HTML de GET / antes da entrega
  Quando o HTML de GET / é medido depois da entrega
  Então os dois são idênticos byte a byte
  E o tamanho em bytes é o mesmo

Cenário: Escrita no caminho do ícone é recusada
  Dado que a rota do ícone é de leitura
  Quando uma requisição de escrita é enviada a /apple-touch-icon.png
  Então a resposta recusa o método
  E nenhum arquivo é criado ou alterado no disco

Cenário: O ícone é reaproveitado pelo sistema móvel sem nova busca completa
  Dado que o sistema móvel já buscou /apple-touch-icon.png uma vez
  Quando ele busca o mesmo caminho de novo
  Então a resposta traz marca de versão do conteúdo
  E a marca não muda entre as duas buscas

Cenário: Ausência do ícone não derruba a aplicação
  Dado que a arte do ícone foi removida do projeto
  Quando a tela inicial é aberta
  Então a tela inicial responde 200 e funciona por inteiro
  E /apple-touch-icon.png responde que não encontrou o recurso
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É a entrega: sem a rota, o atalho continua genérico |
| RF-02 | Must | A medida de 180×180 é a esperada pelo sistema móvel; outra medida é reamostrada e perde nitidez |
| RF-03 | Must | Sem opacidade o ícone fica com fundo preto — defeito visível que anula o ganho |
| RF-04 | Must | Fora de `src/` a rota responde `200` no host e `404` no contêiner: falha silenciosa no ambiente que o operador usa |
| RF-05 | Must | `RN-02`. É a garantia de que a entrega é acréscimo, e não alteração |
| RF-08 | Must | `.reversa/principles.md#III` |
| RF-09 | Must | O ícone da aba já custa 19,3 KB por página; somar mais seria regressão de peso |
| RF-06 | Should | Escrita no caminho do ícone é uso anômalo, não fluxo real |
| RF-07 | Should | Sem marca de versão o ícone é rebuscado, mas o atalho funciona |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] **Escopo dos caminhos convencionais.** Servir **apenas** o caminho principal do
  ícone de atalho, ou também o caminho legado do mesmo ícone (usado por sistemas antigos) e o
  caminho do ícone de aba? Cada caminho adicional é uma linha a mais no contrato HTTP, e o
  contrato tem hoje três linhas. Prioridade: escopo.
- 🔴 [DÚVIDA] **Cor do fundo opaco.** O ícone do atalho precisa de fundo sólido, e a arte não
  define qual. Candidatos medidos: **branco**, o **creme do livro** que já existe na arte, ou o
  **cinza da página** (`#f8f9fa`, o mesmo `body` do template). E os cantos: retos, deixando a
  máscara do sistema móvel arredondar, ou já arredondados na arte?
- 🔴 [DÚVIDA] **Fonte canônica da arte.** O mesmo desenho passaria a existir em três lugares: a
  arte em `docs/assets/img/` (que **não** entra no contexto de build), o `data URI` embutido no
  template e o arquivo novo em `src/`. Qual é a fonte da verdade, e como a entrega impede que
  as três derivem entre si? Prioridade: técnico.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-requirements` | reversa |
