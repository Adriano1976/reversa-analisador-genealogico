# Roadmap: renderizador Graphviz da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/030-renderizador-graphviz/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature entra como **um componente novo e uma dependência nova**, sem tocar em nada existente:
`src/reporting/visualizer.py` monta o texto DOT à mão (Python puro, sem Graphviz) e só usa o pacote
`graphviz` para invocar o binário `dot` na hora de exportar. Essa separação é o que permite testar
cores, arestas e rótulos em máquina sem Graphviz — que é exatamente esta máquina hoje.

O desenho é **reconstruído a partir dos metadados** da `029` e do `documental`, não por travessia do
grafo. O motivo é estrutural: o grafo é bipartido pessoa↔família e a direção genitor→filho não está
na aresta — está no registro da família, que `reporting/` não pode ler (ADR-34). Reconstruir do
caminho documental, das gerações virtuais e das junções é determinístico, testável e não recria
consulta de núcleo na camada de apresentação.

Nada é persistido, nada é servido por HTTP e o container não muda: a renderização é de **host**
(§9 da sessão de esclarecimentos). A imagem só é escrita no caminho que o chamador informar.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Teste com fixture sintética, imagem em diretório temporário e nunca versionada | respeita |
| II. Comportamento observável é preservado em refatoração | Módulo novo; `mermaid_render` e a tela não são tocados | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cores, aresta rompida, caixa, escape e determinismo têm teste; a renderização é pulada com motivo declarado | respeita |
| IV. Arestas do grafo são tipadas | A compressão só produz arestas genitor→filho; nenhuma aresta de casamento é desenhada | respeita |
| V. Toda suposição de genealogia genética cita a fonte | cM e gerações vêm da `028`/`029`, com a fonte já citada lá; o renderizador não inventa número | respeita |

Nenhum conflito com princípio ativo.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Criar `src/reporting/visualizer.py` | É a camada de apresentação: decide desenho e não importa `core` (ADR-34, ADR-11). O nome é o do pedido | (a) `core/visualizer.py`, que fecharia o ciclo `core/`↔`reporting/` de novo; (b) `application/`, que é caso de uso, não emissão | 🟢 |
| D-02 | A exceção `ErroDeRenderizacao` (com `codigo`) mora no próprio módulo | `core/erros.py` faria `reporting/` importar `core/`; um erro de apresentação pertence à apresentação | (a) pôr em `core/erros.py`; (b) `ValueError` genérico, que perde o código | 🟢 |
| D-03 | `texto_dot` monta a string DOT **à mão**; `graphviz` só é importado dentro de `renderizar_...` | Permite testar o desenho inteiro sem o pacote; e o import preguiçoso é o precedente `L-26` do `psycopg2` | (a) `graphviz.Digraph` para tudo, que exigiria o pacote até para o teste de texto; (b) `pydot`, que só troca de dependência | 🟢 |
| D-04 | As duas funções recebem `documental` além de `sugestao` e `resultado` | O contrato da `029` não traz o caminho nem a pessoa do match; sem eles a RN-06 não tem recorte. Emenda registrada no `requirements.md` §11 | (a) ampliar o contrato da `029`; (b) desenhar só o ramo do doador | 🟢 |
| D-05 | O desenho é reconstruído de `documental["path"]["ids"]` + `sugestao["geracoes_virtuais"]` + `sugestao["juncoes"]`; os rótulos vêm de `grafo.nodes[id]["label"]` | Direção não está na aresta bipartida; a reconstrução é determinística e independente de travessia | (a) percorrer `sugestao["grafo"]` e inferir direção pela posição no caminho do grafo; (b) passar `arvore` inteira para o renderizador | 🟢 |
| D-06 | Cores em `fillcolor` + `style=filled`: base `#a8e6cf`, documental `#f5f5f5` com borda `#666666`, virtual `#ffd3b6` | São as cores do pedido; o par do documental foi fixado para não haver duas leituras de "cinza/branco" | (a) usar só o nome da cor; (b) deixar o documental sem borda, que some no fundo branco | 🟢 |
| D-07 | A aresta rompida é desenhada entre `juncoes[*].pai_id` e `filho_id`, com `style=dashed`, `color=red` e o rótulo literal | `arestas_removidas` guarda ids de **família**, que não são desenhados; as junções guardam o par de pessoas equivalente | (a) desenhar a aresta família↔pessoa, que exigiria desenhar família; (b) usar `arestas_removidas` direto, que produziria aresta para nó inexistente | 🟢 |
| D-08 | As famílias não são desenhadas; a direção genitor→filho vem da posição no caminho (antes do ancestral, inverte) | Deixa a imagem hierárquica e legível, como o pedido; a legenda declara a compressão | (a) desenhar nós de família como losangos; (b) desenhar tudo sem direção | 🟢 |
| D-09 | A caixa de evidência é um nó `shape=note`, ligado ao doador por aresta `style=invis` | "Caixa de texto" do pedido sem criar aresta falsa de parentesco | (a) `label` de grafo solto, que o `dot` posiciona mal; (b) `xlabel` de nó, que colide com o rótulo | 🟢 |
| D-10 | Todo rótulo vai entre aspas duplas, com `\"` e `\\` escapados; sem `label=<...>` HTML | O modo HTML muda a gramática e permite injeção de tag vinda de nome de pessoa | (a) labels HTML; (b) confiar no escape do pacote, que só existe se usarmos `Digraph` | 🟢 |
| D-11 | Detectar `dot` com `shutil.which("dot")` **antes** de chamar o pacote, e ainda capturar `ExecutableNotFound` como rede | A mensagem fica acionável (aponta o download e o `PATH`), e a rede cobre o caso de o binário existir e falhar | (a) só capturar a exceção do pacote; (b) só o `which`, que não cobre falha de execução | 🟢 |
| D-12 | `graphviz==0.21` entra pinado no `requirements.txt` — a versão que já está instalada no `.venv` | ADR-13 exige pin de toda direta; a versão foi verificada em 2026-10-18 (0.21), então o plano não inventa número | (a) fixar um número de memória; (b) deixar sem pin | 🟢 |
| D-13 | Três arquivos de teste: texto DOT (sempre roda), renderização (pulado sem `dot`) e fronteira por AST (import de `graphviz` só dentro de função) | Sem o skip a suíte ficaria vermelha em máquina sem Graphviz e esconderia regressão real; o teste de AST protege o import preguiçoso | (a) um arquivo só; (b) marcar tudo como skip | 🟢 |
| D-14 | `documental` e `sugestao` são lidos por chave, com `or {}` e valor padrão | Entrada vem de outro módulo; chave ausente não pode virar `KeyError` no desenho | (a) acessar direto; (b) validar esquema completo, que duplicaria o contrato da `029` | 🟢 |

