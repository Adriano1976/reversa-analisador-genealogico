# Requirements: os recursos visuais da tela vêm da própria aplicação

> Identificador: `054-embutir-bootstrap-e-mermaid`
> Data: `2026-10-31`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Hoje a tela principal e as telas de identidade baixam de um host de terceiros — uma CDN, isto é, uma rede de
entrega de conteúdo — a folha do Bootstrap e, na tela principal, os scripts do Bootstrap, do Mermaid e as duas
famílias de fonte. Sem internet — ou com esse host bloqueado — a tela principal sai sem estilo, as três abas não
alternam e o diagrama não desenha; as telas de entrada saem sem estilo. Esta feature passa a entregar esses
arquivos a partir da própria aplicação, sem nenhuma requisição a origem externa — nem estilo, nem script, nem
fonte —, preservando o comportamento e o desenho de hoje: mesmas abas, mesmos alertas dispensáveis, mesmo tema
claro/escuro, mesmo diagrama com `securityLevel: 'strict'` e mesma tipografia, cores e espaçamentos. Quem usa
ganha um sistema que abre completo numa máquina isolada; quem mantém ganha uma instalação que não depende da
disponibilidade de terceiros.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1. Visão Geral da Arquitetura` | A camada de Apresentação é `src/templates/index.html`, e o contrato da tabela declara: "Bootstrap 5.3.3 e Mermaid 10 por CDN" | 🟢 |
| `_reversa_sdd/architecture.md#6. Mapa de Integrações Externas` | "Nenhuma integração de rede com terceiros. O único tráfego de saída é o download dos assets de CDN feito pelo navegador do usuário" — é esta afirmação que a feature torna falsa | 🟢 |
| `_reversa_sdd/c4-context.md#Legenda dos elementos` | O elemento externo "CDN web" é "Bootstrap 5.3.3 e Mermaid 10, carregados pelo navegador" | 🟢 |
| `_reversa_sdd/c4-containers.md#Inventário de containers` | O Container 2 (navegador) lista "Bootstrap 5.3.3 · Mermaid 10 (CDN)" entre suas tecnologias | 🟢 |
| `_reversa_sdd/adrs/03-mermaid-no-cliente.md` | O diagrama é renderizado **no navegador**, a partir de string gerada pelo servidor, com `securityLevel: 'strict'` | 🟢 |
| `_reversa_sdd/recursos-da-tela/requirements.md#Onde a arte mora, e por que ela é commitada` | `src/static/` é proibida (`W004`), há teste que falha se um arquivo de arte cair numa pasta estática (`BR-E-23`), e os recursos de tela são servidos por rota própria | 🟢 |
| `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#Dívidas declaradas, não fechadas` | `D-06`: o Google Fonts é o **terceiro** host de CDN, com folha bloqueante de renderização, e o fallback declarado é `Georgia`/`system-ui` | 🟢 |
| `.reversa/principles.md#II` | "Comportamento observável é preservado em refatoração": mesmas entradas, mesmas saídas — o desenho e as interações são o comportamento observável desta feature | 🟢 |

> **Bootstrap 5.3.3 e Mermaid 10 não são escolha desta feature.** São fato do legado, já registrados na
> extração. O que se decide aqui é **de onde os arquivos chegam**, não quais são. Os dois nomes próprios
> aparecem no documento porque são o objeto da feature, e não por escolha de tecnologia nova.

Estado medido no código em 2026-10-31:

