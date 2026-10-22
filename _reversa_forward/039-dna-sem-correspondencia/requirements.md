# Requirements: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

**Termos usados neste documento:** cM = centimorgans (unidade de DNA compartilhado); MRCA = ancestral comum mais recente; cartão = resultado de uma conexão na tela; descarte = nome do CSV que não virou cartão; compatível = candidato com prenome parecido e ao menos um sobrenome em comum.

## 1. Resumo executivo

Um match de cM alto que não tem nenhuma pessoa com nome compatível na árvore some no meio de centenas de descartes de cM baixo. Esta feature cria um bloco próprio, visível por padrão, que reúne os descartes com **cM ≥ 40,0** e **sem candidato compatível**, ordenados por cM decrescente, com nome, kit, cM e MRCA estimado. O bloco declara em texto que **não há parentesco documental a afirmar** e não oferece promoção. Nenhum cartão, cM, caminho, motivo ou descarte existente muda.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` | O cM só influencia o limiar de Jaccard; a aceitação é decidida pelo nome. Não há piso de cM. | 🟢 |
| `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados` | A ordem dos cartões é documental primeiro e cM decrescente dentro do grupo; cM global **não** é a ordem, e isso é declarado, não acidental. | 🟢 |
| `_reversa_sdd/analise-dna/contracts.md#62-descartes` | O descarte carrega `csv_name`, `kit`, `cm` e `motivo`; as features 034 e 038 acrescentaram candidatos, código da causa e detalhe técnico. | 🟢 |
| `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` | "Compatível" é prenome parecido **e** sobrenome em comum; só o compatível é listado como candidato; a promoção é ato do operador, nunca automática. | 🟢 |
| `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` | A lista de trabalho em CSV tem uma linha por descarte e é a via de trabalho completa; a tela não pode substituí-la por um recorte. | 🟢 |
| `_reversa_sdd/addenda/038-humanizar-motivo-descartes.md#resumo-da-entrega` | O motivo é uma causa em português; os números da recusa vão para a nona coluna, `Detalhe técnico`; nenhuma decisão de aceitação mudou. | 🟢 |
| `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md#resíduo-declarado` | O cM não tem piso: nomes sem sobrenome utilizável são inalcançáveis por qualquer valor de cM. | 🟢 |
| `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto` | Bloco que carrega aviso nasce **aberto** e com aparência de aviso; o rodapé de descartes nasce fechado. | 🟢 |
| `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` | O payload do kit tem `total_cm`, `segment_count`, `largest_segment_cm` e a chave (nome normalizado, kit); nunca soma kits diferentes. | 🟢 |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | `core/` decide, `application/` projeta, `reporting/` formata e o template renderiza — a apresentação não decide regra. | 🟢 |

> 🟡 **Fora da extração:** o campo `mrca_generations` existe no payload do kit em `src/core/genetic_evidence.py:286-290` (média das linhas do CSV para o kit) e é consumido pela verificação de profundidade, mas o `data-dictionary.md#51` não o lista. Esta feature depende dele; a lacuna de documentação está registrada na seção 10.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| **Adriano**, genealogista-operador | Saber, antes de mergulhar nos cartões e nos 448 descartes, quais matches de cM alto não têm ninguém na árvore e merecem pesquisa | Roda a análise, vê o bloco "DNA sem correspondência na árvore (9)" e usa a lista para decidir qual ramo pesquisar primeiro |
| **Pesquisador ou parente que acompanha a análise** | Entender por que um match forte não virou cartão sem concluir que o sistema o considerou parente | Lê o aviso do bloco e entende que o cM é um sinal de DNA, não um parentesco documentado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Definição de "sem correspondência".** Um item entra no bloco quando é um **descarte** — nome do CSV que não virou cartão — com `cm ≥ 40,0`, **nenhum candidato avaliado tem `compativel = True`** e **o nome não tem nenhum cartão aceito** (mesmo sem caminho documental). Não entra: nome que já tem cartão (de qualquer kit), descarte abaixo de 40,0 cM, e descarte que tem candidato compatível. O item é por **(nome, kit)**: dois kits descartados do mesmo nome, sem cartão, aparecem em duas linhas, cada uma com o seu cM e o seu MRCA; não há soma entre kits. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` (o cM não decide); `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` (definição de compatível).
   - Tipo: nova.
2. **RN-02 — Ordem determinística.** cM decrescente; no empate, nome do CSV em ordem alfabética e, depois, kit em ordem alfabética. A ordem não depende da ordem do CSV nem da iteração de um `set`. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados` (a ordem é declarada); o desempate por `xref_id` do matching é o precedente de determinismo do projeto.
   - Tipo: nova.
