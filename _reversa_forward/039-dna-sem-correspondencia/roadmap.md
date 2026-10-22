# Roadmap: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/039-dna-sem-correspondencia/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

O bloco é uma **leitura derivada** da análise que já existe: nenhum match é reavaliado e nenhum limiar de `core/matching.py` é tocado. Um módulo puro novo — `core/sem_correspondencia.py` — recebe os cartões aceitos e a lista de descartes, seleciona os descartes com `cm ≥ 40,0` que **não têm candidato compatível** e cujo **nome não tem cartão em nenhum kit**, e devolve a lista ordenada por cM decrescente.

Para o bloco poder mostrar o MRCA, o dicionário de descarte do núcleo ganha um campo aditivo: `mrca_generations`, que já existe no payload do kit (`genetic_evidence`) e hoje não chega aos descartes. O caso de uso expõe a lista em `ResultadoDeAnalise.sem_correspondencia`, a borda a passa ao template, e o template renderiza um bloco de aviso **aberto**, dentro da guarda `{% if skipped_matches %}`, entre os cartões e a lista completa.

O bloco mostra **nome, kit, cM e MRCA estimado** e um aviso de que não há parentesco documental a afirmar. Não mostra candidato, motivo, diagrama, confronto nem promoção. A lista completa e o CSV de nove colunas não mudam.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Os testes usam `tests/fixtures/sample_dna.py` e `sample_gedcom.py`, estendidos com um caso sintético; nenhum nome, kit ou cM real entra em fixture, doc ou teste | respeita |
| II. Comportamento observável é preservado em refatoração | A feature **acrescenta** uma leitura; não muda cartões, descartes, cM, caminhos, motivos ou a mensagem. O único delta de payload é aditivo (`mrca_generations`) | respeita |
| III. Nenhuma mudança sem teste que a cubra | A seleção, a ordem, os limites, a exclusão por cartão, o MRCA ausente e o HTML do bloco ganham teste; a caracterização existente prende as decisões | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: o bloco não percorre o grafo; só lê o resultado já calculado | não se aplica |
| V. Toda suposição de genealogia cita a fonte | 40,0 cM é declarado como **corte de triagem** do operador, não como faixa publicada; o MRCA é rotulado como estimativa do relatório de DNA, não como ancestral documentado | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | A seleção e a ordem vivem em um módulo puro novo, `core/sem_correspondencia.py`, com a constante `CM_MINIMO_SEM_CORRESPONDENCIA = 40.0` e uma função `selecionar(resultados, descartados, limite_cm=...)` | O bloco é uma decisão de **apresentação** sobre o resultado; o núcleo já é o dono da ordem (`_ordem`, `domain.md#39`) e o template não decide regra (RF-12). O módulo novo evita engordar `dna_analysis.py` e é testável sem árvore, como `motivos_do_descarte.py` | (a) filtro no template — poria o limiar no Jinja; (b) na camada `application` — o docstring dela declara que ordem de apresentação é do núcleo; (c) quarto elemento no retorno de `dna_analysis` — quebraria todos os chamadores e a caracterização | 🟢 |
| D-02 | O item de descarte do núcleo ganha `mrca_generations`, copiado de `kit["mrca_generations"]` no ramo de recusa | O valor já foi lido do CSV e está no payload do kit; reconsultá-lo no seletor duplicaria a chave (nome, kit) e poderia divergir. O campo é aditivo e não muda a decisão | (a) buscar em `evidencias` dentro do seletor — duplica a indexação; (b) gravar em `skipped_match`/porta — migração sem consumidor | 🟢 |
| D-03 | `ResultadoDeAnalise` ganha `sem_correspondencia: tuple = ()`; o caso de uso chama o seletor depois do núcleo e antes de devolver | A tela precisa da lista pronta; o default preserva construções existentes; a projeção histórica (`projetar_analise`) não muda | (a) recalcular na borda `app.py` — regra fora do caso de uso; (b) campo obrigatório — quebraria testes e chamadores | 🟢 |
| D-04 | A exclusão de nome com cartão usa `norm_name(csv_name)`, e não a string crua | O mesmo nome pode aparecer com caixa/espaço diferente entre kits; normalizar garante que um kit aceito exclua o outro kit descartado, como decidido no clarify (2a) | (a) comparar `csv_name` cru — falha com grafia/caixa diferente; (b) comparar por `pid` — o descarte não tem `pid` | 🟡 |
| D-05 | A ordem é `(-cm, norm_name(csv_name), csv_name, kit or "")` | cM decrescente (RF-03); o desempate por nome normalizado é estável e independente da ordem do CSV ou de `set`; o `csv_name` cru e o kit fecham o empate | (a) só `-cm` — empate não determinístico; (b) nome cru — a ordem de acentos varia | 🟢 |
| D-06 | O limiar é fixo em 40,0 cM, em um único literal nomeado, com a medição (9 casos) no docstring; não há variável de ambiente nem controle na tela | O corte é uma triagem declarada do operador, não uma faixa publicada (RN-08); um controle novo não foi pedido e amplia a superfície de configuração | (a) `os.environ` — configuração sem teste e sem necessidade; (b) campo na tela — mais um estado para o operador | 🟡 |
| D-07 | O bloco fica **dentro** do `{% if skipped_matches %}`, antes do `<details class="card bloco-descartados">`, como `<details class="card bloco-sem-correspondencia" open>` com `--aviso-bg` | O bloco só tem itens quando há descartes; a guarda já é falsa na tela de entrada, o que preserva `SHA_DA_TELA`; a posição é a decidida no clarify (3a): depois dos cartões, antes da lista completa. Nasce aberto porque carrega aviso, como o bloco de observações (adendo `022`) | (a) guarda nova fora de `dna_results` — acrescenta whitespace na tela vazia e arrisca o hash; (b) acima dos cartões — compete com o resultado; (c) dentro da lista completa — esconde o aviso no rodapé | 🟢 |
| D-08 | O bloco mostra só nome, kit, cM e MRCA estimado, mais o aviso; **não** mostra candidato, motivo, diagrama, confronto nem promoção | RN-04/RN-07: o bloco é sobre a ausência de correspondência. Candidato fraco (ex.: Vasconcelos de 1394) e motivo ("prenome diferente") sugerem uma correção que não existe; a promoção fixaria a pessoa errada. Esses dados continuam na lista completa | (a) mostrar o melhor avaliado — ruído com cara de resposta; (b) mostrar o motivo — sugere conferir grafia; (c) promoção — W001 da 034, a decisão é do operador e precisa de candidato compatível | 🟢 |
| D-09 | O MRCA usa o mesmo formatador decimal de cM (`cm_br`), com o rótulo "gerações" | `utils/number_format.formatar_cm` já entrega duas casas, vírgula e sem zeros à direita; um filtro novo teria o mesmo comportamento e mais superfície | (a) criar `mrca_br` — duplicação sem ganho; (b) formatar no núcleo — texto de tela no núcleo | 🟡 |
| D-10 | Nenhuma mudança de persistência: `DescartadoDaAnalise`, `skipped_match` e o esquema PostgreSQL ficam como estão | O bloco é tela; o histórico registra o descarte, não a triagem visual. O MRCA não é necessário no banco e migrar por causa de uma leitura seria custo sem consumidor | (a) coluna nova em `skipped_match` — migração real; (b) backfill — não há dado a preencher | 🟢 |
| D-11 | A caracterização e os testes de descarte serão atualizados de forma **explícita** para o campo aditivo, sem afrouxar a comparação das decisões | O dicionário de descarte ganha uma chave; testes que comparam o dict inteiro vão falhar. O contrato que importa — mesmos aceitos, descartes, cM e caminhos — continua preso | (a) esconder o campo atrás de consulta separada — mais código; (b) remover a chave do dict antes de comparar sem declarar — esconde a mudança | 🟢 |
| D-12 | O bloco ganha um contrato próprio em `interfaces/bloco-dna-sem-correspondencia.md` | A resposta HTML do `POST / action=dna_analysis` é contrato externo e os testes vão prendê-la; o documento registra request inalterado, response, texto, colunas, posição e casos vazios | (a) deixar só no requirements — o coding teria de reconstruir o contrato; (b) tratar como contrato de API — não há JSON nem rota nova | 🟡 |

