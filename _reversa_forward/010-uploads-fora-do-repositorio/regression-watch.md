# Regras sob vigilância — feature `010-uploads-fora-do-repositorio`

> Data: `2026-10-09`
> Origem dos itens: `_reversa_forward/010-uploads-fora-do-repositorio/legacy-impact.md`
> Natureza desta entrega: **nenhuma regra de domínio modificada**. Os itens abaixo vigiam o contrato de
> operação que a feature passou a declarar e as regras que ela **não** podia tocar.

## Itens sob vigilância

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| **W001** | `_reversa_sdd/upload-gedcom/contracts.md#2.2` | A pasta continua resolvida **uma vez, no import**, ancorada no arquivo do app, com `ANALISADOR_UPLOAD_FOLDER` sobrepondo | presença | Resolução por diretório corrente; leitura do ambiente a cada requisição; caminho de escrita divergindo do de leitura |
| **W002** | `_reversa_sdd/upload-gedcom/contracts.md#2.2` (linha "Remoção") e `_reversa_sdd/state-machines.md#5` | A aplicação **nunca** apaga um arquivo enviado; o expurgo é ferramenta separada, por manifesto e com simulação | ausência | Qualquer `unlink`, `os.remove`, `shutil.rmtree` ou `tempfile` em `src/`; expurgo automático no runtime |
| **W003** | `_reversa_sdd/upload-gedcom/contracts.md#2.1` | O nome no disco continua `<16 hexadecimais>__<nome visível>`, com a chave vinda do conteúdo | presença | Forma fechada afrouxada; chave aleatória em vez de derivada do conteúdo; renomeação de arquivo na migração |
| **W004** | `docker-compose.yml`, serviço `app` (feature 010) | A pasta canônica do host é montada no alvo interno que o app deriva (`/app/src/uploads`) | presença | Volta do ponto de montagem para `./src/uploads`; alvo interno diferente do derivado por `__file__` |
| **W005** | `README.md` §Configuração de execução e §Testes (feature 010) | A tabela de configuração lista `ANALISADOR_UPLOAD_FOLDER`, e a paridade é executada por `tests/rodar_paridade.py` | presença | Tabela incompleta outra vez; `README.md` apontando o `harness.py` direto como caminho de execução |
| **W006** | `_reversa_sdd/parity/harness.py` (feature 010, `D-07`) | O instrumento de paridade permanece **byte a byte igual** ao que a extração descreve | ausência de alteração | Qualquer edição no `harness.py`: a paridade passaria a medir com régua diferente da congelada, e a afirmação de 100 % perderia valor |
| **W007** | `tests/manutencao_de_uploads.py` (feature 010, `D-06`) | O expurgo remove **apenas** o que está no manifesto e **nunca** remove cópias idênticas: elas são relatadas | presença | Remoção fora do manifesto; deduplicação automática; remoção sem conferência de `sha256`; seguir link simbólico |
| **W008** | `_reversa_sdd/addenda/006`, `007` e `008` (vigentes) | Os adendos continuam válidos: o leiaute em disco não mudou e nenhum arquivo do operador foi renomeado ou removido | presença | Arquivo do operador ausente ou com hash diferente do inventário de `evidence/inventario-origem.txt` |

## Observações (sem peso de regressão)

Estas não são regras extraídas de código; entram aqui porque são o resultado desta entrega e ainda não
foram confirmadas por uma re-extração:

- **`RF-01` a `RF-08` implementados e medidos.** As evidências estão em
  `_reversa_forward/010-uploads-fora-do-repositorio/evidence/`, e o resumo com os números está no §16 do
  `onboarding.md` da feature.
- **O expurgo real não foi executado.** Os 18 arquivos de resíduo de instrumento (6.631 bytes) continuam
  em `src/uploads/`, e o manifesto está gerado e revisável em `evidence/manifesto-residuo.txt`. A remoção
  é decisão do operador.
- **Quatro arquivos sintéticos de sonda** ficaram no destino canônico durante as provas
  (`*__sonda_t014.ged` e `*__sonda_t014.csv`). São de fixture, não do operador.
- **Três grupos de duplicatas foram encontrados no dado do operador** e preservados: três cópias da
  árvore unificada, três de `Famílias_Sergipanas.csv` e duas de `Adriano_Santos.ged`. A decisão sobre
  elas continua aberta e é do operador.
- **O `harness.py` segue capaz de sujar a pasta real** se for invocado direto, sem o invólucro. É
  consequência declarada de `D-07` e está registrada no `investigation.md` da feature.

## Histórico de re-extrações

### Re-extração 2026-10-13 13:32 (verificação suplementar)

**Verificação suplementar, sem regeneração de spec:** o `_reversa_sdd/` é o de 2026-10-10; o que mudou desde então foi o **código**, e é o código de hoje que está medido. Suíte: **605 passam / 9 pulados / 0 falham**. Paridade: **100 %, exit 0, 6/6 fixtures** (`tests/rodar_paridade.py`).

