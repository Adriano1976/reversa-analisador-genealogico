# Roadmap: Fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/040-fonte-e-cobertura-do-arquivo/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Três leituras novas sobre o dado que já existe, nenhuma decisão de parentesco tocada:

1. **Fonte** — um catálogo fechado (`core/fontes_de_laboratorio.py`) traduz o valor cru de `Source` em
   `Genera`, `MyHeritage`, …, `não declarada` ou `outro`, guardando o texto original. A escolha dentro do
   kit passa a preferir a primeira linha **com laboratório reconhecido**, e dois laboratórios no mesmo kit
   viram o aviso `fontes_divergentes`.
2. **Cobertura** — um módulo puro (`core/cobertura_do_arquivo.py`) mede o arquivo inteiro a partir das
   evidências já montadas: linhas, evidências, kits, laboratórios e grafias, cromossomos, mediana de cM,
   segmentos abaixo do piso de 10 cM e evidências sem bloco de 15 cM. O núcleo preenche essa medida por
   um coletor opcional (o mesmo padrão de `observacoes_do_arquivo`), a aplicação a expõe e o template
   renderiza um bloco de escopo-arquivo **fora da guarda dos cartões**.
3. **Medida** — um estado por cartão (`core/qualidade_da_medida.py`) com dois pisos que o projeto já usa
   (15,0 cM) e um declarado (900 SNPs), sempre com os três números e a ressalva de que é qualidade da
   medida, não do parentesco.

