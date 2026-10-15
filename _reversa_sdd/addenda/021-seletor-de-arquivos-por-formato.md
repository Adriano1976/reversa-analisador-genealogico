# Adendo: o seletor de arquivos por formato

> Identificador: `021-seletor-de-arquivos-por-formato`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

**Declara mudança de `SHA_DA_TELA`** — e desta vez a tela de entrada muda de verdade, por um
atributo visível no HTML servido, e não só pelo `<script>`.

## O pedido

> *"Na hora de 'Enviar nova árvore' na aba 'Analisador de DNA', o usuário deve somente visualizar
> os arquivos .ged para evitar o envio de arquivos de outros formatos. Essa regra deve ser
> aplicada para arquivos do tipo .csv também."*

## O que mudou

| Campo | Onde vive | Antes | Depois |
|---|---|---|---|
| `id="gedcom"` ("Enviar nova árvore") | tela de **entrada** | sem filtro | `accept=".ged"` |
| `id="matches_csv"` (relatório da análise) | formulário da **análise** | sem filtro | `accept=".csv"` |

Os dois campos ganharam um terceiro teste que não existia: **todo** `type="file"` renderizado tem
de trazer `accept`. Sem ele, um quarto campo entra sem filtro e ninguém percebe — o defeito é
silencioso por natureza.

## `accept` filtra o seletor, e não é barreira

Isto é o ponto do adendo, e é o que impede a mudança de ser lida como segurança:

- quem escolher **"Todos os arquivos"** no seletor manda o que quiser;
- **arrastar** o arquivo para o campo ignora o `accept` por completo;
- e **não há nada do lado do servidor olhando a extensão** — de propósito.

A barreira de verdade é a de **conteúdo** (`utils.validate.validar_conteudo_gedcom` exige a
declaração `0 HEAD`), e a `RISK-007` a mantém assim para não recusar GEDCOM de exportador legítimo
com extensão atípica. O teste
`test_um_arquivo_de_extensao_estranha_com_conteudo_valido_e_aceito` existe para que ninguém
"conserte" o `accept` transformando-o em validação de extensão — isso quebraria aquela regra, e é
para o teste cair se acontecer.

O ganho real é **não oferecer o erro**: sem o filtro, o operador escolhe um `.txt`, recebe
*"carregado!"* e o arquivo não aparece em aba nenhuma.

## Por que extensão, e por que só `.ged`

**Extensão e não MIME.** No Windows o `.csv` costuma estar registrado como
`application/vnd.ms-excel`; um `accept="text/csv"` faria o seletor **esconder** arquivos `.csv`
legítimos em algumas máquinas. O teste `test_o_filtro_e_por_extensao_e_nao_por_tipo_mime` recusa
qualquer valor que não comece por ponto.

**`.ged` e não `.gedcom`.** Quem decide a aba é a extensão
(`reporting.lista_de_arquivos.ABA_DE_ARVORES = ".ged"`), e a comparação é `endswith`. Um arquivo
`x.gedcom` não entra em aba nenhuma — oferecê-lo no seletor seria convidar o operador a enviar um
arquivo que depois desaparece. Esconder é menos ruim do que prometer.

## `SHA_DA_TELA`, declarado

```
5e6842bec9258e912ca2f04b6a5ae92efa5fc937a4b124a7e77fda4459feedf7   (30.745 bytes)
39c6257f43419adb15fb521a63a03fdb2193feab6adadd8b10ca11db02fd0560   (30.759 bytes, +14)
```

`+14` é **exatamente** `accept=".ged" `, e nada mais. O campo do CSV não entra nesta conta: ele
vive no formulário da análise, que só existe depois de uma árvore carregada — medido, e não
suposto (`id="matches_csv"` aparece **0 vezes** na tela de entrada).

A primeira versão da mudança deu **+59 bytes**, e a diferença eram os comentários explicativos,
cujo whitespace entra no documento. Os dois fecham com `-#}` para não acrescentarem linha em
branco: sem isso a declaração estaria contando espaço em branco em vez de contar a regra.

## Um teste existente caiu, e a correção foi estreitá-lo

`tests/test_lista_na_tela.py::test_pasta_vazia_nao_despeja_nome_de_arquivo` usava
`".ged" not in corpo and ".csv" not in corpo` como **proxy** de "nenhum nome de arquivo vazou da
pasta vazia". O `accept` contém essas strings legitimamente, e o proxy passou a acusar configuração
de seletor como se fosse vazamento.

A correção foi **remover os atributos `accept` antes de procurar**, e não apagar a asserção: a
pergunta original — "algum NOME de arquivo vazou?" — continua igual, e qualquer outro `.ged` ou
`.csv` na página segue acusando. Um teste que protege algo real não se apaga porque ficou
incomodando; estreita-se o método.

## Verificação

| | |
|---|---|
| Suíte | **1015 passou, 9 pulados**, exit 0 |
| Teste novo | `tests/test_formatos_do_envio.py` — **8 testes** |
| Tela de entrada | 30.745 → **30.759** bytes, delta igual ao atributo |
| Campos de arquivo | 2 na aplicação inteira, os dois com `accept` |

## Resíduo declarado

1. **O `accept` não impede envio**, como dito acima. Se o objetivo for impedir de fato, a mudança é
   no servidor — e ela contraria a `RISK-007`, então precisa de decisão declarada do operador, não
   de um ajuste de template.
2. **O complemento pendente, e é o defeito medido:** um arquivo com extensão que não pertence a aba
   nenhuma é aceito, a tela responde *"carregado!"*, e ele **fica invisível sem explicação**. O
   filtro do seletor torna isso raro; não torna impossível (basta arrastar). O que falta é a tela
   dizer que a extensão não pertence a nenhuma aba — o lugar natural é a mensagem do envio, em
   `application/upload_gedcom.py`, ao lado das mensagens de substituição e de conteúdo idêntico que
   já existem. Não implementado aqui porque não foi pedido.
3. **A recusa de conteúdo é genérica por contrato.** A mensagem é *"Arquivo não reconhecido como
   GEDCOM. Favor, enviar o arquivo correto."*, e o motivo específico calculado por
   `validar_conteudo_gedcom` ("não começa com a declaração `0 HEAD`") **não chega à tela** —
   `RN-18`/`T039` fixam uma mensagem única. Registrado como observação, não como defeito.
