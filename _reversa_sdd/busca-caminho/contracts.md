# Unit `busca-caminho` — Contratos

> Re-extração de **2026-10-10** (nível **Completo**). Substitui o artefato de 2026-10-05, que fixava o grafo por **import tardio de uma global** e o índice de nomes invalidado por `gedcom_state.versao` — **nenhum dos dois existe mais**.
> Este arquivo fixa **o que atravessa a fronteira** da unit: o contrato HTTP, o do parentesco documental, os avisos, a afinidade, o **contrato de escape**, o desfecho tipado, o diagrama e a falha.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Contrato HTTP

| Método | Caminho | Ação | Entrada | Status | Corpo da resposta |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/` | `path_search` | `gedcom_filename`, `person1_name`, `person2_name` | `200` | HTML com `path_result` e/ou `message`, `success`, `all_names` |
| `POST` | `/` (qualquer `action`) | — | corpo acima de **16 MB** | **`413`** | HTML com `"Arquivo maior que o limite de 16 MB."` |

### 1.1 Contrato da requisição

| Campo | Local | Obrigatório | Observação |
| --- | --- | --- | --- |
| `action` | `form` | sim | literal `path_search` 🟢 |
| `gedcom_filename` | `form` | sim | **Referência** validada por forma; a árvore é resolvida e parseada por `_arvore_do_formulario` 🟢 |
| `person1_name` | `form` | sim | Recebe `strip()` na rota **e** no núcleo 🟢 |
| `person2_name` | `form` | sim | idem 🟢 |

> 🟢 **Não há arquivo nesta requisição** — a busca opera só sobre a árvore já armazenada, endereçada pela referência. O corpo é `application/x-www-form-urlencoded`.

### 1.2 Contrato da resposta

| Variável | Quando vem | Significado |
| --- | --- | --- |
| `path_result` | nos dois desfechos de **sucesso** | O resultado completo; **ausente** quando não há conexão 🟢 |
| `message` | sempre | Texto ao operador — §7 🟢 |
| `success` | sempre no `POST` | `True` em sucesso **e em "sem conexão"**; `False` só em erro de entrada 🟢 |
| `all_names` | sempre | Lista de nomes da árvore, para os formulários não esvaziarem 🟢 |
| `gedcom_filename` | sempre | Devolvido para o próximo `POST` 🟢 |

> ⚠️ **Três desfechos, duas formas de payload — e a tela distingue os três.** "Conexão encontrada", "nenhuma conexão" e "pessoa não encontrada" chegam ao template como: `success=True` + `path_result`; `success=True` + **sem** `path_result`; `success=False` + mensagem. A distinção é feita pelo alerta (cor por `success`) e pelo cartão (presença de `path_result`) — verificado em 2026-10-05, o que fecha a lacuna `L-06`. 🟢

### 1.3 Contrato do desfecho tipado *(novo em 2026-10-10)*

| O que o núcleo devolve | `Desfecho` | Modo de renderização |
| --- | --- | --- |
| payload, `success=True` | `RESULTADO` | cartão de resultado 🟢 |
| `None`, `success=True` | `SEM_RESULTADO` | "nenhuma conexão encontrada", **com sucesso** 🟢 |
| `None`, `success=False` | `ERRO_DE_ENTRADA` | alerta de erro 🟢 |

> 🟢 **O desfecho é derivado de `(payload, sucesso)`, nunca do texto da mensagem.** A ordem dos testes é a precedência: payload presente é `RESULTADO` mesmo que o indicador viesse falso — e ele não vem, nos três estados que o núcleo produz. Sem o enum, o adaptador teria de distinguir os dois últimos pelo **texto**, dando ao literal de tela autoridade semântica.
>
> 🟢 **A tupla de três elementos do núcleo é contrato de paridade** — o harness compara o indicador de sucesso contra o oráculo, e nove asserções de teste a desempacotam. **Não mudar a forma.**
>
> 🟢 **A fronteira devolve `dados`, e não `path_result`:** nome de campo de template não atravessa a fronteira. O adaptador decide sob que nome (se algum) ele vai ao template. As dependências de diagrama **não** são montadas pelo caso de uso: chegam por parâmetro, montadas **uma vez na borda**.

---

## 2. Contrato do parentesco documental

### 2.1 O conjunto de estados

| Estado | Quando | Acompanha | Conf. |
| --- | --- | --- | --- |
| `not_found` | Registro ausente (`pessoa_ausente`) **ou** nenhum caminho dentro do teto (`sem_caminho`) | rótulo `"Parentesco documental não encontrado"` | 🟢 |
| `found` | Há caminho e a identidade **não** é ambígua | `label`, `relationship_key`, `meioses`, `degrees` | 🟢 |
| `ambiguous` | Há caminho **e** o dossiê de homônimos é ambíguo | + aviso `homonimo` | 🟢 |
| `affinity` | **Atribuído pelo chamador** quando o caminho direto falha e o indireto existe | + `affinity_path` + aviso `afinidade` | 🟢 |

> ⚠️ **`affinity` é o único estado definido fora do módulo que o calcula.** `documentary_relationship` devolve `not_found`, e `path_search` **sobrescreve** status, rótulo e avisos — **numa cópia** do dicionário. Quem ler apenas o módulo de parentesco **não** descobre que este estado existe (`M-01`). 🟢
>
> ⚠️ **O `status` é mais grosseiro que a causa:** com identidade ambígua **e** sem caminho, o status permanece `not_found` e a ambiguidade aparece **apenas** como aviso (`M-02`). Quem mapear os quatro valores e descartar os avisos perde a maior parte da regra. 🟢

### 2.2 Campos do resultado

| Campo | Contrato | Conf. |
| --- | --- | --- |
| `status` | Um dos quatro acima | 🟢 |
| `source` | `"GEDCOM"` — a afirmação é **documental** | 🟢 |
| `label` | Rótulo legível do parentesco | 🟢 |
| `relationship_key` | Chave canônica que casa com a tabela do Shared cM Project; `None` quando não há (ex.: afinidade) | 🟢 |
| `meioses` | Saltos pai-filho entre as duas pessoas — **a grandeza que o cM mede**; `deg_a + deg_b` em todos os casos | 🟢 |
| `degrees` | `{a_up, b_up, cousin_degree, removed}` | 🟢 |
| `person_a` / `person_b` | **Fichas completas** (**13** campos), sempre — inclusive quando não há caminho | 🟢 |
| `common_ancestor` / `common_ancestors` | O principal (`{id, name, birth}`) e **todos** até 12 níveis | 🟢 |
| `path` | `{ids, names}` do caminho principal | 🟢 |
| `additional_paths` | Caminhos alternativos — **nenhum descartado** | 🟢 |
| `evidence` | **Um item por aresta** do caminho: família, casal declarado, datas, idade implícita e `plausible` | 🟢 |
| `homonyms` | Dossiê de ambiguidade | 🟢 |
| `ambiguous_identity` | Atalho booleano para `homonyms.ambiguous` | 🟢 |
| `warnings` | Lista de `{code, message}` — §3 | 🟢 |

### 2.3 Tradução de graus

| Condição | Rótulo | Chave |
| --- | --- | --- |
| Ambos zero | mesma pessoa | `SELF` 🟢 |
| Um zero, `n = 1` | Pai/Mãe | `PARENT_CHILD` 🟢 |
| Um zero, `n = 2` | Avô/Avó | `GRANDPARENT` 🟢 |
| Um zero, `n > 2` | prefixo `bis` repetido `n−2` vezes | — 🟢 |
| Menor 1, maior 1 | Irmãos | `SIBLINGS` 🟢 |
| Menor 1, maior 2 | Tio/Tia | `AUNT_UNCLE` 🟢 |
| Menor 1, maior > 2 | Tio/Tia com `bis` repetido | `GREAT_AUNT_k` 🟢 |
| Demais | Primos de `g` grau com `r` remoções | `gC` / `gCrR`, com `g = menor−1` e `r = maior−menor` 🟢 |

> 🟡 **`bis` é repetido, não traduzido:** "bisbisavô" onde o português genealógico diria "trisavô". O rótulo usa numerais ordinais até 10º e o número cru acima disso.

---

## 3. Contrato dos avisos

| Código | Gatilho | Efeito no resultado | Conf. |
| --- | --- | --- | --- |
| `pessoa_ausente` | Registro não existe em `people` | `status = not_found` | 🟢 |
| `sem_caminho` | Nenhum percurso por pais dentro do teto de `MAX_DEPTH` | `status = not_found`; a mensagem **afirma que isso não prova ausência de parentesco** | 🟢 |
| `homonimo` | Mais de um registro com o mesmo nome normalizado | `status = ambiguous` **se houver caminho**; aviso em ambos os casos | 🟢 |
| `data_impossivel` | Idade de genitor fora de 12–70 anos | **Nenhum** — o vínculo é mantido e o caminho exibido | 🟢 |
| `caminhos_multiplos` | Mais de um percurso distinto até o par | **Nenhum** — o exibido é o de menor distância total | 🟢 |
| `colapso_de_pedigree` | Mesmo ancestral por mais de uma cadeia (teto 8) | **Nenhum** | 🟢 |
| `afinidade` | Caminho indireto encontrado | `status = affinity` + rótulo próprio | 🟢 |

> ⚠️ **`MAX_DEPTH` está interpolado na mensagem** do aviso `sem_caminho`. Mudar o teto é mudar **texto de contrato**.

---

## 4. Contrato de afinidade

Quando o caminho direto falha e existe caminho indireto, **três marcas simultâneas** o identificam — redundância deliberada, porque o risco é o operador ler afinidade como consanguinidade:

| # | Marca |
| --- | --- |
| 1 | `documentary["status"] = "affinity"` 🟢 |
| 2 | Rótulo `"Sem ancestral comum: conexão por afinidade (casamento)"` 🟢 |
| 3 | Aviso **em maiúsculas**: *"O caminho exibido passa por casamento/afinidade, e não por ancestral comum: ele NÃO representa parentesco consanguíneo."* 🟢 |

**Garantias adicionais** 🟢

- `relationship_key` permanece `None` (não há parentesco canônico a casar).
- `affinity_path` (`{ids, names}`) é o traço do caminho por casamento.
- O diagrama passa a ser o de **ponte**, com a aresta de casamento explícita.
- **Nenhum caminho é inventado a partir da afinidade**: ela é um caminho **real** no grafo de famílias, apenas não consanguíneo.
- A marcação é feita numa **cópia** do dicionário; o original em cache permanece `not_found` (`M-01`). 🟡

---

## 5. Contrato de escape (o mais crítico da unit)

### 5.1 Id do nó

| Regra | Conf. |
| --- | --- |
| Coleção → primeiro elemento | 🟢 |
| `@` removido; `+` → `_` | 🟢 |
| Tudo fora de `[A-Za-z0-9_]` é removido | 🟢 |
| Prefixo `N_` | 🟢 |
| O `sid` do par de cônjuges usa os dois ids **ordenados** unidos por `+` — logo, independente da ordem recebida | 🟢 |
| Resultado **sempre** um identificador válido para a gramática | 🟢 |

### 5.2 Rótulo — a ordem é o contrato

| Ordem | Operação | Conf. |
| ---: | --- | --- |
| 1 | Normalização **NFC** | 🟢 |
| 2 | Espaço inquebrável → espaço; travessões → hífen; aspas curvas → apóstrofo | 🟢 |
| 3 | Aspa dupla → apóstrofo | 🟢 |
| 4 | Quebras de linha achatadas | 🟢 |
| 5 | **Lista branca**: remove tudo que não consta | 🟢 |
| 6 | **Só então** `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;` | 🟢 |

> ⚠️ **A ordem dos passos 5 e 6 é invariante.** Se as entidades vierem **antes** do filtro, o filtro pode remover pedaços de uma entidade já escapada. A lista branca substituiu uma lista **negra** que era furada pela **crase** (`BUG-20260929-J6PQ`); a versão seguinte era **estreita demais** e descartava 14 caracteres sem intenção (`BUG-20261002-T4ZM`). Nenhuma das duas correções pode ser desfeita (`adrs/05`).

### 5.3 Por que o escape é necessário

O texto do nó é interpretado pela **gramática do Mermaid**. O gatilho confirmado é a sequência **aspa dupla seguida de crase**: o lexer desvia para *markdown-string*, o fecha-colchete nunca vira o token exigido, e o **diagrama inteiro** cai — sem erro que o servidor perceba. 🟢

| Camada de defesa | Cobre | **Não** cobre |
| --- | --- | --- |
| Escape do rótulo e do id | A **gramática** do Mermaid | — 🟢 |
| `securityLevel: 'strict'` no template | XSS/HTML embutido | A gramática 🟢 |

> 🔴 **Não há terceira camada.** O escape é a **única** defesa contra conteúdo do GEDCOM quebrar o diagrama.
>
> 🟢 **O critério da lista é INERTE, e não "seguro":** dentro do estado `string` o lexer consome tudo com `<string>[^"]+`, então colchete, dois pontos, barra e palavra-chave são inertes. O que **não pode passar** é a aspa dupla e a crase.

---

## 6. Contrato do diagrama

| Tipo de conexão | Emissor | Forma |
| --- | --- | --- |
| Direta | `generate_mermaid_graph` | `flowchart BT`; **nó de casal** quando o MRCA não é extremidade do caminho; linhagem direta é `ac_idx` em `-1`, `0` ou no último nó; os dois membros do casal são **omitidos** como nós próprios quando o casal é emitido 🟢 |
| Indireta | `generate_mermaid_graph_indirect_bridge` | Subgrafos **aninhados** (`COLUMNS`, `ESQ`/`DIR`, `*_COLS`, `*_L`, `*_R`) com `direction BT`; casamento como aresta rotulada entre **âncoras invisíveis**; cada `subgraph` fechado por **context manager**; delega ao diagrama direto com `mrca=None` quando falta pré-requisito 🟢 |

**Cores fixas por papel** 🟢: p1 verde, p2 vermelho, MRCA/casal amarelo e o casal da afinidade laranja.

**Contrato com a apresentação** 🟢: o renderizador **não importa `core`**. Ele recebe `dominio` — o `dict` de **sete consultas** ligadas à árvore pelo resolvedor de diagrama. As decisões de **layout continuam no renderizador**, porque decidir o casal do ancestral comum é decisão de negócio (`ADR-11`).

---

## 7. Contrato de mensagens

| Literal | Categoria |
| --- | --- |
| `"Conexão direta encontrada (ancestral comum)."` | Sucesso — `RESULTADO` 🟢 |
| `"Conexão indireta encontrada (via casamento/afinidade)."` | Sucesso — `RESULTADO` 🟢 |
| `"Nenhuma conexão encontrada entre '{p1}' e '{p2}'."` | Sem resultado — `SEM_RESULTADO`, **`success=True`** 🟢 |
| `"Pessoa 1 '{nome}' não encontrada."` / `"Pessoa 2 '{nome}' não encontrada."` | Erro de entrada — `ERRO_DE_ENTRADA`, `success=False` 🟢 |
| `"Sem ancestral comum: conexão por afinidade (casamento)"` | Rótulo do parentesco 🟢 |
| `"Pessoas não encontradas no GEDCOM"` / `"Parentesco documental não encontrado"` | Rótulos de `not_found` 🟢 |
| `AVISO_AFINIDADE` (maiúsculas) | Alerta obrigatório 🟢 |
| `"Ocorreu um erro: {e}"` | Erro inesperado, pela rota 🟢 |
| Molduras de erro de domínio | Pela **tabela de tradução compartilhada** (`application/traducao.py`) — ver a unit `analise-dna` §7.2 🟢 |

> 🟢 **Nenhum literal de tela tem autoridade semântica.** O modo de renderização vem do **desfecho**; o texto é consequência, não causa.

---

## 8. Contrato de falha

| Situação | O que **é** garantido | O que **não** é |
| --- | --- | --- |
| Pessoa não resolvida | Mensagem que distingue Pessoa 1 de Pessoa 2; `success=False` | — 🟢 |
| Sem conexão | Mensagem própria com `success=True`; **não é erro**, e a tela o distingue por cor e pela ausência do cartão | — 🟢 |
| Caminho mais fundo que `MAX_DEPTH` | Indistinguível de "sem caminho"; o aviso diz que não prova ausência de parentesco | 🔴 **Corte silencioso** — decisão humana de preservar |
| Caminho indireto acima de `MAX_HOPS` | Rejeitado | 🔴 Indistinguível de "sem caminho" |
| Nó Mermaid com caractere hostil | Rótulo e id sanitizados; diagrama válido | 🔴 Não há terceira camada de defesa |
| `subgraph` mal fechado | **Estruturalmente impossível** — o `end` é escrito pelo context manager | — 🟢 |
| Data cronologicamente impossível | Aviso + vínculo mantido | 🔴 Nada é corrigido no GEDCOM |
| Sem data para julgar | `plausible = None` — **não** é falso | — 🟢 |
| Colapso além do teto | — | 🔴 **Não detectado**, e o silêncio é idêntico a "sem colapso" |
| Segunda árvore de mesmo tamanho e mesmos xrefs extremos no mesmo processo | — | 🟢 **CONFIRMADO por execução em 2026-10-10:** o índice de nomes **não** é reconstruído, e o dossiê cita um xref **que não existe na segunda árvore** (`"existem na arvore B? {'@I2@': False}"`), degradando em silêncio (`L-24`). A correção foi **aceita** e será executada depois do Passo 4 |
| Empate triplo na ordenação de ancestrais comuns | — | 🟡 A ordem pode variar com o `PYTHONHASHSEED` (`L-25`) |
| Exceção inesperada | `"Ocorreu um erro: {e}"` na tela | Nada é registrado em log 🔴 |

---

## 9. Compatibilidade e versionamento

| Elemento do contrato | Estabilidade exigida | Consequência de mudar |
| --- | --- | --- |
| Ordem `filtro → entidades` no rótulo | **Crítica** | Reabre o `BUG-20260929-J6PQ`: o diagrama inteiro deixa de renderizar |
| Lista branca do rótulo | **Crítica** | Estreitá-la descarta caracteres legítimos (`T4ZM`); ampliá-la reabre o vetor da crase |
| Forma da **tupla de três** do núcleo | **Crítica** | É contrato de paridade: o harness e nove asserções a desempacotam |
| O desfecho derivar de `(payload, sucesso)`, nunca do texto | **Crítica** | Voltar ao texto dá autoridade semântica ao literal de tela |
| Os quatro valores de `status` | **Alta** | O template ramifica sobre `found`, `ambiguous` e `affinity` |
| Marcação de afinidade em três lugares | **Alta** | Redundância protetiva; remover uma marca reduz a proteção contra leitura errada |
| Varredura **condicional** de `get_spouses` | **Alta** | Torná-la complementar **muda** o resultado da busca indireta |
| `dados` **não** ser renomeado para `path_result` na fronteira | **Alta** | Reintroduz nome de campo de template atravessando a fronteira |
| Que o renderizador **não** importe `core` | **Alta** | Reabre o ciclo `core/` ↔ `reporting/` que o `ADR-34` fechou |
| Valor de `MAX_DEPTH` | Média | Altera o **texto** do aviso `sem_caminho` e o alcance da busca direta |
| O teto contar **iterações**, e não gerações | **Alta** | Reinterpretar muda o alcance real do corte |
| `success=True` em "sem conexão" | **Alta** | Inverter trata ausência de resultado como erro |
| Chave do cache de nomes | **Alta** | Ampliá-la para algo derivado do conteúdo é a correção de `L-24`, e **não** muda resultado nenhum, só o custo de reconstrução |

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração). Substitui a versão de 2026-10-05.*
