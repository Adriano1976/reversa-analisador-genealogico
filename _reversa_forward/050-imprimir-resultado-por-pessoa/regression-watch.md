# Regression watch: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `src/templates/index.html`, controles do cartão | Cada cartão de resultado tem um `.imprimir-conexao` com `data-imprimir="resultado-N"` e nome acessível que **nomeia a pessoa** daquele cartão | presença | Botão ausente, "Imprimir" genérico, ou `aria-label` sem o nome |
| W002 | `src/templates/index.html`, script do clique | O comando mora dentro do `summary` e o handler chama `preventDefault` e `stopPropagation` | comportamento | Acionar o comando abre ou fecha o cartão junto |
| W003 | `src/templates/index.html`, início do corpo do cartão | Cada cartão traz `.identificacao-da-impressao` com as **referências armazenadas** (árvore e CSV, `chave__rótulo.ext`) e a raiz digitada, mais um `<time class="quando-da-impressao">` vazio | presença | Identificação ausente, ou trocada pelo rótulo visível da lista |
| W004 | `src/templates/index.html`, ramo `{% if dna_results %}` | `#area-de-impressao` existe **com resultado** e **não existe** na tela de entrada vazia | ausência | O contêiner aparece em `GET /` vazio — a tela de entrada ganha marcação sem ter cartão |
| W005 | `src/assets/app.css`, `@media print` | `#area-de-impressao{display:none}` na tela e `body.imprimindo > *:not(#area-de-impressao){display:none}` no papel | presença | A folha imprime a página inteira, ou o contêiner fica visível na tela |
| W006 | `src/assets/app.css`, `@media print` | Os selos saem com fundo branco e tinta escura (contorno), porque o navegador não imprime fundos | presença | Selo branco sobre branco — texto ilegível no papel |
| W007 | `src/assets/app.css`, `@media print` | `.folha-do-diagrama{break-before:page}` e `tr{break-inside:avoid}` | presença | Desenho cortado no meio, ou linha de tabela dividida entre folhas |
| W008 | `src/templates/index.html`, script da impressão | A rotina espera o SVG com `MutationObserver` (teto de 2 s) e restaura o estado no `afterprint` | comportamento | Desenho em branco na folha, ou cartão aberto depois de fechar o diálogo |
| W009 | `tests/test_icone_de_atalho.py` | `SHA_DA_TELA = df6fc12a03609373936f0f3ba2fd6ed3c14da3aada5baf437bf98349d20630c6` (51.064 bytes) | presença | Hash antigo (`5fc0b929…`), ou tela vazia diferente sem mudança declarada |
| W010 | `_reversa_sdd/domain.md#5`, literais de tela | Nenhum literal existente mudou: título da conexão, "Voltar", selos, "Expandir todas"/"Recolher todas" e a contagem seguem idênticos | redação | Texto de tela alterado por engano durante a impressão |

## Observações

Itens 🟡 que **não** têm peso de regressão, mas a re-extração deve conhecer:

- **O momento da impressão é preenchido pelo navegador.** O `<time>` nasce vazio e recebe
  `new Date()` no clique; por isso a `RN-03` do requirements foi ajustada em 2026-10-26
  para exigir "mesmo conteúdo e mesmos valores", admitindo que o carimbo de hora varie.
- **A impressão não é auditada** (`RN-08`): não há requisição, então não há linha na
  trilha da feature 049. É ausência deliberada, não esquecimento.
- **O contêiner é movido para o fim do `<body>` no primeiro uso.** É mecanismo, não
  contrato: a re-extração pode descrevê-lo de outro jeito, desde que a isolação
  (`body.imprimindo`) continue escondendo a página.
- **A verificação em quatro navegadores é manual** e não é reproduzível por re-extração;
  o roteiro está em `onboarding.md#9`.
- **O botão depende do `loop.index`** do `for result in dna_results` para casar com o `id`
  `resultado-N`; renomear um dos dois quebra o `data-imprimir` sem erro visível.

## Histórico de re-extrações

Nenhuma re-extração registrada desde a entrega.

## Arquivadas

Nenhum item arquivado.