3. **RN-03 — Conteúdo de cada item.** Nome como veio do CSV, kit (ou `—`), cM com vírgula decimal e MRCA estimado em gerações, com duas casas e vírgula, sem zeros à direita. Sem MRCA no CSV, o item diz "MRCA não informado" e não inventa número. O MRCA é a **estimativa do relatório de DNA** (média por kit), não um ancestral documentado. 🟡
   - Origem no legado: `_reversa_sdd/data-dictionary.md#51-evidência-por-nome-normalizado-kit` (payload do kit); o campo `mrca_generations` está no código e não no dicionário — ver seção 10.
   - Tipo: nova.
4. **RN-04 — Aviso explícito, sem parentesco.** O bloco diz, em texto: "Estes matches têm cM alto, mas a árvore não tem ninguém com nome compatível. Isto não é parentesco documentado: é um sinal de DNA a investigar. O cM sozinho não define a relação." O bloco não exibe parentesco, MRCA documental, diagrama, confronto, hipóteses nem o rótulo "conexão" para esses itens. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#2-a-regra-central-do-domínio-três-eixos-que-não-se-contaminam` (os eixos não se contaminam); `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação`.
   - Tipo: nova.
5. **RN-05 — Visibilidade.** O bloco nasce **aberto**, com aparência de aviso, e é recolhível; só renderiza quando há pelo menos um item. Segue o precedente do bloco "Observações do arquivo", não o do rodapé de descartes. 🟢
   - Origem no legado: `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto`.
   - Tipo: nova.
6. **RN-06 — A lista completa não muda.** O bloco "Matches descartados (N)" continua com **todos** os descartes, na ordem atual, e a exportação CSV continua com as mesmas nove colunas. Um item do bloco novo **também** aparece na lista completa; o texto do bloco diz que ele é um recorte. 🟢
   - Origem no legado: `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md#resumo-da-entrega` (lista completa); `_reversa_sdd/addenda/038-humanizar-motivo-descartes.md#resumo-da-entrega` (nove colunas).
   - Tipo: nova.
7. **RN-07 — Sem promoção no bloco.** O bloco não tem "usar este candidato" nem qualquer ação que crie cartão. A promoção continua existindo só na lista completa, para candidato compatível, e continua sendo ato do operador. 🟢
   - Origem no legado: `_reversa_sdd/addenda/034-revisao-dos-descartes.md#resumo-da-entrega` (promoção do operador, nunca automática).
   - Tipo: nova.
8. **RN-08 — Limiar declarado.** 40,0 cM é um **corte de triagem** declarado pelo operador, não uma faixa de parentesco publicada. O número e a medição que o sustenta — 9 casos no arquivo real, em 2026-10-22: 154,5; 52,5; 51,3; 50,5; 45,8; 43,7; 43,3; 42,6; 41,2 cM — ficam em um único literal nomeado no código; o template não contém o número. Mudar o limiar é mudança de código, não configuração de tela. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-não-decide-aceitação` (o cM só influencia o Jaccard); a decisão do corte é do operador e fica registrada nesta feature.
   - Tipo: nova.
9. **RN-09 — Sem recálculo.** O bloco é uma leitura da lista de descartes já produzida; não relê o CSV, não remonta o GEDCOM, não recalcula cM, não reordena os cartões e não altera a mensagem "N conexões encontradas. M descartadas." 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` (camadas); `_reversa_sdd/domain.md#39-ordem-de-apresentação-dos-resultados` (a ordem dos cartões é decisão do núcleo).
   - Tipo: nova.
