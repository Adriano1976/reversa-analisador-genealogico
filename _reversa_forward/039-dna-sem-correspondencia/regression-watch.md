# Regression watch: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` | O cM continua sem decidir aceitação; o bloco é somente leitura derivada e não cria cartão | presença | Um descarte sem candidato compatível vira cartão, ou o conjunto de aceitos/descartes da análise real muda (8/448) |
| W002 | `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` | A lista completa continua com todos os descartes e o CSV continua com nove colunas | presença | O bloco de descartes perde itens, ou o CSV muda de coluna/posição |
| W003 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4-regras-de-negócio-novas-ou-alteradas` (RN-04, RN-07) | O bloco não afirma parentesco, não mostra diagrama/confronto e não oferece promoção | presença | O HTML do bloco contém "Parentesco documental", "conexão com", diagrama ou "usar este candidato" |
| W004 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4` (RN-01) | Nome que já tem cartão em qualquer kit não aparece no bloco | presença | Um nome com cartão aparece no bloco; o mesmo nome em outro kit entra |
| W005 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4` (RN-01, RN-08) | O bloco lista somente `cm >= 40,0` sem candidato compatível | presença | Um item de 39,9 cM entra, ou um descarte com candidato compatível aparece no bloco |
| W006 | `tests/test_icone_de_atalho.py` | `SHA_DA_TELA` e `TAMANHO_ESPERADO` continuam `7375696d…` e 16.504 bytes | presença | O teste do hash falha; a tela de entrada mudou |
| W007 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4` (RN-10) | O bloco renderiza mesmo com zero cartões, desde que haja item | presença | Uma análise sem cartões e com item de cM alto não mostra o bloco |
| W008 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4` (RN-01, RN-03) | O item é por (nome, kit); dois kits do mesmo nome são duas linhas e nunca há soma | presença | Um nome com dois kits aparece com um cM somado, ou um kit desaparece |
| W009 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#4` (RN-03) | O MRCA exibido é a estimativa do relatório de DNA, rotulada como estimada, e não um ancestral documentado | presença | O bloco mostra "MRCA documental", um `xref` de ancestral ou um MRCA que não veio do CSV |

## Histórico de re-extrações

*(vazio; será preenchido quando uma extração `/reversa` passar por esta feature)*

## Arquivadas

*(vazio)*

## Observações

- 🟡 `mrca_generations` é um campo do payload do kit que **não** está listado em
  `_reversa_sdd/data-dictionary.md#51`. A feature o consome por contrato de código
  (`src/core/genetic_evidence.py`); a documentação da extração fica devendo a linha. Não
  é item de regressão enquanto a extração não o confirmar — candidato a `/reversa-sync`.
- 🟡 O corte de 40,0 cM é uma **triagem declarada**, não uma faixa de parentesco
  publicada. Se ele mudar, a medição de 9 casos (154,5; 52,5; 51,3; 50,5; 45,8; 43,7;
  43,3; 42,6; 41,2) e o `requirements.md` precisam mudar junto; não há teste que prenda o
  número à faixa do Shared cM Project, porque ele não pertence a ela.
- 🟡 A lista de trabalho em CSV continua sendo a via completa; o bloco novo **não** é
  exportado separadamente. Se uma próxima feature criar um CSV do bloco, ela precisa
  declarar isso como contrato próprio e não tocar nas nove colunas atuais.
- 🟡 O `mrca_generations` do dicionário de descarte ficou **sem consumidor** depois da
  E003: o cartão lê o MRCA de `genetic_evidence`. É um resíduo declarado; removê-lo
  (B+) mexeria na caracterização e fica para outra decisão.

## Emendas 2026-10-22

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W010 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#emendas` (E001) | O corte de triagem é **20,0 cM**, inclusivo; 19,9 fica de fora e 20,0 entra | presença | Um item de 19,9 cM aparece, um de 20,0 some, ou o corte volta a 40,0 |
| W011 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#emendas` (E002) | Os itens sem correspondência são **cartões na lista de resultados**, com o rótulo "Parentesco documental não encontrado", as cinco seções e sem diagrama/promoção; a lista completa e o CSV continuam intactos | presença | O bloco separado volta; o item não vira cartão; o cartão tem diagrama ou promoção; a lista/CSV perde itens |
| W012 | `_reversa_forward/039-dna-sem-correspondencia/requirements.md#emendas` (E003) | A contagem de sem correspondência é **derivada dos próprios cartões** (`sem_correspondencia: True`); não há segunda seleção. A lista completa, o CSV e a promoção continuam iguais | presença | O resumo mostra um número diferente do de cartões marcados; `core.sem_correspondencia.selecionar` volta; `sem_correspondencia` deixa de conter os cartões; a lista/CSV ou a promoção muda |

`W005` (corte de 40,0) e `W007` (bloco renderiza sem cartões) estão **substituídos** por
`W010` e `W011`; ficam no histórico como registro da primeira entrega, não como regra
vigente. A `W012` fecha a vigilância da E003: a contagem deriva dos cartões, sem segunda
seleção. A vigilância vigente é `W001`–`W012`.
