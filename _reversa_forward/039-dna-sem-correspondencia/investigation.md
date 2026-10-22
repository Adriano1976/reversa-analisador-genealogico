# Investigation: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/039-dna-sem-correspondencia/requirements.md`

## 1. A pergunta que originou a feature

O operador viu, na análise real, um match de **154,5 cM** (`Clezia Santos`) e outro de **51,3 cM**
(`Airton Passos Vasconcelos`) fora dos cartões de "Análise de conexão", no meio de centenas de
descartes. A pergunta foi: qual critério deixou esses matches de fora, e eles não deveriam aparecer?

A resposta curta é: **o critério é o nome, não o cM**. O bloco novo não muda esse critério; ele dá
visibilidade ao que o critério deixou de fora e que, por cM, merece investigação.

## 2. O que foi medido

| Medida | Valor |
|--------|-------|
| Análise real de 2026-10-22 (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`, raiz `Adriano Santos`) | **8 cartões**, **448 descartes**, 456 grupos (nome, kit) |
| Cartões sem caminho documental | **7 de 8** — "não achou caminho" não é o que exclui |
| Descartes com cM ≥ 40,0 | **9** |
| Distribuição dos 448 | mediana **9,0 cM**; 249 abaixo de 10; 137 entre 10 e 20; 53 entre 20 e 40; 8 entre 40 e 90; **1** acima de 90 |
| Maiores descartes | 154,5 (`Clezia Santos`, AZ4078391); 52,5; 51,3 (`Airton Passos Vasconcelos`, SD5093704) |
| Descartes com candidato compatível | **15**, nenhum entre os 10 maiores |
| "Clezia" no GEDCOM | **0 ocorrências**; a pessoa mais parecida é `Luzia` (73 de semelhança), e não há `Luzia ... Santos` |
| "Airton"/"Ayrton" no GEDCOM | **0 ocorrências**; os 42 `Vasconcelos` da árvore têm data entre 1100 e 1450; os 3 `Passos`, entre 1834 e 1845 |

Os dois casos foram medidos com o motor real: a Clezia falha em `prenome_diferente` (prenome 62,
nota 75,6, sobrenomes 1/1, grafia 1,0); o Airton falha em `sobrenome_pouco_parecido` (prenome 62,
nota 77,55, grafia 0,33). Nenhum dos dois tem candidato compatível.

As ferramentas que reproduzem a medição estão em `_reversa_bugs/_sondas-matching/`:
`causas_de_nao_entrar.py` (as causas categóricas), `motivo_score_insuficiente.py` (a decomposição
do score) e `_dump_multiplos_kits.json` (o dump da análise). Nenhuma delas é fixture de teste.

## 3. Por que o matching não resolve

- O cM só participa de **uma** decisão em `core/matching.py`: com `cM ≥ 150` e prenome não genérico,
  o limiar de Jaccard cai de 0,50 para 0,33. Não há piso de cM (`domain.md#34`).
- O caso Clezia mostra o limite: ela tem um sobrenome só, então o limiar de Jaccard nem se aplica; o
  que a barra é o prenome (62 contra o piso de 85) e a nota (75,6 contra 86).
- O Airton tem dois sobrenomes e cM abaixo de 150; a grafia do sobrenome (0,33) fica abaixo de 0,50.
  Mesmo com o limiar relaxado, o prenome e a nota continuariam abaixo das portas seguintes.
- O conhecimento extraído já registra que **nomes sem sobrenome utilizável são inalcançáveis por
  qualquer cM** (`addenda/024`, resíduo 1). A Clezia e o Airton não são esse caso, mas a conclusão
  é a mesma: o cM não cria a pessoa que falta na árvore.
- Aceitar um match de cM alto **sem** nome compatível produziria um cartão sem nó: sem parentesco,
  sem MRCA documental, sem diagrama e sem janela de vida. Pior: escolheria um homônimo fraco (o
  Vasconcelos de 1394) e apresentaria a pessoa errada, exatamente o falso positivo que a `W001` da
  feature 034 proíbe.

## 4. Alternativas avaliadas

| Alternativa | Por que não |
|-------------|-------------|
| **A. Mudar o matching** para aceitar cM ≥ 40 sem candidato compatível | Mudaria a decisão de aceitação, criaria cartões com a pessoa errada e violaria a `W001` da 034 e o resíduo 1 da 024. O operador pediu visibilidade, não uma nova regra de parentesco |
| **B. Criar um cartão "só DNA"** para o match sem pessoa | O cartão é uma análise documental: parentesco, identidade, janela, diagrama e sugestão. Sem nó, todas as seções ficariam vazias ou inventadas. É uma feature maior, não o que foi pedido |
| **C. Filtrar todos os descartes com cM ≥ 40** | Mistura os "sem candidato compatível" com os "quase" (candidato compatível, mas recusado). Os segundos têm uma ação — promover — e ficam na lista completa. O título "sem correspondência" ficaria falso |
| **D. Bloco derivado só dos descartes sem candidato compatível** | **Escolhida.** Não muda decisão, não cria cartão, mostra o que o operador precisa ver e preserva a lista completa e o CSV |

## 5. Padrões aplicáveis

- **Visão derivada de um resultado existente**: o bloco é uma função pura sobre `resultados` e
  `descartados`; nenhuma leitura nova de CSV/GEDCOM, nenhum recálculo de cM.
- **Aviso nasce aberto, apêndice nasce fechado**: o bloco carrega aviso, então segue o
  `observacoes-do-arquivo` (`addenda/022`), não o `bloco-descartados` (`addenda/020`).
- **Whitelist de campos**: o seletor devolve só `csv_name`, `kit`, `cm` e `mrca_generations`; não
  copia `motivo` nem `candidatos` para o template do bloco. Isso impede que a tela nova herde a
  leitura de "quase acertou" da lista completa.
- **Determinismo**: ordenar por `(-cm, nome normalizado, csv_name, kit)`, como o matching faz com o
  menor `xref_id`; nada de ordem de `set`.
- **Payload aditivo**: `mrca_generations` já existe no kit; só passa a viajar no descarte. Nenhuma
  porta, tabela ou migração.
- **Constante declarada**: 40,0 cM é um corte de triagem, com a medição no docstring, não uma faixa
  do Shared cM Project.

## 6. Fontes

| Fonte | Uso |
|-------|-----|
| `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` | O cM não decide aceitação; só o Jaccard |
| `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados` | Ordem documental primeiro, cM dentro do grupo; precedente de ordem declarada |
| `_reversa_sdd/analise-dna/contracts.md#62-descartes` | Campos do descarte |
| `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` | Nomes sem sobrenome inalcançáveis por cM; a decisão de não corrigir |
| `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` | Compatível = prenome parecido + sobrenome; promoção do operador |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` | Lista completa em CSV |
| `_reversa_sdd/addenda/038-humanizar-motivo-descartes.md#resumo-da-entrega` | Motivo humano; nona coluna; decisão intacta |
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto` | Aviso nasce aberto |
| `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` | Payload do kit; `mrca_generations` não está listado (lacuna 🟡) |
| `src/core/matching.py`, `src/core/dna_analysis.py`, `src/core/genetic_evidence.py` | O motor que decide e o ponto onde o MRCA se perde |
| `src/application/dna_analysis.py`, `src/app.py`, `src/templates/index.html` | A projeção e a tela |
| `_reversa_bugs/_sondas-matching/causas_de_nao_entrar.py`, `motivo_score_insuficiente.py` | As medições que sustentam os exemplos |

Fontes externas: **n/a**. O corte de 40,0 cM não é uma faixa publicada e o MRCA é a estimativa do
próprio relatório de DNA; nenhum número de genealogia genética é afirmado sem essa ressalva.

## 7. Riscos de interpretação (para o texto da tela)

- **MRCA estimado não é MRCA documental.** O número vem do CSV do relatório, é uma média por kit e
  não localiza ninguém na árvore. O rótulo precisa dizer "estimado".
- **40,0 cM não é um grau de parentesco.** É um corte de triagem; a faixa de relações continua sendo
  a do Shared cM Project, e só o cartão a calcula.
- **O bloco não é uma conexão.** Ele não afirma parentesco, não desenha caminho e não promove
  ninguém; é um convite à pesquisa.
- **O bloco não é a lista completa.** Ele é um recorte; os mesmos nomes continuam na lista de
  descartes com o motivo e os candidatos.

## 8. Perguntas restantes

Nenhuma. O escopo estrito, a exclusão de nome com cartão e a posição do bloco foram decididos no
`/reversa-clarify` de 2026-10-22 e estão registrados em `requirements.md#9-esclarecimentos`.
