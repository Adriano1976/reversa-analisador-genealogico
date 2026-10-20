# Roadmap: Humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Requirements: `_reversa_forward/038-humanizar-motivo-descartes/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

O motivo deixa de ser uma **string montada na hora** e passa a ser um objeto pequeno com três
partes: `codigo` (causa estável), `texto` (a frase em português comum) e `detalhe` (os quatro
números, rotulados). A decisão continua exatamente onde está — `core/matching.py` —; o que muda é
o que ela **relata**.

A causa é diagnosticada depois do veredito, por uma função pura que olha os mesmos valores que a
decisão já calculou (`given`, `final`, `inter`, `jacc`, o veto de token do meio) e devolve **uma**
causa por precedência fixa. O sétimo portão — a penalidade de token do meio, hoje invisível na
mensagem — ganha nome próprio: é a causa real do caso que o operador reportou
(`given=100, final=88.25, inter=1/1, jacc=0.50`).

Na tela, a coluna Motivo mostra só a frase. Na lista de trabalho em CSV, a planilha ganha uma
nona coluna, `Detalhe técnico`, com os números — as oito primeiras não se mexem.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | Os testes usam nomes sintéticos e o pool de features montado à mão de `test_candidatos_do_descarte.py`; nenhum nome, kit ou cM real entra em artefato | respeita |
| II. Comportamento observável é preservado em refatoração | A feature **muda** o texto do motivo de propósito. O que não pode mudar é o resultado da análise — mesmos aceitos, mesmos descartes, mesmos cM, mesmos caminhos (`RN-29`, `RF-08`). A prova é a caracterização já existente mais a rodada antes/depois | respeita, com declaração |
| III. Nenhuma mudança sem teste que a cubra | Cada causa ganha teste unitário; a planilha e a tela ganham teste de contrato; a igualdade da decisão é coberta pela caracterização | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhuma travessia é tocada | não se aplica |
| V. Toda suposição de genealogia cita a fonte | Não se aplica: nenhum limiar, faixa de cM ou heurística de domínio é criada ou alterada | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | O motivo passa a ser um `Motivo` (dataclass congelada) com `codigo`, `texto` e `detalhe`; `avaliar_candidatos` devolve esse objeto no segundo elemento, e `match_candidates` continua devolvendo **texto** | O código é a parte estável (`RN-27`) e o texto é a parte que o operador lê; manter `match_candidates` no contrato antigo evita reabrir `application/validacao.py` e a caracterização de 2026-09-29 | (a) uma string só, com o código embutido e depois parseado — inferência a partir de texto, que o projeto recusa desde a 006; (b) um quarto elemento na tupla | 🟢 |
| D-02 | A causa é diagnosticada **depois** do veredito, por função pura sobre os valores já calculados, e não deduzida da ordem dos `elif` | A cadeia de aceitação é uma disjunção: quando nada aceita, mais de um portão falhou. "O primeiro `elif` que não passou" seria arbitrário e frágil a qualquer mudança de limiar | (a) gravar a causa dentro de cada `elif`; (b) reconstruir a causa por regex no texto antigo | 🟢 |
| D-03 | Precedência fixa: nome do meio → sobrenomes em comum de menos → grafia do sobrenome → prenome → semelhança geral | Do mais acionável ao menos acionável: o primeiro pede conferir um nome, o último diz que não há o que conferir. Fixa também garante que o mesmo par de nomes sempre receba a mesma frase (`RN-26`) | (a) listar todas as causas que falharam — volta a ser a fórmula que o operador não consegue ler; (b) escolher pela maior distância do limiar — imprevisível para quem lê | 🟢 |
| D-04 | O veto de token do meio ganha causa própria (`nome_do_meio_ausente`) e é avaliado **primeiro** | É o único portão que só age quando todos os outros passaram; nos outros casos ele nem é a causa. Sem nome próprio, o caso do operador continuaria caindo em "semelhança insuficiente", que é falso | (a) manter o veto invisível, como na 024; (b) citá-lo no detalhe técnico | 🟢 |
| D-05 | As frases e o diagnóstico moram em `core/motivos_do_descarte.py`, módulo puro, sem importar nada além de `dataclasses` | Texto de apresentação não pertence ao motor de decisão, mas o núcleo é quem sabe a causa. Módulo irmão mantém `matching.py` focado e deixa o texto testável sem montar árvore | (a) textos em `reporting/` — mas a `reporting/` não importa `core/` (`ADR-34`) e o código da causa nasce no núcleo; (b) textos em `matching.py`, que já tem 264 linhas de decisão | 🟢 |
| D-06 | O `detalhe` é montado com os valores que a decisão já tinha, com rótulo e vírgula decimal: `prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · grafia do sobrenome 0,50` | Os quatro números são os que a decisão usa; rótulo sem jargão (`prenome` em vez de `given`) e vírgula decimal alinham a planilha ao Excel em português, como a 035 já fez | (a) manter os nomes `given/final/inter/jacc` no detalhe; (b) omitir o detalhe | 🟢 |
| D-07 | A planilha ganha **uma** coluna ao fim, `Detalhe técnico`; as oito colunas existentes mantêm nome e posição | A lista é aberta em outra ferramenta e já tem dono de formato (`035`); acrescentar ao fim não quebra quem lê por posição | (a) espremer o detalhe dentro da coluna Motivo; (b) duas colunas novas (causa + detalhe) | 🟢 |
| D-08 | A tela **não** exibe os números: mostra a frase e o texto sob o botão de download passa a dizer que o detalhe técnico está na planilha | Premissa `P-01`: o operador pediu legibilidade, não uma segunda camada de ruído na mesma célula. A planilha é o lugar onde ele confere o cálculo, e é para lá que a lista vai | (a) `title` com os números — dica de mouse é inacessível em toque e some na leitura de linha; (b) linha extra dentro da célula | 🟡 |
| D-09 | Os quatro motivos da `024` e o filtro anti-falso-positivo entram no mesmo catálogo, só perdendo o jargão: `sem sobrenome em comum` sem o parêntese `(filtro anti-falso-positivo)` | `RF-07`: o catálogo fica coerente, e a decisão não é tocada — é troca de texto no mesmo ponto | (a) deixar o parêntese; (b) trocar também a decisão do filtro | 🟢 |
| D-10 | Nenhuma coluna nova no banco: `skipped_match.reason` continua guardando **texto**, agora humano | `RN-28` fala do dado que alimenta tela e planilha, não do histórico. Migração de schema por causa de redação seria custo desproporcional; as linhas antigas ficam com o texto antigo, e isso é aceitável (histórico é registro do que foi dito) | (a) duas colunas novas + migração; (b) backfill dos registros antigos | 🟢 |
| D-11 | `SHA_DA_TELA` não muda | O bloco dos descartados não renderiza na tela de entrada (sem análise carregada), que é a tela medida pelo hash. Qualquer mudança de hash é sinal de que a edição vazou para fora do `{% if skipped_matches %}` | (a) remedir e aceitar um hash novo | 🟢 |
| D-12 | O texto do motivo da promoção passa a ser o humano (premissa `P-02`) | O cartão promovido repete "o motivo que o sistema tinha dado"; mostrar a fórmula ali reintroduziria o problema num lugar onde o operador já decidiu | (a) guardar a fórmula e mostrar as duas | 🟡 |
| D-13 | A redação das cinco frases é a do `requirements.md`, revisável pelo operador sem tocar código de decisão (premissa `P-03`) | O texto é o único ponto que o operador pode querer reescrever; mantê-lo numa tabela única `codigo → frase` faz a revisão ser uma linha | (a) espalhar as frases por `matching.py` | 🟡 |

