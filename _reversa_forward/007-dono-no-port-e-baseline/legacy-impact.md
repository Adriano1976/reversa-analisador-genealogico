# Impacto no legado — feature `007-dono-no-port-e-baseline`

> Feature: `007-dono-no-port-e-baseline`
> Data: `2026-10-07`
> Âncora: **legado** — `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`
> Executor: `/reversa-coding`
> Medições: `evidence/` (T004, T010, T011, T012, T014, T015, T016)

## 1. Veredito em uma linha

**Nenhuma regra de negócio mudou.** A feature acrescenta o dono à assinatura de duas
portas internas — sem que ele participe de decisão nenhuma — e corrige o diretório
temporário da suíte. As dez mensagens de tela continuam idênticas em 19 casos
medidos, a paridade continua 100 %, o núcleo não foi tocado e nenhum limiar, peso ou
ordem de avaliação mudou de valor.

O impacto real não está no comportamento: está na **métrica de verificação** do
projeto, que deixou de ter 15 testes cegos.

## 2. Arquivo afetado, componente, tipo e severidade

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/ports/__init__.py` | `src/ports/` (`architecture.md#3`) | `regra-alterada` | **MEDIUM** | `ArmazenamentoDeArquivos.guardar`, `.resolver` e `CarregadorDeArvores.carregar` ganham `dono` obrigatório. É contrato de fronteira: uma chamada montada sem ele deixa de compilar. Nenhum método novo, nenhuma remoção |
| `src/ports/adaptadores.py` | `src/ports/` (`architecture.md#3`) | `regra-alterada` | **MEDIUM** | `ArmazenamentoEmDisco` aceita o dono e **não o usa**; `CarregadorDeArvoresGedcom` o repassa a `resolver`. A regra do armazenamento — chave por conteúdo, validação antes da gravação, não regravar — está **intacta** |
| `src/application/upload_gedcom.py` | `application/` (adendo da 006) | `regra-alterada` | LOW | Duas linhas: repassa o dono já recebido a `guardar` e a `carregar`. Nenhum passo do caso de uso mudou |
| `src/app.py` | `architecture.md#1` | `regra-alterada` | LOW | Dois pontos de chamada passam a citar `DONO_DO_PROCESSO`; o comentário da constante passa a nomear a dívida #3. `index()` **não** ganhou passo de domínio |
| `tests/conftest.py` | *(infraestrutura de teste — fora da extração)* | `regra-alterada` | **MEDIUM** | Passa a ser a autoridade do diretório temporário da suíte. É o que devolve 15 testes à cobertura. Não é componente do sistema extraído, mas muda o que a verificação do projeto enxerga |
| `tests/test_porta_de_armazenamento.py` | *(infraestrutura de teste — fora da extração)* | `regra-alterada` | LOW | Classe nova com 12 provas do contrato; cabeçalho corrigido. Asserções existentes **intocadas** |
| `tests/test_ambiente_temporario_da_suite.py` | *(infraestrutura de teste — fora da extração)* | `componente-novo` | LOW | Arquivo novo, 3 testes. Prende a correção do ambiente, que de outro modo seria invisível |
| `tests/test_upload_seguranca.py` | *(infraestrutura de teste — fora da extração)* | **presença** | — | **NÃO FOI TOCADO.** `git diff --stat` vazio. Os 15 testes executam por efeito do `conftest.py` |
| `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/` | `architecture.md#3` | **presença** | — | `git diff --name-only` vazio nos quatro. A `RF-11` medida |
| `_reversa_sdd/parity/harness.py` | `migration/parity_harness.md` | **presença** | — | Nenhuma alteração. É o instrumento da `RF-10` |
| Dívidas #3, #4, #5, #8, #10, #17, #18 | `architecture.md#7` | **presença** | — | **TODAS INALTERADAS.** A #3 e a #4 passam a estar **nomeadas** no comentário da constante |

## 3. Diff conceitual, por componente

### 3.1 `src/ports/` — o dono chega à segunda porta, sem comportamento

A feature anterior fixou o dono no `RepositorioDeArvores` e o deixou fora do
`ArmazenamentoDeArquivos`. A assimetria era o problema: a Onda 3 teria de reabrir a
assinatura da porta **e todos os seus chamadores**.

Agora as três portas exigem o dono, na mesma forma — **último parâmetro posicional,
sem valor padrão** —, o que é o RNF de Manutenibilidade da feature. Nenhum método
novo foi criado: `CarregadorDeArvores` continua com **um** método, que era a condição
declarada da `D-02` da feature 006, e a condição era sobre a contagem de métodos.

**O dono não participa de decisão nenhuma.** Ele não entra na chave, no nome
armazenado nem no caminho; não filtra a resolução; não altera a ordem de validação.
Duas entradas do mesmo conteúdo com donos diferentes continuam chegando ao **mesmo**
arquivo — medido em `evidence/T010` (a prova inclui marcar o arquivo gravado e
conferir que a marca sobrevive, para distinguir "reusou" de "regravou").

O motivo de ele ir **por chamada** em `carregar`, e não na construção do adaptador,
é o mesmo que sustenta a feature: os adaptadores são **singletons de processo**,
montados uma vez no import de `src/app.py`. Congelar identidade neles é exatamente o
que a Onda 3 teria de desfazer.

### 3.2 A borda — o valor do dono tem um lugar só

`DONO_DO_PROCESSO` continua declarada em `src/app.py`, e o comentário dela passou a
nomear a **dívida #3** ao lado da #4, além de declarar que não é mecanismo de
segurança. A `RF-04` exigia as duas coisas do lugar onde a constante vive: ser o
único, e **dizer** o que ela não é.

