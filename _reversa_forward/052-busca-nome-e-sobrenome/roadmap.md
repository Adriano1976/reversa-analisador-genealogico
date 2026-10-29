# Roadmap: busca por nome e sobrenome em GEDCOM e CSV

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Requirements: `_reversa_forward/052-busca-nome-e-sobrenome/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A busca entra como **quinto caso de uso** da fronteira de aplicação, com uma porta nova (`FonteDeNomes`) e dois adaptadores — a árvore e o relatório de matches —, para que o domínio nunca veja `gedcom_parser` nem `csv_ingest`. O casamento mora em `core/busca_de_nome.py`, puro: um `TermoDeBusca` congelado, uma sequência de estratégias substituíveis e uma ordem total determinística. O índice que torna a busca barata não é cache novo: é a **segunda visão** do mapa que `core/homonimos.py` já constrói, nascida na mesma varredura e pendurada no **grafo da árvore**, como a feature 048 fixou. A borda ganha um Blueprint próprio (`POST /busca`) e a tela ganha um bloco em partial, renderizado sob a mesma condição dos campos de nome — o que mantém `SHA_DA_TELA` e o combobox existente intocados. Nada é persistido, nada é migrado e nenhuma dependência entra.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Toda fixture é sintética (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`); a investigação não transcreve nome real, e o índice é memória de processo | respeita |
| II. Comportamento observável é preservado em refatoração | `RN-06` e `RF-11`: a busca **não** muda normalizador, ranking nem índice dos fluxos de análise; é feature de leitura, não refactor disfarçado | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada `RF` da tabela tem teste nomeado no `actions.md`; o teste negativo A→B e o de não regressão da análise são portão | respeita |
| IV. Arestas do grafo são tipadas | A busca **não percorre aresta nenhuma** — ela indexa nomes, não relações; a tipagem filiação/casamento não é tocada | respeita (não se aplica) |
| V. Toda suposição de genealogia genética cita a fonte | Nenhuma faixa de cM, MRCA ou heurística nova: o único número novo é o teto de 50, herdado do `addenda/037` | respeita (não se aplica) |

