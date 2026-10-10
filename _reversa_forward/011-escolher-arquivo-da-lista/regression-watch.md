# Regression Watch: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Atualizado: `2026-10-10` — cada linha alterada traz a data na propria celula
> Origem dos itens: secao "Modificadas" do `legacy-impact.md` desta feature

## 1. Itens de vigilancia

| ID | Origem (arquivo, secao) | Regra esperada apos a mudanca | Tipo de verificacao | Sinal de violacao |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/domain.md` §4 (linha `action=dna_analysis`) | A pre-condicao e **"CSV presente OU referencia presente"**. Nenhum dos dois presentes continua recusando com a mensagem de sempre | `presenca` | A analise recusa um pedido que traz apenas `matches_csv_filename`; ou aceita um pedido sem CSV e sem referencia |
| W002 | `_reversa_sdd/domain.md` §4 | **A referencia tem PRECEDENCIA** sobre o arquivo quando os dois vem | `presenca` | O arquivo enviado junto e usado no lugar da referencia escolhida |
| W003 | `_reversa_sdd/domain.md` §4 (estado inicial da tela) | A aplicacao **nao tem mais** o estado "envie antes de tudo": `GET /` entrega as duas abas **sem envio previo** | `ausencia` | `GET /` voltar a exigir um upload antes de mostrar qualquer coisa |
| W004 | `_reversa_sdd/upload-gedcom/contracts.md#2.1` | **ATUALIZADO em 2026-10-10.** O resolvedor aceita `<16 hex>__<nome visivel>` quando a parte visivel e um **NOME**: sem barra, sem barra invertida, sem byte nulo, sem `.` nem `..`, e igual ao proprio `basename`. **A forma fechada do alfabeto foi REMOVIDA** pela `RN-20`: ela recusava o acento e o espaco que o gravador PRESERVA (`RF-06`). A defesa contra escape nunca foi o alfabeto, e sim a exigencia de ser um nome | `ausencia` | Um nome com separador de caminho, byte nulo ou `..` passar a resolver; ou voltar a existir um alfabeto fechado que recuse acento e espaco |
| W005 | `_reversa_sdd/domain.md:192` | `"Por favor, carregue o arquivo CSV de matches."` continua **literal** | `redacao` | O texto mudar sem decisao registrada |
| W006 | `_reversa_sdd/screens/golden/` | O golden `SCR-001` continua capturando o **oraculo legado congelado**, com sha256 `ec07f71b4084269a` | `presenca` | O sha256 mudar; ou alguem recapturar o golden a partir da aplicacao atual |
| W007 | `_reversa_sdd/parity/harness.py` | O harness continua **insensivel ao template**: le chaves nomeadas do contexto, e nao compara HTML | `presenca` | A paridade cair de 100 % depois de uma mudanca de tela |
| W008 | `_reversa_sdd/architecture.md` §7 (divida 8) | A aplicacao continua **sem estado entre requisicoes**: a escolha viaja por campo de formulario e nada sobrevive ao fechamento da pagina | `ausencia` | Aparecer sessao, cookie ou cache guardando a escolha do operador |

## 2. Observacoes (sem peso de regressao)

Regras que nao eram 🟢 na extracao, ou que sao consequencia de decisao desta feature e nao de regra
do legado. **Nao entram em priorizacao automatica.**

| ID | Observacao |
|----|------------|
| OBS-01 | **RESOLVIDO em 2026-10-10, com correcao de rumo.** O item dizia que `T020` e `T021` foram verificadas sem teste de tela. A conferencia clausula a clausula mostrou que **a maior parte ja estava coberta** por testes escritos depois do registro — `test_tabela_da_tela.py` e `test_lista_na_tela.py` prendem nome, data, contagem do grupo, a marca de indisponivel COM o motivo, e que a escolha nao e oferecida. Restavam **tres lacunas reais**, e as tres foram fechadas: (a) o **valor** de bytes nao era assertado em lugar nenhum, so o rotulo da coluna; (b) da aba de **DNA** so se assertava o nome do relatorio, e nao as colunas dela, apesar de a `T020` dizer "as duas listas"; (c) o **campo de escolha do CSV** (`T021`) tinha o contrato da ROTA coberto por tres testes em `test_dna_analysis.py`, e **nenhum** assertando o campo no template — a prova e que `name="matches_csv_filename"` nao aparecia em teste nenhum, entao **se o `<select>` sumisse da tela os tres testes continuariam verdes**. Fechadas por 2 testes em `test_tabela_da_tela.py` e 3 em `tests/test_campo_de_escolha_do_csv.py` |
| OBS-02 | **Conflito com a feature 009, RESOLVIDO em 2026-10-09.** `test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte` prendia o `GET /` por SHA fixo. A constante foi **atualizada** (`4b7f0b0c…` → `e18d1749…`, de 23.906 para 25.825 bytes) e o comentario dela passou a registrar quem mudou a tela e por que. Nao foi afrouxamento: o proprio comentario anterior declarava o criterio — "qualquer mudanca aqui e mudanca de tela, e nao desta feature" —, e foi o que aconteceu. O teste continua prendendo que nenhuma mudanca de tela passe despercebida. Suite final: **381 passed, 9 skipped, zero falhas** |
| OBS-03 | **`RN-11` e `RF-09` nasceram de medicao, nao de requisito original.** A auditoria da feature mediu que **7 dos 19 arquivos** sao inalcancaveis por referencia, e o plano passou a marcar o item em vez de esconde-lo. **Atualizacao de 2026-10-10:** depois da `RN-20`, os inalcancaveis **por acento ou espaco foram a ZERO**; o que resta sao os arquivos **sem chave**, que a referencia nao alcanca de jeito nenhum |
| OBS-04 | **RESOLVIDO em 2026-10-10.** O defeito de raiz do nome ficou fora do escopo da `011` e virou o `BUG-20261009-6RKP`, que foi **encerrado**: `DONE.md` gravado, `resolution_kind: fixed`, `spec_verdict: spec-correta` (a spec estava CERTA e o codigo divergia dela), conserto declarado na `RN-20` e medicao de **13 de 13 arquivos aceitos** por referencia. A `011` marcava o item na tela; depois do conserto ele deixou de precisar da marca |
| OBS-05 | **A mitigacao de 2026-10-09 renomeou 4 arquivos da pasta real**, tirando acento e espaco do nome visivel e preservando a chave. E `temporary: true`. **Premissa resolvida em 2026-10-10:** o conserto decidiu **aceitar acento na leitura**, entao as renomeacoes sao **desnecessarias** — e continuam aplicadas, porque o conserto NAO as desfaz. Os nomes de hoje tambem ja nao sao os da mitigacao: o operador renomeou arquivos por conta propria depois dela |

