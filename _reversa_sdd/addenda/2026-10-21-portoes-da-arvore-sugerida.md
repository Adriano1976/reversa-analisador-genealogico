# Adendo: portões da árvore sugerida

> Identificador: `2026-10-21-portoes-da-arvore-sugerida`
> Data: `2026-10-21`
> Cenário: **legado** (ancora em `_reversa_forward/029-desacoplamento-de-nos/requirements.md#RF-05`
> e `_reversa_forward/032-arvore-sugerida-na-tela/requirements.md#RF-06`)
> **Origem do registro:** decisão do operador Adriano em 2026-10-21, depois de o cartão
> `Maria Candida de Jesus` (15,1 cM, kit `BN8387325`) exibir **"3 gerações sugeridas"** num
> veredito `INCONCLUSIVO`, com todos os saltos documentados plausíveis. Adendo ADITIVO: não
> emenda seção existente, porque a condição de emissão nunca foi especificada.

## Vigências

Vigente desde 2026-10-21.

## Por que este adendo existe

A `029` definiu que `arvore_sugerida` devolve grafo para **qualquer** `ERRO CRONICO`, e a
`032` pôs o resumo no cartão sem repetir a condição. O efeito medido: bastava o cM estimar
mais gerações do que a árvore documenta para o cartão propor uma correção — mesmo quando
**nenhum salto era biologicamente impossível** e o veredito era `INCONCLUSIVO`.

No caso que abriu o registro, o cartão dizia "3 gerações sugeridas entre Joaquim De Jesus e
Maria José Santos". Os quatro saltos do caminho são plausíveis (23, 25, 42 e 18 anos), e a
cadeia proposta entre 1886 e 1928 daria **10,5 anos por geração** — uma correção que cria
uma impossibilidade biológica onde não havia. A identidade do match também estava
`a_confirmar` ("Camila Maria de Jesus" × "Maria Cândida de Jesus", 122 anos).

## O que passa a valer

1. **Só há sugestão com quebra localizada.** `resumo_da_sugestao` só devolve resumo e
   rótulos quando **todos** os portões passam:
   - o veredito é `ERRO CRONICO / QUEBRA DE LINHA`;
   - a identidade do match **não** é `a_confirmar`;
   - a janela de vida do match **não** é `impossivel`;
   - existe pelo menos um salto com `plausible is False`;
   - a cadeia não torna impossível um trecho que era possível (ver item 3).
2. **A junção não é escolhida por padrão.** `juncao` devolve `JUNCAO_NAO_EVIDENCIADA` quando
   nenhum lado é acusado. Antes, `[]` caía em `[LADO_DOADOR]` e a cirurgia cortava o ramo do
   doador sem evidência. O código novo vale para `arvore_sugerida` e para a tela.
3. **A idade da cadeia é medida no TRECHO.** A guarda de `SUGESTAO_INSUFICIENTE` passa a usar
   `(nasc_filho - nasc_ancestral) / (k + 1)`, e não os anos do doador divididos pelo caminho
   inteiro. A conta antiga diluía a cadeia: `(1976 - 1886) / 6 = 15` anos por geração, dentro
   de 12–70, embora as quatro gerações entre Joaquim e Maria José coubessem em 42 anos.
4. **Quando há hiato mas um portão barra, o cartão explica.** O `aviso` deixa de ser exclusivo
   do cartão em conflito **nesse caso**: a frase lista todos os motivos aplicáveis. O silêncio
   faria o operador ler "não implementado", que é o problema que a `032` nasceu para resolver.
   O `aviso` de `HIATO_NAO_POSITIVO` e `SEM_MRCA_ESTIMADO` continua restrito ao conflito.
5. **O desenho usa a mesma convenção do diagrama documentado.** `mermaid_da_sugestao` passa a
   emitir `flowchart BT` (antes `graph TD`) com **todas** as arestas do descendente para o
   ascendente — inclusive o ramo do match, que desce no caminho e por isso é invertido —, e
   pinta o match de vermelho, como o `p2` do desenho documentado. Antes, a metade do doador era
   desenhada com o filho acima do pai e a cadeia com o ancestral acima do descendente: duas
   convenções no mesmo gráfico.

## Limitação declarada: o modelo é unilateral

O modelo corrige **no máximo uma junção e uma cadeia**, no lado acusado. Ele não é a soma dos
dois hiatos, e isso precisa ficar dito para que ninguém leia o número como conta exata:

- `hiato = floor(geracoes + 0.5) - a_up` é a distância **do lado do doador** até o ancestral.
  Não é o total do caminho.
- Quando os **dois lados** são acusados, esse único número é **dividido** proporcionalmente ao
  excesso de anos de cada lado (`_deficit`). É uma aproximação declarada: a soma consistente
  seria `(geracoes - a_up) + (geracoes - b_up)`, que o código **não** usa.
- Quando só o lado do **match** é acusado, o núcleo usa `geracoes - a_up` em vez de
  `geracoes - b_up` — dívida conhecida e invisível na tela, porque `resumo_da_sugestao` e
  `mermaid_da_sugestao` só desenham o lado do doador.

O **hiato bilateral (P3)** fica fora deste adendo: exigiria contrato de dois hiatos, desenho de
duas cadeias e cartão com dois números. Medição de 2026-10-21 na base de 8 cartões
(`Adriano_Santos_V2_tratado.ged` + `Famílias_Sergipanas.csv`): **0 cartões com junção
evidenciada**, então o P3 não mudaria nenhum deles. A decisão é revisitar quando a base de 142
cartões for medida — o número a olhar é a contagem de `len(juncoes) == 2`.

## O que NÃO muda

- A fórmula do hiato (`floor(geracoes + 0.5) - a_up`) e o número que ela produz.
- `core.matching`, `core.identidade_do_match`, `core.janela_de_vida` e `core.validator`: os
  estados já existiam; o adendo só lhes dá consequência na emissão da árvore.
- O GEDCOM, o CSV, o histórico, o diagrama documentado e os quatro estados do confronto.
- `arvore_sugerida` continua sem mutar a árvore e sem escrever nada em disco.

## Evidência

- Testes: `tests/test_resumo_da_sugestao.py` (portões, aviso composto e o caso da cadeia que
  cria idade impossível), `tests/test_cirurgia_do_grafo.py` (junção sem evidência),
  `tests/test_sugestao_de_correcao.py` (recusa no núcleo), `tests/test_arvore_sugerida_na_tela.py`
  (frase no lugar do bloco), `tests/test_mermaid_da_sugestao.py` (BT, match vermelho e ramo do
  match invertido) e `tests/test_correcao_de_arquivos.py` (dois kits independentes).
- Suíte completa: `1394 passed, 9 skipped`.
- Caso real (`Adriano_Santos_V2_tratado.ged` + `Famílias_Sergipanas.csv`): o cartão de Maria
  Cândida passa de bloco com 3 gerações para a frase "Não é possível localizar a quebra: o
  veredito é INCONCLUSIVO; a identidade do match está a confirmar; nenhum salto documentado é
  biologicamente impossível; a cadeia de 3 geração(ões) daria 10.5 anos por geração, fora de
  12–70." — e nenhum dos 8 cartões da análise emite árvore.

## Aprovação

Decisão humana de 2026-10-21: implementar os portões P0 (status), P1 (evidência e identidade)
e P2 (trecho), com a frase de substituição. Registrada na sessão em que o operador respondeu
"pode fazer" à tabela de antes × depois. Na mesma data, o desenho (P4) foi alinhado ao diagrama
documentado e o hiato bilateral (P3) ficou declarado fora de escopo, a revisitar com a medição
da base de 142 cartões.
