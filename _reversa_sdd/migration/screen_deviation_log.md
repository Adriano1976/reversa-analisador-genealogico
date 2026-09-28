---
schemaVersion: 1
generatedAt: 2026-09-28T03:20:10Z
reversa:
  version: "1.2.58"
kind: screen_deviation_log
producedBy: screen-translator
mode: append-only
hash: "sha256:9dee212c9905df6b7fb1c81059700f62445945515a324864cf55bd2c103f24b6"
---

# Screen Deviation Log

> Registro de toda divergência entre o legado e a spec gerada em `target_screens.md`. Append-only. Deviations pendentes bloqueiam o handoff ao Inspector.
> Deviations aprovadas são propagadas para `parity_specs.md § Exceções` quando o Inspector rodar.

## Convenções

- **ID**: `DEV-NNN` (sequencial, três dígitos).
- **Tipo**: `tecnica` | `modernizacao` | `plataforma` | `correcao`.
- **Aprovação**: `pendente` | `aprovado` | `rejeitado`.

## Resumo

- **Total**: **10**
- **Pendentes**: **0**
- **Aprovadas**: **10**
- **Rejeitadas**: 0

> ✅ **Handoff ao Inspector desbloqueado.** Todas as deviations estão resolvidas. DEV-010 foi decidida pelo usuário em 2026-09-28T03:24:30Z.

## Entradas

### DEV-001

| Campo | Valor |
|---|---|
| Tela afetada | todas (afeta o adapter, não uma tela) |
| Tipo | `plataforma` |
| Descrição | O par origem→alvo real detectado (`server-rendered-jinja2-bootstrap` → `web-spa`) **não consta** na tabela do `references/adapter-pairs.md` v1. Foi usado `html_legacy__spa` como proxy. |
| Motivo | O `html_legacy__spa` foi desenhado para "web server-rendered → SPA", que é exatamente o caso. O legado **não usa jQuery** (verificado: apenas 2 `addEventListener`), então o nome do adapter é impreciso, mas o propósito e o formato de spec (`route-component`) são idênticos. Travar com `EC-01` por imprecisão nominal quando a informação está disponível seria pior. |
| Origem no legado | `analisador-genealogico/templates/index.html` (todo o arquivo) |
| Implicação para parity tests | Nenhuma — o formato `route-component` é adequado. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (implicitamente, ao aprovar o modo híbrido) |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | não |

### DEV-002

| Campo | Valor |
|---|---|
| Tela afetada | SCR-002, SCR-003, SCR-004 |
| Tipo | `modernizacao` |
| Descrição | O identificador da árvore viaja na UI legada como `<input type="hidden" name="gedcom_filename">` — o **nome do arquivo original do cliente**. No alvo, o contrato é por `tree_id`, resolvido pela sessão/rota. |
| Motivo | Consequência direta de `discard_log.md` **BR-DESCARTAR-003** (nome do cliente deixa de ser chave) e de **BR-HUMANA-001**. Manter o nome do arquivo como identificador na UI reintroduziria no front-end um mecanismo que o backend abandonou. |
| Origem no legado | `analisador-genealogico/templates/index.html:68` e `:87` |
| Implicação para parity tests | A comparação **não** pode asserir sobre `gedcom_filename`. Asserir sobre presença de campo de seleção de árvore e sobre o `tree_id` resolvido. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou BR-DESCARTAR-003 no gate do Curator) |
| Aprovado em | 2026-09-28T02:56:00Z |
| Propaga para `parity_specs.md § Exceções` | sim |

### DEV-003

| Campo | Valor |
|---|---|
| Tela afetada | SCR-002, SCR-003, SCR-004 |
| Tipo | `modernizacao` |
| Descrição | O legado embute **todos** os nomes do GEDCOM em um `<datalist>` no HTML a cada render. No alvo, passa a ser busca/autocomplete paginado por endpoint. |
| Motivo | Com árvores grandes a `datalist` degrada a página; e em contexto multiusuário significa trafegar a lista completa de nomes de pessoas a cada carregamento. O comportamento **funcional** (sugerir nomes existentes) é preservado. |
| Origem no legado | `analisador-genealogico/templates/index.html:102-106` |
| Implicação para parity tests | Comparar **semântica** (autocomplete alimentado pelos nomes da árvore, ordem alfabética), não o mecanismo `datalist`. Não asserir sobre HTML pré-carregado. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou o modo híbrido) |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | sim |

### DEV-004

