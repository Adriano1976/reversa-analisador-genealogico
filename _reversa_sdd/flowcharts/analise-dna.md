# Fluxograma — módulo `analise-dna`

> Gerado pelo Reversa-Archaeologist em 2026-10-05 (re-extração, nível **completo**).
> Fontes: `src/core/dna_analysis.py`, `genetic_evidence.py`, `relationship_hypotheses.py`, `evidence_comparison.py`, `matching.py`, `name_normalization.py`, `cm_estimator.py`, `src/parsers/csv_ingest.py`.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> **Regra do projeto:** o DNA determina a evidência genética; ele **não** determina parentesco. O cM nunca é usado sozinho para afirmar vínculo.

## 1. Visão geral — as três etapas nunca se misturam

```mermaid
flowchart TD
    A[POST action=dna_analysis] --> B[resolve a raiz por nome no GEDCOM]
    B --> C[le o CSV com tolerancia]
    C --> D[ETAPA 1 - parentesco DOCUMENTAL]
    C --> E[ETAPA 2 - evidencia GENETICA]
    D --> F[matching aceita ou descarta candidatos]
    F --> D2[documentary_relationship por candidato]
    E --> G[possibilidades por kit - Shared cM 4.0]
    D2 --> H[ETAPA 3 - CONFRONTO]
    G --> H
    H --> I[COMPATIVEL / POSSIVEL / CONFLITANTE / INCONCLUSIVO]
    I --> J[ordena e renderiza]
    D -. nao le cM .-> D2
    E -. nao le GEDCOM .-> G
```

## 2. Leitura tolerante do CSV (`csv_ingest`)

```mermaid
flowchart TD
    A[read_csv_with_fallback] --> B{encoding utf-8 le?}
    B -- nao --> B1[encoding latin-1]
    B -- sim --> C[detecta separador no cabecalho]
    B1 --> C
    C --> C1[conta virgula, ponto e virgula, TAB e pipe<br/>na primeira linha nao vazia]
    C1 --> C2[maior contagem vence; empate fica com a virgula]
    C2 --> D[localiza o cabecalho]
    D --> D1{n de campos modal entre linhas com 2 ou mais campos<br/>aparece 2 ou mais vezes?}
    D1 -- nao --> D2[cabecalho na linha 1]
    D1 -- sim --> D3{primeira linha ja tem esse n de campos?}
    D3 -- sim --> D2
    D3 -- nao --> D4[primeira linha com o modal,<br/>dentro das primeiras 10]
    D2 --> E[le com pandas]
    D4 --> E
    E --> F{erro de tokenizacao?}
    F -- nao --> G[DataFrame + attrs]
    F -- sim --> F1[rele com on_bad_lines skip]
    F1 --> F2[registra linhas irregulares em attrs]
    F2 --> G
    G --> H{achou coluna de Nome e de cM?}
    H -- nao --> H1[ValueError acionavel em portugues<br/>separador, colunas achadas, linhas tortas]
    H -- sim --> I[agrega por nome + id/e-mail somando cM]
```

## 3. Evidência genética por (nome, kit) — nunca somando kits

```mermaid
flowchart TD
    A[build_genetic_evidence] --> B[descobre colunas por papel<br/>nome, cM, SNPs, cromossomo, start, end, fonte, kit, e-mail]
    B --> C[para cada linha do CSV]
    C --> D{tem nome?}
    D -- nao --> C
    D -- sim --> E[demojibake + norm_name]
    E --> F{coluna de kit?}
    F -- sim --> F1[kit = valor em maiusculas]
    F -- nao --> G{coluna de e-mail?}
    G -- sim --> G1[kit = e-mail]
    G -- nao --> G2[kit = SEM-KIT + aviso kit_ausente]
    F1 --> H[acumula cM SEM round<br/>conta registros e guarda segmentos]
    G1 --> H
    G2 --> H
    H --> I[por kit: ordena segmentos por cM,<br/>maior segmento, SNPs, cromossomos]
    I --> J{maior segmento abaixo de 15 cM?}
    J -- sim --> J1[marca weak_segment + aviso segmento_fraco]
    J -- nao --> K[pronto]
    J1 --> K
    K --> L{mais de um kit para o mesmo nome?}
    L -- sim --> L1[aviso multiplos_kits<br/>cada kit permanece separado]
    L -- nao --> M[evidence_for]
    L1 --> M
    M --> N{um kit so?}
    N -- sim --> N1[totals.cm = cM do kit]
    N -- nao --> N2[totals.cm = None<br/>e cm_por_kit com cada valor]
```

## 4. Do cM às possibilidades (`relationship_hypotheses`)

