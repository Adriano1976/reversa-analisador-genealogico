# Investigation: grupos de triangulação

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. A pergunta técnica

Como agrupar pares de kits que compartilham faixa de DNA de modo que o grupo signifique **ancestral comum**, e
não coincidência geométrica — sem inventar número, sem tocar no parentesco documental e sem rodar um segundo
matching?

## 2. O que é triangulação, e o que ela prova

Triangulação é a leitura em que **três ou mais** matches compartilham a **mesma faixa** do mesmo cromossomo: se
A compartilha com B, B com C e A com C na mesma região, a hipótese de um ancestral comum aos três é a
explicação mais econômica. O que a triangulação sustenta é **um ancestral comum naquela faixa**; ela não diz
*qual*, e não diz que o parentesco documental está correto. É por isso que a feature a trata como evidência de
grupo, e não como veredito.

O que ela **não** prova, e a amostra mostrou em escala: sobreposição de faixas acontece sem triangulação.
Medido: **1.535 regiões** com ≥ 3 kits se sobrepondo, mas só **60** com todos os pares presentes.

## 3. Formatos de arquivo

| Formato | Forma | Consequência |
|---------|-------|--------------|
| Consolidado de pares (a amostra) | Uma linha por par: `Chr`, `Kit1 Number`, `Kit1 Name`, `Kit1 Email`, `Kit2 Number`, `Kit2 Name`, `Kit2 Email`, `B37 Start`, `B37 End`, `cM`; **sem** kit raiz | É o formato da v1 |
| Nativo do GEDmatch | Mesmas colunas, com o kit raiz em algumas linhas | **Fora da v1** (`D-03`): a estrutura não permite distinguir, e o kit raiz entraria como membro |

O adaptador atual (`core.genetic_evidence.detect_segment_columns`) reconhece **um** kit por linha e não
reconhece `B37 Start/End`; num arquivo de pares ele escolhe `Kit1 Number` e devolve `start`/`end` nulos. É a
razão de o adaptador novo ser próprio (`D-02`), e não uma extensão do antigo.

## 4. Alternativas avaliadas

| Alternativa | Como funcionaria | Por que foi descartada |
|-------------|------------------|------------------------|
| **A. Geometria pura** | Qualquer conjunto com interseção comum vira grupo | Produz 1.535 "grupos" na amostra, incluindo uma região de 0,40 Mb com 51 kits. Chama coincidência de parentesco |
| **B. Fechamento dos pares** (escolhida) | Exige que todos os pares do conjunto existam no arquivo | Reduz a 60 grupos, 28 maximais, e rejeita o acúmulo. É a única que separa evidência de coincidência **com o dado disponível** |
| **C. Grafo de cliques** | Grupo = clique maximal no grafo de pares | Equivalente a B para intervalos, mas sem a garantia de interseção comum; mais código para o mesmo resultado |
| **D. cM como critério principal** | Agrupar por faixa de cM | O cM não localiza o segmento: dois pares de 20 cM podem estar em cromossomos diferentes. Contraria a regra central do domínio |
| **E. Só os pares, sem grupo** | Listar pares que se sobrepõem | É o que o app de referência faz de fato: um painel do arquivo, sem decisão. Não entrega a negativa justificada |

### Por que a interseção comum basta para o fechamento

Para intervalos em uma dimensão vale a propriedade de Helly: se todos os intervalos de um conjunto têm
interseção dois a dois, eles têm interseção comum. Logo, exigir interseção comum **implica** que todo par se
sobrepõe — o que o teste de fechamento verifica é a **outra metade**: que o arquivo **registra** esses pares.
Uma região com interseção comum e pares ausentes é uma cadeia; o app a trata como cadeia, e não como grupo.

### Por que a região é a interseção, e não a união

As faixas dos três kits não coincidem: na amostra, o início varia com mediana de **1,46 Mb** e máximo de
**21,9 Mb**. A interseção tem mediana de **11,2 Mb**. Exibir a faixa de um par como se fosse a do grupo
apresentaria uma região que nenhum dos três compartilha — número inventado, ainda que derivado de número real.

## 5. O fenômeno do acúmulo (pile-up)

Regiões curtas compartilhadas por muitos kits são conhecidas na genealogia genética como **excesso de IBD**:
o compartilhamento é real, mas não aponta um ancestral comum recente — é excesso de sinal, e não parentesco.
A literatura registra falsos positivos de segmentos IBD em escala, sobretudo em populações com estrutura e
endogamia ([Reducing Pervasive False-Positive IBD Segments, MBE 2014](https://academic.oup.com/mbe/article/31/8/2212/2925728);
[ISOGG — Identical by descent](https://isogg.org/wiki/Identical_by_descent)).

O caso medido encaixa no padrão: **chr20, 58.958.477–59.362.391, 0,40 Mb, 51 kits, 182 pares de 1.275
possíveis, cM de 5,2 a 10,4**.

**O limiar não vem da literatura.** Nenhum dos textos consultados publica um corte de kits/Mb aplicável aqui;
o número da `RN-05` (≥ 8 kits e (< 2 Mb ou cM máx < 12)) é **heurística declarada do projeto**, ancorada nesse
caso e nos grupos fechados da amostra (2,25–29,85 Mb). É por isso que a confidência é 🟡, e não 🟢.

## 6. A referência externa que originou a feature

O app [DNA Triangulation Dashboard](https://dna-triangulation-dashboard.lovable.app) recebe o mesmo CSV e
mostra três painéis: métricas gerais, distribuição cromossômica e análise de cM. Ele **não** agrupa os pares
nem confronta com árvore. O que se aproveitou foi o **formato de entrada** e a noção de mapa cromossômico; o
que se recusou foi o painel — número agregado sem decisão. A `RN-14` existe para que essa recusa não se perca
no modo sem árvore.

## 7. Padrões aplicáveis do próprio projeto

| Padrão | Origem | Uso aqui |
|--------|--------|----------|
| Leitura tolerante | `parsers/csv_ingest.read_csv_with_fallback` | Reuso integral; nada de leitor novo |
| Bloco de escopo-arquivo | adendo `040` (cobertura) | O bloco de grupos nasce antes dos cartões, aberto |
| Leitura derivada que não cria cartão | adendo `039` (DNA sem correspondência) | A classificação não cria vínculo nem cartão |
| Autoridade única de limpeza de nome | `ADR-07` | O `*` é limpo no adaptador, não em `norm_name` |
| Desempate determinístico | `BR-D-63` (mínimo `xref_id`) | A ordem do grupo é total, sem depender de `set` |

## 8. Lacunas desta investigação

- 🔴 Não há medição do custo de tempo do agrupamento com arquivo grande; o `onboarding.md` fixa o que medir.
- 🔴 Não há fonte publicada para o limiar de acúmulo; ele é heurística declarada (`RN-05`).
- 🔴 O comportamento com o export nativo não foi medido — a amostra disponível é consolidada.
