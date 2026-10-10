# Unit `upload-gedcom` — Tarefas de Implementação

> Unit do tipo **endpoint** — `POST /` com `action=upload_gedcom`.
> Re-extração de **2026-10-10** (nível **Completo**). Substitui as tasks de 2026-10-05, que incluíam a tarefa de **publicar estado global** e a validação por **alfabeto fechado**.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Pré-requisitos

- [ ] Dependências disponíveis e **pinadas**: `Flask==3.1.3`, `ged4py==0.5.5`, `networkx==3.7`, `waitress==3.0.2` 🟢
- [ ] Pasta de upload criada e gravável — é criada pela **mesma função** que a resolve (`app.py:_pasta_uploads`) 🟢
- [ ] `ANALISADOR_UPLOAD_FOLDER` documentado (sobrepõe a pasta; usado pelos testes para não escrever na pasta real) 🟢
- [ ] `.gitignore` contém `uploads/` **com barra final** — é a garantia material de que dado real do operador não é versionado (`ADR-35`) 🟢
- [ ] **O import de `src/app.py` não pode exigir driver de banco, rede nem biblioteca de imagem** — a suíte e o harness de paridade o importam (`adrs/27`) 🟢
- [ ] **Não aplicável a esta unit:** schema, migrations ou banco de dados. A persistência em Postgres pertence a `analise-dna`, e é **opcional** 🟢

## Tarefas

> Cada tarefa referencia o arquivo do legado de onde o comportamento foi extraído.

- [ ] **T-01**, Implementar a rota `GET /` que renderiza `index.html` com as **duas abas de lista**
  - Origem no legado: `src/app.py:index`; `src/app.py:_listas_da_tela`
  - Critério de pronto: `GET /` devolve `200` com o formulário e as listas já preenchidas
  - Confiança: 🟢
  - ⚠️ As listas entram por **processador de contexto**: a rota tem **23** `render_template` (medidos em 2026-10-10), e repetir o argumento seria 23 lugares para esquecer um.

- [ ] **T-02**, Implementar o despacho por campo `action` no `POST /`
  - Origem no legado: `src/app.py:index`
  - Critério de pronto: os **cinco** valores de `action` entram nos seus ramos; `POST` sem referência devolve `"Erro: Arquivo GEDCOM não encontrado."`
  - Confiança: 🟢

- [ ] **T-03**, Validar presença do campo `gedcom` e nome de arquivo não vazio
  - Origem no legado: `src/app.py:index`
  - Critério de pronto: `"Nenhum arquivo GEDCOM enviado."` e `"Nenhum arquivo selecionado."` conforme o caso, ambos com `success=False`
  - Confiança: 🟢

- [ ] **T-04**, Implementar o teto de corpo de 16 MB com handler de `413` em português
  - Origem no legado: `src/app.py:TETO_DE_UPLOAD_EM_BYTES`, `:TETO_DE_UPLOAD_EM_MB`, handler de `RequestEntityTooLarge`
  - Critério de pronto: corpo acima do teto devolve `413` com `"Arquivo maior que o limite de {n} MB."`; **nenhum byte é lido nem gravado**
  - Confiança: 🟢
  - ⚠️ A mensagem **interpola** o valor do teto: mudar a constante muda **texto de contrato** (`spec-impact-matrix.md` §5).

- [ ] **T-05**, Implementar `validar_conteudo_gedcom` com as três recusas nomeadas
  - Origem no legado: `src/utils/validate.py:validar_conteudo_gedcom`
  - Critério de pronto: `arquivo vazio`, `conteudo binario` e `não começa com a declaração 0 HEAD`; remove **um** BOM UTF-8 e os espaços à esquerda antes de comparar
  - Confiança: 🟢
  - ⚠️ Validação **estreita de propósito**: só o cabeçalho. A gramática fica com o `ged4py`.

- [ ] **T-06**, Implementar `chave_de_armazenamento` = `sha256(conteudo).hexdigest()[:16]`
  - Origem no legado: `src/utils/validate.py:chave_de_armazenamento`
  - Critério de pronto: mesmo conteúdo → mesma chave, em processos diferentes
  - Confiança: 🟢

