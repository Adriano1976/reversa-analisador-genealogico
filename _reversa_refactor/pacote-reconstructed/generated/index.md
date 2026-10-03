<!-- GENERATED, DO NOT EDIT: regenerado por /reversa-modularize em 2026-10-03 a partir de 9 oportunidades e 7 transformacoes -->

# Índice de qualidade de código · pacote-reconstructed

> Gerado em `2026-10-03`. Fonte de verdade: `../opportunities/*.md`.
> Sete transformações aplicadas neste contexto, e duas oportunidades abertas.

## Oportunidades

Ordenadas por retorno estimado, não pela ordem da árvore proposta.

| # | ID | Verbo | Confiança | Impacto | Custo | Estado | Retorno esperado |
|---|----|-------|-----------|---------|-------|--------|------------------|
| #19 | `OPP-20261003-TWNT` | modularize | green | acoplamento: seis módulos importavam as globais de `upload.py` | low | **applied** | estado separado do carregamento, e o split em `parsers/` deixa de esconder o estado dentro do parser |
| #20 | `OPP-20261003-DWJC` | decouple | green | acoplamento estrutural: um módulo interno importa pela fachada | low | **applied** | a fachada volta a existir só para consumidores externos |
| #21 | `OPP-20261003-RGKA` | modularize | green | coesão e auditabilidade: heurística de domínio presa no fluxo | low | **applied** | heurística de cM isolada e auditável, com a origem declarada |
| #22 | `OPP-20261003-LMAY` | standardize | green | clareza: um nome descrevia uma camada que o módulo nunca foi | low | **applied** | nome alinhado ao papel real, e a árvore do README coerente com o disco |
| #18 | `OPP-20261003-GUE7` | modularize | green | clareza: módulos planos, cinco papéis, nenhuma fronteira visível | high | **applied** | fronteiras explícitas entre parsing, núcleo, apresentação e validação |
| #23 | `OPP-20261003-FLAT` | modularize | green | clareza: um nível de pacote que expressa proveniência, não responsabilidade | medium | **applied** | o núcleo pendurado direto em `src/`, sem o nível `reconstructed` |
| #24 | `OPP-20261003-RAIZ` | modularize | green | risco de nome global: cinco módulos soltos na raiz viram nomes de primeiro nível | medium | **applied** | raiz do pacote limpa, com só `__init__.py` e os subpacotes |
| #25 | `OPP-20261003-PAST` | standardize | green | nomes de duas pastas e de dois módulos divergem do exemplo do usuário | low | proposed | `parser/`, `generator/`, `state.py` e `analyzer.py`, se o usuário preferir |
| #26 | `OPP-20261003-INIT` | modularize | red | **contradiz a RN-01 e reintroduz risco de duplo carregamento já medido** | low | proposed | nenhum ganho: a intenção do exemplo já é atendida sem o arquivo |

## Transformações

| OPP | Estado | Plano | Diferenças aplicadas | Rede de segurança |
|-----|--------|-------|----------------------|-------------------|
| `OPP-20261003-TWNT` | **aplicada em 2026-10-03** | `plan.html` | 20 arquivos (3 estruturais, 17 de migração) | suíte na linha de base e paridade em 100 por cento |
| `OPP-20261003-DWJC` | **aplicada em 2026-10-03** | `plan.html` | 1 arquivo, 1 linha trocada por 2 | suíte na linha de base e paridade em 100 por cento; fan-in interno da fachada de 1 para 0 |
| `OPP-20261003-RGKA` | **aplicada em 2026-10-03** | `plan.html` | 2 arquivos novos e 1 arquivo reduzido de 137 para 122 linhas | suíte, paridade e equivalência direta da costura em 51 sondagens |
| `OPP-20261003-LMAY` | **aplicada em 2026-10-03** | `plan.html` | 1 arquivo renomeado, 4 importadores, 1 comentário e o README | código intacto por AST, suíte, paridade e 12 referências ao nome antigo reduzidas a 0 |
| `OPP-20261003-GUE7` | **aplicada em 2026-10-03** | `plan.html` | 7 módulos movidos, 30 linhas de import em 18 arquivos e o README | AST dos sete módulos idêntico ao da cópia congelada, 134 imports resolvidos por AST, suíte e paridade |
| `OPP-20261003-RAIZ` | **aplicada em 2026-10-03** | `plan.html` | 5 módulos movidos, `utils/` criado e 42 linhas em 21 arquivos | os três que não importam o pacote byte a byte idênticos, 134 imports resolvidos, caminho do `_verify_fix_gives_parity` verificado, suíte e paridade |
| `OPP-20261003-FLAT` | **aplicada em 2026-10-03** | `plan.html` | 4 pastas subiram, `reconstructed/` apagado, 12 relativos viraram absolutos, 31 prefixos removidos e 10 citações | AST idêntico nos 18 arquivos, zero `from ..` e zero prefixo restantes, `SRC`/`STUB`/`alvo` verificados, suíte e paridade; watch `W001` reescrito |

