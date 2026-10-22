# Actions: Fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/040-fonte-e-cobertura-do-arquivo/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 20 |
| Paralelizáveis (`[//]`) | 14 |
| Maior cadeia de dependência | 11 (T003 → T005 → T009 → T010 → T012 → T013 → T014 → T015 → T016 → T018 → T020) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Medir a linha de base antes de tocar em código: suíte completa, `tests/rodar_paridade.py` e `SHA_DA_TELA`, gravando `evidence/antes/suite.txt`, `evidence/antes/paridade.txt` e `evidence/antes/hash.txt` | - | `[//]` | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/evidence/antes/suite.txt` | 🟢 | `[X]` |
| T002 | Rodar a análise real (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`, raiz `Adriano Santos`) e gravar o estado de hoje: cartões, descartes, as fontes cruas exibidas e a ausência do painel, em `evidence/antes/analise.txt` | - | `[//]` | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/evidence/antes/analise.txt` | 🟢 | `[X]` |
| T003 | Estender `tests/fixtures/sample_dna.py` com a coluna de fonte suja (`Genera`, `GENERA`, `-`, `Selecione uma empresa ou fonte`, `Minha herança`, `L1b1a`, valor inventado) e com evidências nas três faixas de medida (14,99 cM; 15,00/15,00 com 899 SNPs; 15,00/15,00 com 900 SNPs) | - | `[//]` | `tests/fixtures/sample_dna.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar `tests/test_fontes_de_laboratorio.py`: catálogo dos 11 rótulos, aliases por caixa/acento, texto de formulário, empresa não confirmada, nome de projeto, haplogrupo, valor desconhecido, escolha da primeira linha com laboratório e detecção de divergência no kit | T003 | `[//]` | `tests/test_fontes_de_laboratorio.py` | 🟡 | `[X]` |
| T005 | Criar `tests/test_qualidade_da_medida.py`: `robusta` em 15,00/15,00/900, `parcial` em 15,00/15,00/899, `parcial` em 15,00/14,99/900, `insuficiente` em 14,99, SNPs ausentes não penalizam e bloco ausente conta como abaixo do piso | T003 | `[//]` | `tests/test_qualidade_da_medida.py` | 🟢 | `[X]` |
| T006 | Criar `tests/test_cobertura_do_arquivo.py`: os oito números, mediana, percentuais, ordenação dos laboratórios (contagem decrescente, alfabética no empate), arquivo sem coluna de fonte e lista de evidências vazia | T003 | `[//]` | `tests/test_cobertura_do_arquivo.py` | 🟡 | `[X]` |
| T007 | Criar `tests/test_fonte_e_cobertura_na_tela.py`: painel presente com evidência e ausente sem evidência, posição fora da guarda dos cartões, `Fonte:` canônica com etiqueta do texto original, linha da medida no bloco 2 com a ressalva, e ausência dos textos de formulário como rótulo | T003 | `[//]` | `tests/test_fonte_e_cobertura_na_tela.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Criar `src/core/fontes_de_laboratorio.py` com `LABORATORIOS` (11 rótulos), a tabela de alias normalizado, os motivos (`texto_de_formulario`, `empresa_nao_confirmada`, `nome_de_projeto`, `haplogrupo`, `nao_reconhecida`), `rotulo(valor)` e `escolher(valores)` | T004 | `[//]` | `src/core/fontes_de_laboratorio.py` | 🟡 | `[X]` |
| T009 | Criar `src/core/qualidade_da_medida.py` com `PISO_TOTAL_CM`, `PISO_MAIOR_BLOCO_CM`, `PISO_SNPS`, os três estados e `avaliar(total_cm, largest_segment_cm, snps_total)`, e fazer `LIMITE_SEGMENTO_FRACO` de `genetic_evidence` referenciar `PISO_MAIOR_BLOCO_CM` sem mudar o valor 15.0 | T005 | `[//]` | `src/core/qualidade_da_medida.py`, `src/core/genetic_evidence.py` | 🟡 | `[X]` |
| T010 | Criar `src/core/cobertura_do_arquivo.py` com `medir(evidencias, linhas)` devolvendo o dicionário do `data-delta.md` §4, reaproveitando `CM_MINIMO_SEGMENTO` de `core.endogamia` e `PISO_MAIOR_BLOCO_CM` de `qualidade_da_medida` | T006, T009 | `[//]` | `src/core/cobertura_do_arquivo.py` | 🟡 | `[X]` |
| T011 | Integrar em `src/core/genetic_evidence.py`: `source` canônico, `source_raw`, `source_motivo`, a chave `medida` e o aviso `fontes_divergentes` (nível `cartao`, com os dois rótulos), sem tocar em total de cM, segmentos ou decisão de aceitação | T008, T009 | - | `src/core/genetic_evidence.py` | 🟡 | `[X]` |
| T012 | Acrescentar o coletor opcional `cobertura` a `dna_analysis` em `src/core/dna_analysis.py` e preenchê-lo com `cobertura_do_arquivo.medir(evidencias, len(df))` logo depois de `build_genetic_evidence`, mantendo o retorno de três posições | T010, T011 | - | `src/core/dna_analysis.py` | 🟡 | `[X]` |
| T013 | Acrescentar o campo `cobertura` (dicionário com default `None`) a `ResultadoDeAnalise` em `src/application/dna_analysis.py` e passar o coletor na chamada ao núcleo, sem tocar nas demais projeções | T012 | - | `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T014 | Passar `cobertura=resultado.cobertura` ao `render_template` do ramo `dna_analysis` em `src/app.py`, sem tocar nos outros ramos nem na tela de entrada | T013 | - | `src/app.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Renderizar em `src/templates/index.html` o bloco `<details class="card cobertura-do-arquivo" id="cobertura" open>` fora da guarda `{% if dna_results %}` e antes de "Resultados das Análises de Conexão", com os oito números, a contagem por laboratório e as cinco frases; trocar a linha `Fonte:` do bloco 2 pelo rótulo canônico com etiqueta do texto original; acrescentar a linha `medida-da-evidencia` depois da grade do kit | T014, T007 | - | `src/templates/index.html` | 🟡 | `[X]` |
| T016 | Acrescentar em `src/assets/app.css` a grade de números do painel e a linha da medida, sem cor de estado e sem tocar nas classes existentes | T015 | `[//]` | `src/assets/app.css` | 🟡 | `[X]` |
| T017 | Atualizar de forma explícita os testes que comparam o payload do kit inteiro (`tests/test_dna_analysis.py`, `tests/test_characterization_matching.py`) para as chaves novas `source_raw`, `source_motivo` e `medida`, sem afrouxar a comparação das decisões | T011 | `[//]` | `tests/test_dna_analysis.py`, `tests/test_characterization_matching.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Fechar a verificação: rodar a suíte completa, `tests/rodar_paridade.py` e a análise real, conferir os números do critério de pronto (617/456/456/11 de 45/22/9,0/74%/88%, 59 células sem laboratório, 50/62/344) e gravar `evidence/depois/suite.txt`, `paridade.txt` e `analise.txt` | T015, T016, T017 | - | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/evidence/depois/` | 🟢 | `[X]` |
| T019 | Gravar `legacy-impact.md` e `regression-watch.md` da feature, listando os arquivos tocados, as três chaves aditivas, os três módulos novos, os limiares e a divergência declarada de `source` para o `/reversa-sync` | T018 | `[//]` | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/` | 🟢 | `[X]` |
| T020 | Conferir `SHA_DA_TELA` inalterado e varrer o HTML servido atrás de `Selecione uma empresa ou fonte`, `Minha herança` e `Meu Patrimônio` como rótulo de fonte, gravando `evidence/depois/escopo.txt` | T018 | `[//]` | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/evidence/depois/` | 🟢 | `[X]` |

## Notas de execução

- **T001/T002, linha de base:** executados **depois** das primeiras edições, não antes. A suíte
  "antes" é a referência registrada no adendo 039 (`1409 passed, 9 skipped`); a paridade "antes"
  não pôde ser medida, porque o harness grava um coletor em `_reversa_sdd/parity/` e o ambiente
  bloqueia escrita de processo filho. A limitação está declarada em `evidence/antes/`.
- **T009:** `LIMITE_SEGMENTO_FRACO` passou a valer `qualidade_da_medida.PISO_MAIOR_BLOCO_CM`
  (mesmo `15.0`). `_reversa_sdd/code-analysis.md` 4.6 continua verdadeiro; o que mudou foi o
  dono do número.
- **T015, dois ajustes que a suíte exigiu:** o `{% if %}` do painel foi para a **mesma linha** do
  `{% endif %}` anterior (senão o hash da tela de entrada mudava por whitespace) e o cabeçalho do
  painel ganhou a classe `cabecalho-da-cobertura` (senão `_cabecalhos()`, de
  `test_estado_do_resultado.py`, o tomava por cartão de resultado).
- **T017:** nenhum dos dois arquivos previstos precisou mudar — nenhum compara o dicionário do kit
  inteiro. A atualização declarada ficou sem efeito, e a suíte confirma.
- **T018, paridade:** **30 divergências, todas pré-existentes** — texto humanizado do motivo
  (feature 038), aceitação de matches (024/034) e 18 em `ancestral` (busca de caminho). O coletor
  do harness não captura nenhum campo que a 040 acrescentou. Análise em
  `evidence/depois/paridade.txt`.
- **T018, números:** a análise real fechou **68 cartões / 448 descartes**; o painel exibiu
  `617 / 456 / 456 / 11 (de 45) / 22 / 9,05 / 74% / 88%` e `59` células sem laboratório; os
  estados nos 68 cartões são **35 robusta / 28 parcial / 5 insuficiente**.
- **Duas correções de número contra o plano:** `GEN` sozinho é `Genera` (183 → **184**) e "Minha
  herança" tem **três** grafias (empresa não confirmada 10 → **11**, MyHeritage 118 → **117**). O
  formatador de cM exibe a mediana como **9,05**, não `9,0`. Requirements, roadmap, onboarding e
  data-delta foram corrigidos.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-22 | Execução pelo `/reversa-coding`: 20/20 ações concluídas | reversa |