Nenhum conflito. Não há princípio em conflito declarado nesta entrega.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A busca é um caso de uso novo em `src/application/busca_de_nome.py`, servido por Blueprint próprio em `src/web/rotas_busca.py` com `POST /busca` | A rota `/` tem **23** `render_template`, **12** deles passando `gedcom_filename` (`domain.md#3.6`); mais um `action` multiplicaria os pontos de render e de guarda. Blueprint é o padrão já usado por `rotas_auth.py` e `rotas_assets.py` | (a) `action=busca_nome` em `POST /`; (b) `GET /busca` com o termo na query string — o termo pode conter nome de pessoa e cairia em log de acesso e histórico do navegador | 🟢 |
| D-02 | Porta nova `FonteDeNomes` (`Protocol`) em `src/ports/__init__.py`, com dois adaptadores em `src/ports/adaptadores.py`: `NomesDaArvoreGedcom` e `NomesDoArquivoDeMatches` | É o que atende "`.ged` e `.csv`" sem `if` de formato no domínio; uma terceira fonte vira adaptador, não alteração de caso de uso. Mesmo desenho das quatro portas existentes (`architecture.md#3`) | (a) o caso de uso importar `gedcom_parser` e `csv_ingest`; (b) uma porta por formato — duas fronteiras para a mesma pergunta | 🟢 |
| D-03 | Domínio novo `src/core/busca_de_nome.py`, puro: `TermoDeBusca`, `AcertoDeBusca` e `ResultadoDaBusca` congelados; `EstrategiaDeCasamento` como `Protocol` com quatro implementações (exata, sobrenome, prefixo, aproximada) | O critério de casamento é política de negócio: precisa ser substituível e testável isolado, e a **ordem** das estratégias é declaração de produto. `core/` não importa Flask nem pandas (`architecture.md#3`) | (a) `if/elif` no caso de uso; (b) herança de classe-base — acoplamento sem ganho | 🟢 |
| D-04 | O índice ganha **duas visões** — nome normalizado → xrefs (já existente) e token → xrefs (nova) —, construídas na **mesma varredura** e penduradas no **grafo** por `setattr` com atributo próprio (`_analisador_indice_de_tokens`) | `addenda/048`: chave derivada do conteúdo colidia (`L-24`), e a vida do mapa deve ser a vida da árvore. A segunda visão nasce dentro de uma varredura que já acontece | (a) cache de módulo com chave de conteúdo — reintroduz `L-24`; (b) `id()` do grafo — é reciclado; (c) índice ordenado por prefixo — não cobre trecho no meio do token (`RN-09`) | 🟢 |
| D-05 | Casamento por **trecho em qualquer posição**, com prefixo pontuando acima do meio de token; ordem por `(-pontuacao, nome_normalizado, xref)` | `RN-09` e `RN-04`. Preserva o casamento que o combobox já pratica (`indexOf`, `index.html#L665-L669`) e elimina o empate por iteração de `set`, que é a `L-25` | (a) só prefixo — perderia resultado que o operador obtém hoje; (b) ordenar por iteração de `set` — não determinístico | 🟢 |
| D-06 | Cada fonte usa o **seu** normalizador: árvore com `core.homonimos.normalizar`, relatório com `utils.name_keys.norm_name`; sem unificação nesta entrega | `RN-06` e a sessão de 2026-10-28: unificar muda resultado de análise em nome com pontuação (princípio II). A busca deve concordar **dentro** de cada fonte — com o dossiê de um lado, com o matching do outro | (a) unificar em `norm_name`; (b) criar um terceiro normalizador em `utils/` | 🟢 |
| D-07 | Casamento aproximado **fica de fora**; quando entrar, reusa `thefuzz`/`rapidfuzz` já pinados, sob medição | O `requirements.txt` já fixa `rapidfuzz==3.14.6` como backend real do matching difuso (`RISK-006`). Reusar é gratuito em dependência, mas acopla a ordenação da busca ao mesmo pin congelado para não mudar o resultado da análise — um bump passaria a mexer em dois comportamentos | (a) adotar `rapidfuzz` desde já; (b) biblioteca nova com núcleo compilado | 🟢 |
| D-08 | Nenhuma dependência nova; a busca usa stdlib mais o que já está instalado | `L-26`: a ausência de um pacote não pode impedir `import app`, e o `.dockerignore` é lista de permissão (`adrs/28-docker-dois-servicos-dockerignore-permissao.md`). Adoção futura exige medição, não preferência (`requirements.md#6`) | (a) dependência dedicada de busca | 🟢 |
| D-09 | A tela ganha um bloco em partial próprio (`src/templates/_busca.html`), incluído pelo `index.html` sob `{% if gedcom_filename %}`; estilos em `src/assets/app.css` | O `index.html` tem 2407 linhas; o partial mantém o bloco coeso e renderizável em teste isolado. Sob a mesma condição dos campos de nome, `SHA_DA_TELA` — que mede a tela vazia — não muda | (a) escrever direto no `index.html`; (b) barra sempre visível — exige remedição declarada do hash | 🟢 |
| D-10 | Limite de **50** acertos por seção, com o total declarado; ausência de relatório não é confundida com "não encontrado" | `RN-07` e `RN-08`; 50 é o teto que o operador já conhece do combobox (`addenda/037`) | (a) sem limite; (b) limite silencioso | 🟢 |
| D-11 | Relatório ilegível omite a seção do CSV e publica o texto acionável que já existe; a seção da árvore continua | `RF-13` e `domain.md#3.8` ("descartar sim, esconder não"): a degradação aparece, não desaparece | (a) seção vazia; (b) derrubar a busca inteira | 🟢 |
| D-12 | Sem auditoria, sem migração e sem tabela nova nesta entrega | `RN-01` e a sessão de 2026-10-28: enquanto o `all_names` viaja no HTML, auditar a busca não acrescentaria evidência | (a) auditar já | 🟢 |

## 4. Premissas

Nenhuma. O `requirements.md` chegou ao plano com **zero** marcadores `[DÚVIDA]` — os três de 2026-10-28 foram resolvidos na sessão de esclarecimentos e viraram `RN-01`, `RN-06`, `RN-09`, `RF-13` e duas linhas de escopo no MoSCoW.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Domínio da busca (novo) | — | componente-novo | `src/core/busca_de_nome.py`: termo, estratégias, acerto, resultado e as duas visões do índice |
| Índice de nomes (`core/homonimos.py`) | `_reversa_sdd/architecture.md#3` | regra-alterada | A varredura de `_indice_por_nome` passa a produzir também `token → xrefs`, no mesmo laço |
| Portas (`src/ports/__init__.py`) | `_reversa_sdd/architecture.md#3` | contrato-novo | `FonteDeNomes` (`Protocol`) e o payload `NomeDaFonte` |
| Adaptadores (`src/ports/adaptadores.py`) | `_reversa_sdd/architecture.md#3` | componente-novo | `NomesDaArvoreGedcom` e `NomesDoArquivoDeMatches` |
| Caso de uso (novo) | — | componente-novo | `src/application/busca_de_nome.py`: orquestra fontes, ranqueia, trunca e traduz a falha do CSV |
| Borda HTTP (`src/app.py`) | `_reversa_sdd/architecture.md#1` | contrato-novo | Registra o Blueprint e monta o caso de uso com as fontes; continua sem decidir casamento |
| Rotas (novo) | — | contrato-novo | `src/web/rotas_busca.py`: `POST /busca`, sob a guarda da feature 051 |
| Relatório (`src/reporting/`) | `_reversa_sdd/architecture.md#3` | componente-novo | `resultado_da_busca.py`: função pura do resultado ao view-model do template |
| Apresentação (`src/templates/`) | `_reversa_sdd/architecture.md#3` | componente-novo | `_busca.html` (partial) incluído por `index.html` sob `{% if gedcom_filename %}` |
| Estilos (`src/assets/app.css`) | `_reversa_sdd/architecture.md#3` | regra-alterada | Bloco de estilos do campo, das seções e do card de acerto |
| Observabilidade | `_reversa_sdd/addenda/049-sistema-de-log.md` | presença | Nenhuma ação nova na trilha — decisão de 2026-10-28 (`RN-01`) |
| Máquinas de estado | `_reversa_sdd/state-machines.md#6` | presença | A Máquina 4 (Desfecho da Busca) é da **busca de caminho** e não é tocada; nenhuma máquina nova nasce |

