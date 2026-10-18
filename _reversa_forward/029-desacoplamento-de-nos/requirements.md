# Requirements: desacoplamento de nós e gerações virtuais no grafo

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Documento pedido pelo operador em 2026-10-18. O veredito que dispara a transformação é o
> literal de máquina `ERRO CRONICO / QUEBRA DE LINHA` (sem acento), exatamente o mesmo da
> feature `028`; na prosa ele aparece sempre nessa forma, para não haver duas grafias.
>
> **Sobre nomear a biblioteca de grafos.** O documento cita NetworkX porque o operador a exigiu
> no pedido, e porque ela **já** é dependência de runtime (`requirements.txt:22`, `networkx==3.7`)
> — não é escolha de implementação introduzida por este documento, e não adiciona dependência.

## 1. Resumo executivo

O operador já sabe **que** uma linha quebrou — a feature `028` devolve `ERRO CRONICO / QUEBRA DE
LINHA` com o código da anomalia —, mas continua sem saber **o que fazer com isso**. Esta feature
transforma o diagnóstico em uma **árvore sugerida**: uma cópia do grafo em que a junção suspeita é
desacoplada e as gerações que faltam são materializadas como nós virtuais numerados, sem tocar no
GEDCOM, no grafo carregado nem no ramo do doador. A entrega são as funções de manipulação do grafo
(NetworkX) e o fluxo de transformação dos nós, com testes de fixture sintética.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | `core/` decide sem saber de HTTP; a árvore entra **por parâmetro** e a construção do grafo não lê arquivo | 🟢 |
| `_reversa_sdd/architecture.md#4-modelo-de-dados` | `None` significa "não sei / não existe", nunca zero; a árvore **não** é duplicada no banco | 🟢 |
| `_reversa_sdd/domain.md#2-a-regra-central-do-dominio-tres-eixos-que-nao-se-contaminam` | Documental, genético e confronto são eixos separados; o DNA nunca reescreve o vínculo do GEDCOM | 🟢 |
| `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto` | Os quatro estados e seus literais — **não** são tocados por esta feature | 🟢 |
| `_reversa_sdd/domain.md#31-parentesco-documental` | A busca direta sobe **por pais** (FAMC/`child_to_family`); a indireta usa qualquer vínculo, inclusive casamento; a idade só é conferida no caminho direto | 🟢 |
| `_reversa_sdd/domain.md#32-evidencia-genetica` | Chave `(nome, kit)`; **kits diferentes nunca somam cM** | 🟢 |
| `_reversa_sdd/domain.md#7-lacunas` | `L-20`: `get_children` varre todas as famílias sem índice — custo a não repetir na cirurgia | 🟡 |
| `_reversa_sdd/adrs/24-nucleo-puro-arvore-por-parametro.md` | A árvore é **valor**; não há estado global mutável a reescrever | 🟢 |
| `_reversa_sdd/adrs/25-fronteira-de-aplicacao-portas.md` | O núcleo não importa `parsers/`; leitura de arquivo é da fachada de aplicação | 🟢 |
| `_reversa_sdd/adrs/30-aposentar-em-vez-de-apagar.md` | O projeto já escolheu **não apagar**: muda-se a posição/estado, nunca se destrói o registro | 🟢 |
| `_reversa_sdd/addenda/028-validador-de-dados-dna.md` | O veredito de três status é campo separado; `core.validator` é puro e não conhece a árvore | 🟢 |
| `_reversa_forward/028-validador-de-dados-dna/requirements.md#45-contrato-do-resultado` | O contrato do resultado da validação: `status`, `codigos`, `mrca_estimado`, `geracoes_documentais` | 🟢 |
| `src/parsers/gedcom_parser.py` | Grafo **não dirigido** `nx.Graph`; nó de pessoa tem `label` e `type="person"`, nó de família tem `type="family"`; a aresta é sempre pessoa↔família | 🟢 |
| `src/core/path_finding.py` | `find_ancestral_path` devolve o caminho **comprimido**, só com nós de pessoa; a família intermediária não aparece | 🟢 |
| `.reversa/principles.md#i` | Dados reais de DNA/GEDCOM nunca entram no versionamento; teste usa fixture sintética | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `.reversa/principles.md#iv` | Arestas do grafo são **tipadas**: filiação e casamento nunca equivalentes | 🟢 |
| `.reversa/principles.md#v` | Toda suposição de genealogia genética cita a fonte e a data de consulta | 🟢 |

### 2.1 O que já existe e **não** será reimplementado

