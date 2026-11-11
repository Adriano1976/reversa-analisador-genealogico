<!--
Requirements da feature 058 — Detalhamento dos segmentos compartilhados.
Gerado por /reversa-requirements a partir do pedido do operador (2026-11-11) e do _reversa_sdd/.
Máximo de três [DÚVIDA] no documento inicial (seção 10).
-->

# Requirements: Detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Uma **tabela de segmentos** dentro do cartão "Regiões compartilhadas": uma linha por segmento que
forma uma região, com cromossomo, posição inicial e final, tamanho em Mb (megabases), cM
(centimorgans), o kit e o nome do match, e o desfecho documental da região. Ganha busca por texto,
filtro por cromossomo, contador de linhas exibidas, paginação e — ao clicar na linha — o destaque da
faixa correspondente no ideograma. A tabela **lê a mesma projeção** que o ideograma e a lista já
usam: não relê o CSV, não soma cM e não muda nenhum veredito.

**Região compartilhada**, neste documento, é o conjunto de matches que compartilham a mesma faixa de
um cromossomo **com o kit do arquivo** — o kit é o identificador do match no CSV. **Segmento de
região** é o trecho do cromossomo que aquele match contribui para a região.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/addenda/056-regioes-compartilhadas.md` | A região nasce do CSV de matches, com piso de 10 cM como filtro; o bloco já tem ideograma (uma faixa por região) e lista de regiões | 🟢 |
| `_reversa_sdd/addenda/057-distribuicao-por-cromossomo.md` | O gráfico de barras é agregado por cromossomo: **não tem marca por segmento**, então não é a âncora do clique | 🟢 |
| `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | Filtrar e paginar é **camada de apresentação** sobre o HTML já servido; paginar no servidor reexecutaria a análise (12 a 31 s) | 🟢 |
| `_reversa_sdd/data-dictionary.md#5.2` | `Segmento` carrega `cromossomo`, `inicio`, `fim`, `cm` e `snps` | 🟢 |
| `_reversa_sdd/domain.md#3.2` | O cM é evidência por segmento e nunca somado | 🟢 |
| `src/core/regioes.py` (`RegiaoCompartilhada.segmentos`, `.membros`) | Cada região guarda os segmentos escolhidos e o par (kit, nome) de cada membro | 🟢 |
| `src/assets/app.css` (`.card:target`) | A tela já usa `:target` para destacar um elemento por âncora, sem JavaScript | 🟢 |
| `.reversa/principles.md#I` | Dado real de DNA não entra no versionamento; teste usa fixture sintética | 🟢 |

**Sobre o pedido original (2026-11-11).** O operador pediu a tabela "abaixo do gráfico Mapa de
Segmentos Genômicos", com colunas **Kit 1** e **Kit 2**, "tema escuro" e "âmbar/laranja idênticos aos
pontos do gráfico". Essa captura é de outro produto: este analisador não tem o gráfico de dispersão
de segmentos, e o dado do CSV de matches **não tem segundo kit** — cada match compartilha a faixa com
o kit do arquivo, não com outro match (decisão da 056, que removeu o arquivo de pares). As três
adaptações estão declaradas em `RN-02`, `RN-06` e `RN-07`.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador genealogista | Conferir, segmento por segmento, o que sustenta uma região: quem é o match, qual faixa, quantos cM | Abre o bloco, filtra pelo cromossomo 7 e lê as linhas antes de decidir se vale abrir a região |
| Operador revisando o arquivo | Achar um kit específico no meio de centenas de segmentos | Digita o nome do membro na busca e vê só as linhas dele |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A tabela é **leitura derivada da mesma projeção** de regiões que o ideograma e a lista usam; não relê o CSV, não refaz matching e **não soma cM**. 🟢
   - Origem no legado: `_reversa_sdd/addenda/056-regioes-compartilhadas.md`, `_reversa_sdd/domain.md#3.2`
   - Tipo: nova
2. **RN-02:** Uma linha por **segmento de região** — isto é, por par (região, kit) —, com **uma** coluna de kit. Não existe "Kit 2" no dado: duas colunas exigiriam o arquivo de triângulo de pares, que o produto não pede mais. 🟢
   - Origem no legado: `_reversa_sdd/addenda/056-regioes-compartilhadas.md`
   - Tipo: nova (desvio declarado do pedido original) — decidida na sessão de 2026-11-11 (pergunta 1)
3. **RN-03:** Ordem padrão: **cromossomo em ordem natural**, depois posição inicial, depois kit. Determinística, para a tabela não mudar de ordem entre duas análises iguais. 🟢
   - Tipo: nova
4. **RN-04:** Busca, filtro e paginação são **camada de apresentação**: o HTML sai completo e o filtro esconde linhas. Nenhum novo POST, nenhuma análise recalculada. 🟢
   - Origem no legado: `_reversa_sdd/addenda/046-paginacao-dos-resultados.md`
   - Tipo: nova
