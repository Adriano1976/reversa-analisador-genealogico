# Roadmap: desacoplamento de nós e gerações virtuais no grafo

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/029-desacoplamento-de-nos/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature entra como **dois componentes novos e uma emenda aditiva**, sem reescrita de nada:
`core/cirurgia_do_grafo.py` concentra a cirurgia pura (identificar o ramo base, localizar a junção,
desacoplar a aresta e injetar as gerações virtuais sobre uma **cópia** do grafo) e
`application/correcao.py` é o fluxo que lê GEDCOM + CSV, reutiliza `validar_arquivos` da `028` e monta
uma sugestão por comparação com status de erro.

A emenda é de **uma linha de contrato**: `application/validacao.py` ganha o parâmetro aditivo
`incluir_documental: bool = False`, porque o resultado da `028` **não carrega** `path.ids` nem
`evidence` — os campos que dizem *onde* cortar vivem só no dicionário `documental`. Sem isso, a fachada
teria de repetir o laço de matching e produzir uma segunda verdade sobre quem é o match.

O desenho do grafo é preservado: `nx.Graph` não dirigido, nó de pessoa com `label`/`type` e nó de
família com `type`, aresta sempre pessoa↔família. A cirurgia **não cria aresta pessoa↔pessoa**; cada
elo da cadeia virtual ganha um nó-família sintético. Nada é escrito em disco, em banco ou em tela, e o
grafo recebido nunca é mutado: o resultado é `grafo.copy()`.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Toda fixture é sintética; a sugestão não é gravada; nenhuma pessoa é inventada com nome | respeita |
| II. Comportamento observável é preservado em refatoração | Nenhuma função existente muda de resultado; a emenda da `028` é aditiva e desligada por padrão | respeita |
| III. Nenhuma mudança sem teste que a cubra | Seis invariantes (não mutação, ramo intacto, deterministico, só filiação, sem PII, sugestão declarada) têm teste dedicado | respeita |
| IV. Arestas do grafo são tipadas | A única aresta cortada é de filiação; casamento nunca é cortado nem percorrido como linha | respeita |
| V. Toda suposição de genealogia genética cita a fonte | O hiato usa `mrca_estimado.geracoes` da `028` (SCP 4.0) e a faixa 12–70; nenhum número novo é inventado | respeita |

