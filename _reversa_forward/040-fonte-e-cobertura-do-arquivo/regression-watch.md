# Regression watch: fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/core/genetic_evidence.py`; `data-dictionary.md#51` | `source` da evidência exibe **rótulo canônico** (`Genera`, `meuDNA`, …, `não declarada`, `outro`), nunca a célula crua | presença | a tela volta a mostrar `GENERA`, `Meu DNA` ou texto de formulário como rótulo |
| W002 | `src/core/fontes_de_laboratorio.py` | `source_raw` preserva a célula original e `source_motivo` explica o que não é laboratório | presença | `source_raw` some do payload, ou o motivo é `None` para valor não-laboratório |
| W003 | `src/core/fontes_de_laboratorio.py` | A escolha dentro do kit prefere a **primeira linha com laboratório reconhecido**; sem nenhuma, cai para a primeira não vazia | presença | um `-` na primeira linha volta a esconder um laboratório declarado adiante |
| W004 | `src/core/genetic_evidence.py` | Dois laboratórios no mesmo kit emitem o aviso `fontes_divergentes` (nível `cartao`), com os dois rótulos | presença | a divergência volta a ser resolvida em silêncio |
| W005 | `src/core/genetic_evidence.py` | Toda evidência carrega `medida` com `estado`, `rotulo`, `motivos`, `numeros` e `ressalva` | presença | a chave some, ou o estado deixa de acompanhar os três pisos |
| W006 | `src/core/qualidade_da_medida.py` | `insuficiente` quando total < 15,0; `parcial` quando bloco < 15,0 ou SNPs < 900; `robusta` no resto; SNPs ausentes **não** penalizam | redação | um dos pisos muda de valor sem decisão declarada; ausência de SNPs passa a penalizar |
| W007 | `src/core/cobertura_do_arquivo.py` | A cobertura é derivada das evidências já montadas e traz linhas, evidências, kits, laboratórios, grafias, cromossomos, mediana, percentuais e motivos de fonte | presença | surge leitura nova de CSV, ou o painel passa a calcular na aplicação |
| W008 | `src/application/dna_analysis.py` | `ResultadoDeAnalise.cobertura` existe, com default `None`; a projeção histórica **não** a inclui | presença | o campo passa a ser obrigatório, ou entra no payload da porta de histórico |
| W009 | `src/templates/index.html` | O painel fica **fora** da guarda `dna_results`, nasce aberto e não é cartão de resultado | presença | o painel some com zero cartões, ou passa a ser contado por `_cabecalhos()` |
| W010 | `tests/test_icone_de_atalho.py` | `SHA_DA_TELA` continua `7375696d…` e 16504 bytes com `cobertura=None` | presença | o hash muda sem adendo declarado |
| W011 | `src/core/dna_analysis.py` | O retorno de `dna_analysis` continua com **três** posições (`resultados`, `descartados`, `mensagem`) | redação | um quarto valor entra no retorno |

## Observações (sem peso de regressão)

- 🔴 **Paridade com 30 divergências pré-existentes** (2026-10-22): motivo humanizado da feature
  038, aceitação das features 024/034 e 18 em `ancestral`. Nenhuma vem da 040 — o coletor do
  harness não captura `source`, `medida` nem `cobertura`. A última medição com 100% é de
  2026-10-13. **Decisão humana pendente:** atualizar o oráculo de forma declarada ou tratar como
  regressão real.
- 🟡 **`TestCompany` não é reconhecida como coluna de fonte** (`genetic_evidence.py:86`): o export
  um-para-muitos do GEDmatch perde a fonte. Fora do escopo da 040.
- 🟡 **`source` não tem regra `BR-D`** no `code-analysis.md`; a única descrição é a linha do
  `data-dictionary.md#51`, que esta feature alterou. Candidato a `/reversa-sync`.
- 🟡 **`Meu Patrimônio` e as três grafias de "Minha herança"** ficaram `não declarada` por decisão
  do operador (2026-10-22). Se algum dia forem confirmadas como laboratório, é mudança de
  catálogo, com teste e declaração — não ajuste silencioso.

## Histórico de re-extrações

*(vazio — preenchido pelo agente reverso quando `/reversa` rodar de novo)*

## Arquivadas

*(vazio)*
