# Requirements: grupos de triangulação — a evidência que vem de vários matches ao mesmo tempo

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O analisador hoje confronta **um match por vez** com a árvore: ele sabe dizer que Maria tem 45 cM e que o
caminho documental até ela não conflita com isso. O que ele não sabe — porque nunca teve o dado — é que
**Maria, João e Ana compartilham a mesma faixa do cromossomo 7**, o que é a evidência mais forte que existe
de um ancestral comum entre elas, e não de cada uma com o operador. Esta feature recebe o **CSV de
triangulação do GEDmatch** (uma linha por par de kits, com cromossomo e faixa B37) como entrada **opcional**
da Fase 3 — **sozinho ou junto com a análise completa**. Sozinho, entrega os grupos e quem os compõe; com a
árvore carregada, entrega também o desfecho de cada grupo, derivado dos cartões que a análise já produziu.
O grupo recebe um desfecho — **convergente**, **dividido**, **parcial** ou **sem ancestral documentado** — e a
tela passa a dizer onde existe um ancestral comum que a árvore **não** tem. Nada do que existe muda: o grupo
não cria cartão, não soma cM, não altera veredito e não afirma parentesco. A saída mais valiosa continua sendo
a negativa justificada — agora no nível do grupo.

> **Sem árvore não há painel.** A escolha de aceitar o arquivo sozinho (`D-01`, sessão de 2026-11-09) não
> transforma o bloco em dashboard: sem árvore ele mostra grupos, membros e faixa, e **nenhuma** estatística
> agregada (`RN-14`). O que o produto entrega é composição, não média.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#2` | Os três eixos não se contaminam; o DNA não altera o parentesco documental e o cM nunca é usado sozinho | 🟢 |
| `_reversa_sdd/domain.md#3.2` | A evidência genética é chaveada por **(nome, kit)**, e nenhum total é somado entre kits | 🟢 |
| `_reversa_sdd/domain.md#3.8` | Leitura tolerante do CSV: descartar sim, esconder não | 🟢 |
| `_reversa_sdd/domain.md#3.9` | A ordem de apresentação é documental primeiro; o código declara que não é ordem de confiança | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#Evidência genética` | `BR-D-12` a `BR-D-19`: a chave é (nome, kit), `SEM_KIT` tem espaço à esquerda, e `totals.cm` é `None` quando há mais de um kit | 🟢 |
| `_reversa_sdd/code-analysis.md#4.4` | `BR-D-08` a `BR-D-18`: as colunas são detectadas **por papel**, e o cM não é arredondado | 🟢 |
| `_reversa_sdd/code-analysis.md#7.1` | A fronteira de aplicação: `app.py` → `application/` → `core/`, com as portas por parâmetro | 🟢 |
| `_reversa_sdd/addenda/039-dna-sem-correspondencia.md` | O bloco "DNA sem correspondência na árvore" é **leitura derivada**: não cria cartão, não afirma parentesco | 🟢 |
| `_reversa_sdd/addenda/040-fonte-e-cobertura-do-arquivo.md` | A cobertura do arquivo é um **bloco de escopo-arquivo** exibido antes dos cartões | 🟢 |
| `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md` | Observação do arquivo tem lugar próprio e não se repete dentro de cartão | 🟢 |
| `.reversa/principles.md#I` | Dado real de DNA/GEDCOM nunca entra no versionamento; todo teste usa dado sintético | 🟢 |
| `.reversa/principles.md#V` | Toda suposição de genealogia genética cita a fonte; número sem origem é chute | 🟢 |

### Estado medido no código e no arquivo (2026-11-09)

Medições feitas nesta sessão, sobre a amostra real `SY3230889_triangulation_v2.csv` (1.650 linhas), que
permanece **fora do repositório**.