Nenhum conflito com princípio ativo.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Criar `src/core/cirurgia_do_grafo.py` (puro) com seis funções públicas e `src/application/correcao.py` (fachada de arquivos) | Separa cirurgia de I/O e mantém a regra de que `core/` não importa `parsers/` (ADR-25) | (a) tudo na fachada; (b) tudo no núcleo, inclusive leitura de arquivo | 🟢 |
| D-02 | A cirurgia opera sobre `grafo.copy()` e **nunca** em `deepcopy` | `copy()` duplica a estrutura e compartilha os dicionários de atributos; como nenhum atributo é mutado, a cópia rasa é segura e O(V+E) mesmo nas 35.460 pessoas da árvore real | (a) `deepcopy`, que dobraria a memória sem necessidade; (b) mutar o grafo e desfazer | 🟢 |
| D-03 | A junção é resolvida pelo par `(pai_id, filho_id)` do salto, procurando a família em `FAMC`/`CHIL` do filho e no `child_to_family`, com índice local montado uma vez por chamada | `documentary_relationship.hop_evidence` já faz essa busca, mas ela é por par; varrer todas as famílias por salto repete a lacuna `L-20`. Um índice família→filhos custa O(F) uma vez | (a) chamar `hop_evidence` por salto; (b) varrer `families.values()` a cada salto | 🟢 |
| D-04 | `application/validacao.py` ganha `incluir_documental: bool = False`; com `True`, cada item de `comparacoes` passa a trazer a chave `documental` | O resultado de `validar_comparacao` não tem `path.ids`; sem a chave, a fachada nova repetiria o laço de matching e criaria uma segunda verdade sobre o match | (a) duplicar o laço na fachada; (b) reparsear o GEDCOM na fachada; (c) alterar o retorno sem parâmetro | 🟢 |
| D-05 | Os nós sintéticos usam `type="virtual"` e `type="virtual-family"`, rótulo `Geração <k>` e id `VIRTUAL:<doador>:<ancestral>:<lado>:<k>` | Id derivado do conteúdo é estável entre execuções e processos; `uuid` quebraria o determinismo e `id()` é reciclado (a lição do cache de nomes) | (a) `uuid4`; (b) `id()`; (c) contador global | 🟢 |
| D-06 | `arvore_sugerida` devolve `dict` (contrato de §4.7 do requirements), com o grafo na chave `grafo` | Todo o fluxo do projeto devolve dicionário para a borda; uma dataclass com `nx.Graph` dentro não serializa e não traz ganho | (a) dataclass congelada; (b) `NamedTuple` | 🟢 |
| D-07 | O hiato é `floor(geracoes_estimadas + 0.5) - a_up`; a janela é conferida depois, com `(nasc_doador - nasc_ancestral) / (a_up + k)`, e só gera aviso | O cM manda (decisão de §9 do requirements), mas o arredondamento bancário do Python perderia uma geração em silêncio, e a sugestão não pode fingir resolver a contradição | (a) `round()`; (b) `int(x)`; (c) deixar o hiato fracionário | 🟢 |
| D-08 | A distribuição entre lados é 100% no lado acusado; com os dois acusados, `k_doador = floor(k · deficit_doador / deficit_total + 0.5)` e o resto fica no doador | Divisão determinística, sem depender de ordem de iteração, e o resto no doador porque é o ramo que o operador conhece | (a) metade para cada lado sempre; (b) distribuir pelo `a_up`/`b_up` | 🟡 |
| D-09 | O conjunto protegido são as **arestas internas** do ramo base, excluída a aresta da junção — a única que a cirurgia remove; com a injeção no lado do match a exclusão é vazia, porque a junção fica fora do ramo do doador. Os atributos do ancestral continuam imutáveis | Assim "ramo imutável" (RN-01) e "corta a junção" (RN-04/RN-06) não se contradizem: o que muda é a ligação externa do ramo, nunca o seu conteúdo | (a) proteger também a aresta da junção, o que impediria o desacoplamento; (b) excluir o ancestral do ramo, o que perderia a checagem dos seus atributos | 🟢 |
| D-10 | A cadeia virtual usa `k` famílias sintéticas e reaproveita a família do topo do ramo como última ligação | No grafo não existe aresta pessoa↔pessoa: `Geração 1` liga-se ao ancestral por `F_v1`, cada elo seguinte por `F_v(n)`, e `Geração k` liga-se à família que já contém o filho do ancestral | (a) ligar pessoas diretamente; (b) criar uma família por elo, inclusive a última, deixando o filho órfão da família original | 🟢 |
| D-11 | O grafo sugerido **não é** uma árvore válida para os leitores existentes: `people` e `families` não têm os nós virtuais | `get_parents` e `documentary_relationship` consultam os dicionários, não o grafo; alimentá-los com a sugestão devolveria `[]` em silêncio. Fica declarado na docstring e em teste | (a) inventar registros de pessoa para os virtuais; (b) registrar a sugestão no banco | 🟢 |
| D-12 | Sem `interfaces/`, sem tabela, sem coluna, sem migração, sem dependência nova e sem tocar em `app.py`, template, CSS ou `requirements.txt` | O contrato é uma função Python pura; `networkx==3.7` já é dependência de runtime | (a) rota HTTP para a sugestão; (b) gravar a sugestão em `analysis_*` | 🟢 |
| D-13 | Quatro arquivos de teste: cirurgia unitária, fluxo/contrato, fronteira (pureza e imports) e integração com GEDCOM/CSV sintéticos | Segue o desenho da `028`, que separou núcleo, fachada, fronteira e integração | (a) um único arquivo de teste; (b) só teste de integração | 🟢 |

## 4. Premissas

Nenhuma premissa pendente: o `requirements.md` está com **zero** marcadores de dúvida após a sessão de
esclarecimentos de 2026-10-18 (§9).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.cirurgia_do_grafo` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | componente-novo | Ramo base, junção, desacoplamento, injeção e verificação; puro, recebe a árvore por parâmetro |
| `application.correcao` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | componente-novo | Fluxo sobre arquivos: parseia uma vez, valida e monta a sugestão por comparação |
| `application.validacao` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-alterado | Ganha `incluir_documental` (aditivo, padrão `False`); nenhum comportamento existente muda |
| `tests.fixtures.arvore_para_cirurgia` | `tests/fixtures/` | artefato-novo | GEDCOM sintético com ramo datado, salto impossível e família de casamento |
| `tests.test_cirurgia_do_grafo` | `tests/` | artefato-novo | Testes unitários das seis funções puras |
| `tests.test_sugestao_de_correcao` | `tests/` | artefato-novo | Contrato de §4.7, três status, hiato e insuficiência |
| `tests.test_fronteira_da_cirurgia` | `tests/` | artefato-novo | Pureza: sem `parsers`, `application`, `reporting`, HTTP, relógio ou disco |
| `tests.test_correcao_de_arquivos` | `tests/` | artefato-novo | Integração: GEDCOM + CSV sintéticos até a sugestão |

**Arquivos que NÃO mudam:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`,
`init.sql`, `requirements.txt`, `docker-compose.yml`, `src/parsers/*` e qualquer tabela do PostgreSQL.

