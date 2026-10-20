# Delta de dados: humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Modelo extraído: `_reversa_sdd/data-dictionary.md`, `_reversa_sdd/erd-complete.md`

## 1. Resumo

**Nenhuma migração de schema.** O banco continua com as mesmas tabelas e colunas. O que muda é o
**conteúdo** de uma coluna já existente (`skipped_match.reason`, texto livre) e o formato do
dicionário que a análise carrega em memória até a tela.

## 2. Persistência — sem mudança

| Tabela | Coluna | Antes | Depois | Migração |
|--------|--------|-------|--------|----------|
| `skipped_match` | `reason` | texto técnico ou descritivo, livre | texto humano da causa (`Motivo.texto`) | nenhuma |

O código da causa e o detalhe técnico **não são persistidos**. Motivo: a `RN-28` fala do dado que
alimenta tela e planilha; gravar a causa no histórico exigiria coluna nova e migração por causa de
redação, e o histórico deve registrar o que o sistema dizia no dia em que gravou.

Linhas já gravadas mantêm o texto antigo. Não há backfill: reescrever o passado falsificaria o
registro do que o operador viu.

## 3. Payload em memória — campos novos

O dicionário de um descarte atravessa `core/dna_analysis.py` → `templates/index.html` e
`reporting/csv_de_descartes.py`. Ganha dois campos:

| Campo | Tipo | Exemplo | Vai para |
|-------|------|---------|----------|
| `motivo` | `str` | `"o nome tem uma parte a mais que não aparece na árvore"` | coluna Motivo (tela e planilha), histórico da promoção |
| `motivo_codigo` | `str` | `"nome_do_meio_ausente"` | payload; usado por teste e por quem for filtrar no futuro |
| `motivo_detalhe` | `str` | `"prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · grafia do sobrenome 0,50"` | coluna `Detalhe técnico` da planilha |

`motivo_codigo` e `motivo_detalhe` nascem vazios/`"nao_encontrado"` quando o motivo não vem do
motor (o caso `reason is None`, que vira `"não encontrado"`).

## 4. Catálogo de códigos

| Código | Quando |
|--------|--------|
| `nome_do_meio_ausente` | todos os portões de nota passaram e o veto do token do meio recusou |
| `sobrenomes_em_comum_insuficientes` | sobrenomes em comum abaixo do exigido (`inter < exigida`) |
| `sobrenome_pouco_parecido` | grafia do sobrenome abaixo do limiar adaptativo (`jacc`) |
| `prenome_diferente` | semelhança de prenome abaixo de 85 |
| `semelhanca_insuficiente` | nenhuma das anteriores: a nota final ficou abaixo do mínimo |
| `sem_sobrenome_comum` | interseção zero e sem acerto de sufixo (`filtro anti-falso-positivo`, agora sem o parêntese) |
| `sobrenome_lido_como_prenome` | causa do adendo `024` |
| `nome_unico` | causa do adendo `024` |
| `sobrenome_curto` | causa do adendo `024` |
| `sem_sobrenome_no_gedcom` | causa do adendo `024` |
| `nao_encontrado` | o motor não produziu motivo |

## 5. Contrato da planilha

Nove colunas; as oito primeiras não mudam de nome nem de posição.

| # | Coluna |
|---|--------|
| 1 | Nome no CSV |
| 2 | Kit |
| 3 | cM |
| 4 | Motivo |
| 5 | Candidato na árvore |
| 6 | Nascimento |
| 7 | Prenome |
| 8 | Nota |
| 9 | **Detalhe técnico** *(nova, ao fim)* |

## 6. Índices e consultas

Nenhum índice, consulta ou adaptador é tocado. `ports/adaptadores.py` continua gravando
`descartado.reason`; os dois campos novos da dataclass têm default e são ignorados pela escrita.

## 7. Compatibilidade com dados existentes

- Histórico de análises antigas: intocado, com o texto antigo.
- Análises novas: texto humano + detalhe técnico na planilha.
- Nenhum consumidor lê o motivo por conteúdo. Varredura em `src/`: o único ponto que toca o texto
  fora da exibição é `src/app.py:675` (`valor.split("|", 2)`), que trata o motivo como **opaco** e
  o carrega inteiro no terceiro campo; `src/core/dna_analysis.py:876` apenas o repete numa
  observação. Os testes que usavam `startswith` sobre o motivo (`test_dna_analysis.py`) são
  atualizados por esta feature.
