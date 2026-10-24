# Onboarding: índice de nomes sem colisão entre árvores

> Identificador: `048-indice-de-nomes-sem-colisao`
> Data: `2026-10-24`

## 1. Pré-requisitos

- `.venv/` do repositório.
- Nenhuma dependência nova.

## 2. Reproduzir o defeito (antes da correção)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_indice_de_nomes_do_documental.py -q
```

Antes da 048, o teste de colisão não existia. Para ver o defeito, crie duas árvores sintéticas com
o **mesmo número de pessoas** e os **mesmos xrefs extremos**, carregue as duas no mesmo processo e
consulte o dossiê da segunda: ele cita um `xref` que não existe nela.

## 3. Verificar a correção

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_indice_de_nomes_do_documental.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: `7 passed` no arquivo do índice e **`1656 passed, 9 skipped`** na suíte (baseline 1655/9).

## 4. Conferir que o dossiê não mudou

Rode a mesma consulta de homônimos na mesma árvore antes e depois e compare o dossiê: conjunto de
ids, ordem, `exact_count` e fichas. A feature não pode mudar nenhum dos quatro.

## 5. Conferir que o módulo não voltou a ter estado

```powershell
Select-String -Path src\core\homonimos.py -Pattern "_INDICE_DE_NOMES|_chave_de"
```

Esperado: nenhuma ocorrência.

## 6. O que observar se algo parecer errado

| Sintoma | Causa provável |
|---|---|
| Dossiê com `xref` de outra árvore | o índice voltou a ser compartilhado |
| Segunda consulta reconstruindo o índice | o mapa não está preso ao grafo (ou o grafo é `None`) |
| Teste antigo do cache falhando por AST | o arquivo de testes não foi reescrito junto |