### Efeito da `OPP-20261003-TWNT`

`src/reconstructed/upload.py` deixou de existir. Em seu lugar:

| Módulo | Responsabilidade única | Linhas |
|--------|------------------------|--------|
| `gedcom_state.py` | registro do estado do processo e acesso aos registros | 45 |
| `gedcom_parser.py` | leitura do GEDCOM e construção do grafo | 67 |

A transformação ficou vermelha na primeira aplicação (suíte com 60 erros) e foi revertida pelo diff antes de ser corrigida e reaplicada.

### Efeito da `OPP-20261003-RGKA`

| Módulo | Responsabilidade única | Linhas | Fan-out interno |
|--------|------------------------|--------|-----------------|
| `core/cm_estimator.py` | traduzir um valor de cM nas relações prováveis daquela faixa | 57 | **0** |

Efeito medido: `dna_analysis.py` de 137 para 122 linhas e de 4 para 2 definições de topo. O princípio V **continua formalmente aberto**: a transformação declara a ausência de fonte no próprio módulo, e não fecha a lacuna, porque a referência não existe no repositório.

### Efeito da `OPP-20261003-LMAY`

| Módulo | Responsabilidade única | Linhas |
|--------|------------------------|--------|
| `text_cleaning.py` | limpeza de texto corrompido: `strip_bad_utf` e `demojibake` | 86 |

**12 referências vivas ao nome antigo reduzidas a 0**, com o corpo do módulo provado idêntico por AST. O harness de paridade importa o módulo **dentro de uma string**, e o que garante que a linha foi atualizada é a paridade ter rodado.

### Efeito da `OPP-20261003-GUE7`

A árvore do pacote passou a expressar os papéis que antes só os docstrings diziam:

```text
core/        decidir sobre o que foi lido, sem saber de HTTP
parsers/     ler o mundo de fora: o arquivo GEDCOM e o CSV de matches
reporting/   transformar resultado em apresentação
```

Efeito medido: 1 subpacote para 3; 12 módulos soltos na raiz para 5; **zero linha de lógica alterada**, provado por AST contra a cópia congelada antes da transformação.

Duas partes do registro original **não** foram executadas, e a recusa está registrada no `transformation.md` e no registro da oportunidade: as duas fusões de módulo (`core/fuzzy_matcher.py` e `core/path_finder.py`), que desfariam a `ZV52` e a `UXEF`, e os dois renomes, que a `LMAY` já havia julgado desnecessários.

### Efeito da `OPP-20261003-RAIZ`

A raiz do pacote ficou só com o `__init__.py`:

```text
core/        cm_estimator, matching, name_normalization, path_finding,
             family_navigation, gedcom_state, path_search, dna_analysis
parsers/     gedcom_parser, csv_ingest
reporting/   mermaid_render
utils/       text_cleaning, validate      (subpacote novo)
```

