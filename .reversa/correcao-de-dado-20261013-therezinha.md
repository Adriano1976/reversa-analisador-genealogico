# Correção de dado — registro da Therezinha na árvore ativa

**Data:** 2026-10-13
**Escopo:** um byte-range de um arquivo de **dado** do operador (`src/uploads/`). **Nenhum
código foi alterado por esta correção.**

## O que foi corrigido, e por quê

O relatório de DNA (`94e2402671702cac__Familias_Sergipanas.csv`, kit `NG2749622`, MyHeritage)
traz `Therezinha Carvalho do Nascimento Souza`. A árvore grafava a pessoa sem o `Souza`:

```
1 NAME Therezinha Carvalho do /Nascimento/
```

Sem correspondência exata, o motor de matching caiu no ramo difuso e escolheu **outra pessoa**
— `Soraia Carvalho do Nascimento Souza`, que tem os três sobrenomes do CSV contra dois da
Therezinha. O cartão exibia os 31,9 cM da Therezinha sob o nome da Soraia, com o parentesco
documental **da Soraia**. Ver a análise completa em `_reversa_bugs/_sondas-matching/`.

## A alteração, exata

| | |
|---|---|
| Arquivo | `src/uploads/c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged` |
| De | `1 NAME Therezinha Carvalho do /Nascimento/` |
| Para | `1 NAME Therezinha Carvalho do Nascimento /Souza/` |
| Linhas tocadas | 1 (linha 99850) |
| Ocorrências | exatamente 1 — o script aborta se não for |
| Diferença | **+6 bytes** em 5.332.198 |
| Codificação / fim de linha | preservados (sem BOM, LF) |

## Por que o arquivo mudou de nome

O nome do arquivo armazenado é `<chave de conteúdo>__<nome visível>`, e a chave é
`sha256(conteúdo)[:16]`. Corrigir o conteúdo **obriga** a nova chave — manter o nome antigo
deixaria o arquivo com uma chave que não corresponde ao que ele é.

| | |
|---|---|
| Antes | `c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged` |
| Depois | `46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged` |
| Nome visível | inalterado (`Arvore Unificada Oficial V1 2`) |

Mudar só os bytes, mantendo o nome, também funcionaria — `resolver` valida a **forma** da
chave, não o conteúdo. Foi recusado de propósito: a invariante "nome do arquivo = chave do
conteúdo" existe para que dois envios do mesmo conteúdo reencontrem o mesmo arquivo, e
quebrá-la na mão é criar um arquivo que o aplicativo não reconheceria como seu.

## O que aconteceu com o arquivo original

**Nada foi apagado.** Ele foi movido para a aposentadoria do próprio aplicativo:

```
src/uploads/_aposentados/c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged
```

Íntegro, com os mesmos 5.332.198 bytes e o mesmo `sha256` (`c84fd7fb4201b69f…`), verificado
depois da movimentação.

Além disso, uma **cópia de segurança fora da pasta do aplicativo**, para o caso de a
aposentadoria ser desfeita ou a pasta ser limpa:

```
.reversa/backups-de-dados/20261013-c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged
```

## Consequência medida no resultado (ensaio antes de escrever)

O ensaio rodou a análise completa sobre uma cópia corrigida, antes de tocar no dado real:

| | Antes | Depois |
|---|---|---|
| Nome exibido no cartão | Soraia Carvalho do Nascimento Souza ❌ | **Therezinha Carvalho do Nascimento Souza** ✅ |
| Identidade | `a_confirmar` | **`confirmada`** |
| cM | 31,9 | 31,9 |
| Parentesco documental | Primos de 6º grau com 2× remoção (`found`) | **não encontrado (`not_found`)** |
| Caminho no GEDCOM | 7 nós, com grafo | **nenhum** |
| Confronto | Compatível | **Inconclusivo** |

**Nenhum outro cartão mudou de pessoa** (62 antes, 62 depois, 208 descartados nos dois), e os
cartões com aviso de identidade caíram de **10 para 9**.

## ⚠️ O que se ganhou e o que se perdeu — leia antes de reverter

Ganhou-se a **identidade certa**: o cartão agora é da Therezinha, e o aviso de identidade
sumiu porque não há mais divergência.

Perdeu-se a **conclusão documental**: a Therezinha **não tem caminho documental** até
`Adriano Santos` nesta árvore, então o cartão dela passou de "Compatível / Primos de 6º grau"
para "**Inconclusivo / parentesco não encontrado**". O parentesco que aparecia antes era o da
**Soraia** — legítimo para a Soraia, mas não era o dela.

Ou seja: a tela perdeu uma conclusão que estava **apoiada na pessoa errada**. O
"Inconclusivo" é o resultado honesto: há evidência genética (31,9 cM) e não há caminho
documental.

## Como reverter, se for preciso

1. mover de volta `_aposentados/c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged` para
   `src/uploads/` (o nome já é a chave do conteúdo, então ele volta a ser encontrado como era);
2. apagar `src/uploads/46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged`.

## Ferramentas deixadas no repositório

Em `_reversa_bugs/_sondas-matching/`:

| Arquivo | Para que serve |
|---|---|
| `corrigir_therezinha_ensaio.py` | O ensaio: mede antes/depois **sem** tocar no dado real |
| `corrigir_therezinha.py` | O script aplicado: guardas, backup, gravação e conferência |
| `corrigir_therezinha_verificar.py` | A verificação final pela tela, pelo caminho de produção |
