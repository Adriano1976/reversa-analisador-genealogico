# Requirements: cache dos índices derivados da árvore

> Identificador: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A análise de DNA reconstrói, a cada `POST`, estruturas derivadas da árvore GEDCOM que são
idênticas enquanto o arquivo for o mesmo: o parse inteiro (`carregar_arvore`) e os índices de
matching (`build_ged_indexes`). Medido nesta sessão com a árvore real de 19.403 pessoas
(12,5 MB, 695.926 linhas) e o CSV de matches do próprio doador (492 linhas), o `POST` de análise
leva **67,29 s**, assim distribuídos: **50,53 s de parse**, **8,72 s de índices**, 6,84 s de
pipeline por cartão e 0,22 s de renderização. Ou seja: **88 % do tempo é custo fixo reexecutado
para o mesmo arquivo**.

A feature faz esses derivados nascerem **uma vez por árvore**, serem reusados enquanto o arquivo
não mudar e invalidarem quando mudar, sem alterar nenhum resultado. Para quem opera, o mesmo
`POST` cai para **~16,8 s** só com o cache da árvore e para **~8,0 s** com os índices também
cacheados — **8,4×** mais rápido.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#1` | "A cada `POST`, o GEDCOM é re-parseado integralmente… **Não há cache entre requisições** — e isso deixou de ser uma escolha discutível" | 🟢 |
| `_reversa_sdd/architecture.md#4` | Quadro onde o dado vive: **1** estrutura de módulo (o cache de nomes) e **24** em memória por requisição | 🟢 |
| `_reversa_sdd/architecture.md#7` | Dívida #1 (colisão da chave do cache de nomes, `L-24`), #8 e #9 (`get_children` sem índice; fichas completas) | 🟢 |
| `_reversa_sdd/domain.md#7-lacunas` | `L-20` (custo por ficha) e `L-24` (chave do cache de nomes pode não invalidar entre árvores) | 🟢 |
| `_reversa_sdd/analise-dna/design.md#fluxo-principal` | `build_ged_indexes(arvore)` monta índices e cache de atributos **uma vez**; `match_candidates` os consome | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais` | "Sem cache entre requisições: os índices do GEDCOM inteiro são reconstruídos a cada `POST`" | 🟢 |
| `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md#o-que-passa-a-valer` | Regra 2: índice derivado é permitido se (a) nasce e morre com a árvore da requisição, (b) não vira estado de módulo, (c) não usa chave de conteúdo que possa colidir, (d) não altera ordem, deduplicação nem valor | 🟢 |
| `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md#o-que-não-muda` | "**Não há cache entre requisições.** A afirmação de `architecture.md#1` continua verdadeira" | 🟢 |
| `_reversa_sdd/addenda/025-desempenho-carga-arvore.md` | Otimização anterior do parse: ~1,5 s por carga, "não perceptível"; **nenhum cache foi criado** | 🟢 |
| `_reversa_sdd/addenda/046-paginacao-dos-resultados.md` | A paginação foi feita no cliente **porque** cada `POST` reparseia o GEDCOM (12–31 s no arquivo real) | 🟢 |
| `_reversa_sdd/gaps.md#3-lacunas-moderadas` | A colisão do cache de nomes foi **confirmada por execução** em 2026-10-10; o teste `TT-20` já existe e **falha hoje** | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador do analisador | Rodar a mesma árvore contra vários CSVs de matches sem pagar o parse a cada envio | O GEDCOM é carregado uma vez e três análises seguidas não repetem os 50,53 s de parse |
| Operador do analisador | Perceber a resposta em tempo útil quando a árvore é grande | Árvore de 19.403 pessoas: o `POST` de análise sai de 67,29 s para ~8 s |
| Quem reimplementa o sistema | Saber onde um cache é permitido e como ele invalida | Lê a regra e não recria a colisão de chave do `L-24` |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Derivação única por árvore.** Um índice derivado da árvore é construído **no máximo uma vez por árvore** e reusado enquanto ela for a mesma. O índice não pode alterar ordem, deduplicação nem valor de campo. 🟢
   - Origem no legado: `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md#o-que-passa-a-valer` (item 2)
   - Tipo: nova

2. **RN-02 — A chave é a identidade da árvore, nunca uma assinatura derivada do conteúdo.** Dois objetos-árvore distintos nunca compartilham índice, ainda que tenham o mesmo número de pessoas e os mesmos `xref` extremos (`xref` é o identificador do registro no GEDCOM, como `@I123@`). `id()` não serve como chave — é reciclado. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#lacunas` (`L-24`); `_reversa_sdd/gaps.md`
   - Tipo: nova