| Ponto | O que está lá hoje | Confidência |
|-------|--------------------|-------------|
| `src/templates/index.html:96` | Folha do Bootstrap 5.3.3 por CDN, carregada **antes** da folha própria | 🟢 |
| `src/templates/index.html:2011` | Script do Bootstrap 5.3.3 — o pacote consolidado, que já traz o Popper — por CDN, no fim do corpo | 🟢 |
| `src/templates/index.html:128` | Script do Mermaid por CDN, no `<head>`, apontando para a **faixa** `10` (sem versão exata) | 🟢 |
| `src/templates/_entrada_base.html:12` | Folha do Bootstrap 5.3.3 por CDN, herdada por login, cadastro, recuperação, redefinição, definição e mensagem | 🟢 |
| `src/templates/index.html:108-110` | Google Fonts (`Cormorant Garamond` e `Manrope`) mais dois `preconnect` | 🟢 |
| `src/templates/index.html:347-380` | Abas das três fases por `data-bs-toggle="tab"`, dependentes do script do Bootstrap | 🟢 |
| `src/templates/index.html:273` | Alerta dispensável por `data-bs-dismiss="alert"`, dependente do script do Bootstrap | 🟢 |
| `src/templates/index.html:2019-2035` | `mermaid.initialize` com `securityLevel: 'strict'`, `theme: 'base'` e as `themeVariables` da casa | 🟢 |
| `src/web/sessao.py` (`PUBLICOS`) | Lista **fechada** de endpoints públicos, com os quatro de recurso de tela | 🟢 |
| `tests/verificacao_no_conteiner.py:88-92` | A verificação dentro da imagem cobre três rotas de recurso (a dívida `L-33` pede mais) | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Genealogista Genético (única persona do sistema) | Analisar a árvore e o relatório de DNA numa máquina sem saída para a internet | Abre a tela com a rede desligada e vê o mesmo layout, as abas funcionando e o diagrama desenhado |
| Operador que instala e mantém | Rodar o sistema em rede isolada, ou com os hosts de terceiros bloqueados por política | Sobe o contêiner e a tela abre completa, sem depender de disponibilidade de terceiros |
| Auditor de segurança | Saber quais origens a página contata | Abre a tela e não há requisição a origem externa para estilo, script nem fonte |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: a tela principal e as telas de identidade deixam de requisitar estilo, script ou fonte de origem
   externa.** 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#6. Mapa de Integrações Externas` — a frase "o único
     tráfego de saída é o download dos assets de CDN" deixa de valer.
   - Tipo: alterada.
2. **RN-02: os arquivos passam a ser conteúdo do repositório e são entregues pela aplicação, no mesmo regime
   dos recursos de tela que ela já serve.** `src/static/` continua proibida (`W004`); nenhuma pasta estática
   nasce. 🟢
   - Origem no legado: `_reversa_sdd/recursos-da-tela/requirements.md#Onde a arte mora, e por que ela é commitada`.
   - Tipo: nova.
3. **RN-03: as versões não mudam e passam a ser fixas.** Bootstrap 5.3.3 (folha e script) e Mermaid 10. Hoje o
   endereço do Bootstrap já aponta para a versão exata e o do Mermaid aponta para a **faixa** `10`; ao embutir,
   a versão exata do Mermaid é declarada e atualizá-la vira ato deliberado, não efeito de uma nova publicação
   de terceiro. As fontes mantêm as duas famílias e os pesos de hoje — `Cormorant Garamond` em 500, 600 e 700, e
   `Manrope` em 400, 500, 600, 700 e 800 —, sem acrescentar peso nem família. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#1. Visão Geral da Arquitetura` e `src/templates/index.html:128`.
   - Tipo: alterada (modelo de atualização).
4. **RN-04: o comportamento observável é idêntico ao de hoje.** As três abas alternando (inclusive com as setas
   ↑/↓), os alertas dispensáveis fechando, o tema claro/escuro, o diagrama renderizado no cliente com
   `securityLevel: 'strict'` e o layout, a tipografia e as cores atuais. 🟢
   - Origem no legado: `.reversa/principles.md#II` e `_reversa_sdd/adrs/03-mermaid-no-cliente.md`.
   - Tipo: nova (é critério de aceite, não mudança de comportamento).
5. **RN-05: sem rede, a tela sai estilizada e o diagrama desenha.** A degradação de hoje — página sem estilo,
   abas inertes, diagrama ausente — deixa de existir. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#6. Mapa de Integrações Externas`.
   - Tipo: alterada.
6. **RN-06: os recursos são públicos.** São servidos a quem ainda não tem sessão, como os recursos de arte
   (`P-08`), porque a tela de entrada depende deles; a lista de endpoints públicos é **fechada** e cresce
   nomeando cada endpoint novo. 🟢
   - Origem no legado: `_reversa_sdd/addenda/053-conta-com-senha-e-recuperacao.md` e `src/web/sessao.py`.
   - Tipo: alterada.
7. **RN-07: cada arquivo embutido mantém o cabeçalho de licença, e a procedência é declarada.** Versão,
   endereço de origem, `sha256` e licença de cada arquivo embutido — as três bibliotecas e os arquivos de fonte —
   ficam registrados no adendo da feature. 🟡
   - Origem no legado: regime de proveniência dos recursos de tela (`_reversa_sdd/adrs/29-arte-derivada-com-receita-unica.md`).
   - Tipo: nova.