## 6. Delta no modelo de dados

- **Nenhuma migração e nenhuma estrutura persistente nova.** Entram dois atributos de nó sintético
  (`type="virtual"` / `"virtual-family"`, mais `label`, `origem`, `justificativa` e
  `nascimento_estimado`) que vivem só no grafo em memória.
- A chave `documental` acrescentada a cada comparação é o mesmo dicionário que `validar_arquivos` já
  monta internamente — não é cópia nem reformatação.
- Detalhe completo das estruturas em `_reversa_forward/029-desacoplamento-de-nos/data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a | Nenhum contrato HTTP, fila, gRPC ou GraphQL é criado ou alterado | n/a |

A API interna (`ramo_base`, `juncao`, `desacoplar_identidade`, `injetar_geracoes`,
`ramo_base_intacto`, `arvore_sugerida`, `sugerir_correcao`) está descrita em §3 e em `data-delta.md`.
O diretório `interfaces/` é omitido de propósito.

## 8. Plano de migração

n/a. Não há dado a migrar, coluna a criar ou tabela a alterar. A feature é aditiva e efêmera.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O operador ler a sugestão como correção definitiva | alto | alto | `natureza="sugestao"`, aviso fixo no resultado, `onboarding.md` com aviso em destaque e nó virtual rotulado `Geração k` (não nome de pessoa) |
| Alguém alimentar a sugestão em `documentary_relationship` e receber `[]` em silêncio | alto | médio | D-11 declarado na docstring e teste que fixa a diferença entre o grafo sugerido e a árvore de leitores |
| Custo de copiar o grafo da árvore real (35.460 pessoas) | médio | médio | `copy()` de estrutura, sem `deepcopy`; medir no teste de integração e registrar o tempo |
| Varredura linear de famílias por salto (`L-20`) | médio | alto | Índice família→filhos montado uma vez por chamada (D-03) |
| Arredondamento perder uma geração | médio | médio | `floor(x + 0.5)` (D-07) e teste com `2.5` |
| Divergência entre a ordem dos ids e a ordem de inserção do grafo | médio | médio | Ids derivados do conteúdo; teste rodando com `PYTHONHASHSEED` diferente |
| Nó virtual com aparência de pessoa real | alto | baixo | Sem `name`, `sex` ou data exata; `nascimento_estimado` como faixa; teste de atributos |
| A emenda na `028` quebrar contrato existente | alto | baixo | Padrão `False`; nenhuma chave nova quando o parâmetro não é passado; teste que compara o retorno antigo |
| Aresta de casamento cortada por engano | alto | baixo | Só a aresta de filiação é candidata; teste com casamento no caminho devolvendo `AFINIDADE_NAO_INJETAVEL` |
| `k` enorme quando o cM é muito baixo | médio | baixo | Sem teto artificial (seria heurística sem fonte); `SUGESTAO_INSUFICIENTE` declara a grosseria em vez de cortar em silêncio |

## 10. Critério de pronto

- [ ] `src/core/cirurgia_do_grafo.py` com as seis funções públicas e `__all__` declarado
- [ ] `src/application/correcao.py` com `sugerir_correcao`, reutilizando `validar_arquivos`
- [ ] `application/validacao.validar_arquivos` aceita `incluir_documental` sem mudar o retorno padrão
- [ ] `tests/fixtures/arvore_para_cirurgia.py` com dados sintéticos
- [ ] Os quatro arquivos de teste passam, cobrindo os nove códigos de §4.4 do requirements
- [ ] O grafo original é idêntico depois da chamada (teste de não mutação)
- [ ] O ramo base é idêntico na sugestão (teste de `ramo_base_intacto`)
- [ ] Suíte completa passa no `.venv`, sem dependência nova
- [ ] `src/app.py`, template, CSS, `init.sql`, `requirements.txt` e tabelas do banco intocados
- [ ] `git status` lista apenas os arquivos de §5 e os artefatos de `_reversa_forward/029-*`
- [ ] `legacy-impact.md` e `regression-watch.md` gerados nas etapas seguintes

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-plan` | reversa |