O template só interpola números e textos de rótulo; nenhuma regra nasce nele. O retorno de
`core.dna_analysis` continua com três posições (paridade preservada) e todos os acréscimos de payload são
chaves aditivas.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Os testes usam `tests/fixtures/sample_dna.py`, estendido com fonte suja e as três faixas de medida; nenhum valor real do arquivo do operador entra em fixture, doc ou teste | respeita |
| II. Comportamento observável é preservado em refatoração | Confronto, viabilidade, caminho, ordem, descartes, CSV e histórico ficam idênticos; o único delta é aditivo (rótulos, painel, estado) e a mensagem de contagem não muda | respeita |
| III. Nenhuma mudança sem teste que a cubra | Catálogo, escolha da fonte, divergência, cobertura, limites de 14,99/15,00 e 899/900, e o HTML do painel ganham teste próprio | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: a feature não percorre o grafo; lê o resultado já calculado | não se aplica |
| V. Toda suposição de genealogia cita a fonte | O piso de 900 SNPs é declarado como **corte de triagem**, não faixa publicada; os 15,0 cM reaproveitam `LIMITE_SEGMENTO_FRACO`, já documentado como critério do projeto; o catálogo de laboratórios é declarado como tabela do projeto, não como registro oficial de empresas | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O catálogo vive em módulo puro novo, `core/fontes_de_laboratorio.py`, com `rotulo(valor)` e `escolher(valores)`, e o template recebe rótulos prontos | Normalização é decisão de domínio (o que é laboratório), não formatação; módulo próprio é testável sem CSV, como `motivos_do_descarte.py` | (a) normalizar no parser — decisão de domínio na borda; (b) normalizar no template — regra no Jinja; (c) normalizar na aplicação — a evidência nasceria inconsistente para o histórico | 🟡 |
| D-02 | O catálogo é uma tabela literal de **alias normalizado → canônico**, comparando sem acento, sem caixa e com espaços colapsados | Os 45 valores medidos diferem só nisso (`GENERA`, `genera`, `Genera Brasil`); uma tabela explícita é auditável e não inventa laboratório | (a) heurística por prefixo — casaria `Genos` com `Genera`; (b) distância de edição — aproximaria empresas distintas; (c) biblioteca de normalização — dependência nova para 45 strings | 🟢 |
| D-03 | Valor que não é laboratório, texto de formulário, haplogrupo, nome de projeto ou empresa não confirmada vira `não declarada`; o não reconhecido vira `outro`; em ambos o texto cru é preservado em `source_raw` | É a decisão do clarify de 2026-10-22: melhor admitir que não se sabe do que supor laboratório; preservar o cru atende "descartar sim, esconder não" (`domain.md#38`) | (a) mapear `Minha herança` para MyHeritage — suposição sem fonte; (b) descartar a célula — perde rastro; (c) exibir `outro` para tudo — apaga a diferença entre formulário e empresa | 🟢 |
| D-04 | A escolha dentro do kit é a **primeira linha com laboratório reconhecido**; sem nenhuma, a primeira linha não vazia, já normalizada | A regra atual (`primeira não vazia`) faz um `-` na primeira linha esconder um `Genera` declarado adiante — defeito medido; a mudança é declarada em RN-04 | (a) manter a primeira não vazia — mantém o defeito; (b) preferir a mais frequente — inventa votação onde não há; (c) primeira + aviso — o rótulo continuaria errado | 🟡 |
| D-05 | Dois laboratórios no mesmo kit geram o aviso `fontes_divergentes` (nível `cartao`), com os dois rótulos, e o exibido é o primeiro | Silenciar seria escolher por conta própria; o canal de aviso por cartão já existe (`mrca_divergente`), então não há superfície nova | (a) escolher o primeiro em silêncio — esconde dado; (b) bloquear o cartão — a fonte não decide análise; (c) aviso de arquivo — a divergência é do kit, não do arquivo | 🟡 |
| D-06 | O estado da medida vive em módulo puro novo, `core/qualidade_da_medida.py`, chamado de `build_genetic_evidence`, e entra no payload do kit como a chave `medida` | Totais e SNPs já estão no ponto exato da montagem da evidência; calcular no template poria limiar no Jinja e calcular na aplicação duplicaria o payload | (a) no template — regra no Jinja; (b) na aplicação — segundo cálculo sobre o mesmo dado; (c) em `dna_analysis` — longe do dado que o produz | 🟢 |
| D-07 | `PISO_MAIOR_BLOCO_CM` é um literal de `qualidade_da_medida` e `LIMITE_SEGMENTO_FRACO` passa a referenciá-lo, mantendo o valor 15.0 | Um só dono do número evita a divergência que a dívida #27 do projeto já registra para literais duplicados; o valor não muda, então a paridade não sente | (a) dois literais 15.0 — duplicação; (b) limiar do estado derivado de `genetic_evidence` — inverteria a dependência e criaria ciclo | 🟡 |
| D-08 | A cobertura é medida em `core/cobertura_do_arquivo.medir(evidencias, linhas)` e devolvida por um **coletor opcional** em `dna_analysis`, o mesmo padrão de `observacoes_do_arquivo` | O núcleo já tem o `df` e as evidências no mesmo escopo; devolver um quarto valor quebraria chamadores e a caracterização; recalcular na aplicação exigiria reler o CSV | (a) quarto elemento no retorno — quebra contrato e paridade; (b) reler o CSV na aplicação — I/O duplicado; (c) calcular no template — impossível, o dado não chega lá | 🟡 |
| D-09 | O painel renderiza **fora** da guarda `{% if dna_results %}`, imediatamente antes dela, e o bloco "Observações do arquivo" não é tocado | Decisão do clarify: um arquivo com evidências e zero cartões ainda tem cobertura; o bloco de observações mantém o contrato do adendo `017` | (a) dentro da guarda — some no caso de zero cartões; (b) fundir com observações — muda contrato vigente; (c) depois dos cartões — vira rodapé | 🟢 |
| D-10 | As frases do painel são compostas no template a partir dos números que o núcleo devolve | Precedente direto: a contagem em três faixas (feature 033) compõe a frase no template com contadores; o que não pode morar no template é a **regra**, e ela fica no núcleo | (a) núcleo devolvendo frases prontas — texto de tela no núcleo; (b) frases fixas no template — número à mão diverge do dado | 🟡 |
| D-11 | O estado é exibido como **linha de texto** no bloco 2, sem fundo colorido; só o rótulo é negrito, e `parcial`/`insuficiente` acrescentam o motivo | 75% das evidências são `insuficiente`; pintar de amarelo 344 cartões transformaria o aviso em ruído e a cor viraria a mensagem — o RNF exige que a informação não dependa de cor | (a) três cores — ruído e dependência de cor; (b) selo no cabeçalho — competiria com o selo de cM; (c) esconder `insuficiente` — esconderia 75% do arquivo | 🟡 |
| D-12 | Nenhuma migração: nem tabela, nem coluna, nem porta. `cobertura` e `medida` vivem só no payload da análise | O painel e o estado são leitura; o histórico registra evidência e descarte, não triagem visual. Migrar por causa de tela seria custo sem consumidor | (a) coluna em `analysis` — migração real sem leitor; (b) tabela de cobertura — dado derivável | 🟢 |
| D-13 | O contrato HTML do painel e da linha de medida ganha documento próprio em `interfaces/` | A resposta de `POST /` é contrato externo e os testes vão prendê-la; o documento fixa posição, textos, números e proibições | (a) só no requirements — o coding reconstruiria; (b) tratar como API — não há JSON nem rota | 🟡 |

## 4. Premissas

