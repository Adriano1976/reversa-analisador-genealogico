# Linha de base (antes da feature)

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Instrumento: `evidence/medir.py` (versao de uma analise)
> Suíte: `1635 passed, 9 skipped`

## Medição

```json
{"cache": "off", "raiz": "Adriano Santos", "pessoas": 19403, "familias": 21528, "arestas": 77346,
 "upload_s": 84.82, "selecao_s": 82.53, "dna_s": 68.49, "indices_s": 9.23, "analise_s": 17.27,
 "render_s": 0.213, "html_bytes": 10021962,
 "html_sha256": "476b1f5f9ee18d92a88d2b81f2786c18674d9f6e87ab7193d966995de09b1966"}
```

## Ressalva

A máquina estava carregada nesta execução: o parse levou ~82 s, contra 41–55 s nas execuções
seguintes. O número de 68,49 s para o `POST` de análise é a linha de base **desta** execução; a
comparação válida com o "depois" é pareada, feita na mesma sessão (`evidence/depois.md`).

O `sha256` do HTML é a impressão digital usada na prova de paridade (`evidence/paridade.md`).