5. **RN-05:** O clique na linha leva a uma **âncora** da região correspondente, e o destaque dessa âncora **não depende de JavaScript** — a marcação e a folha de estilo bastam. A tela já usa esse recurso para destacar cartão por âncora. 🟢
   - Origem no legado: `src/assets/app.css` (`.card:target`)
   - Tipo: nova — decidida na sessão de 2026-11-11 (pergunta 3)
6. **RN-06:** O desvio visual é declarado: a tabela usa os **tokens da casa** (superfície clara, borda sutil, `--primary`/`--ink`), e **não** um tema escuro com âmbar. Nesta paleta o âmbar (`--aviso-line`) significa **ressalva do arquivo**, e usá-lo como cor de destaque de dado contaminaria esse significado. 🟢
   - Origem no legado: `.reversa/principles.md#V`, tokens de `src/assets/app.css`
   - Tipo: nova (desvio declarado do pedido original)
7. **RN-07:** A tabela **não altera nenhum número** do bloco: regiões, faixas, kits, ideograma, distribuição e desfechos continuam os mesmos; ela só repete, linha a linha, o que a região já contém. 🟢
   - Origem no legado: `_reversa_sdd/addenda/057-distribuicao-por-cromossomo.md`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Seção "Detalhamento dos segmentos compartilhados" **depois da distribuição e antes da lista de regiões**, com contador de linhas exibidas e total | Must | O título consta do HTML, a seção fica entre a legenda da distribuição e a primeira região, e o contador mostra "N de M" quando há filtro e "M" quando não há | 🟢 |
| RF-02 | Campo de busca por texto, aplicado a nome do kit, nome do membro e número do cromossomo | Must | Digitar um nome reduz as linhas às que contêm aquele texto; busca sem resultado mostra mensagem própria | 🟢 |
| RF-03 | Filtro por cromossomo, com opção "Todos" e um item por cromossomo presente no resultado | Must | Escolher um cromossomo deixa só as linhas dele; "Todos" restaura | 🟢 |
| RF-04 | Tabela com as colunas: Cromossomo, Posição inicial–final, Tamanho (Mb), cM, Kit, Nome e Desfecho | Must | Cada linha tem as sete colunas preenchidas com o valor da região correspondente | 🟢 |
| RF-05 | Cromossomo como **badge**; desfecho com o **selo** que a lista de regiões já usa | Must | O HTML traz a badge do cromossomo e o selo de desfecho com a mesma classe da lista | 🟢 |
| RF-06 | Posição formatada como `início – fim` em pares de bases, com o mesmo formatador do resto da tela | Must | A célula mostra os dois números separados por travessão, com separador de milhar do projeto | 🟢 |
| RF-07 | Tamanho em **Mb** com duas casas e unidade | Must | A célula mostra o valor em Mb, igual ao da região | 🟢 |
| RF-08 | cM com o formatador de cM do projeto (até duas casas, vírgula decimal) | Must | A célula mostra o cM do segmento, sem arredondar para inteiro | 🟢 |
| RF-09 | Paginação com **seletor de 10, 20 ou 30 por página** (20 como padrão), com anterior/próxima e posição "Página N de M" | Should | Com mais linhas que o **menor** tamanho de página (10), o seletor aparece e tem as três opções; com 10 linhas ou menos, nenhum controle aparece. Anterior/próxima só quando há mais de uma página | 🟢 |
| RF-10 | Clique numa linha destaca a faixa da região no **ideograma** e rola até ela, sem recarregar | Must | A linha é um link para a âncora da faixa; clicar deixa a faixa destacada | 🟢 |
| RF-11 | Ação de **copiar** a linha como texto (`cromossomo`, posição, tamanho, cM, kit, nome) | Should | O botão copia a linha; sem JavaScript, a tabela continua legível | 🟡 |
| RF-12 | Sem região, a seção não existe; com filtro sem resultado, a tabela mostra uma frase e mantém os controles | Must | O HTML sem região não contém a seção; o estado vazio do filtro tem texto próprio | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Nenhum recálculo no filtro: esconder linhas no documento já servido | Precedente da 046: o `POST` reparseia o GEDCOM em 12 a 31 s; filtrar no servidor repetiria isso | 🟢 |
| Volume | Suportar o teto de 200 regiões com os kits de cada uma sem travar a página | `LIMITE_DE_REGIOES = 200` em `src/core/regioes.py`; a análise real medida na 056 produziu 32 regiões | 🟢 |
| Acessibilidade | Tabela semântica com `<th scope>`, busca e filtro com rótulo, foco visível, contraste dos tokens | O bloco já usa botão focável e conteúdo no DOM (056) | 🟢 |
| Sem recursos externos | Nenhuma biblioteca de tabela, nenhuma origem externa | `tests/test_tela_sem_origem_externa.py` | 🟢 |
| Impressão | A tabela imprime; a paginação não pode esconder linhas na impressão | A 050 entregou impressão do resultado; a 046 convive com ela | 🟡 |
| Invariante de tela | `GET /` sem resultado não muda (`SHA_DA_TELA`) | `tests/test_icone_de_atalho.py` | 🟢 |
| Privacidade | A tabela só repete dado que a lista de regiões já mostra; nada novo é persistido | `.reversa/principles.md#I` | 🟢 |
| Fixture | Testes usam CSV sintético (`DNA_CSV_SEGMENTOS_DISTRIBUICAO`) | `.reversa/principles.md#I` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: tabela com os segmentos das regiões
  Dado um CSV de matches com regiões em mais de um cromossomo
  Quando o operador abre "Regiões compartilhadas"
  Então a seção "Detalhamento dos segmentos compartilhados" aparece depois da distribuição e antes da lista de regiões
  E há uma linha por segmento de região
  E o contador mostra o total de linhas
  E a paginação oferece 10, 20 e 30 por página

