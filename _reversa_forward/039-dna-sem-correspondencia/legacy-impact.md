# Legacy impact: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Política de edição do legado: `allowLegacyEdits: true`; `allowedPaths` libera `src/**`,
> `tests/**`, `README.md`, `pyrefly.toml`, `publicar_docs.py`, `.vscode/**`,
> `requirements.txt`, `.markdownlint-cli2.jsonc`, `_docs_auxiliary/**`, `docker/**`,
> `docker-compose.yml`, `init.sql`, `.dockerignore`, `docs/**`, `*.ps1`, `.github/**`.
> Todos os arquivos tocados estão em `src/**` ou `tests/**`.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/sem_correspondencia.py` | `core.sem_correspondencia` (novo) | componente-novo | LOW | Seletor puro e constante de 40,0; não decide aceitação, não lê arquivo e não persiste |
| `src/core/dna_analysis.py` | `core.dna_analysis` | delta-de-dados | LOW | O dict de descarte ganha `mrca_generations`; nenhum limiar ou ramo mudou |
| `src/application/dna_analysis.py` | `application.dna_analysis` | delta-de-dados | LOW | `ResultadoDeAnalise.sem_correspondencia` e chamada ao seletor; a projeção histórica não muda |
| `src/app.py` | borda HTTP | delta-de-contrato-externo | LOW | Um argumento novo no `render_template` do ramo `dna_analysis`; nenhuma rota, ação ou erro novo |
| `src/templates/index.html` | apresentação | delta-de-contrato-externo | MEDIUM | Bloco visível na resposta HTML da análise e frase no resumo; contrato de tela testado |
| `src/assets/app.css` | apresentação | delta-de-contrato-externo | LOW | Aparência de aviso do bloco; nenhum token novo |
| `tests/test_sem_correspondencia.py` | testes | componente-novo | LOW | 17 testes do seletor e do bloco |
| `tests/test_characterization_matching.py` | testes | regra-alterada (forma) | LOW | A chave aditiva entra no contrato congelado; as decisões continuam presas |
| `tests/test_estilo_da_tela.py` | testes | regra-alterada (forma) | LOW | A classe nova entra na lista de acoplamento template/folha |
| `tests/test_promocao_de_descarte.py` | testes | regra-alterada (forma) | LOW | O resultado falso ganha `sem_correspondencia = ()` |

## 2. Diff conceitual por componente

### `core.sem_correspondencia` (novo)

Uma função pura, `selecionar(resultados, descartados, limite_cm=40.0)`, que lê os cartões
aceitos e os descartes já produzidos e devolve uma tupla enxuta com `csv_name`, `kit`,
`cm` e `mrca_generations`. A regra é: `cm >= 40,0`, nenhum candidato com
`compativel=True` e nome normalizado fora dos cartões; a ordem é cM decrescente com
desempate por nome normalizado, nome cru e kit. Não há mutação das listas de entrada,
soma entre kits nem I/O. A constante `CM_MINIMO_SEM_CORRESPONDENCIA` documenta a medição
e a natureza de triagem do corte.

### `core.dna_analysis`

O dicionário de `skipped_matches` passa a carregar `mrca_generations`, copiado do kit
que já o calculava em `genetic_evidence`. É a única mudança no núcleo: nenhum limiar,
peso, ramo de aceitação, motivo, cM ou caminho mudou. A chave é aditiva e o valor é
`None` quando o CSV não tem a coluna.

### `application.dna_analysis`

`ResultadoDeAnalise` ganha `sem_correspondencia: tuple = ()`, preenchido pela chamada ao
seletor depois de `fluxo_dna`. A projeção `projetar_analise` (histórico) não usa o campo;
`DescartadoDaAnalise`, `AnaliseParaRegistrar`, `skipped_match` e o esquema PostgreSQL
continuam iguais.

### Borda e apresentação

`app.py` passa `sem_correspondencia` ao render do ramo `dna_analysis`. O template ganha
um `<details class="card bloco-sem-correspondencia" id="sem-correspondencia" open>`
**dentro** do `{% if skipped_matches %}`, antes do bloco `bloco-descartados`, com título,
aviso, tabela nome/kit/cM/MRCA e um link no resumo dos resultados. Não há candidato,
motivo, diagrama, confronto nem promoção. A folha ganha a aparência de aviso, no mesmo
desenho de `.observacoes-do-arquivo`.

### Testes

17 testes novos em `tests/test_sem_correspondencia.py` (10 do seletor e 7 do bloco). A
caracterização de matching ganha a chave `mrca_generations: None` na fixture sem MRCA; a
lista de classes da folha ganha `bloco-sem-correspondencia`; o `_ResultadoFalso` da
promoção ganha o campo novo. Nenhum teste de decisão foi afrouxado.

## 3. Preservadas

| Regra | Onde | Por que continua intacta |
|---|---|---|
| O cM não decide aceitação; só o limiar de Jaccard em `matching.py` | `_reversa_sdd/domain.md#34` | `matching.py` não foi tocado; a suíte de decisões e a caracterização passam |
| Ordem dos cartões: documental primeiro, cM dentro do grupo | `_reversa_sdd/domain.md#39` | `_ordem` não foi tocada; a análise real continua 8 cartões/448 descartes |
| Não há piso de cM para entrar; nomes sem sobrenome são inalcançáveis por cM | `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` | Nenhum limiar de matching mudou; o bloco só lê descartes |
| A promoção é ato do operador, nunca automática | `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` | O bloco não tem botão de promoção; a lista completa mantém o fluxo |
| A lista de trabalho em CSV tem uma linha por descarte e nove colunas | `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` | `csv_de_descartes.py` não foi tocado; o CSV real continua com 449 linhas e nove colunas |
| O motivo é uma causa em português, com detalhe técnico ao lado | `_reversa_sdd/addenda/038-humanizar-motivo-descartes.md#resumo-da-entrega` | O motivo não foi alterado; o bloco nem o exibe |
| O descarte carrega `csv_name`, `kit`, `cm`, `motivo`, `motivo_codigo`, `motivo_detalhe`, `candidatos` | `_reversa_sdd/analise-dna/contracts.md#62-descartes` | A chave nova é aditiva; os campos existentes mantêm nome, tipo e posição |
| O bloco de aviso nasce aberto; o rodapé de descartes nasce fechado | `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto` | O bloco novo usa a mesma forma de aviso; o bloco de descartes continua fechado |

