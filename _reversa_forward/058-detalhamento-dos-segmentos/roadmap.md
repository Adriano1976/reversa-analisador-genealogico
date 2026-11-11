<!--
Roadmap da feature 058 — Detalhamento dos segmentos compartilhados.
Gerado por /reversa-plan como DELTA sobre o legado.
-->

# Roadmap: Detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Requirements: `_reversa_forward/058-detalhamento-dos-segmentos/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A tabela é a **terceira leitura** do mesmo dado que o bloco já projeta. O que falta hoje é a linha
por segmento: `projetar_regioes` entrega a região com `membros_lista`, mas não os segmentos um a um.
Então nasce um agregado `core/segmentos.py` que achata as regiões em segmentos, na ordem fixada pela
`RN-03`, e guarda o **índice da região**; a projeção `application/segmentos.py` formata dicionário; a
tela renderiza tudo de uma vez.

O clique não inventa mecanismo: cada faixa do ideograma ganha `id="regiao-N"`, cada linha aponta para
esse `id`, e o destaque é `:target` — o mesmo recurso que a tela já usa em cartão. Busca, filtro e
paginação são **camada de apresentação** sobre o HTML já servido (precedente da 046): um script marca
`hidden` nas linhas que não pertencem à vista, atualiza o contador e desenha os controles. Sem
JavaScript, a tabela aparece inteira e legível — o que se perde é filtrar, não o dado.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Testes usam a fixture sintética da 057 (`DNA_CSV_SEGMENTOS_DISTRIBUICAO`), de 11 segmentos | respeita |
| II. Comportamento observável é preservado em refatoração | `projetar_regioes` ganha **uma chave** (`indice`) e o ideograma ganha um `id`; nenhuma saída existente muda de valor, e o `/regioes.csv` não é tocado | respeita |
| III. Nenhuma mudança sem teste que a cubra | `RN-03` (ordem), `RN-02` (uma linha por par), o vínculo âncora↔faixa e o estado vazio têm teste próprio | respeita |
| IV. Arestas do grafo são tipadas | n/a: a feature não percorre o grafo | respeita |
| V. Toda suposição de cita a fonte | O cM da linha é o do segmento que forma a região — não é total, e o cabeçalho da tabela diz "cM"; nenhum número novo é inventado | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Agregado em `src/core/segmentos.py`, com dataclass `SegmentoDeRegiao` e `segmentos_das_regioes` | A ordenação e o achatamento são regra de domínio (ordem natural de cromossomo, depois início, depois kit) e precisam de teste sem HTTP | (a) achatar no template; (b) achatar em `app.py` | 🟢 |
| D-02 | `SegmentoDeRegiao` guarda **`regiao_indice`** (1-based) além dos campos do segmento | É o vínculo estável entre a linha e a faixa do ideograma; derivar de cromossomo+início quebraria quando o CSV trouxer o cromossomo em caixa diferente | (a) `id` por cromossomo+início; (b) índice de linha | 🟢 |
| D-03 | `projetar_regioes` ganha a chave `indice` (1-based) e o ideograma passa a emitir `id="regiao-N"` | A âncora tem de existir nos dois lados; `montar_ideograma` já repassa as chaves do item, então basta a projeção preencher | (a) calcular índice no template com `loop.index` (quebra quando o ideograma reordena por cromossomo) | 🟢 |
| D-04 | `ordem_do_cromossomo` vira pública em `core/distribuicao.py` e `core/segmentos.py` a importa | Evita a terceira cópia da ordem natural; a 057 já tem teste que compara o núcleo ao `reporting/ideograma.py` | (a) duplicar a função; (b) `core/segmentos.py` importar `reporting` (proibido pelo `ADR-34`) | 🟢 |
| D-05 | Tabela em `<table>` semântica, com `<th scope="col">`, `caption` e `<tbody>` | Leitor de tela e impressão dependem da estrutura; a tela não tem outra tabela de dados para copiar | (a) `div` com `role="table"`; (b) lista de cartões | 🟢 |
| D-06 | Busca, filtro e paginação num `<script>` no fim do documento, escondendo `<tr>` com `hidden` | Precedente da 046: nada é recarregado, a análise não é refeita, e o HTML continua completo sem JavaScript | (a) filtrar no servidor com query string (reparsearia o GEDCOM); (b) `:has()` com seletores (não filtra texto) | 🟢 |
| D-07 | O `data-busca` de cada linha concatena cromossomo, kit e nome, normalizado | Uma célula escondida com o texto reduzido evitaria depender de acento e caixa no script | (a) ler o texto das células no JS; (b) busca por coluna | 🟡 |
| D-08 | Linha clicável via JavaScript **e** link real no badge do cromossomo | O clique na linha inteira é o pedido; o link no badge garante teclado e o caso sem JavaScript, sem aninhar controles interativos | (a) só o badge como link; (b) `onclick` na `<tr>` sem link | 🟢 |
| D-09 | Destaque da faixa com `:target` e `scroll-margin-block-start` na faixa | Sem JavaScript, e o deslocamento evita que a faixa fique sob a barra fixa do topo | (a) classe via JS; (b) `animation` de pulso | 🟢 |
| D-10 | Copiar com `navigator.clipboard`, com o rótulo mudando para "copiado" por 2 s | É a ação de "copiar detalhes" do pedido; falha de permissão não pode quebrar a tabela | (a) `document.execCommand`; (b) selecionar o texto | 🟡 |
| D-11 | Paginação com seletor 10/20/30, 20 como padrão | Decisão 4b do clarify e o mesmo controle da lista de cartões (046) | (a) 20 fixo; (b) rolagem interna | 🟢 |
| D-12 | Tabela **depois da distribuição e antes da lista de regiões** | Decisão 2a do clarify: detalhe fino antes do resumo por região | (a) substituir a lista; (b) cartão recolhível próprio | 🟢 |

