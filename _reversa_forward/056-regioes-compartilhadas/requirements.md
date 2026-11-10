# Requirements: regiões compartilhadas a partir do CSV de matches

> Identificador: `056-regioes-compartilhadas`
> Data: `2026-11-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> **Substitui o insumo da feature 055.** O arquivo de triangulação (pares de kits) sai de cena; a
> região passa a nascer do próprio CSV de matches do Ancestor Projects.

## 1. Resumo executivo

A feature 055 agrupava matches por cromossomo, mas exigia um **segundo arquivo** — o CSV de
triangulação do GEDmatch — porque só ele dizia quais matches compartilham faixa **entre si**. O
operador decidiu não enviar mais esse arquivo: o agrupamento passa a sair do **CSV de matches do
Ancestor Projects**, que já traz `Chromosome`, `Start`, `End` e `cM` por segmento. A região afirma
menos e entrega o mesmo valor de triagem: são matches que compartilham a mesma faixa **com o kit do
arquivo**, e o desfecho documental continua vindo dos cartões já calculados. O piso de 10 cM deixa de
ser marca e vira **filtro**, porque sem a confirmação entre os matches o segmento pequeno é a maior
fonte de falso grupo.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/analise-dna/requirements.md#Evidência genética` | Os segmentos já são lidos por match, com cromossomo, início, fim e cM (`BR-D-08`..`BR-D-18`) | 🟢 |
| `_reversa_sdd/domain.md#3.2` | A evidência é chaveada por **(nome, kit)** e nenhum total é somado entre kits | 🟢 |
| `_reversa_sdd/addenda/055-grupos-de-triangulacao.md` | O bloco de grupos, o desfecho e o alerta de acúmulo nasceram aqui | 🟢 |
| `_reversa_sdd/addenda/039-dna-sem-correspondencia.md` | Leitura derivada: não cria cartão e não afirma parentesco | 🟢 |
| `.reversa/principles.md#V` | Toda suposição de genealogia genética cita a fonte; número sem origem é chute | 🟢 |

### Medição que sustenta o filtro (2026-11-09)

`DNA_Nordestino.csv` — 783 linhas, 606 kits, 23 cromossomos, **76 % dos segmentos abaixo de 10 cM**:

| Critério | Regiões | Maximais | Kits cobertos | Maior região |
|---|---:|---:|---:|---:|
| Sem piso | 535 | 158 | **553 de 606** | 45 kits |
| Com piso de 10 cM | 70 | **32** | **108 de 606** | 12 kits |

Sem o piso, quase todo kit entra em alguma região — o bloco perde poder de decisão.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Genealogista Genético | Ver quais matches se agrupam numa faixa e o que a árvore diz de cada um | Roda a análise de DNA com o CSV do Ancestor Projects e vê três matches sobre o chr 7 com desfecho parcial |
| Genealogista Genético | Distinguir grupo real de acúmulo antes de pesquisar | Vê 9 kits numa faixa de 0,4 Mb com cM ~10 e o selo de acúmulo |

## 4. Regras de negócio

