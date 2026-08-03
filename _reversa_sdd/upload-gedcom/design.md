# Upload e Parsing de GEDCOM, Design Técnico

> Nível de documentação: **Essencial**
> Confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Interface

Para o endpoint HTTP (formulário multipart):

| Método | Caminho | Entrada | Saída | Status codes |
|--------|---------|---------|-------|--------------|
| GET | `/` | — | `index.html` com formulário | 200 |
| POST | `/` | `action=upload_gedcom`, `gedcom: File` | `index.html` com lista de nomes ou mensagem de erro | 200 (sempre; sem redirects) |

Para funções:

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|------------|
| `load_gedcom_and_build_graph` | `(file_path: str)` | `all_names: list[str]` | Popula globais `people`, `families`, `graph`, `child_to_family` |
| `build_graph_from_parser` | `(people_dict: dict, parser: GedcomReader)` | `(g: nx.Graph, c2f: dict)` | Grafo bidirecional + índice filho→famílias |
| `get_name` | `(person)` | `str` | "Sem Nome" se ausente |

## Fluxo Principal
1. Recebe `POST /` com `action=upload_gedcom` (`app.py:562`). 🟢
2. Valida presença do campo `gedcom`; ausente → erro "Nenhum arquivo GEDCOM enviado." (`app.py:563-564`). 🟢
3. Valida `filename` não vazio; vazio → erro "Nenhum arquivo selecionado." (`app.py:566-567`). 🟢
4. Salva o arquivo em `UPLOAD_FOLDER` com nome original (`app.py:569-570`). 🟢
5. Chama `load_gedcom_and_build_graph` para parsear e construir o grafo (`app.py:571`). 🟢
6. Renderiza `index.html` com `gedcom_filename`, `all_names` e mensagem de sucesso (`app.py:572`). 🟢
7. Em exceção, renderiza com mensagem de erro (`app.py:573-574`). 🟢

### Detalhe do fluxo de parsing (`load_gedcom_and_build_graph`)
1. Abre o arquivo com `GedcomReader` (`app.py:177`). 🟢
2. Lê registros `INDI` → dicionário `people` (`app.py:178`). 🟢
3. Lê registros `FAM` → dicionário `families` (`app.py:179`). 🟢
4. Chama `build_graph_from_parser` → `graph`, `child_to_family` (`app.py:180`). 🟢
5. Ordena nomes alfabeticamente e retorna (`app.py:181`). 🟢

### Detalhe do grafo (`build_graph_from_parser`)
1. Adiciona nó por pessoa (`app.py:187-188`). 🟢
2. Adiciona nó por família (`app.py:190-193`). 🟢
3. Lê `HUSB`, `WIFE`, `CHIL` de cada família (`app.py:195-201`). 🟢
4. Conecta cônjuges e filhos ao nó da família (`app.py:202-205`). 🟢
5. Preenche `c2f` (índice filho → famílias) (`app.py:201`). 🟢

## Fluxos Alternativos
- **Sem arquivo:** renderiza erro, não processa (`app.py:563-564`). 🟢
- **Arquivo sem nome:** renderiza erro (`app.py:566-567`). 🟢
- **Exceção no parsing:** renderiza mensagem com `e` (`app.py:573-574`). 🟢
- **Pessoa sem nome:** `get_name` retorna "Sem Nome" (`app.py:43`). 🟢

## Dependências
- **ged4py** — parsing GEDCOM (`GedcomReader`). 🟢
- **networkx** — estrutura do grafo de relacionamento. 🟢
- **Flask** — roteamento e renderização Jinja2. 🟢
- **Sistema de arquivos** — persistência temporária em `uploads/`. 🟢

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Estado em memória global (singleton por processo) | `app.py:20-23` | 🟢 |
| Re-parse a cada requisição POST | `app.py:582` | 🟢 |
| Arquivo salvo com nome original do cliente (risco de path/colisão) | `app.py:569` | 🟡 |
| Pasta de upload fixa `uploads/` criada no boot | `app.py:15-17` | 🟢 |

## Estado Interno
Globais em memória, compartilhados por todo o processo:
- `people: dict[str, Person]` — pessoas do GEDCOM. 🟢
- `families: dict[str, Family]` — famílias do GEDCOM. 🟢
- `graph: nx.Graph` — grafo bidirecional pessoa↔família. 🟢
- `child_to_family: dict[str, list[str]]` — índice filho → famílias onde é `CHIL`. 🟢

Esses globais são sobrescritos a cada novo parse. 🟢

## Observabilidade
- Nenhum log explícito de upload/parse no código. 🔴
- Erros de parsing são propagados ao template como mensagem de usuário (`message=...`). 🟢

## Riscos e Lacunas
- 🔴 Sem validação de extensão/tamanho do arquivo — risco de upload de arquivos arbitrários para `uploads/`.
- 🔴 Sobrescrita de arquivos com mesmo nome no diretório `uploads/`.
- 🔴 Estado global compartilhado — concorrência entre requisições pode corromper a análise em servidores multi-worker.
- 🟡 `secret_key` exposta no código-fonte.