## 4. Modificadas

| Regra/contrato | Antes | Depois | Natureza |
|---|---|---|---|
| Payload do descarte | sete campos | sete campos + `mrca_generations` | aditiva; nenhuma decisão mudou |
| `ResultadoDeAnalise` | cinco campos | cinco + `sem_correspondencia` (default `()`) | aditiva; construções existentes válidas |
| Resposta HTML da análise | sem bloco de cM alto sem correspondência | bloco novo, aberto, e frase no resumo | delta-de-contrato-externo visível |
| Folha de estilo | sem seletor do bloco novo | `.bloco-sem-correspondencia` com `--aviso-bg` | delta visual |
| Testes de contrato | descarte sem `mrca_generations`; classe nova ausente | chave e classe declaradas | atualização de contrato, sem afrouxar decisões |

Nenhuma regra de aceitação, veredito, cM, caminho, motivo ou promoção foi alterada.

## Emendas 2026-10-22 (E001/E002)

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/sem_correspondencia.py` | `core.sem_correspondencia` | regra-alterada | LOW | E001: corte de 40,0 para 20,0 cM; o seletor ignora o cartão sem correspondência ao montar `nomes_com_cartao` |
| `src/core/dna_analysis.py` | `core.dna_analysis` | regra-nova | MEDIUM | E002: os descartes de cM alto sem correspondência viram cartões com `documentary` `not_found`; a lista completa não é filtrada |
| `src/application/dna_analysis.py` | `application.dna_analysis` | regra-alterada | LOW | E002: a projeção histórica ignora os cartões sem correspondência (não há pessoa para `match_result.matched_person_xref` NOT NULL/FK); eles continuam em `skipped_match` |
| `src/templates/index.html` | apresentação | delta-de-contrato-externo | MEDIUM | E002: o bloco separado sai; os itens viram cartões na lista; o resumo ganha a contagem de sem correspondência |
| `src/assets/app.css` | apresentação | delta-de-contrato-externo | LOW | E002: a regra visual do bloco removido sai |
| `tests/test_sem_correspondencia.py` | testes | regra-alterada | LOW | Cobre 20/19,9, o cartão com rótulo de não encontrado e a lista completa intacta |
| `tests/test_characterization_matching.py` | testes | regra-alterada | LOW | O caso de 150 cM passa a ser cartão **e** descarte; a mensagem vira "1 conexões… 1 descartadas." |
| `tests/test_promocao_de_descarte.py` | testes | regra-alterada | LOW | O caso sem promoção passa a ter o cartão de sem correspondência, além do descarte |
| `tests/test_dna_analysis.py` | testes | regra-alterada | LOW | TT-04: o anti-falso-positivo não gera cartão aceito, mas gera o cartão de sem correspondência |
| `tests/test_observacoes_do_arquivo.py` | testes | regra-alterada | LOW | "Cartão zero" passa a significar "cartão aceito zero"; os nomes viram cartões de sem correspondência |
| `tests/test_estilo_da_tela.py` | testes | regra-alterada | LOW | A classe `bloco-sem-correspondencia` sai da lista de acoplamento |

As emendas **substituem** o bloco separado e o corte de 40,0 do corpo original desta
feature. A análise real passa a **68 cartões** (8 aceitos + 60 sem correspondência),
**448 descartes** e **60** itens em `sem_correspondencia`; a lista completa e o CSV de
nove colunas continuam intactos. Nenhum limiar de matching, veredito, cM, caminho, motivo
ou promoção foi alterado.

## Emendas 2026-10-22 (E003)

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/sem_correspondencia.py` | `core.sem_correspondencia` | regra-alterada (forma) | LOW | E003: `selecionar` sai; ficam `elegivel` e `nomes_com_cartao_aceito`. A regra é a mesma; somem a projeção de quatro campos e a ordem interna |
| `src/core/dna_analysis.py` | `core.dna_analysis` | regra-alterada (forma) | LOW | E003: o laço dos cartões usa a regra compartilhada; o conjunto de aceitos/descartes e o construtor do cartão não mudam |
| `src/application/dna_analysis.py` | `application.dna_analysis` | delta-de-dados | LOW | E003: `sem_correspondencia` é derivado dos próprios cartões (tupla de cartões), e não do seletor; a projeção histórica continua filtrando |
| `tests/test_sem_correspondencia.py` | testes | regra-alterada | LOW | E003: 15 testes — 6 da regra, 8 do cartão na lista e 1 da ordem dos cartões; saem os testes de projeção, ordem interna, MRCA ausente e não-mutação |

A E003 é **limpeza interna sem mudança de comportamento**: a análise real continua com
**68 cartões** (8 aceitos + 60 sem correspondência), **448 descartes**, mensagem
"68 conexões encontradas. 448 descartadas." e CSV de nove colunas. A lista completa, a
promoção e o `mrca_generations` do descarte não mudam; o cartão lê o MRCA de
`genetic_evidence`. Suíte em **1409 passed, 9 skipped** (antes: 1412/9).