1. **RN-01: região é um conjunto de ≥ 3 matches distintos com interseção comum no mesmo cromossomo.** 🟢
2. **RN-02: só segmento de 10 cM ou mais entra** — o piso é **filtro**, não marca. 🟢 (medido na §2)
3. **RN-03: a faixa da região é a interseção, nunca a união.** 🟢
4. **RN-04: o desfecho documental vem dos cartões já produzidos**, sem segundo matching: convergente, dividido, parcial ou sem ancestral documentado. 🟢
5. **RN-05: região de acúmulo é alerta, não quinto desfecho** — ≥ 8 kits e (extensão < 2 Mb ou cM máximo < 12). 🟡
6. **RN-06: nenhum cM é somado** — a região guarda mínimo e máximo por segmento. 🟢
7. **RN-07: a identidade do membro é o kit**; sem coluna de kit, o nome normalizado. 🟢
8. **RN-08: um match com mais de um segmento na janela conta uma vez**, e vale o de maior cM. 🟢
9. **RN-09: o bloco não afirma triângulo fechado** — o texto diz que o compartilhamento é com o kit do arquivo. 🟢
10. **RN-10: leitura derivada** — não cria cartão, não altera cM, caminho, veredito nem descartes. 🟢
11. **RN-11: ordem determinística** — cromossomo natural, posição inicial, conjunto de kits. 🟢
12. **RN-12: limite de 200 regiões**, com truncamento declarado. 🟡

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite |
|----|-----------|------------|--------------------|
| RF-01 | Produzir as regiões a partir do CSV de matches, **sem arquivo adicional** | Must | Nenhum formulário novo aparece; a análise de DNA de hoje já produz o bloco |
| RF-02 | Aplicar o piso de 10 cM como filtro | Must | Segmentos de 9 cM não formam região |
| RF-03 | Agrupar por interseção comum e devolver regiões maximais | Must | Na amostra, 32 regiões maximais com o piso |
| RF-04 | Apresentar cromossomo, faixa em pb, extensão em Mb, cM mínimo e máximo, e membros com kit e nome | Must | A faixa exibida é a interseção |
| RF-05 | Classificar o desfecho em convergente, dividido, parcial ou sem ancestral documentado | Must | Um membro com caminho e dois sem → parcial |
| RF-06 | Marcar região de acúmulo pelo critério da `RN-05` | Should | 9 kits em 0,4 Mb recebem o selo |
| RF-07 | Exibir o bloco antes dos cartões, aberto, no regime da cobertura | Must | Visível sem clique |
| RF-08 | Exportar as regiões em CSV por `POST /regioes.csv` | Should | Dialeto de `/descartes.csv`, com BOM e `;` |
| RF-09 | Declarar no bloco que o compartilhamento é com o kit do arquivo | Must | A frase existe no texto do bloco |
| RF-10 | Não alterar cartões, cM, caminhos, vereditos, descartes nem o CSV de descartes | Must | Sem regiões, a tela é a de antes |
| RF-11 | Manter a ordem determinística | Must | Duas execuções produzem a mesma ordem |
| RF-12 | Remover o arquivo de triangulação: formulário, campo, ação e adaptador | Must | `GET /` volta ao hash de antes da 055 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência |
|------|-----------|-----------|
| Desempenho | Custo log-linear; nenhuma comparação de todos com todos | 783 linhas processadas em milissegundos |
| Memória | Nenhuma estrutura quadrática | Os segmentos entram como registros |
| Reprodutibilidade | Ordem total e determinística | Cinco testes de ordem |
| Dependências | Nenhuma nova | Bibliotecas já fixadas |
| Privacidade | Fixtures sintéticas; amostra real fora do repositório | `.reversa/principles.md#I` |
| Acessibilidade | Selos com o contraste preso por teste | `tests/test_estilo_da_tela.py` |

## 7. Critérios de Aceitação

```gherkin
Cenário: três matches sobrepostos viram região
  Dado um CSV de matches com três kits sobre a mesma faixa do chr 7, todos com 10 cM ou mais
  Quando a análise de DNA roda
  Então o bloco mostra uma região com os três kits
  E a faixa é a interseção dos três

Cenário: segmento abaixo do piso não forma região
  Dado três kits sobrepostos em que um tem 9 cM
  Quando a análise roda
  Então nenhuma região é formada

Cenário: desfecho parcial
  Dado uma região em que um membro tem caminho documental e dois não
  Quando a análise roda
  Então o desfecho é parcial
  E a região diz quantos de quantos têm caminho

Cenário: região de acúmulo
  Dado nove kits numa faixa de 0,4 Mb com cM em torno de 10
  Quando a análise roda
  Então a região recebe o selo de acúmulo
  E o desfecho não é alterado

Cenário: o bloco não promete triângulo
  Dado uma região exibida
  Quando o operador lê o texto do bloco
  Então encontra a ressalva de que o compartilhamento é com o kit do arquivo

Cenário: sem regiões, nada muda
  Dado um CSV sem segmentos sobrepostos
  Quando a análise roda
  Então o bloco não aparece
  E os cartões e o CSV de descartes são os de antes
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01/02/03 — região e piso | Must | É o núcleo da mudança |
| RF-04/05 — faixa e desfecho | Must | É o produto |
| RF-10/12 — nada mais muda e o insumo antigo sai | Must | A mudança é de insumo, não de comportamento |
| RF-09 — ressalva | Must | Sem ela, o bloco promete o que o arquivo não prova |
| RF-06/08 — acúmulo e CSV | Should | Alertas e auditoria fora da tela |

## 9. Esclarecimentos

### Sessão 2026-11-09

- **Q:** Com que piso de cM os segmentos entram no agrupamento?
  **R:** 10 cM, como **filtro**. Medido: sem piso, 158 regiões e 553 dos 606 kits; com piso, 32 regiões e 108 kits.
- **Q:** O bloco continua se chamando "grupos de triangulação"?
  **R:** Não. Passa a **"Regiões compartilhadas"**, porque o CSV de matches não confirma o compartilhamento entre os matches.

## 10. Lacunas

Nenhuma dúvida aberta. Limitação declarada: o bloco não confirma que os matches compartilham entre
si; para isso seria preciso o arquivo de pares, que esta feature removeu por decisão do operador.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-09 | Versão inicial, substituindo o insumo da 055 | reversa |
