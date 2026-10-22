# Análise das planilhas do Projeto DNA de Sergipe

**O que é este documento.** Leitura das duas planilhas do projeto de DNA (registro de IDs FamilySearch e
planilha de doadores), extração das regras de negócio embutidas nelas, confronto com o que o Analisador
Genealógico já faz, e proposta do que aproveitar — o que copiar, o que adaptar e o que **não** copiar.

**Arquivos analisados**

| Arquivo | Abas | Volumetria |
| --- | --- | --- |
| `IDs_FamilySearch_Projeto_DNA_Sergipe.xlsx` | `IDs e vínculos`, `IDs únicos` | 504 registros, 410 IDs distintos, 251 pessoas |
| `Projeto DNA de Idosos de Sergipe.xlsx` | `SY3230889-GEDmatch` | 504 linhas (304 com nome), 59 colunas, 22 de cromossomo |

**Cotejado com**: `src/` (código atual, executado com o `.venv`), as árvores GEDCOM de
`D:\dados-genealogicos\Arquivos  GEDCOM\` e os exports CSV do mesmo diretório.

---

## 0. Decisão de escopo (2026-10-22) — leia antes das seções 7 e 8

Decisão do operador: **as entradas do app são sempre GEDCOM + CSV como os de `src/uploads`**, e o ID do
FamilySearch **não** é uma boa base de trabalho. Isso muda o que se aproveita das planilhas:

| Item da seção 7 | Estado depois da decisão |
| --- | --- |
| **F1** — Ponte FamilySearch | **fora de escopo** |
| **F2** — Vínculo declarado | **fora de escopo** (dependia de F1 e do registro de IDs) |
| **F3** — Adapter do arquivo de projeto | **fora de escopo** enquanto a entrada for o CSV de segmentos |
| **F5** — Triangulação entre fontes | **reduzido a vocabulário**: a comparação entre laboratórios já existe (um kit por linha) |
| **F4** — Qualidade da medida | **mantido** |
| **M1** — Vocabulário | **mantido — e virou o item de maior retorno** (campo `Source`) |
| **M2** — Corte declarado | **mantido**, como "o arquivo não declara o corte" |
| **M3** — PII | **reduzido**: o CSV de segmentos não traz e-mail |
| **F6** — Mapa de cromossomos | **adiado**: o card já lista os cromossomos |

**O que sobrevive das planilhas**, medido no arquivo real `Famílias_Sergipanas.csv` (617 linhas, 456 pessoas,
o tipo de arquivo que o operador envia):

| Medida | Valor |
| --- | --- |
| Valores distintos em `Source` | **45** para **~11 laboratórios** |
| Células de `Source` sem laboratório | **50** — 40 texto de formulário, 8 nome de projeto, 1 haplogrupo, 1 não reconhecida |
| Segmentos abaixo do piso de 10 cM | **456 de 617 (74%)** |
| Pessoas sem bloco ≥ 15 cM | **402 de 456 (88%)** |
| Pessoas com menos de 900 SNPs somados | **232 de 456 (51%)** |
| Total ≥ 15 cM mas nenhum bloco ≥ 15 cM | **58 de 112** |
| Mediana de cM por pessoa | **9,05** |
| Cromossomos cobertos / com X | **22 / 0** |

O pacote mínimo revisado — **um só**, sem dependência de ID, link ou roster:

1. **P1 — Vocabulário de fonte.** Normalizar `Source` (45 grafias → 11 laboratórios) e tratar
   `Outro (insira o nome abaixo)`, `Selecione uma empresa ou fonte`, `-`, haplogrupo e nome de projeto como
   *não declarada*, preservando o texto original para exibição.
2. **P2 — Painel do arquivo.** Antes dos cartões: linhas, pessoas, kits, laboratórios, cromossomos, mediana,
   % abaixo do piso, % sem bloco de 15 cM, e as frases que explicam cada número.
3. **P3 — Estado da medida no cartão.** `robusta | parcial | insuficiente`, com os três números (total, maior
   segmento, SNPs) e a ressalva "qualidade da medida, não do parentesco".
4. **P4 — Corte não declarado.** Uma frase no painel: ausência de um nome no arquivo não é ausência de
   parentesco.

A maquete de tela está em
[`simulacao-sem-familysearch.html`](./simulacao-sem-familysearch.html) — HTML autocontido, com os números
acima, para abrir no navegador.

**O que se perde com a decisão, sem rodeio:** a ponte entre a planilha do projeto e a árvore, o gancho de
citação (o ID), e o roster como entrada. As seções 7 e 8 ficam como registro da análise que levou até aqui; a
recomendação vigente é a desta seção.

---

## 1. Resumo executivo

As duas planilhas não são "anexos" do projeto: elas são **o acervo operacional** do projeto de DNA — quem
foi testado, a que tronco pertence, quais ancestrais já estão identificados no FamilySearch, e quanto cada
um compartilha com quem. O Analisador Genealógico hoje não consegue ler nenhuma das duas.

Três achados que mudam a decisão de roteiro:

1. **O formato que o projeto produz é ilegível pelo app.** Rodando os parsers reais contra o CSV exportado
   da planilha de doadores (`Projeto DNA de Idosos de Sergipe.csv`, 504 × 58), a análise morre em
   `DnaCsvSemColunas: Colunas de Nome e cM não encontradas no CSV` — não existe coluna `cM`; o dado está
   espalhado em `Total Match`, `Maior Match`, `SNPs` e 22 colunas de cromossomo. Os **304 doadores reais**
   (o público-alvo do projeto) ficam fora do produto, enquanto o export de um único kit
   (`adriano_santos_SY3230889.csv`) entra sem um único aviso — 484 evidências, 492 segmentos.
2. **A ponte FamilySearch já existe fisicamente e está desligada nas duas pontas.** As árvores
   `Adriano_Santos*.ged` trazem `_FSFTID` em **100% dos indivíduos** (19.403 na `v3`), e as planilhas
   citam **805 IDs distintos**. O código não lê `_FSFTID` em lugar nenhum (varredura em `src/`: zero
   ocorrências). A junção planilha ↔ GEDCOM resolve 48 IDs hoje; o resto não é ausência de dado, é ausência
   de código.
3. **Metade das regras da planilha é aproveitável; a outra metade contradiz os invariantes do projeto.**
   `Are your parents related?` responde `"Sim"` para qualquer cM compartilhado (`IF(BA>0,...)`) — 67 linhas
   — e `Alto Grau de Confiabilidade` é um selo de parentesco disfarçado de medida de qualidade. Copiá-las
   violaria a regra "o cM não afirma parentesco". Já os **limiares** por trás delas (SNPs ≥ 900,
   maior segmento ≥ 6 cM, total ≥ 15 cM), a **matriz de cromossomos**, a **triangulação entre laboratórios**
   e o **corte declarado de cada lista** são regras boas que o app não tem.

---

## 2. Método e o que foi medido

- **Planilhas**: `openpyxl` com `data_only=False` (fórmulas, formatação condicional, validações) e
  `data_only=True` (valores em cache). Nenhum número deste documento vem de estimativa: todos saíram de
  contagem sobre as células.
- **GEDCOM**: índice próprio `_FSFTID → (nome, nascimento, óbito, sexo)`, para medir a cobertura real da
  junção.
- **Código atual**: execução dos parsers de produção (`parsers.csv_ingest`, `core.genetic_evidence`,
  `parsers.segmentos_gedmatch`) contra os dois CSV do diretório, com o Python do `.venv` (3.14.6).
- **Texto de parentesco**: protótipo de gramática (~50 linhas) para medir se a coluna `Generation` é
  interpretável. Resultado: **107 de 108 frases (99,1%)**. Os números de reprodutibilidade estão no Anexo B.

**Convenção de leitura**: o que é **medido** está marcado com números; o que é **inferência** está escrito
como inferência. O projeto é rigoroso nessa distinção e este documento segue a mesma regra.

---

## 3. Inventário dos arquivos

### 3.1 `IDs_FamilySearch_Projeto_DNA_Sergipe.xlsx`

Uma tabela de **vínculos declarados**: cada linha diz "esta pessoa da planilha tem este ID do FamilySearch,
nesta posição da árvore".

| Coluna | Conteúdo | Observação |
| --- | --- | --- |
| `ID FamilySearch` | 504 valores | 100% no formato `XXXX-XXX` |
| `Pessoa/registro na planilha` | 251 valores distintos | nome completo, apelido (`HB`, `MD`) ou rótulo |
| `Relação/observação registrada` | texto livre | **504/504** contêm ao menos um ID |
| `Linha na aba original` | inteiro | aponta para planilha que **não está no arquivo** |
| `Link direto do perfil` | URL | 504/504 no padrão `/tree/person/details/{ID}` |
| `Link para pesquisar por ID` | URL | 504/504 idênticas (constante) |

Aba `IDs únicos`: 410 IDs, deduplicação exata da primeira aba (conferido: conjunto igual, zero faltantes).

O vocabulário da coluna de relação é **controlado e pequeno**: `pai` (119), `mãe` (102), `avô materno` (69),
`avô paterno` (65), `avó paterna` (64), `bisavó materna` (63), `bisavô paterno` (62), `bisavô materno` (61),
`bisavó paterna` (58), `avó materna` (56), mais variações numeradas (`bisavô materno 1`, `... 2`), localidade
(`campo grande e sta. cruz`) e estado civil (`falecidos`). O rótulo pode vir dentro de parênteses ou solto:
`Avó materna (96YH-ZZ3), avô materno (LCZV-W47)...` e `Bisavó Paterno LDQC-4Q5  Tataravô paterno 2H72-T7Q`
convivem no mesmo arquivo.

**100 linhas declaram o par (Pai)+(Mãe)** — ou seja, o arquivo descreve **casais**, não só indivíduos.

### 3.2 `Projeto DNA de Idosos de Sergipe.xlsx`

Uma linha por **doador** (não por par de matches), com quatro grupos de dados:

| Grupo | Colunas | Preenchimento |
| --- | --- | --- |
| Identificação do doador | `Name`, `Kit Number`, `Contact`, `Birth`, `Age`, `Sex`, `Country/State/City`, `E-mail` | 304 linhas; `Age` calculada por `DATEDIF` |
| Ancestrais no FamilySearch | `Father's Side`, `Mother's Side`, `Parental Connection`, coluna sem título (S/T), `Direct Descent`, `Name of Descendant`, `Generation`, `Surnames` | 495 IDs distintos citados |
| Evidência genética | `Kit Shared = 14 cM`, `Shared = 6 cM`, `MRCA`, `Chr1..Chr22`, `Chr's`, `Total Match`, `Maior Match`, `SNPs`, `Total Match Shared`, `Largest Match Shared` | 252 linhas com SNPs; 248 com algum cromossomo |
| Triangulação e veredito | `Validation Match Shared For 4`, `Are your parents related?`, `Genera Total Match`, `MyHeritage Total Match`, `Final Result of Analysis` | 43 regras de formatação condicional |

