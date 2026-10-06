# ADR-17 — Upload por chave derivada do conteúdo, com teto de corpo e extensão preservada

- **Status:** Aceito e vigente (com uma correção de regressão em 2026-10-02)
- **Data da decisão:** 2026-10-02
- **Commit(s):** `12b2a34` (validação de limite), `7c8c5f9` e `c709ea0` (fechamentos), `07d53fd` (corrige a política de escrita)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O legado gravava o arquivo com **o nome enviado pelo cliente**: `os.path.join(UPLOAD_FOLDER, gedcom_file.filename)`. Isso produzia **três** defeitos de uma vez:

1. **Escrita fora da pasta de upload** por nome manipulado (`../`).
2. **Colisão silenciosa** entre envios de mesmo nome — um sobrescrevia o outro.
3. **Nada limitava o tamanho**: o multipart inteiro era gravado em disco **antes** de qualquer verificação de negócio.

Registrado como `BUG-20260929-QMLY`, com reprodução medida: um `POST` de `path_search` com `gedcom_filename` arbitrário respondia **200** e carregava o arquivo correspondente, **sem verificação de propriedade**.

## Decisão

1. **A chave de armazenamento é derivada do CONTEÚDO** (sha256 truncado em 16 hexadecimais), e não do nome do cliente nem de um UUID aleatório.
2. **Teto de corpo de 16 MB**, com `HTTP 413` e mensagem em português, aplicado **antes** de ler o corpo.
3. **Validação do valor recebido por forma fechada** — `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`.
4. **A extensão original é preservada** no nome visível.

## Evidência

- `src/utils/validate.py` — módulo **puro** (não importa Flask, não toca o disco); toda a decisão sobre o que pode ser gravado vive ali. Docstring declara que nasceu do `BUG-20260929-QMLY`.
- `src/app.py:32` (`MAX_CONTENT_LENGTH`), `:65-72` (handler de 413), `:90-96` (gravação idempotente), `:99-108` (`_resolver_caminho_armazenado`).
- `tests/test_upload_seguranca.py` — **425 linhas, 33 funções**: teto de requisição, chave derivada do conteúdo, recusa de GEDCOM inválido.
- `_reversa_sdd/addenda/bug-BUG-20260929-QMLY-v001.md` e `_reversa_bugs/upload-gedcom/bugs/BUG-20260929-QMLY-upload-sem-limites/`.

## Justificativa

**Por que derivação por conteúdo, e não UUID.** O formulário devolve `gedcom_filename` no **POST seguinte** (não há sessão — ver `permissions.md` §4.1). A mesma árvore reenviada **precisa** produzir a mesma chave, senão a continuidade entre requisições quebra e o arquivo é duplicado a cada uso. `validate.py:13-16` declara exatamente isso.

**Por que validação por forma, e não por lista negra.** A expressão exclui `/`, `\` e `..`: um valor manipulado **não tem como** escapar da pasta — não é preciso enumerar o perigo. É o mesmo raciocínio que, no ADR-05, trocou a lista negra do rótulo Mermaid por uma lista branca.

**Por que teto antes de ler.** Sem ele, a recusa por tamanho aconteceria **depois** de o dado já estar em disco — o custo do ataque seria pago antes da defesa.

**Por que preservar a extensão.** Aqui a decisão tem uma **correção registrada**: fixar a extensão em `.ged` renomeava o **CSV de DNA** para `<...>.csv.ged` e **quebrava a análise de DNA**. Foi uma **regressão do próprio QMLY**, encontrada e corrigida em 2026-10-02. O `_guardar_upload` serve aos dois tipos de arquivo, e a primeira versão assumiu que só havia um.

## Consequências

- ✅ **Os três defeitos do legado estão fechados**, e o vetor de "artefato HTML em caminho fixo" deixou de existir com o ADR-03.
- ✅ **Gravação idempotente:** arquivo com a mesma chave **não é reescrito** (`app.py:93-95`).
- ✅ **A pasta de upload é criada a partir da MESMA função que a resolve** (`app.py:60-62`), de modo que o diretório criado no import e o procurado nas requisições **não podem divergir**. A versão anterior era relativa ao diretório corrente, o que dava **dois caminhos para o mesmo arquivo**.
- ⚠️ **O retorno é o CAMINHO COMPLETO, nunca o nome.** O código registra por quê: a versão anterior devolvia o nome e a rota de DNA o passava ao parser, que procurava o CSV no diretório corrente e falhava com `No such file or directory`. **Nome e caminho nunca devem ser intercambiáveis.**
- 🔴 **A chave não é segredo — ela é identificador.** Como a validação é de **forma** e não de **propriedade**, quem conhece a chave carrega a árvore correspondente. O QMLY fechou o escape de caminho; **não** fechou a ausência de dono. Isso é o `BUG-20260929-BJJH` (ADR-18).
- ⚠️ **A validação de conteúdo é assimétrica:** só `kind == "gedcom"` passa por `validar_conteudo_gedcom`; o CSV **não** tem validação de conteúdo (`app.py:86`). Coerente com o ADR-16, mas não há registro de que a assimetria tenha sido decidida de propósito (`P-05`).
