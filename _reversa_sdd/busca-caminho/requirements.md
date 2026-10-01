# busca-caminho

> Unit do tipo **endpoint** — cobre `POST /` com `action=path_search`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui a spec de 2026-08-03.

## Visão Geral

Busca a conexão genealógica entre duas pessoas de uma árvore GEDCOM já carregada. Tenta primeiro a conexão **direta** pelo ancestral comum mais próximo, subindo exclusivamente por linhas parentais; se não existir, cai no **fallback indireto** por afinidade (casamentos), navegando o grafo pessoa↔família. Renderiza o resultado como caminho textual e um diagrama Mermaid cuja forma muda conforme o tipo de conexão. 🟢

É a unit que carrega o **contrato de escape do rótulo Mermaid** — o ponto onde conteúdo vindo do GEDCOM entra numa gramática de diagrama. 🟢

## Responsabilidades

- Localizar as duas pessoas pelo nome na árvore 🟢
- Buscar conexão direta por ancestral comum (BFS bidirecional por pais) 🟢
- Em falha, buscar conexão indireta por afinidade (`shortest_path`, com teto de arestas) 🟢
- Decompor o caminho indireto na ponte matrimonial 🟢
- Sanitizar rótulos de nó e emitir o diagrama Mermaid 🟢
- Reportar ausência de conexão e erros de entrada de forma distinta 🟢

## Regras de Negócio

### Resolução de pessoas
- A busca é em **duas passadas**: igualdade `case-insensitive` primeiro; se nada, substring `case-insensitive`. 🟢
- Havendo homônimos, usa o **primeiro ID** — **sem desempate e sem aviso**. Decisão do usuário (`questions.md#2`): comportamento aceito, já validado várias vezes. 🟢
- Pessoa 1 não resolvida → `"Pessoa 1 '{nome}' não encontrada."`; idem para Pessoa 2. 🟢

### Conexão direta
- BFS **bidirecional**, com duas filas alternando um nível de cada lado. 🟢
- Sobe **apenas por pais** (`FAMC` preferencial; fallback no índice `child_to_family`). 🟢
- Teto de `MAX_DEPTH = 20` **iterações de profundidade** — não de gerações. 🟢
- `start_id == end_id` devolve caminho trivial `[start_id]`. 🟢
- Sucesso → `"Conexão direta encontrada (ancestral comum)."` 🟢

### Conexão indireta (fallback)
- Executada **somente** se a direta falhar. 🟢
- `nx.shortest_path` não ponderado no grafo pessoa↔família. 🟢
- Teto de `MAX_HOPS = 40` arestas; ultrapassar → sem caminho. 🟢
- Os nós de família são **comprimidos**: o caminho devolvido contém só pessoas. 🟢
- Exige ao menos 2 pessoas no caminho comprimido. 🟢
- Sucesso → `"Conexão indireta encontrada (via casamento/afinidade)."` 🟢

### Ponte matrimonial
- `split_path_by_marriage` encontra o **primeiro** par de cônjuges adjacentes no caminho. 🟢
- `pick_spouse_for_couple` prefere o cônjuge que já aparece no caminho; senão, o primeiro. 🟢
- `exclude_tail(n=1)` evita repetir o ancestral nas duas colunas do diagrama. 🟢

### Escape do rótulo Mermaid
- `_mermaid_sid` mantém apenas `[A-Za-z0-9_]`, remove `@`, troca `+` por `_` e prefixa `N_`. 🟢
- `_mermaid_label` aplica **NFC**, normaliza espaço não-quebrável, travessões e aspas curvas, troca `"` por `'`, achata quebras de linha, e então aplica **lista branca**. 🟢
- Depois da lista branca, `&`, `<` e `>` viram entidades HTML. 🟢
- A lista é **branca, não negra** — a negra anterior era furada pela crase, que desvia o lexer para *markdown-string* e derruba o diagrama inteiro. 🟢
- **A ordem é invariante do contrato:** filtro **antes** da conversão em entidades. Inverter reintroduz o defeito. 🟢