**Estado real da base**: 200 linhas vazias (só fórmulas), restando **304 doadores**; `Age` = 0 em 61 linhas
(sem data); três sentinelas distintas para ausência (`Desconhecido`, `Não encontrado`, `Não informado`) mais
célula vazia; `State` com 22 valores, incluindo `Açores` (não é UF), `Espírito Santos`, `Santa Cararina`;
`Portugual` (grafia errada) na coluna `Country`, e `Açores` na coluna `State` — a coluna de UF recebeu
região e país.

**Troncos de descendência direta** — a coluna `Direct Descent` tem exatamente três valores não vazios:

| ID | Doadores ancorados |
| --- | --- |
| `K8V2-14T` | 48 |
| `G19G-2KR` | 37 |
| `G1Z5-SM9` | 23 |
| **Total ancorado** | **108 de 304 (35,5%)** — 196 (64,5%) sem âncora |

Os três IDs também são destacados por regra de formatação condicional (colunas U e W) — são as âncoras que
o próprio projeto trata como especiais.

---

## 4. Regras de negócio embutidas

Cada regra abaixo foi lida **da planilha** (fórmula, rótulo, vocabulário ou padrão de preenchimento), não
inventada. A coluna "Destino" diz o que fazer com ela no Analisador.

| Código | Regra | Onde está na planilha | Destino |
| --- | --- | --- | --- |
| **RN-P01** | **A identidade é o ID do FamilySearch, não o nome.** O nome é rótulo; o ID é chave. 94 repetições de ID em 504 linhas são legítimas (mesma pessoa, vários vínculos). | col. A + aba `IDs únicos` | **Aproveitar integralmente** |
| **RN-P02** | **Todo vínculo tem posição na árvore**: grau + lado (`avô paterno`, `bisavó materna`) + ordem entre irmãos do mesmo grau (`bisavô materno 1/2`). Nas colunas estruturadas do arquivo 2 o **grau não existe**: `Father's Side` pode conter o pai de um doador e o avô paterno de outro. | col. C + parênteses; colunas Q/R | **Aproveitar, com parser** |
| **RN-P03** | **O vínculo pode vir em frase livre** ("O esposo da prima quarta de meu bisavô") e a frase tem gramática: `[artigo] relação [de possessivo referência]`, com composição (cônjuge de, filho de, neto de, primo de grau N). | col. `Generation` (66 frases distintas) | **Aproveitar, com parser** |
| **RN-P04** | **Pai e mãe são declarados como par**, formando a unidade parental do doador. | 100 linhas com `(Pai)`+`(Mãe)` | **Aproveitar** |
| **RN-P05** | **Existe uma lista canônica de IDs** (aba `IDs únicos`) que serve para gerar link de perfil. | aba 2 | **Aproveitar** |
| **RN-P06** | **Um doador = um kit = uma linha.** Os 304 nomes não se repetem; o kit identifica o doador. | `Name` + `Kit Number` | **Aproveitar** (contrato de importação) |
| **RN-P07** | **A mesma pessoa pode ter medida em mais de um laboratório** (GEDmatch, Genera, MyHeritage) — medidas independentes, nunca somadas. | `Total Match Shared`, `Genera Total Match`, `MyHeritage Total Match` | **Aproveitar como confronto entre fontes** |
| **RN-P08** | **Cada coluna veio de uma lista com corte próprio, e o corte está no cabeçalho**: `Kit Shared = 14 cM`, `Shared = 6 cM`, `Kit Number = 16 cM`, `Eurogenes ... = 3.0 cM if no Shared`. Ausência é "não retornado por essa lista", não "não existe". *(Inferência a confirmar com o autor: os quatro rótulos leem-se como cortes de quatro buscas diferentes.)* | cabeçalhos B–E | **Aproveitar — é a mesma tese de `sem_correspondencia`** |
| **RN-P09** | **Pisos de qualidade do segmento**: SNPs ≥ 900, total ≥ 15 cM, maior segmento ≥ 6 cM, e uma faixa de "total compartilhado" < 500 vs < 900. | fórmula de `Final Result of Analysis` | **Aproveitar os limiares; recusar o selo** |
| **RN-P10** | **O cromossomo é a unidade de evidência**: 22 colunas, e o total deve ser a soma delas. | `Chr1..Chr22` + `Total Match` | **Aproveitar + criar checagem de consistência** |
| **RN-P11** | **O doador é ancorado a um tronco** (3 âncoras), o que permite comparar doadores do mesmo ramo. | `Direct Descent` | **Aproveitar (triangulação por tronco)** |
| **RN-P12** | **A idade é derivada da data de nascimento** (coorte de idosos, 78–97 anos), e é ela que decide se o doador pode estar vivo. | `Birth` + `Age` | **Aproveitar** (alimenta `janela_de_vida`) |
| **RN-P13** | **Veredito de confiabilidade em 4 estados**: `Informações Ausentes`, `Alto Grau de Confiabilidade`, `Analisar com Atenção`, `Possível Falso Positivo`. | `Final Result of Analysis` | **Adaptar (renomear e reposicionar)** |
| **RN-P14** | **Lacuna de dado é sinalizada visualmente** — 43 regras destacam "Não encontrado", "Desconhecido", "Não informado" e os 3 IDs de tronco. | formatação condicional | **Aproveitar como painel de lacunas** |

