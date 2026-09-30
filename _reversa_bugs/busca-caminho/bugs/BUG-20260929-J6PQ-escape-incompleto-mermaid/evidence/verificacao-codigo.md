# Verificação de código: BUG-20260929-J6PQ

Evidência produzida pelo `/reversa-debugger` em 2026-09-29 por leitura direta dos arquivos e por
sonda executada fora do versionamento. Nenhum arquivo do projeto foi alterado.

## 1. A função de escape, primeira cópia

`analisador-genealogico/reconstructed/path_search.py:185-199`

```python
def generate_mermaid_graph(path, p1_id, p2_id, common_ancestor_id):
    def sid(raw: str) -> str:
        safe_str = str(raw).replace('@', '').replace('+', '_')
        return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)

    def lab(txt: str) -> str:
        s = unicodedata.normalize("NFC", str(txt))
        s = (s.replace('\u00A0', ' ')
               .replace('\u2013', '-')
               .replace('\u2014', '-')
               .replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'"))
        s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        s = s.replace('"', "'")
        s = re.sub(r'[\r\n]+', ' ', s)
        return s
```

## 2. A função de escape, segunda cópia

`analisador-genealogico/reconstructed/path_search.py:247-262`

```python
def generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path):
    def sid(raw: str) -> str:
        if isinstance(raw, (list, tuple, set)):
            raw = next(iter(raw), "")
        safe_str = str(raw).replace('@', '').replace('+', '_')
        return 'N_' + re.sub(r'[^a-zA-Z0-9_]', '', safe_str)

    def lab(txt: str) -> str:
        s = unicodedata.normalize("NFC", str(txt))
        s = (s.replace('\u00A0', ' ')
               .replace('\u2013', '-').replace('\u2014', '-')
               .replace('\u201c', '"').replace('\u201d', '"').replace('\u2019', "'"))
        s = (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        s = s.replace('"', "'")
        s = re.sub(r'[\r\n]+', ' ', s)
        return s
```

As duas cópias são equivalentes para fins de escape, e ambas omitem colchetes, crase e
palavras-chave do Mermaid. `sid()` difere entre as duas: a segunda trata sequências antes de
converter para texto.

## 3. Nomes do GEDCOM entram como rótulo

`analisador-genealogico/reconstructed/path_search.py:222-229` (recorte)

```python
    for node_id in path:
        if node_id in couple_members_to_skip:
            continue
        node_sid = sid(node_id)
        if node_sid not in seen_nodes:
            node_name = lab(get_name(people.get(node_id)))
            lines.append(f'{node_sid}["{node_name}"]')
            seen_nodes.add(node_sid)
```

`analisador-genealogico/reconstructed/path_search.py:308-314` (recorte)

```python
    def add_node(pid, label=None):
        pid = str(pid)
        node = sid(pid)
        if node not in seen:
            lines.append(f'{node}["{lab(get_name(people.get(pid))) if label is None else label}"]')
            seen.add(node)
        return node
```

`get_name` vem de `reconstructed/upload.py:33-47` e devolve o nome formatado do registro GEDCOM, logo
é conteúdo controlado pelo arquivo enviado pelo usuário.

## 4. Injeção com autoescape desligado

`analisador-genealogico/templates/index.html:125`

```html
                                    <div class="graph-container"><div class="mermaid">{{ result.mermaid_data | safe }}</div></div>
```

`analisador-genealogico/templates/index.html:170`

```html
                                <div class="graph-container"><div class="mermaid">{{ path_result.mermaid_data | safe }}</div></div>
```

São as duas únicas ocorrências de `| safe` no template.

## 5. A defesa existente

`analisador-genealogico/templates/index.html:180-188` (recorte)

```javascript
        document.addEventListener('DOMContentLoaded', function () {
            mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
            setTimeout(() => {
                const mermaidElements = document.querySelectorAll(".mermaid");
                if (mermaidElements.length) {
                    mermaid.run({ nodes: mermaidElements });
                }
            }, 100);
        });
```

O modo estrito bloqueia renderização de HTML e script não seguros nos rótulos. Ele não torna o texto
inerte para a gramática do Mermaid.

## 6. Sonda executada

Script: `.pytest-tmp/probe_mermaid.py` (cópia durável em `evidence/probe_mermaid.py`).
Transcrição completa da saída: `evidence/sonda-escape-mermaid-20260929.txt`.

Resumo do resultado, por entrada hostil:

| Entrada | Resultado |
|---------|-----------|
| Tag HTML | Neutralizada: convertida em `&lt;` e `&gt;` |
| `&` | Neutralizado: `&amp;` |
| Aspas duplas | Substituídas por apóstrofo |
| Quebra de linha | Colapsada em espaço |
| Colchete | Não tratado: permanece no rótulo |
| Crase | Não tratada: permanece no rótulo |
| Palavra-chave `click ... href` | Não tratada: permanece no rótulo |
| Diretiva `%%{init: ...}%%` | Não tratada: permanece no rótulo |

Conclusão: o escape cobre a via de HTML e XSS, e não cobre a via de sintaxe do Mermaid.

## 7. Specs que definem o esperado

| Locator | O que define |
|---------|--------------|
| `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#resumo-da-entrega` | Única mudança funcional autorizada: `securityLevel: 'strict'`, para fechar vetor de XSS vindo dos arquivos do usuário |
| `_reversa_sdd/addenda/001-reconstrua-o-conteudo-da-index.md#impacto-por-artefato-da-extração` | Impacto da decisão sobre `templates/index.html` |
| `_reversa_forward/001-reconstrua-o-conteudo-da-index/legacy-impact.md#modificadas` | "O strict impede a renderização de tags HTML não seguras nos rótulos dos grafos" |
| `_reversa_forward/001-reconstrua-o-conteudo-da-index/investigation.md#segurança-do-mermaid` | Investigação que fundamentou a decisão |
| `_reversa_forward/001-reconstrua-o-conteudo-da-index/requirements.md#9-esclarecimentos` | Resposta humana: "Mudar para o padrão strict (maior segurança)" |
| `_reversa_sdd/busca-caminho/design.md#interface` | Assinatura de `generate_mermaid_graph` e `generate_mermaid_graph_indirect_bridge` |
| `_reversa_sdd/busca-caminho/design.md#riscos-e-lacunas` | Riscos registrados da feature |

---
*Gerado pelo Reversa-Debugger em 2026-09-29.*
