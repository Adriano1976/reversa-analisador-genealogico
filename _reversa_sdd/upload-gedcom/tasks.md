# Unit `upload-gedcom` — Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Re-extração de **2026-10-05** (nível **Completo**). Substitui as tasks de 2026-09-30.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências disponíveis e **pinadas**: `Flask==3.1.3`, `ged4py==0.5.2`, `networkx==3.6.1`, `waitress==3.0.2` 🟢
- [ ] Pasta de upload criada e gravável — é criada **no import**, pela mesma função que a resolve (`app.py:60-62`) 🟢
- [ ] `ANALISADOR_UPLOAD_FOLDER` documentado (sobrepõe a pasta; usado pelos testes para não escrever na pasta real) 🟢
- [ ] **Atenção à divergência de ambiente:** o `.venv/` do repositório **não reproduz** o pin em 5 pacotes (`ged4py` 0.5.5, `networkx` 3.7, `pandas` 3.0.6, `RapidFuzz` 3.14.6, `python-Levenshtein` 0.27.5). O fluxo documentado é o interpretador **global** (`L-19`) 🟢
- [ ] **Não aplicável:** schema, migrations ou banco de dados — o sistema não tem nenhum 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] **T-01**, Implementar a rota única `GET /` que renderiza `index.html`
  - Origem no legado: `src/app.py:112`, `:176`
  - Critério de pronto: `GET /` devolve `200` com o formulário de upload, sem estado
  - Confiança: 🟢

- [ ] **T-02**, Implementar o despacho por campo `action` no `POST /`
  - Origem no legado: `src/app.py:114-116`
  - Critério de pronto: `action=upload_gedcom` entra no ramo de upload; os outros dois valores caem nos seus ramos; `POST` sem `gedcom_filename` devolve `"Erro: Arquivo GEDCOM não encontrado."`
  - Confiança: 🟢

- [ ] **T-03**, Validar presença do campo `gedcom` e nome de arquivo não vazio
  - Origem no legado: `src/app.py:117-121`
  - Critério de pronto: `"Nenhum arquivo GEDCOM enviado."` e `"Nenhum arquivo selecionado."` conforme o caso, ambos com `success=False`
  - Confiança: 🟢

- [ ] **T-04**, Implementar o teto de corpo de 16 MB com handler de `413` em português
  - Origem no legado: `src/app.py:32`, `:65-72`
  - Critério de pronto: corpo acima do teto devolve `413` com `"Arquivo maior que o limite de {n} MB."`; **nenhum byte é lido nem gravado**
  - Confiança: 🟢
  - ⚠️ A mensagem **interpola** o valor do teto: mudar a constante muda texto de contrato (`spec-impact-matrix.md` §5).

- [ ] **T-05**, Implementar `validar_conteudo_gedcom` com as três recusas nomeadas
  - Origem no legado: `src/utils/validate.py:90-105`
  - Critério de pronto: `arquivo vazio`, `conteudo binario` e `não começa com a declaração 0 HEAD`; remove **um** BOM UTF-8 e os espaços à esquerda antes de comparar
  - Confiança: 🟢
  - ⚠️ Validação **estreita de propósito**: só o cabeçalho. A gramática fica com o `ged4py`.

- [ ] **T-06**, Implementar `chave_de_armazenamento` = `sha256(conteudo).hexdigest()[:16]`
  - Origem no legado: `src/utils/validate.py:68-70`
  - Critério de pronto: mesmo conteúdo → mesma chave, em processos diferentes
  - Confiança: 🟢

- [ ] **T-07**, Implementar `nome_visivel_seguro` preservando a extensão original
  - Origem no legado: `src/utils/validate.py:40-65`
  - Critério de pronto: `/`, `\` e NUL viram `_`; acentos e espaços preservados; `matches.csv` continua `.csv`; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged`
  - Confiança: 🟢
  - ⚠️ **Não fixar a extensão em `.ged`.** Fixá-la renomeou o CSV para `<...>.csv.ged` e quebrou a análise de DNA — regressão do `BUG-20260929-QMLY`, corrigida em 2026-10-02.