| Ponto | O que está lá hoje | Confidência |
|-------|--------------------|-------------|
| `src/core/genetic_evidence.py:60` (`detect_segment_columns`) | Detecta nome, cM, SNP, cromossomo e kit **por nome fixo**; `B37 Start` e `B37 End` **não** são reconhecidos — na amostra, `start` e `end` saem `None` | 🟢 medido |
| `src/core/genetic_evidence.py:92` | A coluna de kit é a **primeira** com > 50 % em `[A-Z]{1,3}\d{4,8}`; num arquivo de pares ela escolhe `Kit1 Number` **em silêncio** e perde o segundo kit | 🟢 medido |
| `src/core/genetic_evidence.py:114` | A coluna de e-mail é a **última** com `mail`; no arquivo de pares ela resolve `Kit2 Email` — um e-mail não identifica um par | 🟢 medido |
| `src/parsers/segmentos_gedmatch.py:117` | Sem coluna de nome, levanta `DnaCsvSemColunas("Colunas de Nome e cM não encontradas no CSV.")` — **o arquivo de triangulação é recusado hoje**, com mensagem genérica | 🟢 medido |
| Amostra real | 1.650 linhas, 351 kits, cromossomos 1–22 (sem X nem MT), UTF-8 **com BOM** (já removido na leitura), nenhum auto-par e nenhuma linha duplicada | 🟢 medido |
| Amostra real | Extensão das faixas: cM de 5,0 a 39,0; **788 de 1.650 linhas (47,8 %) abaixo de 10 cM** | 🟢 medido |
| Amostra real | **1.535 regiões** com sobreposição geométrica em ≥ 3 kits; apenas **60** têm todos os pares presentes, que viram **28 grupos maximais**, cobrindo **116 dos 351 kits** | 🟢 medido |
| Amostra real | A maior região é **chr20, 58.958.477–59.362.391 (0,40 Mb), 51 kits, 182 pares de 1.275 possíveis, cM de 5,2 a 10,4** — e **não** fecha | 🟢 medido |
| Amostra real | As faixas dos três pares não coincidem: delta de início com mediana de 1,46 Mb e máximo de 21,9 Mb; a interseção tem mediana de 11,2 Mb | 🟢 medido |
| Amostra real | **18 pares** têm dois segmentos distintos no mesmo cromossomo | 🟢 medido |
| Amostra real | **1.154 de 3.300** ocorrências de nome começam com `*` (`*Teresa`, `*G7`); **922** são de uma palavra só; **2** perderam o encoding na origem | 🟢 medido |

> **O que a amostra ensinou, e que a feature tem de respeitar:** sobreposição geométrica **não é**
> triangulação. Sem o teste de fechamento, o maior "grupo" do arquivo seria uma região de 0,40 Mb com 51
> kits — o oposto de 51 primos. É esse teste que separa evidência de coincidência, e é por isso que ele é
> regra de negócio, e não detalhe de implementação.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Genealogista Genético (única persona do sistema) | Saber quais matches formam um grupo com ancestral comum, e qual ramo da árvore cada grupo sustenta | Sobe o CSV de triangulação junto com o de matches e vê três kits sobre a mesma faixa do chr 7 sem nenhum caminho documental |
| Genealogista Genético | Distinguir um grupo real de uma região de acúmulo antes de investir pesquisa | Vê que 51 kits "compartilham" 0,40 Mb com cM baixo e que o bloco chama aquilo de acúmulo, não de parentesco |
| Operador que audita meses depois | Rever por que um ramo foi considerado corroborado ou contradito | Abre o grupo e lê quais kits o compõem, qual ancestral cada um aponta e qual foi o desfecho |

## 4. Regras de negócio novas ou alteradas

1. **RN-01: grupo de triangulação é um conjunto de ≥ 3 kits distintos cujas faixas, no mesmo cromossomo, têm
   interseção comum não vazia e cujos pares estão todos presentes no arquivo.** 🟢
   - Origem no legado: `_reversa_sdd/domain.md#2` (evidência não vira parentesco) e a medição da amostra
     (1.535 regiões geométricas → 60 fechadas).
   - Tipo: nova.
2. **RN-02: a região do grupo é a interseção das faixas, nunca a união e nunca uma tolerância fixa em pares de
   bases.** 🟢
   - Justificativa medida: as faixas divergem (delta de início com mediana de 1,46 Mb e máximo de 21,9 Mb);
     adotar a faixa de um par qualquer exibiria uma região que nenhum dos três compartilha.
   - Tipo: nova.