Efeito medido: 5 módulos soltos na raiz para **0**; 3 subpacotes para 4; 42 linhas reescritas em 21 arquivos com **zero linha de lógica alterada**. `gedcom_state.py`, `text_cleaning.py` e `validate.py` continuam **byte a byte idênticos**, porque não importam nada do pacote.

A armadilha que nenhum gate enxerga foi tratada neste lote: o `_verify_fix_gives_parity.py` abria `gedcom_state.py` por nome, e passaria a estourar `FileNotFoundError` sem que a suíte ou a paridade avisassem. A conferência agora **verifica esse caminho**.

Os dois renomes previstos no registro foram **transferidos para a `OPP-20261003-PAST`**: renomear e mover são verbos diferentes, e misturá-los estragaria a prova por AST.

### Efeito da `OPP-20261003-FLAT`

O nível de pacote deixou de existir, e o núcleo passou a ser importado direto de `src/`:

```text
src/
├── app.py
├── core/        cm_estimator, matching, name_normalization, path_finding,
│                family_navigation, gedcom_state, path_search, dna_analysis
├── parsers/     gedcom_parser, csv_ingest
├── reporting/   mermaid_render
├── utils/       text_cleaning, validate
├── templates/
└── uploads/
```

Efeito medido: **12 imports entre subpacotes deixaram de ser relativos** e viraram absolutos, porque com os quatro pacotes em primeiro nível `from ..X` é inválido. Mais 31 linhas de import perderam o prefixo `reconstructed.`, e **zero linha de lógica mudou**, provado por AST contra a cópia congelada nos 18 arquivos.

Duas coisas além do plano, ambas registradas:

- o `_verify_fix_gives_parity.py` tinha **código** apontando para `src/reconstructed`, que deixou de existir. Quarta aparição dessa classe de defeito na série, e segunda seguida no mesmo arquivo;
- o watch **`W001` foi reescrito** para a nova identidade do núcleo, com a avaliação registrada. Sem isso ele ficaria permanentemente vermelho.

Risco declarado, e não realizado: `core`, `parsers`, `reporting` e `utils` agora são nomes de primeiro nível, e os quatro estão livres em `site-packages`.

## Mapa do exemplo do usuário contra o projeto real

O exemplo traz uma árvore genérica. Confrontada com o disco, parte dela já existe, parte não tem correspondente e parte contradiz decisão registrada:

| Item do exemplo | Neste projeto | Situação |
|---|---|---|
| `src/__init__.py` | não existe, e a RN-01 proíbe | **conflito registrado** (`OPP-20261003-INIT`) |
| `src/main.py` | `src/app.py` | renomear mudaria o comando documentado, `python src/app.py` |
| `parser/gedcom_parser.py` | `parsers/gedcom_parser.py` | existe, muda só o nome da pasta (`OPP-20261003-PAST`) |
| `parser/legacy_reader.py` | **nada aqui lê código legado** | o nome descreve outro sistema |
| `core/analyzer.py` | `core/dna_analysis.py` | **já está em `core/`**; falta só o nome (`OPP-20261003-PAST`) |
| `core/rules.py` | as regras estão em `core/matching.py`, `core/cm_estimator.py` e `utils/validate.py` | não há módulo de regras separado |
| `models/person.py` | **removido de propósito em 2026-09-30** | recria arquitetura descartada, `/reversa-requirements` |
| `models/relationship.py` | não existe; aresta tipada é o princípio IV | muda comportamento, `/reversa-requirements` |
| `generator/mermaid_render.py` | `reporting/mermaid_render.py` | existe com outro nome de pasta (`OPP-20261003-PAST`) |
| `generator/code_generator.py` | o projeto não gera código | capacidade nova |
| `generator/report_factory.py` | o fluxo monta a lista de resultados direto | abstração sem consumidor, `/reversa-requirements` |
| `utils/text_cleaning.py` | `utils/text_cleaning.py` | **idêntico ao exemplo** |
| `utils/file_handler.py` | a limpeza de temporários não existe | capacidade nova, `/reversa-requirements` |
| `utils/logger.py` | o projeto não tem logging | capacidade nova, `/reversa-requirements` |

