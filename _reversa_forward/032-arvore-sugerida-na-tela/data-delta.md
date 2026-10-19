# Data Delta: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Modelo extraído de referência: `_reversa_sdd/data-dictionary.md` §8 (payload do núcleo → tela).

## 1. Resumo

**Nenhuma estrutura persistente nova, nenhuma coluna, nenhuma migração.** Quatro chaves entram no
dicionário em memória que o template já consome, e o HTML do cartão ganha um bloco.

O que muda, em três linhas:

1. **Quatro chaves novas** em cada item de `resultados`.
2. **Um bloco colapsável** no cartão, com resumo e diagrama.
3. **Nada em disco**: nem PNG, nem rota, nem tabela.

## 2. Chaves novas no dicionário de resultado

| Chave | Tipo | Conteúdo | Quando é `None`/vazio |
|-------|------|----------|------------------------|
| `sugestao_geracoes` | `int` | Número de gerações intermediárias (o hiato aplicado) | `0` quando não há o que injetar |
| `sugestao_resumo` | `str \| None` | `"3 gerações sugeridas"` — o texto do `<summary>` | Sem sugestão |
| `sugestao_mermaid` | `str \| None` | O texto Mermaid do caminho corrigido | Sem sugestão |
| `sugestao_aviso` | `str \| None` | A frase de ausência — **só em cartão em conflito** | Cartão sem conflito, ou com sugestão |

> **Por que a frase só existe em conflito:** o núcleo decide (`D-10` do `roadmap.md`). Nos cartões
> validados e inconclusivos a chave é `None`, e o template não tem regra nenhuma para aplicar.

## 3. Mapeamento (fonte única)

| Situação | `geracoes` | `resumo` | `mermaid` | `aviso` |
|----------|-----------:|----------|-----------|---------|
| Conflito, hiato ≥ 1 | N | `"N gerações sugeridas"` | texto | `None` |
| Conflito, hiato ≤ 0 | 0 | `None` | `None` | "as duas medidas concordam" |
| Conflito, sem estimativa | 0 | `None` | `None` | "o cM não permitiu estimar" |
| Validado | 0 | `None` | `None` | `None` |
| Inconclusivo | 0 | `None` | `None` | `None` |

## 4. Contrato de tela

O HTML do cartão muda em um ponto: um `details` novo, **depois** de `details.grafo-do-registro`.

| Aspecto | Decisão |
|---------|---------|
| Tag | `<details class="arvore-sugerida">`, fechado por padrão |
| `<summary>` | O resumo em texto (`3 gerações sugeridas`), com `visually-hidden` completando o sentido |
| Corpo | `<div class="graph-container"><div class="mermaid">{{ sugestao_mermaid | safe }}</div></div>` |
| Sem sugestão | Nenhum `details`; em conflito, um `<p class="sem-sugestao">` com a frase |
| JS | **não muda**: `details` com `.mermaid` já recebe o `toggle` |

## 5. Contrato do Mermaid

| Elemento | Sintaxe |
|----------|---------|
| Abertura | `graph TD` |
| Nó base | `N_I1["Doador Sintetico"]:::base` |
| Nó documental | `N_I2["Pai Sintetico"]:::doc` |
| Nó virtual | `N_V1["Geração 1"]:::virt` |
| Filiação | `N_I1 --> N_I2` |
| Cadeia sugerida | `N_I10 --> N_V1`, `N_V1 --> N_V2`, `N_V2 --> N_I2` |
| Aresta rompida | `N_I10 -.->|"DESVIO DE CONEXÃO / QUEBRA DE LINHA"| N_I2` (emitida por último) |
| `classDef` | `base`: `#a8e6cf` / `#4a7c68`; `doc`: `#f5f5f5` / `#666666`; `virt`: `#ffd3b6` / `#a8724a` |
| `linkStyle` | `linkStyle <último> stroke:red,stroke-width:2px,stroke-dasharray:5 5` |

## 6. Impacto no ERD e no banco

| Item | Impacto |
|------|---------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Migração | nenhuma |
| Escrita no banco | nenhuma |
| Estruturas do ERD | continuam 42 |

## 7. Compatibilidade e migração

n/a. O `SHA_DA_TELA` não muda: o bloco novo vive dentro do cartão, e `GET /` sem resultados não
renderiza cartão nenhum. **A verificação é feita no coding**, e não suposta — a lição da `031`, em
que a suposição anterior estava errada.

## 8. O que **não** muda

- O diagrama documentado (`details.grafo-do-registro`), os quatro estados e o selo da `031`.
- `src/app.py`, `src/assets/app.css`, `requirements.txt`, `init.sql`, `docker/*` e o banco.
- O JavaScript do template.