### 4.1 A regra de veredito, lida da fórmula

```
=IF(OR(AX=0, AY=0, AZ=0), "Informações Ausentes",
  IF(AND(AZ>=900, AX>=15, BA<500), "Alto Grau de Confiabilidade",
    IF(AND(AZ>=500, AX>=6, BA<900), "Analisar com Atenção", "Possível Falso Positivo")))
```
onde `AX` = total de cM (`SUM` dos cromossomos), `AY` = maior match, `AZ` = SNPs, `BA` = total compartilhado.

Distribuição em cache: **109** Alto Grau, **102** Analisar com Atenção, **56** Informações Ausentes,
**36** Possível Falso Positivo.

Duas coisas a separar nessa fórmula:

- **O que ela mede de verdade** é a *robustez do segmento*: quantos SNPs sustentam a chamada e qual o maior
  bloco contíguo. Isso é qualidade de **evidência**, não de parentesco.
- **O que o rótulo sugere** é que existe um parentesco confiável. `Alto Grau de Confiabilidade` ao lado de um
  nome lê-se como "este parentesco é confiável" — e é exatamente o que o projeto proíbe afirmar a partir do
  cM. O nome tem de mudar, e o lugar na tela também (ver F4).

---

## 5. Defeitos e riscos das regras (o que **não** importar como está)

