# Onboarding: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`

## 1. Pré-requisitos

- `.venv/` do repositório (o interpretador oficial) — `.\.venv\Scripts\python.exe`
- Um GEDCOM de teste **seu**, fora do versionamento. Os testes automatizados usam fixtures
  sintéticas (`tests/fixtures/sample_gedcom.py`); nunca use arquivo de `src/uploads/` em teste.
- Nada de dependência nova.

## 2. Conferir o cache (ligado por padrão)

O cache já vem ligado: nenhuma variável é necessária. Para deixá-lo explícito, ou para medir a
linha de base, use:

```powershell
$env:ANALISADOR_CACHE_DE_ARVORE = "1"              # opcional: já é o padrão
$env:ANALISADOR_CACHE_DE_ARVORE_CAPACIDADE = "1"   # opcional; 1 e o padrao
```

Para medir o **sem cache**, defina `ANALISADOR_CACHE_DE_ARVORE=0` e reinicie o processo.

## 3. Verificar o ganho, em três passos

1. Suba a aplicação e envie o GEDCOM uma vez. O primeiro envio **paga o parse** (~50 s): é o custo
   de entrada, não o cache.
2. Clique na árvore da lista. Sem cache isso custa ~55 s (medido: 54,81 s); com cache,
   **0,92 s**.
3. Rode a mesma análise de DNA duas vezes. A primeira leva **17,79 s** (constrói os índices) e a
   segunda **4,74 s** (reusa o memo). Sem cache, as duas levam ~62–70 s.

Para medir o `POST` inteiro sem instrumentar código:

```powershell
Measure-Command { Invoke-WebRequest -Uri http://127.0.0.1:5000/ -Method Post -Form @{ action = "dna_analysis"; gedcom_filename = "<ref>"; root_name = "<nome>" } }
```

## 4. Conferir a memória

```powershell
Get-Process python | Select-Object WorkingSet64
```

Esperado: **381 MB** depois do parse e **412 MB** depois dos índices. A segunda análise não move
   o RSS (medido: 412 MB antes e depois). Se passar de ~500 MB com uma
árvore, o teto não está valendo — investigue antes de aumentar a capacidade.

## 5. Conferir a paridade

Rode a suíte e compare a impressão digital da árvore e do resultado com cache ligado e desligado:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes novos contam chamadas ao parser e à construção de índices — não cronometram. Tempo é
ruído nesta máquina (o parse variou de 44 s a 92 s entre execuções).

## 6. Desligar

Defina `ANALISADOR_CACHE_DE_ARVORE=0` (ou `false`, `nao`, `off`, `no`) e reinicie o processo.
Remover a variável **não** desliga: o padrão é ligado. Não há resíduo em disco nem em banco.

## 7. O que observar se algo parecer errado

| Sintoma | Causa provável |
|---|---|
| Segunda análise continua lenta | cache desligado (`0`) ou variável não chegou ao processo (`.env` vs `docker-compose`) |
| Resultado diferente do de antes | memo de índices compartilhado entre árvores — é o defeito que o teste de duas árvores cobre |
| Memória crescendo a cada requisição | teto não aplicado; verifique a capacidade lida do ambiente |