| Componente | O que já responde | Por que não basta |
|------------|-------------------|-------------------|
| `core.validator` | O veredito de três status, os códigos de anomalia e a estimativa do MRCA | Diagnostica; **não** propõe correção e não conhece o grafo |
| `core.documentary_relationship` | Caminho, `degrees.a_up`/`b_up`, `evidence` por salto e o ancestral comum | Só lê; não altera o grafo |
| `core.path_finding` | O caminho de menor distância subindo por pais | Devolve ids de pessoa, sem a família intermediária que a cirurgia precisa cortar |
| `parsers.gedcom_parser` | O grafo pessoa↔família e o `child_to_family` | Constrói; não transforma |
| `core.documentary_label` | Traduz `(a_up, b_up)` em chave canônica e meioses | Calcula parentesco; não gera hipótese |

### 2.2 A lacuna que esta feature fecha

1. **Nenhum componente altera o grafo.** Toda a extração e todo o ciclo forward até aqui só leem a
   árvore; não existe função que produza uma variante dela.
2. **Nenhum componente separa identidade.** Quando o validador acusa quebra de linha, o registro
   histórico continua ligado ao doador exatamente como o GEDCOM o declarou, e não há artefato que
   proponha onde o vínculo deveria estar.
3. **Nenhum componente materializa o hiato geracional.** O cM estima um número de gerações e o
   caminho documental declara outro; a diferença é calculada e exibida, mas nunca vira estrutura.
4. **Não existe o conceito de "árvore sugerida" com o ramo do doador protegido.** Sem ele, qualquer
   transformação destruiria justamente a parte que o operador sabe ser verdadeira.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador / genealogista | Ver uma hipótese de correção em vez de só o erro | Recebe `ERRO CRONICO / QUEBRA DE LINHA` para um doador vivo de 1985 ligado a um ancestral de 1650 por duas gerações e vê a árvore sugerida com as gerações que faltam |
| Auditor de dados | Conferir se a sugestão mexe no que não devia | Compara o ramo do doador antes e depois e confirma que ids, nomes e datas não mudaram |
| Desenvolvedor do legado | Chamar a cirurgia sem a borda HTTP e sem arquivo | Chama `arvore_sugerida` a partir de um teste, com árvore de fixture e resultado de validação montado à mão |
| Revisor de privacidade | Garantir que nenhum dado real e nenhuma pessoa inventada entraram | Confere que a fixture é sintética e que os nós virtuais não têm nome nem data exata de pessoa |

## 4. Regras de negócio novas ou alteradas

### 4.1 Definições operacionais

| Termo | Definição nesta feature |
|-------|--------------------------|
| **Ramo base** | O doador mais a cadeia de filiação que vai dele até o ancestral histórico, com os nós-família percorridos por essa cadeia. |
| **Junção** | O ponto do caminho em que o ramo base encontra o registro histórico; é a única região que a transformação pode alterar. |
| **Ancestral histórico** | O ancestral comum que o caminho documental declara (`documental["common_ancestor"]`). |
| **Hiato** | Gerações que faltam entre o que o caminho documental tem e o que a estimativa por cM implica. |
| **Geração virtual** | Nó sintético, `type="virtual"`, que ocupa uma posição no caminho sem afirmar pessoa real. |
| **Árvore sugerida** | Cópia transformada do grafo, marcada como hipótese; nunca substitui o GEDCOM. |
| **Lado** | `doador` (descendente que fez o teste) ou `match` (pessoa do GEDCOM associada ao kit). |
| **Aresta de filiação** | O par pessoa↔família em que a pessoa é `HUSB`/`WIFE` (genitor) ou `CHIL`/`FAMC` (filho). Não existe aresta pessoa↔pessoa no grafo. |

**Siglas.** **GEDCOM** é o formato de árvore genealógica (`.ged`); **cM** é centiMorgan; **MRCA** é
*Most Recent Common Ancestor*; **SCP 4.0** é o Shared cM Project 4.0.

### 4.2 Regras

1. **RN-01: o ramo base é imutável.** Nenhum nó do ramo base tem `id`, `label`, `type` ou atributo
   alterado na árvore sugerida, e nenhuma aresta **interna** a ele é removida. A cópia preserva o
   ramo verbatim — o que muda é apenas a junção a montante. 🟢
   - Origem no legado: `_reversa_sdd/adrs/24-nucleo-puro-arvore-por-parametro.md`;
     `_reversa_sdd/adrs/30-aposentar-em-vez-de-apagar.md`
   - Tipo: nova (alcance confirmado em 2026-10-18, §9: "imutável" cobre ids, atributos e arestas
     internas; a única exceção é a junção)

