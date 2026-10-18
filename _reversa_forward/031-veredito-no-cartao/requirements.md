# Requirements: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Documento pedido pelo operador em 2026-10-18. O literal de máquina do terceiro status é
> `ERRO CRONICO / QUEBRA DE LINHA`; na tela ele **não** aparece como texto visível (RN-04), mas é
> preservado no `title` do selo.

## 1. Resumo executivo

A feature `028` entregou o veredito de viabilidade temporal — `VALIDADO`, `INCONCLUSIVO` ou
`ERRO CRONICO / QUEBRA DE LINHA` — e ele nunca chegou à tela. O operador continua vendo o cartão de
cada match com o confronto de cM, a janela de vida e a profundidade, e **não** vê a única pergunta
que cruza as três: a linha documental é temporalmente viável? Esta feature leva esse veredito para o
cartão, como um selo novo, com o motivo no `title`, sem tocar nos quatro estados existentes.

A entrega mexe no contrato de tela — que é congelado por `sha256` —, então a atualização do
invariante faz parte da feature, não é efeito colateral.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `src/templates/index.html` (538-628) | O cartão `details.card.cartao-do-resultado`: cabeçalho com selo de cM, selo de confronto (`estado-{{ confrontacao_efetiva }}`), selo de identidade e a linha `cabecalho-sinais` | 🟢 |
| `src/assets/app.css` (207-211) | `.badge[class*="estado-"]{color:#fff}` reivindica **qualquer** classe que contenha `estado-`; as quatro cores (`--st-*`) foram escolhidas para texto branco | 🟢 |
| `src/assets/app.css` (311-324) | A lição medida: um selo de aviso nasceu com classe `estado-identidade_impossivel` e o texto branco sobre creme deu **1,11:1** — o rótulo sumiu | 🟢 |
| `src/assets/app.css` (10-40) | Paleta e contraste justificado de cada `--st-*` nos dois temas (`#2F6B3A`, `#7A4F00`, `#A8321F`, `#6A6150`) | 🟢 |
| `src/application/dna_analysis.py:42` | `ResultadoDeAnalise`: a projeção pura que o template consome (ADR-33) | 🟢 |
| `src/core/dna_analysis.py` (438-445) | Cada resultado já carrega `"documentary"` e `"comparison"` — o insumo que o validador precisa | 🟢 |
| `src/app.py:686` | `dna_results=resultado.resultados` é o único ponto em que a análise chega ao template | 🟢 |
| `tests/test_icone_de_atalho.py` (214, 307) | `SHA_DA_TELA`: duas asserções que prendem o HTML de `GET /` byte a byte | 🟢 |
| `_reversa_sdd/addenda/028-validador-de-dados-dna.md` | O contrato do veredito: `status`, `motivo`, `codigos` com severidade | 🟢 |
| `_reversa_sdd/architecture.md#4-modelo-de-dados` | `None` significa "não sei / não existe", nunca zero | 🟢 |
| `_reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md` | A projeção é pura e existe para o literal de tela não ganhar autoridade semântica | 🟢 |
| `.reversa/principles.md#ii` | Comportamento observável preservado: os quatro estados não mudam | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |

### 2.1 O que já existe e **não** será reimplementado

| Componente | O que já responde | Por que não basta |
|------------|-------------------|-------------------|
| `core.validator` | O veredito e os códigos | Não conhece tela nem árvore; nunca é chamado no fluxo de DNA |
| `core.analise_dna` | `documentary` e `comparison` por resultado | Não chama o validador |
| `application.dna_analysis` | A projeção pura que vira payload de **persistência** (`ConexaoDaAnalise`) | Não é o que o template consome, e o banco não tem onde guardar o veredito |
| `index.html` | Selos de cM, confronto, identidade, janela e profundidade | Não tem o veredito temporal |

### 2.2 A lacuna que esta feature fecha

1. **O veredito não sai do Python.** Nenhum caminho do fluxo de DNA chama `validar_comparacao`.
2. **A tela não tem onde mostrá-lo.** O cabeçalho do cartão já tem cinco sinais e nenhum é o
   temporal.
3. **O `motivo` e os `codigos` não têm destino.** Quem recebe `ERRO CRONICO / QUEBRA DE LINHA`
   fica sem saber qual das seis anomalias foi acusada.
4. **Não há teste de tela para o veredito.** O `sha256` prende o HTML, mas nada prende a presença do
   selo.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador / genealogista | Decidir, sem abrir o cartão, se o match é temporalmente possível | Passa os olhos na lista e vê "Linha em conflito" no cartão do doador vivo ligado ao ancestral de 1650 |
