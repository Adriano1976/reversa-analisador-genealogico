# Requirements: Fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

**Termos usados neste documento:** cM = centimorgans (unidade de DNA compartilhado); MRCA = ancestral
comum mais recente; kit = identificador da amostra; **evidência** = o par (nome normalizado, kit) que o
núcleo monta — ver `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit`; **cartão** =
resultado de uma conexão na tela; **medida** = o conjunto total de cM, maior segmento e SNPs de uma
evidência; **cobertura** = o retrato do arquivo inteiro, e não de uma conexão.

## 1. Resumo executivo

A tela de DNA mostra a **fonte** exatamente como veio do CSV — inclusive `Outro (insira o nome abaixo)`,
`Selecione uma empresa ou fonte` e `-` — e não diz **nada sobre o arquivo como um todo**. Esta feature
(a) normaliza a fonte num catálogo de laboratórios, mantendo o texto original visível; (b) acrescenta um
painel **"Cobertura do arquivo"** com oito números e as frases que os explicam; (c) dá a cada cartão um
estado de **qualidade da medida** — `robusta`, `parcial` ou `insuficiente` — com os números que o
produzem. Nenhum veredito, caminho, cM, ordem de cartão, lista de descartes ou CSV exportado muda.

**Medido em 2026-10-22** no arquivo real do operador (`Famílias_Sergipanas.csv`, 617 linhas, 456
evidências): **45 valores distintos** de fonte para **11 laboratórios**; **59 células** sem laboratório
(40 texto de formulário, 11 empresa não confirmada, 7 nome de projeto, 1 haplogrupo, 1 não reconhecida);
**456 de 617** segmentos abaixo do piso de 10 cM; **402 de 456** evidências sem bloco de 15 cM; **232 de
456** com menos de 900 SNPs; mediana de **9,05 cM**; **22** cromossomos, nenhum X.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/data-dictionary.md#41-colunas-reconhecidas-por-papel` | A fonte é lida de `Source`, `Fonte` ou `Company`; não há normalização de valor, só de nome de coluna. | 🟢 |
| `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` | `source` é "fonte declarada (empresa/laboratório); **primeira** não vazia encontrada" — o texto cru, sem catálogo. | 🟢 |
| `_reversa_sdd/data-dictionary.md#54-evidência-consolidada-de-uma-pessoa-evidence_for` | O padrão exibido quando não há fonte é `"fonte não identificada no CSV"`. | 🟢 |
| `_reversa_sdd/domain.md#32-evidência-genética` | A chave é (nome, kit); kits diferentes nunca são somados e o número honesto é `None`, não zero. | 🟢 |
| `_reversa_sdd/domain.md#2-a-regra-central-do-domínio-três-eixos-que-não-se-contaminam` | O DNA não altera o parentesco documental e o cM nunca é usado sozinho para afirmar parentesco. | 🟢 |
| `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração` | `LIMITE_SEGMENTO_FRACO = 15.0` é **critério do projeto, não da fonte** — o precedente para um piso declarado. | 🟢 |
| `_reversa_sdd/code-analysis.md#44-regras-de-negócio--preservadas` | `BR-D-12` (chave nome+kit), `BR-D-14` (nunca somar kits), `BR-D-17` (maior segmento abaixo de 15 cM marca evidência fraca). | 🟢 |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | `core/` decide, `application/` orquestra e projeta, `reporting/` formata, o template renderiza — a apresentação não decide regra. | 🟢 |
| `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md#para-que-a-frase-serve--a-parte-que-se-manteve` | Observação de arquivo tem lugar próprio e não se repete em cada cartão; o bloco vive fora da guarda dos resultados. | 🟢 |
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#o-que-mudou` | Bloco de escopo-arquivo é `details` **aberto**, com `summary` titulando e `card-body`. | 🟢 |
| `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md#resumo-da-entrega` | O cartão tem três faixas de leitura e os blocos "Matches descartados" e "Observações do arquivo" ficaram intocados. | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#evidência-genética` | O módulo entrega evidência descritiva por (nome, kit) e não conhece o GEDCOM. | 🟢 |

