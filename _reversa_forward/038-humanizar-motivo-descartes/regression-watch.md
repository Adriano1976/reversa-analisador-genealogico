# Regression Watch: humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Para a próxima re-extração (`/reversa`): cada item abaixo é uma regra que **precisa continuar
> verdadeira** no código. Violação de item 🟢 é regressão; itens 🟡 moram em Observações.

## 1. Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `src/core/motivos_do_descarte.py:32` | Toda recusa por semelhança nasce de `diagnosticar()` com **uma** causa e um `codigo` estável do catálogo | presença | motivo montado por f-string dentro de `matching.py`, ou código fora de `TEXTOS` |
| W002 | `src/core/motivos_do_descarte.py` (`TEXTOS`) | Nenhuma frase do catálogo contém `given`, `final=`, `inter=`, `jacc` nem dígito | ausência | qualquer termo de máquina ou número voltando para a coluna Motivo |
| W003 | `src/core/motivos_do_descarte.py:detalhe_tecnico` | Toda recusa por semelhança carrega os quatro números rotulados (`prenome`, `nota`, `sobrenomes em comum`, `grafia do sobrenome`) | presença | `detalhe` vazio numa recusa de semelhança |
| W004 | `src/core/matching.py` (portões de aceite) | Nenhum limiar, peso ou ordem de avaliação muda: mesmos aceitos, mesmos descartes, mesmos cM e caminhos | comportamento | `tests/test_characterization_matching.py` vermelho, ou nome trocando de lado numa análise real |
| W005 | `src/core/matching.py` (veto do token do meio) | O veto só age **depois** de todos os portões passarem, com `nota >= 96`, `prenome >= 92`, `interseção >= exigida` e grafia ok | presença + comportamento | veto aplicado a um caso em que o aceite nunca existiu, ou diagnóstico acusando “nome do meio” sem veto |
| W006 | `src/core/motivos_do_descarte.py` (`diagnosticar`) | A precedência é fixa: nome do meio → sobrenomes de menos → grafia → prenome → semelhança geral | comportamento | o mesmo par de nomes recebendo causas diferentes entre execuções |
| W007 | `src/reporting/csv_de_descartes.py` (`CABECALHO`) | A planilha tem nove colunas, as oito primeiras com nome e posição da `035`, e BOM/`;`/vírgula decimal preservados | contrato | coluna faltando, renomeada ou fora de ordem; acento quebrado no Excel |
| W008 | `src/core/dna_analysis.py` (dict do descarte) | `motivo` é texto humano, `motivo_codigo` é do catálogo e `motivo_detalhe` só existe quando há números | contrato | chave ausente, ou `motivo` voltando a conter fórmula |
| W009 | `src/templates/index.html` (bloco dos descartados) | A célula Motivo mostra a frase; o detalhe técnico **não** vai para a tela, e o texto sob o download diz onde ele está | presença | números de volta na célula, ou a frase “Detalhe técnico” sumindo da tela |
| W010 | `src/ports/__init__.py` (`DescartadoDaAnalise`) | `reason_code` e `detail` existem com default vazio, e a persistência continua gravando **só** `reason` | presença | migração de schema por causa de redação, ou `reason` deixando de ser o texto |
| W011 | `src/core/motivos_do_descarte.py` (`NAO_ENCONTRADO`) | O caminho sem recusa continua produzindo `"não encontrado"` com código `nao_encontrado` | presença | descarte sem motivo nenhum |

## 2. Observações (confidência 🟡, sem peso de regressão)

- O código estável por causa (`RN-27`) é **inferido** como desejável: nasceu nesta feature, não de
  uma regra extraída do legado. Se uma re-extração mostrar que ninguém consome o código, ele pode
  ser removido sem regressão de domínio.
- Os dois campos novos da dataclass da porta **não são persistidos**. Isso é decisão declarada
  (`D-10`), não esquecimento: gravar causa no histórico exigiria migração por causa de redação.
- A redação das cinco frases é premissa revisável (`P-03`); mudá-la não é regressão, mas os testes
  de catálogo em `tests/test_motivo_humanizado.py` precisam acompanhar.

## 3. Histórico de re-extrações

| Data | Extração | Resultado |
|------|----------|-----------|
| — | — | — |

## 4. Arquivadas

| ID | Motivo do arquivamento | Data |
|----|------------------------|------|
| — | — | — |