- [ ] **T-07**, Implementar `nome_visivel_seguro` preservando a extensão original
  - Origem no legado: `src/utils/validate.py:nome_visivel_seguro`
  - Critério de pronto: `/`, `\` e NUL viram `_`; acentos e espaços preservados; `matches.csv` continua `.csv`; vazio ou só pontos → `arvore.ged`; sem extensão → recebe `.ged`
  - Confiança: 🟢
  - ⚠️ **Não fixar a extensão em `.ged`.** Fixá-la renomeou o CSV para `<...>.csv.ged` e quebrou a análise de DNA — regressão do `BUG-20260929-QMLY`.
  - ⚠️ **Preserve acentos e espaços.** É essa preservação que torna a antiga validação por alfabeto fechado um defeito (`BUG-20261009-6RKP`).

- [ ] **T-08**, Implementar as **duas** funções de elegibilidade da referência
  - Origem no legado: `src/utils/validate.py:chave_recebida_e_valida` (**tem chave?**) e `:referencia_de_arquivo_da_pasta` (**posso tratar como nome?**)
  - Critério de pronto: `chave_recebida_e_valida` aceita apenas a forma canônica `<16 hex>__<nome visível>`; `referencia_de_arquivo_da_pasta` aceita **qualquer nome simples** e recusa barra, barra invertida, NUL, `.`, `..`, vazio, e exige que o valor seja `basename` de si mesmo
  - Confiança: 🟢
  - ⚠️ **São perguntas diferentes, e a diferença é a correção do `RN-20`.** A leitura exige a chave; a aposentadoria **não**, porque os arquivos sem chave são justamente os que o operador mais quer tirar da lista.

- [ ] **T-09**, Implementar `pode_ser_usado` e `motivo_de_indisponibilidade` para a tela de entrada
  - Origem no legado: `src/utils/validate.py`
  - Critério de pronto: a tela pergunta a **mesma** função que o resolvedor; dois motivos distintos — "sem chave" e "fora da forma"
  - Confiança: 🟢

- [ ] **T-10**, Implementar `ArmazenamentoEmDisco.guardar` com validação prévia e gravação idempotente, devolvendo o **caminho completo**
  - Origem no legado: `src/ports/adaptadores.py:guardar`
  - Critério de pronto: `(caminho_completo, None)` no sucesso; `(None, motivo)` na recusa; arquivo existente **não** é reescrito; o **adaptador não levanta exceção de domínio**
  - Confiança: 🟢
  - ⚠️ `dono` é recebido e **ignorado**: usá-lo na chave ou no caminho quebraria a `RN-02` (dois donos, mesmo conteúdo → **mesmo** arquivo).

- [ ] **T-11**, Implementar `ArmazenamentoEmDisco.resolver` validando a forma **antes** de qualquer acesso ao disco
  - Origem no legado: `src/ports/adaptadores.py:resolver`
  - Critério de pronto: valor sem chave → `None`; valor válido mas inexistente → `None`; **nenhum `os.path.exists` acontece antes da validação de forma**
  - Confiança: 🟢

- [ ] **T-12**, Implementar `ArmazenamentoEmDisco.listar` sem abrir arquivo nenhum
  - Origem no legado: `src/ports/adaptadores.py:listar`
  - Critério de pronto: do diretório lê o nome; do arquivo, apenas `st_size` e `st_mtime`; **pasta ausente devolve lista vazia, e não exceção**; subdiretório é ignorado; **nada é escrito**
  - Confiança: 🟢
  - ⚠️ Pasta ausente **não** é criada: `os.makedirs` dentro de uma leitura é efeito colateral escondido (`D-07`).

- [ ] **T-13**, Implementar `ArmazenamentoEmDisco.aposentar` movendo para `_aposentados/`
  - Origem no legado: `src/ports/adaptadores.py:aposentar`, `PASTA_DE_APOSENTADOS`
  - Critério de pronto: `os.replace` para `<pasta>/_aposentados/<referência>`; colisão recebe sufixo `.1`…`.99`; esgotado, devolve `False` **sem** sobrescrever; **nada é apagado**
  - Confiança: 🟢
  - ⚠️ **Duas camadas:** a forma de nome **e** a conferência de que o `dirname` do caminho resolvido é exatamente a pasta de upload. A primeira já garante; a segunda não confia nela.

- [ ] **T-14**, Implementar `guardar_com_substituicao` com a **foto de antes** e os três desfechos
  - Origem no legado: `src/application/reenvio.py`
  - Critério de pronto: `listar` **antes** de `guardar`; aposentar **todas** as versões anteriores de mesmo nome visível; desfecho `substituido` > `identico` > `novo`, nessa precedência
  - Confiança: 🟢
  - ⚠️ **A ordem é a regra.** Depois de `guardar`, "já existia" e "acabou de nascer" são indistinguíveis na pasta, porque `guardar` não sobrescreve.

- [ ] **T-15**, Implementar as **três mensagens** do reenvio
  - Origem no legado: `src/application/reenvio.py`, `src/app.py:index`
  - Critério de pronto: `substituido` → `"Arquivo 'X' atualizado: a versão anterior saiu da lista e continua guardada, inteira, na pasta de aposentados."`; `identico` → `"Arquivo 'X' já estava armazenado com o mesmo conteúdo: nada mudou."`; `novo` → `"Arquivo 'NOME ORIGINAL' carregado!"` (**literal congelado**)
  - Confiança: 🟢
  - ⚠️ **Preservar o literal de `novo`.** Ele é consumido por golden file e pelo harness de paridade; trocá-lo quebra a paridade sem necessidade.

- [ ] **T-16**, Implementar o caso de uso `upload_gedcom`, que tipifica o motivo em texto
  - Origem no legado: `src/application/upload_gedcom.py`; `src/core/erros.py`
  - Critério de pronto: `motivo` preenchido → `GedcomNaoSuportado(motivo)`; o adaptador **nunca** levanta exceção de domínio (achado `A002`)
  - Confiança: 🟢

- [ ] **T-17**, Implementar `CarregadorDeArvoresGedcom.carregar` como o **único** ponto da fronteira que parseia
  - Origem no legado: `src/ports/adaptadores.py:CarregadorDeArvoresGedcom`
  - Critério de pronto: resolve a referência pelo armazenamento recebido e chama `carregar_arvore`; `None` quando a referência não resolve
  - Confiança: 🟢
  - ⚠️ A porta tem **um único método**, e a `D-02` declara que **um segundo método significa que a decisão estava errada**.

- [ ] **T-18**, Implementar `carregar_arvore` devolvendo a **tupla**, sem publicar estado
  - Origem no legado: `src/parsers/gedcom_parser.py:carregar_arvore`; `adrs/24`
  - Critério de pronto: devolve `(people, families, graph, child_to_family)`; duas chamadas produzem **dois objetos independentes**; **nenhuma** variável de módulo é escrita
  - Confiança: 🟢
  - ⚠️ **Não reintroduzir mutação *in place* nem contador de versão.** Era esse desenho que permitia a contaminação entre requisições concorrentes.

- [ ] **T-19**, Implementar `ref_id(val)` tolerante a objeto ged4py ou string
  - Origem no legado: `src/core/registro.py:ref_id`
  - Critério de pronto: `ref_id("X") == "X"` e `ref_id(obj) == obj.xref_id`
  - Confiança: 🟢

- [ ] **T-20**, Implementar `get_name(person)` com a expressão exata
  - Origem no legado: `src/core/registro.py:get_name`
  - Critério de pronto: `person.name.format()` quando `person and person.name`; `"Sem Nome"` caso contrário; **formato vazio devolve `''`**
  - Confiança: 🟢
  - ⚠️ **Não tratar formato vazio.** Foi essa "melhoria" que gerou a divergência `DIV-001` contra o oráculo congelado.

- [ ] **T-21**, Implementar a limpeza de mojibake como autoridade única
  - Origem no legado: `src/utils/text_cleaning.py:strip_bad_utf`, `demojibake`
  - Critério de pronto: 18 pares de substituição; *round-trip* `latin1 → utf-8` só quando há indício de mojibake **e** só se o resultado não contiver resíduo
  - Confiança: 🟢

- [ ] **T-22**, Construir o grafo bipartido com nós tipados, arestas só para ids resolvíveis e o índice `child_to_family`
  - Origem no legado: `src/parsers/gedcom_parser.py`
  - Critério de pronto: `type="person"` e `type="family"`; nenhuma aresta para id inexistente; `FAM` sem `xref_id` ignorada; pessoa filha em 2 famílias aparece com 2 entradas
  - Confiança: 🟢

- [ ] **T-23**, Implementar `nomes_de_exibicao` devolvendo a lista ordenada
  - Origem no legado: `src/application/__init__.py:nomes_de_exibicao`
  - Critério de pronto: a lista é igual à sua versão ordenada, e a contagem é igual à de `people`
  - Confiança: 🟢
  - ⚠️ A ordenação é **`sorted` sobre `get_name`**, e é contrato da tela, não escolha de implementação.

- [ ] **T-24**, Ancorar a pasta de upload no arquivo do app
  - Origem no legado: `src/app.py:_pasta_uploads`
  - Critério de pronto: o diretório criado e o procurado vêm da **mesma** função; `ANALISADOR_UPLOAD_FOLDER` redireciona
  - Confiança: 🟢

- [ ] **T-25**, Implementar `_arvore_do_formulario` distinguindo **não existe** de **não pôde ser lido**
  - Origem no legado: `src/app.py:_arvore_do_formulario`
  - Critério de pronto: referência ausente → `"Erro: Arquivo GEDCOM não encontrado."`; referência que não resolve → `"Erro: Arquivo 'ROTULO' não existe mais."`; parse falho → `"Erro: o arquivo 'ROTULO' não pôde ser lido como GEDCOM. …"`
  - Confiança: 🟢

- [ ] **T-26**, Exigir `dono` em **todos** os métodos das portas, sem comportamento
  - Origem no legado: `src/ports/__init__.py`; `src/app.py:DONO_DO_PROCESSO`; `adrs/26`
  - Critério de pronto: parâmetro obrigatório, **último posicional e sem valor padrão**, recebido **por chamada** e não na construção do adaptador; declarado em **um único** lugar no `app.py`
  - Confiança: 🟢
  - ⚠️ **NÃO É MECANISMO DE SEGURANÇA.** Não entra na chave, no nome nem no caminho, e nenhuma entrega pode ser citada como tendo implementado isolamento.

## Tarefas de Teste

- [ ] **TT-01**, `ref_id` com string e com objeto 🟢
- [ ] **TT-02**, `get_name` nos quatro casos: pessoa real, `None`, atributo ausente e **formato vazio devolvendo `''`** 🟢
- [ ] **TT-03**, A árvore devolvida tem as quatro posições e um item por pessoa 🟢
- [ ] **TT-04**, Duas cargas consecutivas produzem árvores **independentes** — a primeira continua consultável 🟢
- [ ] **TT-05**, Estrutura do grafo e tipos de nó (`person` / `family`) 🟢
- [ ] **TT-06**, `FAM` sem `xref_id` é ignorada 🟢
- [ ] **TT-07**, Limpeza de mojibake nos cenários de `tests/test_domain.py` 🟢
- [ ] **TT-08**, Segurança do upload: teto de corpo com `413`, chave derivada do conteúdo, recusa de GEDCOM inválido (`tests/test_upload_seguranca.py`) 🟢
- [ ] **TT-09**, Escrita fora da pasta por referência manipulada é impossível — nas **duas** funções de elegibilidade 🟢
- [ ] **TT-10**, Gravação idempotente: segundo envio do mesmo conteúdo não reescreve o arquivo, e o desfecho é `identico` 🟢
- [ ] **TT-11**, Preservação da extensão: enviar `.csv` gera `<chave>__<nome>.csv` 🟢
- [ ] **TT-12**, Referência **com acento** é aceita na leitura e na aposentadoria (`BUG-20261009-6RKP`) 🟢
- [ ] **TT-13**, Reenvio com mesmo nome e conteúdo novo: a versão anterior vai para `_aposentados/`, o desfecho é `substituido`, e o arquivo anterior continua íntegro 🟢
- [ ] **TT-14**, Colisão em `_aposentados/`: o segundo aposentado recebe sufixo `.1`, e **nenhum** é sobrescrito 🟢
- [ ] **TT-15**, Aposentar arquivo **sem chave** funciona; a mesma referência **não** resolve para leitura 🟢
- [ ] **TT-16**, `dono` obrigatório: chamar qualquer método da porta sem o parâmetro falha em tempo de chamada 🟢
- [ ] **TT-17**, Dois envios do mesmo conteúdo com donos diferentes reencontram o **mesmo** arquivo (`RN-02`) 🟢
- [ ] **TT-18**, Pasta ausente: `listar` devolve lista vazia e **não** cria o diretório 🟢
- [ ] **TT-19**, Rota ponta a ponta: `POST` sem arquivo, com nome vazio, válido e com GEDCOM inválido 🟡 *(o legado testa o núcleo; a rota é exercitada de passagem)*
- [ ] **TT-20**, O import de `src/app.py` funciona **sem** driver de banco, **sem** rede e **sem** biblioteca de imagem 🟢

## Tarefas de Migração de Dados

**Não aplicável a esta unit.** Não há schema, migrations ou volume a migrar. O único dado persistente são os arquivos enviados, já no formato final — e o **conteúdo** deles nunca muda; o que muda é a pasta.

> ⚠️ **Ponto de atenção para quem migrar:** a pasta `src/uploads/` contém **13 arquivos do operador** e uma subpasta `_aposentados/`. Qualquer migração precisa **preservar os dois**, e nunca apagar (`RN-07`). Ver `adrs/35` para a garantia de não versionamento.

## Ordem Sugerida

1. **T-05 a T-09 e T-18 a T-23 primeiro (núcleo puro).** Não dependem de framework e concentram toda a decisão de negócio; devem estar implementadas e testadas (TT-01 a TT-07) antes de existir rota.
2. **T-10 a T-13 (a porta de armazenamento) em seguida.** É a fronteira que a rota consome; as duas camadas de defesa do `aposentar` são o ponto mais sensível.
3. **T-14 e T-15 (reenvio) depois da porta.** Dependem de `listar` e de `aposentar` para funcionar.
4. **T-01 a T-03, T-17 e T-24 a T-26 (rota, carregador e costura) em seguida.** Dependem do núcleo e da porta prontos.
5. **T-04 e T-16 (limite e tipificação) depois da rota.** São a fronteira de recusa.
6. **Bloqueio entre units:** nenhuma outra unit pode ser implementada antes desta — `tela-de-entrada`, `analise-dna` e `busca-caminho` consomem a árvore que esta devolve e a pasta que esta publica.

## Lacunas Pendentes (🔴)

- **`L-24` / `E-05` — a chave do cache de nomes pode não invalidar entre duas árvores de mesmo tamanho.** Não é lacuna desta unit, mas **esta unit é a causa indireta**: ao remover o contador `versao` (`ADR-24`), o cache passou a derivar a chave de `(len, primeira chave, última chave)`. Ver `flowcharts/busca-caminho.md` §13.
- **`P-05`** — o CSV não passa por validação de conteúdo. A assimetria em relação ao GEDCOM é deliberada ou herdada? **Continua sem registro**, e agora o CSV compartilha a **mesma** função de reenvio, o que aumenta a superfície da assimetria.
- **`M-07`** — o desfecho do reenvio não sobrevive à requisição: não há como auditar substituições depois do envio.
- **`M-05`** — o estado "aposentado" não é consultável pela aplicação.
- **Dívida #3** — a corrida sobre o armazenamento em disco permanece (verificar-e-depois-agir em `guardar` e `aposentar`). **Não medida.**
- ✅ **Já decididas, não são pendências:** política de upload sem validação de extensão (`RISK-007`); preservação da extensão original (correção do QMLY); `get_name` devolvendo `''` (paridade `DIV-001`); elegibilidade por forma de nome (`RN-20`), com a decisão de **não** afrouxar o `resolver`; o `dono` como costura sem comportamento (`adrs/26`); aposentar em vez de apagar (`adrs/30`).

---

*Gerado pelo Reversa-Writer em 2026-10-10 (re-extração, nível completo).*