2. **RN-02: a transformação nunca muta a árvore recebida.** Toda a cirurgia acontece sobre
   `grafo.copy()`; o `graph`, o `people`, o `families` e o `child_to_family` recebidos permanecem
   estruturalmente idênticos depois da chamada. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes`
   - Tipo: preservada (é a mesma regra que tirou o estado global do sistema)

3. **RN-03: só há sugestão quando o status é `ERRO CRONICO / QUEBRA DE LINHA`.** `VALIDADO` e
   `INCONCLUSIVO` não geram transformação: devolvem sugestão nula com aviso
   `SUGESTAO_INDISPONIVEL` e o motivo. "Não sei" não autoriza inventar estrutura. 🟢
   - Origem no legado: `_reversa_sdd/addenda/028-validador-de-dados-dna.md` (RN-08/RN-10 da 028)
   - Tipo: nova

4. **RN-04: a identidade é separada, nunca apagada.** Nenhum nó do GEDCOM é removido da árvore
   sugerida. O que muda é **a quem o registro histórico se liga**: o vínculo provado quebrado é
   cortado na cópia e o ramo do doador passa a terminar em um nó virtual. 🟢
   - Origem no legado: `_reversa_sdd/adrs/30-aposentar-em-vez-de-apagar.md`;
     `.reversa/principles.md#ii`
   - Tipo: nova (aplicação do princípio de não destruição à estrutura do grafo)

5. **RN-05: só a filiação é cortada e reconstruída.** A aresta removida é sempre pessoa↔família de
   filiação (`CHIL`/`FAMC` ou `HUSB`/`WIFE` na família do filho). Aresta de casamento **nunca** é
   cortada nem usada como se fosse linha consanguínea. 🟢
   - Origem no legado: `.reversa/principles.md#iv`; `_reversa_sdd/domain.md#31-parentesco-documental`
   - Tipo: preservada (explicitada para esta feature)

6. **RN-06: corta-se uma junção, não o caminho.** A cirurgia altera **um** ponto: a aresta entre a
   família de junção e o genitor histórico (ou entre o filho e essa família, quando o lado é o do
   match). O restante do caminho fica intacto, inclusive os caminhos alternativos, que continuam
   listados e não são reescritos. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental` ("caminhos múltiplos nunca
     são descartados")
   - Tipo: nova (confirmado em 2026-10-18, §9: corta-se a aresta e o registro histórico **não** é
     duplicado)

7. **RN-07: o hiato vem do cM.**
   `hiato = floor(mrca_estimado.geracoes + 0.5) - geracoes_documentais.doador`. O arredondamento é
   **meio para cima** e explícito: `round()` do Python usa arredondamento bancário e faria `2.5`
   virar `2`, perdendo uma geração em silêncio. Só se injeta quando `hiato >= 1`; quando
   `hiato <= 0`, a inconsistência **não** é de profundidade faltante — e "remover geração" está
   proibido por RN-01 e RN-04 —, então a sugestão sai vazia com `HIATO_NAO_POSITIVO`. 🟢
   - Origem no legado: `_reversa_forward/028-validador-de-dados-dna/requirements.md#45-contrato-do-resultado`
   - Tipo: nova (fonte confirmada em 2026-10-18, §9: o cM manda, e a insuficiência é declarada)

8. **RN-08: as gerações virtuais entram na junção, nunca no meio de trecho datado.** Os nós são
   inseridos imediatamente abaixo do ancestral histórico, no lado indicado, para que os saltos
   documentados e plausíveis do ramo base fiquem onde estão. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental` (a idade só é conferida no
     caminho direto, salto a salto)
   - Tipo: nova

9. **RN-09: a distribuição entre os lados é determinística.** Injeta-se no lado que o validador
   acusou (`PROFUNDIDADE_TEMPORAL_INCOMPATIVEL`); com os dois lados acusados, a divisão é
   proporcional ao déficit de anos de cada lado; sem lado identificado (por exemplo, só
   `CM_INCOMPATIVEL_COM_PROFUNDIDADE`), toda a injeção vai para o lado do doador. 🟡
   - Origem no legado: `_reversa_forward/028-validador-de-dados-dna/requirements.md#44-codigos-de-anomalia`
   - Tipo: nova

10. **RN-10: ids e rótulos dos nós virtuais são determinísticos.** O id é derivado do par
    (doador, ancestral, lado, ordem), no formato `VIRTUAL:<doador>:<ancestral>:<lado>:<k>`; o rótulo é
    `Geração <k>`; `type="virtual"`. Nada depende de `id()`, de `hash()` nem da iteração de um `set`. 🟢
    - Origem no legado: `.reversa/principles.md#ii`;
      `_reversa_sdd/domain.md#34-matching-difuso-de-nomes-o-cm-nao-decide-aceitacao` (o desempate por
      `xref_id` foi o que tornou o matching independente de `PYTHONHASHSEED`)
    - Tipo: nova

