# ADR-30 — Aposentar em vez de apagar

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-10
- **Commit(s):** `f20a818` ("aposenta um arquivo da lista"), dentro do ciclo `011-escolher-arquivo-da-lista`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A feature `011` fez a tela de entrada listar os arquivos armazenados. Com a lista visível, apareceu um problema que antes era invisível: a pasta real do operador tem arquivos que **ele não quer mais ver**, e que a aplicação **não consegue usar**. Medido: três arquivos com acento no nome e um com espaço, inalcançáveis pelo resolvedor por causa do alfabeto fechado de então (`ADR-32`), mais arquivos antigos sem chave de conteúdo.

A pergunta de negócio era: o operador pode **tirar da lista** um arquivo? E se pode, o que acontece com o dado?

Havia uma proibição vigente e explícita: **`RN-07` — a aplicação nunca apaga arquivo enviado.** Ela existe desde a primeira extração e não é uma preferência de implementação: é a garantia de que o dado genealógico do operador não desaparece por ação do sistema.

## Decisão

**Aposentar, e não apagar.** A operação move o arquivo para `<pasta>/_aposentados/`, e nada mais.

1. **A subpasta fica DENTRO da pasta de upload**, de propósito: `listar` já ignora subdiretório, então o arquivo sai da lista **sem que nenhum filtro novo precise ser escrito** — e sem uma lista de exceções que alguém teria de manter.
2. **A referência é mais permissiva aqui do que em `resolver`**, e isso é deliberado: `referencia_de_arquivo_da_pasta` aceita qualquer **nome** simples, e não apenas a forma canônica com chave. O motivo é medido — os arquivos **sem chave** são os inalcançáveis, e são exatamente os que o operador mais quer tirar da lista. Exigir a chave aqui os tornaria inapagáveis.
3. **Duas camadas de defesa.** Além da forma de nome, o `dirname` do caminho resolvido tem de ser **exatamente** a pasta de upload. A primeira camada já garante isso; a segunda não confia nela.
4. **Não sobrescreve um aposentado.** Se já existe um arquivo de mesmo nome em `_aposentados/`, um sufixo numérico `.1`…`.99` é acrescentado. Para nomes **sem** chave isso é indispensável: o nome não carrega conteúdo, e sobrescrever apagaria um arquivo **diferente**. Esgotadas as 99 tentativas, a operação **desiste** (`False`) — desistir é melhor do que sobrescrever.
5. **A mensagem diz que não apagou**, porque "apagar" é o que o botão parece fazer e o operador precisa saber que dá para voltar.

## Evidência

- `PASTA_DE_APOSENTADOS = "_aposentados"` em `src/ports/adaptadores.py`, com o comentário que explica a escolha da subpasta.
- `aposentar` devolve `False` em quatro casos distintos: referência em forma de caminho, `dirname` divergente, arquivo inexistente e colisão esgotada.
- A mensagem de sucesso, literal: `"'{ROTULO}' saiu da lista. O arquivo não foi apagado: ele continua guardado, inteiro, na pasta de aposentados."`
- A mensagem de fracasso: `"Não foi possível aposentar o arquivo: ele não está mais na pasta."`
- `tests/test_aposentar_arquivo.py` (337 linhas úteis) cobre a operação.
- **Nada foi apagado em nenhum ponto do sistema**: nem no adaptador, nem no banco, nem no esquema. O estado terminal da máquina é "aposentado", e não "excluído" (`state-machines.md` §7).

## Justificativa

**A `RN-07` não foi contrariada, foi honrada por outro caminho.** A necessidade do operador era "tirar da lista", e não "destruir o dado". Mover resolve a primeira sem tocar na segunda. O custo é que o disco cresce — e o projeto aceita esse custo explicitamente, porque o dado é genealógico e irreproduzível.

**A ordem dos ramos da rota é a regra, e não estilo:** `aposentar_arquivo` é tratado **antes** de `_arvore_do_formulario()`, porque essa função resolve e **parseia** a árvore escolhida — e a árvore escolhida pode ser exatamente a que se está aposentando. Depois do move, o parse falharia e o operador veria "arquivo não existe mais" no lugar da confirmação: a ação teria funcionado e a tela diria que não.

## Consequências

- 🟢 **O sistema ganhou seu primeiro estado durável de verdade** (`state-machines.md` §7): a **posição** do arquivo sobrevive ao processo. A rodada anterior concluía que nenhuma entidade persistente tinha ciclo de vida; essa deixou de ser verdade por causa desta decisão.
- 🔴 **O estado "aposentado" não é consultável pela aplicação.** Não há coluna, campo nem índice que registre que um arquivo foi aposentado: quem sabe disso é o sistema de arquivos. Consequência: a tela **não pode oferecer "desaposentar"**, e não há auditoria de quem aposentou o quê (`M-05`).
- 🟢 **A pasta não cresce sem limite visível:** o operador pode mover de volta à mão — é o que a mensagem sugere —, e o caminho está declarado na própria mensagem.
- 🟡 **Aposentar é irreversível pelo sistema e reversível pelo operador.** Essa assimetria é intencional, mas significa que a única forma de desfazer é mexer no sistema de arquivos — o que exige que o operador saiba onde a pasta fica.