## 4. Premissas

Nenhuma: as três `[DÚVIDA]` foram fechadas na sessão de 2026-11-11.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `analise-dna` (núcleo) | `_reversa_sdd/architecture.md#3` | componente-novo | `src/core/segmentos.py` achata as regiões em segmentos ordenados |
| Projeção da tela | `_reversa_sdd/architecture.md#3` (`application/`) | componente-novo | `src/application/segmentos.py` projeta os dicionários da tabela |
| Projeção das regiões | `src/application/regioes.py` | delta-de-dados | Cada região ganha `indice`, usado como âncora |
| Núcleo da distribuição | `src/core/distribuicao.py` | regra-alterada | `ordem_do_cromossomo` passa a ser pública (mesmo comportamento) |
| Desenho do resultado | `src/reporting/ideograma.py` | contrato-alterado | A faixa carrega o `indice` da região; o `id` é emitido no template |
| Página de resultado | `src/templates/index.html` | contrato-alterado | Seção nova: título, contador, toolbar, tabela, paginação e script |
| Folha de estilo | `src/assets/app.css` | regra-alterada | Tabela, toolbar, `:target` da faixa, `scroll-margin` e impressão |

Não muda: `src/parsers/`, `src/ports/`, `src/core/regioes.py` (o agrupador), `src/reporting/csv_das_regioes.py`,
o esquema PostgreSQL e as rotas existentes.

## 6. Delta no modelo de dados

- Resumo: um tipo de domínio novo (`SegmentoDeRegiao`), uma chave nova na projeção de regiões e uma
  chave nova no contexto do template. **Nada é persistido** e o `/regioes.csv` não muda.
- Detalhe completo em: `_reversa_forward/058-detalhamento-dos-segmentos/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /` (HTML do resultado) | HTTP, marcação dentro da resposta existente | n/a — sem rota nova e sem campo de formulário |
| `POST /regioes.csv` | HTTP, arquivo | n/a — o CSV continua com uma linha por região |

Sem `interfaces/`: a feature não abre contrato externo novo.

## 8. Plano de migração

n/a. Nada é persistido; a tabela é recalculada a cada análise, e não há estado de filtro a preservar
entre requisições.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Tabela grande (até 200 regiões × kits) inchar o HTML | médio | baixa | O bloco já nasce fechado; a análise real medida produziu 32 regiões (≈130 linhas); a paginação é de apresentação, o custo é o markup |
| Duas paginações no mesmo documento (cartões da 046 e tabela) disputando o script | alto | baixa | Escopos separados (`data-*` distintos), um único `<script>` com dois blocos independentes |
| A âncora apontar para a faixa errada se a ordem das regiões mudar | alto | baixa | O índice nasce em `projetar_regioes` e é consumido pelos dois lados no mesmo render; teste de contrato prende o par linha↔faixa |
| Filtro perder acento/caixa | médio | média | Normalização em Python no `data-busca` (`norm_name`/minúsculas sem acento) e no JS só `toLowerCase` |
| Impressão esconder linhas por causa da paginação | médio | média | `@media print` força `display:table-row` nas linhas ocultas |
| `SHA_DA_TELA` mudar por engano | alto | baixa | A seção só existe com resultado; o hash da tela vazia continua no teste |
| Clique da linha conflitar com o botão de copiar | baixo | média | O handler ignora cliques dentro do botão de copiar |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] Ordem (`RN-03`), posição (`RF-01`), âncora↔faixa (`RF-10`) e estado vazio (`RF-12`) com teste
- [ ] `SHA_DA_TELA` inalterado, com a medição em `evidence/`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-11 | Versão inicial gerada por `/reversa-plan` | reversa |