10. **RN-10 — Fora da guarda dos resultados.** O bloco renderiza mesmo quando não há cartão nenhum, porque é um aviso sobre o que **não** virou cartão. É o mesmo posicionamento do bloco "Observações do arquivo". 🟢
    - Origem no legado: `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md#a-decisão-que-difere-do-bloco-dos-descartados-ele-nasce-aberto` (o bloco de avisos vive fora da guarda dos resultados).
    - Tipo: nova.

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Exibir o bloco "DNA sem correspondência na árvore (N)", com o aviso da RN-04, entre os cartões e a lista completa de descartes | Must | Com N itens, o bloco aparece uma vez, aberto, com o título contendo a contagem e o texto do aviso; sem itens, não aparece | 🟢 |
| RF-02 | Selecionar somente descartes com cM ≥ 40,0 e sem candidato compatível | Must | Um descarte de 150,0 cM sem compatível entra; um de 39,9 cM não entra; um de 50,0 cM com compatível não entra; um nome que já tem cartão em qualquer kit não entra | 🟢 |
| RF-03 | Ordenar por cM decrescente, com desempate por nome do CSV e kit | Must | Três itens 41,2 / 154,5 / 51,3 aparecem como 154,5; 51,3; 41,2; empate mantém a ordem estável entre execuções | 🟢 |
| RF-04 | Mostrar, por item, nome do CSV, kit, cM e MRCA estimado | Must | Cada linha tem os quatro dados; sem MRCA, mostra "MRCA não informado"; o cM usa vírgula decimal | 🟡 |
| RF-05 | Não afirmar parentesco no bloco | Must | O HTML do bloco não contém "Parentesco documental", "conexão com", diagrama do caminho nem bloco de confronto; o aviso contém "não é parentesco documentado" | 🟢 |
| RF-06 | Nascer aberto, ser recolhível e sumir quando vazio | Must | O bloco nasce aberto; o título permite recolhê-lo; sem itens, o elemento não é renderizado | 🟢 |
| RF-07 | Preservar a lista completa e a exportação CSV | Must | A lista completa continua com os mesmos N descartes e a mesma ordem; o CSV continua com as nove colunas; o item do bloco aparece nos dois lugares | 🟢 |
| RF-08 | Referenciar o bloco no resumo dos resultados | Should | Quando há cartões e itens, o resumo ganha uma frase com a contagem e um link para o bloco; sem cartões, o bloco ainda renderiza | 🟡 |
| RF-09 | Dizer que o bloco é um recorte da lista completa | Should | O texto do bloco informa que os mesmos nomes estão na lista completa, com o motivo de cada recusa | 🟡 |
| RF-10 | Não oferecer promoção dentro do bloco | Could | O bloco não contém botão, formulário ou link de promoção; a única ação é a leitura | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | A seleção e a ordenação são O(n log n) sobre os descartes já calculados; nenhuma leitura nova de CSV ou GEDCOM | RN-09; a análise já é o custo dominante | 🟢 |
| Determinismo | A mesma análise produz a mesma ordem e o mesmo conjunto entre execuções | RN-02; precedente do desempate por `xref_id` | 🟢 |
| Privacidade | O bloco usa apenas o payload já exibido; não grava, não loga e não cria tabela | Princípio I; nenhum dado novo | 🟢 |
| Acessibilidade | Título e aviso em texto; a informação não depende de cor; o `details` é operable por teclado | Padrão dos blocos existentes | 🟡 |
| Compatibilidade | A tela de entrada (`SHA_DA_TELA`) não muda; a tela de resultados muda, e os testes da lista completa e do CSV continuam passando | Adendo 022 (hash da entrada); RN-06 | 🟢 |
| Manutenibilidade | O limiar fica em um único literal nomeado e a seleção tem teste próprio; o template não decide | RN-08; RF-12 do projeto (template não monta regra) | 🟢 |
| Observabilidade | Nenhum log ou evento novo; falha de render segue o comportamento atual | Não há nova porta nem persistência | 🟢 |
| Concorrência | Não aplicável: o bloco é leitura pura do resultado já calculado, sem estado compartilhado novo | RN-09; nenhuma porta ou cache novo | 🟢 |

**Fixtures sintéticas:** `tests/fixtures/sample_dna.py` e `tests/fixtures/sample_gedcom.py`, estendidos com um caso de 150,0 cM sem candidato compatível e com a coluna `MRCA`; nenhum arquivo real de DNA ou GEDCOM é copiado para teste (Princípio I). 🟢