## 4. Premissas

Nenhuma premissa pendente: o `requirements.md` está com **zero** marcadores de dúvida após a sessão
de esclarecimentos de 2026-10-18 (§9).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `reporting.visualizer` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | componente-novo | Monta o DOT e exporta PNG/SVG; recebe sugestão, resultado e documental; não importa `core` |
| `requirements.txt` | `_reversa_sdd/dependencies.md` | contrato-alterado | Ganha `graphviz` pinado (ADR-13); o binário `dot` é dependência de sistema, documentada e não instalada por `pip` |
| `tests.test_visualizer` | `tests/` | artefato-novo | Texto DOT: cores, aresta rompida, caixa, escape, determinismo, recusas |
| `tests.test_visualizer_render` | `tests/` | artefato-novo | Exportação real, com `skipif` quando falta `dot` |
| `tests.test_fronteira_do_visualizer` | `tests/` | artefato-novo | AST: `import graphviz` só dentro de função; sem `core` |

**Arquivos que NÃO mudam:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`,
`src/reporting/mermaid_render.py`, `init.sql`, `docker/Dockerfile`, `docker-compose.yml`, `.dockerignore`
e qualquer tabela do PostgreSQL.

## 6. Delta no modelo de dados

- **Nenhuma estrutura persistente nova.** O DOT é string em memória; a imagem é arquivo efêmero no
  destino informado e nunca é versionada.
- Nenhum campo novo em `sugestao` ou `resultado`: o renderizador só lê o que a `028` e a `029` já
  entregam.
- Detalhe das entradas, saídas e atributos DOT em `_reversa_forward/030-renderizador-graphviz/data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a | Nenhum contrato HTTP, fila, gRPC ou GraphQL é criado ou alterado | n/a |

A API interna (`texto_dot`, `renderizar_arvore_sugerida`, `ErroDeRenderizacao`) está descrita em §3 e
em `data-delta.md`. O diretório `interfaces/` é omitido de propósito.

## 8. Plano de migração

1. Instalar o Graphviz de sistema (binário `dot`) na máquina de quem for gerar imagem — passo manual,
   documentado no `onboarding.md`.
2. Instalar o pacote `graphviz` no `.venv` e fixar a versão no `requirements.txt`.
3. Reexecutar a suíte: o teste de renderização passa a rodar em vez de ser pulado.

Nada disso é migração de dado: não há dado a converter.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Binário `dot` ausente na máquina do operador | alto | **alto — é o estado atual** | Erro `DOT_AUSENTE` com mensagem acionável; passo de instalação no `onboarding.md`; teste de renderização pulado com motivo |
| Cobertura de renderização ficar só no papel | alto | alto | Declarado no `requirements.md` §9 e no relatório do coding; o texto DOT cobre tudo menos a chamada ao `dot` |
| Imagem com nome de pessoa viva commitada por engano | alto | médio | Destino obrigatório e explícito; `.gitignore` já cobre `uploads/`; teste que confere que nada aparece fora do destino |
| Layout ilegível se o caminho tiver muitos nós | médio | médio | Recorte do caminho; `rankdir=TB`; nós de família comprimidos |
| Contraste baixo do amarelo `#ffd3b6` com texto escuro | baixo | baixo | `fontcolor` escuro fixo (`#333333`); as cores são do pedido e não serão trocadas |
| Nome com aspas ou `&` quebrar o DOT | alto | médio | Escape próprio (D-10) e teste com nome hostil |
| O pacote `graphviz` importado no topo derrubar `import app` | alto | baixo | Import dentro da função, protegido por teste de AST |
| `dot` existir mas falhar (layout inválido) | médio | baixo | Captura de `ExecutableNotFound` e de erro de execução → `DOT_AUSENTE`/`ErroDeRenderizacao`, sem arquivo parcial |

## 10. Critério de pronto

- [ ] `src/reporting/visualizer.py` com `texto_dot`, `renderizar_arvore_sugerida` e `ErroDeRenderizacao`
- [ ] `texto_dot` não importa `graphviz` e é determinístico
- [ ] Cores das três classes, aresta rompida tracejada e caixa de evidência no texto DOT
- [ ] `graphviz` pinado em `requirements.txt`; `dot` documentado no `onboarding.md`
- [ ] Testes de DOT, renderização (com skip) e fronteira por AST
- [ ] Suíte completa passa no `.venv`; o skip da renderização aparece no resumo com motivo
- [ ] `app.py`, template, CSS, `mermaid_render.py`, `init.sql`, Docker e banco intocados
- [ ] `git status` lista apenas os arquivos de §5 e os artefatos de `_reversa_forward/030-*`
- [ ] `legacy-impact.md` e `regression-watch.md` gerados nas etapas seguintes

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-plan` | reversa |
