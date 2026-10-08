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
4. **RN-04 — O ícone do atalho é opaco, com fundo branco e cantos retos.** O arquivo servido não
   tem transparência: a área inteira é preenchida com branco sólido `#ffffff`, e os cantos
   ficam **retos**, porque o sistema móvel aplica a própria máscara arredondada — arredondar na
   arte produziria arredondamento duplo e um anel de fundo no canto. O branco foi escolhido por
   contraste: a arte tem **51,5 % de creme em duas tonalidades** (`#f5efca` e `#f9eab0`), e
   eleger uma delas faria a outra página parecer errada. O PNG transparente permanece válido — e
   intocado — para o ícone da aba. 🟢
   - Origem no legado: medido — 32,5 % de pixels transparentes e cantos `(0, 0, 0, 0)` em
     `docs/assets/img/logo.png`; cores dominantes medidas no mesmo arquivo.
   - Tipo: nova. **Decidido pelo operador em 2026-10-08** (§9, `Q-02`).
5. **RN-05 — A arte servida mora dentro de `src/`, e é cópia de uma fonte declarada.** O
   contexto de build só admite `requirements.txt` e `src/**`; qualquer outro caminho produz uma
   rota que responde `200` na máquina de desenvolvimento e `404` no contêiner. A **fonte
   canônica continua sendo `docs/assets/img/logo.png`**, e ela **não sai de lá**: o mini-site
   publicado consome esse mesmo arquivo, e as duas cópias servem a dois alvos de publicação
   distintos. O que a entrega acrescenta é a **detecção de deriva** entre as duas. 🟢
   - Origem no legado: `.dockerignore` na raiz (lista de permissão);
     `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#Impacto por artefato da extração`.
   - Tipo: nova. **Decidido pelo operador em 2026-10-08** (§9, `Q-03`).
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
9. **RN-09 — Só o caminho principal é servido; nenhum caminho sem consumidor.** A entrega
   responde a `/apple-touch-icon.png` e a mais nada. O alias legado
   `/apple-touch-icon-precomposed.png` pertence a sistemas anteriores e nenhum atual o
   requisita; `/favicon.ico` só é buscado quando o documento **não** declara ícone, e o
   `src/templates/index.html:8` declara. Acrescentar qualquer um dos dois repetiria a dívida
   **#17**, que este projeto já fechou: *"superfícies de compatibilidade reexportando nomes
   históricos que ninguém usa"*. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#7` (dívida #17, fechada);
     `src/templates/index.html:8` (o ícone é declarado no documento).
   - Tipo: nova (restrição de escopo). **Decidido pelo operador em 2026-10-08** (§9, `Q-01`).

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A aplicação responde a `/apple-touch-icon.png`, com status `200` e tipo de imagem declarado | Must | Requisição de leitura a `/apple-touch-icon.png` devolve `200` e `Content-Type` de imagem; medido por requisição real, não por leitura de código | 🟢 |
| RF-02 | O ícone servido tem **180×180** pixels | Must | O corpo da resposta decodifica em imagem de 180×180; dimensão medida no binário | 🟢 |
| RF-03 | O ícone servido é **opaco**, com fundo branco `#ffffff` e cantos retos | Must | Varredura do canal alfa do arquivo servido: nenhum pixel com alfa menor que 255; leitura dos quatro cantos confirma `#ffffff` | 🟢 |
| RF-04 | A arte servida está sob `src/` | Must | O arquivo existe dentro de `src/` e a rota responde `200` **a partir do contêiner**, não apenas no host | 🟢 |
| RF-05 | `GET /` devolve exatamente a mesma resposta de antes da feature | Must | Comparação byte a byte da resposta de `GET /` antes e depois; zero diferença | 🟢 |
| RF-06 | A rota aceita apenas leitura, e recusa qualquer outro método | Should | Requisição de escrita ao caminho do ícone recebe recusa de método, e nenhuma escrita acontece no disco | 🟡 |
| RF-07 | A resposta do ícone traz marca de versão por conteúdo, **sem** validade longa declarada | Should | Requisição repetida devolve resposta de "não modificado", sem corpo; e nenhuma resposta declara validade de cache superior a um dia | 🟡 |
| RF-08 | Existe teste automatizado que **falha antes** da mudança e passa depois | Must | O teste novo, executado contra o commit anterior, falha; contra a entrega, passa. `.reversa/principles.md#III` | 🟢 |
| RF-09 | A entrega **não** acrescenta bytes ao HTML de `GET /` | Must | A resposta de `GET /` mantém o mesmo tamanho em bytes de antes da feature | 🟢 |
| RF-10 | Existe teste que falha quando a arte de runtime diverge da arte canônica, comparando **pixel a pixel** | Must | Alterar um pixel de uma das cópias faz o teste falhar; reencodar o mesmo desenho com outra compressão **não** faz. Medido: o mesmo desenho existe com 32.317 e com 44.069 bytes e diferença de pixel **zero** — a comparação por bytes daria alarme falso | 🟢 |
| RF-11 | Os caminhos **não** servidos continuam recusando | Must | `/apple-touch-icon-precomposed.png` e `/favicon.ico` continuam respondendo que o recurso não foi encontrado, exatamente como respondem hoje | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | O ícone é servido **sem** recompô-lo nem lê-lo do disco a cada requisição; nenhuma rota existente fica mais lenta | O ícone da aba já custa 19,3 KB por página; a rota nova não pode somar a esse custo | 🟡 |
| Desempenho | A resposta do ícone é inferior a **50 ms** no host | Mesma ordem de grandeza das demais respostas locais do sistema | 🟡 |
| Segurança | A rota não interpola entrada do cliente em caminho de arquivo | É a mesma classe de falha do `BUG-20260929-QMLY`: nome controlado pelo cliente usado para montar caminho. A rota nova **não tem** entrada, e o requisito existe para que continue assim | 🟢 |
| Segurança | A rota não expõe listagem nem qualquer outro arquivo do projeto | Sem entrada, não há como endereçar outro recurso | 🟢 |
| Compatibilidade | O ícone é opaco, com fundo branco e cantos retos, porque o sistema móvel compõe transparência sobre preto e aplica a própria máscara de canto | Medido: `docs/assets/img/logo.png` tem 32,5 % de pixels transparentes e cantos `(0, 0, 0, 0)`; e 51,5 % de creme em duas tonalidades | 🟢 |
| Compatibilidade | A arte servida **não** substitui o ícone da aba, que continua embutido no documento | O `data URI` é a forma que respeita a rota única e o `W004` | 🟢 |
| Operação | A troca da arte tem de ser vista **sem** esperar expiração de cache | A arte foi trocada **duas vezes em 2026-10-08**; validade longa congelaria o cliente de quem já buscou. Decidido em §9, `Q-04` | 🟢 |
| Manutenibilidade | A mesma arte existe em dois lugares, e a divergência entre eles é **detectada por teste** | Medido: o desenho existe com 32.317 e com 44.069 bytes e diferença de pixel **zero** — comparar bytes daria alarme falso | 🟢 |
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

