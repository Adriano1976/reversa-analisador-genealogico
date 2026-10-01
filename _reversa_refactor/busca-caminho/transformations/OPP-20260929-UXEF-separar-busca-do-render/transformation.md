---
schema_version: 1
id: OPP-20260929-UXEF
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: equivalence-proof
  evidence:
    - before-after/ensaio-divisao.txt
    - safety-net/pytest-after-apply.txt
    - before-after/acoplamento-antes.txt
    - before-after/custo-import-antes.txt
measurement:
  before: "5 blocos num arquivo de 508 linhas, com 5 banners do proprio autor. O bloco de render ocupa 278 linhas (54,7%) e carrega unicodedata e as regras de escape; a busca ocupa 61. O grafo entre blocos tinha o ciclo render -> busca -> render, via handler"
  after: "4 modulos em dependencia estritamente descendente, sem ciclo e sem import tardio novo. render isolado em 296 linhas como autoridade de escape; networkx confinado em path_finding; unicodedata e re confinados em mermaid_render. Custo de import inalterado, e o porque esta medido"
change_set:
  - chg: CHG-001
    kind: code
    artifact: analisador-genealogico/reconstructed/family_navigation.py
    purpose: Novo modulo com a resolucao de pessoa por nome e a navegacao familiar (7 simbolos)
    diff: CHG-001.diff
  - chg: CHG-002
    kind: code
    artifact: analisador-genealogico/reconstructed/path_finding.py
    purpose: Novo modulo com MAX_DEPTH, MAX_HOPS e os dois algoritmos de busca
    diff: CHG-002.diff
  - chg: CHG-003
    kind: code
    artifact: analisador-genealogico/reconstructed/mermaid_render.py
    purpose: Novo modulo com o diagrama Mermaid e o contrato de escape do rotulo
    diff: CHG-003.diff
  - chg: CHG-004
    kind: code
    artifact: analisador-genealogico/reconstructed/path_search.py
    purpose: Passa a compor o fluxo, mantendo o handler e a superficie de compatibilidade
    diff: CHG-004.diff
approval:
  by: user
  at: 2026-10-01T15:06:38-03:00
reversible_via: [CHG-001.diff, CHG-002.diff, CHG-003.diff, CHG-004.diff]
---

## Um aviso sobre esta oportunidade

A proposta original de três módulos **não era realizável como estava escrita**, e o achado está
detalhado na seção 3. O que foi aplicado é a Opção A, aprovada no gate do plano: quatro módulos em
dependência estritamente descendente, em vez de três com um import tardio.

## Responsabilidades antes

O arquivo tinha 508 linhas e cinco banners escritos pelo próprio autor. Como na ZV52, a fronteira não
foi inventada: estava declarada no arquivo.

| Bloco | Linhas | Tam. | Responsabilidade | Depende de fora |
|-------|--------|------|------------------|-----------------|
| `head` | 1-27 | 27 | docstring, imports, `MAX_DEPTH`, `MAX_HOPS` | - |
| `resolucao` | 28-41 | 14 | resolução de pessoa por nome | `.upload` |
| `navegacao` | 42-125 | 84 | navegação familiar | `.upload` |
| `busca` | 126-186 | 61 | busca de caminho | `.upload`, `collections`, **networkx** |
| `render` | 187-464 | 278 | renderização Mermaid | `.upload`, `re`, **unicodedata** |
| `handler` | 465-508 | 44 | fluxo | `.upload` |

## Acoplamento medido

Por AST, com `before-after/analise_blocos.py` e saída em `before-after/acoplamento-antes.txt`. O
instrumento também rastreia quais nomes **importados** cada bloco usa, porque é isso que decide os
imports dos módulos novos.

```
busca    -> head, navegacao
render   -> busca, navegacao
handler  -> busca, head, render, resolucao
```

## O ciclo que a oportunidade não previu

A OPP propõe três módulos, deixando `path_search.py` com a busca **e** o handler. Mas o render precisa
da busca, e o handler precisa do render:

| Aresta | Evidência |
|--------|-----------|
| `render -> busca` | `find_ancestral_path` usado nas linhas 295 e 381, dentro de `generate_mermaid_graph_indirect_bridge` |
| `handler -> render` | `generate_mermaid_graph` (490) e `generate_mermaid_graph_indirect_bridge` (499) |

Com a busca e o handler no mesmo módulo, isso vira `path_search -> mermaid_render -> path_search`. A
OPP não registra esse ponto. Antes de escolher, considerei também repassar o caminho ancestral como
parâmetro para o render, o que eliminaria a aresta: descartado, porque mudaria assinatura, e a
oportunidade é de modularização, não de mudança de contrato.

