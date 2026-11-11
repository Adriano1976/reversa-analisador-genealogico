<!--
Roadmap da feature 057 — Distribuição por cromossomo.
Gerado por /reversa-plan como DELTA sobre o legado; não redescreve a arquitetura.
-->

# Roadmap: Distribuição por cromossomo

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Requirements: `_reversa_forward/057-distribuicao-por-cromossomo/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

O gráfico é **mais uma leitura derivada** do mesmo dado que a 056 já projeta: as regiões
compartilhadas, que guardam os segmentos e o cM de cada um. A conta (kits distintos e média de
cM por cromossomo) nasce numa função pura nova em `core/`, chamada logo depois da classificação
das regiões e **guardada por try/except**, para que uma falha na agregação nunca derrube a
análise. A projeção para dicionário fica em `application/` (o template não importa `core/` —
`ADR-34`), e a geometria do desenho — base zero, topo arredondado, altura de cada barra em
porcentagem — fica em `reporting/`, como o ideograma da 056. No template, o sub-bloco entra
**depois da legenda do ideograma e antes da lista de regiões**, com as duas barras por cromossomo
em CSS (sem biblioteca de gráfico, sem SVG novo), reaproveitando o padrão de cartão do hover e de
botão focável que a 056 já fixou. Nenhuma rota, nenhuma tabela, nenhum veredito mudam.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Testes usam CSV sintético (`tests/fixtures/sample_dna.py` + CSV inline). O gráfico expõe **só agregados**: nenhum nome, kit ou coordenada no cartão (`RN-07`) | respeita |
| II. Comportamento observável é preservado em refatoração | Componentes existentes (`dna_analysis`, `projetar_regioes`, `montar_ideograma`, `/regioes.csv`) não mudam de saída; a feature **acrescenta** campo e marcação | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada regra (`RN-02`, `RN-03`, `RN-06`, `RN-08`) ganha teste próprio antes de o template usar o número | respeita |
| IV. Arestas do grafo são tipadas | n/a: a feature não percorre o grafo | respeita |
| V. Toda suposição de genealogia genética cita a fonte | "cM médio" declara a base (segmentos das regiões, ≥ 10 cM) na legenda e no docstring; o eixo é número e também é declarado (`RN-08`) | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Agregação numa função pura nova em `src/core/distribuicao.py`, recebendo `RegiaoCompartilhada` | A conta é de domínio (kit distinto, média de cM), é testável sem HTTP e mantém `core/` sem importar tela | (a) calcular no template; (b) recalcular sobre o DataFrame; (c) somar no `application/` | 🟢 |
| D-02 | A chamada fica em `application/dna_analysis.py`, num `try/except` que devolve tupla vazia em falha | A análise já é longa e dominada pelo parse; a leitura derivada não pode derrubá-la — mesma política da 056 | (a) chamar em `core/dna_analysis.py` com um segundo sink; (b) chamar na borda | 🟢 |
| D-03 | `ResultadoDeAnalise` ganha `distribuicao: tuple = ()` | Mantém o contrato do caso de uso explícito e deixa o default compatível com quem já monta o objeto | (a) derivar no `app.py` a partir de `regioes`; (b) campo opcional dict | 🟢 |
| D-04 | `src/application/distribuicao.py::projetar_distribuicao` devolve dicionários crus, sem formatar | Mesma regra de `projetar_regioes`: formatação é do filtro do template | (a) formatar na projeção; (b) devolver `dataclass` ao template | 🟢 |
| D-05 | `src/reporting/distribuicao.py::montar_distribuicao` calcula topo dos eixos, marcas e altura em % | Geometria é desenho, não domínio; o `reporting/ideograma.py` já é o precedente | (a) calcular altura no CSS com `calc` por valor; (b) fazer a conta no template | 🟢 |
| D-06 | Barras em CSS (colunas com `height` em %), não em SVG | Imprime sem JavaScript, reaproveita os tokens e é o mesmo vocabulário do ideograma; o teste de origem externa continua valendo | (a) SVG inline; (b) biblioteca de gráfico (proibida: CDN); (c) `canvas` (exige JS) | 🟢 |
| D-07 | Duas cores de token: `--primary` para Matches e `--ink` para cM médio | Não introduz cor nova e não usa `--st-*`, que nesta tela já significa **desfecho**; a diferença não depende de cor, porque a legenda nomeia e o cartão traz os números | (a) `--st-compativel`/`--st-possivel`; (b) `color-mix` novo; (c) textura | 🟢 |
| D-08 | Topo de eixo = "número redondo" ≥ maior valor, com 4 marcas a partir do zero | `RN-08` proíbe base deslocada; 4 marcas é o que cabe na altura do bloco | (a) topo no maior valor exato; (b) marcas automáticas por biblioteca | 🟡 |
| D-09 | Ordem natural do cromossomo implementada em `core/distribuicao.py`, com teste que a compara à de `reporting/ideograma.py` | Hoje a ordem vive só no `reporting`; duas implementações divergentes (10 antes de 9) passariam despercebidas | (a) duplicar sem teste; (b) fazer `reporting` importar `core` (proibido pelo `ADR-34`) | 🟢 |
| D-10 | Reaproveitar `.dica` e o botão focável da 056 para o cartão do cromossomo | O padrão já existe, já é testado e já resolve teclado + leitor de tela | (a) cartão novo com posicionamento próprio; (b) `title` nativo | 🟢 |
| D-11 | Nenhuma rota nova e nenhuma coluna nova em `/regioes.csv` (`RF-12`) | O número do gráfico é derivável das mesmas linhas do CSV de regiões; exportar agregado criaria uma segunda fonte | (a) coluna `cromossomo_total`; (b) rota `/distribuicao.csv` | 🟢 |
| D-12 | Dentro do cromossomo, a média de cM usa **um segmento por kit**, o de maior cM (desempate pelo menor início) | `RN-02` conta kits distintos; sem a mesma deduplicação, um kit em duas regiões do mesmo cromossomo entraria duas vezes na média e a denominador deixaria de casar com a série de matches. O critério é o mesmo de `_montar` (`src/core/regioes.py`) | (a) média sobre todos os segmentos das regiões, com kit repetido; (b) média sobre todas as linhas do CSV no cromossomo (inclui < 10 cM) | 🟡 |

## 4. Premissas

Nenhuma: os três `[DÚVIDA]` do `requirements.md` foram fechados na sessão de esclarecimentos de
2026-11-10, e a quarta pergunta virou a regra `RN-08`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `analise-dna` (núcleo) | `_reversa_sdd/architecture.md#3` | regra-alterada | Passa a expor a agregação por cromossomo como leitura derivada, sem tocar em matching, cM ou veredito |
| `ResultadoDeAnalise` (payload do caso de uso) | `_reversa_sdd/data-dictionary.md#8.2` | contrato-alterado | Campo novo `distribuicao` (tupla), default vazio |
| Projeção da tela | `_reversa_sdd/architecture.md#3` (`application/`) | componente-novo | `application/distribuicao.py` projeta o agregado em dicionários |
| Desenho do resultado | `_reversa_sdd/architecture.md#3` (`reporting/`) | componente-novo | `reporting/distribuicao.py` calcula eixos, marcas e altura das barras |
| Página de resultado | `src/templates/index.html` (bloco `regioes-compartilhadas`) | contrato-alterado | Sub-bloco novo entre a legenda do ideograma e a lista de regiões |
| Folha de estilo | `src/assets/app.css` (`§ Ideograma`) | regra-alterada | Classes do gráfico; nenhum token novo |

