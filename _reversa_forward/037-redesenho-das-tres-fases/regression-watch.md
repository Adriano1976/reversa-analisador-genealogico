# Regras sob vigilância: Redesenho das três fases da tela de entrada

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Base: `legacy-impact.md` desta feature
> Regra de leitura: `presença` = a regra tem de estar no código; `redação` = o texto tem de ser o mesmo; `ausência` = a coisa **não** pode existir; `confidência` = a fonte foi rebaixada.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `tela-de-entrada/requirements.md#RF-22` | A tela de entrada tem **três fases** na barra lateral, iguais nos dois estados (sem árvore e com árvore aberta) | `presença` | Voltarem as duas abas horizontais, ou a fase 1 sumir quando há árvore aberta |
| W002 | `tela-de-entrada/requirements.md#RF-21` | As fases 2 e 3, sem árvore, não oferecem campo de busca/análise e apontam para a fase 1 | `presença` | Aparecer `person1_name`, `root_name`, `type="file"` ou `<select>` sem árvore aberta |
| W003 | `tela-de-entrada/contracts.md#2.1` | A tabela da fase 1 mantém as seis colunas, `Abrir` só no disponível e `Apagar` em todos | `presença` | Coluna sumir; `Abrir` aparecer em item indisponível |
| W004 | `requirements.md#RN-15` | Os contadores mostram **apenas** total de árvores e quantas estão disponíveis | `presença` | Entrar número de "prontas", "cliques" ou qualquer métrica que a aplicação não calcule |
| W005 | `requirements.md#RN-10` | Os nomes viajam num bloco `application/json`, e a `<datalist>` não existe | `ausência` | `<datalist>` ou `gedcom_names` reaparecerem no documento |
| W006 | `combobox` (novo) | Um nome com `</script>` **não** fecha o bloco JSON; o bloco continua sendo JSON válido | `presença` | O bloco cortar no primeiro fechamento de tag, ou um `<` cru aparecer dentro dele |
| W007 | `requirements.md#RN-13` | O combobox declara `role="combobox"`, `aria-controls="lista-de-nomes"`, lista `role="listbox"` e usa `aria-activedescendant` | `presença` | Algum dos atributos sumir, ou o campo virar `select` |
| W008 | `requirements.md#RN-11` | Os literais congelados continuam idênticos: rótulos das fases, campos, botões e mensagens | `redação` | Qualquer um dos oito rótulos mudar de texto |
| W009 | `addenda/011` (`RN-19`) | O caminho de volta continua em `href="/"`, rotulado `escolher outra árvore`, agora na caixa de status da fase 1 | `presença` | O link virar `action`, perder o rótulo ou voltar a aparecer acima das fases |
| W010 | `addenda/036` | A área de resultados (cartão em três faixas, barra lateral, selos) não é alcançada pela mudança | `ausência` | Qualquer regra nova de `.fases-da-tela` alcançar `details.card.cartao-do-resultado` |
| W011 | `tests/test_icone_de_atalho.py` | `SHA_DA_TELA` = `794711aa…`, 38.484 bytes, medido com pasta vazia | `presença` | O hash mudar sem declaração em `_reversa_sdd/addenda/` |

## Observações (sem peso de regressão)

- **OBS-01.** O **comportamento executado** do combobox (abrir ao digitar, manter o foco, `Esc` fechar) **não** é coberto por teste: o projeto não tem navegador headless nem executor de JS (`roadmap.md` `D-14`). O checklist manual está no `onboarding.md`; uma re-extração futura deve tratar isso como limitação declarada, não como regra garantida.
- **OBS-02.** O teto de **50 opções** e o rodapé "mostrando 50 de N" foram decididos por estimativa de tamanho de lista, não por medição com um GEDCOM real de dezenas de milhares de nomes.
- **OBS-03.** O filtro do combobox ignora acento e caixa (`normalize('NFD')`). É conveniência de tela: **não** altera a normalização do servidor (`core/name_normalization.py`), e nenhuma regra de matching depende dele.
- **OBS-04.** A navegação entre fases reusa o componente de abas; as setas ↑/↓ ganharam um handler próprio porque o plugin trata apenas as horizontais. Se o Bootstrap mudar esse comportamento, o handler continua funcionando, mas pode ficar redundante.

## Histórico de re-extrações

## Arquivadas

## Atualização 2026-10-20 (emenda `E001`)