> 🟡 **Fora da extração:** o código atual em `src/core/genetic_evidence.py:86` reconhece `source`, `fonte`
> e `company`, mas **não** `TestCompany` — a coluna equivalente do export de um-para-muitos do GEDmatch.
> Esta feature não muda a lista de colunas (ver seção 10).

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Adriano**, genealogista-operador | Saber, antes de ler dezenas de cartões, se o arquivo tem medida que sustente análise, e de qual laboratório veio cada uma | Roda a análise e o painel diz "456 evidências, 11 laboratórios, 74% dos segmentos abaixo de 10 cM, mediana 9,0 cM" — ele decide olhar primeiro as 50 de medida robusta |
| **Pesquisador ou parente que acompanha** | Entender por que um match forte não virou conclusão, sem concluir que o sistema o considerou parente | Lê "medida parcial" no cartão e o texto "qualidade da medida, não do parentesco" |
| **Quem audita o resultado depois** | Reconstruir de onde veio o número e qual laboratório o declarou | Vê o rótulo canônico e o texto original do CSV lado a lado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Catálogo canônico de fonte.** O valor de `source` passa a ser traduzido por um catálogo fechado
   de laboratórios, comparando sem acento, sem caixa e com espaços colapsados. O catálogo é uma tabela
   literal do núcleo, **declarada pelo projeto** — não é lista publicada por ninguém, e por isso não pode
   ser apresentada como fonte externa (Princípio V). Rótulos canônicos: `Genera`, `MyHeritage`, `meuDNA`,
   `FTDNA`, `23andMe`, `Ancestry`, `FamilyTreeDNA`, `Living DNA`, `Genos`, `DNA Land`, `MundoDNA`. 🟡
   - Origem no legado: `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` (`source`
     é o texto cru) e `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração`
     (precedente de valor declarado pelo projeto).
   - Tipo: nova.
2. **RN-02 — Três desfechos para o valor da fonte.** Toda célula cai em um de três: **laboratório**
   (reconhecido no catálogo), **`não declarada`** (vazia, `-`, texto de formulário, haplogrupo, nome de
   projeto ou empresa não confirmada) ou **`outro`** (valor não reconhecido que não é claramente nenhum dos
   anteriores). Nos três casos o texto original é preservado para exibição (RN-03). 🟢
   - Textos de formulário medidos: `Outro (insira o nome abaixo)`, `Other (enter name below)`,
     `Selecione uma empresa ou fonte`, `Select a Company or Source`, `-`, vazio — **40 células**.
   - Empresas não confirmadas: `Minha herança` / `Minha Herança` / `Minha heran` e `Meu Patrimônio` —
     **11 células**; entram como `não declarada`, nunca como laboratório suposto (decisão do operador,
     seção 9).
   - Nomes de projeto: `Migration - F2 - A`, `Migration - F2 - T`, `Ancestralidade` — **7 células**.
   - Haplogrupo na coluna de fonte: `L1b1a` — **1 célula**.
   - Tipo: nova.
3. **RN-03 — O texto original não é apagado.** `source_raw` guarda a célula como veio; a tela mostra o
   rótulo canônico e, **quando diferem**, o texto original em etiqueta ao lado. Quando são iguais, não há
   etiqueta. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#38-leitura-tolerante-do-csv-descartar-sim-esconder-não`
     (descartar sim, esconder não).
   - Tipo: nova.
4. **RN-04 — A escolha do valor dentro do kit muda, e a mudança é declarada.** A regra atual pega a
   **primeira** linha não vazia do kit. Passa a pegar a **primeira linha cujo valor normalizado é
   laboratório**; se nenhuma for, cai para o primeiro valor não vazio (agora normalizado). Consequência
   medida: uma célula `-` na primeira linha deixava de esconder um `Genera` declarado adiante. 🟡
   - Origem no legado: `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit`
     ("primeira não vazia encontrada").
   - Tipo: alterada. `BR-D-12`/`BR-D-14` não são tocadas: a chave continua (nome, kit) e nada é somado.
