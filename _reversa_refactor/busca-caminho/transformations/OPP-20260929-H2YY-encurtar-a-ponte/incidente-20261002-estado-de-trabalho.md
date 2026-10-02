# Incidente 2026-10-02: estado de trabalho do H2YY destruído e recuperado

> Registrado por iniciativa do próprio agente que causou o incidente.
> Não substitui o registro equivalente em `_reversa_sdd/migration/.state.json`, que tem os
> `INC-001` e `INC-002` da migração. Este fica junto do artefato afetado.

## O que aconteceu

Durante a sessão de correção do `BUG-20261002-T4ZM`, eu precisava desfazer uma alteração temporária
que havia feito em `analisador-genealogico/reconstructed/mermaid_render.py` para medir a viabilidade
da correção. Rodei:

```
git checkout -- analisador-genealogico/reconstructed/mermaid_render.py
```

Esse arquivo **não continha apenas a minha alteração temporária**. Ele tinha a aplicação da
`OPP-20260929-H2YY` inteira, **ainda não commitada** na árvore de trabalho. O `git checkout` reverteu
o arquivo para o `HEAD`, e com isso apagou a aplicação do `H2YY`.

## Por que aconteceu

Eu havia lido a lição registrada no `INC-001` do `.state.json` da migração, que diz, textualmente:

> NUNCA rodar `git checkout --` para 'limpar' um arquivo do usuario sem antes confirmar que a
> alteracao nao e trabalho legitimo. `git status` mostrando M nao significa corrupcao.

Li e repeti o erro. A causa imediata foi assumir que o `M` no `git status` era meu, quando havia
duas fontes de alteração no mesmo arquivo. A causa de fundo é trabalhar em árvore compartilhada com
atividade concorrente, sem isolar a minha mudança antes de revertê-la.

## Como foi recuperado

O `git diff` que eu havia capturado segundos antes continha o estado completo, e a transformação do
`H2YY` guarda o próprio diff em
`_reversa_refactor/busca-caminho/transformations/OPP-20260929-H2YY-encurtar-a-ponte/CHG-001.diff`.
Apliquei esse diff:

```
git apply _reversa_refactor/busca-caminho/transformations/OPP-20260929-H2YY-encurtar-a-ponte/CHG-001.diff
```

## Verificação da recuperação

Três verificações independentes, todas concordando:

| Verificação | Resultado |
|-------------|-----------|
| `git apply --reverse --check` do `CHG-001` do `H2YY` | passa, o que prova que o arquivo está **byte a byte** no estado pós-`H2YY` |
| `caracterizar.py` do `H2YY` reexecutado e comparado com `caracterizacao-depois.txt` | **idêntico**, a saída do diagrama está preservada |
| Suíte completa | **86 passed** |

A primeira é a mais forte: se o patch reverso aplica sem erro, o conteúdo em disco é exatamente o
resultado do patch original. Não sobra diferença.

## Dano residual

Nenhum, verificado. O `H2YY` segue aplicado na árvore e não commitado, que é como estava antes.

## Consequência para quem for aplicar o `CHG-001` do `BUG-20261002-T4ZM`

O arquivo alvo tem **duas** fontes de alteração em potencial enquanto o `H2YY` não for commitado. A
recomendação é commitar o `H2YY` antes, e nunca usar `git checkout` neste arquivo. Para desfazer uma
alteração local, usar `git apply --reverse` do diff específico, ou trabalhar sobre uma cópia do
arquivo.

## Nota de método

A recuperação só foi possível porque o `CHG-001.diff` da transformação estava gravado e era
fiel. Isso é o argumento mais direto a favor da regra do registro de que toda transformação aplicada
guarda o seu diff como fonte de reversão: neste caso, ele foi a fonte de **restauração**.
