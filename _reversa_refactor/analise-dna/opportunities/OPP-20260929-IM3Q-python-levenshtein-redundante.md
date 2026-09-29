---
schema_version: 1
id: OPP-20260929-IM3Q
display_number: 13
context: analise-dna
verb: prune
title: python-Levenshtein é dependência redundante
target:
  files: [analisador-genealogico/requirements.txt]
  symbol: python-Levenshtein
smell: dependência declarada que nenhum código importa e que a biblioteca consumidora não exige
roi:
  confidence: green
  impact: superfície de instalação e tempo de build de ambiente, sem nenhum ganho em troca
  cost: low
  est_return: uma dependência nativa a menos para compilar em cada ambiente novo
state: proposed
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/dependencies.md#2-dependências-diretas-requirementstxt, _reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas]
---

## Antes observado

`requirements.txt:6` declara `python-Levenshtein`. Três verificações:

1. **Nenhum import.** Varredura por `Levenshtein` em todo o `*.py` do app e dos testes devolve zero
   ocorrências.
2. **A biblioteca consumidora não exige.** `importlib.metadata.requires("thefuzz")` devolve apenas
   `['rapidfuzz <4.0.0,>=3.0.0']`. O `thefuzz` resolvia para `python-Levenshtein` em versões antigas;
   hoje resolve para `rapidfuzz`, que é C++ e já está instalado.
3. **Nada mais usa distância de edição direta.** O projeto chama `fuzz.ratio`,
   `fuzz.token_sort_ratio` e `fuzz.partial_ratio`, sempre pelo `thefuzz`.

## Transformação proposta

Remover a linha 6 de `requirements.txt`. O comportamento não muda: a resolução do `thefuzz` continua
sendo `rapidfuzz`, que vem como dependência dele.

## Rede de segurança exigida

`prune` exige `preservation.method: death-proof` com a prova anexada. A prova é a varredura de imports
acima mais a saída de `importlib.metadata.requires("thefuzz")`, ambas reproduzíveis.

## Risco

Baixo, com uma ressalva de ambiente: remover do manifesto não desinstala de ambientes já montados, e
um ambiente antigo que tenha o `thefuzz` preso a uma versão que usava `python-Levenshtein` passaria a
cair no backend puro Python. O `requirements.txt` não fixa versão de nada, então esse cenário já é
possível hoje por outro caminho, e é a dívida número 1 de `architecture.md#5`.

## Observação

Ganho real pequeno, mas o custo também é: é uma linha, com prova mecânica. Fica registrada porque a
re-inventariação deve reportar o que encontrou, não só o que é empolgante.
