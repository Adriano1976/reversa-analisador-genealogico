# Legacy Impact: harmonização visual do topo da tela

> Identificador: `027-harmonizar-topo-da-tela`
> Data: `2026-10-17`
> Âncora: `_reversa_sdd/addenda/011-…`, `013-…`, `018-…`, `023-…` e `026-…`;
> `_reversa_sdd/recursos-da-tela/` e `_reversa_sdd/state-machines.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/assets/app.css` | Folha de estilo da tela (adendo `013`) | `regra-alterada` | **LOW** | Tokens de alerta, regras dos alertas, largura da ação e escala do topo. Nenhuma cor de selo, cartão ou cM muda |
| `src/templates/index.html` | Comentário da masthead (adendo `011`, `RN-24`) | `regra-alterada` (documentação) | **LOW** | O comentário passa a descrever o arranjo centralizado que já existia. Nenhum markup muda; o HTML servido continua byte a byte |

Nenhum outro arquivo de código foi tocado. `tests/` não foi editado (o hash não mudou), e os pacotes
`application/`, `ports/`, `core/`, `parsers/` e `reporting/` estão fora do diff.

## 2. Diff conceitual por componente

### Folha de estilo da tela

**Antes.** O alerta de retorno não tinha regra: herdava o verde padrão do framework, com borda a
1,15:1 contra o fundo — o bloco lia como chapa lisa. A ação principal ocupava a largura inteira do
cartão em qualquer tela. O `h1` chegava a 2,5 rem e a arte a 320 px.

**Depois.** Os alertas usam quatro tokens da paleta, com texto entre 12,16 e 13,70:1 e borda entre
5,57 e 7,47:1, nos dois temas; o X continua o do framework, com opacidade e foco ajustados. A ação
ganha largura natural acima de 576 px e continua total abaixo. O `h1` para em 2,2 rem e a arte em
280 px.

**Efeito observável.** O topo fica mais próximo da gramática dos cartões. Nenhum texto, rota, selo ou
cartão de resultado muda.

### Comentário da masthead

**Antes.** Dizia que os dois parágrafos ficavam "alinhados a esquerda" — descrição do comportamento
anterior à `T045`.

**Depois.** Diz que a masthead e os parágrafos são centralizados, que a `RN-24` pede a coluna estreita
e que o teste prende o arranjo.

**Efeito observável.** Nenhum: é um comentário Jinja, removido do HTML.

## 3. Preservadas

| Regra | Onde vivia | Prova |
|-------|------------|-------|
| A introdução é centralizada e estreita (`RN-24`) | adendo `011`; `tests/test_banner_do_topo.py:270-298` | teste da `RN-24` verde; `text-start` ausente do HTML |
| O `<h1>` é sempre visível (`RN-23`) | adendo `023` | `test_o_titulo_do_produto_esta_sempre_visivel` |
| Os quatro estados e o `status` como classe CSS | `state-machines.md#32` | `test_os_quatro_estados_tem_cor` e `TestOContrasteDosSelos` |
| O selo de cM e as cores dos cartões (`RN-08`) | decisão 3a da sessão de 2026-10-17 | `git diff` não toca `.badge`, `.cartao-*` ou `bg-secondary` |
| As 8 telas literais mantêm diff textual zero (`RF-17` da 006) | `_reversa_forward/006-…/requirements.md` | `SHA_DA_TELA` inalterado; nenhum texto mudou |
| As mensagens da camada de rota continuam ao caractere (`W005` da 006) | `_reversa_forward/006-…/regression-watch.md` | nenhum literal tocado |
| `aria-pressed`, `visually-hidden` e `focus-visible` | `tests/test_estilo_da_tela.py` | guardas verdes |

## 4. Modificadas

| Regra | Tipo | Delta |
|-------|------|-------|
| Apresentação dos alertas de retorno | `regra-alterada` (apresentação) | Saem da cor padrão do framework e entram na paleta, com borda visível |
| Peso da ação principal | `regra-alterada` (apresentação) | Largura natural no desktop; total no telefone |
| Escala do topo | `regra-alterada` (apresentação) | `h1` 2,2 rem; arte 280 px |
| Comentário da masthead | `regra-alterada` (documentação) | Descreve a `RN-24` |

Nenhuma regra de domínio (`_reversa_sdd/domain.md`) foi alterada ou removida. Não há regra com
confidência rebaixada. O `SHA_DA_TELA` permanece `c4a34f7b…` porque o comentário é Jinja e não chega
ao documento.