| Campo | Valor |
|---|---|
| Tela afetada | SCR-005 |
| Tipo | `modernizacao` |
| Descrição | O legado emite **sintaxe Mermaid como string** gerada no servidor (`{{result.mermaid_data | safe}}`) e a renderiza no cliente com `mermaid.run()`. O alvo **não** emite Mermaid: emite `KinshipPath` estruturado (ramos ascendente/descendente, MRCA, par de cônjuges de afinidade) e o React desenha. |
| Motivo | `discard_log.md` **BR-DESCARTAR-005** e **BR-HUMANA-008** (decisão humana explícita): descartar a emissão de Mermaid é autorizado; **descartar a decomposição do parentesco NÃO**. As funções `split_path_by_marriage` e `are_spouses` migram como funções puras de domínio (`core/decomposition.py`). |
| Origem no legado | `analisador-genealogico/templates/index.html:125` e `:170`; `generate_mermaid_graph`, `generate_mermaid_graph_indirect_bridge` |
| Implicação para parity tests | ⚠️ **A asserção mais importante deste log.** A paridade da conexão **indireta** deve ser verificada sobre a **estrutura decomposta** (ramos, MRCA, ponto de afinidade no 1º par de cônjuges adjacentes), **nunca** sobre a string Mermaid. Se a implementação recalcular a decomposição no cliente em vez de consumir o domínio, **RISK-011 se materializa** e a regra de negócio se perde. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou BR-HUMANA-008 no gate do Curator) |
| Aprovado em | 2026-09-28T02:56:00Z |
| Propaga para `parity_specs.md § Exceções` | sim |

### DEV-005

| Campo | Valor |
|---|---|
| Tela afetada | SCR-G01, SCR-G02 (bloco de alerta, global) |
| Tipo | `correcao` |
| Descrição | O botão de fechar o alerta tem `aria-label="Close"` — **em inglês** — num produto integralmente pt-BR. Corrigido para `aria-label="Fechar"`. |
| Motivo | Defeito visual/acessibilidade do legado (EC-11). **Revisão linguística é proibida por padrão**; esta correção foi **explicitamente autorizada** pelo usuário. |
| Origem no legado | `analisador-genealogico/templates/index.html:37` |
| Implicação para parity tests | ⚠️ **Exceção declarada à invariante de diff textual zero.** A asserção de paridade textual deve **ignorar** esta string, ou aceitar `"Fechar"` no lugar de `"Close"`. É a **única** exceção autorizada em todo o modo literal. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | **sim** |

### DEV-006

| Campo | Valor |
|---|---|
| Tela afetada | todas (afeta os tokens) |
| Tipo | `tecnica` |
| Descrição | `_reversa_sdd/design-system/` **não existe** (EC-17). Os tokens usados nas specs foram **derivados** do próprio `templates/index.html` e gravados em `_reversa_sdd/design-system/tokens-derived.md`. |
| Motivo | A mitigação prevista no EC-17 para quando o design-system catalogado está ausente. As fontes primárias estão disponíveis em read-only. |
| Origem no legado | `analisador-genealogico/templates/index.html:9-24` (bloco `<style>`) e classes do Bootstrap 5.3.3 (`index.html:7`) |
| Implicação para parity tests | Os tokens são **derivados**, não catalogados: cores herdadas do Bootstrap (`btn-primary`, `alert-danger`, etc.) podem diferir do design system real do alvo. Comparação visual não é o critério — o critério é conteúdo e estrutura. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou o modo híbrido) |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | não |

### DEV-007

| Campo | Valor |
|---|---|
| Tela afetada | todas (afeta o inventário) |
| Tipo | `tecnica` |
| Descrição | `_reversa_sdd/ui/inventory.md` **não existe** (EC-18). O inventário de telas foi construído diretamente do código-fonte legado (`templates/index.html`) e gravado em `_reversa_sdd/screens/inventory.json`. |
| Motivo | Mitigação prevista no EC-18. Como `ui/inventory.md` não existe, a verificação de divergência >10% (EC-03) **não é aplicável** — não há com o que comparar. |
| Origem no legado | `analisador-genealogico/templates/index.html` (200 linhas, leitura integral) |
| Implicação para parity tests | O inventário é fonte primária, não derivada. Não há risco de divergência com um artefato de Discovery inexistente. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou o modo híbrido) |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | não |

### DEV-008

| Campo | Valor |
|---|---|
| Tela afetada | todas (afeta tipografia) |
| Tipo | `tecnica` |
| Descrição | O legado **não define família tipográfica** — nenhuma regra `font-family` no bloco `<style>` (`index.html:9-24`); usa o system font stack default do Bootstrap. |
| Motivo | Lacuna real, não escolha. Qualquer família definida no alvo é uma **decisão nova**, não uma tradução. |
| Origem no legado | ausência em `analisador-genealogico/templates/index.html:9-24` |
| Implicação para parity tests | Comparação visual de tipografia **não é válida** como critério de paridade — não há origem a comparar. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou o modo híbrido) |
| Aprovado em | 2026-09-28T03:20:10Z |
| Propaga para `parity_specs.md § Exceções` | não |

### DEV-009