5. **RN-05 — Divergência dentro do kit vira aviso, não escolha silenciosa.** Se duas linhas do mesmo kit
   declaram **laboratórios diferentes**, o cartão recebe o aviso `fontes_divergentes`, com os dois rótulos,
   e o rótulo exibido é o **primeiro** deles. Não se escolhe "o melhor"; não se soma nada. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#32-evidência-genética` (avisos existem para o que o
     operador precisa saber, não para esconder).
   - Tipo: nova.
6. **RN-06 — Cobertura é derivada do mesmo payload.** O painel é calculado a partir das evidências já
   montadas e da tabela já lida do CSV — **não relê o CSV**, não remonta o GEDCOM, não recalcula cM e não
   mexe em nenhuma decisão. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` (camadas);
     precedente de leitura derivada no adendo `039`.
   - Tipo: nova.
7. **RN-07 — O painel tem oito números e cinco frases, e cada número é reconstruível.** Números: linhas do
   CSV; evidências; kits distintos; laboratórios distintos (com o número de grafias que os produziu);
   cromossomos cobertos; mediana de cM por evidência; percentual de segmentos abaixo de **10,0 cM**
   (o piso do filtro de endogamia); percentual de evidências sem bloco de **15,0 cM**. Frases: (a) quantos
   segmentos o filtro descarta; (b) quantas evidências passam de 15 cM somados sem nenhum bloco de 15 cM;
   (c) quantas têm menos de 900 SNPs somados; (d) o arquivo **não declara o corte** da busca; (e) quantas
   células de fonte não trazem laboratório, com os motivos. 🟡
   - Origem no legado: `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração`
     (pisos declarados); medição de 2026-10-22 na seção 1.
   - Tipo: nova.
8. **RN-08 — Estado da medida, com dois pisos herdados e um declarado.** O estado de cada evidência é
   decidido por `total_cm`, `largest_segment_cm` e `snps_total`:
   - `insuficiente` — total abaixo de **15,0 cM** (e, por consequência, todo bloco abaixo de 15,0 cM);
   - `parcial` — total ≥ 15,0 cM **e** maior bloco < 15,0 cM, **ou** total e bloco ≥ 15,0 cM com SNPs
     somados < **900**;
   - `robusta` — total ≥ 15,0 cM, maior bloco ≥ 15,0 cM e SNPs ≥ 900 (ou SNPs ausentes no arquivo).
   Os dois primeiros pisos são os que o projeto já usa (`LIMITE_SEGMENTO_FRACO = 15.0` e o piso de 10,0 cM
   do filtro); o de 900 SNPs é **corte de triagem declarado**, com a mesma natureza do corte de 20 cM da
   feature 039, e não uma faixa publicada. Distribuição medida no arquivo real: **50 robusta, 62 parcial,
   344 insuficiente** em 456. 🟡
   - Origem no legado: `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração`;
     `BR-D-17` em `#44-regras-de-negócio-preservadas`.
   - Tipo: nova.
9. **RN-09 — O estado não é parentesco, e o texto diz isso.** O estado acompanha uma frase fixa — "qualidade
   da medida, não do parentesco" — e não substitui, contradiz nem recolore o confronto, a viabilidade, o selo
   de cM ou a classificação do cartão. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#2-a-regra-central-do-domínio-três-eixos-que-não-se-contaminam`.
   - Tipo: nova.
10. **RN-10 — Onde e quando renderiza.** O painel é um bloco de **escopo-arquivo**, no mesmo lugar e com a
    mesma forma do bloco "Observações do arquivo": nasce **aberto**, é recolhível e renderiza **fora da
    guarda dos cartões** — porque descreve o arquivo, não uma conexão. Sem nenhuma evidência, o painel não
    aparece (o aviso `sem_evidencia` já cobre o caso). O estado da medida vive **dentro** do bloco 2 do
    cartão, abaixo da grade. 🟡
    - Origem no legado: `_reversa_sdd/addenda/017-...md` (escopo-arquivo tem lugar próprio);
      `_reversa_sdd/addenda/022-...md#o-que-mudou` (`details` aberto).
    - Tipo: nova.
