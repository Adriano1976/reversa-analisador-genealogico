# Onboarding: núcleo puro em `src/core/`

> Identificador: `005-nucleo-puro-src`
> Data: `2026-10-06`
> Requirements: `_reversa_forward/005-nucleo-puro-src/requirements.md`

## Para quem é este documento

Para quem vai verificar esta feature pela primeira vez e precisa de um caminho executável, na ordem, com o resultado esperado em cada passo. **Não** é um tutorial do Reversa nem do analisador: é o roteiro de aceite desta mudança.

⚠️ **Dado sensível.** Todos os passos usam **fixtures sintéticas** de `_reversa_sdd/parity/fixtures/`. Nunca use arquivos de `src/uploads/`: eles contêm dados genéticos reais de terceiros (Princípio I de `.reversa/principles.md`).

## Pré-requisitos

| Item | Valor |
|---|---|
| Interpretador | `.venv` do projeto (Python 3.14), que é o oficial conforme `README.md` |
| Dependências | instaladas a partir de `requirements.txt` (versões fixadas com `==`) |
| Oráculo | `_reversa_sdd/oracle/app_legacy_e43ca22.py`, **somente leitura** |
| Diretório temporário | **precisa ser gravável** — ver a nota abaixo |

> ⚠️ **Restrição de ambiente medida em 2026-10-06.** Sem um diretório temporário gravável, o `pytest` falha **antes de coletar**, com `FileNotFoundError: No usable temporary directory found`. Não é regressão: é a mesma restrição que produz os 15 erros de ambiente conhecidos. Aponte `TEMP`/`TMP` para um caminho gravável antes de rodar.

## Passo 1 — Linha de base antes de qualquer mudança

Execute, com `TEMP` e `TMP` apontando para um caminho gravável:

```powershell
py -3.14 -m pytest -q
```

**Esperado:** `164 passed, 15 errors`. Os 15 erros são todos de `tests/test_upload_seguranca.py`, em `setup`, por `PermissionError` do sandbox no diretório temporário. **Anote o número 164**: é a linha de base da `RF-11`, medida em 2026-10-06.

**Reprovado se:** a contagem de aprovados for menor que 164. Um teste removido ou desabilitado é recusa de entrega, não economia.

## Passo 2 — Limpar o resíduo do harness

Antes de rodar a paridade, remova o resíduo de execuções anteriores:

```powershell
python _reversa_sdd\parity\_clean_residue.py
```

**Esperado:** o comando remove `_collect_oracle.py`, `_collect_cand.py`, `_obs_oracle.json`, `_obs_cand.json` e os diretórios `.parity-run-*/`. Sem isso, o `git status` mistura resíduo de instrumento com entrega da feature.

## Passo 3 — Paridade diferencial

```powershell
python _reversa_sdd\parity\harness.py
```

**Esperado:** `PARIDADE 100% (zero divergencia)` nas **6 fixtures** sintéticas.

O harness executa o **oráculo congelado** em um subprocesso e o **candidato** em outro, e compara estruturas serializadas com igualdade exata. Ele imprime quatro linhas de contexto úteis:

- `oraculo   : _reversa_sdd/oracle/app_legacy_e43ca22.py` — a proveniência importa. Se apontar para outro arquivo, a medição é inválida (RISK-002).
- `candidato : src/` — o candidato desta feature é `src/`, e não o `reconstructed/` que o `parity_harness.md` ainda documenta.
- `probes    : ...` — quantos valores estão sendo comparados.
- Qualquer divergência vem com **fixture e chave**, e a causa raiz é reportada antes dos sintomas.

**Reprovado se:** houver **qualquer** divergência, mesmo que o resultado novo "pareça mais correto". É o No-go absoluto do `cutover_plan.md`.

**Não confunda:** `INCONCLUSIVO` **não** é paridade. O harness reporta INCONCLUSIVO quando um coletor estoura o tempo limite, e isso significa "não sei", nunca "está certo".

## Passo 4 — Paridade dos probes novos (`RF-10`)

Depois do passo 1 do plano de migração, o harness deve reportar também os probes de:

- **aceitação do matching** — `build_ged_indexes` e `match_candidates`, com veredito **e motivo** para cada candidato;
- **decomposição do caminho** — `split_path_by_marriage` e o par de afinidade do caminho indireto.

**Esperado:** os novos probes aparecem na saída e seguem em paridade 100%.

**Para que serve:** hoje as regras A/B/C/D, o filtro anti-falso-positivo e o Jaccard **não têm probe diferencial**. Como esta feature muda justamente a assinatura dessas funções, sem este passo a decisão mais sensível do sistema ficaria sem rede durante a mudança.

## Passo 5 — Guarda de dependências do núcleo (`RF-08`, `RF-09`)

```powershell
py -3.14 -m pytest -q tests/test_dependencias_nucleo.py
```

