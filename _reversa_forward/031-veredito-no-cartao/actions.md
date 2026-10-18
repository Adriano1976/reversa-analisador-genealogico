# Actions: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Roadmap: `_reversa_forward/031-veredito-no-cartao/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 15 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 5 |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `tests/fixtures/resultado_para_cartao.py` com um dicionário de resultado completo o bastante para renderizar o cartão (incluindo as quatro chaves de validação), parametrizável por status | - | `[//]` | `tests/fixtures/resultado_para_cartao.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Escrever os testes de núcleo do veredito: quatro campos preenchidos em `VALIDADO` e em erro, `status` presente e os outros três nulos em `INCONCLUSIVO`, e os quatro nulos sem veredito | - | - | `tests/test_veredito_no_nucleo.py` | 🟢 | `[X]` |
| T003 | Escrever o teste de custo: espião no validador prova uma chamada por resultado, e nenhuma quando o resultado não tem `documentary` | T002 | - | `tests/test_veredito_no_nucleo.py` | 🟢 | `[X]` |
| T004 | Escrever os testes de tela: selo presente com o texto certo nos dois status, ausente no inconclusivo, classe `validacao-*` sem `estado-`, `title` com o código e `visually-hidden` completo | T001 | - | `tests/test_validacao_no_cartao.py` | 🟢 | `[X]` |
| T005 | Escrever o teste da linha explicativa sob o título da lista, declarando que ausência de selo significa não concluído | T001 | - | `tests/test_validacao_no_cartao.py` | 🟡 | `[X]` |
| T006 | Escrever o teste de contraste: ler a folha, extrair `--validacao-*` dos dois blocos de tema e calcular o contraste pela fórmula WCAG, exigindo ≥ 4,5:1 | - | - | `tests/test_contraste_do_selo.py` | 🟢 | `[X]` |
| T007 | Escrever o teste de fonte única do intervalo de geração: `application.validacao.intervalo_de_geracao_mediano` e a função do núcleo devolvem o mesmo valor para a mesma árvore | T008 | - | `tests/test_veredito_no_nucleo.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Mover `intervalo_de_geracao_mediano` para `core/documentary_relationship.py` e fazer `application.validacao` delegar, mantendo nome e comportamento públicos | - | - | `src/core/documentary_relationship.py` | 🟢 | `[X]` |
| T009 | Implementar no laço de `core/dna_analysis` a chamada ao validador e as quatro chaves (`validacao_status`, `validacao_rotulo`, `validacao_classe`, `validacao_aviso`), com o mapeamento status → rótulo/classe | T008 | - | `src/core/dna_analysis.py` | 🟢 | `[X]` |
| T010 | Calcular o intervalo de geração **uma vez por análise**, antes do laço, e reutilizá-lo em todos os resultados | T008 | - | `src/core/dna_analysis.py` | 🟢 | `[X]` |

## Fase 4, Tela

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Acrescentar `--validacao-valido` e `--validacao-conflito` nos dois blocos de tema e as duas classes de contorno, com o contraste medido no comentário | - | `[//]` | `src/assets/app.css` | 🟢 | `[X]` |
| T012 | Renderizar o selo no cabeçalho do cartão e a linha explicativa no topo da lista | T004, T005, T009, T011 | - | `src/templates/index.html` | 🟢 | `[X]` |
| T013 | **Verificar** que o `SHA_DA_TELA` não muda (o bloco de resultados não entra em `GET /`) e registrar a medição; a proteção do cartão fica com os testes de tela | T012 | - | `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Completar docstrings e comentários: por que contorno e não preenchimento, por que a classe não usa `estado-`, por que o G tem fonte única e por que o veredito viaja no dicionário | T013 | - | `src/core/dna_analysis.py` | 🟡 | `[X]` |
| T015 | Rodar a suíte completa, conferir `git status`, reiniciar o servidor e confirmar o selo na tela nos dois temas | T013, T014 | - | `tests/` | 🟢 | `[X]` |

## Notas de execução

Cinco observações registradas durante o coding.

1. **O `SHA_DA_TELA` não mudou, e isso foi medido antes de virar afirmação.** O teste do hash
   passou sem alteração. Verificado com o cliente de teste: `GET /` **não** contém
   `legenda-da-validacao` — o bloco de resultados só é renderizado quando há `dna_results`.
   Ou seja, o invariante prende a **casca** da tela, não o cartão. `requirements.md` (RN-08,
   RF-09), `roadmap.md` (D-09 e a linha de risco) e `data-delta.md` §7 foram corrigidos.
2. **O aviso do selo passou a levar o literal de máquina na frente.** A primeira versão
   montava `motivo (CÓDIGO)`; o teste de tela mostrou que o literal `ERRO CRONICO / QUEBRA DE
   LINHA` não aparecia em lugar nenhum do cartão, e a RN-04 manda que ele fique no `title`.
   Formato final: `STATUS: motivo (CÓDIGO)`.
3. **O aviso é `None` quando não há selo.** Sem selo não há `title` para exibir, e texto que
   nenhuma tela lê é dado morto. O `status` continua disponível (é dado de domínio).
4. **O primeiro código crítico do aviso é o primeiro na ordem do validador** (severidade e
   depois código alfabético), não o "mais grave" na cabeça de quem lê. No cenário da fixture o
   código é `CONFLITO_CM_DOCUMENTAL`, e não `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` — o teste
   foi corrigido para refletir o contrato real, não o que eu esperava.
5. **O teste de contraste lê a folha, não o navegador.** Ele extrai as variáveis dos dois
   blocos de tema e recalcula a razão WCAG: 5,66:1 e 5,92:1 no claro; 8,30:1 e 8,42:1 no
   escuro. Se alguém mexer num hexadecimal no futuro, a falha aparece no pytest.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-18 | 15 ações executadas; cinco observações, incluindo a correção do alcance do `SHA_DA_TELA` | reversa |