3. **RN-03: o piso de 10 cM não forma nem desfaz grupo.** Ele **marca** o par mais fraco do grupo. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.2` e `BR-D-17` — o piso é regra de **evidência por match**;
     aplicá-lo por linha fraturaria 18 dos 60 grupos fechados da amostra, e 47,8 % das linhas ficariam de fora.
   - Tipo: nova (delimita o alcance de uma regra existente).
4. **RN-04: o desfecho documental do grupo é derivado dos cartões que a análise já produziu**, sem segunda
   passagem de matching, **e só existe quando há árvore carregada**. 🟢
   - Os quatro desfechos: **convergente** (dois ou mais membros apontam para o mesmo ancestral comum),
     **dividido** (dois ou mais membros apontam para ancestrais distintos), **parcial** (parte dos membros tem
     caminho, parte não) e **sem ancestral documentado** (nenhum membro tem caminho).
   - Sem árvore, o grupo é apresentado **sem desfecho**, e o bloco declara que o desfecho depende da árvore
     (decisão `D-01`, sessão de 2026-11-09).
   - Origem no legado: `_reversa_sdd/addenda/039-dna-sem-correspondencia.md` (leitura derivada, sem criar cartão).
   - Tipo: nova.
5. **RN-05: a região de acúmulo é um alerta, e não um quinto desfecho** — ela pode coexistir com qualquer um
   dos quatro. O critério é **≥ 8 kits na mesma interseção e (extensão < 2 Mb ou cM máximo < 12)**. 🟡
   - O limite é **heurística declarada**, não publicação: ancora-se no único caso medido (51 kits, 0,40 Mb,
     cM de 5,2 a 10,4) e nos grupos fechados da amostra, que ficam entre 2,25 e 29,85 Mb
     (`.reversa/principles.md#V`).
   - Tipo: nova.
6. **RN-06: nenhum cM é somado entre pares.** O grupo informa o cM **de cada par** (mínimo e máximo) e a
   extensão da interseção em pares de bases. 🟢
   - Origem no legado: `BR-D-14` e `BR-D-19` — somar cM de amostras diferentes é o erro que o produto recusa.
   - Tipo: nova (reafirma uma proibição existente).
7. **RN-07: o membro do grupo sem cartão aparece com nome e kit, na mesma linguagem de "sem
   correspondência" que a tela já usa.** 🟢
   - Origem no legado: `_reversa_sdd/addenda/039-dna-sem-correspondencia.md`.
   - Tipo: nova.
8. **RN-08: um membro é identificado pelo kit.** O nome serve para chegar ao cartão; quando falta o kit, o
   casamento é pelo nome, e o aviso de identidade ambígua que já existe continua valendo. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.2` (chave (nome, kit)) e o aviso de identidade do cartão.
   - Tipo: nova.
9. **RN-09: o nome do GEDmatch é limpo antes do casamento com a árvore** — o `*` inicial é marcador do
   arquivo e não faz parte do nome. 🟢
   - Justificativa medida: 1.154 de 3.300 ocorrências começam com `*`.
   - Tipo: nova (a limpeza mora no adaptador do arquivo, que é quem conhece o formato; `norm_name` não muda — `ADR-07`).
10. **RN-10: as coordenadas só são agrupadas quando o build é declarado.** O cabeçalho precisa declarar
    `B37` (ou equivalente); sem declaração, o bloco **não agrupa** e diz por quê. 🟢
    - Justificativa: misturar builds corrompe a interseção sem deixar rastro; a amostra declara B37 no nome
      das colunas.
    - Tipo: nova.
11. **RN-11: dois segmentos do mesmo par no mesmo cromossomo são dois segmentos**, e a chave do agrupamento
    inclui as coordenadas. 🟢
    - Justificativa medida: 18 pares na amostra.
    - Tipo: nova.
12. **RN-12: o grupo é leitura derivada e não altera nada do que existe.** Não cria cartão, não muda cM,
    caminho, veredito, descartes nem o CSV de descartes. 🟢
    - Origem no legado: `.reversa/principles.md#II` e `_reversa_sdd/addenda/039-dna-sem-correspondencia.md`.
    - Tipo: nova.
