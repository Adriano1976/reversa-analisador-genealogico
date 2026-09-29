# Verificação de código: BUG-20260929-QMLY

Evidência produzida pelo `/reversa-debugger` em 2026-09-29 por leitura direta dos arquivos.
Nenhum arquivo do projeto foi alterado.

## 1. Ausência de limite de tamanho

`analisador-genealogico/app.py:9-16` (arquivo completo da configuração)

```python
# --- Configuração ---
app = Flask(__name__)
app.secret_key = 'f@milyse@rch_dna_edition_v16'

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
```

Busca por `MAX_CONTENT_LENGTH` em todo o projeto retorna zero ocorrências. O valor padrão do Flask
para esse parâmetro é ilimitado, então a aplicação aceita corpo de requisição de qualquer tamanho.

## 2. Nome do cliente vira caminho de escrita (GEDCOM)

`analisador-genealogico/app.py:24-36` (recorte)

```python
        if action == "upload_gedcom":
            if "gedcom" not in request.files:
                return render_template("index.html", message="Nenhum arquivo GEDCOM enviado.", success=False)
            gedcom_file = request.files["gedcom"]
            if gedcom_file.filename == '':
                return render_template("index.html", message="Nenhum arquivo selecionado.", success=False)
            try:
                gedcom_path = os.path.join(UPLOAD_FOLDER, gedcom_file.filename)
                gedcom_file.save(gedcom_path)
```

As únicas verificações são: o campo existe e o nome não é vazio. Não há
`werkzeug.utils.secure_filename`, não há teste de extensão, não há teste de conteúdo.

## 3. Mesmo padrão para o CSV de DNA

`analisador-genealogico/app.py:48-52`

```python
                if "matches_csv" not in request.files or not request.files["matches_csv"].filename:
                    return render_template("index.html", gedcom_filename=gedcom_filename, all_names=all_names, message="Por favor, carregue o arquivo CSV de matches.", success=False)
                matches_file, root_name = request.files["matches_csv"], request.form["root_name"]
                matches_path = os.path.join(UPLOAD_FOLDER, matches_file.filename)
                matches_file.save(matches_path)
```

## 4. Sem verificação de conteúdo antes do parse

`analisador-genealogico/reconstructed/upload.py:82-91`

```python
def load_gedcom_and_build_graph(file_path: str) -> list[str]:
    """Parseia o GEDCOM e devolve a lista de nomes ordenada.

    Sobrescreve as globais people, families, graph e child_to_family.
    """
    global people, families, graph, child_to_family
    with GedcomReader(file_path) as parser:
        new_people = {ref_id(i.xref_id): i for i in parser.records0("INDI")}
        new_families = {ref_id(f.xref_id): f for f in parser.records0("FAM")}
```

O arquivo é entregue direto ao `GedcomReader`. Nenhuma checagem de magic bytes, extensão ou
estrutura precede o parse.

## 5. O nome do arquivo é devolvido e reenviado como chave

`analisador-genealogico/app.py:34`

```python
                return render_template("index.html", gedcom_filename=gedcom_file.filename, all_names=all_names, message=f"Arquivo '{gedcom_file.filename}' carregado!", success=True)
```

`analisador-genealogico/app.py:38-44` recebe esse mesmo nome de volta e o recompõe em caminho, sem
verificação adicional.

## 6. Sobrescrita silenciosa

Como a chave de armazenamento é o próprio nome do arquivo (linha 31 para o GEDCOM, linha 51 para o
CSV), dois envios com o mesmo nome escrevem no mesmo caminho. Não há detecção de colisão nem aviso
ao usuário.

## 7. Declaração de intenção no próprio código

`analisador-genealogico/reconstructed/upload.py:1-7`

```python
"""Tarefa 02 — Upload e Parsing de GEDCOM.

Salva o .ged em uploads/, faz o parsing de registros INDI/FAM via ged4py,
constrói o grafo bidirecional pessoa<->família (networkx) e retorna a lista
ordenada de nomes. Comportamento idêntico ao legado (inclui as limitações
documentadas: sem validação de extensão/tamanho, colisão sobrescreve).
"""
```

A limitação é conhecida, documentada e deliberada. O que mudou foi o contexto de uso, não o código.

## 8. Specs que definem o esperado

| Locator | O que define |
|---------|--------------|
| `_reversa_sdd/migration/risk_register.md#risk-007` | Risco de upload, gatilhos e mitigação (chave gerada, limite, validação de extensão e conteúdo) |
| `_reversa_sdd/migration/target_business_rules.md#br-humana-001` | Decisão humana de descartar a limitação aceita |
| `_reversa_sdd/migration/discard_log.md#br-descartar-003` | Descarte do armazenamento por nome do cliente |
| `_reversa_sdd/migration/discard_log.md#br-descartar-006` | Descarte da ausência de política de upload |
| `_reversa_sdd/migration/ambiguity_log.md#amb-006` | Reabertura da decisão |
| `_reversa_sdd/questions.md#pergunta-3` | Resposta antiga: limitação aceita para uso local |
| `_reversa_sdd/analise-dna/requirements.md#rastreabilidade-de-código` | Risco registrado: sem sanitização de nomes de arquivos recebidos |
| `_reversa_sdd/upload-gedcom/design.md#riscos-e-lacunas` | Riscos da feature de upload |
| `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais` | Requisitos não funcionais da feature |
| `_reversa_sdd/confidence-report.md#lacunas-pendentes-` | Lacuna registrada na revisão de confiança |
