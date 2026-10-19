# Legacy impact: refino visual do cartão de resultado

> Data: `2026-10-19`
> Feature: `036-refino-do-cartao-de-resultado`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/templates/index.html` | Template da tela (borda de apresentação, `architecture.md#3`) | `regra-alterada` | MEDIUM | O `h5` do cartão de resultado ganha `span.conteudo-do-cabecalho`, `span.titulo-da-conexao` e `span.selos-do-cabecalho`. Nenhum elemento, rota, dado ou texto novo; nenhum `div` dentro do `card-header` |
| `src/assets/app.css` | Folha de estilo da tela, servida por `GET /app.css` (borda de apresentação) | `regra-alterada` | LOW | Bloco novo escopado em `.cartao-do-resultado` (casco, barra, três faixas, pílula, indicador, hover e telefone). As regras genéricas de `summary` ficam intactas |

Nenhum `componente-novo`, `componente-extinto`, `regra-removida`, `delta-de-dados` ou
`delta-de-contrato-externo`.

## 2. Diff conceitual por componente

### Template da tela

O cabeçalho do cartão de resultado continua `details.card.cartao-do-resultado` →
`summary.sumario-do-cartao` → `div.card-header` → `h5`. Dentro do `h5`, o conteúdo passou a ser
agrupado por três `span`s: o título (`titulo-da-conexao`), a faixa dos selos (`selos-do-cabecalho`)
e a faixa de sinais (`cabecalho-sinais`, que já existia). O link `voltar-ao-indice` continua no
mesmo lugar do documento, entre os selos e os sinais, e o `visually-hidden` continua nomeando o
destino.

A árvore foi escolhida para não quebrar os extratores dos testes, que leem o `card-header` até o
primeiro `</div>` — por isso não há `div` novo. O cartão continua fechado por padrão, com o `id` no
`details`.

### Folha de estilo

O bloco novo usa apenas tokens existentes: degradê `--surface → --surface-2`, barra
`--muted → --head`, borda `--line`, fundo da pílula `--surface` e texto herdado `--primary`. Não há
literal de cor novo, fonte nova, `!important` nem requisição nova.

O arranjo das faixas é um grid de três linhas com áreas nomeadas (`titulo`, `selos`, `sinais`,
`acao`), e a coluna `acao` atravessa as três. Abaixo de 575,98 px as áreas empilham e o "Voltar"
desce para a própria linha.

## 3. Preservadas

- `_reversa_sdd/domain.md#5` — as mensagens e rótulos da tela continuam ao caractere (nenhum literal
  mudou; `W005` da feature 006).
- `_reversa_sdd/domain.md#2.1` — os quatro estados do confronto e suas classes CSS
  (`estado-COMPATIVEL`, `estado-POSSIVEL`, `estado-CONFLITANTE`, `estado-INCONCLUSIVO`).
- Adendo `018` — o `card-header` embrulhado pelo `summary`, o cartão fechado e o `id` no `details`.
- Adendo `019` — `cabecalho-sinais` no cabeçalho, com `rotulo-parentesco`.
- Adendo `020`/`022` — os blocos "Matches descartados" e "Observações do arquivo" intocados.
- Adendo `026` — os quatro tokens `--st-*` e o cinza do `INCONCLUSIVO`.
- Adendo `031` — a família de contorno do selo de validação.

## 4. Modificadas

Nenhuma regra de `_reversa_sdd/domain.md` foi alterada ou removida. A única regra de comportamento
visual alterada é a do hover do `summary` no cartão (o sublinhado global deixa de valer ali), e ela
não é regra de domínio: é apresentação, registrada em `app.css:242` e neutralizada por seletor
escopado.