13. **RN-13: a ordem de apresentação é determinística** — cromossomo em ordem natural, depois posição
    inicial, depois o conjunto de kits. 🟢
    - Origem no legado: `BR-D-63` (desempate determinístico) e `_reversa_sdd/domain.md#3.9`.
    - Tipo: nova.
14. **RN-14: sem árvore, o bloco não vira painel de métricas.** Ele mostra grupos, membros, faixa e cM por
    par; **não** calcula média, mediana, distribuição por cromossomo nem percentual. 🟢
    - Justificativa: número agregado sem decisão é o que o produto recusa (`.reversa/principles.md#V`); aceitar
      o arquivo sozinho não pode reintroduzir o painel pela porta dos fundos.
    - Tipo: nova.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Receber o CSV de triangulação como entrada **opcional** da Fase 3 — **sozinho ou junto com a análise completa** —, pela mesma porta de armazenamento e a mesma regra de reenvio do CSV de matches | Must | Enviado sozinho, produz o bloco sem desfecho; junto com a análise, produz o bloco com desfecho; sem ele, a tela não muda um byte | 🟢 |
| RF-02 | Distinguir as duas formas de CSV **pelas colunas**, e não pela extensão nem pelo nome do arquivo | Must | Um CSV de triangulação no campo de matches (e vice-versa) é recusado com mensagem que nomeia o campo correto | 🟢 |
| RF-03 | Ler o arquivo com a leitura tolerante existente, publicando encoding, separador, preâmbulo e linhas irregulares | Must | Arquivo em `latin-1` com `;` e preâmbulo é lido; as linhas irregulares são contadas e numeradas na tela | 🟢 |
| RF-04 | Detectar as colunas do par por papel: dois kits (número e nome), cromossomo, início e fim B37, cM | Must | `B37 Start`/`B37 End` e variantes são reconhecidos; sem os dois kits ou sem cM, o erro é acionável | 🟢 |
| RF-05 | Agrupar por cromossomo com interseção comum e **teste de fechamento**, devolvendo grupos maximais de ≥ 3 kits | Must | Na amostra, 1.535 regiões geométricas produzem 28 grupos; a região de 51 kits do chr20 **não** entra | 🟢 |
| RF-06 | Apresentar cada grupo com cromossomo, faixa de interseção em pb, cM mínimo e máximo dos pares, e a lista de membros com kit e nome | Must | A faixa exibida é a interseção; a tela não mostra a faixa de um par como se fosse a do grupo | 🟢 |
| RF-07 | Marcar o par mais fraco abaixo de 10 cM sem excluí-lo do grupo | Must | Grupo com um par de 6,7 cM aparece com a marca, e não desaparece | 🟢 |
| RF-08 | Classificar o desfecho documental a partir dos cartões já produzidos, **quando há árvore carregada**: convergente, dividido, parcial ou sem ancestral documentado | Must | Dois membros com o mesmo ancestral comum → convergente; ancestrais distintos → dividido; nenhum com caminho → sem ancestral documentado; misto → parcial; sem árvore → sem desfecho | 🟢 |
| RF-09 | Sinalizar região de acúmulo com critério declarado, sem transformá-la em desfecho | Should | A região de 51 kits do chr20 recebe o alerta, e o critério aparece escrito na tela | 🟡 |
| RF-10 | Listar, por grupo, os membros sem correspondência na árvore, com nome e kit | Must | O grupo "sem ancestral documentado" nomeia cada membro, e não apenas a contagem | 🟢 |
| RF-11 | Exibir o bloco **antes** dos cartões, no mesmo lugar dos blocos de escopo-arquivo, e nascer aberto | Must | O bloco é visível sem clique, e os cartões continuam fechados por padrão | 🟢 |
| RF-12 | Não alterar cartões, cM, caminhos, vereditos, descartes nem o CSV de descartes | Must | Nenhum cartão muda de valor por causa do arquivo novo; a lista de descartes é idêntica | 🟢 |
| RF-13 | Declarar, no próprio bloco, o que ele **não** faz: não soma cM, não cria vínculo, não prova parentesco | Must | O texto do bloco contém a negativa explícita, como o bloco 039 contém a dele | 🟢 |
| RF-14 | Recusar com mensagem acionável quando o arquivo não declara o build das coordenadas | Must | Arquivo sem `B37` no cabeçalho não agrupa, e o texto diz o que conferir | 🟢 |
| RF-15 | Manter a ordem determinística dos grupos e dos membros | Must | Duas execuções sobre o mesmo arquivo produzem a mesma ordem, independentemente da ordem das linhas | 🟢 |
| RF-16 | Exportar os grupos em CSV | Should | CSV com cromossomo, faixa, desfecho e kits, por rota própria, no regime do CSV de descartes | 🟡 |
| RF-17 | Limpar o `*` inicial do nome antes do casamento com a árvore | Must | `*Teresa` casa com `Teresa` do GEDCOM, e o par nome↔pessoa aparece no cartão | 🟢 |
| RF-18 | Permitir que o envio do CSV de triangulação dispense raiz e CSV de matches, sem produzir cartão | Must | O envio só com o arquivo devolve o bloco de grupos e a informação de que não há análise de conexão; nenhum cartão é criado | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | O custo cresce no máximo de forma log-linear com o número de linhas; nenhuma comparação de todos os pares com todos | A amostra tem 1.650 linhas e 351 kits; um desenho quadrático em 100 mil linhas seria inviável | 🟡 |
| Desempenho | O custo do bloco é medido com o arquivo real, não estimado | `.reversa/principles.md#III` e o hábito do projeto de medir antes de declarar | 🟢 |
| Reprodutibilidade | A ordem é total e determinística | `BR-D-63` fechou a mesma classe de defeito no matching | 🟢 |
| Memória | Nenhuma estrutura proporcional a pares×pares; os pares entram como arestas | O arquivo pode crescer; a lista de pares completos de um grupo de 51 kits já teria 1.275 arestas | 🟡 |
| Dependências | Nenhuma dependência nova de runtime | As bibliotecas já fixadas em `requirements.txt` bastam | 🟢 |
| Privacidade | Fixture **sintética** com as mesmas formas (BOM, `*`, dois segmentos por par, par incompleto, acúmulo); o arquivo real fica fora do repositório | `.reversa/principles.md#I` | 🟢 |
| Acessibilidade | Os selos do bloco seguem o contraste já preso por teste | `tests/test_estilo_da_tela.py` | 🟢 |
| Observabilidade | Erros de leitura seguem o registro existente, sem log novo por grupo | `_reversa_sdd/addenda/049-sistema-de-log.md` | 🟡 |
| Internacionalização | Todo texto ao operador em PT-BR | Contrato de mensagens do projeto | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: três kits fechados formam um grupo (RF-05)
  Dado um CSV de triangulação com A-B, A-C e B-C sobre a mesma faixa do cromossomo 7
  Quando a análise roda com um GEDCOM carregado
  Então a tela mostra um grupo com os três kits
  E a faixa exibida é a interseção das três
  E nenhuma faixa maior que a interseção é apresentada como sendo do grupo