```mermaid
flowchart TD
    A[possible_relationships total_cm] --> B{total_cm utilizavel?}
    B -- nao --> B1[lista vazia + confianca indeterminada]
    B -- sim --> C[varre as 27 relacoes publicadas do SCP 4.0]
    C --> D[guarda as que contem o valor]
    D --> E[ordena por distancia da media]
    E --> F{quantas cobrem o valor?}
    F -- 0 --> F1[indeterminada - nenhuma relacao publicada cobre]
    F -- 1 a 3 --> F2[baixa - o cM nao distingue qual e a verdadeira]
    F -- 4 a 6 --> F3[muito baixa - sobreposicao ampla]
    F -- mais de 6 --> F4[muito baixa - o cM praticamente nao discrimina]
    F1 --> G[devolve lista - sempre lista, nunca parentesco unico]
    F2 --> G
    F3 --> G
    F4 --> G
```

## 5. Decisão do confronto (`evidence_comparison.compare`)

```mermaid
flowchart TD
    A[compare documental, hipoteses, evidencia] --> B{tem DNA?}
    B -- nao --> B1[INCONCLUSIVO - sem evidencia genetica]
    B -- sim --> C{tem caminho documental?}
    C -- nao --> C1[INCONCLUSIVO - nenhum caminho inventado a partir do DNA]
    C -- sim --> D{identidade ambigua?}
    D -- sim --> D1[INCONCLUSIVO - lista os registros homonimos]
    D -- nao --> E{a relacao documental tem faixa publicada?}
    E -- sim --> E1[janela = faixa do SCP40<br/>method scp40 nome]
    E -- nao --> F{ha relacoes publicadas com o mesmo n de meioses?}
    F -- sim --> F1[janela = envoltoria dessas relacoes<br/>method scp40 meioses]
    F -- nao --> F2[INCONCLUSIVO - nao ha faixa publicada]
    E1 --> G[avalia cada kit]
    F1 --> G
    G --> H{cM dentro da janela?}
    H -- sim --> H1[COMPATIVEL]
    H -- nao --> I{alguma relacao publicada que contem o valor<br/>tem faixa que SE SOBREPOE a janela?}
    I -- sim --> I1[POSSIVEL - o cM nao separa as duas leituras]
    I -- nao --> I2[CONFLITANTE - com o rol de causas]
    H1 --> J{mais de um kit?}
    I1 --> J
    I2 --> J
    J -- sim --> J1[estado final = o MAIS CONSERVADOR<br/>CONFLITANTE, POSSIVEL, COMPATIVEL, INCONCLUSIVO]
    J -- nao --> K[estado do kit]
    J1 --> L[estado final + detalhe + observacoes]
    K --> L
```

## 6. Ordem de apresentação dos resultados

```mermaid
flowchart LR
    A[resultados] --> B{tem caminho documental?}
    B -- sim --> C[grupo 1]
    B -- nao --> D[grupo 2 - so DNA]
    C --> E[dentro do grupo: cM decrescente]
    D --> E
    E --> F[medido no GEDCOM real em 2026-10:<br/>71 conexoes, 64 sem caminho no GEDCOM]
```

## 7. Notas de leitura

* **A ordem de apresentação não é ordem de confiança.** É primeiro o que tem caminho documental, depois o que só tem DNA; dentro de cada grupo, cM decrescente. A justificativa está medida no próprio código: das 71 conexões do GEDCOM real, 64 não têm caminho no GEDCOM — ordenar só por cM enterraria as 7 documentais no meio. 🟢
* **Nenhum caminho é inventado a partir do DNA.** Quando não há caminho documental, o confronto é INCONCLUSIVO e o texto diz isso explicitamente. 🟢
* **A escolha entre homônimos é a do legado** (o primeiro candidato que tenha caminho), preservada de propósito para não alterar resultado — mas passa a ser **declarada** como identidade ambígua, em vez de silenciosa. 🟢
* **`cm_estimator` está fora do fluxo.** As nove faixas escritas à mão continuam existindo por compatibilidade (`__all__` do `dna_analysis`, harness de paridade e `tests/test_dna_analysis.py`), e o próprio módulo declara que não devem ser usadas em código novo. Quem traduz cM agora é `relationship_hypotheses`, com fonte publicada. 🟢
* **`LIMITE_SEGMENTO_FRACO` (15 cM) é critério do projeto, não da fonte.** A própria `relationship_hypotheses` registra que a versão 4.0 do Shared cM Project não afirma nada sobre "segmento abaixo de X é falso positivo". 🟢

---

*Gerado pelo Reversa-Archaeologist em 2026-10-05.*
