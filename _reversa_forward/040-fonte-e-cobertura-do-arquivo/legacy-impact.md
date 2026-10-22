# Legacy impact: fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Política de edição do legado no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**`, `tests/**`, `docs/**` e os arquivos de raiz do projeto.
> Todos os caminhos tocados estão dentro de `src/**` e `tests/**`; nada fora da lista foi escrito.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/fontes_de_laboratorio.py` | — | componente-novo | LOW | Catálogo declarado de 11 laboratórios, tradução de valor e escolha dentro do kit |
| `src/core/qualidade_da_medida.py` | — | componente-novo | LOW | Pisos (15,0 cM / 900 SNPs) e estado `robusta`/`parcial`/`insuficiente` |
| `src/core/cobertura_do_arquivo.py` | — | componente-novo | LOW | Medida do arquivo derivada das evidências já montadas |
| `src/core/genetic_evidence.py` | `analise-dna` | regra-alterada + regra-nova | **MEDIUM** | `source` passa de texto cru a rótulo canônico (com `source_raw`/`source_motivo`); escolha nova dentro do kit; aviso `fontes_divergentes`; chave `medida` |
| `src/core/dna_analysis.py` | `analise-dna` | contrato-alterado | LOW | Coletor opcional `cobertura`; retorno de três posições preservado |
| `src/application/dna_analysis.py` | fronteira de aplicação | contrato-alterado | LOW | `ResultadoDeAnalise.cobertura` (default `None`) |
| `src/app.py` | borda HTTP | contrato-alterado | LOW | Passa `cobertura` ao render do ramo `dna_analysis`; nenhum outro ramo |
| `src/templates/index.html` | apresentação | delta-de-contrato-externo | **MEDIUM** | Bloco "Cobertura do arquivo", linha `Fonte:` com etiqueta e linha da medida no bloco 2 |
| `src/assets/app.css` | apresentação | contrato-alterado | LOW | Grade do painel e linha da medida; nenhuma classe existente muda |
| `tests/fixtures/sample_dna.py` | — | componente-novo | LOW | Constantes sintéticas de fonte suja, três faixas de medida e divergência |
| `tests/test_fontes_de_laboratorio.py` | — | componente-novo | LOW | 63 casos do catálogo, da escolha e do payload |
| `tests/test_qualidade_da_medida.py` | — | componente-novo | LOW | Limites 14,99/15,00 e 899/900 |
| `tests/test_cobertura_do_arquivo.py` | — | componente-novo | LOW | Oito números, percentuais, ordenação, vazio |
| `tests/test_fonte_e_cobertura_na_tela.py` | — | componente-novo | LOW | Painel, fonte e medida na página renderizada |

## 2. Diff conceitual por componente

**`core.genetic_evidence`.** O dicionário da evidência deixa de guardar o texto cru em `source`
e passa a guardar **rótulo canônico** (`Genera`, `meuDNA`, …, `não declarada`, `outro`), com:

- `source_raw` — a célula original, para a tela exibir a etiqueta;
- `source_motivo` — por que não é laboratório, quando não é;
- `medida` — o estado da medida, com números, motivos e a ressalva.

A regra de escolha dentro do kit mudou: era "primeira linha não vazia", passa a ser **primeira
linha com laboratório reconhecido**, caindo para a primeira não vazia. Um kit que declara dois
laboratórios emite `fontes_divergentes` (nível `cartao`) e exibe o primeiro. `LIMITE_SEGMENTO_FRACO`
passa a referenciar `qualidade_da_medida.PISO_MAIOR_BLOCO_CM` — mesmo valor `15.0`, dono único.

**`core.dna_analysis`.** Ganha o coletor `cobertura=None`, preenchido com
`cobertura_do_arquivo.medir(evidencias, len(df))` logo depois de `build_genetic_evidence`. O
retorno continua `(resultados, descartados, mensagem)`.

**Aplicação e borda.** O caso de uso cria `_cobertura = {}`, passa ao núcleo e expõe em
`ResultadoDeAnalise.cobertura`; a borda repassa ao template **somente** no ramo `dna_analysis`.
Fora dele, `cobertura` é `None` — é o que mantém a tela de entrada byte a byte.

**Template.** O painel entra fora da guarda `dna_results`, com o `{% if %}` na mesma linha do
`{% endif %}` anterior (senão o hash da entrada mudaria por whitespace). O cabeçalho do painel
usa `cabecalho-da-cobertura` além de `card-header`, para não ser contado como cartão de
resultado. A linha `Fonte:` mostra o rótulo e, quando difere, o original em etiqueta. A linha
da medida entra depois da grade do kit, sem cor por estado.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.2 — chave de evidência é (nome, kit); kits diferentes nunca somados; `totals.cm` é `None` quando há mais de um kit | `test_dna_analysis.py`, `test_observacoes_do_arquivo.py`, caracterização |
| §3.2 — cM acumulado nunca arredondado no núcleo | `test_formatacao_cm.py` |
| §3.9 — ordem de apresentação (documental primeiro, cM decrescente) | `test_sem_correspondencia.py`, caracterização |
| `BR-D-12` (chave nome+kit), `BR-D-14` (nunca somar), `BR-D-15` (sem arredondamento), `BR-D-17` (fraca abaixo de 15 cM) | `code-analysis.md#44`; testes acima |
| §2 — os três eixos não se contaminam; o cM não afirma parentesco | confronto, veredito e hipóteses intocados; a ressalva da medida é explícita |
| §3.8 — leitura tolerante: descartar sim, esconder não | o valor original da fonte é preservado e exibido em etiqueta |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| `data-dictionary.md#51` — `source` é "texto declarado, primeira não vazia encontrada" | passa a ser **rótulo canônico**; o cru vive em `source_raw`; a escolha prefere laboratório reconhecido | `core/genetic_evidence.py` |
| `data-dictionary.md#54` — `evidence_for.source` | mesmo texto quando não há coluna; com coluna, devolve o rótulo; ganha `source_original` | `core/genetic_evidence.py` |
| `data-dictionary.md#51` (payload) | três chaves novas: `source_raw`, `source_motivo`, `medida` | idem |

> **Para o `/reversa-sync`:** `data-dictionary.md#51` e `#54`, `code-analysis.md#46` (dono do
> 15,0) e a descrição de `source` nos fluxos de `analise-dna` precisam absorver este delta. O
> comportamento não muda para o arquivo sem coluna de fonte (`source` continua `None`).

## 5. Achado fora do escopo, registrado

O harness de paridade está com **30 divergências pré-existentes** (motivo humanizado da feature
038, aceitação das features 024/034 e 18 em `ancestral`). A entrega 040 não toca nenhuma
observação comparada pelo coletor. A análise completa está em `evidence/depois/paridade.txt`; a
decisão (atualizar o oráculo ou tratar como regressão) é humana.
