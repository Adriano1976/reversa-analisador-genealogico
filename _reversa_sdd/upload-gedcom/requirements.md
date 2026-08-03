# Upload e Parsing de GEDCOM

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Endpoint que recebe um arquivo GEDCOM (.ged) enviado pelo usuário, salva-o em `uploads/`, faz o parsing da árvore genealógica e expõe a lista de nomes para uso nas demais análises. O grafo de famílias fica em memória para a sessão.

## Responsabilidades
- Salvar o arquivo `.ged` enviado na pasta `uploads/`.
- Parsear registros `INDI` (pessoas) e `FAM` (famílias) via `ged4py`.
- Construir o grafo NetworkX bidirecional de pessoas ↔ famílias.
- Exibir lista ordenada de nomes formatados para seleção posterior.

## Regras de Negócio
- O upload exige o campo de arquivo com nome `gedcom`. 🟢
- Sem arquivo → erro "Nenhum arquivo GEDCOM enviado." 🟢
- Arquivo sem nome (`filename == ''`) → erro "Nenhum arquivo selecionado." 🟢
- Qualquer exceção no parsing → mensagem de erro com detalhe. 🟢
- Pessoas sem nome são listadas como "Sem Nome". 🟢
- Nomes são ordenados alfabeticamente. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Salvar GEDCOM enviado em `uploads/` com o nome original | Must | Arquivo presente no disco e mensagem de sucesso |
| RF-02 | Parsear INDI e FAM e construir grafo bidirecional | Must | Grafo populado; dicionários `people`/`families` preenchidos |
| RF-03 | Listar nomes ordenados para o front-end | Must | Lista retornada em ordem alfabética |
| RF-04 | Validar presença e nome do arquivo | Must | Erros retornados sem crash |
| RF-05 | Responder erros de parsing de forma amigável | Must | Mensagem de exceção exibida na UI |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | `secret_key` hardcoded e exposta no código-fonte | `app.py:13` | 🟡 |
| Segurança | Sem validação de extensão/tamanho do arquivo enviado | `app.py:563-571` | 🔴 |
| Performance | Re-parse do GEDCOM a cada requisição POST | `app.py:582` | 🟢 |
| Disponibilidade | Sem tratamento de concorrência no estado global | `app.py:20-23` | 🔴 |

## Critérios de Aceitação

```gherkin
Dado um GEDCOM válido (ex.: "familia.ged")
Quando o usuário envia o arquivo no campo "gedcom"
Então o arquivo é salvo em uploads/, o grafo é construído e a lista de nomes é exibida

Dado que nenhum arquivo foi enviado
Quando o usuário submete o formulário sem o campo "gedcom"
Então a mensagem "Nenhum arquivo GEDCOM enviado." é exibida

Dado um arquivo GEDCOM malformado
Quando o sistema tenta fazer o parsing
Então uma mensagem de erro com a exceção é exibida sem quebrar a aplicação
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Salvar e parsear GEDCOM (RF-01, RF-02) | Must | Caminho crítico de todas as análises |
| Validações de entrada (RF-04) | Must | Comportamento esperado sem crash |
| Tratamento de erro amigável (RF-05) | Should | Melhora UX, sem impacto no núcleo |
| Validação de extensão/tamanho | Could | Não implementado no legado 🔴 |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` (bloco `upload_gedcom`) | 🟢 |
| `analisador-genealogico/app.py` | `load_gedcom_and_build_graph()` | 🟢 |
| `analisador-genealogico/app.py` | `build_graph_from_parser()` | 🟢 |
| `analisador-genealogico/app.py` | `get_name()` | 🟢 |