| Auditor de dados | Saber por que aquele cartão está em conflito | Passa o mouse e lê o motivo e o código da anomalia |
| Desenvolvedor do legado | Ligar o veredito sem recalcular nada | Aproveita `documentary` e `comparison` que o laço já produziu |
| Revisor de acessibilidade | Ler o selo com leitor de tela | Ouve a frase completa, não só o rótulo |

## 4. Regras de negócio novas ou alteradas

### 4.1 Definições operacionais

| Termo | Definição nesta feature |
|-------|--------------------------|
| **Veredito de validação** | O `status` de `core.validator.validar_comparacao`: `VALIDADO`, `INCONCLUSIVO` ou `ERRO CRONICO / QUEBRA DE LINHA`. |
| **Selo** | O `span.badge` que mostra o veredito no cabeçalho do cartão. |
| **Rótulo humano** | O texto visível do selo: `Validado` ou `Linha em conflito`. `INCONCLUSIVO` não tem rótulo porque não gera selo (RN-04). |
| **Aviso** | O `title` do selo: o `motivo` e o primeiro código crítico. |
| **Cartão** | O `details.card.cartao-do-resultado` de cada match analisado. |

### 4.2 Regras

1. **RN-01: o veredito é o da `028`, sem recálculo na tela.** O template recebe `status`, `rotulo` e
   `aviso` prontos da projeção; nenhuma regra de validação vive em Jinja nem em JavaScript. 🟢
   - Origem no legado: `_reversa_sdd/addenda/028-validador-de-dados-dna.md`;
     `_reversa_sdd/adrs/33-desfecho-em-tres-valores-e-projecao-pura.md`
   - Tipo: nova (composição, não reimplementação)

2. **RN-02: os quatro estados do confronto não mudam.** `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e
   `INCONCLUSIVO` mantêm texto, classe e cor; o veredito é um **campo novo**, não um quinto estado. 🟢
   - Origem no legado: `.reversa/principles.md#ii`; `src/assets/app.css` (207-211)
   - Tipo: preservada

3. **RN-03: a classe do selo não pode conter `estado-`, e o selo é de contorno.** A regra
   `.badge[class*="estado-"]` pinta o texto de branco; um selo **sem preenchimento** ficaria
   ilegível — foi o que aconteceu com o `estado-identidade_impossivel` (1,11:1). O prefixo é
   `validacao-`, e o selo é de contorno: `background:transparent`, `border:1px solid` na cor do
   status e texto em `--ink`, que já clareia no tema escuro. 🟢
   - Origem no legado: `src/assets/app.css` (311-324); `BUG-20260929-J6PQ` e a medição de
     2026-10-14; `src/assets/app.css` (47-69) para o tema escuro
   - Tipo: preservada (a lição continua valendo; decidido em §9, D3)

4. **RN-04: só o que conclui ganha selo, e o texto é humano.** `VALIDADO` → `Validado`;
   `ERRO CRONICO / QUEBRA DE LINHA` → `Linha em conflito`. **`INCONCLUSIVO` não ganha selo**: numa
   análise real são 142 cartões, e o inconclusivo é o caso mais comum — o selo marcaria quase todos
   e deixaria de marcar coisa alguma. A ausência de selo significa "não concluído", e isso está
   declarado na legenda da lista. O literal de máquina
   `ERRO CRONICO / QUEBRA DE LINHA`, com 31 caracteres e sem acento, **não** vai para o texto
   visível: fica no `title`, onde quem audita lê. 🟢
   - Origem no legado: `src/templates/index.html` (todos os selos usam rótulo humano)
   - Tipo: nova (decidido em §9, D1, D2 e D3)

5. **RN-05: o `title` traz o motivo e o primeiro código crítico.** Se houver mais de um código, o
   texto diz quantos são; sem código crítico, mostra o motivo do `INCONCLUSIVO`. `None` vira
   ausência de texto, nunca a palavra "None". 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#4-modelo-de-dados`
   - Tipo: nova

6. **RN-06: o veredito é calculado uma vez por resultado, no fluxo que já tem os dados.** O laço que
   monta `documentary` e `comparison` passa a chamar `validar_comparacao` com o que já produziu;
   não há segundo parse do GEDCOM nem segunda passada de matching. 🟢
   - Origem no legado: `src/core/dna_analysis.py` (438-445)
   - Tipo: nova (a feature `028` deixou a composição pronta)

