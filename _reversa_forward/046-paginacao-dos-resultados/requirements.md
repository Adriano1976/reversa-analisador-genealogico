# Requirements: paginação dos Resultados das Análises de Conexão

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A tela de resultados entrega a análise inteira numa rolagem só: **68 cartões** e **≈ 3,9 MB** de
HTML, medidos neste repositório em 2026-10-22. Esta feature põe **paginação sobre a lista de
cartões**, com **10 conexões por página** como padrão e escolha entre **10, 20 e 30**.

O que muda é só a leitura. A ordem não muda, os números do topo não mudam, nenhum cartão sai do
documento e nenhum cálculo é refeito ao trocar de página. É **mudança de comportamento**, não
refactor: o padrão de exibição passa de "tudo" para "as 10 primeiras" — declarado porque o
princípio II de `.reversa/principles.md` exige que a feature diga de qual dos dois se trata.

A paginação cobre **só os cartões de conexão**: o bloco de descartes fica como está, decisão
registrada em §9.

> **Vocabulário desta spec.** *Cartão* é o bloco recolhível de uma conexão na tela (`<details>`).
> *Conexão* é a pessoa analisada, com todos os kits dela. *Descartes* são os matches rejeitados,
> que têm bloco próprio e não entram na paginação. *cM* é a soma de centimorgans de um kit.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#3.9` | A ordem é **documental primeiro, cM decrescente depois**, e o código declara que **não é ordem de confiança**. Paginar não reordena. | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#Regras de Negócio` (Apresentação) | `BR-D-41` fixa a ordem; `BR-D-42` fixa a mensagem final; `BR-D-65` fixa a ordem das observações. | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#Requisitos Funcionais` | `RF-25` ordenação, `RF-26` mensagem `"N conexões encontradas. M descartadas."`, `RF-27` lista de descartes com motivo. | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#Requisitos Não Funcionais` | "**Sem cache entre requisições**: os índices do GEDCOM inteiro são reconstruídos a cada `POST`". É o que proíbe paginar no servidor. | 🟢 |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#Nada sai do documento` | O recolhimento é **visual**; uma implementação que removesse conteúdo do HTML "teria destruído a leitura da análise como texto". | 🟢 |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#Os dois acoplamentos que o recolhimento cria` | `abrirCartaoDoAlvo` abre o `details` do alvo no carregamento e no `hashchange`; o `id` mora no próprio `details`. | 🟢 |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` §"`SHA_DA_TELA`, declarado" | O hash da tela de entrada mede também o `<script>` global: mexer no script **muda o hash** e a mudança tem de ser declarada. | 🟢 |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md#O acoplamento que sobrou` | `#resultados` é o alvo do link "Voltar" de cada cartão, preso por teste com prova de sensibilidade. | 🟢 |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md#Resíduo declarado` | "A tabela alinhada era melhor para varrer 142 linhas" — a densidade da lista é a dor declarada, e é ela que esta feature ataca. | 🟢 |
| `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md#E012` | Os textos sob o título são **um parágrafo só**: contagem, árvore sugerida e legenda do selo. O indicador de página entra fora dele. | 🟢 |

> **A extração não especifica o markup da tela de resultados.** A unit `analise-dna` especifica o
> **dado** e o **comportamento** (95 regras), não a marcação: as regras da lista vivem nos adendos
> vigentes (`018`, `019`, `020`, `033`, `036`, `037`). Por isso as âncoras acima são, em maioria,
> adendos — e por isso a fase de plano deve ler o template, não só o `_reversa_sdd/`.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador (dono da árvore) | varrer as conexões sem rolar 68 cartões | abre a análise, lê os 10 primeiros cartões e passa para a página 2 |
| Operador comparando conexões | ver mais de uma dezena de uma vez | troca para 30 por página e compara três dezenas no mesmo bloco |
| Operador que chega por link | abrir um cartão específico | a barra traz `#resultado-37`; a tela mostra a página que o contém, com ele aberto |
| Leitor de tela | saber onde está na lista | o controle anuncia "Página 3 de 7" e marca o botão corrente |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: a unidade da página é o cartão de conexão.** Cada cartão é uma **pessoa analisada**,
   com todos os kits dela; dois kits da mesma pessoa continuam sendo **um** cartão e não contam
   duas vezes. A paginação cobre **só esta lista**: o bloco de descartes tem bloco próprio e fica
   fora. 🟢
   - Origem no legado: `_reversa_sdd/analise-dna/requirements.md#Regras de Negócio` (`BR-D-12`,
     `BR-D-19`: um nome em dois kits é uma pessoa com duas evidências)
   - Tipo: nova