## 4. Premissas

> ⚠️ Adotadas em modo autônomo ("não parar"): cada `[DÚVIDA]` do `requirements.md` virou premissa
> explícita, sem passar por `/reversa-clarify`. Todas estão listadas em `questions.md`.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| **P-01** — o detalhe técnico fica **só** na planilha; a tela mostra a frase e diz onde estão os números | §10, 1ª dúvida | Médio: o operador pode querer os números à vista sem baixar o CSV. Custo de reverter é baixo — a frase e o detalhe já viajam no mesmo dado, então é acrescentar um elemento na célula |
| **P-02** — o motivo guardado no histórico da promoção passa a ser o texto humano | §10, 2ª dúvida | Baixo: registros antigos guardam o texto antigo e não há como comparar os dois períodos. Nada lê o motivo por conteúdo, então não quebra fluxo |
| **P-03** — a redação final é a proposta no `requirements.md`, revisável depois | §10, 3ª dúvida | Baixo: trocar uma frase é editar uma linha da tabela de textos, sem tocar decisão nem testes estruturais |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `core.matching` | `_reversa_sdd/code-analysis.md#43-algoritmos-e-lógica-não-trivial` | contrato-alterado | `avaliar_candidatos` devolve `Motivo` no lugar da string; `match_candidates` preserva o contrato de dois valores com texto |
| `core.motivos_do_descarte` | — | componente-novo | Catálogo `codigo → frase`, diagnóstico por precedência e montagem do detalhe técnico |
| `core.dna_analysis` | `_reversa_sdd/code-analysis.md#43` | contrato-alterado | O dicionário do descarte ganha `motivo_codigo` e `motivo_detalhe`; `motivo` passa a ser o texto humano |
| `ports.DescartadoDaAnalise` | `_reversa_sdd/architecture.md#3` | contrato-alterado | Dois campos opcionais novos (`reason_code`, `detail`), com default vazio |
| `application.dna_analysis` | `_reversa_sdd/architecture.md#3` | contrato-alterado | Projeta os dois campos novos a partir do dicionário |
| `reporting.csv_de_descartes` | `_reversa_sdd/addenda/035-lista-de-trabalho-dos-descartes.md` | contrato-alterado | Nona coluna `Detalhe técnico` |
| `templates/index.html` | `_reversa_sdd/addenda/034-revisao-dos-descartes.md` | contrato-alterado | Só o texto sob o botão de download muda; a célula Motivo já renderiza o texto que vier |