- **`W011` passa a valer com `c5fb4ff7…` (38.476 bytes).** A emenda mudou a masthead, que faz parte de `GET /`. O valor anterior (`794711aa…`, 38.484 bytes) valeu entre a entrega e a emenda, e está registrado em `evidence/depois/hash.txt`.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W012 | `addenda/011` (`RN-24`, emendada) e `recursos-da-tela#a-masthead` | A masthead tem **duas colunas** — texto à esquerda, arte à direita —, e a arte continua sendo o **primeiro** elemento do documento | `presença` | O texto voltar a ser centralizado em `row justify-content-center`/`col-lg-*`, ou a arte deixar de ser o primeiro elemento do bloco |

## Atualização 2026-10-20 (emendas `E003` a `E005`)

- **`W011` passa a valer com `ed4f8734…` (40.222 bytes).** A `E005` acrescentou os três blocos informativos ao documento; as emendas `E003` e `E004` foram só de folha e não moveram o hash.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W013 | `requirements.md#emendas` (`E005`) | A tela tem a faixa de três blocos informativos entre a linha divisória e o painel das fases, com os textos `01 Carregar árvore GEDCOM`, `02 Encontrar conexão documental` e `03 Cruzar com evidência genética` | `presença` | A faixa sumir, mudar de lugar (entrar dentro do painel ou depois dele) ou virar navegação clicável |
| W014 | `requirements.md#emendas` (`E003` e `E004`) | O cabeçalho de fase ocupa a largura inteira e os rótulos dos campos começam na mesma linha | `presença` | O cabeçalho voltar a quebrar em duas linhas no desktop, ou o rótulo da direita nascer mais baixo que o da esquerda |

## Atualização 2026-10-20 (emendas `E006` e `E007`)

- **`W011` passa a valer com `3bac6c24…` (42.293 bytes).** A `E006` acrescentou as abas e o script de sincronia ao documento. A `E007` foi só de folha e não moveu o hash.

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W015 | `requirements.md#emendas` (`E006`) | Existem **dois controles** (`role="tab"`) para cada uma das três fases, e um script iguala `.active` e `aria-selected` entre eles a cada troca | `presença` | Um dos controles sumir, ou os dois ficarem `aria-selected="true"` ao mesmo tempo |
| W016 | `requirements.md#emendas` (`E007`) | As abas ficam na coluna do conteúdo, ao lado da barra lateral, e não atravessando acima dela | `presença` | As abas voltarem a `grid-column:1 / -1`, ou a barra lateral começar abaixo delas |

## Atualização 2026-10-20 (emenda `E008`)

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W017 | `requirements.md#emendas` (`E008`) | A fileira de abas **não** é contêiner de rolagem: não tem `overflow-x:auto` nem `nowrap`, e quebra em vez de rolar | `ausência` | `overflow-x:auto`/`flex-wrap:nowrap` voltarem a `.abas-das-fases`, e a barra reaparecer na fileira |

## Atualização 2026-10-20 (emendas `E009` e `E010`)

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W018 | `requirements.md#emendas` (`E009`) | A arte da masthead fica dentro de uma caixa com fundo, borda, raio de 16 px e sombra, nos dois temas | `presença` | A caixa sumir, ficar sem sombra, ou a arte voltar a flutuar sobre o fundo do cartão |
| W019 | `requirements.md#emendas` (`E010`) | Títulos em `Cormorant Garamond` e texto em `Manrope`, com `Georgia` e `system-ui` na pilha de fallback | `presença` | As famílias mudarem sem declaração, ou a pilha de fallback ser removida (o app ficaria sem fonte se o CDN não responder) |
| W020 | `requirements.md#emendas` (`E010`) | A troca de tipografia alcança a área de resultados, e isso é **declarado** — não é regressão da `RN-14` | `confidência` | Alguém tratar a fonte nova dos resultados como defeito, ou a `RN-14` ser lida como "nenhuma mudança visual de qualquer tipo" |

## Atualização 2026-10-20 (emendas `E011` e `E012`)

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W021 | `addenda/022` (emendado) | O bloco "Observações do arquivo" nasce **fechado**, e continua recolhível com o mesmo título | `ausência` | O atributo `open` voltar ao `<details class="card observacoes-do-arquivo">`, ou o bloco deixar de ser recolhível |
| W022 | `requirements.md#emendas` (`E012`) | O resumo dos resultados é **um** parágrafo: contagem, sugestão e legenda juntas, sem `<br>` entre elas | `presença` | A legenda voltar a ser um `<p>` próprio, ou o `<br>` voltar no meio da frase |
| W023 | `addenda/017` (preservada) | Os avisos do arquivo continuam **fora** dos cartões — a `E011` mudou o estado inicial, não o lugar | `presença` | O bloco voltar para dentro de cada cartão |






