# upload-gedcom, Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Nível de documentação: **Essencial**. Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Re-extração de 2026-09-30. Substitui as tasks de 2026-08-03.

## Pré-requisitos

- [ ] Dependências disponíveis: `Flask` 3.1.3, `ged4py` 0.5.2, `networkx` 3.6.1 🟢
- [ ] Pasta `uploads/` criada e gravável (é criada no boot por `os.makedirs(..., exist_ok=True)`) 🟢
- [ ] `UPLOAD_FOLDER` definido (valor atual: `"uploads"`, relativo ao diretório de trabalho) 🟢
- [ ] **Não aplicável:** schema/migrations de banco — o sistema não tem banco de dados 🟢
- [ ] **Atenção ao diretório de trabalho:** `UPLOAD_FOLDER` é relativo, então o processo cria e usa `uploads/` no cwd. Rodar de dentro de outra pasta cria um `uploads/` novo lá. 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] **T-01**, Definir a rota única `GET /` que renderiza `index.html`
  - Origem no legado: `analisador-genealogico/app.py:18`, `:80`
  - Critério de pronto: `GET /` devolve 200 com o formulário de upload
  - Confiança: 🟢

- [ ] **T-02**, Implementar o despacho por campo `action` no `POST /`
  - Origem no legado: `analisador-genealogico/app.py:20-22`
  - Critério de pronto: `action=upload_gedcom` entra no ramo de upload; valores desconhecidos caem no render inicial
  - Confiança: 🟢

- [ ] **T-03**, Validar presença do campo `gedcom` e nome de arquivo não vazio
  - Origem no legado: `analisador-genealogico/app.py:23-27`
  - Critério de pronto: `"Nenhum arquivo GEDCOM enviado."` e `"Nenhum arquivo selecionado."` conforme o caso, ambos com `success=False`
  - Confiança: 🟢

- [ ] **T-04**, Persistir o arquivo em `UPLOAD_FOLDER` com o nome original
  - Origem no legado: `analisador-genealogico/app.py:29-30`, `reconstructed/upload.py:21`, `:24-25`
  - Critério de pronto: arquivo presente em `uploads/<nome>` após POST válido
  - Confiança: 🟢
  - ⚠️ Reproduzir **de propósito** a ausência de sanitização (decisão `questions.md#3`): não acrescentar validação de extensão/tamanho sem autorização explícita.

- [ ] **T-05**, Implementar `ref_id(val)` tolerante a objeto ged4py ou string
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:28-30`
  - Critério de pronto: `ref_id("X") == "X"` e `ref_id(obj) == obj.xref_id`
  - Confiança: 🟢

- [ ] **T-06**, Implementar `get_name(person)` com a expressão exata do oráculo
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:33-47`
  - Critério de pronto: `person.name.format()` quando `person and person.name`; `"Sem Nome"` caso contrário; **formato vazio devolve `''`**
  - Confiança: 🟢
  - ⚠️ **Não tratar formato vazio.** Foi essa "melhoria" que gerou a divergência `DIV-001`; ver `migration/parity_harness.md`.

- [ ] **T-07**, Implementar a limpeza de mojibake (`strip_bad_utf` e `demojibake`)
  - Origem no legado: `analisador-genealogico/reconstructed/domain.py:25-54`
  - Critério de pronto: 18 pares de substituição aplicados; round-trip `latin1 → utf-8` só quando há marcador e só se o resultado não tiver resíduo
  - Confiança: 🟢

- [ ] **T-08**, Parsear `INDI` e `FAM` com `GedcomReader` e indexar por `xref_id`
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:88-90`
  - Critério de pronto: `people` e `families` preenchidos após parse
  - Confiança: 🟢

- [ ] **T-09**, Construir o grafo não-direcionado com nós tipados e arestas só para ids resolvíveis
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:50-79`
  - Critério de pronto: nó de pessoa com `type="person"`, de família com `type="family"`; nenhuma aresta para id inexistente; `FAM` sem `xref_id` ignorada
  - Confiança: 🟢

- [ ] **T-10**, Construir o índice `child_to_family`
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:71`
  - Critério de pronto: pessoa com 2 famílias como `CHIL` aparece com 2 entradas na lista
  - Confiança: 🟢

- [ ] **T-11**, Publicar o estado global em memória com mutação in-place
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:92-98`
  - Critério de pronto: `people`, `families` e `child_to_family` sofrem `clear()` + `update()`; `graph` sofre rebind
  - Confiança: 🟢
  - ⚠️ A assimetria é deliberada: os três primeiros mantêm referências importadas válidas; `graph` é lido por import tardio dentro da função.

- [ ] **T-12**, Devolver a lista de nomes ordenada
  - Origem no legado: `analisador-genealogico/reconstructed/upload.py:99`
  - Critério de pronto: `all_names == sorted(all_names)` e um nome por pessoa
  - Confiança: 🟢