| Campo | Valor |
|---|---|
| Tela afetada | SCR-001, SCR-003, SCR-004, SCR-005, SCR-G02 |
| Tipo | `plataforma` |
| Descrição | O legado despacha **três ações distintas no mesmo `POST /`** por um campo `action` do formulário e responde **sempre HTTP 200**, renderizando HTML com mensagem de erro. No alvo: endpoints REST distintos + **status HTTP semântico** (`200`/`404`/`422`) + payload JSON de erro. |
| Motivo | `discard_log.md` **BR-DESCARTAR-004**: o transporte SSR com `200 (sempre)` é o mecanismo pelo qual o paradigma procedural entrega resultado; com SPA ele deixa de existir. Um cliente React precisa distinguir erro por status/código, não por presença de chave de template. |
| Origem no legado | `analisador-genealogico/templates/index.html:44,67,86` (campos ocultos `action`); `app.py` (as 3 rotas) |
| Implicação para parity tests | ⚠️ Asserir sobre **código de motivo tipado** e **mensagem textual**, não sobre status `200` nem sobre HTML. As **mensagens** (BR-MIGRAR-028) continuam sendo o contrato textual e devem ser idênticas. |
| Aprovação | `aprovado` |
| Aprovado por | Adriano (aprovou o Curator) |
| Aprovado em | 2026-09-28T02:56:00Z |
| Propaga para `parity_specs.md § Exceções` | sim |

### DEV-010 ⚠️ PENDENTE

| Campo | Valor |
|---|---|
| Tela afetada | SCR-G03 (indicador de carregamento), com efeito em SCR-005 |
| Tipo | `modernizacao` |
| Descrição | O legado, no `submit` de **qualquer** formulário, exibe o spinner global **e oculta a `#results-area` inteira** (`display: none`). Consequência observável: submeter um novo formulário **apaga os resultados anteriores da tela**. Ex.: rodar uma busca de caminho depois de uma análise de DNA faz o usuário perder os resultados do DNA. **Proposta**: loading local ao formulário submetido, preservando os resultados anteriores visíveis. |
| Motivo | Reproduzir isso literalmente é fidelidade a um defeito de usabilidade, não a uma regra. Não há requisito de negócio por trás — é um efeito colateral do `querySelectorAll('form')` global (`index.html:191-196`). |
| Origem no legado | `analisador-genealogico/templates/index.html:109-112` (markup) e `:191-196` (comportamento) |
| Implicação para parity tests | Se **aprovada**, a paridade de SCR-G03 deve asserir sobre a **presença do estado de loading**, não sobre a ocultação da região de resultados — que passa a ser divergência aceita. Se **rejeitada**, o comportamento legado deve ser reproduzido e a asserção inclui a ocultação. |
| Aprovação | **`aprovado`** |
| Aprovado por | Adriano |
| Aprovado em | 2026-09-28T03:24:30Z |
| Propaga para `parity_specs.md § Exceções` | sim |

> **Decisão registrada**: aprovada a proposta do agente — loading local ao formulário submetido, **preservando os resultados anteriores visíveis**. A ocultação da região de resultados deixa de ser comportamento preservado e passa a ser **divergência aceita**. Consequência para o Inspector: a paridade de SCR-G03 deve asserir sobre a **presença do estado de loading** no formulário submetido, **não** sobre a ocultação de `#results-area`.

## Telas com mais de uma deviation

| Tela | IDs |
|---|---|
| SCR-002 | DEV-002, DEV-003 |
| SCR-003 | DEV-002, DEV-003, DEV-009 |
| SCR-004 | DEV-002, DEV-003, DEV-009 |
| SCR-005 | DEV-003, DEV-004, DEV-009 |
| SCR-G02 | DEV-005, DEV-009 |
| SCR-G03 | DEV-010 |
| SCR-001 | DEV-005, DEV-009 |

## Notas

- **9 das 10 deviations já estão aprovadas** porque derivam de decisões humanas tomadas nos gates anteriores (Curator e modo de telas) — não são invenções do agente. Apenas **DEV-010** introduz uma escolha de comportamento nova e não coberta por gate anterior, e por isso está `pendente`.
- **Padrão observado neste par origem→alvo** (sugestão para o catálogo v2): migrações de *web server-rendered → SPA* tendem a gerar **exatamente este conjunto de deviations** — (1) o identificador de recurso que viajava em campo oculto precisa virar ID resolvido por sessão; (2) dados embutidos no HTML precisam virar endpoints; (3) estado decidido no servidor (`{% if %}`) precisa virar estado de tela alimentado por API; (4) `status 200 sempre` vira status semântico. Sugerido adicionar o par `server-rendered-jinja2-bootstrap` → `web-spa` e documentar esse checklist.
- **A observação (3) é a mais subestimada** e vale destacar: o legado decide **qual tela mostrar** no servidor (`{% if not gedcom_filename %}`, `index.html:41`). Em uma SPA isso não existe — o front-end precisa receber esse estado do backend. Se a implementação tratar SCR-001 e SCR-002 como rotas independentes sem essa fonte de estado, o comportamento do usuário muda de forma não intencional. Registrado também em `target_screens.md`.
- **DEV-007 e EC-03**: como `ui/inventory.md` não existe, a checagem de divergência de inventário (>10%) **não pôde ser executada**. Não é uma falha do agente — é consequência da ausência do artefato de Discovery. Se o usuário rodar `reversa-visor` posteriormente, o inventário interno deve ser reconciliado.
- **Este log é append-only.** Entradas não são editadas; mudanças de decisão geram nova entrada e a anterior muda apenas o campo `Aprovação` para refletir o desfecho.