11. **RN-11: nó virtual não fabrica pessoa.** Não tem nome próprio, não tem data exata e não tem
    sexo. Carrega apenas `nascimento_estimado` como faixa (`ano_min`/`ano_max`) derivada da
    estimativa, `origem="estimado"` e uma `justificativa` em texto. A posição é sugerida; a pessoa é
    desconhecida. 🟢
    - Origem no legado: `.reversa/principles.md#i`; `.reversa/principles.md#v`;
      `_reversa_sdd/architecture.md#4-modelo-de-dados`
    - Tipo: nova

12. **RN-12: a saída é sugestão declarada, não correção.** O resultado carrega
    `natureza="sugestao"`, um aviso fixo de que a árvore **não** substitui o GEDCOM e **não** foi
    validada, e não grava `.ged`, não altera `src/uploads/`, não persiste em banco e não toca na
    tela. 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#4-modelo-de-dados`;
      `_reversa_sdd/addenda/028-validador-de-dados-dna.md`
    - Tipo: nova (confirmado em 2026-10-18, §9: só memória — sem exportação, sem persistência e sem
      tela)

13. **RN-13: o resultado é determinístico e o contrato é estável.** Mesma árvore e mesmo resultado de
    validação produzem o mesmo conjunto de nós, arestas e ids, na mesma ordem; toda ordenação é
    explícita. 🟢
    - Origem no legado: `_reversa_sdd/architecture.md#5-o-fluxo-que-define-o-sistema`;
      `.reversa/principles.md#iii`
    - Tipo: nova

> **Princípios aplicados.** I (fixture sintética e nenhuma pessoa inventada), II (o grafo recebido não
> muda; a sugestão é um valor novo), III (todo invariante com teste), IV (só filiação é linha),
> V (o hiato cita a estimativa da 028, não um número novo). Nenhum conflito com princípio ativo.

### 4.3 Valores de domínio e fontes

Esta feature **não introduz número de domínio novo**. Os valores que ela usa vêm da `028`:

