# Adendo: a tela passou a buscar por nome, e a busca é leitura

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`,
> `_reversa_sdd/code-analysis.md#5.7` e `_reversa_sdd/permissions.md`)

## Vigência

Vigente desde 2026-10-28.

## Resumo da entrega

O sistema sabia **preencher** um nome — o combobox da feature 037, que só existe com árvore
aberta, não abre ao digitar e mostra os primeiros 50 nomes na ordem da árvore — e não sabia
**responder** "quem é esta pessoa". A 052 entrega um campo de busca por nome ou sobrenome,
servido pelo servidor, que responde em **duas fontes**: a ficha da pessoa na árvore aberta e
a linha do match no relatório de DNA selecionado. Um termo, duas perguntas separadas e
rotuladas, ordem determinística e limite de 50 acertos por seção com o total declarado.

A busca é **leitura pura**: não grava arquivo, não toca o histórico, não entra na trilha de
auditoria e **não altera o resultado de nenhuma análise**. Cada fonte normaliza com a
autoridade que já usava — `core.homonimos.normalizar` na árvore, `utils.name_keys.norm_name`
no relatório —, e é isso que mantém a busca concordando com o dossiê de homônimos de um lado
e com o `matching` do outro.

**27 de 27 ações concluídas.** Suíte: **1.801 passam / 9 pulados / 5 falham** em 1.815
coletados. Das 5 falhas, **4 são as de `test_characterization_mermaid`** já conhecidas, e a
quinta (`test_tres_fases_da_tela.py`, literal `1. Lista de Matches (CSV)`) **é anterior a
esta entrega** — o template no `HEAD` diz `1. Lista de Matches do Ancestor Projects (CSV)` e
o `git diff` desta feature não toca essa linha. São **49 testes novos**.

Ficam declaradas três coisas: o `all_names` **continua** viajando no HTML (a remoção é a
entrega seguinte, e é ela que traz a auditoria da busca junto); os **normalizadores não
foram unificados** (a unificação mudaria resultado de análise, e é entrega própria com
medição de paridade); e o **casamento aproximado ficou de fora** — quando entrar, entra
atrás de `EstrategiaDeCasamento`, com medição.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md` | §1 (visão geral / borda) | `contrato-novo` | A borda ganha o Blueprint `POST /busca` e monta o caso de uso com as duas fontes; continua sem decidir casamento. As sete operações de dado da 051 seguem iguais |
| `_reversa_sdd/architecture.md` | §2 (containers e concorrência) | `presença` | Nenhum container novo. O índice de tokens é atributo do grafo, e a gravação é idempotente — a mesma propriedade que `architecture.md#2` já declara segura entre as 4 threads |
| `_reversa_sdd/architecture.md` | §3 (componentes e pacotes) | `componente-novo` | Entram `core/busca_de_nome.py`, `ports/fontes_de_nomes.py` (os dois adaptadores), `application/busca_de_nome.py`, `reporting/resultado_da_busca.py`, `web/rotas_busca.py` e o partial `templates/_busca.html`. O grafo de pacotes continua estritamente descendente |
| `_reversa_sdd/architecture.md` | §4 (modelo de dados) | `presença` | **Nenhum dado persistido novo**: as duas visões do índice são memória da árvore, e os payloads duram uma requisição |
| `_reversa_sdd/c4-context.md` | as rotas do sistema | `delta-de-contrato-externo` | As rotas de sistema passam a incluir `POST /busca`; o operador ganha a capacidade de consultar nomes sem executar análise |
| `_reversa_sdd/code-analysis.md` | §5.7 (observações e lacunas da busca-caminho) | `regra-alterada` | O índice de nomes deixa de ter uma visão só: passa a manter `nome → ids` e `token → ids`, na mesma varredura. A `L-24` continua fechada; a `L-25` continua aberta e a busca não a repete, porque ordena por chave total |
| `_reversa_sdd/domain.md` | §3.4 (matching difuso) | `presença` | O `matching` mantém normalizador, limiares e desempate. A busca **não** reusa o ranking dele (`RN-06` da feature) |
| `_reversa_sdd/domain.md` | §3.6 (tela de entrada) | `regra-alterada` | A tela ganha o bloco de busca acima das fases, renderizado **só** com árvore aberta. As duas listas continuam entrando em toda renderização |
| `_reversa_sdd/domain.md` | §5 (contrato de mensagens) | `regra-nova` | Entram quatro literais novos: o rótulo do campo, a dica do campo, o aviso de termo vazio e o de "nenhum nome encontrado". Os 29 catalogados não mudam |
| `_reversa_sdd/permissions.md` | §3 (matriz de permissões) | `presença` | A busca herda o escopo por dono da 051: referência de outro dono responde `404` com o literal de inexistência, nunca `403` |
| `_reversa_sdd/erd-complete.md` | Diagrama E (esquema físico) | `presença` | Nenhuma tabela, coluna, índice ou migração. `init.sql` intocado |
| `_reversa_sdd/state-machines.md` | §6 (Desfecho da Busca) | `presença` | A Máquina 4 é da **busca de caminho** e não foi tocada. A busca por nome não tem ciclo de vida nem máquina de estado |
| `_reversa_sdd/addenda/037-redesenho-das-tres-fases.md` | o combobox de nomes | `presença` | O combobox, o bloco `application/json` e os três campos de nome continuam como a 037 entregou |
| `_reversa_sdd/addenda/048-indice-de-nomes-sem-colisao.md` | o índice preso ao grafo | `regra-alterada` | O índice ganha a segunda visão, **no mesmo laço** e no mesmo atributo do grafo; a ausência de chave de conteúdo continua valendo |
| `_reversa_sdd/addenda/049-sistema-de-log.md` | as ações auditáveis | `presença` | Nenhuma ação nova: a busca **não** entra na trilha. A decisão é da sessão de 2026-10-28 e está registrada no `requirements.md` |
| `_reversa_sdd/addenda/051-login-google-e-isolamento.md` | o escopo por dono | `presença` | A busca é superfície nova que herda o escopo e a recusa da 051 |

