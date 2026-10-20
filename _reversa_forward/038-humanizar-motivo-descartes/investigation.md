# Investigação: como dizer a causa de um descarte

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`

## 1. O problema, medido antes desta feature

A mensagem de recusa por semelhança nasceu no legado e sobreviveu à reescrita do núcleo:

```
score insuficiente ou conflito de sobrenome (given=100, final=88.25, inter=1/1, jacc=0.50)
```

Três defeitos, e nenhum é de estilo:

1. **Oferece duas causas e não diz qual.** "ou" é uma disjunção: quem lê não sabe se o problema foi
   a nota ou o sobrenome. O adendo `024` já mediu que, em **100%** dos 325 descartes com essa
   mensagem na árvore V2, a interseção mínima de sobrenomes foi cumprida — a metade "conflito de
   sobrenome" **nunca** era a causa literal.
2. **Não cita o portão que de fato recusou.** Existe um sétimo portão, a penalidade de token do
   meio, aplicada **depois** de todos os outros passarem: quando o nome do CSV tem uma parte que
   não existe na árvore, o aceite é desfeito a menos que a nota seja altíssima (`best_score >= 96`).
   Ele não aparece em número nenhum da mensagem.
3. **Fala em unidade de máquina.** `given`, `final`, `inter`, `jacc` são nomes de variável do
   scoring. O operador — e quem recebe a planilha — não tem como saber que `inter=1/1` é
   "sobrenomes em comum: 1, e era exigido 1".

O caso que o operador reportou é exatamente o (2): `given=100` (prenome idêntico), `final=88.25`
(alto), `inter=1/1` (exigência cumprida), `jacc=0.50` (grafia no limiar). Todos os portões de nota
passam; o que recusa é o veto do token do meio. A mensagem, porém, acusa "score insuficiente ou
conflito de sobrenome" — as duas coisas falsas.

## 2. Como a decisão funciona hoje (leitura do código)

`core/matching.py:avaliar_candidatos`, ramo do pool não vazio:

| # | Portão | Condição de aceite |
|---|--------|--------------------|
| 1 | interseção dupla com prenome genérico | `inter >= 2` E `jacc >= 0.67` E `nota >= 100` |
| 2 | interseção dupla | `inter >= 2` E `jacc >= 0.50` E `prenome >= 85` E `nota >= 80` |
| 3 | sobrenome quase igual | `inter >= 1` E `jacc >= 0.80` E `nota >= 86` |
| 4 | prenome forte | `prenome >= 90` E `nota >= 92` E `inter >= exigida` E `grafia ok` |
| 5 | prenome quase idêntico | `prenome >= 95` E `nota >= 88` E `inter >= exigida` E `grafia ok` |
| 6 | prefixo de sobrenome | prefixo de 3+ letras E `prenome >= 90` E `nota >= 86` E `inter >= 1` E `grafia ok` |
| 7 | **veto do token do meio** | se todo token do CSV fora prenome/sobrenomes não existe na árvore: só aceita com `nota >= 96` E `prenome >= 92` |

Antes dos portões há dois cortes secos: pool vazio (quatro causas do adendo `024`) e
`inter == 0` sem acerto de sufixo.

O portão 7 é o único que **desfaz** um aceite já obtido. Por isso ele é o primeiro a ser
diagnosticado: se ele agiu, nada mais é causa.

## 3. Alternativas avaliadas

| Alternativa | Por que não |
|---|---|
| **Reescrever só a string com um "ou" melhor** | Continua sem dizer a causa. O operador não ganha nada |
| **Remover os números e escrever "não é a mesma pessoa"** | Perde rastreabilidade: a `024` protegeu justamente isso, e quem confere o cálculo fica sem os valores |
| **Manter a fórmula e explicá-la num glossário** | O operador teria de traduzir a fórmula a cada linha, e a planilha sairia em outra ferramenta |
| **Traduzir cada variável no texto** (`prenome 100, nota 88,25, sobrenomes 1 de 1, grafia 0,50`) | É o detalhe técnico, não o motivo: quatro números seguem sendo quatro números. Serve como **segunda** informação, jamais como a primeira |
| **Derivar a causa da ordem dos `elif`** | A cadeia é uma disjunção: com nada aceito, vários portões falharam. "O primeiro que não passou" muda de sentido à primeira alteração de limiar |
| **Código da causa no banco, com migração** | Redação não justifica migração de schema; e o histórico deve registrar o que foi dito na época |

## 4. O que foi decidido, e a lógica

**Uma causa, por precedência, do mais acionável ao menos acionável.** A ordem responde à pergunta
que o operador faz ao ler a linha: "o que eu posso conferir?".

1. `nome_do_meio_ausente` — "confira se esse nome do meio está na árvore"
2. `sobrenomes_em_comum_insuficientes` — "confira se falta um sobrenome no cadastro"
3. `sobrenome_pouco_parecido` — "confira a grafia do sobrenome"
4. `prenome_diferente` — "confira se é a mesma pessoa com outro prenome"
5. `semelhanca_insuficiente` — "não há o que conferir: o conjunto do nome não bate"

As frases evitam três coisas de propósito: termo técnico (`score`, `jaccard`, `interseção`),
número solto e promessa ("provavelmente", "quase"). O motivo diz **o que aconteceu**, não o que o
operador deve fazer — a ação fica na leitura de quem conhece o cadastro.

## 5. Precedentes internos consultados

- `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md` — a primeira vez que este projeto
  trocou um motivo técnico por quatro motivos humanos. Fixou a regra que vale aqui: **a decisão não
  muda, só o texto**; e mediu que a troca de texto é barata justamente por isso.
- `_reversa_sdd/addenda/034-revisao-dos-descartes.md` — o bloco dos descartados passou a mostrar
  candidatos porque "um motivo técnico não diz ao operador se o descarte foi acerto ou perda".
- `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md` — a planilha é o caminho real de
  trabalho; o formato (BOM, `;`, decimal com vírgula, guarda contra fórmula) é contrato.
- `src/templates/index.html:1644` — o texto atual sob o botão de download já explica o que a coluna
  Motivo separa; ele passa a dizer onde estão os números.

## 6. Fontes externas

Nenhuma. O problema é de redação interna e a solução não depende de biblioteca, padrão de mercado
ou referência externa — por isso este documento não cita URL.
