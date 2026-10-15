# Regra nova — a janela de vida veta o parentesco

**Data:** 2026-10-14
**Tipo:** **regra de negócio**, decidida pelo operador depois de a consequência ter sido medida.
**Declaração formal:** `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`
**Arquivos alterados:** `src/core/dna_analysis.py`, `src/core/documentary_relationship.py`,
`src/core/janela_de_vida.py`, `src/templates/index.html`,
`tests/test_profundidade_do_caminho.py`, `tests/test_janela_de_vida.py`, `README.md`

> Este é o **log de trabalho**. A declaração que autoriza a mudança — inclusive o efeito na
> coluna `documentary_status` do histórico — está no adendo `016`.

## A regra

> *"SE na Janela de vida a idade for > 122, a pessoa será tratada como 'Parentesco documental não
> encontrado' com todas as regras aplicadas para esse tipo de grupo e desconsiderar o diagrama."*

Implementada no núcleo: quando `janela == IMPOSSIVEL` **e** existe caminho, o documental é
substituído pela forma do grupo e o diagrama não é montado. `suspeita` (105–122) continua apenas
avisando; `sem_data` não é impossível.

A forma do grupo **não foi copiada**: foi extraída para `documental_nao_encontrado`, que
`documentary_relationship` já usava no ramo sem caminho. As duas razões de apresentar um cartão
assim saem com a mesma forma, palavra por palavra — duas cópias divergiriam na primeira correção
de texto.

## O que eu já tinha medido, e o que o operador decidiu

| | |
|---|---|
| Alcança | 3 de 62 (`TG8027863`, `ZC1171551`, `ZL6373425`) |
| A árvore tem o caminho | **Sim** — 11, 12 e 10 meioses |
| O que a tela passa a afirmar | *"Nenhum caminho genealógico foi encontrado"* — **inexato sobre a árvore** |
| Perde | A única comparação de cM da análise e 1 dos 5 cartões do mesmo ancestral |

Apresentei isso três vezes, com medição. O operador decidiu mesmo assim, e a decisão é dele — é o
projeto dele. O que fiz foi implementar fielmente e **não destruir o dado**: o parentesco vetado
vai para `documentary_do_registro`, fora da tela.

## A consequência que ninguém pediu — e a mais interessante

O selo combinado `compatível no cM, identidade impossível`, que o adendo `015` criou para resolver
a contradição **por rótulo**, deixou de ser emitido. Não porque foi removido: ele exigia uma
comparação de cM que agora não acontece. **A regra do `016` resolve na raiz o que o `015` resolvia
com um rótulo.**

Pela mesma razão ficaram inatingíveis o bloco de veredicto do doador e o selo
`não atribuível ao doador` no índice. Os três continuam no código, **declarados como inatingíveis**
nos comentários do template, e um teste prende que não aparecem. Apagá-los esconderia o que uma
reversão teria de restaurar.

## Duas frases que a regra tornou falsas, e o que fiz com cada uma

1. **O aviso de idade terminava com** *"O parentesco abaixo é o do registro escolhido, e não pode
   ser lido como o do doador"* — e **não há parentesco abaixo**. Trocado por *"Por isso este cartão
   não apresenta parentesco documental"*, que é literalmente verdadeiro e não afirma parentesco. O
   teste que prendia a frase antiga foi reescrito com o motivo.
2. **O aviso `sem_caminho`** diz *"Nenhum caminho subindo por pais liga as duas pessoas dentro do
   teto de 20 iterações"* — que, para os cartões vetados, também não aconteceu. **Fica**: é parte
   de "todas as regras do grupo", e está declarado como dívida 2 do adendo `016`.

## Um erro meu no caminho

Ao anexar a classe de testes nova, **trunciei o arquivo no meio**: escrevi `texto + "\n"` em vez de
`texto + classe`, apagando a classe antiga sem pôr a nova no lugar. O sintoma foram 7 falhas de
teste apontando para métodos que já não existiam. Corrigido anexando a classe em passo separado —
e a lição é a mesma do modo `append` de mais cedo: quando o script lê, transforma e escreve,
**confira o que foi escrito**, não o que se pretendia escrever.

## Verificação

- **955 testes, zero falhas** (955 antes e depois: 12 testes reescritos, nenhum a mais).
- Medido no HTML servido pelo processo no ar, nos 62 cartões:

```
"Parentesco documental não encontrado" .. 108   (54 cartões × 2)
diagramas .............................   8   (era 11)
"não apresenta parentesco documental" ..  16   (8 impossíveis × 2)
"o parentesco abaixo" ..................   0   (frase obsoleta eliminada)
"veredicto-do-doador" / selo do índice ..  0 / 0
```

- Os 3 cartões alcançados: `nao_encontrado=True`, `grafo=False`, com o aviso de idade preservado.
- O cartão da Eline (com caminho, sem idade impossível) continua **igual**.
- O `SHA_DA_TELA` **não** mudou: as alterações de template foram comentários Jinja, que não chegam
  ao HTML, e o `<script>` não foi tocado.
