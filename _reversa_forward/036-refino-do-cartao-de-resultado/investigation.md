# Investigation: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Requirements: `_reversa_forward/036-refino-do-cartao-de-resultado/requirements.md`

## 1. O material de referência

O operador mandou duas capturas (antes/depois) e um mockup navegável em
`D:\dados-genealogicos\index.html` — **fora do repositório** (10.881 bytes, 417 linhas). O mockup é uma
página isolada, com paleta, fontes e scripts próprios:

- `Cormorant Garamond` no título e `Manrope` no corpo;
- `.connection-card` em `grid-template-columns: 1fr auto`, com `::before` de 5 px (degradê
  `#bda980 → #8a7759`), `::after` de brilho radial, raio de 18 px e sombra `0 8px 24px`;
- título em `clamp(1.5rem, 2vw, 2rem)`, selos em `.tag` com `min-height:32px` e raio de 10 px;
- "Voltar" em pílula com chevron, e um botão de expandir em caixa de 38 px;
- `details` com `grid-template-rows: 0fr → 1fr` e `IntersectionObserver` de entrada (`fadeUp`).

**O que a feature adota:** as três faixas, a barra lateral, a pílula com chevron, a caixa do indicador e
a superfície em degradê.

**O que a feature recusa, e por quê:**

| Do mockup | Decisão | Motivo |
|-----------|---------|--------|
| Fontes `Cormorant`/`Manrope` | não entram | O projeto já carrega `Newsreader` e `IBM Plex Sans` (`index.html:108`); fonte nova é requisição nova |
| Animação de entrada | não entra | `RN-10` (opção 3a): 142 cartões, custo sem ganho; `prefers-reduced-motion` já existe |
| Azul do "Voltar" (`#5b6f8f`) | não entra | Fora da paleta; a ação da tela é `--primary` (verde), com 5,70:1 no claro e 7,67:1 no escuro |
| Cores literais (`#bda980`, `#8a7759`, `#f3efe6`) | não entram | `RN-03`/`RN-04`: cor por token, e token neutro para decoração |
| `<button>` no "Voltar" | não entra | O link é `<a href="#resultados">` e tem contrato de teste (`test_estado_do_resultado.py:220-234`) |
| `details`/`toggle` próprios | não entram | O cartão já é `details` e o `summary` já é o gatilho (`adendo 018`) |

## 2. Restrições descobertas no código e nos testes

| Restrição | Onde | Consequência para o desenho |
|-----------|------|-----------------------------|
| O cabeçalho é extraído até o **primeiro `</div>`** | `tests/test_cartoes_recolhiveis.py:181`; `tests/test_estado_do_resultado.py:139` | As faixas novas usam `span`; **nenhum `div`** dentro do `card-header` |
| `voltar-ao-indice`, `cabecalho-sinais` e `rotulo-parentesco` têm de continuar dentro do cabeçalho | `test_cartoes_recolhiveis.py:246,280-284` | O link e os sinais não podem sair do `h5` |
| O link do retorno exige texto puro antes do `visually-hidden` | `test_estado_do_resultado.py:222-229` | Nada de ícone em markup; o chevron é `::before` de CSS |
| Literais de regra da folha e as duas rotações | `test_cartoes_recolhiveis.py:432-446` | As regras genéricas de `details.card > summary…` ficam intactas; o refino é escopado |
| O contraste dos selos é resolvido pela cascata, com branco fixo em `.badge[class*="estado-"]` | `test_estilo_da_tela.py:478-504` | Nenhuma cor de selo muda; nada de `background` em degradê no selo (o resolvedor não lê gradiente) |
| `details.card{overflow:hidden}` | `app.css:100` | O raio novo já recorta a barra lateral e o conteúdo |
| `details>summary:hover` sublinha todo `summary` | `app.css:242` | Precisa de override escopado (0,2,1 vence 0,1,2) |
| O `::after` do summary é item de `flex` | `app.css:101-109` | Para virar caixa com chevron por cima, o escopo do cartão torna os dois pseudos absolutos |
| `SHA_DA_TELA` mede a tela **vazia** | `tests/test_icone_de_atalho.py:140` | A mudança vive sob `{% if dna_results %}` (`index.html:478`); o hash não deve mover |
| O Bootstrap define `padding` e fundo do `.card-header` | `bootstrap 5.3.3` | O seletor escopado `.cartao-do-resultado .card-header` (0,2,0) vence sem `!important` |