8. **RN-08: o controle de diff visual é exercido, não contornado.** `SHA_DA_TELA` muda por esta feature, com o
   delta e a razão declarados no adendo; o invariante não é removido, afrouxado nem trocado por comparação mais
   frouxa. Nenhum texto, classe ou elemento visual da tela muda além do que a troca das tags do `<head>`
   provoca. As telas de identidade não são cobertas por `SHA_DA_TELA`: nelas o controle é o conjunto de testes de
   contrato que já existe mais a conferência humana registrada em `evidence/`. 🟢
   - Origem no legado: `tests/test_icone_de_atalho.py` (bloco acima de `SHA_DA_TELA`) e as regras `RF-05`/`RN-02`
   da feature 009.
   - Tipo: nova.
9. **RN-09: nenhuma dependência de runtime nova.** Os arquivos embutidos são ativo de front-end; `requirements.txt`
   não muda. 🟢
   - Origem no legado: o mesmo critério que mantém a biblioteca de imagem fora de `requirements.txt`
   (`_reversa_sdd/recursos-da-tela/requirements.md`).
   - Tipo: nova.
10. **RN-10: a decisão de renderizar o diagrama no cliente continua vigente.** Muda só a procedência do
    arquivo; nada migra para o servidor. 🟢
    - Origem no legado: `_reversa_sdd/adrs/03-mermaid-no-cliente.md`.
    - Tipo: nova.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A tela principal não referencia nenhum host externo | Must | Nenhuma tag `link` (folha, fonte ou `preconnect`) nem `script` do HTML de `GET /` aponta para URL absoluta de origem externa | 🟢 |
| RF-02 | As telas de identidade também deixam de requisitar host externo | Must | O HTML de `/login`, `/cadastro`, `/recuperar-senha`, `/redefinir-senha`, `/definir-senha` e da página de mensagem não contém `cdn.jsdelivr.net` em `link` de folha, e a tipografia delas continua exatamente a de hoje | 🟢 |
| RF-03 | A folha do Bootstrap é entregue pela própria aplicação | Must | Responde 200, com tipo de mídia de folha de estilo; o corpo é byte a byte o arquivo oficial 5.3.3, com `sha256` declarado no adendo | 🟢 |
| RF-04 | O script do Bootstrap (bundle) é entregue pela própria aplicação | Must | Responde 200, com tipo de mídia de script (nunca `text/html`); corpo byte a byte o oficial 5.3.3, com `sha256` declarado | 🟢 |
| RF-05 | O script do Mermaid é entregue pela própria aplicação | Must | Responde 200, com tipo de mídia de script; corpo byte a byte a versão exata declarada, com `sha256` declarado | 🟢 |
| RF-06 | Com a estação sem rede, a tela principal mantém o desenho | Must | Conferência humana com a rede desligada, registrada em `evidence/`: mesma composição, mesmas cores, mesma tipografia e mesmos espaçamentos do estado atual | 🟢 |
| RF-07 | As abas das três fases continuam alternando e os alertas continuam fechando | Must | Clique em cada aba troca o painel e atualiza `aria-selected`; as setas ↑/↓ percorrem a barra lateral; o botão de fechar remove o alerta | 🟢 |
| RF-08 | O diagrama mantém a configuração de hoje | Must | `securityLevel: 'strict'`, `theme: 'base'`, as mesmas `themeVariables`, `startOnLoad: false` e a renderização sob demanda permanecem inalteradas no documento | 🟢 |
| RF-09 | Os recursos novos são públicos | Must | Sem sessão, cada um responde 200, e não redirecionamento para a entrada | 🟢 |
| RF-10 | Os recursos novos existem dentro da imagem do contêiner | Must | A verificação executada dentro do contêiner reporta cada um como `OK`, com o `sha256` do arquivo na imagem | 🟢 |
| RF-11 | Os recursos novos recebem os cabeçalhos de borda | Must | Cada um responde com `X-Frame-Options: DENY`, como `/`, `/app.css` e as artes | 🟢 |
| RF-12 | A ordem de carregamento é preservada | Must | No documento servido, a folha do Bootstrap é referenciada **antes** da folha própria | 🟢 |
| RF-13 | O controle de diff visual registra a mudança | Must | `SHA_DA_TELA` tem valor novo, e o adendo declara o delta em bytes e a razão; os textos e as classes da tela são os mesmos de antes | 🟢 |
| RF-14 | A fonte própria é entregue pela aplicação | Must | As duas famílias e os pesos de hoje são servidos pela aplicação; o documento as referencia apenas onde já referencia hoje, e nenhuma tag de fonte aponta para fora | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Disponibilidade | A tela continua respondendo 200 mesmo se um dos arquivos embutidos faltar no disco; o recurso ausente responde 404 e nada mais muda | É o regime das artes e da folha atual (arquivo ausente vira 404, sem `500`) | 🟢 |
| Desempenho | A soma de todos os arquivos embutidos — as três bibliotecas e os arquivos de fonte — não passa de **4 MB**; o peso de cada um e o total por página são medidos e registrados no adendo | O maior deles é o script do diagrama; sem número medido não há como vigiar o crescimento | 🟡 |
| Desempenho | A segunda carga da tela não rebaixa os arquivos inteiros quando eles não mudaram | O navegador hoje os guarda em cache; trocar a origem não pode virar download repetido | 🟡 |
| Segurança | Nenhuma origem externa nova, nenhum script inline novo; a política de segurança de conteúdo continua adiada (`BUG-20261013-4PYJ`) e não é desta feature | `_reversa_sdd/addenda/bug-BUG-20261013-X7EN-v001.md` | 🟢 |
| Compatibilidade | Os mesmos navegadores de hoje; sem JavaScript, o comportamento é o atual (o diagrama não desenha, as abas não alternam) e nada regride | `_reversa_sdd/adrs/03-mermaid-no-cliente.md` | 🟢 |
| Concorrência | Os arquivos embutidos são somente leitura e servidos a cada requisição, como a folha atual; nenhuma trava e nenhum estado de processo novo | regime atual de `GET /app.css` | 🟢 |
| Empacotamento | Os arquivos entram na imagem pela lista de permissão vigente, e a verificação dentro do contêiner passa a cobri-los | `.dockerignore` e `tests/verificacao_no_conteiner.py` (`L-33`) | 🟢 |
| Manutenibilidade | Atualizar uma biblioteca é substituir o arquivo e declarar o novo `sha256` no adendo; nada muda em `requirements.txt` | `RN-03`, `RN-07` e `RN-09` | 🟢 |
| Privacidade | A tela deixa de contatar um host de terceiro, reduzindo a exposição do operador | `_reversa_sdd/addenda/013-revisao-de-design-da-tela.md#Dívidas declaradas, não fechadas` (`D-06`) | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: tela principal sem rede (RF-06, RF-07)
  Dado que a estação está sem saída para a internet
  Quando o operador abre a tela principal
  Então a página apresenta o layout e as cores de hoje
  E as três abas alternam ao clique
  E as setas ↑/↓ percorrem a barra lateral
  E o diagrama do resultado é desenhado

