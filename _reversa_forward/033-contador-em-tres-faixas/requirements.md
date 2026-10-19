# 033 — Contagem em três faixas

> Feature: `033-contador-em-tres-faixas`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `016` e `031`)

## 1. O problema, medido

A frase do topo de "Resultados das Análises de Conexão" dizia:

> `90 conexões analisadas: 6 com caminho genealógico no GEDCOM (6 com identidade ambígua) e 84 apenas com evidência genética (sem caminho no GEDCOM).`

"Sem caminho no GEDCOM" é **falso para 3 das 84**. Quando a janela de vida torna o
parentesco impossível, a regra do adendo `016` troca o parentesco apresentado por "não
encontrado" e guarda o original em `documentary_do_registro`. A tela conta pelo
apresentado; a árvore, pelo original.

Medido no GEDCOM real (`..._V1_2_Tratado.ged` + `Famílias_Sergipanas.csv`, raiz
`adriano`, 2026-10-19):

| Medida | Valor |
|---|---:|
| Cartões | 90 |
| Caminhos que a árvore tem | 9 |
| Apresentados como caminho | 6 |
| Recusados pela janela de vida | 3 |
| Cartões com árvore sugerida na tela | 0 |

O custo não é cosmético: a frase manda o operador procurar **registro faltando** onde o
trabalho é procurar **homônimo** — exatamente o custo que o adendo `016` já descrevia.

## 2. O que a entrega faz

Três faixas que fecham a conta, mais a árvore sugerida como **atributo**:

```
90 conexões analisadas: 6 com caminho genealógico no GEDCOM (6 com identidade
ambígua), 3 com caminho documental recusado pela idade do match e 81 apenas com
evidência genética (sem caminho no GEDCOM).
N conexões mostram árvore sugerida — gerações virtuais que não estão no GEDCOM.
```

### RF-01 — Três faixas mutuamente exclusivas

`com caminho` (`documentary.path`) + `recusados` (`documentary_do_registro.path` sem
`documentary.path`) + `sem caminho` (nenhum dos dois) = total de cartões.

### RF-02 — A faixa dos recusados só aparece quando existe

Com zero recusados a frase volta a ter duas faixas: não se anuncia uma ausência que não
informa.

### RF-03 — Árvore sugerida é atributo, não faixa

Contada em frase própria, e **com a mesma condição do bloco do cartão**
(`sugestao_resumo` **e** `sugestao_mermaid`). Somá-la ao "com caminho" inflaria o número
sem que exista um nó documental novo.

### RF-04 — A frase diz que a geração sugerida não está no GEDCOM

Sem a ressalva, o operador leria hipótese como parentesco documentado.

### RF-05 — O cartão não muda

A contagem conta o que a árvore tem; o cartão continua apresentando "não encontrado",
com a regra do adendo `016` intacta.

## 3. Fora de escopo (e por quê)

- **Contar caminho sugerido como caminho no GEDCOM.** Inflaria o número e destruiria o
  único sinal honesto da tela. A cirurgia consome caminho; ela não cria.
- **Atacar os descartados.** Na mesma medição, 366 nomes foram rejeitados antes de
  qualquer trabalho de grafo — 274 por score de sobrenome, 68 por nome sem sobrenome, 11
  por sobrenome lido como prenome, 7 por sobrenome sem interseção, 5 por sobrenome
  inexistente no GEDCOM, 1 por sobrenome curto. É o reservatório real (4× os cartões),
  mas é motor de identidade, não tela: feature própria.
- **Mexer no núcleo.** Todo o dado necessário já viaja no dicionário do resultado.

## 4. Critérios de aceite

- [x] As três faixas somam o total em qualquer combinação de cartões.
- [x] Cartão recusado não conta como "com caminho" nem como "sem caminho".
- [x] Sem recusados, a faixa não aparece e a conta continua fechando.
- [x] Sugestão sem desenho não é contada (a frase não promete o que a página não mostra).
- [x] Singular e plural corretos na frase da sugestão.
- [x] O cartão recusado continua dizendo "Parentesco documental não encontrado".

## 5. Medições que sustentam as decisões

Ver `evidence/medicoes.md` — inclui a distribuição de vereditos e de sugestões nas quatro
árvores ativas, e a sonda reprodutível (`evidence/_probe_sugestao.py`).