| Código | Defeito | Evidência medida | Consequência se for importado |
| --- | --- | --- | --- |
| **D-01** | `Are your parents related?` = `IF(BA>0,"Sim","Não")`. BA é o cM compartilhado com o kit de referência, não um trecho de homozigose. | 67 linhas "Sim", 236 "Não" | Diria que os pais de 67 doadores são parentes sem nenhuma evidência de ROH |
| **D-02** | `Validation Match Shared For 4` = `BA*4`, sem norma, fonte ou uso declarado. | 67 valores não nulos, de 35,6 a 601,6 | Número sem significado viraria "validação" |
| **D-03** | `Maior Match` não é derivável dos cromossomos; a linha 2 usa `SUM` em vez de `MAX`. | 29 linhas com divergência entre `AY` e o máximo dos cromossomos | Total e maior se confundem, e o piso de 6 cM deixa de valer |
| **D-04** | 200 linhas vazias com fórmulas produzem "Informações Ausentes" (56 casos). | 200 de 504 linhas sem nome | "Ausente" passa a significar "linha em branco" |
| **D-05** | Três sentinelas para ausência + célula vazia. | 507 células `Desconhecido` | Contagem de lacuna fica impossível |
| **D-06** | `State` recebe região (`Açores`) e `Country` recebe grafia errada (`Portugual`); UFs com erro (`Espírito Santos`, `Santa Cararina`). | 22 valores em `State` | Filtro geográfico quebra silenciosamente |
| **D-07** | O registro (arquivo 1) e as colunas Q/R/S/U (arquivo 2) **não são a mesma base**: 100 IDs em comum, **310 só no registro**, **395 só na planilha**. | conjunto: 805 IDs na união | Nenhum dos dois é fonte única; importar um só perde metade |
| **D-08** | A árvore unificada perdeu a ponte: `Arvore_Unificada_Oficial_V1_2.ged` tem ≈35,5 mil pessoas (35.459 na variante crua, 35.470 na `Tratado`) e **zero** `_FSFTID`; as `Adriano_Santos*.ged` têm em 100% dos indivíduos. | junção: 48 de 805 IDs | A junção parece inviável quando o problema é o arquivo errado |
| **D-09** | `Linha na aba original` aponta para planilha ausente do arquivo. | 504 valores órfãos | Rastreabilidade prometida e não cumprida |
| **D-10** | `Chr's` mistura inteiro e texto (`20-20`). | 135 inteiros, 169 textos | Soma silenciosamente errada em planilha |
| **D-11** | Idade `0` quando não há data; no CSV a idade vem como texto (`'86 '`). | 61 linhas | Doador de 0 ano entra na janela de vida |
| **D-12** | 304 registros com telefone e e-mail de idosos, em app **sem autenticação**. | `Contact` + `E-mail` | Exposição de PII a qualquer um com acesso à porta |

