<!--
Requirements da feature 057 — Distribuição por cromossomo.
Gerado por /reversa-requirements a partir do argumento do operador e do _reversa_sdd/.
Máximo de três [DÚVIDA] no documento inicial (seção 10).
-->

# Requirements: Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Dentro do bloco **Regiões compartilhadas**, um gráfico de barras agrupadas mostra, por cromossomo,
quantos matches o arquivo tem e qual o **cM médio** (centimorgan médio) desses segmentos — dois
eixos, duas séries, um cartão de detalhe no hover e no foco de teclado. Entrega uma leitura que
hoje não existe: o ideograma mostra **onde** as regiões caem, e este gráfico mostra **quanto** há
em cada cromossomo e **de que tamanho**. Não muda nenhum veredito: o gráfico lê as regiões já
calculadas.

**Região compartilhada**, neste documento, é o conjunto de matches que compartilham a mesma faixa
de um cromossomo **com o kit do arquivo** (o identificador do match no CSV); não é triângulo
fechado.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/addenda/056-regioes-compartilhadas.md` | A região compartilhada nasce do CSV de matches, com piso de 10 cM **como filtro**; o bloco já tem ideograma por cromossomo e lista de regiões | 🟢 |
| `_reversa_sdd/data-dictionary.md#5.2` | `Segmento` carrega `cromossomo`, `inicio`, `fim`, `cm` e `snps`; o cM é por segmento, nunca somado | 🟢 |
| `_reversa_sdd/data-dictionary.md#8.2` | `ResultadoDeAnalise` leva `regioes` do caso de uso para a tela | 🟢 |
| `_reversa_sdd/domain.md#3.2` | Evidência genética: o cM entra como evidência adicional e nunca decide sozinho | 🟢 |
| `_reversa_sdd/domain.md#2` | Os três eixos (documental, genético, confronto) não se contaminam; nada aqui cria parentesco | 🟢 |
| `_reversa_sdd/code-analysis.md#4.5` | Regras novas da unidade `analise-dna`, incluindo a separação em etapas | 🟢 |
| `_reversa_sdd/architecture.md#3` | Pacotes `core/` (puro), `application/` (projeção), `reporting/` (desenho) e o `ADR-34`: `core/` não é importado por tela nem por relatório | 🟢 |
| `_reversa_sdd/adrs/34-ciclos-quebrados-e-superficies-removidas.md` | A projeção existe para o template e o CSV não importarem `core/` | 🟢 |
| `src/core/regioes.py` (`RegiaoCompartilhada.segmentos`, `SegmentoDaRegiao.cm`) | Cada região guarda os segmentos que a compõem, com o cM de cada um | 🟢 |
| `.reversa/principles.md#V` | Todo número de genealogia genética cita a fonte | 🟢 |
| `tests/test_tela_sem_origem_externa.py` | A tela não pode buscar recurso em origem externa | 🟢 |

Números medidos que servem de âncora (feature 056): 783 segmentos produzem 32 regiões em
0,005 s; o piso de 10 cM leva 158 regiões/553 kits para 32 regiões/108 kits no
`DNA_Nordestino.csv` (`_reversa_forward/056-regioes-compartilhadas/evidence/medicoes.md`).

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador genealogista (dono do projeto) | Ver, de relance, em que cromossomos o arquivo tem mais matches e com que tamanho médio, antes de abrir região por região | Abre "Regiões compartilhadas" e para o mouse sobre o cromossomo com a barra mais alta antes de descer para a lista |
| Operador conferindo qualidade do arquivo | Distinguir arquivo concentrado em poucos cromossomos de arquivo espalhado, sem somar cM na mão | Compara a altura das barras entre cromossomos e lê os dois números no cartão |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O gráfico é **leitura derivada**: agrega as regiões já calculadas na mesma análise e não faz segundo matching, não relê o CSV e não classifica desfecho. 🟢
   - Origem no legado: `_reversa_sdd/addenda/056-regioes-compartilhadas.md` (a região é leitura derivada)
   - Tipo: nova
2. **RN-02:** A série **Matches** conta **kits distintos** — o kit é o identificador do match no arquivo — com pelo menos um segmento naquele cromossomo, contando o kit uma única vez mesmo que ele apareça em duas regiões do mesmo cromossomo. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#3.2` (a identidade da evidência é o kit)
   - Tipo: nova — decidida na sessão de 2026-11-10 (pergunta 1)
3. **RN-03:** A série **cM médio** é a **média aritmética simples** dos cM dos segmentos que compõem as regiões daquele cromossomo, sem ponderar por tamanho e **sem somar** cM entre segmentos nem entre cromossomos. 🟢
   - Origem no legado: `_reversa_sdd/data-dictionary.md#5.2`, `_reversa_sdd/domain.md#3.2`
   - Tipo: nova — decidida na sessão de 2026-11-10 (pergunta 2)
4. **RN-04:** As duas séries têm **escalas independentes** (eixo esquerdo para Matches, direito para cM médio). A altura de uma barra só é comparável com barras da mesma série; o gráfico não insinua correlação entre as duas. 🟢
   - Tipo: nova
