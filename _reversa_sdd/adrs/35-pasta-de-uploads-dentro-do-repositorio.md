# ADR-35 — A pasta de uploads dentro do repositório, com o `.gitignore` como garantia

- **Status:** Aceito e **vigente** — **reverte** a decisão da feature `010`
- **Data da decisão:** 2026-10-09
- **Commit(s):** `e052cb7` (registra a feature `010-uploads-fora-do-repositorio`), `0806674` (registra a feature `012-pasta-canonica-no-repositorio`), `71cb73c` (publica os dois adendos)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Este é o **único caso de decisão revertida** no histórico do projeto, e por isso fica registrado nos dois sentidos.

**A decisão original (feature 010, 2026-10-09).** A feature `010-uploads-fora-do-repositorio` decidiu que a pasta canônica de arquivos enviados viveria **fora** da árvore do repositório. O problema que ela atacava é real e está declarado no `README` e no Princípio I do projeto: a pasta `src/uploads/` guarda **dado real do operador** — 13 arquivos, entre eles um GEDCOM de 5,3 MB —, e dado real nunca deve ser versionado. Manter a pasta dentro do repositório deixa a proteção inteiramente a cargo do `.gitignore`.

**A reversão (feature 012, no mesmo dia).** `012-pasta-canonica-no-repositorio` desfez a decisão `D-01`/`3b` da 010 e fixou **uma única pasta, dentro do repositório**: `src/uploads/`.

## Decisão

**Uma única pasta canônica, dentro da árvore do repositório (`src/uploads/`), com a exclusão do Git como garantia material.**

O que sustenta a decisão vigente não é preferência de organização, e sim **duas garantias verificáveis**:

1. **O `.gitignore` tem `uploads/` com barra final.** O padrão com barra final casa em **qualquer profundidade**, e o comentário do arquivo declara isso explicitamente — a linha cobre `uploads/` **e** `analisador-genealogico/uploads/`.
2. **A verificação feita nesta rodada confirma o efeito:** `git ls-files src/uploads` devolve **0** arquivos, e a pasta tem **13** em disco.

E há uma terceira garantia, de empacotamento: o `.dockerignore` é lista de **permissão** (`ADR-28`) e reexclui `src/uploads/` **depois** do `!src/**`, porque a última regra que casa vence. Dado real do operador **não entra na imagem**.

## Evidência

- `.gitignore` contém, entre os comentários que declararam a decisão: `uploads/`, com a nota de que a barra final cobre as duas profundidades.
- `git ls-files src/uploads` → **0** arquivos rastreados; `Get-ChildItem src/uploads -File` → **13** arquivos em disco.
- `.dockerignore` reexclui `src/uploads/` **depois** de `!src/**`, com o comentário que explica a ordem.
- Os dois adendos (`010` e `012`) foram publicados em `_reversa_sdd/addenda/`, e a extração anterior os registrou como vigentes.

## Justificativa

**A garantia que a feature 010 buscava já existe, e ela é mais barata que mudar a pasta.** Tirar a pasta do repositório resolve o risco de versionamento acidental por **arquitetura**; o `.gitignore` resolve o mesmo risco por **configuração verificável**. A diferença prática é que a segunda solução não obriga o operador a saber onde a pasta fica, não quebra o caminho ancorado no arquivo do app (`_pasta_uploads()`) e não muda o comportamento de nenhum teste.

**Mas a decisão vigente tem um custo declarado, e ele é maior que o da alternativa:** ela depende de uma linha de configuração continuar existindo. Se o `uploads/` sair do `.gitignore`, o próximo `git add .` versiona um GEDCOM de 5,3 MB. A decisão foi tomada com esse custo à vista, e é por isso que a verificação está registrada aqui, com números.

## Consequências

- 🟢 **O caminho da pasta continua ancorado no arquivo do app** (`_pasta_uploads()`), e não no diretório corrente — o que resolve o defeito que quebrou a análise de DNA quando o CWD mudava. Tirar a pasta do repositório teria reaberto essa questão.
- 🟢 **`ANALISADOR_UPLOAD_FOLDER` continua sendo o mecanismo de redirecionamento**, e é o que os testes usam para não escrever na pasta real.
- 🟢 **A pasta de aposentados (`_aposentados/`) fica dentro da pasta de upload** (`ADR-30`), o que faz a decisão de localização valer também para os arquivos aposentados — que, pela `RN-07`, nunca saem do sistema.
- 🔴 **O risco é de configuração, e não de código.** Nenhum teste prende a existência da linha `uploads/` no `.gitignore`. Um teste que verificasse a exclusão seria possível, e **não existe** — é a lacuna que esta reversão deixa aberta.
- 🟡 **A decisão anterior não foi apagada.** Os adendos `010` e `012` ficam os dois preservados em `_reversa_sdd/addenda/`, e a leitura correta dos dois é cronológica: a 012 é a vigente.
- 🟡 **A pasta tem 13 arquivos hoje, e o número só cresce** — a aplicação nunca apaga (`RN-07`), e o aposentar move para dentro, não para fora. Não há política de retenção para arquivos, assim como não há para o histórico da análise (`L-29`).
