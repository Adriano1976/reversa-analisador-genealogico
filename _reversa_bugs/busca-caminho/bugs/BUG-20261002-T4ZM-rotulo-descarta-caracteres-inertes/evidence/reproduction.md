# Cápsula de reprodução

> Bug: `BUG-20261002-T4ZM`
> Data: 2026-10-02
> Classificação: `deterministic`, 15 falhas em 15 caracteres testados
> Executado por: o agente que registrou o bug, por varredura comparativa

## Ambiente

| Item | Valor |
|------|-------|
| Candidato | `analisador-genealogico/reconstructed/mermaid_render.py`, lista branca `_LABEL_SEGURO` |
| Oráculo | `_reversa_sdd/oracle/app_legacy_e43ca22.py`, sha256 `44370b23...` |
| Commit base | `d9e9e5d` |
| Python | 3.14 |

## Passos executados

1. Varredura de todos os **95 caracteres ASCII imprimíveis** (`0x20` a `0x7E`), cada um inserido no
   meio de um nome, na forma `Ana<caractere>Silva`.
2. Cada lado rodou em **processo separado**, porque o oráculo mantém estado global mutável e
   importar os dois no mesmo processo contaminaria o candidato.
3. O rótulo emitido foi extraído da linha de nó e comparado caractere a caractere.
4. Para provar a causação, a mesma varredura foi repetida contra a versão de `_mermaid_label`
   extraída **verbatim** de `c709ea0^:analisador-genealogico/reconstructed/path_search.py`, isto é,
   o commit imediatamente anterior ao `CHG-001` do `BUG-20260929-J6PQ`.

## Resultado observado

| Comparação | Divergências |
|------------|--------------|
| oráculo contra a versão **anterior** ao `CHG-001` | **0** |
| oráculo contra a versão **atual** | **15** |

Os 15 caracteres divergentes e o comportamento em cada lado:

| Caractere | Oráculo e versão anterior | Versão atual |
|-----------|---------------------------|--------------|
| `#` `$` `%` `*` `+` `=` `@` `\` `^` `_` `{` `\|` `}` `~` | preservado | **descartado** |
| `` ` `` | preservado | **descartado**, e este descarte é o pretendido |

## O que esta reprodução prova

**Prova o defeito e a causação.** A versão anterior ao `CHG-001` era **idêntica ao oráculo** em
todos os 95 caracteres. A versão atual diverge em 15. Logo, os 15 descartes foram introduzidos
por aquele `CHG`, e 14 deles não eram pretendidos.

**Prova o modo de falha.** O descarte é silencioso: o diagrama continua válido, a conexão exibida
continua correta, e nada avisa. Só se percebe olhando o nome no nó.

## O que esta reprodução não prova

**Não prova o efeito visual em navegador.** O que se mede aqui é a string emitida pelo servidor.
Que o nome aparece sem o caractere na tela é consequência direta, e não foi conferido em navegador
como no `BUG-20260929-J6PQ`. Para um defeito de severidade `low` com efeito textual direto, isso me
parece suficiente, e registro a diferença por honestidade.

## Evidência

- `causacao-medida.txt`: a tabela de três colunas que fecha a causação.
- `varredura-divergencias.txt`: oráculo contra o candidato atual, 15 de 95.
- `varredura-antes-da-correcao.txt`: saída crua da versão anterior ao `CHG-001`.
- `varredura-oraculo.txt` e `varredura-candidato.txt`: as duas saídas cruas da versão atual.
- `probe_escape_sweep.py` e `probe_varredura_antes.py`: as sondas reproduzíveis.