**Opção A, aplicada.** O handler sai do módulo da busca e passa a compor os três. Justificativa pelo
domínio, não pela estética: a decisão #5 da alma, "conexão direta primeiro, afinidade como fallback",
é a **política** que o handler implementa, e os dois algoritmos são o **mecanismo**.

```
family_navigation  ->  .upload
path_finding       ->  family_navigation, .upload, collections, networkx
mermaid_render     ->  family_navigation, path_finding, .upload, re, unicodedata
path_search        ->  family_navigation, path_finding, mermaid_render, .upload
```

**Opção B, descartada** no gate: os três módulos da OPP, com o handler importando o render dentro da
função, como o arquivo já faz com `graph`. Ficou registrada como a alternativa de menor diff. A
diferença entre as duas era de uma decisão: um módulo a mais, ou um import tardio a mais.

## A fronteira aplicada

| Módulo | Responsabilidade única | Linhas |
|--------|------------------------|--------|
| `family_navigation.py` | quem é parente de quem, na árvore carregada | 106 |
| `path_finding.py` | achar o caminho entre duas pessoas | 85 |
| `mermaid_render.py` | emitir o diagrama, e as regras de escape do rótulo | 296 |
| `path_search.py` | compor o fluxo e manter a superfície pública | 112 (eram 508) |

## Ganho medido

### O que eu esperava e caiu

Eu esperava que a divisão reduzisse o custo de import de quem só quer a busca. Medi antes de propor:

| Alvo | Módulos | ms | Dependências caras |
|------|---------|----|--------------------|
| `reconstructed.path_search` | 503 | 482 | ged4py, networkx |
| `reconstructed.upload` | 501 | 525 | ged4py, networkx |
| `reconstructed.domain` | 67 | 19 | nenhuma |

O arquivo inteiro custa **2 módulos a mais** que o `.upload` sozinho, e a diferença de tempo ficou
dentro do ruído: entre duas execuções, o próprio `upload` variou de 416 ms para 525 ms. Todos os blocos
dependem de `.upload`, que arrasta ged4py e networkx, então **esta divisão não reduz o custo de import
em nada**. É o oposto da ZV52, onde a normalização conseguiu fugir de pandas e thefuzz.

### O que a divisão entrega

| Propriedade | Antes | Depois |
|-------------|-------|--------|
| Arquivo que um teste do contrato de escape precisa carregar | 508 linhas, com busca, navegação e handler dentro | `mermaid_render.py`, 296 linhas, e só ele |
| Onde `networkx` é necessário | no módulo inteiro | só em `path_finding` |
| Onde `unicodedata` e `re` são necessários | no módulo inteiro | só em `mermaid_render` |
| Onde vive a autoridade de escape | no meio de um arquivo de 508 linhas | isolada, em módulo próprio |

O confinamento não é uma afirmação de intenção: o ensaio mostra que `nx`, `re`, `unicodedata`,
`deque`, `families` e `child_to_family` **deixam de existir** no namespace do `path_search`.

É um ganho estrutural, e não um número de tempo. Registro isso explicitamente porque, na NUMT e na
ZV52, havia um número; aqui não existe equivalente, e inventar um seria pior do que dizer que não há.

## Superfície de compatibilidade

A OPP avisa que dois consumidores dependem dos nomes atuais. A varredura achou **sete**, incluindo o
harness de paridade e as sondas do BUG-J6PQ.

| Consumidor | Nomes usados |
|------------|--------------|
| `app.py` | `path_search` |
| `reconstructed/dna_analysis.py` | `find_ancestral_path`, `generate_mermaid_graph` |
| `tests/test_path_search.py` | `find_ancestral_path`, `find_indirect_path`, `find_person_by_name`, `path_search` |
| `tests/test_mermaid_escape.py` | `_mermaid_label`, `path_search` |
| `tests/test_characterization_mermaid.py` | `path_search` |
| `_reversa_sdd/parity/harness.py` | `get_parents`, `get_spouses`, `find_ancestral_path`, `find_indirect_path` |
| sondas do `BUG-20260929-J6PQ` e da `TPSH` | `path_search`, `_mermaid_label` |

O módulo reexporta **todos** os nomes que expunha, e não só os que a varredura achou: um superconjunto
custa nada e evita que uma sonda antiga quebre. A superfície não foi removida, pela mesma razão da
ZV52: migrar consumidores mexeria nos arquivos de teste que são a rede de segurança.

## O que a alma e a spec exigiram preservar

