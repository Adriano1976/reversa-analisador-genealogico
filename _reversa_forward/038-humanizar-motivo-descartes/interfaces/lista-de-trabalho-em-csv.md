# Contrato: lista de trabalho dos descartes (CSV)

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Rota: `POST /descartes.csv`
> Formato: arquivo CSV, `text/csv`, `Content-Disposition: attachment`

## 1. Request

| Campo | Tipo | Obrigatório | Conteúdo |
|-------|------|-------------|----------|
| `dados` | JSON em campo de formulário | não | Lista dos descartes como a tela os renderizou |

Corpo inválido, JSON que não seja lista ou campo ausente devolvem a planilha **só com o cabeçalho**,
com `200`. Não há erro HTTP nesse caminho — é o contrato da feature 035, preservado.

## 2. Response

- `200` sempre.
- `Content-Type: text/csv`.
- `Content-Disposition: attachment; filename=...`.
- Corpo: BOM (`\ufeff`) + cabeçalho + uma linha por descarte, terminador `\r\n`, separador `;`.

## 3. Colunas

| # | Coluna | Origem | Observação |
|---|--------|--------|------------|
| 1 | `Nome no CSV` | `csv_name` | Desarmado contra fórmula do Excel (prefixo `'`) |
| 2 | `Kit` | `kit` | vazio quando ausente |
| 3 | `cM` | `cm` | decimal com vírgula, duas casas sem zero à direita |
| 4 | `Motivo` | `motivo` | **agora texto humano** — sem `given`/`final`/`inter`/`jacc` |
| 5 | `Candidato na árvore` | `candidatos[compativel]` | vários separados por ` \| ` |
| 6 | `Nascimento` | idem | |
| 7 | `Prenome` | idem | número com vírgula |
| 8 | `Nota` | idem | número com vírgula |
| 9 | `Detalhe técnico` | `motivo_detalhe` | **nova**; vazia quando a recusa não vem do bloco de semelhança |

## 4. Exemplo

```csv
Nome no CSV;Kit;cM;Motivo;Candidato na árvore;Nascimento;Prenome;Nota;Detalhe técnico
Maria José de Souza Santos;TG0000001;12,3;o nome tem uma parte a mais que não aparece na árvore;Mariza Souza Santos;26 AUG 1970;100;88,25;prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · grafia do sobrenome 0,50
Fulano de Tal;TG2;9,5;não encontrado;;;;;
```

## 5. Regras de compatibilidade

1. As oito primeiras colunas mantêm **nome e posição**; qualquer consumidor que lê por índice
   continua funcionando nas posições 0 a 7.
2. A nona coluna é aditiva. Quem lê por cabeçalho não percebe diferença.
3. O separador do detalhe é `·`, **não** `;`, para não exigir escape à toa.
4. Acento e BOM são obrigatórios: sem eles o Excel em português abre em ANSI e quebra o texto.
5. Idempotência: a mesma lista de descartes produz byte a byte o mesmo arquivo.

## 6. Erros

Não há caminho de erro HTTP. Falha de formatação cai no `_texto`/`_numero`, que devolvem string
vazia — o contrato é "planilha sempre abre".