### 5.1 O cruzamento que só aparece juntando os dois arquivos

O caso mais instrutivo, medido:

- O registro diz que `LB4M-994` é **avô paterno** de Sandro Stéfano Sá Azevedo e Walden Alexey Sá Azevedo,
  e que o **avô materno** deles é `G7WV-FKW`.
- Na planilha de doadores, os dois têm `LB4M-994` na coluna do lado paterno **e também na do lado materno** —
  o mesmo acontece com Kátia Georgia Sá Azevedo e Mário Alberto de Azevedo: **4 doadores**, um único ID em
  ambos os lados.

Isso não é implex: é a coluna materna repetindo o ID paterno (ou o registro está errado). Nenhum dos dois
arquivos, olhado sozinho, mostra o problema — e o app não tem como mostrar, porque não lê nenhum dos dois.
É a demonstração mais curta de por que F1+F2 valem o esforço: **a contradição está entre os arquivos, não
dentro deles.**

---

## 6. O que o projeto já tem × o que a planilha oferece

| Capacidade | Hoje no Analisador | Coberto pela planilha | Lacuna |
| --- | --- | --- | --- |
| Evidência por (pessoa, kit), sem somar kits | **Sim** — `core/genetic_evidence` | parcialmente | formato da planilha não entra |
| cM → conjunto de relações (SCP 4.0) | **Sim** — `core/relationship_hypotheses` | — | OK |
| Confronto em 4 estados | **Sim** — `core/evidence_comparison` | — | OK |
| Viabilidade temporal em 3 estados | **Sim** — `core/validator` | RN-P12 (idade) | idade do doador não entra |
| Profundidade documental × MRCA do kit | **Sim** — `core/profundidade_do_caminho` | RN-P03 (geração declarada) | declarado não é confrontado |
| Endogamia / tronco comum | **Sim** — `core/endogamia` | RN-P11 (troncos) | tronco do projeto não entra |
| Não achado ≠ não existe | **Sim** — `core/sem_correspondencia` | RN-P08 (corte declarado) | corte do arquivo não é lido |
| Identidade por ID externo (FamilySearch) | **Não** — zero ocorrências de `_FSFTID` | RN-P01/P05 | **maior lacuna** |
| Vínculo declarado estruturado | **Não** | RN-P02/P03/P04 | **segunda maior lacuna** |
| Triangulação entre laboratórios | **Não** — 1 fonte por linha | RN-P07 | lacuna |
| Mapa de cromossomos | **Não** (só lista de cromossomos) | RN-P10 | lacuna visual |
| Qualidade/cobertura do arquivo | **Não** (só avisos pontuais) | RN-P09/P14 | lacuna |

O diagnóstico em uma frase: **o app sabe cruzar um arquivo de matches com uma árvore; não sabe quem são os
doadores, de que tronco vêm, nem a que ancestral cada vínculo declarado se refere.**

---

## 7. O que aproveitar e aplicar

Seis funcionalidades e três melhorias, ordenadas por relação custo/benefício. Cada uma diz **onde encaixa**
na arquitetura atual (borda → aplicação → núcleo → portas) para não furar a separação que o projeto mantém.

### F1 — Ponte FamilySearch (`_FSFTID` ↔ planilhas)

**Problema.** Os IDs estão no GEDCOM e nas planilhas, e o app não os vê. Hoje a junção resolve 48 de 805
IDs por falta de código, não de dado.

**Proposta.**
- `parsers/gedcom_parser` passa a expor um **índice** `FSFTID → xref_id`, construído ao lado da árvore
  (não dentro da tupla — ver Riscos).
- Novo `core/ponte_familysearch` (funções puras): resolve ID → pessoa, devolve `encontrado | ausente |
  ambíguo`, e monta o link canônico `https://www.familysearch.org/tree/person/details/{ID}`.
- Tela: cada pessoa do caminho documental que tenha `_FSFTID` ganha link para o perfil; o bloco de
  observações recebe a cobertura ("48 de 805 IDs citados têm perfil nesta árvore").