7. **RN-07: o `ano_referencia` é o mesmo que a janela de vida já usa.** O veredito é de hoje, como o
   resto da tela; não se congela o ano nem se lê relógio em dois lugares diferentes. 🟢
   - Origem no legado: `src/core/janela_de_vida.py` (`ano_de_referencia`)
   - Tipo: preservada

8. **RN-08: o `SHA_DA_TELA` NÃO muda nesta entrega — e isso foi verificado, não suposto.** O
   invariante prende o HTML de `GET /` **sem resultados**, e o bloco do cartão só é
   renderizado quando há `dna_results`. Medido em 2026-10-18: `GET /` não contém
   `legenda-da-validacao`, e o teste do hash passa sem alteração. Logo o hash **não** protege
   o cartão; quem passa a protegê-lo são os testes de tela novos (RF-11). 🟢
   - Origem no legado: `tests/test_icone_de_atalho.py` (214, 307) — asserções sobre `GET /`
   - Tipo: alterada (a premissa de que o hash cobria o cartão estava **errada**)

9. **RN-09: o selo é acessível.** O texto visível é curto e o `visually-hidden` diz a frase completa
   ("veredito de validação: linha em conflito"), como já fazem os selos de janela e profundidade. 🟢
   - Origem no legado: `src/templates/index.html` (614, 617, 624)
   - Tipo: preservada (padrão da tela)

10. **RN-10: sem veredito, sem selo.** Resultado sem `status` (confronto não executado, por exemplo)
    não renderiza selo nenhum — nada de selo inventado no template. O mesmo vale para `INCONCLUSIVO`,
    por decisão de §9. 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#4-modelo-de-dados`
    - Tipo: nova

11. **RN-11: nada muda fora do cartão.** O diagrama Mermaid, a busca de caminho, a lista de
    arquivos e o banco continuam como estão. 🟢
    - Origem no legado: `.reversa/principles.md#ii`
    - Tipo: preservada

> **Princípios aplicados.** I (fixture sintética nos testes de tela), II (os quatro estados e o resto
> da tela intactos), III (todo selo com teste, e o hash atualizado como decisão), IV (nenhuma
> travessia nova), V (o veredito carrega a fonte da `028`). Nenhum conflito com princípio ativo.

### 4.3 Valores de domínio e fontes

| Constante | Valor | Fonte | Confidência |
|-----------|-------|-------|-------------|
| Rótulo de `VALIDADO` | `Validado` | Decidido em §9 (D2) | 🟢 |
| Rótulo de `ERRO CRONICO / QUEBRA DE LINHA` | `Linha em conflito` | Decidido em §9 (D2); "quebra de linha" é jargão do domínio e longo demais para um selo | 🟢 |
| `INCONCLUSIVO` | sem selo | Decidido em §9 (D2): marcar quase todos os cartões não marcaria nenhum | 🟢 |
| Variáveis de cor | `--validacao-valido` e `--validacao-conflito`, definidas **nos dois temas** | Decidido em §9 (D3): contorno com texto em `--ink`; as cores reaproveitam os valores que `--primary`/`--danger` já usam em cada tema | 🟢 |
| Contraste mínimo | **4,5:1** para o texto; **3:1** para a borda | WCAG AA (texto pequeno) e AA para elemento não textual; a lição do 1,11:1 está em `app.css` (311-324) | 🟢 |

> **Por que não mostrar o literal.** `ERRO CRONICO / QUEBRA DE LINHA` tem 31 caracteres, sem acento
> e com barra — ocupa o cabeçalho inteiro e não cabe num `badge`. O literal continua disponível no
> `title`, que é onde quem audita vai ler.

> **O custo de escolher contorno, dito por inteiro.** O contorno põe a cor do status no texto/borda,
> e as cores atuais dos quatro estados **não** são redefinidas no tema escuro (`--st-*` ficam
> escuras, porque o texto do selo delas é branco). Por isso a decisão de §9 implica **duas variáveis
> novas por tema** — é o único jeito de o contorno ficar legível nos dois. O texto do selo fica em
> `--ink`, que já vira claro no escuro; só a borda usa a cor do status.

### 4.4 Códigos de aviso (contrato de tela)

