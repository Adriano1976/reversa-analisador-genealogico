# Mudança — a tabela do índice saiu; o cabeçalho do cartão é a lista

**Data:** 2026-10-14
**Tipo:** **apresentação**. Não altera decisão de matching, caminho, cM, veredito, contagem de
cartões nem ordem de apresentação.
**Adendo:** `_reversa_sdd/addenda/019-a-tabela-do-indice-saiu.md`
**Arquivos alterados:** `src/templates/index.html`, `src/assets/app.css`
**Testes reescritos:** `test_estado_do_resultado.py`, `test_identidade_do_match.py`,
`test_janela_de_vida.py`, `test_cartoes_recolhiveis.py`, `test_estilo_da_tela.py`
**Servidor:** reiniciado (PID 18112) e verificado com a análise real de 142 cartões

## O que o operador disse

> *"Já que temos essa lista criada, não precisamos mais desse formato que ainda ficou porque a
> lista com o novo recurso já é o suficiente."*

Certo, e o motivo é **consequência do adendo `018`**: enquanto os cartões nasciam todos abertos, a
tabela era a única visão geral. Com os cartões recolhíveis passou a haver **duas listas de
resumos** — a tabela e a pilha de cabeçalhos —, e a coluna *Confrontação* repetia o selo do
cabeçalho.

## O que não podia sumir junto

Medido antes de remover: **duas colunas existiam só na tabela**, e o próprio template registrava
por quê — *"aparece na LISTA para o operador não precisar abrir 62 cartões para achar as conexões
em que a identidade não fecha"*.

| Coluna | Situação | Destino |
|---|---|---|
| Match, cM, Confrontação, Identidade | duplicadas no cabeçalho | — |
| **Parentesco no GEDCOM** | só a tabela | → `.rotulo-parentesco` no cabeçalho |
| **Janela de vida** | **só a tabela** | → selo `janela-*` no cabeçalho |
| **Profundidade** | **só a tabela** | → selo `profundidade-*` no cabeçalho |

Remover a tabela sem realocar isso teria trocado uma duplicação por uma perda. As três subiram para
uma segunda linha do cabeçalho, que é o `<summary>` do cartão: aparecem **com o cartão fechado**.

`<span>` e não `<div>` nessa linha: um `div` fecharia o `card-header` cedo para o extrator de teste,
e o teste passaria a medir um cabeçalho truncado.

## O acoplamento realocado

`#indice` era o alvo do link "**Voltar**". O alvo passou a ser o título `#resultados`. Os dois
nascem em pontos separados do template, e renomear um só não levanta erro — o link apenas deixa de
ter alvo. O par continua preso por teste, com prova de sensibilidade.

## Verificação

| | |
|---|---|
| Suíte | **1000 passou, 9 pulados**, exit 0 |
| `SHA_DA_TELA` | **inalterado** — a tabela estava dentro da guarda dos resultados |
| No servidor, 142 cartões | `indice-resultados` **0**; 142 `cabecalho-sinais`; 142 `Voltar` → `#resultados`; 1 `id="resultados"` |
| Página | 7.369.558 → **7.175.897** bytes |

## O erro que a verificação pegou

`test_o_sinal_de_janela_esta_no_cabecalho_do_cartao` **falhou** depois da mudança: o comentário que
eu acrescentei ao template cita `<div class="card-header">` e `</div>` **em prosa**, e o regex do
teste casou ali dentro — medindo a documentação em vez do documento. É a armadilha já registrada em
`test_estilo_da_tela.py::_o_que_o_navegador_recebe`, e reapareceu porque escrevi o comentário antes
de rodar a suíte. Corrigido tirando os comentários Jinja antes de procurar o cabeçalho, **nos dois
arquivos** — inclusive no teste que estava passando por acidente pelo mesmo motivo.

## Resíduo

1. Colunas alinhadas varrem 142 linhas melhor do que 142 cabeçalhos empilhados; a troca foi
   decidida pelo operador, e o ganho é não ter duas listas dizendo a mesma coisa.
2. O cabeçalho ficou mais denso. O corte natural, se incomodar, é o `rotulo-parentesco` — os dois
   selos são os que evitam abrir cartão a cartão.
3. `parentesco-do-registro` mudou de lugar junto e continua **inatingível** pela regra do adendo
   `016`; o ramo foi preservado com o comentário, porque a regra é reversível numa linha.
