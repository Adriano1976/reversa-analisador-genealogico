# Adendo: tabela das possibilidades com o antepassado comum

> Identificador: `043-tabela-do-antepassado-comum`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/data-dictionary.md`)
> Modo: **express** — a spec fina vive em `_reversa_forward/043-tabela-do-antepassado-comum/`

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

O bloco 3 listava as relações compatíveis com o cM como uma lista de nomes, e o nome era tudo: `Primos
de 2º grau (0–234 cM na fonte; média 73 cM)`. A lista virou **tabela de quatro colunas**, e com isso o
cartão passou a dizer **onde procurar o antepassado comum** e **onde o valor observado cai dentro da
faixa publicada** — além de declarar a ordem que já existia no núcleo e era invisível.

| Relação | Faixa na fonte | Onde o valor cai | Antepassado comum mais recente |
|---|---|---|---|
| Primos de 2º grau | 41–592 cM (média 229) | 21%, abaixo do centro | **bisavós** — 3 gerações acima, nos dois lados |
| Primos de 2º grau (1× removido) | 14–353 cM (média 122) | 41%, no centro | **bisavós e trisavós** — 3 e 4 gerações acima |
| Meio-primos de 2º grau | 10–325 cM (média 120) | 46%, no centro | **bisavós (um de dois)** — só um dos bisavós é compartilhado |
| Primos de 1º grau (3× removidos) | 25–238 cM (média 117) | 61%, acima do centro | **avós e tetravós** — 2 e 5 gerações acima |
| Primos de 7º grau | 0–57 cM (média 14) | 26%, abaixo do centro | **heptavós** — 8 gerações acima, nos dois lados |

As quatro primeiras linhas são do mesmo cartão real (154,5 cM) e a última é de um cartão de 15,1 cM. Nas
relações de ascendente direto o detalhe muda de forma: `Avô/Avó ↔ Neto(a)` traz **avós** e "2 gerações
acima; um dos dois é o próprio antepassado", porque de um lado o antepassado **é** a outra pessoa.

Duas regras de leitura entraram no rodapé do bloco, e nenhuma delas é decoração:

- a ordem é **da relação mais próxima da média da faixa para a mais distante** — o critério já estava em
  `possible_relationships` (`|média − cm|`, desempate pelo nome na fonte) e não era dito em lugar nenhum;
- **o antepassado comum não vem da fonte**, é a **definição** do parentesco. Primo de 2º grau tem os
  bisavós por definição, não por estatística — por isso essa coluna não tem versão nem ressalva de
  amostra, e é a única do bloco que não envelhece quando o Shared cM Project publicar a 5.0.

**A coluna `Probabilidade` foi recusada**, e a recusa é regra, não gosto. A versão 4.0 **não publica
probabilidade por relação** (publica número de envios, mínimo, média, máximo e desvio); os percentuais da
referência somam 100,0 %, o que afirma que a resposta está entre as listadas, e o projeto recusa fechar
esse conjunto — `1C6R`, `3C2R` e as relações mais profundas ficam fora da fonte de propósito; e na
profundidade real do arquivo (mediana de 9,05 cM) cada cartão tem **9 a 16 relações** compatíveis, com
confiança "muito baixa" em todas, então o maior percentual seria lido como resposta. No lugar entrou
`posicao_na_faixa`, que descreve o intervalo publicado sem inventar número.

A série portuguesa de graus — `avô → bisavô → trisavô → …` — saiu de `core.documentary_relationship` para
`core/graus_de_parentesco.py`, um módulo **sem import nenhum** (só `__future__`), e ganhou o plural
`bisavós`. O motivo é de dependência: `core.relationship_hypotheses` precisa do plural e é importado no
caminho da leitura do CSV; importar `documentary_relationship` de lá arrastaria `path_finding` e
`networkx`. `documentary_relationship` **reexporta** `nome_do_grau`, então quem já o importava de lá não
mudou de linha.

**6 ações concluídas** (`T001`–`T006`). Suíte em **1548 passed, 9 skipped** (1.557 coletados), com **68
casos novos**. `SHA_DA_TELA` inalterado. Na análise real: **68 cartões / 448 descartes** — os mesmos da
039 e da 040 —, **919 linhas** de tabela nas 68 páginas, **0** sem antepassado comum e **514** (56 %) com
dois lados ou meia-relação. Custo das duas colunas medido à parte: ~8 ms nas 919 linhas.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | O bloco 3 da resposta HTML de `POST /` (`action=dna_analysis`) deixa de ser lista e passa a ser tabela de quatro colunas (`Relação`, `Faixa na fonte`, `Onde o valor cai`, `Antepassado comum mais recente`), com barra da faixa e rodapé com o sentido da ordem e a natureza definicional da coluna |
| `_reversa_sdd/data-dictionary.md#62-linha-publicada-do-shared-cm-project-40` | §6.2 Linha publicada do SCP 4.0 (o **item** de `possible_relationships`) | delta-de-dados | Cada item ganha `mrca` (`graus`, `rotulo`, `detalhe`) e `posicao` (`fracao`, `percentual`, `chave`, `rotulo`) — aditivos; `key`, `name_en`, `name_pt`, `meioses`, `average`, `range_low` e `range_high` não mudam, e a ordenação também não |
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | §3.3 Possibilidades (Shared cM Project 4.0) | regra-alterada | A lista ordenada passa a carregar o **antepassado comum mais recente** — definição de parentesco, duas profundidades quando os lados diferem, "(um de dois)" nas meias-relações — e a **posição do valor na faixa**, em cinco rótulos |
| `_reversa_sdd/c4-components.md#inventário-de-componentes` | Inventário de componentes | regra-alterada | Nasce `core/graus_de_parentesco.py` (folha, sem import) e `relationship_hypotheses.py` deixa de ser "**sem dependência de projeto**": depende dessa folha, que não importa nada por sua vez. O `networkx` continua fora do caminho do CSV |
| `_reversa_sdd/addenda/017-observacao-de-arquivo-nao-e-observacao-de-cartao.md#2-a-frase-virou-fato-dos-dados` | §2 A frase virou fato dos dados | regra-alterada | A justificativa "aquele módulo não importa nada do pacote (só `__future__`)" deixa de valer na letra: ele importa `core.graus_de_parentesco`. A conclusão que ela sustentava — **não há ciclo** — continua verdadeira, agora por um motivo mais forte, e há teste que falha se a folha ganhar import |