Nenhuma. Os dois marcadores de dúvida do requirements foram resolvidos na sessão de esclarecimentos de
2026-10-22 (empresa não confirmada, posição do painel) e as duas decisões de escopo (piso de SNPs e
contagem por laboratório) também.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.fontes_de_laboratorio` | — | componente-novo | Catálogo, rótulo, escolha dentro do kit e detecção de divergência |
| `core.qualidade_da_medida` | — | componente-novo | Pisos de 15,0 cM e 900 SNPs, estado `robusta`/`parcial`/`insuficiente` |
| `core.cobertura_do_arquivo` | — | componente-novo | Medida do arquivo inteiro a partir das evidências |
| `core.genetic_evidence` | `_reversa_sdd/code-analysis.md#4-unidade-analise-dna` | contrato-alterado | `source` normalizado + `source_raw`/`source_motivo`, chave `medida`, aviso `fontes_divergentes` |
| `core.dna_analysis` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | Coletor opcional `cobertura`, preenchido após `build_genetic_evidence` |
| `application.dna_analysis` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | `ResultadoDeAnalise.cobertura` (default `None`) |
| `app.py` (borda) | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | Passa `cobertura` ao render do ramo `dna_analysis` |
| `templates/index.html` | `_reversa_sdd/addenda/022-bloco-de-observacoes-recolhivel.md` | contrato-alterado | Bloco do painel, linha `Fonte:` e linha da medida no bloco 2 |
| `src/assets/app.css` | `_reversa_sdd/addenda/036-refino-do-cartao-de-resultado.md` | contrato-alterado | Grade de números do painel e linha da medida (sem cor de estado) |
| `tests/` | — | componente-novo / contrato-alterado | Testes dos três módulos, do bloco e atualização declarada das fixtures |

## 6. Delta no modelo de dados

- Resumo: **sem migração**. O payload da evidência ganha `source_raw`, `source_motivo` e `medida`; o
  resultado da aplicação ganha `cobertura`. Nenhum campo persistido, tabela ou porta muda.
- Detalhe completo em: `_reversa_forward/040-fonte-e-cobertura-do-arquivo/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Bloco "Cobertura do arquivo" e linha da medida na resposta de `POST /` (`action=dna_analysis`) | HTTP (HTML) | `_reversa_forward/040-fonte-e-cobertura-do-arquivo/interfaces/bloco-cobertura-e-estado.md` |

## 8. Plano de migração

n/a — nenhum dado é migrado. O histórico (`analysis`, `analysis_person`, `match_result`, `match_path_node`,
`skipped_match`) não ganha coluna: `cobertura` e `medida` são leitura de tela. A lista de trabalho em CSV
continua com as mesmas nove colunas, e as análises já gravadas não são reescritas.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A paridade acusar divergência por causa das chaves aditivas no payload da evidência | alto | média | Rodar `tests/rodar_paridade.py` **antes** da primeira edição; se o coletor capturar o payload, declarar o delta esperado e atualizar o oráculo só com decisão explícita (nunca ampliar a tolerância) |
| Testes que comparam o dicionário do kit inteiro quebrarem | médio | alta (esperado) | Atualização declarada: `test_dna_analysis.py` e `test_characterization_matching.py` ganham as chaves novas de forma explícita, sem afrouxar decisões |
| O catálogo errar um laboratório e a tela afirmar empresa que não é | alto | média | 10 células ambíguas ficam `não declarada` (decisão do clarify); valor não reconhecido nunca vira laboratório; teste por alias |
| O painel poluir a tela ou competir com os cartões | médio | média | Bloco recolhível, fora do cartão, sem cor de estado; nasce aberto uma vez por análise |
| `SHA_DA_TELA` mudar por whitespace no template | médio | baixa | O bloco fica fora da guarda dos **resultados**, mas depende de `cobertura` — que é `None` na tela de entrada; medir o hash antes/depois em `test_icone_de_atalho.py` |
| A mediana e os percentuais divergirem do medido no requirements | médio | média | Cálculo em módulo puro com teste sobre fixture sintética; a análise real de 2026-10-22 é o critério de pronto |
| `Fonte:` passar a exibir `não declarada` e o operador achar que piorou | baixo | média | O texto original fica visível em etiqueta ao lado; o painel conta quantas células estão sem laboratório |
| O estado `insuficiente` em 75% dos cartões desanimar a leitura | médio | média | O estado é informativo e não veta nada; o painel diz que o arquivo é de cM baixo antes de o operador ler cartão por cartão |
| `cobertura` ausente em construções de teste de `ResultadoDeAnalise` | baixo | baixa | Campo por último, com default `None`; o template usa `{% if cobertura %}` |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Suíte completa verde e `tests/rodar_paridade.py` sem divergência (ou com delta declarado)
- [ ] `SHA_DA_TELA` inalterado
- [ ] Análise real (`Adriano_Santos_v3_tratado.ged` + `Famílias_Sergipanas.csv`): painel com **617 / 456 /
      456 / 11 (de 45) / 22 / 9,05 / 74% / 88%**, `59` células sem laboratório e a frase do corte não
      declarado; estados **35 robusta / 28 parcial / 5 insuficiente** nos 68 cartões (e **50 / 62 / 344** nas
      456 evidências)
- [ ] O HTML servido não contém `Selecione uma empresa ou fonte`, `minha herança` nem `Meu Patrimônio` como
      rótulo de fonte
- [ ] Nenhum cartão exibe "Parentesco documental" alterado, e a contagem de conexões continua a mesma
- [ ] `regression-watch.md` gerado
- [ ] Adendo `040` convergido em `_reversa_sdd/addenda/` (recomendado)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-plan` | reversa |