## 4. Premissas

Nenhuma. O único marcador `[DÚVIDA]` do requirements foi resolvido na sessão de esclarecimentos de 2026-10-22 (escopo estrito, exclusão de nome com cartão e posição do bloco).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.sem_correspondencia` | — | componente-novo | Constante de 40,0 cM, seleção por cM/candidato/cartão e ordem determinística |
| `core.dna_analysis` | `_reversa_sdd/code-analysis.md#4-unidade-analise-dna` | contrato-alterado | O dict de descarte ganha `mrca_generations`; nenhuma decisão muda |
| `application.dna_analysis` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | `ResultadoDeAnalise.sem_correspondencia` e chamada ao seletor |
| `app.py` (borda) | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | Passa `sem_correspondencia` ao render da análise de DNA |
| `templates/index.html` | `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md` | contrato-alterado | Bloco de aviso e frase no resumo dos resultados |
| `src/assets/app.css` | `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md` | contrato-alterado | Aparência de aviso do bloco novo |
| `tests/` | — | componente-novo / contrato-alterado | Testes do seletor e do bloco; atualização declarada dos testes de descarte |

## 6. Delta no modelo de dados

- Resumo: **sem migração**. O payload do descarte ganha `mrca_generations`; o resultado da aplicação ganha `sem_correspondencia`; nenhum campo persistido, nenhuma tabela, nenhuma porta.
- Detalhe completo em: `_reversa_forward/039-dna-sem-correspondencia/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Bloco "DNA sem correspondência na árvore" na resposta de `POST /` (`action=dna_analysis`) | HTTP (HTML) | `_reversa_forward/039-dna-sem-correspondencia/interfaces/bloco-dna-sem-correspondencia.md` |

## 8. Plano de migração

n/a — nenhum dado é migrado. As linhas de `skipped_match` já gravadas continuam iguais, e o novo
campo `mrca_generations` vive só no payload da análise (tela). A lista de trabalho em CSV continua
com as mesmas nove colunas.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O bloco novo ser contado como "cartão" por testes que assumem só cartões de resultado e o rodapé de descartes | médio | média | Classe própria (`bloco-sem-correspondencia`), posição dentro da guarda dos descartes e revisão de `test_cartoes_recolhiveis.py` / `test_estilo_da_tela.py` |
| `SHA_DA_TELA` mudar por whitespace novo na tela de entrada | médio | baixa | O bloco fica dentro do `{% if skipped_matches %}`, já falso na entrada; hash medido antes/depois por `test_icone_de_atalho.py` |
| Um nome com cartão em outro kit aparecer no bloco | alto | baixa | Exclusão por `norm_name(csv_name)` (D-04) + cenário Gherkin próprio |
| O bloco exibir parentesco, diagrama ou promoção por engano | alto | baixa | Template sem esses elementos; teste que procura "Parentesco documental", "conexão com", formulário de promoção e diagrama |
| A lista completa ou o CSV mudarem | alto | baixa | Nenhuma coluna/ordem alterada; testes de `test_csv_de_descartes.py` e da lista completa; a chave nova é ignorada pelo formatador |
| O MRCA faltar ou vier divergente no CSV | médio | média | "MRCA não informado" quando `None`; média por kit já é o valor do payload; o aviso de divergência continua no cartão |
| O limiar de 40,0 virar número mágico e divergir do requirements | médio | baixa | Constante única nomeada, com a medição no docstring; teste do limite 39,9 / 40,0 |
| A caracterização falhar por causa da chave aditiva | médio | alta (esperado) | Atualização declarada (D-11), com a comparação de decisões preservada; rodar antes/depois |
| Construções posicionais de `ResultadoDeAnalise` quebrarem | baixo | baixa | Campo novo por último, com default `()` |
| O seletor importar `core` na camada errada e criar ciclo | baixo | baixa | `core.sem_correspondencia` importa só `name_normalization`; a aplicação importa o núcleo, como já faz |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte completa verde, incluindo a caracterização de matching
- [ ] `SHA_DA_TELA` inalterado
- [ ] Análise real: bloco com 9 itens, primeiro `Clezia Santos` (154,5 cM, AZ4078391), `Airton Passos Vasconcelos` (51,3 cM) presente; lista completa com 448 descartes; CSV com nove colunas
- [ ] Bloco sem "Parentesco documental", "conexão com", diagrama ou formulário de promoção
- [ ] Caso de zero cartões renderiza o bloco (teste sintético)
- [ ] `regression-watch.md` gerado
- [ ] Adendo `039` convergido em `_reversa_sdd/addenda/` (recomendado)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-plan` | reversa |