Cenário: nenhuma referência a host externo (RF-01)
  Dado o HTML servido por GET /
  Quando se procuram endereços de origem externa em link de folha, link de fonte, preconnect e script
  Então não há nenhum endereço para fora

Cenário: os três recursos são entregues pela aplicação (RF-03, RF-04, RF-05)
  Dado a aplicação em execução
  Quando o navegador pede a folha e os dois scripts
  Então cada um responde 200, com o tipo de mídia próprio
  E o corpo é byte a byte o arquivo oficial da versão declarada

Cenário: configuração do diagrama preservada (RF-08)
  Dado o documento da tela principal
  Quando se comparam as opções de inicialização do diagrama com as de antes
  Então o nível de segurança, o tema, as variáveis de tema e o início automático são os mesmos

Cenário: tela de identidade sem rede (RF-02)
  Dado que a estação está sem saída para a internet
  Quando o operador abre a tela de entrada
  Então o cartão, o banner, os campos e o botão mantêm o desenho de hoje
  E a tipografia continua a de hoje, sem webfont

Cenário: recurso ausente não derruba a tela (RNF de disponibilidade)
  Dado que um dos arquivos embutidos não existe no disco
  Quando o operador abre a tela principal
  Então o recurso responde 404
  E a tela continua respondendo 200

Cenário: cliente sem sessão recebe os recursos (RF-09)
  Dado um cliente sem sessão
  Quando ele pede a folha do Bootstrap
  Então recebe 200, e não um redirecionamento para a entrada

Cenário: os recursos existem dentro da imagem (RF-10)
  Dado o contêiner construído pela lista de permissão vigente
  Quando a verificação roda dentro dele
  Então os recursos embutidos respondem 200 com o conteúdo esperado

Cenário: os recursos novos recebem os cabeçalhos de borda (RF-11)
  Dado um cliente qualquer
  Quando pede qualquer um dos recursos embutidos
  Então a resposta traz o controle de enquadramento, como a tela e as artes

