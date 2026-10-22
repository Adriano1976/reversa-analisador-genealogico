# Actions: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/039-dna-sem-correspondencia/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 13 |
| Paralelizáveis (`[//]`) | 5 |
| Maior cadeia de dependência | 10 (T001 → T002 → T004 → T006 → T007 → T008 → T010 → T011 → T012 → T013) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Medir a linha de base antes de tocar em código: rodar a suíte completa, registrar `passed`/`skipped`/`failed` e o `SHA_DA_TELA`, e salvar em `evidence/antes/suite.txt` e `evidence/antes/hash.txt` | - | - | `_reversa_forward/039-dna-sem-correspondencia/evidence/antes/` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Criar `tests/test_sem_correspondencia.py` com os testes do seletor: 40,0 entra e 39,9 não; candidato compatível exclui; nome com cartão em outro kit exclui; ordem por cM e desempate estável; MRCA `None` preservado; dois kits do mesmo nome sem cartão viram duas linhas; nenhuma soma entre kits | T001 | `[//]` | `tests/test_sem_correspondencia.py` | 🟢 | `[X]` |
| T003 | Acrescentar ao mesmo arquivo os testes de renderização: bloco com itens, nome/kit/cM/MRCA, aviso, ausência de parentesco/diagrama/promoção, lista completa intacta, zero itens, zero cartões e link no resumo | T002 | - | `tests/test_sem_correspondencia.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar `src/core/sem_correspondencia.py` com `CM_MINIMO_SEM_CORRESPONDENCIA = 40.0`, a função `selecionar(resultados, descartados, limite_cm=...)` e o docstring com a medição; filtro por cM, candidato compatível e nome com cartão; ordem `(-cm, norm_name(csv_name), csv_name, kit)` | T002 | `[//]` | `src/core/sem_correspondencia.py` | 🟢 | `[X]` |
| T005 | Acrescentar `mrca_generations` ao dicionário de descarte em `src/core/dna_analysis.py`, copiando de `kit["mrca_generations"]`, sem tocar em nenhuma decisão de aceitação | T001 | `[//]` | `src/core/dna_analysis.py` | 🟢 | `[X]` |
| T006 | Acrescentar `sem_correspondencia: tuple = ()` a `ResultadoDeAnalise` e chamar `core.sem_correspondencia.selecionar(resultados, descartados)` em `src/application/dna_analysis.py`; a projeção histórica não muda | T004, T005 | - | `src/application/dna_analysis.py` | 🟢 | `[X]` |
| T007 | Passar `sem_correspondencia=resultado.sem_correspondencia` ao `render_template` do ramo `dna_analysis` em `src/app.py`, sem tocar nos outros ramos | T006 | - | `src/app.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Renderizar o bloco em `src/templates/index.html` dentro do `{% if skipped_matches %}`, antes do `bloco-descartados`, com título/contagem, aviso, tabela nome/kit/cM/MRCA e link no resumo; adicionar a aparência de aviso em `src/assets/app.css`; sem promoção, candidato, motivo, diagrama ou confronto | T007 | `[//]` | `src/templates/index.html`, `src/assets/app.css` | 🟡 | `[X]` |
| T009 | Atualizar os testes que comparam o dicionário de descarte (`test_characterization_matching.py`, `test_dna_analysis.py`, `test_candidatos_do_descarte.py`) para incluir `mrca_generations` de forma explícita, sem afrouxar a comparação das decisões | T005 | `[//]` | `tests/test_characterization_matching.py`, `tests/test_dna_analysis.py`, `tests/test_candidatos_do_descarte.py` | 🟢 | `[X]` |
| T010 | Atualizar os testes de integração da tela (`test_cartoes_recolhiveis.py`, `test_estilo_da_tela.py`, `test_icone_de_atalho.py`) para o bloco novo: ele não é cartão de resultado nem rodapé de descartes, a classe de aviso existe e o hash da tela de entrada não muda | T008 | - | `tests/test_cartoes_recolhiveis.py`, `tests/test_estilo_da_tela.py`, `tests/test_icone_de_atalho.py` | 🟢 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Fechar a verificação: rodar os testes focados e a suíte completa, corrigir regressões, medir `SHA_DA_TELA` e gravar `evidence/depois/suite.txt`, `hash.txt` e `escopo.txt` | T010, T009 | - | `_reversa_forward/039-dna-sem-correspondencia/evidence/depois/` | 🟢 | `[X]` |
| T012 | Rodar a análise real (árvore v3 tratada + CSV Sergipanas) e conferir 8 conexões/448 descartes, bloco com 9 itens, primeiro `Clezia Santos` (154,5 cM), `Airton Passos Vasconcelos` (51,3 cM), lista completa com 448 e CSV com nove colunas; gravar `evidence/depois/analise.txt` | T011 | - | `_reversa_forward/039-dna-sem-correspondencia/evidence/depois/analise.txt` | 🟢 | `[X]` |
| T013 | Gravar `legacy-impact.md` e `regression-watch.md` da feature, listando arquivos tocados, a chave aditiva, a constante de 40,0 e as regras sob vigilância | T012 | - | `_reversa_forward/039-dna-sem-correspondencia/` | 🟢 | `[X]` |

## Notas de execução

- **T002/T003:** o arquivo novo fechou com **17 testes** — 10 do seletor e 7 do bloco na tela.
- **T009:** só `tests/test_characterization_matching.py` precisou da chave aditiva. `test_dna_analysis.py` e `test_candidatos_do_descarte.py` já liam campos do descarte, e não o dicionário inteiro; passaram sem edição.
- **T010:** além dos três arquivos previstos, `tests/test_promocao_de_descarte.py` ganhou `sem_correspondencia = ()` no `_ResultadoFalso` (o `app.py` passou a ler o campo). `test_cartoes_recolhiveis.py` e `test_icone_de_atalho.py` passaram sem edição; `test_estilo_da_tela.py` ganhou a classe `bloco-sem-correspondencia`.
- **T011:** suíte completa em **1411 passed, 9 skipped** (antes: 1394/9; delta de +17). `SHA_DA_TELA` e `TAMANHO_ESPERADO` inalterados.
- **T012:** análise real confirmou **8 cartões, 448 descartes e 9 no bloco**; Clezia 154,5 cM (AZ4078391, MRCA 3,27) em primeiro, Airton 51,3 cM (SD5093704, MRCA 4,06) presente; CSV com nove colunas e 449 linhas.
- **E003:** `sem_correspondencia.py` passou de 88 para 70 linhas; `dna_analysis.py` (núcleo) de 1111 para 1102; o caso de uso de 341 para 339; o teste de 276 para 251 (15 testes). Suíte em **1409 passed, 9 skipped** (−3 testes do seletor); análise real inalterada em **68 cartões (8 + 60), 448 descartes**, CSV 9/449; promoção e lista completa intactas.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-22 | Execução pelo `/reversa-coding`: 13/13 ações concluídas | reversa |

## Emendas

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| E001 | Corte de triagem de 40,0 para 20,0 cM | - | - | `src/core/sem_correspondencia.py` | 🟢 | `[X]` |
| E002 | Itens sem correspondência viram cartões na lista de resultados, com o tratamento de "Parentesco documental não encontrado"; o bloco separado deixa de existir e a lista completa/CSV ficam intactos | E001 | - | `src/core/dna_analysis.py`, `src/application/dna_analysis.py`, `src/templates/index.html`, `src/assets/app.css`, `tests/` | 🟡 | `[X]` |
| E003 | Limpeza sem mudança de comportamento: `core.sem_correspondencia.selecionar` sai; ficam `elegivel` e `nomes_com_cartao_aceito`; a aplicação deriva `sem_correspondencia` dos cartões já em `resultados`; testes do seletor viram testes da regra + ordem dos cartões | E002 | - | `src/core/sem_correspondencia.py`, `src/core/dna_analysis.py`, `src/application/dna_analysis.py`, `src/app.py`, `tests/test_sem_correspondencia.py` | 🟢 | `[X]` |