### Saída
- Sem conexão → `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` com `success=True`. 🟡

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Resolver pessoa por nome em duas passadas (exato, depois substring) | Must | Nome exato tem precedência sobre substring 🟢 |
| RF-02 | Usar o primeiro ID quando houver homônimos | Must | Duas pessoas com o mesmo nome resolvem para o mesmo ID 🟢 |
| RF-03 | Reportar por pessoa quando o nome não resolve | Must | Mensagem distingue Pessoa 1 de Pessoa 2 🟢 |
| RF-04 | Buscar conexão direta por BFS bidirecional subindo por pais | Must | Caminho com ancestral comum e caminho textual completos 🟢 |
| RF-05 | Respeitar o teto de 20 iterações de profundidade | Must | Caminho mais fundo que o teto devolve `(None, None)` 🟢 |
| RF-06 | Tratar pessoas idênticas com caminho trivial | Should | `path == [id]` e `common_ancestor == id` 🟢 |
| RF-07 | Cair para a busca indireta somente quando a direta falhar | Must | Conexão com ancestral comum nunca é reportada como indireta 🟢 |
| RF-08 | Buscar indireta por `shortest_path` com teto de 40 arestas | Must | Caminho mais longo que o teto é rejeitado 🟢 |
| RF-09 | Comprimir nós de família do caminho indireto | Must | O caminho devolvido contém apenas ids de pessoa 🟢 |
| RF-10 | Decompor o caminho pela primeira ponte matrimonial | Should | Caminho com casamento adjacente é partido em dois ramos 🟢 |
| RF-11 | Sanitizar o rótulo do nó por **lista branca** | Must | Aspas duplas e crase neutralizadas; acentos e pontuação legítima sobrevivem 🟢 |
| RF-12 | Converter `&`, `<`, `>` em entidades HTML **após** o filtro | Must | O diagrama não contém `&`/`<`/`>` crus que quebrem a gramática 🟢 |
| RF-13 | Emitir diagrama Mermaid adequado ao tipo de conexão | Must | Direto usa `generate_mermaid_graph`; indireto usa a variante de ponte 🟢 |
| RF-14 | Distinguir "sem conexão" de erro de entrada | Should | Sem conexão devolve mensagem própria com `success=True`; entrada inválida devolve `success=False` 🟡 |
| RF-15 | Reportar erro amigável em exceções | Must | Exceção → `"Ocorreu um erro: {e}"`, sem quebrar 🟢 |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Performance | BFS bidirecional com teto de 20 iterações — limite que corta a explosão combinatória de subir duas linhagens | `analisador-genealogico/reconstructed/path_search.py:22`, `:144-178` | 🟢 |
| Performance | `shortest_path` não ponderado com teto de 40 arestas | `analisador-genealogico/reconstructed/path_search.py:23`, `:126-141` | 🟢 |
| Performance | **Sem cache.** O grafo é reconstruído a cada POST antes da busca | `analisador-genealogico/app.py:42` | 🟢 |
| Segurança | **Sem autenticação** na rota — qualquer visitante executa a busca | `analisador-genealogico/app.py:18` | 🟢 |
| Segurança | O escape de rótulo é a **única** defesa contra conteúdo do GEDCOM quebrar o diagrama; `securityLevel: 'strict'` cobre XSS, não a gramática | `reconstructed/path_search.py:201-214`; `templates/index.html:182` | 🟢 |

> A unit **não emite nenhuma observabilidade**: sem `logging`, métrica ou trace. 🟢

## Critérios de Aceitação

