# Adendo: observação de arquivo não é observação de cartão

> Identificador: `017-observacao-de-arquivo-nao-e-observacao-de-cartao`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

Não substitui adendo nenhum. O adendo `016` continua vigente integralmente, e a
**inatingibilidade** que ele declarou para o `015` não é tocada aqui.

## A pergunta do operador

> *"Para que serve essa informação e se é realmente necessário o usuário saber disso?"* — sobre a
> frase que aparecia em **"5. Observações"** de cada cartão: *"O mesmo nome aparece associado a
> mais de um kit (FX8497870, WK9592536). Cada combinação pessoa + kit foi mantida separada; os
> segmentos nunca foram somados entre kits diferentes."*

A resposta foi **separar**, e a decisão é dele: a observação do arquivo passa a ter lugar próprio e
a seção 5 do cartão fica só com o que é daquele cartão.

## Para que a frase serve — a parte que se manteve

Ela é um **recibo de uma conta que o programa não fez**. `build_genetic_evidence` soma o cM de
todas as linhas do CSV com o mesmo par (nome, kit); quando o mesmo nome aparece sob dois números de
kit, essa soma misturaria amostras diferentes. Medido no arquivo que produziu o print
(`03f50d273442cef1__Famílias_Sergipanas.csv`):

| nome | kit A | kit B | a soma proibida | o que a soma faria acreditar | tem cartão? |
|---|---|---|---|---|---|
| `*DPF` | ZA5409607 = **12,5** | WE9804196 = **12,5** | 25,0 | Primo de **4º grau 1× rem.** (cada kit diz 7º grau) | **nenhum** |
| `Moacir Andrade` | JX1969406 = **24,6** | UV3651699 = **5,7** | 30,3 | Primo de **4º grau** (8º grau no 2º kit) | **nenhum** |
| `*Carol` | FX8497870 = **12,7** | WK9592536 = **6,1** | 18,8 | Primo de **5º grau 1× rem.** (7º e 8º grau) | **nenhum** |
| `*Maria` | LY5102040 = **16,0** | LR4550033 = **5,7** | 21,7 | Primo de **5º grau 1× rem.** (6º vs 8º grau) | 2 |
| `Maria do Carmo dos Santos` | MW3062586 = **27,8** | QN1766036 = **5,3** | 33,1 | Primo de **4º grau** (8º grau no 2º kit) | 2 |

`*DPF` é o retrato da armadilha: as duas linhas de ZA5409607 e as duas de WE9804196 são
**idênticas** (6,9 cM no cromossomo 1 e 5,6 no 15, MRCA 7,08) — a mesma pessoa testada duas vezes.
Somadas viram "primo de 4º grau", dois graus mais perto do que o único match real de 12,5 cM
sustenta. E o caso que **nenhuma outra camada cobre** é `Maria do Carmo dos Santos`: a identidade
está `confirmada` (nome que casa perfeitamente com a árvore) e mesmo assim vem de dois kits, com os
dois cartões na tela convidando à soma de 27,8 + 5,3.

## Por que, como estava, não se pagava

| Medição | Valor |
|---|---|
| Cartões da análise | **142** |
| Linhas de observação somadas em todos os cartões | **1010** |
| Dessas, a frase de múltiplos kits | **710 (70,3%)** |
| Cartões em que ela aparecia | **142 de 142** (5 linhas idênticas cada) |
| Avisos distintos de múltiplos kits | **5**, para **5 nomes** |
| Avisos que falavam de nome **sem cartão nenhum** | **3 de 5** (`*Carol`, `*DPF`, `Moacir Andrade` — descartados na triagem: *"sem candidatos por sobrenome"*, *"score insuficiente"*) |

E a frase **não protegia número visível nenhum**: o bloco "2. Evidência genética" renderiza um
`<dl>` por kit, com `kit.total_cm` de cada um (`index.html:927-943`), e `evidence_for` deixa
`totals["cm"]` como `None` quando há mais de um kit. A soma proibida nunca chegou a ser exibida.

A redação anterior era, além disso, um recibo da **contabilidade interna** — *"cada combinação
pessoa + kit foi mantida separada"* descreve o programa, e não o arquivo do operador, e não diz o
que fazer com a informação.

## O que mudou

### 1. O nível é declarado na origem

Todo aviso de `build_genetic_evidence` passa a carregar **`nivel`**:

- `"arquivo"` — vale para o CSV inteiro: `multiplos_kits`, `kit_ausente`.
- `"cartao"` — vale para um par (nome, kit): `mrca_divergente`, que passa a carregar também
  `chave_nome` e `chave_kit`. Era o mesmo vazamento um nível abaixo, **latente** (medido antes:
  0 dos 270 kits divergem entre linhas), e agora o orquestrador entrega o aviso ao cartão certo em
  vez de a todos.

O contrato do nível está na docstring do módulo, em `core/genetic_evidence.py`.

### 2. A frase virou fato dos dados

