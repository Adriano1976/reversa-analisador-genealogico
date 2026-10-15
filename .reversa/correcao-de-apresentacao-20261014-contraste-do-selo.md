# Correção — selo do cabeçalho ilegível (branco sobre creme)

**Data:** 2026-10-14
**Tipo:** defeito de **apresentação** — contraste. Não altera decisão de matching, caminho, cM,
veredito nem o texto do selo.
**Arquivos alterados:** `src/assets/app.css`, `src/templates/index.html`
**Teste novo:** `tests/test_estilo_da_tela.py::TestOContrasteDosSelos` (24 testes)
**Sonda:** `_reversa_bugs/_sondas-matching/contraste_dos_selos.py`

## O que o operador viu

No cartão **"Análise de conexão com Manoel da Silva Vieira"**, o selo do cabeçalho aparecia
**em branco**: *"a caixa está em branco, pois não consigo ler"*.

O texto estava lá — `compatível no cM, identidade impossível` —, mas em **branco sobre o creme
de `--aviso-bg`**.

## A causa não era a regra do selo

Era uma **interação de cascata**:

```css
.badge[class*="estado-"]{color:#fff}                    /* especificidade (0,2,0)  */
.estado-identidade_impossivel{ ... color:var(--danger) } /* especificidade (0,1,0) */
```

A primeira vence, e existe por um bom motivo: os quatro estados do confronto são **cor cheia com
texto branco**, e o comentário da própria folha registra que ela nasceu de um defeito de
contraste anterior (`#fd7e14` com texto branco). O prefixo `estado-` é **reivindicado** por ela.

O selo combinado do cabeçalho **não é um estado** — eu mesmo documentei isso ("os quatro
continuam quatro: `RF-19`, `BR-D-27`, ADR-15") — e mesmo assim o nomeei `.estado-identidade_impossivel`.
O nome foi o defeito: ele herdou o texto branco de uma família à qual não pertence.

## Medido

Sonda que resolve a **cascata** e não a regra isolada:

| Selo | Tema claro | Tema escuro |
|---|---|---|
| `estado-identidade_impossivel` (antes) | **1,11:1** — ilegível | 15,26:1 |
| `identidade-impossivel` (depois) | **6,03:1** | **6,99:1** |
| os outros 10 selos da tela | 6,03:1 a 13,90:1 | 6,11:1 a 13,90:1 |

Dois fatos que só a medição dá:

1. **no tema escuro o mesmo selo era legível** (15,26:1), porque lá `--aviso-bg` é escuro. Um
   teste de um tema só não pegaria o defeito;
2. **os outros dez selos estavam saudáveis.** Medi todos antes de mexer, para não "corrigir" o
   que não estava quebrado — o defeito era só este.

## A correção: o nome, e não a especificidade

Renomeado para `.identidade-impossivel`, irmão de `.identidade-a-confirmar` — mesma família de
aviso, mesmo par de cores de `.janela-impossivel`, e fora do prefixo reivindicado. Sem `!important`
e sem disputa de especificidade: a colisão deixa de existir por construção.

## O teste que teria pegado

`TestOContrasteDosSelos` calcula o contraste WCAG de **cada selo que o template emite**, nos
**dois temas**, resolvendo a cascata como o navegador: todas as regras que casam com o elemento,
vencendo a de maior especificidade e, no empate, a última. Um teste que lesse só a regra do selo
teria passado com a tela ilegível.

Confirmado por **falsificação**: aplicando o nome antigo em memória, o teste devolve 1,11:1 no
claro e reprova; no escuro passa — que é exatamente a assinatura do defeito.

Há ainda a guarda `test_o_prefixo_estado_e_reservado_aos_quatro_estados`, que impede outro selo
de aviso de voltar a usar o prefixo.

## Os dois erros do meu instrumento

A sonda mentiu duas vezes antes de servir, e as duas estão registradas no teste porque são
armadilhas fáceis de repetir:

1. **O parser engolia os comentários.** O regex de bloco capturava também o comentário que precede
   a regra, e o seletor virava `/* ... */ .badge[class*="estado-"]`, que não casa com nada. A
   primeira medição devolveu "?" para todos os selos — o instrumento mentia, não a folha;
2. **Seletor de elemento casava com tudo.** `body` e `h1,h2,h3` não têm classe, e a minha condição
   `all(... for ... in [])` é verdadeira para lista vazia: todo selo herdava a cor do `h5`. Foi o
   que fez a primeira tabela mostrar `--head` como cor de todos os selos.

E a **mesma armadilha do item 1 apareceu no teste**: a checagem de que `.estado-identidade` não
está na folha achou a **própria documentação do defeito** no comentário da folha. Corrigido
tirando os comentários antes das checagens de texto.

## Um achado sobre o ferramental, que custou tempo

O editor de arquivos me mostrou `def ...(self, folha: str):` na linha 298 de
`tests/test_estilo_da_tela.py`, mas o arquivo tinha `def ...(self, folha):`. Toda edição que
usava um trecho multi-linha como âncora falhava com "old_string não encontrado", enquanto as de
uma linha só funcionavam — o que me levou a suspeitar de fim de linha (e não era: o arquivo é LF).

O que resolveu foi **conferir a âncora contra o arquivo real** (`Get-Content`) antes de editar, e
passar a fazer inserções por splice ancorado no fim do arquivo. Fica registrado porque o sintoma
("o texto está lá, mas a ferramenta não acha") não aponta para a causa.

## E o servidor tinha o template em cache

Reiniciei o servidor por precaução e descobri que **não era precaução**: sem reiniciar, o Jinja
servia o template antigo — o selo continuava saindo com a classe velha e o CSS novo não tinha
efeito. A nota de sessão anterior dizia que HTML/CSS apareciam sem reiniciar; para o template,
não aparecem. Vale para a próxima mudança de tela.

## Verificação

- **934 testes, zero falhas** (910 → 934; 24 novos de contraste).
- Falsificação: com o nome antigo, o teste de contraste reprova no claro; com o novo, passa nos
  dois temas.
- Na tela servida pelo processo no ar: o selo chega como `class="badge identidade-impossivel"` com
  o texto `compatível no cM, identidade impossível`, e **0** selos com o prefixo antigo.
