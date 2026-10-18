# Roadmap: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Requirements: `_reversa_forward/031-veredito-no-cartao/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Quatro mudanças pequenas e encadeadas, nenhuma dependência nova: o laço de `core/dna_analysis` passa a
chamar `validar_comparacao` com o que **já** produziu (`documentary`, `comparison`, `ano_base`) e
grava quatro chaves no dicionário de resultado; o template renderiza o selo quando há rótulo; a folha
ganha duas variáveis por tema e duas classes de contorno; o `SHA_DA_TELA` é recalculado como decisão
registrada.

O ponto que exige cuidado **não** é o selo: é de onde sai o intervalo de geração. Hoje
`intervalo_de_geracao_mediano` mora em `application/validacao.py` (feature `028`). Se o cartão usasse
o prior de 25 anos e a fachada usasse a mediana da árvore, o **mesmo kit** receberia dois vereditos
diferentes em duas telas diferentes. A função passa a morar em `core/documentary_relationship.py`
(onde já vivem `parse_year` e `birth_date`), e `application/validacao` delega — uma implementação, um
G, um veredito.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais nunca entram no versionamento | Testes de tela com fixture sintética; nenhum GEDCOM real | respeita |
| II. Comportamento observável preservado | Os quatro estados, o Mermaid e a busca ficam intactos; o hash muda **declaradamente** | respeita |
| III. Nenhuma mudança sem teste | Núcleo, tela, folha e o invariante têm teste | respeita |
| IV. Arestas tipadas | Nenhuma travessia nova | respeita |
| V. Fonte citada | O veredito carrega a `028`; nenhum limiar novo | respeita |

Nenhum conflito com princípio ativo.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O veredito é calculado em `core/dna_analysis`, no mesmo laço que monta o resultado | É o único ponto com `documentary`, `comparison`, a árvore, a raiz e o `ano_base` na mão; evita segunda passada e segundo parse | (a) calcular na borda `app.py`; (b) calcular em `application/dna_analysis`, que só recebe os dicts prontos | 🟢 |
| D-02 | As chaves novas entram no **dicionário de resultado**, não na dataclass `ResultadoDeAnalise` | O template itera esses dicionários (`dna_results=resultado.resultados`) e lê `result.<chave>`; `ResultadoDeAnalise` só carrega a lista | (a) criar um segundo objeto de tela; (b) mudar `ResultadoDeAnalise` (não é o que o template vê) | 🟢 |
| D-03 | O mapeamento status → rótulo e status → classe mora em Python e viaja nos campos | `RF-12`: o template não decide regra; e o precedente já existe (`confrontacao_rotulo`, `janela_aviso` saem do núcleo) | (a) `{% if %}` no template; (b) filtro Jinja | 🟢 |
| D-04 | `intervalo_de_geracao_mediano` passa para `core/documentary_relationship.py` e `application/validacao` delega | Uma implementação só; sem isso o cartão e a fachada divergiriam no G, e o mesmo kit teria dois vereditos | (a) duplicar a função no núcleo; (b) passar o intervalo por parâmetro até a rota | 🟢 |
| D-05 | `INCONCLUSIVO` e ausência de status não geram selo | Decidido em §9 do requirements: marcar quase todos não marcaria nenhum; a ausência vira "não concluído" | (a) selo sempre; (b) selo só no erro | 🟢 |
| D-06 | O selo é `badge validacao-valido` / `badge validacao-conflito`, de **contorno**, com texto em `--ink` | Distingue por forma do selo de confronto (preenchido) e não cai na regra `.badge[class*="estado-"]` | (a) selo preenchido com `--st-*`; (b) cor nova inventada | 🟢 |
| D-07 | Duas variáveis por tema: `--validacao-valido` e `--validacao-conflito`, com os valores de `--primary`/`--danger` de cada bloco | `--st-*` não são redefinidas no escuro; sem isso o contorno sumiria no tema noturno. Contraste **medido**: 5,66:1 e 5,92:1 no claro; 8,30:1 e 8,42:1 no escuro | (a) reusar `--st-*` (escuro sobre escuro); (b) texto branco (exigiria preenchimento) | 🟢 |
| D-08 | Uma linha explicativa sob o título da lista: os dois selos e "sem selo = não concluído" | Sem ela, a ausência é ambígua entre "validado", "inconclusivo" e "não calculado" | (a) nada; (b) legenda por cartão (ruído multiplicado) | 🟡 |
| D-09 | O `SHA_DA_TELA` é recalculado nesta entrega, com data e motivo no comentário | O invariante existe para impedir mudança **não declarada**; mantê-lo velho deixaria a suíte vermelha e o teste sem sentido | (a) afrouxar o teste; (b) remover o invariante | 🟢 |
| D-10 | Teste de contraste **calculado** a partir da folha, não "olhado" | O par claro/escuro muda com o tema; um teste que lê as variáveis dos dois blocos e aplica a fórmula WCAG pega regressão de cor sem abrir navegador | (a) conferência manual; (b) teste de screenshot | 🟢 |
| D-11 | O teste de "uma chamada por resultado" usa espião no validador, injetado no módulo | Prova o requisito de custo sem depender de contador global | (a) contar tempo; (b) confiar na leitura do código | 🟢 |
| D-12 | Sem dependência nova, sem tabela, sem rota, sem persistência do veredito | O banco não tem coluna para ele, e criar uma é migração fora do pedido | (a) gravar em `match_result`; (b) expor rota nova | 🟢 |