- Quando a árvore não tem nenhum `_FSFTID`, um aviso de arquivo explica que a ponte não pode ser usada
  **naquele arquivo** (caso da árvore unificada) — e não que o vínculo não existe.

**Contrato.** `{"id": "K8V2-14T", "estado": "encontrado", "xref_id": "I123", "nome": "...", "link": "..."}`

**Aceite.** (a) 19.403 de 19.403 IDs indexados na `v3`; (b) árvore unificada produz aviso, não erro;
(c) nenhum caminho existente muda de resultado (paridade).

**Custo medido (e onde ele não está).** Índice `_FSFTID` sobre a árvore já carregada: **0,058 s** para
19.403 entradas. Carregar a mesma árvore: **52,3 s**. A ponte é praticamente gratuita — o custo é o
`carregar_arvore` que já existe e já se repete a cada `POST` (ver README, "O ciclo de uma requisição"). Isso
fixa uma decisão de escopo: F1 **não** abre o arquivo de novo; constrói o índice na mesma passagem em que a
árvore é montada.

**Impacto alto · esforço médio.** É pré-requisito de F2 e F6.

### F2 — Vínculos declarados: parser + validação de posição

**Problema.** O registro declara "avô paterno = LCZV-W47" e o app não sabe o que fazer com isso. Pior: as
colunas estruturadas **achatam graus diferentes no mesmo campo** (o mesmo campo guarda o pai de um doador e o
avô paterno de outro) e aceitam o mesmo ID nos dois lados — os 4 doadores da seção 5.1. Nenhum dos arquivos,
sozinho, revela isso.

**Proposta.**
- `parsers/vinculos_declarados` lê a coluna de relação e devolve
  `(grau, lado, ordem, id, texto_original)`, com vocabulário fechado e tolerância a variações.
- `core/parentesco_declarado` (puro) transforma **texto livre** em cadeia de passos, com a mesma gramática
  medida: `cônjuge`, `primo(grau)`, `tio_avô`, `descendente(n)`, `referência(gerações)`.
- `core/validacao_de_slot` compara o declarado com o documental: `avô paterno` deve estar a 2 saltos pelo
  lado do pai. Divergência vira **aviso de cartão** (como `mrca_divergente`), nunca reescrita do GEDCOM.

**Números que sustentam a viabilidade.** 108 frases não vazias, 66 distintas, **107 interpretadas (99,1%)**
por uma gramática de ~50 linhas; 6 casos de afinidade (`esposo da...`); referências de 0 a 6 gerações
acima do doador; graus de primo de 2 a 15 mais "distante". O único caso não interpretado é um erro de
digitação (`terceito`), que um mapa tolerante resolve.

**Invariante preservado.** O declarado é **declarado**: entra como hipótese confrontada, nunca como
parentesco documental. `VALIDADO` continua sendo ausência de contradição.

**Aceite.** (a) ≥ 99% das frases atuais interpretadas; (b) frase não interpretada **não** impede a análise —
vira observação com o texto original; (c) `esposo da` marca afinidade e a validação temporal devolve
`INCONCLUSIVO`, como já faz hoje para afinidade no caminho; (d) os 4 doadores da seção 5.1 aparecem como
divergência entre arquivos, com os dois IDs citados.

**Impacto alto · esforço médio-alto.** É a funcionalidade nova de maior valor genealógico.

### F3 — Adapter do arquivo de projeto (doadores e evidência multi-fonte)

**Problema.** O arquivo que o projeto produz (`Projeto DNA de Idosos de Sergipe.csv`) não entra: sem coluna
`cM`, a análise aborta. 304 doadores fora.

**Proposta.**
- `parsers/arquivo_do_projeto`: reconhece **assinatura de colunas** (não nome fixo): presença de
  `Kit Number` + (`Total Match` ou `Maior Match` ou `SNPs`) + colunas `Chr\d+` → é arquivo de projeto, não
  lista de matches.
- Traduz para o contrato que `core/genetic_evidence` já consome, com campos a mais por evidência:
  `fontes` (lista), `cromossomos_cm` (mapa), `pisos_declarados` (corte de cada lista), `tronco`.
- **Nunca somar** entre fontes nem entre kits: cada fonte vira um bloco de evidência próprio, exatamente
  como o código já faz com múltiplos kits (`SEM_KIT`, `multiplos_kits`).
- Checagem de consistência nova: **total declarado × soma dos cromossomos** (29 linhas falham hoje) e
  **maior declarado × máximo dos cromossomos**. Divergência = aviso de arquivo, sem corrigir o dado.

**Aceite.** (a) o CSV de 504 × 58 entra e produz 304 evidências; (b) nenhuma soma entre laboratórios;
(c) as 29 inconsistências aparecem como aviso com o número da linha.

**Impacto alto · esforço médio.** Sem ele, F4/F5/F6 não têm dado.