| Constante | Valor | Fonte | Confidência |
|-----------|-------|-------|-------------|
| Faixa de idade por salto | 12–70 anos | `_reversa_forward/028-.../requirements.md#43-valores-de-dominio-e-fontes`; `core.documentary_relationship` | 🟢 |
| Intervalo de geração | mediana da árvore, fallback 25 anos | `core.validator.INTERVALO_DE_GERACAO_PADRAO`; Fenner (2005), DOI [10.1002/ajpa.20188](https://doi.org/10.1002/ajpa.20188), consultado em 2026-10-18 | 🟡 |
| Gerações estimadas pelo cM | `mrca_estimado.geracoes` | `core.validator.estimar_mrca` (SCP 4.0) | 🟢 |
| Idade impossível | 122 anos | `core.janela_de_vida.IDADE_IMPOSSIVEL` | 🟢 |

> **Por que não há limiar novo.** Um "número máximo de gerações virtuais" seria heurística sem
> fonte. O teto desta feature é a própria estimativa do cM; se ela apontar 40 gerações faltantes, o
> resultado são 40 nós — e o aviso de que a sugestão é grosseira, não um corte silencioso.

### 4.4 Códigos de aviso

| Código | Quando aparece | Efeito |
|--------|----------------|--------|
| `SUGESTAO_INDISPONIVEL` | `status` é `VALIDADO` ou `INCONCLUSIVO` | Sugestão nula, com o motivo |
| `HIATO_NAO_POSITIVO` | `hiato <= 0` com status de erro | Sugestão nula; a inconsistência não é falta de geração |
| `SEM_MRCA_ESTIMADO` | Não há `mrca_estimado.geracoes` | Sugestão nula; sem estimativa não há hiato |
| `SEM_CAMINHO_DOCUMENTAL` | O resultado de validação não trouxe caminho | Sugestão nula |
| `AFINIDADE_NAO_INJETAVEL` | O caminho é por afinidade | Sugestão nula; casamento não é linha |
| `JUNCAO_NAO_LOCALIZADA` | A família intermediária do salto não foi encontrada | Sugestão nula, com o salto citado |
| `DOIS_LADOS_ACUSADOS` | Os dois lados têm `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` | Divisão proporcional aplicada e registrada |
| `SUGESTAO_INSUFICIENTE` | A cadeia injetada ainda deixa a idade por geração fora de 12–70 | A sugestão sai, mas declarada insuficiente para resolver a contradição temporal |
| `RAMO_BASE_VIOLADO` | A verificação pós-cirurgia encontrou diferença no ramo | Defensivo: o resultado é descartado |

### 4.5 Entrada necessária (e por que o resultado da 028 não basta)

A cirurgia precisa de **duas** entradas além da árvore: o dicionário `documental` e o resultado de
`validar_comparacao`. O resultado do validador **não carrega** `path.ids` nem `evidence` — ele traz
apenas `mrca_documentado`, `geracoes_documentais` e `status`. Medido em `src/core/validator.py`: os
campos que dizem **onde** cortar vivem só no `documental` (que vem de
`core.documentary_relationship`). Por isso a assinatura da orquestração recebe os dois. 🟢

### 4.6 Fluxo de transformação dos nós

1. **Ler o status.** Se não for `ERRO CRONICO / QUEBRA DE LINHA`, encerrar com sugestão nula e
   `SUGESTAO_INDISPONIVEL` (RN-03).
2. **Recusar afinidade e ausência de caminho.** `status` documental `affinity`, `not_found` ou
   `path.ids` vazio → sugestão nula com o código próprio (RN-04, RN-05).
3. **Montar o ramo base.** Do doador até o ancestral histórico, na ordem do caminho, mais os
   nós-família percorridos. Guardar ids e arestas; é o conjunto protegido (RN-01).
4. **Escolher o lado e localizar a junção.** O lado sai dos códigos do resultado (RN-09: o lado
   acusado, os dois, ou o doador por padrão). Traduzir o primeiro salto desse lado (id de pessoa → id
   de pessoa) para o par pessoa↔família real, consultando `FAMC`/`CHIL` e o `child_to_family`. Não
   achou → `JUNCAO_NAO_LOCALIZADA` (RN-06).
5. **Copiar o grafo.** `grafo.copy()`: estrutura nova, atributos compartilhados e **nunca** mutados
   (RN-02).
6. **Desacoplar.** Remover a aresta de filiação da junção; o registro histórico permanece, com todas
   as suas outras arestas (RN-04). Nada é apagado.
7. **Calcular o hiato.** `floor(geracoes_estimadas + 0.5) - a_up`, para o lado escolhido no passo 4.
   Sem estimativa → `SEM_MRCA_ESTIMADO`; `hiato <= 0` → `HIATO_NAO_POSITIVO` (RN-07).
8. **Injetar.** Criar `k` nós virtuais numerados de 1 a `k` e ligá-los em cadeia de filiação, cada
   elo passando por um nó-família sintético (`type="virtual-family"`), porque no grafo não existe
   aresta pessoa↔pessoa: `Geração 1` é filho do ancestral, `Geração 2` é filho de `Geração 1`, e
   assim por diante até o topo do ramo base (RN-08, RN-10, RN-11).
9. **Conferir a janela resultante.** Com a profundidade nova (`a_up + k`), recalcular
   `(nasc_doador - nasc_ancestral) / (a_up + k)`. Fora de 12–70 → `SUGESTAO_INSUFICIENTE`: a sugestão
   é entregue, mas declarando que **não** resolve a contradição temporal, porque o cM pediu menos
   gerações do que a janela exigiria. Sem o ano do ancestral, a conferência é `None` e não vira
   aviso — `None` não é falso.
10. **Verificar o ramo.** Comparar ids, atributos e arestas internas do ramo base entre o original e a
    cópia. Qualquer diferença → `RAMO_BASE_VIOLADO` e resultado descartado (RN-01).
11. **Emitir.** Devolver a árvore sugerida com a lista de nós e arestas adicionados, a junção, o
    hiato, a justificativa e o aviso de que é sugestão (RN-12, RN-13).

> **Por que a cadeia é pendurada abaixo do ancestral, e não logo acima do doador.** Pendurar perto do
> doador deslocaria datas que o operador conhece; pendurar abaixo do ancestral coloca a incerteza
> onde ela de fato está — entre o registro histórico e a primeira geração documentada do ramo —, e é
> o único ponto em que a junção já vai ser mexida.

> **A cópia não é um GEDCOM, e a diferença é declarada.** No arquivo, quem diz quem é `HUSB`, `WIFE`
> ou `CHIL` é o registro da família; no grafo, o nó de família é **estrutural** e não carrega essa
> lista. Por isso a cirurgia **não** reescreve a composição de uma família existente: ela remove a
> aresta provada errada e cria nós-família sintéticos para os vínculos que inventa. A composição
> original continua no arquivo como a evidência do que o GEDCOM declara — e é justamente por isso
> que a saída se chama árvore sugerida, e não árvore corrigida.

### 4.7 Contrato do resultado

| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `natureza` | `str` | Sempre `"sugestao"` |
| `status_origem` | `str` | O status que disparou a transformação |
| `grafo` | `nx.Graph \| None` | A cópia transformada; `None` quando não há sugestão |
| `doador` | `dict` | `{id, nome}` |
| `ancestral` | `dict` | `{id, nome, ano}`; `ano` pode ser `None` |
| `juncao` | `dict` | `{familia_id, pai_id, filho_id, lado, aresta_removida}`; `None` sem sugestão |
| `hiato` | `dict` | `{calculado, aplicado, por_lado}`; `aplicado` é 0 quando não há injeção |
| `geracoes_virtuais` | `list[dict]` | `{id, label, lado, ordem, nascimento_estimado: {ano_min, ano_max}}` |
| `familias_virtuais` | `list[str]` | Ids das famílias sintéticas criadas (`type="virtual-family"`) |
| `nos_adicionados` | `list[str]` | Ids, em ordem determinística |
| `arestas_adicionadas` | `list[tuple]` | Pares ordenados |
| `arestas_removidas` | `list[tuple]` | Pares ordenados |
| `ramo_base` | `dict` | `{ids, arestas, intacto: bool}` |
| `justificativa` | `str` | Uma frase para o operador, sem jargão de código |
| `avisos` | `list[dict]` | `{codigo, mensagem}`, na ordem de §4.4 |

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | `ramo_base(arvore, doador_id, ancestral_id, caminho)` devolve os ids e as arestas protegidos, em ordem determinística | Must | Para um caminho de 4 pessoas e 3 famílias, devolve exatamente esses ids e as 6 arestas pessoa↔família, na ordem do caminho | 🟢 |
| RF-02 | `ramo_base_intacto(original, sugerida, ramo)` devolve a lista de violações; vazia significa intacto | Must | Teste que remove à força uma aresta interna do ramo na cópia faz a função devolver uma violação com o id do nó | 🟢 |
| RF-03 | `desacoplar_identidade(arvore, juncao)` devolve um grafo novo com a aresta de filiação removida e nada mais alterado | Must | O grafo original continua com a aresta; a cópia não; o nó histórico continua presente com todas as suas outras arestas | 🟢 |
| RF-04 | `injetar_geracoes(grafo, juncao, k, lado, estimativa)` devolve o grafo com `k` nós virtuais em cadeia de filiação | Must | Com `k=3`, existem 3 nós `type="virtual"` rotulados `Geração 1..3`, ligados em sequência por nós-família sintéticos, e `k=0` não altera o grafo | 🟢 |
| RF-05 | `arvore_sugerida(arvore, documental, resultado, doador_id)` orquestra §4.6 e devolve o contrato de §4.7 | Must | Com status de erro, devolve `grafo` não nulo e `natureza="sugestao"`; com `VALIDADO`, devolve `grafo=None` e `SUGESTAO_INDISPONIVEL` | 🟢 |
| RF-06 | O hiato é calculado a partir do cM e só injeta quando é positivo | Must | `geracoes_estimadas=6` e `a_up=2` injetam 4 nós; `geracoes_estimadas=2` e `a_up=2` devolvem `HIATO_NAO_POSITIVO` | 🟢 |
| RF-07 | A distribuição entre os lados segue RN-09 | Should | Só o lado do match acusado injeta tudo no lado do match; os dois lados acusados dividem proporcionalmente e registram `DOIS_LADOS_ACUSADOS` | 🟡 |
| RF-08 | Ids e rótulos dos nós virtuais são determinísticos | Must | Duas chamadas com a mesma entrada produzem os mesmos ids, na mesma ordem; o teste roda com `PYTHONHASHSEED` diferente e o resultado é idêntico | 🟢 |
| RF-09 | A árvore recebida não é mutada | Must | Comparação de nós, arestas e atributos antes e depois da chamada: idênticos; o teste falha se a implementação chamar `remove_edge` no grafo original | 🟢 |
| RF-10 | A cirurgia só toca arestas de filiação | Must | Caminho com casamento no meio não injeta nada e devolve `AFINIDADE_NAO_INJETAVEL`; nenhuma aresta de cônjuge é removida em nenhum cenário | 🟢 |
| RF-11 | Nós virtuais não fabricam pessoa | Must | O nó virtual não tem `name`, `birth` nem `sex` de pessoa; tem `nascimento_estimado` com faixa e `justificativa` não vazia | 🟢 |
| RF-12 | O resultado declara que é sugestão e não escreve nada | Must | `natureza="sugestao"`, aviso fixo presente; nenhum arquivo é criado ou aberto em modo escrita durante a chamada | 🟢 |
| RF-13 | Os testes cobrem os três status, hiato zero e negativo, dois lados, junção não localizada, afinidade e múltiplos kits | Must | A suíte do projeto passa no `.venv` e cada código de §4.4 tem ao menos um teste | 🟢 |
| RF-14 | Docstrings explicam a fórmula do hiato, o formato do id, o que é a junção e por que o ramo base é imutável | Should | Inspeção do módulo mostra a fórmula e a citação à 028 e ao princípio IV | 🟡 |
| RF-15 | A sugestão declara insuficiência quando a cadeia injetada ainda viola a faixa 12–70 | Must | Doador de 1985, ancestral de 1650, 2 gerações documentadas e cM que estima 3: cria 1 nó virtual e emite `SUGESTAO_INSUFICIENTE` | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Arquitetura | A cirurgia fica no núcleo (recebe árvore por parâmetro, devolve valor) e a leitura de arquivo, se houver fachada, fica em `application/` | `ADR-24`/`ADR-25`: o núcleo não importa `parsers/` nem a borda HTTP | 🟢 |
| Dependência | Nenhuma dependência nova: `networkx==3.7` já é dependência de runtime e `requirements.txt` não muda | `requirements.txt` linha 22 | 🟢 |
| Determinismo | Mesma entrada produz o mesmo grafo, os mesmos ids e a mesma ordem; nada depende de iteração de `set`, `hash()` ou `id()` | `RN-10`; o projeto já fechou o desempate por `xref_id` | 🟢 |
| Pureza | Sem arquivo, sem relógio, sem HTTP, sem estado global e sem escrita em disco | `ADR-24`; `_reversa_sdd/architecture.md#3-...` | 🟢 |
| Desempenho | Custo O(V+E) por sugestão; cópia de **estrutura** (`graph.copy()`), nunca `deepcopy`, e nenhuma varredura linear de famílias por salto (`L-20`) | `_reversa_sdd/domain.md#7-lacunas` (L-20); a árvore real tem 35.460 pessoas | 🟡 |
| Privacidade | Nenhum dado real de DNA/GEDCOM em código, teste ou fixture; nós virtuais sem nome de pessoa e sem data exata; a sugestão não é persistida | `.reversa/principles.md#i`; `RN-11`, `RN-12` | 🟢 |
| Compatibilidade | Python 3.14.6 do `.venv`; `networkx` 3.7 | `requirements.txt`; `setup.json` | 🟢 |
| Observabilidade | O resultado explica o que foi feito: `justificativa`, `juncao`, `hiato` e `avisos`; nenhum `print` e nenhum log de dado pessoal | Contrato de §4.7 | 🟢 |
| Concorrência | n/a: não há estado compartilhado, cache nem escrita; a transformação é pura e reentrante, e duas chamadas simultâneas não compartilham grafo | `ADR-24` (o estado global saiu); `RN-02` | 🟢 |
| Testabilidade | As funções são puras e o teste monta a árvore com fixture sintética, sem banco, rede ou arquivo | `.reversa/principles.md#iii`; `tests/fixtures/` | 🟢 |
| Documentação | A docstring cita a fonte da estimativa do cM (SCP 4.0) e o motivo de a cadeia ser pendurada na junção | `.reversa/principles.md#v` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: doador vivo ligado a ancestral do século XVII recebe árvore sugerida
  Dado um doador nascido em 1985 e um ancestral documentado nascido em 1650
  E um caminho com 2 gerações no lado do doador
  E um resultado de validação com status "ERRO CRONICO / QUEBRA DE LINHA"
  E uma estimativa de 6 gerações pelo cM
  Quando a árvore sugerida é montada
  Então o grafo sugerido tem 4 nós virtuais rotulados "Geração 1" a "Geração 4"
  E a junção registra a aresta de filiação que foi cortada
  E o resultado declara natureza "sugestao"

Cenário: o ramo base do doador não muda
  Dado um grafo com um doador e sua cadeia de filiação até o ancestral
  Quando a árvore sugerida é montada
  Então os ids, os nomes e as datas do ramo base são idênticos aos do original
  E nenhuma aresta interna ao ramo base foi removida

Cenário: o grafo original permanece intacto
  Dado um grafo carregado de fixture
  Quando a árvore sugerida é montada
  Então o grafo original continua com todas as arestas que tinha
  E nenhum atributo de nó foi alterado

Cenário: comparação validada não gera sugestão
  Dado um resultado de validação com status "VALIDADO"
  Quando a árvore sugerida é montada
  Então o grafo sugerido é nulo
  E o aviso SUGESTAO_INDISPONIVEL está presente

Cenário: comparação inconclusiva não gera sugestão
  Dado um resultado de validação com status "INCONCLUSIVO"
  Quando a árvore sugerida é montada
  Então o grafo sugerido é nulo
  E nenhum nó virtual foi criado

Cenário: hiato não positivo
  Dado um resultado de erro cujo cM estima 2 gerações
  E um caminho que já tem 2 gerações no lado do doador
  Quando a árvore sugerida é montada
  Então o grafo sugerido é nulo
  E o aviso HIATO_NAO_POSITIVO está presente

Cenário: sugestão insuficiente é declarada
  Dado um doador nascido em 1985 e um ancestral nascido em 1650
  E um caminho que já tem 2 gerações no lado do doador
  E uma estimativa de 3 gerações pelo cM
  Quando a árvore sugerida é montada
  Então 1 nó virtual é criado
  E o aviso SUGESTAO_INSUFICIENTE está presente
  E a justificativa diz que a sugestão não resolve a contradição temporal

Cenário: caminho por afinidade não é injetado
  Dado um caminho que chega ao outro ramo por casamento
  Quando a árvore sugerida é montada
  Então nenhuma aresta de casamento é removida
  E o aviso AFINIDADE_NAO_INJETAVEL está presente

Cenário: determinismo do id do nó virtual
  Dado o mesmo grafo e o mesmo resultado de validação
  Quando a árvore sugerida é montada duas vezes, em processos com PYTHONHASHSEED diferente
  Então os ids dos nós virtuais são exatamente os mesmos
  E a ordem dos nós adicionados é a mesma

Cenário: nó virtual não inventa pessoa
  Dado um nó virtual criado pela injeção
  Quando seus atributos são inspecionados
  Então ele não tem nome próprio, sexo nem data exata de nascimento
  E tem uma faixa estimada e uma justificativa

Cenário: múltiplos kits, apenas o quebrado recebe sugestão
  Dado dois kits para o mesmo doador, um "VALIDADO" e outro "ERRO CRONICO / QUEBRA DE LINHA"
  Quando as sugestões são montadas
  Então só o kit com erro produz grafo sugerido
  E o kit validado produz grafo nulo com SUGESTAO_INDISPONIVEL

Cenário: junção não localizada
  Dado um caminho cujo salto não tem família intermediária localizável
  Quando a árvore sugerida é montada
  Então o grafo sugerido é nulo
  E o aviso JUNCAO_NAO_LOCALIZADA cita o salto
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem ramo base identificável e verificável, a proteção do requisito 1 é promessa sem prova |
| RF-03 | Must | É o desacoplamento de identidade do requisito 2 |
| RF-04, RF-06 | Must | É a injeção de gerações do requisito 3 |
| RF-05 | Must | Sem a orquestração, as três peças não formam fluxo |
| RF-08, RF-09, RF-10 | Must | São os invariantes: determinismo, não mutação e só filiação |
| RF-11, RF-12 | Must | Privacidade e honestidade da sugestão |
| RF-13 | Must | `.reversa/principles.md#iii` |
| RF-07 | Should | A divisão entre lados melhora a sugestão, mas a regra do lado único já entrega valor |
| RF-14 | Should | Documentação e fonte são exigidas pelo projeto, mas não mudam o grafo |
| RF-15 | Must | Sem declarar a insuficiência, a sugestão mentiria sobre ter resolvido a contradição |
| Exportação da árvore sugerida (JSON/GEDCOM) | Won't (esta feature) | Decidido em §9: só memória. Exportar GEDCOM sugerido criaria um arquivo de árvore com nós sem pessoa |
| Persistência em banco | Won't (esta feature) | Decidido em §9: nenhuma tabela nova; o banco grava retrato de análise, não hipótese |
| Exibição na tela | Won't (esta feature) | Decidido em §9: o contrato de tela é congelado por hash e por teste; mudança de UI é feature separada |

## 9. Esclarecimentos

### Sessão 2026-10-18

- **Q:** Até onde vai a entrega da árvore sugerida?
  **R:** Só memória — funções puras e testes. Sem exportação JSON/GEDCOM, sem persistência em banco
  e sem alteração de tela. Consistente com a `028`, que também entregou módulo + testes.
- **Q:** O que o desacoplamento faz com o registro do ancestral histórico?
  **R:** Corta a aresta de filiação provada errada e pendura a cadeia virtual no lugar. O registro
  histórico permanece **um só**, com todas as suas outras arestas; nenhum nó do GEDCOM é duplicado
  nem removido.
- **Q:** Qual grandeza decide quantas gerações virtuais injetar?
  **R:** O cM, como pedido (`mrca_estimado.geracoes`). Quando a cadeia resultante ainda deixar a
  idade por geração fora de 12–70, a sugestão é entregue com o aviso `SUGESTAO_INSUFICIENTE` — ela
  não finge ter resolvido a contradição temporal que o validador provou.
- **Consequência técnica registrada:** a fórmula do hiato usa arredondamento **meio para cima**
  (`floor(x + 0.5)`), e não `round()`, porque o arredondamento bancário do Python transformaria
  `2.5` em `2` e perderia uma geração sem aviso.

## 10. Lacunas

Nenhuma lacuna aberta após a sessão de esclarecimentos de 2026-10-18. As três dúvidas iniciais
(escopo, semântica do desacoplamento e fonte do hiato) foram resolvidas em §9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-18 | Auto-validação de qualidade: explicitada a origem da citação a NetworkX, os nós-família sintéticos, a concorrência n/a e o contrato de `familias_virtuais` | reversa |
| 2026-10-18 | Sessão de esclarecimentos: só memória, corta a aresta sem duplicar o registro, hiato pelo cM com aviso de insuficiência e arredondamento meio para cima | reversa |