Cenário: filtro por cromossomo
  Dado a tabela com segmentos em três cromossomos
  Quando o operador escolhe o cromossomo 7 no filtro
  Então só as linhas do cromossomo 7 ficam visíveis
  E o contador passa a mostrar quantas de quantas

Cenário: busca sem resultado
  Dado a tabela preenchida
  Quando o operador digita um nome que não existe
  Então nenhuma linha fica visível
  E a tabela mostra uma frase de estado vazio
  E os controles continuam na tela

Cenário: cada coluna traz o valor da região
  Dado a tabela preenchida
  Quando o operador lê uma linha
  Então o cromossomo aparece como badge
  E a posição aparece como início e fim em pares de bases
  E o tamanho aparece em Mb com duas casas
  E o cM aparece com o formatador de cM do projeto
  E o desfecho aparece com o mesmo selo da lista de regiões

Cenário: copiar os detalhes de uma linha
  Dado a tabela preenchida
  Quando o operador aciona "copiar" numa linha
  Então o texto da linha vai para a área de transferência
  E a tabela continua legível quando o navegador não tem JavaScript

Cenário: clique na linha destaca a faixa no ideograma
  Dado a tabela preenchida
  Quando o operador clica numa linha
  Então o navegador rola até a faixa correspondente no ideograma
  E a faixa fica destacada

Cenário: arquivo sem região
  Dado um CSV em que nenhuma região se forma
  Quando a análise termina
  Então o cartão "Regiões compartilhadas" não é renderizado
  E não existe seção de detalhamento no HTML
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-04 | Must | Sem título e colunas não há tabela |
| RF-02, RF-03 | Must | São os dois filtros que o operador pediu explicitamente |
| RF-05, RF-06, RF-07, RF-08 | Must | Formatação é o que torna a linha verificável contra a região |
| RF-10 | Must | É a interação pedida ("destacar o ponto correspondente no gráfico") |
| RF-09 | Should | O teto de 200 regiões pede paginação; o seletor de 10/20/30 repete o controle que a lista de cartões já usa (046) |
| RF-11 | Should | Conveniência; a tabela é legível sem ela |
| RF-12 | Must | Estado vazio e ausência de seção são contrato do bloco |

## 9. Esclarecimentos

### Sessão 2026-11-11

- **Q:** Qual é a granularidade da linha? (a) uma por par (região, kit), (b) uma por região com os kits numa célula, (c) uma por segmento bruto do CSV, (d) uma por par agrupada por região
  **R:** (a) uma linha por par (região, kit) — o segmento escolhido para aquele match naquela região. Fecha a dúvida 1 e fixa `RN-02`.
- **Q:** Onde a tabela entra, e o que acontece com a lista de regiões? (a) depois da distribuição e antes da lista, as duas coexistem, (b) depois da lista, (c) substituindo a lista, (d) em cartão recolhível próprio
  **R:** (a) depois da distribuição e antes da lista, as duas coexistem: a tabela é o detalhe fino e a lista o resumo por região. Fecha a dúvida 2 e fixa a posição em `RF-01`.
- **Q:** Até onde vai o clique na linha? (a) destaca a faixa no ideograma sem JavaScript, (b) destaca e abre o cartão da região, (c) destaca e rola até a linha da região na lista, (d) só copia
  **R:** (a) destaca a faixa correspondente no ideograma e rola até ela, sem JavaScript. Fecha a dúvida 3 e confirma `RN-05`.
- **Q:** Como a tabela lida com lista longa? (a) 20 fixo, (b) seletor 10/20/30, (c) rolagem interna com cabeçalho fixo, (d) "mostrar mais"
  **R:** (b) seletor de 10, 20 ou 30 por página, com 20 como padrão — o mesmo controle da lista de cartões (046). Ajusta `RF-09`.

## 10. Lacunas

Nenhuma lacuna em aberto nesta versão: as três dúvidas da versão inicial foram fechadas na sessão de 2026-11-11.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-11-11 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-11-11 | Sessão de esclarecimentos: 4 perguntas respondidas, 3 `[DÚVIDA]` fechadas, `RN-02`/`RN-05` confirmadas, posição em `RF-01` e seletor de 10/20/30 em `RF-09` | reversa |