5. **RN-05:** O gráfico não altera nenhum número do bloco: contagem de regiões, faixas, kits e desfechos continuam os mesmos, e o piso de 10 cM continua sendo filtro das regiões. 🟢
   - Origem no legado: `src/core/regioes.py` (`PISO_DE_CM`)
   - Tipo: nova
6. **RN-06:** Cromossomo sem região **não entra no eixo**: o gráfico mostra o que o arquivo tem, e inventar cromossomos vazios sugeriria cobertura que não existe. 🟢
   - Tipo: nova
7. **RN-07:** O cartão do detalhe mostra **só agregados** (cromossomo, matches, cM médio) e nenhum nome ou kit de match. 🟢
   - Origem no legado: `.reversa/principles.md#I` (dado pessoal fora de superfície desnecessária)
   - Tipo: nova
8. **RN-08:** Os dois eixos partem de **zero**, e o topo é arredondado para um valor redondo. Eixo com base deslocada fica proibido: barra de dois eixos com base recortada exagera diferença e mente sobre o que o arquivo tem. 🟢
   - Origem no legado: `.reversa/principles.md#V` (nenhum número sem procedência; eixo é número)
   - Tipo: nova — decidida na sessão de 2026-11-10 (pergunta 4)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Sub-bloco "Distribuição por cromossomo" dentro do cartão "Regiões compartilhadas", **depois do ideograma e da sua legenda e antes da lista de regiões**, renderizado na mesma condição do ideograma (há região) | Must | Com uma análise que produz região, o HTML do cartão contém o sub-bloco entre a legenda do ideograma e a primeira região; sem região, o cartão inteiro não aparece | 🟢 |
| RF-02 | Uma barra por cromossomo para **Matches**, lida no eixo da esquerda | Must | O número de barras da série é igual ao de cromossomos distintos com região; a altura é proporcional ao valor pelo eixo esquerdo | 🟢 |
| RF-03 | Uma barra por cromossomo para **cM médio**, lida no eixo da direita | Must | Idem, pelo eixo direito, com a média calculada conforme `RN-03` | 🟢 |
| RF-04 | Dois eixos rotulados ("Matches" à esquerda, "cM médio" à direita), com marcas de escala, ambos **partindo de zero** (`RN-08`) | Must | As legendas dos eixos constam do HTML; cada eixo tem marcas com valor; a marca inferior de cada eixo é zero | 🟢 |
| RF-05 | Eixo dos cromossomos em **ordem natural** (`1..22`, `X`, `Y`, `MT`) e rótulo curto `Chr N` | Must | Cromossomo 10 vem depois do 9 e antes do 11 | 🟢 |
| RF-06 | Ao passar o mouse sobre um cromossomo, o par de barras daquele cromossomo é destacado e abre um cartão com o cromossomo (`Chr N`), o número de matches e o cM médio | Must | O cartão nomeia o cromossomo e os dois números, e o destaque não depende de cor | 🟢 |
| RF-07 | O mesmo cartão abre por **teclado**: cada cromossomo é um controle focável e o `aria-label` repete os dois números | Must | `Tab` percorre os cromossomos; o `aria-label` contém "Matches" e "cM" com valores | 🟢 |
| RF-08 | Legenda nomeia as duas séries e declara a origem do dado (regiões compartilhadas, segmentos de 10 cM ou mais) | Must | A legenda contém os dois nomes de série e a nota de origem | 🟢 |
| RF-09 | O gráfico é marcação gerada no servidor, sem biblioteca de gráfico e sem recurso externo | Must | A página não pede nada fora da origem; o teste de origem externa continua verde | 🟢 |
| RF-10 | O gráfico **imprime** junto do resultado, sem depender de hover | Should | Na impressão, os dois números permanecem legíveis em texto | 🟡 |
| RF-11 | Nenhum cM é somado nem convertido: o valor de `cM médio` é apresentado com o mesmo formato de cM do resto da tela | Must | O valor exibido corresponde à média e usa o mesmo formatador | 🟢 |
| RF-12 | O bloco não ganha ação nova: não há botão, não há exportação própria | Must | A superfície de ações do bloco não muda | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Agregar por cromossomo em uma passada sobre as regiões, sem leitura de arquivo, dentro do orçamento de 5 ms | O agrupamento inteiro leva 0,005 s em 783 segmentos (`056/evidence/medicoes.md`); a agregação é O(regiões) | 🟢 |
| Sem recursos externos | Nenhuma chamada a CDN, fonte remota ou script de terceiro | `tests/test_tela_sem_origem_externa.py`; os recursos da tela são servidos pela própria aplicação desde a 054 | 🟢 |
| Acessibilidade | A informação não existe só na cor nem só no mouse; foco visível; contraste herdado dos tokens | O ideograma da 056 já adotou botão focável e conteúdo no DOM; o gráfico segue a mesma forma | 🟢 |
| Invariante de tela | `GET /` sem resultado não muda: `SHA_DA_TELA` só muda se declarado em `evidence/` | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`), padrão das features 055/056 | 🟢 |
| Privacidade | O gráfico só expõe agregados; nenhum nome, kit ou coordenada de match no cartão do gráfico | `.reversa/principles.md#I` | 🟢 |
| Rastreabilidade do número | Cada eixo declara o que mede, e a origem do dado aparece na legenda | `.reversa/principles.md#V` | 🟢 |
| Fixture | Testes usam CSV sintético; nenhum arquivo real do operador entra no repositório | `.reversa/principles.md#I`; fixtures existentes em `tests/fixtures/sample_dna.py` | 🟢 |
| Impressão | O gráfico usa o mesmo mecanismo de impressão da tela de resultado, sem depender de JavaScript | `src/assets/app.css` (§ impressão) e o padrão da feature 050 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: gráfico por cromossomo com regiões no resultado
  Dado um CSV de matches com regiões em mais de um cromossomo
  Quando o operador abre "Regiões compartilhadas"
  Então o sub-bloco "Distribuição por cromossomo" aparece
  E há um par de barras por cromossomo com região
  E os dois eixos estão rotulados
  E o bloco continua sem ação nova