**Conclusão:** a árvore do exemplo **está de pé**, com quatro diferenças de nome. `src/` tem `app.py`, quatro pacotes e `templates/`/`uploads/`, que é exatamente a forma pedida. `models/` fica fora, porque o projeto não tem modelo de classes por decisão de 2026-09-30, e `utils/` recebe dois utilitários, não os quatro do exemplo.

## Ordem de encadeamento

| Ordem | Oportunidade | Verbo | Por quê nesta posição |
|---|---|---|---|
| ~~1~~ | ~~`OPP-20261003-RAIZ`~~ | modularize | **aplicada em 2026-10-03.** Deixou a raiz do pacote só com `__init__.py` e os subpacotes |
| ~~2~~ | ~~`OPP-20261003-FLAT`~~ | modularize | **aplicada em 2026-10-03.** Subiu os quatro pacotes e apagou o nível `reconstructed` |
| 3 | `OPP-20261003-PAST` | standardize | os quatro nomes do exemplo: `parser/`, `generator/`, `state.py` e `analyzer.py` |
| não rotear | `OPP-20261003-INIT` | modularize | contradiz a RN-01. Se o usuário quiser `src` como pacote, o caminho é mudar o requisito primeiro |

Cada passo é uma transformação separada, com gate e prova próprios: mover e provar antes de renomear, como já ficou estabelecido na série.

## Fora do escopo do time Code Quality

Itens da árvore proposta que **não são refactor**, por alterarem comportamento observável ou introduzirem capacidade inexistente. Cada um é candidato a `/reversa-requirements`.

| Item proposto | Motivo | Encaminhamento |
|---|---|---|
| `models/person.py` | reintroduz modelo de classes removido deliberadamente em 2026-09-30 | `/reversa-requirements` |
| `models/relationship.py` (aresta tipada) | muda comportamento: implementa o princípio IV, ainda não implementado | `/reversa-requirements` |
| `utils/logger.py` | o projeto não tem logging algum | `/reversa-requirements` |
| `utils/file_handler.py` com limpeza de temporários | a limpeza não existe; e mover `validate.py` renomearia módulo que carrega contrato vigente | `/reversa-requirements` |
| `reporting/report_factory.py` | não existe fábrica de relatório, e abstração sem consumidor foi o que produziu as entidades removidas | `/reversa-requirements` |
| `src/__init__.py` | conflita com RN-01: `src` é raiz de caminho, não pacote | registrado como `OPP-20261003-INIT`, com recomendação de não rotear |

## Candidatos novos, ainda não registrados

Observados durante as cinco transformações, e nenhum deles é código morto por acidente:

| Observação | Verbo provável |
|---|---|
| `_reversa_sdd/parity/harness.py` importa `text_cleaning` como `DM` e **nunca usa** o alias | `prune` |
| `tests/test_domain.py` testa `text_cleaning.py` e mantém o nome antigo no arquivo | `standardize` |

## Pendências de registro, conhecidas

| Onde | O que está desatualizado |
|---|---|
| `README.md` deste registro | diz que o harness de paridade "não pode mais rodar" e que a suíte tem 76 testes. Ele roda, dá 100 por cento, e a suíte tem 118 aprovados |
| `_reversa_sdd/` e `_reversa_docs/` | ainda citam `analisador-genealogico/`, componentes na raiz do pacote e `domain.py`. São artefatos de extração e de documentação publicada, de outros donos |
| `.reversa/soul.md` | a linha 39 chama a tabela de cM de "padrão do Shared cM Project", e a decisão humana de 2026-09-30 diz o contrário |

## Legenda

- Confiança: 🟢 coberto e entendido | 🟡 parcial | 🔴 sem prova de comportamento
- Custo: `low` | `medium` | `high`
- Estado: `proposed` | `approved` | `applied` | `reverted` | `declined`

---
*Gerado pelo Reversa-Refactor em 2026-10-03.*
