# Investigation: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/028-validador-de-dados-dna/requirements.md`

## 1. Pergunta de investigação

Como responder, para cada comparação entre um kit de DNA e uma pessoa do GEDCOM, se a linha
documental é **temporalmente viável** — e acusar conflitos biológicos críticos — sem quebrar os
quatro estados existentes (`COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`) e sem
reimplementar o parentesco documental, o matching ou a leitura dos arquivos?

## 2. O que o legado já oferece

| Componente | O que entrega hoje | O que falta para esta feature |
|------------|--------------------|-------------------------------|
| `core.documentary_relationship` | Caminho, `degrees.a_up`/`b_up`, `meioses`, `common_ancestor` com `birth`, `evidence` por salto com `plausible`, `parent_birth`, `child_birth` e `age_at_birth` | Não olha o cM nem estima o ano do MRCA |
| `core.janela_de_vida` | O match escolhido pode ter doado? Corte duro em 122 anos; qualificadores de data | Não verifica o doador nem a linha inteira |
| `core.profundidade_do_caminho` | A árvore afirma a mesma profundidade que o `MRCA` do kit, por razão entre gerações | Depende da coluna `MRCA`; não usa datas de nascimento nem a idade por lado |
| `core.evidence_comparison` | cM × parentesco documental, em quatro estados, com o porquê | Não é um veredito de viabilidade temporal e não acusa quebra de linha |
| `core.relationship_hypotheses` | Tabela SCP 4.0 com `meioses`, média e faixa por relação; `possible_relationships(cm)` | Não converte gerações em anos |
| `core.genetic_evidence` | cM total, `largest_segment_cm`, `mrca_generations`, chave `(nome, kit)` | É descritivo; não decide |
| `parsers.csv_ingest` + `parsers.gedcom_parser` | Leitura tolerante do CSV; `carregar_arvore` devolve a árvore como valor | Nada a acrescentar |
| `core.matching` | Índices e candidatos por nome; desempate determinístico | Nada a acrescentar |

## 3. Alternativas avaliadas

| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| **A. Estender `evidence_comparison` com os três status** | Menos arquivos; um único lugar de confronto | Quebra o contrato de quatro estados, o texto congelado e a classe CSS do selo; mistura dois eixos (compatibilidade cM × viabilidade temporal) | Descartada |
| **B. Novo parser/validador autônomo, lendo GEDCOM e CSV do zero** | Independência | Duplica leitura tolerante, matching e parentesco; cria duas verdades sobre a árvore | Descartada |
| **C. Núcleo puro novo + fachada de aplicação que reutiliza o legado** | Respeita a arquitetura (ADR-24/25), testável sem I/O, aditivo | Exige dois arquivos e um contrato de entrada bem definido | **Escolhida** |
| **D. Usar o maior segmento como estimador do MRCA** | Um número só | Não há tabela publicada que mapeie maior segmento → meioses; violaria o princípio V | Descartada |

## 4. Fundamento de domínio

### 4.1 cM total é a métrica principal

O Shared cM Project 4.0 publica, para 27 relações, uma faixa e uma média de **cM total** (soma dos
segmentos compartilhados). É essa grandeza que `core.relationship_hypotheses` usa para devolver as
relações possíveis; cada relação traz o número de `meioses`, que é a ponte para gerações até o MRCA.
O cM total é, portanto, o estimador calibrado — e o único que pode alimentar a estimativa sem
inventar número.

### 4.2 O maior segmento é um confirmador, não um estimador

A recombinação quebra os blocos a cada geração: um **único segmento grande** é sinal de ancestral
comum recente e tem menos chance de ser IBS (*Identical by State* — igual por estado, por acaso ou
ancestralidade muito remota). Já um total alto formado por muitos segmentos pequenos pode indicar
endogamia, múltiplos caminhos distantes ou acúmulo de falsos positivos.

Duas consequências para o desenho:

1. O maior segmento **não** entra na estimativa do MRCA. Não existe tabela publicada que o mapeie
   para meioses; usá-lo como estimador seria inventar número.
2. O maior segmento continua sendo um sinal de **qualidade/recência**. No legado, ele já é tratado
   em `genetic_evidence` (`LIMITE_SEGMENTO_FRACO = 15.0`; `largest_segment_cm < 15` liga
   `weak_segment` e gera o aviso `segmento_fraco`). Esta feature **não duplica** essa regra nem a
   transforma em veredito: o validador usa o cM total para estimar e deixa a marca de evidência
   fraca onde ela já vive.

O limiar de 15 cM é aplicado ao **maior segmento**, não a cada segmento. Um match real e distante
costuma ter vários segmentos pequenos; o que caracteriza evidência fraca é o maior bloco abaixo de
15 cM. O corte é heurística do projeto, não padrão científico universal — outras ferramentas usam
7 cM, 10 cM etc.

### 4.3 Como estimar o MRCA

1. Se o kit traz a coluna `MRCA` (gerações estimadas pelo GEDmatch a partir do cM), ela é a primeira
   escolha: é a estimativa do próprio arquivo para aquele kit.
2. Sem ela, usa-se a mediana das `meioses` das relações publicadas que contêm o cM, dividida por 2.
   A divisão por 2 é a mesma calibragem já declarada em `core.profundidade_do_caminho`: `MRCA` é um
   número por lado, e `meioses` soma os dois lados.
