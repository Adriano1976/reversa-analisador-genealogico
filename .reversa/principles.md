# Princípios do projeto

> Projeto: `analisador-genealogico`
> Data da última alteração: `2026-09-29`
> Mantido por: `/reversa-principles`

## Princípios ativos

### I. Dados reais de DNA/GEDCOM nunca entram no versionamento

**Descrição.** Dados reais de terceiros — árvores GEDCOM, relatórios de DNA/cM, nomes, e-mails e identificadores de kit de correspondentes — são dados pessoais sensíveis e jamais podem ser commitados, em nenhum caminho: nem em `uploads/`, nem em fixtures, golden files, capturas de tela, logs, documentação ou artefatos de análise. Todo teste, exemplo e documentação usa dado sintético, e qualquer arquivo real necessário para reproduzir um problema permanece fora do repositório.

**Exemplo de aplicação.** Ao corrigir a lógica de matching, a validação usa os geradores sintéticos já existentes (`tests/fixtures/sample_gedcom.py`, `tests/fixtures/sample_dna.py`) em vez de copiar algo de `uploads/`. Se um arquivo real for indispensável para reproduzir um bug, ele fica fora do repositório (pasta offline não sincronizada) e é referenciado por caminho, nunca versionado.

**Impacto em templates.**
- `requirements-template.md`: toda feature que recebe arquivo do usuário precisa de uma seção declarando a fixture sintética correspondente.
- `roadmap-template.md`: tarefas de teste especificam a fixture em vez de "usar um arquivo real".
- `actions-template.md`: ação de verificação pré-commit (`git status` não pode listar `uploads/`).

**Criado em.** `2026-09-29`
**Última revisão.** `2026-09-29`

---

### II. Comportamento observável é preservado em refatoração

**Descrição.** Refatorar muda estrutura, nunca comportamento. Um refactor só é considerado concluído quando as mesmas entradas produzem as mesmas saídas antes e depois — mesmos caminhos de parentesco, mesmo conjunto de matches aceitos e rejeitados, mesmos arquivos gerados. Se o comportamento precisa mudar, isso é uma feature e percorre o fluxo de requisito, não se disfarça de refactor.

**Exemplo de aplicação.** Ao extrair a lógica de matching de `analisador-genealogico/app.py` para um módulo separado, roda-se a mesma dupla GEDCOM+CSV antes e depois e compara-se o resultado: mesmos matches aceitos, mesmos descartados, mesmos cM e mesmos caminhos. Qualquer divergência invalida o refactor e ele é revertido, em vez de aceito como "melhoria".

**Impacto em templates.**
- `requirements-template.md`: toda feature declara explicitamente o que é refactor e o que é mudança de comportamento.
- `roadmap-template.md`: tarefas de refactor exigem etapa de comparação antes/depois.
- `actions-template.md`: ação de verificação de paridade de saída.

**Criado em.** `2026-09-29`
**Última revisão.** `2026-09-29`

---

### III. Nenhuma mudança sem teste que a cubra

**Descrição.** Toda mudança de comportamento chega acompanhada de um teste automatizado que falha antes e passa depois. Regra crítica sem cobertura é tratada como não confiável — inclusive regras que hoje só existem no código e na documentação do Reversa.

**Exemplo de aplicação.** A suíte atual tem 50 testes (`py -3.14 -m pytest`, 50 passed). Antes de mexer nos limiares de matching (`HARD_MIN`, `GIVEN_MIN`), escreve-se primeiro o teste que fixa o comportamento atual com as fixtures sintéticas; só então o limiar é alterado, e o teste tem de mudar de resultado junto.

**Impacto em templates.**
- `requirements-template.md`: todo requisito traz seu critério de teste verificável.
- `roadmap-template.md`: nenhuma tarefa de código sem tarefa de teste associada.
- `actions-template.md`: ação de rodar a suíte antes de encerrar a mudança.

**Criado em.** `2026-09-29`
**Última revisão.** `2026-09-29`

### IV. Arestas do grafo são tipadas

**Descrição.** O grafo pessoa↔família carrega dois tipos de vínculo que não são equivalentes: parentesco biológico (filiação, quando a pessoa aparece como filha na família) e vínculo por casamento (quando aparece como cônjuge). Parentesco biológico e vínculo por casamento nunca são tratados como o mesmo tipo de aresta em cálculo de parentesco, de distância ou de cM esperado. Toda travessia que produza grau de parentesco declara qual tipo de aresta está percorrendo, e a apresentação do resultado deixa explícito quando a conexão é por afinidade e não por sangue.

**Exemplo de aplicação.** `find_indirect_path` percorre o grafo com `nx.shortest_path` e comprime os nós de família, contando hops sem distinguir filiação de casamento, e `split_path_by_marriage` (`analisador-genealogico/reconstructed/path_search.py:95-103`) reconhece apenas o primeiro par de cônjuges adjacentes do caminho. Um trajeto com um casamento no meio e descida depois disso pode ser exibido como se fosse linhagem. Sob este princípio, a travessia registra o tipo de cada aresta percorrida e o diagrama marca a aresta de casamento em vez de apresentar a rota como parentesco sanguíneo.

**Impacto em templates.**
- `requirements-template.md`: toda regra que percorre o grafo declara quais tipos de aresta atravessa.
- `roadmap-template.md`: decisões sobre o modelo do grafo registram a tipagem das arestas.
- `actions-template.md`: ação de teste com um caminho que misture filiação e casamento.

**Criado em.** `2026-09-29`
**Última revisão.** `2026-09-29`

---

### V. Toda suposição de genealogia genética cita a fonte

**Descrição.** Faixas de cM, regras de MRCA, pedigree collapse e qualquer outro número ou heurística do domínio citam a fonte no código ou na spec, com a referência e a data de consulta. Número ou heurística sem origem declarada não é regra de negócio: é chute, e não pode sustentar previsão de parentesco exibida ao usuário.

**Exemplo de aplicação.** `SHARED_CM_DATA` (`analisador-genealogico/reconstructed/dna_analysis.py:31`) traduz cM em relação provável, mas o código não cita fonte alguma: o Shared cM Project aparece apenas no `README.md`, e `_reversa_sdd/domain.md:72` registra isso como lacuna. Sob este princípio, a tabela ganha no próprio arquivo o comentário de origem com a referência e a data de consulta, e qualquer ajuste futuro de faixa cita a mesma referência.

**Impacto em templates.**
- `requirements-template.md`: coluna de fonte para todo valor numérico de domínio.
- `roadmap-template.md`: decisões técnicas que fixam número de domínio citam a referência.
- `actions-template.md`: ação de registrar a citação junto ao valor no código.

**Criado em.** `2026-09-29`
**Última revisão.** `2026-09-29`

---

## Princípios aposentados

Nenhum princípio aposentado até o momento.

---

## Histórico de alterações

| Data | Operação | Princípio | Resumo |
|------|----------|-----------|--------|
| 2026-09-29 | criar | I | Versão inicial: dados reais de DNA/GEDCOM nunca entram no versionamento |
| 2026-09-29 | criar | II | Versão inicial: comportamento observável preservado em refatoração |
| 2026-09-29 | criar | III | Versão inicial: nenhuma mudança sem teste que a cubra |
| 2026-09-29 | adicionar | IV | Arestas do grafo são tipadas: filiação e casamento nunca equivalentes em cálculo |
| 2026-09-29 | adicionar | V | Toda suposição de genealogia genética cita a fonte, nunca número chutado |