Cenário: O ícone é revalidado, e não congelado por validade longa
  Dado que o cliente já buscou /apple-touch-icon.png uma vez
  Quando ele busca o mesmo caminho de novo
  Então a resposta informa que o conteúdo não mudou e não traz corpo
  E nenhuma resposta declara validade de cache superior a um dia

Cenário: Caminhos que ninguém requisita continuam sem resposta
  Dado que a aplicação está no ar
  Quando /apple-touch-icon-precomposed.png é buscado
  Então a resposta informa que o recurso não foi encontrado
  Quando /favicon.ico é buscado
  Então a resposta informa que o recurso não foi encontrado

Cenário: A arte de runtime divergindo da canônica é detectada
  Dado que a arte canônica e a cópia de runtime estão idênticas em pixel
  Quando um único pixel da cópia de runtime é alterado
  Então o teste de deriva falha
  E reencodar o mesmo desenho com outra compressão não faz o teste falhar

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
| RF-03 | Must | Fundo transparente vira fundo preto no atalho, e canto arredondado na arte vira arredondamento duplo — dois defeitos visíveis que anulariam o ganho |
| RF-04 | Must | Fora de `src/` a rota responde `200` no host e `404` no contêiner: falha silenciosa no ambiente que o operador usa |
| RF-05 | Must | `RN-02`. É a garantia de que a entrega é acréscimo, e não alteração |
| RF-08 | Must | `.reversa/principles.md#III` |
| RF-09 | Must | O ícone da aba já custa 19,3 KB por página; somar mais seria regressão de peso |
| RF-10 | Must | Sem detecção de deriva, a cópia de runtime envelhece em silêncio e o atalho passa a mostrar uma arte que não é mais a do projeto |
| RF-11 | Must | `RN-09`. É o que impede a entrega de criar caminho sem consumidor |
| RF-06 | Should | Escrita no caminho do ícone é uso anômalo, não fluxo real |
| RF-07 | Should | O atalho funciona sem marca de versão; o que se perde é a revalidação barata |

## 9. Esclarecimentos

### Sessão 2026-10-08

Quatro perguntas dirigidas, todas respondidas. Cada resposta foi integrada **in-place** no
ponto do documento onde a dúvida vivia; o mapa pergunta → mudança está em cada item.