## 3. Alternativas avaliadas

| Tema | Opções | Escolha | Razão |
|------|--------|---------|-------|
| Arranjo das faixas | `grid` com `grid-row:1/-1`; `flex`; `float` mantido | `flex` no `h5` | Centra a ação nas três faixas sem depender de linhas explícitas; `float` não centraliza |
| Caixa do indicador | `::before` + `::after` absolutos; SVG em `background-image`; `box-shadow` no losango | `::before` + `::after` | Mantém `transform:rotate(45deg/-135deg)` literal, exigido por teste; SVG perderia o giro |
| Cor da barra | `--aviso-line`; `--primary`; `--muted → --head`; literal do mockup | `--muted → --head` | Neutro (não diz aviso nem ação), existe nos dois temas, mede 6,11→10,87:1 e 6,48→12,14:1 |
| Superfície | `--surface` plano; `--surface-2`; degradê `--surface → --surface-2` | degradê | Dá o painel do mockup sem sair da paleta; no escuro o degradê separa sem sombra |
| Escopo | genérico em `summary.sumario-do-cartao`; `.cartao-do-resultado` | `.cartao-do-resultado` | `RN-07`: os blocos irmãos não podem mudar |
| Sublinhado | remover a regra global; `!important`; override escopado | override escopado | Não muda os outros `summary` da tela |

## 4. Medições de contraste dos elementos novos

Fórmula WCAG 2.1 (luminância relativa). Superfície de referência: `--surface` (topo do degradê).

| Par | Claro | Escuro |
|-----|-------|--------|
| Título `--head` sobre `--surface` | 10,87:1 | 12,14:1 |
| Sinais `--muted` sobre `--surface` | 6,11:1 | 6,48:1 |
| "Voltar" `--primary` sobre `--surface` | 6,26:1 | 7,67:1 |
| Chevron `--muted` sobre `--surface` | 6,11:1 | 6,48:1 |
| Barra `--muted → --head` | 6,11 → 10,87:1 | 6,48 → 12,14:1 |
| Borda da caixa `--line` (decorativa) | 1,47:1 | 1,38:1 |
| Selo de cM `bg-secondary` + branco (não muda) | 4,69:1 | 4,69:1 |

Todo texto fica acima de 4,5:1; os elementos não textuais que carregam significado (chevron e barra)
ficam acima de 3:1. A borda da caixa é decoração — o chevron é a pista.

## 5. Arquivos lidos nesta sessão

- `src/templates/index.html` (masthead, abas, formulários, cartão de resultado, bloco dos descartados)
- `src/assets/app.css` (tokens, cartão, summary, selos, avisos, media queries)
- `tests/test_cartoes_recolhiveis.py`, `tests/test_estado_do_resultado.py`,
  `tests/test_estilo_da_tela.py`, `tests/test_validacao_no_cartao.py`,
  `tests/test_contador_em_tres_faixas.py`, `tests/test_icone_de_atalho.py`
- `_reversa_sdd/addenda/018`, `019`, `020`, `026`, `027`, `031`
- `_reversa_sdd/architecture.md#3`, `_reversa_sdd/domain.md#5`
- `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` (`RF-17`) e `regression-watch.md` (`W005`)
- `.reversa/principles.md`, `.reversa/templates/roadmap-template.md`
- `D:\dados-genealogicos\index.html` (mockup, fora do repositório)

## 6. Resíduos

- A conferência visual renderizada (sombra, barra, alinhamento fino) depende de humano; os testes
  provam estrutura, classe e contraste resolvido pela cascata.
- O mockup tem nome de pessoa e cM; nada disso é transcrito para artefato (princípio I).