11. **RN-11 — Nada mais muda.** Confronto, viabilidade, hipóteses, caminho, ordem dos cartões, lista de
    descartes, CSV exportado, contagem "N conexões analisadas" e histórico persistido ficam **idênticos**.
    A tela de entrada (`GET /`) não muda e o `SHA_DA_TELA` continua o mesmo. 🟢
    - Origem no legado: Princípio II; `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados`.
    - Tipo: nova.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Normalizar `source` pelo catálogo e exibir o rótulo canônico no bloco 2 | Must | `GENERA`, `genera` e `Genera Brasil` exibem `Genera`; `Meu DNA`, `MEUDNA` e `MeuDna` exibem `meuDNA` | 🟡 |
| RF-02 | Preservar e exibir o texto original quando difere do canônico | Must | Célula `Outro (insira o nome abaixo)` exibe `não declarada` e a etiqueta com o texto original; célula `Genera` não exibe etiqueta | 🟢 |
| RF-03 | Classificar todo valor em laboratório, `não declarada` ou `outro` | Must | `-`, vazio, `Selecione uma empresa ou fonte`, `L1b1a` e `Migration - F2 - A` viram `não declarada`; valor inventado vira `outro` com o texto original | 🟡 |
| RF-04 | Escolher a fonte do kit pela primeira linha com laboratório reconhecido | Must | Kit com `-` na primeira linha e `Genera` na terceira exibe `Genera`; kit só com `-` exibe `não declarada` | 🟡 |
| RF-05 | Emitir `fontes_divergentes` quando o mesmo kit declara dois laboratórios | Should | Kit com `Genera` e `MyHeritage` no mesmo arquivo mostra o aviso com os dois rótulos e exibe o primeiro | 🟡 |
| RF-06 | Exibir o painel "Cobertura do arquivo" com os oito números da RN-07 | Must | Arquivo real exibe `617`, `456`, `456`, `11` (de `45`), `22`, `9,05`, `74%`, `88%` | 🟡 |
| RF-07 | Exibir as cinco frases da RN-07, com números derivados e não escritos à mão | Must | "456 de 617 segmentos abaixo de 10 cM", "58 de 112…", "232…", "o arquivo não declara o corte", "59 células sem laboratório" | 🟡 |
| RF-08 | Dar estado à medida de cada cartão, com os três números | Must | Cartão de 154,5 cM / 56,9 cM / 15.959 SNPs exibe `robusta`; cartão de 51,3 / 13,7 / 7.349 exibe `parcial` com "menor bloco de 13,7 cM" | 🟡 |
| RF-09 | Acompanhar o estado com a ressalva de escopo | Must | O texto "qualidade da medida, não do parentesco" aparece junto de todo estado | 🟢 |
| RF-10 | Renderizar o painel aberto, recolhível, fora da guarda dos cartões e ausente sem evidência | Must | Análise com 8 cartões e 456 evidências mostra o painel; análise sem evidência não mostra | 🟢 |
| RF-11 | Não alterar veredito, caminho, ordem, descartes, CSV, contagem e histórico | Must | Suíte e paridade passam; o CSV de descartes mantém as nove colunas; a contagem de conexões não muda | 🟢 |
| RF-12 | Listar a contagem de evidências por laboratório no painel | Could | Lista completa, em ordem decrescente de contagem e alfabética no empate: `Genera 184`, `MyHeritage 117`, `meuDNA 49`, `FTDNA 22`, `23andMe 15`, `Ancestry 5`, e os de uma evidência cada; sem alterar nenhum cartão | 🟡 |
| RF-13 | Dizer "nenhuma fonte declarada" quando o arquivo não traz coluna de fonte | Could | Arquivo sem coluna de fonte mostra o painel, e o item de laboratórios diz "nenhuma fonte declarada" | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Uma passada O(n) sobre evidências e segmentos já em memória; nenhuma leitura nova de arquivo | RN-06; o custo dominante continua sendo o parse do GEDCOM | 🟢 |
| Determinismo | Laboratórios em ordem decrescente de contagem e, no empate, alfabética; mediana por valor exato | Precedente de ordem declarada (`domain.md#39`) | 🟢 |
| Privacidade | Nenhum dado novo: fonte é nome de empresa; nada é gravado, logado ou persistido | Princípio I; nenhuma tabela ou porta nova | 🟢 |
| Compatibilidade | A tela de entrada (`SHA_DA_TELA`) não muda; a tela de resultados muda, e os testes que prendem texto de cartão são atualizados de forma declarada | Adendo 022 (hash da entrada); RN-11 | 🟢 |
| Acessibilidade | Números e frases em texto; nenhuma informação depende de cor; o `details` é operable por teclado | Padrão dos blocos existentes | 🟡 |
| Manutenibilidade | Catálogo e pisos em um único literal nomeado no núcleo; o template não contém número nem decisão | RN-01, RN-08; `architecture.md#3` | 🟢 |
| Observabilidade | Nenhum log novo; o aviso `fontes_divergentes` entra no canal de avisos existente | `domain.md#32` (avisos) | 🟢 |
| Concorrência | Não aplicável: leitura pura do resultado já calculado | RN-06 | 🟢 |