### F4 — Painel de qualidade da evidência (substitui o "Final Result")

**Problema.** O veredito em 4 estados é útil como *diagnóstico do dado*, mas o rótulo atual promete
parentesco. E o app já tem **dois eixos de veredito** (confronto e viabilidade); um terceiro selo no cartão
inflacionaria a tela.

**Proposta.** Transformar a regra em **cobertura do arquivo**, no bloco de fonte — não no cartão:
`evidência completa | parcial | insuficiente | sem dado`, calculada com os pisos da RN-P09, sempre
acompanhada dos números que a produziram (SNPs, total, maior segmento) e da frase "qualidade da medida, não
do parentesco".

**Aceite.** (a) o estado aparece **fora** do cartão de confronto; (b) o texto não usa "confiável" nem
"falso positivo" para o vínculo; (c) cada estado é reproduzível a partir dos números exibidos.

**Impacto médio-alto · esforço pequeno.**

### F5 — Triangulação entre fontes

**Problema.** O app tem `source` por linha e nunca compara; a planilha tem GEDmatch + Genera + MyHeritage
para as mesmas pessoas.

**Proposta.** Um bloco "fontes" no cartão: uma linha por laboratório, com cM e maior segmento; quando duas
fontes medem a mesma pessoa, `concordante | divergente` (diferença > 20% do menor valor) — sem somar, sem
média, sem escolher "a melhor".

**Aceite.** (a) dois kits da mesma pessoa continuam em cartões separados; (b) divergência vira aviso, nunca
silêncio; (c) nenhuma tela mostra a soma entre fontes.

**Impacto médio · esforço médio.**

### F6 — Mapa de cromossomos no cartão

**Proposta.** Barra por cromossomo (1–22) com o cM, o total à direita e o maior segmento destacado; a mesma
consistência de F3 visível na tela. Sem heatmap entre pessoas na primeira versão.

**Aceite.** (a) soma visual = total exibido; (b) cromossomo ausente ≠ cromossomo com zero; (c) cabe no cartão
sem rolagem horizontal em 1280 px.

**Impacto médio · esforço pequeno-médio.**

### M1 — Vocabulário controlado e lacunas (rápido)

- Unificar sentinelas: `Desconhecido` / `Não encontrado` / `Não informado` / vazio → **um** estado interno
  `ausente`, com o texto original preservado para exibição.
- Normalizar UF/país com tabela pequena e explícita (Açores → região, não UF; `Portugual` → Portugal;
  corrigir os erros medidos).
- Normalizar kit: prefixo de laboratório (`GENERA37`, `8C752AC7`, `A2513A871`…) para não tratar formatos
  distintos como o mesmo tipo de identificador.
- Relatório de lacunas por arquivo (a RN-P14 em forma de tabela, não de cor de célula).

**Aceite.** (a) zero sentinela tratada como valor; (b) UF inválida lista o valor original; (c) nenhuma
correção silenciosa.

### M2 — Corte declarado: "não encontrado" é "não retornado"

- Ler o corte do cabeçalho de cada lista (`= 14 cM`, `= 6 cM`, `= 16 cM`, `= 3.0 cM`) e propagar para o
  texto: "não retornado pela lista de 14 cM", nunca "não há correspondência".
- É a mesma tese de `core/sem_correspondencia`, aplicada à **origem do dado**.

**Aceite.** (a) nenhuma tela diz "não existe match"; (b) o corte aparece junto do resultado; (c) corte
ausente no arquivo vira "corte não declarado", não zero.

### M3 — PII do roster

- Contato e e-mail **nunca** vão para a tela de análise nem para HTML (o app já injeta todos os nomes no
  HTML — a planilha acrescentaria telefones e e-mails de 304 idosos).
- Exportação de descartes/CSV sem PII; documentar que o app não tem autenticação.

**Aceite.** (a) varrer o HTML servido por `@`/telefone do roster: zero; (b) nenhuma rota devolve contato.

---

## 8. Roadmap sugerido

> **Substituído pela seção 0.** O roadmap abaixo pressupõe o FamilySearch como ponte e o roster como entrada;
> nenhum dos dois vale depois da decisão de 2026-10-22. Fica registrado para mostrar de onde veio a proposta.

| Onda | Itens | Por quê |
| --- | --- | --- |
| **1 — destravar dado** | F3 (adapter), M1, M2, M3 | Sem F3 não há dado; M1/M2/M3 são pequenos e evitam retrabalho de vocabulário e PII |
| **2 — ligar a ponte** | F1, F6 | F1 é pré-requisito de F2; F6 só depende de F3 |
| **3 — subir o valor genealógico** | F2, F5, F4 | F2 é a funcionalidade nova de maior valor; F4/F5 só fazem sentido com dado de F3 |

Dependências: **F1 → F2**; **F3 → F4, F5, F6**; M2 → F3 (o adapter lê o corte).