## 6. Delta no modelo de dados

- Resumo: **sem migração de schema**. `skipped_match.reason` continua sendo texto livre e passa a
  receber a frase humana. O código da causa e o detalhe técnico viajam no payload da análise
  (tela e planilha) e não são persistidos.
- Detalhe completo em: `_reversa_forward/038-humanizar-motivo-descartes/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Lista de trabalho dos descartes | arquivo (CSV) | `_reversa_forward/038-humanizar-motivo-descartes/interfaces/lista-de-trabalho-em-csv.md` |

## 8. Plano de migração

n/a — nenhum dado é migrado. As linhas de `skipped_match` já gravadas mantêm o texto que tinham
quando foram gravadas, e isso é o comportamento correto para um histórico: ele registra o que o
sistema disse naquele dia.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| A troca de redação mexer, por acidente, no conjunto de aceitos | alto | baixa | `RN-29` + caracterização de `test_characterization_matching.py` rodada antes e depois; os limiares não são tocados por nenhuma ação |
| O diagnóstico mentir quando mais de um portão falha | médio | média | Precedência fixa documentada (`D-03`), testada por caso, e o detalhe técnico sempre ao lado para conferência |
| A célula Motivo crescer a ponto de quebrar a tabela | baixo | média | As frases são curtas e sem números; a coluna já é a mais larga (`width:34%` fica nos candidatos) |
| O CSV quebrar no Excel por causa de `;` ou acento no detalhe | médio | baixa | Separador do detalhe é `·`, não `;`; BOM preservado; teste do formatador cobre acento e separador |
| `SHA_DA_TELA` mudar por edição fora do bloco | médio | baixa | A edição fica dentro do `{% if skipped_matches %}`; o hash é remedido no fecho |
| Testes antigos presos ao literal `score insuficiente…` | baixo | alta (esperado) | Três arquivos serão atualizados de propósito: `test_dna_analysis.py`, `test_candidatos_do_descarte.py`, `test_csv_de_descartes.py` |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado
- [ ] Suíte completa verde (as duas falhas de `graphviz` do ambiente são declaradas, não novas)
- [ ] `SHA_DA_TELA` inalterado
- [ ] Adendo `038` convergido em `_reversa_sdd/addenda/`

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-20 | Versão inicial gerada por `/reversa-plan` (modo autônomo) | reversa |
