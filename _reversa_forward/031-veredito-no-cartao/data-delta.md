# Data Delta: veredito de validação no cartão

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Modelo extraído de referência: `_reversa_sdd/data-dictionary.md` §8 (payload do núcleo → tela) e
> `_reversa_sdd/erd-complete.md` (42 estruturas, 6 tabelas).

## 1. Resumo

**Nenhuma estrutura persistente nova, nenhuma coluna, nenhuma migração.** As quatro chaves do
veredito vivem no dicionário em memória que o template já consome, e morrem com a requisição.

O que muda, em três linhas:

1. **Quatro chaves novas** em cada item de `resultados`.
2. **Dois pares de variáveis CSS** (claro e escuro) e duas classes de selo.
3. **O HTML de `GET /`** — e, com ele, o `SHA_DA_TELA`.

## 2. Chaves novas no dicionário de resultado

| Chave | Tipo | Conteúdo | Quando é `None` |
|-------|------|----------|-----------------|
| `validacao_status` | `str \| None` | `VALIDADO`, `INCONCLUSIVO` ou `ERRO CRONICO / QUEBRA DE LINHA` | Sem veredito |
| `validacao_rotulo` | `str \| None` | `Validado` ou `Linha em conflito` | `INCONCLUSIVO` ou sem veredito |
| `validacao_classe` | `str \| None` | `validacao-valido` ou `validacao-conflito` | `INCONCLUSIVO` ou sem veredito |
| `validacao_aviso` | `str \| None` | Motivo + primeiro código crítico | `INCONCLUSIVO` ou sem veredito |

> **Por que `INCONCLUSIVO` tem `status` e não tem rótulo:** o status é dado de domínio e continua
> disponível para quem quiser filtrar no futuro; o rótulo é vocabulário de tela, e a tela decidiu não
> mostrar (D-05 do `roadmap.md`).

## 3. Mapeamento (fonte única)

| `status` | `rotulo` | `classe` | Selo? |
|----------|----------|----------|-------|
| `VALIDADO` | `Validado` | `validacao-valido` | sim |
| `ERRO CRONICO / QUEBRA DE LINHA` | `Linha em conflito` | `validacao-conflito` | sim |
| `INCONCLUSIVO` | `None` | `None` | não |
| `None` | `None` | `None` | não |

O mapeamento mora em Python (`core/dna_analysis`), como o `confrontacao_rotulo` já mora: o template
não decide regra (RF-12).

## 4. Contrato de tela

O HTML de `GET /` muda em três pontos:

| Ponto | Antes | Depois |
|-------|-------|--------|
| Cabeçalho do cartão | selos de cM, confronto, identidade e sinais | mais o selo de validação, quando há rótulo |
| Topo da lista de resultados | sem explicação | uma linha: os dois selos e "sem selo = não concluído" |
| Folha de estilo | `--st-*` e quatro classes `estado-*` | mais `--validacao-*` nos dois temas e duas classes `validacao-*` |

O texto do selo vai no `visually-hidden` completo ("veredito de validação: linha em conflito"), e o
`title` carrega o motivo e o código.

## 5. Folha de estilo

| Variável | Claro | Escuro | Uso |
|----------|-------|--------|-----|
| `--validacao-valido` | `#2F6B3A` | `#8DBB6E` | borda e ícone do selo validado |
| `--validacao-conflito` | `#A8321F` | `#EE9A88` | borda e ícone do selo em conflito |

| Classe | Regra |
|--------|-------|
| `.badge.validacao-valido` | `background:transparent; border:1px solid var(--validacao-valido); color:var(--ink)` |
| `.badge.validacao-conflito` | `background:transparent; border:1px solid var(--validacao-conflito); color:var(--ink)` |

Contraste medido em 2026-10-18: 5,66:1 e 5,92:1 no claro; 8,30:1 e 8,42:1 no escuro (detalhe em
`investigation.md#4-contraste-calculado`).

> **A classe não contém `estado-`.** A regra `.badge[class*="estado-"]` pinta o texto de branco e
> tornaria o contorno ilegível — é a lição do 1,11:1, registrada em `app.css:311-324`.

## 6. Impacto no ERD e no banco

| Item | Impacto |
|------|---------|
| Tabelas novas | nenhuma |
| Colunas novas | nenhuma |
| Migração | nenhuma |
| Escrita no banco | nenhuma |
| `ConexaoDaAnalise` (payload de persistência) | **não** ganha os campos: o veredito é derivável da árvore |
| Estruturas do ERD | continuam 42 |

## 7. Compatibilidade e migração

n/a para dado. A única migração é do **invariante**: `SHA_DA_TELA` é recalculado dentro da entrega,
com data e motivo no comentário, e o teste continua prendendo a tela contra mudança não declarada.

## 8. O que **não** muda

- `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e `INCONCLUSIVO` — texto, classe e cor.
- O diagrama Mermaid, a busca de caminho, a lista de arquivos e o histórico de análises.
- `src/app.py`, `requirements.txt`, `init.sql`, `docker/*` e as tabelas do banco.