## 6. Delta no modelo de dados

- Resumo: **nenhum campo, tabela, índice ou migração**. O que nasce são estruturas **em memória**: as duas visões do índice (presas ao grafo) e os payloads congelados do caso de uso. O Diagrama E do `erd-complete.md` — o esquema físico Postgres — fica intocado.
- Detalhe completo em: `_reversa_forward/052-busca-nome-e-sobrenome/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `POST /busca` | HTTP (formulário, resposta HTML) | `_reversa_forward/052-busca-nome-e-sobrenome/interfaces/busca.md` |

## 8. Plano de migração

n/a. Não há migração de esquema, de layout de disco nem de dado existente: a entrega é código puro, e uma instalação já em uso não precisa de passo de atualização. A única consequência operacional é o **custo de memória do índice novo**, que nasce junto com a árvore e morre com ela.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Reintroduzir estado de módulo no índice e reabrir a `L-24` (dossiê de uma árvore citando xrefs de outra) | alto | baixa | Índice pendurado no grafo por `setattr` (`addenda/048`); teste com **duas árvores do mesmo tamanho e mesmos xrefs extremos**, que é o cenário que reproduzia o defeito |
| A busca divergir do dossiê de homônimos — o mesmo nome produzindo duas listas diferentes na mesma tela | médio | média | Teste de concordância: para o mesmo termo, o conjunto de xrefs da busca de nome completo é igual ao de `homonym_dossier` |
| A varredura por trecho custar mais do que o aceitável com 35 mil pessoas | médio | média | Medir antes de fechar, com a árvore real, e registrar o número no `actions.md`; se estourar o alvo, cair para prefixo com a medição na mão — decisão declarada, não silenciosa |
| `SHA_DA_TELA` mudar sem intenção declarada | baixo | baixa | Bloco renderizado sob `{% if gedcom_filename %}`; o teste do hash roda na suíte e acusa |
| A busca devolver nome de outro dono | alto | baixa | Escopo herdado da 051; teste negativo A→B espelhando `test_isolamento_por_dono.py` |
| Regressão no combobox existente | médio | baixa | O bloco JSON e o script não são tocados; `tests/test_combobox_de_nomes.py` permanece byte a byte |
| O campo existir e o operador não achar — repetindo o combobox escondido | médio | média | Campo no cabeçalho, com rótulo e dica visíveis, e asserção de HTML entregue (não de contexto) |
| O partial novo inchar a resposta com árvore aberta | baixo | baixa | Bloco pequeno, sem repetir a lista de nomes; o payload de nomes continua vindo do combobox, que não é tocado |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte com **1.745 + os testes novos** passando, e as **4 falhas pré-existentes** continuando exatamente as mesmas (`addenda/051`)
- [ ] Paridade sem divergência nova contra a linha de base
- [ ] `tests/test_combobox_de_nomes.py` inalterado
- [ ] `SHA_DA_TELA` inalterado
- [ ] Teste negativo A→B da busca, com `404` e sem `403`
- [ ] Teste de determinismo: duas execuções com a mesma ordem, e a mesma ordem sob `PYTHONHASHSEED` diferente
- [ ] Teste de não regressão da análise: veredito, contagem de conexões e descartados idênticos antes e depois de buscas
- [ ] Medição registrada do custo de construção do índice e da varredura por trecho
- [ ] `regression-watch.md` gerado
- [ ] Nenhuma dependência nova no `requirements.txt`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-28 | Versão inicial gerada por `/reversa-plan` a partir do `requirements.md` com zero marcadores, das decisões da sessão de esclarecimentos e dos adendos 037, 048 e 051 | reversa |