`_texto_de_multiplos_kits` compõe, no próprio núcleo: o nome como está no CSV, cada kit com o seu
valor, a soma que não pode ser feita, e o parentesco que `possible_relationships` admitiria para
essa soma. Exemplo do CSV de dois kits:

> O mesmo nome aparece em mais de um kit. Ana Silva Souza: A1111111 com 100 cM e B2222222 com
> 50 cM. São amostras diferentes e os valores não podem ser somados: a soma daria 150 cM, que o
> Shared cM Project admitiria como Primos de 1º grau — parentesco que nenhum dos kits sustenta
> sozinho. Cada kit tem o seu próprio cartão e o seu próprio valor.

A frase **acrescentou uma dependência de núcleo**: `genetic_evidence` passa a importar
`relationship_hypotheses`. É seguro e verificado — aquele módulo não importa nada do pacote (só
`__future__`), então não há ciclo —, e o valor está em que o número da soma passa a vir com a
leitura que o torna perigoso, em vez de pedir que o operador acredite na frase.

Os valores saem por **`utils.number_format.formatar_cm`**, a autoridade única do formato de cM. A
primeira versão usava `f"{valor:g}"` e o bloco dizia *"27.8 cM"* enquanto o cartão logo abaixo dizia
*"27,8 cM"* — dois formatos para o mesmo número na mesma página. Foi medido no arquivo real
(`03f50d273442cef1__Famílias_Sergipanas.csv`) antes de virar teste.

### 3. O orquestrador separa, e a tela ganha um bloco

- `core/dna_analysis.dna_analysis` ganha o parâmetro **opcional** `observacoes_do_arquivo` (lista
  que a função preenche). A aridade de retorno **não mudou**: `(resultados, descartados, mensagem)`
  continua igual, e os ~12 pontos de teste que desempacotam três valores seguem válidos.
- `_observacoes` perdeu o parâmetro `extra` e a docstring diz que a seção 5 é do cartão.
- `application.dna_analysis.ResultadoDeAnalise` ganha `observacoes_do_arquivo: tuple = ()`, com
  valor padrão — mesmo padrão de `aviso_de_persistencia`.
- `index.html` ganha o bloco **"Observações do arquivo"**, renderizado **fora** da guarda
  `{% if dna_results %}`: com zero conexões aceitas não há cartão nenhum, e o aviso do arquivo é
  justamente o que explica o zero. `app.css` ganha `.observacoes-do-arquivo`.

## Resíduo declarado

1. **Quem não passa a lista não recebe os avisos de arquivo.** É deliberado — eles não podem voltar
   para dentro do cartão — e não há perda: `build_genetic_evidence` é pública e continua devolvendo
   os mesmos avisos com `nivel == "arquivo"`. A tela de produção passa a lista sempre.
2. **A mensagem de contrato não foi ampliada.** `dna_analysis` continua anexando à mensagem, no caso
   de zero resultados, **apenas** `avisos_do_arquivo` (preâmbulo e linhas ignoradas) — o que sempre
   anexou. Ampliá-la ali mudaria, por tabela, um contrato de tela que o oráculo congelado prende
   (`tests/test_characterization_matching.py::test_pipeline_caracterizado`). Consequência: no caso
   raro de zero cartões **e** preâmbulo, o texto aparece na mensagem **e** no bloco.
3. **`SHA_DA_TELA` não mudou.** O bloco entra entre duas guardas que são falsas na tela de entrada,
   mas o texto literal entre as tags continuaria sendo emitido; o comentário e o `if` usam controle
   de whitespace (`{#-` … `-#}`) para que a página de entrada **não mude de byte**. Foi medido, não
   suposto — e a primeira tentativa **falhou** por um `-` esquecido no fechamento do comentário, o
   que o próprio teste do hash pegou.
4. **`documentary_status` e `documentary_do_registro`** seguem como o adendo `016` os declarou.
   Nada aqui os toca.

## Contratos que acompanharam a mudança

| Arquivo | O que mudou | Por quê |
|---|---|---|
| `tests/test_confrontacao_gedcom_dna.py::test_8_mesmo_nome_em_dois_kits_nao_soma_segmentos` | o aviso passou a ser cobrado no canal do arquivo, e a frase passou a ser cobrada por conteúdo (nome, os dois kits, a soma) | o **intuito** do TESTE 8 é preservado — *"nunca somar kits"* —, e a asserção que mudou era de **apresentação**, não de decisão |
| `tests/test_confrontacao_gedcom_dna.py` (linha torta e preâmbulo) | idem: fato do arquivo, e não do cartão | idem |
| `tests/test_observacoes_do_arquivo.py` | **novo**, 20 testes | prende o nível, a frase, o não-vazamento, o template e a tela pelo caminho de produção |

Nenhuma decisão de matching, caminho, cM, veredito ou contagem foi alterada: a suíte foi de
**955 passou / 9 pulados** para **975 passou / 9 pulados** (exit 0), e os 20 a mais são os testes
novos deste adendo.
