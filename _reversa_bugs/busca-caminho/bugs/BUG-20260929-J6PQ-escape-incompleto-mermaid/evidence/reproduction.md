# Cápsula de reprodução

> Bug: `BUG-20260929-J6PQ`
> Data: 2026-09-29
> Executado por: o usuário, em navegador real
> Classificação: `deterministic`, 1 falha em 1 tentativa

## Ambiente

| Item | Valor |
|------|-------|
| Aplicação | `py -3.14 analisador-genealogico/app.py`, servidor de desenvolvimento do Flask |
| URL | `http://127.0.0.1:5000/` |
| Renderizador | **Mermaid 10.9.8**, versão informada pela própria mensagem de erro |
| Entrada | `.pytest-tmp/j6pq-repro/gedcom-nome-hostil.ged`, GEDCOM sintético, fora do versionamento |
| Commit base | `4a27198` |

## Passos executados

1. Upload do GEDCOM sintético pelo formulário.
2. Busca de caminho entre `Ana Raiz` e `Alvo Filho`.

O caminho encontrado foi `Ana Raiz → Joao] --> N_evil["pwn Hostil → `pwn Crase → Alvo Filho`,
com quatro pessoas, duas delas com nome hostil.

## Resultado observado

No lugar do diagrama, a página exibiu:

```
Syntax error in text
mermaid version 10.9.8
```

O diagrama **não renderiza**.

## Texto que a aplicação injetou

```
flowchart BT
N_I1["Ana Raiz"]
N_I2["Joao] --&gt; N_evil['pwn Hostil"]
N_I4["`pwn Crase"]
N_I3["Alvo Filho"]
N_I1 --> N_I2
N_I2 --> N_I4
N_I4 --> N_I3
style N_I1 fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px
style N_I3 fill:#ffebee,stroke:#ef5350,stroke-width:2px
```

## Causa do erro, segundo a gramática do Mermaid

A linha `N_I4["`pwn Crase"]` contém a sequência **aspa imediatamente seguida de crase**, para a qual
existe uma regra dedicada no lexer do `flowchart`:

```
<*>["][`]     { this.begin("md_string");}
```

Como o casamento mais longo vence, essa regra tem precedência sobre `<*>["]`, que casaria apenas a
aspa. O modo de lexing passa a `md_string`, e ali o `]` de fechamento é consumido por
`<md_string>[^`"]+` e por `<string>[^"]+`, nunca retornando o token `SQE` que a regra
`vertex: idString SQS text SQE` exige. O resultado é erro de sintaxe.

A linha do `Joao]` **não** produz esse efeito: sem crase depois das aspas, o lexer entra no estado
`string`, cujo `[^"]+` engole o `]` como texto. Análise completa em
`analise-gramatica-mermaid-20260929.md`.

## O que esta reprodução prova, e o que ela não prova

**Prova:** o texto vindo do arquivo do usuário é capaz de impedir a renderização do diagrama. É
defeito de disponibilidade e de robustez, com sintoma determinístico.

**Não prova:** falsificação do parentesco exibido. Nenhum dos dez payloads medidos encerrou o rótulo,
e a aspa dupla, único caractere que sairia do estado `string`, é substituída por apóstrofo em
`path_search.py:201`.

Isto é, o defeito **existe**, mas o sintoma é outro. O `bug.md` registrava "permite falsificar o
grafo exibido" e o que se observa é "impede o grafo de ser exibido".

## Ressalva sobre o escopo do gatilho

A reprodução usou **dois** nomes hostis no mesmo diagrama, então ela não isola qual deles causou o
erro. A atribuição à crase vem da leitura da gramática, e é a explicação mais provável, não uma
medição isolada. Uma segunda passada com um único nome hostil por diagrama fecharia essa lacuna.

---
*Gerado pelo Reversa-Debugger em 2026-09-29.*