## 3. Historico de re-extracoes

### Re-extração 2026-10-10 21:40

**Primeira verificação real destes watch items.**

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | A pré-condição é "CSV **ou** referência": `RF-01` de `analise-dna/requirements.md` e `analise-dna/contracts.md` §1.1. O literal `"Por favor, carregue o arquivo CSV de matches."` presente (medido). |
| W002 | 🟢 verde | A **precedência da referência** é contrato de estabilidade **Alta** em `analise-dna/contracts.md` §1.1 e §9, com a justificativa de que inverter reintroduz o CSV duplicado na lista. `BR-D-89`. |
| W003 | 🟢 verde | `GET /` entrega as **duas abas sem envio prévio**: `tela-de-entrada/contracts.md` §1 e §2 (as listas vêm por processador de contexto, em **toda** renderização). `BR-T-01`; o estado "envie antes de tudo" não existe. |
| W004 | 🟢 verde | Confirmado: a elegibilidade é por **forma de nome** e o alfabeto fechado **não** existe mais. As duas funções estão em `upload-gedcom/contracts.md` §2.2 e a **defesa não afrouxou em `resolver`**. `RN-20`/`ADR-32`. |
| W005 | 🟢 verde | O literal continua exatamente `"Por favor, carregue o arquivo CSV de matches."` (1 ocorrência em `src/app.py`, medido) e está tabelado em `analise-dna/contracts.md` §7.1. |
| W006 | 🟢 verde | **`SCR-001-initial-upload.html.txt` tem `sha256 ec07f71b4084269a…`** — exatamente o esperado (medido). E a **substância** foi conferida: o arquivo **não** contém nenhum marcador do app atual (`banner.png`, `arvores_da_lista`, `Apagar`, `selecionar_arvore`, `Enviado em` — todos com **zero** ocorrências), isto é, continua sendo o HTML do **oráculo**, não uma recaptura da aplicação. ⚠️ Ver o achado novo sobre o **manifesto**, na observação abaixo. |
| W007 | 🟢 verde | O harness continua **insensível ao template**: `tela-de-entrada/design.md` § Riscos e `contracts.md` §7 registram que ele substitui `render_template` por captura de contexto e que o processador de contexto **não roda** — a cobertura das listas é da suíte, por construção. |
| W008 | 🟢 verde | A aplicação continua **sem estado entre requisições**: medido, **zero** ocorrências de `session`/`cookie`/`flask.session` no template, e a escolha viaja por campo oculto. `ADR-24` removeu até o estado de árvore. |

> ⚠️ **Achado novo desta verificação, registrado sem alterar a tabela principal:** o `manifest.yaml` dos goldens declara, para `SCR-001-initial-upload.html.txt`, o `sha256 2e2a5c02…` — **diferente** do hash dos bytes em disco (`ec07f71b…`). O mesmo ocorre em `SCR-G01` e `SCR-G02`. Como o oráculo **não** mudou (sha256 `44370b23…`), a explicação provável é que o texto foi recapturado sobre uma **revisão intermediária do template** — que não é congelado —, e o manifesto nunca foi atualizado. **O conteúdo está certo** (é o oráculo, conferido acima); o que está quebrado é a **cadeia de integridade do manifesto**. Decisão humana necessária: atualizar o manifesto, ou documentar a convenção de hash dos `.html.txt`.

*(vazio: sera preenchido pelo agente reverso quando `/reversa` rodar de novo)*

## 4. Arquivadas

*(vazio)*
