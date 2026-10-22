# Requirements: Renomear o filtro de segmentos no título do bloco

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Modo: express
> Pasta da extração reversa: `_reversa_sdd/`

## 1. Resumo executivo

O bloco da seção 2 que mostra a aritmética do cM depois do piso de 10 cM chama-se **"Filtro de
endogamia"** — nome que sugere um diagnóstico de endogamia que ele não faz: ele apenas descarta
segmentos abaixo de 10 cM e recalcula o total. Passa a se chamar **"Filtro de segmentos (10 cM)"**,
que nomeia o objeto e o limiar. Nada mais muda: o selo do cabeçalho, os rótulos estruturais, os
números e as frases continuam iguais.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#32-evidência-genética` | O filtro de 10 cM e a mitigação de endogamia **avisam, não corrigem**; o total bruto continua ao lado do recalculado | 🟢 |
| `_reversa_sdd/code-analysis.md#46-constantes-parâmetros-e-configuração` | `CM_MINIMO_SEGMENTO = 10.0` é critério do projeto; o número deve vir do dado, não do texto | 🟢 |
| `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md#por-que-a-razao-nao-separa` | `ADR-21`: endogamia avisa, não corrige — o bloco é aviso, e o título deve dizer do que | 🟢 |
| `src/templates/index.html` (bloco `endogamia-bloco`, seção 2) | O título cai no literal `Filtro de endogamia` sempre que não há sinal estrutural | 🟢 |
| `src/core/dna_analysis.py#_selo_da_endogamia` | "Endogamia estrutural" e "Sinal estrutural na árvore" são decisões do núcleo e **não** mudam aqui | 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — O título nomeia o filtro, não um diagnóstico.** O bloco que exibe total bruto, total após
   filtro, segmentos descartados e maior bloco passa a se titular **"Filtro de segmentos (10 cM)"**; o
   limite exibido vem de `result.endogamia.limiares.segmento`, e não de um literal no template. 🟢
   - Tipo: alterada (texto de tela).
2. **RN-02 — Os rótulos estruturais não mudam.** `Sinal estrutural na árvore`, `Endogamia estrutural`,
   `Evidência fraca` e `Filtro: N seg. abaixo de 10 cM` continuam exatamente como estão, e a lógica que
   escolhe entre eles fica intocada. 🟢
   - Tipo: preservada.

## 7. Critérios de Aceitação

- O bloco da seção 2, num cartão sem sinal estrutural, exibe **"Filtro de segmentos (10 cM)"**.
- A string **"Filtro de endogamia"** não aparece no HTML servido por nenhuma análise.
- Num cartão com sinal estrutural, o título continua sendo **"Sinal estrutural na árvore"** (ou
  "Endogamia estrutural", quando houver caminho documental).
- A suíte completa continua verde, e as contagens de cartões, cM, descartes e selos não mudam.

## Emendas
