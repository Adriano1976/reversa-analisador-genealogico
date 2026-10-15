# Mudança — o seletor de arquivos oferece só o formato de cada aba

**Data:** 2026-10-14
**Tipo:** **apresentação** (atributo `accept`). Não altera validação, decisão nem contrato.
**Adendo:** `_reversa_sdd/addenda/021-seletor-de-arquivos-por-formato.md` (declara `SHA_DA_TELA`)
**Arquivo alterado:** `src/templates/index.html`
**Teste novo:** `tests/test_formatos_do_envio.py` (8 testes)
**Teste ajustado:** `tests/test_lista_na_tela.py` (proxy de vazamento estreitado)
**Servidor:** reiniciado (PID 24316) e verificado nos dois estados

## O pedido

> *"Na hora de 'Enviar nova árvore' na aba 'Analisador de DNA', o usuário deve somente visualizar
> os arquivos .ged para evitar o envio de arquivos de outros formatos. Essa regra deve ser aplicada
> para arquivos do tipo .csv também."*

## O que mudou

| Campo | Estado em que existe | Antes | Depois |
|---|---|---|---|
| `id="gedcom"` ("Enviar nova árvore") | **entrada**, sem árvore carregada | sem filtro | `accept=".ged"` |
| `id="matches_csv"` (relatório da análise) | **carregado**, no formulário da análise | sem filtro | `accept=".csv"` |

## O ponto que não pode passar em branco

**`accept` filtra o seletor; não é barreira.** Quem escolher "Todos os arquivos" manda o que
quiser, e **arrastar** o arquivo para o campo ignora o `accept` por completo. Do lado do servidor
não há nada olhando extensão — de propósito: a `RISK-007` manda validar **conteúdo**
(`0 HEAD`), para não recusar GEDCOM de exportador legítimo com extensão atípica.

O ganho é **não oferecer o erro**: sem o filtro, o operador escolhe um `.txt`, recebe
*"carregado!"* e o arquivo não aparece em aba nenhuma.

Por isso o teste `test_um_arquivo_de_extensao_estranha_com_conteudo_valido_e_aceito` **prende** o
comportamento em vez de elogiá-lo: se alguém transformar o `accept` em validação de extensão no
servidor, é para esse teste cair.

## Extensão, e não MIME — e só `.ged`

**Extensão**: no Windows o `.csv` costuma estar registrado como `application/vnd.ms-excel`, e um
`accept="text/csv"` esconderia `.csv` legítimos em algumas máquinas.

**Só `.ged`, não `.gedcom`**: quem decide a aba é a extensão
(`ABA_DE_ARVORES = ".ged"`, comparada com `endswith`). Um `x.gedcom` não entra em aba nenhuma —
oferecê-lo seria convidar o operador a enviar um arquivo que depois desaparece.

## `SHA_DA_TELA`, declarado

```
5e6842be…   (30.745 bytes)
39c6257f…   (30.759 bytes, +14)
```

`+14` é exatamente `accept=".ged" `. A primeira versão deu **+59**, e a diferença eram os
comentários explicativos, cujo whitespace entra no documento; os dois fecham com `-#}` para não
acrescentarem linha em branco.

## Verificação, nos dois estados

O campo do GEDCOM **não existe** com árvore carregada, e o do CSV **não existe** na entrada —
medir cada um no estado errado passaria por vacuidade. Verificado no servidor no ar:

| Estado | Campo verificado |
|---|---|
| Entrada (30.759 bytes) | `<input … id="gedcom" name="gedcom" accept=".ged" required>` |
| Carregado | `<input … id="matches_csv" name="matches_csv" accept=".csv">` |

| | |
|---|---|
| Suíte | **1015 passou, 9 pulados**, exit 0 |
| Testes novos | 8 (`tests/test_formatos_do_envio.py`) |

## Um teste existente caiu, e a correção foi estreitá-lo

`test_lista_na_tela.py::test_pasta_vazia_nao_despeja_nome_de_arquivo` usava
`".ged" not in corpo and ".csv" not in corpo` como **proxy** de "nenhum nome de arquivo vazou". O
`accept` contém essas strings legitimamente, e o proxy passou a acusar configuração de seletor
como se fosse vazamento. Corrigido **removendo os atributos antes de procurar** — a pergunta
original continua igual, e qualquer outro `.ged`/`.csv` na página segue acusando.

Um teste que protege algo real não se apaga porque ficou incômodo; estreita-se o método.

## Resíduo declarado

1. **O `accept` não impede envio.** Impedir de fato exige mudança no servidor, que contraria a
   `RISK-007` — decisão do operador, não ajuste de template.
2. **O complemento pendente, e é o defeito medido:** arquivo com extensão que não pertence a aba
   nenhuma é aceito, a tela diz *"carregado!"*, e ele **fica invisível sem explicação**. O filtro
   torna isso raro; arrastar ainda contorna. O lugar da correção é a mensagem do envio, em
   `application/upload_gedcom.py`, ao lado das mensagens de substituição e de conteúdo idêntico.
3. **A recusa de conteúdo é genérica por contrato** (`RN-18`/`T039`): o motivo específico
   ("não começa com a declaração `0 HEAD`") é calculado e não chega à tela. Observação, não defeito.