3. **RN-03 — O cache entre requisições passa a existir, com escopo e teto declarados.** A árvore (e os índices presos a ela) sobrevive à requisição que a carregou, invalidada pelo arquivo e limitada por teto de memória. Esta regra **supersede** a afirmação absoluta de `architecture.md#1` e o item "O que NÃO muda" do adendo `bug-BUG-20261021-7O7V-v001`; a **regra 2** do mesmo adendo (índice derivado, sem colisão de chave) continua valendo para todo derivado que nascer e morrer com a requisição. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#1`; `_reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais`; `_reversa_sdd/addenda/bug-BUG-20261021-7O7V-v001.md#o-que-não-muda`; decisão humana de 2026-10-24 registrada na seção 9
   - Tipo: alterada

4. **RN-04 — Resultado idêntico.** Com o cache ligado ou desligado, a análise devolve os mesmos cartões, vereditos, ordem, descartes e motivos; a árvore devolvida é indistinguível por impressão digital. 🟢
   - Origem no legado: princípio II de `.reversa/principles.md`
   - Tipo: nova

5. **RN-05 — Memória com teto.** Nenhuma árvore é mantida sem limite. Cada árvore medida custa ~340 MB; o teto de capacidade é explícito e configurável, e o despejo é do mais antigo. 🟢
   - Tipo: nova

6. **RN-06 — Invalidação pelo arquivo.** A entrada do cache é chaveada por caminho absoluto, `mtime` em nanossegundos e tamanho. Arquivo substituído no mesmo caminho força reconstrução. 🟢
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Os índices de matching (`ged_index`, `surname_index`, `features`) são construídos no máximo uma vez por árvore e reusados na mesma árvore | Must | Duas chamadas de `build_ged_indexes(arvore)` devolvem o **mesmo objeto**, e a segunda não percorre as pessoas | 🟢 |
| RF-02 | A entrada é invalidada quando o arquivo muda (conteúdo, `mtime` ou tamanho), e falha de leitura não deixa entrada no cache | Must | Trocar o GEDCOM no mesmo caminho e recarregar produz índices novos, com os nomes do arquivo novo; um arquivo ilegível levanta e não é cacheado | 🟢 |
| RF-03 | O cache é controlado por variável de ambiente; desligado, o comportamento é bit a bit o atual | Must | Com a variável ausente, duas análises seguidas pagam duas construções de índice | 🟢 |
| RF-04 | Duas árvores distintas nunca compartilham índice, mesmo com mesmo tamanho e mesmos `xref` extremos | Must | Teste de regressão da classe `L-24`: a segunda árvore não enxerga `xref` da primeira | 🟢 |
| RF-05 | O cache tem teto de capacidade configurável, com despejo do mais antigo | Should | Com teto 1, carregar A, B e A de novo reconstrói A na terceira | 🟡 |
| RF-06 | Acertos, erros e reconstruções são contados e registrados em log, sem dado pessoal | Should | O log de um `POST` diz quantas construções houve; nenhum nome, `xref` ou cM aparece | 🟡 |
| RF-07 | O cache da árvore entre requisições é formalizado, com invalidação por arquivo, teto de capacidade e *single-flight* | Must | Duas requisições seguidas na mesma árvore pagam um único parse; quatro threads simultâneas pagam um parse | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | No caso real medido (19.403 pessoas, CSV de matches de 492 linhas), o `POST` de análise cai de **67,29 s para ≤ 9 s** com árvore e índices cacheados | Medição desta sessão: 50,53 s de parse + 8,72 s de índices + 6,84 s de pipeline + 0,22 s de render | 🟢 |
| Desempenho | Só com o cache da árvore, o `POST` cai para ~16,8 s; o `POST` de seleção de árvore cai de 47,56 s para 0,58 s | Medição desta sessão, mesmo arquivo e mesma máquina | 🟢 |
| Desempenho | Desligado, o cache não pode piorar o caminho atual em mais que 1 % | Regra de não regressão; o custo desligado é um `os.stat` por carga | 🟢 |
| Memória | Uma árvore ocupa ~340 MB; o teto é **1 árvore por padrão**, configurável por ambiente, com despejo do mais antigo | Medição desta sessão: RSS 42 → 380 MB com uma árvore; 714 MB com duas | 🟢 |
| Paridade | Com cache ligado e desligado, a impressão digital da árvore e do resultado de DNA são idênticas | Princípio II; precedente da feature 025 (hashes antes/depois) | 🟢 |
| Concorrência | Quatro threads na mesma árvore pagam **um** parse e **uma** construção de índice | `ANALISADOR_THREADS = 4`; a medição anterior de quatro requisições concorrentes deu ~72 s cada | 🟢 |
| Determinismo | O cache não introduz ordem nova: a ordem de inserção de nós e arestas e a ordem dos resultados continuam as mesmas | `architecture.md#3` (`@ordem`); princípio II | 🟢 |
| Privacidade | Nenhum nome, `xref`, cM ou conteúdo de arquivo entra em log, métrica ou artefato | Princípio I; a árvore é dado pessoal de terceiros | 🟢 |
| Portabilidade | Sem dependência nova; roda no `.venv` (Python 3.14) e no contêiner Docker | `requirements.txt` pinado por ADR; a feature usa apenas a biblioteca padrão | 🟢 |
| Testes | Usa fixtures sintéticas (`tests/fixtures/sample_gedcom.py`, `tests/fixtures/sample_dna.py`) e o gerador de escala; **nunca** arquivo real de `src/uploads/` | Princípio I | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Segunda análise na mesma árvore não reconstrói índice
  Dado que a árvore de 19.403 pessoas já foi carregada uma vez
  Quando o operador envia um segundo CSV de matches
  Então o arquivo não é reparseado
  E os índices de matching são reusados
  E nenhuma pessoa é percorrida para reconstruí-los
  E os cartões, vereditos e descartes são idênticos aos da primeira análise

