# upload-gedcom

> Unit do tipo **endpoint** — cobre `POST /` com `action=upload_gedcom`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui a spec de 2026-08-03.

## Visão Geral

Recebe o arquivo GEDCOM (.ged) enviado pelo genealogista, parseia os registros `INDI` e `FAM`, constrói o grafo não-direcionado pessoa↔família em memória e publica esse grafo como estado global do processo, que os outros dois fluxos (busca de caminho e análise de DNA) consomem na sequência. 🟢

É a **porta de entrada do sistema**: sem um GEDCOM carregado com sucesso, nenhuma outra funcionalidade opera. 🟢

## Responsabilidades

- Receber e validar minimamente o upload do arquivo GEDCOM 🟢
- Persistir o arquivo em `uploads/` com o nome original 🟢
- Parsear registros `INDI` e `FAM` via `ged4py` 🟢
- Construir grafo `nx.Graph` com nós tipados (`person` / `family`) e o índice `child_to_family` 🟢
- Substituir o estado global anterior **in-place** (recarga limpa, sem resíduo) 🟢
- Devolver a lista ordenada de nomes para popular o seletor de pessoa-raiz na tela 🟢
- Corrigir mojibake de nomes (Latin-1 lido como UTF-8) 🟢

## Regras de Negócio

- Nome formatado é `person.name.format()`; o literal `'Sem Nome'` só aparece se `person` ou `person.name` estiver **ausente**. 🟢
- 🔴 **Formato vazio devolve string vazia** — e isso é o comportamento canônico, medido em dado real: 296 de 35.460 pessoas numa árvore e 17 de 3.056 em outra. **Nunca "melhorar" isso para devolver `'Sem Nome'`** — foi exatamente esse "melhoramento" que produziu a divergência `DIV-001` contra o oráculo congelado. 🟢
- O grafo é **não-direcionado**; a direção parental não é armazenada e é derivada depois por `get_parents`. 🟢
- Aresta pessoa↔família só é criada **se a pessoa já existir como nó**; referências órfãs são descartadas em silêncio. 🟢
- `FAM` sem `xref_id` é ignorada por completo. 🟢
- `child_to_family` acumula **todas** as famílias em que a pessoa aparece como `CHIL`. 🟢
- A recarga **substitui** o estado anterior (não acumula): recarregar um GEDCOM menor descarta as pessoas do anterior. 🟢
- Sem validação de extensão, tipo ou tamanho; o nome enviado vira caminho, então colisão **sobrescreve**. Limitação **aceita explicitamente** pelo usuário em 2026-08-03 (`questions.md#3`). 🟢
- `register_person` é idempotente: `xref_id` já existente é ignorado. 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Aceitar upload de arquivo GEDCOM e persistir em `uploads/` com o nome recebido | Must | O arquivo existe em `uploads/<nome>` após o POST 🟢 |
| RF-02 | Rejeitar envio sem arquivo GEDCOM com `"Nenhum arquivo GEDCOM enviado."` | Must | Resposta contém a mensagem e `success=False` 🟢 |
| RF-03 | Rejeitar arquivo com nome vazio com `"Nenhum arquivo selecionado."` | Should | Resposta contém a mensagem e `success=False` 🟢 |
| RF-04 | Parsear `INDI` e `FAM` e popular `people` e `families` indexados por `xref_id` | Must | Cada `xref_id` do arquivo aparece no dicionário correspondente 🟢 |
| RF-05 | Construir grafo com nós tipados e arestas apenas para referências resolvíveis | Must | Nó de pessoa tem `type="person"`; de família, `type="family"`; sem aresta para id inexistente 🟢 |
| RF-06 | Construir `child_to_family` com todas as famílias em que a pessoa é `CHIL` | Must | Pessoa com 2 famílias como filho aparece com 2 entradas 🟢 |
| RF-07 | Substituir integralmente o estado global anterior a cada carga | Must | Carregar árvore menor depois de maior deixa só as pessoas da menor 🟢 |
| RF-08 | Devolver a lista de nomes ordenada alfabeticamente | Must | `all_names == sorted(all_names)` 🟢 |
| RF-09 | Corrigir mojibake de nomes nos pontos de entrada de texto | Should | `"JoA�o"` vira `"João"`; string sem marcador de mojibake fica intacta 🟢 |
| RF-10 | Reportar falha de parsing sem derrubar a aplicação | Must | Mensagem `"Erro ao processar GEDCOM: {e}"` e `success=False` 🟢 |
| RF-11 | Recusar operação quando o arquivo não existe mais no disco | Should | Mensagem `"Erro: Arquivo '{nome}' não existe mais."` 🟢 |
| RF-12 | Devolver **exatamente um nome por pessoa**, sem entradas vazias indevidas | Should | Contagem de nomes == contagem de pessoas 🟢 |