**Fixtures sintéticas:** `tests/fixtures/sample_dna.py`, estendido com (a) um arquivo de fonte suja —
`Genera`, `GENERA`, `-`, `Selecione uma empresa ou fonte`, `L1b1a`, valor inventado — e (b) evidências nas
três faixas de medida. Nenhum CSV real é copiado para teste (Princípio I). 🟢

**Princípios:** I (fixtures sintéticas), II (nenhum veredito muda), III (cada RF com critério de teste),
V (o piso de 900 SNPs é declarado como triagem, não como faixa publicada). O Princípio IV não se aplica:
a feature não percorre o grafo. Não há conflito com princípio ativo. 🟢

## 7. Critérios de Aceitação

```gherkin
Cenário: Fonte crua vira rótulo canônico
  Dado um CSV cuja coluna Source traz "GENERA" na primeira linha do kit
  Quando a tela de resultados é renderizada
  Então o bloco 2 exibe "Fonte: Genera"
  E não exibe etiqueta de texto original

Cenário: Texto de formulário e empresa não confirmada não viram laboratório
  Dado um CSV cuja coluna Source traz "Outro (insira o nome abaixo)" e, em outro kit, "Minha herança"
  Quando a tela de resultados é renderizada
  Então os dois cartões exibem "Fonte: não declarada"
  E exibem a etiqueta com o texto original
  E nenhum dos dois exibe laboratório suposto

Cenário: A primeira linha vazia não esconde o laboratório declarado depois
  Dado um kit cuja primeira linha traz "-" e a terceira traz "Genera"
  Quando a tela de resultados é renderizada
  Então o bloco 2 exibe "Fonte: Genera"

Cenário: Dois laboratórios no mesmo kit
  Dado um kit com "Genera" em uma linha e "MyHeritage" em outra
  Quando a tela de resultados é renderizada
  Então o cartão exibe "Fonte: Genera"
  E o cartão traz o aviso "fontes_divergentes" com os dois rótulos

Cenário: Painel de cobertura com os oito números
  Dado um arquivo de 617 linhas, 456 evidências, 11 laboratórios em 45 grafias e 22 cromossomos
  Quando a tela de resultados é renderizada
  Então o painel exibe "617", "456", "11", "22", a mediana de cM, o percentual abaixo de 10 cM e o percentual sem bloco de 15 cM
  E o painel nasce aberto e pode ser recolhido

Cenário: Corte não declarado é dito, e não inventado
  Dado um arquivo que não declara o corte da busca
  Quando o painel é renderizado
  Então ele diz que o arquivo não declara o corte
  E diz que ausência no arquivo não é ausência de parentesco

Cenário: Medida robusta
  Dado um cartão com total de 154,5 cM, maior bloco de 56,9 cM e 15.959 SNPs
  Quando o cartão é renderizado
  Então ele exibe "robusta"
  E exibe os três números
  E exibe "qualidade da medida, não do parentesco"

Cenário: Medida parcial por bloco pequeno
  Dado um cartão com total de 51,3 cM, maior bloco de 13,7 cM e 7.349 SNPs
  Quando o cartão é renderizado
  Então ele exibe "parcial"
  E nomeia o bloco de 13,7 cM como motivo

Cenário: Medida parcial por poucos SNPs
  Dado um cartão com total e bloco acima de 15 cM e 800 SNPs
  Quando o cartão é renderizado
  Então ele exibe "parcial"
  E nomeia os 800 SNPs como motivo

Cenário: Medida insuficiente
  Dado um cartão com total de 9,1 cM
  Quando o cartão é renderizado
  Então ele exibe "insuficiente"

Cenário: Sem evidência, sem painel
  Dado um CSV sem nenhuma evidência utilizável
  Quando a tela de resultados é renderizada
  Então o painel não é renderizado
  E o aviso de falta de evidência continua no cartão

Cenário: Nenhum veredito muda
  Dado o arquivo real analisado antes e depois da feature
  Quando as duas telas são comparadas
  Então o confronto, a viabilidade, o caminho, a ordem dos cartões, a contagem e o CSV de descartes são idênticos
  E o SHA_DA_TELA da tela de entrada não mudou

Cenário: Contagem por laboratório no painel
  Dado um arquivo com 183 evidências de Genera e 127 de MyHeritage
  Quando o painel é renderizado
  Então ele lista os dois rótulos com as respectivas contagens
  E os cartões continuam com a fonte do seu próprio kit

Cenário: Arquivo sem coluna de fonte
  Dado um CSV sem nenhuma coluna reconhecida como fonte
  Quando o painel é renderizado
  Então o item de laboratórios diz "nenhuma fonte declarada"
  E nenhum cartão inventa laboratório
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Sem catálogo, a tela continua exibindo texto de formulário como laboratório |
| RF-02 | Must | Esconder o original repetiria o erro que a leitura tolerante do CSV existe para evitar |
| RF-03 | Must | Sem os três desfechos, valor desconhecido vira laboratório inventado |
| RF-04 | Must | É a correção que faz a fonte declarada aparecer |
| RF-05 | Should | Divergência é rara, mas silenciá-la seria escolher por conta própria |
| RF-06 | Must | É o retrato que hoje não existe |
| RF-07 | Must | Número sem frase vira ornamento; as frases são a leitura |
| RF-08 | Must | É o que orienta qual cartão ler primeiro |
| RF-09 | Must | Sem a ressalva, o estado lê-se como selo de parentesco |
| RF-10 | Must | Fora da guarda é o que faz o painel existir sem cartões |
| RF-11 | Must | É o contrato de não-regressão |
| RF-12 | Could | Ajuda a entender de onde vem o arquivo, mas não é a decisão |
| RF-13 | Could | Arquivo sem coluna de fonte é caso possível, não o caso medido |

## 9. Esclarecimentos

### Sessão 2026-10-22

- **Q:** Duas grafias do arquivo real não têm laboratório óbvio — `Minha herança` / `Minha Herança`
  (9 células) e `Meu Patrimônio` (1 célula). Como tratá-las?
  **R:** As duas como `não declarada`, nunca como laboratório suposto. O catálogo fica em 11 laboratórios
  e a contagem do MyHeritage cai de 127 para 118.
- **Q:** Onde o painel "Cobertura do arquivo" deve viver na tela?
  **R:** Bloco novo, imediatamente antes dos cartões. O bloco "Observações do arquivo" fica intocado, e o
  contrato do adendo `017` não muda.
- **Q:** O piso de 900 SNPs entra no estado da medida?
  **R:** Sim, como terceira condição de `parcial` — 4 dos 50 cartões `robusta` do arquivo real caem para
  `parcial` por SNPs abaixo de 900.
- **Q:** O painel deve listar a contagem por laboratório (RF-12)?
  **R:** Sim, lista completa em ordem decrescente de contagem e alfabética no empate.

## 10. Lacunas

- 🟡 **`TestCompany` não é reconhecida como coluna de fonte** (`src/core/genetic_evidence.py:86`). O export
  de um-para-muitos do GEDmatch do projeto usa esse nome, e a fonte se perde. Não é escopo desta feature;
  fica registrado para uma próxima.
- 🟡 **`source` não tem regra catalogada** no `code-analysis.md` (não há `BR-D` para ele); a única descrição
  é a linha do `data-dictionary.md#51`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-22 | Sessão de esclarecimentos: empresa não confirmada vira `não declarada`, painel como bloco novo antes dos cartões, piso de 900 SNPs confirmado e contagem por laboratório completa | reversa |