**Contagem por tipo:** `presença` 9 · `regra-alterada` 3 · `regra-nova` 1 · `componente-novo` 1
· `contrato-novo` 1 · `delta-de-contrato-externo` 1 — **16 impactos**.

Nenhuma regra de `_reversa_sdd/domain.md` foi removida. Não há `delta-de-dados`: o modelo
persistido é o mesmo.

## Regras sob vigilância

| ID | O que vigiar |
|----|--------------|
| `W001` | O dossiê de homônimos continua devolvendo o mesmo conjunto de ids, na mesma ordem |
| `W002` | O índice continua preso ao grafo, sem chave de conteúdo — agora nas duas visões |
| `W003` | A fonte de nomes declara a própria normalização; não existe normalizador único na busca |
| `W004` | A borda registra o Blueprint e monta o serviço, sem decidir casamento nem ranking |
| `W005` | O bloco de busca continua fora da tela vazia; `SHA_DA_TELA` só muda com declaração |
| `W006` | A busca não grava: sem disco, sem histórico, sem trilha |
| `W007` | A busca não altera veredito, número de conexões nem descartados |
| `W008` | Referência de outro dono responde `404`, nunca `403` |
| `W009` | A ordem dos acertos é total e estável entre buscas iguais |

Detalhe de cada item, com o sinal de violação:
`_reversa_forward/052-busca-nome-e-sobrenome/regression-watch.md`.

## Fontes

- `_reversa_forward/052-busca-nome-e-sobrenome/requirements.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/roadmap.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/actions.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/progress.jsonl`
- `_reversa_forward/052-busca-nome-e-sobrenome/legacy-impact.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/regression-watch.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/data-delta.md`
- `_reversa_forward/052-busca-nome-e-sobrenome/interfaces/busca.md`

## Atualização 2026-10-29

**Defeito medido em uso, e corrigido.** Com `POST /busca` no ar, a Fase 3 respondia
"Digite um nome ou sobrenome para buscar." ao analisar. A causa não era a busca: **seis
formulários da tela não declaravam `action`** e postavam para a URL corrente — o que era
seguro enquanto a única URL da aplicação era `/`. Depois de uma busca, a URL é `/busca`, e
o formulário da análise caía na rota da busca, que via `termo` vazio.

Correções, todas declaradas:

- os **seis** formulários (abrir, apagar, envio de árvore, conexão, análise de DNA e
  promover candidato) passam a declarar `action="/"`;
- `GET /busca` responde `302` para `/`, para que recarregar a página não devolva `405`;
- entra o teste `test_todo_formulario_declara_action`, que reprova qualquer formulário sem
  `action` — a guarda contra a volta do defeito.

**`SHA_DA_TELA` foi remedido**: `386f2fef…` (51.601 bytes) → `577a17fd…` (51.612,
**+11 bytes**), exatamente o ` action="/"` do formulário de envio, o único dos seis que
aparece na tela vazia. A medição está declarada em `tests/test_icone_de_atalho.py`, décima
segunda. **Isto corrige o que este adendo afirmava antes:** a feature altera o hash, ainda
que por um efeito colateral declarado, e a linha `presença` da tabela acima deve ser lida
como `regra-alterada` no que toca a `index.html`.

Suíte depois da correção: **1.802 passam / 9 pulados / 5 falham** — as mesmas 5 de antes
(4 de `test_characterization_mermaid` e a do literal `1. Lista de Matches (CSV)`, ambas
anteriores a esta entrega).