Cenário: ordem das folhas preservada (RF-12)
  Dado o documento da tela principal
  Quando se lê a ordem das folhas
  Então a folha do Bootstrap aparece antes da folha própria

Cenário: mudança de tela declarada (RF-13)
  Dado o invariante SHA_DA_TELA
  Quando a feature termina
  Então o valor é diferente do anterior
  E o adendo declara o delta em bytes e a razão
  E nenhum texto, classe ou elemento visual da tela mudou

Cenário: a fonte própria é servida pela aplicação (RF-14)
  Dado o documento da tela principal
  Quando se procura a referência de fonte dele
  Então ela aponta para a própria aplicação
  E os pesos usados na tela são os mesmos de hoje

Cenário: a pasta estática continua proibida (negativo, RN-02)
  Dado o projeto depois da entrega
  Quando se procura uma pasta estática de recursos de tela
  Então ela continua ausente
  E o teste que a proíbe continua passando

Cenário: versão embutida é fixa (RN-03)
  Dado o script do diagrama embutido numa versão exata
  Quando alguém substitui o arquivo por outra versão
  Então o sha256 declarado no adendo muda no mesmo commit
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o objetivo da feature: sair da CDN |
| RF-03, RF-04, RF-05 | Must | Sem as três bibliotecas servidas, nada muda |
| RF-06 | Must | Sem o mesmo desenho, a feature trocou um defeito por outro |
| RF-07 | Must | As abas e os alertas dependem do script do Bootstrap; perdê-los é regressão |
| RF-08 | Must | `securityLevel: 'strict'` é decisão de segurança vigente desde a feature 001 |
| RF-09 | Must | Sem isso, a tela de entrada quebra para quem não tem sessão |
| RF-10 | Must | A imagem do contêiner é a forma de uso real (`L-33`) |
| RF-11 | Must | O cabeçalho de enquadramento é a correção do `BUG-20261013-X7EN` |
| RF-12 | Must | A folha própria redefine `--bs-*` e precisa vencer |
| RF-13 | Must | É o controle de diff visual do projeto |
| RF-14 | Must | Sem a fonte embutida, a tipografia muda quando não há rede |
| RF-02 | Must | Sem a folha, as telas de entrada quebram quando não há rede |
| RNF de desempenho | Should | Precisa ser medido, não estimado |

## 9. Esclarecimentos

### Sessão 2026-10-31

- **Q:** A fonte da tela — `Cormorant Garamond` e `Manrope`, hoje carregadas do Google Fonts — entra nesta
  feature?
  **R:** Sim, embutir as fontes também. Decisão da lacuna `L-01`: a tipografia passa a ser servida pela própria
  aplicação, com as duas famílias e os pesos de hoje. Consequências: `RF-14` passa a exigir a fonte servida pela
  aplicação; `RF-01` passa a valer para folha, fonte e script; e o terceiro host de CDN deixa de existir.
- **Q:** As telas de identidade (login, cadastro, recuperação, redefinição, definição e mensagem) entram nesta
  entrega?
  **R:** Sim, as seis telas entram. Decisão da lacuna `L-02`: `RF-02` sobe de `Should` para `Must`. Como essas
  telas **não** carregam a webfont hoje, a entrega não lhes acrescenta tipografia nova: a referência de fonte
  continua restrita ao documento que a tem hoje, e a tipografia das telas de identidade permanece a atual
  (`Georgia` e `system-ui`). O controle de diff visual delas é o conjunto de testes de contrato mais a
  conferência humana registrada em `evidence/`.
- **Q:** O pedido diz "colocar em `static/`", mas `src/static/` é proibida pelo `W004`, com teste que falha. O
  que vale?
  **R:** O regime vigente — arquivo no repositório, entregue por rota própria, como a folha de estilo atual.
  Decisão da lacuna `L-03`: o `W004` **não** é revogado, nenhuma pasta estática nasce, e o teste que proíbe a
  pasta estática continua passando. O local exato e os nomes das rotas ficam para o plano.

## 10. Lacunas

Nenhuma lacuna aberta. As três dúvidas da versão inicial foram resolvidas na sessão de esclarecimentos de
2026-10-31.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-31 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-31 | `/reversa-clarify`: fonte embutida (`L-01`), telas de identidade no escopo (`L-02`) e destino no regime vigente, com o `W004` mantido (`L-03`) — 3 dúvidas resolvidas | reversa |
