---
schema_version: 1
id: OPP-20260929-EHNZ
display_number: 10
context: upload-gedcom
verb: decouple
title: Estado global mutável acopla upload, path_search e dna_analysis
target:
  files: [analisador-genealogico/reconstructed/upload.py, analisador-genealogico/reconstructed/path_search.py, analisador-genealogico/reconstructed/dna_analysis.py]
  symbol: people, families, graph, child_to_family
smell: acoplamento por variável global de módulo, com duas semânticas de import diferentes no mesmo projeto
roi:
  confidence: yellow
  impact: acoplamento estrutural. É a raiz do BUG-20260929-BJJH (exposição entre usuários)
  cost: high
  est_return: nenhum ganho como refactor. Ver a nota de escopo abaixo antes de rotear
state: declined
superseded_by: OPP-20261006-3WR5
declined_reason: Caminhos do alvo nao existem mais e o conteudo esta duplicado por OPP-20261006-3WR5, que registra o mesmo acoplamento sobre os arquivos atuais. Ver a reconciliacao de 2026-10-06 no fim do arquivo.
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras, .reversa/soul.md#lacunas-🔴-validação-humana]
  specs: [_reversa_sdd/migration/target_business_rules.md#br-humana-004, _reversa_sdd/migration/ambiguity_log.md#amb-009, _reversa_sdd/migration/discard_log.md#br-descartar-002]
---

## Antes observado

`upload.py:15-19` declara quatro globais de módulo, descritas no próprio código como "singleton por
processo". `load_gedcom_and_build_graph` as sobrescreve in place (linhas 95-98) a cada parse.

Os consumidores dependem delas por dois mecanismos diferentes, e a diferença não está documentada:

| Consumidor | Import | Por que funciona |
|------------|--------|------------------|
| `path_search.py:20` | `from .upload import child_to_family, families, get_name, people` | Os quatro são mutados in place, então o binding continua apontando para o objeto vivo |
| `path_search.py:131` | `from .upload import graph` **dentro da função** | `graph` é **reatribuído** (linha 97), então um import no topo ficaria preso ao valor antigo |
| `dna_analysis.py:25` | `from .upload import get_name, people` | Mesmo caso dos mutados |

Ou seja: a mesma variável exige regra de import diferente conforme seja mutada ou reatribuída. Quem
editar `upload.py` sem saber disso introduz um bug silencioso, e o `# noqa: E402` da linha 501 mostra
que a anomalia já incomodou alguém.

## Transformação proposta

Nenhuma como refactor. Este registro existe para dar rastreabilidade à decisão, não para propor
execução.

## Nota de escopo: isto NÃO é refactor

Trocar o estado global por estado explícito, passado por parâmetro ou encapsulado, **altera
arquitetura e o comportamento de concorrência**. Pelo princípio II, isso é feature do Forward, e já
está decidido e registrado lá:

- `_reversa_sdd/migration/target_business_rules.md#br-humana-004` e
  `_reversa_sdd/migration/ambiguity_log.md#amb-009`: decisão humana de eliminar o conceito de "GEDCOM
  carregado" global, com árvore como aggregate persistido com `owner_id`.
- `_reversa_sdd/migration/discard_log.md#br-descartar-002`: o singleton de módulo foi descartado por ser
  incompatível com isolamento por usuário.
- `BUG-20260929-BJJH`: o defeito de exposição entre usuários tem este acoplamento como mecanismo.

Roteamento correto: Forward, não um especialista de Code Quality. Encaminhar para lá se o usuário
quiser atacar isso agora.

## Rede de segurança exigida

Se algum dia for tentado como refactor, a exigência seria caracterização de concorrência, que não
existe hoje: nenhum teste exercita duas requisições simultâneas. Sem isso, a preservação de
comportamento não é demonstrável, e o gate deve barrar.

## Risco

Alto se executado como refactor. É exatamente o caso que o princípio II prevê: uma mudança que parece
estrutural mas muda comportamento observável em cenário multiusuário.

## Reconciliação de 2026-10-06

Esta oportunidade foi marcada `declined` na auditoria das quatro configurações pedidas pelo usuário,
por dois motivos independentes.

**1. Os caminhos do alvo estão mortos.** O bloco `target` aponta para
`analisador-genealogico/reconstructed/{upload,path_search,dna_analysis}.py`. Essa raiz deixou de
existir em 2026-10-03, quando a `OPP-20261003-FLAT` moveu o pacote para `src/` com quatro
subpacotes. Nenhum dos três caminhos resolve hoje.

**2. O conteúdo está duplicado pela `OPP-20261006-3WR5`.** A oportunidade nova registra o mesmo
acoplamento por variável global de módulo, com medição atualizada (nove módulos importando as
globais, `parsers/gedcom_parser.py:62-67` escrevendo o estado do domínio, o import tardio de
`graph` em `path_finding.py:38`) e sobre os arquivos que existem: `src/core/gedcom_state.py` e seus
consumidores.

**O que NÃO foi descartado com esta decisão**, e continua valendo integralmente:

| Conteúdo original | Onde vive agora |
|---|---|
| A conclusão de que trocar o estado global **não é refactor** e pertence ao Forward (princípio II) | `OPP-20261006-3WR5`, seção "Aviso de escopo" |
| O encaminhamento ao Forward, com `BR-HUMANA-004`, `AMB-009` e `BR-DESCARTAR-002` | `OPP-20261006-3WR5`, bloco `traceability.specs` |
| O vínculo com o `BUG-20260929-BJJH` como mecanismo de exposição entre usuários | `.reversa/soul.md` §4 L2 e `_reversa_sdd/architecture.md` §7 |
| A exigência de caracterização de concorrência como rede de segurança | `OPP-20261006-3WR5`, seção "Aviso de escopo" |

A decisão é de auditoria, não de produto: nenhum código foi tocado, e o histórico fica preservado
porque `declined` nunca apaga o registro.

---
*Gerado pelo Reversa-Refactor em 2026-09-29. Reconciliado em 2026-10-06.*
