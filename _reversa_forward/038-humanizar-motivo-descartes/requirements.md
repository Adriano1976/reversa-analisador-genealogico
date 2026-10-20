# Requirements: humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O bloco "Matches descartados" mostra, na coluna Motivo, textos como
`score insuficiente ou conflito de sobrenome (given=100, final=88.25, inter=1/1, jacc=0.50)`.
Isso é uma fórmula, não uma explicação: oferece duas causas possíveis e nunca diz qual
aconteceu — e a própria extração já registrou que a metade "conflito de sobrenome" não era a
causa em **100%** dos 325 descartes medidos. Esta feature troca a fórmula por uma frase em
português comum, **uma por causa**, na tela, na lista de trabalho em CSV e no histórico da
promoção. Os números medidos não se perdem: viram um detalhe técnico ao lado. **Nenhuma
decisão de aceitação muda.**

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/analise-dna/contracts.md#6-contrato-do-payload-e-dos-avisos` | Catálogo dos motivos de recusa, incluindo o literal `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"` | 🟢 |
| `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` | Resíduo 3, medido: a mensagem de score nunca diz qual das duas causas aconteceu; em 100% dos 325 descartes a interseção mínima de sobrenomes foi cumprida; existe um sétimo portão (penalidade de token do meio) que não aparece em número nenhum da mensagem | 🟢 |
| `_reversa_sdd/code-analysis.md#43-algoritmos-e-lógica-não-trivial` | Bloco de scoring: `given`, `final`, `inter`, `jacc` e os limiares de aceitação (A/B/C/D) | 🟢 |
| `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` | O cM não decide aceitação; a decisão é por semelhança de nome, com filtro anti-falso-positivo | 🟢 |
| `_reversa_sdd/domain.md#52-núcleo-e-aplicação-srccore-srcapplication` | O motivo do descarte é **texto do núcleo**, que atravessa aplicação e apresentação sem virar código | 🟢 |
| `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` | O bloco dos descartados passou a mostrar os candidatos avaliados; o motivo continuou sendo o único explicador da recusa | 🟢 |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#impacto-por-artefato-da-extração` | Lista de trabalho em CSV: oito colunas, com `Motivo` como quarta | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Adriano**, genealogista-operador | Decidir, nome a nome, se vale corrigir a grafia na árvore, procurar um homônimo ou aceitar o descarte | Abre o bloco dos descartados e lê a coluna Motivo para triar centenas de nomes |
| **Quem recebe a planilha** (parente ou pesquisador que não conhece o sistema) | Conferir os descartes no cadastro da árvore, em outra ferramenta | Recebe a lista de trabalho em CSV e precisa entender por que cada nome ficou de fora sem ter o código à vista |

## 4. Regras de negócio novas ou alteradas

1. **RN-25:** o Motivo de um descarte é **texto de apresentação**, escrito em português comum.
   Nomes de medida (`given`, `final`, `inter`, `jacc`) e parênteses de fórmula não aparecem na
   coluna Motivo, nem na tela nem na planilha. 🟢
   - Origem no legado: `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` (resíduo 3)
   - Tipo: alterada
2. **RN-26:** cada recusa nomeia **uma** causa, escolhida por precedência fixa — do mais
   acionável ao menos acionável: (a) o nome tem uma parte a mais que não existe na árvore;
   (b) sobrenomes em comum de menos para o prenome; (c) sobrenome parecido, mas abaixo do
   limiar; (d) prenome diferente; (e) semelhança geral insuficiente. A precedência é parte do
   contrato: o mesmo par de nomes sempre recebe a mesma frase. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#43-algoritmos-e-lógica-não-trivial`
   - Tipo: nova
3. **RN-27:** toda recusa carrega, além do texto, um **código estável de causa**
   (`nome_do_meio_ausente`, `sobrenomes_em_comum_insuficientes`, `sobrenome_pouco_parecido`,
   `prenome_diferente`, `semelhanca_insuficiente`, `sem_sobrenome_comum`). O texto pode ser
   reescrito sem quebrar quem depende da causa. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#52-núcleo-e-aplicação-srccore-srcapplication` (o motivo é texto, não código — esta regra acrescenta o código ao lado do texto)
   - Tipo: nova
4. **RN-28:** os quatro números medidos (`given`, `final`, `inter`, `jacc`) continuam
   disponíveis como **detalhe técnico**, em campo próprio. Nada é apagado: o operador não lê a
   planilha para entender o motivo, mas quem confere o cálculo continua tendo os números. 🟢
   - Origem no legado: `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` (resíduo 3 é a origem do pedido)
   - Tipo: nova
