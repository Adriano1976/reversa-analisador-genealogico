# Adendo: a janela de vida veta o parentesco

> Identificador: `016-janela-de-vida-veta-o-parentesco`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador — é uma **decisão dele**, tomada
> depois de a consequência ter sido medida e apresentada. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

**Substitui a apresentação declarada no adendo `015-veredicto-do-doador-no-cartao`**, que
mantinha o caminho documental na tela e o ressalvava. Aquele adendo continua vigente no que não
é tocado aqui — a regra da identidade de um prenome só, o selo do índice —, e o que ele declarou
sobre o veredicto, o selo e o diagrama recolhido passa a ser **inatingível**.

## A regra, como o operador a formulou

> *"SE na Janela de vida a idade for > 122, a pessoa será tratada como 'Parentesco documental não
> encontrado' com todas as regras aplicadas para esse tipo de grupo e desconsiderar o diagrama."*

Implementada em `core/dna_analysis.py`, com o corte no estado `impossivel` (> `IDADE_IMPOSSIVEL`,
122) e **não** em `suspeita` (105–122), que continua apenas avisando.

A forma do grupo não foi copiada: foi **extraída** para `core.documental_nao_encontrado`, que
`documentary_relationship` já usava no ramo sem caminho. As duas razões de apresentar um cartão
assim — não existir caminho e o caminho estar vetado — saem com a **mesma forma, palavra por
palavra**; se fossem duas cópias, divergiriam na primeira correção de texto.

## O que isto custa — medido, e é consequência, não acidente

| | |
|---|---|
| Cartões alcançados hoje | **3** de 62 (`TG8027863`, `ZC1171551`, `ZL6373425`) |
| A árvore tem o caminho? | **Sim**: 11, 12 e 10 meioses, com ancestral comum localizado |
| O que a tela passa a afirmar | *"Nenhum caminho genealógico foi encontrado no GEDCOM entre as duas pessoas"* — **falso sobre a árvore** |
| Efeito prático | Manda o operador procurar **registro faltando**, quando o trabalho é procurar **homônimo** |
| Perde | A **única** comparação de cM × parentesco da análise: `TG8027863` sai de `COMPATIVEL` para `INCONCLUSIVO` |
| Perde | 1 dos **5** cartões que apontam para o mesmo ancestral (`Manoel da Silva Vieira`, 1720) |

Está declarado porque é consequência declarada, e não porque seja desejável. A alternativa —
manter o caminho e ressalvá-lo — foi implementada, medida e **substituída por decisão do
operador**, que preferiu o cartão do grupo ao cartão ressalvado.

## O que a regra NÃO faz

**Não destrói o dado.** O parentesco original vai para `documentary_do_registro`, no próprio
resultado e **fora da tela**: caminho, meioses, ancestral comum, caminhos alternativos e avisos.
É o que permite auditar a regra e revertê-la sem recarregar a árvore, e é a mesma disciplina do
resto do projeto — aposentar, nunca apagar.

**Não toca na camada congelada.** A escolha da pessoa, o `matching`, o caminho encontrado e os
quatro estados do confronto continuam intactos. A regra age **depois** da escolha e decide o que
se apresenta.

**Não marca `sem_data` nem `suspeita`.** Sem data não é impossível; e 105–122 continua avisando
com o parentesco visível.

## A consequência que ninguém pediu, e que é a mais interessante

O selo combinado do cabeçalho — `compatível no cM, identidade impossível` — **deixou de ser
emitido**, e não por ter sido removido: ele exigia uma comparação de cM que agora não acontece.
A contradição que o adendo `015` resolveu **por rótulo**, este resolve **na raiz**: nos cartões
com idade impossível, o cM não é mais confrontado com um parentesco que a tela não mostra.

Pela mesma razão ficaram inatingíveis o bloco de veredicto do doador e o selo `não atribuível ao
doador` no índice. Os três continuam no código — a regra é reversível em uma linha de
`core.dna_analysis` —, **declarados como inatingíveis** nos comentários do template, e um teste
prende que não aparecem. Apagá-los agora esconderia o que a reversão teria de restaurar.

## Impacto por artefato da extração

| Artefato | Impacto |
|---|---|
| `_reversa_sdd/analise-dna/contracts.md` | **Sem impacto.** Os quatro estados e a ordem de conservadorismo continuam; o que muda é qual ramo o confronto toma |
| `_reversa_sdd/analise-dna/requirements.md` | **Sem impacto formal.** Nenhuma `RF` cobre "apresentar parentesco com idade impossível", porque esse caso não existia na extração |
| `_reversa_sdd/state-machines.md` | **Diverge.** A máquina do confronto continua a mesma, mas uma entrada nova a alimenta: o documental pode chegar ao `compare` já vetado. Fica registrado |
| `_reversa_sdd/erd-complete.md` / `init.sql` | **Diverge, e é material.** `match_result.documentary_status` passa a gravar `not_found` para cartões em que existe caminho. O `CHECK` continua válido (o valor é um dos previstos); o **significado** da coluna deixa de ser "a busca não achou" e passa a ser "a análise não apresenta" |
| Adendo `015` | **Parcialmente substituído**, como declarado em "Vigência" |
| `tests/test_profundidade_do_caminho.py` | `TestOCartaoDoDoadorImpossivel` reescrito para a regra; o teste do selo combinado virou `test_a_contradicao_do_selo_morreu_na_raiz` |

## Dívidas declaradas, não fechadas

1. **A coluna `documentary_status` do histórico muda de sentido** para esses cartões. Quem ler o
   banco depois desta data não consegue distinguir "a busca não achou caminho" de "a análise não
   apresentou o caminho que achou". O `documentary_do_registro` vive só no payload da resposta e
   **não é persistido** — se a auditoria a longo prazo importar, ele precisa de coluna.
2. **O aviso `sem_caminho` é reaproveitado**, e ele diz *"Nenhum caminho subindo por pais liga as
   duas pessoas dentro do teto de 20 iterações"* — o que, para os cartões vetados, também não
   aconteceu. Fica como parte de "todas as regras do grupo", e é a **segunda** frase que a regra
   torna inexata.
3. **A moldura do adendo `015` está inatingível**, e o código dela não tem teste de
   alcançabilidade que avise se voltar a ser alcançável — só o inverso (que não aparece).
4. **Nada disto foi verificado em navegador** para o caso de o `details` voltar a ser usado.

## Regras sob vigilância

- **`RF-19` / `BR-D-27` / ADR-15** — os quatro estados. A regra não os toca; ela escolhe qual
  ramo o confronto toma, e o ramo escolhido é o que já existia.
- **`ADR-14`** (separar documental, genética e confronto) — a regra age sobre o **documental
  apresentado**, e é a primeira vez que uma política de um eixo altera a entrada de outro. É a
  tensão mais relevante deste adendo: o confronto deixa de ser independente do veredito da
  janela de vida.
- **A ordem de apresentação** — os 3 cartões passam a ordenar junto com os 51 sem caminho, porque
  `_ordem` lê o caminho apresentado. Consequência esperada de "tratado como esse grupo".

## Fontes

- `_reversa_bugs/_sondas-matching/avaliar_regra_nao_encontrado.py` — a sonda que mediu o alcance e
  as três consequências, antes de a regra existir.
- `_reversa_bugs/_sondas-matching/pista_documental_da_margarida.py` — a que mostrou que o
  "caminho" do cartão da Margarida não era pista nenhuma.
- `src/core/dna_analysis.py`, `src/core/documentary_relationship.py`
  (`documental_nao_encontrado`), `tests/test_profundidade_do_caminho.py`.