- [ ] **T-13**, Tratar exceção de parsing com mensagem amigável, preservando o estado anterior
  - Origem no legado: `analisador-genealogico/app.py:33-34`
  - Critério de pronto: GEDCOM malformado gera `"Erro ao processar GEDCOM: {e}"` sem quebrar; globais não são tocadas
  - Confiança: 🟢

- [ ] **T-14**, Implementar a guarda de arquivo inexistente para os fluxos de busca
  - Origem no legado: `analisador-genealogico/app.py:40-41`
  - Critério de pronto: `"Erro: Arquivo '{nome}' não existe mais."` quando o `.ged` foi removido do disco
  - Confiança: 🟢

## Tarefas de Teste

O legado **já tem** estes testes; a reimplementação deve passar pelos equivalentes:

- [ ] **TT-01**, `ref_id` com string e com objeto (`test_ref_id_passthrough_for_str`, `test_ref_id_reads_xref_id_attribute`) 🟢
- [ ] **TT-02**, `get_name` nos 4 casos: pessoa real, `None`/vazio, atributo ausente, **formato vazio devolvendo `''`** (`test_get_name_real_person`, `test_get_name_empty_none`, `test_get_name_absent_attribute_returns_sem_nome`, `test_get_name_empty_formatted_returns_empty_string`) 🟢
- [ ] **TT-03**, `get_name` para `INDI` sem tag `NAME` devolve `''` (`test_get_name_indian_without_name_tag_returns_empty_string`) 🟢
- [ ] **TT-04**, `ensure_dirs` cria `uploads/` (`test_ensure_dirs_creates_uploads`) 🟢
- [ ] **TT-05**, A carga popula as globais e devolve nomes ordenados (`test_load_populates_globals`, `test_load_returns_sorted_names`) 🟢
- [ ] **TT-06**, **Exatamente um nome por pessoa, sem entradas vazias** (`test_load_returns_exactly_one_name_per_person_and_no_empty_entries`) 🟢
- [ ] **TT-07**, Recarga substitui as globais (`test_reload_replaces_globals`) 🟢
- [ ] **TT-08**, Estrutura do grafo e tipos de nó (`test_build_graph_structure`, `test_graph_bidirectional_nodes_person_family_types`) 🟢
- [ ] **TT-09**, GEDCOM malformado levanta exceção (`test_parse_malformed_raises`) 🟢
- [ ] **TT-10**, `FAM` sem id é ignorada (`test_family_without_id_skipped`) 🟢
- [ ] **TT-11**, Limpeza de mojibake nos 6 cenários de `tests/test_domain.py` 🟢
- [ ] **TT-12**, Teste de integração da rota: POST sem arquivo, POST com nome vazio e POST válido 🟡 (não existe no legado — o legado testa o núcleo, não a rota)

## Tarefas de Migração de Dados

**Não aplicável** — o sistema não tem banco de dados, schema ou volume de dados a migrar. 🟢

## Ordem Sugerida

1. **T-03 a T-11 (núcleo puro) primeiro.** São funções sem dependência de framework e concentram toda a regra de negócio; devem ser implementadas e testadas (TT-01 a TT-11) antes de existir qualquer rota.
2. **T-01, T-02 e T-14 (rota) em seguida.** Dependem do núcleo pronto.
3. **T-12 e T-13 por último.** São contrato de saída e tratamento de erro.
4. **TT-12 (integração de rota)** só faz sentido depois de T-01/T-02.
5. **Bloqueios:** nenhuma outra unit pode ser implementada antes desta — `analise-dna` e `busca-caminho` leem o estado global que esta publica.

## Lacunas Pendentes (🔴)

- ✅ **L-01 RESOLVIDA em 2026-09-30:** `Family`, `GenealogyGraph` e `DNAGroup` eram arquitetura abandonada — **removidas** de `domain.py` por decisão do usuário (`questions.md#pergunta-3`). A remoção exigiu retirar 9 testes de `tests/test_domain.py`; suíte passou de 95 para 86 itens coletados, com 85 passando. O único erro de coleta é `PermissionError` do sandbox ao escanear diretórios temporários, reproduzível em qualquer `--basetemp` — restrição de ambiente, não regressão.
- ✅ **L-11 RESOLVIDA em 2026-09-30:** a contradição do `networkx.MultiGraph` no docstring de `GenealogyGraph` **desapareceu junto com a classe**. Não há mais divergência.
- **L-12:** O `app.secret_key` hardcoded deve ser preservado por fidelidade ou substituído por configuração? (Irrelevante em comportamento hoje — não há sessão.)
- **Já decididas, não são pendências:** política de upload sem validação (`questions.md#3`, aceita); uso do 1º ID em homônimos (`questions.md#2`, aceito).

---

*Gerado pelo Reversa-Writer em 2026-09-30 (re-extração).*