**Princípios:** I (fixtures sintéticas), II (nenhum comportamento existente muda), III (cada RF tem critério de teste) e V (o corte de 40,0 cM é declarado como triagem, não como faixa publicada) são respeitados. O Princípio IV não se aplica: o bloco não percorre o grafo. Não há conflito com princípio ativo. 🟢

## 7. Critérios de Aceitação

```gherkin
Cenário: Match de cM alto sem candidato compatível entra no bloco
  Dado uma análise com o descarte "Clezia Santos", kit AZ4078391, 154,5 cM, e nenhum candidato compatível
  Quando a tela de resultados é renderizada
  Então o bloco "DNA sem correspondência na árvore (1)" aparece aberto
  E mostra "Clezia Santos", "AZ4078391", "154,5" e "MRCA estimado: 3,27 gerações"
  E o aviso contém "não é parentesco documentado"
  E o texto diz que os mesmos nomes estão na lista completa, com o motivo de cada recusa

Cenário: Referência no resumo
  Dado uma análise com 8 cartões e 9 itens no bloco
  Quando a tela de resultados é renderizada
  Então o resumo dos resultados informa a contagem de itens e liga ao bloco

Cenário: Descarte abaixo do limiar não entra
  Dado um descarte de 39,9 cM sem candidato compatível
  Quando a tela de resultados é renderizada
  Então o bloco não o lista
  E a lista completa continua a exibi-lo

Cenário: Descarte com candidato compatível não entra
  Dado um descarte de 50,0 cM com um candidato marcado como compatível
  Quando a tela de resultados é renderizada
  Então o bloco não o lista
  E a lista completa o exibe com a ação de promoção

Cenário: Cartão aceito não entra
  Dado um match de 25,4 cM que virou cartão, mesmo sem caminho documental
  Quando a tela de resultados é renderizada
  Então o bloco não o lista
  E o cartão continua nos resultados

Cenário: Nome com cartão em outro kit não entra
  Dado um nome com um kit aceito e outro kit descartado de 60,0 cM
  Quando a tela de resultados é renderizada
  Então o bloco não lista esse nome
  E o descarte do outro kit continua na lista completa

Cenário: Ordem por cM e desempate estável
  Dado três itens de 41,2, 154,5 e 51,3 cM
  Quando o bloco é renderizado
  Então a ordem é 154,5; 51,3; 41,2
  E um empate de cM é desempatado por nome do CSV e depois por kit

Cenário: Sem itens, sem bloco
  Dado que nenhum descarte atende ao critério
  Quando a tela de resultados é renderizada
  Então o elemento do bloco não aparece

Cenário: Sem cartões, com um item
  Dado uma análise com zero cartões e um descarte de 154,5 cM sem candidato compatível
  Quando a tela de resultados é renderizada
  Então o bloco é renderizado
  E a lista completa também é renderizada

Cenário: MRCA ausente
  Dado um item cujo CSV não traz MRCA
  Quando o bloco é renderizado
  Então o item mostra "MRCA não informado"
  E nenhum número é inventado

Cenário: Nenhuma afirmação de parentesco
  Dado o bloco com um item
  Quando o HTML é inspecionado
  Então não há "Parentesco documental", "conexão com" nem diagrama
  E não há botão nem formulário de promoção no bloco
  E o aviso afirma que o cM não define a relação

Cenário: Lista completa e CSV inalterados
  Dado o bloco com 9 itens
  Quando a página é renderizada
  Então a lista completa continua com os 448 descartes
  E o CSV continua com as nove colunas
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Sem o bloco, o caso de 154,5 cM continua enterrado entre 448 descartes |
| RF-02 | Must | É a definição do recorte; sem ela o bloco vira uma segunda lista completa |
| RF-03 | Must | A ordem por cM é o que dá prioridade ao operador |
| RF-04 | Must | Kit, cM e MRCA são o mínimo para investigar o match |
| RF-05 | Must | Sem a ressalva, o bloco afirmaria parentesco que não existe |
| RF-06 | Must | O aviso precisa ser visto; o recolhimento é conveniência |
| RF-07 | Must | A lista completa e o CSV são o contrato de trabalho do operador |
| RF-08 | Should | Ajuda a descobrir o bloco quando há cartões, mas não é a informação |
| RF-09 | Should | Evita a leitura de que o item saiu da lista completa |
| RF-10 | Could | A ausência de promoção é uma consequência da definição, não uma ação |

## 9. Esclarecimentos

### Sessão 2026-10-22

- **Q:** O bloco deve listar só os descartes sem candidato compatível, também os que têm candidato compatível, ou todos os de cM ≥ 40,0?
  **R:** Só os sem candidato compatível. Os que têm candidato compatível continuam apenas na lista completa, com a promoção.
- **Q:** Se um nome tiver um kit que virou cartão e outro kit descartado com cM ≥ 40,0, o kit descartado aparece no bloco?
  **R:** Não. O bloco só lista nomes que não têm nenhum cartão; o descarte do outro kit fica na lista completa.
- **Q:** Onde o bloco deve ficar?
  **R:** Depois dos cartões e antes da lista completa de descartes, aberto.

## 10. Lacunas

- 🟡 **MRCA no dicionário de dados:** `mrca_generations` existe no payload do kit em `src/core/genetic_evidence.py:286-290` e é consumido pela profundidade, mas o `data-dictionary.md#51` não o lista. A feature depende do campo; a documentação da extração fica devendo essa linha (candidata a `/reversa-sync`, não a esta feature).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-22 | Sessão de esclarecimentos: escopo estrito, exclusão de nome com cartão e posição do bloco | reversa |