Cenário: cadeia não é grupo (RF-05, RN-01)
  Dado um CSV com A-B e A-C, mas sem B-C
  Quando a análise roda
  Então A, B e C não formam grupo
  E o bloco informa que os pares não fecham

Cenário: região de acúmulo não vira parentesco (RF-09)
  Dado 51 kits sobre 0,40 Mb com cM entre 5,2 e 10,4 e apenas 182 dos 1.275 pares
  Quando a análise roda
  Então a região não é apresentada como grupo de triangulação
  E, se listada, recebe o alerta de acúmulo com o critério escrito

Cenário: grupo convergente (RF-08)
  Dado um grupo de três kits em que dois membros têm cartão apontando para o mesmo ancestral comum
  Quando a análise roda
  Então o desfecho é convergente
  E o grupo nomeia o ancestral comum
  E o texto diz que isso corrobora o ramo, sem provar o parentesco

Cenário: grupo dividido (RF-08)
  Dado um grupo em que um membro aponta para o ramo materno e outro para o paterno
  Quando a análise roda
  Então o desfecho é dividido
  E o grupo mostra os dois ancestrais e os membros de cada um

Cenário: grupo sem ancestral documentado (RF-08, RF-10)
  Dado um grupo em que nenhum membro tem caminho documental
  Quando a análise roda
  Então o desfecho é "sem ancestral documentado"
  E cada membro aparece com nome e kit
  E o texto diz que a evidência aponta um ancestral que a árvore não tem

