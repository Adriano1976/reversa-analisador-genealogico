# Adendo: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `029`, `030` e `031`)

## Vigência

Vigente desde 2026-10-19.

## Resumo da entrega

A cirurgia da `029` e o renderizador da `030` existiam **sem consumidor de tela**: o operador
recebia o veredito `ERRO CRONICO / QUEBRA DE LINHA`, mas não via a árvore sugerida. Esta feature
leva o resultado ao cartão, como um bloco recolhível **dentro do cartão e depois do diagrama
documentado**: título com a contagem (`3 gerações sugeridas`), desenho Mermaid com as gerações
virtuais marcadas (`Geração 1..k`), o ramo base em verde, os nós documentais em cinza e a aresta
rompida em vermelho tracejado — sempre a **última** aresta, porque `linkStyle` indexa por
posição de declaração.

A entrega foi concluída em **14 de 14 ações**, com 26 testes novos — 8 de resumo (núcleo), 10 de
desenho (reporting) e 8 de tela. Suíte: **1198 passam, 11 pulados, 0 falham**.

**Duas decisões de fronteira, e as duas por medição:**

- `resumo_da_sugestao` é **O(1) e não copia o grafo**. `arvore_sugerida` faz `grafo.copy()`
  (O(V+E)); numa análise real de 142 cartões sobre uma árvore de 35.460 pessoas, chamá-la por
  cartão tornaria a requisição inviável.
- A frase de ausência aparece **só em cartão em conflito** (§9 dos requirements): repetir a
  explicação em 142 cartões, a maioria sem conflito, trocaria um silêncio ruidoso por ruído
  constante.

**Achado registrado:** `sugestao_geracoes` chega ao dicionário mesmo sem caminho documental (a
fórmula do hiato não depende do caminho), mas o **bloco** exige `sugestao_resumo` **e**
`sugestao_mermaid`, e o emissor devolve `None` sem `path.ids`. A tela, portanto, nunca promete
sugestão que não pode desenhar — e a contagem da feature `033` usa exatamente essa condição.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `core.cirurgia_do_grafo.resumo_da_sugestao(resultado, documental)` — O(1), sem cópia de grafo |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `reporting.mermaid_render.mermaid_da_sugestao(documental, resumo)`, injetado em `Dependencias.gerar_mermaid_da_sugestao` (ADR-34: `core/` não importa `reporting/`) |
| `_reversa_sdd/data-dictionary.md` | §8 Payload do núcleo → tela | delta-de-dados | Cada item de `resultados` ganha `sugestao_geracoes`, `sugestao_resumo`, `sugestao_mermaid` e `sugestao_aviso` |
| `_reversa_sdd/domain.md` | §Contrato de tela do cartão | regra-nova | Entra o bloco `arvore-sugerida`, com título `N gerações sugeridas` e o aviso de ausência restrito a cartão em conflito |

## Regras sob vigilância

- **W001** — a aresta rompida é a **última** do diagrama; reordenar manda o vermelho tracejado
  para a aresta errada, em silêncio. Fixado em `tests/test_mermaid_da_sugestao.py`.
- **W002** — `resumo_da_sugestao` e `arvore_sugerida` compartilham a fórmula do hiato
  (`floor(geracoes + 0,5) - a_up`); duas casas dariam números diferentes para o cartão e a
  imagem.

## Fontes

- `_reversa_forward/032-arvore-sugerida-na-tela/requirements.md`
- `_reversa_forward/032-arvore-sugerida-na-tela/roadmap.md`
- `_reversa_forward/032-arvore-sugerida-na-tela/actions.md`
- `_reversa_forward/032-arvore-sugerida-na-tela/legacy-impact.md`
- `_reversa_forward/032-arvore-sugerida-na-tela/regression-watch.md`