**Esperado:** passa. O teste falha se qualquer módulo de `src/core/` importar `flask`, `fastapi`, `sqlalchemy`, `pydantic`, `waitress`, `parsers/` ou `reporting/`, ou se contiver leitura de arquivo, de rede ou de variável de ambiente.

> O nome exato do arquivo é definido pela ação correspondente do `actions.md`. Se ele ainda não existir, este passo é o que a feature precisa criar.

## Passo 6 — O sistema continua de pé (verificação manual)

A paridade prova o **domínio**. Ela não prova que o aplicativo ainda sobe e responde — e esta feature mexe em `app.py`.

1. Suba a aplicação:

   ```powershell
   py -3.14 src\app.py
   ```

   **Esperado:** uma linha de inicialização com o servidor, o endereço e a porta em uso. O padrão é `127.0.0.1` e a porta padrão do código.

2. Abra `http://127.0.0.1:5088/` no navegador.

   **Esperado:** `HTTP 200`, o cabeçalho de resposta com `Server: waitress` e o formulário de upload presente.

3. Suba o GEDCOM sintético `_reversa_sdd/parity/fixtures/gedcom/basic.ged`.

   **Esperado:** a lista de nomes é oferecida no campo de sugestão. É a mesma lista que o oráculo produz — o harness compara isso no probe `names`.

4. Escolha uma pessoa da lista como raiz e suba o CSV `_reversa_sdd/parity/fixtures/dna/cm_boundaries.csv`.

   **Esperado:** as quatro seções de resultado aparecem. A tabela de cM traz **listas** de relacionamentos, e valores `0` e `-5` produzem **lista vazia** — não o literal "Relação distante ou indeterminada", que só aparece com valor positivo fora de todas as faixas.

5. Use a aba de busca de caminho entre duas pessoas da árvore.

   **Esperado:** o caminho, o ancestral comum e, quando houver casamento no trajeto, a marcação de **afinidade** — nunca apresentada como parentesco sanguíneo.

6. Encerre com `Ctrl+C` e confirme que a porta foi liberada.

**Reprovado se:** o app não sobe, a rota não responde `200`, o formulário não aparece, ou qualquer resultado de domínio divergir do que a mesma entrada produzia antes da mudança.

## Passo 7 — O estado global não existe mais

```powershell
Select-String -Path src\core\*.py -Pattern "^people\s*=|^families\s*=|^graph\s*=|^child_to_family\s*=|^versao\s*="
```

**Esperado:** nenhuma linha de nível de módulo atribuindo essas estruturas.

**Reprovado se:** qualquer módulo de `src/core/` ainda declarar estado mutável de módulo.

## Passo 8 — O parse devolve, não escreve (`RF-13`)

```powershell
Select-String -Path src\parsers\gedcom_parser.py -Pattern "\.clear\(\)|\.update\(|gedcom_state"
```

**Esperado:** nenhuma ocorrência. O parse devolve a árvore como valor.

## Passo 9 — Recolher e registrar

- Registre a evidência em `_reversa_forward/005-nucleo-puro-src/evidence/`: saída da suíte, saída do harness e saída da verificação manual.
- Rode `python _reversa_sdd\parity\_clean_residue.py` de novo.
- Confira `git status` **antes** de commitar: nenhum arquivo de `src/uploads/`, nenhum `.ged`/`.csv` de dado real, nenhum resíduo de instrumento (Princípio I).
- Se algo divergir e você não souber a causa, **não** ajuste a asserção. Registre a divergência antes de corrigir — é a regra do `cutover_plan.md` § plano de rollback.

## Resumo dos comandos

```powershell
# 1. linha de base
py -3.14 -m pytest -q

# 2. limpar resíduo
python _reversa_sdd\parity\_clean_residue.py

# 3. paridade
python _reversa_sdd\parity\harness.py

# 4. guarda do núcleo (arquivo criado pela feature)
py -3.14 -m pytest -q tests/test_dependencias_nucleo.py

# 5. verificação manual
py -3.14 src\app.py
# abrir http://127.0.0.1:5088/
```

## O que este roteiro NÃO cobre

- **Análise de DNA ponta a ponta contra o oráculo.** O harness não orquestra `dna_analysis(csv, root)` contra o fluxo equivalente do oráculo, porque no legado esse fluxo vive **dentro da rota Flask** e extraí-lo exige executar o app e ler o HTML. O passo 6 cobre isso de forma manual, não automática.
- **Paridade visual das telas.** Os goldens continuam com **0 capturados** (AMB-022). Nenhuma tela foi comparada byte a byte, e esta feature não muda `src/templates/index.html`.
- **Concorrência.** A dívida #3 (`architecture.md#7`) é de contaminação entre requisições concorrentes. Esta feature **reduz a superfície** — remove o global que as threads compartilham — mas não fecha a dívida, que é da Onda 3.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-06 | Versão inicial gerada por `/reversa-plan` | reversa |
