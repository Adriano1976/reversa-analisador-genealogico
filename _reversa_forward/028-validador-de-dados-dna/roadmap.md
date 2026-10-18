# Roadmap: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/028-validador-de-dados-dna/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature entra como **dois componentes novos e nenhuma reescrita**: `core/validator.py` concentra a
decisão pura (estimar o MRCA, medir a viabilidade temporal por lado, classificar as anomalias e
devolver um dos três status) e `application/validacao.py` faz a leitura e o cruzamento, reutilizando
o parser de GEDCOM, a leitura tolerante de CSV, o matching e o parentesco documental que já existem.
O núcleo recebe valores prontos — datas, `degrees`, `meioses`, `common_ancestor`, `kit` e o intervalo
de geração — e não conhece arquivo, árvore, HTTP nem relógio.

A regra nova é uma **composição** das verificações existentes, não uma segunda implementação delas:
`hop_evidence` já diz se um salto é implausível (12–70), `janela_de_vida` já tem o corte de 122,
`relationship_hypotheses` já tem a tabela SCP 4.0 e `evidence_comparison` já tem os quatro estados.
O validador acrescenta a idade por lado, a estimativa do ano do MRCA e a precedência dos três status.
O maior segmento não entra na estimativa do MRCA; a marca de evidência fraca continua onde já está,
em `genetic_evidence`, e não altera o veredito.

Não há mudança em `app.py`, template, CSS, banco ou `requirements.txt`. A API é interna e o resultado
é um dicionário serializável, pronto para uma feature futura de apresentação.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Toda fixture é sintética; nenhum arquivo de `uploads/` é lido ou copiado | respeita |
| II. Comportamento observável é preservado em refatoração | Os quatro estados, as mensagens e a tela ficam intocados; o validador é um campo novo | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada código crítico e cada status tem teste; a fachada tem teste de integração | respeita |
| IV. Arestas do grafo são tipadas | A validação percorre apenas filiação; caminho por afinidade devolve `INCONCLUSIVO` | respeita |
| V. Toda suposição de genealogia genética cita a fonte | 12–70, 122, SCP 4.0 e o prior de 25 estão citados no requirements e nas docstrings | respeita |

Nenhum conflito com princípio ativo.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Criar `src/core/validator.py` (puro) + `src/application/validacao.py` (fachada de leitura) | Separa decisão de I/O e preserva a regra de que `core/` não importa `parsers/` (ADR-25) | (a) estender `evidence_comparison` com os três status; (b) pôr leitura e regra no mesmo módulo | 🟢 |
| D-02 | Compor `documentary_relationship`, `janela_de_vida`, `profundidade_do_caminho`, `relationship_hypotheses`, `genetic_evidence` e, quando existir, `evidence_comparison` | Nenhuma dessas peças responde à pergunta completa; reimplementá-las criaria duas verdades | (a) reescrever o cálculo de parentesco; (b) duplicar a tabela SCP 4.0 | 🟢 |
| D-03 | O núcleo recebe uma `ComparacaoParaValidar` congelada, com datas já parseadas, `degrees`, `meioses`, `kit`, `comparacao_existente`, `intervalo_de_geracao` e `ano_referencia` | Mantém o núcleo puro e testável sem árvore, arquivo ou relógio | (a) passar a árvore para o núcleo; (b) ler o CSV dentro do núcleo | 🟢 |
| D-04 | A estimativa do MRCA usa o **cM total** do kit; a ordem é `MRCA` do kit e, na falta dele, mediana das `meioses` publicadas ÷ 2 | É a grandeza que a SCP 4.0 calibra; o maior segmento não tem tabela publicada que o mapeie para meioses | (a) usar o maior segmento como estimador; (b) somar kits | 🟢 |
| D-05 | A idade por lado usa `degrees.a_up` (doador) e `degrees.b_up` (match), não `meioses / 2` | A média esconde um lado curto e um lado longo; o caminho real já tem a divisão | (a) usar a média dos dois lados; (b) usar só o total | 🟢 |
| D-06 | Os limites 12–70 vêm de `hop_evidence`/`documentary_relationship`; o 122 vem de `janela_de_vida`; a imprecisão de data usa um wrapper público novo em `janela_de_vida` | Uma autoridade só para cada limiar; evita constante duplicada | (a) copiar as constantes para `validator.py`; (b) importar função privada | 🟢 |
| D-07 | `G` (intervalo de geração) é a mediana dos intervalos pai-filho datados da árvore, com fallback de 25 anos e menos de 3 amostras | Usa o dado da própria árvore e só cai no prior quando não há evidência suficiente | (a) fixar 25; (b) fixar 30; (c) usar um valor único da literatura | 🟢 |
| D-08 | O status segue `ERRO CRONICO / QUEBRA DE LINHA` > `INCONCLUSIVO` > `VALIDADO`; `VALIDADO` exige a linha inteira datada e sem atenção | Erro pode ser provado com dado parcial; validação não pode ser afirmada com dado faltante | (a) tratar dado faltante como erro; (b) validar com data estimada | 🟢 |
| D-09 | Códigos estáveis com severidade, ordenados por severidade e código, sem duplicata; `motivo` é uma frase humana | O código é o contrato de máquina; o texto é para o operador | (a) só texto livre; (b) só código sem explicação | 🟢 |
| D-10 | A fachada reutiliza `carregar_arvore`, `read_csv_with_fallback`, `detect_columns`, `build_genetic_evidence`, `build_ged_indexes`, `match_candidates` e `documentary_relationship` | Não cria segundo parser nem segundo matching; a árvore é parseada uma vez | (a) parser próprio; (b) matching próprio | 🟢 |
| D-11 | Caminho por afinidade devolve `INCONCLUSIVO` com `AFINIDADE_NAO_BIOLOGICA`; o validador não percorre casamento como sangue | Princípio IV: aresta de casamento não é aresta de filiação | (a) validar afinidade como consanguinidade; (b) ignorar o caso | 🟢 |
| D-12 | Sem persistência, sem migração, sem coluna nova e sem dependência nova | O resultado é efêmero e o banco não é necessário para validar; `statistics` e `dataclasses` são da biblioteca padrão | (a) gravar o resultado no Postgres; (b) criar tabela de validação | 🟢 |

