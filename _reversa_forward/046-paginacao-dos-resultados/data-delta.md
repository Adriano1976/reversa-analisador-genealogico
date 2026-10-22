# Delta de dados: paginação da lista de resultados

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> Modelo extraído: `_reversa_sdd/erd-complete.md` (42 estruturas) e `_reversa_sdd/data-dictionary.md`

## Veredito

**Nenhuma estrutura, campo, índice, restrição ou migração.** A feature é de apresentação e não toca
o modelo de dados — nem o das 24 estruturas em memória, nem as 6 tabelas do PostgreSQL.

## 1. O que a feature consome, e não altera

| Estrutura | Onde vive | O que a paginação faz com ela | Mudança |
|---|---|---|---|
| Lista de conexões (`dna_results`) | memória, por requisição | **lê** o comprimento para calcular o total de páginas | nenhuma |
| Cartão de conexão (o `result` do laço) | memória, por requisição | **não lê** nada; cada cartão é uma unidade de exibição | nenhuma |
| `match_result.ordinal` | PostgreSQL, tabela `match_result` | **não muda de contrato**: continua sendo a posição na ordem apresentada da **lista inteira** | nenhuma |
| `dna_analysis`, `analysis_person`, `match_kit`, `match_path_node`, `skipped_match` | PostgreSQL | fora do escopo | nenhuma |

## 2. O estado que a feature cria, e onde ele NÃO está

O único dado novo é o par **`(página corrente, tamanho da página)`**. Ele vive:

| Onde | Sobrevive a | Chega ao servidor? | É persistido? |
|---|---|---|---|
| Duas variáveis de closure no `<script>` da tela | troca de página, abertura/fechamento de cartão | não | não |
| — | recarregamento da página | — | morre |

Consequências declaradas:

- **`RN-14`**: como o estado não é persistido, toda análise começa em 10. Não há linha no banco, nem
  `localStorage`, nem cookie.
- **`RN-06`/`RF-14`**: como o estado não viaja, trocar de página não gera `POST` — e por isso não há
  campo novo no formulário nem na assinatura do caso de uso.
- Uma eventual "preferência lembrada" (`Won't` desta feature) teria de morar no **navegador**, não no
  banco: o sistema não tem identidade de operador (`permissions.md`), então não há a quem amarrar a
  preferência no servidor.

## 3. O contrato do `ordinal`, que parece vizinho e não é

`BR-D-74` (`_reversa_sdd/analise-dna/requirements.md`) define `ordinal` como a posição na **ordem
apresentada**, com defaults `INCONCLUSIVO`, `not_found` e string vazia. Com paginação, "ordem
apresentada" continua sendo a lista inteira — a página é uma janela sobre ela, não uma reordenação.

Se alguém, mais tarde, redefinir `ordinal` como "posição na página", o histórico do banco passa a
guardar números que se repetem a cada página, e a reconstrução da análise (que hoje não existe,
`architecture.md#4`) ficaria impossível. Fica registrado aqui porque é a única armadilha de dado
que esta feature cria por vizinhança.

## 4. Migração

| Item | Necessário? | Observação |
|---|---|---|
| Script de migração | não | não há schema |
| Backfill | não | não há coluna nova |
| Compatibilidade de leitura | não | nenhum consumidor lê o que a feature grava — ela não grava |
| Rollback | trivial | reverter o template e a folha devolve o comportamento anterior; nada fica no banco |