## Emendas

### E001, 2026-10-22

O que muda: o corte de triagem passa de **40,0** para **20,0 cM**. Na análise real, o recorte passa de **9 para 60 itens** (medido: 40 → 9; 30 → 20; 20 → 60).
Motivo: o operador pediu o corte em 20 cM para incluir os matches de 20–40 cM.
Arquivos previstos: `src/core/sem_correspondencia.py`, `tests/test_sem_correspondencia.py`.

### E002, 2026-10-22

O que muda: os itens sem correspondência deixam de ser um **bloco separado** e passam a ser **cartões na lista de resultados**, com o mesmo tratamento dos cartões "Parentesco documental não encontrado": mesmo cabeçalho, mesmo rótulo e as cinco seções, sem diagrama e sem promoção. O **MRCA estimado do kit** continua visível na seção 2 (Evidência genética), como no bloco antigo. A lista completa de descartes e o CSV continuam intactos; o mesmo item aparece nos dois lugares e o resumo diz isso. A projeção histórica **ignora** esses cartões — não há pessoa para `match_result.matched_person_xref` (NOT NULL/FK) — e eles continuam em `skipped_match` como descartes.
Motivo: o operador quer que esses matches tenham o mesmo tratamento dos classificados "Parentesco documental não encontrado" na aba "Resultados das Análises de Conexão".
Arquivos previstos: `src/core/dna_analysis.py`, `src/application/dna_analysis.py`, `src/templates/index.html`, `src/assets/app.css`, `src/core/sem_correspondencia.py`, `tests/test_sem_correspondencia.py`, `tests/test_characterization_matching.py`, `tests/test_promocao_de_descarte.py`, `tests/test_dna_analysis.py`, `tests/test_observacoes_do_arquivo.py`, `tests/test_estilo_da_tela.py`.

### E003, 2026-10-22

O que muda: **limpeza interna, sem mudança de comportamento**. O `core.sem_correspondencia.selecionar` é removido; o módulo fica só com a regra (`CM_MINIMO_SEM_CORRESPONDENCIA`, `elegivel` e `nomes_com_cartao_aceito`). O núcleo usa a regra para decidir quais descartes viram cartão, e o caso de uso deriva `sem_correspondencia` dos **próprios cartões** já presentes em `resultados` — não há segunda seleção. A tupla `ResultadoDeAnalise.sem_correspondencia` passa a conter os cartões, e não a projeção de quatro campos; o template só usa o tamanho. A lista completa (448), o CSV de nove colunas, a ordem, a mensagem e a promoção continuam iguais.
Motivo: depois da E002, o seletor tinha um único consumidor real — o `|length` do resumo — e repetia a mesma regra do núcleo. A contagem derivada dos cartões impede que resumo e lista divirjam. O `mrca_generations` do descarte permanece (B+ não foi aplicado); o cartão lê o MRCA de `genetic_evidence`.
Arquivos previstos: `src/core/sem_correspondencia.py`, `src/core/dna_analysis.py`, `src/application/dna_analysis.py`, `src/app.py`, `tests/test_sem_correspondencia.py`.