Não muda: `src/parsers/`, `src/ports/`, `src/core/matching.py`, `src/core/regioes.py` (a agregação
é módulo novo, não alteração do agrupador), o esquema PostgreSQL e as rotas existentes.

## 6. Delta no modelo de dados

- Resumo das mudanças: um tipo de domínio novo (`ResumoDoCromossomo`) e um campo novo no payload
  do caso de uso; **nada é persistido** e o esquema do banco não muda.
- Detalhe completo em: `_reversa_forward/057-distribuicao-por-cromossomo/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` (HTML do resultado) | HTTP, marcação dentro da resposta existente | n/a — sem rota nova, sem campo de formulário; o contrato HTTP não muda |
| `POST /regioes.csv` | HTTP, arquivo | n/a — `D-11`: o CSV não ganha coluna |

Nenhum diretório `interfaces/` é criado: a feature não abre contrato externo novo, só acrescenta
marcação dentro de uma resposta que já existe.

## 8. Plano de migração

n/a. Não há dado persistido, nem formato de arquivo, nem versão de esquema a migrar: a agregação
é calculada em memória a cada análise, e a tela antiga não guarda estado do gráfico.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Leitura errada de dois eixos (concluir correlação entre séries) | alto | médio | Eixos rotulados, base zero (`RN-08`), legenda declarando que cada série tem escala própria (`RN-04`) e cartão com os dois números |
| Divergência entre a ordem de cromossomo do núcleo e a do ideograma (`10` antes de `9`) | médio | baixa | `D-09`: teste que compara as duas ordens no mesmo conjunto |
| Contagem de "Matches" inflada por não deduplicar kit entre regiões do mesmo cromossomo | alto | médio | `RN-02` com teste que usa um kit em duas regiões do mesmo cromossomo |
| Rótulos de 22+ cromossomos sem espaço no eixo | médio | médio | Rótulo curto `Chr N`, giro de 45° e largura mínima por coluna; o cartão e o `aria-label` carregam o nome completo |
| O bloco ficar pesado e empurrar a lista de regiões para longe | baixo | médio | Altura fixa do gráfico (≈ 9 rem) e largura total do cartão, sem sombra nem moldura extra |
| `SHA_DA_TELA` mudar por engano | alto | baixa | O sub-bloco só renderiza com resultado; o hash da tela vazia é verificado no mesmo teste que já existe |
| Média de cM interpretada como "cM da região" | médio | baixo | A legenda e o docstring dizem "média dos segmentos das regiões (≥ 10 cM)"; o rótulo do eixo é "cM médio", não "cM da região" |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `RN-02`, `RN-03`, `RN-06` e `RN-08` com teste próprio, e o teste do contrato da tela
      prendendo a posição do sub-bloco entre a legenda do ideograma e a lista de regiões
- [ ] `SHA_DA_TELA` inalterado, com a medição registrada em `evidence/`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-10 | Versão inicial gerada por `/reversa-plan` | reversa |
