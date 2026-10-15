# Correção — a observação do arquivo era repetida dentro de cada cartão

**Data:** 2026-10-14
**Tipo:** **apresentação** e **arquitetura de avisos**. Não altera decisão de matching, caminho,
cM, veredito, contagem de cartões nem o texto de nenhum veredito.
**Adendo:** `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md`
**Arquivos alterados:** `src/core/genetic_evidence.py`, `src/core/dna_analysis.py`,
`src/application/dna_analysis.py`, `src/app.py`, `src/templates/index.html`, `src/assets/app.css`
**Testes alterados:** `tests/test_confrontacao_gedcom_dna.py` (TESTE 8, linha torta, preâmbulo)
**Teste novo:** `tests/test_observacoes_do_arquivo.py` (20 testes)
**Sondas:** `_reversa_bugs/_sondas-matching/pergunta_multiplos_kits.py`,
`_reversa_bugs/_sondas-matching/whitespace_jinja.py`

## O que o operador perguntou

Print da análise de `03f50d273442cef1__Famílias_Sergipanas.csv`, seção **"5. Observações"**:

> *"Nos resultados que aparece para o usuário, aparece essa frase: O mesmo nome aparece associado a
> mais de um kit (FX8497870, WK9592536). Cada combinação pessoa + kit foi mantida separada; os
> segmentos nunca foram somados entre kits diferentes. Para que serve essa informação e se é
> realmente necessário o usuário saber disso?"*

## Para que a frase serve

Ela é um recibo de uma conta que o programa não fez. `build_genetic_evidence` soma o cM de todas as
linhas com o mesmo par (nome, kit); com o mesmo nome sob dois kits, essa soma misturaria amostras.
O número que ela impede, medido no arquivo do print: `*DPF` tem 12,5 cM em ZA5409607 e 12,5 cM em
WE9804196 — as linhas são idênticas (6,9 cM no chr 1, 5,6 no chr 15, MRCA 7,08: a mesma pessoa
testada duas vezes). Somadas dão 25,0 cM, que o Shared cM Project admite como **primo de 4º grau
1× removido** — dois graus mais perto do que o match real de 12,5 cM sustenta.

E o caso que **nenhuma outra camada cobre** é `Maria do Carmo dos Santos`: identidade `confirmada`,
nome que casa perfeitamente com a árvore, e mesmo assim dois kits com dois cartões na tela,
convidando à soma de 27,8 + 5,3 = 33,1 cM.

## Por que, como estava, não se pagava

| Medição | Valor |
|---|---|
| Cartões | **142** |
| Linhas de observação somadas | **1010** |
| Dessas, a frase de múltiplos kits | **710 (70,3%)** |
| Cartões em que aparecia | **142 de 142** |
| Avisos distintos | **5**, para 5 nomes |
| Avisos sobre nomes **sem cartão** | **3 de 5** (`*Carol`, `*DPF`, `Moacir Andrade`) |

Três fatos que a medição deu e a leitura do código não daria:

1. A frase **não protegia número visível nenhum**. O bloco "2. Evidência genética" mostra um `<dl>`
   por kit, com `kit.total_cm` de cada um, e `evidence_for` deixa `totals["cm"]` como `None` quando
   há mais de um kit: a soma proibida nunca chegou a ser exibida.
2. Ela era **global mas copiada para dentro de cada cartão** — `evidence_for` fazia
   `avisos_do_kit + list(avisos or [])`, e a lista do arquivo inteiro entrava em todo cartão.
3. Em **3 dos 5 casos** ela falava de nomes que a triagem **descartou** e que não têm cartão algum.
   O operador lia, no cartão de uma conexão qualquer, a contabilidade de kits de gente que não
   aparece em lugar nenhum do relatório.

E a redação era da **contabilidade interna**: *"cada combinação pessoa + kit foi mantida separada"*
descreve o programa, não o arquivo do operador, e não diz o que fazer com a informação.

## O que mudou

1. **O nível vem da origem.** Todo aviso de `build_genetic_evidence` carrega `nivel`
   (`"arquivo"` | `"cartao"`). `mrca_divergente` — o mesmo vazamento um nível abaixo, latente
   porque 0 dos 270 kits divergem — passa a carregar `chave_nome` e `chave_kit`, e o orquestrador
   o entrega ao cartão certo em vez de a todos.
2. **A frase virou fato dos dados**, composta no núcleo por `_texto_de_multiplos_kits`: o nome, cada
   kit com o seu valor, a soma que não pode ser feita e o parentesco que essa soma faria acreditar.
   Os valores saem por `utils.number_format.formatar_cm` — a primeira versão usava `:g` e o bloco
   dizia *"27.8 cM"* enquanto o cartão abaixo dizia *"27,8 cM"*.
3. **O orquestrador separa.** `dna_analysis` ganha o parâmetro opcional `observacoes_do_arquivo`
   (lista que a função preenche). A aridade de retorno **não mudou** — os ~12 pontos que
   desempacotam três valores seguem válidos.
4. **A tela ganha o bloco "Observações do arquivo"**, uma vez, acima do índice, **fora** da guarda
   `{% if dna_results %}`: com zero cartões o aviso do arquivo é justamente o que explica o zero.

## Verificação

| | |
|---|---|
| Suíte | **975 passou, 9 pulados**, exit 0 (antes: 955 / 9) |
| Seção 5 dos cartões (arquivo real de 142 cartões) | **1010 → 300 linhas**; a frase: **142 de 142 cartões → 0** |
| Bloco do arquivo | **5 linhas, uma por nome**, cada uma nomeando o nome, os dois kits e os valores |
| Tela de entrada | **`SHA_DA_TELA` não mudou** — o bloco usa controle de whitespace para não alterar um byte |
| Mensagem de contrato | **não ampliada** — `test_characterization_matching` continua prendendo o texto congelado |
| Tela de resultado | bloco renderizado **uma vez** na página inteira; a seção 5 de cada cartão sem a frase |

## O erro que a própria verificação pegou

A primeira tentativa de preservar `SHA_DA_TELA` **falhou**: eu escrevi o comentário Jinja com o `-`
de abertura mas sem o de fechamento, e a página de entrada ganhava uma linha de 20 espaços. O teste
do hash acusou. Antes de corrigir, escrevi `whitespace_jinja.py` para **medir** qual das formas de
`{% if %}` é neutra, em vez de tentar adivinhar — a sonda confirma que `{#- … -#}` com `{% if %}`
sem dash é neutra, e que o defeito era o dash faltando, não a estratégia.

Um segundo defeito meu, também pego na hora: o comentário continha o literal `{#- … -#}`, e o `#}`
**encerrou o comentário antes do fim** — o texto restante vazou para o HTML. Comentário dentro de
comentário Jinja não é texto: é o fim dele.
