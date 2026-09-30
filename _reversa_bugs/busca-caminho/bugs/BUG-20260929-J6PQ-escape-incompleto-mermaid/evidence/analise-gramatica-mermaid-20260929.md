# Análise da gramática do Mermaid aplicada ao escape do J6PQ

> Fonte: `packages/mermaid/src/diagrams/flowchart/parser/flow.jison`, do repositório
> `mermaid-js/mermaid`, lido em 2026-09-29. Trechos citados literalmente do arquivo.
> Data da análise: 2026-09-29.

## Regras do lexer que importam

```
<string>[^"]+           { return "STR"; }
<string>["]             this.popState();
<*>["]                  this.pushState("string");
<*>["][`]               { this.begin("md_string");}
<md_string>[^`"]+       { return "MD_STR";}
<md_string>[`]["]       { this.popState();}
<text>"]"               { this.popState(); return 'SQE'; }
<*>"["                  { this.pushState("text"); return 'SQS'; }
```

E a regra da gramática que monta o nó quadrado:

```
vertex: idString SQS text SQE
        {$$ = $idString;yy.addVertex($idString,$text,'square');}
```

## Caso 1: colchete e aspa no meio do nome. Inerte.

Linha emitida pela aplicação:

```
N_I2["Joao] --&gt; N_evil['pwn Hostil"]
```

Traço do lexing:

| Entrada | Regra | Efeito |
|---------|-------|--------|
| `N_I2` | `NODE_STRING` | idString |
| `[` | `<*>"["` | entra no estado `text`, devolve `SQS` |
| `"` | `<*>["]` | entra no estado `string` |
| `Joao] --&gt; N_evil['pwn Hostil` | `<string>[^"]+` | devolve **um único** `STR`, engolindo o `]` |
| `"` | `<string>["]` | volta para `text` |
| `]` | `<text>"]"` | devolve `SQE` |

O `]` do nome entra dentro do `STR` e nunca chega a ser lido como `SQE`. A forma **nao** e encerrada
pelo colchete. A gramática confirma o que a sonda de emissao ja mostrava.

## Caso 2: crase no inicio do nome. Nao resolvido pela leitura.

Linha emitida pela aplicação:

```
N_I4["`pwn Crase"]
```

Aqui a sequencia e aspa seguida imediatamente de crase, e existe uma regra especifica para ela:
`<*>["][`]` casa dois caracteres e troca o modo de lexing para `md_string`. Como o casamento mais
longo vence em jison, essa regra tem precedencia sobre `<*>["]`, que casaria apenas a aspa.

Leitura do traco, marcada como **hipotese**:

| Entrada | Regra candidata | Efeito esperado |
|---------|-----------------|-----------------|
| `[` | `<*>"["` | estado `text`, `SQS` |
| `"` + crase | `<*>["][`]` | entra em `md_string` em vez de `string` |
| `pwn Crase` | `<md_string>[^`"]+` | `MD_STR` |
| `"` | `<*>["]` | empilha `string` |
| `]` | `<string>[^"]+` | vira `STR`, **nao** vira `SQE` |

Se esse traco estiver certo, a gramática recebe `idString SQS text STR` sem o `SQE` que a regra
`vertex` exige, e o diagrama **nao renderiza**: seria erro de sintaxe, nao falsificacao.

**Isto e hipotese de leitura da gramática, nao medicao.** O desfecho depende do parser em execucao e
a confirmacao e em navegador. O estado epistemologico desta parte permanece `hypothesized`.

## Por que o nome hostil nao pode conter aspa dupla

`path_search.py:201` substitui `"` por `'` depois de `:199` converter as aspas curvas em retas. A
sonda de emissao confirma, em todos os dez payloads, que nenhuma aspa dupla sobrevive ao escape. E a
aspa dupla e o unico caractere capaz de encerrar o rotulo antes do fim, porque o estado `string` so
sai por `<string>["]`.

Logo, o vetor de falsificacao nao e alcancavel pelo texto do rotulo. O que a regra
`<*>["][`]` abre e outra coisa: um caminho para **quebrar a renderizacao**, nao para falsificar o
parentesco exibido.

---
*Gerado pelo Reversa-Debugger em 2026-09-29.*