Cenário: Arquivo trocado no mesmo caminho invalida o cache
  Dado que uma árvore foi carregada e está no cache
  Quando o arquivo é substituído por outro de conteúdo diferente
  E a mesma referência é carregada de novo
  Então os índices e a árvore são reconstruídos
  E os nomes exibidos são os do arquivo novo

Cenário: Duas árvores de mesmo tamanho não compartilham índice
  Dado que duas árvores distintas têm o mesmo número de pessoas e os mesmos xrefs extremos
  Quando a segunda árvore é carregada no mesmo processo
  Então os índices dela são reconstruídos
  E nenhum xref da primeira aparece em seus resultados

Cenário: Cache desligado reproduz o comportamento atual
  Dado que a variável de ambiente do cache está ausente
  Quando o operador roda duas análises seguidas na mesma árvore
  Então as duas pagam parse e construção de índice
  E o resultado é idêntico ao das execuções com cache ligado

Cenário: Teto de capacidade despeja a árvore mais antiga
  Dado que o cache tem capacidade 1 e a árvore A está guardada
  Quando a árvore B é carregada
  Então A é descartada
  E carregar A de novo reconstrói os índices dela

Cenário: O log conta as construções sem expor dado pessoal
  Dado que o cache está ligado
  Quando uma análise roda e reusa os índices
  Então o log registra uma reconstrução anterior e nenhuma agora
  E o log não contém nome, xref nem cM
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | É o ganho medido: 52 % do `POST` de análise |
| RF-02 | Must | Cache que não invalida produz resultado errado e silencioso |
| RF-04 | Must | É a classe do `L-24`, já confirmada por execução neste projeto |
| RF-05 | Should | Sem teto, o processo cresce ~340 MB por árvore aberta |
| RF-07 | Must | É o maior ganho isolado: 50,53 s dos 67,29 s do `POST` |
| RF-03 | Must | Desligado por padrão é o que permite reverter em produção sem editar código |
| RNF de desempenho | Should | O alvo numérico do operador (60 s) ainda não foi acordado |

## 9. Esclarecimentos

### Sessão 2026-10-24

- **Q:** O cache da árvore entre requisições entra nesta feature?
  **R:** Entra. A feature formaliza o cache da árvore e supersede o item "O que NÃO muda" do adendo `bug-BUG-20261021-7O7V-v001` e a afirmação absoluta de `architecture.md#1`. A decisão veio depois da medição de 67,29 s, que atribuiu 88 % do `POST` a custo fixo reexecutado.
- **Q:** Qual é o teto de memória do cache?
  **R:** Uma árvore por padrão (~340 MB), com teto configurável por ambiente e despejo do mais antigo. Duas árvores levam o processo a ~714 MB e não são o padrão.
- **Q:** A correção do `L-24` entra nesta feature?
  **R:** Não. O cache de nomes de `documentary_relationship._INDICE_DE_NOMES` continua na correção agendada; esta feature não toca o módulo.

## 10. Lacunas

Nenhuma lacuna aberta. As três dúvidas da versão inicial foram resolvidas na sessão de 2026-10-24
(seção 9): escopo do cache entre requisições, teto de memória e a correção do `L-24`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-24 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-24 | `/reversa-clarify`: escopo fechado no cache da árvore + índices; teto 1 árvore; `L-24` fora; números substituídos pela medição de 67,29 s | reversa |
