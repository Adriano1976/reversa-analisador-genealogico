# Regression watch: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/core/graus_de_parentesco.py` (`nome_do_primo`) | O rótulo do primo sai de **uma** função, e as duas superfícies (`SCP40_ROWS` e `documentary_label`) dizem o mesmo texto | igualdade | volta a existir literal de `name_pt` na tabela, e as duas divergem |
| W002 | `src/core/graus_de_parentesco.py` (`geracoes_de_diferenca`) | Singular não recebe `s` (`uma geração`), plural recebe (`duas gerações`) | redação | aparece `uma gerações` ou `duas geração` |
| W003 | `src/core/relationship_hypotheses.py` e `src/core/documentary_relationship.py` | Nenhum rótulo de tela contém `×` nem a palavra `remoção` | ausência | `(1× removido)` volta a aparecer no bloco 3 ou no parentesco documental |
| W004 | `src/core/validator.py` (`_meioses_totais_da_relacao`) | A tradução de chave para meioses continua lendo a **chave**, não o rótulo | valor | alguém passa a extrair o número do texto e o `×` deixa de existir para extrair |
| W005 | `src/core/documentary_relationship.py` (`documentary_label`) | `key`, `meioses` e `degrees` continuam iguais para todo par — só o `label` mudou | valor | a chave muda junto com o texto, e o confronto deixa de casar a relação |

## Observações (sem peso de regressão)

- 🟢 **`core/cm_estimator.py` mantém os literais antigos de propósito.** É LEGADO fora do fluxo: não é
  exibido, e é superfície de compatibilidade do harness de paridade. Mudá-lo seria mexer no que o
  oráculo compara sem ganho para o operador.
- 🟡 **A contagem vira algarismo acima de dez.** `11 gerações de diferença` — não é inconsistência, é
  escolha: a série dos primos chega a `(11, 1)` no arquivo real, e `onze` num rótulo de tabela não
  ajuda a ler.
- 🟡 **"Diferença" é geracional, não de idade.** Duas pessoas com a mesma idade podem ter uma geração
  de diferença na linha do ancestral comum. A frase é a tradução corrente de *once removed*; a forma
  relacional ("primo de 1º grau de um dos pais") foi descartada porque o bloco 3 **não sabe** qual dos
  dois lados está mais alto — a linha da tabela é simétrica.
- 🟡 **O termo `removido` continua correto em outros contextos** (arquivo removido, byte removido, 1 %
  dos envios removido). A proibição vale para o rótulo de parentesco, e não para a palavra.