## Regras sob vigilância

- `W001` a `W007` — ver `_reversa_forward/043-tabela-do-antepassado-comum/regression-watch.md`.
  Os primeiros quatro são os que um futuro `/reversa` deve conferir antes de reescrever as specs: a ida
  e volta dos graus, as três meias-relações fora da tabela completa, a ausência de probabilidade e a
  folha sem import.
- As cinco observações sem peso (redação das frases, cortes 15/40/60/85 % da posição, `nome_do_grau(1)`
  agora `pai/mãe`, a coluna ser a única sem fonte externa, e a convenção de `meioses` nas linhas de
  primos) estão no mesmo arquivo. **Correção de 2026-10-22:** a convenção de `meioses` é **declarada**,
  não um defeito — `core/validator.py` registra que a coluna é "a chave da relação, não o total do
  caminho" e deriva o total da chave. O ponto que segue aberto é outro: `core/evidence_comparison`
  passa um **total** a `meioses_window`, cuja coluna guarda **chaves**, e isso desloca a envoltória das
  relações não publicadas.

## Fontes

- `_reversa_forward/043-tabela-do-antepassado-comum/requirements.md`
- `_reversa_forward/043-tabela-do-antepassado-comum/roadmap.md`
- `_reversa_forward/043-tabela-do-antepassado-comum/actions.md`
- `_reversa_forward/043-tabela-do-antepassado-comum/legacy-impact.md`
- `_reversa_forward/043-tabela-do-antepassado-comum/regression-watch.md`
- `_reversa_forward/043-tabela-do-antepassado-comum/progress.jsonl`
- `_reversa_forward/043-tabela-do-antepassado-comum/interfaces/bloco-3-tabela.html` (mock estático)