2. **RN-02: paginar não reordena.** A página 1 começa no primeiro cartão da ordem apresentada, e a
   ordem é a de `BR-D-41` / `domain.md#3.9`. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.9`
   - Tipo: nova (declara que `BR-D-41` permanece intacta)
3. **RN-03: 10 é o padrão, e 10, 20 e 30 são as únicas opções.** Não há campo livre: nenhum outro
   valor é aceito, e valor inválido não existe na tela. 🟢
   - Tipo: nova
4. **RN-04: paginar é apresentar — nenhum cartão sai do documento.** Os 68 cartões continuam no
   HTML; a página apenas esconde os que não pertencem a ela. 🟢
   - Origem no legado: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#Nada sai do documento`
   - Tipo: nova (restrição herdada do adendo `018`)
5. **RN-05: o documento nasce com tudo visível; o script é que esconde.** O HTML não traz página 2
   pré-oculta, e sem script o operador vê a lista inteira. 🟢
   - Justificativa dupla: não se perde conteúdo sem script, e um `details` escondido tem container
     de tamanho zero — o diagrama só mede certo com o cartão visível (mesma razão do `toggle`
     registrada no adendo `018`).
   - Tipo: nova
6. **RN-06: trocar de página não reexecuta a análise.** Nenhum envio de formulário, nenhuma
   releitura de GEDCOM ou CSV: a troca é local. 🟢
   - Origem no legado: `_reversa_sdd/analise-dna/requirements.md#Requisitos Não Funcionais` ("sem
     cache entre requisições")
   - Tipo: nova
7. **RN-07: os números do topo descrevem a análise inteira, nunca a página.** "68 conexões
   analisadas", a contagem de sem correspondência, a árvore sugerida, a legenda do selo e a
   cobertura do arquivo ficam como estão; o indicador de página é um texto próprio, separado. 🟢
   - Origem no legado: `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md#E012` e `RF-26`
   - Tipo: alterada (declara explicitamente o que **não** muda, para que ninguém "corrija" o 68
     para 10)
8. **RN-08: mudar o tamanho da página volta para a página 1.** A lista mudou de tamanho; só a
   primeira posição significa a mesma coisa antes e depois. 🟢
   - Tipo: nova
9. **RN-09: `#resultado-N` mostra a página que contém N e depois abre o cartão.** Nessa ordem,
   porque abrir um cartão escondido dispara o `toggle` e o diagrama mediria um container de
   tamanho zero. 🟢
   - Origem no legado: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md#Os dois acoplamentos que o recolhimento cria`
   - Tipo: alterada (o acoplamento existente ganha a etapa de trocar de página antes de abrir)
10. **RN-10: "Expandir todas" e "Recolher todas" agem só nos cartões da página corrente.** 🟢
    - Origem no legado: `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` (os dois
      botões existem desde o `018`, quando todos os cartões eram visíveis)
    - Tipo: alterada — decisão de 2026-10-22. O **rótulo não muda**; a diferença entre o rótulo e
      o alcance fica registrada em §10.
11. **RN-11: o controle só existe quando há mais de uma página.** Com N menor ou igual ao tamanho
    escolhido, nada é renderizado — a mesma ideia da guarda `dna_results | length > 1` dos botões
    de expandir/recolher. 🟢
    - Tipo: nova
12. **RN-12: a última página tem o resto, sem inventar cartão.** 68 cartões a 10 por página dão
    **7 páginas**: seis cheias e uma com oito. 🟢
    - Tipo: nova
13. **RN-13: o "Voltar" de cada cartão continua apontando para `#resultados` e não troca a página
    corrente.** Quem volta de um cartão da página 4 continua na página 4. 🟢
    - Origem no legado: `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md#O acoplamento que sobrou`
    - Tipo: nova (preservação declarada)
14. **RN-14: a escolha do tamanho vale para a análise corrente e não é lembrada na próxima.**
    Toda análise começa em 10. 🟢
    - Tipo: nova — decisão de 2026-10-22
15. **RN-15: o controle fica no topo da lista**, entre o parágrafo de contagem e o primeiro
    cartão: seletor "Conexões por página", "anterior", "próxima" e os números das páginas. 🟢
    - Tipo: nova — decisão de 2026-10-22

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Mostrar **10** cartões por página quando o operador não escolheu nada | Must | Com 68 cartões, a tela mostra os cartões 1 a 10 e "Página 1 de 7" | 🟢 |
| RF-02 | Oferecer **10, 20 e 30** por página e aplicar a escolha na hora | Must | Escolher 20 mostra 1 a 20 e "Página 1 de 4"; nenhuma requisição é disparada | 🟢 |
| RF-03 | Navegar por **anterior**, **próxima** e **número da página** | Must | Da página 1, "próxima" mostra 11 a 20; na página 1, "anterior" e o número 0 não existem | 🟢 |
| RF-04 | Manter **todos** os cartões no documento, em qualquer página | Must | O HTML traz 68 `details.cartao-do-resultado` estando na página 1 ou na 7 | 🟢 |
| RF-05 | Manter os números do topo referidos à **análise inteira** | Must | Na página 3, a frase continua "68 conexões analisadas" e a cobertura não muda | 🟢 |
| RF-06 | Anunciar a página corrente | Must | Existe o texto "Página 3 de 7" e o botão 3 carrega `aria-current="page"` | 🟢 |
| RF-07 | Não renderizar controle quando tudo cabe numa página | Should | Com 8 cartões e 10 por página, nenhum controle de paginação aparece | 🟢 |
| RF-08 | Voltar à página 1 ao mudar o tamanho | Must | Estando na página 3 com 10 por página, escolher 30 mostra "Página 1 de 3" | 🟢 |
| RF-09 | Honrar `#resultado-N`: mostrar a página de N e **depois** abrir o cartão | Must | Abrir a URL com `#resultado-37` a 10 por página mostra a página 4 com o cartão 37 aberto | 🟢 |
| RF-10 | Restringir "Expandir todas" e "Recolher todas" à página corrente | Should | Com 10 por página, "Expandir todas" deixa exatamente 10 `details` abertos | 🟡 |
| RF-11 | Degradar para a lista inteira quando não há script | Must | Com JavaScript desligado, os 68 cartões aparecem em sequência | 🟢 |
| RF-12 | Preservar os contratos do cartão: `id` no `details`, numeração sem buraco e "Voltar" → `#resultados` | Must | `tests/test_estado_do_resultado.py` passa sem alteração de asserção | 🟢 |
| RF-13 | Levar a lista de volta ao topo ao trocar de página | Should | Depois de "próxima", o primeiro cartão da página nova está na área visível | 🟡 |
| RF-14 | Não reexecutar a análise ao trocar de página | Must | Nenhuma requisição de rede é disparada; descartes e cobertura seguem idênticos | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A troca de página é **local**: sem rede, sem `POST`, sem leitura de arquivo | `analise-dna/requirements.md#Requisitos Não Funcionais` — cada `POST` reconstrói os índices do GEDCOM inteiro | 🟢 |
| Desempenho | A paginação **não reduz bytes**: os 68 cartões seguem no HTML (~3,9 MB) | Adendo `018`, resíduo 2: reduzir HTML exigiria remover conteúdo, que é o que o adendo recusa | 🟢 |
| Acessibilidade | O controle é navegável por teclado, o grupo tem rótulo e a página corrente é marcada com `aria-current="page"` | Sem marcação, "Página 3" não é anunciada e o operador de leitor de tela não sabe onde está | 🟢 |
| Acessibilidade | Cartão fora da página é escondido de forma que saia do fluxo de foco e da árvore de acessibilidade | Esconder só com opacidade deixaria 58 cartões focáveis e invisíveis | 🟢 |
| Compatibilidade | Sem dependência de rede nova e sem biblioteca nova | A tela já carrega o que precisa; a paginação é markup, estilo e script locais | 🟢 |
| Compatibilidade | Sem script, a tela mostra a lista inteira | `RN-05`; é também o estado atual do sistema | 🟢 |
| Manutenibilidade | As três opções e o padrão têm **uma** fonte; nenhum desses números é repetido na marcação | Repetir `10` em `<option>`, em `data-*` e no script é como o padrão se perde | 🟢 |
| Manutenibilidade | A mudança de `SHA_DA_TELA` e `TAMANHO_ESPERADO` é **declarada e medida**, não descoberta no vermelho | `tests/test_icone_de_atalho.py`; o hash mede o `<script>` global, como o adendo `018` já registrou | 🟢 |
| Observabilidade | Nenhuma nova: não há log, métrica ou trace, e o estado da página não é registrado nem persistido | `analise-dna/requirements.md#Requisitos Não Funcionais` (Observabilidade) | 🟢 |
| Privacidade | Nenhum dado novo trafega ou é exposto; a paginação não filtra, não busca e não esconde cartão por conteúdo | A feature não toca GEDCOM, CSV nem histórico | 🟢 |
| Internacionalização | Literais em português, como o resto da tela | `traducao.py`, `evidence_comparison.py`, template | 🟢 |
| Princípios | A verificação com o arquivo real usa `src/uploads/` em execução e **nada** dele entra em fixture, golden ou documento; os testes usam `tests/fixtures/sample_gedcom.py` e `sample_dna.py` | `.reversa/principles.md` I | 🟢 |
| Princípios | Toda regra desta feature chega com teste que falha antes e passa depois | `.reversa/principles.md` III | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: a primeira página é a de 10
  Dado uma análise com 68 cartões e o operador sem escolha registrada
  Quando a tela de resultados é exibida
  Então os cartões 1 a 10 estão visíveis
  E os cartões 11 a 68 estão no documento, porém escondidos
  E o indicador diz "Página 1 de 7"

Cenário: escolher 20 por página
  Dado que o operador está na página 1 com 10 por página
  Quando ele escolhe 20 por página
  Então os cartões 1 a 20 ficam visíveis
  E o indicador diz "Página 1 de 4"
  E nenhuma requisição de rede é disparada

Cenário: a última página tem o resto
  Dado uma análise com 68 cartões e 10 por página
  Quando o operador vai para a última página
  Então 8 cartões estão visíveis, e não 10
  E o indicador diz "Página 7 de 7"

Cenário: mudar o tamanho volta para a primeira página
  Dado que o operador está na página 3 com 10 por página
  Quando ele escolhe 30 por página
  Então o indicador diz "Página 1 de 3"

Cenário: abrir um cartão por link direto
  Dado a URL com "#resultado-37" e 10 por página
  Quando a página termina de carregar
  Então a página 4 está visível
  E o cartão 37 está aberto
  E o diagrama dele foi desenhado com o container visível

Cenário: os números do topo não são os da página
  Dado que o operador está na página 3 de 7
  Quando ele lê a contagem sob o título
  Então a frase diz "68 conexões analisadas"
  E a cobertura do arquivo e a contagem de sem correspondência não mudaram

Cenário: lista que cabe numa página
  Dado uma análise com 8 cartões e 10 por página
  Quando a tela de resultados é exibida
  Então os 8 cartões estão visíveis
  E nenhum controle de paginação é renderizado

Cenário: sem script
  Dado que o navegador está com JavaScript desligado
  Quando a tela de resultados é exibida
  Então os 68 cartões aparecem em sequência, na ordem apresentada

Cenário: voltar de um cartão não troca a página
  Dado que o operador abriu o cartão 34 na página 4
  Quando ele clica em "Voltar"
  Então a tela rola até o título dos resultados
  E a página corrente continua sendo a 4

Cenário: trocar de página devolve a lista ao topo
  Dado que o operador está na página 1 e rolou até o último cartão dela
  Quando ele clica em "próxima"
  Então os cartões 11 a 20 ficam visíveis
  E o primeiro cartão da página nova está na área visível

Cenário: expandir todas na página corrente
  Dado 68 cartões a 10 por página, com o operador na página 2
  Quando ele clica em "Expandir todas as análises"
  Então os 10 cartões da página 2 estão abertos
  E os cartões das outras páginas continuam como estavam

Cenário: os contratos do cartão continuam valendo
  Dado que o operador está em qualquer página
  Então cada cartão tem `id="resultado-N"` no próprio `details`
  E a numeração vai de 1 a 68 sem buraco
  E o "Voltar" de cada cartão aponta para "#resultados"

Cenário: análise sem nenhum cartão
  Dado uma análise sem conexões
  Quando a tela é exibida
  Então o bloco de resultados não é renderizado, como hoje
  E nenhum controle de paginação existe no documento
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 / RF-02 / RF-03 | **Must** | É o pedido literal: 10 por padrão, com 10, 20 e 30 |
| RF-04 | **Must** | Sem ela a feature remove conteúdo da análise — o que o adendo `018` recusa |
| RF-05 | **Must** | A contagem do topo é a leitura da análise; trocá-la por "10" seria dizer que a análise encolheu |
| RF-06 | **Must** | Uma paginação sem "onde estou" é uma lista que some |
| RF-08 | **Must** | Sem a volta à página 1, "página 3 de 3" mostra cartões que o operador não pediu |
| RF-09 | **Must** | É o único caminho de entrada em um cartão específico, e ele já existe no código |
| RF-11 | **Must** | O estado sem script tem de ser o estado atual (lista inteira), não uma tela vazia |
| RF-12 | **Must** | São contratos presos por teste, com prova de sensibilidade |
| RF-14 | **Must** | Reexecutar a análise a cada página custaria de 12 a 31 s por clique no arquivo real |
| RF-07 | **Should** | Melhora a leitura de análise pequena, sem bloquear nada |
| RF-13 | **Should** | Sem ela, trocar de página deixa o operador no meio do documento |
| RF-10 | **Should** | Restrita à página corrente por decisão de 2026-10-22; a feature entrega sem ela |
| Persistir a escolha entre análises | **Won't** | Decidido em 2026-10-22: não lembrar; exigiria armazenamento no navegador, que o sistema não tem |
| Paginar no servidor | **Won't** | A análise não é cacheada entre requisições: cada página custaria uma análise inteira |
| Paginar a lista de descartes | **Won't** | Decidido em 2026-10-22: só os cartões; descarte é match rejeitado, não pessoa analisada |

## 9. Esclarecimentos

### Sessão 2026-10-22

As cinco perguntas foram respondidas pelo operador, e as cinco respostas coincidiram com a
recomendação do documento.

- **Q:** Os descartes entram na paginação?
  **R:** Não — a paginação cobre só os cartões de conexão.
- **Q:** "Expandir todas as análises" abre só a página corrente ou todos os cartões da análise?
  **R:** Só os cartões da página corrente. A opção que também trocava o rótulo foi recusada, então
  o rótulo fica como está — e a diferença entre rótulo e alcance fica registrada em §10.
- **Q:** A escolha de 10, 20 ou 30 é lembrada na próxima análise?
  **R:** Não — toda análise começa em 10.
- **Q:** Que controles, e onde?
  **R:** No topo da lista: seletor, "anterior", "próxima" e os números das páginas.
- **Q:** Rótulo do seletor — "conexões" ou "pessoas"?
  **R:** "Conexões por página", um nome só na tela toda.

## 10. Lacunas

- 🟡 **O rótulo do botão promete mais do que ele faz.** "Expandir todas as análises" passa a abrir
  as dez da página corrente. A decisão de 2026-10-22 foi manter o rótulo; se incomodar na prática,
  o conserto é uma linha de texto ("Expandir as análises desta página").
- 🟡 **Densidade do controle.** O adendo `019` já registrou que o cabeçalho do cartão ficou denso.
  Com seletor, anterior, próxima e sete números, o controle ocupa uma linha inteira. Se pesar, o
  corte é a lista de números, mantendo anterior/próxima e "página X de Y".
- 🟡 **O `#resultado-N` ficou sem gerador.** Com a tabela do índice fora (adendo `019`), quem
  produz esse hash é a barra de endereços ou um recarregamento. O suporte continua valendo e é
  barato, mas a frequência de uso é baixa — vale medir antes de investir em polimento.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-22 | Sessão de esclarecimentos: 5 perguntas respondidas, as 3 dúvidas zeradas, `RN-10`/`RN-14` fechadas e `RN-15` acrescentada | reversa |
