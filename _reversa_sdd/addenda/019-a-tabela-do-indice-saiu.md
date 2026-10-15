# Adendo: a tabela do índice saiu — o cabeçalho do cartão é a lista

> Identificador: `019-a-tabela-do-indice-saiu`
> Data: `2026-10-14`
> Cenário: **legado** (âncora em `_reversa_sdd/analise-dna/`)
> **Origem do registro:** escrito à mão, a pedido do operador. O canal canônico de adendo é o
> `/reversa-sync`, e esta linha existe para que a próxima rodada saiba que este arquivo **não**
> saiu daquele pipeline.

## Vigência

Vigente desde 2026-10-14.

**Substitui o comentário do índice em `src/templates/index.html`**, que declarava a tabela como
necessária ("um índice com âncoras resolve a navegação SEM esconder conteúdo"), e **corrige uma
justificativa do adendo `018`**, que dizia que "o índice acima já traz as sete colunas de todas as
conexões, então nada some quando o cartão fecha". Com a tabela fora, quem garante isso é o
**cabeçalho do cartão**.

**Não altera `SHA_DA_TELA`**: a tabela vivia dentro de `{% if dna_results %}`, e a tela de entrada
vazia não tem resultado. Verificado, e não suposto.

## O pedido

> *"Já que temos essa lista criada, não precisamos mais desse formato que ainda ficou porque a
> lista com o novo recurso já é o suficiente."*

O operador está certo, e o motivo é **consequência do adendo `018`**: enquanto os cartões nasciam
todos abertos, a tabela era a única visão geral. Com os cartões recolhíveis, passou a haver **duas
listas de resumos** — a tabela e a pilha de cabeçalhos —, e a coluna *Confrontação* dizia
exatamente o que o selo do cabeçalho já dizia.

## O que a tabela dava, e para onde foi

| Coluna | Situação | Destino |
|---|---|---|
| Match | duplicada (o cabeçalho diz o nome) | — |
| cM | duplicada | — |
| Confrontação | **duplicada** | — |
| Identidade | o cabeçalho já marcava, e só quando `a_confirmar` | — |
| **Parentesco no GEDCOM** | só a tabela | → `.rotulo-parentesco` no cabeçalho |
| **Janela de vida** | **só a tabela** | → selo `janela-*` no cabeçalho |
| **Profundidade** | **só a tabela** | → selo `profundidade-*` no cabeçalho |

As três que só a tabela dava **não podiam simplesmente sumir**. O próprio template registrava por
quê, na coluna de janela de vida:

> *"Aparece na LISTA para o operador não precisar abrir 62 cartões para achar as conexões em que a
> identidade não fecha."*

Remover a tabela sem realocar isso teria trocado uma duplicação por uma perda: achar as conexões
com idade impossível ou profundidade divergente voltaria a exigir abrir cartão por cartão. As três
subiram para uma segunda linha do cabeçalho (`.cabecalho-sinais`), que é o `<summary>` do cartão —
ou seja, aparecem **com o cartão fechado**, que era exatamente o trabalho da coluna.

## O `card-header` foi preservado, e por que isso importa

A segunda linha usa `<span>`, e **não** `<div>`. Um `div` fecharia o `card-header` cedo para o
extrator de teste (`_cabecalhos` lê até o primeiro `</div>`), e o teste passaria a medir um
cabeçalho truncado — quebra silenciosa, do tipo que este projeto persegue.

## O acoplamento que sobrou

O `#indice` era o alvo do link "**Voltar**" de cada cartão. Com a tabela fora, o alvo passou a ser
o título `#resultados`. Os dois nascem em pontos separados do template, e renomear um só não
levanta erro nenhum — o link apenas deixa de ter alvo. O par continua preso por teste
(`tests/test_estado_do_resultado.py`), com prova de sensibilidade de que a checagem **detecta** a
divergência.

## Verificação

| | |
|---|---|
| Suíte | **1000 passou, 9 pulados**, exit 0 |
| `SHA_DA_TELA` | **inalterado** — a tabela estava dentro da guarda dos resultados |
| Testes reescritos | `test_estado_do_resultado.py` (o índice e o retorno), `test_identidade_do_match.py` e `test_janela_de_vida.py` (as colunas → o cabeçalho), `test_cartoes_recolhiveis.py` |
| No servidor, 142 cartões reais | `indice-resultados` **0**; 142 `cabecalho-sinais`; 142 `Voltar` → `#resultados`; 1 `id="resultados"` |
| Página | 7.369.558 → **7.175.897** bytes |

## O erro que a verificação pegou

`test_o_sinal_de_janela_esta_no_cabecalho_do_cartao` **falhou** depois de eu escrever a mudança: o
comentário que eu acrescentei ao template cita `<div class="card-header">` e `</div>` **em prosa**,
e o regex do teste casou ali dentro, medindo a documentação em vez do documento. É a armadilha já
registrada em `tests/test_estilo_da_tela.py::_o_que_o_navegador_recebe` ("sem esta limpeza o teste
mede a prosa dos comentários"), e ela reapareceu porque eu escrevi o comentário **antes** de rodar a
suíte. A correção foi tirar os comentários Jinja antes de procurar o cabeçalho — nos dois arquivos,
inclusive no que estava passando **por acidente**, pelo mesmo motivo.

## Resíduo declarado

1. **A tabela alinhada era melhor para varrer 142 linhas.** Colunas alinhadas comparam-se de
   relance; 142 cabeçalhos empilhados, não. A troca foi decidida pelo operador, e o ganho que a
   compensa é não ter duas listas dizendo a mesma coisa.
2. **O cabeçalho ficou mais denso**: nome, cM, veredito, identidade e a linha de sinais. Se ficar
   carregado demais na prática, o corte natural é o `rotulo-parentesco` — os dois selos são os que
   evitam abrir cartão a cartão.
3. **`parentesco-do-registro`** (o selo "não atribuível ao doador") mudou de lugar junto, e
   continua **inatingível** pela regra do adendo `016`. O ramo foi preservado com o comentário, e
   não apagado, pelo mesmo motivo declarado lá: a regra é reversível numa linha.
