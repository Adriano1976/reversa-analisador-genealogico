# Regression Watch: paginação dos Resultados das Análises de Conexão

> Identificador: `046-paginacao-dos-resultados`
> Data: `2026-10-22`
> O que este arquivo guarda: o que precisa **continuar verdadeiro** nas próximas extrações. Cada
> item é uma afirmação que a mudança desta feature tornou possível de perder em silêncio.

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|
| W001 | `src/templates/index.html` (guarda `dna_results`) + `requirements.md` §RN-04 | Os **68 cartões** continuam no documento em **qualquer** página; nenhum é removido do HTML | presença | A contagem de `details.cartao-do-resultado` no HTML for menor que o número de conexões da análise |
| W002 | `src/templates/index.html` (parágrafo `contagem-das-conexoes`) + `requirements.md` §RN-07 | A frase do topo conta a **análise**, nunca a página: "68 conexões analisadas" mesmo na página 3 | redação | A frase passar a dizer o tamanho da página (10, 20, 30) |
| W003 | `src/templates/index.html` (`abrirCartaoDoAlvo`) + `requirements.md` §RN-09 | Um `#resultado-N` na barra de endereços mostra a página que contém N **e depois** abre o cartão | presença (ordem) | `alvo.open = true` acontecer antes de `mostrarPaginaDo(alvo)` no script |
| W004 | `src/templates/index.html` (`<option selected>`) + `requirements.md` §RN-03 | O padrão é **10**, e as únicas opções são **10, 20 e 30**, com o padrão marcado no HTML | presença | `<option>` com outro `selected`, valores diferentes ou uma quarta opção |
| W005 | `src/templates/index.html` (botões de expandir/recolher) + `requirements.md` §RN-10 | "Expandir todas" e "Recolher todas" agem nos cartões da **página corrente** | redação | Os botões voltarem a usar `todosOsCartoes()` em vez de `cartoesDaPagina()` |
| W006 | `tests/test_icone_de_atalho.py` (`SHA_DA_TELA`) | A tela de entrada tem **46.264 bytes** e hash `05f2179adca5fa17b7073c472df308e6672753ce3d8f34e0e52f0c36b5d0934d` | presença | O hash ou o tamanho divergirem sem declaração em `_reversa_sdd/addenda/` |
| W007 | `src/assets/app.css` (guarda `[hidden]`) + `requirements.md` §RN-05 | O cartão fora da página usa o atributo `hidden`, e a folha tem uma regra própria que o faz valer | presença | A regra `details.cartao-do-resultado[hidden]` desaparecer, ou um cartão fora da página aparecer |
| W008 | `src/templates/index.html` (motor da paginação) + `requirements.md` §RN-06 | Trocar de página **não** dispara requisição: sem `fetch`, sem `XMLHttpRequest`, sem envio de formulário | presença | Qualquer chamada de rede no caminho da paginação — cada uma custaria uma análise inteira |

## Histórico de re-extrações

<!-- Preenchido pelo agente reverso quando /reversa rodar de novo. Vazio por enquanto. -->

## Arquivadas

<!-- Vazio por enquanto. -->

## Observações

Itens que **não** têm peso de regressão — são consequências declaradas ou limites conhecidos, e não
contratos que a extração deva cobrar:

- **A busca do navegador (Ctrl+F) só alcança a página corrente.** É consequência de `hidden`, não
  defeito: o texto está no documento, mas sai da busca. A resposta definitiva para "achar um nome"
  seria busca/filtro — outra feature. Registrado em `requirements.md` §10 e `roadmap.md` §9.
- **Nenhuma verificação em navegador real.** A suíte prende marcação, folha e ligação de script; não
  prova o clique. É o mesmo limite que o adendo `018` declarou para o recolhimento.
- **A densidade do controle em análise grande.** 142 cartões a 10 por página dão 15 números numa
  linha. Se incomodar na prática, o corte é a lista de números.
- **O rótulo "Expandir todas as análises" promete mais do que faz.** A decisão de 2026-10-22 foi
  manter o rótulo; a diferença está registrada em `requirements.md` §10.
