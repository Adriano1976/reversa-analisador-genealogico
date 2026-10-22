# Regression watch: renomear o filtro de segmentos

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/templates/index.html`, seção 2 (bloco `endogamia-bloco`) | O título de queda do bloco é **`Filtro de segmentos (<limite> cM)`**, e o limite vem de `result.endogamia.limiares.segmento` | presença | o título volta a dizer `Filtro de endogamia`, ou o template passa a ter um `10` literal |

## Observações (sem peso de regressão)

- 🟢 **Os rótulos estruturais não mudaram e não devem mudar com esta emenda:** o ramo estrutural do
  título continua lendo `result.endogamia.selo.rotulo` (`Sinal estrutural na árvore` sem caminho
  documental, `Endogamia estrutural` com ele). A decisão mora em
  `core/dna_analysis._selo_da_endogamia`, não no template.
- 🟢 **Os demais rótulos do conjunto continuam iguais:** `Filtro: N seg. abaixo de 10 cM` (selo do
  cabeçalho) e `Evidência fraca`. Renomear o título do bloco não os alcança.
- 🟡 A maquete `_reversa_sdd/analise-planilhas-dna-sergipe/simulacao-sem-familysearch.html` mantém o
  rótulo antigo de propósito: ela é retrato do estado anterior à feature 040, não documentação do
  comportamento atual.

## Histórico de re-extrações

*(vazio — preenchido pelo agente reverso quando `/reversa` rodar de novo)*

## Arquivadas

*(vazio)*
