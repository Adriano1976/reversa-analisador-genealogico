# Legacy Impact: paginação dos Resultados das Análises de Conexão

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Âncora: **legado** (`_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)
> Política de edição do legado no momento da execução: **`allowLegacyEdits: true`**, com
> `allowedPaths` liberando `src/**` e `tests/**` entre outros. Todos os arquivos tocados casam com
> a lista; nenhuma recusa foi necessária.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | Apresentação (camada de tela) | `contrato-alterado` | **MEDIUM** | O documento da análise ganha um `nav` de paginação e o script ganha o motor; os cartões deixam de ser todos visíveis ao mesmo tempo |
| `src/assets/app.css` | Apresentação (folha servida por rota) | `contrato-alterado` | LOW | Sete classes novas e a guarda `[hidden]`; nenhuma regra existente foi removida |
| `tests/test_paginacao_na_tela.py` | Instrumentação de tela | `componente-novo` | LOW | 30 testes: marcação, folha, ligação do script e "nada sai do documento" |
| `tests/fixtures/sample_dna.py` | Instrumentação de tela | `contrato-alterado` | LOW | Duas fixtures novas (68 e 8 cartões), produzidas por kits distintos da mesma pessoa |
| `tests/test_icone_de_atalho.py` | Instrumentação de tela | `contrato-alterado` | LOW | `SHA_DA_TELA` movido de forma **declarada**: 42.290 → 46.264 bytes |

**Nada fora destes cinco arquivos foi tocado.** `src/app.py`, `src/application/`, `src/core/` e
`src/ports/` continuam idênticos — conferido por `git status` ao fim da execução.

## 2. Diff conceitual por componente

### Apresentação, `src/templates/index.html`

O bloco nasce entre o parágrafo de contagem e o primeiro cartão, dentro da guarda
`{% if dna_results %}` e sob uma segunda guarda, `total_de_paginas > 1`. A marcação traz o seletor de
tamanho com as três opções, a posição ("Página 1 de N"), os dois botões de passo e os números das
páginas, calculados pelo Jinja para o tamanho padrão.

O script ganhou o motor: o estado da página em duas variáveis de closure, o cálculo do total, a
fatia visível, o desenho (marcar e desmarcar `hidden`, atualizar texto, `aria-current` e `disabled`)
e quatro ouvintes — seletor, números, anterior e próxima. **Nada é re-renderizado:** o cartão que sai
de vista continua no documento, aberto se estava aberto, com o diagrama já desenhado.

Duas mudanças de ordem merecem registro, porque nenhum teste de estrutura as pegaria:

1. `abrirCartaoDoAlvo()` deixou de ser chamado logo depois da definição e passou a ser chamado **depois**
   do bloco da paginação. Antes disso, `mostrarPaginaDo` ainda é `null`, e o cartão do `#` abriria sem
   a página trocar.
2. Dentro de `abrirCartaoDoAlvo`, a revelação da página vem **antes** de `alvo.open = true`: aberto o
   cartão escondido, o `toggle` dispara e o Mermaid mede um container de tamanho zero.

Os dois botões de expandir/recolher passaram a consumir `cartoesDaPagina()`, que devolve **todos** os
cartões quando não há controle — é o que mantém o comportamento antigo em análise de uma página só.

### Apresentação, `src/assets/app.css`

Sete classes (`paginacao-das-conexoes`, `rotulo-do-tamanho`, `seletor-do-tamanho`,
`posicao-da-pagina`, `botao-de-pagina`, `numeros-das-paginas`, `numero-de-pagina`), o estado
`:disabled` dos botões de passo e a regra que sustenta tudo:

```css
details.cartao-do-resultado[hidden]{display:none !important}
```

O `!important` não é descuido: `hidden` é o atributo mais frágil da plataforma, e qualquer `display`
de biblioteca o vence. A página corrente é pintada pelo **atributo** (`[aria-current="page"]`), e
não por uma classe — assim a cor e o anúncio do leitor de tela não podem divergir.

### Instrumentação, `tests/`

`tests/test_paginacao_na_tela.py` é o arquivo novo. Ele mede **marcação renderizada e ligação de
script**, pelos mesmos limites do adendo `018`: não executa JavaScript, não prova o clique. As duas
fixtures novas usam kits distintos da mesma pessoa do GEDCOM sintético — a forma mais barata de
variar o número de cartões sem inventar pessoas.

`tests/test_icone_de_atalho.py` teve o `SHA_DA_TELA` movido com o valor **medido**, e a medição está
documentada no comentário do arquivo, na mesma série das cinco anteriores. `TAMANHO_ESPERADO`
**não** mudou: ele mede o PNG do ícone, e a arte não foi tocada.

## 3. Preservadas

Regras 🟢 que continuam verdadeiras depois da mudança:

| Regra | Onde vive | Por que continua valendo |
|---|---|---|
| `BR-D-41` — ordem documental primeiro, cM decrescente depois | `_reversa_sdd/domain.md#3.9` | Paginar é uma janela sobre a ordem; nada é reordenado |
| `BR-D-42` — mensagem final `"N conexões encontradas. M descartadas."` | `_reversa_sdd/analise-dna/requirements.md` | A mensagem não foi tocada |
| `BR-D-74` — `ordinal` é a posição na **lista inteira** | `_reversa_sdd/analise-dna/requirements.md` | A página não redefine a ordem; a armadilha está registrada em `data-delta.md` |
| Os quatro estados do confronto e suas regras | `BR-D-27`..`BR-D-34` | Nenhum cálculo foi tocado |
| "Nada sai do documento" | `_reversa_sdd/addenda/018-…md` | Os 68 cartões continuam no HTML; nenhum é removido |
| "Voltar" aponta para `#resultados` | `_reversa_sdd/addenda/019-…md` | O par continua preso pelo mesmo teste |
| Numeração `resultado-N` sem buraco, `id` no `details` | `tests/test_estado_do_resultado.py` | Continua passando sem alteração de asserção |

## 4. Modificadas

| Regra | Onde vivia | O que mudou |
|---|---|---|
| Alcance de "Expandir todas"/"Recolher todas" | `_reversa_sdd/addenda/018-…md` | Agiam nos 68; passam a agir nos cartões da página corrente (decisão de 2026-10-22) |
| Visibilidade do documento de resultado | `_reversa_sdd/addenda/018-…md` | O documento nasce com tudo visível (inalterado); o **script** esconde o que não é da página |
| O que o `SHA_DA_TELA` mede | `tests/test_icone_de_atalho.py` | O valor mudou: 42.290 → 46.264 bytes, +3.974 de script. A declaração está no comentário do arquivo e vai para o adendo |

## 5. O que NÃO mudou, e poderia ter mudado

- **A resposta HTTP.** O `POST /` com `action=dna_analysis` tem o mesmo request, o mesmo status e os
  mesmos erros; só o corpo HTML ganhou o bloco. Nenhum campo novo no formulário — o tamanho da
  página não viaja para o servidor.
- **O modelo de dados.** Nenhuma estrutura, campo, índice ou migração. Ver `data-delta.md`.
- **O custo da análise.** A paginação não acrescenta trabalho ao servidor: ela age depois que o HTML
  já chegou.
