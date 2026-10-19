# 034 — Revisão dos descartes

> Feature: `034-revisao-dos-descartes`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `024` e `033`)

## 1. O problema, medido

Na análise com `..._V1_2_Tratado.ged` + `Famílias_Sergipanas.csv`, **364 dos 454 nomes do CSV
não viram cartão**. Eles caem em "Matches descartados" com um motivo técnico
(`score insuficiente ou conflito de sobrenome (given=46, final=81.5, …)`), sem que o operador
possa saber se o descarte foi acerto ou perda.

A pergunta que decide a feature: **quantos desses 364 têm, na árvore, alguém compatível com o
nome?** Medido em 2026-10-19 (`evidence/medicoes.md`):

| | Tratado | Adriano V2 |
|---|---:|---:|
| Nomes no CSV | 454 | 454 |
| Descartados | 364 | 446 |
| Com candidato plausível (prenome ≥ 85 + sobrenome em comum) | **76** | **15** |
| … e esse candidato **tem caminho** até o doador | **10** | **8** |
| … e o caminho **sobrevive à janela de vida** | **7** | **1** |

"Plausível" é condição **necessária**, não prova de que seja a mesma pessoa — é por isso que a
decisão final tem de ser humana.

## 2. O que a entrega faz

### RF-01 — O candidato vai para a lista dos descartados

Cada linha passa a mostrar os **três melhores** candidatos da árvore (nome, ano de nascimento,
`given`, `final`, `jacc`), além do nome do CSV, do kit, do cM e do motivo de hoje.

Três, e não um: no caso real `*Maria de Fátima Oliveira de Jesus`, o melhor colocado foi
*Angelica Maria De Jesus De Oliveira* (`given` 55) — pessoa errada —, e o candidato compatível,
*Maria de Fátima da Mata Oliveira* (n. 1966), ficou atrás. Com um candidato só, a tela mostraria
a pessoa errada e o operador não teria como saber.

### RF-01b — Compatível é diferente de "melhor avaliado"

"Compatível" é prenome parecido **e** sobrenome em comum — a condição que o operador consegue
julgar. Medido no GEDCOM real: dos **366** descartes, **281** têm algum candidato avaliado e
**76** têm um compatível. Os 281 entram como lista; os demais aparecem como "melhor avaliado",
em texto fraco, porque listá-los como parentes seria ruído com cara de resposta.

### RF-01c — A ordem é a do operador, não a da decisão

A decisão desempata por interseção de sobrenomes primeiro; para a tela isso enterra o candidato
certo atrás de homônimos de sobrenome. Medido: pela ordem da decisão, **50** descartes mostravam
um compatível; pela ordem do operador (compatível, prenome, nota), **76**.

### RF-02 — A promoção é uma ação do operador, nunca automática

Um botão "usar este candidato" cria o cartão e roda a análise normal (parentesco, veredito,
janela de vida, árvore sugerida). Nada é promovido por nota.

### RF-03 — O motivo continua visível

Promover não apaga o descarte: a linha passa a dizer que foi promovida, e o motivo original
fica no cartão como observação.

### RF-04 — Nenhum veredito existente muda

Os cartões já calculados não são recalculados. A promoção cria cartões novos.

## 3. O que a medição derrubou (e por que fica registrado)

- **Promover por nota.** O melhor candidato pode ser outra pessoa: no caso real do kit
  `TG8027863` ("Manoel Vieira da Silva"), a árvore Sandro escolheu **Adelina da Silva Vieira**
  (sobrenome idêntico, prenome 46) e recusou — a recusa estava certa.
- **Escolher entre homônimos como conserto.** Os **4** homônimos exatos "Manoel da Silva Vieira"
  da árvore Tratado nasceram em 1720, 1790, 1793 e 1845 (idades 306, 236, 233 e 181 em 2026):
  **todos** caem em janela impossível. Trocar de homônimo não recupera esse caso; os 7 casos
  recuperáveis são outros, com candidatos nascidos entre 1911 e 1995.
- **Relaxar a janela dos 122 anos.** Os 3 descartes que têm caminho mas não sobrevivem à idade
  são justamente os que a regra do adendo `016` existe para barrar.

## 4. Escopo

**Entra:** coluna do candidato na lista dos descartados; ação de promover um candidato; o cartão
promovido entra na análise normalmente.

**Não entra:** promoção automática; mudança de limiar de score; revisão dos que não têm
candidato plausível (288 na Tratado, 431 na Adriano V2 — não há o que revisar).

## 5. Critérios de aceite

- [ ] A lista dos descartados mostra o candidato e os três números de cada linha com candidato.
- [ ] Promover cria exatamente um cartão, com o `documentary` recalculado para aquele nó.
- [ ] Promover não altera contagem, veredito ou caminho de nenhum cartão existente.
- [ ] O motivo original continua legível depois da promoção.
- [ ] Nome sem candidato plausível continua mostrando só o motivo (sem botão).
