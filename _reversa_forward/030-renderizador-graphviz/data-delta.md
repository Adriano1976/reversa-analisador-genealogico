# Data Delta: renderizador Graphviz

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Modelo extraído de referência: `_reversa_sdd/erd-complete.md` (42 estruturas, 6 tabelas) e
> `_reversa_sdd/data-dictionary.md` §8 (payload do núcleo → tela).

## 1. Resumo

**Nenhuma estrutura persistente nova, nenhuma coluna, nenhuma migração.** O renderizador recebe três
dicionários que já existem, produz uma string (o DOT) e, quando o Graphviz está disponível, escreve
**um arquivo de imagem no caminho que o chamador informar**.

O que muda, em duas linhas:

1. **Entra uma dependência de runtime** (`graphviz`, pinada) e uma **de sistema** (`dot`, documentada).
2. **Sai um artefato efêmero** (`.png`/`.svg`), que não é versionado e não é servido pela aplicação.

## 2. Entradas

| Entrada | Tipo | Origem | Já existe? |
|---------|------|--------|------------|
| `sugestao` | `dict` | `core.cirurgia_do_grafo.arvore_sugerida` (feature 029) | sim — só é lida |
| `resultado` | `dict` | `core.validator.validar_comparacao` (feature 028) | sim — traz `cm`, `mrca_estimado`, `codigos`, `status` |
| `documental` | `dict` | `core.documentary_relationship.documentary_relationship` | sim — traz `path.ids`, `common_ancestor`, `person_b` |
| `destino` | `str` | quem chama | — |
| `formato` | `str \| None` | quem chama; padrão derivado da extensão | — |

> **Por que `documental` é necessário:** o contrato da `029` não carrega o caminho nem a pessoa do
> match. Sem ele, o recorte da RN-06 não existe. A emenda está registrada no `requirements.md` §11.

## 3. Saída

| Item | Tipo | Observação |
|------|------|------------|
| Texto DOT | `str` | Determinístico, com `digraph`, nós, arestas e a caixa de evidência |
| Arquivo de imagem | `str` (caminho) | `renderizar_arvore_sugerida` devolve o caminho gravado |
| Erro | `ErroDeRenderizacao` | Exceção do próprio `reporting`, com atributo `codigo` |

## 4. Classes de nó no DOT

| Classe | `shape` | `style` | `fillcolor` | `color` | Rótulo |
|--------|---------|---------|-------------|---------|--------|
| Base | `box` | `filled,rounded` | `#a8e6cf` | `#4a7c68` | nome da pessoa |
| Documental | `box` | `filled,rounded` | `#f5f5f5` | `#666666` | nome da pessoa |
| Virtual | `box` | `filled,dashed` | `#ffd3b6` | `#a8724a` | `Geração k` |
| Evidência | `note` | `filled` | `#ffffff` | `#333333` | texto da caixa |

`fontcolor` é `#333333` em todas as classes, para o texto não depender do tema do Graphviz.

## 5. Classes de aresta

| Classe | `style` | `color` | `label` | Quando |
|--------|---------|---------|---------|--------|
| Filiação | `solid` | `#555555` | — | Trechos datados do caminho |
| Cadeia sugerida | `solid` | `#a8724a` | — | Ancestral → `Geração 1` → … → filho |
| Rompida | `dashed` | `red` | `DESVIO DE CONEXÃO / QUEBRA DE LINHA` | Cada junção: `pai_id` → `filho_id` |
| Evidência | `invis` | — | — | Caixa → doador |

## 6. Atributos do grafo

| Atributo | Valor | Por quê |
|----------|-------|---------|
| `rankdir` | `TB` | Hierarquia de cima para baixo, como pedido |
| `labelloc` | `t` | Título no topo |
| `label` | `Árvore sugerida — <nome do doador>` | Identifica a imagem fora de contexto |
| `fontname` | `Helvetica` | Fonte disponível em Windows e Linux; evita depender de fonte instalada |
| `bgcolor` | `white` | PNG previsível, sem fundo transparente que fica preto em alguns visualizadores |

## 7. Emenda em `requirements.txt`

| Situação | Antes | Depois |
|----------|-------|--------|
| Dependências de runtime | 9 pins | 10 pins, com `graphviz` na versão instalada durante o coding |
| Dependência de sistema | nenhuma | `dot` (Graphviz), documentado e **não** instalável por `pip` |
| Docker | `python:3.14-slim` + `pip install` | **sem mudança**: a renderização é de host |

## 8. Impacto no ERD e no banco

| Item | Impacto |
|------|---------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Migração | nenhuma |
| Escrita no banco | nenhuma |
| Estruturas do ERD | continuam 42; nenhuma é tocada |

O DOT e a imagem são payload efêmero de uma chamada, como `MrcaEstimado` na `028` e `sugestao` na
`029`. Não entram no ERD porque não são domínio persistente.

## 9. Compatibilidade e migração

n/a para dado. A única migração é de **ambiente**: instalar o Graphviz de sistema e o pacote no
`.venv` (passo manual no `onboarding.md`). Sem isso, a feature falha com `DOT_AUSENTE` — e é assim de
propósito.

## 10. O que **não** muda

- `sugestao`, `resultado` e `documental` — lidos, nunca mutados.
- `reporting/mermaid_render.py` — o renderizador de tela continua intocado.
- `src/app.py`, template, CSS, `init.sql`, Docker, `.dockerignore` e as 6 tabelas.
- Os quatro estados do confronto e os três status da validação — o renderizador só **lê** o status.
