# Regression Watch — feature `012-pasta-canonica-no-repositorio`

> Data: `2026-10-09`
> Requirements: `_reversa_forward/012-pasta-canonica-no-repositorio/requirements.md`
> Legacy impact: `_reversa_forward/012-pasta-canonica-no-repositorio/legacy-impact.md`
> Âncora: **legado** (`_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`)

O que este arquivo vigia: as regras que **precisam continuar verdadeiras** nas próximas extrações e nas
próximas features. Cada item nasce de uma regra que esta feature tocou, e o sinal de violação é o que se
observa quando ela deixa de valer.

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| **W001** | `_reversa_sdd/upload-gedcom/contracts.md#2.2` | A pasta canônica é `<diretório do app>/uploads`, **dentro** do repositório, resolvida uma vez no import e ancorada em `__file__` — nunca no diretório corrente | presença | Qualquer artefato que declare a pasta canônica fora da árvore do repositório; resolução por diretório corrente; caminho de escrita divergindo do de leitura |
| **W002** | `_reversa_sdd/inventory.md#4`; `README.md` | `ANALISADOR_UPLOAD_FOLDER` é **sobreposição de processo**, sobretudo para a suíte e para o invólucro de paridade — não modo de operação | redação | A tabela ou a prosa apresentarem a variável como o caminho para operar; a linha sair da tabela de configuração (a suíte depende dela) |
| **W003** | `.gitignore`; `.reversa/principles.md#I` | `uploads/` está no `.gitignore` e cobre a pasta em qualquer profundidade | presença | A linha sair do `.gitignore`, ou o padrão deixar de casar `src/uploads/` — o dado real passa a ser versionável |
| **W004** | `.dockerignore` | `src/uploads/` é reexcluído do contexto de build **depois** de `!src/**` | presença | A linha sair, **ou** a ordem inverter: no `.dockerignore` a última regra que casa vence, e o dado real volta ao contexto de build sem que nenhuma linha seja removida |
| **W005** | `docker-compose.yml` | O serviço `app` monta `./src/uploads` sobre `/app/src/uploads` | presença | Caminho absoluto de host no `volumes:`; alvo interno diferente de `/app/src/uploads`; variável de ambiente de pasta declarada no serviço |
| **W006** | `README.md`; `tests/rodar_paridade.py` | O caminho documentado de execução da paridade é o **invólucro**, e o `harness.py` permanece byte a byte idêntico | presença | O `README.md` apontar o `harness.py` direto; o `sha256` do `harness.py` mudar |
| **W007** | `tests/test_guardas_do_armazenamento.py` | Existe teste que falha quando qualquer uma das duas guardas sai, com asserção de efeito e de ordem, exercitado por mutação | presença | O arquivo de teste desaparecer, ou as asserções virarem só de presença literal (a mutação de ordem tem de falhar) |
| **W008** | `_reversa_sdd/upload-gedcom/contracts.md#2.1`; `domain.md#3.5` | O nome no disco continua na forma fechada, com a extensão original preservada, e o sistema **nunca** apaga arquivo enviado | presença | Um arquivo de `src/uploads` renomeado ou removido pelo runtime; a forma do nome afrouxada; o expurgo deixando de operar por manifesto revisável |

## Observações (sem peso de regressão)

Itens que **não** entram na tabela principal, porque não nascem de regra 🟢 do `domain.md`: são achados
medidos nesta feature, declarados para não se perderem.

| ID | Achado | Origem | Por que não tem peso |
|----|--------|--------|---------------------|
| **OBS-01** | O critério de resíduo do manifesto é um **conjunto fechado de 12 nomes visíveis**, e não alcança nome novo de instrumento. A própria feature 010 documenta quatro arquivos `*__sonda_t014.*` que o conjunto não cobre | `D-12`; `tests/manutencao_de_uploads.py`; `010/onboarding.md` §16 | É limitação declarada de um critério de ferramenta, não regra de domínio. O expurgo não promete limpeza geral, e o fechamento testável é o manifesto regenerado devolver 0 |
| **OBS-02** | O banco tem **2 linhas** de `dna_analysis` com `tree_ref` apontando para `0646f8431ba58cca__sonda_t014.ged` e `dbc25ecc1cb17db3__sonda_t014.ged`, e **nenhum arquivo com `sonda` no nome existe** em lugar nenhum | `data-delta.md` §6; consulta ao histórico em 2026-10-09 | Referência não resolvida, mas **latente**: a varredura de `src/` mostra zero `SELECT`, e nenhuma das três `action` lê o histórico. Correção é decisão de produto, e o rastreamento é `/reversa-debugger` |
| **OBS-03** | Os dois instrumentos do refactor **já falhavam antes desta feature**: `registrar-diff.py` aborta em `src/core/gedcom_state.py` (apagado pelo `T023` da feature 005) e `verificar-estrutura.py` compara o `src/` de hoje com o congelado de 2026-10-03 | `evidence/T013-instrumentos-do-refactor.txt` | São artefatos de um refactor concluído, não runtime nem extração. A prova A/B estabelece o que importa: a retirada das cópias de arrasto **não altera a saída** de nenhum dos dois |
| **OBS-04** | Sobra `src/core/__pycache__/gedcom_state.cpython-314.pyc`, bytecode de um módulo **apagado** pela feature 005 | varredura de 2026-10-09 | Resíduo de bytecode, sem efeito em runtime (o import de `core.gedcom_state` falha, e nada o importa). Pode confundir uma extração futura que varra `__pycache__` |
| **OBS-05** | O `src/uploads` terminou com **18 arquivos e 27.925.843 bytes**, e os 3 grupos de duplicatas continuam **relatados e preservados** (`D-06` da 010) | `evidence/T021-numeros-finais.txt`; `evidence/duplicatas-pos-expurgo.txt` | É estado medido, não regra. A feature 011 depende dele: aba de árvore com 7 arquivos / 6 itens, aba de DNA com 10 arquivos / 10 itens |
| **OBS-06** | Cada execução da paridade deixa **4 byproducts** em `_reversa_sdd/parity/`: `_collect_cand.py`, `_collect_oracle.py`, `_obs_cand.json` e `_obs_oracle.json`. O `.gitignore` cobre os dois `.json` (`:18`) e os diretórios de execução (`:13`, `:14`, `:17`) — **mas não cobre os dois `_collect_*.py`** | `harness.py:459` (`runner = os.path.join(HERE, "_collect_%s.py" % tag)`); `.gitignore:12-18`; `git status --porcelain` depois do `T016`; limpador da 010 em `010/evidence/T024-limpeza-de-residuo.md` | Não é regra de domínio, e os arquivos **não** estão rastreados. Mas o próprio `.gitignore` declara esse lixo como padrão a ignorar e deixou dois nomes de fora: toda execução da paridade devolve dois `??` no `git status`, e o limpador da 010 já precisou removê-los à mão. **Conserto durável:** acrescentar `_reversa_sdd/parity/_collect_*.py` ao `.gitignore`, na mesma seção. Não foi feito aqui porque sai do escopo das 25 ações desta feature, e apagar os arquivos sem fechar a lacuna apenas esconderia o problema — a execução seguinte os recria |

## Histórico de re-extrações

*(vazio — preenchido pelo agente reverso quando o `/reversa` rodar de novo)*

| Data | Extração | W001 | W002 | W003 | W004 | W005 | W006 | W007 | W008 |
|------|----------|------|------|------|------|------|------|------|------|
| — | — | — | — | — | — | — | — | — | — |

## Arquivadas

*(vazio)*