Cenário: piso de 10 cM não apaga o grupo (RF-07)
  Dado um grupo cujo par mais fraco tem 6,7 cM
  Quando a análise roda
  Então o grupo continua existindo
  E o par fraco é marcado

Cenário: o CSV de triangulação no campo errado (RF-02)
  Dado um CSV de triangulação enviado no campo de matches
  Quando a análise roda
  Então a tela recusa com uma mensagem que nomeia o campo correto
  E nenhum cartão é produzido a partir dele

Cenário: sem o arquivo, nada muda (RF-01)
  Dado um operador que não envia o CSV de triangulação
  Quando ele roda a análise de DNA de hoje
  Então o resultado é idêntico ao de antes da feature
  E o bloco de grupos não existe no documento

Cenário: só o CSV de triangulação (RF-18)
  Dado um operador que envia apenas o CSV de triangulação, sem raiz e sem CSV de matches
  Quando o envio é processado
  Então o bloco de grupos aparece
  E cada grupo é apresentado sem desfecho documental
  E a tela informa que o desfecho depende da árvore carregada
  E nenhum cartão de conexão é produzido
  E nenhuma média, mediana ou distribuição é exibida (RN-14)

Cenário: build não declarado (RF-14)
  Dado um arquivo cujas colunas não declaram B37
  Quando a análise roda
  Então nenhum grupo é formado
  E o texto diz qual declaração falta

Cenário: dois segmentos do mesmo par (RN-11)
  Dado um par que aparece duas vezes no mesmo cromossomo com faixas distintas
  Quando o agrupamento roda
  Então os dois segmentos são tratados como segmentos distintos

Cenário: nome com asterisco (RF-17)
  Dado um membro cujo nome é "*Teresa" e cuja árvore tem "Teresa"
  Quando o membro é confrontado
  Então ele encontra o cartão de Teresa
  E o vínculo é apresentado com a identidade a confirmar que já existe

Cenário: leitura tolerante do arquivo (RF-03)
  Dado um CSV de triangulação em latin-1, com ponto e vírgula e duas linhas de preâmbulo
  Quando a análise roda
  Então o separador, o encoding e o cabeçalho são reconhecidos
  E a tela informa as linhas de preâmbulo ignoradas

Cenário: arquivo sem nenhum grupo fechado (RF-05)
  Dado um CSV de triangulação em que nenhum conjunto de três kits fecha
  Quando a análise roda
  Então o bloco informa que não há grupo
  E diz quantas regiões de sobreposição encontrou e que os pares não fecham

Cenário: o bloco não muda os cartões (RF-11, RF-12)
  Dado que o operador envia o CSV de triangulação junto com o de matches
  Quando a análise roda
  Então o bloco de grupos aparece antes dos cartões
  E os cartões têm os mesmos cM, caminhos, vereditos e descartes de quando o arquivo não foi enviado