## 4. Premissas

Nenhuma premissa pendente: o `requirements.md` está com **zero** marcadores de dúvida após a sessão
de esclarecimentos de 2026-10-18 (§9).

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.dna_analysis` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | regra-nova | Chama o validador por resultado e grava quatro chaves de veredito no dicionário da tela |
| `core.documentary_relationship` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | contrato-novo | Ganha `intervalo_de_geracao_mediano(arvore)` — fonte única do G |
| `application.validacao` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | regra-alterada | `intervalo_de_geracao_mediano` passa a delegar para o núcleo; nome e comportamento públicos idênticos |
| `tela: cartão de DNA` | `_reversa_sdd/domain.md#39-ordem-de-apresentacao-dos-resultados` | contrato-alterado | Cabeçalho do cartão ganha o selo de validação; a lista ganha uma linha explicativa |
| `tela: folha de estilo` | `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | regra-nova | Duas variáveis por tema e as classes de contorno `validacao-*` |
| `tests.test_icone_de_atalho` | `tests/` | regra-alterada | `SHA_DA_TELA` recalculado, com data e motivo no comentário |
| `tests.test_validacao_no_cartao` | `tests/` | artefato-novo | Presença, ausência, classe, `title`, acessibilidade e a linha explicativa |
| `tests.test_veredito_no_nucleo` | `tests/` | artefato-novo | Os quatro campos por status, a ausência e a chamada única por resultado |
| `tests.test_contraste_do_selo` | `tests/` | artefato-novo | Lê a folha, extrai as variáveis dos dois temas e calcula o contraste |

**Arquivos que NÃO mudam:** `src/app.py`, `requirements.txt`, `init.sql`, `docker/*`, o Mermaid
(`reporting/mermaid_render.py`), a busca de caminho e as tabelas do banco.

## 6. Delta no modelo de dados

- **Nenhuma estrutura persistente nova.** As quatro chaves vivem no dicionário em memória que a tela
  consome; o banco não recebe coluna nem linha nova.
- `ConexaoDaAnalise` (payload de persistência) **não** ganha os campos: ele descreve o que é gravado,
  e o veredito é derivável da árvore a qualquer momento.
- Detalhe das chaves e do mapeamento em
  `_reversa_forward/031-veredito-no-cartao/data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `GET /` (HTML da tela) | HTML | `_reversa_forward/031-veredito-no-cartao/data-delta.md#4-contrato-de-tela` |

O HTML muda — é o objeto da feature. Não há contrato novo de rede: a rota é a mesma, e o
`SHA_DA_TELA` é o registro do que mudou.

## 8. Plano de migração

n/a. Não há dado a migrar. A única "migração" é o hash da tela, atualizado dentro da entrega.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Divergência de G entre o cartão e `validar_arquivos` | **alto** | média | D-04: uma implementação só, e o teste da `028` continua provando o valor |
| Esquecer o `SHA_DA_TELA` | alto | média | D-09 e teste dedicado; a suíte fica vermelha se esquecer, o que é o comportamento desejado |
| Contorno ilegível no tema escuro | alto | alta sem D-07 | Duas variáveis por tema e teste de contraste calculado |
| Custo de 142 chamadas ao validador | médio | baixa | Função pura e O(saltos); espião conta as chamadas; medir no teste de integração |
| Selo contradizer o de confronto no mesmo cabeçalho | médio | média | Textos distintos ("Validado" × "Compatível") e eixos declarados na linha explicativa |
| Linha explicativa poluir o topo da lista | baixo | média | Uma frase, no tom de `legenda-informativa` que já existe |
| Teste de tela frágil a mudança de HTML | médio | alta | Asserção por presença de `validacao-` e pelo texto, não por posição |
| `INCONCLUSIVO` marcado por engano no template | médio | baixa | O campo `validacao_rotulo` vem `None` do núcleo; teste de ausência |

## 10. Critério de pronto

- [ ] `core/documentary_relationship.intervalo_de_geracao_mediano` implementado, e `application.validacao` delegando
- [ ] `core/dna_analysis` grava `validacao_status`, `validacao_rotulo`, `validacao_classe` e `validacao_aviso`
- [ ] `INCONCLUSIVO` e ausência de status produzem os quatro campos `None`
- [ ] Selo renderizado no cabeçalho, com `title` e `visually-hidden`
- [ ] Linha explicativa sob o título da lista
- [ ] Duas variáveis por tema na folha, com o contraste medido no comentário
- [ ] `SHA_DA_TELA` recalculado, com data e motivo
- [ ] Testes de núcleo, de tela e de contraste passando; suíte completa verde
- [ ] `app.py`, `requirements.txt`, `init.sql`, Mermaid, busca e banco intocados
- [ ] `git status` lista apenas os arquivos de §5 e os artefatos de `_reversa_forward/031-*`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-plan` | reversa |
