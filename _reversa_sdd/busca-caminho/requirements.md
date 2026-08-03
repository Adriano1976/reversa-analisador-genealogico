# Busca de Caminho (Path Search)

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Visão Geral

Endpoint que busca a conexão genealógica entre duas pessoas da árvore GEDCOM. Tenta primeiro a conexão **direta** via ancestral comum (MRCA) e, se não existir, o fallback por **conexão indireta** via afinidade (casamentos/cunhados) usando BFS no grafo pessoa↔família. Renderiza o resultado como caminho textual + diagrama Mermaid.

## Responsabilidades
- Localizar as duas pessoas pelo nome no GEDCOM.
- Buscar conexão direta por ancestral comum (`find_ancestral_path`).
- Em falha, buscar conexão indireta por afinidade (`find_indirect_path`).
- Renderizar caminho textual e diagrama Mermaid adequado ao tipo de conexão.

## Regras de Negócio
- Requer GEDCOM já carregado (via `gedcom_filename`). 🟢
- Requer `person1_name` e `person2_name` não vazios. 🟢
- Pessoa inexistente → mensagem de erro específica. 🟢
- Usa o **primeiro** ID encontrado para cada nome. 🟢
- Conexão direta: BFS bidirecional subindo por pais, profundidade máx. `20`. 🟢
- Conexão indireta: `networkx.shortest_path` no grafo geral, máx. `40` hops; comprime nós de família. 🟢
- Sem conexão → mensagem "Nenhuma conexão encontrada entre 'X' e 'Y'." 🟢
- Conexão indireta divide o caminho no 1º par de cônjuges adjacentes. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Localizar pessoas por nome | Must | IDs resolvidos ou erro específico |
| RF-02 | Buscar conexão direta por ancestral comum | Must | Caminho com MRCA exibido |
| RF-03 | Fallback para conexão indireta por afinidade | Must | Caminho via casamento exibido quando não há direta |
| RF-04 | Renderizar caminho textual e Mermaid | Must | `path_result` com `text_path` e `mermaid_data` |
| RF-05 | Tratar erro amigável em exceções | Must | Erro não quebra a aplicação |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | BFS bidirecional com `max_depth=20` | `app.py:297` | 🟢 |
| Performance | `shortest_path` (BFS) com `max_hops=40` | `app.py:281-294` | 🟢 |
| Performance | Cálculo em memória, sem cache | `app.py:856-870` | 🟡 |
| Segurança | Sem autenticação na rota | `app.py:558` | 🟢 |

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e duas pessoas existentes com ancestral comum
Quando o usuário submete path_search
Então "Conexão direta encontrada (ancestral comum)." é exibido com caminho e Mermaid

Dado duas pessoas existentes sem ancestral comum mas com vínculo por afinidade
Quando o usuário submete path_search
Então "Conexão indireta encontrada (via casamento/afinidade)." é exibido

Dado um nome de pessoa inexistente
Quando o usuário submete path_search
Então a mensagem "Pessoa 1 'X' não encontrada." (ou Pessoa 2) é exibida

Dado duas pessoas sem nenhuma conexão no grafo
Quando o usuário submete path_search
Então "Nenhuma conexão encontrada entre 'X' e 'Y'." é exibido
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Localizar pessoas (RF-01) | Must | Pré-condição do fluxo |
| Conexão direta (RF-02) | Must | Núcleo da busca |
| Conexão indireta (RF-03) | Should | Fallback importante, com alternativa |
| Renderização (RF-04) | Must | Saída principal |
| Erros amigáveis (RF-05) | Must | Robustez |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` (bloco `path_search`) | 🟢 |
| `analisador-genealogico/app.py` | `find_person_by_name` | 🟢 |
| `analisador-genealogico/app.py` | `find_ancestral_path` | 🟢 |
| `analisador-genealogico/app.py` | `find_indirect_path` | 🟢 |
| `analisador-genealogico/app.py` | `generate_mermaid_graph` / `generate_mermaid_graph_indirect_bridge` | 🟢 |
