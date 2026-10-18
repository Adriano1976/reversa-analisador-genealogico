# Legacy Impact: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`
> Âncora: `_reversa_sdd/architecture.md`, `_reversa_sdd/state-machines.md`,
> `_reversa_sdd/recursos-da-tela/`, `_reversa_sdd/addenda/013-…` e `023-…`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/assets/app.css` | Folha de estilo da tela (`_reversa_sdd/architecture.md#3`; rota descrita no adendo `013`) | `regra-alterada` | **LOW** | Quatro tokens de estado sem uso foram removidos, o token do `INCONCLUSIVO` ganhou comentário e o comentário dos estados ganhou a medição. Nenhuma cor efetiva, classe ou regra aplicada mudou |

Nenhum outro arquivo de código do projeto foi tocado. `src/templates/index.html`, `src/app.py`,
`tests/` e os pacotes `application/`, `ports/`, `core/`, `parsers/` e `reporting/` estão fora do diff
(`evidence/depois/escopo.txt`).

## 2. Diff conceitual por componente

### Folha de estilo da tela

**Antes.** As quatro cores de estado tinham **dois** nomes cada: a família curta (`--ok`, `--poss`,
`--conf`, `--inc`) e a família usada de fato (`--st-compativel`, `--st-possivel`, `--st-conflitante`,
`--st-inconclusivo`). A família curta nunca era referenciada — nem na folha, nem no template, nem nos
testes. O comentário dos estados registrava apenas o caso histórico do laranja, e os dois comentários
do bloco do banner descreviam a arte anterior a 2026-10-16 (a que trazia o título desenhado).

**Depois.** Sobrevive a família `--st-*`, com os mesmos valores. O token do `INCONCLUSIVO` carrega o
comentário que explica por que o cinza é próprio (estado inicial e caminho de falha) e por que **não**
pode seguir `--muted` (2,62:1 no tema escuro). O comentário dos estados traz os quatro contrastes
medidos (6,39 / 7,13 / 6,69 / 6,11:1) e a razão de não haver override no tema escuro. Os dois
comentários do banner passam a descrever a arte atual: sem texto, com a placa clara justificada pelo
fundo claro da ilustração.

**Efeito observável.** Nenhum. As cores aplicadas são as mesmas; o teste de contraste e o de hash da
tela passam antes e depois.

## 3. Preservadas

Regras 🟢 que continuam verdadeiras, com o instrumento que as sustenta:

| Regra | Onde vivia | Prova |
|-------|------------|-------|
| O ícone de atalho é descoberto por caminho convencional, sem declaração no documento (`RN-02` / `W027`) | `_reversa_sdd/recursos-da-tela/requirements.md#requisitos-funcionais` (`RF-07`) | `test_a_tela_nao_declara_o_icone_de_atalho` |
| O favicon continua embutido como `data URI`, e não vira rota | idem (`RF-08`) | `test_a_tela_mantem_o_icone_da_aba_embutido` |
| `favicon.ico` e `apple-touch-icon-precomposed.png` continuam sem resposta | idem (`RF-09`) | `test_os_caminhos_nao_servidos_continuam_sem_resposta` |
| O `<h1>` é sempre visível e não recebe `visually-hidden` (`RN-23`) | `_reversa_sdd/addenda/023-arte-do-topo-sem-o-titulo.md` | `test_o_titulo_do_produto_esta_sempre_visivel` |
| Os quatro estados do confronto continuam quatro, e o `status` continua nome de classe CSS | `_reversa_sdd/state-machines.md#32-tabela-de-transições` | `test_os_quatro_estados_tem_cor`, `test_o_template_emite_a_classe_de_estado` |
| `INCONCLUSIVO` continua o estado inicial e o caminho de falha, sem afirmar veredito | `_reversa_sdd/state-machines.md#33-fatos-de-contrato` | `TestOContrasteDosSelos` e os testes de confronto |
| Todo selo de estado continua legível (≥ 4,5:1) nos dois temas | `src/assets/app.css:162`; `tests/test_estilo_da_tela.py` | `TestOContrasteDosSelos` |
| O documento servido em `GET /` continua byte a byte o mesmo (`RF-17` da 006) | `_reversa_forward/006-fronteira-aplicacao-ports/requirements.md` | `test_a_tela_nao_mudou_sem_mudanca_declarada` |
| As mensagens da camada de rota continuam ao caractere (`W005` da 006) | `_reversa_forward/006-fronteira-aplicacao-ports/regression-watch.md` | Nenhuma mensagem tocada; o template está fora do diff |

## 4. Modificadas

| Regra | Tipo | Delta |
|-------|------|-------|
| Declaração dos tokens de estado | `regra-alterada` (apresentação) | As quatro definições curtas deixam de existir; a família `--st-*` passa a ser a única. **Nenhuma cor efetiva muda** |

Nenhuma regra de domínio (`_reversa_sdd/domain.md`) foi alterada ou removida. Não há regra com
confidência rebaixada.