Cenário: impressão do resultado
  Dado o gráfico renderizado
  Quando o operador imprime o resultado
  Então os dois números de cada cromossomo continuam legíveis em texto

Cenário: detalhe no hover e no teclado
  Dado o gráfico renderizado
  Quando o operador passa o mouse (ou foca pelo teclado) o cromossomo 17
  Então o par de barras do 17 é destacado
  E o cartão mostra "Chr 17", o número de matches e o cM médio

Cenário: a legenda declara a métrica e a origem
  Dado o gráfico renderizado
  Então a legenda nomeia as duas séries
  E declara que os números vêm das regiões compartilhadas, sobre segmentos de 10 cM ou mais
  E o cM médio aparece com o mesmo formato de cM do resto da tela

Cenário: arquivo sem região
  Dado um CSV de matches em que nenhuma região se forma
  Quando a análise termina
  Então o cartão "Regiões compartilhadas" não é renderizado
  E não existe eixo, barra ou legenda do gráfico no HTML
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Sem o sub-bloco a feature não existe |
| RF-02, RF-03 | Must | São as duas séries que dão nome à feature |
| RF-04 | Must | Sem eixo rotulado, barra de dois eixos vira leitura errada; sem base no zero, o eixo exagera a diferença |
| RF-05 | Must | Ordem de cromossomo é convenção do domínio, não estética |
| RF-06, RF-07 | Must | O número exato é o motivo do gráfico; sem hover/foco ele não existe |
| RF-08 | Must | A legenda é o que declara a métrica e a origem |
| RF-09 | Must | Restrição dura do projeto (sem origem externa) |
| RF-10 | Should | Impressão é uso secundário, mas o resultado impresso é uma entrega da 050 |
| RF-11, RF-12 | Must | Não somar cM e não abrir superfície nova são invariantes do produto |
| RNF de desempenho | Should | O ganho é de leitura, não de tempo; mas não pode pesar |

## 9. Esclarecimentos

### Sessão 2026-11-10

- **Q:** A série "Matches" conta o quê? (a) kits distintos, (b) segmentos, (c) kits por região, (d) os dois números no cartão
  **R:** (a) kits distintos com pelo menos um segmento no cromossomo; o kit conta uma vez, mesmo que apareça em duas regiões do mesmo cromossomo. Fecha a dúvida 1 e fixa `RN-02`.
- **Q:** De onde sai o "cM médio"? (a) só dos segmentos das regiões (≥ 10 cM), (b) de todos os segmentos do CSV, (c) só das regiões com a contagem dos descartados, (d) todos com o piso como linha de referência
  **R:** (a) média dos segmentos que formam as regiões, isto é, acima do piso de 10 cM — o gráfico reconcilia com a lista de regiões. Fecha a dúvida 2 e fixa `RN-03`.
- **Q:** Onde o gráfico entra no bloco? (a) acima do ideograma, (b) depois do ideograma e da legenda, (c) em cartão recolhível próprio, (d) substituindo o ideograma
  **R:** (b) depois do ideograma e da sua legenda, antes da lista de regiões. Fecha a dúvida 3 e fixa a posição em `RF-01`.
- **Q:** Como os dois eixos se comportam nos extremos? (a) ambos do zero, topo arredondado, (b) ambos do zero, topo no maior valor, (c) cM a partir do menor valor, (d) cM com marcas fixas
  **R:** (a) ambos partem de zero, com o topo arredondado para um valor redondo. Fixa `RN-08` e o critério de `RF-04`.

## 10. Lacunas

Nenhuma lacuna em aberto nesta versão: as três dúvidas da versão inicial foram fechadas na sessão de 2026-11-10.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-10 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-11-10 | Sessão de esclarecimentos: 4 perguntas respondidas, 3 `[DÚVIDA]` fechadas, `RN-02`/`RN-03` confirmadas e `RN-08` acrescentada | reversa |
