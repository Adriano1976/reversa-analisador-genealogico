# Legacy impact: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Política de edição no momento da execução: `allowLegacyEdits: true`, com
> `allowedPaths` liberando `src/**` e `tests/**` — os únicos caminhos do legado que esta
> feature toca.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|-----------|------|-----------|---------------|
| `src/templates/index.html` | Tela de resultados (`_reversa_sdd/architecture.md#3`) | `delta-de-contrato-externo` | MEDIUM | O **corpo HTML** de `POST /` com `action=dna_analysis` ganha o botão por cartão, o bloco de identificação e o contêiner `#area-de-impressao`; o script da tela ganha a rotina de impressão. Método, `action`, campos, status e mensagens **não** mudam |
| `src/assets/app.css` | Folha de estilo (`_reversa_sdd/architecture.md#3`) | `componente-novo` | MEDIUM | Entra o bloco de impressão (isolação, papel claro, selos de contorno, folha do desenho, rodapé fixo) e o estilo do comando e da identificação na tela |
| `tests/test_impressao_do_resultado.py` | Suíte de testes | `componente-novo` | LOW | Arquivo novo: 30 testes prendem marcação, folha e ligação do script |
| `tests/test_icone_de_atalho.py` | Invariante de tela (`SHA_DA_TELA`) | `regra-alterada` | LOW | Nona medição declarada: `5fc0b929…` (46.477 bytes) → `df6fc12a…` (51.064, +4.587) |
| `tests/test_icone_de_atalho.py` | Invariante de tela (`SHA_DA_TELA`) | `regra-alterada` | LOW | Correção do registro acima: a nona medição fechou em `f49dd6da…` (51.117), depois do ajuste do seletor; a décima (`df702cbb…`, 51.150) veio da feature 051 |
| `src/templates/index.html` | Tela de resultados (`_reversa_sdd/architecture.md#3`) | `regra-alterada` | LOW | **E001**: o script troca o `document.title` durante a impressão, para o PDF sair como "Análise de conexão com <nome>", e devolve o original no `afterprint` |
| `tests/test_icone_de_atalho.py` | Invariante de tela (`SHA_DA_TELA`) | `regra-alterada` | LOW | **E001**, décima primeira medição: `df702cbb…` (51.150) → `386f2fef…` (51.601, +451) |

## 2. Diff conceitual por componente

**Tela de resultados.** O cartão ganha três nós: o `<button class="imprimir-conexao">` no
grupo de controles do cabeçalho, o `div.identificacao-da-impressao` no início do corpo e,
no documento, o `#area-de-impressao` ao fim do ramo `{% if dna_results %}`. O script
ganha a rotina de impressão: move o contêiner para o fim do `<body>`, abre o cartão, espera
o SVG do desenho (teto de 2 s), clona o cartão, abre os `details` do clone, move os
diagramas para `.folha-do-diagrama`, acrescenta o rodapé de origem e chama `print()`; o
`afterprint` desfaz tudo. **Nenhuma regra de domínio é avaliada de novo**: os valores
impressos são os que a análise já produziu.

**Folha de estilo.** O bloco novo é todo condicionado a `@media print` ou às classes da
feature. As regras de tela existentes não foram tocadas, exceto o cartão, que **não**
muda: o clone é que recebe a classe `cartao-em-impressao`.

**Testes.** O arquivo novo segue o caminho de produção (`POST` real com fixture sintética).
O invariante de tela foi atualizado por medição, com a origem do delta declarada no
comentário — o padrão das oito medições anteriores.

## 3. Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas:

- `BR-D-41` — ordem de apresentação documental primeiro, cM decrescente. O documento
  impresso preserva a ordem da lista; só a diagramação interna do cartão muda (`RN-07`).
- `BR-D-42` — mensagem final `"N conexões encontradas. M descartadas."`: intocada.
- `BR-D-65` — observações deduplicadas na ordem documental → genética → confronto → avisos.
- `BR-D-66` — o diagrama só é montado com caminho documental; é o que faz a impressão não
  reservar folha de desenho quando não há caminho.
- `RN-09` — a tela não muda: todos os literais existentes foram preservados, e o controle é
  aditivo.
- `RN-14` — aposentar move e nunca apaga; intocada.
- `RN-04` da feature 049 — a auditoria cobre ações de servidor; imprimir não gera evento e
  não ganha linha de auditoria (`RN-08`).

## 4. Modificadas

**Nenhuma regra 🟢 do `_reversa_sdd/domain.md` foi alterada ou removida.** O que muda é o
**documento** entregue no corpo do `POST` (delta de contrato externo) e o **invariante de
tela** mantido à mão em `tests/test_icone_de_atalho.py`. A distinção importa para a
re-extração: nenhuma regra de negócio precisa ser reescrita; o contrato de tela ganhou uma
superfície nova, que o adendo do `/reversa-sync` deve registrar.