**Roadmap vigente:** uma onda só — P1 (vocabulário), P2 (painel), P3 (estado da medida), P4 (corte não
declarado), na ordem. Todos tocam a apresentação e o vocabulário; nenhum altera regra de parentesco.

---

## 9. Riscos de implementação

1. **Paridade.** A árvore é tupla congelada e há harness de paridade
   (`_reversa_sdd/parity`). O índice `_FSFTID` deve ser construído **na aplicação**, ao lado da tupla, e
   nunca dentro dela.
2. **Inflação de veredito.** Já existem dois eixos (confronto, viabilidade). F4 entra como **cobertura do
   arquivo**; se virar selo no cartão, a tela passa a ter três respostas concorrentes para a mesma pergunta.
3. **Autoridade do declarado.** A planilha declara posições que o GEDCOM pode não ter. A regra do projeto
   continua: o GEDCOM decide o parentesco documental; o declarado é hipótese confrontada.
4. **PII.** O roster traz telefone e e-mail de pessoas idosas; o app não tem autenticação. M3 é pré-requisito
   de qualquer carga real.
5. **Fonte única inexistente.** Registro (410 IDs) e planilha (495 IDs) se sobrepõem em 100. Tratar um como
   canônico perde dado; a importação precisa aceitar **as duas** e reportar a diferença.

---

## 10. Decisões pendentes

1. **O roster de doadores entra como fonte de evidência no app ou só como cadastro?** Se entra, F3 é
   obrigatório na onda 1; se é só cadastro, F3 cai para "importar para exibição" e F4/F5/F6 saem do escopo.
2. **Qual base é canônica para vínculo declarado: o registro (arquivo 1), as colunas Q/R/S/U (arquivo 2), ou
   a união?** A sobreposição é de 100 IDs em 805; sem essa decisão, F2 valida contra duas verdades.
3. **A árvore unificada vai recuperar `_FSFTID`** (retrabalho de merge) ou aceitamos cobertura parcial e
   aviso de arquivo? Hoje a unificada tem zero IDs.
4. **PII:** a tela pode exibir contato/e-mail do doador? Recomendação: não, enquanto não houver autenticação.

---

## Anexo A — dicionário das 59 colunas, por grupo

| Grupo | Colunas |
| --- | --- |
| Identificação | `Name`, `Kit Number = 16 cM`, `Contact`, `Birth`, `Age`, `Sex`, `Country`, `State`, `City`, `E-mail` |
| Ancestralidade declarada | ` Y-haplo`, `MT-haplo`, `Surnames of Ancestors` |
| FamilySearch | `Relationship`, `Father's Side - FS`, `Mother's Side - FS`, `Parental Connection - FS`, coluna sem título, `Direct Descent - FS`, `Name of Descendant`, `Generation` |
| Evidência GEDmatch | `Kit Shared = 14 cM`, `Shared = 6 cM`, `Eurogenes K13 ...`, `Eurogenes K13 Matching alleles`, `MRCA`, `Chr1..Chr22`, `Chr's`, `Total Match = 6,0 cM`, `Maior Match = 15,0 cM`, `SNPs = 900`, `Total Match Shared (cM)`, `Largest Match Shared (cM)` |
| Outras fontes | `Genera Total Match`, `MyHeritage Total Match` |
| Derivadas | `Age`, `Total Match`, `Maior Match`, `Validation Match Shared For 4`, `Are your parents related?`, `Final Result of Analysis` |

## Anexo B — reprodutibilidade das medições

| Medição | Como foi feita |
| --- | --- |
| Estrutura, fórmulas, formatação condicional | `openpyxl.load_workbook(..., data_only=False)` |
| Valores em cache dos vereditos | `openpyxl.load_workbook(..., data_only=True)` |
| Sentinela, UF, tipos mistos | contagem sobre as células das 304 linhas com nome |
| Junção planilha ↔ GEDCOM | índice `_FSFTID` lido linha a linha (regex `_FSFTID\s+(\S+)`) |
| Comportamento atual do app | `parsers.csv_ingest.read_csv_with_fallback`, `core.genetic_evidence.build_genetic_evidence`, `parsers.segmentos_gedmatch.ler_segmentos_gedmatch` com o `.venv` |
| Cobertura do parser de frases | protótipo de gramática de ~50 linhas sobre as 108 frases não vazias |
| Custo do índice `_FSFTID` | `carregar_arvore` + laço sobre `person.sub_records`, cronometrado com `time.perf_counter` na `v3` (52,3 s para a árvore, 0,058 s para o índice) |

**Reprodutibilidade do comportamento atual:**

```
Projeto DNA de Idosos de Sergipe.csv   → 504 × 58, separador ';', latin-1
                                       → DnaCsvSemColunas: Colunas de Nome e cM não encontradas
adriano_santos_SY3230889.csv          → 492 × 14, separador ','
                                       → 484 evidências, 492 segmentos, 0 avisos
```