**Segunda verificação real destes watch items.**

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | A pasta é resolvida uma vez, no import, ancorada no arquivo do app, com `ANALISADOR_UPLOAD_FOLDER` sobrepondo (medido em `src/app.py`). |
| W002 | 🟢 verde | **Zero** ocorrências de `unlink`, `os.remove`, `shutil.rmtree` e `tempfile` em todo o `src/` (medido). |
| W003 | 🟢 verde | O nome em disco segue `<16 hexadecimais>__<nome visível>`, com a chave vinda do conteúdo (medido em `src/utils/validate.py` e `src/ports/adaptadores.py`). |
| W004 | 🟢 verde | `docker-compose.yml` monta `./src/uploads:/app/src/uploads` (medido), o mesmo alvo que `src/app.py` deriva de `__file__`. |
| W005 | 🟢 verde | O `README.md` lista `ANALISADOR_UPLOAD_FOLDER` na tabela de configuração e manda executar a paridade pelo invólucro (`tests/rodar_paridade.py`), com o `harness.py` marcado como instrumento a não rodar direto. |
| W006 | 🟢 verde | `harness.py` com `sha256 33e45b055aef8458…`, **inalterado desde 2026-10-07** (commit `ffa835e`, que diz por quê) e sem alteração não commitada (`git status` limpo para o arquivo). O amarelo da passagem anterior era histórico: hoje o instrumento é exatamente o que a extração descreve. |
| W007 | 🟢 verde | `tests/manutencao_de_uploads.py` presente: manifesto revisável, conferência de `sha256`, expurgo que **não** remove fora do manifesto, duplicatas **relatadas** em vez de deduplicadas, e `--dry-run`. |
| W008 | 🔴 vermelho | **Segue vermelho, agora com a medição completa contra o inventário de 2026-10-09 (34 entradas).** **Nenhum conteúdo do operador foi perdido:** zero arquivos com hash desaparecido entre os dados do operador, zero arquivos com conteúdo diferente. **Sete renomeações** (acento e forma da chave: `Famílias_*` → `Familias_*`, e os dois `.ged` do operador ganharam prefixo de chave), todas de 2026-10-09/10 e já declaradas. Das 16 entradas do inventário que não estão mais na pasta, **9 reaparecem no repositório** (`_reversa_sdd/parity/fixtures/…` e `_reversa_forward/008…/evidence/_tmp_e2e/`) e **7 são sondas do instrumento** (`probe.ged` e um `matches_dois_kits.csv`) sem rastro. Quatro arquivos **novos** foram acrescentados pelo operador. Conclusão: a **integridade** está preservada e o **nome** não. A triagem pedida na passagem anterior continua **pendente e é ato humano**: ou o item passa a vigiar integridade (nada removido, conteúdo preservado), ou permanece vermelho a cada rodada por um fato histórico que não se desfaz. *A tabela principal não foi alterada.* |

### Re-extração 2026-10-10 21:40

**Primeira verificação real destes watch items.**

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | A pasta é resolvida **uma vez** e ancorada no arquivo do app (`src/app.py:127-130`, medido), com `ANALISADOR_UPLOAD_FOLDER` como sobreposição de processo. `upload-gedcom/contracts.md` §2.3. |
| W002 | 🟢 verde | **Zero ocorrências** de `os.remove`, `os.unlink` ou `shutil.rmtree` em todo o `src/` (medido). `upload-gedcom/contracts.md` §2.3, linha "Remoção". |
| W003 | 🟢 verde | Forma `<16 hex>__<nome visível>` com a chave vinda do conteúdo — `upload-gedcom/contracts.md` §2.1. ⚠️ **Atenção à leitura:** a *elegibilidade* deixou de ser alfabeto fechado (`RN-20`), mas a **forma gravada não afrouxou** — mudou o critério de aceitação da referência, não o nome escrito em disco. |
| W004 | 🟢 verde | `docker-compose.yml` monta `./src/uploads:/app/src/uploads` (medido) e o `.dockerignore` reexclui `src/uploads/` **depois** de `!src/**`. O alvo interno é o mesmo que `src/app.py` deriva de `__file__`. |
| W005 | 🟢 verde | O `README.md` lista `ANALISADOR_UPLOAD_FOLDER` na tabela de configuração (linha 278), declara que ela é sobreposição de processo (linha 307), e a paridade é executada por `tests/rodar_paridade.py` (linha 644), com o `harness.py` marcado como "não deve ser executado direto" (linha 647). |
| W006 | 🟡 amarelo | **O instrumento não é byte a byte o da publicação — e a mudança é deliberada, commitada e sem drift.** O `harness.py` de hoje tem `sha256 33e45b05…`; o último commit que o tocou é `ffa835e test(parity): atualiza o harness para a fronteira sem a casca`, da **própria feature 006**. O `git diff` contra o HEAD é **vazio**. A regra que este item protege — *a régua não pode mudar em silêncio* — está satisfeita: ela mudou **com mensagem que diz por quê**. |
| W007 | 🟢 verde | `tests/manutencao_de_uploads.py` presente: expurgo por manifesto, conferência de `sha256` e simulação (`D-06`). |
| W008 | 🔴 vermelho | **A expectativa NÃO bate, e a causa é registrada: 4 arquivos do operador FORAM renomeados em 2026-10-09.** A mitigação da feature **011** tirou acento e espaço do nome visível de 4 arquivos, preservando a chave (`OBS-05` da 011, `temporary: true`). **Nenhum arquivo foi removido ou perdido** — o conteúdo é o mesmo e a chave foi preservada —, e a premissa da renomeação foi depois **resolvida em sentido contrário** (o conserto decidiu aceitar acento na leitura, `RN-20`), mas o conserto **não desfaz** as renomeações, e o operador renomeou outros por conta própria depois. **Triagem necessária:** ou o item passa a vigiar a **integridade** (nada removido, conteúdo preservado) em vez do **nome**, ou permanece vermelho a cada rodada por um fato histórico que não se desfaz. **O Reversa não altera a tabela principal** — a decisão é humana. |

| Data | Extração | Veredito |
|------|----------|----------|
| — | — | Nenhuma re-extração executada desde esta entrega |

## Arquivadas

| ID | Item | Motivo | Data |
|----|------|--------|------|
| — | — | Nenhum item arquivado | — |