Cenário: exportação dos grupos (RF-16)
  Dado um resultado com grupos
  Quando o operador pede o CSV dos grupos
  Então recebe um CSV com cromossomo, faixa, desfecho e kits
  E o CSV de descartes continua o de antes
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-05 / RN-01 — fechamento | **Must** | É o que separa triangulação de coincidência; sem isso a feature produz o oposto do que promete |
| RF-08 — desfecho documental | **Must** | É o produto: convergente, dividido, parcial ou sem ancestral |
| RF-06 — interseção, não união | **Must** | Reportar faixa errada é inventar dado |
| RF-12 — não alterar o existente | **Must** | O produto não pode ganhar uma feature que reescreve o que já afirma |
| RF-01 / RF-02 — entrada opcional e forma detectada | **Must** | Sem isso o arquivo certo não entra, e o errado entra calado |
| RF-04 / RF-14 — B37 e build declarado | **Must** | Coordenada sem build corrompe a interseção em silêncio |
| RF-03 — leitura tolerante | **Must** | O arquivo real tem BOM, preâmbulo e linha torta como qualquer export |
| RF-13 — o que o bloco não faz | **Must** | Mesma disciplina do bloco 039 |
| RF-07 — piso como marca | **Must** | Sem isso, 18 dos 60 grupos da amostra desapareceriam |
| RF-17 — limpar o `*` | **Must** | Sem isso, um terço dos nomes não casa |
| RF-18 — envio isolado | **Must** | É a decisão `D-01`: sem ele, o arquivo sozinho não entra |
| RN-14 — sem painel | **Must** | Impede o modo sem árvore de virar dashboard |
| RF-09 — acúmulo | Should | Depende de limiar declarado; a amostra mostra que é frequente |
| RF-16 — exportar | Should | Útil para auditar fora da tela, mas não é o produto |
| RNF de desempenho | Should | Precisa ser medido com o arquivo real |

## 9. Esclarecimentos

### Sessão 2026-11-09

- **Q:** O bloco de grupos exige a análise de DNA completa (raiz + GEDCOM), ou o CSV de triangulação sozinho já
  mostra os grupos?
  **R:** O arquivo sozinho já mostra os grupos. Decisão da lacuna `D-01`: `RF-01` e `RF-18` passam a prever o
  envio isolado, que produz o bloco **sem desfecho documental** e **sem cartão**; o desfecho (`RF-08`, `RN-04`)
  só existe com árvore carregada. Para o modo isolado não virar o painel de métricas que o produto recusa, a
  `RN-14` proíbe estatística agregada.
- **Q:** Qual critério define "região de acúmulo" e evita chamar 51 kits de parentesco?
  **R:** ≥ 8 kits na mesma interseção **e** (extensão < 2 Mb **ou** cM máximo < 12). Decisão da lacuna `D-02`:
  é heurística declarada, ancorada no caso medido (51 kits, 0,40 Mb, 5,2–10,4 cM) e nos grupos fechados da
  amostra (2,25–29,85 Mb). A `RN-05` registra o número e a natureza da heurística.
- **Q:** O export nativo do GEDmatch, com o kit raiz numa das colunas, entra no escopo?
  **R:** Fora do escopo da v1. Decisão da lacuna `D-03`: a v1 lê o formato consolidado de pares (`Kit1`/`Kit2`,
  sem o kit raiz). Se um export nativo for enviado, o aplicativo **não o distingue** e o kit raiz entra como
  membro — é a limitação declarada abaixo. Um caso de teste próprio para o formato nativo fica para uma
  próxima feature.
- **Q:** Em que ordem os grupos aparecem no bloco?
  **R:** Cromossomo em ordem natural e, dentro dele, posição inicial — a `RN-13` fica como está.

## 10. Lacunas

Nenhuma dúvida aberta: as três da versão inicial foram resolvidas na sessão de 2026-11-09.

**Limitação declarada (não é dúvida):** a v1 não distingue o export consolidado do nativo. Um arquivo que
traga o kit raiz em algumas linhas produzirá grupos que incluem esse kit como membro, e o aplicativo não tem
como detectar isso pela estrutura do arquivo. O bloco declara o formato esperado; a distinção fica para uma
próxima feature.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-09 | Versão inicial gerada por `/reversa-requirements`, ancorada na amostra real medida nesta sessão | reversa |
| 2026-11-09 | `/reversa-clarify`: `D-01` (grupos sem árvore, com `RF-18` e `RN-14`), `D-02` (limiar de acúmulo), `D-03` (export nativo fora da v1) e ordem dos grupos — 3 dúvidas resolvidas | reversa |