> ⚠️ **Correção contra a spec anterior.** O `requirements.md` de 2026-08-03 afirmava, na seção Regras de Negócio, que "pessoas sem nome são listadas como 'Sem Nome'". **Isso é falso**: o literal só é inalcançável a partir de `INDI` reais; o caso comum (nome presente com formato vazio) devolve `''`. Ver `RF-12` e a regra 🔴 acima.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Escalabilidade | **Inexistente por design.** Estado global no processo; sem isolamento entre usuários nem entre requisições concorrentes. Dois uploads simultâneos escrevem no mesmo dicionário. | `analisador-genealogico/reconstructed/upload.py:16-19`, `:95-98` | 🟢 |
| Performance | **Sem cache.** O GEDCOM é re-parseado integralmente a cada `POST` que dependa da árvore. | `analisador-genealogico/app.py:31`, `:42` | 🟢 |
| Segurança | **Sem validação de entrada.** Nenhuma checagem de extensão, tipo MIME ou tamanho; o nome fornecido pelo cliente vira caminho de escrita. | `analisador-genealogico/app.py:29` | 🟢 |
| Segurança | `app.secret_key` **hardcoded**. | `analisador-genealogico/app.py:11` | 🟢 |
| Disponibilidade | Sem retry, timeout ou tratamento de disco cheio. Falha de parse vira mensagem na tela. | `analisador-genealogico/app.py:33-34` | 🟢 |

> Inferido do código. **A unit não emite nenhuma observabilidade** — sem `logging`, métrica ou trace. 🟢

## Critérios de Aceitação

```gherkin
Dado que o usuário está na tela inicial sem GEDCOM carregado
Quando ele envia um arquivo .ged válido com nome "familia.ged"
Então o arquivo é salvo em uploads/familia.ged
E o grafo é construído com nós de pessoa e de família
E a tela exibe "Arquivo 'familia.ged' carregado!"
E a lista de nomes aparece ordenada alfabeticamente

Dado que o usuário está na tela inicial
Quando ele submete o formulário sem selecionar arquivo
Então a tela exibe "Nenhum arquivo GEDCOM enviado."
E nenhum arquivo é gravado em uploads/

Dado que o usuário selecionou um arquivo cujo nome veio vazio
Quando ele submete o formulário
Então a tela exibe "Nenhum arquivo selecionado."
E nenhum arquivo é gravado

Dado que o usuário envia um arquivo .ged sintaticamente inválido
Quando o parse falha
Então a aplicação não quebra
E a tela exibe "Erro ao processar GEDCOM: {mensagem}"

Dado que uma árvore com 1.000 pessoas já está carregada
Quando o usuário carrega uma árvore diferente com 10 pessoas
Então o estado global contém exatamente as 10 pessoas da nova árvore
E nenhuma pessoa da árvore anterior permanece consultável

Dado um registro INDI cujo nome existe mas cujo formato resulta em string vazia
Quando a lista de nomes é montada
Então essa pessoa NÃO aparece como "Sem Nome"
E a contagem de nomes continua igual à contagem de pessoas
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| RF-04 Parsear `INDI`/`FAM` | **Must** | Caminho crítico: sem parse não há sistema |
| RF-05 Construir grafo | **Must** | Consumido por busca-caminho e análise-dna |
| RF-06 Índice `child_to_family` | **Must** | Fallback obrigatório de `get_parents` |
| RF-07 Substituir estado global | **Must** | Recarga correta é pré-condição das outras units |
| RF-08 Lista ordenada de nomes | **Must** | Alimenta o seletor de raiz da tela |
| RF-01 Persistir arquivo | **Must** | A árvore é relida do disco a cada POST |
| RF-02 / RF-10 Tratamento de erro | **Must** | Sem isso a aplicação devolve 500 |
| RF-09 Correção de mojibake | **Should** | Importante para nomes portugueses; há fallback de matching difuso |
| RF-03 / RF-11 / RF-12 | **Could** | Casos de borda, acionados raramente |
| Validação de extensão/tamanho | **Won't** | Decisão do usuário: limitação aceita para uso local |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `analisador-genealogico/app.py` | `index()` — ramo `upload_gedcom` (`:22-34`) | 🟢 |
| `analisador-genealogico/reconstructed/upload.py` | `load_gedcom_and_build_graph` (`:82`) | 🟢 |
| `analisador-genealogico/reconstructed/upload.py` | `build_graph_from_parser` (`:50`) | 🟢 |
| `analisador-genealogico/reconstructed/upload.py` | `get_name` (`:33`), `ref_id` (`:28`), `ensure_dirs` (`:24`) | 🟢 |
| `analisador-genealogico/reconstructed/domain.py` | `strip_bad_utf` (`:25`), `demojibake` (`:44`), `Family` (`:61`), `GenealogyGraph` (`:74`) | 🟢 |
| `tests/test_upload.py` | 16 testes, incl. `test_reload_replaces_globals`, `test_get_name_empty_formatted_returns_empty_string`, `test_load_returns_exactly_one_name_per_person_and_no_empty_entries` | 🟢 |
| `tests/test_domain.py` | 14 testes de entidades e limpeza de nome | 🟢 |

> ⚠️ **Correção de rastreabilidade.** A spec anterior apontava todas as funções para `app.py` com linhas como `:177`, `:187-188`, `:569`. Essas linhas **não existem mais** — o núcleo foi movido para `reconstructed/` (ADR-02) e `app.py` tem 84 linhas. As referências acima foram conferidas contra o código atual.

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
