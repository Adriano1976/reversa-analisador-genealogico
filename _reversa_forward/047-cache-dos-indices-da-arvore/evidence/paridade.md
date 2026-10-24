# Paridade: cache ligado e desligado produzem o mesmo HTML

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Cenário: GEDCOM de 19.403 pessoas + CSV de 492 linhas, quatro execuções

## O que foi comparado

O `sha256` do HTML final de `POST /` com `action=dna_analysis` — a saída que o operador vê. O
template não tem data, hora, `uuid` nem número aleatório (verificado por varredura), então o HTML
é determinístico para a mesma entrada.

## Resultado

| Execução | Estado | `html_bytes` | `sha256` |
|---|---|---:|---|
| Linha de base | sem cache | 10.021.962 | `476b1f5f9ee18d92a88d2b81f2786c18674d9f6e87ab7193d966995de09b1966` |
| Depois nº 1 | sem cache | 10.021.962 | `476b1f5f9ee18d92a88d2b81f2786c18674d9f6e87ab7193d966995de09b1966` |
| Depois nº 1 | com cache | 10.021.962 | `476b1f5f9ee18d92a88d2b81f2786c18674d9f6e87ab7193d966995de09b1966` |
| Depois nº 2 | com cache | 10.021.962 | `476b1f5f9ee18d92a88d2b81f2786c18674d9f6e87ab7193d966995de09b1966` |

**Quatro execuções, dois estados, um único `sha256`.** Nenhum cartão, veredito, ordem, descarte
ou texto mudou — o cache só mudou quando o trabalho é feito.

## Limite desta prova

O hash cobre a saída de UMA análise, com a mesma raiz e o mesmo CSV. Ele não prova paridade para
outros arquivos; para isso existem os testes de contagem (que não dependem de relógio) e o
harness de paridade da extração.