## 4. Premissas

Nenhuma premissa pendente: o `requirements.md` está com **zero** marcadores de dúvida após a sessão
de esclarecimentos de 2026-10-18.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.validator` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | componente-novo | Regras puras de estimativa do MRCA, viabilidade temporal, anomalias e status |
| `application.validacao` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | componente-novo | Fachada de leitura/cruzamento e agregação por kit; não é ligada à borda HTTP |
| `core.janela_de_vida` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-novo | Expõe `data_imprecisa(texto) -> bool` como wrapper público; comportamento existente idêntico |
| `tests.fixtures.arvore_com_datas` | `tests/fixtures/` | artefato-novo | GEDCOM sintético com datas de nascimento para os cenários de viabilidade |
| `tests.test_validator` | `tests/` | artefato-novo | Testes unitários das regras puras |
| `tests.test_validacao_de_arquivos` | `tests/` | artefato-novo | Teste de integração da fachada com GEDCOM e CSV sintéticos |

**Arquivos que NÃO mudam:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`,
`init.sql`, `requirements.txt`, `docker-compose.yml` e qualquer tabela do PostgreSQL.

## 6. Delta no modelo de dados

- **Nenhuma migração e nenhuma estrutura persistente nova.** O validador trabalha com dataclasses
  congeladas em memória e devolve dicionário serializável.
- As estruturas de entrada e saída (`ComparacaoParaValidar`, `MrcaEstimado`, `ResultadoDeValidacao`)
  estão detalhadas em `_reversa_forward/028-validador-de-dados-dna/data-delta.md`.
- O banco continua com as 6 tabelas atuais; `analysis_person` e `match_result` não são tocadas.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a | Nenhum contrato HTTP, fila, gRPC ou GraphQL é criado ou alterado | n/a |

A API interna (`estimar_mrca`, `validar_comparacao`, `agregar_resultados`, `validar_arquivos`) está
descrita em §3 e em `data-delta.md`. O diretório `interfaces/` é omitido de propósito.

## 8. Plano de migração

n/a. Não há dado a migrar, coluna a criar ou tabela a alterar. A feature é aditiva e efêmera.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `VALIDADO` raro porque exige a linha inteira datada | médio | alto | Comportamento declarado na RN-09; o `INCONCLUSIVO` carrega `SEM_DATA_DE_NASCIMENTO` e o operador vê o motivo; os testes fixam os dois lados |
| Divergência entre os limiares 12–70/122 e o código existente | alto | baixo | Importar as constantes/funções de `documentary_relationship` e `janela_de_vida`; teste que compara os valores |
| Viés do prior de 25 anos quando a árvore tem poucas datas | médio | médio | Mediana da árvore primeiro; prior só com menos de 3 amostras; testes com árvore de intervalo conhecido |
| Envoltória de cM ampla (muitas relações candidatas) | médio | médio | Tolerância de 2 meioses declarada; testes com valores de canto (0, 15, 25, 200, 3400 cM) |
| Duplicar parsing ou matching na fachada | alto | baixo | Reutilizar as funções nomeadas em D-10; revisão de código e teste de importação |
| Dado real entrar em fixture | alto | baixo | Fixture sintética; `.reversa/principles.md#i`; `git status` sem `uploads/` |
| Ciclo de importação `core/` ↔ `parsers/` | médio | baixo | `core/validator.py` só importa `core/` e stdlib; a fachada é que importa `parsers/` |
| Caminho por afinidade ser tratado como linhagem | médio | baixo | Checar `documental.status == "affinity"` e devolver `AFINIDADE_NAO_BIOLOGICA`; teste dedicado |
| Custo de varrer a árvore para a mediana de geração | baixo | baixo | Uma passada O(n) por chamada, sem segundo parse; medir no teste de integração |
| Arredondamento de anos/gerações | baixo | médio | Anos inteiros; arredondamento só na apresentação; testes de fronteira |

## 10. Critério de pronto

- [ ] `src/core/validator.py` implementado com `estimar_mrca`, `validar_comparacao` e `agregar_resultados`
- [ ] `src/application/validacao.py` implementado com `validar_arquivos`
- [ ] `core.janela_de_vida.data_imprecisa` público, sem mudança de comportamento
- [ ] `tests/fixtures/arvore_com_datas.py` com GEDCOM sintético datado
- [ ] `tests/test_validator.py` cobre os três status, todos os códigos críticos e os casos de borda
- [ ] `tests/test_validacao_de_arquivos.py` cobre leitura, cruzamento, múltiplos kits e ausência de evidência
- [ ] Suíte completa passa no `.venv`, sem dependência nova
- [ ] `src/app.py`, template, CSS, `init.sql`, `requirements.txt` e tabelas do banco intocados
- [ ] `git status` lista apenas os arquivos previstos em §5 e os artefatos de `_reversa_forward/028-*`
- [ ] `legacy-impact.md` e `regression-watch.md` gerados nas etapas seguintes

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-plan` | reversa |