| Código | Quando aparece | Efeito |
|--------|----------------|--------|
| `VALIDACAO_AUSENTE` | O resultado não tem `status` | Nenhum selo é renderizado |
| `VALIDACAO_INCONCLUSIVA` | `status` é `INCONCLUSIVO` | Nenhum selo; o status continua na projeção para uso futuro |
| `VALIDACAO_EM_CONFLITO` | `status` é `ERRO CRONICO / QUEBRA DE LINHA` | Selo de contorno vermelho, com o primeiro código crítico no `title` |
| `VALIDACAO_CONFIRMADA` | `status` é `VALIDADO` | Selo de contorno verde, com o motivo no `title` |

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Cada item de `resultados` — o dicionário que o template consome — ganha `validacao_status`, `validacao_rotulo`, `validacao_classe` e `validacao_aviso` | Must | Com um resultado de erro, os quatro campos vêm preenchidos; sem `status`, vêm `None` nos quatro | 🟢 |
| RF-02 | O fluxo de DNA chama `validar_comparacao` uma vez por resultado, reutilizando `documentary`, `comparison` e o `ano_referencia` que o laço já calculou | Must | Teste com espião confirma uma chamada por resultado e nenhum parse extra | 🟢 |
| RF-03 | O cartão renderiza o selo quando o veredito conclui (`VALIDADO` ou `ERRO CRONICO / QUEBRA DE LINHA`) | Must | HTML de `GET /` contém `badge validacao-` no cartão do resultado com veredito que conclui | 🟢 |
| RF-04 | O texto visível é o rótulo humano, e o `title` traz motivo e código | Must | No HTML: `>Linha em conflito<` e um `title` contendo o código crítico | 🟢 |
| RF-05 | A classe do selo não contém `estado-` | Must | Teste que varre o HTML e falha se achar `validacao` casando com `estado-` | 🟢 |
| RF-06 | O selo é de contorno, com texto em `--ink` e borda na cor do status, legível nos dois temas | Must | A folha define `--validacao-valido` e `--validacao-conflito` nos dois blocos de tema; o contraste medido é ≥ 4,5:1 no texto e ≥ 3:1 na borda | 🟢 |
| RF-07 | Sem veredito **ou** com veredito inconclusivo, nenhum selo é renderizado | Must | Resultado sem `status` e resultado `INCONCLUSIVO` não produzem nó com `validacao-` | 🟢 |
| RF-08 | Os quatro estados e os demais selos não mudam | Must | `estado-COMPATIVEL` e companhia continuam com o mesmo texto e a mesma cor; o teste de hash passa após atualização declarada | 🟢 |
| RF-09 | O `SHA_DA_TELA` é **verificado** e permanece igual, porque o bloco de resultados não entra em `GET /` | Must | As duas asserções continuam passando sem alteração, e o teste de tela prova o selo no cartão | 🟢 |
| RF-10 | O selo é acessível | Must | O `visually-hidden` contém a frase completa do veredito | 🟢 |
| RF-11 | Testes de tela cobrem os três status e a ausência | Must | Suíte verde; um teste por status, com fixture sintética | 🟢 |
| RF-12 | O mapeamento status → rótulo e status → classe mora em Python, não em Jinja | Should | O template só testa presença e imprime o que recebe | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Arquitetura | O cálculo entra no fluxo que já tem `documentary`/`comparison`; a projeção continua pura (ADR-33) e `reporting/` não importa `core` | `ADR-33`; `ADR-34` | 🟢 |
| Desempenho | Uma chamada de `validar_comparacao` por cartão; a análise real tem 142 cartões e a função é pura e O(saltos + relações) | Medição futura no teste de integração; sem segunda passada de parsing | 🟡 |
| Contrato de tela | O `SHA_DA_TELA` é atualizado na entrega, com data e motivo no comentário | `tests/test_icone_de_atalho.py` | 🟢 |
| Acessibilidade | Contraste ≥ 4,5:1 e `visually-hidden` com a frase completa | `app.css` (311-324); selos 614/617/624 | 🟢 |
| Segurança | Nenhum dado real em teste; o HTML não recebe nome novo além dos que já exibe | `.reversa/principles.md#i` | 🟢 |
| Compatibilidade | Sem dependência nova; Python 3.14.6 e Jinja do Flask atual | `requirements.txt` intocado | 🟢 |
| Determinismo | Mesma árvore, mesmo CSV e mesmo ano de referência produzem o mesmo selo | `RN-07`; `ano_referencia` de `janela_de_vida` | 🟢 |
| Observabilidade | O `title` carrega o código da anomalia — o selo é legível sem abrir o cartão | `RN-05` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: cartão com linha em conflito mostra o selo
  Dado um resultado de análise cujo veredito é ERRO CRONICO / QUEBRA DE LINHA
  Quando a tela é renderizada
  Então o cartão exibe o selo "Linha em conflito"
  E o title do selo cita o primeiro código crítico