- [ ] **T-08**, Implementar `chave_recebida_e_valida` pela forma fechada
  - Origem no legado: `src/utils/validate.py:31-32`, `:78-87`
  - Critério de pronto: aceita apenas `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`; recusa ausente, vazio, com separador de caminho ou com nome escolhido pelo cliente
  - Confiança: 🟢

- [ ] **T-09**, Implementar `_guardar_upload` com leitura integral, validação prévia e gravação idempotente, devolvendo o **caminho completo**
  - Origem no legado: `src/app.py:75-96`
  - Critério de pronto: `(caminho_completo, None)` no sucesso; `(None, motivo)` na recusa; arquivo existente não é reescrito
  - Confiança: 🟢

- [ ] **T-10**, Implementar `_resolver_caminho_armazenado` validando a forma antes de compor o caminho
  - Origem no legado: `src/app.py:99-108`
  - Critério de pronto: valor fora da forma → `None`; valor válido mas inexistente em disco → `None`
  - Confiança: 🟢

- [ ] **T-11**, Ancorar a pasta de upload no arquivo do app, com criação no import
  - Origem no legado: `src/app.py:42-62`
  - Critério de pronto: o diretório criado e o procurado vêm da **mesma** função; `ANALISADOR_UPLOAD_FOLDER` redireciona
  - Confiança: 🟢

- [ ] **T-12**, Implementar `ref_id(val)` tolerante a objeto ged4py ou string
  - Origem no legado: `src/core/gedcom_state.py:33-36`
  - Critério de pronto: `ref_id("X") == "X"` e `ref_id(obj) == obj.xref_id`
  - Confiança: 🟢

- [ ] **T-13**, Implementar `get_name(person)` com a expressão exata
  - Origem no legado: `src/core/gedcom_state.py:38-52`
  - Critério de pronto: `person.name.format()` quando `person and person.name`; `"Sem Nome"` caso contrário; **formato vazio devolve `''`**
  - Confiança: 🟢
  - ⚠️ **Não tratar formato vazio.** Foi essa "melhoria" que gerou a divergência `DIV-001` contra o oráculo congelado.

- [ ] **T-14**, Implementar a limpeza de mojibake como autoridade única
  - Origem no legado: `src/utils/text_cleaning.py:37-54`, `:56`
  - Critério de pronto: 18 pares de substituição; *round-trip* `latin1 → utf-8` só quando há indício de mojibake **e** só se o resultado não contiver resíduo
  - Confiança: 🟢

- [ ] **T-15**, Parsear `INDI` e `FAM` com `GedcomReader` e indexar por `xref_id`
  - Origem no legado: `src/parsers/gedcom_parser.py:56-57`
  - Critério de pronto: `people` e `families` preenchidos após o parse
  - Confiança: 🟢

- [ ] **T-16**, Construir o grafo bipartido com nós tipados e arestas só para ids resolvíveis, mais o índice `child_to_family`
  - Origem no legado: `src/parsers/gedcom_parser.py:18-48`, `:62-63`
  - Critério de pronto: `type="person"` e `type="family"`; nenhuma aresta para id inexistente; `FAM` sem `xref_id` ignorada; pessoa filha em 2 famílias aparece com 2 entradas
  - Confiança: 🟢

- [ ] **T-17**, Publicar o estado com a assimetria deliberada e incrementar `versao`
  - Origem no legado: `src/parsers/gedcom_parser.py:65-67`
  - Critério de pronto: `people`, `families` e `child_to_family` sofrem `clear()` + `update()` (**identidade preservada**); `graph` sofre reatribuição; `versao` cresce
  - Confiança: 🟢
  - ⚠️ A assimetria é contrato, não estilo: os três primeiros mantêm válidos os bindings importados no topo; o `graph` é lido por import **dentro da função** (`path_finding.py:38`).

- [ ] **T-18**, Devolver a lista de nomes ordenada, com um item por pessoa
  - Origem no legado: `src/parsers/gedcom_parser.py:68`
  - Critério de pronto: a lista é igual à sua versão ordenada, e a contagem é igual à de `people`
  - Confiança: 🟢