3. O ano estimado é `nasc_doador - geracoes_kit × G`, com `G` mediano dos intervalos pai-filho
   datados da árvore (fallback de 25 anos com menos de 3 amostras).

### 4.4 Como medir a viabilidade temporal

- **Por salto:** cada salto pai-filho datado precisa ficar entre 12 e 70 anos. O legado já faz isso
  em `hop_evidence`, com `IDADE_MINIMA_GENITOR` e `IDADE_MAXIMA_GENITOR`.
- **Por lado:** `(nasc_descendente - nasc_mrca) / geracoes_do_lado` precisa ficar entre 12 e 70. É
  a conta que pega o doador vivo ligado a um ancestral do século XVII por um caminho curto demais.
- **Ordem:** o MRCA não pode nascer depois (ou no mesmo ano) de um descendente com geração > 0.
- **cM × profundidade:** a profundidade documental precisa caber na envoltória das relações
  publicadas que contêm o cM, com tolerância de 2 meioses. Se a comparação de quatro estados já
  existe, o estado dela é o insumo (`CONFLITANTE` vira conflito crítico).
- **MRCA documentado × janela estimada:** o ano que o GEDCOM declara precisa caber na janela
  estimada, com tolerância de 2 gerações; data estimada (`ABT`, `EST`, ...) é atenção, não erro.

### 4.5 Por que `VALIDADO` é estrito

Um erro pode ser provado com dados parciais (ex.: dois nascimentos e um salto de 300 anos). Uma
validação não pode: se falta data em um salto, não se sabe se aquele trecho é possível. Por isso a
RN-09 exige a linha inteira datada, sem identidade ambígua e sem atenção aberta. É preferível um
`INCONCLUSIVO` honesto a um `VALIDADO` que afirma mais do que se sabe.

## 5. Achados do código que sustentam o desenho

| Achado | Onde | Uso no plano |
|--------|------|--------------|
| `documental["degrees"]` traz `a_up` (doador) e `b_up` (match) | `src/core/documentary_relationship.py:681-698` | Idade por lado sem dividir meioses |
| `documental["evidence"]` traz `plausible`, `parent_birth`, `child_birth`, `age_at_birth` | `src/core/documentary_relationship.py:620-637` | Checagem por salto sem recalcular |
| `hop_evidence` usa 12–70 | `src/core/documentary_relationship.py` | Não duplicar os limites |
| `janela_de_vida` tem `IDADE_IMPOSSIVEL = 122` e qualificadores de data | `src/core/janela_de_vida.py:76-106` | Doador vivo e imprecisão |
| `genetic_evidence` tem `largest_segment_cm`, `mrca_generations`, `total_cm` | `src/core/genetic_evidence.py:281-310` | Insumos do kit |
| `relationship_hypotheses` tem `possible_relationships(cm)` e `meioses` por relação | `src/core/relationship_hypotheses.py:64-92` | Candidatos e mediana |
| `evidence_comparison` tem os quatro estados e a precedência | `src/core/evidence_comparison.py:292-311` | Composição, não reescrita |
| `profundidade_do_caminho` usa razão 1,5/2,0 | `src/core/profundidade_do_caminho.py:61-93` | Referência; o validador usa anos, não razão |
| `carregar_arvore` devolve a árvore como valor | `src/parsers/gedcom_parser.py:79` | Fachada parseia uma vez |
| `dna_analysis` resolve a raiz por substring e escolhe o primeiro candidato com caminho | `src/core/dna_analysis.py:175-302` | A fachada repete a mesma política, sem inventar match |

## 6. Padrões aplicáveis

- **Núcleo puro + fachada:** o núcleo recebe valores e devolve valores; a fachada lê e cruza.
- **Injeção de dependência:** a fachada recebe as funções de leitura (ou usa as padrão), como
  `core.dna_analysis.Dependencias` já faz na borda.
- **Precedência conservadora:** o pior status vence, como no confronto de múltiplos kits.
- **`None` é "não sei":** data ausente não vira zero nem erro.
- **Código estável + mensagem humana:** `{codigo, severidade, mensagem}`.
- **Fixture sintética:** nenhum dado real de DNA/GEDCOM entra no repositório.

## 7. Perguntas remanescentes

Nenhuma. As três dúvidas do `requirements.md` foram resolvidas em 2026-10-18. A discussão sobre o
maior segmento não é uma dúvida aberta: a decisão vigente é que ele **não** entra na estimativa do
MRCA e que a marca de evidência fraca continua em `genetic_evidence`, fora do veredito do validador.

## 8. Fontes

- Bettinger, B. T. *The Shared cM Project Version 4.0 (March 2020)*.
  <https://thegeneticgenealogist.com/wp-content/uploads/2020/03/Shared-cM-Project-Version-4.pdf>
- DNA Painter. *Shared cM Project 4.0 tool*. <https://dnapainter.com/tools/sharedcmv4>
- Fenner, J. N. *Cross-cultural estimation of the human generation interval for use in
  genetics-based population divergence studies*. Am J Phys Anthropol. 2005;128(2):415–423.
  DOI: [10.1002/ajpa.20188](https://doi.org/10.1002/ajpa.20188). Consultado em 2026-10-18.
- `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto`,
  `#31-parentesco-documental`, `#32-evidencia-genetica`, `#33-possibilidades-shared-cm-project-40`.
- `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md` e
  `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`.
- `_reversa_sdd/code-analysis.md#4-unidade-analise-dna`.
