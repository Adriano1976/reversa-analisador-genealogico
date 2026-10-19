# Adendo: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e nos
> adendos `018`, `019`, `020`, `026` e `027`)

## Vigência

Vigente desde 2026-10-19.

## Resumo da entrega

O operador pediu que a apresentação dos **Resultados das Análises de Conexão** ficasse com a estética
do desenho que ele anexou. O cartão de cada conexão deixou de ser uma ficha de duas linhas e passou a
ter **três faixas de leitura** — título, selos e sinais —, com o "Voltar" e o indicador de abrir
ancorados à direita, dentro de uma superfície em degradê com barra lateral, raio de 16 px e sombra.

O que **não** mudou está registrado como restrição, não como promessa: nenhum texto visível ou
escondido mudou (`RF-17`/`W005`), os quatro estados e o selo de cM mantêm classes e cores, a árvore
`details → summary → card-header → h5` continua igual (sem `div` novo no cabeçalho) e os blocos
"Matches descartados" e "Observações do arquivo" ficaram intocados (`RN-07`).

A entrega vive em duas superfícies: `src/templates/index.html` (+6/−1, três `span`s) e
`src/assets/app.css` (+93, bloco escopado em `.cartao-do-resultado`), mais o teste novo
`tests/test_cartao_em_tres_faixas.py` (11 testes).

**Medido:** suíte de **1.282/11 para 1.293/11** (zero falhas; os 11 novos são do arquivo novo),
guardas do cartão e do estilo em **291 passam**, e `GET /` (tela vazia) continua com **30.781 bytes**
e `sha256 c4a34f7b…` — o `SHA_DA_TELA` não precisou de edição. Os contrastes dos elementos novos vão
de 5,56:1 a 10,87:1 no claro e de 6,03:1 a 12,14:1 no escuro; a barra é decoração e não usa cor de
veredito, aviso ou ação.

**Vinte ações:** as 19 de código e esta, a `T020`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | `#3` (Componentes e estrutura de pacotes) | `regra-alterada` | O template da tela ganha o agrupamento do `h5` do cartão em três faixas, e a folha servida por `GET /app.css` ganha um bloco escopado em `.cartao-do-resultado` (casco, barra, faixas, pílula, indicador, hover e telefone). Nenhum componente, container, rota ou dependência nova |
| `_reversa_sdd/domain.md` | `#5` (Contrato de Mensagens ao Usuário) | `presença` | Nenhum literal mudou: título, nome, cM, vereditos, "Voltar" e o texto escondido continuam ao caractere (`W005` da 006) |
| `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md` | "O que mudou" e "Nada sai do documento" | `presença` | A árvore do cartão continua a mesma, o `card-header` continua embrulhado pelo `summary`, o cartão nasce fechado e o `id` fica no `details`. O recolhimento segue visual |
| `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md` | (a segunda linha do cabeçalho) | `presença` | `cabecalho-sinais` e `rotulo-parentesco` continuam no cabeçalho; os sinais agora ocupam a **terceira faixa** do arranjo novo |
| `_reversa_sdd/addenda/020-bloco-dos-descartados-recolhivel.md` e `022-bloco-de-observacoes-recolhivel.md` | (aparência de apêndice e de aviso) | `presença` | Os dois blocos irmãos usam a mesma forma de `summary`, mas **não** recebem a barra, o raio nem a sombra: continuam com o losango e a superfície antiga (`RN-07`) |
| `_reversa_sdd/addenda/026-polimento-visual-da-tela.md` | "Regras sob vigilância" (`--st-*`) | `presença` | Os quatro tokens de estado e o cinza do `INCONCLUSIVO` não foram tocados; o selo de cM continua em `bg-secondary` (4,69:1) |
| `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md` | (gramática visual do topo) | `presença` | O topo continua com a escala e os alertas da 027; a mudança desta feature é só do cartão de resultado |
| `_reversa_sdd/screens/golden/manifest.yaml` | as 8 entradas literais | `presença` | `GET /` continua byte a byte (`sha256 c4a34f7b…`, 30.781 bytes) e as 8 telas literais mantêm diff textual zero. O cartão de resultado não é uma das telas vazias |
| `_reversa_sdd/design-system/tokens-derived.md` | "Cores" | `presença` | ⚠️ O arquivo derivado de 2026-09-28 continua sem descrever a paleta atual e não ganhou os elementos novos do cartão; é dívida documental declarada, não delta desta entrega |

**Contagem por tipo:** `regra-alterada` 1 · `presença` 8 — **9 impactos**.

Nenhuma regra de `_reversa_sdd/domain.md` foi criada, alterada ou removida. Não há `delta-de-dados`
(nenhum campo, tabela, payload ou migração) nem `delta-de-contrato-externo` (as rotas e o `/app.css`
mantêm método, `Content-Type`, `ETag`, `304` e `404`).

## Regras sob vigilância

`W001` a `W008`, definidos em
`_reversa_forward/036-refino-do-cartao-de-resultado/regression-watch.md`, mais as observações
`OBS-01` a `OBS-04` do mesmo arquivo.

| Item | Cobre |
|------|-------|
| `W001` | As três faixas na ordem e o título em 1,4 rem |
| `W002` | Nenhum `div` dentro do `card-header` |
| `W003` | O link do "Voltar" intacto, sem ícone em markup |
| `W004` | Regras escopadas; blocos irmãos intocados |
| `W005` | O hover do cabeçalho continua sem sublinhado |
| `W006` | `SHA_DA_TELA` inalterado |
| `W007` | Selos e cores de estado inalterados |
| `W008` | As regras genéricas de `summary` e as duas rotações do losango |

## Fontes

- `_reversa_forward/036-refino-do-cartao-de-resultado/requirements.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/roadmap.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/actions.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/legacy-impact.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/regression-watch.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/progress.jsonl` (19 linhas de ação)
- `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/RELATORIO.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/cartao.md`
- `_reversa_forward/036-refino-do-cartao-de-resultado/evidence/depois/hash.txt`
- `_reversa_sdd/addenda/018-cartao-de-resultado-recolhivel.md`
- `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md`
- `_reversa_sdd/addenda/020-bloco-dos-descartados-recolhivel.md`
- `_reversa_sdd/addenda/026-polimento-visual-da-tela.md`
- `_reversa_sdd/addenda/027-harmonizar-topo-da-tela.md`