5. **RN-29:** o motivo não decide nada. A troca de redação **não pode** alterar o conjunto de
   matches aceitos, o conjunto de descartes, o cM, os caminhos nem as notas. O motivo é
   consequência da decisão, nunca causa. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação`
   - Tipo: alterada (a redação do motivo muda; a decisão fica congelada)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O Motivo de uma recusa por semelhança aparece em português comum, sem medidas nem fórmula | Must | Nenhuma célula Motivo da tela nem da planilha contém `given=`, `final=`, `inter=`, `jacc=`; cada motivo é uma frase com sujeito e predicado | 🟢 |
| RF-02 | O motivo nomeia a causa que **de fato** recusou, não uma lista de hipóteses | Must | O caso medido `given=100, final=88.25, inter=1/1, jacc=0.50` (todos os portões de nota cumpridos, recusado pelo veto de token do meio) sai como "o nome tem uma parte a mais que não existe na árvore", e não como "score insuficiente" | 🟢 |
| RF-03 | Cada recusa tem código estável de causa, independente do texto | Should | O mesmo par de nomes produz o mesmo código em execuções repetidas; o código é legível no dado que abastece a tela e a planilha | 🟡 |
| RF-04 | Os números medidos continuam disponíveis como detalhe técnico | Must | Os quatro valores (`prenome`, `nota`, `sobrenomes em comum`, `semelhança de grafia`) continuam acessíveis para uma recusa por semelhança, com rótulo, fora da coluna Motivo | 🟢 |
| RF-05 | A lista de trabalho em CSV preserva o formato e ganha o detalhe técnico | Must | A planilha continua abrindo no Excel em português (BOM, `;`, decimal com vírgula, guarda contra fórmula) e traz o detalhe técnico em coluna própria ao fim | 🟢 |
| RF-06 | O motivo registrado na promoção de um candidato é o texto humano | Should | O cartão promovido mostra o motivo como o operador o leu na lista, não a fórmula | 🟡 |
| RF-07 | Os motivos que já estavam em linguagem comum seguem o mesmo padrão | Should | O filtro anti-falso-positivo deixa de exibir o parêntese técnico "(filtro anti-falso-positivo)" | 🟢 |
| RF-08 | A decisão de aceitação fica congelada | Must | Rodada a mesma dupla de arquivos, os cartões, os descartes, o cM e os caminhos são idênticos antes e depois da feature; muda apenas o texto do motivo | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A humanização não acrescenta leitura de arquivo, chamada de rede nem laço novo sobre os descartes | O texto é derivado dos valores que a decisão já calculou, no mesmo ponto do laço de avaliação | 🟢 |
| Acessibilidade | O motivo é conteúdo textual — não depende de cor, ícone, `hover` ou tooltip para ser lido | O bloco já é acessível hoje; a feature não pode trocar texto por dica de mouse | 🟢 |
| Compatibilidade | O CSV mantém BOM, separador `;`, decimal com vírgula e a guarda contra fórmula | Formato definido na feature 035 e verificado por teste | 🟢 |
| Rastreabilidade | O detalhe técnico permite reproduzir a decisão de qualquer descarte | `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` (resíduo 3 registra que a mensagem escondia causa e portão) | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: recusa causada por uma parte do nome que não existe na árvore
  Dado um descarte medido com prenome 100, nota 88.25, sobrenomes em comum 1 de 1 e semelhança de grafia 0.50
  Quando o operador abre o bloco dos Matches descartados
  Então o motivo exibido diz que o nome tem uma parte a mais que não existe na árvore
  E a célula não contém "given", "final", "inter" nem "jacc"

Cenário: recusa causada pela grafia do sobrenome
  Dado um descarte em que a semelhança de grafia do sobrenome fica abaixo do limiar
  Quando o motivo é exibido
  Então o texto diz que o sobrenome é parecido, mas não o suficiente
  E o detalhe técnico traz os quatro números

Cenário: recusa causada pelo prenome
  Dado um descarte em que a semelhança de prenome fica abaixo de 85
  Quando o motivo é exibido
  Então o texto diz que o prenome é diferente do que está na árvore

Cenário: recusa sem causa dominante
  Dado um descarte em que sobrenomes e prenome passam, e a nota final fica abaixo do mínimo
  Quando o motivo é exibido
  Então o texto diz que o nome é parecido, mas não o suficiente para ser a mesma pessoa

Cenário: planilha de trabalho
  Dado o bloco dos Matches descartados com pelo menos uma recusa por semelhança
  Quando o operador baixa a lista de trabalho em CSV
  Então a coluna Motivo traz a frase humana
  E a última coluna traz o detalhe técnico com os quatro números rotulados
  E as oito colunas anteriores mantêm nome e posição

Cenário: decisão congelada
  Dada a mesma dupla GEDCOM + CSV usada nos testes de aceitação
  Quando a análise roda depois da feature
  Então os cartões, os descartes, o cM e os caminhos são idênticos aos de antes
  E nenhum nome muda de lado

Cenário negativo: motivo que não vem do bloco de semelhança
  Dado um descarte por ausência de sobrenome na árvore
  Quando o motivo é exibido
  Então o texto continua descrevendo aquela causa
  E não ganha frase de semelhança nem detalhe técnico inventado
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o pedido do operador: sem isso a feature não existe |
| RF-02 | Must | Trocar a fórmula por uma frase genérica continuaria sem dizer a causa |
| RF-08 | Must | A decisão é o produto; texto não pode mexer nela |
| RF-04 | Must | Sem os números, a mudança perde a rastreabilidade que a 024 já tinha protegido |
| RF-05 | Must | A planilha é o caminho real de trabalho do operador |
| RF-03 | Should | O código protege as próximas mudanças de redação, mas não é percebido pelo operador |
| RF-06 | Should | O histórico da promoção é secundário, mas coerente com o resto |
| RF-07 | Should | Fecha o jargão remanescente com custo baixo |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] o detalhe técnico deve ficar visível também na tela, ou basta a coluna da planilha?
- 🔴 [DÚVIDA] o motivo guardado no histórico de uma promoção passa a ser o texto humano, ou continua sendo a fórmula que o sistema deu na hora?
- 🔴 [DÚVIDA] a redação final das cinco frases é a proposta acima, ou o operador quer revisar palavra por palavra?

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-requirements` | reversa |
