# Regression Watch: renomear a raiz de código de `analisador-genealogico/` para `src/`

> Identificador da feature: `003-renomear-pasta-app-para-src`
> Data: `2026-10-03`
> Base: `legacy-impact.md` desta feature
> Peso: os itens abaixo são condições **estruturais** estabelecidas por esta feature, verificadas na execução. Uma extração futura deve encontrá-las verdadeiras.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/inventory.md#2`, `#4` | A raiz de código se chama `src/` e o núcleo é importado direto dela, como os pacotes de primeiro nível `parsers.*`, `core.*`, `reporting.*` e `utils.*`, sem nível de pacote intermediário | presença | Reaparecimento de um diretório com o nome antigo contendo código, reaparecimento do nível `reconstructed`, ou mudança dos nomes dos pacotes do núcleo |
| W002 | `_reversa_sdd/dependencies.md#1` | O arquivo de dependências está na raiz do repositório | presença | Arquivo de dependências dentro de `src/`, ou ausente da raiz |
| W003 | `_reversa_sdd/architecture.md#3.3`, `addenda/bug-BUG-20260929-QMLY-v001.md#2` | A pasta de upload é `src/uploads/` e é resolvida a partir do arquivo do aplicativo, nunca do diretório corrente | presença | Resolução por caminho relativo ao diretório corrente; divergência entre o caminho de escrita e o de leitura |
| W004 | `_reversa_sdd/inventory.md#2` | O README herdado do módulo, o arquivo de ignore do módulo e o diretório vazio de artefatos estáticos **não existem** | ausência | Reaparecimento de `src/README.md`, `src/.gitignore.txt` ou `src/static/` |
| W005 | `.reversa/principles.md#II`; `_reversa_sdd/parity/` | A paridade de comportamento com o oráculo congelado permanece em 100%, e a suíte mantém o mesmo conjunto de testes | presença | Divergência nova no comparador; teste removido, desabilitado ou com resultado diferente |

> **Atualização 2026-10-03, `OPP-20261003-FLAT`.** O `W001` vigiava `reconstructed.*`. A transformação `FLAT` apagou esse nível de pacote, e o núcleo passou a ser importado direto de `src/` como `core.*`, `parsers.*`, `reporting.*` e `utils.*`. A condição foi reescrita para a nova identidade. A avaliação está em `_reversa_refactor/pacote-reconstructed/transformations/OPP-20261003-FLAT-achatar-o-nivel-de-pacote/transformation.md`, e nenhuma regra de negócio mudou: a suíte e a paridade foram remedidas. A observação `O5` perde o objeto, porque o `__init__.py` que ela cita deixou de existir.

## Observações

Itens sem peso de regressão. Não eram regras confirmadas antes da mudança, ou são imprecisões conhecidas que esta feature não resolveu:

- **O1** — A contagem de pontos de alteração no requisito de testes da feature fala em 9; a medição encontrou 16 inserções de caminho em 8 arquivos, das quais 9 linhas nomeiam o diretório. A decisão D-09 do roadmap registra a correção; o texto do requisito não foi alterado.
- **O2** — `_reversa_sdd/architecture.md#3.3` aponta a pasta de upload para o símbolo `UPLOAD_FOLDER`, que não existe mais no módulo do núcleo: ele migrou para o arquivo de entrada, e a resolução passou a ser feita por função ancorada no próprio arquivo. O adendo desta feature registra a mudança de leitura.
- **O3** — `_reversa_sdd/architecture.md#5` acumula dívidas desatualizadas por motivos alheios a esta feature: a dívida 9 perdeu o objeto com a remoção do README herdado; a dívida 4 deixou de valer quando o upload ganhou validação e teto; a dívida 6 afirma ausência de fluxo de publicação, e existe um no repositório.
- **O4** — A regeneração do mini-site de documentação ficou pendente (`T021`). Enquanto ela não rodar, o site derivado continua citando o caminho antigo.
- **O5** — A citação ao nome do projeto dentro de `src/reconstructed/__init__.py` é intencional e não é um caminho: o projeto continua se chamando `analisador-genealogico`, apenas a raiz de código mudou.

## Histórico de re-extrações

### Re-extração 2026-10-05 03:05

**Primeira verificação real destes watch items.** Eles foram publicados em 2026-10-03, depois do congelamento do SDD de 2026-09-30; a extração de **2026-10-05** é a primeira que regenera o `_reversa_sdd/` a partir do código atual.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | `src/` é a raiz de código, e o núcleo é importado direto dela como `core.*`, `parsers.*`, `reporting.*` e `utils.*`. Verificado no disco: `src/` contém exatamente esses quatro pacotes (mais `templates/` e `uploads/`). **`src/reconstructed/` não existe.** Registrado em `inventory.md` §2 e `c4-components.md`. |
| W002 | 🟢 verde | `requirements.txt` está na raiz do repositório. Verificado no disco, e registrado em `inventory.md` §2 e `architecture.md`. |
| W003 | 🟢 verde | A pasta de upload é `src/uploads/`, resolvida por `_pasta_uploads()` **ancorada no arquivo do app** — escrita e leitura usam o mesmo caminho. Contratado em `upload-gedcom/contracts.md` §2.2 e `adrs/17`. |
| W004 | 🟢 verde | Ausências confirmadas no disco: `src/README.md`, `src/.gitignore.txt` e `src/static/` **não existem**. Registrado em `inventory.md` §2 ("Ausências confirmadas"). |
| W005 | 🟢 verde | **Paridade remedida em 2026-10-05: 100 % (zero divergência) em 6/6 fixtures**, com o harness diferencial contra o oráculo congelado. A suíte cresceu para **179 itens** e **164 passam** (15 erros de ambiente, pré-existentes e de mesma natureza dos já registrados); **nenhum teste foi removido ou desabilitado**. |

> ⚠️ **A paridade NÃO foi medida em árvore real nesta passagem.** A execução sobre `Arvore_Unificada_Oficial_V1_2.ged` (35.460 pessoas) estourou o teto de tempo do próprio harness (600 s). O resultado de 2026-09-28 (5/5 árvores reais) segue como referência **histórica**, não como verificação desta rodada.
>
> **Nota operacional para a próxima passagem:** o `--gedcom` do harness exige **caminho absoluto** — o oráculo roda em diretório isolado (`.parity-run-oracle/`) e um caminho relativo resolve contra lá, produzindo `FileNotFoundError` no lado do oráculo e uma "divergência" que é artefato do probe.

## Histórico de re-extrações (formato anterior)

| Data | Extração | Veredito | Observação |
|------|----------|----------|------------|
| — | — | — | Nenhuma re-extração executada desde a publicação deste watch. |

## Arquivadas

| ID | Motivo do arquivamento | Data |
|----|------------------------|------|
| — | Nenhum item arquivado. | — |
