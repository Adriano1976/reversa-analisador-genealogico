# ADR-27 — Histórico da análise em PostgreSQL, opcional e fora da decisão

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-08
- **Commit(s):** `187b3ef` (abre o ciclo `008-persistencia-postgres-docker`), `0971de9`, `ce8867a`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O sistema **nunca persistiu resultado** — o `domain.md` de 2026-10-05 registrava `L-21` como lacuna, e a pergunta correspondente foi respondida em 2026-10-05: você quer **histórico de análises** no sistema alvo. A feature 008 decidiu trazer essa capacidade para o legado, e o fez sob três restrições que não eram negociáveis:

1. **Não havia banco.** Nem DDL, nem driver instalado, nem serviço.
2. **A persistência não pode quebrar o que já funciona.** A suíte de testes e o harness de paridade **importam `src/app.py`**.
3. **O `dono` existe sem isolar** (`ADR-26`), e a persistência não podia ser a porta de entrada do isolamento pela lateral.

## Decisão

**Criar a persistência como quarta porta, opcional, que grava depois do cálculo e nunca participa dele.**

1. **Quarta porta `RegistroDeAnalises`**, com **um** método: `registrar(analise, dono) -> (referencia, aviso)`.
2. **Opcional por ambiente.** Sem `DATABASE_URL` a borda monta um registrador **nulo** (`_REGISTRO = None`), e a tela não muda um byte. O mesmo vale sem a referência da árvore: sem a chave de conteúdo não há o que gravar.
3. **O payload viaja em tipos próprios** (`AnaliseParaRegistrar`, `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise`), para que o adaptador receba **dado já projetado** e não precise conhecer o formato do resultado do núcleo.
4. **A projeção é pura e mora no caso de uso** (`ADR-33` para a variante da busca; aqui, `projetar_analise`).
5. **Falha de persistência vira aviso, nunca exceção** (`RN-13`), e a `RN-13` vale para **as duas metades**: nem a projeção nem a gravação podem impedir o resultado de chegar à tela.
6. **Import preguiçoso do driver**, dentro de `registrar`, e **nada acontece na construção** do adaptador.
7. **Uma conexão e UMA transação por análise**, sem pool.
8. **A árvore não é duplicada**: o que se grava é o **retrato** das pessoas daquela análise, e não a árvore.

## Evidência

- `init.sql` (189 linhas) cria **6 tabelas**: `dna_analysis`, `analysis_person`, `match_result`, `match_path_node`, `match_kit` e `skipped_match`.
- `RegistroDeAnalisesPostgres.registrar` faz o import dentro do `try`, devolve `(None, aviso)` no `ImportError`, e usa `with conexao:` (gerenciador do próprio psycopg2: commit no fim, rollback se algo levantar) com `finally` fechando a conexão.
- `_escrever` respeita a ordem das chaves estrangeiras: `dna_analysis` → `analysis_person` → `match_result` → `match_kit` / `match_path_node` → `skipped_match`.
- **`psycopg2-binary==2.9.13` está no pin e NÃO está instalado no `.venv`** — verificado no ambiente. A persistência fica desligada no interpretador oficial, e é exatamente o caso que o import preguiçoso existe para tornar inofensivo.
- `tests/test_persistencia_desabilitada.py` e `tests/test_persistencia_indisponivel.py` cobrem os estados degradados; **não existe teste de caminho feliz de INSERT**.
- `analysis_person` **não é** a tabela `person` do alvo: o comentário do `init.sql` declara que a árvore continua sendo o arquivo imutável de `src/uploads/`, referenciado por `tree_ref`.

## Justificativa

**Registrar não é decidir.** A porta responde "o que esta análise concluiu, e por quê" — não produz a resposta. Colocá-la **depois** do núcleo e **fora** de todo caminho de decisão é o que permite que ela seja opcional: um sistema que consulta o banco para decidir não pode funcionar sem ele; um que só registra, pode.

O import preguiçoso é requisito, e não estilo: `src/app.py` é importado pela suíte e pelo harness de paridade, e um `import psycopg2` no topo derrubaria os dois **por ambiente**.

## Consequências

- 🔴 **`L-26`: o driver está pinado e ausente do interpretador oficial.** A persistência desligada no `.venv` não é decisão — é ambiente. É o **inverso** da divergência de versão da rodada anterior.
- 🟢 **`L-27`: o resultado da suíte depende do ambiente.** Com `DATABASE_URL` presente e sem o driver, 2 testes de `test_persistencia_desabilitada.py` falham, porque o aviso não bloqueante aparece onde o contrato de tela congelado exige silêncio. Sem a variável: 527 passam, 9 pulados, 0 falham.
- 🔴 **`L-28`: não há teste do caminho de gravação.** Erro de SQL, de ordem de FK ou de tipo só apareceria no contêiner.
- 🔴 **`P-07` / `L-29`: o sistema passou a persistir dado pessoal que antes era efêmero.** `analysis_person` guarda xref, nome, sexo, nascimento, local de nascimento e falecimento — inclusive de pessoas vivas —, e **não há retenção, expurgo nem consentimento**. Apagar a árvore já não apaga o retrato. É a consequência de negócio mais séria desta decisão, e ela não estava no horizonte quando a persistência foi pedida.
- 🟡 **`owner_id` é gravado e não filtra nada.** A coluna satisfaz a forma do requisito do alvo (`migration/risk_register.md#risk-005`) e **não** o satisfaz em conteúdo: o teste negativo de 404 continua sendo portão de go-live da Onda 3.
- 🟢 **`match_result.result_ordinal` é o único campo que reproduz a ordem do núcleo** — que é `(tem_caminho, -cM)` e não cM decrescente puro. O índice `ix_match_result_ordinal` serve a ele, e o `init.sql` registra que o índice do alvo **não** reproduziria essa ordem.