Cenário: cartão validado mostra o selo
  Dado um resultado cujo veredito é VALIDADO
  Quando a tela é renderizada
  Então o cartão exibe o selo "Validado"

Cenário: cartão inconclusivo não ganha selo
  Dado um resultado cujo veredito é INCONCLUSIVO
  Quando a tela é renderizada
  Então o cartão não exibe nenhum selo de validação
  E o status continua disponível na projeção

Cenário: resultado sem veredito não ganha selo
  Dado um resultado sem campo de validação
  Quando a tela é renderizada
  Então o cartão não exibe nenhum selo de validação

Cenário: a classe do selo não colide com os quatro estados
  Dado o HTML de uma análise com veredito
  Quando a classe do selo é inspecionada
  Então ela começa com "validacao-"
  E não contém "estado-"

Cenário: os quatro estados continuam iguais
  Dado um cartão com confronto COMPATIVEL
  Quando a tela é renderizada
  Então o selo de confronto continua com o mesmo texto e a mesma classe de antes

Cenário: o invariante da tela é atualizado e continua valendo
  Dado o HTML novo da tela
  Quando o hash é recalculado
  Então o SHA_DA_TELA novo corresponde ao HTML servido
  E o comentário registra a data e o motivo da mudança
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem o dado na projeção e sem a chamada no fluxo, não há o que mostrar |
| RF-03, RF-04, RF-07 | Must | É a feature: o selo, o texto e a ausência correta |
| RF-05, RF-06 | Must | A lição do 1,11:1 e o contraste são requisitos, não estética |
| RF-08, RF-09 | Must | Preservar os quatro estados e manter o invariante com sentido |
| RF-10, RF-11 | Must | `.reversa/principles.md#iii`; acessibilidade é padrão da tela |
| RF-12 | Should | Sem isso o template acumularia regra, mas o selo ainda funciona |
| Selo no resumo da análise | Won't (esta feature) | Decidido em §9: um selo por cartão; o resumo agrega vários e exigiria regra de agregação |
| Filtro ou ordenação por veredito | Won't (esta feature) | É outra pergunta ("mostre só os quebrados") e muda a lista, não o cartão |
| Selo preenchido com cor fora da paleta | Won't (esta feature) | Decidido em §9: contorno com as cores que a paleta já tem; inventar cor é decisão de design system |

## 9. Esclarecimentos

### Sessão 2026-10-18

- **Q:** Onde o selo do veredito entra?
  **R:** No **cabeçalho do cartão**, junto aos outros selos (cM, confronto, identidade). Sem selo na
  seção 4 e sem resumo agregado: um selo por cartão é o que o pedido descreve.
- **Q:** Mostrar o selo quando o veredito é `INCONCLUSIVO`?
  **R:** **Não.** O selo marca o que **conclui** — `Validado` e `Linha em conflito`. O inconclusivo é
  o caso mais comum numa análise de 142 cartões, e marcar quase todos não marcaria nenhum. A ausência
  de selo significa "não concluído", e a legenda da lista declara isso.
- **Q:** Como o selo se distingue visualmente dos quatro estados?
  **R:** **Contorno**, não preenchimento, usando as cores dos estados. Distingue por forma em vez de
  criar cor nova, e não compete com o selo de confronto, que é preenchido.
- **Custo registrado, e ele é real:** o contorno põe a cor do status no texto/borda, mas `--st-*`
  **não** são redefinidas no tema escuro (ficam escuras, porque o texto do selo delas é branco).
  Então a escolha implica **duas variáveis novas por tema** (`--validacao-valido`,
  `--validacao-conflito`), com os valores que `--primary`/`--danger` já usam em cada um. É a menor
  versão possível da "cor nova" — e sem ela o contorno sumiria no tema escuro.

## 10. Lacunas

Nenhuma lacuna aberta após a sessão de esclarecimentos de 2026-10-18. As três dúvidas iniciais
(lugar do selo, veredito inconclusivo e aparência) foram resolvidas em §9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-18 | Sessão de esclarecimentos: selo no cabeçalho, só o que conclui, contorno com duas variáveis por tema | reversa |
| 2026-10-18 | Correção no plano: os campos entram no **dicionário de resultado** que o template consome (não em `ResultadoDeAnalise`) e são **quatro**, porque a classe CSS também é decidida em Python (RF-12) | reversa |