| Fonte | Exigência | Como foi honrada |
|-------|-----------|------------------|
| Alma #5 | Conexão direta primeiro, afinidade como fallback, 20 e 40 hops | É a política do handler, que não mudou. `MAX_DEPTH` e `MAX_HOPS` foram para `path_finding` com os mesmos valores |
| Alma #2 | Monolito Flask server-side, sem API | Nenhuma rota muda |
| `design.md` § Interface | 15 símbolos do núcleo com assinatura e retorno fixos | Nenhuma assinatura muda. O contrato é da unit, não de um arquivo |
| `design.md` § Estado Interno | O import de `graph` dentro da função, e o motivo | Preservado inteiro, com o comentário da 5XGJ junto |

## Prova de equivalência

**Ensaio antes de aplicar.** `before-after/ensaio_equivalencia.py` copia o pacote para
`.pytest-tmp/uxef-ensaio/`, sobrepõe os quatro arquivos gerados e roda o mesmo runner em dois
processos. Saída em `before-after/ensaio-divisao.txt`.

| Frente | Extensão | Resultado |
|--------|----------|-----------|
| Superfície de compatibilidade | 18 nomes | 0 divergentes |
| Constantes e lista branca do rótulo | `MAX_DEPTH`, `MAX_HOPS`, padrão do regex | idênticas |
| Navegação familiar | 7 pessoas | idêntica |
| `are_spouses` | 42 pares | idêntico |
| `split_path_by_marriage`, `pick_spouse_for_couple` | 7 cada | idênticos |
| `find_person_by_name` | 9 consultas, incluindo vazia e com espaços | idêntico |
| `find_ancestral_path` | **49 pares** de id | idêntico |
| `find_indirect_path` | **49 pares** de id | idêntico |
| `_mermaid_sid`, `_mermaid_label` | 7 e 11 amostras, com aspas, crase, colchete, emoji, tab e quebra de linha | idênticos |
| Fluxo `path_search` | 8 pares, cobrindo direto, indireto, não encontrado, sem conexão e idênticos | idêntico |
| Fluxo na árvore de 1023 pessoas | 3 pares | idêntico |

**Depois de aplicar**, os quatro arquivos na árvore foram conferidos por SHA-256 contra o espelho
ensaiado: **byte a byte idênticos**, o que faz a prova do ensaio valer para a árvore aplicada.

**Suíte completa**: 85 passed, 1 error, idêntico ao estado anterior. O erro é o `PermissionError` de
sandbox em `test_ensure_dirs_creates_uploads`.

**Harness de paridade diferencial**: reexecutado depois da divisão, **PARIDADE 100%, zero divergência**
nas 6 fixtures GEDCOM. Ele usa quatro nomes por esta superfície, então sem a reexportação teria
quebrado no import.

## Três falhas dos meus instrumentos, não do código

Registro porque as três são do mesmo tipo, e porque cada uma teria feito o registro afirmar mais do
que a evidência sustentava.

1. **Off-by-one no extrator de texto.** O texto de cada símbolo começava uma linha antes, então cada
   constante multilinha levava o prefixo da vizinha. A conferência de "verbatim" não pegou porque era
   tautológica; quem pegou foi o `compile()`.
2. **Contabilidade de linhas errada.** A conferência de linhas não movidas guardava `no.lineno` em vez
   do início do bloco de comentário, então acusava como não movida uma linha que viajou. O comentário
   do `BUG-20260929-J6PQ` apareceu como órfão, e ao ir conferir estava no módulo novo.
3. **Comparador com lista fixa de chaves.** O ensaio calculava o `fluxo_grande` na árvore de 1023
   pessoas, mas o comparador tinha uma lista fixa que não o incluía: teria dado EQUIVALENTE sem ter
   comparado. Trocado por interseção dinâmica mais checagem de chaves assimétricas.

## Estado dos arquivos

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `reconstructed/path_search.py` | 508 linhas | 112 linhas |
| `reconstructed/family_navigation.py` | não existia | 106 linhas |
| `reconstructed/path_finding.py` | não existia | 85 linhas |
| `reconstructed/mermaid_render.py` | não existia | 296 linhas |

## Reversão

Por `git apply -R` de cada diff, na ordem inversa (CHG-004, CHG-003, CHG-002, CHG-001). Os quatro são
reversíveis de forma independente, verificado com `git apply --check --reverse`. Para reverter o
conjunto:

```
git checkout -- analisador-genealogico/reconstructed/path_search.py
rm analisador-genealogico/reconstructed/{family_navigation,path_finding,mermaid_render}.py
```

---
*Gerado pelo Reversa-Modularize em 2026-10-01.*
