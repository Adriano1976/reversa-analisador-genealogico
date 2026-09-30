# Verificação de código: BUG-20260929-BJJH

Evidência produzida pelo `/reversa-debugger` em 2026-09-29 por leitura direta dos arquivos.
Nenhum arquivo do projeto foi alterado.

## 1. Estado global de processo

`analisador-genealogico/reconstructed/upload.py:15-19`

```python
# Estado global em memória (singleton por processo) — não persistente.
people = {}
families = {}
graph = None
child_to_family: dict[str, list[str]] = {}
```

`analisador-genealogico/reconstructed/upload.py:87-98` (recorte)

```python
    global people, families, graph, child_to_family
    ...
        # Mutação in-place (clear + update) mantém válidas referências
        # importadas por outros módulos (ex.: path_search), preservando o
        # design de estado global do legado.
        people.clear(); people.update(new_people)
        families.clear(); families.update(new_families)
        graph = new_graph
        child_to_family.clear(); child_to_family.update(new_child_to_family)
```

O comentário do próprio autor registra que a preservação do estado global é deliberada, por
fidelidade ao legado. É exatamente o mecanismo que a migração decidiu eliminar
(`_reversa_sdd/migration/target_business_rules.md#br-humana-004`).

## 2. Pasta de upload única e compartilhada

`analisador-genealogico/app.py:13-16`

```python
UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
```

## 3. Nome do arquivo do cliente como identificador de sessão

`analisador-genealogico/app.py:31-33`

```python
                gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_file.filename)
                gedcom_file.save(gedcom_path)
                all_names = load_gedcom_and_build_graph(gedcom_path)
```

`analisador-genealogico/app.py:38-44`

```python
        gedcom_filename = request.form.get("gedcom_filename")
        if not gedcom_filename:
            return render_template("index.html", message="Erro: Arquivo GEDCOM não encontrado.", success=False)
        gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_filename)
        if not os.path.exists(gedcom_path):
            return render_template("index.html", message=f"Erro: Arquivo '{gedcom_filename}' não existe mais.", success=False)
        all_names = load_gedcom_and_build_graph(gedcom_path)
```

Não existe verificação de propriedade entre a linha 38 e a linha 44: qualquer valor de
`gedcom_filename` que corresponda a um arquivo existente em `uploads/` é carregado.

## 4. Lista completa de nomes exposta no HTML

`analisador-genealogico/templates/index.html:102-106`

```html
                            <datalist id="gedcom_names">
                                {% for name in all_names %}
                                ...
                            </datalist>
```

## 5. Ausência de autenticação ou de escopo por dono

Busca por `login`, autenticação, sessão de usuário ou `owner_id` em
`analisador-genealogico/*.py` e `analisador-genealogico/reconstructed/*.py` não retorna nenhuma
ocorrência. `app.secret_key` existe em `app.py:11`, mas nenhuma sessão de usuário é criada ou
validada, e nenhuma rota verifica identidade.

## 6. Specs que definem o esperado

| Locator | O que define |
|---------|--------------|
| `_reversa_sdd/migration/risk_register.md#risk-005` | Vazamento de dados genéticos entre usuários; exige `owner_id` como invariante e teste negativo com `404` |
| `_reversa_sdd/migration/ambiguity_log.md#amb-009` | Decisão humana de eliminar o "GEDCOM carregado" global; árvore como aggregate persistido com `owner_id` |
| `_reversa_sdd/migration/target_business_rules.md#br-humana-004` | Mesma decisão, registrada do lado das regras de negócio |
| `_reversa_sdd/migration/parity_specs.md#2-isolamento-por-tenant` | Isolamento por tenant como dimensão nova de paridade |
| `_reversa_sdd/migration/cutover_plan.md#criterios-de-go-no-go` | Teste negativo de isolamento como portão de go-live |
| `_reversa_sdd/migration/migration_brief.md#métricas-de-sucesso` | Métrica: nenhum cruzamento de árvores entre contas |
| `_reversa_sdd/domain.md#4-lacunas-requerem-validação-humana` | Registra a ausência de autenticação e autorização como lacuna |
| `_reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas` | Dívida 4: estado em memória com re-parse a cada requisição |

---
*Gerado pelo Reversa-Debugger em 2026-09-29.*