```gherkin
Dado um GEDCOM carregado e duas pessoas existentes com ancestral comum
Quando o usuário busca o caminho entre elas
Então a tela exibe "Conexão direta encontrada (ancestral comum)."
E o caminho textual mostra a sequência do ancestral comum até as duas pessoas
E o diagrama Mermaid é renderizado

Dado que a busca direta falha mas existe vínculo por casamento
Quando o usuário busca o caminho
Então a tela exibe "Conexão indireta encontrada (via casamento/afinidade)."
E o diagrama é emitido na forma de ponte, com a aresta rotulada "Casamento"

Dado um nome que não existe na árvore
Quando o usuário busca o caminho
Então a tela exibe "Pessoa 1 'X' não encontrada." (ou Pessoa 2, conforme o caso)
E nenhum diagrama é emitido

Dado duas pessoas existentes sem nenhum caminho no grafo
Quando o usuário busca o caminho
Então a tela exibe "Nenhuma conexão encontrada entre 'X' e 'Y'."
E a resposta não é tratada como erro

Dado duas pessoas que são a mesma pessoa
Quando o usuário busca o caminho
Então o caminho é a própria pessoa
E o ancestral comum é ela mesma

Dado um nome vindo do GEDCOM que contém aspa dupla seguida de crase
Quando o diagrama é emitido
Então o rótulo do nó é neutralizado
E o diagrama continua sendo um flowchart válido
E nenhuma aspa dupla crua ou crase sobrevive no rótulo

Dado um nome com "&", "<" ou ">"
Quando o diagrama é emitido
Então esses caracteres aparecem como &amp;, &lt; e &gt;
E os caracteres legítimos (acentos, pontos, parênteses) sobrevivem intactos
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-01 / RF-02 / RF-03 Resolução de pessoas | **Must** | Pré-condição de todo o fluxo |
| RF-04 / RF-05 Conexão direta e teto | **Must** | Núcleo da busca |
| RF-07 / RF-08 / RF-09 Conexão indireta | **Must** | Sem o fallback, todo parentesco por afinidade fica invisível |
| RF-11 / RF-12 Escape do rótulo | **Must** | **Sem isso o diagrama inteiro deixa de renderizar** — foi o `BUG-20260929-J6PQ` |
| RF-13 Emissão do diagrama | **Must** | Saída principal |
| RF-15 Erro amigável | **Must** | Robustez |
| RF-10 Decomposição por casamento | **Should** | Melhora o layout do diagrama indireto; há fallback |
| RF-06 Pessoas idênticas | **Should** | Caso de borda com tratamento explícito |
| RF-14 Distinção sem-conexão × erro | **Should** | Ambos funcionam; a clareza é que depende do contrato |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` — ramo `path_search` (`:65-78`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `path_search` (`:463`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `find_person_by_name` (`:30`), `get_parents` (`:42`), `get_spouses` (`:64`), `are_spouses` (`:91`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `find_ancestral_path` (`:144`), `find_indirect_path` (`:126`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `split_path_by_marriage` (`:95`), `pick_spouse_for_couple` (`:106`), `exclude_tail` (`:117`) | 🟢 |
| `analisador-genealogico/reconstructed/path_search.py` | `_mermaid_sid` (`:185`), `_mermaid_label` (`:204`), `generate_mermaid_graph` (`:217`), `generate_mermaid_graph_indirect_bridge` (`:266`) | 🟢 |
| `analisador-genealogico/templates/index.html` | Inicialização do Mermaid com `securityLevel: 'strict'` (`:182`) | 🟢 |
| `tests/test_path_search.py` | 9 testes, incl. `test_indirect_connection_via_marriage`, `test_no_connection`, `test_identical_persons` | 🟢 |
| `tests/test_mermaid_escape.py` | 6 testes, incl. `test_rotulo_neutraliza_crase`, `test_entidades_html_preservadas` | 🟢 |
| `tests/test_characterization_mermaid.py` | 2 testes de caracterização da saída Mermaid | 🟢 |

> ⚠️ **Correção de rastreabilidade.** A spec anterior apontava tudo para `app.py` com linhas como `:297-318`, `:534`, `:853`. Essas linhas **não existem mais** — o núcleo está em `reconstructed/path_search.py`. As referências acima foram conferidas contra o código atual.

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
