# Adendo: revisão de design da tela

> Identificador: `013-revisao-de-design-da-tela`
> Data: `2026-10-11`
> Cenário: **legado** (âncora em `_reversa_sdd/recursos-da-tela/` e `_reversa_sdd/design-system/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não** saiu
> daquele pipeline — o conteúdo é fiel ao entregue, o formato pode divergir do que ele gera.

## Vigência

Vigente desde 2026-10-11.

**Emenda a `RN-23` e a `RN-24` do adendo `011-escolher-arquivo-da-lista.md`.** As duas continuam
vigentes no espírito; o que muda está declarado em "Regras alteradas", e não substituído em silêncio.

## Resumo da entrega

O operador pediu que as sugestões de design que ele enviou fossem aplicadas, com uma condição: os
elementos de `src/assets/` — a arte do topo e o ícone de atalho — continuam sendo **os mesmos
arquivos**.

A entrega tem seis frentes:

1. **A folha de estilo deixou de ser `<style>` embutido** no template e passou a ser
   `src/assets/app.css`, servida por **`GET /app.css`** — rota nova, no mesmo desenho das duas rotas
   de arte (`GET` sozinho com `405` na escrita, `ETag` com `304` sem corpo, e `404` sem corpo quando
   o arquivo falta, sem nada mais mudar). `src/static/` **continua ausente e proibida** (`W004`, da
   feature 003) e nenhum diretório estático foi configurado (`RN-07` da 009). O arquivo entra na
   imagem por `!src/**` + `COPY src/ /app/src/`, como as duas artes.
2. **Controle de tema.** Botão fixo no canto superior direito, com **claro como padrão** e a escolha
   lembrada em `localStorage`. Antes o tema vinha de `matchMedia('(prefers-color-scheme: dark)')`:
   quem tinha o Windows no escuro abria a aplicação no escuro **sem ter pedido**.
3. **Masthead emendado.** O `<h1>` passou a ser escondido **apenas quando a arte do topo responde**
   (ver "Regras alteradas").
4. **Estado de resultado.** Índice de matches com âncoras no topo, selo da confrontação no cabeçalho
   de cada cartão, e a evidência genética em grade (`dl.kit-grid`) com as Posições atrás de
   `<details>`. Os oito rótulos do kit são os mesmos da tabela de nove linhas que a grade substituiu.
5. **Acessibilidade.** Texto `visually-hidden` ao lado do ✓ e do ⚠ (cor e `title` não chegam a leitor
   de tela), `aria-controls`/`aria-selected` nas abas, e o par `--on-danger` que conserta o hover do
   "Apagar" no tema escuro — que dava **2,18:1** com o `#fff` fixo que ali estava.
6. **Um defeito medido, corrigido.** O botão "Apagar" abre um `confirm()`; CANCELAR ligava o
   indicador e escondia a área de resultados, porque o ouvinte de `submit` rodava de qualquer forma.
   A tela travava em "Analisando..." até a pessoa recarregar. A guarda `if (e.defaultPrevented)
   return;` fecha isso.

**Suíte: `561 passed, 9 skipped` → `586 passed, 9 skipped`.** Os 25 itens novos são os dois arquivos
de teste desta entrega: `tests/test_estado_do_resultado.py`, que **não existia**, e os acréscimos em
`tests/test_estilo_da_tela.py`. Nenhum teste foi removido ou desabilitado.

**Paridade diferencial em 100 %** pelo invólucro, com o `harness.py` byte a byte idêntico. O golden
`SCR-001-initial-upload.html.txt` continua `ec07f71b4084269a…`.

**Nenhum rótulo congelado, nome de campo ou valor de `action` mudou.** Conferido por diff dos nós de
texto do template: as únicas adições são "Disponível", "Indisponível:", o botão de tema, os quatro
cabeçalhos do índice, o selo do cabeçalho do cartão e os rótulos do kit. Zero literais alterados ou
removidos.

**A superfície HTTP passa de 3 para 4 rotas.** As três existentes ficam intocadas.

## Regras alteradas

| Regra | Onde | Antes | Agora | Por quê |
|-------|------|-------|-------|---------|
| `RN-23` (título) | 011, tabela de regras | "o titulo volta a ser **texto visivel**" | o título é texto no documento, e **visível apenas quando a arte do topo não responde** | a arte do topo traz "Analisador Genealógico" **desenhado**; com os dois visíveis o produto se nomeia duas vezes, uma logo abaixo da outra. A condição vem do **servidor** (`arte_do_topo_disponivel`), porque o CSS não sabe se uma imagem carregou e o JS só descobriria depois da primeira pintura |
| `RN-23` (largura da arte) | 011, tabela de regras | "arte reduzida a **metade** da largura (`w-50`)" | `w-50` **com teto de 320 px** | 50 % de um `col-lg-10` é ~520 px, e o formulário ficava abaixo da dobra. **Emenda declarada, e não presa por teste** — ver "Dívidas" |
| `RN-23` (tipografia) | 011, tabela de regras; `DEV-008` | o legado não define família tipográfica | `Newsreader` (títulos) e `IBM Plex Sans` (corpo), com `Georgia` e `system-ui` atrás | identidade do design system novo |
| `RN-24` | 011, tabela de regras | texto de apresentação centralizado em `col-lg-9` | **inalterada** | o refresh não a tocou; ela segue valendo e tem teste |

**A emenda do título não afrouxa a `RN-23` — ela a cumpre.** A regra existe para o operador nunca
ficar sem título; o `visually-hidden` existe para não repetir o que a arte já desenha. As duas só
conflitavam porque o template não sabia se a arte ia responder. Agora sabe.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/openapi/index.yaml` | rotas | delta-de-contrato-externo | **3 → 4 rotas**: entra `GET /app.css`, com `200 text/css`, `405` na escrita e `404` sem corpo quando o arquivo falta |
| `_reversa_sdd/recursos-da-tela/contracts.md` | §4 superfície | delta-de-contrato-externo | A folha deixou de ser `<style>` embutido no documento e passou a ser arquivo servido por rota; `src/static/` continua ausente |
| `_reversa_sdd/recursos-da-tela/requirements.md` | `RF-23`, `BR-E-23` | **sem-impacto** | A proibição de pasta estática continua verdadeira e continua presa por teste |
| `_reversa_sdd/design-system/tokens-derived.md` | tokens | regra-alterada | Descrevia o `<style>` em `index.html:9-24` e os literais `#f8f9fa` / `#dee2e6` / `#fafafa`. As linhas **não existem mais**; os tokens agora vivem em `src/assets/app.css`, em variáveis CSS com bloco de tema escuro |
| `_reversa_sdd/migration/screen_deviation_log.md` | `DEV-008` | regra-alterada | Afirmava que o legado **não define família tipográfica**. Passou a definir, e por webfont |
| `_reversa_sdd/traceability/code-spec-matrix.md` | cobertura de `src/` | delta-de-dados | Entram `src/assets/app.css` (novo) e uma rota; a contagem de arquivos de `src/` sobe |
| `_reversa_forward/004-servidor-waitress/regression-watch.md` | `W003` | delta-de-contrato-externo | O item já registrava 3 rotas contra 1 do legado; agora são **4**. Sem essa nota, a próxima re-extração relata 🔴 sobre código correto |
| `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md` | `W004` | **sem-impacto** | `src/static/` continua ausente; a folha mora em `src/assets/` |
| `README.md` (fora da extração, citado por completude) | "A tela de entrada", "Estrutura do Projeto" | delta-de-contrato-externo | A árvore de `src/` não menciona `src/assets/app.css`; a seção da tela não descreve o controle de tema nem o índice de resultados |
| `tests/test_banner_do_topo.py` | `RN-23` | regra-alterada | Dois testes nomeavam "título visível" e passavam por **vacuidade** — o regex `>([^<]+)<` continua encontrando o texto que a folha esconde. Um foi renomeado para declarar o que mede, e o teste da arte ausente passou a prender o **efeito** |
| `tests/test_icone_de_atalho.py` | `SHA_DA_TELA` | delta-de-contrato-externo | `17240e5a…` (27.502 bytes) → `f2b2233e…` (28.858). O valor intermediário `1066e272…` foi medido na sessão e **nunca existiu em commit** |

## Dívidas declaradas, não fechadas

Registradas aqui porque foram **medidas** nesta entrega e a decisão foi consciente de não fechá-las.

| # | O que é | Gravidade | Por que ficou aberta |
|---|---------|-----------|----------------------|
| D-01 | O ⚠ de "Indisponível" é `#ffc107` sobre branco = **1,63:1** | 🟡 | Reprovado em WCAG 1.4.3/1.4.11, mas o acervo real do operador tem **12 itens e zero indisponíveis** (medido): o defeito não alcança ninguém hoje. O motivo continua legível ao lado, em texto |
| D-02 | `formatar_cm` **não** trata `None` (levanta `TypeError` por decisão, `number_format.py:32-33`), enquanto `formatar_inteiro` devolve `—`; o domínio modela `total_cm = None` como estado legítimo | 🟡 | Quatro pontos do template aplicam `cm_br` sem guarda e três usam `is not none`, que é **verdadeiro para chave ausente**. Nenhum produtor de produção alcança os casos — é um `500` de página inteira a uma linha de distância, não um defeito vivo |
| D-03 | Os quatro `role="tabpanel"` não têm `aria-labelledby`; o `role="tablist"` não tem nome acessível | 🟢 | O par ARIA ficou pela metade: `aria-controls` e `aria-selected` entraram, o rótulo do painel não |
| D-04 | **A folha de estilo não tem guarda de deriva** | 🟡 | Enquanto o CSS era `<style>` embutido, ele estava dentro do artefato coberto por `SHA_DA_TELA`. Agora a única proteção são 12 nomes de classe procurados como substring. Apagar `body{background:var(--bg)}` não falha nada |
| D-05 | O markup do **estado de resultado** não tinha guarda nenhuma | 🟢 **fechada nesta entrega** | `tests/test_estado_do_resultado.py` prende o acoplamento índice↔cartão, o selo do cabeçalho e os oito rótulos da grade, com prova por mutação |
| D-06 | Google Fonts é o **terceiro** host de CDN, com stylesheet bloqueante de renderização | 🟢 | Num projeto cujo Princípio I é "dado real nunca sai", carregar fonte de terceiro é decisão a declarar. O fallback é honesto (`Georgia`, `system-ui`) |
| D-07 | O botão de tema fixo sobrepõe o cartão em janela de ~992–1130 px, e cobre o cabeçalho do cartão depois de um salto de âncora | 🟢 | Medido por aritmética de box model, não em navegador — este ambiente não tem browser headless |

## Regras sob vigilância

| Item | Onde | Sinal de quebra |
|------|------|-----------------|
| `src/static/` continua **ausente** | `W004` (003) | A pasta reaparecer no disco, ou a folha passar a responder em `/static/...` |
| A folha entra na imagem | `.dockerignore`, `docker/Dockerfile` | `.dockerignore` deixar de ser lista de permissão, ou `COPY src/ /app/src/` sair |
| `<h1>` escondido **se, e somente se,** a arte responde | `RN-23` emendada | O `h1` voltar a ser escondido por literal fixo, ou o título sumir do documento |
| O selo da confrontação fica no **cabeçalho** do cartão | D-05 | O selo voltar a existir só na seção 4 |
| `--on-danger` definido nos **dois** temas | D-02 da revisão de acessibilidade | O `.btn-danger` voltar a fixar `#fff`: no escuro o rótulo do "Apagar" desaparece (2,18:1) |
| `SHA_DA_TELA` mede a tela **vazia** | `tests/test_icone_de_atalho.py` | Uma mudança do estado de resultado **não** move este hash — o alcance dele é declarado, e é por isso que o D-05 existia |

## Fontes

- `src/app.py` — a rota `GET /app.css`, o processador `_arte_do_topo_disponivel` e o bloco da arte do topo
- `src/assets/app.css` — a folha, com os tokens, o bloco de tema escuro e o botão de tema
- `src/templates/index.html` — o `<h1>` condicional, o índice, o selo, a grade e o controle de tema
- `tests/test_estado_do_resultado.py`, `tests/test_estilo_da_tela.py`, `tests/test_banner_do_topo.py`
- `_reversa_sdd/addenda/011-escolher-arquivo-da-lista.md` — `RN-23` e `RN-24`, emendadas aqui
- `_reversa_sdd/adrs/29-arte-derivada-com-receita-unica.md` — o desenho de rota por arte que a folha seguiu
- `_reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md#W004` — a proibição de `src/static/`
- Revisão adversarial de 2026-10-11: três leitores independentes em contexto novo (Jinja/HTML, acessibilidade e contratos/regressão), mais conferência do operador. Os achados que viraram D-01 a D-07 saíram dela