- **Q-01 (escopo funcional) — qual o escopo de caminhos que a feature serve?**
  **R:** ✅ **Só o caminho principal.** Apenas `/apple-touch-icon.png`. O alias legado
  `/apple-touch-icon-precomposed.png` e o `/favicon.ico` continuam **sem resposta**: nenhum dos
  dois tem consumidor — o alias pertence a sistemas anteriores, e o `favicon.ico` só é buscado
  quando o documento **não** declara ícone, e o `src/templates/index.html:8` declara. Criá-los
  repetiria a dívida **#17**, que o projeto já fechou.
  *Aplicado em:* `RN-09` (nova), `RF-11` (novo), cenário Gherkin novo, MoSCoW. Marca de dúvida
  removida.
- **Q-02 (experiência) — qual a cor do fundo opaco do ícone, e os cantos?**
  **R:** ✅ **Branco `#ffffff`, cantos retos.** Os cantos ficam retos porque o sistema móvel
  aplica a própria máscara arredondada — arredondar na arte produziria arredondamento duplo e
  um anel de fundo no canto. O branco foi escolhido por contraste: a arte tem 51,5 % de creme em
  **duas** tonalidades (`#f5efca` e `#f9eab0`), e eleger uma delas faria a outra página parecer
  errada.
  *Aplicado em:* `RN-04` (detalhada), `RF-03` (critério com leitura dos quatro cantos), MoSCoW,
  RNF de Compatibilidade. Marca de dúvida removida.
- **Q-03 (compatibilidade com o legado) — qual passa a ser a fonte canônica da arte?**
  **R:** ✅ **`docs/assets/img/logo.png` continua a fonte, e não sai de lá.** O mini-site
  publicado consome o mesmo arquivo, então as duas cópias servem a dois alvos de publicação
  distintos — e isso é legítimo. O que a entrega acrescenta é uma cópia de runtime sob `src/` e
  a **detecção de deriva** entre as duas. O teste compara **pixel a pixel**, nunca bytes:
  medido, o mesmo desenho existe com 32.317 e com 44.069 bytes e diferença de pixel **zero**,
  então uma comparação por `sha256` daria alarme falso na primeira recompressão.
  *Aplicado em:* `RN-05` (detalhada), `RF-10` (novo), cenário Gherkin novo, RNF de
  Manutenibilidade. Marca de dúvida removida.
- **Q-04 (atributos não funcionais) — que política de cache o ícone deve ter?**
  **R:** ✅ **Marca de versão por conteúdo, sem validade longa declarada.** O `ETag` responde
  `304` sem corpo na rebusca, e nenhuma validade superior a um dia é declarada. Razão: a arte
  foi trocada **duas vezes em 2026-10-08**, e uma validade de um ano congelaria o cliente que já
  tivesse buscado — o `ETag` não salva, porque só age depois de a validade expirar. Sendo a
  aplicação local e monousuário, a revalidação é barata.
  *Aplicado em:* `RF-07` (critério reescrito), cenário Gherkin reescrito, RNF de Operação,
  MoSCoW. Marca de dúvida removida.

> **Nota de escopo declarada, e não escondida.** As quatro respostas fecham as três lacunas do
> documento inicial e ainda abriram trabalho novo: `RN-09`, `RF-10` e `RF-11` não existiam antes
> desta sessão. Uma quinta questão foi levantada durante a recomendação técnica e **não** entrou
> nesta feature: o ícone da aba, embutido no documento, responde por **19.298 dos 23.906 bytes
> da página** — 81 % da resposta. Está registrada em §12, com a razão de ter ficado de fora.

## 10. Lacunas

n/a — nenhuma lacuna em aberto. As três lacunas do documento inicial foram resolvidas na sessão
de esclarecimento de 2026-10-08 (§9).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-08 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-08 | Sessão de esclarecimento: `Q-01` a `Q-04` resolvidas; `RN-04`, `RN-05` e `RN-09` detalhadas; `RF-10` e `RF-11` acrescentados; três lacunas fechadas | reversa |

## 12. Fora de escopo

**Registrado aqui para não se perder, decidido fora desta feature.**

O ícone da aba é entregue como `data URI` embutido em `src/templates/index.html:8` e responde
por **19.298 dos 23.906 bytes** de cada resposta de `GET /` — **81 % da página**. Medido nesta
sessão, com a página servida na `5080`.

Não entra nesta feature por três razões: contraria a `RN-02` (o `GET /` deixaria de ser byte a
byte idêntico), mexeria no template vigiado pelo `W005`, e o projeto trata cada onda como
entregável fechado (`_reversa_sdd/migration/risk_register.md#RISK-008`).

Candidato a feature própria, se o operador quiser: servir o ícone da aba por um caminho
dedicado, o que também respeitaria o `W004`. A decisão registrada em §9, `Q-01` (opção 1-d),
foi **não** fazer agora.