Os três pontos da borda que **fornecem** o valor a citam; o caso de uso apenas
**repassa** o que recebe. Nenhum chamador escreve o literal no próprio local — e
isso não é observável em execução, porque passar a constante ou o literal produz o
mesmo comportamento. Por isso a prova é a varredura de forma
(`evidence/_t011_varredura.py`), e não um teste.

### 3.3 O núcleo — intocado, e a prova disso é dupla

Nenhuma linha de `src/core/`, `src/parsers/`, `src/reporting/` ou `src/utils/`
mudou. A assinatura de retorno do núcleo continua congelada: `path_search` e
`dna_analysis` devolvem a tupla de três com o indicador de sucesso, e o `Tree`
continua com quatro elementos. As duas provas são independentes — o `git diff`
vazio e a paridade em 100 %.

### 3.4 A verificação — a mudança de maior consequência prática

Antes desta feature, 15 testes de rota de `tests/test_upload_seguranca.py` **não
executavam** nesta máquina. Eles são justamente os da superfície que a Onda 2
reescreveu, e foi por isso que a 006 precisou construir uma sonda à mão para medir o
`app.py`.

A causa, medida: o `TempPathFactory.getbasetemp()` do pytest cria
`<temp>/pytest-of-<usuário>` com `mode=0o700`, e o `os.scandir` de
`_pytest/pathlib.py:175` não consegue **listá-lo**. A correção declarou o fixture
`tmp_path` em `tests/conftest.py`, delegando a `pasta_temporaria`, e com isso
`getbasetemp()` não é mais chamado.

| Medição | Antes | Depois |
|---|---|---|
| Suíte | `231 passed, 15 errors` | **`261 passed, 0 errors`** |
| `test_upload_seguranca.py` | `21 passed, 15 errors` | **`36 passed`** |
| Paridade | `100 %`, exit 0 | **`100 %`, exit 0** |
| Mensagens de tela (19 casos) | referência da 006 | **zero divergência** |
| Resíduo em `tests/.tmp/` | *(não existia)* | **ausente** |

A aritmética, que importa para a `RN-04`: `231` aprovados que já existiam, `+15` que
passaram a **executar** (não são testes novos), `+3` do arquivo novo de guarda, `+12`
das provas de contrato do `T010` = **261**.

## 4. Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam **intactas**, com o instrumento
que sustenta cada uma:

- **As dez mensagens da camada de rota** (`domain.md#5.1`) e as nove congeladas de
  `12-paridade-telas.feature`: ao caractere, no mesmo caso. Medido em **19 casos**
  com comparação de status HTTP, classe do alerta e texto (`evidence/T012-mensagens.txt`).
- **O contrato de armazenamento** (`domain.md#3.5`): chave `sha256` truncada em 16
  hex, forma `<chave>__<nome visível>`, conteúdo já armazenado não é regravado,
  extensão original preservada, teto de 16 MB, validação de conteúdo **antes** da
  gravação. Conferido item a item em `data-delta.md` §3.
- **A assimetria do CSV** (`dívida #10`): o CSV de DNA continua **sem** validação de
  conteúdo. Preservada de propósito.
- **A assinatura de retorno do núcleo** e o `Tree` de quatro elementos.
- **As nove faixas de cM, o score difuso, o teto de 20 saltos do BFS, o teto de 40
  do caminho indireto e a ordem de apresentação** — paridade em 100 % nas 6 fixtures.
- **O fallback Latin-1 do CSV** e o **fallback de nome** (`AMB-024`).
- **A autoridade única de `utils/validate.py`** sobre a regra de upload: o adaptador
  continua **chamando**, não reimplementando.
- **A distinção "não achei" × "entrada inválida"**: continua saindo do campo de
  desfecho, nunca do texto da mensagem.

## 5. Modificadas

Só há uma coisa modificada neste documento, e ela não é comportamento: **a métrica**.
O par `178 aprovados, 15 erros de ambiente` (feature 005) e o par
`231 aprovados, 15 erros` (feature 006) passam a ser leitura **histórica**. Nenhum
dos dois é reescrito nos artefatos que os registraram — a marca de histórico vive
nos artefatos desta feature, como a `RN-04` exige.

A regra de comparação muda junto: deixa de ser **total** e passa a ser **conjunto**.
Nenhum aprovado pode virar falha; comparar totais contra os números antigos compara
coisas diferentes, porque os conjuntos de testes que executam não são os mesmos.

Além disso, e sem tocar em regra do legado: **um comentário** de `src/app.py` foi
reescrito (nomeando a dívida #3 e removendo o "nesta onda"), e **um parágrafo de
cabeçalho** de `tests/test_porta_de_armazenamento.py` foi corrigido porque a correção
do ambiente o tornou falso.

## 6. O que este impacto **não** inclui

- **Não** fecha a dívida #4 (isolamento). Nenhum arquivo é separado por dono.
- **Não** fecha a dívida #3 (corrida entre requisições concorrentes). A guarda de
  exclusividade continua de processo, não de thread.
- **Não** implementa o `RepositorioDeArvores`, que segue sem consumidor.
- **Não** cria superfície de compatibilidade: o dono não tem valor padrão e não há
  sobrecarga que aceite a chamada antiga.
- **Não** remove nenhum dos 13 diretórios presos, e **não** altera `pytest.ini` nem
  `.gitignore`, que estão fora de `allowedPaths`.
- **Não** altera a superfície HTTP: mesmas rotas, campos, status e literais.