- [ ] **T-19**, Tratar exceção de parse com mensagem amigável, preservando o estado anterior
  - Origem no legado: `src/app.py:128-129`
  - Critério de pronto: GEDCOM malformado gera `"Erro ao processar GEDCOM: {e}"` sem derrubar; as globais permanecem íntegras
  - Confiança: 🟢

- [ ] **T-20**, Tratar chave ausente ou inválida nos fluxos pós-upload
  - Origem no legado: `src/app.py:131-136`
  - Critério de pronto: ausente → `"Erro: Arquivo GEDCOM não encontrado."`; inválida ou removida → `"Erro: Arquivo '{valor}' não existe mais."`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] **TT-01**, `ref_id` com string e com objeto (`test_ref_id_passthrough_for_str`, `test_ref_id_reads_xref_id_attribute`) 🟢
- [ ] **TT-02**, `get_name` nos quatro casos: pessoa real, `None`, atributo ausente e **formato vazio devolvendo `''`** 🟢
- [ ] **TT-03**, Carga popula as globais e devolve nomes ordenados, **um por pessoa** 🟢
- [ ] **TT-04**, Recarga substitui as globais: árvore menor depois de maior não deixa resíduo 🟢
- [ ] **TT-05**, Estrutura do grafo e tipos de nó (`person` / `family`) 🟢
- [ ] **TT-06**, `FAM` sem `xref_id` é ignorada 🟢
- [ ] **TT-07**, Limpeza de mojibake nos cenários de `tests/test_domain.py` 🟢
- [ ] **TT-08**, Segurança do upload: teto de corpo com `413`, chave derivada do conteúdo, recusa de GEDCOM inválido (`tests/test_upload_seguranca.py`) 🟢
- [ ] **TT-09**, Escrita fora da pasta por `gedcom_filename` manipulado é impossível (forma fechada) 🟢
- [ ] **TT-10**, Gravação idempotente: segundo envio do mesmo conteúdo não reescreve o arquivo 🟢
- [ ] **TT-11**, Preservação da extensão: enviar `.csv` gera `<chave>__<nome>.csv` 🟢
- [ ] **TT-12**, Rota ponta a ponta: `POST` sem arquivo, `POST` com nome vazio, `POST` válido e `POST` com GEDCOM inválido 🟡 *(o legado testa o núcleo; a rota é exercitada de passagem)*
- [ ] **TT-13**, Estado preservado após falha de parse: as globais anteriores continuam consultáveis 🟡

## Tarefas de Migração de Dados

**Não aplicável** — o sistema não tem banco de dados, schema ou volume a migrar. O único dado persistente são os arquivos enviados, já no formato final. 🟢

## Ordem Sugerida

1. **T-05 a T-08 e T-12 a T-16 primeiro (núcleo puro).** Não dependem de framework e concentram toda a decisão de negócio; devem estar implementadas e testadas (TT-01 a TT-07) antes de existir rota.
2. **T-01, T-02, T-09 a T-11 e T-20 (rota e guardas) em seguida.** Dependem do núcleo pronto.
3. **T-03, T-04 e T-19 (tratamento de erro e limite) depois da rota.** São a fronteira de recusa.
4. **T-17 e T-18 por último entre as de produção.** São contrato de estado e de saída, e só fazem sentido com o parse funcionando.
5. **Bloqueio entre units:** nenhuma outra unit pode ser implementada antes desta — `analise-dna` e `busca-caminho` leem o estado que esta publica.

## Lacunas Pendentes (🔴)

- **L-12 / P-04:** o `app.secret_key` embutido deve ser preservado por fidelidade, removido, ou movido para configuração por ambiente? Irrelevante em comportamento hoje (não há sessão), mas decisivo **antes** de qualquer introdução de `session`.
- **L-16:** o estado global reescrito a cada requisição, com 4 threads, permite contaminação entre requisições concorrentes. **Não medido.**
- **P-05:** o CSV não passa por validação de conteúdo. A assimetria em relação ao GEDCOM é deliberada ou herdada? Não há registro.
- **L-21:** não há decisão de negócio sobre não persistir resultados de análise.
- ✅ **Já decididas, não são pendências:** política de upload sem validação de extensão (`RISK-007`, deliberada); preservação da extensão original (correção do QMLY); `get_name` devolvendo `''` (paridade `DIV-001`).

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
